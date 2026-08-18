"""R5 leak guards — the learned router may be *scored* by gold, never *fed* it.

`docs/R5_EXPERIMENT_CONTRACT.md` § 6 pre-registers nine guards on the feature boundary.
They are here, one test function each (guard 9 is the import ban, which lives in
`test_routing_no_gold_leak.py` and is only pinned from here), plus one extra test that
ties the snapshot to the incumbent R4 gate: if the features could not reproduce
`should_escalate(signals_from(...))`, then "R4 ∨ risk ≥ τ" would not be measuring the
residual over R4 and every DEV comparison in § 12 would be against a moving baseline.

The trajectories are built by hand rather than run, so a guard cannot pass because a
fixture happened not to carry the field it is supposed to prove is unread.
"""

import inspect
import json

import pytest
from pydantic import ValidationError

from fis_platform.routing.features import (
    FEATURE_FAMILIES,
    FEATURE_ORDER,
    FEATURE_SCHEMA_VERSION,
    FORBIDDEN_FEATURE_NAMES,
    AnswerFields,
    RoutingFeatureSnapshot,
    is_forbidden_feature_name,
    snapshot_from,
)
from schemas import (
    GOLD_FEATURE_NAMES,
    FailureClass,
    HumanFeedback,
    InvestigationResult,
    LatencyRecord,
    ModelInvocation,
    ModelTier,
    Provider,
    RouterDecision,
    TokenUsage,
    ToolCall,
    Trajectory,
    VerificationResult,
)
from schemas.investigator import Fact, NextAction, RootCause, RootCauseLabel
from services.ai_orchestrator.cascade import EscalationPolicy, should_escalate, signals_from
from tests.test_routing_no_gold_leak import ROOT, ROUTING_MODULES

CLEAN_CHECKS = {
    "schema_validation": True, "citation_required": True, "citation_resolves_to_call": True,
    "cited_ids_observed": True, "known_action_code": True, "confidence_supported": True,
    "facts_present": True,
}


def _invocation(**overrides) -> ModelInvocation:
    kwargs = {
        "tier": ModelTier.SPECIALIST,
        "provider": Provider.LOCAL_LLAMACPP,
        "model_id": "qwen3-8b-q4km",
        "canonical_model": "qwen3-8b",
        "prompt_version": "cause_action_directed@1",
        "usage": TokenUsage(input_tokens=12000, output_tokens=900),
        "latency": LatencyRecord(wall_ms=41000, api_ms=40500),
        "stop_reason": "stop",
        "max_tokens": 4096,
        "reasoning_chars": 3000,
        "content_chars": 1000,
    }
    kwargs.update(overrides)
    return ModelInvocation(**kwargs)


def _calls() -> list[ToolCall]:
    return [
        ToolCall(tool="get_case", version=1, args_hash="h1", status="success",
                 latency_ms=3, sequence=0),
        ToolCall(tool="get_webhook_history", version=1, args_hash="h2", status="success",
                 latency_ms=7, sequence=1),
        ToolCall(tool="get_webhook_history", version=1, args_hash="h2", status="success",
                 latency_ms=5, sequence=2),
        ToolCall(tool="get_verifications", version=1, args_hash="h3", status="error",
                 error_code="not_found", latency_ms=2, sequence=3),
    ]


def _traj(*, verification: VerificationResult | None = None, error: str | None = None,
          invocations: list[ModelInvocation] | None = None,
          calls: list[ToolCall] | None = None, **eval_fields) -> Trajectory:
    """A local-stage trajectory. `eval_fields` carries the harness-only metadata the
    extractor must not read (scenario_id, experiment_arm, case_id, runtime_context)."""
    return Trajectory(
        workflow="case_investigation", workflow_version="1", task_type="investigate",
        user="analyst",
        model_invocations=invocations if invocations is not None else [_invocation()],
        tool_calls=_calls() if calls is None else calls,
        verification=verification, error=error, **eval_fields,
    )


def _result() -> InvestigationResult:
    return InvestigationResult(
        case_id="CASE-1", classification="ledger_reconciliation",
        root_cause=RootCause(label=RootCauseLabel.SETTLEMENT_AMOUNT_MAPPING_ERROR,
                             confidence=0.8),
        facts=[Fact(claim="Settlement set_1 recorded 4210", source="tool://processor/set_1"),
               Fact(claim="Ledger le_1 recorded 4201", source="tool://ledger/le_1")],
        recommended_next_action=NextAction.INSPECT_MAPPING_VERSION,
        summary="Settlement and ledger amounts disagree by nine units.",
    )


