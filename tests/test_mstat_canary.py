"""Leakage-canary mechanism (`scenarios/generator/canary.py`) — mechanism-only, for
FUTURE suites (playbook §8, implementation-map §9).

The one invariant every test here ultimately serves: for `SUITE_VERSION="3"` (the
frozen suite this repo currently ships), the mechanism is a total no-op — every path
that suite v3's own generator run can reach returns `None` or is never taken — so
regenerating the v3 corpus with this module present is byte-identical to regenerating
it without. Nothing here touches Postgres: `canary_token`/`canary_guid`/
`activate_canary` are pure, and the `run.py` wiring test proves the injection point is
inert (or active) purely by inspecting `World.published[i].raw_payload` after `build()`
— `build()` never opens a database connection.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scenarios.generator.canary import (
    CANARY_ACTIVE_FROM_SUITE,
    CanaryRefused,
    activate_canary,
    canary_guid,
    canary_token,
)

# ----------------------------------------------------------------- the frozen constant

def test_active_from_suite_is_4():
    """The owner decision this whole module exists to encode (playbook §8): activation
    begins only with a future versioned suite release, not with Suite v3."""
    assert CANARY_ACTIVE_FROM_SUITE == 4


# ---------------------------------------------------------------- canary_token: inert for v3

@pytest.mark.parametrize("suite_version", ["1", "2", "3", 1, 2, 3])
@pytest.mark.parametrize("split", ["train", "dev", "test"])
def test_canary_token_none_for_every_split_of_every_frozen_suite(suite_version, split):
    """Suite v3 (and every suite before it) is frozen. `canary_token` must return
    `None` for ALL THREE splits, not just train/dev — a TEST-split canary on suite 3
    would still mutate the v3 corpus digest and break the freeze."""
    assert canary_token(suite_version, split) is None


@pytest.mark.parametrize("split", ["train", "dev"])
def test_canary_token_none_for_suite_4_train_and_dev(split):
    """Even once a suite is canary-eligible, TRAIN/DEV stay uncanaried — they are read
    repeatedly by design (screening, calibration), so a canary there would just fire on
    the lab's own legitimate use. Only TEST is content whose reappearance is leakage."""
    assert canary_token(4, split) is None


# ------------------------------------------------------------- canary_token: active for v4 test

def test_canary_token_present_for_suite_4_test():
    token = canary_token(4, "test")
    assert token is not None
    assert token.startswith("FIS-CANARY-DO-NOT-TRAIN ")
    assert token.endswith("suite-v4")
    assert canary_guid(4) in token


def test_canary_token_is_deterministic():
    """Same (suite, split) -> the same string on every call — a fresh GUID per
    generation run would make a leak undatable and a v3-regeneration diff meaningless."""
    assert canary_token(4, "test") == canary_token(4, "test")
    assert canary_token("4", "test") == canary_token(4, "test")  # str/int suite agree


def test_canary_token_accepts_a_suite_beyond_the_activation_floor():
    """Activation is a floor (">="), not an exact match — v5, v6, ... stay active too."""
    assert canary_token(5, "test") is not None
    assert canary_token(4, "test") != canary_token(5, "test")


# --------------------------------------------------------------------------- canary_guid

def test_canary_guid_stable_across_calls():
    assert canary_guid(4) == canary_guid(4)
    assert canary_guid("4") == canary_guid(4)


def test_canary_guid_distinct_across_suites():
    """One GUID per suite release — a leak has to be datable to the release that
    produced it, which requires v4's GUID and v5's GUID to differ."""
    guids = {canary_guid(v) for v in (1, 2, 3, 4, 5, 6)}
    assert len(guids) == 6


def test_canary_guid_is_a_well_formed_uuid_string():
    import uuid

    parsed = uuid.UUID(canary_guid(4))
    assert str(parsed) == canary_guid(4)


# ------------------------------------------------------------------------ activate_canary

