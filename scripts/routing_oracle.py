"""R2 — paired weak/strong opportunity map (the routing oracle).

Before inventing a router, measure how much routing opportunity exists. Join a weak
arm and a strong arm by scenario id and classify every paired case:

    weak pass / strong pass   weak is sufficient          -> ideal cheap coverage
    weak fail / strong pass   strong can rescue           -> a router must escalate these
    weak pass / strong fail   model diversity / inversion -> inspect the harness first
    weak fail / strong fail   neither solves it           -> system/capability work

From that: the theoretical safe-local rate (a perfect router keeps these local), the
rescueable escalation rate, the oracle's quality (all-pass under a router that always
knew), the oracle strong-call minimum, and the both-fail floor no router can lift.

This is a SELECTION tool: it exists to design a routing policy, so it runs on the
dev split. It refuses the test split unless told explicitly, and even then only to
report a policy already chosen elsewhere — pairing on test and then designing from
it is tuning against the test set with extra steps.

Nothing here reads gold labels as *features*; it reads persisted scores, which is
what a scorer is for.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")

DIMENSIONS = ("root_cause_correct", "next_action_acceptable", "verifier_passed")


def _load(conn, run_id: str) -> dict[str, dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT cs.scenario_id, cs.all_pass, cs.payload, m.split, m.category
               FROM learning.case_scores cs
               JOIN ground_truth.scenario_manifests m USING (scenario_id)
               WHERE cs.run_id = %s""",
            (run_id,),
        )
        rows = cur.fetchall()
    if not rows:
        raise SystemExit(f"run {run_id!r} has no persisted scores")
    return {r["scenario_id"]: r for r in rows}


def _cell(weak_pass: bool, strong_pass: bool) -> str:
    return {
        (True, True): "weak-pass/strong-pass",
        (False, True): "weak-fail/strong-pass",
        (True, False): "weak-pass/strong-fail",
        (False, False): "both-fail",
    }[(weak_pass, strong_pass)]


def _pct(n: int, d: int) -> str:
    return "  n/a" if not d else f"{100.0 * n / d:5.1f}%"


