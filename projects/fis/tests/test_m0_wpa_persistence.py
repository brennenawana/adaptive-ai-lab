"""M0 WP-A — reasoning + raw-content persistence round-trip (NEXT_STEP_M0.md § 6-A).

The required test, verbatim from the doc: "a fake llama.cpp `length`-stop response
round-trips reasoning + truncated content to the store." The store boundary here is
the serialized Trajectory payload — `persist()` writes `model_dump_json()` into
`learning.trajectories.payload` byte-for-byte (evals/runner/run_eval.py persist()),
so what survives serialization is exactly what Postgres holds.

Also proven: the parse-SUCCESS path does NOT duplicate the answer text into the
trajectory (it already lands in learning.model_outputs), old records without the new
fields still validate (backward compatibility), and the request body remains free of
any reasoning key (the frozen genconfig digest depends on build_body being unchanged).
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.model_gateway.base import GenerationRequest, Message
from fis_platform.model_gateway.local import LocalLlamaCppAdapter
from schemas.common import LatencyRecord, ModelTier, Provider
from schemas.model_manifest import ModelManifest
from schemas.trajectory import ModelInvocation, Trajectory

REASONING = ("Consider the settlement path. The ledger shows entry led_000123 posted "
             "before the reversal. " * 40)
TRUNCATED_JSON = '{"case_id": "CASE-1", "root_cause": {"label": "reversal_r'


def _manifest() -> ModelManifest:
    return ModelManifest(
        ref="qwen38-27b", tier=ModelTier.SPECIALIST, provider=Provider.LOCAL_LLAMACPP,
        model_id="fis-qwen38-27b", canonical_model="qwen3.8-27b",
        context_window=16384, max_output_tokens=12288,
        supports_structured_output=True, supports_seed=True,
        base_url="http://127.0.0.1:0/v1",
    )


def _fake_payload(*, finish_reason: str, content: str, reasoning: str | None,
                  with_timings: bool = True) -> dict:
    msg: dict = {"role": "assistant", "content": content}
    if reasoning is not None:
        msg["reasoning_content"] = reasoning
    payload = {
        "choices": [{"index": 0, "message": msg, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 3700, "completion_tokens": 8192},
        "system_fingerprint": "b1-9b05354",
    }
    if with_timings:
        payload["timings"] = {"prompt_n": 3700, "prompt_ms": 2411.7,
                              "predicted_n": 8192, "predicted_ms": 301345.2,
                              "predicted_per_second": 27.18}
    return payload


def _generate(payload: dict) -> object:
    adapter = LocalLlamaCppAdapter(_manifest())

    async def fake_post(body):
        return payload, {}

    adapter._post = fake_post  # type: ignore[method-assign]
    req = GenerationRequest(model_ref="qwen38-27b",
                            messages=[Message(role="user", content="case")],
                            json_schema={"type": "object"}, max_tokens=8192)
    return asyncio.run(adapter.generate(req))


def _invocation(resp) -> ModelInvocation:
    """Exactly the construction services/ai_orchestrator/investigate.py performs."""
    return ModelInvocation(
        tier=ModelTier.SPECIALIST, provider=Provider.LOCAL_LLAMACPP,
        model_id=resp.model_id, prompt_version="1", usage=resp.usage,
        latency=resp.latency, stop_reason=resp.stop_reason, max_tokens=8192,
        reasoning_chars=resp.reasoning_chars,
        content_chars=len(resp.text) if resp.text else 0,
        reasoning_text=resp.reasoning_content,
        content_text=(resp.text or None) if resp.structured is None else None,
        timings=resp.timings,
    )


def test_length_stop_round_trips_reasoning_and_truncated_content_to_the_store():
    resp = _generate(_fake_payload(finish_reason="length", content=TRUNCATED_JSON,
                                   reasoning=REASONING))
    assert resp.stop_reason == "length"
    assert resp.structured is None                      # truncated JSON does not parse
    assert resp.reasoning_content == REASONING          # the text, not just its length
    assert resp.reasoning_chars == len(REASONING)
    assert resp.latency.ttft_ms == 2412                 # round(prompt_ms)
    assert resp.timings["predicted_per_second"] == 27.18

    traj = Trajectory(workflow="w", workflow_version="1", task_type="t", user="u",
                      experiment_arm="M0", model_invocations=[_invocation(resp)])
    stored = json.loads(traj.model_dump_json())         # == learning.trajectories.payload
    inv = stored["model_invocations"][0]
    assert inv["reasoning_text"] == REASONING
    assert inv["content_text"] == TRUNCATED_JSON
    assert inv["timings"]["prompt_ms"] == 2411.7
    assert inv["stop_reason"] == "length"
    assert inv["latency"]["ttft_ms"] == 2412

    # And back out: the stored row reconstructs the exact texts.
    revived = Trajectory(**stored)
    assert revived.model_invocations[0].reasoning_text == REASONING
    assert revived.model_invocations[0].content_text == TRUNCATED_JSON


def test_parse_success_keeps_reasoning_but_not_a_duplicate_answer_body():
    good = '{"case_id": "CASE-1"}'
    resp = _generate(_fake_payload(finish_reason="stop", content=good,
                                   reasoning=REASONING))
    assert resp.structured == {"case_id": "CASE-1"}
    inv = _invocation(resp)
    assert inv.reasoning_text == REASONING
    assert inv.content_text is None       # the parsed answer lives in model_outputs


def test_no_reasoning_and_no_timings_stay_none():
    resp = _generate(_fake_payload(finish_reason="stop", content='{"a": 1}',
                                   reasoning=None, with_timings=False))
    assert resp.reasoning_content is None
    assert resp.reasoning_chars is None
    assert resp.timings is None
    assert resp.latency.ttft_ms is None


def test_old_records_without_the_new_fields_still_validate():
    inv = ModelInvocation(tier=ModelTier.SPECIALIST, provider=Provider.LOCAL_LLAMACPP,
                          model_id="fis-qwen38-27b", prompt_version="1",
                          latency=LatencyRecord(wall_ms=1))
    assert inv.reasoning_text is None
    assert inv.content_text is None
    assert inv.timings is None


def test_request_body_still_carries_no_reasoning_key():
    """The frozen genconfig digest is computed from build_body — WP-A must not have
    touched the request side."""
    adapter = LocalLlamaCppAdapter(_manifest())
    body = adapter.build_body(GenerationRequest(
        model_ref="qwen38-27b", messages=[Message(role="user", content="x")],
        json_schema={"type": "object"}, max_tokens=8192))
    assert not {k for k in body if "reason" in k.lower()}
    assert body["max_tokens"] == 8192 and body["temperature"] == 0.0 and body["seed"] == 42