@pytest.mark.parametrize("suite_version", ["1", "2", "3", 1, 2, 3])
@pytest.mark.parametrize("force", [False, True])
def test_activate_canary_refuses_every_frozen_suite_with_and_without_force(suite_version, force):
    """The core guard this unit exists to ship: mutating an already-released suite's
    corpus is never legal, `force=True` included. `force` must not be an escape hatch
    here the way it legitimately is elsewhere in this codebase."""
    with pytest.raises(CanaryRefused):
        activate_canary(suite_version, force=force)


def test_activate_canary_refusal_is_a_systemexit_subclass():
    """Matches the house idiom (`TransitionRefused`, `RegistryIntegrityError` in
    `fis_platform/provenance.py`): a guard refusal is a `SystemExit` subclass, so an
    uncaught refusal exits the process cleanly instead of dumping a traceback."""
    assert issubclass(CanaryRefused, SystemExit)
    with pytest.raises(SystemExit):
        activate_canary(3)


def test_activate_canary_returns_the_test_token_for_suite_4():
    assert activate_canary(4) == canary_token(4, "test")


def test_activate_canary_force_is_irrelevant_once_a_suite_qualifies():
    """`force` changes nothing in either direction: refused suites stay refused, and a
    qualifying suite needs no `force` to activate."""
    assert activate_canary(4, force=True) == activate_canary(4, force=False)


# --------------------------------------------------------------- run.py wiring: the real point

from scenarios.generator import run as generator_run


def test_v3_wiring_is_a_no_op_on_every_split(monkeypatch):
    """Prove the frozen-suite path is a no-op — no database needed. `build()` is pure:
    it never opens a connection, so this exercises the exact code path the real
    corpus-generation run takes for SUITE_VERSION="3" without touching Postgres.
    """
    monkeypatch.setattr(generator_run, "SUITE_VERSION", "3")
    for split, seed in (("train", 1_000_100), ("dev", 2_000_100), ("test", 3_000_100)):
        code = min(generator_run.BUILDERS)
        world, manifest = generator_run.build(code, seed)
        assert manifest["split"] == split
        assert world.published, f"{code} at {seed} published nothing to check"
        assert all("canary" not in e.raw_payload for e in world.published)


def test_v4_wiring_injects_only_on_test_split(monkeypatch):
    """With the module attribute the wiring actually reads (`generator_run.
    SUITE_VERSION`) monkeypatched to a canary-eligible suite, the token must appear on
    every published event of a TEST-split build and on none of a TRAIN/DEV one — the
    exact behaviour the injection point in `run.py` is supposed to have once the owner
    activates a future suite."""
    monkeypatch.setattr(generator_run, "SUITE_VERSION", "4")
    code = min(generator_run.BUILDERS)

    world_test, manifest_test = generator_run.build(code, 3_000_200)
    assert manifest_test["split"] == "test"
    assert world_test.published
    expected = canary_token("4", "test")
    assert all(e.raw_payload.get("canary") == expected for e in world_test.published)

    for split, seed in (("train", 1_000_200), ("dev", 2_000_200)):
        world, manifest = generator_run.build(code, seed)
        assert manifest["split"] == split
        assert all("canary" not in e.raw_payload for e in world.published)


def test_v4_wiring_does_not_disturb_non_event_fields(monkeypatch):
    """The injection point is additive: it must not touch anything about the world
    besides `ProviderEvent.raw_payload` — state rows, ids, and manifest content are
    unrelated to the canary and must be identical with the mechanism on or off."""
    monkeypatch.setattr(generator_run, "SUITE_VERSION", "3")
    code = min(generator_run.BUILDERS)
    world_v3, manifest_v3 = generator_run.build(code, 3_000_300)

    monkeypatch.setattr(generator_run, "SUITE_VERSION", "4")
    world_v4, manifest_v4 = generator_run.build(code, 3_000_300)

    assert manifest_v3 == manifest_v4
    assert len(world_v3.published) == len(world_v4.published)
    for e3, e4 in zip(world_v3.published, world_v4.published, strict=True):
        p3, p4 = dict(e3.raw_payload), dict(e4.raw_payload)
        p4.pop("canary", None)
        assert p3 == p4
        assert "canary" not in e3.raw_payload
        assert e4.raw_payload.get("canary") == canary_token("4", "test")
