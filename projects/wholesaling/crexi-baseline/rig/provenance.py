"""Provenance ledger for the Crexi ingest -> value-route lane.

The per-listing trace records VALUES. It can say the rent was $5,382 via
``market_median`` -- but not, in a structured way, that this value is a FALLBACK
that exists only because an LLM extraction of $46,000 was REJECTED by a
deterministic validator. That distinction is the whole point of the baseline: we
are establishing what the LLM contributes versus what the script does, and in a
value-only trace the two are indistinguishable.

This module owns three things:

  1. :class:`PValue` -- the per-value record (field / value / producer /
     producer_detail / inputs / validated_by / fallback_from / confidence).
  2. :func:`build_ledger` -- DERIVES those records from one captured trace
     record. Derivation lives here, not in trace.py, so trace.py stays a pure
     CAPTURE layer: it wraps seams and writes evidence, every judgement about
     "what produced this" is made in one place, and the ledger can be re-derived
     from a frozen trace after the fact (a taxonomy fix does not require a re-run).
  3. :func:`aggregate` / :func:`render` + a CLI -- the deliverable table: per
     sellable field, the fraction of values produced by deterministic code, an
     LLM, an external API or a default constant, and how many were fallbacks
     from a rejected higher-tier producer.

    ./rig/run.sh $CREXI_BASELINE_ROOT/rig/provenance.py runs/trace_armB.jsonl

TAXONOMY NOTE (deliberate, documented because it is the one debatable call):
``producer`` names the code that COMPUTED AND EMITTED the value that reached the
DB, not the ultimate origin of every number that fed it. So a tier-4 rent is
``deterministic`` (``listing_income._from_market`` multiplied a median by the unit
count and clamped it to the HUD FMR ceiling) even though the median itself came
off a Crexi endpoint. The external dependency is NOT lost: it is recorded in
``inputs`` with its own ``producer``/``endpoint``, and :func:`aggregate` reports
an ``ext-in`` column counting values whose dominant input came from an external
API. ``producer=external_api`` is reserved for a value that reached the lead
essentially unmodified from an endpoint.
"""
from __future__ import annotations

import argparse
import collections
import dataclasses
import json
import os
import sys
from typing import Any

# --- the producer vocabulary. Fixed set: an unknown value raises, so a new
# producer is a deliberate addition rather than a silent new column. -----------
DETERMINISTIC = "deterministic"
LLM = "llm"
EXTERNAL_API = "external_api"
DEFAULT_CONSTANT = "default_constant"
HUMAN_ATTESTED = "human_attested"
ABSENT = "absent"
PRODUCERS = (DETERMINISTIC, LLM, EXTERNAL_API, DEFAULT_CONSTANT, HUMAN_ATTESTED, ABSENT)

#: Order the aggregate prints fields in -- the order a lead is built, so the table
#: reads as the pipeline reads.
FIELD_ORDER = (
    "rent_estimate",
    "arv",
    "arv_confidence",
    "rehab_estimate",
    "condition_tier",
    "offer_price",
    "gate_decision",
    "gate_hold",
    "lifecycle_stage",
)


@dataclasses.dataclass
class PValue:
    """One value that would appear on a sellable lead, plus what produced it."""

    field: str
    value: Any
    producer: str
    producer_detail: str
    inputs: dict = dataclasses.field(default_factory=dict)
    validated_by: dict | None = None
    #: REQUIRED when this value is a fallback: what was attempted first and why it
    #: lost. This is the field that makes F-B1/F-B4 visible without prose.
    fallback_from: dict | None = None
    confidence: float | None = None
    #: True when a higher-trust producer was attempted and lost. Set explicitly (not
    #: inferred from ``fallback_from``) so the invariant below can be enforced.
    is_fallback: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.producer not in PRODUCERS:
            raise ValueError(f"provenance: unknown producer {self.producer!r} for {self.field!r}")
        if self.is_fallback and not self.fallback_from:
            # Fail loudly: a fallback with no record of what it fell back FROM is
            # exactly the un-auditable state this ledger exists to remove.
            raise ValueError(f"provenance: {self.field!r} is a fallback but names no fallback_from")

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Derivation: one captured trace record -> its provenance records
# ---------------------------------------------------------------------------

