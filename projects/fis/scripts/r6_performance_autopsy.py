"""R6 performance autopsy — read-only reconstruction of where the ~24 h went.

Sources, in order of authority:
  CLOCK_REALTIME  Postgres `learning.trajectories.created_at`, the R6 run ledger's
                  `started_at`/`finished_at`, git commit times, llama.cpp *log-prefix*
                  timestamps. These agree with each other end-to-end and are treated as
                  wall-clock truth.
  CLOCK_MONOTONIC every in-process timer: Python `time.perf_counter`/`time.monotonic`
                  (per-case `wall_ms`, the ledger's `wall_s`) and llama.cpp's
                  `ggml_time_us` (`timings` → `api_ms`, all tok/s). On this WSL2 guest
                  these ran ~7–8 % SLOW versus realtime during the runs (measured below,
                  per run) — so every monotonic-based duration in the R6 report
                  understates realtime by that factor. Cross-arm comparisons are
                  unaffected (same skew everywhere).

Writes (tracked, non-canonical analysis artifacts):
  artifacts/r6_performance_autopsy_phase_timing.csv
  artifacts/r6_performance_autopsy_model_timing.csv
  artifacts/r6_performance_autopsy_slowest_cases.csv
  artifacts/r6_performance_autopsy_summary.json

Nothing here mutates the database, the registry, or any R6 result.
"""

from __future__ import annotations

import csv
import json
import os
import re
import statistics as st
import sys
from datetime import UTC, datetime
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")
REG = ROOT / "learning" / "registry" / "r6"
ART = ROOT / "artifacts"

GOAL_AT = datetime.fromisoformat("2026-08-18T20:59:46+00:00")   # /goal receipt (job log)
END_AT = datetime.fromisoformat("2026-08-19T21:02:56+00:00")    # final commit 5f785a7 (git)

RUN_MODEL = {  # run_id -> (model label, artifact_id short)
    "R6-qwen35-train-pilot": "qwen3.5-9b", "R6-qwen35-train-stab": "qwen3.5-9b",
    "R6-qwen35-dev": "qwen3.5-9b",
    "R6-qwen38-q3km-train-pilot": "qwen3.8-27b-q3km", "R6-qwen38-q3km-train-stab": "qwen3.8-27b-q3km",
    "R6-qwen38-q3km-dev": "qwen3.8-27b-q3km", "R6-qwen38-q3km-test": "qwen3.8-27b-q3km",
    "R6-qwen38-udq3kxl-train-pilot": "qwen3.8-27b-udq3kxl",
    "R6-bonsai-train-pilot": "bonsai-27b", "R6-bonsai-train-stab": "bonsai-27b",
    "R6-bonsai-dev": "bonsai-27b", "R6-bonsai-test": "bonsai-27b",
}

SURVIVING_LOGS = {  # only the LAST session per server survives (serve script truncates)
    "R6-qwen35-dev": "/tmp/fis-r6-fis-qwen35-9b.log",
    "R6-qwen38-q3km-test": "/tmp/fis-r6-fis-qwen38-27b.log",
    "R6-bonsai-test": "/tmp/fis-r6-fis-bonsai-27b.log",
}


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_ledger() -> list[dict]:
    return [json.loads(ln) for ln in (REG / "ledger.jsonl").read_text().splitlines() if ln.strip()]


def run_windows(ledger: list[dict]) -> list[dict]:
    """One row per ledger run segment: realtime start/end. The interrupted first segment of
    R6-bonsai-train-stab has no end line; its end is bounded by the DB below."""
    rows = []
    open_starts: dict[str, list[dict]] = {}
    for ln in ledger:
        if ln["event"] == "start":
            open_starts.setdefault(ln["run_id"], []).append(
                {"run_id": ln["run_id"], "start": ln["started_at"], "end": None,
                 "wall_s_monotonic": None, "cases_done": None, "planned": ln["planned_cases"],
                 "session": ln.get("local_server_session", "")})
            rows.append(open_starts[ln["run_id"]][-1])
        else:
            seg = open_starts[ln["run_id"]][-1]
            seg["end"] = ln["finished_at"]
            seg["wall_s_monotonic"] = ln.get("wall_s")
            seg["cases_done"] = ln.get("cases_done")
    return rows


