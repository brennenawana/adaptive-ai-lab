"""Model gateway: Claude Code CLI on subscription auth (the FIS pattern).

Flag set inherited from fis_platform/model_gateway (validated by measurement
there: bare `claude -p` loads the whole agent harness, ~33.6K tokens; with
--safe-mode + --system-prompt the model sees exactly the prompt we hand it).
--bare is forbidden: it disables OAuth and would demand an API key.

Spend semantics under subscription: marginal dollars are $0; the meter records
LIST-PRICE-EQUIVALENT dollars from token usage so caps S2-S5 remain
enforceable consumption governance (and stay comparable if a run ever moves
to API billing).
"""

import json
import os
import shutil
import subprocess

from . import config
from .budget import Meter

BASE_ARGS = [
    "--safe-mode",              # strips CLAUDE.md/skills/plugins/hooks/MCP, keeps OAuth
    "--disable-slash-commands",
    "--strict-mcp-config",
    "--no-session-persistence",
]


class GatewayError(Exception):
    pass


def cli_binary() -> str:
    path = shutil.which("claude")
    if not path:
        raise GatewayError("`claude` CLI not found on PATH")
    return path


def _extract_usage(payload: dict, model: str) -> tuple[dict, float]:
    """(tokens attributed to the model under test, total list-equivalent USD).

    modelUsage may hold several entries (dated + alias keys, side models); the
    smoke audit showed summing only one undercounts ~30x. Budget totals bill
    EVERY entry's costUSD (== total_cost_usd); attribution sums the matching
    canonical model's entries only."""
    attributed = {"input_tokens": 0, "output_tokens": 0,
                  "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    total_usd = 0.0
    for entry in (payload.get("modelUsage") or {}).values():
        total_usd += entry.get("costUSD") or 0.0
        canonical = entry.get("canonicalModel") or ""
        if canonical == model or canonical.startswith(model):
            attributed["input_tokens"] += entry.get("inputTokens", 0)
            attributed["output_tokens"] += entry.get("outputTokens", 0)
            attributed["cache_creation_input_tokens"] += entry.get("cacheCreationInputTokens", 0)
            attributed["cache_read_input_tokens"] += entry.get("cacheReadInputTokens", 0)
    reported = payload.get("total_cost_usd") or 0.0
    return attributed, max(total_usd, reported)


def run_cli(*, meter: Meter, role: str, model: str, system: str, prompt: str,
            cwd=None, tools: str = "", max_turns: int | None = None,
            json_schema: dict | None = None, stream: bool = False,
            timeout: int = 1800, extra_env: dict | None = None,
            meta: dict | None = None) -> tuple[dict, list]:
    """One CLI invocation = one (possibly multi-turn) model conversation.
    Returns (final result payload, event list [] unless stream)."""
    meter.precheck()

    argv = [cli_binary(), "-p", prompt, *BASE_ARGS,
            "--tools", tools,
            "--system-prompt", system,
            "--model", model,
            "--output-format", "stream-json" if stream else "json"]
    if stream:
        argv += ["--verbose"]
    if max_turns is not None:
        argv += ["--max-turns", str(max_turns)]
    if json_schema is not None:
        argv += ["--json-schema", json.dumps(json_schema)]
    if tools:
        argv += ["--permission-mode", "bypassPermissions"]

    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    try:
        proc = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise GatewayError(f"{role}: CLI wall-clock timeout after {timeout}s") from e

    events: list = []
    payload: dict = {}
    if stream:
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            events.append(obj)
            if obj.get("type") == "result":
                payload = obj
    else:
        try:
            payload = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            payload = {}

    if not payload:
        raise GatewayError(
            f"{role}: no result payload (rc={proc.returncode}) "
            f"stderr={proc.stderr[:400]!r} stdout={proc.stdout[:400]!r}")

    usage, total_usd = _extract_usage(payload, model)
    meter.record(model=model, usage=usage, role=role, usd_total=total_usd,
                 meta={**(meta or {}),
                       "cli_reported_usd": payload.get("total_cost_usd"),
                       "num_turns": payload.get("num_turns"),
                       "is_error": bool(payload.get("is_error"))})
    return payload, events


def structured_or_json(payload: dict):
    """Prefer --json-schema structured output; fall back to parsing the result text."""
    s = payload.get("structured_output")
    if isinstance(s, dict):
        return s
    text = payload.get("result") or ""
    if isinstance(text, dict):
        return text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None
