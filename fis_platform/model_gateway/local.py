"""Local llama.cpp adapter — OpenAI-compatible HTTP.

The local tier is the one arm that is bit-reproducible (fixed seed, --parallel 1),
which makes it the reference point every other arm is compared against.
"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from schemas.common import LatencyRecord, TokenUsage

from .base import GenerationRequest, GenerationResponse, ModelAdapter
from .schema_compat import to_gbnf_safe


class LocalLlamaCppAdapter(ModelAdapter):
    def __init__(self, manifest, timeout_s: float = 600.0) -> None:
        super().__init__(manifest)
        self._timeout = timeout_s

    @property
    def _base(self) -> str:
        return (self.manifest.base_url or "").rstrip("/")

    async def health(self) -> bool:
        root = self._base.removesuffix("/v1")
        try:
            async with httpx.AsyncClient(timeout=5.0) as c:
                r = await c.get(f"{root}/health")
                return r.status_code == 200 and r.json().get("status") == "ok"
        except (httpx.HTTPError, ValueError):
            return False

    # ------------------------------------------------------------------ request
    def build_body(self, req: GenerationRequest) -> dict[str, Any]:
        """The exact JSON sent to /chat/completions.

        Kept as its own method so a routed arm (Switchyard passthrough) can be
        shown to send a byte-identical body — R1's equivalence claim is a claim
        about this dict, and a test can assert it without a server.
        """
        messages: list[dict[str, Any]] = []
        if req.system:
            messages.append({"role": "system", "content": req.system})
        messages += [
            {k: v for k, v in m.model_dump().items() if v is not None} for m in req.messages
        ]

        body: dict[str, Any] = {
            "model": self.manifest.model_id,
            "messages": messages,
            "max_tokens": req.max_tokens,
            # Greedy. The local arm is the reproducible baseline; sampling noise
            # here would show up as eval variance and be mistaken for a real effect.
            "temperature": 0.0,
            "seed": 42,
        }
        if req.stop:
            body["stop"] = req.stop
        if req.tools:
            body["tools"] = req.tools
        if req.json_schema is not None:
            # llama.cpp converts this to a GBNF grammar and constrains decoding, so
            # the output cannot be malformed rather than merely usually being valid.
            # Length/numeric constraints must be stripped first — this build fails
            # grammar compilation on them. The verifier still enforces them.
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "fis_output",
                    "schema": to_gbnf_safe(req.json_schema),
                    "strict": True,
                },
            }
        return body

    # ------------------------------------------------------------------ transport
    async def _post(self, body: dict[str, Any]) -> tuple[dict[str, Any], httpx.Headers]:
        async with httpx.AsyncClient(timeout=self._timeout) as c:
            r = await c.post(f"{self._base}/chat/completions", json=body)
            r.raise_for_status()
            return r.json(), r.headers

    def _annotate(self, resp: GenerationResponse, headers: httpx.Headers) -> GenerationResponse:
        """Hook for subclasses that learn something from the transport (a routing
        gateway's headers). The direct path learns nothing and returns as-is."""
        return resp

    # ------------------------------------------------------------------ generate
    async def generate(self, req: GenerationRequest) -> GenerationResponse:
        self._check_policy(req)
        body = self.build_body(req)

        started = time.perf_counter()
        try:
            payload, headers = await self._post(body)
        except httpx.HTTPError as exc:
            # Include the server's response body. llama.cpp returns the actual
            # reason (bad grammar, context overflow) in the body; without it a 400
            # is just "something was wrong" and costs an hour to diagnose.
            detail = ""
            if isinstance(exc, httpx.HTTPStatusError):
                detail = f" | body: {exc.response.text[:600]}"
            return GenerationResponse(
                text="", model_id=self.manifest.model_id, provider=self.manifest.provider,
                tier=self.manifest.tier,
                latency=LatencyRecord(wall_ms=int((time.perf_counter() - started) * 1000)),
                is_error=True, error=f"{type(exc).__name__}: {exc}{detail}",
            )
        wall_ms = int((time.perf_counter() - started) * 1000)

        # llama.cpp reports its own compute time. Recording it as api_ms makes
        # wall - api the transport overhead, which is the quantity a routing
        # gateway adds — measurable per request instead of inferred from p50s.
        timings = payload.get("timings") or {}
        api_ms = wall_ms
        if "prompt_ms" in timings and "predicted_ms" in timings:
            api_ms = int(round(float(timings["prompt_ms"]) + float(timings["predicted_ms"])))

        choice = (payload.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        u = payload.get("usage") or {}

        usage = TokenUsage(
            input_tokens=u.get("prompt_tokens", 0),
            output_tokens=u.get("completion_tokens", 0),
        )

        structured = None
        if req.json_schema is not None and isinstance(msg.get("content"), str):
            try:
                structured = json.loads(msg["content"])
            except json.JSONDecodeError:
                # Grammar-constrained decoding should make this unreachable. If it
                # fires, the grammar was not applied — worth surfacing loudly rather
                # than silently degrading to free-form text.
                structured = None

        resp = GenerationResponse(
            text=msg.get("content") or "",
            structured=structured,
            tool_calls=msg.get("tool_calls") or [],
            model_id=self.manifest.model_id,
            canonical_model=self.manifest.canonical_model,
            provider=self.manifest.provider,
            tier=self.manifest.tier,
            usage=usage,
            cost=self._price(usage),
            latency=LatencyRecord(wall_ms=wall_ms, api_ms=api_ms),
            stop_reason=choice.get("finish_reason"),
            runtime_fingerprint=payload.get("system_fingerprint"),
            raw=payload,
        )
        return self._annotate(resp, headers)
