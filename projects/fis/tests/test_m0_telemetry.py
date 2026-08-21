"""M0 WP-D — telemetry floor (NEXT_STEP_M0.md § 6-D, § 9).

Required by the doc: dual-clock fields present and sane; a run-end line written on
SIGINT. The SIGINT test runs a real child process and delivers a real signal — the
guarantee under test is exactly "the process died and the line is there anyway".
"""

from __future__ import annotations

import json
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.telemetry import ResourceSampler, RunEventLog, dual_clock


def test_dual_clock_fields_present_and_sane():
    a = dual_clock()
    assert set(a) == {"ts_realtime", "ts_monotonic"}
    parsed = datetime.fromisoformat(a["ts_realtime"])
    assert parsed.tzinfo is not None
    assert abs((datetime.now(UTC) - parsed).total_seconds()) < 5
    b = dual_clock()
    assert b["ts_monotonic"] >= a["ts_monotonic"]
    assert dual_clock("started")["started_monotonic"] > 0


def test_run_event_log_lines_carry_both_clocks_and_context(tmp_path):
    log = RunEventLog(tmp_path / "e.jsonl", run_id="M0-x-train-diag", arm="M0")
    log.run_start(planned_cases=15)
    log.event("case_start", scenario_id="S02-1001001", index=1)
    log.run_end(status="completed", cases_done=15)
    lines = [json.loads(ln) for ln in (tmp_path / "e.jsonl").read_text().splitlines()]
    assert [ln["event"] for ln in lines] == ["run_start", "case_start", "run_end"]
    for ln in lines:
        assert ln["run_id"] == "M0-x-train-diag" and ln["arm"] == "M0"
        assert "ts_realtime" in ln and "ts_monotonic" in ln
    assert lines[-1]["status"] == "completed" and lines[-1]["cases_done"] == 15


def test_run_end_is_written_at_most_once(tmp_path):
    log = RunEventLog(tmp_path / "e.jsonl", run_id="r")
    log.run_start()
    assert log.run_end(status="completed") is not None
    assert log.run_end(status="interrupted-atexit") is None
    events = [json.loads(ln)["event"]
              for ln in (tmp_path / "e.jsonl").read_text().splitlines()]
    assert events.count("run_end") == 1


def test_sigint_leaves_a_run_end_line(tmp_path):
    """A child process installs the log, starts a run, and blocks; SIGINT must leave
    a run_end line saying it was interrupted (the R6 Bonsai-probe gap)."""
    events_path = tmp_path / "events.jsonl"
    child = subprocess.Popen(
        [sys.executable, "-c", (
            "import sys, time\n"
            f"sys.path.insert(0, {str(Path(__file__).resolve().parents[1])!r})\n"
            "from fis_platform.telemetry import RunEventLog\n"
            f"log = RunEventLog({str(events_path)!r}, run_id='M0-sigint-train-diag')\n"
            "log.run_start(planned_cases=1)\n"
            "print('ready', flush=True)\n"
            "time.sleep(60)\n")],
        stdout=subprocess.PIPE, text=True)
    assert child.stdout is not None
    assert child.stdout.readline().strip() == "ready"
    child.send_signal(signal.SIGINT)
    child.wait(timeout=15)
    assert child.returncode != 0                    # the interrupt was not swallowed
    lines = [json.loads(ln) for ln in events_path.read_text().splitlines()]
    assert lines[0]["event"] == "run_start"
    assert lines[-1]["event"] == "run_end"
    assert "SIGINT" in lines[-1]["status"]


def test_resource_sampler_writes_dual_clocked_samples(tmp_path):
    path = tmp_path / "samples.jsonl"
    with ResourceSampler(path, interval_s=0.05, context={"run_id": "r"}):
        time.sleep(0.2)
    lines = [json.loads(ln) for ln in path.read_text().splitlines()]
    assert len(lines) >= 2
    for ln in lines:
        assert ln["run_id"] == "r"
        assert "ts_realtime" in ln and "ts_monotonic" in ln
    # host sampling works everywhere Linux; GPU fields are best-effort
    assert any("host_mem_available_kib" in ln for ln in lines)
