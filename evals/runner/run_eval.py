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
from typing import Any, Callable

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv  # noqa: E402

from evals.scorers.score import SCORER_VERSION, score_case  # noqa: E402
from fis_platform.model_gateway import ModelGateway, default_registry  # noqa: E402
from fis_platform.ordering import class_of, round_robin_rows  # noqa: E402
from fis_platform.provenance import SMOKE_TOTAL_CASES  # noqa: E402
from fis_platform.routing.learn import digest as content_digest  # noqa: E402
from fis_platform.suite import (  # noqa: E402
    ONTOLOGY_VERSION, SUITE_VERSION, SuiteMismatch, corpus_suite, git_head, suite_of_run,
)
from fis_platform.telemetry import ResourceSampler, RunEventLog  # noqa: E402
from fis_platform.test_looks import LookRefused, TestLookLedger, validate_mirror  # noqa: E402
from fis_platform.tolerances import (  # noqa: E402
    Consequence, CurtailmentPolicy, ToleranceSpec, ToleranceTracker,
    append_curtailed_run, make_curtailment_report,
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


def r6_candidate_preflight(args, run_id: str, manifest, runtime_context: dict[str, str],
                           kind: str = "eval"):
    """R6 fail-closed provenance gate (docs/R6_EXPERIMENT_CONTRACT.md § 13–14).

    Before a single model call: the candidate's registry state must allow this split and
    run id; DEV/TEST need a clean tree; the SERVED system must be the registered one —
    `/props.build_info` == the runtime record's expected build, the served file's basename
    == the artifact's filename and its SHA-256 (re-hashed now) == the artifact's, and, once
    the execution system is frozen (TRAIN_COMPATIBLE), the live `/proc` server args and
    the generation config this run would send must digest to the frozen values. Every
    identity is stamped into `runtime_context` so each trajectory carries it. Returns
    (registry, identity) for the run ledger.

    `kind` (default "eval") is passed straight through to `require_state`; `--smoke`
    passes `kind="smoke"` so `require_state` runs its SMOKE branch (train-only, state
    must be SMOKE exactly) instead of the ordinary TRAIN/DEV/TEST rules. Every other
    check below runs unconditionally — SMOKE is served/hashed/session-bound exactly
    like an ordinary TRAIN run, it just measures a different split of the population.
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
    ident = require_state(reg, args.candidate, args.split, run_id, args.resume, kind=kind)
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


def load_manifests(conn, split: str, scenario_ids: list[str] | None = None) -> list[dict]:
    """The split's manifests, in the DB's own scenario-id order (deterministic
    retrieval only — NOT the run's execution order; see `apply_ordering`, called
    right after this). `scenario_ids` (R6) restricts the run to a pre-registered
    subset — still constrained to `split`, so a TRAIN pilot list can never pull a
    DEV/TEST case in — and refuses ids the split does not hold rather than silently
    running fewer cases than the pilot record says.

    No `LIMIT` here (playbook §4, M-STAT map §4): a SQL-side prefix would take the
    *first N by scenario_id* — i.e. by class, since ids sort class-major — which is
    exactly the class-blocked prefix `apply_ordering` replaces. Truncation now
    happens in Python, on the round-robin order, after this function returns.
    """
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
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
    if scenario_ids:
        missing = sorted(set(scenario_ids) - {r["scenario_id"] for r in rows})
        if missing:
            raise SystemExit(f"{len(missing)} requested scenario id(s) are not in split "
                             f"{split!r}: {missing[:5]}{'…' if len(missing) > 5 else ''}")
    return rows


def apply_ordering(manifests: list[dict], limit: int | None) -> list[dict]:
    """The runner's ONLY execution-order + prefix-selection step (playbook §4,
    M-STAT implementation map §4): canonical class-balanced round-robin order,
    truncated to `limit` AFTER ordering, never before.

    Consequence (deliberate): `--limit N` is now a class-balanced round-robin
    prefix. The old class-blocked prefix (`ORDER BY scenario_id` truncated by a SQL
    `LIMIT`, measured 5.4x worse as a prefix estimate) is not merely discouraged —
    `load_manifests` no longer has a SQL `LIMIT` branch, so that code path does not
    exist to be reached by any caller, correct or otherwise. This applies to every
    split, not just TRAIN: DEV/TEST curtailment arithmetic (`fis_platform.
    tolerances.CurtailmentPolicy`) also reads a prefix of `cases_done`, so an
    unrepresentative prefix would bias curtailment decisions the same way it biases
    a TRAIN screening pilot.

    Comparability boundary (playbook §4; `fis_platform/ordering.py` module
    docstring): changing execution order changes each case's prompt-cache
    predecessor within a local llama.cpp server session — a documented source of
    within-session nondeterminism. A round-robin run therefore does not share
    predecessor structure, case for case, with a historical class-blocked run over
    the same scenario ids; case-level comparisons between the two are descriptive
    only, never a paired statistical claim.
    """
    return round_robin_rows(manifests)[:limit]


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


def check_corpus_pinned(live_digest: str) -> None:
    """Fail-closed corpus identity (M-STAT map §8): `live_digest` (the DB's own
    `corpus_digest(conn)["digest"]`, already computed at run start) must match the
    PINNED identity recorded at `scenarios/manifests/corpus_v{SUITE_VERSION}.json`
    (written once, by `scripts/corpus_digest.py --write`, at suite release time).

    Before this, the live digest was recorded on every trajectory's
    `runtime_context` but never compared to anything — a corpus that drifted (a bad
    migration, a partial regeneration, a manual row edit) would score silently
    against the wrong worlds, discovered only by someone reading the recorded
    digest later and noticing it looked wrong. Both a digest mismatch and a missing
    pinned manifest are refused: a suite with no pinned identity to check against is
    not verified, not merely unverified-but-fine.
    """
    manifest_path = ROOT / "scenarios" / "manifests" / f"corpus_v{SUITE_VERSION}.json"
    if not manifest_path.exists():
        raise SuiteMismatch(
            f"no pinned corpus manifest at {manifest_path} for suite {SUITE_VERSION!r} — "
            f"live corpus digest is {live_digest}, but there is nothing pinned to verify it "
            "against (run `scripts/corpus_digest.py --write` at suite release time)")
    pinned = json.loads(manifest_path.read_text(encoding="utf-8"))
    pinned_digest = pinned.get("corpus_digest")
    if pinned_digest != live_digest:
        raise SuiteMismatch(
            f"corpus digest mismatch: live digest {live_digest} != pinned digest "
            f"{pinned_digest!r} ({manifest_path}) — the corpus in the database has drifted "
            f"from the suite-{SUITE_VERSION} identity this code was pinned against")


def validate_smoke_args(args) -> None:
    """Fail-closed guards for `--smoke`, checkable with no DB connection (extracted so
    the test suite can drive every refusal directly against a parsed `args`, the same
    way `apply_ordering`/`check_corpus_pinned` are driven directly elsewhere in this
    module). Mirrors `require_state`'s smoke branch (TRAIN-only, run id must say
    "smoke") but fires here first, at arg-validation time, before a connection or a
    model call — `require_state` still enforces its own copy independently.

    A no-op when `--smoke` was not passed at all.
    """
    if not getattr(args, "smoke", False):
        return
    if not args.candidate:
        raise SystemExit("--smoke requires --candidate — SMOKE is a per-candidate lifecycle "
                         "gate (playbook §3), not a bare model probe")
    if args.split != "train":
        raise SystemExit(f"--smoke is TRAIN-only (got --split {args.split!r}) — SMOKE measures "
                         "the fixed 36-case population before any REGISTERED work opens")
    if args.limit is not None:
        raise SystemExit("--smoke refuses --limit — the canonical 36-case population may not "
                         "be subset")
    if args.scenario_ids_file is not None:
        raise SystemExit("--smoke refuses --scenario-ids-file — the canonical 36 may not be "
                         "substituted")
    if args.escalate_to:
        raise SystemExit("--smoke refuses --escalate-to — the canonical 36 may not be cascaded")
    if args.tolerance_spec is not None:
        raise SystemExit("--smoke refuses --tolerance-spec — SMOKE may not be wrapped in "
                         "tolerance machinery")
    if args.curtail_bar is not None:
        raise SystemExit("--smoke refuses --curtail-bar — SMOKE may not be wrapped in "
                         "curtailment machinery")
    run_id = args.run_id or f"{args.arm}-{args.model_ref}-{args.split}"
    if "smoke" not in run_id.lower():
        raise SystemExit(f"--smoke run id {run_id!r} must contain 'smoke' — run ids are how "
                         "the ledger tells run kinds apart (require_state enforces this too, "
                         "but --smoke fails fast here)")


def reconstruct_smoke_cases(conn, run_id: str,
                            scenario_ids: set[str]) -> dict[str, dict[str, Any]]:
    """`--resume`'s reconstruction of already-persisted SMOKE case evidence, keyed by
    scenario_id (canonical storage — `learning.case_scores` joined to
    `learning.trajectories` — is the authority, not in-memory state from a crashed
    process). Same pattern as `reconstruct_tolerance_trackers`: a trajectory's payload
    carries `tool_calls[].status` and `model_invocations`, which is exactly the raw
    evidence `smoke_case_flags` needs.
    """
    if not scenario_ids:
        return {}
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT cs.scenario_id AS scenario_id, cs.all_pass AS all_pass,
                      t.payload AS payload
                 FROM learning.case_scores cs
                 JOIN learning.trajectories t ON t.trace_id = cs.trace_id
                WHERE cs.run_id = %s""",
            (run_id,))
        rows = cur.fetchall()
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        if r["scenario_id"] not in scenario_ids:
            continue
        payload = r["payload"]
        tool_calls = payload.get("tool_calls") or []
        model_invocations = payload.get("model_invocations") or []
        out[r["scenario_id"]] = {
            "scenario_id": r["scenario_id"],
            "trace_id": str(payload.get("trace_id", "")),
            "tool_call_statuses": [c.get("status") for c in tool_calls],
            "n_model_invocations": len(model_invocations),
            "all_pass": bool(r["all_pass"]),
        }
    return out


