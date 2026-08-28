"""Stable defect-class registry for the Crexi baseline.

IDs are permanent once assigned: a per-listing trace tags observations with
these, so renaming one silently rewrites history. Add, never repurpose.

Each class carries the STAGE it manifests at, so aggregation can answer
"where does the pipeline lose listings" without re-reading prose.
"""
from __future__ import annotations

STAGES = ("ingest", "identity", "income", "arv", "linkage", "routing", "gate")

DEFECTS: dict[str, dict] = {
    "F-B1": dict(
        stage="income", severity="high",
        title="per-unit band rejects a correct high-rent extraction",
        detect="llm returned a gross, validator rejected it, gross > units*_MAX_UNIT_RENT",
    ),
    "F-B2": dict(
        stage="arv", severity="high",
        title="comp_set NULL though arv_source advertises a comp count",
        detect="arv is not None and comp_set is empty",
    ),
    "F-B3": dict(
        stage="arv", severity="medium",
        title="arv_confidence below the 0.35 credibility floor",
        detect="arv is not None and arv_confidence < 0.35",
    ),
    "F-B4": dict(
        stage="income", severity="high",
        title="anti-hallucination check cannot parse $NNNk / $NNNM notation",
        detect="llm gross rejected, and gross*12 (or gross) appears in text only in K/M form",
    ),
    "F-B5": dict(
        stage="arv", severity="unknown",
        title="no ARV produced despite comps being fetched",
        detect="comps fetched > 0 and arv is None",
    ),
    "F-B6": dict(
        stage="income", severity="medium",
        title="priced off tier-4 market median (no listing-specific income signal)",
        detect="income method == 'market_median'",
    ),
    "F-B8": dict(
        stage="arv", severity="high",
        title="sale_event_name never reaches Comp.exclusion_reason -> universal 0.55 haircut",
        detect="arv_source contains ';no_flip_package_signal'",
    ),
    "F-B7": dict(
        stage="income", severity="low",
        title="no income signal at all",
        detect="income method in (None, 'none')",
    ),
    # --- ingest stage (added 2026-08-27 from the first instrumented ingest pass) ---
    "F-B10": dict(
        stage="ingest", severity="high",
        title="unit count stated only in prose -> units NULL -> disqualified downstream",
        detect="units is None and property_name/marketing_description carries a unit signal",
    ),
    "F-B11": dict(
        stage="ingest", severity="medium",
        title="tenancy/occupancy/neighborhood unreachable: to_search_stub never maps them",
        detect="field is NULL on 100% of an ingest pass and its only source is the search stub",
    ),
    "F-B12": dict(
        stage="ingest", severity="low",
        title="plausibility envelopes never applied on the Crexi path",
        detect="a normalized value lies outside its plausible_* envelope",
    ),
    "F-B13": dict(
        stage="ingest", severity="low",
        title="a normalization drop is invisible in every IngestStats counter",
        detect="normalize_listing returned None (not fetch_errors, not fetched -- uncounted)",
    ),
    # RUN-level, not per-asset: detected by comparing probe families, not by inspecting
    # one record. classify_ingest() cannot see these; ingest_funnel.py flags them.
    "F-B14": dict(
        stage="ingest", severity="high", scope="run",
        title="county partitions do not cover the state scope, and nothing says so",
        detect="sum(county totalCount) < whole-state totalCount on a partitioned full sweep",
    ),
    "F-B15": dict(
        stage="ingest", severity="high", scope="run",
        title="type gate compares a JOINED compound type string by exact membership",
        detect="a type-gate drop whose stub type_str CONTAINS a configured property_type",
    ),
    # Kept in the registry although currently INERT: the hazard is in the code, and an
    # id that exists is what lets a future run say "still inert" instead of rediscovering
    # it. Retiring it would make the refutation unfindable.
    "F-B16": dict(
        stage="ingest", severity="inert", scope="run",
        title="cross-partition dedupe winner is arrival-order dependent (inert: payloads identical)",
        detect="an asset appears in >1 partition AND its stub payloads differ between them",
    ),
}


#: Fields whose ONLY source is the search stub, which ``to_search_stub`` does not map.
#: Their null rate on the ingest path is 1.0 by construction, not by data quality.
STUB_UNREACHABLE: tuple[str, ...] = ("tenancy_type", "occupancy_rate_percent", "neighborhood")


def classify_ingest(rec: dict) -> list[str]:
    """Attach stable defect ids to ONE per-asset ingest record (ingest_trace.py shape).

    Only assets that reached normalization can carry a field-level ingest defect; one
    dropped at the stub type gate never had fields to inspect, and tagging it would
    inflate every rate by the size of the swept population rather than the fetched one.
    """
    d: list[str] = []
    if rec.get("drop_stage") == "normalization":
        d.append("F-B13")
    fields = rec.get("fields")
    if not fields:
        return d
    ev = fields.get("_units_evidence") or {}
    if ev.get("verdict") in ("prose_only", "unmapped_summary_key", "parse_failure"):
        d.append("F-B10")
    if any(fields.get(f, {}).get("state") == "null" for f in STUB_UNREACHABLE):
        d.append("F-B11")
    if any(isinstance(v, dict) and v.get("would_null_at_merge_boundary") for v in fields.values()):
        d.append("F-B12")
    return d


def summarize(records: list[dict]) -> dict:
    """Aggregate per-listing traces into a stage x defect table."""
    by_defect: dict[str, int] = {}
    by_stage: dict[str, int] = {}
    terminal: dict[str, int] = {}
    for r in records:
        for d in r.get("defects", []):
            by_defect[d] = by_defect.get(d, 0) + 1
            st = DEFECTS.get(d, {}).get("stage", "?")
            by_stage[st] = by_stage.get(st, 0) + 1
        terminal[r.get("terminal_stage") or "?"] = terminal.get(r.get("terminal_stage") or "?", 0) + 1
    return {"n": len(records), "by_defect": by_defect, "by_stage": by_stage, "terminal": terminal}