#: The rent ladder's four tiers, most-trustworthy first (listing_income module
#: docstring). Keyed by the ``method`` the resolved IncomeSignal carries.
_RENT_TIER = {
    "llm_extract": 1,
    "regex_extract": 2,
    "unit_mix_market": 3,
    "market_median": 4,
    "market_median_fmr_clamped": 4,
}


def _rent(rec: dict, c: dict) -> list[PValue]:
    """``rent_estimate`` + which of the 4 income-ladder tiers produced it."""
    method = rec.get("income_method")
    gross = rec.get("income_gross")
    tier = _RENT_TIER.get(method or "")
    llm_t = rec.get("llm_transport") or {}
    val = rec.get("validator") or {}
    t2, t3, t4 = rec.get("tier2") or {}, rec.get("tier3") or {}, rec.get("tier4") or {}

    # The ladder is the EVIDENCE fallback_from is derived from: every tier above the
    # winner, whether it was attempted, and what happened to it.
    ladder = [
        {"tier": 1, "producer": LLM, "attempted": bool(llm_t.get("attempted")),
         "served": bool(llm_t.get("served")), "candidate": rec.get("llm_gross"),
         "outcome": _llm_outcome(llm_t, val), "detail": val.get("reject_detail")},
        {"tier": 2, "producer": DETERMINISTIC, "attempted": bool(t2.get("attempted")),
         "candidate": t2.get("gross"),
         "outcome": "produced" if t2.get("produced") else "no_explicit_income_claim"},
        {"tier": 3, "producer": DETERMINISTIC, "attempted": bool(t3.get("attempted")),
         "candidate": t3.get("gross"),
         "outcome": ("produced" if t3.get("produced")
                     else ("no_fmr_coverage" if t3.get("attempted")
                           else f"unit_mix_not_coherent(parsed={t3.get('mix_units')})"))},
        {"tier": 4, "producer": DETERMINISTIC, "attempted": bool(t4.get("attempted")),
         "candidate": t4.get("gross"),
         "outcome": ("produced" if t4.get("produced")
                     else ("no_market_stats" if t4.get("attempted") else "not_reached"))},
    ]

    lost = _highest_loss(ladder, tier)
    inputs: dict[str, Any] = {
        "asset_id": rec.get("asset_id"),
        "units": rec.get("units"),
        "has_description": rec.get("has_description"),
        "ladder": ladder,
    }

    if tier is None or gross is None:
        return [PValue(
            field="rent_estimate", value=None, producer=ABSENT,
            producer_detail="listing_income.resolve_income -> IncomeSignal(method='none')",
            inputs=inputs, is_fallback=bool(lost), fallback_from=lost,
            notes="every tier declined; the card holds rather than inventing a rent",
        )]

    if tier == 1:
        producer, detail = LLM, _llm_detail(llm_t)
        validated = {"check": "listing_income._validate_facts", "outcome": "accepted",
                     "guards": ["confidence_floor", "per_unit_band", "appears_in_source"]}
    elif tier == 2:
        producer = DETERMINISTIC
        detail = "listing_income._from_regex (explicit income claim stated in the description)"
        validated = {"check": "listing_income._from_regex/plausibility_bounds",
                     "outcome": "accepted"}
    elif tier == 3:
        producer = DETERMINISTIC
        detail = ("listing_income._from_unit_mix_fmr (HUD FMR schedule x "
                  f"rent_fmr_haircut_pct={c.get('rent_fmr_haircut_pct')})")
        validated = {"check": "listing_income._from_unit_mix_fmr/per_unit_band",
                     "outcome": "accepted"}
        inputs["fmr_haircut_pct"] = c.get("rent_fmr_haircut_pct")
    else:
        # Tier 4. See the module TAXONOMY NOTE: the emitting code is deterministic;
        # the median it multiplies is an external-API number, recorded as an input.
        producer = DETERMINISTIC
        detail = "listing_income._from_market (market median x units, FMR-clamped)"
        validated = {"check": "listing_income._from_market/fmr_clamp+per_unit_band",
                     "outcome": "clamped" if method == "market_median_fmr_clamped" else "accepted"}
        inputs["market_median"] = {
            "producer": EXTERNAL_API,
            "endpoint": "GET /universal-search/rental-markets/stats",
            "market_name": t4.get("market_name"),
            "rent_median": t4.get("rent_median"),
            "is_approximate": t4.get("is_approximate"),
        }

    return [PValue(
        field="rent_estimate", value=gross, producer=producer, producer_detail=detail,
        inputs=inputs, validated_by=validated, confidence=rec.get("income_conf"),
        is_fallback=bool(lost), fallback_from=lost,
        notes=f"income ladder tier {tier} ({method}); source={rec.get('income_source')}",
    )]


