"""The gateway: resolve a logical model_ref to a transport, execute, record.

This is the only place in the codebase that knows a provider exists.
"""

from __future__ import annotations

import os

from schemas.common import ModelTier, Provider
from schemas.model_manifest import CliInvocation, ModelManifest, ModelRegistry, PriceTable

from .base import GenerationRequest, GenerationResponse, ModelAdapter
from .claude_cli import ClaudeCliAdapter
from .local import LocalLlamaCppAdapter

_ADAPTERS: dict[Provider, type[ModelAdapter]] = {
    Provider.LOCAL_LLAMACPP: LocalLlamaCppAdapter,
    Provider.CLAUDE_CLI: ClaudeCliAdapter,
}


class ModelGateway:
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry
        self._cache: dict[str, ModelAdapter] = {}

    def adapter(self, ref: str) -> ModelAdapter:
        if ref not in self._cache:
            manifest = self.registry.resolve(ref)
            cls = _ADAPTERS.get(manifest.provider)
            if cls is None:
                raise NotImplementedError(
                    f"no adapter registered for provider {manifest.provider!r} "
                    f"(model '{ref}'). Registered: {sorted(p.value for p in _ADAPTERS)}"
                )
            self._cache[ref] = cls(manifest)
        return self._cache[ref]

    async def generate(self, req: GenerationRequest) -> GenerationResponse:
        return await self.adapter(req.model_ref).generate(req)

    async def health(self) -> dict[str, bool]:
        return {ref: await self.adapter(ref).health() for ref in self.registry.models}


# --------------------------------------------------------------------------------------
# Default registry
# --------------------------------------------------------------------------------------

# Published list prices per MTok. Used ONLY to compute reference cost for comparing
# experiment arms — on a subscription plan none of this is actually billed.
_CLAUDE_OPUS_5 = PriceTable(
    basis="list-2026-08", input_per_mtok=5.00, output_per_mtok=25.00,
    cache_write_per_mtok=6.25, cache_read_per_mtok=0.50,
)
_CLAUDE_SONNET_5 = PriceTable(
    basis="list-2026-08", input_per_mtok=3.00, output_per_mtok=15.00,
    cache_write_per_mtok=3.75, cache_read_per_mtok=0.30,
)

# Flags validated by measurement — see claude_cli.py for the 33,633 -> 685 token story.
_CLAUDE_BASE_ARGS = [
    "--safe-mode",              # strips CLAUDE.md/skills/plugins/hooks/MCP, keeps OAuth
    "--tools", "",              # no agentic tools: same evidence contract as the local arm
    "--disable-slash-commands",
    "--strict-mcp-config",
    "--no-session-persistence",
    "--output-format", "json",
]


def default_registry() -> ModelRegistry:
    local_url = os.environ.get("FIS_LOCAL_MODEL_BASE_URL", "http://127.0.0.1:8082/v1")

    return ModelRegistry(models={
        "local-specialist": ModelManifest(
            ref="local-specialist",
            tier=ModelTier.SPECIALIST,
            provider=Provider.LOCAL_LLAMACPP,
            model_id="fis-local-specialist",
            canonical_model="qwen3-8b",
            quantization="Q4_K_M",
            context_window=16_384,
            max_output_tokens=4096,
            supports_tool_calling=True,
            supports_structured_output=True,   # GBNF-constrained decoding
            supports_seed=True,                # the reproducible baseline arm
            base_url=local_url,
            price=PriceTable(basis="local-marginal-zero", input_per_mtok=0.0,
                             output_per_mtok=0.0),
            notes="Primary local worker. Greedy, --parallel 1, for eval determinism.",
        ),

        "claude-frontier": ModelManifest(
            ref="claude-frontier",
            tier=ModelTier.FRONTIER,
            provider=Provider.CLAUDE_CLI,
            model_id="opus",
            canonical_model="claude-opus-5",
            context_window=1_000_000,
            max_output_tokens=64_000,
            supports_tool_calling=False,  # deliberately: --tools "" for a fair E4
            supports_structured_output=True,
            supports_seed=False,          # subscription CLI exposes no sampling controls
            price=_CLAUDE_OPUS_5,
            cli=CliInvocation(
                binary=os.path.expanduser("~/.local/bin/claude"),
                base_args=_CLAUDE_BASE_ARGS,
                auth_env_var="CLAUDE_CODE_OAUTH_TOKEN",
                startup_overhead_ms=2200,
            ),
            notes="Capability ceiling for E4. Not bit-reproducible — see supports_seed.",
        ),

        "claude-judge": ModelManifest(
            ref="claude-judge",
            tier=ModelTier.FRONTIER,
            provider=Provider.CLAUDE_CLI,
            model_id="sonnet",
            canonical_model="claude-sonnet-5",
            context_window=1_000_000,
            max_output_tokens=64_000,
            supports_structured_output=True,
            supports_seed=False,
            price=_CLAUDE_SONNET_5,
            cli=CliInvocation(
                binary=os.path.expanduser("~/.local/bin/claude"),
                base_args=_CLAUDE_BASE_ARGS,
                auth_env_var="CLAUDE_CODE_OAUTH_TOKEN",
                startup_overhead_ms=2200,
            ),
            notes=(
                "Cheaper frontier tier for bulk work. Per the evidence hierarchy, a "
                "model judge ranks BELOW deterministic checks — used only where no "
                "objective test exists."
            ),
        ),
    })