def _clean_snapshot() -> RoutingFeatureSnapshot:
    verification = VerificationResult(passed=True, checks=dict(CLEAN_CHECKS), violations=[])
    return snapshot_from(_traj(verification=verification), _result())


# --- guard 1: forbidden and unlisted names are a schema error -------------------------

@pytest.mark.parametrize("leak", sorted(
    GOLD_FEATURE_NAMES | {"strict_all_pass", "score", "frontier", "truth", "expected_root_cause"}
))
def test_forbidden_feature_names_cannot_enter_a_snapshot(leak):
    features = dict(_clean_snapshot().features)
    features[leak] = 1.0
    with pytest.raises(ValidationError, match="forbidden routing feature"):
        RoutingFeatureSnapshot(features=features, digest="")


def test_a_name_outside_the_allowlist_is_a_schema_error():
    features = dict(_clean_snapshot().features)
    features["local_gpu_temperature_c"] = 61.0
    with pytest.raises(ValidationError, match="outside the FEATURE_ORDER allowlist"):
        RoutingFeatureSnapshot(features=features, digest="")


def test_an_incomplete_or_non_finite_vector_is_a_schema_error():
    """Positions are the contract: a missing feature would shift every coefficient."""
    features = dict(_clean_snapshot().features)
    features.pop("budget_used")
    with pytest.raises(ValidationError, match="incomplete feature vector"):
        RoutingFeatureSnapshot(features=features, digest="")
    features = dict(_clean_snapshot().features)
    features["budget_used"] = float("inf")
    with pytest.raises(ValidationError, match="non-finite"):
        RoutingFeatureSnapshot(features=features, digest="")


def test_the_allowlist_and_the_forbidden_list_are_disjoint():
    assert not [n for n in FEATURE_ORDER if is_forbidden_feature_name(n)]
    assert set(FEATURE_ORDER) == set(sum(FEATURE_FAMILIES.values(), ()))
    assert len(set(FEATURE_ORDER)) == len(FEATURE_ORDER)
    assert GOLD_FEATURE_NAMES <= FORBIDDEN_FEATURE_NAMES


# --- guard 2: extraction works with no gold/scorer fields at all -----------------------

def test_extraction_succeeds_on_a_trajectory_with_no_eval_metadata():
    traj = _traj(verification=VerificationResult(passed=True, checks=dict(CLEAN_CHECKS)),
                 scenario_id=None, experiment_arm=None, case_id=None, runtime_context={})
    snap = snapshot_from(traj, _result())
    assert set(snap.features) == set(FEATURE_ORDER)
    assert snap.local_model == "qwen3-8b"
    assert snap.features["produced_output"] == 1.0
    assert snap.features["n_repeated_calls"] == 1.0        # get_webhook_history twice, same args
    assert snap.features["n_tool_errors"] == 1.0
    assert snap.features["said_label_settlement_amount_mapping_error"] == 1.0
    assert snap.features["said_action_inspect_mapping_version"] == 1.0


# --- guard 3: gold-removal invariance --------------------------------------------------

def test_digest_is_invariant_to_scenario_arm_case_and_runtime_metadata():
    """Every field the harness writes *after* the R4 decision point, plus the eval
    metadata written before it. `router`, `human_feedback`, `business_outcome`,
    `failure_class` and `ToolCall.was_useful` are all filled by the learning plane once
    the case has been scored — a snapshot that moved with any of them would be reading
    the future of the decision it is supposed to be taken at.
    """
    verification = VerificationResult(passed=True, checks=dict(CLEAN_CHECKS))
    scored_calls = [_calls()[0].model_copy(update={"was_useful": True}), *_calls()[1:]]
    labelled = _traj(
        verification=verification,
        calls=scored_calls,
        scenario_id="S05-2001000", experiment_arm="E4", case_id="CASE-1",
        runtime_context={"root_cause": "settlement_amount_mapping_error", "split": "test",
                         "seed": "2001000", "strict_all_pass": "true", "category": "ledger"},
        router=RouterDecision(selected_specialist="x", confidence=0.5,
                              features={"x": 1.0}),
        failure_class=FailureClass.MODEL_REASONING_FAILURE,
        human_feedback=HumanFeedback(accepted=False, reason="wrong root cause"),
        business_outcome="failed",
    )
    bare = _traj(verification=VerificationResult(passed=True, checks=dict(CLEAN_CHECKS)))
    a, b = snapshot_from(labelled, _result()), snapshot_from(bare, _result())
    assert a.features == b.features
    assert a.digest == b.digest
    assert a.local_model == b.local_model
    # the perturbation really was present on the trajectory the extractor was handed
    assert labelled.router is not None and labelled.failure_class is not None
    assert labelled.human_feedback.accepted is False and labelled.business_outcome == "failed"
    assert labelled.tool_calls[0].was_useful is True and bare.tool_calls[0].was_useful is None


