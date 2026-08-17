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

from evals.scorers.score import SCORER_VERSION, score_case  # noqa: E402
from fis_platform.model_gateway import ModelGateway, default_registry  # noqa: E402
from fis_platform.suite import (  # noqa: E402
    ONTOLOGY_VERSION, SUITE_VERSION, SuiteMismatch, corpus_suite, git_head, suite_of_run,
)
from fis_platform.tool_broker.broker import ToolBroker  # noqa: E402
from fis_platform.verification.verifier import VERIFIER_VERSION  # noqa: E402
from schemas.scenario import EvalRun, SeedSplit  # noqa: E402
from scripts.corpus_digest import corpus_digest  # noqa: E402
from services.ai_orchestrator.cascade import EscalationPolicy, investigate_cascade  # noqa: E402
from services.ai_orchestrator.investigate import (  # noqa: E402
    DEFAULT_MAX_TOKENS, PROMPT_VERSION, WORKFLOW_VERSION, EvidenceMode, investigate,
)
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


def config_digest(*, model_ref: str, mode: str, prompt: str,
                  escalate_to: str | None = None, escalation_policy: str | None = None,
                  strong_prompt: str | None = None,
                  max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
    """The run's configuration string, recorded on `EvalRun.config_digest`.

    Two arms with the same digest are the same configuration. The historical form is
    `model|mode|prompt` (+ the cascade suffix), and every run before R3b was made at
    the default budget, so the budget is appended ONLY when it differs from the
    default: a run at 4096 keeps the digest its predecessors recorded, and a run at
    any other budget can never be mistaken for one of them.
    """
    digest = f"{model_ref}|{mode}|{prompt}"
    if escalate_to:
        digest += f"|cascade:{escalation_policy}->{escalate_to}|{strong_prompt}"
    if max_tokens != DEFAULT_MAX_TOKENS:
        digest += f"|max_tokens:{max_tokens}"
    return digest


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


def guard_suite(conn, run_id: str, split: str, resume: bool) -> None:
    """Refuse the two ways a suite bump can be silently absorbed.

    1. Code and corpus disagree: the manifests in the database were generated for a
       different suite than this runner scores against. Every score would be
       measured against the wrong worlds and labelled with the wrong version.
    2. A run id is reused across suites: `--resume` would treat the old suite's rows
       as done, and a fresh run would keep the old rows via ON CONFLICT DO NOTHING.
       Either way one run id would carry two suites' numbers.
    """
    corpus = corpus_suite(conn)
    if corpus != SUITE_VERSION:
        raise SuiteMismatch(
            f"the corpus in the database is suite {corpus!r} but this code scores suite "
            f"{SUITE_VERSION!r} — run `make migrate corpus` (and `make reachability`) first")
    existing = suite_of_run(conn, run_id)
    if existing is not None and existing != SUITE_VERSION:
        raise SuiteMismatch(
            f"run id {run_id!r} already holds suite-{existing} scores; a suite-{SUITE_VERSION} run "
            "needs its own run id")
    if existing is not None and not resume:
        raise SuiteMismatch(
            f"run id {run_id!r} already has scores; pass --resume to continue it or choose a new id")


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
                 (run_id, scenario_id, trace_id, experiment_arm, payload, all_pass, suite_version)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (run_id, scenario_id) DO NOTHING""",
            (run_id, score.scenario_id, str(trajectory.trace_id), score.experiment_arm,
             Jsonb(json.loads(score.model_dump_json())), score.all_pass, SUITE_VERSION),
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
    # R3b — the generation budget as an explicit factor. Applies to --model-ref (the
    # weak stage in a cascade); the strong stage keeps the default.
    ap.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                    help=f"Generation budget for --model-ref (default {DEFAULT_MAX_TOKENS}, the "
                         "budget every recorded run was made with). Recorded on every "
                         "invocation and, when non-default, in the config digest.")
    args = ap.parse_args()
    if args.max_tokens < 256:
        raise SystemExit(f"--max-tokens {args.max_tokens} is below the manifest minimum (256)")

    run_id = args.run_id or f"{args.arm}-{args.model_ref}-{args.split}"
    gateway = ModelGateway(default_registry())

    manifest = gateway.registry.resolve(args.model_ref)
    if args.max_tokens > manifest.max_output_tokens:
        raise SystemExit(f"--max-tokens {args.max_tokens} exceeds {args.model_ref}'s declared "
                         f"ceiling max_output_tokens={manifest.max_output_tokens}")
    if args.max_tokens + 3_600 > manifest.context_window:
        # The largest dev/test prompt is ~3.5k tokens (either tokenizer). A budget the
        # context cannot hold would fail mid-run on the longest case, not at start.
        raise SystemExit(f"--max-tokens {args.max_tokens} + a ~3.6k-token prompt exceeds "
                         f"{args.model_ref}'s context window ({manifest.context_window})")
    runtime_context = {"run_id": run_id, "model_ref": args.model_ref, "prompt": args.prompt,
                       "max_tokens": str(args.max_tokens),
                       # Suite v3: enough identity on every trajectory to tie a score to
                       # the suite, the scoring code and the commit that produced it.
                       "suite_version": SUITE_VERSION, "scorer_version": SCORER_VERSION,
                       "verifier_version": VERIFIER_VERSION, "ontology_version": ONTOLOGY_VERSION,
                       "prompt_version": PROMPT_VERSION, "workflow_version": WORKFLOW_VERSION,
                       "git_head": git_head()}
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
        guard_suite(owner, run_id, args.split, args.resume)
        runtime_context["corpus_digest"] = corpus_digest(owner)["digest"]
        manifests = load_manifests(owner, args.split, args.limit)
        done = already_done(owner, run_id) if args.resume else set()
        pending = [m for m in manifests if m["scenario_id"] not in done]

        print(f"run_id={run_id}  arm={args.arm}  model={args.model_ref}  mode={args.mode}")
        print(f"{len(manifests)} scenarios in split, {len(done)} already scored, "
              f"{len(pending)} to run")
        print("runtime: " + "  ".join(f"{k}={v}" for k, v in runtime_context.items()
                                     if k not in ("run_id", "model_ref", "prompt")) + "\n")

        # The suite a score is measured against is `fis_platform.suite.SUITE_VERSION`
        # (v2: the event migration; v3: the four benchmark-defect fixes of
        # SUITE_V3_RELEASE_CONTRACT.md). Numbers are never comparable across it.
        digest = config_digest(model_ref=args.model_ref, mode=args.mode, prompt=args.prompt,
                               escalate_to=args.escalate_to, escalation_policy=args.escalation_policy,
                               strong_prompt=args.strong_prompt, max_tokens=args.max_tokens)
        run = EvalRun(run_id=run_id, suite="fis-eval", suite_version=SUITE_VERSION,
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
                            weak_max_tokens=args.max_tokens,
                        )
                        result, traj = out.result, out.trajectory
                    else:
                        out = None
                        result, traj = await investigate(
                            m["case_id"], gateway=gateway, broker=broker,
                            model_ref=args.model_ref, experiment_arm=args.arm,
                            mode=EvidenceMode(args.mode), scenario_id=m["scenario_id"],
                            prompt_ref=args.prompt, runtime_context=runtime_context,
                            max_tokens=args.max_tokens,
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
            # First invocation = the model under test (the weak stage in a cascade).
            inv = traj.model_invocations[0] if traj.model_invocations else None
            gen = (f"{inv.usage.output_tokens:>5}tok/{inv.stop_reason or '?'}" if inv else "")
            print(f"[{i}/{len(pending)}] {m['scenario_id']:<12} {mark:<4} "
                  f"rc={'ok' if score.root_cause_correct else 'X'} "
                  f"ev={score.required_evidence_recall:.2f} "
                  f"act={'ok' if score.next_action_acceptable else 'X'} "
                  f"ver={'ok' if score.verifier_passed else 'X'} "
                  f"{score.wall_ms:>6}ms {gen}  ${score.reference_cost_usd:.4f}  {said}{route}")

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
