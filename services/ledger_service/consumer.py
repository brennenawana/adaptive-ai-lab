"""Ledger service — posts entries from normalized domain events.

Where the remaining event-shaped failures become real:

  REVERSAL RACE (S07)
    Entries are posted in ARRIVAL order but carry the event's `occurred_at`. When a
    reversal arrives before the settlement it reverses, the ledger ends up correct
    in total but confusing in sequence — postings whose `posted_at` ordering does
    not match their `occurred_at` ordering. That is the real operational hazard:
    nothing is lost, but reading the account in insertion order misleads you.

  RECONCILIATION GAP (S10)
    A settlement event that never produces a posting. Modelled as the consumer
    simply not receiving it — the processor recorded a settlement, the ledger never
    heard about it. Proving that requires noticing an absence, which no single
    record states.

  AMOUNT MAPPING ERROR (S06)
    The amount written is whatever the normalized payload carries. If the mapper
    corrupted it upstream, the ledger faithfully posts the corrupted value — which
    is exactly how this fails in production. The ledger is not the bug; it is the
    place the bug becomes visible.
"""

from __future__ import annotations

from typing import Any

import psycopg

from fis_platform.events.envelope import DomainEvent

# Which normalized event types produce a ledger effect, and in which direction.
_POSTING_RULES: dict[str, tuple[str, str]] = {
    # normalized_type -> (direction, reference_type)
    "settlement.created": ("debit", "settlement"),
    "authorization.reversed": ("credit", "reversal"),
    "fee.charged": ("debit", "fee"),
    "adjustment.applied": ("credit", "adjustment"),
}


class LedgerConsumer:
    def __init__(self, conn: psycopg.Connection) -> None:
        self.conn = conn
        self.posted: list[str] = []
        self.skipped: list[tuple[str, str]] = []

    async def handle(self, raw: dict[str, Any]) -> None:
        event = DomainEvent.model_validate(raw)

        rule = _POSTING_RULES.get(event.normalized_type)
        if rule is None:
            # Not every domain event moves money. Identity and risk events flow
            # past the ledger untouched.
            self.skipped.append((event.normalized_type, "no_posting_rule"))
            return

        direction, reference_type = rule
        account_id = event.payload.get("account_id")
        amount = event.payload.get("amount")

        if account_id is None or amount is None:
            self.skipped.append((event.normalized_type, "missing_account_or_amount"))
            return

        entry_id = f"le_{event.envelope_id.hex[:12]}"
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO ledger.entries
                     (entry_id, account_id, direction, amount, currency,
                      reference_type, reference_id, posted_at, scenario_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (entry_id) DO NOTHING""",
                (
                    entry_id,
                    account_id,
                    direction,
                    int(amount),
                    event.payload.get("currency", "GBP"),
                    reference_type,
                    event.payload.get("reference_id") or event.provider_event_id,
                    # occurred_at, NOT published_at. Posting with arrival time would
                    # hide the very reordering S07 is about.
                    event.occurred_at,
                    event.scenario_id,
                ),
            )
        self.posted.append(entry_id)

    def ordering_anomalies(self) -> list[tuple[str, str]]:
        """Entries whose POSTING ORDER disagrees with their EVENT ORDER.

        Ordered by `posting_seq` (a monotonic sequence) rather than `entry_id`,
        which is a random uuid hex and therefore not an ordering at all — an
        earlier version made that mistake and silently reported no anomalies.

        Not used for scoring. This is a harness self-check: if a scenario intends a
        race and this returns nothing, the scenario failed to create one and the
        case would be unsolvable for the wrong reason.
        """
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT entry_id, scenario_id FROM (
                    SELECT entry_id, scenario_id, posted_at,
                           LAG(posted_at) OVER (PARTITION BY account_id
                                                ORDER BY posting_seq) AS prev_posted
                    FROM ledger.entries
                ) t
                WHERE prev_posted IS NOT NULL AND posted_at < prev_posted
                """
            )
            return [(r[0], r[1]) for r in cur.fetchall()]
