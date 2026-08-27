"""Transport-level record/replay for Crexi HTTP, so a re-run needs no network.

Why this exists: even with every listing and comp stored locally, a re-pass still
issues two calls per listing --
  POST /universal-search/v2/search              (comp bbox search, UNCONDITIONAL)
  GET  /universal-search/rental-markets/stats   (tier-4 market median rent)
Both take deterministic inputs, so both are cacheable. With them cached the whole
ingest->value-route path replays offline against frozen inputs, which is what
makes "change the code, re-run, compare" a valid experiment instead of a
measurement of Crexi's churn.

Modes:
  record  -- call through, persist every response (misses allowed)
  replay  -- serve from the cassette; a MISS RAISES rather than silently
             falling through to the network, so "it stayed offline" is proven,
             not assumed.

Keyed by sha256(METHOD path + canonical-json body). Install BEFORE any pass.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time


class CassetteMiss(RuntimeError):
    """Replay hit an unrecorded request -- fail closed rather than phone home."""


class Cassette:
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
                cas.misses += 1
                raise CassetteMiss(
                    f"no recording for {method} {path} (key {k_}). "
                    "Re-record, or the corpus is incomplete for this pass."
                )
            t0 = time.time()
            resp = orig(self_client, method, path, *a, **k)
            entry = {"key": k_, "method": method, "path": path,
                     "body": body, "response": resp,
                     "recorded_at": time.time(), "ms": round((time.time() - t0) * 1000)}
            cas.entries[k_] = entry
            cas.recorded += 1
            with self.__class__._lock_free_append(cas.path) as fh:
                fh.write(json.dumps(entry, default=str) + "\n")
            return resp

        CrexiClient._request = patched

    @staticmethod
    def _lock_free_append(path: pathlib.Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.open("a")

    def summary(self) -> dict:
        return {"mode": self.mode, "entries": len(self.entries), "hits": self.hits,
                "misses": self.misses, "recorded": self.recorded, "path": str(self.path)}


def from_env() -> Cassette | None:
    """Build from CREXI_CASSETTE (path) + CREXI_CASSETTE_MODE (record|replay)."""
    p = os.environ.get("CREXI_CASSETTE")
    if not p:
        return None
    return Cassette(p, os.environ.get("CREXI_CASSETTE_MODE", "replay"))
