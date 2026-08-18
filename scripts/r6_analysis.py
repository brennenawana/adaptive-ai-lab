"""R6 offline system analysis (plan § 13–14, contract § 15) — one JSON per split.

Given the arms of a split (label → run id, cheapest-first order for tier coverage), compute
from Postgres only:
  per-arm summary (quality, failure shape, runtime)      scripts/r6_metrics.summarize
  unchanged R4 verifier-cascade replay vs the frontier   scripts/routing_cascade_report machinery
  post-answer ideal oracle vs the frontier               contract § 15
  pairwise A/B/C/D + dominance for every pair            scripts/r6_metrics.pairwise
  unique successes of every arm vs the union of the others
  tier-coverage orderings (cheapest-sufficient)          contract § 15 list

    r6_analysis.py --split dev --arm qwen3-8b=V3-qwen-dev --arm qwen35-9b=R6-qwen35-dev ...
                   --strong E4-v3-dev --order "qwen3-8b,qwen35-9b,qwen38-27b" [--json-out F]

Historical arms are read from their frozen runs (never rerun); nothing here writes to the
database or calls a model.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from itertools import combinations
from pathlib import Path
from statistics import median

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.suite import require_comparable  # noqa: E402
from scripts.r6_metrics import (  # noqa: E402
    load_run, pairwise, post_answer_oracle, summarize, tier_coverage,
)
from scripts.routing_cascade_report import _signals  # noqa: E402
from services.ai_orchestrator.cascade import EscalationPolicy, should_escalate  # noqa: E402

DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")


def r4_replay(weak: dict[str, dict], strong: dict[str, dict]) -> dict:
    """The unchanged deterministic verifier cascade, replayed offline on a recorded weak arm
    against the recorded frontier — the same signals the runtime gate reads (routing_cascade_report)."""
    ids = sorted(set(weak) & set(strong))
    esc, unnecessary, false_neg, rescued, final_pass, cost = [], [], [], [], 0, 0.0
    walls = []
    for sid in ids:
        w, s = weak[sid], strong[sid]
        escalated, reason = should_escalate(_signals(w), EscalationPolicy.VERIFIER)
        final = s if escalated else w
        final_pass += int(final["all_pass"])
        cost += float(w["score"]["reference_cost_usd"]) + (float(s["score"]["reference_cost_usd"]) if escalated else 0.0)
        walls.append(float(w["score"]["wall_ms"]) + (float(s["score"]["wall_ms"]) if escalated else 0.0))
        if escalated:
            esc.append(sid)
            if w["all_pass"]:
                unnecessary.append(sid)
            if final["all_pass"] and not w["all_pass"]:
                rescued.append(sid)
        elif not w["all_pass"] and s["all_pass"]:
            false_neg.append(sid)
    n = len(ids)
    return {"n": n, "cascade_all_pass": final_pass, "escalated": len(esc),
            "utilization": round(len(esc) / n, 4) if n else None,
            "unnecessary": len(unnecessary), "routing_fn": len(false_neg), "rescued": len(rescued),
            "false_negative_ids": false_neg, "unnecessary_ids": unnecessary,
            "cost_per_attempt": round(cost / n, 5) if n else None,
            "cost_per_success": round(cost / final_pass, 5) if final_pass else None,
            "wall_p50_ms": int(median(walls)) if walls else None}


def unique_successes(arms: dict[str, dict[str, dict]]) -> dict:
    out = {}
    for label, rows in arms.items():
        others = [o for o in arms if o != label]
        ids = sorted(rows)
        uniq = [s for s in ids if rows[s]["all_pass"] and not any(arms[o][s]["all_pass"] for o in others if s in arms[o])]
        out[label] = {"unique_successes": len(uniq), "ids": uniq}
    return out


def dominance_matrix(arms: dict[str, dict[str, dict]]) -> dict:
    labels = list(arms)
    mat = {}
    for a, b in combinations(labels, 2):
        p = pairwise(arms[a], arms[b])
        mat[f"{a} vs {b}"] = {k: p[k] for k in ("n", "both_pass", "a_only", "b_only", "both_fail",
                                                 "a_dominates_b", "b_dominates_a")}
    dominated = {}
    for a in labels:
        by = [b for b in labels if b != a and pairwise(arms[b], arms[a])["a_dominates_b"]]
        dominated[a] = by
    return {"pairs": mat, "dominated_by": dominated}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    ap.add_argument("--arm", action="append", required=True, help="label=run_id (local arms)")
    ap.add_argument("--strong", required=True, help="frontier run id for the split")
    ap.add_argument("--order", action="append", default=[],
                    help="comma-separated labels cheapest-first (frontier appended automatically); repeatable")
    ap.add_argument("--json-out")
    args = ap.parse_args()
    arms_spec = dict(a.split("=", 1) for a in args.arm)

    with psycopg.connect(DSN) as conn:
        require_comparable(conn, [*arms_spec.values(), args.strong])
        arms = {label: load_run(conn, rid) for label, rid in arms_spec.items()}
        strong = load_run(conn, args.strong)

    out = {"split": args.split, "arms": arms_spec, "strong": args.strong,
           "summary": {label: summarize(rows) for label, rows in arms.items()},
           "strong_summary": summarize(strong),
           "r4_replay": {label: r4_replay(rows, strong) for label, rows in arms.items()},
           "post_answer_oracle": {label: post_answer_oracle(rows, strong) for label, rows in arms.items()},
           "pairwise": dominance_matrix({**arms, "frontier": strong}),
           "unique_successes_among_locals": unique_successes(arms),
           "unique_successes_incl_frontier": unique_successes({**arms, "frontier": strong}),
           "tiers": {}}
    for order in args.order:
        labels = [x.strip() for x in order.split(",") if x.strip()]
        seq = [(lbl, arms[lbl]) for lbl in labels] + [("frontier", strong)]
        t = tier_coverage(seq)
        t.pop("per_case")
        out["tiers"][order] = t
    # per-class pass counts side by side
    classes = sorted({s[:3] for s in strong})
    out["by_class"] = {cls: {label: sum(1 for s in rows if s[:3] == cls and rows[s]["all_pass"])
                             for label, rows in {**arms, "frontier": strong}.items()} for cls in classes}
    # verifier-clean silent failures per arm (already in summary) + failure-pattern matrix
    out["fail_patterns"] = {label: out["summary"][label]["fail_patterns"] for label in arms}
    out["fail_patterns"]["frontier"] = out["strong_summary"]["fail_patterns"]
    for label in arms:      # trim id lists that only clutter the JSON
        out["summary"][label].pop("silent_ids", None)
    out["strong_summary"].pop("silent_ids", None)
    text = json.dumps(out, indent=2, default=str)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n")
        print(f"written {args.json_out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
