"""R6 runtime compatibility probe (contract § 8) — does a served candidate speak the FIS
execution contract? One synthetic request (not a corpus case) through the SAME adapter path
the eval runner uses: `LocalLlamaCppAdapter.build_body` with the real `InvestigationResult`
json_schema (strict, gbnf-safe), greedy, seed 42. Reports the facts the eligibility rule
reads: `/props` build/model, `timings` present, `system_fingerprint` present,
`reasoning_content` present, `finish_reason`, and whether the content parses and validates as
`InvestigationResult`. Nothing is persisted; nothing touches the corpus or the DB.

    r6_runtime_compat.py --ref bonsai-27b [--max-tokens 2048] [--json-out F]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.model_gateway import GenerationRequest, Message, ModelGateway, default_registry  # noqa: E402
from schemas.investigator import InvestigationResult  # noqa: E402

SYSTEM = ("You are a fintech operations investigator. Decide the root cause from the evidence "
          "and answer ONLY with the JSON object the schema requires.")
USER = ("Case: a card authorization for 42.10 EUR was approved, then the settlement file posted "
        "4210.00 EUR for the same authorization id auth_7f3a; the ledger entry le_7f3a shows "
        "4210.00. Provider event evt_7f3a carries amount_minor=4210 with currency_exponent=2. "
        "Identify the root cause, cite the evidence ids you relied on, and propose the next action.")


async def probe(ref: str, max_tokens: int) -> dict:
    gw = ModelGateway(default_registry())
    manifest = gw.registry.resolve(ref)
    root = (manifest.base_url or "").rstrip("/").removesuffix("/v1")
    with urllib.request.urlopen(f"{root}/props", timeout=5) as r:
        props = json.load(r)
    req = GenerationRequest(model_ref=ref, system=SYSTEM, messages=[Message(role="user", content=USER)],
                            max_tokens=max_tokens, json_schema=InvestigationResult.model_json_schema())
    resp = await gw.generate(req)
    raw = resp.raw or {}
    msg = ((raw.get("choices") or [{}])[0].get("message") or {})
    parsed = validated = False
    parse_error = None
    try:
        obj = json.loads(resp.text or "")
        parsed = True
        InvestigationResult.model_validate(obj)
        validated = True
    except Exception as exc:  # noqa: BLE001 — the point is to report it
        parse_error = f"{type(exc).__name__}: {str(exc)[:200]}"
    return {
        "ref": ref, "base_url": manifest.base_url,
        "props": {k: props.get(k) for k in ("build_info", "model_path", "model_alias", "model_ftype")},
        "n_ctx": (props.get("default_generation_settings") or {}).get("n_ctx"),
        "is_error": resp.is_error, "error": resp.error,
        "finish_reason": resp.stop_reason,
        "timings_present": bool(raw.get("timings")),
        "system_fingerprint": raw.get("system_fingerprint"),
        "reasoning_content_present": bool(msg.get("reasoning_content")),
        "reasoning_chars": len(msg.get("reasoning_content") or ""),
        "content_chars": len(resp.text or ""),
        "usage": {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens},
        "wall_ms": resp.latency.wall_ms, "api_ms": resp.latency.api_ms,
        "content_parses": parsed, "content_validates_as_InvestigationResult": validated,
        "parse_error": parse_error,
        "content_head": (resp.text or "")[:300],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ref", required=True)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--json-out")
    args = ap.parse_args()
    out = asyncio.run(probe(args.ref, args.max_tokens))
    text = json.dumps(out, indent=2, default=str)
    print(text)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n")


if __name__ == "__main__":
    main()
