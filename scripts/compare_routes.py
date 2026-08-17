"""R1 — scenario-by-scenario equivalence of two runs that should be the same.

The first Switchyard experiment is a zero-semantic-change transport experiment: the
same prompt, evidence, model, decoding parameters, grammar and scorer, with only the
path between orchestrator and model changed. Aggregate rates are too coarse to prove
that — two runs can post the same all-pass rate while disagreeing on a third of the
cases. So this compares per scenario:

  * output digest        sha256 of the model's raw text (exact equivalence)
  * scored outcome       root cause said, action said, evidence recall, unsupported
                         claims, verifier, all-pass, no-output
  * accounting           input/output tokens, stop reason, model latency
  * routing metadata     coverage and selected backend on the routed arm

Any quality delta is a transport/configuration bug until proven otherwise; any
latency delta is the gateway's overhead and is reported as such.

Also useful for direct-vs-direct: run the control twice and the disagreement you see
is the floor of "expected nondeterminism" against which the routed arm is judged.
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
ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")


def _load(conn, run_id: str) -> dict[str, dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT cs.scenario_id, cs.all_pass, cs.payload AS score, t.payload AS traj
               FROM learning.case_scores cs
               JOIN learning.trajectories t ON t.trace_id = cs.trace_id
               WHERE cs.run_id = %s""",
            (run_id,),
        )
        rows = cur.fetchall()
    if not rows:
        raise SystemExit(f"run {run_id!r} has no persisted scores")
    return {r["scenario_id"]: r for r in rows}


def _said(score: dict, dim: str) -> str | None:
    for d in score.get("dimensions", []):
        if d["name"] == dim and d.get("detail", "") and d["detail"].startswith("said "):
            return d["detail"][5:].split(",")[0]
    return None


def _view(row: dict) -> dict:
    s, t = row["score"], row["traj"]
    inv = (t.get("model_invocations") or [{}])[0]
    return {
        "digest": t.get("output_digest"),
        "no_output": any(d["name"] == "produced_output" for d in s.get("dimensions", [])),
        "rc": _said(s, "root_cause"),
        "act": _said(s, "next_action"),
        "ev": round(s["required_evidence_recall"], 4),
        "unsup": s["unsupported_claims"],
        "ver": s["verifier_passed"],
        "all_pass": row["all_pass"],
        "in_tok": inv.get("usage", {}).get("input_tokens"),
        "out_tok": inv.get("usage", {}).get("output_tokens"),
        "stop": inv.get("stop_reason"),
        "model_ms": inv.get("latency", {}).get("wall_ms"),
        "wall_ms": s["wall_ms"],
        "routing": inv.get("routing"),
        "error": t.get("error"),
    }


def _pct(n: int, d: int) -> str:
    return "  n/a" if not d else f"{100.0 * n / d:5.1f}%"


