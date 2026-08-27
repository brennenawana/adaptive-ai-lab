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
}


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
