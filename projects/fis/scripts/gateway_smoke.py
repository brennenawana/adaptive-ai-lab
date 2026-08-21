"""End-to-end gateway check: the same request, both tiers, one contract.

This is the experiment-matrix primitive. If this script works, E2 and E4 differ by
exactly one string — the model_ref — which is what makes the comparison controlled.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

from fis_platform.model_gateway import GenerationRequest, Message, ModelGateway, default_registry  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SCHEMA = {
    "type": "object",
    "properties": {
        "root_cause": {
            "type": "string",
            "enum": ["settlement_amount_mapping_error", "processor_decline", "kyc_hold"],
        },
        "confidence": {"type": "number"},
        "key_evidence": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["root_cause", "confidence", "key_evidence"],
    "additionalProperties": False,
}

SYSTEM = (
    "You are a fintech operations investigator. Given evidence, identify the root "
    "cause. Respond only via the provided schema."
)

EVIDENCE = (
    "Case case_001.\n"
    "processor.settlement set_912: amount=4210 USD, card_id=card_77\n"
    "ledger.entry le_884: amount=4120 USD, reference=set_912\n"
    "integration.event evt_111: mapping_version=3, raw_amount=4210\n"
    "identity.verification ver_22: status=approved\n"
    "What is the root cause?"
)


async def run(gw: ModelGateway, ref: str) -> None:
    req = GenerationRequest(
        model_ref=ref,
        system=SYSTEM,
        messages=[Message(role="user", content=EVIDENCE)],
        json_schema=SCHEMA,
        max_tokens=2048,
        purpose="gateway_smoke",
    )
    print(f"\n=== {ref} ===")
    healthy = await gw.adapter(ref).health()
    print(f"health        : {healthy}")
    if not healthy:
        print("SKIPPED (adapter unhealthy)")
        return

    resp = await gw.generate(req)
    if resp.is_error:
        print(f"ERROR         : {resp.error}")
        return

    print(f"structured    : {json.dumps(resp.structured)}")
    print(f"schema-valid  : {resp.structured is not None}")
    print(f"model         : {resp.model_id} ({resp.provider})")
    print(f"tokens in/out : {resp.usage.input_tokens}/{resp.usage.output_tokens}")
    print(f"cost ref/rep  : ${resp.cost.reference_usd} / {resp.cost.reported_usd}")
    print(f"latency wall  : {resp.latency.wall_ms} ms")
    print(f"latency api   : {resp.latency.api_ms} ms")
    print(f"harness over. : {resp.latency.harness_overhead_ms} ms")


async def main() -> None:
    gw = ModelGateway(default_registry())
    await run(gw, "local-specialist")
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        await run(gw, "claude-frontier")
    else:
        print("\n=== claude-frontier === SKIPPED: CLAUDE_CODE_OAUTH_TOKEN not loaded")


if __name__ == "__main__":
    asyncio.run(main())
