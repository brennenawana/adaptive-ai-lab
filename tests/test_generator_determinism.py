"""If the generator is not deterministic, every before/after comparison built on it
is meaningless — a regenerated test set would move the goalposts silently.

These tests exist to make that failure loud.
"""

import json

import pytest

from scenarios.generator.catalog import BUILDERS
from scenarios.generator.run import SPLIT_RANGES, build, split_for_seed

CODES = sorted(BUILDERS)


def _fingerprint(world) -> str:
    """Everything the generator produced, order included."""
    payload = {
        attr: getattr(world, attr)
        for attr in (
            "customers", "verifications", "accounts", "entries", "cards",
            "authorizations", "settlements", "alerts", "deliveries", "events", "cases",
        )
    }
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


@pytest.mark.parametrize("code", CODES)
def test_required_evidence_actually_exists_in_the_world(code):
    """A manifest that demands evidence the generator never wrote would make
    100% recall unreachable and quietly cap the score for that class."""
    world, m = build(code, 3_000_500)
    produced = set()
    for attr, key in (
        ("customers", "customer_id"), ("verifications", "verification_id"),
        ("accounts", "account_id"), ("entries", "entry_id"), ("cards", "card_id"),
        ("authorizations", "auth_id"), ("settlements", "settlement_id"),
        ("alerts", "alert_id"), ("deliveries", "delivery_id"),
        ("events", "event_id"), ("cases", "case_id"),
    ):
        produced |= {row[key] for row in getattr(world, attr)}

    missing = [e for e in m["required_evidence"] if e not in produced]
    assert not missing, f"{code} requires evidence that was never generated: {missing}"


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
