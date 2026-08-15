"""Pure replay of the consumer pipeline, without a broker or a database.

Why this exists. Once the generator publishes events instead of inserting rows, the
rows a scenario produces are decided by the consumers — but the scenario's manifest
has to name some of those rows as required evidence, and the manifest is built before
anything is published. There are only three ways out of that:

  1. Read the ids back out of Postgres after materialising. Makes generation
     non-pure, makes `--dry-run` need a database, and makes the determinism tests
     need one too.
  2. Re-derive the ids in the generator by hand. Two implementations of the same
     rules, guaranteed to drift, and the drift surfaces as an unwinnable eval case
     — the exact failure mode that has cost the most time on this project.
  3. Run the real decision functions against an in-memory sink. This file.

So this is not a second implementation: `normalize`, `delivery_row`,
`normalized_row` and `entry_row` are imported from the services that own them. Only
the sink differs. `test_projection_matches_the_live_pipeline` pins the two together
against a real Postgres so a divergence fails loudly rather than silently capping a
scenario class.

The dedupe ledger is modelled as a set rather than the table. Equivalent per
scenario: dedupe keys embed the scenario seed, so no two scenarios can collide, and
a projection only ever covers one scenario.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from services.integration_service.consumer import (
    delivery_row,
    normalize,
    normalized_row,
)
from services.ledger_service.consumer import entry_row

from .envelope import ProviderEvent


@dataclass
class Projection:
    """The rows a sequence of published events will cause the pipeline to write."""

    deliveries: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    entries: list[dict] = field(default_factory=list)

    def ids(self) -> set[str]:
        return (
            {r["delivery_id"] for r in self.deliveries}
            | {r["event_id"] for r in self.events}
            | {r["entry_id"] for r in self.entries}
        )


def project(published: Iterable[ProviderEvent], mapping_version: int = 4) -> Projection:
    """Replay `published` through the real consumer logic, in publish order.

    Publish order is the argument order — the same order the generator will use on
    the bus. S07's race is an inversion of this list, so it is reproduced here too.
    """
    out = Projection()
    seen: set[str] = set()

    for event in published:
        deduped = event.has_safe_idempotency and event.dedupe_key in seen
        out.deliveries.append(delivery_row(event, "deduplicated" if deduped else "processed"))
        if deduped:
            continue
        if event.has_safe_idempotency:
            seen.add(event.dedupe_key)

        domain, recognised = normalize(event, mapping_version)
        out.events.append(normalized_row(event, domain, recognised))

        row, _ = entry_row(domain)
        if row is not None:
            out.entries.append(row)

    return out
