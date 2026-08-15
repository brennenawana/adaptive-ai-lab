"""Investigator output contract — what the AI must return for a case.

The guide's central design choice is the fact/hypothesis split. A model that says
"the settlement amount was mis-mapped" as a *fact* without a tool citation is
hallucinating; the same sentence as a *hypothesis* is good operational reasoning.
Separating them at the type level is what makes "unsupported-claim rate" measurable
rather than a matter of opinion.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, field_validator

from .common import Base, Confidence, FrozenBase


class RootCauseLabel(StrEnum):
    """Closed label set, matching the twelve seeded scenario classes.

    Closed rather than free-text because root-cause accuracy is scored by exact or
    accepted-label match — the guide is explicit that we should not ask an LLM judge
    to grade something we can test objectively.
    """

    DUPLICATE_WEBHOOK_HANDLED = "duplicate_webhook_handled"
    MISSING_IDEMPOTENCY = "missing_idempotency"
    KYC_HOLD = "kyc_hold"
    PROVIDER_OUTAGE = "provider_outage"
    PROCESSOR_DECLINE = "processor_decline"
    SETTLEMENT_AMOUNT_MAPPING_ERROR = "settlement_amount_mapping_error"
    REVERSAL_RACE = "reversal_race"
    RISK_HOLD = "risk_hold"
    STALE_INTEGRATION_MAPPING = "stale_integration_mapping"
    RECONCILIATION_GAP = "reconciliation_gap"
    FALSE_POSITIVE_ALERT = "false_positive_alert"
    COMPOUND_FAILURE = "compound_failure"
    UNKNOWN = "unknown"


class NextAction(StrEnum):
    """Allowed action codes. Read-only project: these are recommendations an
    operator executes, never something the AI performs."""

    OPEN_RECONCILIATION_REVIEW = "open_reconciliation_review"
    INSPECT_MAPPING_VERSION = "inspect_mapping_version"
    REPLAY_WEBHOOK = "replay_webhook"
    CONTACT_IDENTITY_VENDOR = "contact_identity_vendor"
    REQUEST_KYC_DOCUMENTS = "request_kyc_documents"
    ESCALATE_TO_RISK_TEAM = "escalate_to_risk_team"
    RELEASE_RISK_HOLD_REVIEW = "release_risk_hold_review"
    NO_ACTION_REQUIRED = "no_action_required"
    ESCALATE_TO_ENGINEERING = "escalate_to_engineering"


class Fact(FrozenBase):
    """A claim the model asserts as true. Requires a tool citation, always.

    `source` must be a tool:// URI naming the call that produced it, so the verifier
    can confirm the referenced call actually happened in this trajectory.
    """

    claim: str = Field(min_length=5)
    source: str = Field(pattern=r"^tool://[a-z_]+/[A-Za-z0-9_./:-]+$")
    entity_ids: list[str] = Field(default_factory=list)

    @field_validator("claim")
    @classmethod
    def _no_hedging_in_facts(cls, v: str) -> str:
        # A hedged sentence is a hypothesis wearing a fact's clothes. Rejecting it
        # here forces the model to put it in `hypotheses`, which is what we want to
        # measure — not to punish uncertainty, but to locate it correctly.
        hedges = ("probably", "likely", "might be", "may be", "possibly", "i think", "appears to be")
        if any(h in v.lower() for h in hedges):
            raise ValueError(
                f"hedged language belongs in hypotheses, not facts: {v!r}"
            )
        return v


class RootCause(Base):
    label: RootCauseLabel
    confidence: Confidence


class InvestigationResult(Base):
    """The structured case assessment. This is the schema the verifier validates and
    the scorer grades against the hidden manifest."""

    case_id: str
    classification: str

    root_cause: RootCause
    facts: list[Fact] = Field(min_length=1)
    hypotheses: list[str] = Field(default_factory=list)

    recommended_next_action: NextAction
    escalation_required: bool = False
    uncertainties: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=20, max_length=2000)

    @field_validator("facts")
    @classmethod
    def _distinct_sources(cls, v: list[Fact]) -> list[Fact]:
        # A "multi-source" conclusion drawn from one tool call is a common failure:
        # the model finds one record and pads the fact list from it. Cross-service
        # corroboration is the actual skill being tested.
        if len(v) > 1 and len({f.source.split("/")[2] for f in v}) < 2:
            raise ValueError(
                "facts must draw on at least two distinct services when more than one "
                "fact is asserted — single-source corroboration is not corroboration."
            )
        return v