def _llm_outcome(llm_t: dict, val: dict) -> str:
    """One string for what happened to the LLM tier -- the arm-A/arm-B discriminator."""
    if not llm_t.get("attempted"):
        return "not_attempted(no_description)"
    if not llm_t.get("served"):
        # Arm A lands here: every transport is structurally disabled, so the tier
        # cannot serve at all. Arm B lands here only on a real transport failure.
        return f"transport_unavailable({str(llm_t.get('error') or 'no_transport')[:70]})"
    if val.get("accepted"):
        return "accepted"
    # Names the rejecting CHECK, which is what fallback_from must carry: an
    # `_validate_facts/band` is self-explaining where "rejected" is not.
    return f"_validate_facts/{val.get('reject_reason') or 'unknown'}"


def _llm_detail(llm_t: dict) -> str:
    prov, model = llm_t.get("provider") or "?", llm_t.get("model") or "?"
    return f"{prov}/{model} prompt=extract@{llm_t.get('prompt_sha12') or '?'}"


def _highest_loss(ladder: list[dict], winning_tier: int | None) -> dict | None:
    """The highest-trust tier that was ATTEMPTED and did not win -> ``fallback_from``.

    Prefers a tier that actually produced a candidate value (the informative case:
    "an LLM said $46,000 and a validator threw it out") over one that merely
    declined, which is why the two passes below are ordered that way.
    """
    losers = [t for t in ladder if t["attempted"] and (winning_tier is None or t["tier"] < winning_tier)]
    if not losers:
        return None
    with_value = [t for t in losers if t.get("candidate") is not None]
    pick = with_value[0] if with_value else losers[0]
    out = {"producer": pick["producer"], "tier": pick["tier"],
           "value": pick.get("candidate"), "rejected_by": pick["outcome"]}
    if pick.get("detail"):
        out["detail"] = pick["detail"]
    return out


