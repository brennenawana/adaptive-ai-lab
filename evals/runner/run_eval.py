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
                argv = [a for a in f.read().decode(errors="replace").split("\0") if a]
            if (argv and Path(argv[0]).name == "llama-server"
                    and ("--port", str(port)) in list(zip(argv, argv[1:]))):
                with open(f"/proc/{pid}/stat") as f:
                    start_ticks = f.read().rsplit(")", 1)[1].split()[19]
                with open("/proc/sys/kernel/random/boot_id") as f:
                    boot = f.read().strip()
                ctx["local_server_session"] = f"pid={pid} start_ticks={start_ticks} boot={boot[:8]}"
                break
    except Exception:  # noqa: BLE001
        pass
    return ctx


def gpu_mem_used_mib() -> str:
    """`nvidia-smi` memory.used (MiB) for GPU 0, or "" — the resident-footprint sample the R6
    efficiency gate reads (contract § 11). WSL cannot attribute VRAM per process, so this is
    the card total; R6 keeps exactly one candidate server resident, which is what makes the
    total the candidate's footprint."""
    import subprocess
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10, check=True).stdout
        return out.strip().splitlines()[0].strip()
    except Exception:  # noqa: BLE001 — telemetry only
        return ""


def r6_candidate_preflight(args, run_id: str, manifest, runtime_context: dict[str, str]):
    """R6 fail-closed provenance gate (docs/R6_EXPERIMENT_CONTRACT.md § 13–14).

    Before a single model call: the candidate's registry state must allow this split and
    run id; DEV/TEST need a clean tree; the SERVED system must be the registered one —
    `/props.build_info` == the runtime record's expected build, the served file's basename
    == the artifact's filename and its SHA-256 (re-hashed now) == the artifact's, and, once
    the execution system is frozen (TRAIN_COMPATIBLE), the live `/proc` server args and
    the generation config this run would send must digest to the frozen values. Every
    identity is stamped into `runtime_context` so each trajectory carries it. Returns
    (registry, identity) for the run ledger.
    """
    from fis_platform.provenance import (
        R6Registry, bind_running_server, build_generation_config, capture_server_args,
        default_root, llama_server_pids, require_state, sha256_file, tree_state,
    )
    if args.escalate_to:
        raise SystemExit("R6: --candidate runs are local-only; no cascade/frontier calls (contract § 1)")
    if args.split in ("dev", "test") and (args.limit or args.scenario_ids_file):
        raise SystemExit("R6: DEV/TEST are evaluated on the whole split — --limit / --scenario-ids-file "
                         "are TRAIN-only with --candidate")
    reg = R6Registry(default_root())
    ident = require_state(reg, args.candidate, args.split, run_id, args.resume)
    gh, code_clean, dirty = tree_state()
    runtime_context["code_tree_clean_except_registry"] = "true" if code_clean else "false"
    if dirty:
        runtime_context["dirty_paths_outside_registry"] = ",".join(dirty)[:500]
    if not code_clean:
        raise SystemExit(f"R6: candidate inference needs a committed code tree "
                         f"(git_head={gh!r}, dirty/untracked outside the registry: {dirty}); the only "
                         "paths allowed to be ahead of HEAD are the registry's own append-only "
                         "records under learning/registry/r6/ (contract § 14)")
    if manifest.provider.value != "local_llamacpp":
        raise SystemExit("R6: --candidate applies to local llama.cpp arms only")
    pids = llama_server_pids()
    if len(pids) != 1:
        raise SystemExit(f"R6: exactly one llama-server may be resident (found {pids}) — the "
                         "resource footprint is measured as the card total")
    artifact = reg.get_artifact(ident["identity"]["artifact_id"])
    runtime = reg.get_runtime(ident["identity"]["runtime_id"])
    if not runtime.build_info_expected:
        raise SystemExit(f"R6: runtime {runtime.runtime_id} has no build_info_expected — cannot bind")
    if runtime_context.get("llamacpp_build", "") != runtime.build_info_expected:
        raise SystemExit(f"R6: served build_info {runtime_context.get('llamacpp_build')!r} != registered "
                         f"runtime {runtime.runtime_id} ({runtime.build_info_expected!r}) — wrong binary")
    served_path = runtime_context.get("model_path", "")
    if not served_path or Path(served_path).name != artifact.filename:
        raise SystemExit(f"R6: served model_path {served_path!r} is not the registered artifact "
                         f"{artifact.artifact_id} ({artifact.filename})")
    served_sha = sha256_file(Path(served_path))
    if served_sha != artifact.sha256:
        raise SystemExit(f"R6: served file sha256 {served_sha} != registered {artifact.sha256} "
                         f"({artifact.artifact_id})")
    import re
    port = int((re.search(r":(\d+)", (manifest.base_url or "").rstrip("/").removesuffix("/v1")) or [None, "0"])[1])
    sargs = capture_server_args(port)
    if sargs is None:
        raise SystemExit(f"R6: no llama-server process found on port {port}")
    bound = bind_running_server(port, runtime)      # exe + mapped libs hash-match the record
    runtime_context["server_ld_library_path"] = bound["ld_library_path"]
    runtime_context["server_exe"] = bound["exe"]
    runtime_context["server_libs_bound"] = str(len(bound["checked"]))
    if bound["extra_libs"]:
        runtime_context["server_extra_libs"] = ",".join(f"{k}={v[:12]}" for k, v in sorted(bound["extra_libs"].items()))
    session = runtime_context.get("local_server_session", "")
    if not session:
        raise SystemExit("R6: could not identify the local server session (pid/start_ticks)")
    prior = ident.get("prior_start") or {}
    if prior and prior.get("local_server_session") and prior["local_server_session"] != session:
        raise SystemExit(f"R6: --resume would mix server sessions ({prior['local_server_session']} vs "
                         f"{session}); a {args.split.upper()} evaluation is one session (contract § 14)")
    if args.split in ("dev", "test") and not prior:
        # a DEV/TEST evaluation runs in a FRESH server session: one that no earlier ledger line
        # (any candidate, any split) has seen — so no TRAIN case can pre-warm its prompt cache.
        used = {ln.get("local_server_session") for ln in reg.read_ledger() if ln.get("local_server_session")}
        if session in used:
            raise SystemExit(f"R6: server session {session} already served an earlier run — "
                             f"{args.split.upper()} needs a fresh session (contract § 10)")
    genconf = build_generation_config(args.prompt, args.max_tokens)
    frozen = ident.get("execution_system") or {}
    if frozen:
        if sargs.server_args_digest != frozen["server_args_digest"]:
            raise SystemExit("R6: live server args differ from the frozen execution system:\n"
                             f"  live   {sargs.server_args_digest} {sargs.material}\n"
                             f"  frozen {frozen['server_args_digest']} {frozen.get('server_args_material')}")
        if genconf.record_digest != frozen["generation_config_digest"]:
            raise SystemExit(f"R6: generation config {genconf.record_digest} (prompt={args.prompt}, "
                             f"max_tokens={args.max_tokens}) != frozen {frozen['generation_config_digest']}")
        runtime_context["execution_system_digest"] = frozen["record_digest"]
    runtime_context.update({
        "candidate_id": ident["candidate_id"], "artifact_id": artifact.artifact_id,
        "artifact_sha256": artifact.sha256, "gguf_metadata_digest": artifact.gguf_metadata_digest,
        "runtime_id": runtime.runtime_id, "runtime_digest": runtime.record_digest,
        "server_args_digest": sargs.server_args_digest, "generation_config_digest": genconf.record_digest,
        "generation_config_id": genconf.genconfig_id, "gpu_mem_used_mib_start": gpu_mem_used_mib(),
    })
    return reg, ident


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


