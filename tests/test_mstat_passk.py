"""pass^k protocol — SPEC, sample-set validation, estimator (M_STAT_IMPLEMENTATION_MAP.md
item 13; playbook § 7 / master plan § 7). Implementation without execution: nothing
here draws a sample, calls a model, or touches the database — every test builds its
own PassKSpec + PassKSample fixtures in memory.

What each group defends:

  spec         a malformed declaration (bad k, duplicate case, wrong subset digest, a
               TEST spec with no declared look, a selection-use spec) must be
               unrepresentable or refused at construction — never silently accepted
               and discovered later at the estimator;
  samples      `validate_samples` is the ONE gate between caller-supplied draws and any
               arithmetic; every one of its checks needs a fixture that trips it;
  estimator    `estimate` must agree with `validate_samples` about what is valid, and
               its arithmetic must match a hand-computed known answer.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.passk import (
    PassKSample,
    PassKSampleRefused,
    PassKSpec,
    estimate,
    validate_samples,
)
from fis_platform.provenance import digest

SCENARIO_IDS = ["S01-0000001", "S01-0000002", "S01-0000003"]


def _spec(**over) -> PassKSpec:
    fields = dict(
        spec_id="passk-smoke-1",
        suite_version="3",
        split="test",
        k=3,
        scenario_ids=list(SCENARIO_IDS),
        look_run_id="R6-smoke-test",
        measurement_only=True,
    )
    fields.update(over)
    return PassKSpec(**fields)


def _samples(spec: PassKSpec, *, run_id: str | None = None,
             fail: frozenset[tuple[str, int]] = frozenset()) -> list[PassKSample]:
    """All-pass fixture, k samples per declared case, unless (scenario_id, index) is
    in `fail` (then that draw is recorded as failed) or `run_id` overrides the spec's
    declared look."""
    rid = run_id if run_id is not None else spec.look_run_id
    out = []
    for sid in spec.scenario_ids:
        for i in range(spec.k):
            out.append(PassKSample(scenario_id=sid, sample_index=i,
                                    passed=(sid, i) not in fail, run_id=rid))
    return out


# --------------------------------------------------------------------------- spec

def test_valid_fixture_roundtrip():
    spec = _spec()
    assert spec.subset_digest == digest(sorted(SCENARIO_IDS))
    assert len(spec.spec_digest) == 64
    # deterministic: an identical spec built again digests identically
    assert _spec().spec_digest == spec.spec_digest

    samples = _samples(spec)
    validate_samples(spec, samples)  # does not raise
    result = estimate(spec, samples)
    assert result == {
        "per_case": {sid: True for sid in SCENARIO_IDS},
        "pass_k": 1.0,
        "pass_1_mean": 1.0,
        "n_cases": 3,
        "k": 3,
    }


def test_k_out_of_range_refused():
    with pytest.raises(ValueError, match="k"):
        _spec(k=1)
    with pytest.raises(ValueError, match="k"):
        _spec(k=11)


def test_duplicate_scenario_refused():
    with pytest.raises(ValueError, match="duplicate"):
        _spec(scenario_ids=[SCENARIO_IDS[0], SCENARIO_IDS[1], SCENARIO_IDS[0]])


def test_bad_scenario_id_pattern_refused():
    with pytest.raises(ValueError, match="scenario_ids must match"):
        _spec(scenario_ids=["not-a-scenario-id", SCENARIO_IDS[1], SCENARIO_IDS[2]])


def test_subset_digest_mismatch_refused():
    with pytest.raises(ValueError, match="subset_digest"):
        _spec(subset_digest="a" * 64)


def test_split_test_without_look_run_id_refused():
    with pytest.raises(ValueError, match="look_run_id is required"):
        _spec(look_run_id=None)


def test_rehearsal_split_allows_no_look_run_id():
    spec = _spec(split="train", look_run_id=None)
    assert spec.look_run_id is None
    samples = _samples(spec, run_id="rehearsal-run-1")
    validate_samples(spec, samples)  # does not raise: one shared run_id is enough


def test_measurement_only_false_is_unrepresentable():
    with pytest.raises(ValueError):
        _spec(measurement_only=False)


# --------------------------------------------------------------------- validate_samples

def test_missing_sample_refused():
    spec = _spec()
    samples = _samples(spec)
    short = [s for s in samples if not (s.scenario_id == SCENARIO_IDS[0] and s.sample_index == 2)]
    with pytest.raises(PassKSampleRefused, match="fewer than k=3"):
        validate_samples(spec, short)
    with pytest.raises(PassKSampleRefused, match="fewer than k=3"):
        estimate(spec, short)


def test_extra_sample_refused():
    spec = _spec()
    samples = _samples(spec)
    extra = samples + [PassKSample(scenario_id=SCENARIO_IDS[0], sample_index=2,
                                   passed=True, run_id=spec.look_run_id)]
    with pytest.raises(PassKSampleRefused, match="more than k=3"):
        validate_samples(spec, extra)


def test_wrong_run_id_refused():
    spec = _spec()
    samples = _samples(spec)
    tampered = list(samples)
    tampered[0] = PassKSample(scenario_id=tampered[0].scenario_id,
                              sample_index=tampered[0].sample_index,
                              passed=tampered[0].passed, run_id="some-other-run")
    with pytest.raises(PassKSampleRefused, match="do not match the spec's declared look"):
        validate_samples(spec, tampered)


def test_sample_index_gap_refused():
    spec = _spec()
    samples = _samples(spec)
    # for SCENARIO_IDS[0]: duplicate index 0, drop index 2 — count stays k=3
    gapped = [s for s in samples if not (s.scenario_id == SCENARIO_IDS[0] and s.sample_index == 2)]
    gapped.append(PassKSample(scenario_id=SCENARIO_IDS[0], sample_index=0,
                              passed=True, run_id=spec.look_run_id))
    assert len([s for s in gapped if s.scenario_id == SCENARIO_IDS[0]]) == 3
    with pytest.raises(PassKSampleRefused, match="not exactly"):
        validate_samples(spec, gapped)


def test_samples_outside_subset_refused():
    spec = _spec()
    samples = _samples(spec)
    samples.append(PassKSample(scenario_id="S01-9999999", sample_index=0,
                               passed=True, run_id=spec.look_run_id))
    with pytest.raises(PassKSampleRefused, match="outside the declared subset"):
        validate_samples(spec, samples)


def test_rehearsal_samples_must_share_one_run_id():
    spec = _spec(split="dev", look_run_id=None)
    samples = _samples(spec, run_id="rehearsal-a")
    samples[0] = PassKSample(scenario_id=samples[0].scenario_id,
                             sample_index=samples[0].sample_index,
                             passed=samples[0].passed, run_id="rehearsal-b")
    with pytest.raises(PassKSampleRefused, match="distinct run_id"):
        validate_samples(spec, samples)


# ------------------------------------------------------------------------ estimator

def test_estimator_known_answer_one_failed_sample():
    spec = _spec()
    samples = _samples(spec, fail=frozenset({(SCENARIO_IDS[0], 1)}))
    result = estimate(spec, samples)
    assert result["per_case"] == {
        SCENARIO_IDS[0]: False, SCENARIO_IDS[1]: True, SCENARIO_IDS[2]: True,
    }
    assert result["pass_k"] == pytest.approx(2 / 3)
    assert result["pass_1_mean"] == pytest.approx(8 / 9)
    assert result["n_cases"] == 3
    assert result["k"] == 3