def _arv(rec: dict, c: dict) -> list[PValue]:
    """``arv`` + ``arv_confidence`` (incl. whether the x0.55 no-provenance haircut applied)."""
    out: list[PValue] = []
    value = rec.get("arv_value")
    src = rec.get("arv_source") or ""
    hc = rec.get("arv_haircut") or {}
    inputs = {
        "comps_fetched": rec.get("arv_comps_in"),
        "comp_set_len": rec.get("arv_comp_set_len"),
        "surviving_comps": _n_from_source(src),
        "comp_ids_sample": rec.get("arv_comp_ids_sample"),
        "recency_months": c.get("arv_recency_months"),
    }

    if value is None:
        out.append(PValue(
            field="arv", value=None, producer=ABSENT,
            producer_detail=("providers.crexi.arv.compute_mf_arv -> Valuation(arv=None) "
                             "(no surviving comp geometry / no $/sqft pairs)"),
            inputs=inputs,
            notes="comps were fetched but no per-property ARV was emitted (F-B5)"
            if (rec.get("arv_comps_in") or 0) > 0 else None,
        ))
        out.append(PValue(
            field="arv_confidence", value=None, producer=ABSENT,
            producer_detail="no ARV -> no confidence", inputs={},
        ))
        return out

    if src.startswith("assessed_fallback"):
        out.append(PValue(
            field="arv", value=value, producer=DEFAULT_CONSTANT,
            producer_detail=("valuation.engine._assessed_fallback_arv "
                             f"(assessed x opendata.assessed_to_market_multiple)"),
            inputs=inputs, confidence=rec.get("arv_confidence"),
            is_fallback=True,
            fallback_from={"producer": DETERMINISTIC, "tier": 1, "value": None,
                           "rejected_by": "comps_thin(no usable sold-comp ARV)"},
            notes=src,
        ))
    else:
        out.append(PValue(
            field="arv", value=value, producer=DETERMINISTIC,
            producer_detail=("providers.crexi.arv.compute_mf_arv -> "
                             "valuation.engine.compute_arv (weighted comp central tendency)"),
            inputs=inputs, confidence=rec.get("arv_confidence"),
            validated_by={"check": "valuation.engine._evaluate_comp + _flag_price_outliers",
                          "outcome": f"{_n_from_source(src)} comps survived the §1.5 screens"},
            notes=src,
        ))

    applied = bool(hc.get("applied"))
    floor = c.get("arv_confidence_floor", 0.35)
    conf = rec.get("arv_confidence")
    out.append(PValue(
        field="arv_confidence", value=conf,
        # DETERMINISTIC even when the haircut fires: the number still varies with comp
        # count/spread/recency, so calling it a constant would misstate the mix. The
        # constant's effect is carried by producer_detail + fallback_from + the
        # `fallback` column, which is where "a config factor moved this" belongs.
        producer=DETERMINISTIC,
        producer_detail=(
            f"type1.no_provenance_confidence_discount={hc.get('factor')} applied to "
            "valuation.engine._arv_confidence(count, spread, recency)"
            if applied else "valuation.engine._arv_confidence(count, spread, recency)"
        ),
        inputs={"pre_haircut_confidence": hc.get("pre_haircut_confidence"),
                "surviving_comps": _n_from_source(src),
                "no_provenance_haircut_applied": applied,
                "haircut_factor": hc.get("factor")},
        validated_by={"check": f"credibility_floor({floor})",
                      "outcome": "below_floor" if (conf or 1) < floor else "above_floor"},
        is_fallback=applied,
        fallback_from=({"producer": DETERMINISTIC, "tier": 1,
                        "value": hc.get("pre_haircut_confidence"),
                        "rejected_by": ("no comp in the set carries a sale-type/owner-occupant "
                                        "signal -> _comp_set_has_sale_type_provenance false (F-B8)")}
                       if applied else None),
        notes=("the haircut applies to 100% of Crexi ARVs because sale_event_name never reaches "
               "Comp.exclusion_reason (F-B8)") if applied else None,
    ))
    return out


def _n_from_source(src: str) -> int | None:
    for part in (src or "").split(";"):
        if ":n=" in part:
            try:
                return int(part.split(":n=")[1])
            except ValueError:
                return None
    return None


