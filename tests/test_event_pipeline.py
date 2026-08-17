"""Event pipeline: idempotency and mapping behaviour.

These are the tests that justify the event layer existing. If dedupe and stale
mapping were still hand-authored rows, none of them could fail.
"""

import os
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from fis_platform.events.envelope import DomainEvent, ProviderEvent, Subject
from fis_platform.events.projection import project
from scenarios.generator.run import build
from services.integration_service.consumer import (
    IntegrationConsumer,
    map_amount,
    map_status,
)

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


def test_only_the_defective_release_corrupts_amounts():
    """v2 is stale about vocabulary but handles money correctly. Conflating the two
    would make S06 and S09 the same defect wearing different labels."""
    assert map_amount(4210, 4) == (4210, True)
    assert map_amount(4210, 2) == (4210, True)
    assert map_amount(4210, 3) == (4201, False)


def test_transposed_amount_differs_by_a_multiple_of_nine():
    """The arithmetic signature a reconciliation analyst looks for, and the reason
    this defect is worth modelling rather than a random perturbation."""
    for amount in (4210, 12_345, 99_01, 500):
        corrupted, faithful = map_amount(amount, 3)
        if faithful:
            continue
        assert abs(corrupted - amount) % 9 == 0


# ------------------------------------------------- emergent scenario behaviour
# These assert on the scenarios as built, through the real consumer logic. Before
# the migration none of them could fail: the rows were written by the fixture, so
# they described the generator rather than the pipeline.
#
# Since Suite v3 every card-holding class also publishes its background purchases
# (`catalog._background`), so the assertions select the INJECTED events by the
# provider ref the builder gave them rather than assuming they are the only ones.
def _injected(world, provider_ref):
    return [e for e in world.published if e.provider_event_id == provider_ref]


def _entries_for(p, provider_ref, world):
    sett = next(s for s in world.settlements if s["provider_ref"] == provider_ref)
    return [e for e in p.entries if e["reference_id"] == sett["settlement_id"]]


def test_s01_dedupe_suppresses_the_second_effect():
    world, manifest = build("S01", 3_000_500)
    p = project(world.published, world.mapping_versions)

    pev = world.settlements[0]["provider_ref"]          # the injected settlement
    injected = _injected(world, pev)
    assert len(injected) == 2, "S01 must actually deliver twice"
    statuses = [d["status"] for d in p.deliveries if d["provider_event_id"] == pev]
    assert statuses == ["processed", "deduplicated"]
    assert len(_entries_for(p, pev, world)) == 1, "dedupe worked, so exactly one posting exists"
    assert manifest["root_cause"] == "duplicate_webhook_handled"


def test_s02_missing_key_produces_a_real_double_posting():
    world, _ = build("S02", 3_000_500)
    p = project(world.published, world.mapping_versions)

    pev = world.settlements[0]["provider_ref"]
    statuses = [d["status"] for d in p.deliveries if d["provider_event_id"] == pev]
    assert statuses == ["processed", "processed"]
    entries = _entries_for(p, pev, world)
    assert len(entries) == 2, "without an idempotency key both deliveries must post"
    assert entries[0]["amount"] == entries[1]["amount"]


def test_s01_and_s02_differ_by_exactly_the_idempotency_key():
    """The ontology calls these 'same surface, opposite verdicts'. If the scenarios
    differed in any other way the eval would be measuring that difference instead."""
    s01, _ = build("S01", 3_000_500)
    s02, _ = build("S02", 3_000_500)

    def shape(w):
        return [(e.event_type, e.attempt, sorted(e.raw_payload)) for e in w.published]

    assert shape(s01) == shape(s02)
    inj01 = _injected(s01, s01.settlements[0]["provider_ref"])
    inj02 = _injected(s02, s02.settlements[0]["provider_ref"])
    assert [e.has_safe_idempotency for e in inj01] == [True, True]
    assert [e.has_safe_idempotency for e in inj02] == [False, False]
    # Background is identical in kind on both sides: keyed, posted once each.
    for w in (s01, s02):
        bg = [e for e in w.published if e.provider_event_id != w.settlements[0]["provider_ref"]]
        assert bg and all(e.has_safe_idempotency for e in bg)


