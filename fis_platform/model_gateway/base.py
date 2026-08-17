"""The model gateway contract.

Canonical Architecture: "Nothing in the business logic should care where the model
physically lives." Everything above this layer speaks `GenerationRequest` and gets a
`GenerationResponse`; whether that was answered by llama.cpp on the RTX 5080, a
Claude subscription CLI, or a hosted API is a registry decision.

That indirection is not tidiness — it is what makes E2/E4/E5 a *controlled*
comparison. If each arm had its own call path, differences in results would be
confounded with differences in plumbing.
"""

from __future__ import annotations

import abc
from typing import Any, Literal

from pydantic import Field

from schemas.common import (
    Base,
    CostRecord,
    DataPolicy,
    LatencyRecord,
    ModelTier,
    Provider,
    TokenUsage,
)
from schemas.model_manifest import ModelManifest
from schemas.routing import RoutingRecord


class Message(Base):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: str | None = None
    name: str | None = None


class GenerationRequest(Base):
    """One generation. Identical shape for every tier."""

    model_ref: str
    messages: list[Message] = Field(min_length=1)
    system: str | None = None

    # Both tiers can enforce this: llama.cpp via --json-schema (GBNF), the Claude
    # CLI via --json-schema. Holding both to the same contract is what makes
    # verifier pass rate comparable instead of an artefact of one side being free-form.
    json_schema: dict[str, Any] | None = None

    tools: list[dict[str, Any]] | None = None
    max_tokens: int = 4096
    effort: str | None = None
    stop: list[str] | None = None

    data_policy: DataPolicy = DataPolicy.CLOUD_OK
    trace_id: str | None = None
    purpose: str | None = Field(
        default=None, description="Free-text tag for telemetry, e.g. 'investigate' or 'route'."
    )


class GenerationResponse(Base):
    text: str
    structured: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)

    model_id: str
    canonical_model: str | None = None
    provider: Provider
    tier: ModelTier

    usage: TokenUsage = Field(default_factory=TokenUsage)
    cost: CostRecord = Field(default_factory=CostRecord)
    latency: LatencyRecord

    stop_reason: str | None = None
    runtime_fingerprint: str | None = Field(
        default=None, description="Backend build id as the backend reports it (llama.cpp system_fingerprint).")
    reasoning_chars: int | None = Field(
        default=None,
        description="Length of the backend's separately-returned reasoning text (llama.cpp "
                    "`reasoning_content`), when it exposes one. Telemetry: says how much of "
                    "the generation budget went to thinking rather than to the answer.")
    is_error: bool = False
    error: str | None = None

    # Set only by adapters that sit behind a routing gateway, from what the gateway
    # actually reported. The direct path leaves it None.
    routing: RoutingRecord | None = None

    raw: dict[str, Any] | None = Field(
        default=None, description="Provider-native response, for diagnosis and replay."
    )


class PolicyViolation(RuntimeError):
    """Raised when a request would send data somewhere its policy forbids.

    FIS is entirely synthetic so this should never fire — it exists because the
    check must be in the code path from day one, not retrofitted once the platform
    is pointed at something real."""


class ModelAdapter(abc.ABC):
    """One transport. Adapters do not make routing decisions — they execute."""

    def __init__(self, manifest: ModelManifest) -> None:
        self.manifest = manifest

    @abc.abstractmethod
    async def generate(self, req: GenerationRequest) -> GenerationResponse: ...

    @abc.abstractmethod
    async def health(self) -> bool: ...

    def _check_policy(self, req: GenerationRequest) -> None:
        leaves_machine = self.manifest.provider not in (Provider.LOCAL_LLAMACPP,)
        if req.data_policy is DataPolicy.LOCAL_ONLY and leaves_machine:
            raise PolicyViolation(
                f"request is LOCAL_ONLY but model '{self.manifest.ref}' "
                f"({self.manifest.provider}) sends data off-device"
            )

    def _price(self, usage: TokenUsage) -> CostRecord:
        """Reference cost at published list prices — see CostRecord for why this
        is not the amount billed."""
        if self.manifest.price is None:
            return CostRecord()
        return CostRecord(
            reference_usd=self.manifest.price.cost_usd(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cache_creation=usage.cache_creation_input_tokens,
                cache_read=usage.cache_read_input_tokens,
            ),
            price_basis=self.manifest.price.basis,
        )
