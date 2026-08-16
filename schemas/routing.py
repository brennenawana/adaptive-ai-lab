"""Routing metadata — what a routing gateway did to a request, recorded on the FIS side.

The pivot guide draws one line and this module sits on it: a routing layer
(NeMo Switchyard first) may own protocol translation, backend selection inside an
approved profile, fallback and per-request backend statistics. It may **not** own
scenario truth, evidence rules, the scorer, or the trajectory record. So whatever
the gateway reports about a request is copied *into* the canonical FIS trajectory
as one more field on the model invocation — it enriches the record, it never
replaces it. If the gateway is swapped out, these fields go empty and nothing else
in the eval harness notices.

Two shapes, deliberately separate:

* `RoutingProfile` — what a registry entry *declares* about how its traffic is
  routed. Config, known before any request is made.
* `RoutingRecord`  — what *actually happened* on one invocation, as observed from
  the response. Only fields the gateway really reported are set; nothing is
  inferred from the profile and written back as if it had been observed.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator

from .common import Base


class RouteMode(StrEnum):
    """How the gateway chose a backend. Mirrors the pivot guide's vocabulary."""

    PASSTHROUGH = "passthrough"   # one route id -> one backend, no decision at all
    RANDOM = "random"             # fixed traffic split (A/B, baselines)
    CASCADE = "cascade"           # weak first, deterministic checks decide escalation
    CLASSIFIER = "classifier"     # a model reads the request and picks a tier
    STAGE = "stage"               # signal / history driven stage router


# Names that must never appear as routing features. These are eval labels — the
# scorer may use them to *judge* a route after the fact, but a router that reads
# them is cheating in the most invisible way: it would look like a router that
# had learned the task. `test_routing_no_gold_leak.py` pins this list to the
# manifest schema so a new gold field cannot slip past it unnoticed.
GOLD_FEATURE_NAMES: frozenset[str] = frozenset({
    "root_cause", "required_evidence", "acceptable_next_actions", "forbidden_claims",
    "distractor_event_ids", "scenario_id", "seed", "split", "category",
})


class RoutingProfile(Base):
    """Declared routing for one registry entry."""

    gateway: str = Field(description="e.g. 'switchyard'")
    gateway_version: str | None = None
    route_profile: str = Field(description="Route/model id the gateway is asked for.")
    route_mode: RouteMode
    backends: list[str] = Field(
        min_length=1,
        description="Backends the profile may select between, as the gateway names them.",
    )
    all_backends_local: bool = Field(
        description="True only if every backend is on this machine. Drives the "
        "LOCAL_ONLY data-policy check, so it must be conservative.",
    )
    config_path: str | None = Field(
        default=None, description="Repo-relative path of the gateway config, for lineage.",
    )


class RoutingRecord(Base):
    """What the gateway reported for one invocation."""

    gateway: str
    gateway_version: str | None = None
    route_profile: str
    route_mode: RouteMode
    decision_id: str | None = None
    selected_backend: str | None = Field(
        default=None, description="As reported by the gateway. None if it did not say.",
    )
    upstream_model: str | None = None
    router_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    router_signals: dict[str, Any] = Field(default_factory=dict)
    escalated: bool = False
    escalation_reason: str | None = None
    fallback_used: bool = False
    gateway_overhead_ms: int | None = Field(
        default=None,
        description="Time spent in the gateway itself, if it reports it — separate "
        "from backend latency so a slow router cannot hide inside model latency.",
    )

    @field_validator("router_signals")
    @classmethod
    def _no_gold_features(cls, v: dict[str, Any]) -> dict[str, Any]:
        leaked = sorted(k for k in v if k in GOLD_FEATURE_NAMES)
        if leaked:
            raise ValueError(
                f"router_signals contains eval-only ground truth {leaked}; a router "
                "may be scored by these fields, never fed them"
            )
        return v


__all__ = ["GOLD_FEATURE_NAMES", "RouteMode", "RoutingProfile", "RoutingRecord"]
