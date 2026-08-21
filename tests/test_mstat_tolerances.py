"""Consequence-bearing tolerances + certainty curtailment (fis_platform/tolerances.py).

Curtailed exact counting is pinned at the k+1 boundary; every consequence-commitment
guard (RECALIBRATE needs a procedure, PROCEED needs a priced ceiling) is proven to
refuse at spec construction, not at breach time; ABORT is proven to structurally
block further observation; curtailment arithmetic is pinned at its exact boundary.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.tolerances import (  # noqa: E402
    Consequence,
    ConsequenceAction,
    CurtailmentPolicy,
    ToleranceBreach,
    ToleranceSpec,
    ToleranceTracker,
    append_curtailed_run,
    make_curtailment_report,
    read_curtailed_runs,
)


def _spec(consequence: Consequence = Consequence.ABORT, max_violations: int = 2, **kw) -> ToleranceSpec:
    fields = {
        "spec_id": "cap-tolerance",
        "metric": "cap_hit_rate",
        "description": "output-cap tolerance, TRAIN pilot",
        "denominator_n": 36,
        "max_violations": max_violations,
        "consequence": consequence,
    }
    fields.update(kw)
    return ToleranceSpec(**fields)


# ---------------------------------------------------------------- Part A: spec construction

def test_consequence_is_required_by_type_not_by_convention():
    with pytest.raises(ValidationError):
        ToleranceSpec(spec_id="x", metric="m", description="d", denominator_n=10, max_violations=1)


def test_recalibrate_without_procedure_refused_at_construction():
    with pytest.raises(ValidationError, match="recalibration_procedure"):
        _spec(consequence=Consequence.RECALIBRATE)
    with pytest.raises(ValidationError, match="recalibration_procedure"):
        _spec(consequence=Consequence.RECALIBRATE, recalibration_procedure="   ")


def test_recalibrate_with_procedure_constructs():
    s = _spec(consequence=Consequence.RECALIBRATE, recalibration_procedure="re-run the 36-case pilot at cap 8192")
    assert s.consequence is Consequence.RECALIBRATE


def test_proceed_without_ceiling_or_without_cost_refused_at_construction():
    with pytest.raises(ValidationError, match="declared_ceiling"):
        _spec(consequence=Consequence.PROCEED_WITH_DECLARED_CEILING)
    with pytest.raises(ValidationError, match="projected_cost"):
        _spec(consequence=Consequence.PROCEED_WITH_DECLARED_CEILING, declared_ceiling="cap 8192")
    with pytest.raises(ValidationError, match="declared_ceiling"):
        _spec(consequence=Consequence.PROCEED_WITH_DECLARED_CEILING, projected_cost="~10h wall")


def test_proceed_with_both_ceiling_and_cost_constructs():
    s = _spec(consequence=Consequence.PROCEED_WITH_DECLARED_CEILING,
              declared_ceiling="cap 8192", projected_cost="~10h wall, 145 zero-scoring cases")
    assert s.declared_ceiling and s.projected_cost


def test_spec_digest_is_deterministic_and_content_sensitive():
    a = _spec()
    b = _spec()
    assert a.spec_digest == b.spec_digest
    c = _spec(max_violations=3)
    assert c.spec_digest != a.spec_digest


# ---------------------------------------------------------------- Part A: curtailed counting

def test_k_plus_1_boundary_exact_no_consequence_at_k_then_fires_once_at_k_plus_1():
    spec = _spec(consequence=Consequence.ABORT, max_violations=2)
    tracker = ToleranceTracker(spec)
    # k=2 violations observed: no consequence yet.
    assert tracker.observe(True) is None
    assert tracker.observe(True) is None
    assert tracker.breached is False
    # the (k+1)-th violation: consequence fires, exactly once.
    result = tracker.observe(True)
    assert result is Consequence.ABORT
    assert tracker.breached is True
    assert tracker.violations == 3
    assert tracker.cases_observed == 3


def test_consequence_returned_exactly_once_even_if_more_violations_follow_non_abort():
    spec = _spec(consequence=Consequence.PROCEED_WITH_DECLARED_CEILING, max_violations=1,
                 declared_ceiling="cap 8192", projected_cost="~10h wall")
    tracker = ToleranceTracker(spec)
    assert tracker.observe(True) is None            # violation 1 of <=1
    assert tracker.observe(True) is Consequence.PROCEED_WITH_DECLARED_CEILING   # violation 2: fires
    # further violations under the declared ceiling never re-fire the consequence.
    assert tracker.observe(True) is None
    assert tracker.observe(False) is None
    assert tracker.violations == 3
    assert tracker.breached is True


def test_non_violations_never_advance_the_counter_or_trip_the_boundary():
    spec = _spec(consequence=Consequence.ABORT, max_violations=1)
    tracker = ToleranceTracker(spec)
    for _ in range(10):
        assert tracker.observe(False) is None
    assert tracker.violations == 0 and tracker.cases_observed == 10 and not tracker.breached


def test_abort_then_further_observe_refused():
    spec = _spec(consequence=Consequence.ABORT, max_violations=0)
    tracker = ToleranceTracker(spec)
    assert tracker.observe(True) is Consequence.ABORT   # k=0: the 1st violation is k+1
    assert tracker.aborted is True
    with pytest.raises(ToleranceBreach) as exc_info:
        tracker.observe(False)   # even a non-violation is refused: the run halted
    assert exc_info.value.spec is spec
    assert exc_info.value.count == 1


def test_recalibrate_does_not_structurally_block_further_observe():
    spec = _spec(consequence=Consequence.RECALIBRATE, max_violations=0,
                 recalibration_procedure="re-run the pilot at the recalibrated cap")
    tracker = ToleranceTracker(spec)
    assert tracker.observe(True) is Consequence.RECALIBRATE
    assert tracker.aborted is False
    # RECALIBRATE licenses continuation; this must not raise.
    assert tracker.observe(False) is None


def test_to_consequence_action_snapshots_the_dispatch_moment_not_later_state():
    spec = _spec(consequence=Consequence.RECALIBRATE, max_violations=0,
                 recalibration_procedure="re-run the pilot at the recalibrated cap")
    tracker = ToleranceTracker(spec)
    tracker.observe(True)                 # violation 1 of <=0: fires, snapshot (1, 1)
    tracker.observe(True)                 # continues legally under RECALIBRATE
    tracker.observe(False)
    tracker.observe(True)                 # violations now 3, cases_observed now 4
    action = tracker.to_consequence_action()
    assert (action.at_violation, action.cases_observed) == (1, 1)
    assert (tracker.violations, tracker.cases_observed) == (3, 4)


def test_to_consequence_action_refused_before_breach_and_correct_after():
    spec = _spec(consequence=Consequence.ABORT, max_violations=1)
    tracker = ToleranceTracker(spec)
    tracker.observe(True)
    with pytest.raises(ValueError, match="not breached"):
        tracker.to_consequence_action()
    tracker.observe(True)   # the 2nd violation crosses the boundary
    action = tracker.to_consequence_action()
    assert isinstance(action, ConsequenceAction)
    assert action.spec_id == spec.spec_id
    assert action.spec_digest == spec.spec_digest
    assert action.consequence is Consequence.ABORT
    assert action.at_violation == 2
    assert action.cases_observed == 2


# ---------------------------------------------------------------- Part A: resume / from_persisted

def test_from_persisted_reconstructs_mid_run_not_yet_breached():
    spec = _spec(consequence=Consequence.ABORT, max_violations=3)
    tracker = ToleranceTracker.from_persisted(spec, [True, False, True, False])
    assert tracker.violations == 2 and tracker.cases_observed == 4
    assert tracker.breached is False
    # continuing live behaves exactly as if it had never stopped.
    assert tracker.observe(True) is None
    assert tracker.observe(True) is Consequence.ABORT


def test_from_persisted_is_born_breached_when_the_persisted_prefix_already_crosses():
    spec = _spec(consequence=Consequence.PROCEED_WITH_DECLARED_CEILING, max_violations=2,
                 declared_ceiling="cap 8192", projected_cost="~10h wall")
    tracker = ToleranceTracker.from_persisted(spec, [True, True, True])
    assert tracker.breached is True
    assert tracker.violations == 3
    # PROCEED licenses continuation even born-breached.
    assert tracker.observe(False) is None


def test_from_persisted_is_born_aborted_and_refuses_replay_past_the_abort_point():
    spec = _spec(consequence=Consequence.ABORT, max_violations=1)
    with pytest.raises(ToleranceBreach):
        # a persisted prefix with a row recorded AFTER the abort crossing should
        # never exist structurally (ABORT halts the run); replay refuses it.
        ToleranceTracker.from_persisted(spec, [True, True, True])


def test_from_persisted_born_aborted_then_live_observe_refused():
    spec = _spec(consequence=Consequence.ABORT, max_violations=1)
    tracker = ToleranceTracker.from_persisted(spec, [True, True])
    assert tracker.aborted is True
    with pytest.raises(ToleranceBreach):
        tracker.observe(False)


# ---------------------------------------------------------------- Part B: curtailment arithmetic

def test_curtailment_boundary_not_curtailed_exactly_at_the_ceiling():
    # n=10, bar=0.6 -> threshold = ceil(6.0) = 6. passes=4, cases_done=8 -> remaining=2,
    # 4+2 == 6 == threshold: NOT curtailed (a clean sweep of the remainder exactly qualifies).
    policy = CurtailmentPolicy(bar=0.6, n_total=10)
    assert policy.threshold == 6
    assert policy.should_curtail(passes=4, cases_done=8) is False


def test_curtailment_fires_one_below_the_ceiling():
    policy = CurtailmentPolicy(bar=0.6, n_total=10)
    # passes=3, cases_done=8 -> remaining=2, 3+2=5 < 6: curtailed.
    assert policy.should_curtail(passes=3, cases_done=8) is True


def test_curtailment_uses_exact_ceiling_not_a_float_bar_times_n():
    # bar*n_total = 0.55 * 20 = 11.0 exactly at float precision, but pick a bar/n pair
    # where bar*n_total is NOT an integer, so ceil() must actually round up.
    policy = CurtailmentPolicy(bar=1 / 3, n_total=10)
    assert policy.threshold == 4    # ceil(3.333...) == 4, not 3
    assert policy.should_curtail(passes=2, cases_done=8) is False   # 2+2=4 == threshold: not curtailed
    assert policy.should_curtail(passes=1, cases_done=8) is True    # 1+2=3 < 4: curtailed


def test_curtailment_policy_rejects_out_of_range_bar_and_n_total():
    with pytest.raises(ValueError):
        CurtailmentPolicy(bar=0.0, n_total=10)
    with pytest.raises(ValueError):
        CurtailmentPolicy(bar=1.1, n_total=10)
    with pytest.raises(ValueError):
        CurtailmentPolicy(bar=0.5, n_total=0)
    with pytest.raises(ValueError):
        CurtailmentPolicy(bar=0.5, n_total=-3)


def test_certain_interval_is_passes_to_passes_plus_remaining():
    policy = CurtailmentPolicy(bar=0.6, n_total=48)
    assert policy.certain_interval(passes=10, cases_done=30) == (10, 28)


# ---------------------------------------------------------------- Part B: curtailment reporting

def test_make_curtailment_report_has_no_point_estimate_key():
    report = make_curtailment_report(
        run_id="r6-efficiency-dev-01", split="dev", arm="candidate-x",
        passes=3, cases_done=8, n_total=10, bar=0.6, unrun_classes=["S09", "S10", "S11", "S12"],
    )
    # guard 2 (interval-only reporting): no key that could be read as a point estimate.
    forbidden = {"rate", "pass_rate", "estimate", "point_estimate", "mean", "avg", "score"}
    assert forbidden.isdisjoint(report.keys())
    assert report["interval"] == [3, 5]
    assert report["curtailed"] is True
    assert report["unrun_classes"] == ["S09", "S10", "S11", "S12"]
    assert report["run_id"] == "r6-efficiency-dev-01"


def test_make_curtailment_report_only_reports_when_actually_curtailed_by_policy():
    # sanity: the interval computed by the report matches CurtailmentPolicy directly.
    policy = CurtailmentPolicy(bar=0.6, n_total=10)
    assert policy.should_curtail(passes=3, cases_done=8) is True
    report = make_curtailment_report("r1", "test", "arm", 3, 8, 10, 0.6, [])
    assert tuple(report["interval"]) == policy.certain_interval(3, 8)


# ---------------------------------------------------------------- Part B: append-only jsonl

def test_append_and_read_curtailed_runs_roundtrip(tmp_path):
    path = tmp_path / "curtailed_runs.jsonl"
    assert read_curtailed_runs(path) == []   # missing file reads as empty, not an error
    r1 = make_curtailment_report("r1", "dev", "candidate-a", 3, 8, 10, 0.6, ["S09"])
    r2 = make_curtailment_report("r2", "test", "candidate-b", 40, 70, 96, 0.55, ["S11", "S12"])
    append_curtailed_run(path, r1)
    append_curtailed_run(path, r2)
    rows = read_curtailed_runs(path)
    assert [row["run_id"] for row in rows] == ["r1", "r2"]
    assert rows[0]["curtailed"] is True and rows[1]["curtailed"] is True


def test_append_curtailed_run_never_truncates_existing_lines(tmp_path):
    path = tmp_path / "curtailed_runs.jsonl"
    append_curtailed_run(path, make_curtailment_report("r1", "dev", "a", 1, 5, 10, 0.6, []))
    before = path.read_text()
    append_curtailed_run(path, make_curtailment_report("r2", "dev", "b", 1, 5, 10, 0.6, []))
    after = path.read_text()
    assert after.startswith(before)
