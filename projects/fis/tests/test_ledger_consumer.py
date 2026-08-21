"""Ledger consumer behaviour.

The reversal-race test is the one that matters: it asserts the race is genuinely
produced by publish order, not by a fixture writing inverted timestamps.
"""

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest

from fis_platform.events.envelope import DomainEvent
from services.ledger_service.consumer import LedgerConsumer

OWNER_DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")
T0 = datetime(2026, 1, 6, 9, 0, tzinfo=timezone.utc)


def _pg_up() -> bool:
    try:
        with psycopg.connect(OWNER_DSN, connect_timeout=3):
            return True
    except psycopg.Error:
        return False


pytestmark = pytest.mark.skipif(not _pg_up(), reason="FIS Postgres not running")


def _domain(ntype: str, *, occurred_at: datetime, payload: dict,
            scenario: str = "T-ledger") -> dict:
    return DomainEvent(
        causation_id=uuid4(), normalized_type=ntype, normalized_state="settled",
        mapping_version=4, provider_event_id=f"pe_{uuid4().hex[:8]}",
        occurred_at=occurred_at, payload=payload, scenario_id=scenario,
    ).model_dump(mode="json")


@pytest.fixture
def account():
    """A throwaway customer+account, rolled back after the test."""
    with psycopg.connect(OWNER_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO customer.customers
                     (customer_id, display_name, dob, country, onboarding_state,
                      created_at, scenario_id)
                   VALUES ('cus_t','T Person','1990-01-01','GB','active',now(),'T-ledger')
                   ON CONFLICT DO NOTHING""")
            cur.execute(
                """INSERT INTO ledger.accounts
                     (account_id, customer_id, status, currency, available_balance,
                      ledger_balance, opened_at, scenario_id)
                   VALUES ('acc_t','cus_t','active','GBP',100000,100000,now(),'T-ledger')
                   ON CONFLICT DO NOTHING""")
        yield conn, "acc_t"
        conn.rollback()


async def test_settlement_produces_a_debit(account):
    conn, acct = account
    c = LedgerConsumer(conn)
    await c.handle(_domain("settlement.created", occurred_at=T0,
                           payload={"account_id": acct, "amount": 4210}))
    assert len(c.posted) == 1


async def test_event_with_no_posting_rule_is_skipped_not_dropped_silently(account):
    """Identity events must flow past the ledger — but visibly, so a missing
    posting can be distinguished from an unnoticed one."""
    conn, acct = account
    c = LedgerConsumer(conn)
    await c.handle(_domain("verification.updated", occurred_at=T0,
                           payload={"account_id": acct, "amount": 1}))
    assert c.posted == []
    assert c.skipped == [("verification.updated", "no_posting_rule")]


async def test_posting_uses_occurred_at_not_arrival_time(account):
    """If entries were stamped with arrival time the reversal race would be
    invisible — the very thing S07 tests."""
    conn, acct = account
    c = LedgerConsumer(conn)
    await c.handle(_domain("settlement.created", occurred_at=T0,
                           payload={"account_id": acct, "amount": 500}))
    with conn.cursor() as cur:
        cur.execute("SELECT posted_at FROM ledger.entries WHERE entry_id = %s",
                    (c.posted[0],))
        assert cur.fetchone()[0] == T0


async def test_reversal_race_is_produced_by_publish_order(account):
    """S07, emergent.

    The reversal OCCURRED before the settlement but is PUBLISHED after it. Posting
    in arrival order with occurred_at timestamps yields entries whose insertion
    order disagrees with their event order — which is the operational hazard.
    """
    conn, acct = account
    c = LedgerConsumer(conn)

    # Published second, but occurred earlier.
    await c.handle(_domain("settlement.created", occurred_at=T0 + timedelta(hours=2),
                           payload={"account_id": acct, "amount": 4210}))
    await c.handle(_domain("authorization.reversed", occurred_at=T0,
                           payload={"account_id": acct, "amount": 4210}))

    assert len(c.posted) == 2
    anomalies = [a for a in c.ordering_anomalies() if a[1] == "T-ledger"]
    assert anomalies, "publish order did not actually create an ordering anomaly"


async def test_corrupted_amount_is_posted_faithfully(account):
    """S06: the ledger is not the bug, it is where the bug becomes visible.
    A consumer that 'helpfully' corrected the amount would erase the evidence."""
    conn, acct = account
    c = LedgerConsumer(conn)
    await c.handle(_domain("settlement.created", occurred_at=T0,
                           payload={"account_id": acct, "amount": 4120}))
    with conn.cursor() as cur:
        cur.execute("SELECT amount FROM ledger.entries WHERE entry_id = %s",
                    (c.posted[0],))
        assert cur.fetchone()[0] == 4120