def per_case(conn, run_id: str) -> list[dict]:
    rows = conn.execute(
        """SELECT cs.scenario_id, (cs.payload->>'wall_ms')::bigint,
                  (t.payload->'model_invocations'->0->'latency'->>'api_ms')::bigint,
                  (t.payload->'model_invocations'->0->'usage'->>'input_tokens')::int,
                  (t.payload->'model_invocations'->0->'usage'->>'output_tokens')::int,
                  t.payload->'model_invocations'->0->>'stop_reason',
                  (t.payload->'model_invocations'->0->>'reasoning_chars')::int,
                  (t.payload->'model_invocations'->0->>'content_chars')::int,
                  cs.all_pass, t.created_at,
                  t.payload->'runtime_context'->>'gpu_mem_used_mib_now',
                  (cs.payload->>'tool_calls_total')::int,
                  jsonb_array_length(t.payload->'model_invocations')
             FROM learning.case_scores cs
             JOIN learning.trajectories t ON t.trace_id = cs.trace_id
            WHERE cs.run_id = %s ORDER BY t.created_at""", (run_id,)).fetchall()
    return [{"scenario_id": r[0], "wall_ms": r[1], "api_ms": r[2], "in_tok": r[3],
             "out_tok": r[4], "stop": r[5], "reasoning_chars": r[6], "content_chars": r[7],
             "all_pass": r[8], "created_at": r[9], "gpu_mib": int(r[10]) if r[10] else None,
             "tool_calls": r[11], "model_turns": r[12]}
            for r in rows]


def parse_server_log(path: str) -> dict | None:
    """launch/release realtime-prefixed events + model-load time for a surviving session."""
    if not Path(path).exists():
        return None
    def rel(s: str) -> float:
        p = s.split(".")
        return int(p[0]) * 60 + int(p[1]) + int(p[2]) / 1000 + int(p[3]) / 1e6
    launches, releases, order = {}, {}, []
    load_start = load_end = None
    lines = Path(path).read_text(errors="replace").splitlines()
    for line in lines:
        m = re.match(r"^(\d+\.\d+\.\d+\.\d+) I srv\s+load_model: loading model", line)
        if m:
            load_start = rel(m.group(1))
        m = re.match(r"^(\d+\.\d+\.\d+\.\d+) I srv\s+llama_server: model loaded", line)
        if m:
            load_end = rel(m.group(1))
        m = re.match(r"^(\d+\.\d+\.\d+\.\d+) I slot launch_slot_: id  0 \| task (\d+) \| processing task, is_child = 0", line)
        if m:
            launches[m.group(2)] = rel(m.group(1)); order.append(m.group(2)); continue
        m = re.match(r"^(\d+\.\d+\.\d+\.\d+) I slot\s+release: id  0 \| task (\d+) \|", line)
        if m:
            releases[m.group(2)] = rel(m.group(1))
    durs = [releases[t] - launches[t] for t in order if t in releases and t in launches]
    idles = [launches[order[i]] - releases[order[i - 1]] for i in range(1, len(order))
             if order[i] in launches and order[i - 1] in releases]
    return {"requests": len(order),
            "load_s": round(load_end - load_start, 1) if load_start is not None and load_end is not None else None,
            "busy_s": round(sum(durs), 1),
            "request_p50_s": round(st.median(durs), 1) if durs else None,
            "idle_between_requests_s_sum": round(sum(idles), 1) if idles else 0.0,
            "idle_between_requests_s_median": round(st.median(idles), 2) if idles else None}


