"""Event envelopes.

Every message on the bus carries the same envelope, because the interesting
operational failures live in the envelope rather than the payload:

  * `provider_event_id` — the provider's identity for this event. NOT unique:
    a provider re-delivering is the normal case (S01) and the whole point of dedupe.
  * `idempotency_key`   — the consumer's dedupe key. Absent in S02, which is what
    makes the double posting a real consequence rather than a scripted one.
  * `attempt`           — delivery attempt number. Retry storms are visible.
  * `occurred_at` vs `published_at` — when it happened at the provider vs when we
    saw it. S07's reversal race is exactly a divergence between these two.

Keeping `occurred_at` separate from `published_at` is what lets out-of-order
arrival be modelled honestly instead of by fudging timestamps after the fact.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from schemas.common import Base, utc_now


class Subject(StrEnum):
    """NATS subjects. Hierarchical so a consumer can bind to a wildcard."""

    WEBHOOK_RECEIVED = "fis.webhook.received"
    DOMAIN_NORMALIZED = "fis.domain.normalized"

    @staticmethod
    def webhook(provider: str) -> str:
        return f"{Subject.WEBHOOK_RECEIVED}.{provider}"

    @staticmethod
    def domain(event_type: str) -> str:
        return f"{Subject.DOMAIN_NORMALIZED}.{event_type}"


class ProviderEvent(Base):
    """Raw event as a provider would deliver it, before normalization.

    `raw_payload` is deliberately untyped: the provider owns its own schema and can
    change it under us. S09 is precisely that happening.
    """

    envelope_id: UUID = Field(default_factory=uuid4)
    provider: str
    provider_event_id: str
    event_type: str

    idempotency_key: str | None = None
    attempt: int = Field(default=1, ge=1)

    occurred_at: datetime
    published_at: datetime = Field(default_factory=utc_now)

    raw_payload: dict[str, Any] = Field(default_factory=dict)
    scenario_id: str

    @property
    def payload_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.raw_payload, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

    @property
    def dedupe_key(self) -> str:
        """What the consumer keys on.

        Falls back to provider_event_id when no idempotency key was supplied — which
        is deliberately NOT sufficient, because a provider may legitimately send the
        same event id for a retry AND for a genuine second occurrence. That
        ambiguity is the S02 defect, modelled rather than papered over.
        """
        return self.idempotency_key or f"unsafe:{self.provider_event_id}"

    @property
    def has_safe_idempotency(self) -> bool:
        return self.idempotency_key is not None


class DomainEvent(Base):
    """Post-normalization internal event. This is what downstream services consume."""

    envelope_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID = Field(description="envelope_id of the ProviderEvent that caused it")

    normalized_type: str
    normalized_state: str
    mapping_version: int

    provider_event_id: str
    occurred_at: datetime
    published_at: datetime = Field(default_factory=utc_now)

    payload: dict[str, Any] = Field(default_factory=dict)
    scenario_id: str
