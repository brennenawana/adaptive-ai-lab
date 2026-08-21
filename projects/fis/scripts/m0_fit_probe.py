"""M0 WP-C — context/cap fit probe. Runs BEFORE WP-B; certifies the treatment config.

For each candidate server context (-c 12288 / 16384 / 20480) this script launches the
frozen Qwen3.8 Q3_K_M execution system's server (same binary, same artifact, same
flags except -c), measures load-time VRAM and KV size, then drives ONE full-cap
stability generation with the REAL fixed-evidence prompt of the pre-registered probe
case and measures peak VRAM and decode rate. Output: the fit table
(artifacts/m0_fit_probe.csv) and the WP-B certification
(artifacts/m0_fit_certification.json) that m0_paired_probe.py refuses to run without.

Pre-registered choices (frozen before any probe ran):
  * probe case: S01-1000000 — the pilot's first case, NOT in the 15-case primary
    population (no primary case is previewed at a raised cap before its paired run),
    and the known cold-start case, so warm-up lands here rather than in a measurement;
  * stability request: the real ~3.6k-token fixed-evidence prompt, free-form (no
    grammar) with ignore_eos=true so decode runs to exactly the cap — the worst-case
    slot occupancy at that (ctx, cap). A grammar plus ignore_eos would sample past the
    grammar's accept state; memory/stability is what is being measured, and the KV
    cost of a token does not depend on the sampling mask. Disclosed in the artifact:
    the fit-probe request is NOT the frozen genconfig (WP-B asserts its own
    request-side identity separately);
  * certification criteria (all must hold): server healthy; generation completes with
    HTTP 200 and the server alive after; peak VRAM <= 16000 MiB of 16303; decode rate
    >= 15 tok/s (collapse guard — the 8192 baseline is ~27);
  * certified WP-B config: ctx 16384 (the FROZEN execution system's own context, so
    only the request-level cap differs between WP-B arms) with the largest certified
    cap in {12288, 10240}. If neither certifies, the certification file records
    failure and WP-B refuses to start (decision table row: "no cap > 8192 fits").

Quality is deliberately NOT measured (NEXT_STEP_M0.md § 6-C: "No quality measurement").
Every generation is ledgered under the diagnostic run kind.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx
import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from fis_platform.model_gateway.base import GenerationRequest, Message
from fis_platform.model_gateway.gateway import default_registry
from fis_platform.model_gateway.local import LocalLlamaCppAdapter
from fis_platform.provenance import (
    R6Registry,
    begin_run,
    bind_running_server,
    capture_server_args,
    default_root,
    end_run,
    llama_server_pids,
    require_state,
    sha256_file,
    tree_state,
)
from fis_platform.telemetry import ResourceSampler, RunEventLog, dual_clock
from fis_platform.tool_broker.broker import ToolBroker
from scripts.m0_classify import PRIMARY_CASES
from services.ai_orchestrator.investigate import _phase_one, _phase_two
from services.ai_orchestrator.prompts import PROMPTS

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

OWNER_DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")
TOOLS_DSN = os.environ.get("FIS_TOOLS_DSN",
                           "postgresql://fis_tools:fis_tools_local_dev@127.0.0.1:5433/fis")

CANDIDATE = "qwen38-27b-q3km@8528f049af75"
RUN_ID = "M0-qwen38-q3km-train-diag-fitprobe"
PURPOSE = "M0-truncation-diag"
PROBE_SCENARIO = "S01-1000000"
PORT, ALIAS = 8085, "fis-qwen38-27b"
PROMPT_REF = "cause_action_directed"

#: (ctx, [caps to attempt a stability generation at, in order — first success wins]).
#: Caps whose prompt+cap exceed ctx are structurally NOT-APPLICABLE (recorded, not run).
#: Smaller caps at a ctx share the server footprint (KV is allocated for the full ctx
#: at startup), so one worst-case generation per ctx bounds the whole column.
MATRIX: list[tuple[int, list[int]]] = [
    (12288, [8192]),
    (16384, [12288, 10240]),
    (20480, [12288]),
]
PROMPT_ALLOWANCE = 3700          # the largest FIS prompt is ~3.6k tokens
VRAM_CEILING_MIB = 16000
MIN_DECODE_TOK_S = 15.0

CERT_PATH = ROOT / "artifacts" / "m0_fit_certification.json"
CSV_PATH = ROOT / "artifacts" / "m0_fit_probe.csv"


def sh(cmd: list[str], timeout: float = 660.0) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def stop_server() -> None:
    subprocess.run(["pkill", "-f", f"llama-serve[r] .*--port {PORT}"], check=False)
    for _ in range(30):
        if not llama_server_pids():
            return
        time.sleep(1)
    raise SystemExit("!! could not stop the llama-server; refusing to continue")


def start_server(ctx: int) -> str:
    res = sh(["bash", str(ROOT / "infra" / "serve-r6.sh"), "--model",
              "Qwen3.8-27B-Q3_K_M.gguf", "--port", str(PORT), "--alias", ALIAS,
              "--ctx", str(ctx), "--runtime", "upstream", "--offload", "-ngl 99"],
             timeout=660)
    print(res.stdout.strip())
    if res.returncode != 0:
        print(res.stderr.strip())
        return ""
    m = re.search(r"log=(\S+)", res.stdout)
    return m.group(1) if m else ""


def vram_used_mib() -> int:
    try:
        out = sh(["nvidia-smi", "--query-gpu=memory.used",
                  "--format=csv,noheader,nounits"], timeout=15).stdout
        return int(out.strip().splitlines()[0])
    except Exception:  # noqa: BLE001
        return -1


def kv_size_from_log(log_path: str) -> str:
    try:
        for ln in Path(log_path).read_text(errors="replace").splitlines():
            if "KV self size" in ln:
                return ln.split("KV self size")[1].strip(" :=")
    except OSError:
        pass
    return ""


def probe_prompt(conn) -> tuple[str, str, list[dict[str, Any]]]:
    """The probe case's REAL fixed-evidence prompt, built exactly as investigate()
    builds it (same phase-one/phase-two evidence plan, same bundle serialisation)."""
    assert PROBE_SCENARIO not in PRIMARY_CASES
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT scenario_id, split, case_id FROM ground_truth.scenario_manifests "
                    "WHERE scenario_id = %s", (PROBE_SCENARIO,))
        row = cur.fetchone()
    if not row or row["split"] != "train":
        raise SystemExit(f"!! probe case {PROBE_SCENARIO} missing or not TRAIN")
    case_id = row["case_id"]
    with ToolBroker(TOOLS_DSN) as broker:
        case, call = broker.invoke("get_case", {"case_id": case_id})
        if call.status != "success":
            raise SystemExit(f"!! probe case lookup failed: {case}")
        results: list[Any] = [case]
        for tool, tool_args in _phase_one(case):
            res, _ = broker.invoke(tool, tool_args)
            results.append({tool: res})
        for tool, tool_args in _phase_two(case, results):
            res, _ = broker.invoke(tool, tool_args)
            results.append({tool: res})
    bundle = json.dumps(results, indent=2, default=str)
    user = (f"Case {case_id}.\n\nEvidence gathered from the platform:\n\n{bundle}\n\n"
            "Determine the root cause.")
    messages = [{"role": "system", "content": PROMPTS[PROMPT_REF]},
                {"role": "user", "content": user}]
    return case_id, user, messages


def stability_generation(messages: list[dict[str, Any]], cap: int,
                         events: RunEventLog) -> dict[str, Any]:
    """One full-cap decode: free-form + ignore_eos so exactly `cap` tokens generate."""
    manifest = default_registry().resolve("qwen38-27b").model_copy(
        update={"max_output_tokens": max(cap, 8192)})
    adapter = LocalLlamaCppAdapter(manifest, timeout_s=1800.0)
    req = GenerationRequest(model_ref="qwen38-27b",
                            messages=[Message(**{k: v for k, v in m.items()})
                                      for m in messages[1:]],
                            system=messages[0]["content"], max_tokens=cap)
    body = adapter.build_body(req)
    body["ignore_eos"] = True          # fit stress only — never a scored answer
    events.event("fit_generation_start", cap=cap)
    t0 = time.monotonic()
    try:
        with httpx.Client(timeout=1800.0) as client:
            r = client.post(f"http://127.0.0.1:{PORT}/v1/chat/completions", json=body)
        wall_s = round(time.monotonic() - t0, 1)
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:300]}",
                    "wall_s": wall_s}
        payload = r.json()
        timings = payload.get("timings") or {}
        usage = payload.get("usage") or {}
        return {"ok": True, "wall_s": wall_s,
                "finish_reason": (payload.get("choices") or [{}])[0].get("finish_reason"),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "prompt_ms": timings.get("prompt_ms"),
                "predicted_ms": timings.get("predicted_ms"),
                "decode_tok_s": timings.get("predicted_per_second")}
    except httpx.HTTPError as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "wall_s": round(time.monotonic() - t0, 1)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-dirty", action="store_true",
                    help="skip the committed-tree check (development only; the real "
                         "probe run must be from a commit)")
    args = ap.parse_args()

    gh, clean, dirty = tree_state()
    if not clean and not args.allow_dirty:
        raise SystemExit(f"!! fit probe needs a committed code tree (git_head={gh}, "
                         f"dirty outside registry: {dirty})")

    reg = R6Registry(default_root())
    ident = require_state(reg, CANDIDATE, "train", RUN_ID, kind="diagnostic",
                          purpose=PURPOSE)
    frozen_es = ident["execution_system"] or {}
    artifact = reg.get_artifact(ident["identity"]["artifact_id"])
    runtime = reg.get_runtime(ident["identity"]["runtime_id"])
    print(f"candidate {CANDIDATE} at {ident['state']}; frozen ES ctx={frozen_es.get('ctx')}")

    art_sha = sha256_file(artifact.local_path)
    if art_sha != artifact.sha256:
        raise SystemExit(f"!! artifact on disk hashes to {art_sha[:12]}, registered "
                         f"{artifact.sha256[:12]} — STOP")

    CSV_PATH.parent.mkdir(exist_ok=True)
    events = RunEventLog(ROOT / "artifacts" / "m0_fit_probe_events.jsonl",
                         run_id=RUN_ID, arm="M0-fitprobe")

    with psycopg.connect(OWNER_DSN) as conn:
        case_id, user_msg, messages = probe_prompt(conn)
    print(f"probe case {PROBE_SCENARIO} ({case_id}); prompt ~{len(user_msg) // 4} tokens")

    planned = sum(1 for _ctx, caps in MATRIX for _ in caps[:1])   # >=1 gen per ctx
    events.run_start(planned_generations=planned)
    begin_run(reg, CANDIDATE, "train", RUN_ID, planned_cases=planned,
              extra={"matrix": json.dumps(MATRIX)}, kind="diagnostic", purpose=PURPOSE)

    rows: list[dict[str, Any]] = []
    gens_done = 0
    certified: dict[str, Any] | None = None

    stop_server()
    for ctx, caps in MATRIX:
        applicable = [c for c in caps if c + PROMPT_ALLOWANCE <= ctx]
        for cap in [c for c in caps if c not in applicable]:
            rows.append({"ctx": ctx, "cap": cap, "applicable": False, "fit": "N/A",
                         "note": f"prompt allowance {PROMPT_ALLOWANCE} + cap > ctx"})
        if not applicable:
            continue

        log_path = start_server(ctx)
        if not log_path:
            rows.append({"ctx": ctx, "cap": applicable[0], "applicable": True,
                         "fit": "NO-LOAD", "note": "server failed to start"})
            events.event("fit_load_failed", ctx=ctx)
            stop_server()
            continue
        time.sleep(2)
        vram_load = vram_used_mib()
        kv = kv_size_from_log(log_path)
        sargs = capture_server_args(PORT)
        bound = bind_running_server(PORT, runtime)
        events.event("fit_server_up", ctx=ctx, vram_load_mib=vram_load, kv_size=kv,
                     server_args_digest=sargs.server_args_digest if sargs else "",
                     exe=bound["exe"])

        for cap in applicable:
            sampler_path = ROOT / "artifacts" / f"m0_fit_samples_ctx{ctx}_cap{cap}.jsonl"
            with ResourceSampler(sampler_path, interval_s=1.0,
                                 context={"ctx": ctx, "cap": cap}):
                gen = stability_generation(messages, cap, events)
            gens_done += 1
            peak = vram_load
            try:
                for ln in sampler_path.read_text().splitlines():
                    v = json.loads(ln).get("vram_used_mib")
                    if v and int(v) > peak:
                        peak = int(v)
            except (OSError, ValueError):
                pass
            alive = bool(llama_server_pids())
            ok = (gen["ok"] and alive and peak <= VRAM_CEILING_MIB
                  and (gen.get("decode_tok_s") or 0) >= MIN_DECODE_TOK_S)
            row = {"ctx": ctx, "cap": cap, "applicable": True,
                   "fit": "OK" if ok else "FAIL",
                   "vram_load_mib": vram_load, "vram_peak_mib": peak,
                   "kv_size": kv, "server_alive_after": alive,
                   "server_args_digest": sargs.server_args_digest if sargs else "",
                   **{k: gen.get(k) for k in ("finish_reason", "prompt_tokens",
                                              "completion_tokens", "prompt_ms",
                                              "predicted_ms", "decode_tok_s",
                                              "wall_s", "error")}}
            rows.append(row)
            events.event("fit_generation_end", **{k: v for k, v in row.items()
                                                  if k != "error" or v})
            print(f"ctx={ctx} cap={cap}: {row['fit']}  peak={peak}MiB  "
                  f"decode={gen.get('decode_tok_s')} tok/s  wall={gen.get('wall_s')}s")
            if ok and ctx == 16384 and certified is None and cap > 8192:
                certified = {"ctx": ctx, "cap": cap,
                             "server_args_material": sargs.material if sargs else [],
                             "server_args_digest": sargs.server_args_digest if sargs else "",
                             "matches_frozen_es_server_args":
                                 (sargs.server_args_digest == frozen_es.get("server_args_digest")
                                  if sargs else False),
                             "vram_peak_mib": peak,
                             "decode_tok_s": gen.get("decode_tok_s")}
                break          # largest certified cap at the frozen ctx wins
            if ok:
                break          # per-ctx worst case done; smaller caps share the footprint
        stop_server()

    # Arithmetic fill-in: caps not generation-tested at a ctx whose worst case passed.
    fit_by_ctx = {r["ctx"]: r for r in rows if r.get("fit") == "OK"}
    for ctx, _caps in MATRIX:
        for cap in (8192, 10240, 12288):
            if any(r["ctx"] == ctx and r["cap"] == cap for r in rows):
                continue
            if cap + PROMPT_ALLOWANCE > ctx:
                rows.append({"ctx": ctx, "cap": cap, "applicable": False, "fit": "N/A",
                             "note": "prompt allowance + cap > ctx"})
            elif ctx in fit_by_ctx:
                rows.append({"ctx": ctx, "cap": cap, "applicable": True,
                             "fit": "OK-derived",
                             "note": f"derived: worst-case cap {fit_by_ctx[ctx]['cap']} "
                                     "passed at this ctx (KV is allocated per ctx)"})

    fields = sorted({k for r in rows for k in r})
    with CSV_PATH.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["ctx"], r["cap"])))

    cert = {"written_at": dual_clock(), "run_id": RUN_ID, "candidate": CANDIDATE,
            "probe_scenario": PROBE_SCENARIO, "criteria": {
                "vram_ceiling_mib": VRAM_CEILING_MIB,
                "min_decode_tok_s": MIN_DECODE_TOK_S},
            "certified": certified is not None, "certification": certified,
            "artifact_sha256_verified": art_sha}
    CERT_PATH.write_text(json.dumps(cert, indent=2, sort_keys=True) + "\n")

    end_run(reg, CANDIDATE, RUN_ID, cases_done=gens_done, wall_s=0.0,
            extra={"generations": gens_done, "certified": certified is not None})
    events.run_end(status="completed", generations=gens_done)
    print(f"\nwrote {CSV_PATH}\nwrote {CERT_PATH}")
    if certified:
        print(f"CERTIFIED for WP-B: ctx={certified['ctx']} cap={certified['cap']} "
              f"(frozen-ES server args match: {certified['matches_frozen_es_server_args']})")
    else:
        print("NO cap > 8192 certified at ctx 16384 — WP-B must not run as designed; "
              "see the decision table row for this outcome.")


if __name__ == "__main__":
    main()
