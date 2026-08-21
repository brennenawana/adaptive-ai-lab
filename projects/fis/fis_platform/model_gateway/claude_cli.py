"""Claude subscription-CLI adapter.

Drives `claude -p` as a model backend so the frontier tier runs on a Claude
subscription instead of an API key.

The flag set below is not arbitrary — it was measured. A bare `claude -p` loads the
whole Claude Code agent harness (system prompt, tool schemas, CLAUDE.md, skill
listings): 33,633 input tokens and $0.337 for a one-word prompt. Using that for E4
would measure Claude Code, not the model. With these flags the same investigation
costs 685 tokens and $0.036, with the model seeing exactly the system prompt and
evidence we hand it — the controlled comparison the guide requires.

Do NOT swap --safe-mode for --bare. --bare looks like the stricter choice but its
help text states Anthropic auth becomes "strictly ANTHROPIC_API_KEY or apiKeyHelper
(OAuth and keychain are never read)", which defeats subscription auth entirely.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any

from schemas.common import LatencyRecord, TokenUsage

from .base import GenerationRequest, GenerationResponse, ModelAdapter


class ClaudeCliAdapter(ModelAdapter):
    async def health(self) -> bool:
        cli = self.manifest.cli
        if cli is None:
            return False
        try:
            proc = await asyncio.create_subprocess_exec(
                cli.binary, "--version",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
            return proc.returncode == 0 and b"Claude Code" in out
        except (TimeoutError, FileNotFoundError, OSError):
            return False

    def _build_argv(self, req: GenerationRequest) -> list[str]:
        cli = self.manifest.cli
        assert cli is not None

        # The CLI takes a single prompt string, so a multi-turn exchange is
        # flattened. FIS investigations are single-shot over an evidence bundle,
        # so nothing is lost; if that changes, switch to --input-format stream-json.
        prompt = "\n\n".join(
            m.content if m.role == "user" else f"[{m.role}]\n{m.content}"
            for m in req.messages
            if m.role != "system"
        )

        argv = [cli.binary, "-p", prompt, *cli.base_args]

        if req.system or any(m.role == "system" for m in req.messages):
            system = req.system or next(m.content for m in req.messages if m.role == "system")
            argv += ["--system-prompt", system]

        if req.json_schema is not None:
            argv += ["--json-schema", json.dumps(req.json_schema)]

        argv += ["--model", self.manifest.model_id]

        if req.effort:
            argv += ["--effort", req.effort]

        return argv

    async def generate(self, req: GenerationRequest) -> GenerationResponse:
        self._check_policy(req)
        cli = self.manifest.cli
        assert cli is not None, "ClaudeCliAdapter requires a CliInvocation"

        env = os.environ.copy()
        if cli.auth_env_var and (tok := os.environ.get(cli.auth_env_var)):
            env[cli.auth_env_var] = tok

        argv = self._build_argv(req)
        started = time.perf_counter()
        proc = await asyncio.create_subprocess_exec(
            *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env
        )
        raw_out, raw_err = await proc.communicate()
        wall_ms = int((time.perf_counter() - started) * 1000)

        try:
            payload: dict[str, Any] = json.loads(raw_out.decode() or "{}")
        except json.JSONDecodeError:
            return GenerationResponse(
                text="", model_id=self.manifest.model_id, provider=self.manifest.provider,
                tier=self.manifest.tier, latency=LatencyRecord(wall_ms=wall_ms),
                is_error=True,
                error=f"non-JSON CLI output: {raw_err.decode()[:400] or raw_out.decode()[:400]}",
            )

        usage = self._extract_usage(payload)
        cost = self._price(usage)
        # The CLI also reports its own figure; keep it for audit alongside ours.
        cost.reported_usd = payload.get("total_cost_usd")

        structured = payload.get("structured_output")
        text = payload.get("result") or ""

        return GenerationResponse(
            text=text if isinstance(text, str) else json.dumps(text),
            structured=structured if isinstance(structured, dict) else None,
            model_id=self.manifest.model_id,
            canonical_model=self.manifest.canonical_model,
            provider=self.manifest.provider,
            tier=self.manifest.tier,
            usage=usage,
            cost=cost,
            latency=LatencyRecord(
                wall_ms=wall_ms,
                api_ms=payload.get("duration_api_ms"),
                ttft_ms=payload.get("ttft_ms"),
            ),
            stop_reason=payload.get("stop_reason"),
            is_error=bool(payload.get("is_error")),
            # `api_error_status` is an HTTP status (an int) when the API failed — an
            # upstream 500 must surface as an error response the runner records or
            # retries on --resume, not as a pydantic ValidationError that drops the
            # case (E4-v3-dev, three cases on 2026-08-17).
            error=(None if payload.get("api_error_status") is None
                   else f"api_error_status={payload.get('api_error_status')}"),
            raw=payload,
        )

    def _extract_usage(self, payload: dict[str, Any]) -> TokenUsage:
        """Attribute tokens to the model under test only.

        Claude Code invokes a small side model (observed: claude-haiku-4-5) for
        internal bookkeeping on every call. Rolling that into the investigation's
        usage would inflate the arm's measured cost with work the investigator
        never did, so `modelUsage` is filtered to the canonical model when present.
        """
        model_usage = payload.get("modelUsage") or {}
        target = self.manifest.canonical_model or self.manifest.model_id

        for entry in model_usage.values():
            if entry.get("canonicalModel") == target:
                return TokenUsage(
                    input_tokens=entry.get("inputTokens", 0),
                    output_tokens=entry.get("outputTokens", 0),
                    cache_creation_input_tokens=entry.get("cacheCreationInputTokens", 0),
                    cache_read_input_tokens=entry.get("cacheReadInputTokens", 0),
                )

        u = payload.get("usage") or {}
        return TokenUsage(
            input_tokens=u.get("input_tokens", 0),
            output_tokens=u.get("output_tokens", 0),
            cache_creation_input_tokens=u.get("cache_creation_input_tokens", 0),
            cache_read_input_tokens=u.get("cache_read_input_tokens", 0),
            thinking_tokens=(u.get("output_tokens_details") or {}).get("thinking_tokens", 0),
        )