def _summ(views: list[dict]) -> dict:
    n = len(views)
    return {
        "n": n,
        "all_pass": sum(1 for v in views if v["all_pass"]),
        "rc_ok": None,  # filled by caller with the truth-aware count
        "no_output": sum(1 for v in views if v["no_output"]),
        "ver": sum(1 for v in views if v["ver"]),
        "ev_mean": mean(v["ev"] for v in views),
        "in_tok": mean(v["in_tok"] or 0 for v in views),
        "out_tok": mean(v["out_tok"] or 0 for v in views),
        "p50_model": int(median(v["model_ms"] or 0 for v in views)),
        "p95_model": sorted(v["model_ms"] or 0 for v in views)[min(n - 1, int(0.95 * n))],
        "p50_wall": int(median(v["wall_ms"] for v in views)),
        "stop": Counter(v["stop"] for v in views),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="R1 per-scenario equivalence of two runs")
    ap.add_argument("--a", required=True, help="control run_id (direct path)")
    ap.add_argument("--b", required=True, help="candidate run_id (routed path)")
    ap.add_argument("--json-out")
    ap.add_argument("--allow-cross-suite", action="store_true",
                    help="Proceed even if the runs (or the corpus) span suite versions; the "
                         "caveat is printed. Cross-suite numbers are structural, not causal.")
    args = ap.parse_args()

    with psycopg.connect(DSN) as conn:
        require_comparable(conn, [args.a, args.b], allow_cross_suite=args.allow_cross_suite,
                           against_corpus=False)
        A, B = _load(conn, args.a), _load(conn, args.b)

    common = sorted(set(A) & set(B))
    if len(common) != len(A) or len(common) != len(B):
        print(f"WARNING: unpaired scenarios — only-in-a {len(set(A) - set(B))}, "
              f"only-in-b {len(set(B) - set(A))}; comparing {len(common)} paired")
    n = len(common)

    va = {s: _view(A[s]) for s in common}
    vb = {s: _view(B[s]) for s in common}

    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute("SELECT scenario_id, root_cause FROM ground_truth.scenario_manifests "
                    "WHERE scenario_id = ANY(%s)", (common,))
        truth = dict(cur.fetchall())

    digest_avail = sum(1 for s in common if va[s]["digest"] and vb[s]["digest"])
    digest_same = sum(1 for s in common if va[s]["digest"] and va[s]["digest"] == vb[s]["digest"])
    outcome_keys = ("no_output", "rc", "act", "ev", "unsup", "ver", "all_pass")
    same_outcome = [s for s in common if all(va[s][k] == vb[s][k] for k in outcome_keys)]
    same_tokens = sum(1 for s in common if (va[s]["in_tok"], va[s]["out_tok"])
                      == (vb[s]["in_tok"], vb[s]["out_tok"]))
    same_stop = sum(1 for s in common if va[s]["stop"] == vb[s]["stop"])

    sa, sb = _summ([va[s] for s in common]), _summ([vb[s] for s in common])
    sa["rc_ok"] = sum(1 for s in common if va[s]["rc"] == truth.get(s))
    sb["rc_ok"] = sum(1 for s in common if vb[s]["rc"] == truth.get(s))

    print(f"R1 equivalence — a={args.a} (control)  b={args.b}  paired n={n}\n")
    print(f"exact output digest equal      {digest_same}/{digest_avail} "
          f"({'digests not recorded on both' if not digest_avail else _pct(digest_same, digest_avail).strip()})")
    print(f"identical scored outcome       {len(same_outcome)}/{n}  {_pct(len(same_outcome), n).strip()}"
          f"   (no-output, rc said, action said, evidence, unsupported, verifier, all-pass)")
    print(f"identical token counts         {same_tokens}/{n}")
    print(f"identical stop reason          {same_stop}/{n}")
    print()
    hdr = f"{'':<28}{'a (control)':>16}{'b':>16}{'delta':>12}"
    print(hdr)
    print("-" * len(hdr))

    def row(label, ka, kb, fmt="{:>16}", delta=True):
        d = ""
        if delta and isinstance(ka, (int, float)) and isinstance(kb, (int, float)):
            d = f"{kb - ka:+.4g}"
        print(f"{label:<28}{fmt.format(ka)}{fmt.format(kb)}{d:>12}")

    row("all-pass", sa["all_pass"], sb["all_pass"])
    row("root cause correct", sa["rc_ok"], sb["rc_ok"])
    row("verifier pass", sa["ver"], sb["ver"])
    row("no scoreable output", sa["no_output"], sb["no_output"])
    row("evidence recall mean", round(sa["ev_mean"], 4), round(sb["ev_mean"], 4))
    row("input tokens / case", round(sa["in_tok"], 1), round(sb["in_tok"], 1))
    row("output tokens / case", round(sa["out_tok"], 1), round(sb["out_tok"], 1))
    row("model latency p50 ms", sa["p50_model"], sb["p50_model"])
    row("model latency p95 ms", sa["p95_model"], sb["p95_model"])
    row("case wall p50 ms", sa["p50_wall"], sb["p50_wall"])
    row("stop reasons", str(dict(sa["stop"])), str(dict(sb["stop"])), delta=False)

    routed = [vb[s]["routing"] for s in common if vb[s]["routing"]]
    print()
    print(f"routing metadata on b          {len(routed)}/{n} invocations carry a RoutingRecord")
    if routed:
        print(f"  gateway/version              "
              f"{Counter((r.get('gateway'), r.get('gateway_version')) for r in routed).most_common()}")
        print(f"  route_mode                   {Counter(r.get('route_mode') for r in routed).most_common()}")
        print(f"  selected_backend             "
              f"{Counter(r.get('selected_backend') for r in routed).most_common()}")
        print(f"  upstream_model               "
              f"{Counter(r.get('upstream_model') for r in routed).most_common()}")
        overhead = [r["gateway_overhead_ms"] for r in routed if r.get("gateway_overhead_ms") is not None]
        if overhead:
            print(f"  gateway overhead ms          p50 {int(median(overhead))}  max {max(overhead)}")
    routed_a = [va[s]["routing"] for s in common if va[s]["routing"]]
    print(f"routing metadata on a          {len(routed_a)}/{n} (expected 0 for the direct path)")

    diffs = [s for s in common if s not in same_outcome]
    if diffs:
        print("\nscenarios whose scored outcome differs:")
        for s in diffs:
            what = [k for k in outcome_keys if va[s][k] != vb[s][k]]
            print(f"  {s:<12} differs on {what}")
            for k in what:
                print(f"      {k:<9} a={va[s][k]!r:<40} b={vb[s][k]!r}")
            print(f"      tokens    a={va[s]['in_tok']}/{va[s]['out_tok']}   b={vb[s]['in_tok']}/{vb[s]['out_tok']}"
                  f"   stop a={va[s]['stop']} b={vb[s]['stop']}")

    out = Path(args.json_out) if args.json_out else (
        ROOT / "evals" / "reports" / f"compare-routes-{args.a}-vs-{args.b}.json")
    out.write_text(json.dumps({
        "a": args.a, "b": args.b, "n": n,
        "digest_equal": digest_same, "digest_available": digest_avail,
        "identical_outcome": len(same_outcome), "identical_tokens": same_tokens,
        "summary_a": {k: (dict(v) if isinstance(v, Counter) else v) for k, v in sa.items()},
        "summary_b": {k: (dict(v) if isinstance(v, Counter) else v) for k, v in sb.items()},
        "differing": diffs,
        "per_scenario": {s: {"a": va[s], "b": vb[s]} for s in common},
    }, indent=2, default=str))
    print(f"\nwritten: {out}")


if __name__ == "__main__":
    main()
