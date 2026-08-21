"""R6 TRAIN pilot — a deterministic, class-stratified subset of the TRAIN split.

The R6 plan (§ 8–9) calibrates generation caps and selects the Qwen3.8 quant on a
pre-registered TRAIN pilot. `run_eval --limit N` cannot express that: it is a prefix
of `ORDER BY scenario_id`, i.e. all-S01. This script picks the first `k` scenarios of
EVERY class (S01–S12) in scenario-id order — scenario ids are `<class>-<seed>`, so
this is seed order within class — and prints the id list with its digest. No RNG, no
argument other than `k`, so the pilot is reproducible from the corpus alone.

TRAIN only. It refuses any other split by construction (the query is pinned).

    .venv/bin/python scripts/r6_pilot.py --k 3            # 36 ids + digest (JSON)
    .venv/bin/python scripts/r6_pilot.py --k 3 --ids-only  # one id per line, for --scenario-ids-file
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

from scripts.corpus_digest import corpus_digest  # noqa: E402

DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")
SPLIT = "train"


def select_pilot(conn, k: int) -> dict:
    with conn.cursor() as cur:
        cur.execute("SELECT scenario_id FROM ground_truth.scenario_manifests "
                    "WHERE split = %s ORDER BY scenario_id", (SPLIT,))
        ids = [r[0] for r in cur.fetchall()]
    by_class: dict[str, list[str]] = {}
    for sid in ids:
        by_class.setdefault(sid[:3], []).append(sid)
    picked = [sid for cls in sorted(by_class) for sid in by_class[cls][:k]]
    corpus = corpus_digest(conn)
    record = {
        "protocol": "r6-train-pilot-v1",
        "split": SPLIT, "k_per_class": k, "n_classes": len(by_class), "n": len(picked),
        "rule": "first k scenario ids of every class in ascending scenario_id (= seed) order",
        "corpus_digest": corpus["digest"], "train_digest": corpus["splits"][SPLIT],
        "scenario_ids": picked,
    }
    record["pilot_digest"] = hashlib.sha256(
        json.dumps({k_: v for k_, v in record.items()}, sort_keys=True,
                   separators=(",", ":")).encode()).hexdigest()
    return record


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--k", type=int, required=True, help="scenarios per class")
    ap.add_argument("--ids-only", action="store_true")
    ap.add_argument("--out", type=Path, help="write the JSON record here (refuses to overwrite)")
    args = ap.parse_args()
    if args.k < 1:
        raise SystemExit("--k must be >= 1")
    with psycopg.connect(DSN) as conn:
        rec = select_pilot(conn, args.k)
    if args.out:
        if args.out.exists():
            raise SystemExit(f"refusing to overwrite {args.out} — a pilot record is pre-registered once")
        args.out.write_text(json.dumps(rec, indent=2) + "\n")
        print(f"wrote {args.out}  n={rec['n']}  pilot_digest={rec['pilot_digest']}")
        return
    if args.ids_only:
        print("\n".join(rec["scenario_ids"]))
    else:
        print(json.dumps(rec, indent=2))


if __name__ == "__main__":
    main()