def test_look_gate(split: str, run_id: str, resume: bool, ledger_path: Path | None = None,
                   mirror_path: Path | None = None) -> TestLookLedger | None:
    """The machine TEST-look gate (playbook §1; M-STAT map §7) — consulted for
    EVERY arm, local or frontier, before a single case executes. Closes the
    frontier bypass: the pre-M-STAT gate (`r6_candidate_preflight`) only ever ran
    for `--candidate` (local llama.cpp) arms, so a frontier-model TEST run was
    ungated. This function takes no provider/candidate argument at all — it cannot
    be, because nothing about "which model" is relevant to whether a TEST look was
    planned.

    Returns `None` immediately for TRAIN/DEV — a TEST-look ledger has nothing to
    say about a split it does not gate. For TEST: constructs the ledger at
    `ledger_path` (default the live `learning/registry/test_looks.jsonl`),
    validates the human-readable mirror at `mirror_path` (default the live
    `docs/current/TEST_LOOK_LEDGER.md`) against it — a diverged mirror refuses
    before anything else, since a divergence means the record of record itself is
    in a state nobody has reconciled yet — then requires a planned look for
    `(SUITE_VERSION, run_id)` (`require_planned`, which itself re-checks the
    look-#8 trigger-review requirement at consumption time, not just at plan time).
    Any of these refusals is a `LookRefused`/`MirrorDivergence` `SystemExit`.

    `resume` is accepted for interface symmetry with the runner's other TEST-path
    guards (`r6_candidate_preflight` takes `args`, `resume` included) but is not
    branched on here: `require_planned` must hold whether this is a fresh run or a
    resume of one already spent — the ledger's own `record_spend` is what makes
    resuming a spent run safe (idempotent per `run_id`), not this gate relaxing.
    """
    if split != "test":
        return None
    ledger = TestLookLedger(ledger_path or ROOT / "learning" / "registry" / "test_looks.jsonl")
    validate_mirror(ledger.path, mirror_path or ROOT / "docs" / "current" / "TEST_LOOK_LEDGER.md")
    ledger.require_planned(SUITE_VERSION, run_id)
    return ledger