def _condition(rec: dict, c: dict) -> list[PValue]:
    """``condition_tier`` -- the input the rehab estimate is a multiple of."""
    cond = rec.get("condition")
    if not cond:
        return [PValue(field="condition_tier", value=None, producer=ABSENT,
                       producer_detail="routing.route never ran for this listing", inputs={})]
    if not cond.get("from_property"):
        # The router's own no-information constant: UNKNOWN @ 0.2. Not a measurement.
        return [PValue(
            field="condition_tier", value=cond.get("tier"), producer=DEFAULT_CONSTANT,
            producer_detail=(f"workers.routing.RoutingWorker._route -> ConditionSignal("
                             f"tier={cond.get('tier')}, confidence={cond.get('confidence')}) "
                             "-- the hardcoded no-signal default"),
            inputs={"property.condition_signal": None},
            confidence=cond.get("confidence"),
            notes=cond.get("rationale"),
        )]
    src = (cond.get("source") or "heuristic").lower()
    producer = {"vision": LLM, "human": HUMAN_ATTESTED}.get(src, DETERMINISTIC)
    return [PValue(
        field="condition_tier", value=cond.get("tier"), producer=producer,
        producer_detail=f"property.condition_signal(source={src})",
        inputs={"property.condition_signal": src}, confidence=cond.get("confidence"),
        notes=cond.get("rationale"),
    )]


def _rehab(rec: dict, c: dict) -> list[PValue]:
    """``rehab_estimate`` -- sqft x condition-tier multiplier x market $/sqft."""
    r = rec.get("rehab_in") or {}
    cond = rec.get("condition") or {}
    if not r.get("present"):
        return [PValue(
            field="rehab_estimate", value=None, producer=ABSENT,
            producer_detail=("valuation.rehab_estimate is NULL -- the Crexi lane never writes one "
                             "(crexi_linkage.link_listing seeds arv+rent only; "
                             "recompute._refresh_rehab runs on the RE-gate path, not route_new_property)"),
            inputs={"valuation_row": rec.get("link", {}).get("property_id")},
            notes="router.route sees estimated_rehab=None -> the cash terms are UNPRICEABLE",
        )]
    # Present: the estimate is a heuristic multiple. When the TIER it multiplies is
    # itself the router's default constant, the whole number is constant-derived.
    tier_is_default = not cond.get("from_property")
    return [PValue(
        field="rehab_estimate", value=r.get("cost"),
        producer=DEFAULT_CONSTANT if tier_is_default else DETERMINISTIC,
        producer_detail=("valuation.engine.estimate_rehab (sqft x "
                         "rehab.tier_multipliers[tier] x rehab.market_cost_per_sqft"
                         + (", tier itself the UNKNOWN default constant)" if tier_is_default else ")")),
        inputs={"condition_tier": cond.get("tier"), "sqft_known": r.get("sqft_known"),
                "default_sqft": c.get("rehab_default_sqft"),
                "market_cost_per_sqft": c.get("rehab_market_cost_per_sqft")},
        confidence=r.get("confidence"), notes=r.get("source"),
    )]


def _offer(rec: dict, c: dict) -> list[PValue]:
    """``offer_price`` -- the number a buyer would actually transact on."""
    rt = rec.get("route")
    if not rt:
        return [PValue(field="offer_price", value=None, producer=ABSENT,
                       producer_detail="routing.route never ran for this listing", inputs={})]
    failed = rt.get("failed_rules") or []
    inputs = {"list_price": rt.get("list_price"), "arv_in": rt.get("arv_in"),
              "rent_in": rt.get("rent_in"), "rehab_in": rt.get("rehab_in"),
              "mortgage_known": rt.get("mortgage_known"), "failed_rules": failed}
    if rt.get("offer_price") is None:
        return [PValue(
            field="offer_price", value=None, producer=ABSENT,
            producer_detail=f"routing.router.route -> deal_type={rt.get('deal_type')} (no terms)",
            inputs=inputs,
            notes=(f"{failed[0][:160]} (+{len(failed) - 1} more failed rules)"
                   if failed else None),
        )]
    return [PValue(
        field="offer_price", value=rt.get("offer_price"), producer=DETERMINISTIC,
        producer_detail=f"routing.router.route (subtype={rt.get('subtype')})",
        inputs=inputs, confidence=rt.get("data_quality"),
        validated_by={"check": "CashTerms.offerable (sub-payoff guard)",
                      "outcome": "offerable" if rt.get("offerable", True) else
                                 f"non_offerable{tuple(rt.get('offerable_reasons') or ())}"},
        notes=f"offer_pct_of_list={rt.get('offer_pct_of_list')}",
    )]


