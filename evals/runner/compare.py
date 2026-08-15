"""Cross-arm comparison table.

The guide's demo ends with numbers: local-only vs cloud-only vs hybrid, on
all-pass, escalation, latency and cost per successful case. This renders that
directly from the persisted scores rather than from any in-memory run, so it is
always consistent with what was actually recorded.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")

QUERY = """
SELECT run_id,
       experiment_arm                                              AS arm,
       count(*)                                                    AS n,
       avg((all_pass)::int)                                        AS all_pass,
       avg(((payload->>'root_cause_correct')::bool)::int)          AS root_cause,
       avg((payload->>'required_evidence_recall')::float)          AS evidence,
       avg(((payload->>'next_action_acceptable')::bool)::int)      AS action,
       avg(((payload->>'verifier_passed')::bool)::int)             AS verifier,
       sum((payload->>'unsupported_claims')::int)                  AS unsupported,
       sum(((payload->>'forbidden_claim_made')::bool)::int)        AS forbidden,
       avg(((payload->>'escalated_to_frontier')::bool)::int)       AS cloud,
       percentile_disc(0.5) WITHIN GROUP (ORDER BY (payload->>'wall_ms')::int)  AS p50_ms,
       percentile_disc(0.95) WITHIN GROUP (ORDER BY (payload->>'wall_ms')::int) AS p95_ms,
       avg((payload->>'tool_calls_total')::float)                  AS tools,
       sum((payload->>'reference_cost_usd')::float)                AS total_cost
FROM learning.case_scores
GROUP BY run_id, experiment_arm
ORDER BY experiment_arm, run_id;
"""


def _pct(v) -> str:
    return "  n/a" if v is None else f"{float(v) * 100:5.1f}%"


def main() -> None:
    with psycopg.connect(DSN) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(QUERY)
        rows = cur.fetchall()

    if not rows:
        print("no scored runs yet — run `make eval-e2`")
        return

    hdr = (f"{'run':<26}{'n':>4}{'all-pass':>10}{'root':>8}{'evid':>8}{'act':>8}"
           f"{'ver':>8}{'unsup':>7}{'forb':>6}{'cloud':>8}{'p50':>8}{'p95':>8}"
           f"{'tools':>7}{'$/win':>9}")
    print(hdr)
    print("-" * len(hdr))

    for r in rows:
        wins = float(r["all_pass"] or 0) * r["n"]
        cost_per_win = (r["total_cost"] / wins) if wins else None
        print(
            f"{r['run_id']:<26}{r['n']:>4}{_pct(r['all_pass']):>10}{_pct(r['root_cause']):>8}"
            f"{_pct(r['evidence']):>8}{_pct(r['action']):>8}{_pct(r['verifier']):>8}"
            f"{r['unsupported']:>7}{r['forbidden']:>6}{_pct(r['cloud']):>8}"
            f"{r['p50_ms']:>7}ms{r['p95_ms']:>7}ms{r['tools']:>7.1f}"
            f"{('  n/a' if cost_per_win is None else f'${cost_per_win:.4f}'):>9}"
        )

    print("\nall-pass is strictly conjunctive: root cause AND evidence recall >= threshold")
    print("AND zero unsupported claims AND acceptable action AND verifier passed.")
    print("$/win uses reference list prices — subscription marginal cost is ~zero, so")
    print("billed amounts would make every cloud arm look free.")


if __name__ == "__main__":
    main()