def load_manifests(conn, split: str, limit: int | None,
                   scenario_ids: list[str] | None = None) -> list[dict]:
    """The split's manifests in scenario-id order. `scenario_ids` (R6) restricts the
    run to a pre-registered subset — still constrained to `split`, so a TRAIN pilot
    list can never pull a DEV/TEST case in — and refuses ids the split does not hold
    rather than silently running fewer cases than the pilot record says."""
    sql = """
        SELECT scenario_id, seed, split, category, root_cause, required_evidence,
               acceptable_next_actions, forbidden_claims, distractor_event_ids,
               case_id, subject_ids
        FROM ground_truth.scenario_manifests
        WHERE split = %s
    """
    params: tuple = (split,)
    if scenario_ids:
        sql += " AND scenario_id = ANY(%s)"
        params += (list(scenario_ids),)
    sql += " ORDER BY scenario_id"
    if limit:
        sql += " LIMIT %s"
        params += (limit,)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
    if scenario_ids:
        missing = sorted(set(scenario_ids) - {r["scenario_id"] for r in rows})
        if missing:
            raise SystemExit(f"{len(missing)} requested scenario id(s) are not in split "
                             f"{split!r}: {missing[:5]}{'…' if len(missing) > 5 else ''}")
    return rows


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


def persist(conn, run_id: str, score, trajectory, result=None) -> None:
    """`result` (the parsed InvestigationResult, or None) is stored in
    `learning.model_outputs` since R5: the answer body is what a learned router reads,
    and every run before R5 kept only its sha256. Best-effort and after the score row —
    a persistence problem here must never lose a scored case."""
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
        if result is not None:
            try:
                with conn.transaction():   # a savepoint: failure here rolls back only itself
                    cur.execute(
                        """INSERT INTO learning.model_outputs (trace_id, run_id, scenario_id, output)
                           VALUES (%s,%s,%s,%s) ON CONFLICT (trace_id) DO NOTHING""",
                        (str(trajectory.trace_id), run_id, score.scenario_id,
                         Jsonb(json.loads(result.model_dump_json()))),
                    )
            except psycopg.Error as exc:  # e.g. a pre-007 database without the table
                print(f"    (model_outputs not persisted: {exc.__class__.__name__}; score kept)")
    conn.commit()


