"""Canonical identity of the generated corpus.

The determinism release gate (`SUITE_V3_RELEASE_CONTRACT.md` § 4) asks that two
regenerations under the same seeds and code produce the same worlds. "Same" is made
checkable here: a SHA-256 per split over every manifest, every state row and every
pipeline-caused row, serialised canonically, and one digest over the three. Anything a
model could observe or a scorer could grade is in it; the two things that legitimately
differ between regenerations are out:

  * `ground_truth.scenario_manifests.generated_at`  — wall clock;
  * `ledger.entries.posting_seq`                     — a bigserial that TRUNCATE does
    not reset, so its absolute value moves between regenerations. Its ORDER is what
    S07 depends on, so entries are digested in posting order without the value.

    .venv/bin/python scripts/corpus_digest.py                       # print
    .venv/bin/python scripts/corpus_digest.py --write FILE          # record the identity
    .venv/bin/python scripts/corpus_digest.py --check FILE          # exit 1 on mismatch

`evals/runner/run_eval.py` records `digest` in every trajectory's runtime_context, so
a run is tied to the exact corpus it was measured against.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.suite import SUITE_VERSION, git_head  # noqa: E402

DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")

# (table, order-by, columns to drop). Every table carries scenario_id.
_TABLES: list[tuple[str, str, tuple[str, ...]]] = [
    ("ground_truth.scenario_manifests", "scenario_id", ("generated_at",)),
    ("customer.customers", "customer_id", ()),
    ("identity.verifications", "verification_id", ()),
    ("ledger.accounts", "account_id", ()),
    ("ledger.entries", "posting_seq", ("posting_seq",)),
    ("processor.cards", "card_id", ()),
    ("processor.authorizations", "auth_id", ()),
    ("processor.settlements", "settlement_id", ()),
    ("risk.alerts", "alert_id", ()),
    ("webhook.deliveries", "delivery_id", ()),
    ("integration.events", "event_id", ()),
    ("integration.dedupe_ledger", "dedupe_key", ()),
    ("cases.cases", "case_id", ()),
]


def _split_ids(conn, split: str) -> list[str]:
    return [r[0] for r in conn.execute(
        "SELECT scenario_id FROM ground_truth.scenario_manifests WHERE split = %s ORDER BY scenario_id",
        (split,)).fetchall()]


def corpus_digest(conn) -> dict:
    """Per-split and overall digests plus row counts. Pure function of the tables."""
    out: dict = {"suite_version": None, "splits": {}, "rows": {}}
    versions = {r[0] for r in conn.execute(
        "SELECT DISTINCT suite_version FROM ground_truth.scenario_manifests").fetchall()}
    out["suite_version"] = sorted(versions, key=str)[0] if len(versions) == 1 else sorted(versions, key=str)
    split_digests = []
    for split in ("train", "dev", "test"):
        ids = _split_ids(conn, split)
        h = hashlib.sha256()
        counts: dict[str, int] = {}
        for table, order, drop in _TABLES:
            rows = conn.execute(
                f"SELECT row_to_json(t) FROM {table} t WHERE t.scenario_id = ANY(%s) ORDER BY {order}",
                (ids,)).fetchall()
            counts[table] = len(rows)
            for (row,) in rows:
                for col in drop:
                    row.pop(col, None)
                h.update(json.dumps(row, sort_keys=True, separators=(",", ":"), default=str).encode())
                h.update(b"\n")
        d = h.hexdigest()
        out["splits"][split] = {"scenarios": len(ids), "digest": d}
        out["rows"][split] = counts
        split_digests.append(d)
    out["digest"] = hashlib.sha256("|".join(split_digests).encode()).hexdigest()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Canonical corpus digest")
    ap.add_argument("--write", metavar="FILE", help="record suite version, digests, counts, HEAD")
    ap.add_argument("--check", metavar="FILE", help="compare against a recorded identity; exit 1 on mismatch")
    args = ap.parse_args()

    with psycopg.connect(DSN) as conn:
        ident = corpus_digest(conn)

    print(f"suite_version {ident['suite_version']}  digest {ident['digest']}")
    for split, d in ident["splits"].items():
        print(f"  {split:<6} {d['scenarios']:>4} scenarios  {d['digest']}")

    if args.write:
        record = {
            "suite_version": SUITE_VERSION,
            "corpus_digest": ident["digest"],
            "splits": ident["splits"],
            "rows": ident["rows"],
            "generator": {"per_class": {"test": 8, "dev": 4, "train": 12},
                          "seed_ranges": {"train": [1_000_000, 1_999_999],
                                          "dev": [2_000_000, 2_999_999],
                                          "test": [3_000_000, 3_999_999]}},
            "git_head": git_head(),
        }
        Path(args.write).write_text(json.dumps(record, indent=2) + "\n")
        print(f"recorded -> {args.write}")

    if args.check:
        recorded = json.loads(Path(args.check).read_text())
        same = recorded["corpus_digest"] == ident["digest"] and all(
            recorded["splits"][s]["digest"] == ident["splits"][s]["digest"] for s in ident["splits"])
        print("DETERMINISTIC — identical to the recorded identity" if same
              else f"MISMATCH — recorded {recorded['corpus_digest']} vs live {ident['digest']}")
        return 0 if same else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
