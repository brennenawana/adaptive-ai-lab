"""Integration service — normalizes provider events into domain events.

This is where two of the sandbox's most realistic failures stop being scripted and
start being *emergent*:

  IDEMPOTENCY (S01 vs S02)
    Dedupe is keyed on the event's idempotency key. When the provider supplies one,
    a re-delivery is recognised and dropped. When it does not (S02), the consumer
    genuinely cannot tell a retry from a second real occurrence, and processes both
    — producing two ledger effects for one economic event. The double posting is a
    consequence of a real defect, not two rows written by a fixture.

  STALE MAPPING (S09)
    The mapper is versioned. Version 4 knows the provider's current status
    vocabulary; version 2 does not, and silently maps an unrecognised status to
    'failed'. A scenario pinned to an old mapping_version reproduces the real
    incident shape: provider says approved, our domain state says failed, and the
    only way to see it is to compare raw payload against normalized state.
"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from fis_platform.events.envelope import DomainEvent, ProviderEvent

# ---------------------------------------------------------------------------
# Versioned status mapping.
#
# The provider's vocabulary changes over time. Each mapping version encodes what we
# believed the provider's vocabulary was at that time. Running an old version
# against new provider output is the S09 defect.
# ---------------------------------------------------------------------------
_STATUS_MAPS: dict[int, dict[str, str]] = {
    2: {
        "APPROVED": "approved",
        "REJECTED": "failed",
        "PENDING": "pending",
        # v2 predates APPROVED_WITH_CONDITIONS. Anything unknown -> failed.
    },
    4: {
        "APPROVED": "approved",
        "APPROVED_WITH_CONDITIONS": "approved",
        "REJECTED": "failed",
        "PENDING": "pending",
        "TIMEOUT": "vendor_timeout",
    },
}

UNKNOWN_STATUS_FALLBACK = "failed"


def map_status(raw_status: str, mapping_version: int) -> tuple[str, bool]:
    """Return (normalized_state, was_recognised).

    The bool matters: an unrecognised status silently falling back to 'failed' is
    exactly the bug. Surfacing it lets the eval distinguish "mapper was stale" from
    "provider genuinely rejected".
    """
    table = _STATUS_MAPS.get(mapping_version, _STATUS_MAPS[4])
    if raw_status in table:
        return table[raw_status], True
    return UNKNOWN_STATUS_FALLBACK, False


class IntegrationConsumer:
    """Stateful across a generation run — holds the dedupe ledger."""

    def __init__(self, conn: psycopg.Connection, mapping_version: int = 4) -> None:
        self.conn = conn
        self.mapping_version = mapping_version
        self.emitted: list[DomainEvent] = []

    async def handle(self, raw: dict[str, Any]) -> None:
        event = ProviderEvent.model_validate(raw)

        deduped = self._is_duplicate(event)
        status = "deduplicated" if deduped else "processed"

        self._record_delivery(event, status)

        if deduped:
            # Correct behaviour: the delivery is logged, no downstream effect.
            return

        self._remember(event)

        raw_status = str(event.raw_payload.get("status", ""))
        normalized_state, recognised = map_status(raw_status, self.mapping_version)

        # Non-identity events carry no status; pass their own state through.
        if not raw_status:
            normalized_state = str(event.raw_payload.get("state", event.event_type))
            recognised = True

        domain = DomainEvent(
            causation_id=event.envelope_id,
            normalized_type=event.event_type,
            normalized_state=normalized_state,
            mapping_version=self.mapping_version,
            provider_event_id=event.provider_event_id,
            occurred_at=event.occurred_at,
            payload=event.raw_payload,
            scenario_id=event.scenario_id,
        )
        self._record_normalized(event, domain, recognised)
        self.emitted.append(domain)

    # ------------------------------------------------------------- dedupe
    def _is_duplicate(self, event: ProviderEvent) -> bool:
        """Only a SAFE idempotency key can prove a duplicate.

        Without one we have no way to distinguish a retry from a genuine second
        occurrence, so we must process it — which is the S02 defect, faithfully.
        """
        if not event.has_safe_idempotency:
            return False
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM integration.dedupe_ledger WHERE dedupe_key = %s",
                (event.dedupe_key,),
            )
            return cur.fetchone() is not None

    def _remember(self, event: ProviderEvent) -> None:
        if not event.has_safe_idempotency:
            return
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO integration.dedupe_ledger (dedupe_key, provider_event_id,
                       scenario_id, first_seen_at)
                   VALUES (%s,%s,%s,%s) ON CONFLICT (dedupe_key) DO NOTHING""",
                (event.dedupe_key, event.provider_event_id, event.scenario_id,
                 event.published_at),
            )

    # ------------------------------------------------------------- persist
    def _record_delivery(self, event: ProviderEvent, status: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO webhook.deliveries
                     (delivery_id, provider_event_id, event_type, payload_hash,
                      idempotency_key, attempt, status, received_at, scenario_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (delivery_id) DO NOTHING""",
                (f"dlv_{event.envelope_id.hex[:12]}", event.provider_event_id,
                 event.event_type, event.payload_hash, event.idempotency_key,
                 event.attempt, status, event.published_at, event.scenario_id),
            )

    def _record_normalized(self, src: ProviderEvent, domain: DomainEvent,
                           recognised: bool) -> None:
        payload = dict(src.raw_payload)
        if not recognised:
            # Leave a breadcrumb the investigator can actually find. Without this
            # the only signal is raw != normalized, which is the point of S09.
            payload["_mapper_note"] = (
                f"status {src.raw_payload.get('status')!r} not recognised by "
                f"mapping_version {self.mapping_version}"
            )
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO integration.events
                     (event_id, provider_event_id, delivery_id, normalized_type,
                      mapping_version, raw_payload, normalized_state, created_at,
                      scenario_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (event_id) DO NOTHING""",
                (f"evt_{domain.envelope_id.hex[:12]}", src.provider_event_id,
                 f"dlv_{src.envelope_id.hex[:12]}", domain.normalized_type,
                 domain.mapping_version, Jsonb(payload), domain.normalized_state,
                 domain.occurred_at, domain.scenario_id),
            )
