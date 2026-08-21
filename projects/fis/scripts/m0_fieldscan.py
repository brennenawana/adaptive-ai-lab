"""M0 WP-B Pass 1 — offline field scan of every known R6 cap-hit case.

SECONDARY, DESCRIPTIVE ONLY (NEXT_STEP_M0.md § 6-B Pass 1): context for the report,
zero influence on the R7 decision. No inference, no model server — a pure read of
fields already stored in learning.* (content_chars / reasoning_chars per invocation).

Covers 100% of the cap-hit (run, case) pairs across ALL R6 runs — including the DEV
and TEST runs. That is a read of historical rows, not a split look: no case executes,
and only numeric fields and the stop reason leave the database (never case content).

Output: artifacts/m0_caphit_fieldscan.csv
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.m0_classify import PRIMARY_CASES

ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")

SQL = """
SELECT cs.run_id,
       cs.scenario_id,
       m.split,
       inv->>'canonical_model'          AS canonical_model,
       inv->>'quantization'             AS quantization,
       (inv->>'max_tokens')::int        AS max_tokens,
       inv->>'stop_reason'              AS stop_reason,
       (inv->'usage'->>'output_tokens')::int AS output_tokens,
       (inv->>'reasoning_chars')::int   AS reasoning_chars,
       (inv->>'content_chars')::int     AS content_chars,
       (inv->'latency'->>'wall_ms')::int AS wall_ms,
       cs.all_pass
FROM learning.case_scores cs
JOIN learning.trajectories t ON t.trace_id = cs.trace_id
JOIN ground_truth.scenario_manifests m ON m.scenario_id = cs.scenario_id,
LATERAL jsonb_array_elements(t.payload->'model_invocations') inv
WHERE cs.run_id LIKE 'R6-%%'
  AND inv->>'stop_reason' = 'length'
ORDER BY cs.run_id, cs.scenario_id
"""

FIELDS = ["run_id", "scenario_id", "split", "canonical_model", "quantization",
          "max_tokens", "stop_reason", "output_tokens", "reasoning_chars",
          "content_chars", "wall_ms", "all_pass", "content_started",
          "in_primary_population"]


def main() -> None:
    out_path = ROOT / "artifacts" / "m0_caphit_fieldscan.csv"
    rows = []
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(SQL)
        cols = [d.name for d in cur.description]
        for rec in cur.fetchall():
            row = dict(zip(cols, rec))
            row["content_started"] = bool(row["content_chars"] or 0)
            row["in_primary_population"] = (
                row["scenario_id"] in PRIMARY_CASES
                and row["run_id"] in ("R6-qwen38-q3km-train-pilot",
                                      "R6-qwen38-q3km-train-stab"))
            rows.append(row)

    out_path.parent.mkdir(exist_ok=True)
    with out_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    started = sum(1 for r in rows if r["content_started"])
    primary = sum(1 for r in rows if r["in_primary_population"])
    print(f"cap-hit (run, case) pairs: {len(rows)}  (expected 145)")
    print(f"  content started (cut inside the answer): {started}")
    print(f"  still inside reasoning:                  {len(rows) - started}")
    print(f"  rows from the primary population runs:   {primary}  (expected 19: 15 pilot + 4 stab)")
    print(f"wrote {out_path}")
    if len(rows) != 145:
        raise SystemExit(f"!! expected 145 cap-hit pairs, found {len(rows)} — "
                         "the known-population premise changed; STOP and report")


if __name__ == "__main__":
    main()