#: Hold reasons the gate does NOT author -- each is added by a named check outside
#: guardrails.gate.evaluate, so the ledger can attribute it to the right producer.
_HOLD_OWNERS = (
    ("no reachable contact", "guardrails.apply.NO_CONTACT_HOLD_REASON"),
    ("no arv", "guardrails.apply.NO_ARV_HOLD_REASON"),
    ("area cost", "guardrails.apply.AREA_COSTS_HOLD_REASON"),
    ("mf review", "crexi_value_route.MF_REVIEW_HOLD_REASON"),
    ("multi-family underwriting", "crexi_value_route.MF_REVIEW_HOLD_REASON"),
    ("multifamily underwriting", "crexi_value_route.MF_REVIEW_HOLD_REASON"),
    ("generation incomplete", "guardrails.apply.apply_gate/generation_failure"),
    ("condition", "guardrails.apply.apply_gate/condition_confidence"),
)


def _norm_decision(v: object) -> str | None:
    """``GateDecision.HOLD`` and ``hold`` are the same decision spelled two ways.

    evaluate() returns the enum; the guardrail audit row stores its value. Comparing
    the raw strings marked every gated listing as a fallback from itself.
    """
    return str(v).rsplit(".", 1)[-1].lower() if v is not None else None


def _gate(rec: dict, c: dict) -> list[PValue]:
    """The gate decision and each hold reason, one record per reason."""
    out: list[PValue] = []
    decision = rec.get("gate_decision")
    ga = rec.get("gate_apply") or {}
    ran = decision is not None or bool(ga)
    if not ran:
        # The gate genuinely never fired (the router minted nothing to gate). That is
        # itself a producer fact, not a missing column.
        out.append(PValue(
            field="gate_decision", value=None, producer=ABSENT,
            producer_detail="guardrails.gate.evaluate never ran (no deal reached the guardrail worker)",
            inputs={"deal_id": (rec.get("link") or {}).get("deal_id")},
        ))
    else:
        final = ga.get("decision") or decision
        moved = bool(ga.get("decision") and decision
                     and _norm_decision(ga["decision"]) != _norm_decision(decision))
        out.append(PValue(
            field="gate_decision", value=final, producer=DETERMINISTIC,
            producer_detail="guardrails.gate.evaluate -> guardrails.apply.apply_gate",
            inputs={"gate_reasons": len(rec.get("gate_reasons") or []),
                    "apply_reasons": len(ga.get("reasons") or []),
                    "holds": rec.get("gate_holds"), "overridden": rec.get("gate_overridden"),
                    "final_status": ga.get("status")},
            is_fallback=moved,
            fallback_from=({"producer": DETERMINISTIC, "tier": 1, "value": decision,
                            "rejected_by": "guardrails.apply.apply_gate added a post-evaluate hold"}
                           if moved else None),
        ))

    seen = set(rec.get("gate_reasons") or [])
    reasons = list(rec.get("gate_reasons") or []) + \
              [r for r in (ga.get("reasons") or []) if r not in seen]
    if rec.get("mf_review_hold"):
        reasons.append(rec.get("mf_review_reason") or "Held for MF review.")
    for reason in reasons:
        low = reason.lower()
        owner = next((o for k, o in _HOLD_OWNERS if k in low), "guardrails.gate.evaluate")
        out.append(PValue(
            field="gate_hold", value=reason[:160], producer=DETERMINISTIC,
            producer_detail=owner, inputs={"decision": decision},
        ))
    return out


