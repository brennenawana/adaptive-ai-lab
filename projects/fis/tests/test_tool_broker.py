"""Broker behaviour, and the ground-truth boundary.

The boundary tests are the important ones: if the tool role can read
ground_truth.scenario_manifests, every eval score in the project is worthless.
"""

import os

import psycopg
import pytest

from fis_platform.tool_broker.broker import ToolBroker
from fis_platform.tool_broker.definitions import BY_NAME, TOOLS, openai_tool_specs

TOOLS_DSN = os.environ.get(
    "FIS_TOOLS_DSN", "postgresql://fis_tools:fis_tools_local_dev@127.0.0.1:5433/fis"
)
OWNER_DSN = os.environ.get(
    "FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis"
)


def _pg_up() -> bool:
    try:
        with psycopg.connect(OWNER_DSN, connect_timeout=3):
            return True
    except psycopg.Error:
        return False


pytestmark = pytest.mark.skipif(not _pg_up(), reason="FIS Postgres not running")


# ----------------------------------------------------------- the boundary
def test_tool_role_cannot_read_ground_truth():
    """The database refuses, independently of any Python-side check."""
    with psycopg.connect(TOOLS_DSN) as conn, conn.cursor() as cur:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            cur.execute("SELECT root_cause FROM ground_truth.scenario_manifests LIMIT 1")


def test_tool_role_cannot_read_trajectories():
    with psycopg.connect(TOOLS_DSN) as conn, conn.cursor() as cur:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            cur.execute("SELECT * FROM learning.trajectories LIMIT 1")


def test_tool_role_cannot_write():
    """default_transaction_read_only means even a mistaken INSERT fails."""
    with psycopg.connect(TOOLS_DSN) as conn, conn.cursor() as cur:
        with pytest.raises(psycopg.Error):
            cur.execute("INSERT INTO cases.cases (case_id, category, summary, status, "
                        "opened_at, scenario_id) VALUES ('x','y','z','open',now(),'s')")


def test_owner_can_read_ground_truth():
    """The scorer must still be able to — otherwise nothing can grade."""
    with psycopg.connect(OWNER_DSN) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM ground_truth.scenario_manifests")
        assert cur.fetchone()[0] >= 0


# ----------------------------------------------------------- definitions
def test_every_tool_forbids_ground_truth():
    for t in TOOLS:
        assert "ground_truth" in t.forbidden_schemas


def test_all_tools_have_handlers():
    from fis_platform.tool_broker.broker import HANDLERS
    assert set(HANDLERS) == set(BY_NAME), "a declared tool with no handler would 500 at runtime"


def test_openai_specs_render():
    specs = openai_tool_specs()
    assert len(specs) == len(TOOLS)
    assert all(s["function"]["description"] for s in specs)


# ----------------------------------------------------------- behaviour
def test_unknown_tool_is_denied_not_crashed():
    with ToolBroker(TOOLS_DSN) as b:
        result, call = b.invoke("drop_everything", {})
    assert call.status == "denied"
    assert call.error_code == "unknown_tool"
    assert "error" in result


def test_missing_case_returns_not_found():
    with ToolBroker(TOOLS_DSN) as b:
        result, call = b.invoke("get_case", {"case_id": "case_does_not_exist"})
    assert call.status == "error"
    assert call.error_code == "not_found"


def test_failed_call_does_not_poison_later_calls():
    """A failed statement aborts the transaction; without a rollback every
    subsequent tool call would fail too and look like a cascade of real errors."""
    with ToolBroker(TOOLS_DSN) as b:
        b.invoke("get_ledger_entries", {"account_id": "nope"})
        with psycopg.connect(OWNER_DSN) as c, c.cursor() as cur:
            cur.execute("SELECT case_id FROM cases.cases LIMIT 1")
            row = cur.fetchone()
        if row:
            _, call = b.invoke("get_case", {"case_id": row[0]})
            assert call.status == "success", "broker did not recover from a failed call"


def test_calls_are_recorded_in_order():
    with ToolBroker(TOOLS_DSN) as b:
        b.invoke("get_case", {"case_id": "a"})
        b.invoke("get_case", {"case_id": "b"})
    assert [c.sequence for c in b.calls] == [0, 1]
    assert all(c.args_hash for c in b.calls)


# ---------------------------------------------------------------- S07 visibility
def test_ledger_entries_expose_posting_order(pg_required=None):
    """S07's hazard must be visible through the TOOL, not just in the database.

    The reversal race lives in the disagreement between `posting_seq` (the order
    postings were made) and `posted_at` (when the events occurred). If the tool
    sorts by `posted_at` and omits `posting_seq`, the ledger reads as perfectly
    chronological and net zero — so the only conclusion the evidence supports is
    that nothing is wrong, and `reversal_race` becomes unreachable by correct
    reasoning while remaining guessable from the case summary.

    That is the same defect as unreachable webhook evidence, one layer down: the
    fact exists, and no tool call surfaces it.
    """
    import os

    import psycopg

    from fis_platform.tool_broker.broker import ToolBroker

    dsn = os.environ.get("FIS_TOOLS_DSN",
                         "postgresql://fis_tools:fis_tools_local_dev@127.0.0.1:5433/fis")
    try:
        with psycopg.connect(dsn, connect_timeout=3):
            pass
    except psycopg.Error:
        import pytest
        pytest.skip("FIS Postgres not running")

    owner = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")
    with psycopg.connect(owner) as conn:
        row = conn.execute(
            "SELECT subject_ids->>'account_id' FROM ground_truth.scenario_manifests "
            "WHERE scenario_id LIKE 'S07%' AND split = 'test' LIMIT 1"
        ).fetchone()
    if row is None or row[0] is None:
        import pytest
        pytest.skip("no S07 scenario generated yet")

    with ToolBroker(dsn) as broker:
        res, _ = broker.invoke("get_ledger_entries", {"account_id": row[0]})

    entries = res["entries"]
    assert entries, "S07 account has no ledger entries"
    assert all("posting_seq" in e for e in entries), (
        "posting_seq must be returned — without it the reversal race is invisible"
    )
    # Returned in insertion order, which is the misleading view the case describes.
    seqs = [e["posting_seq"] for e in entries]
    assert seqs == sorted(seqs), "entries must be returned in posting order"

    inverted = any(b["posted_at"] < a["posted_at"] for a, b in zip(entries, entries[1:]))
    assert inverted, (
        "S07 must show a posting whose event time precedes its predecessor's — "
        "that disagreement is the whole scenario"
    )
