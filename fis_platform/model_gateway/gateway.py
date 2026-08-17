"""The gateway: resolve a logical model_ref to a transport, execute, record.

This is the only place in the codebase that knows a provider exists.
"""

from __future__ import annotations

import os

from schemas.common import ModelTier, Provider
from schemas.model_manifest import CliInvocation, ModelManifest, ModelRegistry, PriceTable
from schemas.routing import RouteMode, RoutingProfile

from .base import GenerationRequest, GenerationResponse, ModelAdapter
from .claude_cli import ClaudeCliAdapter
from .local import LocalLlamaCppAdapter
from .switchyard import SwitchyardAdapter, installed_switchyard_version

_ADAPTERS: dict[Provider, type[ModelAdapter]] = {
    Provider.LOCAL_LLAMACPP: LocalLlamaCppAdapter,
    Provider.CLAUDE_CLI: ClaudeCliAdapter,
    Provider.SWITCHYARD: SwitchyardAdapter,
}

# The Switchyard route id for the R1 passthrough. Equal to the local model_id on
# purpose: the request body the orchestrator sends is then byte-identical on both
# paths, and Switchyard's one rewrite (model -> target model) is a no-op.
SWITCHYARD_PASSTHROUGH_ROUTE = "fis-local-specialist"
SWITCHYARD_ROUTES_YAML = "infra/switchyard/routes.yaml"


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
    nemotron_url = os.environ.get("FIS_NEMOTRON_BASE_URL", "http://127.0.0.1:8083/v1")
    switchyard_url = os.environ.get("FIS_SWITCHYARD_BASE_URL", "http://127.0.0.1:4000/v1")

    local_price = PriceTable(basis="local-marginal-zero", input_per_mtok=0.0,
                             output_per_mtok=0.0)

    return ModelRegistry(models={
        "local-specialist": ModelManifest(
            ref="local-specialist",
            tier=ModelTier.SPECIALIST,
            provider=Provider.LOCAL_LLAMACPP,
            model_id="fis-local-specialist",
            canonical_model="qwen3-8b",
            quantization="Q4_K_M",
            context_window=16_384,
            # Ceiling, not the budget: a run picks its budget with `--max-tokens`
            # (default 4096, every recorded run before R3b). 8192 is the largest
            # value the served 16k context holds beside the longest FIS prompt
            # (~3.5k tokens) with headroom — the R3b level.
            max_output_tokens=8192,
            supports_tool_calling=True,
            supports_structured_output=True,   # GBNF-constrained decoding
            supports_seed=True,                # the reproducible baseline arm
            base_url=local_url,
            price=local_price,
            notes="Primary local worker. Greedy, --parallel 1, for eval determinism.",
        ),

        # R3: candidate weak arm. Same adapter, same decoding (greedy, seed 42), same
        # grammar path as local-specialist — the arms differ by model_ref only. Served
        # by infra/serve-nemotron.sh on 8083 alongside Qwen on 8082 (design A:
        # simultaneous endpoints, so the incumbent's session is never restarted).
        "nemotron-lightning": ModelManifest(
            ref="nemotron-lightning",
            tier=ModelTier.SPECIALIST,
            provider=Provider.LOCAL_LLAMACPP,
            model_id="fis-nemotron-lightning",
            canonical_model="nemotron-3.5-lightning-30b-a3b",
            quantization="IQ4_XS",
            context_window=16_384,
            max_output_tokens=8192,            # same ceiling as local-specialist (R3b)
            supports_tool_calling=True,
            supports_structured_output=True,
            supports_seed=True,
            base_url=nemotron_url,
            price=local_price,
            notes="R3 candidate. Hybrid Mamba-2/attention/MoE, 30B total / ~3B active, "
                  "128 experts; experts partly in system RAM (--fit on).",
        ),

        # R1: the same local model, reached through NeMo Switchyard in passthrough.
        # Every field that describes the MODEL is identical to local-specialist;
        # only the transport differs. This is the arm that has to prove the gateway
        # is semantically invisible before any routing decision is allowed in.
        "local-specialist-switchyard": ModelManifest(
            ref="local-specialist-switchyard",
            tier=ModelTier.SPECIALIST,
            provider=Provider.SWITCHYARD,
            model_id=SWITCHYARD_PASSTHROUGH_ROUTE,
            canonical_model="qwen3-8b",
            quantization="Q4_K_M",
            context_window=16_384,
            max_output_tokens=8192,            # identical to local-specialist by construction
            supports_tool_calling=True,
            supports_structured_output=True,
            supports_seed=True,
            base_url=switchyard_url,
            price=local_price,
            routing=RoutingProfile(
                gateway="switchyard",
                gateway_version=installed_switchyard_version(),
                route_profile=SWITCHYARD_PASSTHROUGH_ROUTE,
                route_mode=RouteMode.PASSTHROUGH,
                backends=["llamacpp-8082"],
                all_backends_local=True,
                config_path=SWITCHYARD_ROUTES_YAML,
            ),
            notes="R1 passthrough. Same model, same decoding, one extra hop on 4000.",
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
