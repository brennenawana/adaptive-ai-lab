"""R4 — deterministic cascade report: cascade vs weak-only vs strong-only vs oracle.

Two modes, one report:

  replay   --weak RUN --strong RUN --policy P
           Apply the gate offline to a recorded weak run's trajectories (verifier
           result, no-output) and take the strong run's recorded outcome wherever the
           gate would have escalated. Exact for the weak side (the signals are what
           the runtime gate reads); the strong side is the recorded strong arm, not a
           fresh call. Cheap enough to compare policies on dev without spending
           frontier calls — that is where selection happens.

  live     --cascade RUN --strong RUN
           Report a run produced by `run_eval --escalate-to`: final outcomes under
           RUN, the weak stage under RUN.weak, decisions on Trajectory.router. The
           strong run is still needed as the reference for regret (would strong have
           passed where the weak result was accepted?) and for the oracle cells.

Every routing metric is defined once, below, from the pairing:

  weak-local acceptance     accepted weak / n
  escalation rate           escalated / n
  rescue rate               escalated AND final pass / escalated
  unnecessary escalation    escalated AND weak would pass / n     (false positive)
  false negative            accepted AND weak fail AND strong-ref pass / n
  regret vs oracle          oracle pass − cascade pass, in cases

Cost is list-price reference cost from the recorded invocations (the frontier arm's
input tokens are known to be under-reported by the CLI — see architecture.md — so
strong cost is a floor, marked as such).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, median

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.suite import require_comparable  # noqa: E402
from fis_platform.tolerances import refuse_curtailed  # noqa: E402
from services.ai_orchestrator.cascade import (  # noqa: E402
    EscalationPolicy, EscalationSignals, should_escalate,
)

ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")
_UNSUPPORTED_MARKERS = ("citation", "never successfully called", "no tool returned")


def _load(conn, run_id: str) -> dict[str, dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT cs.scenario_id, cs.all_pass, cs.payload AS score, t.payload AS traj,
                      m.split, m.root_cause AS truth
               FROM learning.case_scores cs
               JOIN learning.trajectories t ON t.trace_id = cs.trace_id
               JOIN ground_truth.scenario_manifests m ON m.scenario_id = cs.scenario_id
               WHERE cs.run_id = %s""",
            (run_id,),
        )
        rows = cur.fetchall()
    if not rows:
        raise SystemExit(f"run {run_id!r} has no persisted scores")
    return {r["scenario_id"]: r for r in rows}


def _signals(row: dict) -> EscalationSignals:
    """Recompute the gate's inputs from a persisted trajectory — the same fields the
    runtime gate reads, so replay and live agree by construction."""
    t = row["traj"]
    v = t.get("verification") or {}
    violations = tuple(v.get("violations") or [])
    produced = not any(d["name"] == "produced_output" for d in row["score"].get("dimensions", []))
    return EscalationSignals(
        produced_output=produced,
        verifier_passed=bool(v.get("passed")) and produced,
        unsupported_claims=sum(1 for m in violations if any(k in m for k in _UNSUPPORTED_MARKERS)),
        violations=violations,
    )


def _pct(n: int, d: int) -> str:
    return "  n/a" if not d else f"{100.0 * n / d:5.1f}%"


def _tokens(traj: dict, tier: str | None = None) -> tuple[int, int]:
    i = o = 0
    for inv in traj.get("model_invocations") or []:
        if tier is None or inv.get("tier") == tier:
            i += inv.get("usage", {}).get("input_tokens", 0)
            o += inv.get("usage", {}).get("output_tokens", 0)
    return i, o


