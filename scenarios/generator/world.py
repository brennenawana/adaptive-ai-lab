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


class Ids:
    """Short, readable, deterministic ids.

    Every entity gets both an internal id and a provider-native one. The mismatch
    between the two id spaces is realistic and is what S09 exercises.
    """

    def __init__(self, rng: Random) -> None:
        self._rng = rng
        self._counters: dict[str, int] = {}

    def next(self, prefix: str) -> str:
        n = self._counters.get(prefix, 0) + 1
        self._counters[prefix] = n
        return f"{prefix}_{n:03d}{self._rng.randint(100, 999)}"

    def provider(self, vendor_prefix: str) -> str:
        return f"{vendor_prefix}-{self._rng.randint(10**7, 10**8 - 1)}"


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
    """Accumulates rows for one scenario, then hands them to the writer.

    Nothing here touches the database — keeping generation pure makes it testable
    without Postgres and makes a dry run genuinely free.
    """

    scenario_id: str
    seed: int
    rng: Random
    clock: Clock
    ids: Ids

    customers: list[dict] = field(default_factory=list)
    verifications: list[dict] = field(default_factory=list)
    accounts: list[dict] = field(default_factory=list)
    entries: list[dict] = field(default_factory=list)
    cards: list[dict] = field(default_factory=list)
    authorizations: list[dict] = field(default_factory=list)
    settlements: list[dict] = field(default_factory=list)
    alerts: list[dict] = field(default_factory=list)
    deliveries: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    cases: list[dict] = field(default_factory=list)

    # --- builders ---------------------------------------------------------------

    def add_customer(self, state: str = "active") -> dict:
        name, dob, country = person(self.rng)
        row = {
            "customer_id": self.ids.next("cus"),
            "display_name": name,
            "dob": dob,
            "country": country,
            "onboarding_state": state,
            "created_at": self.clock.tick(days=-30),
            "scenario_id": self.scenario_id,
        }
        self.customers.append(row)
        return row

    def add_verification(self, customer: dict, *, check_type: str, status: str,
                         reason_code: str | None = None, minutes: int = 5) -> dict:
        row = {
            "verification_id": self.ids.next("ver"),
            "provider_ref": self.ids.provider("vs"),
            "customer_id": customer["customer_id"],
            "vendor": vendor(self.rng),
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
            "opened_at": self.clock.tick(days=-29),
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
            "issued_at": self.clock.tick(days=-28) if status != "not_issued" else None,
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

    def add_delivery(self, *, provider_event_id: str, event_type: str, attempt: int = 1,
                     status: str = "processed", idempotency_key: str | None = None,
                     payload: dict | None = None, minutes: int = 2) -> dict:
        row = {
            "delivery_id": self.ids.next("dlv"),
            "provider_event_id": provider_event_id,
            "event_type": event_type,
            "payload_hash": digest(payload or {"e": provider_event_id}),
            "idempotency_key": idempotency_key,
            "attempt": attempt,
            "status": status,
            "received_at": self.clock.tick(minutes=minutes),
            "scenario_id": self.scenario_id,
        }
        self.deliveries.append(row)
        return row

    def add_event(self, *, provider_event_id: str, normalized_type: str,
                  normalized_state: str, raw_payload: dict, mapping_version: int = 4,
                  delivery: dict | None = None, minutes: int = 1) -> dict:
        row = {
            "event_id": self.ids.next("evt"),
            "provider_event_id": provider_event_id,
            "delivery_id": delivery["delivery_id"] if delivery else None,
            "normalized_type": normalized_type,
            "mapping_version": mapping_version,
            "raw_payload": raw_payload,
            "normalized_state": normalized_state,
            "created_at": self.clock.tick(minutes=minutes),
            "scenario_id": self.scenario_id,
        }
        self.events.append(row)
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
