"""M0 — the `diagnostic` run kind's legality matrix (NEXT_STEP_M0.md § 5, § 9).

The one authorized extension of the fail-closed machine, proven here to be exactly as
narrow as the M0 document specifies:

  * TRAIN-split-only — DEV and TEST are refused;
  * permitted at TEST_EVALUATED and at the states TRAIN runs allow today, and at
    NOTHING in between (no non-terminal DEV/TEST-adjacent bypass);
  * mandatory non-empty purpose tag;
  * recorded as ledger lines only — the candidate's state log and HEAD.json are
    byte-identical before and after, so state and promotability cannot move;
  * the default ("eval") kind is byte-for-byte unchanged behaviour.

Same fixture discipline as test_r6_state_machine: a temporary registry, never the
canonical tree.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_r6_state_machine import (
    _candidate,
    _finished_run,
    _run_id,
    _step,
    _walk,
)

from fis_platform.provenance import (
    CONTRACT_FROZEN,
    DEV_EVALUATED,
    DEV_QUALIFIED,
    DEV_REJECTED,
    DIAGNOSTIC_STATES,
    REGISTERED,
    TEST_EVALUATED,
    TEST_UNLOCKED,
    TRAIN_COMPATIBLE,
    WITHDRAWN,
    R6Registry,
    TransitionRefused,
    begin_run,
    end_run,
    require_state,
)

PURPOSE = "M0-truncation-diag"


@pytest.fixture
def reg(tmp_path: Path) -> R6Registry:
    return R6Registry(tmp_path / "registry", git_checks=False)


def _diag_run_id(cid: str) -> str:
    return f"M0-{cid.split('@')[0]}-train-diag"


def _registry_bytes(reg: R6Registry, cid: str) -> tuple[bytes, bytes]:
    return reg.state_file(cid).read_bytes(), reg.head_file.read_bytes()


# ------------------------------------------------------------------ split rules

def test_diagnostic_refuses_dev_and_test_splits(reg, tmp_path):
    cid = _walk(reg, _candidate(reg, tmp_path), TEST_EVALUATED)
    for split in ("dev", "test"):
        with pytest.raises(TransitionRefused, match="TRAIN-only"):
            require_state(reg, cid, split, f"M0-x-{split}-diag", kind="diagnostic",
                          purpose=PURPOSE)


def test_diagnostic_requires_nonempty_purpose(reg, tmp_path):
    cid = _walk(reg, _candidate(reg, tmp_path), TEST_EVALUATED)
    for bad in (None, "", "   "):
        with pytest.raises(TransitionRefused, match="purpose"):
            require_state(reg, cid, "train", _diag_run_id(cid), kind="diagnostic",
                          purpose=bad)


def test_diagnostic_run_id_must_name_train_and_diag(reg, tmp_path):
    cid = _walk(reg, _candidate(reg, tmp_path), TEST_EVALUATED)
    with pytest.raises(TransitionRefused, match="diag"):
        require_state(reg, cid, "train", "M0-x-train-probe", kind="diagnostic",
                      purpose=PURPOSE)
    with pytest.raises(TransitionRefused, match="split"):
        require_state(reg, cid, "train", "M0-x-diag", kind="diagnostic", purpose=PURPOSE)


def test_unknown_run_kind_is_refused(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="run kind"):
        require_state(reg, cid, "train", _diag_run_id(cid), kind="calibration",
                      purpose=PURPOSE)


# ------------------------------------------------------------------ state matrix

def test_diagnostic_allowed_at_test_evaluated(reg, tmp_path):
    cid = _walk(reg, _candidate(reg, tmp_path), TEST_EVALUATED)
    ident = require_state(reg, cid, "train", _diag_run_id(cid), kind="diagnostic",
                          purpose=PURPOSE)
    assert ident["state"] == TEST_EVALUATED
    assert ident["kind"] == "diagnostic"
    assert ident["purpose"] == PURPOSE
    # The frozen execution system is returned for the caller to verify against.
    assert ident["execution_system"] is not None


def test_diagnostic_allowed_at_every_train_state(reg, tmp_path):
    assert set(DIAGNOSTIC_STATES) == {REGISTERED, TRAIN_COMPATIBLE, CONTRACT_FROZEN,
                                      TEST_EVALUATED}
    cid = _candidate(reg, tmp_path)
    assert require_state(reg, cid, "train", _diag_run_id(cid), kind="diagnostic",
                         purpose=PURPOSE)["state"] == REGISTERED
    _step(reg, cid, TRAIN_COMPATIBLE)
    assert require_state(reg, cid, "train", _diag_run_id(cid), kind="diagnostic",
                         purpose=PURPOSE)["state"] == TRAIN_COMPATIBLE
    _step(reg, cid, CONTRACT_FROZEN)
    assert require_state(reg, cid, "train", _diag_run_id(cid), kind="diagnostic",
                         purpose=PURPOSE)["state"] == CONTRACT_FROZEN


@pytest.mark.parametrize("target", [DEV_EVALUATED, DEV_QUALIFIED, TEST_UNLOCKED])
def test_diagnostic_refused_at_intermediate_states(reg, tmp_path, target):
    cid = _walk(reg, _candidate(reg, tmp_path), target)
    with pytest.raises(TransitionRefused, match="diagnostic TRAIN inference"):
        require_state(reg, cid, "train", _diag_run_id(cid), kind="diagnostic",
                      purpose=PURPOSE)


def test_diagnostic_refused_at_dev_rejected_and_withdrawn(reg, tmp_path):
    cid = _walk(reg, _candidate(reg, tmp_path), DEV_EVALUATED)
    _step(reg, cid, DEV_REJECTED)
    with pytest.raises(TransitionRefused, match="diagnostic TRAIN inference"):
        require_state(reg, cid, "train", _diag_run_id(cid), kind="diagnostic",
                      purpose=PURPOSE)
    other = _candidate(reg, tmp_path, "qwen38-27b-x", family="qwen38.27b",
                       role="modern_strong")
    _step(reg, other, WITHDRAWN)
    with pytest.raises(TransitionRefused, match="diagnostic TRAIN inference"):
        require_state(reg, other, "train", _diag_run_id(other), kind="diagnostic",
                      purpose=PURPOSE)


def test_eval_kind_behaviour_is_unchanged(reg, tmp_path):
    """The default kind still refuses TRAIN at the terminal state — the M0 extension
    opens a new door, it does not widen the old one."""
    cid = _walk(reg, _candidate(reg, tmp_path), TEST_EVALUATED)
    with pytest.raises(TransitionRefused, match="TRAIN inference is allowed only at"):
        require_state(reg, cid, "train", _run_id(cid, "train") + "-2")


# ------------------------------------------------------------------ no state effect

def test_begin_end_diagnostic_leaves_chain_and_head_byte_identical(reg, tmp_path):
    cid = _walk(reg, _candidate(reg, tmp_path), TEST_EVALUATED)
    state_before, head_before = _registry_bytes(reg, cid)
    run_id = _diag_run_id(cid)

    require_state(reg, cid, "train", run_id, kind="diagnostic", purpose=PURPOSE)
    begin_run(reg, cid, "train", run_id, planned_cases=15,
              extra={"local_server_session": "pid=1 start_ticks=2 boot=abc"},
              kind="diagnostic", purpose=PURPOSE)
    end_run(reg, cid, run_id, cases_done=15, wall_s=1.0)

    state_after, head_after = _registry_bytes(reg, cid)
    assert state_after == state_before        # not one byte of candidate history moved
    assert head_after == head_before
    assert reg.current_state(cid) == TEST_EVALUATED

    lines = [ln for ln in reg.read_ledger(cid) if ln.get("run_id") == run_id]
    assert [ln["event"] for ln in lines] == ["start", "end"]
    assert all(ln.get("run_kind") == "diagnostic" for ln in lines)
    assert all(ln.get("purpose") == PURPOSE for ln in lines)
    assert lines[0]["local_server_session"] == "pid=1 start_ticks=2 boot=abc"
    assert lines[0]["state_at_run"] == TEST_EVALUATED


def test_begin_run_diagnostic_requires_purpose(reg, tmp_path):
    cid = _walk(reg, _candidate(reg, tmp_path), TEST_EVALUATED)
    with pytest.raises(TransitionRefused, match="purpose"):
        begin_run(reg, cid, "train", _diag_run_id(cid), planned_cases=15,
                  kind="diagnostic")


def test_diagnostic_run_does_not_disturb_later_promotion(reg, tmp_path):
    """A diagnostic TRAIN run at CONTRACT_FROZEN must not count against any DEV/TEST
    guard — promotability is untouched."""
    cid = _walk(reg, _candidate(reg, tmp_path), CONTRACT_FROZEN)
    run_id = _diag_run_id(cid)
    require_state(reg, cid, "train", run_id, kind="diagnostic", purpose=PURPOSE)
    begin_run(reg, cid, "train", run_id, planned_cases=3, kind="diagnostic",
              purpose=PURPOSE)
    end_run(reg, cid, run_id, cases_done=3, wall_s=1.0)

    # The normal DEV path proceeds exactly as if the diagnostic never happened.
    assert require_state(reg, cid, "dev", _run_id(cid, "dev"))["state"] == CONTRACT_FROZEN
    _finished_run(reg, cid, "dev", _run_id(cid, "dev"), 48)
    _step(reg, cid, DEV_EVALUATED)
    assert reg.current_state(cid) == DEV_EVALUATED


def test_diagnostic_run_id_collision_across_candidates_refused(reg, tmp_path):
    cid_a = _walk(reg, _candidate(reg, tmp_path), TEST_EVALUATED)
    run_id = _diag_run_id(cid_a)
    begin_run(reg, cid_a, "train", run_id, planned_cases=1, kind="diagnostic",
              purpose=PURPOSE)
    cid_b = _candidate(reg, tmp_path, "qwen38-27b-y", family="qwen38.27b",
                       role="modern_strong")
    with pytest.raises(TransitionRefused, match="one run id, one candidate"):
        require_state(reg, cid_b, "train", run_id, kind="diagnostic", purpose=PURPOSE)