def test_s06_amount_is_corrupted_by_the_mapper_not_by_the_fixture():
    world, manifest = build("S06", 3_000_500)
    p = project(world.published, world.mapping_versions)

    sett = world.settlements[0]                          # the injected settlement
    entry = _entries_for(p, sett["provider_ref"], world)[0]
    assert world.mapping_versions[0] == 3, "the injected settlement arrived under the bad release"
    assert entry["amount"] != sett["amount"], "the v3 mapper did not actually corrupt the amount"
    assert abs(entry["amount"] - sett["amount"]) % 9 == 0
    assert entry["entry_id"] == manifest["required_evidence"][1]
    # The raw payload must survive uncorrupted or the discrepancy is undiagnosable.
    ev = next(e for e in p.events if e["provider_event_id"] == sett["provider_ref"])
    assert ev["raw_payload"]["amount"] == sett["amount"]
    assert ev["mapping_version"] == 3
    # The release was rolled back before the background arrived: every other
    # posting is faithful and says so. Otherwise the named settlement would be one
    # of four with the same defect and evidence recall would be a coin toss.
    for s in world.settlements[1:]:
        (bg,) = _entries_for(p, s["provider_ref"], world)
        assert bg["amount"] == s["amount"]
    assert set(world.mapping_versions[1:]) == {4}


def test_s07_race_comes_from_publish_order_not_from_timestamps():
    """The determinism claim, tested rather than asserted.

    The entries are written in publish order but stamped with `occurred_at`, so the
    later-published event carries the earlier timestamp. Reverse the publish order
    and the anomaly is gone — which is what it means for the race to be deliberate.
    """
    world, _ = build("S07", 3_000_500)
    p = project(world.published, world.mapping_versions)

    assert [e.event_type for e in world.published[:2]] == [
        "authorization.reversed", "settlement.created"
    ], "the reversal must be published first — that IS the race"
    assert p.entries[0]["direction"] == "credit"
    assert p.entries[1]["direction"] == "debit"
    assert p.entries[1]["posted_at"] < p.entries[0]["posted_at"], (
        "the settlement occurred before the reversal but posted after it"
    )
    # Delivery is what is late: both webhooks are received after their events.
    for e in world.published[:2]:
        assert e.published_at > e.occurred_at
    # Background purchases follow the race and add no second inversion.
    later = p.entries[2:]
    assert later and all(a["posted_at"] <= b["posted_at"] for a, b in zip(later, later[1:]))
    assert later[0]["posted_at"] > p.entries[0]["posted_at"]

    swapped = [world.published[1], world.published[0], *world.published[2:]]
    versions = [world.mapping_versions[1], world.mapping_versions[0], *world.mapping_versions[2:]]
    reversed_order = project(swapped, versions)
    assert reversed_order.entries[1]["posted_at"] > reversed_order.entries[0]["posted_at"], (
        "publish order is the only thing controlling the anomaly"
    )


def test_s09_stale_mapper_turns_an_approval_into_a_failure():
    world, _ = build("S09", 3_000_500)
    p = project(world.published, world.mapping_versions)

    assert world.mapping_versions == [2]
    assert p.events[0]["raw_payload"]["status"] == "APPROVED_WITH_CONDITIONS"
    assert p.events[0]["normalized_state"] == "failed"
    assert "_mapper_note" in p.events[0]["raw_payload"]
    assert not p.entries, "a verification event moves no money"


def test_s10_gap_is_an_event_that_was_never_published():
    world, manifest = build("S10", 3_000_500)
    p = project(world.published, world.mapping_versions)

    assert len(world.settlements) == 2
    assert len(p.entries) == 1, "exactly one of the two settlements reached the ledger"
    gap = manifest["required_evidence"][0]
    posted_refs = {e["reference_id"] for e in p.entries}
    assert gap not in posted_refs, "the settlement named as evidence must be the unposted one"


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
