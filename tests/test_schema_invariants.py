"""These test the *guardrails*, not the happy path.

Each one corresponds to a way the eval could be silently corrupted. If any of these
stop failing, a scoring bug has become possible.
"""

import pytest
from pydantic import ValidationError

from schemas import (
    CaseScore, Fact, InvestigationResult, ModelManifest, ModelTier, NextAction,
    PriceTable, Provider, RootCause, RootCauseLabel, RoutingPolicy, Specialist,
    ModelBinding, ToolDefinition, ToolKind,
)

GOOD_DESC = "Use when the case involves a settlement or ledger discrepancy needing amounts."


def test_tool_cannot_unforbid_ground_truth():
    """The answer key must stay unreachable from any AI-facing tool."""
    with pytest.raises(ValidationError, match="ground_truth"):
        ToolDefinition(
            name="get_ledger_entries", version=1, kind=ToolKind.READ,
            description=GOOD_DESC, owning_service="ledger_service",
            input_schema={}, output_schema={}, forbidden_schemas=[],
        )


def test_tool_description_must_say_when_to_use():
    with pytest.raises(ValidationError, match="WHEN to use"):
        ToolDefinition(
            name="get_ledger_entries", version=1, kind=ToolKind.READ,
            description="Returns ledger entries for an account and time window.",
            owning_service="ledger_service", input_schema={}, output_schema={},
        )


def test_facts_reject_hedged_language():
    """Hedged claims belong in hypotheses — that split is what makes
    unsupported-claim rate measurable."""
    with pytest.raises(ValidationError, match="hedged"):
        Fact(claim="The amount was probably mis-mapped", source="tool://ledger/le_884")


def test_facts_require_cross_service_corroboration():
    facts = [
        Fact(claim="Settlement set_912 recorded 4210 USD", source="tool://processor/set_912"),
        Fact(claim="Settlement set_912 currency is USD", source="tool://processor/set_912"),
    ]
    with pytest.raises(ValidationError, match="corroboration"):
        InvestigationResult(
            case_id="case_1", classification="ledger_reconciliation",
            root_cause=RootCause(label=RootCauseLabel.SETTLEMENT_AMOUNT_MAPPING_ERROR,
                                 confidence=0.8),
            facts=facts, recommended_next_action=NextAction.INSPECT_MAPPING_VERSION,
            summary="Settlement and ledger amounts disagree by ninety units.",
        )


def test_valid_investigation_passes():
    result = InvestigationResult(
        case_id="case_1", classification="ledger_reconciliation",
        root_cause=RootCause(label=RootCauseLabel.SETTLEMENT_AMOUNT_MAPPING_ERROR,
                             confidence=0.82),
        facts=[
            Fact(claim="Settlement set_912 recorded 4210 USD", source="tool://processor/set_912"),
            Fact(claim="Ledger entry le_884 posted 4120 USD", source="tool://ledger/le_884"),
        ],
        hypotheses=["The v3 mapping may transpose digits during minor-unit conversion."],
        recommended_next_action=NextAction.INSPECT_MAPPING_VERSION,
        summary="Processor settlement and ledger posting disagree by ninety units.",
    )
    assert result.root_cause.confidence == 0.82


def test_specialist_must_declare_schema_validation():
    with pytest.raises(ValidationError, match="schema_validation"):
        Specialist(
            id="ops-investigator", version="0.1.0", description="d",
            primary=ModelBinding(tier=ModelTier.SPECIALIST, model_ref="local-8b"),
            system_contract_ref="prompts/investigator.md", prompt_version="1",
            tools=["get_case@v1"], output_schema_ref="schemas.InvestigationResult",
            verifiers=["citation_required"],
            routing=RoutingPolicy(task_types=["ops.investigate"]),
            eval_suite="fis-eval-v1",
        )


def test_frontier_model_requires_price_table():
    """A frontier arm with no price table contributes 0.0 to reference cost and
    would look free in the KPI."""
    with pytest.raises(ValidationError, match="PriceTable"):
        ModelManifest(
            ref="claude-frontier", tier=ModelTier.FRONTIER, provider=Provider.CLAUDE_CLI,
            model_id="claude-opus-5", context_window=1_000_000, max_output_tokens=64_000,
            base_url="http://x",
        )


def test_model_must_be_reachable():
    with pytest.raises(ValidationError, match="unreachable"):
        ModelManifest(
            ref="ghost", tier=ModelTier.SPECIALIST, provider=Provider.LOCAL_LLAMACPP,
            model_id="qwen3-8b", context_window=32_768, max_output_tokens=4096,
        )


def test_all_pass_is_conjunctive():
    """Every dimension must hold. A near-miss is a fail — that is the point of the
    strict metric."""
    base = dict(
        scenario_id="S06-00421", trace_id="t", experiment_arm="E2",
        root_cause_correct=True, required_evidence_recall=1.0, unsupported_claims=0,
        next_action_acceptable=True, verifier_passed=True,
    )
    assert CaseScore(**base).all_pass

    assert not CaseScore(**{**base, "unsupported_claims": 1}).all_pass
    assert not CaseScore(**{**base, "required_evidence_recall": 0.5}).all_pass
    assert not CaseScore(**{**base, "verifier_passed": False}).all_pass
    assert not CaseScore(**{**base, "forbidden_claim_made": True}).all_pass


def test_price_table_costs_cache_tokens():
    """Cached tokens must not be priced at zero by omission."""
    p = PriceTable(basis="list-2026-08", input_per_mtok=5.0, output_per_mtok=25.0)
    # 685 cache-creation tokens fall back to the input rate, not free.
    assert p.cost_usd(input_tokens=0, output_tokens=0, cache_creation=1_000_000) == 5.0
    assert p.cost_usd(input_tokens=1_000_000, output_tokens=1_000_000) == 30.0
