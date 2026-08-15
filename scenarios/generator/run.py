"""Generate scenarios and write them to Postgres.

Splits are disjoint SEED RANGES, not a shuffle. The guide's rule is "frozen
train/dev/test seeds — do not tune against the test set"; allocating by range makes
leakage structurally impossible rather than a thing you have to remember. A scenario
family cannot drift across the boundary because its seed determines its split.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from random import Random

import psycopg
from psycopg.types.json import Jsonb

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scenarios.generator import catalog  # noqa: E402,F401  (registers builders)
from scenarios.generator.catalog import BUILDERS  # noqa: E402
from scenarios.generator.world import Clock, Ids, World  # noqa: E402

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


def build(code: str, seed: int) -> tuple[World, dict]:
    if code not in BUILDERS:
        raise KeyError(f"unknown scenario {code!r}; known: {sorted(BUILDERS)}")
    rng = Random(seed)
    # The FULL seed, not seed % 100_000 — the modulo made train seed 1_000_000 and
    # test seed 3_000_000 both render as "S01-00000", colliding a training scenario
    # with a test one on the primary key and quietly breaking the split boundary.
    scenario_id = f"{code}-{seed:07d}"
    world = World(scenario_id=scenario_id, seed=seed, rng=rng, clock=Clock(),
                  ids=Ids(rng, seed))
    manifest = BUILDERS[code](world)
    manifest |= {
        "scenario_id": scenario_id,
        "seed": seed,
        "split": split_for_seed(seed),
    }
    return world, manifest


_TABLES = [
    ("customer.customers", "customers"),
    ("identity.verifications", "verifications"),
    ("ledger.accounts", "accounts"),
    ("processor.cards", "cards"),
    ("processor.authorizations", "authorizations"),
    ("processor.settlements", "settlements"),
    ("ledger.entries", "entries"),
    ("risk.alerts", "alerts"),
    ("webhook.deliveries", "deliveries"),
    ("integration.events", "events"),
    ("cases.cases", "cases"),
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


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate FIS scenarios.")
    ap.add_argument("--split", choices=list(SPLIT_RANGES), default="test")
    ap.add_argument("--per-class", type=int, default=1,
                    help="Scenarios per class. 12 classes, so total = 12 x this.")
    ap.add_argument("--dsn", default=os.environ.get(
        "FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis"))
    ap.add_argument("--dry-run", action="store_true",
                    help="Build in memory and print counts without touching Postgres.")
    args = ap.parse_args()

    lo, _ = SPLIT_RANGES[args.split]
    codes = sorted(BUILDERS)
    plan = [
        (code, lo + i * 1000 + idx)
        for idx, code in enumerate(codes)
        for i in range(args.per_class)
    ]

    if args.dry_run:
        total = 0
        for code, seed in plan:
            world, manifest = build(code, seed)
            n = sum(len(getattr(world, a)) for _, a in _TABLES)
            total += n
            print(f"{manifest['scenario_id']:>14}  {manifest['root_cause']:<34} "
                  f"rows={n:<4} evidence={len(manifest['required_evidence'])}")
        print(f"\n{len(plan)} scenarios, {total} rows (dry run — nothing written)")
        return

    with psycopg.connect(args.dsn) as conn:
        for code, seed in plan:
            world, manifest = build(code, seed)
            write(conn, world, manifest)
        conn.commit()

    print(f"wrote {len(plan)} scenarios to split={args.split}")


if __name__ == "__main__":
    main()
