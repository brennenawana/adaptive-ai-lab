"""Eval runner — checkpointed and resumable.

Resumability is not a nicety here. The frontier arms run on subscription plans with
rolling rate limits, and a 200-case run WILL be interrupted. A runner that cannot
resume turns a rate-limit pause into a lost afternoon and, worse, tempts you to
re-run a partial set and compare it against a full one.

Every scored case is committed immediately with a UNIQUE(run_id, scenario_id)
constraint doing the deduplication, so resume is exact rather than best-effort.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv  # noqa: E402

from evals.scorers.score import score_case  # noqa: E402
from fis_platform.model_gateway import ModelGateway, default_registry  # noqa: E402
from fis_platform.tool_broker.broker import ToolBroker  # noqa: E402
from schemas.scenario import EvalRun, SeedSplit  # noqa: E402
from services.ai_orchestrator.investigate import EvidenceMode, investigate  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

OWNER_DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")
TOOLS_DSN = os.environ.get("FIS_TOOLS_DSN",
                           "postgresql://fis_tools:fis_tools_local_dev@127.0.0.1:5433/fis")


def load_manifests(conn, split: str, limit: int | None) -> list[dict]:
    sql = """
        SELECT scenario_id, seed, split, category, root_cause, required_evidence,
               acceptable_next_actions, forbidden_claims, distractor_event_ids,
               case_id, subject_ids
        FROM ground_truth.scenario_manifests
        WHERE split = %s ORDER BY scenario_id
    """
    params: tuple = (split,)
    if limit:
        sql += " LIMIT %s"
        params += (limit,)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def already_done(conn, run_id: str) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT scenario_id FROM learning.case_scores WHERE run_id = %s", (run_id,))
        return {r[0] for r in cur.fetchall()}


def persist(conn, run_id: str, score, trajectory) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO learning.trajectories
                 (trace_id, scenario_id, case_id, experiment_arm, workflow,
                  workflow_version, payload)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (trace_id) DO NOTHING""",
            (str(trajectory.trace_id), trajectory.scenario_id, trajectory.case_id,
             trajectory.experiment_arm, trajectory.workflow, trajectory.workflow_version,
             Jsonb(json.loads(trajectory.model_dump_json()))),
        )
        cur.execute(
            """INSERT INTO learning.case_scores
                 (run_id, scenario_id, trace_id, experiment_arm, payload, all_pass)
               VALUES (%s,%s,%s,%s,%s,%s)
               ON CONFLICT (run_id, scenario_id) DO NOTHING""",
            (run_id, score.scenario_id, str(trajectory.trace_id), score.experiment_arm,
             Jsonb(json.loads(score.model_dump_json())), score.all_pass),
        )
    conn.commit()


async def main() -> None:
    ap = argparse.ArgumentParser(description="Run a FIS experiment arm.")
    ap.add_argument("--arm", required=True, help="E2, E4, ... — recorded on every trajectory")
    ap.add_argument("--model-ref", required=True)
    ap.add_argument("--mode", choices=[m.value for m in EvidenceMode],
                    default=EvidenceMode.FIXED_EVIDENCE.value)
    ap.add_argument("--split", choices=[s.value for s in SeedSplit], default="test")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--run-id")
    ap.add_argument("--resume", action="store_true",
                    help="Skip scenarios already scored under this run-id.")
    args = ap.parse_args()

    run_id = args.run_id or f"{args.arm}-{args.model_ref}-{args.split}"
    gateway = ModelGateway(default_registry())

    with psycopg.connect(OWNER_DSN) as owner:
        manifests = load_manifests(owner, args.split, args.limit)
        done = already_done(owner, run_id) if args.resume else set()
        pending = [m for m in manifests if m["scenario_id"] not in done]

        print(f"run_id={run_id}  arm={args.arm}  model={args.model_ref}  mode={args.mode}")
        print(f"{len(manifests)} scenarios in split, {len(done)} already scored, "
              f"{len(pending)} to run\n")

        run = EvalRun(run_id=run_id, suite="fis-eval", suite_version="1",
                      experiment_arm=args.arm, split=SeedSplit(args.split),
                      config_digest=f"{args.model_ref}|{args.mode}|prompt1")

        for i, m in enumerate(pending, 1):
            with ToolBroker(TOOLS_DSN) as broker:
                try:
                    result, traj = await investigate(
                        m["case_id"], gateway=gateway, broker=broker,
                        model_ref=args.model_ref, experiment_arm=args.arm,
                        mode=EvidenceMode(args.mode), scenario_id=m["scenario_id"],
                    )
                except Exception as exc:  # noqa: BLE001 — one bad case must not kill the run
                    print(f"[{i}/{len(pending)}] {m['scenario_id']}  EXCEPTION {exc}")
                    continue

            score = score_case(result=result, trajectory=traj, manifest=m, run_id=run_id)
            run.scores.append(score)
            persist(owner, run_id, score, traj)   # commit per case: resume stays exact

            mark = "PASS" if score.all_pass else "fail"
            said = result.root_cause.label.value if result else "-"
            print(f"[{i}/{len(pending)}] {m['scenario_id']:<12} {mark:<4} "
                  f"rc={'ok' if score.root_cause_correct else 'X'} "
                  f"ev={score.required_evidence_recall:.2f} "
                  f"act={'ok' if score.next_action_acceptable else 'X'} "
                  f"ver={'ok' if score.verifier_passed else 'X'} "
                  f"{score.wall_ms:>6}ms  ${score.reference_cost_usd:.4f}  {said}")

    print("\n" + "=" * 78)
    print(f"strict all-pass    : {_pct(run.strict_all_pass_rate)}")
    print(f"root-cause accuracy: {_pct(run.root_cause_accuracy)}")
    print(f"cloud escalation   : {_pct(run.cloud_escalation_rate)}")
    print(f"P95 latency        : {run.p95_latency_ms()} ms")
    cps = run.cost_per_successful_case
    print(f"cost / success     : {'n/a' if cps is None else f'${cps:.4f}'}")

    out = ROOT / "evals" / "reports" / f"{run_id}.json"
    out.write_text(run.model_dump_json(indent=2))
    print(f"report             : {out}")


def _pct(v: float | None) -> str:
    return "n/a" if v is None else f"{v * 100:.1f}%"


if __name__ == "__main__":
    asyncio.run(main())
