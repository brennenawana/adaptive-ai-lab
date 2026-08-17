"""R3b — token-budget delta: the same model, the same contract, two generation budgets.

    --before  the run at the historical budget (R3, max_tokens 4096)
    --after   the run at the new budget      (R3b, max_tokens 8192)

For one model at a time. Reports the arm summary at each level (completion, cap
hits, quality, token distribution, reasoning/answer split where the adapter observed
it, latency, throughput), the per-case transitions (outcome changed, newly
completing, became worse, output digest equal), the silent-failure counts, and —
the question R3b was run to answer — a classification of every `length`-stopped case
in the BEFORE run into exactly one of:

    RECOVERED_PASS        completed at the new budget and passes strictly
    RECOVERED_FAIL        completed at the new budget and still fails (a wrong or
                          incomplete answer, now visible instead of a truncated one)
    STILL_LENGTH_CAPPED   `stop_reason == length` again — the budget is still binding
    OTHER_FAILURE         not complete for another reason (schema-invalid, error)

Two caveats the report prints rather than hides: (1) the two runs are in different
server sessions unless their `local_server_session` agrees, so a per-case difference
on a case whose BEFORE output never approached the old cap is session drift, not
budget; (2) `reasoning_chars`/`content_chars` exist only on records written after
the telemetry was added — for older records the split is known only for `length`
stops (all reasoning, no answer).

Selection happens on dev; this script reads persisted scores and trajectories only.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.model_migration_matrix import (  # noqa: E402
    _fail_pattern, _inv, _load, _no_output, _said, _silent,
)

ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")

CLASSES = ("RECOVERED_PASS", "RECOVERED_FAIL", "STILL_LENGTH_CAPPED", "OTHER_FAILURE")


def _stop(row: dict) -> str | None:
    return _inv(row).get("stop_reason")


def _out(row: dict) -> int:
    return int(_inv(row).get("usage", {}).get("output_tokens", 0) or 0)


def _pctl(xs: list, q: float):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None


def _complete(row: dict) -> bool:
    return not _no_output(row)


def _classify(before: dict, after: dict) -> str:
    """Only meaningful for a BEFORE row whose stop_reason was `length`."""
    if _stop(after) == "length":
        return "STILL_LENGTH_CAPPED"
    if not _complete(after):
        return "OTHER_FAILURE"
    return "RECOVERED_PASS" if after["all_pass"] else "RECOVERED_FAIL"


def _arm(rows: list[dict]) -> dict:
    n = len(rows)
    rc = [r for r in rows if r["score"]["root_cause_correct"]]
    outs = [_out(r) for r in rows]
    walls = [r["score"]["wall_ms"] for r in rows]
    apis = [r["score"].get("api_ms") or r["score"]["wall_ms"] for r in rows]
    tps = [1000.0 * _out(r) / a for r, a in zip(rows, apis) if a]
    reasoning = [_inv(r).get("reasoning_chars") for r in rows]
    content = [_inv(r).get("content_chars") for r in rows]
    have_split = [i for i, v in enumerate(reasoning) if v is not None]
    return {
        "n": n,
        "complete": sum(1 for r in rows if _complete(r)),
        "cap_hits": sum(1 for r in rows if _stop(r) == "length"),
        "stop": dict(Counter(_stop(r) for r in rows)),
        "all_pass": sum(1 for r in rows if r["all_pass"]),
        "rc": len(rc),
        "act_given_rc": sum(1 for r in rc if r["score"]["next_action_acceptable"]),
        "evidence": mean(r["score"]["required_evidence_recall"] for r in rows),
        "verifier": sum(1 for r in rows if r["score"]["verifier_passed"]),
        "no_output": sum(1 for r in rows if _no_output(r)),
        "unsupported": sum(r["score"]["unsupported_claims"] for r in rows),
        "forbidden": sum(1 for r in rows if r["score"].get("forbidden_claim_made")),
        "silent": sum(1 for r in rows if _silent(r)),
        "out_total": sum(outs), "out_mean": mean(outs), "out_p50": median(outs),
        "out_p95": _pctl(outs, 0.95), "out_max": max(outs),
        "out_gt_4096": sum(1 for t in outs if t > 4096),
        "out_ge_8192": sum(1 for t in outs if t >= 8192),
        "wall_p50": int(median(walls)), "wall_p95": int(_pctl(walls, 0.95)), "wall_mean": int(mean(walls)),
        "wall_max": max(walls),
        "api_p50": int(median(apis)),
        "tps_median": round(median(tps), 1) if tps else None,
        "reasoning_chars_observed": len(have_split),
        "reasoning_chars_mean": (round(mean(reasoning[i] for i in have_split)) if have_split else None),
        "content_chars_mean": (round(mean(content[i] for i in have_split if content[i] is not None))
                               if have_split else None),
        "max_tokens": dict(Counter(str(_inv(r).get("max_tokens") or (r["traj"].get("runtime_context") or {}).get("max_tokens") or "unrecorded(4096)") for r in rows)),
        "session": sorted({(r["traj"].get("runtime_context") or {}).get("local_server_session") or "?" for r in rows}),
        "fingerprint": dict(Counter(_inv(r).get("runtime_fingerprint") for r in rows)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="R3b token-budget delta for one model")
    ap.add_argument("--model", required=True, help="label, e.g. qwen / nemotron")
    ap.add_argument("--before", required=True, help="run id at the historical budget")
    ap.add_argument("--after", required=True, help="run id at the new budget")
    ap.add_argument("--strong", default="E4-v2-dev", help="strong reference run for false-negative counts")
    ap.add_argument("--json-out")
    args = ap.parse_args()

    with psycopg.connect(DSN) as conn:
        B = _load(conn, args.before)
        A = _load(conn, args.after)
        try:
            S = _load(conn, args.strong)
        except SystemExit:
            S = {}

    ids = sorted(set(A) & set(B))
    n = len(ids)
    if len(A) != n or len(B) != n:
        print(f"WARNING: unpaired scenarios dropped (before {len(B)}, after {len(A)}, paired {n})")

    b_arm, a_arm = _arm([B[s] for s in ids]), _arm([A[s] for s in ids])
    same_session = b_arm["session"] == a_arm["session"]

    print(f"R3b token-budget delta — model={args.model}  before={args.before}  after={args.after}  n={n}")
    print(f"  server session before {b_arm['session']}  after {a_arm['session']}  "
          f"-> {'SAME session' if same_session else 'DIFFERENT sessions: per-case differences on cases the old cap never touched are session drift, not budget'}")
    print(f"  max_tokens before {b_arm['max_tokens']}  after {a_arm['max_tokens']}\n")

    hdr = f"{'metric':<32}{'before':>16}{'after':>16}{'delta':>10}"
    print(hdr); print("-" * len(hdr))

    def row(label, key, fmt=lambda v: str(v)):
        vb, va = b_arm[key], a_arm[key]
        d = ""
        if isinstance(vb, (int, float)) and isinstance(va, (int, float)) and not isinstance(vb, bool):
            d = f"{va - vb:+.3f}" if isinstance(vb, float) or isinstance(va, float) else f"{va - vb:+d}"
        print(f"{label:<32}{fmt(vb):>16}{fmt(va):>16}{d:>10}")

    pc = lambda v: f"{v} ({100.0 * v / n:.1f}%)"  # noqa: E731
    row("complete (scoreable output)", "complete", pc)
    row("cap hits (stop=length)", "cap_hits", pc)
    row("no-output (any reason)", "no_output", pc)
    row("strict all-pass", "all_pass", pc)
    row("root cause correct", "rc", pc)
    print(f"{'act | rc':<32}{(str(b_arm['act_given_rc']) + '/' + str(b_arm['rc'])):>16}{(str(a_arm['act_given_rc']) + '/' + str(a_arm['rc'])):>16}")
    row("evidence recall (mean)", "evidence", lambda v: f"{v:.3f}")
    row("verifier pass", "verifier", pc)
    row("unsupported claims (total)", "unsupported")
    row("forbidden claims (cases)", "forbidden")
    row("SILENT failures", "silent")
    row("output tokens total", "out_total", lambda v: f"{v:,}")
    row("output tokens mean", "out_mean", lambda v: f"{v:,.0f}")
    row("output tokens p50", "out_p50", lambda v: f"{v:,.0f}")
    row("output tokens p95", "out_p95", lambda v: f"{v:,}")
    row("output tokens max", "out_max", lambda v: f"{v:,}")
    row("cases > 4096 output tokens", "out_gt_4096")
    row("cases >= 8192 output tokens", "out_ge_8192")
    row("wall p50 ms", "wall_p50", lambda v: f"{v:,}")
    row("wall p95 ms", "wall_p95", lambda v: f"{v:,}")
    row("wall mean ms", "wall_mean", lambda v: f"{v:,}")
    row("wall max ms", "wall_max", lambda v: f"{v:,}")
    row("llama.cpp api p50 ms", "api_p50", lambda v: f"{v:,}")
    row("gen throughput tok/s (median)", "tps_median", lambda v: "n/a" if v is None else f"{v}")
    row("reasoning split observed (n)", "reasoning_chars_observed")
    row("reasoning chars mean", "reasoning_chars_mean", lambda v: "n/a" if v is None else f"{v:,}")
    row("answer chars mean", "content_chars_mean", lambda v: "n/a" if v is None else f"{v:,}")
    print(f"{'runtime fingerprint':<32}{str(b_arm['fingerprint']):>16}{str(a_arm['fingerprint']):>16}")

    # ---- transitions --------------------------------------------------------------
    per = []
    for sid in ids:
        b, a = B[sid], A[sid]
        per.append({
            "scenario_id": sid, "class": sid[:3], "category": b["category"], "truth": b["truth"],
            "before": {"pass": b["all_pass"], "pattern": _fail_pattern(b), "stop": _stop(b), "out_tok": _out(b),
                       "complete": _complete(b), "silent": _silent(b), "rc_said": _said(b, "root_cause"),
                       "evidence": b["score"]["required_evidence_recall"], "wall_ms": b["score"]["wall_ms"],
                       "digest": b["traj"].get("output_digest")},
            "after": {"pass": a["all_pass"], "pattern": _fail_pattern(a), "stop": _stop(a), "out_tok": _out(a),
                      "complete": _complete(a), "silent": _silent(a), "rc_said": _said(a, "root_cause"),
                      "evidence": a["score"]["required_evidence_recall"], "wall_ms": a["score"]["wall_ms"],
                      "digest": a["traj"].get("output_digest"),
                      "reasoning_chars": _inv(a).get("reasoning_chars"), "content_chars": _inv(a).get("content_chars")},
            "strong_pass": S[sid]["all_pass"] if S else None,
            "length_class": _classify(b, a) if _stop(b) == "length" else None,
        })

    changed = [p for p in per if p["before"]["pass"] != p["after"]["pass"]]
    improved = [p for p in changed if p["after"]["pass"]]
    worse = [p for p in changed if not p["after"]["pass"]]
    newly_complete = [p for p in per if not p["before"]["complete"] and p["after"]["complete"]]
    lost_complete = [p for p in per if p["before"]["complete"] and not p["after"]["complete"]]
    digest_equal = [p for p in per if p["before"]["digest"] and p["before"]["digest"] == p["after"]["digest"]]
    outcome_equal = [p for p in per if p["before"]["pass"] == p["after"]["pass"]]
    pattern_equal = [p for p in per if p["before"]["pattern"] == p["after"]["pattern"]]

    print("\nper-case transitions (before -> after)")
    print(f"  output digest equal            {len(digest_equal)}/{n}")
    print(f"  scored outcome equal           {len(outcome_equal)}/{n}   failure pattern equal {len(pattern_equal)}/{n}")
    print(f"  outcome changed                {len(changed)}  (fail->PASS {len(improved)}, PASS->fail {len(worse)})")
    print(f"  newly completing               {len(newly_complete)}   lost completion {len(lost_complete)}")
    for title, rows in (("fail -> PASS", improved), ("PASS -> fail (worse)", worse), ("lost completion", lost_complete)):
        if rows:
            print(f"  {title}:")
            for p in rows:
                b, a = p["before"], p["after"]
                print(f"    {p['scenario_id']:<12} truth={p['truth']:<28} before: {b['pattern']:<22} {b['stop']}/{b['out_tok']}tok said={b['rc_said']} ev={b['evidence']:.2f} | "
                      f"after: {a['pattern']:<22} {a['stop']}/{a['out_tok']}tok said={a['rc_said']} ev={a['evidence']:.2f}"
                      + (f" | strong-ref {'pass' if p['strong_pass'] else 'FAIL'}" if S else ""))

    # ---- silent failures ------------------------------------------------------------
    b_sil = {p["scenario_id"] for p in per if p["before"]["silent"]}
    a_sil = {p["scenario_id"] for p in per if p["after"]["silent"]}
    print("\nSILENT failures (verifier-clean, schema-valid, wrong)")
    print(f"  before {len(b_sil)}   after {len(a_sil)}   delta {len(a_sil) - len(b_sil):+d}   "
          f"still silent {len(b_sil & a_sil)}   new {sorted(a_sil - b_sil)}")
    if S:
        b_fn = [s for s in b_sil if S[s]["all_pass"]]
        a_fn = [s for s in a_sil if S[s]["all_pass"]]
        print(f"  routing false negatives (silent AND strong-ref passes): before {len(b_fn)}  after {len(a_fn)}  delta {len(a_fn) - len(b_fn):+d}")
    print("  after silent patterns: " + ", ".join(f"{k} {v}" for k, v in Counter(p["after"]["pattern"] for p in per if p["after"]["silent"]).most_common()))

    # ---- historical length-cap classification ---------------------------------------
    capped = [p for p in per if p["length_class"]]
    counts = Counter(p["length_class"] for p in capped)
    print(f"\nBEFORE `length` cases classified at the new budget ({len(capped)}):")
    for c in CLASSES:
        print(f"  {c:<22}{counts.get(c, 0):>3}   {_pct(counts.get(c, 0), len(capped))}")
    print("  by class: " + ", ".join(
        f"{cls} " + "/".join(str(sum(1 for p in capped if p['class'] == cls and p['length_class'] == c)) for c in CLASSES)
        for cls in sorted({p["class"] for p in capped})) + "   (order: " + "/".join(c.split('_')[0][:4] for c in CLASSES) + ")")
    for p in capped:
        a = p["after"]
        print(f"    {p['scenario_id']:<12} {p['length_class']:<20} truth={p['truth']:<28} after: {a['pattern']:<22} {a['stop']}/{a['out_tok']}tok "
              f"said={a['rc_said']} ev={a['evidence']:.2f} reasoning={a['reasoning_chars']} answer={a['content_chars']} {a['wall_ms']}ms"
              + (f" | strong-ref {'pass' if p['strong_pass'] else 'FAIL'}" if S else ""))

    # what fraction of the BEFORE weakness was the cap: cases failing before that pass now, among cap cases
    before_fail = [p for p in per if not p["before"]["pass"]]
    cap_recovered = counts.get("RECOVERED_PASS", 0)
    print(f"\nattribution: before-run failures {len(before_fail)}/{n}; of them length-capped {len(capped)}; "
          f"length-capped cases now passing {cap_recovered} = {_pct(cap_recovered, len(capped)).strip()} of the capped cases, "
          f"{_pct(cap_recovered, len(before_fail)).strip()} of all before-run failures")

    out = Path(args.json_out) if args.json_out else (
        ROOT / "evals" / "reports" / f"token-budget-{args.before}-vs-{args.after}.json")
    out.write_text(json.dumps({
        "model": args.model, "before": args.before, "after": args.after, "strong": args.strong if S else None, "n": n,
        "same_session": same_session, "arms": {"before": b_arm, "after": a_arm},
        "transitions": {"digest_equal": len(digest_equal), "outcome_equal": len(outcome_equal),
                        "changed": len(changed), "improved": len(improved), "worse": len(worse),
                        "newly_complete": len(newly_complete), "lost_complete": len(lost_complete)},
        "silent": {"before": sorted(b_sil), "after": sorted(a_sil)},
        "length_classification": dict(counts), "per_scenario": per,
    }, indent=2, default=str))
    print(f"\nwritten: {out}")


def _pct(a: int, b: int) -> str:
    return "  n/a" if not b else f"{100.0 * a / b:5.1f}%"


if __name__ == "__main__":
    main()
