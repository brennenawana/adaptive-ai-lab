"""M0 WP-B Pass 2 — the paired cap-raise probe (NEXT_STEP_M0.md § 6-B, rev 4).

The causal design, enforced fail-closed:

  * 15 pre-registered primary cases (scripts/m0_classify.PRIMARY_CASES), each run
    twice in ONE llama-server session: CONTROL at cap 8192 and TREATMENT at the
    WP-C-certified cap, in the pre-registered deterministic AB/BA order;
  * ONLY the request-level generation cap differs between the arms — asserted, not
    assumed: the live server args must digest-equal the FROZEN execution system's,
    the control generation config must digest-equal the frozen genconfig, and the
    treatment genconfig must differ from it in max_tokens alone (field-wise proof);
  * the session must be FRESH (never seen by any earlier ledger line) and must not
    change across the 31 generations (session probe + 15 pairs) — any change aborts;
  * every generation is scored by the deterministic scorer against TRAIN ground truth
    and persisted through the standard persist() path (trajectories now carry
    reasoning_text/content_text per WP-A);
  * ledgered under the `diagnostic` run kind: ledger lines only, and the script
    proves the candidate state log and HEAD.json are byte-identical afterwards;
  * ABORT policy (pre-registered): any generation error, server death or session
    change ends the probe; a partial session never enters the primary analysis —
    the probe re-runs whole, in a fresh session, under -v2 run ids.

Order of arms within a pair: "AB" = control first; "BA" = treatment first.
Session warm-up: the r6-prime 8-token request, then the pre-registered NON-primary
probe case S01-1000000 at cap 8192 (the same-session rule's TRAIN-case probe; also
absorbs the known cold-start). Neither belongs to the primary population.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import httpx
import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from evals.runner.run_eval import (
    OWNER_DSN,
    TOOLS_DSN,
    guard_suite,
    load_manifests,
    local_server_session,
    persist,
)
from evals.scorers.score import SCORER_VERSION, score_case
from fis_platform.model_gateway import ModelGateway, default_registry
from fis_platform.provenance import (
    R6Registry,
    begin_run,
    bind_running_server,
    build_generation_config,
    capture_server_args,
    default_root,
    end_run,
    llama_server_pids,
    require_state,
    sha256_file,
    tree_state,
)
from fis_platform.suite import SUITE_VERSION, git_head
from fis_platform.telemetry import (
    ResourceSampler,
    RunEventLog,
    monotonic_s,
    realtime_iso,
)
from fis_platform.tool_broker.broker import ToolBroker
from fis_platform.verification.verifier import VERIFIER_VERSION
from scripts.corpus_digest import corpus_digest
from scripts.m0_classify import (
    CONTROL_CAP,
    PRIMARY_CASES,
    classify_treatment,
    paired_order,
)
from services.ai_orchestrator.investigate import EvidenceMode, investigate

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

CANDIDATE = "qwen38-27b-q3km@8528f049af75"
MODEL_REF = "qwen38-27b"
PURPOSE = "M0-truncation-diag"
PROMPT_REF = "cause_action_directed"
PROBE_SCENARIO = "S01-1000000"
PROMPT_ALLOWANCE = 3700
CERT_PATH = ROOT / "artifacts" / "m0_fit_certification.json"
CSV_PATH = ROOT / "artifacts" / "m0_paired_probe.csv"

CSV_FIELDS = [
    "scenario_id", "class", "pair_index", "order",
    "control_run_id", "control_trace_id", "control_stop_reason", "control_pass",
    "control_output_tokens", "control_reasoning_chars", "control_content_chars",
    "control_input_tokens", "control_wall_ms", "control_ttft_ms",
    "reconfirmed",
    "treatment_run_id", "treatment_trace_id", "treatment_stop_reason", "treatment_pass",
    "treatment_parseable", "treatment_output_tokens", "treatment_reasoning_chars",
    "treatment_content_chars", "treatment_input_tokens", "treatment_wall_ms",
    "treatment_ttft_ms", "treatment_cap",
    "treatment_class", "shape_verdict", "shape_fired", "shape_dup_rate",
    "shape_tail_novelty", "shape_distinct_hypotheses", "shape_tail_new_evidence",
    "input_tokens_equal", "deterministic_rationale",
]


class ProbeAbort(SystemExit):
    """Fail-closed: the paired design's preconditions stopped holding mid-run."""


def _fail(events: RunEventLog, msg: str) -> ProbeAbort:
    events.run_end(status="aborted", reason=msg[:500])
    return ProbeAbort(f"!! ABORT: {msg}")


