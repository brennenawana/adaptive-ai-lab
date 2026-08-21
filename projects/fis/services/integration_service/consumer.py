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

  AMOUNT CORRUPTION (S06)
    Version 3 shipped a field-order defect that transposes the last two digits of
    a minor-units amount. The ledger then posts the corrupted value faithfully, so
    the processor and the ledger disagree by a 9-divisible delta — the arithmetic
    signature of a transposition. The corruption happens HERE, in the mapper, which
    is what makes S06 a produced failure rather than a depicted one.

Row construction is deliberately split out into module-level `*_row` functions. The
consumer persists them; `fis_platform.events.projection` replays the same functions
without a database so the generator can declare required evidence up front. One
source of truth for both the decision and the row shape — if they were written twice
they would drift, and the drift would surface as unwinnable eval cases.
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


# Mapping versions carrying the amount-transposition defect. A set rather than a
# comparison because this is a specific bad release, not "everything before v4" —
# v2 is stale about vocabulary but handles money correctly.
AMOUNT_TRANSPOSING_VERSIONS = frozenset({3})


def map_amount(amount: int, mapping_version: int) -> tuple[int, bool]:
    """Return (normalized_amount, was_faithful).

    v3 transposes the final two digits of the minor-units value. Any adjacent-digit
    transposition shifts the value by a multiple of 9, which is the signature a
    reconciliation analyst looks for — and the reason this defect is worth modelling
    rather than a random perturbation.

    A value whose last two digits are equal cannot be visibly transposed. The
    generator pins S06's amount so this never silently produces a clean mapping;
    returning the amount unchanged here is the honest answer, not a fallback.
    """
    if mapping_version not in AMOUNT_TRANSPOSING_VERSIONS:
        return amount, True
    digits = f"{amount:d}"
    if len(digits) < 2 or digits[-1] == digits[-2]:
        return amount, True
    return int(digits[:-2] + digits[-1] + digits[-2]), False


# ---------------------------------------------------------------------------
# Row construction. Pure — no database, no clock. Shared with the projection.
# ---------------------------------------------------------------------------
def delivery_row(event: ProviderEvent, status: str) -> dict[str, Any]:
    return {
        "delivery_id": event.delivery_id,
        "provider_event_id": event.provider_event_id,
        "event_type": event.event_type,
        "payload_hash": event.payload_hash,
        "idempotency_key": event.idempotency_key,
        "attempt": event.attempt,
        "status": status,
        "received_at": event.published_at,
        "scenario_id": event.scenario_id,
    }


def normalized_row(src: ProviderEvent, domain: DomainEvent, recognised: bool) -> dict[str, Any]:
    payload = dict(src.raw_payload)
    if not recognised:
        # Leave a breadcrumb the investigator can actually find. Without this the
        # only signal is raw != normalized, which is the point of S09.
        payload["_mapper_note"] = (
            f"status {src.raw_payload.get('status')!r} not recognised by "
            f"mapping_version {domain.mapping_version}"
        )
    return {
        "event_id": domain.event_id,
        "provider_event_id": src.provider_event_id,
        "delivery_id": src.delivery_id,
        "normalized_type": domain.normalized_type,
        "mapping_version": domain.mapping_version,
        # The RAW payload, uncorrupted. S06 is only diagnosable because what the
        # provider sent survives next to what we made of it.
        "raw_payload": payload,
        "normalized_state": domain.normalized_state,
        "created_at": domain.occurred_at,
        "scenario_id": domain.scenario_id,
    }


def normalize(event: ProviderEvent, mapping_version: int) -> tuple[DomainEvent, bool]:
    """The mapper itself. Pure, so the projection and the consumer cannot diverge."""
    raw_status = str(event.raw_payload.get("status", ""))
    normalized_state, recognised = map_status(raw_status, mapping_version)

    # Non-identity events carry no status; pass their own state through.
    if not raw_status:
        normalized_state = str(event.raw_payload.get("state", event.event_type))
        recognised = True

    payload = dict(event.raw_payload)
    if isinstance(payload.get("amount"), int):
        payload["amount"], _ = map_amount(payload["amount"], mapping_version)

    domain = DomainEvent(
        envelope_id=event.domain_envelope_id,
        causation_id=event.envelope_id,
        normalized_type=event.event_type,
        normalized_state=normalized_state,
        mapping_version=mapping_version,
        provider_event_id=event.provider_event_id,
        occurred_at=event.occurred_at,
        published_at=event.published_at,
        payload=payload,
        scenario_id=event.scenario_id,
    )
    return domain, recognised


class IntegrationConsumer:
    """Stateful across a generation run — holds the dedupe ledger."""

    def __init__(self, conn: psycopg.Connection, mapping_version: int = 4) -> None:
        self.conn = conn
        self.mapping_version = mapping_version
        self.emitted: list[DomainEvent] = []
        # What was actually persisted, for the generator's projection self-check.
        self.wrote_deliveries: list[str] = []
        self.wrote_events: list[str] = []

    async def handle(self, raw: dict[str, Any]) -> None:
        event = ProviderEvent.model_validate(raw)

        deduped = self._is_duplicate(event)
        status = "deduplicated" if deduped else "processed"

        self._record_delivery(event, status)

        if deduped:
            # Correct behaviour: the delivery is logged, no downstream effect.
            return

        self._remember(event)

        domain, recognised = normalize(event, self.mapping_version)
        self._record_normalized(event, domain, recognised)
        self.emitted.append(domain)

    def take_emitted(self) -> list[DomainEvent]:
        """Hand off what this batch produced and reset.

        The consumer does not publish downstream itself: the generator's driver
        does, so that publish order stays under the generator's control. That is
        what keeps S07's inverted order deliberate rather than incidental.
        """
        out, self.emitted = self.emitted, []
        return out

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
        row = delivery_row(event, status)
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO webhook.deliveries
                     (delivery_id, provider_event_id, event_type, payload_hash,
                      idempotency_key, attempt, status, received_at, scenario_id)
                   VALUES (%(delivery_id)s,%(provider_event_id)s,%(event_type)s,
                           %(payload_hash)s,%(idempotency_key)s,%(attempt)s,
                           %(status)s,%(received_at)s,%(scenario_id)s)
                   ON CONFLICT (delivery_id) DO NOTHING""",
                row,
            )
        self.wrote_deliveries.append(row["delivery_id"])

    def _record_normalized(self, src: ProviderEvent, domain: DomainEvent,
                           recognised: bool) -> None:
        row = normalized_row(src, domain, recognised)
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO integration.events
                     (event_id, provider_event_id, delivery_id, normalized_type,
                      mapping_version, raw_payload, normalized_state, created_at,
                      scenario_id)
                   VALUES (%(event_id)s,%(provider_event_id)s,%(delivery_id)s,
                           %(normalized_type)s,%(mapping_version)s,%(raw_payload)s,
                           %(normalized_state)s,%(created_at)s,%(scenario_id)s)
                   ON CONFLICT (event_id) DO NOTHING""",
                {**row, "raw_payload": Jsonb(row["raw_payload"])},
            )
        self.wrote_events.append(row["event_id"])
