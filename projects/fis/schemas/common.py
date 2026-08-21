"""Shared vocabulary for the platform.

Everything here is deliberately domain-neutral. The FIS fintech specifics live in
`investigator.py` and `scenario.py`; these types are the reusable platform asset the
guide describes — the part that transfers to a real client workflow unchanged.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Timezone-aware UTC. Naive datetimes cause silent ordering bugs once
    trajectories are compared across runs."""
    return datetime.now(timezone.utc)


def new_trace_id() -> UUID:
    return uuid4()


class Base(BaseModel):
    """Strict by default.

    `extra="forbid"` is the important choice: a typo in a hand-written manifest
    should fail loudly at load time, not silently produce a field nobody reads.
    """

    model_config = ConfigDict(extra="forbid", frozen=False, validate_assignment=True)


class FrozenBase(Base):
    """For records that must never mutate after creation — trajectory entries,
    eval results, scenario manifests."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_assignment=True)


# --------------------------------------------------------------------------------------
# Risk and permission
# --------------------------------------------------------------------------------------


class RiskClass(StrEnum):
    """How much damage a task could do if the model is wrong.

    The first FIS project is READ_ONLY throughout; the other members exist so the
    authorization layer has somewhere to grow without a schema migration.
    """

    READ_ONLY = "read_only"
    SUGGEST_ONLY = "suggest_only"      # may propose an action code, never executes
    REVERSIBLE_WRITE = "reversible_write"
    IRREVERSIBLE_WRITE = "irreversible_write"


class DataPolicy(StrEnum):
    """Where a payload is allowed to be processed.

    FIS is entirely synthetic, so everything is CLOUD_OK — but the field is carried
    on every request from day one, because retrofitting a policy field onto an
    existing trajectory store is exactly the migration nobody wants to do later.
    """

    LOCAL_ONLY = "local_only"
    CLOUD_REDACTED = "cloud_redacted"
    CLOUD_OK = "cloud_ok"


# --------------------------------------------------------------------------------------
# Model placement
# --------------------------------------------------------------------------------------


class ModelTier(StrEnum):
    """The three logical tiers from the Canonical Architecture. Not model names —
    a tier is a role, and which model fills it is a config decision."""

    ROUTER = "router"                  # tiny classifier, ~1-4B
    SPECIALIST = "specialist"          # main local worker, ~4-14B
    FRONTIER = "frontier"              # hosted escalation / planner / teacher


class Provider(StrEnum):
    LOCAL_LLAMACPP = "local_llamacpp"
    CLAUDE_CLI = "claude_cli"          # subscription auth via `claude -p`
    CODEX_CLI = "codex_cli"            # subscription auth via `codex exec`
    ANTHROPIC_API = "anthropic_api"    # kept so an API key is a config change, not a rewrite
    OPENAI_API = "openai_api"
    SWITCHYARD = "switchyard"          # NeMo Switchyard routing gateway (OpenAI-compatible)


# --------------------------------------------------------------------------------------
# Cost accounting
# --------------------------------------------------------------------------------------


class TokenUsage(Base):
    """Token counts, provider-neutral.

    Cache fields matter more than they look: the subscription CLI reports a large
    `cache_creation_input_tokens` for its own harness preamble, and conflating that
    with real prompt tokens would wreck the cost-per-successful-case metric.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    thinking_tokens: int = 0

    @property
    def total_input(self) -> int:
        return self.input_tokens + self.cache_creation_input_tokens + self.cache_read_input_tokens


class CostRecord(Base):
    """Two figures, deliberately.

    On a subscription plan the marginal cost of a frontier call is ~zero, so using
    amounts actually billed would make the cloud tier look free and render the
    intelligence-density KPI meaningless. `reference_usd` recomputes what the same
    tokens would have cost at published API list prices; that is what the KPI uses.
    `reported_usd` is whatever the provider claimed, kept for audit.
    """

    reported_usd: float | None = None
    reference_usd: float | None = None
    price_basis: str | None = Field(
        default=None,
        description="Identifier of the price table used for reference_usd, e.g. 'list-2026-08'.",
    )


class LatencyRecord(Base):
    """Wall-clock and in-API time are tracked separately on purpose.

    A subscription-CLI call pays ~2s of process startup that a local HTTP endpoint
    does not. Comparing raw wall-clock across tiers would make the frontier model
    look slower than it is, so both numbers are recorded and reports show both.
    """

    wall_ms: int
    api_ms: int | None = None
    ttft_ms: int | None = None

    @property
    def harness_overhead_ms(self) -> int | None:
        if self.api_ms is None:
            return None
        return max(0, self.wall_ms - self.api_ms)


Confidence = Annotated[float, Field(ge=0.0, le=1.0)]
