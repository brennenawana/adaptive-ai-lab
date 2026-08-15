"""Scenario manifest — the hidden answer key, and the eval schema.

This module is the reason `ground_truth` is a separate Postgres schema with no
tool-broker route to it. The generator writes authoritative records across the
service schemas AND a manifest here; the model can query the former and never the
latter. Everything the eval knows that the model does not lives in this file.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field, computed_field

from .common import Base, FrozenBase, utc_now
from .investigator import NextAction, RootCauseLabel


class SeedSplit(StrEnum):
    """Frozen splits. The guide is blunt about this: "Do not tune against the test
    set." Splitting by seed rather than by row means a scenario family cannot leak
    across the boundary through a near-duplicate variant."""

    TRAIN = "train"
    DEV = "dev"
    TEST = "test"


class ScenarioManifest(FrozenBase):
    """Ground truth for one generated incident. Frozen — a manifest that can be
    edited after scoring is not ground truth."""

    scenario_id: str = Field(pattern=r"^S\d{2}-\d{5}$")
    seed: int
    split: SeedSplit
    category: str
    root_cause: RootCauseLabel

    # Evidence IDs the investigator must surface. Drives required-evidence recall.
    required_evidence: list[str] = Field(min_length=1)

    # More than one action can be defensible; scoring accepts any member.
    acceptable_next_actions: list[NextAction] = Field(min_length=1)

    # Conclusions that are wrong and harmful — e.g. asserting confirmed customer
    # fraud from a mapping bug. Any of these appearing is an automatic fail,
    # regardless of whether the root-cause label happened to be right.
    forbidden_claims: list[str] = Field(default_factory=list)

    # Deliberate noise. Without distractors a model can score well by summarising
    # everything it sees; these make evidence *selection* the thing being measured.
    distractor_event_ids: list[str] = Field(default_factory=list)

    case_id: str
    subject_ids: dict[str, str] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=utc_now)


class DimensionScore(Base):
    name: str
    value: float
    passed: bool
    detail: str | None = None


class CaseScore(Base):
    """Per-case result. `all_pass` is intentionally strict and conjunctive —
    real operational tasks fail if any one critical dimension is wrong."""

    scenario_id: str
    trace_id: str
    experiment_arm: str

    root_cause_correct: bool
    required_evidence_recall: float = Field(ge=0.0, le=1.0)
    unsupported_claims: int = Field(ge=0)
    next_action_acceptable: bool
    verifier_passed: bool
    forbidden_claim_made: bool = False

    tool_calls_total: int = 0
    tool_calls_useful: int = 0
    escalated_to_frontier: bool = False

    wall_ms: int = 0
    api_ms: int | None = None
    reference_cost_usd: float = 0.0

    evidence_recall_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    dimensions: list[DimensionScore] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_pass(self) -> bool:
        return (
            self.root_cause_correct
            and self.required_evidence_recall >= self.evidence_recall_threshold
            and self.unsupported_claims == 0
            and self.next_action_acceptable
            and self.verifier_passed
            and not self.forbidden_claim_made
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tool_efficiency(self) -> float | None:
        if self.tool_calls_total == 0:
            return None
        return self.tool_calls_useful / self.tool_calls_total


class EvalRun(Base):
    """An experiment arm executed over a frozen scenario set.

    Checkpointed by design: subscription rate limits will interrupt a 200-case run,
    and a run that cannot resume turns a rate-limit pause into a lost afternoon.
    """

    run_id: str
    suite: str
    suite_version: str
    experiment_arm: str
    split: SeedSplit = SeedSplit.TEST

    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None

    config_digest: str = Field(description="Hash of model + prompt + tool versions under test.")
    scores: list[CaseScore] = Field(default_factory=list)

    completed_scenario_ids: list[str] = Field(
        default_factory=list, description="Resume marker — skip these on restart."
    )
    interrupted_reason: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def strict_all_pass_rate(self) -> float | None:
        if not self.scores:
            return None
        return sum(1 for s in self.scores if s.all_pass) / len(self.scores)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def root_cause_accuracy(self) -> float | None:
        if not self.scores:
            return None
        return sum(1 for s in self.scores if s.root_cause_correct) / len(self.scores)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cloud_escalation_rate(self) -> float | None:
        if not self.scores:
            return None
        return sum(1 for s in self.scores if s.escalated_to_frontier) / len(self.scores)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cost_per_successful_case(self) -> float | None:
        """The intelligence-density KPI. Denominator is *successful* cases, so a
        cheap arm that fails often is correctly penalised rather than rewarded."""
        wins = [s for s in self.scores if s.all_pass]
        if not wins:
            return None
        return sum(s.reference_cost_usd for s in self.scores) / len(wins)

    def p95_latency_ms(self) -> int | None:
        if not self.scores:
            return None
        ordered = sorted(s.wall_ms for s in self.scores)
        return ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))]
