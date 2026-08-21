"""SMOKE — the formal lifecycle state that precedes REGISTERED (playbook §3; owner
decision 2026-08-21; M_STAT_IMPLEMENTATION_MAP.md §0.1 / #2).

Every new candidate now opens at SMOKE, not REGISTERED, and must pass a fixed,
36-case (12 classes x 3), deterministic-round-robin TRAIN population before
REGISTERED work opens. This module proves the state is exactly as narrow as the
playbook specifies:

  * SMOKE has no edge INTO it (only `register_candidate` opens one there) and no
    edge OUT of it beyond REGISTERED — CONTRACT_FROZEN/DEV_*/TEST_* are all
    unreachable directly from SMOKE;
  * the `smoke` run kind is TRAIN-split-only, legal only when the candidate is
    AT SMOKE, and its run ids must say "smoke";
  * `begin_run(kind="smoke")` refuses any `planned_cases` other than the fixed 36,
    and — like `diagnostic` — writes ledger lines only, no chain entry;
  * SMOKE -> REGISTERED requires a clean (zero-violation), complete, round-robin
    36-case pass, cross-checked against the ledger;
  * SMOKE evidence never justifies adoption (`TRAIN_COMPATIBLE`'s `train_run_ids`
    guard) or elimination (`WITHDRAWN`'s `evidence_run_ids` guard, covered in
    `test_r6_state_machine.py`);
  * `smoke_case_selection` is the fixed, deterministic population-selection rule.

Same fixture discipline as `test_r6_state_machine.py`: a temporary registry, never
the canonical tree.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_r6_state_machine import (
    _candidate,
    _pass_smoke,
    _register_only,
    _smoke_run_id,
    _step,
    _walk,
)

from fis_platform.provenance import (
    CONTRACT_FROZEN,
    DEV_EVALUATED,
    DEV_QUALIFIED,
    DEV_REJECTED,
    REGISTERED,
    SMOKE,
    SMOKE_CASES_PER_CLASS,
    SMOKE_TOTAL_CASES,
    TEST_EVALUATED,
    TEST_UNLOCKED,
    TRAIN_COMPATIBLE,
    WITHDRAWN,
    IllegalTransition,
    R6Registry,
    TransitionRefused,
    begin_run,
    end_run,
    require_state,
    smoke_case_selection,
)


@pytest.fixture
def reg(tmp_path: Path) -> R6Registry:
    return R6Registry(tmp_path / "registry", git_checks=False)


def _registry_bytes(reg: R6Registry, cid: str) -> tuple[bytes, bytes]:
    return reg.state_file(cid).read_bytes(), reg.head_file.read_bytes()


def _train_ids(n_per_class: int = 5, n_classes: int = 12) -> list[str]:
    """Synthetic TRAIN scenario ids: `n_classes` classes, `n_per_class` ids each,
    in the `Sxx-<7 digits>` shape `fis_platform.ordering` requires."""
    out = []
    for c in range(1, n_classes + 1):
        for s in range(n_per_class):
            out.append(f"S{c:02d}-{1000000 + s:07d}")
    return out


# ------------------------------------------------------------------ 1. the edges

def test_new_candidates_open_at_smoke(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    assert reg.current_state(cid) == SMOKE
    entries = reg.read_state(cid)
    assert len(entries) == 1
    assert entries[0]["from"] is None and entries[0]["to"] == SMOKE


@pytest.mark.parametrize("target", [CONTRACT_FROZEN, DEV_EVALUATED, DEV_QUALIFIED,
                                    DEV_REJECTED, TEST_UNLOCKED, TEST_EVALUATED])
def test_smoke_cannot_jump_directly_to_a_promotable_state(reg, tmp_path, target):
    cid = _register_only(reg, tmp_path)
    before = reg.state_file(cid).read_bytes()
    with pytest.raises(IllegalTransition, match="is not a legal transition"):
        reg.transition(cid, target, {}, require_clean_tree=False)
    assert reg.current_state(cid) == SMOKE
    assert reg.state_file(cid).read_bytes() == before


def test_smoke_can_withdraw(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    _step(reg, cid, WITHDRAWN)
    assert reg.current_state(cid) == WITHDRAWN


def test_smoke_promotes_to_registered_and_then_follows_the_normal_lifecycle(reg, tmp_path):
    cid = _candidate(reg, tmp_path)          # register_only + a clean SMOKE pass
    assert reg.current_state(cid) == REGISTERED
    _walk(reg, cid, TRAIN_COMPATIBLE)
    assert reg.current_state(cid) == TRAIN_COMPATIBLE


# ------------------------------------------------------------------ 2. the smoke run kind

def test_smoke_kind_refuses_dev_and_test_splits(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    for split in ("dev", "test"):
        with pytest.raises(TransitionRefused, match="TRAIN-only"):
            require_state(reg, cid, split, f"R6-x-{split}-smoke", kind="smoke")


def test_smoke_kind_refuses_at_any_non_smoke_state(reg, tmp_path):
    cid = _candidate(reg, tmp_path)          # already promoted past SMOKE
    with pytest.raises(TransitionRefused, match="SMOKE inference is allowed only at SMOKE"):
        require_state(reg, cid, "train", _smoke_run_id(cid), kind="smoke")
    _walk(reg, cid, CONTRACT_FROZEN)
    with pytest.raises(TransitionRefused, match="SMOKE inference is allowed only at SMOKE"):
        require_state(reg, cid, "train", _smoke_run_id(cid), kind="smoke")


def test_smoke_run_id_must_say_smoke(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="must say 'smoke'"):
        require_state(reg, cid, "train", "R6-x-train-warmup", kind="smoke")


def test_smoke_kind_allowed_at_smoke_with_a_shaped_run_id(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    ctx = require_state(reg, cid, "train", _smoke_run_id(cid), kind="smoke")
    assert ctx["state"] == SMOKE and ctx["kind"] == "smoke"


def test_begin_run_smoke_refuses_any_planned_cases_but_36(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    run_id = _smoke_run_id(cid)
    for bad in (35, 37, 12, 0):
        with pytest.raises(TransitionRefused, match=f"fixed at {SMOKE_TOTAL_CASES}"):
            begin_run(reg, cid, "train", run_id, bad, kind="smoke")


def test_begin_end_smoke_leaves_chain_and_head_byte_identical(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    state_before, head_before = _registry_bytes(reg, cid)
    run_id = _smoke_run_id(cid)

    begin_run(reg, cid, "train", run_id, SMOKE_TOTAL_CASES,
             extra={"smoke_case_digest": "e" * 64}, kind="smoke")
    end_run(reg, cid, run_id, cases_done=SMOKE_TOTAL_CASES, wall_s=1.0)

    state_after, head_after = _registry_bytes(reg, cid)
    assert state_after == state_before          # not one byte of candidate history moved
    assert head_after == head_before
    assert reg.current_state(cid) == SMOKE

    lines = [ln for ln in reg.read_ledger(cid) if ln.get("run_id") == run_id]
    assert [ln["event"] for ln in lines] == ["start", "end"]
    assert all(ln.get("run_kind") == "smoke" for ln in lines)
    assert lines[0]["planned_cases"] == SMOKE_TOTAL_CASES
    assert lines[0]["state_at_run"] == SMOKE
    assert lines[0]["smoke_case_digest"] == "e" * 64


def test_smoke_run_id_collision_across_candidates_refused(reg, tmp_path):
    cid_a = _register_only(reg, tmp_path, "qwen35-9b-q4km")
    run_id = _smoke_run_id(cid_a)
    begin_run(reg, cid_a, "train", run_id, SMOKE_TOTAL_CASES, kind="smoke")
    cid_b = _register_only(reg, tmp_path, "qwen38-27b-y", family="qwen38.27b",
                           role="modern_strong")
    with pytest.raises(TransitionRefused, match="one run id, one candidate"):
        require_state(reg, cid_b, "train", run_id, kind="smoke")


# ------------------------------------------------------------------ 3. SMOKE -> REGISTERED

def test_smoke_to_registered_requires_every_key(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    run_id = _smoke_run_id(cid)
    begin_run(reg, cid, "train", run_id, SMOKE_TOTAL_CASES, kind="smoke")
    end_run(reg, cid, run_id, cases_done=SMOKE_TOTAL_CASES, wall_s=1.0)
    with pytest.raises(TransitionRefused, match="missing"):
        reg.transition(cid, REGISTERED, {"smoke_run_id": run_id}, require_clean_tree=False)


def test_smoke_to_registered_refuses_wrong_smoke_cases(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="smoke_cases must be 36"):
        _pass_smoke(reg, cid, smoke_cases=35)


def test_smoke_to_registered_refuses_nonzero_violations(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="cannot open REGISTERED work"):
        _pass_smoke(reg, cid, violations=1)
    assert reg.current_state(cid) == SMOKE


def test_smoke_to_registered_refuses_non_round_robin_ordering(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="ordering must be 'round_robin'"):
        _pass_smoke(reg, cid, ordering="class_blocked")


def test_smoke_to_registered_refuses_without_a_ledger_start_line(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    payload = {"smoke_run_id": _smoke_run_id(cid), "smoke_cases": SMOKE_TOTAL_CASES,
              "smoke_violations": 0, "smoke_case_digest": "d" * 64,
              "ordering": "round_robin"}
    with pytest.raises(TransitionRefused, match="no SMOKE ledger start line"):
        reg.transition(cid, REGISTERED, payload, require_clean_tree=False)


def test_smoke_to_registered_refuses_an_unfinished_run(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    run_id = _smoke_run_id(cid)
    begin_run(reg, cid, "train", run_id, SMOKE_TOTAL_CASES, kind="smoke")
    payload = {"smoke_run_id": run_id, "smoke_cases": SMOKE_TOTAL_CASES,
              "smoke_violations": 0, "smoke_case_digest": "d" * 64,
              "ordering": "round_robin"}
    with pytest.raises(TransitionRefused, match="has no ledger end line"):
        reg.transition(cid, REGISTERED, payload, require_clean_tree=False)


def test_smoke_to_registered_refuses_a_partial_run(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    run_id = _smoke_run_id(cid)
    begin_run(reg, cid, "train", run_id, SMOKE_TOTAL_CASES, kind="smoke")
    end_run(reg, cid, run_id, cases_done=30, wall_s=1.0)          # short
    payload = {"smoke_run_id": run_id, "smoke_cases": SMOKE_TOTAL_CASES,
              "smoke_violations": 0, "smoke_case_digest": "d" * 64,
              "ordering": "round_robin"}
    with pytest.raises(TransitionRefused, match="a full SMOKE pass is 36"):
        reg.transition(cid, REGISTERED, payload, require_clean_tree=False)


def test_smoke_to_registered_refuses_a_case_digest_that_does_not_match_the_start_line(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    run_id = _smoke_run_id(cid)
    begin_run(reg, cid, "train", run_id, SMOKE_TOTAL_CASES,
             extra={"smoke_case_digest": "e" * 64}, kind="smoke")
    end_run(reg, cid, run_id, cases_done=SMOKE_TOTAL_CASES, wall_s=1.0)
    payload = {"smoke_run_id": run_id, "smoke_cases": SMOKE_TOTAL_CASES,
              "smoke_violations": 0, "smoke_case_digest": "f" * 64,   # disagrees
              "ordering": "round_robin"}
    with pytest.raises(TransitionRefused, match="SMOKE start line recorded"):
        reg.transition(cid, REGISTERED, payload, require_clean_tree=False)


def test_smoke_to_registered_with_a_clean_full_pass_succeeds(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    entry = _pass_smoke(reg, cid)
    assert entry["to"] == REGISTERED and entry["from"] == SMOKE
    assert entry["payload"]["smoke_cases"] == SMOKE_TOTAL_CASES
    assert entry["payload"]["smoke_violations"] == 0
    assert reg.current_state(cid) == REGISTERED


def test_smoke_to_registered_a_second_time_is_illegal(reg, tmp_path):
    cid = _candidate(reg, tmp_path)          # already at REGISTERED
    with pytest.raises(IllegalTransition, match="is not a legal transition"):
        _pass_smoke(reg, cid, run_id=_smoke_run_id(cid) + "-2")


# ------------------------------------------------------------------ 4. non-promotability

def test_train_compatible_refuses_train_run_ids_that_cite_a_smoke_run(reg, tmp_path):
    cid = _candidate(reg, tmp_path)          # its own SMOKE run is already ledgered
    smoke_id = _smoke_run_id(cid)
    with pytest.raises(TransitionRefused, match="never justify adoption"):
        _step(reg, cid, TRAIN_COMPATIBLE, train_run_ids=[smoke_id])
    assert reg.current_state(cid) == REGISTERED


def test_train_compatible_refuses_train_run_ids_that_cite_a_diagnostic_run(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    diag_id = f"M0-{cid.split('@')[0]}-train-diag"
    begin_run(reg, cid, "train", diag_id, 12, kind="diagnostic", purpose="probe")
    end_run(reg, cid, diag_id, cases_done=12, wall_s=1.0)
    with pytest.raises(TransitionRefused, match="never justify adoption"):
        _step(reg, cid, TRAIN_COMPATIBLE, train_run_ids=[diag_id])


# ------------------------------------------------------------------ 5. smoke_case_selection

def test_smoke_case_selection_is_the_first_three_of_every_class_in_round_robin_order():
    ids = _train_ids(n_per_class=5)
    selected = smoke_case_selection(ids)
    assert len(selected) == SMOKE_TOTAL_CASES

    expected_by_class = {f"S{c:02d}": [f"S{c:02d}-{1000000 + s:07d}" for s in range(3)]
                         for c in range(1, 13)}
    from fis_platform.ordering import class_of, is_round_robin
    assert is_round_robin(selected)
    got_by_class: dict[str, list[str]] = {}
    for sid in selected:
        got_by_class.setdefault(class_of(sid), []).append(sid)
    for cls, ids_for_class in got_by_class.items():
        assert sorted(ids_for_class) == expected_by_class[cls]

    # deterministic: same input, same output, regardless of input order
    import random
    shuffled = list(ids)
    random.Random(7).shuffle(shuffled)
    assert smoke_case_selection(shuffled) == selected


def test_smoke_case_selection_refuses_fewer_than_twelve_classes():
    ids = [i for i in _train_ids(n_per_class=5) if not i.startswith("S12")]
    with pytest.raises(TransitionRefused, match="exactly 12 scenario classes"):
        smoke_case_selection(ids)


def test_smoke_case_selection_refuses_a_thin_class():
    # remove just two members of S03, leaving it at 3 — should still pass
    thin_ok = [i for i in _train_ids(n_per_class=5)
              if not (i.startswith("S03") and i.endswith(("3", "4")))]
    assert len(smoke_case_selection(thin_ok)) == SMOKE_TOTAL_CASES

    # remove three members of S03, leaving it at 2 — must refuse
    too_thin = [i for i in _train_ids(n_per_class=5)
               if not (i.startswith("S03") and i.endswith(("2", "3", "4")))]
    with pytest.raises(TransitionRefused, match="too few"):
        smoke_case_selection(too_thin)


def test_smoke_case_selection_needs_exactly_36_when_classes_are_exactly_full():
    ids = _train_ids(n_per_class=3)                 # exactly 3 per class, 12 classes
    selected = smoke_case_selection(ids)
    assert sorted(selected) == sorted(ids)
    assert len(selected) == SMOKE_TOTAL_CASES == SMOKE_CASES_PER_CLASS * 12
