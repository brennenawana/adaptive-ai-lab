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
from services.ai_orchestrator.cascade import EscalationPolicy, investigate_cascade  # noqa: E402
from services.ai_orchestrator.investigate import EvidenceMode, investigate  # noqa: E402
from services.ai_orchestrator.prompts import DEFAULT_PROMPT, PROMPTS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

OWNER_DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")
TOOLS_DSN = os.environ.get("FIS_TOOLS_DSN",
                           "postgresql://fis_tools:fis_tools_local_dev@127.0.0.1:5433/fis")


def local_server_session(base_url: str) -> dict[str, str]:
    """Best-effort identity of the local llama.cpp server this run talks to.

    Case-level local results were found to reproduce only within ONE server session
    (same process, same request order): across a restart the same 48 dev cases moved
    23 scored outcomes with identical prompts. So a run has to say which session it
    ran in, or two runs cannot be told comparable. Recorded on every trajectory as
    `runtime_context`; never shown to the model.

    Sources: llama.cpp `/props` (build id, model path, slots) and, when the server is
    on this machine, /proc (pid + start ticks + boot id — stable within a boot, unlike
    `ps lstart` under WSL). Empty on failure rather than blocking a run.
    """
    import re
    import urllib.request
    ctx: dict[str, str] = {}
    root = base_url.rstrip("/").removesuffix("/v1")
    try:
        with urllib.request.urlopen(f"{root}/props", timeout=3) as r:
            props = json.load(r)
        ctx["llamacpp_build"] = str(props.get("build_info", ""))
        ctx["model_path"] = str(props.get("model_path", ""))
        ctx["model_alias"] = str(props.get("model_alias", ""))
        ctx["total_slots"] = str(props.get("total_slots", ""))
    except Exception:  # noqa: BLE001 — telemetry only
        pass
    port = (re.search(r":(\d+)", root) or [None, "8082"])[1]
    try:
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                cmd = f.read().replace(b"\0", b" ").decode(errors="replace")
            if "llama-server" in cmd and f"--port {port}" in cmd:
                with open(f"/proc/{pid}/stat") as f:
                    start_ticks = f.read().rsplit(")", 1)[1].split()[19]
                with open("/proc/sys/kernel/random/boot_id") as f:
                    boot = f.read().strip()
                ctx["local_server_session"] = f"pid={pid} start_ticks={start_ticks} boot={boot[:8]}"
                break
    except Exception:  # noqa: BLE001
        pass
    return ctx


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
    ap.add_argument("--prompt", default=DEFAULT_PROMPT, choices=sorted(PROMPTS),
                    help="Investigator system prompt variant (E6). The prompt is part\n"
                         "of the config digest, so two arms that differ only by prompt\n"
                         "stay distinguishable in the persisted run.")
    ap.add_argument("--resume", action="store_true",
                    help="Skip scenarios already scored under this run-id.")
    # R4 — deterministic cascade. --model-ref is the WEAK stage; these add the strong one.
    ap.add_argument("--escalate-to", metavar="MODEL_REF",
                    help="R4: run --model-ref first and escalate to this model when the "
                         "escalation policy fires. The weak stage is also scored under "
                         "'<run-id>.weak' so unnecessary escalations can be counted.")
    ap.add_argument("--escalation-policy", default=EscalationPolicy.VERIFIER.value,
                    choices=[p.value for p in EscalationPolicy])
    ap.add_argument("--strong-prompt", default=DEFAULT_PROMPT, choices=sorted(PROMPTS),
                    help="Prompt for the strong stage (default: the control, as E4 was baselined).")
    args = ap.parse_args()

    run_id = args.run_id or f"{args.arm}-{args.model_ref}-{args.split}"
    gateway = ModelGateway(default_registry())

    manifest = gateway.registry.resolve(args.model_ref)
    runtime_context = {"run_id": run_id, "model_ref": args.model_ref, "prompt": args.prompt}
    if args.escalate_to:
        gateway.registry.resolve(args.escalate_to)   # fail loudly before any case runs
        runtime_context["escalate_to"] = args.escalate_to
        runtime_context["strong_prompt"] = args.strong_prompt
    if manifest.routing is not None:
        runtime_context["gateway"] = f"{manifest.routing.gateway} {manifest.routing.gateway_version}"
    # The local backend's session, whether reached directly or through the gateway.
    # A directly-served local model (Qwen on 8082, Nemotron on 8083) is identified by
    # its own base_url; a Switchyard route by the local backend it fronts.
    if manifest.provider.value == "local_llamacpp":
        runtime_context.update(local_server_session(manifest.base_url or ""))
    elif manifest.provider.value == "switchyard":
        runtime_context.update(local_server_session(
            os.environ.get("FIS_LOCAL_MODEL_BASE_URL", "http://127.0.0.1:8082/v1")))

    with psycopg.connect(OWNER_DSN) as owner:
        manifests = load_manifests(owner, args.split, args.limit)
        done = already_done(owner, run_id) if args.resume else set()
        pending = [m for m in manifests if m["scenario_id"] not in done]

        print(f"run_id={run_id}  arm={args.arm}  model={args.model_ref}  mode={args.mode}")
        print(f"{len(manifests)} scenarios in split, {len(done)} already scored, "
              f"{len(pending)} to run")
        print("runtime: " + "  ".join(f"{k}={v}" for k, v in runtime_context.items()
                                     if k not in ("run_id", "model_ref", "prompt")) + "\n")

        # v2: the event migration. The corpus is regenerated (failures are now
        # produced by the consumers rather than written by the generator) and the
        # tool set gained the vendor-window form of get_verifications. Neither the
        # root-cause set nor the cause->action mapping changed, but the suite a score
        # was measured against did — v1 numbers are not comparable to v2 numbers.
        digest = f"{args.model_ref}|{args.mode}|{args.prompt}"
        if args.escalate_to:
            digest += f"|cascade:{args.escalation_policy}->{args.escalate_to}|{args.strong_prompt}"
        run = EvalRun(run_id=run_id, suite="fis-eval", suite_version="2",
                      experiment_arm=args.arm, split=SeedSplit(args.split),
                      config_digest=digest)
        escalations = 0

        for i, m in enumerate(pending, 1):
            with ToolBroker(TOOLS_DSN) as broker:
                try:
                    if args.escalate_to:
                        out = await investigate_cascade(
                            m["case_id"], gateway=gateway, broker=broker,
                            weak_ref=args.model_ref, strong_ref=args.escalate_to,
                            policy=EscalationPolicy(args.escalation_policy),
                            experiment_arm=args.arm, mode=EvidenceMode(args.mode),
                            scenario_id=m["scenario_id"], weak_prompt_ref=args.prompt,
                            strong_prompt_ref=args.strong_prompt,
                            runtime_context=runtime_context,
                        )
                        result, traj = out.result, out.trajectory
                    else:
                        out = None
                        result, traj = await investigate(
                            m["case_id"], gateway=gateway, broker=broker,
                            model_ref=args.model_ref, experiment_arm=args.arm,
                            mode=EvidenceMode(args.mode), scenario_id=m["scenario_id"],
                            prompt_ref=args.prompt, runtime_context=runtime_context,
                        )
                except Exception as exc:  # noqa: BLE001 — one bad case must not kill the run
                    print(f"[{i}/{len(pending)}] {m['scenario_id']}  EXCEPTION {exc}")
                    continue

            score = score_case(result=result, trajectory=traj, manifest=m, run_id=run_id)
            run.scores.append(score)
            persist(owner, run_id, score, traj)   # commit per case: resume stays exact

            route = ""
            if out is not None:
                # The weak stage is scored and persisted under its own run id so the
                # eval can count unnecessary escalations and false accepts later.
                # Same trajectory when the weak result was accepted; a separate one
                # (its own trace_id) when the cascade escalated.
                weak_score = score_case(result=out.weak_result, trajectory=out.weak_trajectory,
                                        manifest=m, run_id=f"{run_id}.weak")
                persist(owner, f"{run_id}.weak", weak_score, out.weak_trajectory)
                if out.decision.escalated:
                    escalations += 1
                route = (f" -> {out.decision.escalation_reason}" if out.decision.escalated
                         else " -> weak accepted")

            mark = "PASS" if score.all_pass else "fail"
            said = result.root_cause.label.value if result else "-"
            print(f"[{i}/{len(pending)}] {m['scenario_id']:<12} {mark:<4} "
                  f"rc={'ok' if score.root_cause_correct else 'X'} "
                  f"ev={score.required_evidence_recall:.2f} "
                  f"act={'ok' if score.next_action_acceptable else 'X'} "
                  f"ver={'ok' if score.verifier_passed else 'X'} "
                  f"{score.wall_ms:>6}ms  ${score.reference_cost_usd:.4f}  {said}{route}")

    print("\n" + "=" * 78)
    print(f"strict all-pass    : {_pct(run.strict_all_pass_rate)}")
    print(f"root-cause accuracy: {_pct(run.root_cause_accuracy)}")
    print(f"cloud escalation   : {_pct(run.cloud_escalation_rate)}"
          + (f"  ({escalations} escalated by policy '{args.escalation_policy}')" if args.escalate_to else ""))
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
