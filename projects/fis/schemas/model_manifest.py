"""Model manifest and registry.

The gateway resolves a logical `model_ref` to a concrete endpoint. Business logic
never names a provider — that indirection is what lets E5 swap the frontier tier
from a subscription CLI to an API key as a config change rather than a rewrite.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, model_validator

from .common import Base, ModelTier, Provider, utc_now
from .routing import RoutingProfile


class PriceTable(Base):
    """Published list prices, per million tokens.

    Used to compute `CostRecord.reference_usd`. This is a *reference* basis for
    comparing arms, not a billing record — on a subscription nothing here is charged.
    """

    basis: str = Field(description="e.g. 'list-2026-08'")
    input_per_mtok: float
    output_per_mtok: float
    cache_write_per_mtok: float | None = None
    cache_read_per_mtok: float | None = None

    def cost_usd(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_creation: int = 0,
        cache_read: int = 0,
    ) -> float:
        m = 1_000_000
        total = (input_tokens / m) * self.input_per_mtok
        total += (output_tokens / m) * self.output_per_mtok
        # Fall back to the input rate when a provider does not publish cache rates,
        # rather than silently pricing cached tokens at zero.
        total += (cache_creation / m) * (self.cache_write_per_mtok or self.input_per_mtok)
        total += (cache_read / m) * (self.cache_read_per_mtok or self.input_per_mtok)
        return round(total, 6)


class CliInvocation(Base):
    """How to drive a subscription CLI as a model backend.

    The defaults are not cosmetic. A bare `claude -p` loads the full Claude Code
    harness — measured at 33,633 input tokens and $0.337 for a trivial prompt —
    which would make E4 a measurement of the harness rather than of the model.
    With these flags the same call costs 685 tokens and $0.036.
    """

    binary: str
    base_args: list[str] = Field(default_factory=list)
    system_prompt_flag: str | None = None
    schema_flag: str | None = None
    model_flag: str | None = None
    json_output_args: list[str] = Field(default_factory=list)

    # Env var carrying subscription auth. Never the secret itself.
    auth_env_var: str | None = None

    startup_overhead_ms: int = Field(
        default=2200,
        description="Measured process-startup cost, subtracted when reporting model latency.",
    )


class ModelManifest(Base):
    """One registered, resolvable model."""

    ref: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    tier: ModelTier
    provider: Provider

    model_id: str
    canonical_model: str | None = None
    quantization: str | None = None
    context_window: int = Field(ge=1024)
    max_output_tokens: int = Field(ge=256)

    supports_tool_calling: bool = False
    supports_structured_output: bool = False
    supports_seed: bool = Field(
        default=False,
        description="False for subscription CLIs — runs are not bit-reproducible. "
        "Recorded so eval reports can say which arms are replayable.",
    )

    base_url: str | None = None
    cli: CliInvocation | None = None
    price: PriceTable | None = None

    # Set when this entry is served through a routing gateway rather than a model
    # endpoint. The gateway is a transport detail: an entry with a profile is still
    # resolved, priced and recorded like any other model.
    routing: RoutingProfile | None = None

    registered_at: datetime = Field(default_factory=utc_now)
    notes: str | None = None

    @model_validator(mode="after")
    def _needs_a_transport(self) -> "ModelManifest":
        if self.base_url is None and self.cli is None:
            raise ValueError(f"model '{self.ref}' declares neither base_url nor cli — unreachable")
        return self

    @model_validator(mode="after")
    def _routed_entries_name_their_gateway_provider(self) -> "ModelManifest":
        # A routing profile without the SWITCHYARD provider (or vice versa) would be
        # a manifest that lies about its transport, and the R1 equivalence claim
        # rests on knowing exactly which path a run took.
        routed = self.provider is Provider.SWITCHYARD
        if routed != (self.routing is not None):
            raise ValueError(
                f"model '{self.ref}': provider {self.provider.value!r} and routing "
                f"profile {'present' if self.routing else 'absent'} disagree"
            )
        return self

    @model_validator(mode="after")
    def _frontier_needs_price_basis(self) -> "ModelManifest":
        # Without a price table a frontier arm contributes 0.0 to reference cost,
        # which would silently make it look free in the intelligence-density KPI.
        if self.tier is ModelTier.FRONTIER and self.price is None:
            raise ValueError(
                f"frontier model '{self.ref}' needs a PriceTable: reference cost is how "
                "cloud and local arms are compared, and a missing table reads as free."
            )
        return self


class ModelRegistry(Base):
    models: dict[str, ModelManifest] = Field(default_factory=dict)

    def resolve(self, ref: str) -> ModelManifest:
        if ref not in self.models:
            raise KeyError(f"unknown model ref {ref!r}; registered: {sorted(self.models)}")
        return self.models[ref]

    def by_tier(self, tier: ModelTier) -> list[ModelManifest]:
        return [m for m in self.models.values() if m.tier is tier]