def _lifecycle(rec: dict, c: dict) -> list[PValue]:
    """The terminal lifecycle stage the listing came to rest at."""
    link = rec.get("link") or {}
    if not link:
        return [PValue(
            field="lifecycle_stage", value=rec.get("terminal_stage"), producer=ABSENT,
            producer_detail="crexi_linkage.link_listing never ran (dry-run pass)",
            inputs={"trace_terminal_stage": rec.get("terminal_stage")},
        )]
    held = bool(rec.get("mf_review_hold"))
    return [PValue(
        field="lifecycle_stage",
        value="guardrail (held: MF review)" if held else link.get("lifecycle_stage"),
        producer=DETERMINISTIC,
        producer_detail=("crexi_value_route._hold_for_mf_review -> repositories.update_deal_status"
                         if held else
                         "recompute.route_new_property -> domain.lifecycle_graph (monotonic advance)"),
        inputs={"property_id": link.get("property_id"), "deal_id": link.get("deal_id"),
                "qualified": link.get("qualified"), "deduped": link.get("deduped")},
        is_fallback=held,
        fallback_from=({"producer": DETERMINISTIC, "tier": 1,
                        "value": link.get("lifecycle_stage"),
                        "rejected_by": "router minted deal_type=none -> parked as an MF review card"}
                       if held else None),
    )]


def build_ledger(rec: dict, consts: dict | None = None) -> list[dict]:
    """Every provenance record for ONE captured listing trace."""
    c = consts or {}
    out: list[PValue] = []
    for fn in (_rent, _arv, _rehab, _condition, _offer, _gate, _lifecycle):
        out.extend(fn(rec, c))
    return [p.to_dict() for p in out]


# ---------------------------------------------------------------------------
# The aggregate -- the deliverable table
# ---------------------------------------------------------------------------


def aggregate(ledgers: list[list[dict]]) -> dict:
    """Producer mix per sellable field over N listings."""
    per: dict[str, dict] = {}
    for led in ledgers:
        for p in led:
            f = per.setdefault(p["field"], {"n": 0, "by_producer": collections.Counter(),
                                            "fallbacks": 0, "ext_in": 0,
                                            "by_detail": collections.Counter()})
            f["n"] += 1
            f["by_producer"][p["producer"]] += 1
            f["by_detail"][p["producer_detail"].split(" (")[0].split(" -- ")[0]] += 1
            if p.get("fallback_from"):
                f["fallbacks"] += 1
            if _has_external_input(p):
                f["ext_in"] += 1
    return {"n_listings": len(ledgers), "fields": per}


def _has_external_input(p: dict) -> bool:
    """Did an external API supply the dominant input to a value we call deterministic?"""
    for v in (p.get("inputs") or {}).values():
        if isinstance(v, dict) and v.get("producer") == EXTERNAL_API:
            return True
    return False


def render(agg: dict) -> str:
    """The producer-mix table, terminal width."""
    n = agg["n_listings"]
    fields = agg["fields"]
    order = [f for f in FIELD_ORDER if f in fields] + \
            [f for f in sorted(fields) if f not in FIELD_ORDER]
    cols = ["determ", "llm", "ext-api", "const", "human", "absent"]
    keys = [DETERMINISTIC, LLM, EXTERNAL_API, DEFAULT_CONSTANT, HUMAN_ATTESTED, ABSENT]
    lines = [f"PRODUCER MIX  (n={n} listings)", ""]
    head = f"{'field':<16}{'vals':>5}  " + "".join(f"{c:>8}" for c in cols) + \
           f"{'fallback':>10}{'ext-in':>8}"
    lines += [head, "-" * len(head)]
    for f in order:
        d = fields[f]
        cells = "".join(f"{_pct(d['by_producer'].get(k, 0), d['n']):>8}" for k in keys)
        lines.append(f"{f:<16}{d['n']:>5}  {cells}{d['fallbacks']:>10}{d['ext_in']:>8}")
    lines += ["", "producer_detail breakdown (what actually computed each value):"]
    for f in order:
        d = fields[f]
        lines.append(f"  {f}")
        for detail, k in d["by_detail"].most_common():
            lines.append(f"      {k:>4}  {detail}")
    return "\n".join(lines)


