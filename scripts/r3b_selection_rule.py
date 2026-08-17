"""R3b — apply the pre-registered selection rule mechanically.

The rule (OVERNIGHT_STATUS.md § M4.2, committed before any 8 192-token result was
observed) has six mandatory criteria; this script computes each one from the
persisted runs and prints PASS / FAIL with the supporting value. It exists so the
decision is a function of the recorded rows, not of a reading of them.

    reproducibility gate   Qwen A vs Qwen B: ≥ 46/48 output digests AND ≥ 46/48 outcomes
    A  completion          Nemotron complete (stop_reason "stop") ≥ 43/48
    B  quality             Nemotron all-pass ≥ 14/48; rc ≥ rc(Qwen A) − max(2, 2·|rc(A) − rc(B)|)
    C  silent failure      Nemotron silent failures ≤ 6/48  (routing false negatives also reported)
    D  regressions         cell B (Qwen pass / Nemotron fail) ≤ 5, against Qwen A AND against Qwen B
    E  cascade economics   unchanged R4 `verifier` replay vs the strong reference:
                           strong calls < 50% (≤ 23/48) AND cost / success ≤ $0.070
    F  latency             Nemotron-only wall p50 ≤ 75 000 ms as run; p95 reported

Definitions: complete = `stop_reason == "stop"` (finished inside the budget; R3: 19 =
17 schema-valid + 2 schema-invalid), the scoreable count is reported beside it; silent
= schema-valid, verifier-clean, all_pass false (`model_migration_matrix.py`); replay as
in `routing_cascade_report.py` (apply the gate to the recorded weak trajectories, take
the recorded strong outcome where it fires; cost = strong reference cost on escalated
cases, local $0).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from statistics import median

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.suite import require_comparable  # noqa: E402
from scripts.model_migration_matrix import _load, _no_output, _silent  # noqa: E402
from scripts.routing_cascade_report import _signals  # noqa: E402
from services.ai_orchestrator.cascade import EscalationPolicy, should_escalate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")


def _pctl(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


def replay(weak: dict, strong: dict, ids: list[str]) -> dict:
    esc, passes, cost = 0, 0, 0.0
    for sid in ids:
        w, s = weak[sid], strong[sid]
        e, _ = should_escalate(_signals(w), EscalationPolicy.VERIFIER)
        final = s if e else w
        esc += int(e)
        passes += int(final["all_pass"])
        cost += s["score"]["reference_cost_usd"] if e else 0.0
    return {"escalated": esc, "passes": passes, "cost": cost,
            "cost_per_success": (cost / passes) if passes else None,
            "cost_per_attempt": cost / len(ids)}


def main() -> None:
    ap = argparse.ArgumentParser(description="R3b pre-registered selection rule")
    ap.add_argument("--qwen-a", default="R3b-qwen-dev")
    ap.add_argument("--qwen-b", default="R3b-qwen2-dev")
    ap.add_argument("--nemotron", default="R3b-nemotron-dev")
    ap.add_argument("--strong", default="E4-v2-dev")
    ap.add_argument("--historical-nemotron", default="R3-nemotron-dev")
    ap.add_argument("--json-out")
    ap.add_argument("--allow-cross-suite", action="store_true",
                    help="Proceed even if the runs (or the corpus) span suite versions; the "
                         "caveat is printed. Cross-suite numbers are structural, not causal.")
    args = ap.parse_args()

    with psycopg.connect(DSN) as conn:
        require_comparable(conn, [args.qwen_a, args.qwen_b, args.nemotron, args.strong, args.historical_nemotron], allow_cross_suite=args.allow_cross_suite,
                           against_corpus=True)
        QA, QB, N, S = (_load(conn, args.qwen_a), _load(conn, args.qwen_b),
                        _load(conn, args.nemotron), _load(conn, args.strong))
        H = _load(conn, args.historical_nemotron)

    ids = sorted(set(QA) & set(QB) & set(N) & set(S))
    n = len(ids)
    if any(len(x) != n for x in (QA, QB, N, S)):
        print(f"WARNING: unpaired scenarios dropped -> n={n}")
    if {QA[s]["split"] for s in ids} != {"dev"}:
        raise SystemExit("selection belongs on dev")

    def cnt(run, pred):
        return sum(1 for s in ids if pred(run[s]))

    results = []

    def crit(key, label, ok, value):
        results.append({"criterion": key, "label": label, "pass": bool(ok), "value": value})

    # ---- reproducibility gate -----------------------------------------------------
    digests = sum(1 for s in ids if QA[s]["traj"].get("output_digest")
                  and QA[s]["traj"].get("output_digest") == QB[s]["traj"].get("output_digest"))
    outcomes = sum(1 for s in ids if QA[s]["all_pass"] == QB[s]["all_pass"])
    crit("gate", "Qwen A vs B: digests >= 46/48 and outcomes >= 46/48",
         digests >= 46 and outcomes >= 46, f"digests {digests}/{n}, outcomes {outcomes}/{n}")

    # ---- A completion --------------------------------------------------------------
    # complete = finished inside the budget (stop_reason "stop"); R3: 19 = 17 schema-valid
    # + 2 schema-invalid, 29 `length`. Scoreable (not no-output) is reported beside it.
    def _stop(r):
        return ((r["traj"].get("model_invocations") or [{}])[0]).get("stop_reason")
    complete = cnt(N, lambda r: _stop(r) == "stop")
    scoreable = cnt(N, lambda r: not _no_output(r))
    capped = cnt(N, lambda r: _stop(r) == "length")
    hist_complete = sum(1 for s in ids if s in H and _stop(H[s]) == "stop")
    hist_scoreable = sum(1 for s in ids if s in H and not _no_output(H[s]))
    crit("A", "Nemotron complete (stop inside budget) >= 43/48", complete >= 43,
         f"{complete}/{n} complete, {capped} still length-capped, {scoreable} scoreable "
         f"(historical {hist_complete} complete / {hist_scoreable} scoreable; +{complete - hist_complete})")

    # ---- B quality -----------------------------------------------------------------
    ap_n = cnt(N, lambda r: r["all_pass"])
    rc_n = cnt(N, lambda r: r["score"]["root_cause_correct"])
    rc_a = cnt(QA, lambda r: r["score"]["root_cause_correct"])
    rc_b = cnt(QB, lambda r: r["score"]["root_cause_correct"])
    tol = max(2, 2 * abs(rc_a - rc_b))
    crit("B1", "Nemotron strict all-pass >= 14/48", ap_n >= 14, f"{ap_n}/{n}")
    crit("B2", f"Nemotron rc >= rc(Qwen A) - {tol}", rc_n >= rc_a - tol,
         f"rc Nemotron {rc_n} vs Qwen A {rc_a} (B {rc_b}); exact difference {rc_n - rc_a:+d}; tolerance {tol}")

    # ---- C silent ------------------------------------------------------------------
    silent = [s for s in ids if _silent(N[s])]
    fn = [s for s in silent if S[s]["all_pass"]]
    crit("C", "Nemotron silent failures <= 6/48", len(silent) <= 6,
         f"silent {len(silent)} {silent}; routing false negatives {len(fn)}")

    # ---- D regressions -------------------------------------------------------------
    cell_b_a = [s for s in ids if QA[s]["all_pass"] and not N[s]["all_pass"]]
    cell_b_b = [s for s in ids if QB[s]["all_pass"] and not N[s]["all_pass"]]
    crit("D", "cell B (Qwen pass / Nemotron fail) <= 5, vs Qwen A and vs Qwen B",
         len(cell_b_a) <= 5 and len(cell_b_b) <= 5,
         f"vs A {len(cell_b_a)} {cell_b_a}; vs B {len(cell_b_b)}")

    # ---- E cascade economics -------------------------------------------------------
    rp = replay(N, S, ids)
    rq = replay(QA, S, ids)
    crit("E1", "Nemotron+R4 strong calls < 50% (<= 23/48)", rp["escalated"] <= 23,
         f"{rp['escalated']}/{n} = {100.0 * rp['escalated'] / n:.1f}%  (Qwen A+R4 {rq['escalated']}/{n})")
    cps = rp["cost_per_success"]
    crit("E2", "Nemotron+R4 cost / success <= $0.070", cps is not None and cps <= 0.070,
         f"${cps:.4f} ({rp['passes']}/{n} passes, ${rp['cost']:.3f} total)  (Qwen A+R4 ${rq['cost_per_success']:.4f}, {rq['passes']}/{n})"
         if cps is not None else "no passes")

    # ---- F latency -----------------------------------------------------------------
    walls = [N[s]["score"]["wall_ms"] for s in ids]
    p50, p95 = int(median(walls)), int(_pctl(walls, 0.95))
    crit("F", "Nemotron-only wall p50 <= 75 000 ms (as run)", p50 <= 75_000, f"p50 {p50:,} ms, p95 {p95:,} ms, max {max(walls):,} ms")

    # ---- verdict --------------------------------------------------------------------
    mandatory = [r for r in results if r["criterion"] != "gate"]
    gate_ok = results[0]["pass"]
    qualifies = gate_ok and all(r["pass"] for r in mandatory)
    print(f"R3b pre-registered selection rule — Qwen A={args.qwen_a}  Qwen B={args.qwen_b}  "
          f"Nemotron={args.nemotron}  strong-ref={args.strong}  n={n}\n")
    for r in results:
        print(f"  {r['criterion']:<5}{'PASS' if r['pass'] else 'FAIL':<6}{r['label']:<62} {r['value']}")
    print(f"\nreproducibility gate: {'OK — comparison valid' if gate_ok else 'FAILED — stop and diagnose before interpreting'}")
    print(f"verdict: Nemotron {'QUALIFIES — exactly one TEST confirmation is permitted' if qualifies else 'does NOT qualify — Qwen remains incumbent, TEST untouched'}")

    out = Path(args.json_out) if args.json_out else ROOT / "evals" / "reports" / f"r3b-selection-{args.nemotron}.json"
    out.write_text(json.dumps({"runs": vars(args), "n": n, "results": results, "gate_ok": gate_ok,
                               "qualifies": qualifies, "replay": {"nemotron": rp, "qwen_a": rq}}, indent=2))
    print(f"written: {out}")


if __name__ == "__main__":
    main()