def registry_snapshot(reg: R6Registry) -> dict[str, str]:
    files = [reg.head_file] + [reg.state_file(c) for c in reg.candidate_ids()]
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()}


async def run_probe(args: argparse.Namespace) -> None:
    # ---------------------------------------------------------------- certification
    if not CERT_PATH.exists():
        raise SystemExit(f"!! {CERT_PATH} missing — run scripts/m0_fit_probe.py first "
                         "(WP-C certifies the treatment cap before WP-B may run)")
    cert = json.loads(CERT_PATH.read_text())
    if not cert.get("certified"):
        raise SystemExit("!! WP-C certified no cap > 8192 at the frozen context — WP-B "
                         "must not run as designed (decision table: 'no cap > 8192 "
                         "fits the 5080 safely')")
    certified = cert["certification"]
    treat_cap = int(certified["cap"])
    suffix = f"-v{args.attempt}" if args.attempt > 1 else ""
    run_ctrl = f"M0-qwen38-q3km-train-diag-ctrl{CONTROL_CAP}{suffix}"
    run_treat = f"M0-qwen38-q3km-train-diag-treat{treat_cap}{suffix}"
    run_probe_id = f"M0-qwen38-q3km-train-diag-sessionprobe{suffix}"

    events = RunEventLog(ROOT / "artifacts" / "m0_paired_probe_events.jsonl",
                         run_id=run_ctrl.replace("-ctrl8192", ""), arm="M0-paired-probe")

    if int(certified["ctx"]) != 16384:
        raise SystemExit("!! certification is not at the frozen ctx 16384 — the "
                         "same-config paired design cannot run; return to the owner")

    # ---------------------------------------------------------------- code identity
    gh, clean, dirty = tree_state()
    if not clean:
        raise SystemExit(f"!! paired probe needs a committed code tree (git_head={gh}, "
                         f"dirty outside registry: {dirty})")

    # ---------------------------------------------------------------- registry
    reg = R6Registry(default_root())
    ident = require_state(reg, CANDIDATE, "train", run_ctrl, kind="diagnostic",
                          purpose=PURPOSE)
    require_state(reg, CANDIDATE, "train", run_treat, kind="diagnostic", purpose=PURPOSE)
    require_state(reg, CANDIDATE, "train", run_probe_id, kind="diagnostic",
                  purpose=PURPOSE)
    frozen_es = ident["execution_system"] or {}
    if not frozen_es:
        raise SystemExit("!! candidate has no frozen execution system — cannot pair")
    artifact = reg.get_artifact(ident["identity"]["artifact_id"])
    runtime = reg.get_runtime(ident["identity"]["runtime_id"])
    snapshot_before = registry_snapshot(reg)

    # ---------------------------------------------------------------- server identity
    pids = llama_server_pids()
    if len(pids) != 1:
        raise SystemExit(f"!! exactly one llama-server must be resident (found {pids}) "
                         "— start it fresh: make r6-serve MODEL=Qwen3.8-27B-Q3_K_M.gguf "
                         "PORT=8085 ALIAS=fis-qwen38-27b CTX=16384")
    manifest = default_registry().resolve(MODEL_REF)
    port = int(re.search(r":(\d+)", manifest.base_url.removesuffix("/v1")).group(1))
    sargs = capture_server_args(port)
    if sargs is None:
        raise SystemExit(f"!! no llama-server on port {port}")
    if sargs.server_args_digest != frozen_es["server_args_digest"]:
        raise SystemExit("!! live server args differ from the FROZEN execution system:\n"
                         f"  live   {sargs.material}\n  frozen {frozen_es.get('server_args_material')}")
    if sargs.server_args_digest != certified["server_args_digest"]:
        raise SystemExit("!! live server args differ from the WP-C-certified configuration")
    bound = bind_running_server(port, runtime)
    served_path = None
    session_ctx = local_server_session(manifest.base_url)
    if session_ctx.get("llamacpp_build", "") != runtime.build_info_expected:
        raise SystemExit(f"!! served build {session_ctx.get('llamacpp_build')!r} != "
                         f"registered {runtime.build_info_expected!r}")
    served_path = session_ctx.get("model_path", "")
    if Path(served_path).name != artifact.filename:
        raise SystemExit(f"!! served model {served_path!r} is not {artifact.filename}")
    served_sha = sha256_file(served_path)
    if served_sha != artifact.sha256:
        raise SystemExit("!! served file sha256 does not match the registered artifact")
    session = session_ctx.get("local_server_session", "")
    if not session:
        raise SystemExit("!! could not identify the server session (pid/start_ticks)")
    used_sessions = {ln.get("local_server_session") for ln in reg.read_ledger()
                     if ln.get("local_server_session")}
    if session in used_sessions:
        raise SystemExit(f"!! session {session} already served an earlier ledgered run — "
                         "the paired probe needs a FRESH session (restart the server)")

    # ---------------------------------------------------------------- request identity
    cgc = build_generation_config(PROMPT_REF, CONTROL_CAP)
    if cgc.record_digest != frozen_es["generation_config_digest"]:
        raise SystemExit("!! control generation config does not digest-match the frozen "
                         "genconfig — the control arm would not be the frozen system")
    tgc = build_generation_config(PROMPT_REF, treat_cap)
    c_pay = {k: v for k, v in cgc.digest_payload().items()
             if k not in ("genconfig_id", "max_tokens")}
    t_pay = {k: v for k, v in tgc.digest_payload().items()
             if k not in ("genconfig_id", "max_tokens")}
    if c_pay != t_pay:
        diff = {k for k in set(c_pay) | set(t_pay) if c_pay.get(k) != t_pay.get(k)}
        raise SystemExit(f"!! treatment request differs from control beyond max_tokens: "
                         f"{sorted(diff)} — the causal contrast would be confounded")
    if treat_cap + PROMPT_ALLOWANCE > frozen_es["ctx"]:
        raise SystemExit(f"!! cap {treat_cap} + prompt allowance exceeds ctx {frozen_es['ctx']}")

    schedule = paired_order()
    schedule_digest = hashlib.sha256(json.dumps(schedule).encode()).hexdigest()
    print(f"candidate {CANDIDATE} at {ident['state']}  session={session}")
    print(f"control cap {CONTROL_CAP} (gc {cgc.genconfig_id}) | treatment cap {treat_cap} "
          f"(gc {tgc.genconfig_id}) | only max_tokens differs: PROVEN")
    print(f"schedule sha256 {schedule_digest[:16]} ({len(schedule)} pairs)")

    # ---------------------------------------------------------------- gateway + DB
    gateway = ModelGateway(default_registry())
    adapter = gateway.adapter(MODEL_REF)
    adapter._timeout = 1800.0     # client-side patience only; not part of any digest

    base_runtime_context = {
        "m0": "paired-probe", "purpose": PURPOSE, "schedule_digest": schedule_digest,
        "suite_version": SUITE_VERSION, "scorer_version": SCORER_VERSION,
        "verifier_version": VERIFIER_VERSION, "git_head": git_head(),
        "candidate_id": CANDIDATE, "artifact_id": artifact.artifact_id,
        "artifact_sha256": artifact.sha256, "runtime_id": runtime.runtime_id,
        "server_args_digest": sargs.server_args_digest,
        "execution_system_digest": frozen_es.get("record_digest", ""),
        "server_exe": bound["exe"], **session_ctx,
    }

    with psycopg.connect(OWNER_DSN) as owner:
        for rid in (run_ctrl, run_treat, run_probe_id):
            guard_suite(owner, rid, "train", resume=False)
        base_runtime_context["corpus_digest"] = corpus_digest(owner)["digest"]
        manifests = {m["scenario_id"]: m
                     for m in load_manifests(owner, "train",
                                             list(PRIMARY_CASES) + [PROBE_SCENARIO])}
        if set(manifests) != set(PRIMARY_CASES) | {PROBE_SCENARIO}:
            raise SystemExit("!! TRAIN manifests do not contain the pre-registered cases")

        events.run_start(schedule=schedule, treatment_cap=treat_cap, session=session,
                         control_genconfig=cgc.genconfig_id,
                         treatment_genconfig=tgc.genconfig_id)
        sampler = ResourceSampler(ROOT / "artifacts" / "m0_paired_probe_samples.jsonl",
                                  interval_s=5.0, context={"run": "m0-paired"}).start()
        t_start_mono, t_start_real = monotonic_s(), realtime_iso()

        begin_run(reg, CANDIDATE, "train", run_probe_id, planned_cases=1,
                  extra={"local_server_session": session}, kind="diagnostic",
                  purpose=PURPOSE)
        begin_run(reg, CANDIDATE, "train", run_ctrl, planned_cases=len(schedule),
                  extra={"local_server_session": session, "max_tokens": CONTROL_CAP,
                         "schedule_digest": schedule_digest},
                  kind="diagnostic", purpose=PURPOSE)
        begin_run(reg, CANDIDATE, "train", run_treat, planned_cases=len(schedule),
                  extra={"local_server_session": session, "max_tokens": treat_cap,
                         "schedule_digest": schedule_digest},
                  kind="diagnostic", purpose=PURPOSE)

        def check_session(where: str) -> None:
            now = local_server_session(manifest.base_url).get("local_server_session", "")
            if now != session:
                raise _fail(events, f"server session changed at {where}: "
                                    f"{session!r} -> {now!r} — pairs are no longer "
                                    "same-session; re-run whole with --attempt "
                                    f"{args.attempt + 1}")

        async def one_generation(scenario_id: str, run_id: str, arm: str, cap: int,
                                 order: str, pair_index: int) -> dict[str, Any]:
            check_session(f"{scenario_id}/{arm}")
            events.event("generation_start", scenario_id=scenario_id, arm=arm, cap=cap)
            rc = dict(base_runtime_context)
            rc.update({"run_id": run_id, "arm": arm, "max_tokens": str(cap),
                       "order": order, "pair_index": str(pair_index)})
            m = manifests[scenario_id]
            with ToolBroker(TOOLS_DSN) as broker:
                result, traj = await investigate(
                    m["case_id"], gateway=gateway, broker=broker, model_ref=MODEL_REF,
                    experiment_arm=arm, mode=EvidenceMode.FIXED_EVIDENCE,
                    scenario_id=scenario_id, prompt_ref=PROMPT_REF,
                    runtime_context=rc, max_tokens=cap)
            if traj.error and not traj.model_invocations:
                raise _fail(events, f"{scenario_id}/{arm}: {traj.error}")
            inv = traj.model_invocations[0]
            if inv.stop_reason is None and traj.error:
                raise _fail(events, f"{scenario_id}/{arm}: generation error {traj.error}")
            score = score_case(result=result, trajectory=traj, manifest=m, run_id=run_id)
            persist(owner, run_id, score, traj, result)
            rec = {"scenario_id": scenario_id, "arm": arm, "run_id": run_id,
                   "trace_id": str(traj.trace_id), "cap": cap,
                   "stop_reason": inv.stop_reason, "pass": bool(score.all_pass),
                   "parseable": result is not None,
                   "output_tokens": inv.usage.output_tokens,
                   "input_tokens": inv.usage.input_tokens,
                   "reasoning_chars": inv.reasoning_chars or 0,
                   "content_chars": inv.content_chars or 0,
                   "wall_ms": score.wall_ms, "ttft_ms": inv.latency.ttft_ms,
                   "reasoning_text": inv.reasoning_text, "content_text": inv.content_text}
            events.event("generation_end", **{k: v for k, v in rec.items()
                                              if k not in ("reasoning_text",
                                                           "content_text")})
            print(f"  {arm:<22} {scenario_id} cap={cap:<6} "
                  f"stop={inv.stop_reason:<7} pass={score.all_pass} "
                  f"out={inv.usage.output_tokens} wall={score.wall_ms}ms")
            return rec

        # ------------------------------------------------------------ warm-up
        with httpx.Client(timeout=120.0) as client:
            r = client.post(f"http://127.0.0.1:{port}/v1/chat/completions",
                            json={"model": manifest.model_id,
                                  "messages": [{"role": "user", "content": "prime"}],
                                  "max_tokens": 8, "temperature": 0, "seed": 42})
            if r.status_code != 200:
                raise _fail(events, f"prime request failed: HTTP {r.status_code}")
        events.event("primed")
        print("primed (8 tokens)")

        probe_rec = await one_generation(PROBE_SCENARIO, run_probe_id,
                                         "M0-diag-sessionprobe", CONTROL_CAP,
                                         "probe", -1)
        end_run(reg, CANDIDATE, run_probe_id, cases_done=1,
                wall_s=monotonic_s() - t_start_mono,
                extra={"stop_reason": probe_rec["stop_reason"]})

        # ------------------------------------------------------------ the 15 pairs
        rows: list[dict[str, Any]] = []
        for pair_index, (scenario_id, order) in enumerate(schedule):
            print(f"[{pair_index + 1}/15] {scenario_id}  order={order}")
            arms = [("control", run_ctrl, CONTROL_CAP), ("treatment", run_treat, treat_cap)]
            if order == "BA":
                arms.reverse()
            recs: dict[str, dict[str, Any]] = {}
            for arm_name, rid, cap in arms:
                recs[arm_name] = await one_generation(
                    scenario_id, rid, f"M0-diag-{arm_name}", cap, order, pair_index)
            c, t = recs["control"], recs["treatment"]
            reconfirmed = c["stop_reason"] == "length"
            cls, shape = classify_treatment(
                stop_reason=t["stop_reason"], passed=t["pass"],
                parseable=t["parseable"], reasoning_text=t["reasoning_text"],
                content_text=t["content_text"])
            rationale = {
                "a": "treatment passed the deterministic scorer",
                "b": "treatment completed and parsed but failed the scorer",
                "c": f"still length-stopped; rubric convergent ({shape.fired if shape else []})",
                "d": f"still length-stopped; rubric degenerate ({shape.fired if shape else []})",
                "e": "no length stop but no parseable object (pre-declared edge)",
            }[cls]
            rows.append({
                "scenario_id": scenario_id, "class": scenario_id[:3],
                "pair_index": pair_index, "order": order,
                "control_run_id": run_ctrl, "control_trace_id": c["trace_id"],
                "control_stop_reason": c["stop_reason"], "control_pass": c["pass"],
                "control_output_tokens": c["output_tokens"],
                "control_reasoning_chars": c["reasoning_chars"],
                "control_content_chars": c["content_chars"],
                "control_input_tokens": c["input_tokens"],
                "control_wall_ms": c["wall_ms"], "control_ttft_ms": c["ttft_ms"],
                "reconfirmed": reconfirmed,
                "treatment_run_id": run_treat, "treatment_trace_id": t["trace_id"],
                "treatment_stop_reason": t["stop_reason"], "treatment_pass": t["pass"],
                "treatment_parseable": t["parseable"],
                "treatment_output_tokens": t["output_tokens"],
                "treatment_reasoning_chars": t["reasoning_chars"],
                "treatment_content_chars": t["content_chars"],
                "treatment_input_tokens": t["input_tokens"],
                "treatment_wall_ms": t["wall_ms"], "treatment_ttft_ms": t["ttft_ms"],
                "treatment_cap": treat_cap,
                "treatment_class": cls,
                "shape_verdict": shape.verdict if shape else "",
                "shape_fired": ";".join(shape.fired) if shape else "",
                "shape_dup_rate": shape.dup_rate if shape else "",
                "shape_tail_novelty": shape.tail_novelty if shape else "",
                "shape_distinct_hypotheses": shape.distinct_hypotheses if shape else "",
                "shape_tail_new_evidence": shape.tail_new_evidence if shape else "",
                "input_tokens_equal": c["input_tokens"] == t["input_tokens"],
                "deterministic_rationale": rationale,
            })
            events.event("pair_done", scenario_id=scenario_id, order=order,
                         reconfirmed=reconfirmed, treatment_class=cls)

        wall_s = monotonic_s() - t_start_mono
        end_run(reg, CANDIDATE, run_ctrl, cases_done=len(schedule), wall_s=wall_s,
                extra={"reconfirmed": sum(1 for r in rows if r["reconfirmed"])})
        end_run(reg, CANDIDATE, run_treat, cases_done=len(schedule), wall_s=wall_s,
                extra={"rescues": sum(1 for r in rows if r["treatment_class"] == "a"
                                      and r["reconfirmed"])})
        sampler.stop()

    # ---------------------------------------------------------------- integrity
    snapshot_after = registry_snapshot(reg)
    if snapshot_after != snapshot_before:
        changed = [p for p in snapshot_after
                   if snapshot_after.get(p) != snapshot_before.get(p)]
        raise _fail(events, f"candidate state/HEAD changed during the probe: {changed}")
    check_session("post-run")

    CSV_PATH.parent.mkdir(exist_ok=True)
    with CSV_PATH.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)

    # preserve the session's server log (autopsy §13) — gitignored operational copy
    log_link = Path(f"/tmp/fis-r6-{ALIAS_LOG}.log")
    if log_link.exists():
        import shutil
        dst = ROOT / "evals" / "reports" / "m0_paired_probe.server.log"
        shutil.copyfile(log_link, dst)
        events.event("server_log_preserved", path=str(dst),
                     sha256=hashlib.sha256(dst.read_bytes()).hexdigest())

    n_reconf = sum(1 for r in rows if r["reconfirmed"])
    n_rescue = sum(1 for r in rows if r["reconfirmed"] and r["treatment_class"] == "a")
    events.run_end(status="completed", pairs=len(rows), reconfirmed=n_reconf,
                   rescues=n_rescue, wall_s=wall_s,
                   started_realtime=t_start_real)
    print(f"\nwrote {CSV_PATH}")
    print(f"pairs={len(rows)}  n_control_reconfirmed={n_reconf}  n_rescue={n_rescue}")
    print("state/HEAD byte-identity: VERIFIED")


ALIAS_LOG = "fis-qwen38-27b"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--attempt", type=int, default=1,
                    help="probe attempt number; >1 suffixes run ids with -vN after an "
                         "aborted session (a partial session never enters the analysis)")
    args = ap.parse_args()
    asyncio.run(run_probe(args))


if __name__ == "__main__":
    main()
