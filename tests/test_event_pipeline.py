"""Event pipeline: idempotency and mapping behaviour.

These are the tests that justify the event layer existing. If dedupe and stale
mapping were still hand-authored rows, none of them could fail.
"""

import os
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from fis_platform.events.envelope import DomainEvent, ProviderEvent, Subject
from services.integration_service.consumer import IntegrationConsumer, map_status

OWNER_DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")
T0 = datetime(2026, 1, 6, 9, 0, tzinfo=timezone.utc)


def _pg_up() -> bool:
    try:
        with psycopg.connect(OWNER_DSN, connect_timeout=3):
            return True
    except psycopg.Error:
        return False


def _event(**kw) -> ProviderEvent:
    base = dict(
        provider="northpay", provider_event_id="pe_1", event_type="settlement.created",
        occurred_at=T0, scenario_id="S01-3000000",
        raw_payload={"amount": 4210, "status": "APPROVED"},
    )
    return ProviderEvent(**{**base, **kw})


# ------------------------------------------------------------------ envelope
def test_safe_idempotency_requires_a_key():
    assert _event(idempotency_key="idem-1").has_safe_idempotency
    assert not _event(idempotency_key=None).has_safe_idempotency


def test_unsafe_dedupe_key_is_marked_as_such():
    """A key derived from provider_event_id alone must be visibly unsafe — it
    cannot distinguish a retry from a genuine second occurrence."""
    assert _event(idempotency_key=None).dedupe_key.startswith("unsafe:")


def test_payload_hash_is_stable_and_order_independent():
    a = _event(raw_payload={"amount": 1, "status": "APPROVED"})
    b = _event(raw_payload={"status": "APPROVED", "amount": 1})
    assert a.payload_hash == b.payload_hash


def test_occurred_at_is_independent_of_published_at():
    """S07 depends on these diverging — a reversal that happened before a
    settlement can still be published after it."""
    late = _event(occurred_at=T0, published_at=T0 + timedelta(hours=2))
    assert late.occurred_at < late.published_at


def test_subject_hierarchy():
    assert Subject.webhook("northpay") == "fis.webhook.received.northpay"
    assert Subject.domain("settlement.created") == "fis.domain.normalized.settlement.created"


# ------------------------------------------------------------------- mapper
def test_current_mapper_understands_current_vocabulary():
    state, ok = map_status("APPROVED_WITH_CONDITIONS", 4)
    assert (state, ok) == ("approved", True)


def test_stale_mapper_misreads_a_new_status_as_failure():
    """The S09 defect, reproduced by the mapper rather than written by a fixture.
    v2 predates APPROVED_WITH_CONDITIONS, so a genuine approval becomes 'failed'."""
    state, ok = map_status("APPROVED_WITH_CONDITIONS", 2)
    assert state == "failed"
    assert ok is False, "an unrecognised status must be flagged, not silently mapped"


def test_stale_mapper_still_handles_statuses_it_does_know():
    assert map_status("APPROVED", 2) == ("approved", True)


# ----------------------------------------------------------------- pipeline
pytestmark_db = pytest.mark.skipif(not _pg_up(), reason="FIS Postgres not running")


@pytestmark_db
@pytest.mark.asyncio
async def test_duplicate_with_idempotency_key_is_deduplicated():
    """S01: provider re-delivers, dedupe works, exactly one downstream effect."""
    with psycopg.connect(OWNER_DSN) as conn:
        conn.execute("DELETE FROM integration.dedupe_ledger WHERE scenario_id = 'T-dedupe'")
        c = IntegrationConsumer(conn)
        e1 = _event(idempotency_key="idem-A", attempt=1, scenario_id="T-dedupe")
        e2 = _event(idempotency_key="idem-A", attempt=2, scenario_id="T-dedupe")

        await c.handle(e1.model_dump(mode="json"))
        await c.handle(e2.model_dump(mode="json"))
        conn.rollback()

    assert len(c.emitted) == 1, "a deduplicated redelivery must produce no second effect"


@pytestmark_db
@pytest.mark.asyncio
async def test_duplicate_without_idempotency_key_is_processed_twice():
    """S02: the defect. Without a key the consumer cannot tell retry from reality,
    so two downstream effects occur — which is the double posting."""
    with psycopg.connect(OWNER_DSN) as conn:
        c = IntegrationConsumer(conn)
        e1 = _event(idempotency_key=None, attempt=1, scenario_id="T-nodedupe")
        e2 = _event(idempotency_key=None, attempt=2, scenario_id="T-nodedupe")

        await c.handle(e1.model_dump(mode="json"))
        await c.handle(e2.model_dump(mode="json"))
        conn.rollback()

    assert len(c.emitted) == 2, "without idempotency the duplicate must NOT be suppressed"


@pytestmark_db
@pytest.mark.asyncio
async def test_stale_mapper_leaves_a_discoverable_breadcrumb():
    """The investigator has to be able to find it — otherwise S09 is unsolvable
    rather than merely hard."""
    with psycopg.connect(OWNER_DSN) as conn:
        c = IntegrationConsumer(conn, mapping_version=2)
        await c.handle(_event(
            event_type="verification.updated",
            raw_payload={"status": "APPROVED_WITH_CONDITIONS"},
            scenario_id="T-stale",
        ).model_dump(mode="json"))
        conn.rollback()

    assert c.emitted[0].normalized_state == "failed"
    assert c.emitted[0].payload["status"] == "APPROVED_WITH_CONDITIONS", (
        "raw payload must be preserved so raw-vs-normalized can be compared"
    )
