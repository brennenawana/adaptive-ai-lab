"""M-STAT deferred telemetry (M0 §6-D items landed here — M_STAT_IMPLEMENTATION_MAP.md
§14): ToolBroker dual-clock stamps + optional on_event spans, sampler clock_offset_s,
and migration 009's no-backfill inserted_at shape.

The broker/on_event tests deliberately never open a DB connection: `invoke()` on an
unknown tool name returns before touching `self._conn` at all (see broker.py), so a
`ToolBroker` constructed without `__enter__` is enough to exercise the dual-clock
stamping and the on_event hook end to end.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import UTC, datetime
from pathlib import Path

import psycopg
import pytest

from fis_platform.telemetry import ResourceSampler
from fis_platform.tool_broker.broker import ToolBroker
from schemas.tool import ToolCall

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MIGRATION_PATH = _REPO_ROOT / "infra" / "migrations" / "009_inserted_at.sql"
_TABLES = ("trajectories", "case_scores", "model_outputs", "routing_decisions")

OWNER_DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")


# --------------------------------------------------------------- A. broker stamps
def test_broker_stamps_toolcall_with_dual_clock_on_the_denied_path():
    """An unknown-tool call never touches the DB, so this needs no connection — and
    the denied path is exactly the one the spec calls out as still needing stamps."""
    broker = ToolBroker("postgresql://unused/unused")
    before = datetime.now(UTC)
    _, call = broker.invoke("does_not_exist", {})
    after = datetime.now(UTC)

    assert call.status == "denied" and call.error_code == "unknown_tool"
    assert call.ts_realtime is not None and call.ts_monotonic is not None
    stamped = datetime.fromisoformat(call.ts_realtime)
    assert stamped.tzinfo is not None
    # dual_clock()'s realtime stamp is millisecond-resolution (rounds toward the
    # nearest millisecond), so a tight microsecond-precision bracket can legitimately
    # miss by a fraction of a millisecond; a generous window still catches a stamp
    # that is wrong by seconds, which is the failure this guards against.
    assert abs((stamped - before).total_seconds()) < 1
    assert abs((after - stamped).total_seconds()) < 1
    assert isinstance(call.ts_monotonic, float) and call.ts_monotonic > 0


def test_on_event_sequence_emitted_including_denied_path():
    events: list[tuple[str, dict]] = []

    def sink(event: str, **fields):
        events.append((event, fields))

    broker = ToolBroker("postgresql://unused/unused", on_event=sink)
    broker.invoke("does_not_exist", {})

    assert [e for e, _ in events] == ["tool_call_start", "tool_call_end"]
    start_fields, end_fields = events[0][1], events[1][1]
    for f in (start_fields, end_fields):
        assert f["tool"] == "does_not_exist" and f["sequence"] == 0
        assert "ts_realtime" in f and "ts_monotonic" in f
    assert end_fields["status"] == "denied"
    assert end_fields["error_code"] == "unknown_tool"
    assert isinstance(end_fields["latency_ms"], int)


def test_on_event_sequence_advances_across_calls():
    events: list[str] = []
    broker = ToolBroker("postgresql://unused/unused",
                        on_event=lambda event, **f: events.append(f"{event}:{f['sequence']}"))
    broker.invoke("nope_one", {})
    broker.invoke("nope_two", {})
    assert events == ["tool_call_start:0", "tool_call_end:0",
                      "tool_call_start:1", "tool_call_end:1"]
    assert [c.sequence for c in broker.calls] == [0, 1]


def test_on_event_exception_is_swallowed_not_raised():
    """A broken telemetry sink must degrade to 'no telemetry', never break the call
    the guard docstring promises."""
    def bad_sink(event, **fields):
        raise RuntimeError("telemetry backend is down")

    broker = ToolBroker("postgresql://unused/unused", on_event=bad_sink)
    result, call = broker.invoke("does_not_exist", {})   # must not raise

    assert call.status == "denied"
    assert result == {"error": "unknown tool 'does_not_exist'"}
    assert len(broker.calls) == 1


def test_old_style_construction_without_on_event_is_unchanged():
    """Every existing caller — `ToolBroker(dsn)`, no on_event — keeps working."""
    broker = ToolBroker("postgresql://unused/unused")
    assert broker.on_event is None
    result, call = broker.invoke("does_not_exist", {})
    assert call.status == "denied" and call.error_code == "unknown_tool"
    assert result == {"error": "unknown tool 'does_not_exist'"}


# ------------------------------------------------------------- B. ToolCall compat
def test_toolcall_validates_without_the_new_fields():
    """A dict shaped like a pre-M-STAT persisted trajectory (no ts_realtime /
    ts_monotonic keys at all) must still validate — historical trajectories are
    read back through this model."""
    payload = {
        "tool": "get_case", "version": 1, "args_hash": "deadbeef",
        "status": "success", "latency_ms": 12, "sequence": 0,
    }
    call = ToolCall.model_validate(payload)
    assert call.ts_realtime is None
    assert call.ts_monotonic is None


def test_toolcall_accepts_the_new_fields():
    call = ToolCall(tool="get_case", version=1, args_hash="deadbeef", status="success",
                    latency_ms=12, sequence=0, ts_realtime="2026-08-21T00:00:00.000+00:00",
                    ts_monotonic=123.456)
    assert call.ts_monotonic == 123.456


# ---------------------------------------------------------------- C. sampler
def test_sampler_lines_carry_a_sane_clock_offset_s():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "samples.jsonl"
        with ResourceSampler(path, interval_s=0.05, context={"run_id": "r"}):
            time.sleep(0.2)
        lines = [json.loads(ln) for ln in path.read_text().splitlines()]

    assert len(lines) >= 2
    reference_offset = time.time() - time.monotonic()
    for ln in lines:
        assert "clock_offset_s" in ln
        assert isinstance(ln["clock_offset_s"], (int, float))
        # Both clocks tick at (approximately) the same rate, so a fresh offset taken
        # right after the run must agree with every sampled one to within a couple
        # of seconds — the whole point of the field is that a MUCH bigger gap, or a
        # gap that widens over the run, is the WSL2 skew becoming visible.
        assert abs(ln["clock_offset_s"] - reference_offset) < 5


# ------------------------------------------------------ D. migration 009 shape
def _strip_line_comments(sql: str) -> str:
    """Drop everything from `--` to end of line, so a prose comment that mentions
    `DEFAULT now()` (explaining the defect being fixed) cannot be mistaken for SQL
    code carrying a DEFAULT. Line-comment-only stripping is safe for this file: no
    string literal in it contains `--`."""
    return "\n".join(re.sub(r"--.*$", "", line) for line in sql.splitlines())


def _statements(sql: str) -> list[str]:
    return [s.strip() for s in _strip_line_comments(sql).split(";") if s.strip()]


def test_migration_009_file_exists():
    assert _MIGRATION_PATH.is_file(), _MIGRATION_PATH


def test_migration_009_no_add_column_statement_carries_a_default():
    """Text-level guard against the backfill hazard: a DEFAULT written directly on
    ADD COLUMN would be evaluated once and stamped onto every existing row."""
    stmts = _statements(_MIGRATION_PATH.read_text())
    add_column_stmts = [s for s in stmts if re.search(r"ADD\s+COLUMN", s, re.IGNORECASE)]
    assert len(add_column_stmts) == len(_TABLES), "expected one ADD COLUMN per table"
    for stmt in add_column_stmts:
        assert "DEFAULT" not in stmt.upper(), (
            f"an ADD COLUMN statement must never carry a DEFAULT (backfill hazard): {stmt!r}"
        )
        assert re.search(r"IF\s+NOT\s+EXISTS", stmt, re.IGNORECASE), (
            f"ADD COLUMN must be idempotent: {stmt!r}"
        )


def test_migration_009_sets_default_as_a_separate_statement_per_table():
    sql = _MIGRATION_PATH.read_text()
    stmts = _statements(sql)
    for table in _TABLES:
        qualified = f"learning.{table}"
        add_stmt = next((s for s in stmts if re.search(
            rf"ALTER TABLE\s+{re.escape(qualified)}\b.*ADD\s+COLUMN", s,
            re.IGNORECASE | re.DOTALL)), None)
        assert add_stmt is not None, f"{qualified}: no ADD COLUMN IF NOT EXISTS inserted_at"

        set_default_stmt = next((s for s in stmts if re.search(
            rf"ALTER TABLE\s+{re.escape(qualified)}\b.*ALTER\s+COLUMN\s+inserted_at\s+"
            r"SET\s+DEFAULT\s+clock_timestamp\(\)", s, re.IGNORECASE | re.DOTALL)), None)
        assert set_default_stmt is not None, (
            f"{qualified}: no separate SET DEFAULT clock_timestamp() statement"
        )
        assert set_default_stmt is not add_stmt, (
            f"{qualified}: SET DEFAULT must be a statement distinct from ADD COLUMN"
        )
        # And the ADD COLUMN statement itself must precede the SET DEFAULT one in
        # the file, so a linear `psql -f` apply never sees the default first.
        assert sql.index(add_stmt) < sql.index(set_default_stmt)


# ---------------------------------------------------- DB-gated: historical rows
def _pg_up() -> bool:
    try:
        with psycopg.connect(OWNER_DSN, connect_timeout=3):
            return True
    except psycopg.Error:
        return False


def _column_exists(conn, schema: str, table: str, column: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name = %s AND column_name = %s",
        (schema, table, column),
    ).fetchone() is not None


def test_historical_rows_keep_inserted_at_null_when_migration_is_applied():
    """Live-DB guard against the exact hazard the migration's ordering avoids: no
    row created before this M-STAT unit landed may carry a non-NULL inserted_at.
    Skips cleanly when Postgres is down, and again when migration 009 has not been
    applied yet (this unit does not run `make migrate` — the integrator does)."""
    if not _pg_up():
        pytest.skip("FIS Postgres not running")
    with psycopg.connect(OWNER_DSN) as conn:
        if not all(_column_exists(conn, "learning", t, "inserted_at") for t in _TABLES):
            pytest.skip("migration 009 not applied yet (inserted_at column absent)")
        for table in _TABLES:
            bad = conn.execute(
                f"SELECT count(*) FROM learning.{table} "
                f"WHERE created_at < '2026-08-21' AND inserted_at IS NOT NULL"
            ).fetchone()[0]
            assert bad == 0, (
                f"learning.{table}: historical (pre-migration) rows must keep "
                f"inserted_at NULL — {bad} row(s) do not"
            )
