"""Tool schema — the contract between the AI and company systems.

Guide's constraint: "Tools should be narrow, typed, and read-only for the first
project. The AI should never receive direct SQL access to every service database."

The `forbidden_schemas` field enforces the answer-key boundary at the type level:
`ground_truth` is unreachable by construction, not by reviewer vigilance.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator

from .common import Base, FrozenBase, RiskClass


class ToolKind(StrEnum):
    READ = "read"          # pure query, no side effects
    SEARCH = "search"      # retrieval over knowledge memory
    ACTION = "action"      # emits an action code; never moves money in FIS


class ToolDefinition(Base):
    """A tool the broker is willing to expose. Versioned, because a tool's shape
    changing is a legitimate explanation for a regression and the trajectory has
    to be able to say which version ran."""

    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    version: int = Field(ge=1)
    kind: ToolKind
    description: str = Field(min_length=20)
    owning_service: str

    input_schema: dict[str, Any]
    output_schema: dict[str, Any]

    risk_class: RiskClass = RiskClass.READ_ONLY

    # Deterministic post-conditions the verifier runs on this tool's output.
    verifiers: list[str] = Field(default_factory=list)

    # Hard boundary. The eval answer key lives in `ground_truth`; a tool that could
    # read it would make every score meaningless.
    forbidden_schemas: list[str] = Field(default_factory=lambda: ["ground_truth"])

    @field_validator("forbidden_schemas")
    @classmethod
    def _ground_truth_always_forbidden(cls, v: list[str]) -> list[str]:
        if "ground_truth" not in v:
            raise ValueError(
                "ground_truth must remain forbidden: a tool that can read the "
                "scenario answer key invalidates every eval score."
            )
        return v

    @field_validator("description")
    @classmethod
    def _description_states_when_to_use(cls, v: str) -> str:
        # Tool descriptions are the single biggest lever on tool-selection accuracy.
        # A description that only says *what* the tool does, not *when* to reach for
        # it, measurably degrades routing — so require the trigger condition.
        lowered = v.lower()
        if not any(k in lowered for k in ("use when", "call when", "when the", "use this")):
            raise ValueError(
                "description must state WHEN to use the tool, not just what it does "
                "(e.g. 'Use when the case involves a settlement/ledger discrepancy')."
            )
        return v

    @property
    def qualified_name(self) -> str:
        return f"{self.name}@v{self.version}"


class ToolCall(FrozenBase):
    """One invocation, as recorded in a trajectory.

    Arguments are stored hashed by default. The guide's security boundary says to
    "log hashed/redacted arguments where full values are unnecessary" — the raw
    args go to object storage keyed by this hash when they're actually needed.
    """

    tool: str
    version: int
    args_hash: str
    args_ref: str | None = Field(
        default=None, description="Object-store key for the full arguments, if retained."
    )

    status: str = Field(pattern=r"^(success|error|timeout|denied)$")
    error_code: str | None = None

    result_ref: str | None = None
    result_digest: str | None = None

    latency_ms: int
    sequence: int = Field(ge=0, description="Ordinal within the trajectory.")

    # Set during scoring, not at call time: did this call contribute evidence that
    # the scenario manifest marks as required? Drives the tool-efficiency metric.
    was_useful: bool | None = None

    # Start-of-call dual-clock stamps (M-STAT; NEXT_STEP_M0.md §6-D "TOOLS spans").
    # Optional and additive on purpose: every trajectory persisted before this field
    # existed must still validate, so both default to None ("not recorded") rather
    # than being required. See fis_platform.telemetry.clocks.dual_clock — realtime
    # names WHEN the call started, monotonic is immune to the WSL2 realtime skew.
    ts_realtime: str | None = None
    ts_monotonic: float | None = None
