"""Render the R6 report's tables (markdown) from the offline analysis JSONs.

    r6_report_tables.py --dev learning/registry/r6/analysis/dev.json --test learning/registry/r6/analysis/test.json

Pure formatting: every number comes from scripts/r6_analysis.py output; nothing is recomputed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _s(x, nd=1):
    if x is None:
        return "—"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def summary_table(a: dict) -> str:
    arms = list(a["arms"]) + ["frontier"]
    S = dict(a["summary"]); S["frontier"] = a["strong_summary"]
    n = a["strong_summary"]["n"]
    rows = [("strict all-pass", lambda s: f"{s['all_pass']}/{n} ({100*s['all_pass']/n:.1f}%)"),
            ("root cause correct", lambda s: str(s["root_cause_correct"])),
            ("action acceptable", lambda s: str(s["action_acceptable"])),
            ("evidence recall ≥ 0.8", lambda s: str(s["evidence_ok"])),
            ("verifier passed", lambda s: str(s["verifier_passed"])),
            ("no-output (cap / schema)", lambda s: f"{s['no_output']} ({s['cap_hits']} / {s['schema_or_parse_failures']})"),
            ("silent (verifier-clean, wrong)", lambda s: str(s["silent"])),
            ("root-cause failures", lambda s: str(s["root_cause_failures"])),
            ("evidence failures", lambda s: str(s["evidence_failures"])),
            ("p50 / p95 wall (s)", lambda s: f"{s['p50_wall_ms']/1000:.1f} / {s['p95_wall_ms']/1000:.1f}"),
            ("output tokens p50 / sum", lambda s: f"{s['output_tokens_p50']} / {s['output_tokens_sum']}"),
            ("tok/s median", lambda s: _s(s.get("tokens_per_s_median"))),
            ("resident GPU MiB (max sample)", lambda s: _s(s.get("gpu_mem_used_mib")))]
    out = ["| metric | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    for label, f in rows:
        out.append(f"| {label} | " + " | ".join(f(S[x]) for x in arms) + " |")
    return "\n".join(out)


def r4_table(a: dict) -> str:
    out = ["| arm | R4 cascade all-pass | escalated (util.) | unnecessary | routing FN | rescued | $/success | wall p50 (s) |",
           "|---|---|---|---|---|---|---|---|"]
    n = a["strong_summary"]["n"]
    for arm, r in a["r4_replay"].items():
        out.append(f"| {arm} | {r['cascade_all_pass']}/{n} | {r['escalated']} ({100*r['utilization']:.1f}%) | "
                   f"{r['unnecessary']} | {r['routing_fn']} | {r['rescued']} | {_s(r['cost_per_success'],4)} | "
                   f"{r['wall_p50_ms']/1000:.1f} |")
    return "\n".join(out)


def oracle_table(a: dict) -> str:
    out = ["| arm | local-safe | rescueable | unresolved | oracle all-pass | oracle utilization |", "|---|---|---|---|---|---|"]
    for arm, o in a["post_answer_oracle"].items():
        out.append(f"| {arm} | {o['local_safe']} | {o['rescueable']} | {o['unresolved']} | {o['oracle_all_pass']}/{o['n']} | {100*o['oracle_utilization']:.1f}% |")
    return "\n".join(out)


def pairwise_table(a: dict) -> str:
    out = ["| pair (A vs B) | both | A-only | B-only | neither | relation |", "|---|---|---|---|---|---|"]
    for pair, p in a["pairwise"]["pairs"].items():
        rel = "A dominates B" if p["a_dominates_b"] else "B dominates A" if p["b_dominates_a"] else (
            "complementary" if p["a_only"] and p["b_only"] else "equal")
        out.append(f"| {pair} | {p['both_pass']} | {p['a_only']} | {p['b_only']} | {p['both_fail']} | {rel} |")
    return "\n".join(out)


def unique_table(a: dict) -> str:
    out = ["| arm | unique successes among locals | unique incl. frontier |", "|---|---|---|"]
    for arm in a["unique_successes_among_locals"]:
        u1 = a["unique_successes_among_locals"][arm]["unique_successes"]
        u2 = a["unique_successes_incl_frontier"][arm]["unique_successes"]
        out.append(f"| {arm} | {u1} | {u2} |")
    fr = a["unique_successes_incl_frontier"]["frontier"]["unique_successes"]
    out.append(f"| frontier | — | {fr} |")
    return "\n".join(out)


def tiers_table(a: dict) -> str:
    out = ["| ordering (cheapest first → frontier) | first-pass by tier | covered / n |", "|---|---|---|"]
    for order, t in a["tiers"].items():
        fp = ", ".join(f"{k}: {v}" for k, v in t["first_pass_by_tier"].items())
        out.append(f"| {order} → frontier | {fp} | {t['coverage']}/{t['n']} |")
    return "\n".join(out)


def by_class_table(a: dict) -> str:
    arms = list(next(iter(a["by_class"].values())).keys())
    out = ["| class | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    for cls, d in a["by_class"].items():
        out.append(f"| {cls} | " + " | ".join(str(d[x]) for x in arms) + " |")
    return "\n".join(out)


def fail_table(a: dict) -> str:
    arms = list(a["fail_patterns"])
    pats = sorted({p for arm in arms for p in a["fail_patterns"][arm]})
    out = ["| failure pattern | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    for p in pats:
        out.append(f"| {p} | " + " | ".join(str(a["fail_patterns"][arm].get(p, 0)) for arm in arms) + " |")
    return "\n".join(out)


def render(a: dict) -> str:
    parts = [f"### {a['split'].upper()} — arms {a['arms']} vs frontier `{a['strong']}`",
             "**Quality / failure shape / runtime**", summary_table(a),
             "**Failure patterns**", fail_table(a),
             "**Unchanged R4 verifier cascade (offline replay)**", r4_table(a),
             "**Post-answer ideal oracle vs frontier**", oracle_table(a),
             "**Pairwise pass sets**", pairwise_table(a),
             "**Unique successes**", unique_table(a),
             "**Tier coverage (cheapest-sufficient)**", tiers_table(a),
             "**All-pass by class**", by_class_table(a)]
    return "\n\n".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev")
    ap.add_argument("--test")
    args = ap.parse_args()
    for path in (args.dev, args.test):
        if path:
            print(render(json.loads(Path(path).read_text())))
            print()


if __name__ == "__main__":
    main()
