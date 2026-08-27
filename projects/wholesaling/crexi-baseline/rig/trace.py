"""Per-listing pipeline trace for the Crexi value-route lane.

Wraps the product's own seams at runtime (no product-code edits) so every
listing yields ONE record spanning income -> arv -> linkage -> routing -> gate,
tagged with stable defect ids from defects.py.

Design note: the seams below are private names in product modules. A rename
would silently drop a column, so install() ASSERTS every target exists and
records its source digest -- a drifted seam is visible, not silent.

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

from defects import DEFECTS, summarize  # noqa: E402

CUR: dict = {}          # accumulates the record for the listing in flight
PATCHES: list[dict] = []


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
    """A listing is finished when a DIFFERENT asset appears at any seam.

    Necessary because seams do not fire in a fixed order: _process_listing computes
    the ARV BEFORE resolving income, so keying the boundary off income alone
    attributed each listing's ARV to its predecessor.
    """
    if aid and CUR.get("asset_id") and CUR["asset_id"] != aid:
        FLUSH()
    if aid:
        CUR["asset_id"] = aid


def _digest(fn) -> str:
    try:
        return hashlib.sha256(inspect.getsource(fn).encode()).hexdigest()[:12]
    except (OSError, TypeError):
        return "?"


def install() -> None:
    """Wrap every seam. Fails loudly if a target has moved."""
    import app.services.listing_income as LI
    import app.services.crexi_value_route as VR
    import app.guardrails.apply as GA

    targets = [
        (LI, "_try_llm_extract"), (LI, "_validate_facts"), (LI, "resolve_income"),
        (VR, "compute_mf_arv"), (GA, "evaluate"),
    ]
    for mod, name in targets:
        obj = getattr(mod, name, None)
        if obj is None:
            raise SystemExit(f"trace: seam {mod.__name__}.{name} does not exist -- product code moved")
        PATCHES.append({"target": f"{mod.__name__}.{name}", "source_sha12": _digest(obj)})

    # ---- income -----------------------------------------------------------
    _llm, _val = LI._try_llm_extract, LI._validate_facts

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
        g = getattr(facts, "gross_monthly_rent", None)
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
        return out

    LI._try_llm_extract, LI._validate_facts = t_llm, t_val

    _resolve = LI.resolve_income

    def t_resolve(listing, settings, **k):
        # _process_listing is a closure inside value_route_pass and cannot be
        # patched, so identity is captured here -- resolve_income runs once per
        # listing and therefore also serves as the record BOUNDARY: seeing a new
        # asset_id means the previous listing finished.
        _boundary(_asset_of(listing))
        CUR["units"] = getattr(listing, "units", None)
        CUR["ask"] = getattr(listing, "asking_price", None)
        CUR["has_description"] = bool(getattr(listing, "marketing_description", None))
        t0 = time.time()
        sig = _resolve(listing, settings, **k)
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
        val = getattr(getattr(out, "arv", None), "value", None) if out else None
        prov = getattr(getattr(out, "arv", None), "provenance", None) if out else None
        CUR["arv_value"] = val
        CUR["arv_confidence"] = getattr(prov, "confidence", None)
        CUR["arv_source"] = getattr(prov, "source", None)
        CUR["arv_comp_set_len"] = len(getattr(out, "comp_set", []) or []) if out else 0
        CUR["arv_ms"] = round((time.time() - t0) * 1000)
        return out

    VR.compute_mf_arv = t_arv

    # ---- gate (captures holds/overridden, which apply_gate drops) ----------
    _eval = GA.evaluate

    def t_eval(*a, **k):
        res = _eval(*a, **k)
        CUR["gate_decision"] = str(getattr(res, "decision", None))
        CUR["gate_reasons"] = list(getattr(res, "reasons", []) or [])
        CUR["gate_holds"] = list(getattr(res, "holds", []) or [])
        CUR["gate_overridden"] = list(getattr(res, "overridden", []) or [])
        return res

    GA.evaluate = t_eval


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
    args = ap.parse_args()

    install()

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
    seen: set[str] = set()
    with open(out, "w") as fh:
        fh.write(json.dumps({"_manifest": {
            "arm": arm, "wholesaling_git": git, "n_requested": args.limit,
            "seams": PATCHES, "defect_classes": sorted(DEFECTS)}}) + "\n")
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
                chunk_limit=None, after_key=None, stamp_cursor=False,
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

    summ = summarize(records)
    print(f"\n=== trace arm={arm}  n={summ['n']}  -> {out} ===")
    print("defects by class:")
    for k, v in sorted(summ["by_defect"].items(), key=lambda kv: -kv[1]):
        print(f"   {k}  {v:3d}  {DEFECTS[k]['stage']:8s} {DEFECTS[k]['title']}")
    print(f"\nby stage: {summ['by_stage']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
