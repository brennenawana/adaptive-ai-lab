"""R5 — oracle ceilings and the R4 reproduction gate (contract § 3/§ 7/§ 11, plan § 10).

Four sections, one report, per split:

  A  R4 REPRODUCTION      Replay the *unchanged* R4 `verifier` policy for both local
                          arms against the frozen frontier run, exactly as
                          `routing_cascade_report.py --weak … --strong … --policy
                          verifier` does (its `_load`, `_signals`, `_tokens` and
                          `_arm_summary` are imported, not re-derived), and check every
                          headline number against the values published in
                          `SUITE_V3_RELEASE_REPORT.md` § 6 (DEV) and § 7 (TEST).
                          A disagreement exits 2: the contract says stop and reconcile
                          before any R5 number is read.

  B  POST-ANSWER ORACLE   Plan § 10: the ideal gate keeps a passing local answer,
                          escalates a local failure the frontier can rescue, and can do
                          nothing for the rest. Ceiling on quality, floor on frontier
                          utilization — the two axes R5's Pareto plot lives on.

  C  THREE-TIER ORACLE    Qwen → Nemotron → frontier cheapest-sufficient assignment.
                          Descriptive groundwork for R6, not a policy: the assignment
                          reads outcomes, which are only known after the answer exists.

  D  SILENT-FAILURE       What the R4 blind spot is *made of*: the routing false
     ANATOMY              negatives split by which scored dimension actually failed,
                          plus the failure anatomy of the whole local run. This is the
                          target R5 is trying to learn, so it is worth naming precisely.

Everything here is an ANALYSIS-LAYER tool. It reads persisted scores and gold labels
(that is what a scorer is for) and it is *not* a router: nothing computed here is a
feature, and § 6 of the contract governs what a feature may be. No model is called.

TEST is sealed (contract § 14): `--split test` refuses without `--allow-test` and prints
a loud caveat when it is given.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from routing_cascade_report import (  # noqa: E402  — one definition of the R4 replay
    _arm_summary,
    _load,
    _signals,
    _tokens,
)

from fis_platform.suite import require_comparable  # noqa: E402
from services.ai_orchestrator.cascade import (  # noqa: E402
    EscalationPolicy,
    should_escalate,
)

ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")

# Frozen source runs (contract § 3). TRAIN has no frontier arm and no R4 replay, so it
# is not a split this report accepts.
RUNS = {
    "dev": {"qwen": "V3-qwen-dev", "nemotron": "V3-nemotron-dev", "strong": "E4-v3-dev"},
    "test": {"qwen": "V3-qwen-96", "nemotron": "V3-nemotron-96", "strong": "E4-v3-96"},
}

# Published baselines to reproduce, transcribed from SUITE_V3_RELEASE_REPORT.md.
# DEV: § 4 (weak-only all-pass) and § 6 (cascade replay). TEST: § 7 (both).
# These are the EXPECTED values; they are never adjusted to match a computed number.
EXPECTED = {
    "dev": {
        "n": 48,
        "qwen": {"weak_all_pass": 17, "cascade_all_pass": 32, "strong_calls": 15,
                 "rescue_needed": 15, "escalated": 15, "unnecessary": 0, "routing_fn": 16,
                 "cost_per_attempt": 0.0405, "cost_per_success": 0.0608, "wall_p50_s": 16.7},
        "nemotron": {"weak_all_pass": 23, "cascade_all_pass": 35, "strong_calls": 12,
                     "rescue_needed": 12, "escalated": 12, "unnecessary": 0, "routing_fn": 13,
                     "cost_per_attempt": 0.0330, "cost_per_success": 0.0453, "wall_p50_s": 54.7},
        "strong": {"all_pass": 48, "cost_per_attempt": 0.1160, "cost_per_success": 0.1160},
    },
    "test": {
        "n": 96,
        "qwen": {"weak_all_pass": 27, "cascade_all_pass": 48, "strong_calls": 22,
                 "rescue_needed": 21, "escalated": 22, "unnecessary": 0, "routing_fn": 47,
                 "cost_per_attempt": 0.0256, "cost_per_success": 0.0513, "wall_p50_s": 15.4},
        "nemotron": {"weak_all_pass": 48, "cascade_all_pass": 69, "strong_calls": 21,
                     "rescue_needed": 21, "escalated": 21, "unnecessary": 0, "routing_fn": 26,
                     "cost_per_attempt": 0.0273, "cost_per_success": 0.0380, "wall_p50_s": 56.1},
        "strong": {"all_pass": 95, "cost_per_attempt": 0.1139, "cost_per_success": 0.1139},
    },
}

COST_TOL = 0.0005   # the report rounds costs to 4 dp
WALL_TOL = 0.2      # the report rounds wall p50 to 0.1 s
ARMS = ("qwen", "nemotron")

# The release report's *prose* also splits the routing false negatives by dimension
# (§ 6: "Qwen: 10 evidence, 6 rc/action; Nemotron: 8 evidence, 5 rc"). That split is
# narrative, not a table cell, and it is checked here NON-FATALLY: it is not one of the
# headline fields the reproduction gate covers, and § 6's Qwen pair is not reproducible
# under any exclusive bucketing of the 16 FNs (see the NOTE printed in section D).
# Recorded rather than quietly dropped, because contract § 11 requires exactly this
# split ("root-cause misses, evidence misses, other") in every R5 policy report, so the
# bucketing has to be pinned down once, here.
FN_SUBSPLIT_NARRATIVE = {
    "dev": {"qwen": {"evidence": 10, "root_cause": 6}, "nemotron": {"evidence": 8, "root_cause": 5}},
    "test": {},   # § 7 states the family but publishes no sub-split
}


# ---------------------------------------------------------------------------
# pure helpers (unit-tested in tests/test_r5_oracles.py)
# ---------------------------------------------------------------------------

def evidence_short(score: dict) -> bool:
    return score["required_evidence_recall"] < score.get("evidence_recall_threshold", 0.8)


def no_output(score: dict) -> bool:
    """The scorer emits a `produced_output` dimension only when there was none."""
    return any(d["name"] == "produced_output" for d in score.get("dimensions", []))


def fn_bucket(score: dict) -> str:
    """Which dimension actually sank a verifier-clean answer.

    Buckets are ordered and exclusive: a wrong root cause dominates whatever else the
    answer got wrong, because it is a different *kind* of failure — the model reached a
    conclusion and the conclusion was false, rather than reaching the right conclusion
    with a thin citation set.
    """
    if not score["root_cause_correct"]:
        return "root_cause"
    ev, act = evidence_short(score), not score["next_action_acceptable"]
    forb = bool(score.get("forbidden_claim_made"))
    if ev and not act and not forb:
        return "evidence_only"
    if act and not ev and not forb:
        return "action_only"
    return "other"


def fail_pattern(score: dict, all_pass: bool) -> str:
    """One label per case, ordered by what a deterministic gate could see:
    no-output and verifier failures are visible, `silent:*` is the blind spot."""
    if all_pass:
        return "pass"
    if no_output(score):
        return "no-output"
    if not score["verifier_passed"]:
        return "verifier-fail(unsupported)" if score["unsupported_claims"] else "verifier-fail(other)"
    return "silent:" + fn_bucket(score)


def three_tier(qwen_pass: bool, nemotron_pass: bool, strong_pass: bool) -> str:
    """Plan § 10: cheapest tier that would have produced a passing answer."""
    if qwen_pass:
        return "qwen"
    if nemotron_pass:
        return "nemotron"
    if strong_pass:
        return "frontier"
    return "unresolved"


def said_vs_truth(score: dict) -> str | None:
    for d in score.get("dimensions", []):
        if d["name"] == "root_cause":
            return d.get("detail")
    return None


def pct(n: int, d: int) -> str:
    return "  n/a" if not d else f"{100.0 * n / d:5.1f}%"


def cmp_int(got: int, want: int) -> tuple[bool, str]:
    ok = got == want
    return ok, f"{'AGREES  ' if ok else 'DISAGREES'} got {got:<8} expected {want}"


def cmp_float(got: float, want: float, tol: float, unit: str = "") -> tuple[bool, str]:
    ok = abs(got - want) <= tol
    return ok, (f"{'AGREES  ' if ok else 'DISAGREES'} got {got:<8.4f} expected {want:.4f}"
                f"  (|Δ| {abs(got - want):.4f} vs tol {tol}{unit})")


# ---------------------------------------------------------------------------
# A — R4 replay, one local arm
# ---------------------------------------------------------------------------

def replay_r4(weak: dict, strong: dict, ids: list[str]) -> dict:
    """Exactly `routing_cascade_report.py` replay mode with policy=verifier."""
    policy = EscalationPolicy.VERIFIER
    per = []
    for sid in ids:
        w, s = weak[sid], strong[sid]
        escalated, reason = should_escalate(_signals(w), policy)
        final = s if escalated else w
        per.append({
            "scenario_id": sid, "class": sid[:3], "escalated": escalated, "reason": reason,
            "weak_pass": w["all_pass"], "strong_pass": s["all_pass"],
            "final_pass": final["all_pass"], "oracle_pass": w["all_pass"] or s["all_pass"],
        })
    n = len(per)
    esc = [p for p in per if p["escalated"]]
    acc = [p for p in per if not p["escalated"]]
    rescued_needed = [p for p in esc if p["final_pass"] and not p["weak_pass"]]
    unnecessary = [p for p in esc if p["weak_pass"]]
    false_neg = [p for p in acc if not p["weak_pass"] and p["strong_pass"]]

    W = _arm_summary([weak[sid] for sid in ids])
    S = _arm_summary([strong[sid] for sid in ids])
    C = _arm_summary([strong[p["scenario_id"]] if p["escalated"] else weak[p["scenario_id"]]
                      for p in per])
    # A cascade pays for the weak stage on every case; replay has to add it explicitly.
    C["wall_p50"] = int(median(
        weak[p["scenario_id"]]["score"]["wall_ms"]
        + (strong[p["scenario_id"]]["score"]["wall_ms"] if p["escalated"] else 0) for p in per))
    C["in_tok"] = W["in_tok"] + sum(_tokens(strong[p["scenario_id"]]["traj"])[0] for p in esc)
    C["out_tok"] = W["out_tok"] + sum(_tokens(strong[p["scenario_id"]]["traj"])[1] for p in esc)
    C["cost"] = W["cost"] + sum(strong[p["scenario_id"]]["score"]["reference_cost_usd"] for p in esc)

    return {
        "n": n, "per": per, "weak": W, "cascade": C, "strong": S,
        "escalated": len(esc), "accepted": len(acc),
        "reasons": dict(Counter(p["reason"] for p in esc)),
        "rescue_needed": len(rescued_needed), "unnecessary": len(unnecessary),
        "routing_fn": len(false_neg), "routing_fn_ids": [p["scenario_id"] for p in false_neg],
        "cost_per_attempt": C["cost"] / n,
        "cost_per_success": (C["cost"] / C["all_pass"]) if C["all_pass"] else None,
        "wall_p50_s": C["wall_p50"] / 1000.0,
    }


def report_reproduction(split: str, arms: dict, strong_summary: dict, n: int) -> tuple[bool, dict]:
    exp = EXPECTED[split]
    print("=" * 100)
    print(f"A. R4 REPRODUCTION — unchanged `verifier` policy replayed against the frozen "
          f"frontier run  (split={split}, n={n})")
    print("=" * 100)
    if n != exp["n"]:
        print(f"  !! n={n} but the release report is over n={exp['n']}")

    hdr = (f"{'arm':<12}{'weak-only':>11}{'cascade':>10}{'strong calls':>14}{'rescue':>9}"
           f"{'unnec':>7}{'FN':>5}{'$/attempt':>11}{'$/success':>11}{'wall p50':>10}")
    print("\n" + hdr)
    print("-" * len(hdr))
    for name in ARMS:
        r = arms[name]
        print(f"{name:<12}"
              f"{f'{r['weak']['all_pass']}/{n}':>11}"
              f"{f'{r['cascade']['all_pass']}/{n}':>10}"
              f"{f'{r['escalated']} ({100.0 * r['escalated'] / n:.1f}%)':>14}"
              f"{f'{r['rescue_needed']}/{r['escalated']}':>9}"
              f"{r['unnecessary']:>7}{r['routing_fn']:>5}"
              f"{'$' + format(r['cost_per_attempt'], '.4f'):>11}"
              f"{('$' + format(r['cost_per_success'], '.4f')) if r['cost_per_success'] else 'n/a':>11}"
              f"{format(r['wall_p50_s'], '.1f') + ' s':>10}")
    S = strong_summary
    print(f"{'strong-only':<12}{'—':>11}{'—':>10}{f'{n} (100.0%)':>14}{'—':>9}{'—':>7}{'—':>5}"
          f"{'$' + format(S['cost'] / n, '.4f'):>11}"
          f"{'$' + format(S['cost'] / S['all_pass'], '.4f'):>11}"
          f"{format(S['wall_p50'] / 1000.0, '.1f') + ' s':>10}   all-pass "
          f"{S['all_pass']}/{n}")
    for name in ARMS:
        print(f"  {name} escalation reasons: {arms[name]['reasons']}   "
              f"weak-stage reference cost ${arms[name]['weak']['cost']:.4f} (local = $0)")
    print("  strong reference cost is a FLOOR: the CLI under-reports input tokens.")

    print(f"\ncheck against SUITE_V3_RELEASE_REPORT.md "
          f"{'§ 4 + § 6' if split == 'dev' else '§ 7'}  "
          f"(costs ±${COST_TOL}, wall ±{WALL_TOL} s)\n")
    ok_all = True
    checks: dict[str, dict] = {}
    for name in ARMS:
        r, e = arms[name], exp[name]
        rows = [
            ("weak-only all-pass", *cmp_int(r["weak"]["all_pass"], e["weak_all_pass"])),
            ("cascade all-pass", *cmp_int(r["cascade"]["all_pass"], e["cascade_all_pass"])),
            ("strong calls", *cmp_int(r["escalated"], e["strong_calls"])),
            ("rescue (needed)", *cmp_int(r["rescue_needed"], e["rescue_needed"])),
            ("rescue (of escalated)", *cmp_int(r["escalated"], e["escalated"])),
            ("unnecessary escalation", *cmp_int(r["unnecessary"], e["unnecessary"])),
            ("routing FN", *cmp_int(r["routing_fn"], e["routing_fn"])),
            ("cost / attempt", *cmp_float(r["cost_per_attempt"], e["cost_per_attempt"], COST_TOL)),
            ("cost / success", *cmp_float(r["cost_per_success"], e["cost_per_success"], COST_TOL)),
            ("wall p50 (s)", *cmp_float(r["wall_p50_s"], e["wall_p50_s"], WALL_TOL, " s")),
        ]
        print(f"  {name} + R4")
        for label, ok, msg in rows:
            print(f"    {label:<26}{msg}")
            ok_all &= ok
        checks[name] = {label: ok for label, ok, _ in rows}
    e = exp["strong"]
    rows = [
        ("all-pass", *cmp_int(S["all_pass"], e["all_pass"])),
        ("cost / attempt", *cmp_float(S["cost"] / n, e["cost_per_attempt"], COST_TOL)),
        ("cost / success", *cmp_float(S["cost"] / S["all_pass"], e["cost_per_success"], COST_TOL)),
    ]
    print("  strong-only")
    for label, ok, msg in rows:
        print(f"    {label:<26}{msg}")
        ok_all &= ok
    checks["strong"] = {label: ok for label, ok, _ in rows}
    print(f"\n  => REPRODUCTION {'AGREES with the release report on every field'
                                if ok_all else 'DISAGREES — stop and reconcile (contract § 11)'}")
    return ok_all, checks


# ---------------------------------------------------------------------------
# B — post-answer oracle
# ---------------------------------------------------------------------------

def post_answer_oracle(weak: dict, strong: dict, ids: list[str]) -> dict:
    local_safe = [s for s in ids if weak[s]["all_pass"]]
    rescueable = [s for s in ids if not weak[s]["all_pass"] and strong[s]["all_pass"]]
    unresolved = [s for s in ids if not weak[s]["all_pass"] and not strong[s]["all_pass"]]
    inversion = [s for s in ids if weak[s]["all_pass"] and not strong[s]["all_pass"]]
    n = len(ids)

    def costed(escalate: list[str]) -> dict:
        e = set(escalate)
        cost = (sum(weak[s]["score"]["reference_cost_usd"] for s in ids)
                + sum(strong[s]["score"]["reference_cost_usd"] for s in e))
        wall = median(weak[s]["score"]["wall_ms"]
                      + (strong[s]["score"]["wall_ms"] if s in e else 0) for s in ids)
        return {"escalated": len(e), "cost": cost, "cost_per_attempt": cost / n,
                "wall_p50_s": wall / 1000.0}

    all_pass = len(local_safe) + len(rescueable)
    min_useful = costed(rescueable)
    every_fail = costed(rescueable + unresolved)
    for d in (min_useful, every_fail):
        d["cost_per_success"] = d["cost"] / all_pass if all_pass else None
        d["utilization"] = d["escalated"] / n
    return {
        "n": n, "local_safe": local_safe, "rescueable": rescueable, "unresolved": unresolved,
        "inversion": inversion, "oracle_all_pass": all_pass,
        "min_useful": min_useful, "escalate_every_failure": every_fail,
    }


def report_post_answer(split: str, oracles: dict, r4: dict, n: int) -> None:
    print("\n" + "=" * 100)
    print("B. POST-ANSWER ORACLE per local arm (plan § 10) — the ideal gate: keep a passing")
    print("   local answer, escalate a local failure the frontier can rescue, and accept the rest")
    print("=" * 100)
    for name in ARMS:
        o = oracles[name]
        print(f"\n  {name}  n={n}")
        print(f"    local-safe    (local pass)                 {len(o['local_safe']):>4}  "
              f"{pct(len(o['local_safe']), n)}")
        print(f"    rescueable    (local fail, frontier pass)  {len(o['rescueable']):>4}  "
              f"{pct(len(o['rescueable']), n)}")
        print(f"    unresolved    (local fail, frontier fail)  {len(o['unresolved']):>4}  "
              f"{pct(len(o['unresolved']), n)}"
              + (f"   {o['unresolved']}" if o["unresolved"] else ""))
        print(f"    oracle final all-pass (local ∨ frontier)   {o['oracle_all_pass']:>4}  "
              f"{pct(o['oracle_all_pass'], n)}"
              f"   vs R4 cascade {r4[name]['cascade']['all_pass']} "
              f"({pct(r4[name]['cascade']['all_pass'], n).strip()}), "
              f"gap {o['oracle_all_pass'] - r4[name]['cascade']['all_pass']:+d} cases")
        mu, ev = o["min_useful"], o["escalate_every_failure"]
        print(f"    minimum USEFUL frontier utilization        "
              f"{100.0 * mu['utilization']:5.1f}%  ({mu['escalated']}/{n} — escalating an "
              f"unresolved case buys nothing)")
        print(f"    'escalate every local failure' util.       "
              f"{100.0 * ev['utilization']:5.1f}%  ({ev['escalated']}/{n})"
              + ("   [identical here: no unresolved cases]" if mu["escalated"] == ev["escalated"]
                 else f"   [+{ev['escalated'] - mu['escalated']} wasted calls]"))
        print(f"    R4 actual utilization                      "
              f"{100.0 * r4[name]['escalated'] / n:5.1f}%  ({r4[name]['escalated']}/{n})")
        for label, d in (("min-useful", mu), ("every-failure", ev)):
            print(f"    cost/attempt ${d['cost_per_attempt']:.4f}   cost/success "
                  f"${d['cost_per_success']:.4f}   wall p50 {d['wall_p50_s']:.1f} s   [{label}]")
        print(f"    inversion (local pass ∧ frontier fail)     {len(o['inversion']):>4}"
              + (f"   {o['inversion']}" if o["inversion"] else "   —"))


# ---------------------------------------------------------------------------
# C — three-tier cheapest-sufficient oracle
# ---------------------------------------------------------------------------

def three_tier_oracle(qwen: dict, nem: dict, strong: dict, ids: list[str]) -> dict:
    assign = {s: three_tier(qwen[s]["all_pass"], nem[s]["all_pass"], strong[s]["all_pass"])
              for s in ids}
    counts = Counter(assign.values())
    by_class: dict[str, Counter] = defaultdict(Counter)
    for s, tier in assign.items():
        by_class[s[:3]][tier] += 1
    # Qwen and Nemotron reference cost is $0 (local weights); the frontier row carries
    # the CLI's list-price floor.
    sufficient = sum(strong[s]["score"]["reference_cost_usd"]
                     for s in ids if assign[s] == "frontier")
    cascade = sum(strong[s]["score"]["reference_cost_usd"]
                  for s in ids if assign[s] in ("frontier", "unresolved"))
    return {
        "n": len(ids), "assignment": assign, "counts": dict(counts),
        "by_class": {c: dict(v) for c, v in sorted(by_class.items())},
        "sufficient_tier_cost": sufficient, "sufficient_tier_cost_per_attempt": sufficient / len(ids),
        "cascade_cost": cascade, "cascade_cost_per_attempt": cascade / len(ids),
        "local_cost": sum(qwen[s]["score"]["reference_cost_usd"] for s in ids)
                      + sum(nem[s]["score"]["reference_cost_usd"] for s in ids),
    }


def report_three_tier(tt: dict) -> None:
    n = tt["n"]
    print("\n" + "=" * 100)
    print("C. THREE-TIER CHEAPEST-SUFFICIENT ORACLE (descriptive; R6 groundwork, not a policy)")
    print("=" * 100)
    print("\n   qwen passes -> qwen · elif nemotron passes -> nemotron · elif frontier passes -> "
          "frontier · else unresolved\n")
    order = ("qwen", "nemotron", "frontier", "unresolved")
    for tier in order:
        c = tt["counts"].get(tier, 0)
        print(f"    {tier:<12}{c:>4}  {pct(c, n)}")
    print(f"\n    {'class':<8}" + "".join(f"{t:>12}" for t in order))
    print("    " + "-" * (8 + 12 * len(order)))
    for cls, counts in tt["by_class"].items():
        tot = sum(counts.values())
        print(f"    {cls:<8}" + "".join(f"{counts.get(t, 0):>12}" for t in order) + f"   n={tot}")
    print(f"\n    reference cost, Qwen = Nemotron = $0 (local weights; measured local cost "
          f"${tt['local_cost']:.4f})")
    print(f"    sufficient-tier cost   ${tt['sufficient_tier_cost']:8.4f}   "
          f"${tt['sufficient_tier_cost_per_attempt']:.4f} / attempt   "
          f"(pay only the one tier that suffices; an unresolved case is charged $0 because "
          f"no tier suffices)")
    print(f"    cascade cost           ${tt['cascade_cost']:8.4f}   "
          f"${tt['cascade_cost_per_attempt']:.4f} / attempt   "
          f"(a real cascade also pays the tiers it tried first, and pays the frontier on "
          f"unresolved cases too)")


# ---------------------------------------------------------------------------
# D — silent-failure anatomy
# ---------------------------------------------------------------------------

def anatomy(weak: dict, ids: list[str], fn_ids: list[str]) -> dict:
    fn_buckets: dict[str, list[str]] = defaultdict(list)
    for s in fn_ids:
        fn_buckets[fn_bucket(weak[s]["score"])].append(s)
    patterns: dict[str, list[str]] = defaultdict(list)
    for s in ids:
        patterns[fail_pattern(weak[s]["score"], weak[s]["all_pass"])].append(s)
    silent = [s for s in ids if fail_pattern(weak[s]["score"], weak[s]["all_pass"]).startswith("silent")]
    return {
        "fn_buckets": {k: sorted(v) for k, v in fn_buckets.items()},
        "patterns": {k: sorted(v) for k, v in sorted(patterns.items())},
        "silent": sorted(silent),
        "silent_are_fn": sorted(set(silent) & set(fn_ids)),
    }


def report_anatomy(anat: dict, weak_runs: dict, n: int, split: str) -> dict:
    print("\n" + "=" * 100)
    print("D. SILENT-FAILURE ANATOMY — what the R4 blind spot is made of (this is R5's target)")
    print("=" * 100)
    print("   buckets are exclusive and ordered: root_cause (rc wrong, whatever else is also")
    print("   wrong) > evidence_only (rc right, action ok, evidence short) > action_only > other")
    order = ("root_cause", "evidence_only", "action_only", "other")
    for name in ARMS:
        a, weak = anat[name], weak_runs[name]
        total_fn = sum(len(v) for v in a["fn_buckets"].values())
        print(f"\n  {name} — {total_fn} R4 routing false negatives (accepted, weak fail, "
              f"strong pass), by failed dimension")
        for b in order:
            ids = a["fn_buckets"].get(b, [])
            print(f"    {b:<14}{len(ids):>4}  {pct(len(ids), total_fn)}"
                  + (f"   {ids}" if ids else ""))
        rc_ids = a["fn_buckets"].get("root_cause", [])
        if rc_ids:
            print("    root-cause bucket, model's label vs truth (analysis layer — gold is "
                  "shown here, never routed on):")
            for s in rc_ids:
                sc = weak[s]["score"]
                extra = []
                if evidence_short(sc):
                    extra.append(f"evidence {sc['required_evidence_recall']:.2f}")
                if not sc["next_action_acceptable"]:
                    extra.append("action bad")
                print(f"      {s}  {said_vs_truth(sc)}"
                      + (f"   [+ {', '.join(extra)}]" if extra else ""))

        print(f"\n  {name} — failure anatomy of the whole local run (n={n})")
        for pat in ("pass", "no-output", "verifier-fail(unsupported)", "verifier-fail(other)",
                    "silent:root_cause", "silent:evidence_only", "silent:action_only",
                    "silent:other"):
            ids = a["patterns"].get(pat, [])
            if not ids and pat.startswith(("verifier-fail", "silent")):
                print(f"    {pat:<28}{0:>4}")
                continue
            print(f"    {pat:<28}{len(ids):>4}  {pct(len(ids), n)}"
                  + (f"   {ids}" if pat.startswith("silent") and ids else ""))
        print(f"    silent (verifier-clean & wrong) {len(a['silent']):>3}  of which R4 routing "
              f"FN {len(a['silent_are_fn'])}"
              + (f"   (not FN — the frontier failed them too: "
                 f"{sorted(set(a['silent']) - set(a['silent_are_fn']))})"
                 if len(a["silent"]) != len(a["silent_are_fn"]) else ""))

    # Non-fatal reconciliation of the release report's narrative FN sub-split.
    narrative = FN_SUBSPLIT_NARRATIVE.get(split) or {}
    notes: dict[str, dict] = {}
    if narrative:
        print("\n  NOTE — release report § 6 prose splits the same false negatives as:")
        for name in ARMS:
            want = narrative.get(name, {})
            got = {"evidence": len(anat[name]["fn_buckets"].get("evidence_only", [])),
                   "root_cause": len(anat[name]["fn_buckets"].get("root_cause", []))}
            same = got == want
            notes[name] = {"narrative": want, "computed": got, "matches": same}
            print(f"    {name:<10} prose {want['evidence']} evidence / {want['root_cause']} "
                  f"rc   vs computed {got['evidence']} evidence_only / {got['root_cause']} "
                  f"root_cause   {'matches' if same else 'DIFFERS'}")
        if not all(v["matches"] for v in notes.values()):
            print("    The differing pair is prose, not a table cell, and is NOT part of the "
                  "reproduction gate above.")
            print("    Both readings total the same number of FNs; they disagree only on where "
                  "cases that fail")
            print("    root cause AND evidence are counted. The bucketing used here is the one "
                  "contract § 11")
            print("    requires and is exclusive by construction, so it is the number R5 "
                  "reports; § 6's prose")
            print("    should be amended to match, or its bucketing stated. Do not adjust "
                  "either silently.")
    return notes


# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="R5 oracle ceilings + R4 reproduction gate (analysis layer only)")
    ap.add_argument("--split", default="dev", choices=["dev", "test"])
    ap.add_argument("--qwen", help="override the frozen Qwen run id")
    ap.add_argument("--nemotron", help="override the frozen Nemotron run id")
    ap.add_argument("--strong", help="override the frozen frontier run id")
    ap.add_argument("--allow-test", action="store_true",
                    help="Required for --split test (contract § 14: TEST is opened once, "
                         "for a frozen policy, after DEV selection).")
    ap.add_argument("--json-out")
    ap.add_argument("--allow-cross-suite", action="store_true",
                    help="Proceed even if the runs (or the corpus) span suite versions.")
    args = ap.parse_args()

    if args.split == "test" and not args.allow_test:
        raise SystemExit(
            "refusing to read the TEST split without --allow-test. Contract § 4/§ 14: TEST is "
            "opened once, only for a policy that qualified on DEV and was frozen. Oracle "
            "ceilings computed on TEST before that point are a selection signal from the "
            "sealed split.")
    if args.split == "test":
        print("!" * 100)
        print("!! TEST SPLIT OPENED (--allow-test). Contract § 4: no threshold, feature or")
        print("!! classifier may be chosen from anything below. If R5 selection is not already")
        print("!! frozen (§ 13) and the TEST unlock condition (§ 14) not already met, this run")
        print("!! has contaminated the split and must be recorded as such in the experiment log.")
        print("!" * 100 + "\n")

    runs = dict(RUNS[args.split])
    for k in ("qwen", "nemotron", "strong"):
        if getattr(args, k):
            runs[k] = getattr(args, k)
    print(f"R5 oracles — split={args.split}  qwen={runs['qwen']}  nemotron={runs['nemotron']}  "
          f"frontier={runs['strong']}\n")

    with psycopg.connect(DSN) as conn:
        suites = require_comparable(conn, list(runs.values()),
                                    allow_cross_suite=args.allow_cross_suite, against_corpus=True)
        loaded = {k: _load(conn, rid) for k, rid in runs.items()}

    for k, rows in loaded.items():
        splits = {r["split"] for r in rows.values()}
        if splits != {args.split}:
            raise SystemExit(f"{k} run {runs[k]!r} scored scenarios in splits {sorted(splits)}, "
                             f"expected only {args.split!r}")
    ids = sorted(set(loaded["qwen"]) & set(loaded["nemotron"]) & set(loaded["strong"]))
    union = set(loaded["qwen"]) | set(loaded["nemotron"]) | set(loaded["strong"])
    if len(union) != len(ids):
        print(f"WARNING: {len(union) - len(ids)} unpaired scenarios dropped — "
              f"{sorted(union - set(ids))}")
    n = len(ids)
    print(f"suite versions: {suites}   paired scenarios: n={n}   "
          f"classes: {len({s[:3] for s in ids})}\n")

    strong = loaded["strong"]
    r4 = {name: replay_r4(loaded[name], strong, ids) for name in ARMS}
    S = _arm_summary([strong[s] for s in ids])
    agrees, checks = report_reproduction(args.split, r4, S, n)

    oracles = {name: post_answer_oracle(loaded[name], strong, ids) for name in ARMS}
    report_post_answer(args.split, oracles, r4, n)

    tt = three_tier_oracle(loaded["qwen"], loaded["nemotron"], strong, ids)
    report_three_tier(tt)

    anat = {name: anatomy(loaded[name], ids, r4[name]["routing_fn_ids"]) for name in ARMS}
    notes = report_anatomy(anat, {name: loaded[name] for name in ARMS}, n, args.split)

    out = Path(args.json_out) if args.json_out else (
        ROOT / "evals" / "reports" / f"r5-oracles-{args.split}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "split": args.split, "runs": runs, "suites": suites, "n": n,
        "reproduction": {
            "agrees": agrees, "checks": checks, "expected": EXPECTED[args.split],
            "tolerances": {"cost_usd": COST_TOL, "wall_s": WALL_TOL},
            "computed": {name: {k: v for k, v in r4[name].items() if k != "per"} for name in ARMS}
            | {"strong": {"all_pass": S["all_pass"], "cost": S["cost"],
                          "cost_per_attempt": S["cost"] / n,
                          "cost_per_success": S["cost"] / S["all_pass"],
                          "wall_p50_s": S["wall_p50"] / 1000.0}},
        },
        "r4_replay_per_scenario": {name: r4[name]["per"] for name in ARMS},
        "post_answer_oracle": {name: {k: v for k, v in oracles[name].items()} for name in ARMS},
        "three_tier": tt,
        "anatomy": anat,
        "fn_subsplit_note": notes,
    }, indent=2, default=str))
    print(f"\nwritten: {out}")

    if not agrees:
        print("\nEXIT 2 — the R4 reproduction disagrees with the frozen release report. "
              "Contract § 11: reconcile before any R5 number is read.")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
