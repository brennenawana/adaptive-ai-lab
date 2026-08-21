"""Can the fixed-evidence plan actually reach every case's required evidence?

Run this after regenerating the corpus and before trusting any score.

A case whose required evidence no tool call can return is not hard, it is
impossible — and it fails in a way that looks exactly like model weakness. Two of
the four design bugs found on 2026-08-15 were this, and a third instance survived
until the event migration: every webhook delivery in the pre-migration corpus was
addressed by a `provider_event_id` that no state row carried, so `get_webhook_history`
could never be called with it. Four classes were capped below the recall threshold
before a model saw them.

This replays the real `_phase_one`/`_phase_two` plan against the real broker with the
real `fis_tools` role, and reports the CEILING on evidence recall per class. Any
class below the scorer's threshold is a harness bug, not a result.

    .venv/bin/python scripts/evidence_reachability.py [--split test]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.tool_broker.broker import ToolBroker  # noqa: E402
from services.ai_orchestrator.investigate import _phase_one, _phase_two  # noqa: E402

OWNER_DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")
TOOLS_DSN = os.environ.get("FIS_TOOLS_DSN",
                           "postgresql://fis_tools:fis_tools_local_dev@127.0.0.1:5433/fis")
THRESHOLD = 0.8  # evals.scorers.score.evidence_threshold


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    args = ap.parse_args()

    with psycopg.connect(OWNER_DSN) as conn:
        manifests = conn.execute(
            "SELECT scenario_id, case_id, required_evidence FROM ground_truth.scenario_manifests "
            "WHERE split = %s ORDER BY scenario_id",
            (args.split,),
        ).fetchall()

    by_class: dict[str, list[float]] = defaultdict(list)
    unreachable: list[tuple[str, str]] = []

    with ToolBroker(TOOLS_DSN) as broker:
        for scenario_id, case_id, required in manifests:
            case, _ = broker.invoke("get_case", {"case_id": case_id})
            results = [case]
            for tool, tool_args in _phase_one(case):
                res, _ = broker.invoke(tool, tool_args)
                results.append({tool: res})
            for tool, tool_args in _phase_two(case, results):
                res, _ = broker.invoke(tool, tool_args)
                results.append({tool: res})

            # Recall is scored over ids the model cites, and it can only cite what it
            # was shown. Substring containment over the serialised bundle is exactly
            # the question "was this id in front of the model at all".
            bundle = json.dumps(results, default=str)
            hits = [e for e in required if e in bundle]
            by_class[scenario_id.split("-")[0]].append(len(hits) / len(required))
            unreachable += [(scenario_id, e) for e in required if e not in bundle]

    print(f"{'class':<6} {'n':>3} {'ceiling':>8}   status")
    failing = 0
    for code in sorted(by_class):
        ceilings = by_class[code]
        worst = min(ceilings)
        ok = worst >= THRESHOLD
        failing += 0 if ok else 1
        print(f"{code:<6} {len(ceilings):>3} {worst:>8.3f}   "
              f"{'ok' if ok else 'UNWINNABLE — capped below the ' + str(THRESHOLD) + ' threshold'}")

    if unreachable:
        print(f"\n{len(unreachable)} unreachable evidence ids, first 10:")
        for scenario_id, eid in unreachable[:10]:
            print(f"  {scenario_id}  {eid}")

    print(f"\n{len(manifests)} cases, {failing} classes with an unreachable-evidence cap")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
