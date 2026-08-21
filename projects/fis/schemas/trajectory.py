"""Trajectory — the primary data object.

Canonical Architecture: "Every meaningful job gets one trace_id." The exit condition
for Phase 1 is that for almost every request we can reconstruct who asked, what was
requested, what context was supplied, what tools ran, what model version ran, what it
returned, what the employee changed, whether it succeeded, and what it cost.

Each field below exists to answer exactly one of those questions. Large or sensitive
payloads are referenced by object-store key rather than inlined, per the guide.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from .common import (
    Base,
    Confidence,
    CostRecord,
    DataPolicy,
    FrozenBase,
    LatencyRecord,
    ModelTier,
    Provider,
    RiskClass,
    TokenUsage,
    new_trace_id,
    utc_now,
)
from .routing import RoutingRecord
from .tool import ToolCall


class FailureClass(StrEnum):
    """The Discovery Controller's competing explanations.

    The whole point of the taxonomy is to stop the system training itself to
    compensate for broken infrastructure — so system-side causes are enumerated
    first and in more detail than model-side ones.
    """

    ROUTING_FAILURE = "routing_failure"
    RETRIEVAL_FAILURE = "retrieval_failure"
    MISSING_KNOWLEDGE = "missing_knowledge"
    STALE_DATA = "stale_data"
    TOOL_FAILURE = "tool_failure"
    TOOL_SCHEMA_FAILURE = "tool_schema_failure"
    TOOL_SELECTION_FAILURE = "tool_selection_failure"
    PERMISSION_FAILURE = "permission_failure"
    PROMPT_FAILURE = "prompt_failure"
    SCHEMA_FAILURE = "schema_failure"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    MODEL_REASONING_FAILURE = "model_reasoning_failure"
    MODEL_CAPABILITY_FAILURE = "model_capability_failure"
    BAD_RUBRIC = "bad_rubric"
    NOVEL_TASK = "novel_task"
    UNKNOWN = "unknown"


class RouterDecision(Base):
    selected_specialist: str
    confidence: Confidence
    escalated: bool = False
    escalation_reason: str | None = None
    features: dict[str, float] = Field(default_factory=dict)


class ModelInvocation(Base):
    """Which model actually ran. `tier` and `provider` are separate because the
    same tier can be filled by different providers across experiments — that
    substitution is the thing E5 measures."""

    tier: ModelTier
    provider: Provider
    model_id: str
    canonical_model: str | None = None
    quantization: str | None = None
    adapter_version: str | None = None
    prompt_version: str
    effort: str | None = None

    usage: TokenUsage = Field(default_factory=TokenUsage)
    cost: CostRecord = Field(default_factory=CostRecord)
    latency: LatencyRecord
    stop_reason: str | None = Field(
        default=None,
        description="Provider finish reason (e.g. 'stop', 'length'). Two arms that "
        "truncate on different cases are not equivalent even if their scores agree.",
    )

    # Present only when a routing gateway sat between the orchestrator and the model.
    # None means the direct path — the control every routed arm is compared with.
    routing: RoutingRecord | None = None

    # The backend's own build fingerprint (llama.cpp `system_fingerprint`, e.g.
    # `b1-9b05354`). Case-level local results were found to reproduce only within one
    # server session; the build is the first thing to compare when two runs disagree.
    runtime_fingerprint: str | None = None

    # The generation budget this invocation was made with. R3 found a whole class of
    # failures — `stop_reason == "length"` with an empty answer — that are the budget
    # meeting the model's reasoning length, not a wrong answer; two runs that differ
    # only here (R3b) must be distinguishable per invocation, not just per run.
    # None on records written before the field existed (all of them were 4096).
    max_tokens: int | None = None

    # Observation only, filled by adapters that expose the split (llama.cpp returns
    # `reasoning_content` beside `content` for thinking models). Lengths in characters
    # because the backend does not report reasoning tokens separately; the answer is
    # grammar-constrained JSON so `content_chars` tracks answer tokens closely enough
    # to say how much of the budget went to thinking. Never read by the model or the
    # router. None where the adapter cannot observe it.
    reasoning_chars: int | None = None
    content_chars: int | None = None

    # M0/WP-A (2026-08-20). The texts themselves, persisted per invocation because the
    # cap-hit population produces no parseable output and therefore no
    # learning.model_outputs row — a column there would miss exactly the cases that
    # need diagnosing. `reasoning_text` is kept whenever the adapter exposes it;
    # `content_text` only when the strict-grammar parse produced no object (a parsed
    # answer already lands in model_outputs). Never read by the model, the router, or
    # any routing feature (tests/test_routing_features_no_gold_leak.py governs that
    # surface). None on every record written before the fields existed.
    reasoning_text: str | None = None
    content_text: str | None = None

    # M0/WP-D (2026-08-20). The backend's own timing block (llama.cpp `timings`),
    # verbatim: prompt_n/prompt_ms/predicted_n/predicted_ms/predicted_per_second/….
    # The autopsy (§13) had to reconstruct all of these by hand; `ttft_ms` on
    # `latency` is derived from prompt_ms. None where the backend reports none.
    timings: dict[str, Any] | None = None


class RetrievalRef(FrozenBase):
    document_id: str
    version: str
    score: float
    used_in_output: bool | None = None


class VerificationResult(Base):
    """Deterministic checks only.

    Guide: the verifier "should reject missing citations, invalid IDs, impossible
    amounts, unsupported facts, unknown action codes, or schemas that do not
    validate. It should not attempt to judge every reasoning nuance."
    """

    passed: bool
    checks: dict[str, bool] = Field(default_factory=dict)
    violations: list[str] = Field(default_factory=list)
    schema_valid: bool = True


class HumanFeedback(Base):
    accepted: bool | None = None
    correction_id: str | None = None
    corrected_artifact_ref: str | None = None
    diff_ref: str | None = None
    reason: str | None = None
    reviewer: str | None = None
    reviewed_at: datetime | None = None


class Trajectory(Base):
    """One complete production attempt.

    Deliberately NOT frozen: outcome, human feedback and diagnosis are enriched
    after the run completes. The immutable parts are the individual tool calls and
    the model invocations.
    """

    trace_id: UUID = Field(default_factory=new_trace_id)
    created_at: datetime = Field(default_factory=utc_now)

    # --- what was asked -------------------------------------------------------
    workflow: str
    workflow_version: str
    task_type: str
    risk_class: RiskClass = RiskClass.READ_ONLY
    data_policy: DataPolicy = DataPolicy.CLOUD_OK

    user: str
    permissions_snapshot: dict[str, bool] = Field(default_factory=dict)

    # --- FIS linkage ----------------------------------------------------------
    case_id: str | None = None
    scenario_id: str | None = Field(
        default=None,
        description="Present for eval runs. The model never sees this; the scorer joins on it.",
    )
    experiment_arm: str | None = Field(
        default=None, description="E0..E8 — which configuration produced this trajectory."
    )

    # --- how it was handled ---------------------------------------------------
    router: RouterDecision | None = None
    model_invocations: list[ModelInvocation] = Field(default_factory=list)
    retrieval: list[RetrievalRef] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)

    # --- what came out --------------------------------------------------------
    output_ref: str | None = None
    output_digest: str | None = None
    verification: VerificationResult | None = None

    # --- what happened next ---------------------------------------------------
    human_feedback: HumanFeedback = Field(default_factory=HumanFeedback)
    business_outcome: str | None = None

    # --- diagnosis (learning plane writes this, not the runtime) --------------
    failure_class: FailureClass | None = None
    failure_confidence: Confidence | None = None
    failure_alternatives: list[FailureClass] = Field(default_factory=list)
    recommended_experiment: str | None = None
    training_recommended: bool = False

    error: str | None = None

    # Free-form context the runner knew and the model did not: local model-server
    # session (pid / start ticks / build), gateway version, run id. Enough to tell
    # whether two case-level local results are comparable (same server session,
    # same order) — no more. Never read by the model or the router.
    runtime_context: dict[str, str] = Field(default_factory=dict)

    # ---------------------------------------------------------------------------
    # Derived metrics. Computed rather than stored so they can never drift out of
    # sync with the underlying records.
    # ---------------------------------------------------------------------------

    @property
    def total_usage(self) -> TokenUsage:
        agg = TokenUsage()
        for inv in self.model_invocations:
            agg.input_tokens += inv.usage.input_tokens
            agg.output_tokens += inv.usage.output_tokens
            agg.cache_creation_input_tokens += inv.usage.cache_creation_input_tokens
            agg.cache_read_input_tokens += inv.usage.cache_read_input_tokens
            agg.thinking_tokens += inv.usage.thinking_tokens
        return agg

    @property
    def reference_cost_usd(self) -> float:
        """Sum of list-price-equivalent cost. This is the figure the
        cost-per-successful-case KPI uses — see CostRecord for why."""
        return sum(i.cost.reference_usd or 0.0 for i in self.model_invocations)

    @property
    def wall_ms(self) -> int:
        return sum(i.latency.wall_ms for i in self.model_invocations) + sum(
            c.latency_ms for c in self.tool_calls
        )

    @property
    def used_frontier(self) -> bool:
        """Drives the cloud-dependence metric — percent of cases needing cloud."""
        return any(i.tier is ModelTier.FRONTIER for i in self.model_invocations)

    @property
    def tool_efficiency(self) -> float | None:
        """Useful calls / total calls. None until scoring has set `was_useful`."""
        scored = [c for c in self.tool_calls if c.was_useful is not None]
        if not scored:
            return None
        return sum(1 for c in scored if c.was_useful) / len(scored)