# --- guard 4: no feature name, and no parameter, smells of the answer key --------------

@pytest.mark.parametrize("banned", ["scenario", "class", "seed", "split", "category",
                                    "truth", "expected", "gold"])
def test_no_feature_name_mentions_the_answer_key(banned):
    assert not [name for name in FEATURE_ORDER if banned in name]


def test_extractor_signature_takes_no_score_or_manifest():
    params = inspect.signature(snapshot_from).parameters
    assert list(params) == ["trajectory", "answer"]


# --- guard 5: split metadata is neither a feature nor an input -------------------------

def test_split_metadata_is_not_an_input():
    verification = VerificationResult(passed=True, checks=dict(CLEAN_CHECKS))
    dev = _traj(verification=verification, runtime_context={"split": "dev"})
    test = _traj(verification=VerificationResult(passed=True, checks=dict(CLEAN_CHECKS)),
                 runtime_context={"split": "test"})
    assert snapshot_from(dev, _result()).digest == snapshot_from(test, _result()).digest
    assert "split" not in FEATURE_ORDER and is_forbidden_feature_name("split")


# --- guard 6: deterministic serialization ----------------------------------------------

def test_serialization_is_deterministic_and_ordered():
    first, second = _clean_snapshot(), _clean_snapshot()
    assert first.digest == second.digest
    assert first.canonical_json() == second.canonical_json()
    payload = json.loads(first.canonical_json())
    assert [name for name, _ in payload["features"]] == list(FEATURE_ORDER)
    assert payload["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert ", " not in first.canonical_json() and '": ' not in first.canonical_json()
    assert first.ordered_values() == [first.features[n] for n in FEATURE_ORDER]
    assert first.digest == RoutingFeatureSnapshot.compute_digest(first.features)


def test_a_digest_that_does_not_match_its_features_is_rejected():
    """The digest is the vector's identity in `learning.routing_decisions`; a stale one
    would silently join a decision to the wrong feature row."""
    snap = _clean_snapshot()
    with pytest.raises(ValidationError, match="does not match the features"):
        RoutingFeatureSnapshot(features=dict(snap.features), digest="0" * 64)


# --- guard 7: the schema version travels with every snapshot ---------------------------

def test_every_snapshot_records_the_feature_schema_version():
    assert FEATURE_SCHEMA_VERSION == "1"
    assert _clean_snapshot().feature_schema_version == FEATURE_SCHEMA_VERSION


# --- guard 8: production shape, and the scorer echo agrees with the real answer --------

def test_production_trajectory_and_answer_echo_agree():
    """DEV/TEST answers were not persisted (§ 5), so the two answer fields are rebuilt
    from the scorer's verbatim `said <label>` echo. The snapshot must not be able to
    tell the difference — otherwise the replayed features are not the live ones."""
    traj = _traj(verification=VerificationResult(passed=True, checks=dict(CLEAN_CHECKS)))
    result = _result()
    from_result = snapshot_from(traj, result)
    from_echo = snapshot_from(traj, AnswerFields(
        root_cause_label=result.root_cause.label.value,
        recommended_next_action=result.recommended_next_action.value,
    ))
    assert from_result.features == from_echo.features
    assert from_result.digest == from_echo.digest
    assert from_result.features["answer_present"] == 1.0


def test_an_unknown_echoed_label_matches_no_one_hot():
    traj = _traj(verification=VerificationResult(passed=True, checks=dict(CLEAN_CHECKS)))
    snap = snapshot_from(traj, AnswerFields(root_cause_label="not_a_label",
                                            recommended_next_action=None))
    one_hots = [v for k, v in snap.features.items() if k.startswith(("said_label_",
                                                                    "said_action_"))]
    assert sum(one_hots) == 0.0
    assert snap.features["answer_present"] == 1.0     # the model did answer, unusably


def test_a_no_output_trajectory_extracts_as_all_zero_family_a_and_no_answer():
    traj = _traj(verification=None, error="model produced no parseable structured output",
                 invocations=[_invocation(stop_reason="length",
                                          usage=TokenUsage(input_tokens=12000,
                                                           output_tokens=4096))])
    snap = snapshot_from(traj, None)
    assert snap.features["produced_output"] == 0.0
    assert snap.features["no_output_error"] == 1.0
    assert snap.features["stop_length"] == 1.0
    assert snap.features["budget_used"] == 1.0
    assert snap.features["answer_present"] == 0.0
    assert snap.features["checks_evaluated"] == 0.0


def test_a_trajectory_with_no_invocation_zeroes_family_a():
    snap = snapshot_from(_traj(invocations=[], verification=None, error="gateway timeout"), None)
    assert all(snap.features[name] == 0.0 for name in FEATURE_FAMILIES["A"])
    assert snap.local_model is None


def test_verifier_family_counts_the_violation_texts_the_verifier_actually_emits():
    verification = VerificationResult(
        passed=False,
        checks={"schema_validation": True, "citation_required": True,
                "citation_resolves_to_call": False, "cited_ids_observed": False,
                "known_action_code": True, "confidence_supported": True,
                "facts_present": True},
        violations=["cites an id no tool returned: le_999",
                    "cites a service that was never successfully called: tool://risk/r_1"],
    )
    snap = snapshot_from(_traj(verification=verification), _result())
    assert snap.features["n_violations"] == 2.0
    assert snap.features["n_fabricated_ids"] == 1.0
    assert snap.features["n_uncalled_services"] == 1.0
    assert snap.features["n_unsupported_claims"] == 2.0     # both carry an R4 marker
    assert snap.features["check_cited_ids_observed"] == 0.0
    assert snap.features["checks_evaluated"] == 7.0
    assert snap.features["schema_error_count"] == 0.0

    invalid = VerificationResult(passed=False, schema_valid=False,
                                 checks={"schema_validation": False},
                                 violations=["schema invalid: 3 error(s); first: field required"])
    bad = snapshot_from(_traj(verification=invalid), None)
    assert bad.features["schema_error_count"] == 3.0
    assert bad.features["produced_output"] == 0.0 and bad.features["schema_valid"] == 0.0


# --- guard 9: the package inherits the import ban --------------------------------------

def test_routing_package_is_covered_by_the_import_ban():
    assert ROOT / "fis_platform" / "routing" in ROUTING_MODULES


# --- the snapshot must reproduce the incumbent R4 gate ---------------------------------

def _r4_from_features(features: dict[str, float]) -> tuple[bool, str | None]:
    """R4's VERIFIER policy, recomputed from snapshot features alone."""
    if not features["produced_output"]:
        return True, "no_output"
    if features["n_unsupported_claims"]:
        return True, "unsupported_claims"
    if not features["verifier_passed"]:
        return True, "verifier_failed"
    return False, None


@pytest.mark.parametrize("verification,error,has_result", [
    (VerificationResult(passed=True, checks=dict(CLEAN_CHECKS)), None, True),
    (VerificationResult(passed=False, checks=dict(CLEAN_CHECKS, cited_ids_observed=False),
                        violations=["cites an id no tool returned: le_999"]), None, True),
    (VerificationResult(passed=False, checks=dict(CLEAN_CHECKS, confidence_supported=False),
                        violations=[("confidence 0.95 asserted after only 1 "
                                     "successful tool call(s)")]), None, True),
    (VerificationResult(passed=False, schema_valid=False, checks={"schema_validation": False},
                        violations=["schema invalid: 1 error(s); first: field required"]),
     None, False),
    (None, "model produced no parseable structured output", False),
])
def test_snapshot_features_reproduce_the_r4_decision(verification, error, has_result):
    """`escalate = R4 ∨ risk ≥ τ` only measures the residual if the snapshot can still
    express R4 exactly. Any drift here would move the baseline, not the policy."""
    result = _result() if has_result else None
    traj = _traj(verification=verification, error=error)
    snap = snapshot_from(traj, result)
    expected = should_escalate(signals_from(result, traj), EscalationPolicy.VERIFIER)
    assert _r4_from_features(snap.features) == expected
