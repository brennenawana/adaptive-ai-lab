"""M0 §9 integration smoke — one TRAIN case through the instrumented path, live-gated.

Skipped unless FIS_LIVE_TESTS=1 (the standard lockout: NEVER set during a paired
run). Requires the frozen Qwen3.8 execution system's server on 8085. Uses the
pre-registered NON-primary probe case S01-1000000 at a tiny cap (512) — a smoke of
the WP-A/WP-D plumbing, not a measurement: it proves that a real llama.cpp response
lands in the trajectory with dual-clocked lifecycle events, per-invocation timings,
TTFT, and the reasoning/content text fields wired end-to-end.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

pytestmark = pytest.mark.skipif(os.environ.get("FIS_LIVE_TESTS") != "1",
                                reason="live test; set FIS_LIVE_TESTS=1 (never during "
                                       "a paired run)")

PROBE_SCENARIO = "S01-1000000"


def test_train_smoke_through_instrumented_path(tmp_path):
    import psycopg
    from psycopg.rows import dict_row

    from evals.runner.run_eval import OWNER_DSN, TOOLS_DSN, local_server_session
    from evals.scorers.score import score_case
    from fis_platform.model_gateway import ModelGateway, default_registry
    from fis_platform.telemetry import RunEventLog
    from fis_platform.tool_broker.broker import ToolBroker
    from scripts.m0_classify import PRIMARY_CASES
    from services.ai_orchestrator.investigate import EvidenceMode, investigate

    assert PROBE_SCENARIO not in PRIMARY_CASES

    gateway = ModelGateway(default_registry())
    manifest = gateway.registry.resolve("qwen38-27b")
    session = local_server_session(manifest.base_url or "")
    if not session.get("local_server_session"):
        pytest.skip("no llama-server on the qwen38 port")

    with psycopg.connect(OWNER_DSN) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM ground_truth.scenario_manifests WHERE scenario_id=%s",
                    (PROBE_SCENARIO,))
        m = dict(cur.fetchone())
    assert m["split"] == "train"

    events = RunEventLog(tmp_path / "smoke.events.jsonl", run_id="m0-smoke-train")
    events.run_start(planned_cases=1)
    events.event("case_start", scenario_id=PROBE_SCENARIO)

    async def go():
        with ToolBroker(TOOLS_DSN) as broker:
            return await investigate(
                m["case_id"], gateway=gateway, broker=broker, model_ref="qwen38-27b",
                experiment_arm="M0-smoke", mode=EvidenceMode.FIXED_EVIDENCE,
                scenario_id=PROBE_SCENARIO, prompt_ref="cause_action_directed",
                runtime_context={"smoke": "m0"}, max_tokens=512)

    result, traj = asyncio.run(go())
    inv = traj.model_invocations[0]

    # WP-D per-invocation stats, from a REAL llama.cpp response
    assert inv.timings is not None and "prompt_ms" in inv.timings
    assert inv.latency.ttft_ms is not None and inv.latency.ttft_ms > 0
    assert inv.usage.input_tokens > 0 and inv.usage.output_tokens > 0
    assert inv.stop_reason in ("stop", "length")
    # WP-A text fields wired (512 tokens almost certainly truncates mid-reasoning)
    if inv.stop_reason == "length":
        assert (inv.reasoning_text or inv.content_text)
    # the scorer runs end-to-end on the smoke case
    score = score_case(result=result, trajectory=traj, manifest=m, run_id="m0-smoke")
    events.event("case_end", scenario_id=PROBE_SCENARIO, all_pass=score.all_pass,
                 stop_reason=inv.stop_reason, ttft_ms=inv.latency.ttft_ms)
    events.run_end(status="completed", cases_done=1)

    lines = [json.loads(ln)
             for ln in (tmp_path / "smoke.events.jsonl").read_text().splitlines()]
    assert [ln["event"] for ln in lines] == ["run_start", "case_start", "case_end",
                                             "run_end"]
    assert all("ts_realtime" in ln and "ts_monotonic" in ln for ln in lines)