async def main() -> None:
    ap = argparse.ArgumentParser(description="Run a FIS experiment arm.")
    ap.add_argument("--arm", required=True, help="E2, E4, ... — recorded on every trajectory")
    ap.add_argument("--model-ref", required=True)
    ap.add_argument("--mode", choices=[m.value for m in EvidenceMode],
                    default=EvidenceMode.FIXED_EVIDENCE.value)
    ap.add_argument("--split", choices=[s.value for s in SeedSplit], default="test")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--scenario-ids-file", type=Path,
                    help="R6: run only these scenario ids (one per line; '#' comments), e.g. "
                         "the pre-registered TRAIN pilot from scripts/r6_pilot.py. Ids must "
                         "belong to --split.")
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
    ap.add_argument("--candidate", metavar="CANDIDATE_ID",
                    help="R6: the registered candidate (learning/registry/r6) this run evaluates. "
                         "Fail-closed: the run refuses to start unless the candidate's state allows "
                         "the split and the served model/binary/args match the frozen execution system.")
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
    if manifest.provider.value == "local_llamacpp" and not args.candidate:
        # R6: no local trajectory enters canonical storage without artifact + runtime identity;
        # the historical arms (local-specialist, nemotron-lightning) are replay-only now.
        raise SystemExit("R6: local llama.cpp arms require --candidate <registered candidate id> "
                         "(contract § 14); historical local arms are replay-only")
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

    r6_reg = r6_ident = None
    if args.candidate:
        r6_reg, r6_ident = r6_candidate_preflight(args, run_id, manifest, runtime_context)

    import time as _time
    run_started = _time.monotonic()
    with psycopg.connect(OWNER_DSN) as owner:
        guard_suite(owner, run_id, args.split, args.resume)
        runtime_context["corpus_digest"] = corpus_digest(owner)["digest"]
        scenario_ids = None
        if args.scenario_ids_file:
            scenario_ids = [ln.strip() for ln in args.scenario_ids_file.read_text().splitlines()
                            if ln.strip() and not ln.lstrip().startswith("#")]
            if not scenario_ids:
                raise SystemExit(f"--scenario-ids-file {args.scenario_ids_file} holds no ids")
            runtime_context["scenario_ids_file"] = str(args.scenario_ids_file)
            runtime_context["scenario_ids_digest"] = __import__("hashlib").sha256(
                "\n".join(scenario_ids).encode()).hexdigest()
        manifests = load_manifests(owner, args.split, args.limit, scenario_ids)
        done = already_done(owner, run_id) if args.resume else set()
        pending = [m for m in manifests if m["scenario_id"] not in done]

        print(f"run_id={run_id}  arm={args.arm}  model={args.model_ref}  mode={args.mode}")
        print(f"{len(manifests)} scenarios in split, {len(done)} already scored, "
              f"{len(pending)} to run")
        if r6_reg is not None:
            from fis_platform.provenance import begin_run
            if args.split in ("dev", "test"):
                # canonical storage is the authority on whether the look was spent
                with owner.cursor() as cur:
                    cur.execute(
                        """SELECT DISTINCT cs.run_id FROM learning.case_scores cs
                             JOIN learning.trajectories t ON t.trace_id = cs.trace_id
                             JOIN ground_truth.scenario_manifests m ON m.scenario_id = cs.scenario_id
                            WHERE t.payload->'runtime_context'->>'candidate_id' = %s AND m.split = %s""",
                        (args.candidate, args.split))
                    seen = {r[0] for r in cur.fetchall()}
                if seen - {run_id}:
                    raise SystemExit(f"R6: canonical storage already holds {args.split.upper()} rows for "
                                     f"{args.candidate} under {sorted(seen)} — the look is spent")
            begin_run(r6_reg, args.candidate, args.split, run_id, planned_cases=len(manifests),
                      extra={"pending": len(pending), "resume": bool(args.resume),
                             "max_tokens": args.max_tokens, "prompt": args.prompt,
                             "scenario_ids_digest": runtime_context.get("scenario_ids_digest", ""),
                             "local_server_session": runtime_context.get("local_server_session", "")})
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
            if r6_reg is not None:
                runtime_context["gpu_mem_used_mib_now"] = gpu_mem_used_mib()
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
            persist(owner, run_id, score, traj, result)   # commit per case: resume stays exact

            route = ""
            if out is not None:
                # The weak stage is scored and persisted under its own run id so the
                # eval can count unnecessary escalations and false accepts later.
                # Same trajectory when the weak result was accepted; a separate one
                # (its own trace_id) when the cascade escalated.
                weak_score = score_case(result=out.weak_result, trajectory=out.weak_trajectory,
                                        manifest=m, run_id=f"{run_id}.weak")
                persist(owner, f"{run_id}.weak", weak_score, out.weak_trajectory, out.weak_result)
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
    if r6_reg is not None:
        from fis_platform.provenance import end_run
        end_run(r6_reg, args.candidate, run_id, cases_done=len(run.scores),
                wall_s=round(_time.monotonic() - run_started, 1),
                extra={"all_pass": sum(1 for sc in run.scores if sc.all_pass),
                       "gpu_mem_used_mib_end": gpu_mem_used_mib()})


def _pct(v: float | None) -> str:
    return "n/a" if v is None else f"{v * 100:.1f}%"


if __name__ == "__main__":
    asyncio.run(main())
