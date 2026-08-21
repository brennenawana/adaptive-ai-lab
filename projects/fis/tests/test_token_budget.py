"""R3b — the generation budget is an explicit, recorded factor.

Three properties the token-budget experiment depends on:

  1. `investigate()` sends exactly the budget it was given, and records it on the
     invocation — otherwise a run at 8192 is indistinguishable, per case, from one at
     4096 (`stop_reason` alone cannot tell them apart when neither is reached).
  2. The default is the historical budget, so every make target that predates R3b
     still produces the configuration it recorded (config digest unchanged).
  3. The local adapter's reasoning/answer split is observation only: filled from
     what llama.cpp already returns, never sent, and absent (None) when the backend
     does not expose it.
"""

from __future__ import annotations

import asyncio

from evals.runner.run_eval import config_digest
from fis_platform.model_gateway import GenerationRequest, GenerationResponse, default_registry
from fis_platform.model_gateway.local import LocalLlamaCppAdapter
from schemas.common import LatencyRecord
from schemas.tool import ToolCall
from schemas.trajectory import ModelInvocation
from services.ai_orchestrator.investigate import DEFAULT_MAX_TOKENS, EvidenceMode, investigate


class _Broker:
    """The smallest broker `investigate()` can run against: one case, no evidence."""

    def __init__(self) -> None:
        self.calls: list[ToolCall] = []

    def invoke(self, name: str, args: dict):
        call = ToolCall(tool=name, version=1, args_hash="x", status="success",
                        latency_ms=1, sequence=len(self.calls))
        self.calls.append(call)
        if name == "get_case":
            return {"case_id": args["case_id"], "subject_ids": {}}, call
        return [], call


class _Gateway:
    """Captures the request and answers with an error, so investigate() returns
    right after recording the invocation — the request is what is under test."""

    def __init__(self) -> None:
        self.registry = default_registry()
        self.requests: list[GenerationRequest] = []

    async def generate(self, req: GenerationRequest) -> GenerationResponse:
        self.requests.append(req)
        m = self.registry.resolve(req.model_ref)
        return GenerationResponse(text="", model_id=m.model_id, provider=m.provider, tier=m.tier,
                                  latency=LatencyRecord(wall_ms=1), is_error=True, error="test")


def _run(**kw):
    gw, br = _Gateway(), _Broker()
    _, traj = asyncio.run(investigate("case-1", gateway=gw, broker=br, model_ref="local-specialist",
                                      experiment_arm="T", mode=EvidenceMode.FIXED_EVIDENCE, **kw))
    return gw, traj


def test_default_budget_is_the_historical_4096_and_is_recorded():
    gw, traj = _run()
    assert DEFAULT_MAX_TOKENS == 4096
    assert gw.requests[0].max_tokens == 4096
    assert traj.model_invocations[0].max_tokens == 4096


def test_budget_is_threaded_to_the_request_and_the_invocation():
    gw, traj = _run(max_tokens=8192)
    assert gw.requests[0].max_tokens == 8192
    assert traj.model_invocations[0].max_tokens == 8192


def test_local_body_carries_the_budget_verbatim():
    adapter = LocalLlamaCppAdapter(default_registry().resolve("nemotron-lightning"))
    body = adapter.build_body(GenerationRequest(model_ref="nemotron-lightning",
                                                messages=[{"role": "user", "content": "x"}],
                                                max_tokens=8192))
    assert body["max_tokens"] == 8192
    assert (body["temperature"], body["seed"]) == (0.0, 42)   # decoding otherwise frozen


def test_local_ceiling_admits_8192_beside_the_longest_fis_prompt():
    reg = default_registry()
    for ref in ("local-specialist", "nemotron-lightning", "local-specialist-switchyard"):
        m = reg.resolve(ref)
        assert m.max_output_tokens >= 8192
        assert 8192 + 3_600 <= m.context_window, ref   # ~3.5k is the largest dev/test prompt


def test_config_digest_is_unchanged_at_the_default_and_marked_otherwise():
    base = config_digest(model_ref="local-specialist", mode="fixed_evidence", prompt="cause_action_directed")
    assert base == "local-specialist|fixed_evidence|cause_action_directed"   # every pre-R3b run
    assert config_digest(model_ref="local-specialist", mode="fixed_evidence", prompt="cause_action_directed",
                         max_tokens=4096) == base
    assert config_digest(model_ref="local-specialist", mode="fixed_evidence", prompt="cause_action_directed",
                         max_tokens=8192) == base + "|max_tokens:8192"
    casc = config_digest(model_ref="local-specialist", mode="fixed_evidence", prompt="cause_action_directed",
                         escalate_to="claude-frontier", escalation_policy="verifier", strong_prompt="baseline")
    assert casc == base + "|cascade:verifier->claude-frontier|baseline"    # R4's recorded digest


def test_reasoning_split_is_telemetry_with_backward_compatible_defaults():
    # Records written before the fields existed load with None, not a validation error.
    inv = ModelInvocation(tier="specialist", provider="local_llamacpp", model_id="m",
                          prompt_version="1", latency=LatencyRecord(wall_ms=1))
    assert (inv.max_tokens, inv.reasoning_chars, inv.content_chars) == (None, None, None)
    # And nothing about the split is ever part of the request body.
    adapter = LocalLlamaCppAdapter(default_registry().resolve("local-specialist"))
    body = adapter.build_body(GenerationRequest(model_ref="local-specialist",
                                                messages=[{"role": "user", "content": "x"}]))
    assert not {k for k in body if "reason" in k}
