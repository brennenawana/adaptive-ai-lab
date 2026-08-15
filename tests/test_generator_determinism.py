"""If the generator is not deterministic, every before/after comparison built on it
is meaningless — a regenerated test set would move the goalposts silently.

These tests exist to make that failure loud.
"""

import json

import pytest

from fis_platform.events.projection import project
from scenarios.generator.catalog import BUILDERS
from scenarios.generator.run import SPLIT_RANGES, build, split_for_seed

CODES = sorted(BUILDERS)

# Classes the migration made genuinely event-driven. The rest are state-based on
# purpose — not every operational problem is an event-ordering problem.
EVENT_DRIVEN = ["S01", "S02", "S06", "S07", "S09", "S10"]

STATE_ATTRS = (
    "customers", "verifications", "accounts", "entries", "cards",
    "authorizations", "settlements", "alerts", "deliveries", "cases",
)


def _fingerprint(world) -> str:
    """Everything the generator produced, order included.

    Published events are part of the fingerprint, and their envelope ids with them.
    Those ids name every row the pipeline will write, so a uuid4 leaking back into
    the generator would show up here as a determinism failure rather than as a
    corpus whose manifests point at the previous run's rows.
    """
    payload = {attr: getattr(world, attr) for attr in STATE_ATTRS}
    payload["published"] = [e.model_dump(mode="json") for e in world.published]
    payload["mapping_version"] = world.mapping_version
    return json.dumps(payload, sort_keys=True, default=str)


@pytest.mark.parametrize("code", CODES)
def test_same_seed_produces_identical_world(code):
    w1, m1 = build(code, 3_000_500)
    w2, m2 = build(code, 3_000_500)
    assert _fingerprint(w1) == _fingerprint(w2), f"{code} is not deterministic"
    assert m1 == m2


@pytest.mark.parametrize("code", CODES)
def test_different_seeds_produce_different_worlds(code):
    """Variation must be real — a generator that ignores its seed would pass the
    determinism test above while producing 200 identical cases."""
    w1, _ = build(code, 3_000_500)
    w2, _ = build(code, 3_000_777)
    assert _fingerprint(w1) != _fingerprint(w2), f"{code} ignores its seed"


@pytest.mark.parametrize("code", CODES)
def test_manifest_is_well_formed(code):
    _, m = build(code, 3_000_500)
    assert m["required_evidence"], f"{code} has no required evidence to recall"
    assert m["acceptable_next_actions"], f"{code} has no acceptable action"
    assert m["scenario_id"].startswith(code)
    # Every scenario needs at least one forbidden claim, otherwise the
    # unsupported-claim dimension is unscoreable for that class.
    assert m["forbidden_claims"], f"{code} defines no forbidden claims"


def _produced_ids(world) -> set[str]:
    """Every id this scenario results in — inserted state plus what the pipeline
    will materialise from the events it publishes.

    The second half runs the real consumer decision functions (see
    `fis_platform.events.projection`) rather than re-deriving them, so this cannot
    quietly agree with a generator that is wrong.
    """
    produced = set()
    for attr, key in (
        ("customers", "customer_id"), ("verifications", "verification_id"),
        ("accounts", "account_id"), ("entries", "entry_id"), ("cards", "card_id"),
        ("authorizations", "auth_id"), ("settlements", "settlement_id"),
        ("alerts", "alert_id"), ("deliveries", "delivery_id"),
        ("cases", "case_id"),
    ):
        produced |= {row[key] for row in getattr(world, attr)}
    return produced | project(world.published, world.mapping_version).ids()


@pytest.mark.parametrize("code", CODES)
def test_required_evidence_actually_exists_in_the_world(code):
    """A manifest that demands evidence the generator never wrote would make
    100% recall unreachable and quietly cap the score for that class."""
    world, m = build(code, 3_000_500)
    missing = [e for e in m["required_evidence"] if e not in _produced_ids(world)]
    assert not missing, f"{code} requires evidence that was never generated: {missing}"


@pytest.mark.parametrize("code", CODES)
def test_required_evidence_is_reachable_by_the_tool_set(code):
    """Ontology §5 invariant 2, enforced instead of merely written down.

    Webhook and integration evidence is addressed by `provider_event_id`. The
    fixed-evidence plan discovers those ids by walking `provider_ref` out of
    phase-one results, so a delivery keyed to a reference no state row carries is
    unreachable by any model and its scenario is permanently unwinnable — not hard,
    impossible. That was true of every delivery in the pre-migration corpus, and it
    capped four classes below the recall threshold before a model saw them.
    """
    world, _ = build(code, 3_000_500)
    refs = {
        row["provider_ref"]
        for attr in ("verifications", "cards", "authorizations", "settlements")
        for row in getattr(world, attr)
        if row.get("provider_ref")
    }
    addressed = {e.provider_event_id for e in world.published}
    addressed |= {d["provider_event_id"] for d in world.deliveries}

    unreachable = sorted(addressed - refs)
    assert not unreachable, (
        f"{code} has webhook evidence addressed by {unreachable}, which no state row "
        "carries as provider_ref — get_webhook_history can never be called with it"
    )


@pytest.mark.parametrize("code", EVENT_DRIVEN)
def test_event_driven_scenarios_do_not_hand_author_their_consequences(code):
    """Step 7 of the migration, made structural.

    A ported class must publish, and must not write the rows publishing produces.
    Without this the direct-insert path can come back one builder at a time and
    nothing fails — the corpus would simply go back to depicting its failures.
    """
    world, _ = build(code, 3_000_500)
    assert world.published, f"{code} is listed as event-driven but publishes nothing"
    assert not world.entries, (
        f"{code} hand-authored ledger entries; a pipeline-caused posting must come "
        "from the ledger consumer"
    )
    assert not world.deliveries, (
        f"{code} hand-authored webhook deliveries; publish() and let the consumer "
        "record what it did with them"
    )


def test_the_fabrication_builders_are_gone():
    """`add_event` and the general-purpose `add_delivery` no longer exist. Named
    explicitly so that reintroducing one is a deliberate act with a failing test
    attached, rather than an autocomplete accident."""
    world, _ = build("S01", 3_000_500)
    assert not hasattr(world, "add_event")
    assert not hasattr(world, "add_delivery")
    assert not hasattr(world, "events")


def test_split_ranges_are_disjoint():
    spans = sorted(SPLIT_RANGES.values())
    for (_, hi), (lo, _) in zip(spans, spans[1:]):
        assert hi < lo, "split seed ranges overlap — train/test leakage is possible"


def test_seed_outside_all_ranges_is_rejected():
    with pytest.raises(ValueError, match="outside every split"):
        split_for_seed(42)


def test_split_assignment_is_stable():
    assert split_for_seed(1_000_000) == "train"
    assert split_for_seed(2_500_000) == "dev"
    assert split_for_seed(3_999_999) == "test"
