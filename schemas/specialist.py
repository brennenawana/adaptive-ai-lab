"""Specialist and Task schemas.

The architecture's central definitional claim: a specialist is NOT a fine-tuned
model. It is base model + adapter + system contract + permitted tools + retrieval
policy + context rules + output schema + verifier + rubric + eval suite.

Encoding that as a type is what makes the claim enforceable — you cannot register a
specialist without declaring its eval suite and its verifiers.
"""

from __future__ import annotations

from pydantic import Field, field_validator

from .common import Base, DataPolicy, ModelTier, RiskClass


class ContextPolicy(Base):
    """How the Context Builder assembles evidence for this specialist."""

    max_documents: int = Field(default=12, ge=0, le=200)
    max_tool_calls: int = Field(default=15, ge=1, le=100)
    prefer_authoritative_sources: bool = True
    include_history: bool = False
    max_context_tokens: int = Field(default=32_000, ge=1024)


class RoutingPolicy(Base):
    """When this specialist is chosen, and when it must hand off.

    `escalate_below_confidence` is the E5 lever: raising it sends more work to the
    frontier tier and should raise all-pass rate while raising cloud dependence.
    The whole point of the experiment is finding where that curve is worth it.
    """

    task_types: list[str] = Field(min_length=1)
    escalate_below_confidence: float = Field(default=0.55, ge=0.0, le=1.0)
    escalate_on_failure_classes: list[str] = Field(default_factory=list)
    max_local_attempts: int = Field(default=1, ge=1, le=5)


class ModelBinding(Base):
    tier: ModelTier
    model_ref: str = Field(description="Key into the model registry, not a raw model id.")
    adapter: str | None = None
    effort: str | None = None


class Specialist(Base):
    """A registered, versioned specialist."""

    id: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    description: str

    primary: ModelBinding
    escalation: ModelBinding | None = None

    system_contract_ref: str = Field(description="Path/key of the versioned system prompt.")
    prompt_version: str

    tools: list[str] = Field(min_length=1, description="Qualified tool names the broker will allow.")
    permissions: dict[str, bool] = Field(default_factory=lambda: {"read_only": True})
    risk_class: RiskClass = RiskClass.READ_ONLY
    data_policy: DataPolicy = DataPolicy.CLOUD_OK

    context_policy: ContextPolicy = Field(default_factory=ContextPolicy)
    routing: RoutingPolicy

    output_schema_ref: str
    verifiers: list[str] = Field(min_length=1)
    rubric_ref: str | None = None

    # Non-optional on purpose. "Every specialist must have an eval suite before we
    # train it" is only enforceable if you cannot register one without naming it.
    eval_suite: str = Field(min_length=1)

    @field_validator("verifiers")
    @classmethod
    def _must_verify_schema(cls, v: list[str]) -> list[str]:
        if "schema_validation" not in v:
            raise ValueError(
                "every specialist needs 'schema_validation' — machine-actionable output "
                "is the floor, and an unvalidated output cannot be scored."
            )
        return v

    @property
    def qualified_id(self) -> str:
        return f"{self.id}@{self.version}"


class TaskState(Base):
    """Working memory for one in-flight task.

    The architecture is explicit that this should be "explicit versioned artifacts,
    not buried inside a gigantic chat context" — so the orchestrator's state machine
    reads and writes this object, and it is persisted per step.
    """

    trace_id: str
    task_type: str
    user: str
    permissions: dict[str, bool] = Field(default_factory=dict)

    stage: str = Field(
        default="classify",
        pattern=r"^(classify|authorize|route|retrieve|generate|verify|execute|capture|done|failed)$",
    )

    route: str | None = None
    evidence: list[dict] = Field(default_factory=list)
    tool_results: list[dict] = Field(default_factory=list)
    candidate_output: dict | None = None
    verification: dict | None = None
    approval: str | None = None
    outcome: str | None = None

    open_questions: list[str] = Field(default_factory=list)
    completed_steps: list[str] = Field(default_factory=list)
