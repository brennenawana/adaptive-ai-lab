"""Record/replay for the two NON-DETERMINISTIC boundaries of a value-route pass.

Why this exists: "change the code, re-run, diff" is only an experiment if
everything else is frozen. Two things move on their own between runs --

  1. CREXI HTTP. Even with every listing and comp stored locally, a re-pass still
     issues two calls per listing:
       POST /universal-search/v2/search              (comp bbox search, UNCONDITIONAL)
       GET  /universal-search/rental-markets/stats   (tier-4 market median rent)
     Both take deterministic inputs, so both are cacheable.
  2. THE LLM. Income tier 1 asks a model to read the marketing prose. Measured on
     two identical Crexi-cassette replays of the same 5 listings, arm B produced
     DIFFERENT rent producers (2659977: llm_extract, then regex_extract after the
     extraction was rejected `not_in_source`) and a self-reported confidence that
     moved 0.9 -> 0.6. With Crexi frozen, the model was the whole remaining
     variance -- so arm B was not a measurable arm until this cached it too.

Modes (both cassettes):
  record  -- call through, persist every response (misses allowed)
  replay  -- serve from the cassette; a MISS RAISES rather than silently falling
             through, so "it stayed offline / it re-used the same answers" is
             proven, not assumed.

The raise matters more for the LLM than for HTTP: `_try_llm_extract` swallows
MessageGeneratorError and drops to tier 2, so a miss that surfaced as an AiError
would be INVISIBLE -- it would look exactly like arm A. CassetteMiss is a plain
RuntimeError for that reason: `_dispatch` catches only AiError and
`value_route_pass` catches only ListingTimeoutError / connection errors, so it
propagates all the way out and aborts the pass.

Install BEFORE any pass, and before trace.install() -- the trace then observes
what the cassette served, which is what "post-cassette" means in its summaries.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time


class CassetteMiss(RuntimeError):
    """Replay hit an unrecorded request -- fail closed rather than phone home."""


class _Store:
    """A JSONL-backed keyed store. Shared by both cassettes; owns no protocol."""

    def __init__(self, path: str | pathlib.Path, mode: str = "replay") -> None:
        self.path = pathlib.Path(path)
        self.mode = mode
        self.entries: dict[str, dict] = {}
        self.hits = 0
        self.misses = 0
        self.recorded = 0
        if self.path.exists():
            with self.path.open() as fh:
                for line in fh:
                    if line.strip():
                        e = json.loads(line)
                        self.entries[e["key"]] = e

    def _miss(self, what: str, key: str) -> None:
        self.misses += 1
        raise CassetteMiss(
            f"no recording for {what} (key {key}). "
            "Re-record, or the corpus is incomplete for this pass."
        )

    def _append(self, entry: dict) -> None:
        self.entries[entry["key"]] = entry
        self.recorded += 1
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")

    def summary(self) -> dict:
        return {"mode": self.mode, "entries": len(self.entries), "hits": self.hits,
                "misses": self.misses, "recorded": self.recorded, "path": str(self.path)}


class Cassette(_Store):
    """Crexi HTTP. Keyed by sha256(METHOD path + canonical-json body)."""

    @staticmethod
    def key(method: str, path: str, body) -> str:
        blob = json.dumps(body, sort_keys=True, default=str) if body is not None else ""
        return hashlib.sha256(f"{method.upper()} {path}\n{blob}".encode()).hexdigest()[:32]

    def install(self) -> None:
        from app.providers.crexi.client import CrexiClient

        orig = CrexiClient._request
        cas = self

        def patched(self_client, method, path, *a, **k):
            body = k.get("json_body")
            if body is None and a:
                body = a[0] if isinstance(a[0], (dict, list)) else None
            k_ = cas.key(method, path, body)
            hit = cas.entries.get(k_)
            if hit is not None:
                cas.hits += 1
                return hit["response"]
            if cas.mode == "replay":
                cas._miss(f"{method} {path}", k_)
            t0 = time.time()
            resp = orig(self_client, method, path, *a, **k)
            cas._append({"key": k_, "method": method, "path": path, "body": body,
                         "response": resp, "recorded_at": time.time(),
                         "ms": round((time.time() - t0) * 1000)})
            return resp

        CrexiClient._request = patched


class AiCassette(_Store):
    """LLM completions, at the single chokepoint every AI call passes through.

    Keyed by what the model was actually ASKED -- kind, label, system prompt, user
    prompt and the response schema. Not by the listing id: two listings with an
    identical description are genuinely the same question, and a prompt-template
    edit correctly invalidates every entry (a re-record is the honest response to
    "the prompt changed", not a stale cache hit).

    Records SUCCESSES ONLY. A failure during a record pass passes through
    unrecorded, so the next replay misses on that key and raises -- rather than
    this module having to faithfully reconstruct a provider exception, which it
    cannot do without guessing.
    """

    @staticmethod
    def key(task) -> str:
        payload = json.dumps({
            "kind": getattr(task, "kind", None),
            "label": getattr(task, "label", None),
            "system": getattr(task, "system", None),
            "user": getattr(task, "user", None),
            "schema": getattr(task, "schema", None),
            "max_tokens": getattr(task, "max_tokens", None),
        }, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()[:32]

    def install(self) -> None:
        import app.generation.message_generator as MG
        from app.ai.types import Completion

        orig = MG.ai_complete
        cas = self

        def patched(task, settings, *, client=None, **k):
            k_ = cas.key(task)
            hit = cas.entries.get(k_)
            if hit is not None:
                cas.hits += 1
                # Replay the raw provider TEXT, not a parsed object: _dispatch still
                # runs parse_into + post_validate, so a replayed run exercises the
                # same validation path a live one does.
                return Completion(text=hit["text"], model=hit["model"],
                                  provider=hit["provider"], usage=hit.get("usage") or {})
            if cas.mode == "replay":
                cas._miss(f"ai {getattr(task, 'label', '?')}/{getattr(task, 'kind', '?')}", k_)
            t0 = time.time()
            comp = orig(task, settings, client=client, **k)
            cas._append({"key": k_, "kind": getattr(task, "kind", None),
                         "label": getattr(task, "label", None),
                         "prompt_sha12": hashlib.sha256(
                             (getattr(task, "system", "") or "").encode()).hexdigest()[:12],
                         "text": comp.text, "model": comp.model, "provider": comp.provider,
                         "usage": dict(comp.usage or {}), "recorded_at": time.time(),
                         "ms": round((time.time() - t0) * 1000)})
            return comp

        MG.ai_complete = patched


def from_env() -> Cassette | None:
    """Crexi cassette from CREXI_CASSETTE (path) + CREXI_CASSETTE_MODE (record|replay)."""
    p = os.environ.get("CREXI_CASSETTE")
    if not p:
        return None
    return Cassette(p, os.environ.get("CREXI_CASSETTE_MODE", "replay"))


def ai_from_env() -> AiCassette | None:
    """LLM cassette from CREXI_AI_CASSETTE (path) + CREXI_AI_CASSETTE_MODE (record|replay)."""
    p = os.environ.get("CREXI_AI_CASSETTE")
    if not p:
        return None
    return AiCassette(p, os.environ.get("CREXI_AI_CASSETTE_MODE", "replay"))
