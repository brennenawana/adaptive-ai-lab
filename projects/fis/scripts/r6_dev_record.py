"""Record a finished DEV (or TEST) evaluation in the R6 registry — the ONLY writer of
`dev_result.json` / `test_result.json` and the DEV verdict.

    r6_dev_record.py dev  --candidate ID --run RUN [--reference-run RUN]
    r6_dev_record.py test --candidate ID --run RUN

`dev`: reads the run from Postgres (scripts/r6_metrics.summarize), writes DEV_EVALUATED with
`dev_result = {metrics, summary, reference, role, run_id}` (the metrics the gates read, plus
the reference system's metrics for the efficiency role), then applies
`fis_platform.r6_gates.evaluate_gates` and records DEV_QUALIFIED or DEV_REJECTED with the
evaluation trace. The registry re-derives the verdict from the stored file, so this script
cannot record a verdict the gates do not produce. Refuses anything but a full split.
`test`: writes TEST_EVALUATED with the TEST summary (terminal).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.provenance import (  # noqa: E402
    DEV_EVALUATED, DEV_QUALIFIED, DEV_REJECTED, TEST_EVALUATED, R6Registry, default_root,
)
from fis_platform.r6_gates import GATES_DIGEST, evaluate_gates  # noqa: E402
from fis_platform.routing.learn import digest  # noqa: E402
from scripts.r6_metrics import load_run, summarize  # noqa: E402

DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")
EXPECTED = {"dev": 48, "test": 96}


def _metrics(summary: dict) -> dict:
    return {k: summary[k] for k in ("all_pass", "no_output", "p50_wall_ms", "gpu_mem_used_mib",
                                     "cap_hits", "silent", "root_cause_correct", "evidence_ok",
                                     "verifier_passed", "p95_wall_ms", "output_tokens_p50", "n")}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("split", choices=["dev", "test"])
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--reference-run", help="efficiency role: the reference system's DEV run id")
    ap.add_argument("--reference-label")
    args = ap.parse_args()

    reg = R6Registry(default_root())
    identity = reg.read_identity(args.candidate)
    entries = reg.read_state(args.candidate)
    contract = next(e for e in entries if e["kind"] == "transition" and e["to"] == "CONTRACT_FROZEN")["payload"]
    with psycopg.connect(DSN) as conn:
        rows = load_run(conn, args.run)
        summary = summarize(rows)
        splits = {r["split"] for r in rows.values()}
        if splits != {args.split} or len(rows) != EXPECTED[args.split]:
            raise SystemExit(f"run {args.run} is not a full {args.split} split: splits={splits} n={len(rows)}")
        ref = None
        if args.reference_run:
            ref = _metrics(summarize(load_run(conn, args.reference_run)))
            ref["label"] = args.reference_label or args.reference_run
    summary.pop("silent_ids", None)

    if args.split == "test":
        result = {"run_id": args.run, "role": identity["role"], "metrics": _metrics(summary), "summary": summary}
        entry = reg.transition(args.candidate, TEST_EVALUATED,
                               {"test_run_id": args.run, "test_result": result, "expected_cases": 96})
        print(json.dumps({"state": entry["to"], "test_result_digest": entry["payload"].get("test_result_digest")}, indent=2))
        return

    result = {"run_id": args.run, "role": identity["role"], "metrics": _metrics(summary),
              "summary": summary, "reference": ref, "gates_digest": GATES_DIGEST}
    entry = reg.transition(args.candidate, DEV_EVALUATED, {
        "dev_run_id": args.run, "dev_result": result, "expected_cases": 48,
        "contract_revision": contract["contract_revision"],
        "execution_system_digest": contract["execution_system_digest"]})
    dev_result_digest = entry["payload"]["dev_result_digest"]
    assert dev_result_digest == digest(result)
    verdict = evaluate_gates(identity["role"], result["metrics"], ref)
    to = DEV_QUALIFIED if verdict["qualified"] else DEV_REJECTED
    entry2 = reg.transition(args.candidate, to, {
        "gate_evaluation": verdict, "gates_digest": GATES_DIGEST,
        "dev_result_digest": dev_result_digest, "contract_revision": contract["contract_revision"]})
    print(json.dumps({"state": entry2["to"], "metrics": result["metrics"], "verdict": verdict}, indent=2))


if __name__ == "__main__":
    main()