def main() -> None:
    ART.mkdir(exist_ok=True)
    ledger = load_ledger()
    segments = run_windows(ledger)
    phases = [json.loads(ln) for ln in (REG / "phases.jsonl").read_text().splitlines() if ln.strip()]

    with psycopg.connect(DSN) as conn:
        cases_by_run = {r: per_case(conn, r) for r in RUN_MODEL}

    # ---------------- run/model table ----------------
    model_rows = []
    all_cases = []
    for seg in segments:
        rid = seg["run_id"]
        cs = cases_by_run[rid]
        start = datetime.fromisoformat(seg["start"])
        # NOTE: case 1's created_at is stamped when the owner connection's transaction
        # opens (at guard_suite, BEFORE begin_run stamps started_at) — so assign cases to
        # segments by the resume boundary only, never by the window edges.
        resume_cut = datetime.fromisoformat("2026-08-19T05:39:07+00:00")
        if rid == "R6-bonsai-train-stab":
            first_seg = seg["end"] is None
            seg_cases = [c for c in cs if (c["created_at"].astimezone(UTC) < resume_cut) == first_seg]
        else:
            seg_cases = cs
        if seg["end"] is None:
            end = max(c["created_at"] for c in seg_cases).astimezone(UTC)
            seg_end_note = "no end line (interrupted by a 10-min tool timeout); end = last insert"
        else:
            end = datetime.fromisoformat(seg["end"])
            seg_end_note = ""
        window = (end - start).total_seconds()
        walls = [c["wall_ms"] / 1000 for c in seg_cases]
        apis = [c["api_ms"] / 1000 for c in seg_cases if c["api_ms"]]
        deltas = [(seg_cases[i + 1]["created_at"] - seg_cases[i]["created_at"]).total_seconds()
                  for i in range(len(seg_cases) - 1)]
        # realtime p50 cycle: consecutive-insert deltas, excluding the first interval
        # (case 1's created_at is stamped at the pre-loop transaction start, an artifact)
        cyc = deltas[1:] if len(deltas) > 2 else deltas
        skew = (sum(deltas[1:]) / sum(c["wall_ms"] / 1000 for c in seg_cases[2:])
                if len(seg_cases) > 3 else None)
        caps = sum(1 for c in seg_cases if c["stop"] == "length")
        cap_wall = sum(c["wall_ms"] for c in seg_cases if c["stop"] == "length") / 1000
        gpu = [c["gpu_mib"] for c in seg_cases if c["gpu_mib"]]
        model_rows.append({
            "run_id": rid, "model": RUN_MODEL[rid], "split": rid.split("-")[-1] if "train" not in rid else "train",
            "start_utc": _iso(start), "end_utc": _iso(end),
            "window_s_realtime": round(window, 1),
            "wall_s_monotonic_ledger": seg["wall_s_monotonic"],
            "cases": len(seg_cases), "all_pass": sum(1 for c in seg_cases if c["all_pass"]),
            "sum_case_wall_s_monotonic": round(sum(walls), 1),
            "sum_api_s_monotonic": round(sum(apis), 1),
            "in_tokens": sum(c["in_tok"] or 0 for c in seg_cases),
            "out_tokens": sum(c["out_tok"] or 0 for c in seg_cases),
            "cap_hits": caps, "cap_hit_wall_s": round(cap_wall, 1),
            "case_p50_s_monotonic": round(st.median(walls), 1) if walls else None,
            "case_p50_s_realtime": round(st.median(cyc), 1) if cyc else None,
            "case_p95_s_monotonic": round(sorted(walls)[max(0, int(0.95 * len(walls)) - 1)], 1) if walls else None,
            "cases_per_hour_realtime": round(len(seg_cases) / (window / 3600), 1) if window else None,
            "monotonic_vs_realtime": round(1 / skew - 0 if False else (skew if skew else 0), 4) if skew else None,
            "gpu_mib_min": min(gpu) if gpu else None, "gpu_mib_max": max(gpu) if gpu else None,
            "note": seg_end_note,
        })
        for c in seg_cases:
            all_cases.append({**c, "run_id": rid, "model": RUN_MODEL[rid]})
        # In-window harness overhead is NOT derivable from created_at (case 1's stamp
        # predates the window: transaction-open artifact); use the server-log
        # idle-between-requests measurement instead (surviving sessions).


    # inter-segment gaps on the critical path
    ordered = sorted(model_rows, key=lambda r: r["start_utc"])
    gaps = []
    prev_end = GOAL_AT
    for r in ordered:
        s = datetime.fromisoformat(r["start_utc"])
        e = datetime.fromisoformat(r["end_utc"])
        gaps.append({"before_run": r["run_id"], "gap_s": round((s - prev_end).total_seconds(), 1),
                     "from": _iso(prev_end), "to": r["start_utc"]})
        prev_end = e
    gaps.append({"before_run": "(end: final commit 5f785a7)",
                 "gap_s": round((END_AT - prev_end).total_seconds(), 1),
                 "from": _iso(prev_end), "to": _iso(END_AT)})

    # ---------------- slowest cases ----------------
    slow = sorted(all_cases, key=lambda c: -(c["wall_ms"] or 0))[:20]
    slow_rows = []
    for i, c in enumerate(slow, 1):
        slow_rows.append({
            "rank": i, "model": c["model"], "run_id": c["run_id"], "scenario_id": c["scenario_id"],
            "class": c["scenario_id"][:3],
            "wall_s_monotonic": round(c["wall_ms"] / 1000, 1),
            "api_s_monotonic": round(c["api_ms"] / 1000, 1) if c["api_ms"] else None,
            "in_tokens": c["in_tok"], "out_tokens": c["out_tok"],
            "reasoning_chars": c["reasoning_chars"], "content_chars": c["content_chars"],
            "cap_hit": c["stop"] == "length", "stop_reason": c["stop"],
            "model_turns": c["model_turns"], "tool_calls": c["tool_calls"],
            "retry": False, "server_restart": False,   # measured: 0 errors/restarts in all of R6
            "all_pass": c["all_pass"],
        })

    # ---------------- phase table ----------------
    run_by_phase = {
        "R6.1-provenance": [], "R6.2-train": [r for r in ordered if "train" in r["run_id"]],
        "R6.3-freeze": [], "R6.4-dev": [r for r in ordered if r["run_id"].endswith("-dev")],
        "R6.5-test": [r for r in ordered if r["run_id"].endswith("-test")],
        "R6.6-analysis": [], "R6.7-report": [],
    }
    phase_rows = []
    marks: dict[str, dict] = {}
    for p in phases:
        marks.setdefault(p["name"], {})[p["event"]] = p["at"]
    for name in ("R6.1-provenance", "R6.2-train", "R6.3-freeze", "R6.4-dev", "R6.5-test",
                 "R6.6-analysis", "R6.7-report"):
        m = marks.get(name, {})
        if "start" not in m or "end" not in m:
            continue
        s, e = datetime.fromisoformat(m["start"]), datetime.fromisoformat(m["end"])
        runs = run_by_phase.get(name, [])
        inf = sum(r["window_s_realtime"] for r in runs)
        phase_rows.append({"phase": name, "start_utc": _iso(s), "end_utc": _iso(e),
                           "elapsed_s": round((e - s).total_seconds(), 1),
                           "model_run_window_s": round(inf, 1),
                           "non_run_s": round((e - s).total_seconds() - inf, 1),
                           "evidence": "phases.jsonl + ledger + trajectories.created_at"})

    # ---------------- surviving server-log forensics ----------------
    logs = {rid: parse_server_log(p) for rid, p in SURVIVING_LOGS.items()}

    summary = {
        "goal_at": _iso(GOAL_AT), "end_at": _iso(END_AT),
        "total_elapsed_s": round((END_AT - GOAL_AT).total_seconds(), 1),
        "sum_run_windows_s": round(sum(r["window_s_realtime"] for r in model_rows), 1),
        "inter_segment_gaps": gaps,
        "sum_gaps_s": round(sum(g["gap_s"] for g in gaps), 1),
        "per_model_window_s": {
            m: round(sum(r["window_s_realtime"] for r in model_rows if r["model"] == m), 1)
            for m in sorted(set(RUN_MODEL.values()))},
        "total_out_tokens": sum(r["out_tokens"] for r in model_rows),
        "total_in_tokens": sum(r["in_tokens"] for r in model_rows),
        "total_cases": sum(r["cases"] for r in model_rows),
        "total_cap_hits": sum(r["cap_hits"] for r in model_rows),
        "total_cap_hit_wall_s_monotonic": round(sum(r["cap_hit_wall_s"] for r in model_rows), 1),
        "monotonic_vs_realtime_by_run": {
            r["run_id"]: r["monotonic_vs_realtime"] for r in model_rows if r["monotonic_vs_realtime"]},
        "surviving_server_logs": logs,
    }

    with open(ART / "r6_performance_autopsy_phase_timing.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(phase_rows[0].keys())); w.writeheader(); w.writerows(phase_rows)
    with open(ART / "r6_performance_autopsy_model_timing.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(model_rows[0].keys())); w.writeheader(); w.writerows(model_rows)
    with open(ART / "r6_performance_autopsy_slowest_cases.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(slow_rows[0].keys())); w.writeheader(); w.writerows(slow_rows)
    (ART / "r6_performance_autopsy_summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str))
    print("\nwrote", ART)


if __name__ == "__main__":
    main()
