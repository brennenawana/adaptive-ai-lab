"""R6 accounting — new inference by split/artifact and wall time by phase (report § 10).

Cases are counted from canonical storage (learning.case_scores rows whose trajectory carries
an R6 candidate_id), not from the ledger, so an interrupted-and-resumed run is counted once
per case. Run wall is summed from the ledger end lines; phase wall from phases.jsonl.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.provenance import R6Registry, default_root  # noqa: E402

DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")


def main() -> None:
    reg = R6Registry(default_root())
    with psycopg.connect(DSN) as conn:
        rows = conn.execute(
            """SELECT t.payload->'runtime_context'->>'candidate_id',
                      t.payload->'runtime_context'->>'artifact_id',
                      m.split, cs.run_id, count(*),
                      sum((t.payload->'model_invocations'->0->'usage'->>'output_tokens')::int),
                      sum((t.payload->'model_invocations'->0->'usage'->>'input_tokens')::int),
                      sum((cs.payload->>'wall_ms')::bigint)
                 FROM learning.case_scores cs
                 JOIN learning.trajectories t ON t.trace_id = cs.trace_id
                 JOIN ground_truth.scenario_manifests m ON m.scenario_id = cs.scenario_id
                WHERE t.payload->'runtime_context'->>'candidate_id' IS NOT NULL
                GROUP BY 1,2,3,4 ORDER BY 2,3,4""").fetchall()
        frontier_new = conn.execute(
            """SELECT count(*) FROM learning.case_scores cs JOIN learning.trajectories t ON t.trace_id=cs.trace_id
                WHERE cs.experiment_arm = 'R6' AND t.payload->>'used_frontier' = 'true'""").fetchone()[0]
    by_run = [{"candidate_id": r[0], "artifact_id": r[1], "split": r[2], "run_id": r[3], "cases": r[4],
               "output_tokens": int(r[5] or 0), "input_tokens": int(r[6] or 0), "wall_s_sum": round(int(r[7] or 0) / 1000, 1)} for r in rows]
    by_artifact_split: dict[str, dict[str, int]] = {}
    for r in by_run:
        by_artifact_split.setdefault(r["artifact_id"], {}).setdefault(r["split"], 0)
        by_artifact_split[r["artifact_id"]][r["split"]] += r["cases"]
    total = sum(r["cases"] for r in by_run)

    ledger = reg.read_ledger()
    wall_by_run: dict[str, float] = {}
    for ln in ledger:
        if ln.get("event") == "end":
            wall_by_run[ln["run_id"]] = wall_by_run.get(ln["run_id"], 0.0) + float(ln.get("wall_s", 0))
    phases = [json.loads(l) for l in reg.phases_file.read_text().splitlines() if l.strip()]
    starts: dict[str, str] = {}
    phase_wall: dict[str, float] = {}
    for p in phases:
        if p["event"] == "start":
            starts[p["name"]] = p["at"]
        elif p["name"] in starts:
            a = datetime.fromisoformat(starts[p["name"]]); b = datetime.fromisoformat(p["at"])
            phase_wall[p["name"]] = round((b - a).total_seconds() / 3600, 2)
    out = {"total_new_local_cases": total, "new_frontier_calls": int(frontier_new),
           "by_artifact_split": by_artifact_split, "by_run": by_run,
           "run_wall_hours_from_ledger": {k: round(v / 3600, 2) for k, v in sorted(wall_by_run.items())},
           "phase_wall_hours": phase_wall, "phases": phases}
    print(json.dumps(out, indent=2, default=lambda o: int(o) if hasattr(o, "__int__") else str(o)))


if __name__ == "__main__":
    main()