def _pct(k: int, n: int) -> str:
    return "." if k == 0 else (f"{k}" if n == 0 else f"{k} {round(100 * k / n)}%")


# ---------------------------------------------------------------------------
# CLI -- run the aggregate over an existing trace file
# ---------------------------------------------------------------------------


def _resolve(path: str) -> str:
    """Accept an absolute path, a cwd-relative one, or one relative to the rig root.

    run.sh execs from the guarded work dir, so a path typed relative to the rig root
    would otherwise miss.
    """
    if os.path.exists(path):
        return path
    root = os.environ.get("CREXI_BASELINE_ROOT", "")
    cand = os.path.join(root, path)
    if root and os.path.exists(cand):
        return cand
    raise SystemExit(f"provenance: no such trace file: {path}")


def load(paths: list[str]) -> tuple[list[tuple[str, list[dict]]], list[dict]]:
    """Read trace JSONL files -> ([(arm, ledger)], manifests).

    Records written before the ledger existed carry no ``provenance`` key; they are
    re-derived here from the captured evidence, which is why derivation lives in this
    module (see the module docstring). The arm rides along so the aggregate can print
    one table per arm -- A and B differ only in whether the LLM can serve, and a
    blended table would hide exactly the difference we are measuring.
    """
    ledgers: list[tuple[str, list[dict]]] = []
    manifests: list[dict] = []
    for p in paths:
        consts: dict = {}
        arm = "?"
        for line in open(_resolve(p)):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if "_manifest" in rec:
                manifests.append(rec["_manifest"])
                consts = rec["_manifest"].get("consts") or {}
                arm = rec["_manifest"].get("arm", "?")
                continue
            ledgers.append((arm, rec.get("provenance") or build_ledger(rec, consts)))
    return ledgers, manifests


def _json_agg(agg: dict) -> dict:
    return {"n_listings": agg["n_listings"],
            "fields": {f: {"n": d["n"], "by_producer": dict(d["by_producer"]),
                           "fallbacks": d["fallbacks"], "ext_in": d["ext_in"]}
                       for f, d in agg["fields"].items()}}


def main() -> int:
    ap = argparse.ArgumentParser(description="Producer-mix aggregate over a trace file.")
    ap.add_argument("traces", nargs="+", help="trace_arm*.jsonl produced by rig/trace.py")
    ap.add_argument("--json", action="store_true", help="emit the aggregate as JSON")
    ap.add_argument("--fallbacks", action="store_true",
                    help="also list every fallback record (value + what it fell back from)")
    args = ap.parse_args()

    ledgers, manifests = load(args.traces)
    if not ledgers:
        raise SystemExit("provenance: no listing records found")
    arms = sorted({a for a, _ in ledgers})
    groups = [(a, [led for arm, led in ledgers if arm == a]) for a in arms]
    if args.json:
        print(json.dumps({a: _json_agg(aggregate(g)) for a, g in groups}, indent=2))
        return 0

    print(f"=== provenance ledger  arms={', '.join(arms)}  files={len(args.traces)} ===")
    for a, g in groups:
        print(f"\n---------- arm {a} ----------")
        print(render(aggregate(g)))
    if args.fallbacks:
        print("\nFALLBACKS (a higher-trust producer was attempted and lost):")
        for _, led in ledgers:
            for p in led:
                fb = p.get("fallback_from")
                if fb:
                    print(f"  {p['field']:<16} = {str(p['value'])[:28]:<28} <- "
                          f"{fb.get('producer')} {fb.get('value')} rejected_by={fb.get('rejected_by')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