# --------------------------------------------------------- consequence-bearing tolerances

def _tolerance_cap_hit(ctx: dict[str, Any]) -> bool:
    """Violation iff the case's FIRST model invocation stopped for hitting the
    output-token cap (`stop_reason == "length"`). A case that raised before any
    invocation completed is never a cap_hit — `ctx["stop_reason"]` is `None` there,
    which compares unequal to `"length"`."""
    return ctx.get("stop_reason") == "length"


def _tolerance_case_fail(ctx: dict[str, Any]) -> bool:
    """Violation iff the case did not score `all_pass` — INCLUDING a case that
    raised an exception before it could be scored at all: a case that never scored
    plainly did not pass either. Only the `"exception"` metric distinguishes the
    two failure shapes from each other; `case_fail` counts both as one."""
    return bool(ctx.get("exception")) or ctx.get("all_pass") is False


def _tolerance_exception(ctx: dict[str, Any]) -> bool:
    """Violation iff the case raised before it could be scored."""
    return bool(ctx.get("exception"))


TOLERANCE_METRICS: dict[str, Callable[[dict[str, Any]], bool]] = {
    "cap_hit": _tolerance_cap_hit,
    "case_fail": _tolerance_case_fail,
    "exception": _tolerance_exception,
}


class UnknownToleranceMetric(SystemExit):
    """A `--tolerance-spec` entry named a `metric` outside `TOLERANCE_METRICS`.
    Refused at load time, before any case runs — a tolerance the runner cannot
    evaluate is not a pre-registered tolerance, it is a promise with no mechanism,
    which is the exact class of defect this module closes (module docstring)."""


def load_tolerance_specs(path: Path) -> list[ToleranceSpec]:
    """`--tolerance-spec`'s JSON list, parsed into `ToleranceSpec` objects.

    Construction is fail-closed per `fis_platform.tolerances` itself (a spec naming
    RECALIBRATE with no procedure, or PROCEED_WITH_DECLARED_CEILING with no priced
    ceiling, refuses to construct at all — a `pydantic.ValidationError`). The one
    check this function adds on top is metric support: a spec naming a `metric` not
    in `TOLERANCE_METRICS` is refused here, by name, before any case runs — never
    discovered case-by-case as a `KeyError` mid-run.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise SystemExit(f"--tolerance-spec {path}: expected a JSON list of tolerance specs")
    specs = [ToleranceSpec(**entry) for entry in raw]
    unknown = [(s.spec_id, s.metric) for s in specs if s.metric not in TOLERANCE_METRICS]
    if unknown:
        raise UnknownToleranceMetric(
            f"--tolerance-spec {path}: unsupported metric(s) {unknown} — supported metrics "
            f"are {sorted(TOLERANCE_METRICS)}")
    return specs


def reconstruct_tolerance_trackers(conn, run_id: str,
                                   specs: list[ToleranceSpec]) -> dict[str, ToleranceTracker]:
    """`--resume`'s reconstruction of every tolerance tracker from already-persisted
    rows for `run_id` (canonical storage — `learning.case_scores` joined to
    `learning.trajectories` — is the authority here, not any in-memory state from
    the crashed process).

    Refuses FIRST, before any query, if any spec's metric is `"exception"`: an
    excepted case is never persisted (there is no `case_scores`/`trajectories` row
    for it — `persist()` is only ever called after a case scores), so the exception
    count from before the resume boundary is not recoverable from canonical
    storage. Resuming would silently under-count violations for that tolerance
    rather than fail closed, so this refuses instead and says restart.

    `case_fail`/`cap_hit` reconstruction has the same blind spot in one respect: an
    excepted case also does not persisted-reconstruct as a `case_fail` violation
    (live-loop `_tolerance_case_fail` counts an exception as a failure; a resumed
    tracker, having no row for it, cannot). This is a known, narrower gap than the
    `exception` metric's — it under-counts by excepted cases only, never fabricates
    a pass — and is not fixed here; a contract relying on exact `case_fail`
    reconstruction across a resume boundary with prior exceptions should know this.
    """
    exception_specs = [s.spec_id for s in specs if s.metric == "exception"]
    if exception_specs:
        raise SystemExit(
            f"--resume refused: tolerance spec(s) {exception_specs} use metric='exception', "
            "which cannot be reconstructed from canonical storage (an excepted case is never "
            "persisted, so its violation is not recoverable) — restart the run instead of "
            "resuming it")
    trackers: dict[str, ToleranceTracker] = {}
    if not specs:
        return trackers
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT cs.id AS id, cs.all_pass AS all_pass,
                      t.payload->'model_invocations'->0->>'stop_reason' AS stop_reason
                 FROM learning.case_scores cs
                 JOIN learning.trajectories t ON t.trace_id = cs.trace_id
                WHERE cs.run_id = %s
                ORDER BY cs.id""",
            (run_id,))
        rows = cur.fetchall()
    for spec in specs:
        extractor = TOLERANCE_METRICS[spec.metric]
        violations = [extractor({"exception": False, "stop_reason": r["stop_reason"],
                                 "all_pass": r["all_pass"]}) for r in rows]
        trackers[spec.spec_id] = ToleranceTracker.from_persisted(spec, violations)
    return trackers


