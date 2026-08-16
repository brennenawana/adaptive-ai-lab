"""R4 gate semantics: production-available signals only, policies nested as documented."""

import pytest

from schemas import GOLD_FEATURE_NAMES, InvestigationResult, Trajectory, VerificationResult
from schemas.investigator import Fact, NextAction, RootCause, RootCauseLabel
from services.ai_orchestrator.cascade import (
    EscalationPolicy, EscalationSignals, should_escalate, signals_from,
)


def _traj(passed: bool, violations: list[str], error: str | None = None) -> Trajectory:
    return Trajectory(workflow="w", workflow_version="1", task_type="t", user="u",
                      verification=VerificationResult(passed=passed, violations=violations),
                      error=error)


def _result() -> InvestigationResult:
    return InvestigationResult(
        case_id="c", classification="ledger_reconciliation",
        root_cause=RootCause(label=RootCauseLabel.SETTLEMENT_AMOUNT_MAPPING_ERROR, confidence=0.8),
        facts=[Fact(claim="Settlement set_1 recorded 4210", source="tool://processor/set_1"),
               Fact(claim="Ledger le_1 recorded 4201", source="tool://ledger/le_1")],
        recommended_next_action=NextAction.INSPECT_MAPPING_VERSION,
        summary="Settlement and ledger amounts disagree by nine units.",
    )


def test_no_output_is_a_verifier_failure_and_escalates_under_parse_and_verifier():
    sig = signals_from(None, _traj(False, ["schema invalid: 1 error(s)"],
                                   error="model produced no parseable structured output"))
    assert not sig.produced_output and not sig.verifier_passed
    assert should_escalate(sig, EscalationPolicy.NONE) == (False, None)
    assert should_escalate(sig, EscalationPolicy.PARSE) == (True, "no_output")
    assert should_escalate(sig, EscalationPolicy.VERIFIER) == (True, "no_output")


def test_unsupported_claim_escalates_only_under_verifier_policy():
    sig = signals_from(_result(), _traj(False, ["cites an id no tool returned: le_999"]))
    assert sig.produced_output and sig.unsupported_claims == 1 and not sig.verifier_passed
    assert should_escalate(sig, EscalationPolicy.PARSE) == (False, None)
    assert should_escalate(sig, EscalationPolicy.VERIFIER) == (True, "unsupported_claims")


def test_other_verifier_failures_escalate_as_verifier_failed():
    sig = signals_from(_result(), _traj(False, ["confidence 0.95 asserted after only 1 successful tool call(s)"]))
    assert sig.unsupported_claims == 0
    assert should_escalate(sig, EscalationPolicy.VERIFIER) == (True, "verifier_failed")
    assert should_escalate(sig, EscalationPolicy.PARSE) == (False, None)


def test_clean_weak_result_is_accepted_by_every_policy():
    sig = signals_from(_result(), _traj(True, []))
    for p in EscalationPolicy:
        assert should_escalate(sig, p) == (False, None)


def test_gate_features_are_production_available():
    """The features a RouterDecision records must never be scorer knowledge."""
    feats = EscalationSignals(True, True, 0, ()).as_features()
    assert set(feats) == {"produced_output", "verifier_passed", "unsupported_claims"}
    assert not set(feats) & GOLD_FEATURE_NAMES


@pytest.mark.parametrize("policy", list(EscalationPolicy))
def test_policies_are_nested_prefixes(policy):
    """NONE ⊂ PARSE ⊂ VERIFIER: anything PARSE escalates, VERIFIER escalates too."""
    cases = [
        signals_from(None, _traj(False, ["schema invalid"])),
        signals_from(_result(), _traj(False, ["malformed citation: x"])),
        signals_from(_result(), _traj(True, [])),
    ]
    order = [EscalationPolicy.NONE, EscalationPolicy.PARSE, EscalationPolicy.VERIFIER]
    for weaker, stronger in zip(order, order[1:]):
        for sig in cases:
            if should_escalate(sig, weaker)[0]:
                assert should_escalate(sig, stronger)[0]