def _dim_fail_reasons(p: dict) -> list[str]:
    out = []
    if not p["root_cause_correct"]:
        out.append("rc")
    if p["required_evidence_recall"] < p.get("evidence_recall_threshold", 0.8):
        out.append(f"ev={p['required_evidence_recall']:.2f}")
    if p["unsupported_claims"]:
        out.append(f"unsup={p['unsupported_claims']}")
    if not p["next_action_acceptable"]:
        out.append("act")
    if not p["verifier_passed"]:
        out.append("ver")
    if p.get("forbidden_claim_made"):
        out.append("FORBIDDEN")
    if not out:
        out.append("no-output" if any(d["name"] == "produced_output"
                                     for d in p.get("dimensions", [])) else "-")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="R2 paired weak/strong oracle analysis")
    ap.add_argument("--weak", required=True, help="run_id of the weak / local arm")
    ap.add_argument("--strong", required=True, help="run_id of the strong / frontier arm")
    ap.add_argument("--split", default="dev", choices=["dev", "test", "train"])
    ap.add_argument("--allow-test", action="store_true",
                    help="Required to run on the test split. Reporting only — a policy "
                         "designed from this output on test is tuned against test.")
    ap.add_argument("--json-out", help="Write the full paired table here (default: "
                                       "evals/reports/routing-oracle-<weak>-vs-<strong>.json)")
    args = ap.parse_args()

    if args.split == "test" and not args.allow_test:
        raise SystemExit("refusing to pair on the test split without --allow-test: the "
                         "oracle map is a selection tool and selection happens on dev")

    with psycopg.connect(DSN) as conn:
        weak = _load(conn, args.weak)
        strong = _load(conn, args.strong)

    for name, rows in (("weak", weak), ("strong", strong)):
        splits = {r["split"] for r in rows.values()}
        if splits != {args.split}:
            raise SystemExit(f"{name} run {getattr(args, name)!r} scored scenarios in splits "
                             f"{sorted(splits)}, expected only {args.split!r}")

    common = sorted(set(weak) & set(strong))
    only_w, only_s = sorted(set(weak) - set(strong)), sorted(set(strong) - set(weak))
    if only_w or only_s:
        print(f"WARNING: unpaired scenarios dropped — weak-only {len(only_w)}, "
              f"strong-only {len(only_s)}. Both runs should be complete before trusting "
              f"the rates below.")
    n = len(common)
    if not n:
        raise SystemExit("no paired scenarios")

    paired = []
    cells: Counter[str] = Counter()
    by_class: dict[str, Counter] = defaultdict(Counter)
    for sid in common:
        w, s = weak[sid], strong[sid]
        cell = _cell(w["all_pass"], s["all_pass"])
        cells[cell] += 1
        by_class[sid[:3]][cell] += 1
        paired.append({
            "scenario_id": sid, "class": sid[:3], "category": w["category"], "cell": cell,
            "weak_pass": w["all_pass"], "strong_pass": s["all_pass"],
            "weak_fail_reasons": _dim_fail_reasons(w["payload"]),
            "strong_fail_reasons": _dim_fail_reasons(s["payload"]),
            "weak_rc": w["payload"]["root_cause_correct"],
            "strong_rc": s["payload"]["root_cause_correct"],
            "weak_ms": w["payload"]["wall_ms"], "strong_ms": s["payload"]["wall_ms"],
            "weak_cost": w["payload"]["reference_cost_usd"],
            "strong_cost": s["payload"]["reference_cost_usd"],
        })

    ww, fw, wf, ff = (cells["weak-pass/strong-pass"], cells["weak-fail/strong-pass"],
                      cells["weak-pass/strong-fail"], cells["both-fail"])
    weak_pass = ww + wf
    strong_pass = ww + fw
    oracle_pass = ww + fw + wf          # a router that always knew picks whichever passes
    weak_only_cost = sum(p["weak_cost"] for p in paired)
    strong_only_cost = sum(p["strong_cost"] for p in paired)
    # Oracle cascade: weak always runs; strong runs only where weak failed.
    oracle_cost = weak_only_cost + sum(p["strong_cost"] for p in paired if not p["weak_pass"])
    oracle_ms = [p["weak_ms"] + (0 if p["weak_pass"] else p["strong_ms"]) for p in paired]

    print(f"R2 routing oracle — weak={args.weak}  strong={args.strong}  split={args.split}  n={n}\n")
    print(f"{'cell':<26}{'n':>5}{'rate':>9}   meaning")
    print("-" * 70)
    for cell, meaning in (
        ("weak-pass/strong-pass", "weak sufficient — ideal cheap coverage"),
        ("weak-fail/strong-pass", "strong can rescue — router must escalate"),
        ("weak-pass/strong-fail", "INVERSION — inspect scenario/tool/scorer before believing"),
        ("both-fail", "neither solves it — system/capability work, not routing"),
    ):
        print(f"{cell:<26}{cells[cell]:>5}{_pct(cells[cell], n):>9}   {meaning}")

    print()
    print(f"weak-only all-pass            {_pct(weak_pass, n)}  ({weak_pass}/{n})")
    print(f"strong-only all-pass          {_pct(strong_pass, n)}  ({strong_pass}/{n})")
    print(f"oracle hybrid all-pass        {_pct(oracle_pass, n)}  ({oracle_pass}/{n})  "
          f"= 1 - both-fail; the quality ceiling for ANY router over these two arms")
    print(f"theoretical safe-local rate   {_pct(weak_pass, n)}  cases a perfect router keeps local")
    print(f"rescueable escalation rate    {_pct(fw, n)}  weak fails that strong would fix")
    print(f"oracle strong-call minimum    {_pct(n - weak_pass, n)}  = 1 - safe-local "
          f"(of which {_pct(ff, n - weak_pass) if n - weak_pass else 'n/a'} would still fail)")
    print(f"hard-case rate                {_pct(ff, n)}  floor no router can lift")
    print(f"weak>strong disagreements     {wf}  (listed below if any)")
    print()
    print("reference cost (list-price equivalent, whole split):")
    print(f"  weak-only   ${weak_only_cost:8.4f}   per strict pass "
          f"{'n/a' if not weak_pass else f'${weak_only_cost / weak_pass:.4f}'}")
    print(f"  strong-only ${strong_only_cost:8.4f}   per strict pass "
          f"{'n/a' if not strong_pass else f'${strong_only_cost / strong_pass:.4f}'}")
    print(f"  oracle      ${oracle_cost:8.4f}   per strict pass "
          f"{'n/a' if not oracle_pass else f'${oracle_cost / oracle_pass:.4f}'}   "
          f"(cascade: weak always, strong on weak-fail)")
    print("latency (wall ms, per case, cascade assumption for oracle):")
    print(f"  weak-only   p50 {int(median(p['weak_ms'] for p in paired)):>7}   "
          f"strong-only p50 {int(median(p['strong_ms'] for p in paired)):>7}   "
          f"oracle p50 {int(median(oracle_ms)):>7}")

    print("\nper class:")
    print(f"{'class':<6}{'n':>3}{'w+s+':>6}{'w-s+':>6}{'w+s-':>6}{'--':>5}   weak rc  strong rc"
          f"   category")
    for cls in sorted(by_class):
        c = by_class[cls]
        cn = sum(c.values())
        wrc = sum(1 for p in paired if p["class"] == cls and p["weak_rc"])
        src = sum(1 for p in paired if p["class"] == cls and p["strong_rc"])
        cat = next(p["category"] for p in paired if p["class"] == cls)
        flag = "  <-- weak rc > strong rc: harness alarm" if wrc > src else ""
        print(f"{cls:<6}{cn:>3}{c['weak-pass/strong-pass']:>6}{c['weak-fail/strong-pass']:>6}"
              f"{c['weak-pass/strong-fail']:>6}{c['both-fail']:>5}   {wrc:>2}/{cn:<3}   "
              f"{src:>2}/{cn:<3}   {cat}{flag}")

    inversions = [p for p in paired if p["cell"] == "weak-pass/strong-fail"]
    if inversions:
        print("\nweak-pass/strong-fail — REQUIRES HARNESS REVIEW before treating as model "
              "diversity (strong arm is not bit-reproducible; check the scorer excerpt):")
        for p in inversions:
            print(f"  {p['scenario_id']:<12} {p['class']}  strong failed on: "
                  f"{', '.join(p['strong_fail_reasons'])}")

    hard = [p for p in paired if p["cell"] == "both-fail"]
    if hard:
        print("\nboth-fail:")
        for p in hard:
            print(f"  {p['scenario_id']:<12} weak: {', '.join(p['weak_fail_reasons']):<28} "
                  f"strong: {', '.join(p['strong_fail_reasons'])}")

    print("\nweak-fail/strong-pass, why the weak arm failed (what a router must detect):")
    reasons: Counter[str] = Counter()
    for p in paired:
        if p["cell"] == "weak-fail/strong-pass":
            for r in p["weak_fail_reasons"]:
                reasons[r.split("=")[0]] += 1
    for r, k in reasons.most_common():
        print(f"  {r:<12}{k:>4}")

    out = Path(args.json_out) if args.json_out else (
        ROOT / "evals" / "reports" / f"routing-oracle-{args.weak}-vs-{args.strong}.json")
    out.write_text(json.dumps({
        "weak": args.weak, "strong": args.strong, "split": args.split, "n": n,
        "cells": dict(cells),
        "weak_only_all_pass": weak_pass, "strong_only_all_pass": strong_pass,
        "oracle_all_pass": oracle_pass, "oracle_strong_calls": n - weak_pass,
        "reference_cost": {"weak_only": weak_only_cost, "strong_only": strong_only_cost,
                           "oracle": oracle_cost},
        "paired": paired,
    }, indent=2, default=str))
    print(f"\nwritten: {out}")


if __name__ == "__main__":
    main()
