"""Generate scenarios and write them to Postgres.

Splits are disjoint SEED RANGES, not a shuffle. The guide's rule is "frozen
train/dev/test seeds — do not tune against the test set"; allocating by range makes
leakage structurally impossible rather than a thing you have to remember. A scenario
family cannot drift across the boundary because its seed determines its split.

Writing a scenario has two halves, and they are not the same kind of thing:

  * **State is inserted.** Customers, accounts, cards, authorizations, settlements,
    verifications, alerts and cases are what each service independently knows. No
    event produced them.
  * **Consequences are published.** Webhook deliveries, normalized integration
    events and ledger entries are written by the consumers, reached through NATS.
    `webhook.deliveries` and `integration.events` are absent from `_TABLES` on
    purpose — the writer cannot insert them even if a builder tried.

Publish-then-drain, one event at a time, awaiting consumer acknowledgement before
the next publish. Slower than fire-and-forget and deliberately so: see the reasoning
in `fis_platform/events/bus.py`. Ordering hazards come from the order a builder
publishes in, never from what the scheduler happens to do.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from random import Random

import psycopg
from psycopg.types.json import Jsonb

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fis_platform.events.bus import DOMAIN_STREAM, WEBHOOK_STREAM, EventBus  # noqa: E402
from fis_platform.events.envelope import Subject  # noqa: E402
from fis_platform.events.projection import project  # noqa: E402
from scenarios.generator import catalog  # noqa: E402,F401  (registers builders)
from scenarios.generator.catalog import BUILDERS  # noqa: E402
from scenarios.generator.world import EPOCH, Clock, Ids, World  # noqa: E402
from services.integration_service.consumer import IntegrationConsumer  # noqa: E402
from services.ledger_service.consumer import LedgerConsumer  # noqa: E402

WEBHOOK_SUBJECT = f"{Subject.WEBHOOK_RECEIVED}.>"
DOMAIN_SUBJECT = f"{Subject.DOMAIN_NORMALIZED}.>"
INTEGRATION_DURABLE = "integration-service"
LEDGER_DURABLE = "ledger-service"

SPLIT_RANGES = {
    "train": (1_000_000, 1_999_999),
    "dev":   (2_000_000, 2_999_999),
    "test":  (3_000_000, 3_999_999),
}


def split_for_seed(seed: int) -> str:
    for name, (lo, hi) in SPLIT_RANGES.items():
        if lo <= seed <= hi:
            return name
    raise ValueError(f"seed {seed} falls outside every split range — refusing to guess")


SPLIT_INDEX = {"train": 0, "dev": 1, "test": 2}

# Wider than the longest scenario span. Distractor activity reaches ~22 hours past a
# scenario's start, so a slot has to clear that with room for the vendor window on
# either side or two scenarios could still meet in the middle.
SCENARIO_SLOT = timedelta(hours=48)
_SLOTS_PER_SPLIT = 1000  # caps a split at 1000 scenarios; the corpus uses 144


def scenario_epoch(seed: int) -> datetime:
    """Each scenario gets its own slot on the timeline.

    Every scenario used to start at the same instant, which was harmless while every
    tool was keyed by a scenario-unique id. It stops being harmless the moment a tool
    can ask a question scoped by TIME rather than by entity: `get_verifications` with
    a vendor window would sweep in all 288 scenarios at once, so S04's outage cluster
    would be unreadable and every other class would appear to have one.

    Slots are packed by (split, per-class index, class index) rather than by raw
    seed, which would spread 3 million slots over geological time. Packed, the whole
    corpus fits in about a decade of simulated wall time.
    """
    split = split_for_seed(seed)
    lo, _ = SPLIT_RANGES[split]
    rel = seed - lo
    slot = SPLIT_INDEX[split] * _SLOTS_PER_SPLIT + (rel // 1000) * len(BUILDERS) + (rel % 1000)
    return EPOCH + SCENARIO_SLOT * slot


def build(code: str, seed: int) -> tuple[World, dict]:
    if code not in BUILDERS:
        raise KeyError(f"unknown scenario {code!r}; known: {sorted(BUILDERS)}")
    rng = Random(seed)
    # The FULL seed, not seed % 100_000 — the modulo made train seed 1_000_000 and
    # test seed 3_000_000 both render as "S01-00000", colliding a training scenario
    # with a test one on the primary key and quietly breaking the split boundary.
    scenario_id = f"{code}-{seed:07d}"
    world = World(scenario_id=scenario_id, seed=seed, rng=rng,
                  clock=Clock(base=scenario_epoch(seed)), ids=Ids(rng, seed))
    manifest = BUILDERS[code](world)
    manifest |= {
        "scenario_id": scenario_id,
        "seed": seed,
        "split": split_for_seed(seed),
    }
    return world, manifest


# Authoritative service state only.
#
# `integration.events` is absent because nothing may hand-author a normalized event
# — that is the mapper's output and the mapper is the thing under test. `ledger.
# entries` is absent since Suite v3: every posting, including S11's already-reconciled
# background, is a consequence the ledger consumer writes, and
# `test_no_scenario_hand_authors_ledger_entries` fails loudly if a builder grows a
# way to write one again.
#
# `webhook.deliveries` is here for exactly one reason: a delivery that FAILED cannot
# be recorded by the consumer that failed to handle it. See `World.add_failed_delivery`.
_TABLES = [
    ("customer.customers", "customers"),
    ("identity.verifications", "verifications"),
    ("ledger.accounts", "accounts"),
    ("processor.cards", "cards"),
    ("processor.authorizations", "authorizations"),
    ("processor.settlements", "settlements"),
    ("risk.alerts", "alerts"),
    ("webhook.deliveries", "deliveries"),
    ("cases.cases", "cases"),
]

# Emptied before a regeneration, children first. The corpus is a frozen artefact:
# regenerating on top of an old one collides primary keys, and a surviving dedupe
# ledger would make S01's FIRST delivery look like a duplicate.
_RESET_TABLES = [
    "ground_truth.scenario_manifests",
    "cases.cases",
    "integration.events",
    "integration.dedupe_ledger",
    "webhook.deliveries",
    "risk.alerts",
    "ledger.entries",
    "processor.settlements",
    "processor.authorizations",
    "processor.cards",
    "ledger.accounts",
    "identity.verifications",
    "customer.customers",
]

_JSON_COLS = {"subject_ids", "raw_payload"}


def write(conn: psycopg.Connection, world: World, manifest: dict) -> None:
    with conn.cursor() as cur:
        for table, attr in _TABLES:
            rows = getattr(world, attr)
            if not rows:
                continue
            cols = list(rows[0].keys())
            placeholders = ", ".join(["%s"] * len(cols))
            sql = f'INSERT INTO {table} ({", ".join(cols)}) VALUES ({placeholders})'
            cur.executemany(
                sql,
                [
                    tuple(Jsonb(r[c]) if c in _JSON_COLS else r[c] for c in cols)
                    for r in rows
                ],
            )

        cur.execute(
            """
            INSERT INTO ground_truth.scenario_manifests
              (scenario_id, seed, split, category, root_cause, required_evidence,
               acceptable_next_actions, forbidden_claims, distractor_event_ids,
               case_id, subject_ids)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (scenario_id) DO NOTHING
            """,
            (
                manifest["scenario_id"], manifest["seed"], manifest["split"],
                manifest["category"], manifest["root_cause"],
                manifest["required_evidence"], manifest["acceptable_next_actions"],
                manifest["forbidden_claims"], manifest["distractor_event_ids"],
                manifest["case_id"], Jsonb(manifest["subject_ids"]),
            ),
        )


async def materialise(bus: EventBus, world: World, conn: psycopg.Connection) -> tuple[int, int]:
    """Publish this scenario's events and block until the consumers have acked them.

    One event in flight at a time. Each publish is followed by a drain that waits for
    the integration consumer to acknowledge it, and each normalized event it emits is
    published and drained to the ledger consumer before the next provider event goes
    out. Nothing is concurrent, so nothing is timing-dependent.

    The integration consumer is rebuilt per scenario, and its mapper version is set
    per event from the schedule the builder recorded (`World.mapping_versions`) —
    S09 runs at v2 throughout, S06 runs at v3 for the injected settlement and at v4
    for its background. The dedupe ledger lives in Postgres rather than in the
    consumer, so dedupe state correctly survives that.
    """
    integration = IntegrationConsumer(conn, mapping_version=world.mapping_version)
    ledger = LedgerConsumer(conn)

    for event, version in zip(world.published, world.mapping_versions, strict=True):
        integration.mapping_version = version
        await bus.publish_provider_event(event)
        await bus.drain(stream=WEBHOOK_STREAM, subject=WEBHOOK_SUBJECT,
                        durable=INTEGRATION_DURABLE, handler=integration.handle, expect=1)

        for domain in integration.take_emitted():
            await bus.publish_domain_event(domain)
            await bus.drain(stream=DOMAIN_STREAM, subject=DOMAIN_SUBJECT,
                            durable=LEDGER_DURABLE, handler=ledger.handle, expect=1)

    # The manifest's required evidence was named from `project()` before anything was
    # published. If the live pipeline just wrote a different set of rows, the manifest
    # now points at ids that do not exist and the class is unwinnable for a reason no
    # score would explain. Fail here instead, where the cause is obvious.
    expected = project(world.published, world.mapping_versions).ids()
    actual = set(integration.wrote_deliveries) | set(integration.wrote_events) | set(ledger.posted)
    if expected != actual:
        raise RuntimeError(
            f"{world.scenario_id}: projection and live pipeline disagree. "
            f"projected-only={sorted(expected - actual)} live-only={sorted(actual - expected)}"
        )

    return len(ledger.posted), len(world.published)


def reset(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE {', '.join(_RESET_TABLES)} CASCADE")


async def generate(plan: list[tuple[str, int]], dsn: str, nats_url: str,
                   do_reset: bool) -> tuple[int, int]:
    posted = published = 0
    with psycopg.connect(dsn) as conn:
        async with EventBus(nats_url) as bus:
            if do_reset:
                reset(conn)
                await bus.purge()

            for code, seed in plan:
                world, manifest = build(code, seed)
                write(conn, world, manifest)          # state first — entries FK accounts
                p, n = await materialise(bus, world, conn)
                posted += p
                published += n

            # architecture.md: a generation run is complete only when consumer lag is
            # zero. A partially-materialised world must never be scoreable.
            for stream, durable in ((WEBHOOK_STREAM, INTEGRATION_DURABLE),
                                    (DOMAIN_STREAM, LEDGER_DURABLE)):
                lag = await bus.pending(stream, durable)
                if lag:
                    raise RuntimeError(
                        f"{stream}/{durable} still has {lag} unacknowledged messages — "
                        "the corpus is only partly materialised and must not be scored"
                    )
        conn.commit()
    return published, posted


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate FIS scenarios.")
    ap.add_argument("--split", choices=list(SPLIT_RANGES), default="test")
    ap.add_argument("--per-class", type=int, default=1,
                    help="Scenarios per class. 12 classes, so total = 12 x this.")
    ap.add_argument("--dsn", default=os.environ.get(
        "FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis"))
    ap.add_argument("--nats-url", default=os.environ.get(
        "FIS_NATS_URL", "nats://127.0.0.1:4222"))
    ap.add_argument("--dry-run", action="store_true",
                    help="Build in memory and print counts without touching Postgres.")
    ap.add_argument("--reset", action="store_true",
                    help="Truncate the corpus and purge the streams first. Required "
                         "when regenerating: the frozen corpus is replaced, not added to.")
    args = ap.parse_args()

    lo, _ = SPLIT_RANGES[args.split]
    codes = sorted(BUILDERS)
    plan = [
        (code, lo + i * 1000 + idx)
        for idx, code in enumerate(codes)
        for i in range(args.per_class)
    ]

    if args.dry_run:
        total = events = 0
        for code, seed in plan:
            world, manifest = build(code, seed)
            n = sum(len(getattr(world, a)) for _, a in _TABLES)
            total += n
            events += len(world.published)
            print(f"{manifest['scenario_id']:>14}  {manifest['root_cause']:<34} "
                  f"state={n:<4} published={len(world.published):<3} "
                  f"evidence={len(manifest['required_evidence'])}")
        print(f"\n{len(plan)} scenarios, {total} state rows, {events} published events "
              "(dry run — nothing written, nothing published)")
        return

    published, posted = asyncio.run(
        generate(plan, args.dsn, args.nats_url, do_reset=args.reset))

    print(f"wrote {len(plan)} scenarios to split={args.split}: "
          f"{published} events published, {posted} ledger entries materialised")


if __name__ == "__main__":
    main()
