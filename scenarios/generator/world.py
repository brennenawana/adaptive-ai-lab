"""Deterministic synthetic world primitives.

Hard rules, both load-bearing for eval reproducibility:
  * No global `random` — every draw comes from a seeded Random passed in.
  * No `datetime.now()` — all timestamps derive from a fixed epoch plus offsets.
Break either and the same seed stops producing the same world, which silently
invalidates every before/after comparison built on it.

Names are obviously fictional by construction, per the guide's security boundary.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from random import Random
from typing import Any
from uuid import UUID, uuid5

from fis_platform.events.envelope import ProviderEvent

# Envelope ids must be deterministic or the whole corpus stops being reproducible:
# every row the pipeline writes is named after the envelope that caused it, so a
# uuid4 here would give the same seed a different set of delivery, event and entry
# ids on every regeneration — and the manifest's required evidence would point at
# the previous run's rows.
ENVELOPE_NAMESPACE = UUID("2b9d7c41-8e56-5a03-b1f4-7c8d9e0a1b23")

# Fixed. Not "now" — a generator whose output depends on the wall clock is not
# reproducible, and the test set would drift every time it was regenerated.
EPOCH = datetime(2026, 1, 6, 9, 0, 0, tzinfo=timezone.utc)

_FIRST = ["Marlow", "Piper", "Wexler", "Juno", "Ondine", "Caspian", "Bly", "Vesper",
          "Thorne", "Lark", "Emory", "Sable", "Quill", "Rune", "Nym", "Halcyon"]
_LAST = ["Ashgrove", "Fenwick", "Dunmore", "Quillon", "Ravensmere", "Holloway",
         "Stonebridge", "Vandermolen", "Ashcombe", "Blackwood", "Merriwether", "Tarrant"]
_MERCHANTS = ["Northwind Grocers", "Aperture Coffee", "Bluepeak Transit", "Cindershop",
              "Delta Provisions", "Everline Books", "Foxglove Pharmacy", "Grainhouse"]
_COUNTRIES = ["GB", "IE", "NL", "PT", "SE"]
_VENDORS = ["veriscope", "trustloop", "idmirror"]


def digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


@dataclass
class Clock:
    """Monotonic, deterministic timeline for one scenario."""

    base: datetime = EPOCH
    cursor: timedelta = field(default_factory=timedelta)

    def tick(self, *, minutes: int = 0, hours: int = 0, days: int = 0, seconds: int = 0) -> datetime:
        self.cursor += timedelta(minutes=minutes, hours=hours, days=days, seconds=seconds)
        return self.base + self.cursor

    def at(self, offset_minutes: int) -> datetime:
        """Absolute offset from base — used when a scenario needs out-of-order
        timestamps (S07 reversal race) rather than a monotonic sequence."""
        return self.base + timedelta(minutes=offset_minutes)

    def before(self, *, days: int = 0, hours: int = 0, minutes: int = 0) -> datetime:
        """A time in the past WITHOUT moving the cursor.

        Backdated facts — when a customer signed up, when an account was opened —
        are not events on the scenario's timeline. Expressing them with `tick(days=-30)`
        rewound the shared cursor, so each extra customer dragged everything after it
        another month into the past. S04 suffered worst: its four "simultaneous"
        vendor timeouts were generated a month apart, so the outage it claimed to
        model had no temporal cluster in it at all.
        """
        return self.base + self.cursor - timedelta(days=days, hours=hours, minutes=minutes)


class Ids:
    """Deterministic ids, globally unique across every scenario.

    The seed is part of every id. An earlier version used a per-scenario counter
    plus a few random digits, which collided as soon as the split grew past a
    handful of scenarios — entity ids must be unique across the whole corpus
    because they all land in one set of tables.
    """

    def __init__(self, rng: Random, seed: int) -> None:
        self._rng = rng
        self._seed = seed
        self._counters: dict[str, int] = {}

    def next(self, prefix: str) -> str:
        n = self._counters.get(prefix, 0) + 1
        self._counters[prefix] = n
        return f"{prefix}_{self._seed}_{n:02d}"

    def provider(self, vendor_prefix: str) -> str:
        n = self._counters.get("_prov", 0) + 1
        self._counters["_prov"] = n
        return f"{vendor_prefix}-{self._seed}-{n:02d}"


def person(rng: Random) -> tuple[str, str, str]:
    name = f"{rng.choice(_FIRST)} {rng.choice(_LAST)}"
    dob = f"19{rng.randint(60, 99)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
    return name, dob, rng.choice(_COUNTRIES)


def merchant(rng: Random) -> str:
    return rng.choice(_MERCHANTS)


def vendor(rng: Random) -> str:
    return rng.choice(_VENDORS)


def minor_units(rng: Random, low: int = 500, high: int = 900_00) -> int:
    """Money in minor units, always an int. Floats for currency are a bug."""
    return rng.randrange(low, high, 5)


@dataclass
class World:
    """Accumulates one scenario: authoritative service state, plus the provider
    events whose consequences the pipeline will materialise.

    Nothing here touches the database or the broker — keeping generation pure makes
    it testable without Postgres and makes a dry run genuinely free.

    The two halves are not interchangeable:

      * **State** (customers, accounts, cards, authorizations, settlements,
        verifications, alerts, cases) is what each service independently knows. The
        writer INSERTs it, because no event produced it — the processor really did
        record that settlement.
      * **Published events** are causes, not records. Whatever they produce —
        webhook deliveries, normalized integration events, ledger entries — is
        written by the consumers, because a failure the generator writes down by
        hand is depicted rather than produced.

    `webhook.deliveries`, `integration.events` and pipeline-caused `ledger.entries`
    therefore have no builder here. That absence is the point of step 7 of the
    migration: a scenario that wants a duplicate delivery has to publish twice and
    let dedupe fail, which is the only version of the bug that can surprise us.
    """

    scenario_id: str
    seed: int
    rng: Random
    clock: Clock
    ids: Ids

    # Which mapper version the integration service runs at for THIS scenario.
    # v2 is stale about status vocabulary (S09); v3 corrupts amounts (S06).
    mapping_version: int = 4

    customers: list[dict] = field(default_factory=list)
    verifications: list[dict] = field(default_factory=list)
    accounts: list[dict] = field(default_factory=list)
    entries: list[dict] = field(default_factory=list)
    cards: list[dict] = field(default_factory=list)
    authorizations: list[dict] = field(default_factory=list)
    settlements: list[dict] = field(default_factory=list)
    alerts: list[dict] = field(default_factory=list)
    deliveries: list[dict] = field(default_factory=list)
    cases: list[dict] = field(default_factory=list)

    published: list[ProviderEvent] = field(default_factory=list)
    _envelope_n: int = 0

    # --- events -----------------------------------------------------------------

    def publish(self, *, provider_event_id: str, event_type: str, raw_payload: dict,
                provider: str = "northpay", idempotency_key: str | None = None,
                attempt: int = 1, occurred_at: datetime | None = None,
                delivery_lag_minutes: int = 2) -> ProviderEvent:
        """Queue a provider event for publication, in call order.

        `published_at` advances the scenario clock on every call, so it is monotonic
        in publish order by construction. `occurred_at` defaults to the same instant
        but can be set earlier — that divergence is the whole of S07: an event that
        happened first but arrived second.

        Call order IS publish order IS the order the consumers will see. Nothing
        downstream reorders, so a race is something a builder chooses, never
        something timing does to it.

        The returned envelope already knows the ids its consequences will carry
        (`delivery_id`, `normalized_event_id`, `ledger_entry_id`), so a builder can
        cite them as required evidence without predicting a uuid.
        """
        seen_at = self.clock.tick(minutes=delivery_lag_minutes)
        self._envelope_n += 1
        event = ProviderEvent(
            envelope_id=uuid5(ENVELOPE_NAMESPACE, f"{self.scenario_id}:{self._envelope_n}"),
            provider=provider,
            provider_event_id=provider_event_id,
            event_type=event_type,
            idempotency_key=idempotency_key,
            attempt=attempt,
            occurred_at=occurred_at or seen_at,
            published_at=seen_at,
            raw_payload=raw_payload,
            scenario_id=self.scenario_id,
        )
        self.published.append(event)
        return event

    # --- builders ---------------------------------------------------------------

    def add_customer(self, state: str = "active") -> dict:
        name, dob, country = person(self.rng)
        row = {
            "customer_id": self.ids.next("cus"),
            "display_name": name,
            "dob": dob,
            "country": country,
            "onboarding_state": state,
            "created_at": self.clock.before(days=30),
            "scenario_id": self.scenario_id,
        }
        self.customers.append(row)
        return row

    def add_verification(self, customer: dict, *, check_type: str, status: str,
                         reason_code: str | None = None, minutes: int = 5,
                         vendor_name: str | None = None) -> dict:
        # `vendor_name` pins the vendor instead of drawing one. S04 needs it: an
        # outage is one vendor failing, and drawing independently per verification
        # scattered the cluster across three vendors, which is not the incident the
        # scenario claims to be.
        row = {
            "verification_id": self.ids.next("ver"),
            "provider_ref": self.ids.provider("vs"),
            "customer_id": customer["customer_id"],
            "vendor": vendor_name or vendor(self.rng),
            "check_type": check_type,
            "status": status,
            "reason_code": reason_code,
            "event_time": self.clock.tick(minutes=minutes),
            "scenario_id": self.scenario_id,
        }
        self.verifications.append(row)
        return row

    def add_account(self, customer: dict, *, status: str = "active",
                    balance: int | None = None) -> dict:
        bal = balance if balance is not None else minor_units(self.rng, 10_000, 500_000)
        row = {
            "account_id": self.ids.next("acc"),
            "customer_id": customer["customer_id"],
            "status": status,
            "currency": "GBP",
            "available_balance": bal,
            "ledger_balance": bal,
            "opened_at": self.clock.before(days=29),
            "scenario_id": self.scenario_id,
        }
        self.accounts.append(row)
        return row

    def add_card(self, customer: dict, account: dict, *, status: str = "active") -> dict:
        row = {
            "card_id": self.ids.next("card"),
            "provider_ref": self.ids.provider("cd"),
            "customer_id": customer["customer_id"],
            "account_id": account["account_id"],
            "status": status,
            "pan_token": f"tok_{self.rng.randint(10**11, 10**12 - 1)}",
            "issued_at": self.clock.before(days=28) if status != "not_issued" else None,
            "scenario_id": self.scenario_id,
        }
        self.cards.append(row)
        return row

    def add_auth(self, card: dict, *, amount: int | None = None, state: str = "approved",
                 decline_code: str | None = None, minutes: int = 30,
                 at: datetime | None = None) -> dict:
        row = {
            "auth_id": self.ids.next("auth"),
            "provider_ref": self.ids.provider("au"),
            "card_id": card["card_id"],
            "amount": amount if amount is not None else minor_units(self.rng),
            "currency": "GBP",
            "merchant": merchant(self.rng),
            "mcc": str(self.rng.choice([5411, 5812, 4111, 5912, 5942])),
            "processor_state": state,
            "decline_code": decline_code,
            "authorized_at": at or self.clock.tick(minutes=minutes),
            "reversed_at": None,
            "scenario_id": self.scenario_id,
        }
        self.authorizations.append(row)
        return row

    def add_settlement(self, auth: dict, *, amount: int | None = None,
                       minutes: int = 90, at: datetime | None = None) -> dict:
        row = {
            "settlement_id": self.ids.next("set"),
            "provider_ref": self.ids.provider("st"),
            "auth_id": auth["auth_id"],
            "amount": amount if amount is not None else auth["amount"],
            "currency": auth["currency"],
            "settled_at": at or self.clock.tick(minutes=minutes),
            "scenario_id": self.scenario_id,
        }
        self.settlements.append(row)
        return row

    def add_entry(self, account: dict, *, amount: int, direction: str = "debit",
                  reference_type: str = "settlement", reference_id: str | None = None,
                  minutes: int = 5, at: datetime | None = None) -> dict:
        row = {
            "entry_id": self.ids.next("le"),
            "account_id": account["account_id"],
            "direction": direction,
            "amount": amount,
            "currency": account["currency"],
            "reference_type": reference_type,
            "reference_id": reference_id,
            "posted_at": at or self.clock.tick(minutes=minutes),
            "scenario_id": self.scenario_id,
        }
        self.entries.append(row)
        return row

    def add_alert(self, customer: dict, *, rule_code: str, severity: str = "high",
                  status: str = "open", transaction_id: str | None = None,
                  minutes: int = 10) -> dict:
        row = {
            "alert_id": self.ids.next("alr"),
            "customer_id": customer["customer_id"],
            "transaction_id": transaction_id,
            "rule_code": rule_code,
            "severity": severity,
            "status": status,
            "raised_at": self.clock.tick(minutes=minutes),
            "scenario_id": self.scenario_id,
        }
        self.alerts.append(row)
        return row

    # Deliveries that FAILED. Deliberately the only delivery builder left.
    #
    # A delivery the pipeline handled — processed or deduplicated — is a consequence
    # and must come from `publish()`. A delivery that never got handled is not: the
    # consumer's contract is that a handler exception is naked and redelivered, so
    # it cannot record its own failure without pretending to have survived it.
    # Modelling retry storms properly means poison-message handling in the bus,
    # which is a capability this migration deliberately does not add.
    #
    # Restricted to failure statuses so that closing that gap later is a change
    # here, not a silent return of hand-authored success paths.
    _FAILED_STATUSES = frozenset({"retrying", "failed"})

    def add_failed_delivery(self, *, provider_event_id: str, event_type: str,
                            attempt: int = 1, status: str = "failed",
                            payload: dict | None = None, minutes: int = 2) -> dict:
        if status not in self._FAILED_STATUSES:
            raise ValueError(
                f"add_failed_delivery is for undelivered events only, got {status!r}. "
                "A delivery the pipeline handled must come from publish()."
            )
        row = {
            "delivery_id": self.ids.next("dlv"),
            "provider_event_id": provider_event_id,
            "event_type": event_type,
            "payload_hash": digest(payload or {"e": provider_event_id}),
            "idempotency_key": None,
            "attempt": attempt,
            "status": status,
            "received_at": self.clock.tick(minutes=minutes),
            "scenario_id": self.scenario_id,
        }
        self.deliveries.append(row)
        return row

    def add_case(self, *, category: str, summary: str, subject_ids: dict[str, str]) -> dict:
        row = {
            "case_id": self.ids.next("case"),
            "category": category,
            "subject_ids": subject_ids,
            "summary": summary,
            "status": "open",
            "opened_at": self.clock.tick(hours=2),
            "scenario_id": self.scenario_id,
        }
        self.cases.append(row)
        return row
