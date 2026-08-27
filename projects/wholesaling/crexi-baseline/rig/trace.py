"""Per-listing pipeline trace + provenance ledger for the Crexi value-route lane.

Wraps the product's own seams at runtime (no product-code edits) so every listing
yields ONE record spanning income -> arv -> linkage -> routing -> gate, tagged with
stable defect ids from defects.py AND carrying a per-value PROVENANCE LEDGER
(provenance.py): for every value that would appear on a sellable lead, what
produced it -- deterministic code, an LLM, an external API, or a default constant --
and, when it is a fallback, what was attempted first and why it lost.

Division of labour: this module CAPTURES (wrap a seam, write evidence into CUR).
provenance.py DERIVES (evidence -> producer records) and AGGREGATES. So a taxonomy
fix re-derives from a frozen trace instead of forcing a re-run.

Design note: the seams below are private names in product modules. A rename would
silently drop a column, so install() ASSERTS every target exists and records its
source digest -- a drifted seam is visible, not silent.

  ./rig/run.sh $CREXI_BASELINE_ROOT/rig/trace.py --limit 10
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.environ["WHOLESALING_REPO"], "backend"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cassette import ai_from_env as ai_cassette_from_env  # noqa: E402
from cassette import from_env as cassette_from_env  # noqa: E402
from defects import DEFECTS, summarize  # noqa: E402
from provenance import build_ledger  # noqa: E402

CUR: dict = {}          # accumulates the record for the listing in flight
PATCHES: list[dict] = []
HTTP: list[dict] = []   # every outbound Crexi call, in order (external-api provenance)
AI: list[dict] = []     # every LLM completion, in order (llm provenance)


def _asset_of(obj) -> str | None:
    """Asset id from either a CrexiListing (asset_id) or the Property the ARV seam sees
    (id formatted 'crexi:<asset_id>')."""
    aid = getattr(obj, "asset_id", None)
    if aid:
        return str(aid)
    pid = getattr(obj, "id", None)
    if isinstance(pid, str) and pid.startswith("crexi:"):
        return pid.split(":", 1)[1]
    return None


def _boundary(aid: str | None) -> None:
    """A listing is finished when a DIFFERENT asset appears at an OPENING seam.

    Necessary because seams do not fire in a fixed order: _process_listing computes
    the ARV BEFORE resolving income, so keying the boundary off income alone
    attributed each listing's ARV to its predecessor.

    Only the three OPENING seams may call this -- resolve_income, compute_mf_arv and
    link_listing, i.e. the ones that receive the listing itself and can be the first
    thing that fires for a new asset. Everything else is nested inside one of them
    and must use _inner().
    """
    if aid and CUR.get("asset_id") and CUR["asset_id"] != aid:
        FLUSH()
    if aid:
        CUR["asset_id"] = aid


def _inner(aid: str | None = None) -> None:
    """Boundary check for a seam that is always NESTED inside an opening seam.

    Such a seam must never flush: it cannot be the first event of a new listing, so a
    disagreeing id means the attribution is wrong, not that a listing ended. Flushing
    on it would re-introduce exactly the misattribution _boundary() exists to prevent
    (a deduped property carries a canonical id that is not this listing's asset id).
    Records the disagreement instead, so it is visible rather than silently absorbed.
    """
    if aid and CUR.get("asset_id") and CUR["asset_id"] != aid:
        CUR.setdefault("seam_id_mismatch", []).append(aid)


def _digest(fn) -> str:
    try:
        return hashlib.sha256(inspect.getsource(fn).encode()).hexdigest()[:12]
    except (OSError, TypeError):
        return "?"


def _reject_reason(facts, listing) -> tuple[str, str]:
    """Which guard in _validate_facts rejected this extraction, mirroring its order.

    Mirrored (not re-implemented) on purpose: it reads the product's OWN constants and
    helpers, so a bound change moves this with it. The order below is the order in
    listing_income._validate_facts -- the first failing guard is the rejecting check,
    which is what `fallback_from.rejected_by` must name.
    """
    import app.services.listing_income as LI

    if facts.confidence < LI._MIN_LLM_CONFIDENCE:
        return "confidence_floor", f"self-reported {facts.confidence} < {LI._MIN_LLM_CONFIDENCE}"
    g = facts.gross_monthly_rent
    if g is None or g <= 0:
        return "no_gross", "the extraction reported no stated income (a correct answer, not an error)"
    units = listing.units or (len(facts.per_unit_rents) or None)
    hi = (units or 4) * LI._MAX_UNIT_RENT
    if not (LI._MIN_UNIT_RENT <= g <= hi):
        return "band", (f"gross {g} outside [{LI._MIN_UNIT_RENT}, units({units}) x "
                        f"_MAX_UNIT_RENT({LI._MAX_UNIT_RENT}) = {hi}]")
    for r in facts.per_unit_rents:
        if r and not (LI._MIN_UNIT_RENT <= r <= LI._MAX_UNIT_RENT):
            return "per_unit_band", f"per-unit {r} outside [{LI._MIN_UNIT_RENT}, {LI._MAX_UNIT_RENT}]"
    return "not_in_source", ("neither the gross nor 12x it appears in the description "
                            "(_numbers_in/_appears anti-hallucination check)")


def runtime_consts() -> dict:
    """The product constants the ledger cites, read from the product at run time.

    Read, never hardcoded: a ledger that names ``x0.55`` while the parameter says
    something else is worse than one that names nothing.
    """
    import app.providers.crexi.arv as CA
    import app.services.listing_income as LI
    from app.config.parameters import DEFAULT_PARAMETERS as P

    return {
        "rent_fmr_haircut_pct": P.type1.rent_fmr_haircut_pct,
        "no_provenance_confidence_discount": P.type1.no_provenance_confidence_discount,
        "arv_confidence_floor": 0.35,  # the F-B3 credibility floor (defects.py)
        "arv_recency_months": CA.DEFAULT_RECENCY_MONTHS,
        "rehab_default_sqft": P.rehab.default_sqft,
        "rehab_market_cost_per_sqft": P.rehab.market_cost_per_sqft,
        "min_llm_confidence": LI._MIN_LLM_CONFIDENCE,
        "min_unit_rent": LI._MIN_UNIT_RENT,
        "max_unit_rent": LI._MAX_UNIT_RENT,
    }


def install() -> None:
    """Wrap every seam. Fails loudly if a target has moved."""
    import app.generation.message_generator as MG
    import app.guardrails.apply as GA
    import app.persistence.repositories as REPO
    import app.services.crexi_linkage as CL
    import app.services.crexi_value_route as VR
    import app.services.listing_income as LI
    import app.services.recompute as RC
    import app.valuation.engine as VE
    import app.workers.guardrail as WG
    import app.workers.routing as WR

    # Every seam this trace depends on, asserted up front. A rename must fail here
    # rather than silently drop a provenance column (the discipline that keeps a
    # missing producer distinguishable from an ABSENT one).
    targets = [
        # income ladder, tier by tier
        (LI, "_try_llm_extract"), (LI, "_validate_facts"), (LI, "resolve_income"),
        (LI, "request_listing_extract"), (LI, "_from_regex"), (LI, "_parse_unit_mix"),
        (LI, "_from_unit_mix_fmr"), (LI, "_from_market"),
        (LI, "_MIN_LLM_CONFIDENCE"), (LI, "_MIN_UNIT_RENT"), (LI, "_MAX_UNIT_RENT"),
        (LI, "_numbers_in"), (LI, "_appears"),
        # the LLM transport chokepoint (model id + prompt digest for producer_detail)
        (MG, "ai_complete"),
        # arv
        (VR, "compute_mf_arv"),
        # linkage -> routing -> rehab -> gate
        (CL, "link_listing"), (WR, "route"), (VE, "estimate_rehab"), (RC, "estimate_rehab"),
        (WG, "apply_gate"), (GA, "evaluate"), (REPO, "append_audit_log"),
        (VR, "_hold_for_mf_review"), (VR, "MF_REVIEW_HOLD_REASON"),
    ]
    for mod, name in targets:
        obj = getattr(mod, name, None)
        if obj is None:
            raise SystemExit(f"trace: seam {mod.__name__}.{name} does not exist -- product code moved")
        PATCHES.append({"target": f"{mod.__name__}.{name}", "source_sha12": _digest(obj)})

    # ---- external API: every outbound Crexi request ------------------------
    # Answers "does a re-run actually stay offline?" and supplies the
    # external-api half of the provenance ledger. _request is the single
    # chokepoint for search/detail/brokers/gallery/market-stats.
    from app.providers.crexi.client import CrexiClient

    _req = CrexiClient._request

    def t_req(self, method, path, *a, **k):
        t0 = time.time()
        err = None
        try:
            return _req(self, method, path, *a, **k)
        except Exception as exc:
            err = type(exc).__name__
            raise
        finally:
            ev = {"method": method, "path": path,
                  "ms": round((time.time() - t0) * 1000), "error": err,
                  "asset_id": CUR.get("asset_id")}
            HTTP.append(ev)
            CUR["http_calls"] = CUR.get("http_calls", 0) + 1

    CrexiClient._request = t_req
    PATCHES.append({"target": "CrexiClient._request", "source_sha12": _digest(_req)})

    # ---- llm transport: the single chokepoint every AI call passes through --
    # Supplies the llm half of the ledger (`producer_detail` = served model + prompt
    # digest) and is what makes arm A vs arm B legible: in arm A this raises before any
    # provider is tried, so the income tier-1 loss is "transport_unavailable", not
    # "the model had nothing to say".
    _aic = MG.ai_complete

    def t_aic(task, settings, *, client=None, **k):
        t0 = time.time()
        ev = {"kind": getattr(task, "kind", None), "label": getattr(task, "label", None),
              "prompt_sha12": hashlib.sha256(
                  (getattr(task, "system", "") or "").encode()).hexdigest()[:12],
              "provider": None, "model": None, "error": None}
        try:
            comp = _aic(task, settings, client=client, **k)
            ev["provider"], ev["model"] = comp.provider, comp.model
            return comp
        except Exception as exc:
            ev["error"] = f"{type(exc).__name__}: {str(exc)[:120]}"
            raise
        finally:
            ev["ms"] = round((time.time() - t0) * 1000)
            CUR.setdefault("llm_calls", []).append(ev)
            AI.append(dict(ev, asset_id=CUR.get("asset_id")))
            if ev["label"] == "extract":
                CUR.setdefault("llm_transport", {}).update(
                    provider=ev["provider"], model=ev["model"], prompt_sha12=ev["prompt_sha12"])

    MG.ai_complete = t_aic

    # ---- income: tier 1 (llm) ---------------------------------------------
    _llm, _val, _rle = LI._try_llm_extract, LI._validate_facts, LI.request_listing_extract

    def t_rle(ctx, settings, *, client=None):
        # _try_llm_extract swallows MessageGeneratorError, so WHY the tier lost is only
        # observable here. Without it arm A and arm B are indistinguishable in the trace.
        t = CUR.setdefault("llm_transport", {})
        t.update(attempted=True, served=False, error=None)
        t0 = time.time()
        try:
            out = _rle(ctx, settings, client=client)
            t.update(served=True, model=getattr(out, "model", None) or t.get("model"))
            return out
        except Exception as exc:
            t["error"] = f"{type(exc).__name__}: {str(exc)[:120]}"
            raise
        finally:
            t["ms"] = round((time.time() - t0) * 1000)

    LI.request_listing_extract = t_rle

    def t_llm(*a, **k):
        try:
            o = _llm(*a, **k)
            CUR["llm_gross"] = getattr(o, "gross_monthly_rent", None) if o else None
            CUR["llm_conf"] = getattr(o, "confidence", None) if o else None
            CUR["llm_per_unit"] = list(getattr(o, "per_unit_rents", []) or []) if o else []
            return o
        except Exception as exc:
            CUR["llm_error"] = type(exc).__name__
            raise

    def t_val(facts, listing):
        out = _val(facts, listing)
        CUR["validator_accepted"] = out is not None
        v = CUR.setdefault("validator", {})
        v.update(ran=True, accepted=out is not None)
        g = getattr(facts, "gross_monthly_rent", None)
        if out is None:
            reason, detail = _reject_reason(facts, listing)
            v.update(reject_reason=reason, reject_detail=detail)
        if out is None and g:
            units = listing.units or 4
            CUR["band_ceiling"] = units * LI._MAX_UNIT_RENT
            CUR["over_band"] = g > CUR["band_ceiling"]
            # F-B4: is the value present in the text only as $NNNk / $NNNM?
            import re
            text = listing.marketing_description or ""
            km = re.findall(r"\$\s?([0-9][\d.,]*)\s?([kKmM])\b", text)
            expanded = set()
            for val, suf in km:
                try:
                    expanded.add(round(float(val.replace(",", "")) * (1000 if suf in "kK" else 1_000_000)))
                except ValueError:
                    pass
            CUR["km_tokens_in_text"] = sorted(expanded)
            CUR["km_would_rescue"] = bool(expanded & {round(g), round(g * 12)})
            v.update(band_ceiling=CUR["band_ceiling"], over_band=CUR["over_band"],
                     km_would_rescue=CUR["km_would_rescue"])
        return out

    LI._try_llm_extract, LI._validate_facts = t_llm, t_val

    # ---- income: tiers 2-4 (the deterministic ladder) ----------------------
    # Each tier's ATTEMPT and OUTCOME, not just the winner. This is what lets the
    # ledger say a market median is a fallback even in arm A, where no LLM ever ran.
    _regex, _mix, _fmr, _mkt = (LI._from_regex, LI._parse_unit_mix,
                                LI._from_unit_mix_fmr, LI._from_market)

    def t_regex(text, listing):
        out = _regex(text, listing)
        CUR["tier2"] = {"attempted": bool((text or "").strip()), "produced": out is not None,
                        "gross": getattr(out, "gross_monthly_rent", None),
                        "confidence": getattr(out, "confidence", None)}
        return out

    def t_mix(text):
        out = _mix(text)
        CUR.setdefault("tier3", {})["mix_units"] = len(out or [])
        return out

    def t_fmr(mix, listing):
        out = _fmr(mix, listing)
        CUR.setdefault("tier3", {}).update(
            attempted=True, produced=out is not None,
            gross=getattr(out, "gross_monthly_rent", None))
        return out

    def t_market(market, listing, *, mix, mismatch):
        out = _mkt(market, listing, mix=mix, mismatch=mismatch)
        CUR["tier4"] = {"attempted": True,
                        "market_name": getattr(market, "market_name", None),
                        "rent_median": getattr(market, "rent_median", None),
                        "is_approximate": getattr(market, "is_approximate", None),
                        "produced": out is not None,
                        "gross": getattr(out, "gross_monthly_rent", None),
                        "method": getattr(out, "method", None)}
        return out

    LI._from_regex, LI._parse_unit_mix = t_regex, t_mix
    LI._from_unit_mix_fmr, LI._from_market = t_fmr, t_market

    _resolve = LI.resolve_income

    def t_resolve(listing, settings, **k):
        # _process_listing is a closure inside value_route_pass and cannot be
        # patched, so identity is captured here -- resolve_income runs once per
        # listing and therefore is one of the three OPENING seams.
        _boundary(_asset_of(listing))
        CUR["units"] = getattr(listing, "units", None)
        CUR["ask"] = getattr(listing, "asking_price", None)
        CUR["has_description"] = bool(getattr(listing, "marketing_description", None))
        # Seed every tier as NOT attempted, so a tier whose wrapper never fires is
        # recorded as "not reached" rather than missing.
        CUR.setdefault("llm_transport", {"attempted": False, "served": False, "error": None})
        CUR["tier2"] = {"attempted": False, "produced": False, "gross": None}
        CUR["tier3"] = {"mix_units": 0, "attempted": False, "produced": False, "gross": None}
        CUR["tier4"] = {"attempted": False, "produced": False, "gross": None}
        t0 = time.time()
        sig = _resolve(listing, settings, **k)
        # Tier-3 coherence mirrors resolve_income's own gate (mix parsed AND its unit
        # count agrees with the listing's), so "unit_mix_not_coherent" is exact.
        t3 = CUR["tier3"]
        units = CUR.get("units")
        t3["coherent"] = bool(t3.get("mix_units")) and (units is None or t3["mix_units"] == units)
        CUR["income_method"] = getattr(sig, "method", None)
        CUR["income_source"] = getattr(sig, "source", None)
        CUR["income_gross"] = getattr(sig, "gross_monthly_rent", None)
        CUR["income_conf"] = getattr(sig, "confidence", None)
        CUR["income_ms"] = round((time.time() - t0) * 1000)
        return sig

    LI.resolve_income = t_resolve

    # ---- arv --------------------------------------------------------------
    _arv = VR.compute_mf_arv

    def t_arv(subject, comps, params, *a, **k):
        _boundary(_asset_of(subject))
        t0 = time.time()
        out = _arv(subject, comps, params, *a, **k)
        CUR["arv_comps_in"] = len(comps or [])
        CUR["arv_comp_ids_sample"] = [getattr(c, "property_record_id", None)
                                      for c in (comps or [])[:5]]
        val = getattr(getattr(out, "arv", None), "value", None) if out else None
        prov = getattr(getattr(out, "arv", None), "provenance", None) if out else None
        source = getattr(prov, "source", None)
        conf = getattr(prov, "confidence", None)
        CUR["arv_value"] = val
        CUR["arv_confidence"] = conf
        CUR["arv_source"] = source
        comp_set = getattr(out, "comp_set", []) or [] if out else []
        CUR["arv_comp_set_len"] = len(comp_set)
        CUR["arv_comp_set_excluded"] = sum(1 for c in comp_set if getattr(c, "excluded", False))
        # The x0.55 no-provenance haircut: read the FACTOR off the params that were
        # actually used, and reconstruct the pre-haircut confidence, so the ledger can
        # say what the confidence would have been without F-B8.
        applied = ";no_flip_package_signal" in (source or "")
        factor = getattr(getattr(params, "type1", None), "no_provenance_confidence_discount", None)
        CUR["arv_haircut"] = {
            "applied": applied, "factor": factor,
            "pre_haircut_confidence": (round(conf / factor, 3)
                                       if applied and conf and factor else None),
        }
        CUR["arv_ms"] = round((time.time() - t0) * 1000)
        return out

    VR.compute_mf_arv = t_arv

    # ---- linkage (the third OPENING seam: everything below is nested in it) -
    _link = CL.link_listing

    def t_link(session, listing, **k):
        _boundary(_asset_of(listing))
        CUR["link_inputs"] = {"arv": k.get("arv"), "arv_confidence": k.get("arv_confidence"),
                              "rent_estimate": k.get("rent_estimate"),
                              "rent_confidence": k.get("rent_confidence"),
                              "rent_source": k.get("rent_source"),
                              "disclosed_annual_taxes": k.get("disclosed_annual_taxes"),
                              "disclosed_tax_source": k.get("disclosed_tax_source")}
        res = _link(session, listing, **k)
        CUR["link"] = {"property_id": getattr(res, "property_id", None),
                       "deal_id": getattr(res, "deal_id", None),
                       "qualified": getattr(res, "qualified", None),
                       "lifecycle_stage": getattr(res, "lifecycle_stage", None),
                       "deduped": getattr(res, "deduped_onto_existing", None),
                       "reentered": getattr(res, "reentered", None)}
        return res

    CL.link_listing = t_link

    # ---- routing: condition tier + the rehab input + the offer -------------
    _route = WR.route

    def t_route(prop, valuation, mortgage, condition, params, **k):
        _inner(_asset_of(prop))
        CUR["condition"] = {
            "tier": getattr(getattr(condition, "tier", None), "value", None),
            "confidence": getattr(condition, "confidence", None),
            "source": getattr(condition, "source", None),
            "rationale": (getattr(condition, "rationale", "") or "")[:140],
            # The discriminator: did a stored signal exist, or did the router mint its
            # hardcoded UNKNOWN@0.2 constant? Same tier value, entirely different producer.
            "from_property": getattr(prop, "condition_signal", None) is not None,
        }
        reh = getattr(valuation, "rehab_estimate", None)
        rprov = getattr(reh, "provenance", None)
        CUR["rehab_in"] = {"present": reh is not None, "cost": getattr(reh, "cost", None),
                           "source": getattr(rprov, "source", None),
                           "confidence": getattr(rprov, "confidence", None),
                           "sqft_known": bool(getattr(prop, "sqft", None))}
        deal = _route(prop, valuation, mortgage, condition, params, **k)
        terms = getattr(deal, "terms", None)
        arv_in = getattr(getattr(valuation, "arv", None), "value", None)
        rent_in = getattr(getattr(valuation, "rent_estimate", None), "monthly_rent", None)
        CUR["route"] = {
            "deal_type": getattr(getattr(deal, "deal_type", None), "value", None),
            "channel": getattr(getattr(deal, "channel", None), "value", None),
            "subtype": getattr(getattr(terms, "subtype", None), "value", None),
            "offer_price": getattr(terms, "offer_price", None),
            "offer_pct_of_list": getattr(terms, "offer_pct_of_list", None),
            "assignment_fee": getattr(terms, "assignment_fee", None),
            "offerable": getattr(terms, "offerable", True),
            "offerable_reasons": list(getattr(terms, "offerable_reasons", ()) or ()),
            "list_price": k.get("list_price"),
            "arv_in": arv_in, "rent_in": rent_in, "rehab_in": getattr(reh, "cost", None),
            "mortgage_known": k.get("mortgage_known"),
            "failed_rules": [f"{s.rule}: {(s.detail or '')[:110]}"
                             for s in (getattr(deal, "rationale_trace", ()) or ())
                             if not getattr(s, "passed", True)],
        }
        return deal

    WR.route = t_route

    # ---- rehab -------------------------------------------------------------
    # Patched at BOTH bindings: recompute imports the name at module load, so
    # patching only the engine would leave the caller pointing at the original.
    _reh_engine = VE.estimate_rehab

    def t_rehab(subject, condition_signal, params, **k):
        out = _reh_engine(subject, condition_signal, params, **k)
        _inner(_asset_of(subject))
        CUR["rehab_computed"] = {"cost": getattr(out, "cost", None),
                                 "source": getattr(getattr(out, "provenance", None), "source", None)}
        return out

    VE.estimate_rehab = RC.estimate_rehab = t_rehab

    # ---- gate (captures holds/overridden, which apply_gate drops) ----------
    _eval = GA.evaluate

    def t_eval(*a, **k):
        res = _eval(*a, **k)
        _inner()
        CUR["gate_decision"] = str(getattr(res, "decision", None))
        CUR["gate_reasons"] = list(getattr(res, "reasons", []) or [])
        CUR["gate_holds"] = list(getattr(res, "holds", []) or [])
        CUR["gate_overridden"] = list(getattr(res, "overridden", []) or [])
        return res

    GA.evaluate = t_eval

    # apply_gate adds its OWN holds after evaluate returns (no contact / no ARV / area
    # costs / generation failure) and returns only a DealStatus, so the added reasons
    # are recoverable only from the guardrail audit row it writes. Filtered to
    # event_type=guardrail so this stays a gate seam, not a global audit tap.
    _ag = WG.apply_gate
    # Attribution by CALL SCOPE, not by matching the audit row's actor/text. The lane
    # writes its OWN event_type=guardrail row from _hold_for_mf_review, and letting
    # that populate gate_apply made the ledger report `gate_decision = hold, produced
    # by guardrails.gate.evaluate` on a listing where evaluate returned nothing --
    # a confidently wrong record. Only rows written INSIDE apply_gate are apply_gate's.
    in_apply_gate = [0]

    def t_apply(*a, **k):
        in_apply_gate[0] += 1
        try:
            st = _ag(*a, **k)
        finally:
            in_apply_gate[0] -= 1
        CUR.setdefault("gate_apply", {})["status"] = getattr(st, "value", str(st))
        return st

    WG.apply_gate = t_apply

    _aal = REPO.append_audit_log

    def t_aal(session, *, audit_id, values, **k):
        if (values or {}).get("event_type") == "guardrail":
            d = (values or {}).get("detail") or {}
            entry = {"actor": values.get("actor"), "decision": d.get("decision"),
                     "status": d.get("status"), "reasons": list(d.get("reasons") or []),
                     "from_apply_gate": bool(in_apply_gate[0])}
            # Every guardrail row is kept as evidence, whoever wrote it...
            CUR.setdefault("guardrail_audit", []).append(entry)
            # ...but only apply_gate's own row supplies the holds it added after
            # evaluate returned (they are recoverable nowhere else -- apply_gate
            # returns a bare DealStatus).
            if entry["from_apply_gate"]:
                ga = CUR.setdefault("gate_apply", {})
                ga.setdefault("decision", entry["decision"])
                ga.setdefault("reasons", entry["reasons"])
        return _aal(session, audit_id=audit_id, values=values, **k)

    REPO.append_audit_log = t_aal

    # The lane's own terminal move for an unqualified MF card: it overrides the
    # lifecycle stage link_listing returned, so the ledger records it as a fallback.
    _mf = VR._hold_for_mf_review

    def t_mf(session, *, deal_id):
        out = _mf(session, deal_id=deal_id)
        _inner()
        CUR["mf_review_hold"] = bool(out)
        if out:
            CUR["mf_review_reason"] = VR.MF_REVIEW_HOLD_REASON
        return out

    VR._hold_for_mf_review = t_mf


def classify(rec: dict) -> list[str]:
    """Attach stable defect ids. Detection mirrors defects.py's `detect` text."""
    d = []
    if rec.get("validator_accepted") is False and rec.get("llm_gross"):
        if rec.get("over_band"):
            d.append("F-B1")
        if rec.get("km_would_rescue"):
            d.append("F-B4")
    if rec.get("arv_value") is not None:
        if not rec.get("arv_comp_set_len"):
            d.append("F-B2")
        if (rec.get("arv_confidence") or 1) < 0.35:
            d.append("F-B3")
        if ";no_flip_package_signal" in (rec.get("arv_source") or ""):
            d.append("F-B8")
    if rec.get("arv_value") is None and (rec.get("arv_comps_in") or 0) > 0:
        d.append("F-B5")
    if rec.get("income_method") == "market_median":
        d.append("F-B6")
    if rec.get("income_method") in (None, "none"):
        d.append("F-B7")
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--out", default=None)
    # Walk PAST listings a previous pass already handled. skip_asset_ids is the wrong
    # lever for this: a poison-skip still increments stats.processed, which is what
    # max_deals budgets, so a skip list just burns the budget. The keyset cursor is
    # the right one -- it filters in SQL, before any per-listing work.
    ap.add_argument("--after-key", default=None, metavar="ISO_TS,ASSET_ID",
                    help="resume the DESC keyset walk strictly after this boundary")
    ap.add_argument("--after-last-linked", action="store_true",
                    help="compute --after-key as the OLDEST already-linked listing, i.e. "
                         "start at the first listing this lane has never routed")
    args = ap.parse_args()

    # Both cassettes install BEFORE the trace, so the trace observes what they
    # served -- which is what "post-cassette" means in the summaries below.
    cas = cassette_from_env()
    if cas is not None:
        cas.install()
        print(f"cassette: mode={cas.mode} entries={len(cas.entries)} path={cas.path}")
    aicas = ai_cassette_from_env()
    if aicas is not None and os.environ.get("CREXI_BASELINE_ARM") == "A":
        # Arm A is DEFINED as "no transport can serve the extract". A cassette hit
        # would fabricate a completion that arm A can never produce, silently turning
        # it into arm B and voiding the whole A/B comparison -- and the prompts are
        # identical across arms, so it WOULD hit. Refuse rather than measure a lie.
        raise SystemExit(
            "trace: CREXI_AI_CASSETTE is set but the arm is A. Arm A must have no LLM "
            "transport at all; serving one from a cassette makes it arm B. Unset "
            "CREXI_AI_CASSETTE for arm A."
        )
    if aicas is not None:
        aicas.install()
        print(f"ai-cassette: mode={aicas.mode} entries={len(aicas.entries)} path={aicas.path}")
    install()
    CONSTS = runtime_consts()

    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    from app.config.settings import Settings
    from app.db.models import CrexiListingORM
    from app.persistence.crexi_listing_store import listing_from_row
    from app.providers.crexi.client import CrexiClient
    import app.services.listing_income as LI

    s = Settings()
    eng = create_engine(s.database_url, future=True)
    with Session(eng) as sess:
        rows = sess.execute(select(CrexiListingORM).order_by(CrexiListingORM.asset_id)
                            .limit(args.limit)).scalars().all()
        available = len(rows)

    after_key = None
    if args.after_last_linked:
        from sqlalchemy import text as _text
        with Session(eng) as sess:
            row = sess.execute(_text(
                "select l.harvested_at, l.asset_id from crexi_listings l "
                "where exists (select 1 from property p where p.id = 'crexi:' || l.asset_id) "
                "order by l.harvested_at asc, l.asset_id asc limit 1")).first()
        if row is None:
            raise SystemExit("trace: --after-last-linked but no listing is linked yet")
        after_key = (row[0], row[1])
    elif args.after_key:
        from datetime import datetime as _dt
        ts, aid = args.after_key.split(",", 1)
        after_key = (_dt.fromisoformat(ts.strip()), aid.strip())
    if after_key is not None:
        print(f"after_key: resuming strictly after {after_key[0].isoformat()},{after_key[1]}")

    _ = available  # candidate pool size; value_route_pass selects its own slice
    client = CrexiClient(token=s.crexi_token, base_url=s.crexi_base_url,
                         requests_per_second=s.crexi_requests_per_second,
                         max_retries=s.crexi_max_retries)

    arm = os.environ.get("CREXI_BASELINE_ARM", "?")
    out = args.out or os.path.join(os.environ["CREXI_BASELINE_ROOT"], "runs", f"trace_arm{arm}.jsonl")
    git = subprocess.run(["git", "-C", os.environ["WHOLESALING_REPO"], "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True).stdout.strip()

    # Drive the REAL pass (not just resolve_income) so the arv/linkage/routing/gate
    # seams actually fire. We call value_route_pass directly rather than the CLI
    # because run_value_route hardcodes `started = datetime.now(UTC)` and we need a
    # pinned clock for reproducibility.
    from datetime import UTC, datetime
    from sqlalchemy.orm import Session as _Session
    from app.services.crexi_value_route import value_route_pass
    from app.services.scrape_profile_service import get_effective_scrape_config
    from app.config.parameters import DEFAULT_PARAMETERS

    pinned_now = datetime.fromisoformat(os.environ.get("CREXI_PINNED_NOW", "")) \
        if os.environ.get("CREXI_PINNED_NOW") else datetime.now(UTC)

    records = []
    with open(out, "w") as fh:
        fh.write(json.dumps({"_manifest": {
            "arm": arm, "wholesaling_git": git, "n_requested": args.limit,
            "pinned_now": pinned_now.isoformat(),
            "after_key": (list(after_key) if after_key else None),
            "crexi_cassette": (cas.mode if cas else None),
            "ai_cassette": (aicas.mode if aicas else None),
            "seams": PATCHES, "defect_classes": sorted(DEFECTS),
            "consts": CONSTS}}, default=str) + "\n")
        with _Session(eng) as sess:
            cfg = get_effective_scrape_config(sess)

        def _flush() -> None:
            if not CUR.get("asset_id"):
                return
            CUR.setdefault("terminal_stage",
                           "gate" if CUR.get("gate_decision") else
                           ("arv" if CUR.get("arv_value") is not None else "income"))
            rec = dict(CUR)
            rec["defects"] = classify(rec)
            # Derive the per-value provenance ledger from the captured evidence. Done
            # HERE (at the boundary) rather than inside each seam so it sees the whole
            # listing -- a fallback is only knowable once you know which tier won.
            rec["provenance"] = build_ledger(rec, CONSTS)
            records.append(rec)
            fh.write(json.dumps(rec, default=str) + "\n")
            fh.flush()
            CUR.clear()

        globals()["FLUSH"] = _flush

        lines: list[str] = []
        t0 = time.time()
        with _Session(eng) as sess:
            stats = value_route_pass(
                sess, client, cfg, DEFAULT_PARAMETERS, s,
                apply=True, all_rows=True, overlap_minutes=120,
                max_deals=args.limit, states=("FL",), keep_raw=True, now=pinned_now,
                chunk_limit=None, after_key=after_key, stamp_cursor=False,
                listing_timeout_s=None, skip_asset_ids=frozenset(),
                parcel_registry=None, reverse_geocoder=None,
                log=lines.append,
            )
        _flush()  # the final listing has no successor to trigger the boundary
        wall = round(time.time() - t0)
        print(f"pass: candidates={stats.candidates} qualified={stats.qualified} "
              f"processed={stats.processed} held={getattr(stats,'held_for_review',None)} "
              f"comps_new={getattr(stats,'comps_new',None)} wall={wall}s")
        # attach the lane's own per-listing summary lines to their records
        for ln in lines:
            if "| ask " in ln:
                addr = ln.strip().split("|")[0].strip()
                for r in records:
                    if r.get("summary_line") is None and addr and addr in ln:
                        r["summary_line"] = ln.strip()
                        break

    # --- external-api summary: the replayability answer ---------------------
    import collections as _c
    by_path = _c.Counter()
    for e in HTTP:
        p = e["path"]
        # collapse ids so /properties/<hash> groups together. Keyed on the SHAPE of an
        # id (all digits, or a long hex hash) -- a plain length test ate real path
        # segments like "universal-search" and printed /<id>/v2/search.
        import re as _re
        parts = ["<id>" if (seg.isdigit() or _re.fullmatch(r"[0-9a-f]{12,}", seg)) else seg
                 for seg in p.split("/")]
        by_path["/".join(parts)] += 1
    http_path = os.path.join(os.environ["CREXI_BASELINE_ROOT"], "runs",
                             f"http_arm{arm}.jsonl")
    with open(http_path, "w") as hf:
        for e in HTTP:
            hf.write(json.dumps(e) + "\n")
    if cas is not None:
        sm = cas.summary()
        print(f"\ncassette: hits={sm['hits']} misses={sm['misses']} recorded={sm['recorded']} "
              f"entries={sm['entries']}")
    print(f"\nOUTBOUND CREXI CALLS (post-cassette): {len(HTTP)}  -> {http_path}")
    for k, v in by_path.most_common():
        print(f"   {v:4d}  {k}")

    # --- llm summary: the arm A / arm B discriminator -----------------------
    ai_path = os.path.join(os.environ["CREXI_BASELINE_ROOT"], "runs", f"ai_arm{arm}.jsonl")
    with open(ai_path, "w") as af:
        for e in AI:
            af.write(json.dumps(e) + "\n")
    served = _c.Counter(f"{e['label']}:{e['provider']}/{e['model']}" for e in AI if not e["error"])
    failed = _c.Counter(f"{e['label']}:{(e['error'] or '').split(':')[0]}" for e in AI if e["error"])
    if aicas is not None:
        sm = aicas.summary()
        print(f"\nai-cassette: hits={sm['hits']} misses={sm['misses']} "
              f"recorded={sm['recorded']} entries={sm['entries']}")
    print(f"\nLLM COMPLETIONS: {len(AI)}  -> {ai_path}")
    for k, v in served.most_common():
        print(f"   {v:4d}  served   {k}")
    for k, v in failed.most_common():
        print(f"   {v:4d}  FAILED   {k}")

    summ = summarize(records)
    print(f"\n=== trace arm={arm}  n={summ['n']}  -> {out} ===")
    print("defects by class:")
    for k, v in sorted(summ["by_defect"].items(), key=lambda kv: -kv[1]):
        print(f"   {k}  {v:3d}  {DEFECTS[k]['stage']:8s} {DEFECTS[k]['title']}")
    print(f"\nby stage: {summ['by_stage']}")

    mismatched = [r["asset_id"] for r in records if r.get("seam_id_mismatch")]
    if mismatched:
        print(f"\n!! seam id mismatch on {mismatched} -- a nested seam saw a different "
              f"asset than the listing in flight; attribution is suspect")

    from provenance import aggregate, render
    print()
    print(render(aggregate([r["provenance"] for r in records])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