def apply_tolerance_consequence(
    consequence: Consequence,
    tracker: ToleranceTracker,
    events: RunEventLog,
    *,
    candidate_end_run: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    """Dispatch ONE crossing of a pre-registered tolerance (playbook §5). Callers
    invoke this only when `tracker.observe(...)` just returned non-`None` — i.e.
    exactly once per tolerance, on the (k+1)-th violation — so the
    `tolerance_consequence` event this writes is written exactly once by
    construction, never by caller discipline.

    ABORT and RECALIBRATE halt the run in the same shape: the consequence event,
    a `run_end` naming the halt status, the same payload folded into `end_run`
    extra for a `--candidate` run (never "curtail now, finish later" — the
    tolerance fired, the run is over), and a `SystemExit` naming the spec so the
    exit message alone says which tolerance and which consequence fired.
    RECALIBRATE additionally prints the pre-registered `recalibration_procedure` —
    the runner never improvises one. PROCEED_WITH_DECLARED_CEILING records the
    event (with its priced ceiling) and returns normally, so the loop continues:
    the R6 defect this module exists to close was an UNPRICED silent default, not
    the act of proceeding itself.
    """
    action = tracker.to_consequence_action()
    events.event("tolerance_consequence", **action.model_dump(mode="json"))
    if consequence is Consequence.PROCEED_WITH_DECLARED_CEILING:
        print(f"    tolerance {action.spec_id!r}: PROCEED_WITH_DECLARED_CEILING — "
             f"declared_ceiling={action.declared_ceiling!r} projected_cost={action.projected_cost!r}")
        return
    status = "aborted-tolerance" if consequence is Consequence.ABORT else "halted-recalibrate"
    events.run_end(status=status, tolerance_spec_id=action.spec_id, at_violation=action.at_violation)
    if candidate_end_run is not None:
        candidate_end_run({"tolerance_consequence": action.model_dump(mode="json")})
    if consequence is Consequence.RECALIBRATE:
        print(f"    tolerance {action.spec_id!r}: RECALIBRATE — pre-registered procedure: "
             f"{action.recalibration_procedure}")
        raise SystemExit(
            f"tolerance {action.spec_id!r} breached ({action.at_violation} violations of a "
            f"<={tracker.spec.max_violations} bar) — RECALIBRATE: re-derive the calibrated "
            "parameter per the pre-registered procedure above, then re-freeze before "
            "continuing (the runner never improvises a recalibration)")
    raise SystemExit(
        f"tolerance {action.spec_id!r} breached ({action.at_violation} violations of a "
        f"<={tracker.spec.max_violations} bar) — ABORT: the run halted, the experiment "
        "returns to design (playbook §5)")


def observe_tolerances(trackers: dict[str, ToleranceTracker], ctx: dict[str, Any], *,
                       events: RunEventLog,
                       candidate_end_run: Callable[[dict[str, Any]], None] | None = None) -> None:
    """One case's outcome (`ctx` — the shape `TOLERANCE_METRICS` extractors read:
    `exception`/`stop_reason`/`all_pass`), fed to every active tolerance tracker via
    its own metric's extractor. `ToleranceTracker.observe` returns the consequence
    exactly once, on the crossing call, so `apply_tolerance_consequence` (which can
    raise `SystemExit`) is only ever invoked at that one call per tracker.
    """
    for tracker in trackers.values():
        violation = TOLERANCE_METRICS[tracker.spec.metric](ctx)
        consequence = tracker.observe(violation)
        if consequence is not None:
            apply_tolerance_consequence(consequence, tracker, events,
                                        candidate_end_run=candidate_end_run)


# ------------------------------------------------------------------- certainty curtailment

def curtail_and_exit(
    policy: CurtailmentPolicy, passes: int, cases_done: int, *, run_id: str, split: str, arm: str,
    remaining_manifests: list[dict], events: RunEventLog, curtailed_runs_path: Path,
    candidate_end_run: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    """Certainty curtailment (playbook §6). Called once `policy.should_curtail(passes,
    cases_done)` is true: even a clean sweep of every remaining case cannot reach
    the pre-registered bar, so the arm is irreversibly rejected (guard 1 — spend
    semantics: the split is already spent, there is no "curtail now, finish later").

    Writes the INTERVAL-ONLY report (guard 2 — never a partial point estimate) via
    `append_curtailed_run` to `curtailed_runs_path`, emits a `curtailed` event and a
    `run_end(status="curtailed")`, folds the same interval + unrun classes into
    `end_run` extra for a `--candidate` run, prints ONLY the certain interval
    `[passes, passes+remaining]/n_total` and the unrun classes (never a rate), and
    raises `SystemExit`. `remaining_manifests` are the NOT-YET-ATTEMPTED manifests —
    their scenario classes are what `unrun_classes` reports (guard 3, the paired
    firewall, is enforced by the tools that CONSULT `curtailed_runs_path`, not here
    — see the `fis_platform.tolerances` module docstring).
    """
    unrun_classes = sorted({class_of(m["scenario_id"]) for m in remaining_manifests})
    report = make_curtailment_report(run_id=run_id, split=split, arm=arm, passes=passes,
                                     cases_done=cases_done, n_total=policy.n_total,
                                     bar=policy.bar, unrun_classes=unrun_classes)
    append_curtailed_run(curtailed_runs_path, report)
    events.event("curtailed", **report)
    events.run_end(status="curtailed", passes=passes, cases_done=cases_done)
    if candidate_end_run is not None:
        candidate_end_run({"curtailed": True, "certain_interval": report["interval"],
                           "unrun_classes": unrun_classes})
    lo, hi = report["interval"]
    print(f"\nCURTAILED (bar={policy.bar}, n_total={policy.n_total}): "
         f"certain interval [{lo}, {hi}]/{policy.n_total}; unrun classes: {unrun_classes}")
    raise SystemExit(
        f"run {run_id!r} curtailed at cases_done={cases_done} — arm {arm!r} cannot reach "
        f"bar={policy.bar} even with a clean sweep of the remaining cases (guard 1: this arm "
        "is irreversibly rejected, not paused)")


# ---------------------------------------- Finding 2: the TEST-write choke point in persist()
#
# `test_look_gate` (above) fires only from `main()` — a future script that imports
# `persist()` directly (as `scripts/m0_paired_probe.py` already does) could write a
# TEST-split `case_scores` row completely unledgered. This is the second, independent
# guard: it lives INSIDE `persist()`, the one function every write path shares, so it
# cannot be bypassed by skipping `main()`.

# scenarios/generator/run.py:55-58 SPLIT_RANGES — inlined here, not imported, so this
# module never has to import the generator to derive a split. TEST is the disjoint
# seed range 3_000_000..3_999_999.
_TEST_SEED_LO, _TEST_SEED_HI = 3_000_000, 3_999_999

# The default TEST-look ledger location — the same value `fis_platform.test_looks.
# default_path()` returns, restated as a module-level constant here (the `tolerances.
# CURTAILED_RUNS_PATH` pattern) so a test can monkeypatch it and have every call site
# that omits an explicit path see the redirected ledger. Resolved fresh inside
# `_require_test_look_planned_or_spent` on every call, never bound into a parameter
# default.
TEST_LOOK_LEDGER_PATH = ROOT / "learning" / "registry" / "test_looks.jsonl"

# One ledger read per (base) run id, not one per case — a TEST run persists dozens to
# hundreds of cases through the same run_id, and the ledger only needs to be asked once.
_test_look_verdict_cache: dict[str, bool] = {}


def _seed_from_scenario_id(scenario_id: str) -> int:
    """The seed out of a `Sxx-NNNNNNN` scenario id — no DB, no
    `scenarios.generator` import (see the comment above `_TEST_SEED_LO`)."""
    return int(scenario_id.split("-")[1])


def _require_test_look_planned_or_spent(run_id: str) -> None:
    """Fail-closed: `run_id` (or, for a `.weak` id, its base id) must hold a
    `planned` or `spent` entry in the TEST-look ledger, or this raises `LookRefused`.

    A run id ending `.weak` is checked under its base id — the cascade's weak stage
    is scored and persisted under `f"{run_id}.weak"`, but it is spent within the SAME
    counted TEST look as the strong arm (`docs/current/TEST_LOOK_LEDGER.md`'s
    counting convention), so it never plans (or spends) a look of its own.

    `planned` is accepted, not just `spent`, because the runner's own `record_spend`
    call (`main()`, at the first case) may not have landed yet the very first time
    `persist()` runs for a fresh TEST run — a planned-but-not-yet-spent look is still
    a real, pre-registered TEST look, just not yet exercised.
    """
    base_run_id = run_id[:-len(".weak")] if run_id.endswith(".weak") else run_id
    if base_run_id in _test_look_verdict_cache:
        ok = _test_look_verdict_cache[base_run_id]
    else:
        entries = TestLookLedger(TEST_LOOK_LEDGER_PATH).read()
        ok = any(e.get("run_id") == base_run_id and e.get("kind") in ("planned", "spent")
                for e in entries)
        _test_look_verdict_cache[base_run_id] = ok
    if not ok:
        raise LookRefused(
            f"persist() refused: run {base_run_id!r} has no planned or spent TEST look in "
            f"{TEST_LOOK_LEDGER_PATH} — TEST-split case_scores may not be written off the "
            "runner's own gate (fail closed: no plan, no TEST)")


def persist(conn, run_id: str, score, trajectory, result=None) -> None:
    """`result` (the parsed InvestigationResult, or None) is stored in
    `learning.model_outputs` since R5: the answer body is what a learned router reads,
    and every run before R5 kept only its sha256. Best-effort and after the score row —
    a persistence problem here must never lose a scored case.

    Fail-closed FIRST, before `conn` is touched at all (Finding 2, above): if
    `score.scenario_id`'s seed falls in the TEST range, `run_id` (or its `.weak` base)
    must already hold a planned or spent TEST look, or this raises `LookRefused`."""
    seed = _seed_from_scenario_id(score.scenario_id)
    if _TEST_SEED_LO <= seed <= _TEST_SEED_HI:
        _require_test_look_planned_or_spent(run_id)
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


def build_arg_parser() -> argparse.ArgumentParser:
    """The production CLI parser, extracted from `main()` so tests can build a real
    `args` (defaults included) with no DB and no event loop — the same pattern
    `scripts/r6_registry.py`'s `build_parser()` uses."""
    ap = argparse.ArgumentParser(description="Run a FIS experiment arm.")
    ap.add_argument("--arm", required=True, help="E2, E4, ... — recorded on every trajectory")
    ap.add_argument("--model-ref", required=True)
    ap.add_argument("--mode", choices=[m.value for m in EvidenceMode],
                    default=EvidenceMode.FIXED_EVIDENCE.value)
    ap.add_argument("--split", choices=[s.value for s in SeedSplit], required=True,
                    help="TRAIN/DEV/TEST. Required — a bare invocation must never silently "
                         "default to TEST (M-STAT map §7: the historical default made an "
                         "unledgered TEST look one missing flag away).")
    ap.add_argument("--limit", type=int,
                    help="Prefix size, applied AFTER round-robin ordering (playbook §4) — a "
                         "class-balanced prefix. The old class-blocked SQL-LIMIT prefix path "
                         "no longer exists (see apply_ordering).")
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
    ap.add_argument("--tolerance-spec", type=Path, metavar="PATH.JSON",
                    help="Playbook §5: JSON list of pre-registered ToleranceSpec dicts. "
                         "In-run curtailed exact counting to violation k+1, per case; a "
                         "breach dispatches its named consequence (ABORT / RECALIBRATE / "
                         "PROCEED_WITH_DECLARED_CEILING) — never a silent default.")
    ap.add_argument("--curtail-bar", type=float, metavar="0..1",
                    help="Playbook §6: certainty curtailment. Abort this arm the instant its "
                         "remaining cases cannot reach ceil(bar * n_total) passes; reports "
                         "the certain interval only, never a point estimate.")
    ap.add_argument("--smoke", action="store_true",
                    help=f"R6/playbook §3: run the fixed {SMOKE_TOTAL_CASES}-case SMOKE "
                         "population instead of the ordinary split content. TRAIN-only, "
                         "requires --candidate, and refuses --limit/--scenario-ids-file/"
                         "--escalate-to/--tolerance-spec/--curtail-bar — the canonical "
                         "population may not be substituted, subset, cascaded, or wrapped in "
                         "other machinery (validate_smoke_args).")
    return ap


async def main() -> None:
    args = build_arg_parser().parse_args()
    if args.max_tokens < 256:
        raise SystemExit(f"--max-tokens {args.max_tokens} is below the manifest minimum (256)")
    validate_smoke_args(args)   # fail-closed, before a connection or a model call

    # Parsed and metric-checked before anything else runs (E): a spec this runner
    # cannot evaluate is refused by name now, not discovered case-by-case mid-run.
    tolerance_specs = load_tolerance_specs(args.tolerance_spec) if args.tolerance_spec else []

    run_id = args.run_id or f"{args.arm}-{args.model_ref}-{args.split}"

    # The machine TEST-look gate (C): consulted for EVERY arm, before any model
    # execution, regardless of provider or --candidate. Returns None on TRAIN/DEV.
    test_look_ledger = test_look_gate(args.split, run_id, args.resume)

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
        r6_reg, r6_ident = r6_candidate_preflight(args, run_id, manifest, runtime_context,
                                                  kind="smoke" if args.smoke else "eval")

    # The suite a score is measured against is `fis_platform.suite.SUITE_VERSION`
    # (v2: the event migration; v3: the four benchmark-defect fixes of
    # SUITE_V3_RELEASE_CONTRACT.md). Numbers are never comparable across it.
    # Computed here (G) — BEFORE the RunEventLog below — so the digest can be part
    # of that log's context from its very first line, not reconstructed later.
    digest = config_digest(model_ref=args.model_ref, mode=args.mode, prompt=args.prompt,
                           escalate_to=args.escalate_to, escalation_policy=args.escalation_policy,
                           strong_prompt=args.strong_prompt, max_tokens=args.max_tokens)

    import time as _time
    run_started = _time.monotonic()
    with psycopg.connect(OWNER_DSN) as owner:
        guard_suite(owner, run_id, args.split, args.resume)
        runtime_context["corpus_digest"] = corpus_digest(owner)["digest"]
        check_corpus_pinned(runtime_context["corpus_digest"])   # D: fail-closed pinned identity
        scenario_ids = None
        if args.scenario_ids_file:
            scenario_ids = [ln.strip() for ln in args.scenario_ids_file.read_text().splitlines()
                            if ln.strip() and not ln.lstrip().startswith("#")]
            if not scenario_ids:
                raise SystemExit(f"--scenario-ids-file {args.scenario_ids_file} holds no ids")
            runtime_context["scenario_ids_file"] = str(args.scenario_ids_file)
            runtime_context["scenario_ids_digest"] = __import__("hashlib").sha256(
                "\n".join(scenario_ids).encode()).hexdigest()
        canonical_smoke_ids: list[str] | None = None
        if args.smoke:
            # The canonical 36-case SMOKE population (playbook §3): selected from every
            # TRAIN scenario id in the DB, never a caller-supplied subset.
            from fis_platform.provenance import smoke_case_selection
            with owner.cursor() as cur:
                cur.execute("SELECT scenario_id FROM ground_truth.scenario_manifests "
                           "WHERE split = 'train'")
                train_ids = [r[0] for r in cur.fetchall()]
            canonical_smoke_ids = smoke_case_selection(train_ids)
            manifests = load_manifests(owner, args.split, canonical_smoke_ids)
            manifests = apply_ordering(manifests, None)
            if [m["scenario_id"] for m in manifests] != canonical_smoke_ids:
                raise SystemExit(
                    "R6: SMOKE manifest ordering diverges from the canonical selection — "
                    "refusing (smoke_case_selection and apply_ordering both use round_robin, "
                    "so this should be unreachable)")
            runtime_context["smoke_case_digest"] = content_digest(canonical_smoke_ids)
        else:
            manifests = load_manifests(owner, args.split, scenario_ids)
            # B: canonical class-balanced round-robin order + prefix, right after load —
            # see apply_ordering's docstring for the consequence and the comparability
            # boundary (playbook §4).
            manifests = apply_ordering(manifests, args.limit)
        runtime_context["ordering"] = "round_robin"
        done = already_done(owner, run_id) if args.resume else set()
        pending = [m for m in manifests if m["scenario_id"] not in done]

        # SMOKE-only: per-case harness evidence, reconstructed from canonical storage for
        # already-persisted (resumed) cases and collected in memory for the rest, then
        # assembled into the SMOKE result record once (and only if) all 36 have scored.
        smoke_case_evidence: dict[str, dict[str, Any]] = {}
        if args.smoke and args.resume and done:
            smoke_case_evidence.update(reconstruct_smoke_cases(owner, run_id, done))

        # E: reconstruct trackers from persisted rows on --resume; fresh otherwise.
        tolerance_trackers = (reconstruct_tolerance_trackers(owner, run_id, tolerance_specs)
                              if args.resume else
                              {s.spec_id: ToleranceTracker(s) for s in tolerance_specs})

        # F: certainty curtailment. passes/cases_done include resumed rows — counted
        # from the DB, not from `done` (which is scenario ids, not a pass count).
        curtailment_policy = None
        passes = cases_done = 0
        if args.curtail_bar is not None:
            curtailment_policy = CurtailmentPolicy(bar=args.curtail_bar, n_total=len(manifests))
            with owner.cursor() as cur:
                cur.execute(
                    "SELECT count(*) FILTER (WHERE all_pass), count(*) "
                    "FROM learning.case_scores WHERE run_id = %s", (run_id,))
                passes, cases_done = cur.fetchone()

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
            begin_extra = {"pending": len(pending), "resume": bool(args.resume),
                          "max_tokens": args.max_tokens, "prompt": args.prompt,
                          "scenario_ids_digest": runtime_context.get("scenario_ids_digest", ""),
                          "local_server_session": runtime_context.get("local_server_session", "")}
            if args.smoke:
                begin_extra["smoke_case_digest"] = runtime_context.get("smoke_case_digest", "")
            begin_run(r6_reg, args.candidate, args.split, run_id, planned_cases=len(manifests),
                      kind="smoke" if args.smoke else "eval", extra=begin_extra)
        print("runtime: " + "  ".join(f"{k}={v}" for k, v in runtime_context.items()
                                     if k not in ("run_id", "model_ref", "prompt")) + "\n")

        # M0 telemetry floor (autopsy §13): dual-clock lifecycle events with a
        # signal-safe run_end, plus a GPU/RAM sampler for local candidate runs.
        # evals/reports/ is gitignored operational telemetry, same as the run report.
        # G: context enriched with config_digest/experiment_id/candidate_id/
        # execution_system_digest/ordering — HARNESS events previously lacked all five.
        events = RunEventLog(ROOT / "evals" / "reports" / f"{run_id}.events.jsonl",
                             run_id=run_id, arm=args.arm, split=args.split,
                             model_ref=args.model_ref, config_digest=digest,
                             experiment_id=args.arm, candidate_id=args.candidate or "",
                             execution_system_digest=runtime_context.get("execution_system_digest", ""),
                             ordering="round_robin")
        events.run_start(planned_cases=len(manifests), pending=len(pending),
                         resume=bool(args.resume), max_tokens=args.max_tokens,
                         local_server_session=runtime_context.get("local_server_session", ""))
        sampler = None
        if args.candidate:
            sampler = ResourceSampler(ROOT / "evals" / "reports" / f"{run_id}.samples.jsonl",
                                      interval_s=5.0, context={"run_id": run_id}).start()

        run = EvalRun(run_id=run_id, suite="fis-eval", suite_version=SUITE_VERSION,
                      experiment_arm=args.arm, split=SeedSplit(args.split),
                      config_digest=digest)
        escalations = 0

        # E/F: a --candidate run's premature halt (tolerance consequence or
        # curtailment) still needs its own end_run ledger line — same shape as the
        # normal completion at the bottom of main(), folding in whichever extra
        # payload the halt reason carries.
        candidate_end_run: Callable[[dict[str, Any]], None] | None = None
        if r6_reg is not None:
            def candidate_end_run(extra: dict[str, Any]) -> None:
                from fis_platform.provenance import end_run as _end_run
                _end_run(r6_reg, args.candidate, run_id, cases_done=len(run.scores),
                         wall_s=round(_time.monotonic() - run_started, 1), extra=extra)

        for i, m in enumerate(pending, 1):
            events.event("case_start", scenario_id=m["scenario_id"], index=i)
            if test_look_ledger is not None and i == 1:
                # C: spend at the FIRST executed case (playbook §1), before the
                # investigate call — idempotent per run_id on a resumed spent run.
                test_look_ledger.record_spend(run_id, m["scenario_id"])
            if r6_reg is not None:
                runtime_context["gpu_mem_used_mib_now"] = gpu_mem_used_mib()
            with ToolBroker(TOOLS_DSN,
                            on_event=lambda name, _sid=m["scenario_id"], **f: events.event(
                                name, scenario_id=_sid, **f)) as broker:
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
                    events.event("case_end", scenario_id=m["scenario_id"], index=i,
                                 status="exception", error=str(exc)[:500])
                    observe_tolerances(tolerance_trackers,
                                       {"exception": True, "stop_reason": None, "all_pass": None},
                                       events=events, candidate_end_run=candidate_end_run)
                    continue

            score = score_case(result=result, trajectory=traj, manifest=m, run_id=run_id)
            run.scores.append(score)
            persist(owner, run_id, score, traj, result)   # commit per case: resume stays exact

            if args.smoke:
                # Raw evidence only — smoke_case_flags derives the violation flags once
                # the record is assembled after the loop, from tool_call_statuses and
                # n_model_invocations exactly as recorded here.
                smoke_case_evidence[m["scenario_id"]] = {
                    "scenario_id": m["scenario_id"], "trace_id": str(traj.trace_id),
                    "tool_call_statuses": [c.status for c in traj.tool_calls],
                    "n_model_invocations": len(traj.model_invocations),
                    "all_pass": score.all_pass,
                }

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
            events.event("case_end", scenario_id=m["scenario_id"], index=i,
                         status="scored", all_pass=score.all_pass,
                         stop_reason=inv.stop_reason if inv else None,
                         output_tokens=inv.usage.output_tokens if inv else None,
                         ttft_ms=inv.latency.ttft_ms if inv else None,
                         wall_ms=score.wall_ms)
            print(f"[{i}/{len(pending)}] {m['scenario_id']:<12} {mark:<4} "
                  f"rc={'ok' if score.root_cause_correct else 'X'} "
                  f"ev={score.required_evidence_recall:.2f} "
                  f"act={'ok' if score.next_action_acceptable else 'X'} "
                  f"ver={'ok' if score.verifier_passed else 'X'} "
                  f"{score.wall_ms:>6}ms {gen}  ${score.reference_cost_usd:.4f}  {said}{route}")

            observe_tolerances(tolerance_trackers,
                               {"exception": False, "stop_reason": inv.stop_reason if inv else None,
                                "all_pass": score.all_pass},
                               events=events, candidate_end_run=candidate_end_run)

            if curtailment_policy is not None:
                cases_done += 1
                if score.all_pass:
                    passes += 1
                if curtailment_policy.should_curtail(passes, cases_done):
                    curtail_and_exit(curtailment_policy, passes, cases_done, run_id=run_id,
                                     split=args.split, arm=args.arm,
                                     remaining_manifests=pending[i:], events=events,
                                     curtailed_runs_path=ROOT / "learning" / "registry"
                                                         / "curtailed_runs.jsonl",
                                     candidate_end_run=candidate_end_run)

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
    if sampler is not None:
        sampler.stop()
    # Preserve the server log with the run (autopsy §13: 8 of 11 session logs were
    # destroyed by log truncation). Best-effort: the alias names the serve-r6 log.
    alias = runtime_context.get("model_alias", "")
    if alias:
        src = Path(f"/tmp/fis-r6-{alias}.log")
        if src.exists():
            import shutil
            shutil.copyfile(src, ROOT / "evals" / "reports" / f"{run_id}.server.log")
    events.run_end(status="completed", cases_done=len(run.scores),
                   wall_s=round(_time.monotonic() - run_started, 1))

    smoke_extra: dict[str, Any] = {}
    if args.smoke and r6_reg is not None:
        assert canonical_smoke_ids is not None   # set whenever args.smoke, above
        if len(smoke_case_evidence) == SMOKE_TOTAL_CASES:
            from fis_platform.provenance import (
                SMOKE_VIOLATION_RULE, SMOKE_VIOLATION_RULE_DIGEST, smoke_case_flags,
                write_smoke_result,
            )
            cases = []
            total_violations = 0
            for sid in canonical_smoke_ids:
                case = dict(smoke_case_evidence[sid])
                flags = smoke_case_flags(case)
                case["violations"] = flags
                total_violations += len(flags)
                cases.append(case)
            eligible = total_violations == 0
            record = {
                "candidate_id": args.candidate, "smoke_run_id": run_id, "split": "train",
                "suite_version": SUITE_VERSION,
                "corpus_digest": runtime_context.get("corpus_digest", ""),
                "ordering": "round_robin",
                "violation_rule_version": SMOKE_VIOLATION_RULE["version"],
                "violation_rule_digest": SMOKE_VIOLATION_RULE_DIGEST,
                "case_ids": canonical_smoke_ids,
                "smoke_case_digest": runtime_context["smoke_case_digest"],
                "cases": cases, "total_violations": total_violations, "eligible": eligible,
            }
            smoke_result_digest = write_smoke_result(r6_reg, args.candidate, run_id, record)
            smoke_extra = {"smoke_result_digest": smoke_result_digest,
                           "smoke_case_digest": runtime_context["smoke_case_digest"],
                           "smoke_violations": total_violations}
            print(f"\nSMOKE {run_id}: {total_violations} violation(s) of "
                  f"{SMOKE_TOTAL_CASES} cases — eligible={eligible}")
            if eligible:
                print("  operator may now attempt: scripts/r6_registry.py smoke-eligibility "
                     f"--candidate {args.candidate} --run-id {run_id} | "
                     f"scripts/r6_registry.py transition --candidate {args.candidate} "
                     "--to REGISTERED --payload-json -")
            else:
                print("  SMOKE -> REGISTERED will be refused (smoke_violations must be 0)")
        else:
            print(f"\nSMOKE {run_id}: only {len(smoke_case_evidence)}/{SMOKE_TOTAL_CASES} cases "
                 "scored — no SMOKE result was recorded; the completeness gate refuses "
                 "SMOKE -> REGISTERED until a full 36-case pass is recorded")

    if r6_reg is not None:
        from fis_platform.provenance import end_run
        end_run(r6_reg, args.candidate, run_id, cases_done=len(run.scores),
                wall_s=round(_time.monotonic() - run_started, 1),
                extra={"all_pass": sum(1 for sc in run.scores if sc.all_pass),
                       "gpu_mem_used_mib_end": gpu_mem_used_mib(),
                       **smoke_extra})


def _pct(v: float | None) -> str:
    return "n/a" if v is None else f"{v * 100:.1f}%"


if __name__ == "__main__":
    asyncio.run(main())
