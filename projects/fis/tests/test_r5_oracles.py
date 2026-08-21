"""The two classifications R5's oracle report is read through — the false-negative
bucketing and the three-tier cheapest-sufficient assignment — are pure functions of a
persisted score, so they are pinned here. Both feed prose in every R5 policy report
(contract § 11), and a bucketing that quietly changed would move published counts
without moving a single measurement."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from r5_oracles import fail_pattern, fn_bucket, three_tier  # noqa: E402


def score(*, rc=True, ev=1.0, act=True, forb=False, verifier=True, unsupported=0,
          produced=True, threshold=0.8):
    dims = [] if produced else [{"name": "produced_output", "value": 0.0, "passed": False,
                                 "detail": "no structured output"}]
    return {
        "root_cause_correct": rc, "required_evidence_recall": ev,
        "evidence_recall_threshold": threshold, "next_action_acceptable": act,
        "forbidden_claim_made": forb, "verifier_passed": verifier,
        "unsupported_claims": unsupported, "dimensions": dims,
    }


class TestFnBucket:
    def test_wrong_root_cause_dominates(self):
        assert fn_bucket(score(rc=False)) == "root_cause"
        # …even when evidence and action are also wrong: it is a different kind of failure.
        assert fn_bucket(score(rc=False, ev=0.25, act=False)) == "root_cause"

    def test_evidence_only(self):
        assert fn_bucket(score(ev=0.67)) == "evidence_only"

    def test_evidence_at_threshold_is_not_short(self):
        assert fn_bucket(score(ev=0.8)) == "other"          # nothing failed on these dims
        assert fn_bucket(score(ev=0.79)) == "evidence_only"

    def test_non_default_threshold_is_honoured(self):
        assert fn_bucket(score(ev=0.9, threshold=1.0)) == "evidence_only"

    def test_action_only(self):
        assert fn_bucket(score(act=False)) == "action_only"

    def test_mixed_and_forbidden_fall_to_other(self):
        assert fn_bucket(score(ev=0.5, act=False)) == "other"
        assert fn_bucket(score(ev=0.5, forb=True)) == "other"
        assert fn_bucket(score(forb=True)) == "other"

    def test_buckets_are_exclusive_and_total(self):
        cases = [score(rc=r, ev=e, act=a, forb=f)
                 for r in (True, False) for e in (1.0, 0.5) for a in (True, False)
                 for f in (True, False)]
        assert {fn_bucket(c) for c in cases} <= {"root_cause", "evidence_only",
                                                 "action_only", "other"}
        assert all(isinstance(fn_bucket(c), str) for c in cases)


class TestFailPattern:
    def test_visible_failures_come_first(self):
        # no-output outranks everything: the gate sees it before any dimension.
        assert fail_pattern(score(produced=False, verifier=False, rc=False, ev=0.0,
                                  act=False), False) == "no-output"
        assert fail_pattern(score(verifier=False, unsupported=2), False) == \
            "verifier-fail(unsupported)"
        assert fail_pattern(score(verifier=False), False) == "verifier-fail(other)"

    def test_silent_is_the_blind_spot(self):
        assert fail_pattern(score(ev=0.5), False) == "silent:evidence_only"
        assert fail_pattern(score(rc=False), False) == "silent:root_cause"

    def test_all_pass_short_circuits(self):
        assert fail_pattern(score(), True) == "pass"


class TestThreeTier:
    @pytest.mark.parametrize("q,nm,s,expected", [
        (True, True, True, "qwen"),
        (True, False, False, "qwen"),      # cheapest sufficient, not "best available"
        (False, True, True, "nemotron"),
        (False, True, False, "nemotron"),
        (False, False, True, "frontier"),
        (False, False, False, "unresolved"),
    ])
    def test_assignment(self, q, nm, s, expected):
        assert three_tier(q, nm, s) == expected