def _arm_summary(rows: list[dict]) -> dict:
    n = len(rows)
    rc = [r for r in rows if r["score"]["root_cause_correct"]]
    return {
        "n": n,
        "all_pass": sum(1 for r in rows if r["all_pass"]),
        "rc": len(rc),
        "act_given_rc": sum(1 for r in rc if r["score"]["next_action_acceptable"]),
        "evidence": mean(r["score"]["required_evidence_recall"] for r in rows),
        "verifier": sum(1 for r in rows if r["score"]["verifier_passed"]),
        "no_output": sum(1 for r in rows if any(d["name"] == "produced_output"
                                                for d in r["score"].get("dimensions", []))),
        "wall_p50": int(median(r["score"]["wall_ms"] for r in rows)),
        "wall_mean": int(mean(r["score"]["wall_ms"] for r in rows)),
        "cost": sum(r["score"]["reference_cost_usd"] for r in rows),
        "in_tok": sum(_tokens(r["traj"])[0] for r in rows),
        "out_tok": sum(_tokens(r["traj"])[1] for r in rows),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="R4 cascade report (replay or live)")
    ap.add_argument("--weak", help="weak run id (replay) — for live runs defaults to <cascade>.weak")
    ap.add_argument("--strong", required=True, help="strong reference run id (e.g. E4-v2-dev)")
    ap.add_argument("--cascade", help="live cascade run id (from run_eval --escalate-to)")
    ap.add_argument("--policy", default=EscalationPolicy.VERIFIER.value,
                    choices=[p.value for p in EscalationPolicy], help="replay policy")
    ap.add_argument("--json-out")
    ap.add_argument("--allow-cross-suite", action="store_true",
                    help="Proceed even if the runs (or the corpus) span suite versions; the "
                         "caveat is printed. Cross-suite numbers are structural, not causal.")
    args = ap.parse_args()
    if not args.cascade and not args.weak:
        raise SystemExit("need --cascade RUN (live) or --weak RUN (replay)")

    weak_id = args.weak or f"{args.cascade}.weak"
    # Guard C (playbook §6 guard 3, paired firewall): a curtailed arm never enters a
    # paired comparison. Checked before any of the paired run ids touches the DB —
    # this script computes the paired oracle cells (weak vs strong-ref) directly.
    refuse_curtailed([weak_id, args.strong, *([args.cascade] if args.cascade else [])])
    with psycopg.connect(DSN) as conn:
        require_comparable(conn, [weak_id, args.strong, *([args.cascade] if args.cascade else [])], allow_cross_suite=args.allow_cross_suite,
                           against_corpus=True)
        weak = _load(conn, weak_id)
        strong = _load(conn, args.strong)
        cascade = _load(conn, args.cascade) if args.cascade else None

    ids = sorted(set(weak) & set(strong) & (set(cascade) if cascade else set(weak)))
    dropped = len(set(weak) | set(strong)) - len(ids)
    if dropped:
        print(f"WARNING: {dropped} unpaired scenarios dropped")
    n = len(ids)
    splits = {weak[s]["split"] for s in ids} | {strong[s]["split"] for s in ids}
    policy = EscalationPolicy(args.policy)

    per: list[dict] = []
    for sid in ids:
        w, s = weak[sid], strong[sid]
        sig = _signals(w)
        if cascade:
            c = cascade[sid]
            router = c["traj"].get("router") or {}
            escalated = bool(router.get("escalated"))
            reason = router.get("escalation_reason")
            final = c
        else:
            escalated, reason = should_escalate(sig, policy)
            final = s if escalated else w
        weak_pass, strong_pass, final_pass = w["all_pass"], s["all_pass"], final["all_pass"]
        oracle_pass = weak_pass or strong_pass
        per.append({
            "scenario_id": sid, "class": sid[:3],
            "escalated": escalated, "reason": reason,
            "weak_pass": weak_pass, "strong_ref_pass": strong_pass, "final_pass": final_pass,
            "oracle_pass": oracle_pass,
            "final_score": final["score"], "final_traj": final["traj"],
            "weak_score": w["score"], "strong_score": s["score"],
            "final_row": final,
        })

    esc = [p for p in per if p["escalated"]]
    acc = [p for p in per if not p["escalated"]]
    rescued = [p for p in esc if p["final_pass"]]
    rescued_needed = [p for p in esc if p["final_pass"] and not p["weak_pass"]]
    unnecessary = [p for p in esc if p["weak_pass"]]
    false_neg = [p for p in acc if not p["weak_pass"] and p["strong_ref_pass"]]
    accepted_fail = [p for p in acc if not p["weak_pass"]]
    cells = Counter(
        ("w+" if p["weak_pass"] else "w-") + ("s+" if p["strong_ref_pass"] else "s-") for p in per)
    rescueable = [p for p in per if not p["weak_pass"] and p["strong_ref_pass"]]
    caught = [p for p in rescueable if p["escalated"]]
    safe_local = [p for p in per if p["weak_pass"]]
    safe_escalated = [p for p in safe_local if p["escalated"]]
    inversion = [p for p in per if p["weak_pass"] and not p["strong_ref_pass"]]

    weak_rows = [weak[p["scenario_id"]] for p in per]
    strong_rows = [strong[p["scenario_id"]] for p in per]
    final_rows = [p["final_row"] for p in per]
    oracle_rows = [weak[p["scenario_id"]] if p["weak_pass"] else strong[p["scenario_id"]] for p in per]
    W, S, C, O = (_arm_summary(weak_rows), _arm_summary(strong_rows),
                  _arm_summary(final_rows), _arm_summary(oracle_rows))
    # A cascade pays for the weak stage on every case, and so does the oracle read as
    # a cascade. Live cascade trajectories already carry both stages' invocations
    # (wall, tokens, cost); replay has to add the weak stage explicitly.
    if not cascade:
        C["wall_p50"] = int(median(
            weak[p["scenario_id"]]["score"]["wall_ms"] + (strong[p["scenario_id"]]["score"]["wall_ms"] if p["escalated"] else 0)
            for p in per))
        C["wall_mean"] = int(mean(
            weak[p["scenario_id"]]["score"]["wall_ms"] + (strong[p["scenario_id"]]["score"]["wall_ms"] if p["escalated"] else 0)
            for p in per))
        C["in_tok"] = W["in_tok"] + sum(_tokens(strong[p["scenario_id"]]["traj"])[0] for p in esc)
        C["out_tok"] = W["out_tok"] + sum(_tokens(strong[p["scenario_id"]]["traj"])[1] for p in esc)
        C["cost"] = sum(strong[p["scenario_id"]]["score"]["reference_cost_usd"] for p in esc)
    O["wall_p50"] = int(median(
        weak[p["scenario_id"]]["score"]["wall_ms"] + (0 if p["weak_pass"] else strong[p["scenario_id"]]["score"]["wall_ms"])
        for p in per))
    O["cost"] = sum(strong[p["scenario_id"]]["score"]["reference_cost_usd"] for p in per if not p["weak_pass"])
    O["in_tok"] = W["in_tok"] + sum(_tokens(strong[p["scenario_id"]]["traj"])[0] for p in per if not p["weak_pass"])
    O["out_tok"] = W["out_tok"] + sum(_tokens(strong[p["scenario_id"]]["traj"])[1] for p in per if not p["weak_pass"])

    mode = f"LIVE cascade={args.cascade}" if cascade else f"REPLAY policy={policy.value}"
    print(f"R4 deterministic cascade — {mode}  weak={weak_id}  strong-ref={args.strong}  "
          f"split={sorted(splits)}  n={n}\n")

    hdr = f"{'metric':<30}{'weak-only':>12}{'cascade':>12}{'strong-only':>13}{'oracle':>10}"
    print(hdr); print("-" * len(hdr))

    def row(label, key, fmt):
        vals = [W[key], C[key], S[key], O[key]]
        print(f"{label:<30}" + "".join(f"{fmt(v):>{w}}" for v, w in zip(vals, (12, 12, 13, 10))))

    pc = lambda v: f"{100.0 * v / n:.1f}%"  # noqa: E731
    row("strict all-pass", "all_pass", pc)
    row("root cause correct", "rc", pc)
    print(f"{'act | rc':<30}" + "".join(
        f"{_pct(a['act_given_rc'], a['rc']).strip():>{w}}" for a, w in zip((W, C, S, O), (12, 12, 13, 10))))
    row("evidence recall (mean)", "evidence", lambda v: f"{v:.3f}")
    row("verifier pass", "verifier", pc)
    row("no-output (parse/schema)", "no_output", pc)
    row("wall p50 ms", "wall_p50", lambda v: f"{v:,}")
    row("input tokens (total)", "in_tok", lambda v: f"{v:,}")
    row("output tokens (total)", "out_tok", lambda v: f"{v:,}")
    row("reference cost (total)", "cost", lambda v: f"${v:.3f}")
    print(f"{'cost / attempted case':<30}" + "".join(
        f"{'$' + format(a['cost'] / n, '.4f'):>{w}}" for a, w in zip((W, C, S, O), (12, 12, 13, 10))))
    print(f"{'cost / successful case':<30}" + "".join(
        f"{('$' + format(a['cost'] / a['all_pass'], '.4f')) if a['all_pass'] else 'n/a':>{w}}"
        for a, w in zip((W, C, S, O), (12, 12, 13, 10))))
    print("  strong reference cost is a FLOOR: the CLI under-reports input tokens (~2/case).")

    print("\nrouting metrics")
    print(f"  weak-local acceptance rate     {_pct(len(acc), n)}  ({len(acc)}/{n})")
    print(f"  escalation (strong-call) rate  {_pct(len(esc), n)}  ({len(esc)}/{n})   "
          f"by reason: {dict(Counter(p['reason'] for p in esc))}")
    print(f"  rescue rate                    {_pct(len(rescued_needed), len(esc))}  "
          f"({len(rescued_needed)}/{len(esc)} escalations turned a weak fail into a pass; "
          f"{len(rescued)} of {len(esc)} escalated cases pass)")
    print(f"  unnecessary escalation (FP)    {_pct(len(unnecessary), n)}  ({len(unnecessary)}/{n}: "
          f"escalated although the weak result would have passed)")
    print(f"  false negative (accepted, weak fail, strong-ref pass) {_pct(len(false_neg), n)}  "
          f"({len(false_neg)}/{n})")
    print(f"  accepted weak failures (any)   {len(accepted_fail)}/{n}")
    print(f"  strong-call reduction vs strong-only  {100.0 * (1 - len(esc) / n):.1f}%")
    print(f"  quality delta vs strong-only   {C['all_pass'] - S['all_pass']:+d} cases   "
          f"vs oracle {C['all_pass'] - O['all_pass']:+d} cases")

    print("\nagainst the paired oracle (weak vs strong-ref cells)")
    print(f"  cells: w+s+ {cells['w+s+']}  w-s+ {cells['w-s+']}  w+s- {cells['w+s-']}  w-s- {cells['w-s-']}")
    print(f"  rescueable (w-s+) caught by the gate   {len(caught)}/{len(rescueable)}"
          + (f"   missed: {[p['scenario_id'] for p in rescueable if not p['escalated']]}"
             if len(caught) < len(rescueable) else ""))
    print(f"  safe-local (w+) escalated unnecessarily {len(safe_escalated)}/{len(safe_local)}"
          + (f"   {[p['scenario_id'] for p in safe_escalated]}" if safe_escalated else ""))
    print(f"  known inversion (w+s-) kept local       "
          f"{sum(1 for p in inversion if not p['escalated'])}/{len(inversion)}  {[p['scenario_id'] for p in inversion]}")
    print(f"  oracle hybrid all-pass {_pct(O['all_pass'], n)}   cascade {_pct(C['all_pass'], n)}   "
          f"strong-only {_pct(S['all_pass'], n)}   weak-only {_pct(W['all_pass'], n)}")

    print("\nper class  (esc = escalated, cascade pass / n)")
    by = {}
    for p in per:
        by.setdefault(p["class"], []).append(p)
    for cls in sorted(by):
        ps = by[cls]
        print(f"  {cls}  n={len(ps)}  esc={sum(1 for p in ps if p['escalated'])}  "
              f"weak {sum(1 for p in ps if p['weak_pass'])}  cascade {sum(1 for p in ps if p['final_pass'])}  "
              f"strong {sum(1 for p in ps if p['strong_ref_pass'])}  oracle {sum(1 for p in ps if p['oracle_pass'])}")

    if false_neg:
        print("\nfalse negatives (weak accepted, would have needed strong):")
        for p in false_neg:
            fails = [d["name"] for d in p["weak_score"].get("dimensions", []) if not d["passed"]]
            print(f"  {p['scenario_id']}  weak failed on {fails}  (verifier passed — invisible to the gate)")

    out = Path(args.json_out) if args.json_out else (
        ROOT / "evals" / "reports" / f"cascade-{args.cascade or 'replay-' + policy.value}-{weak_id}-vs-{args.strong}.json")
    out.write_text(json.dumps({
        "mode": mode, "weak": weak_id, "strong": args.strong, "cascade": args.cascade, "n": n,
        "arms": {"weak": W, "cascade": C, "strong": S, "oracle": O},
        "routing": {
            "accepted": len(acc), "escalated": len(esc), "reasons": dict(Counter(p["reason"] for p in esc)),
            "rescued_needed": len(rescued_needed), "unnecessary": len(unnecessary),
            "false_negative": len(false_neg), "accepted_fail": len(accepted_fail),
            "cells": dict(cells), "rescueable_caught": len(caught), "rescueable": len(rescueable),
            "safe_local_escalated": len(safe_escalated), "safe_local": len(safe_local),
        },
        "per_scenario": [{k: v for k, v in p.items() if k not in ("final_row", "final_traj", "final_score", "weak_score", "strong_score")}
                         for p in per],
    }, indent=2, default=str))
    print(f"\nwritten: {out}")


if __name__ == "__main__":
    main()
