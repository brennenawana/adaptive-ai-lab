"""Canonical round-robin scenario ordering (playbook §4, M-STAT map §4) — pin the
interleave, its determinism, its class balance, and its refusal of malformed ids.

Pure module, no database, no registry: everything here is synthetic ids/rows.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.ordering import (  # noqa: E402
    MalformedScenarioId,
    class_of,
    is_round_robin,
    round_robin,
    round_robin_rows,
)

CLASSES = [f"S{i:02d}" for i in range(1, 13)]


def _ids(n_per_class: int, classes: list[str] = CLASSES) -> list[str]:
    """`n_per_class` ids per class, seeded 1..n_per_class, built in class-blocked
    (sorted) order — the exact order this module's canonical order must NOT equal."""
    return [f"{cls}-{seed:07d}" for cls in classes for seed in range(1, n_per_class + 1)]


# --------------------------------------------------------------------- class_of

def test_class_of_extracts_the_three_char_prefix():
    assert class_of("S01-1000000") == "S01"
    assert class_of("S12-0000042") == "S12"


@pytest.mark.parametrize(
    "bad",
    [
        "S1-1000000",       # class needs 2 digits
        "S01-100000",       # seed needs 7 digits
        "s01-1000000",      # lowercase
        "S01_1000000",      # wrong separator
        "S01-10000000",     # 8-digit seed
        "",
        "S01-1000000 ",     # trailing space
    ],
)
def test_class_of_refuses_malformed_ids(bad):
    with pytest.raises(MalformedScenarioId):
        class_of(bad)


def test_malformed_scenario_id_is_a_systemexit_subclass():
    # House rule: guards fail closed via SystemExit subclasses, not plain exceptions
    # a caller might blanket-catch with `except Exception`.
    assert issubclass(MalformedScenarioId, SystemExit)


# ------------------------------------------------------------------- round_robin

def test_round_robin_correctness_on_a_12_class_synthetic_set():
    ids = _ids(3)  # 36 ids, class-blocked input order (S01x3, S02x3, ..., S12x3)
    out = round_robin(ids)
    assert len(out) == 36
    assert set(out) == set(ids)
    expected = [f"{cls}-{seed:07d}" for seed in (1, 2, 3) for cls in CLASSES]
    assert out == expected


def test_round_robin_is_deterministic_across_repeat_calls_and_input_order():
    ids = _ids(3)
    first = round_robin(ids)
    assert round_robin(ids) == first             # repeat call, same input order
    assert round_robin(list(reversed(ids))) == first   # shuffled input order
    import random
    shuffled = ids[:]
    random.Random(7).shuffle(shuffled)
    assert round_robin(shuffled) == first


def test_round_robin_prefixes_are_class_balanced():
    ids = _ids(5)  # 60 ids, 5 per class
    out = round_robin(ids)
    first_12 = out[:12]
    assert len(first_12) == len(set(class_of(i) for i in first_12)) == 12
    first_24 = out[:24]
    counts: dict[str, int] = {}
    for sid in first_24:
        counts[class_of(sid)] = counts.get(class_of(sid), 0) + 1
    assert counts == {cls: 2 for cls in CLASSES}


def test_round_robin_interleaves_unequal_class_sizes_and_skips_exhausted_classes():
    ids = ["S01-0000001", "S01-0000002", "S01-0000003",
           "S02-0000001",
           "S03-0000001", "S03-0000002"]
    out = round_robin(ids)
    # round 0: one of each class in class order; round 1: S01 + S03 (S02 exhausted);
    # round 2: S01 only (S03 exhausted too).
    assert out == [
        "S01-0000001", "S02-0000001", "S03-0000001",
        "S01-0000002", "S03-0000002",
        "S01-0000003",
    ]


def test_round_robin_within_class_order_is_lexicographic_seed_order():
    ids = ["S01-0000010", "S01-0000002", "S01-0000001"]
    assert round_robin(ids) == ["S01-0000001", "S01-0000002", "S01-0000010"]


def test_round_robin_empty_input():
    assert round_robin([]) == []


def test_round_robin_refuses_a_malformed_id_in_the_set():
    with pytest.raises(MalformedScenarioId):
        round_robin(["S01-0000001", "bogus"])


# ----------------------------------------------------------------- is_round_robin

def test_is_round_robin_true_for_canonical_order():
    ids = _ids(3)
    assert is_round_robin(round_robin(ids)) is True


def test_is_round_robin_false_for_class_blocked_sorted_order_of_the_same_ids():
    ids = _ids(3)
    class_blocked = sorted(ids)  # sorted() on these strings is exactly class-blocked order
    assert class_blocked != round_robin(ids)
    assert is_round_robin(class_blocked) is False


def test_is_round_robin_false_for_any_other_permutation():
    ids = _ids(2)
    canonical = round_robin(ids)
    swapped = canonical[:]
    swapped[0], swapped[1] = swapped[1], swapped[0]
    assert is_round_robin(swapped) is False


def test_is_round_robin_empty_is_trivially_true():
    assert is_round_robin([]) is True


# --------------------------------------------------------------- round_robin_rows

def test_round_robin_rows_preserves_row_objects_and_applies_canonical_order():
    ids = _ids(2)
    rows = [{"scenario_id": sid, "payload": object()} for sid in ids]
    by_id = {row["scenario_id"]: row for row in rows}
    out = round_robin_rows(rows)
    assert [r["scenario_id"] for r in out] == round_robin(ids)
    # every returned row is the SAME object as the input row for that id — not a copy.
    for row in out:
        assert row is by_id[row["scenario_id"]]


def test_round_robin_rows_honors_a_custom_key():
    rows = [{"sid": "S02-0000001", "x": 1}, {"sid": "S01-0000001", "x": 2}]
    out = round_robin_rows(rows, key="sid")
    assert [r["sid"] for r in out] == ["S01-0000001", "S02-0000001"]


def test_round_robin_rows_refuses_a_malformed_scenario_id():
    rows = [{"scenario_id": "S01-0000001"}, {"scenario_id": "not-an-id"}]
    with pytest.raises(MalformedScenarioId):
        round_robin_rows(rows)
