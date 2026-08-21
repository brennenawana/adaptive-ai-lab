"""R3 — paired model migration matrix: incumbent weak arm vs candidate weak arm.

For every scenario the two arms both scored:

    A  incumbent PASS / candidate PASS   commoditised, local-safe territory
    B  incumbent PASS / candidate FAIL   candidate regression — investigate before adoption
    C  incumbent FAIL / candidate PASS   candidate rescue — the primary value signal
    D  incumbent FAIL / candidate FAIL   unresolved by switching weak models

…broken down by scenario class, root-cause category, evidence-recall pattern,
verifier behaviour and parse behaviour. Then the question the whole experiment is
about: SILENT failures — verifier-clean answers that are nevertheless wrong (the
family a deterministic gate cannot see). With a strong reference run, a silent
failure the strong arm would pass is a routing false negative; the report counts how
many of the incumbent's the candidate removes and how many new ones it introduces.

Selection happens on dev; this script is a dev tool. Nothing here reads gold labels
as routing features — it reads persisted scores, which is what a scorer is for.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.suite import require_comparable  # noqa: E402
from fis_platform.tolerances import refuse_curtailed  # noqa: E402
ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")


def _load(conn, run_id: str) -> dict[str, dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT cs.scenario_id, cs.all_pass, cs.payload AS score, t.payload AS traj,
                      m.split, m.root_cause AS truth, m.category
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


def _no_output(row: dict) -> bool:
    return any(d["name"] == "produced_output" for d in row["score"].get("dimensions", []))


def _fail_pattern(row: dict) -> str:
    """One label per failed case, ordered by what a router could or could not see."""
    s = row["score"]
    if _no_output(row):
        return "no-output"
    if not s["verifier_passed"]:
        return "verifier-fail" + ("(unsupported)" if s["unsupported_claims"] else "")
    parts = []
    if not s["root_cause_correct"]:
        parts.append("rc")
    if s["required_evidence_recall"] < s.get("evidence_recall_threshold", 0.8):
        parts.append("evidence")
    if not s["next_action_acceptable"]:
        parts.append("action")
    if s.get("forbidden_claim_made"):
        parts.append("FORBIDDEN")
    return "silent:" + "+".join(parts) if parts else "pass"


def _silent(row: dict) -> bool:
    """Verifier-clean, schema-valid, and still failing — invisible to a deterministic gate."""
    s = row["score"]
    return (not row["all_pass"]) and s["verifier_passed"] and not _no_output(row)


def _said(row: dict, dim: str) -> str | None:
    for d in row["score"].get("dimensions", []):
        if d["name"] == dim and (d.get("detail") or "").startswith("said "):
            return d["detail"][5:].split(",")[0]
    return None


def _inv(row: dict) -> dict:
    return (row["traj"].get("model_invocations") or [{}])[0]


def _pct(n: int, d: int) -> str:
    return "  n/a" if not d else f"{100.0 * n / d:5.1f}%"


def _arm(rows: list[dict]) -> dict:
    n = len(rows)
    rc = [r for r in rows if r["score"]["root_cause_correct"]]
    walls = sorted(r["score"]["wall_ms"] for r in rows)
    return {
        "n": n, "all_pass": sum(1 for r in rows if r["all_pass"]), "rc": len(rc),
        "act_given_rc": sum(1 for r in rc if r["score"]["next_action_acceptable"]),
        "evidence": mean(r["score"]["required_evidence_recall"] for r in rows),
        "verifier": sum(1 for r in rows if r["score"]["verifier_passed"]),
        "no_output": sum(1 for r in rows if _no_output(r)),
        "unsupported": sum(r["score"]["unsupported_claims"] for r in rows),
        "forbidden": sum(1 for r in rows if r["score"].get("forbidden_claim_made")),
        "silent": sum(1 for r in rows if _silent(r)),
        "wall_p50": int(median(walls)), "wall_p95": walls[min(n - 1, int(0.95 * n))],
        "in_tok": sum(_inv(r).get("usage", {}).get("input_tokens", 0) for r in rows),
        "out_tok": sum(_inv(r).get("usage", {}).get("output_tokens", 0) for r in rows),
        "stop": Counter(_inv(r).get("stop_reason") for r in rows),
        "fingerprint": Counter(_inv(r).get("runtime_fingerprint") for r in rows),
        "session": Counter((r["traj"].get("runtime_context") or {}).get("local_server_session") for r in rows),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="R3 paired model migration matrix")
    ap.add_argument("--incumbent", required=True, help="run id of the incumbent weak arm (Qwen control)")
    ap.add_argument("--candidate", required=True, help="run id of the candidate weak arm (Nemotron)")
    ap.add_argument("--strong", help="strong reference run id for silent-failure routing regret (e.g. E4-v2-dev)")
    ap.add_argument("--json-out")
    ap.add_argument("--allow-cross-suite", action="store_true",
                    help="Proceed even if the runs (or the corpus) span suite versions; the "
                         "caveat is printed. Cross-suite numbers are structural, not causal.")
    args = ap.parse_args()

    compared_runs = [args.incumbent, args.candidate, *([args.strong] if args.strong else [])]
    # Guard C (playbook §6 guard 3, paired firewall): a curtailed arm never enters a
    # paired comparison. Checked before any of the compared runs touches the DB.
    refuse_curtailed(compared_runs)

    with psycopg.connect(DSN) as conn:
        require_comparable(conn, compared_runs, allow_cross_suite=args.allow_cross_suite,
                           against_corpus=True)
        A_ = _load(conn, args.incumbent)
        B_ = _load(conn, args.candidate)
        S_ = _load(conn, args.strong) if args.strong else {}

    ids = sorted(set(A_) & set(B_) & (set(S_) if S_ else set(A_)))
    n = len(ids)
    if len(A_) != n or len(B_) != n:
        print(f"WARNING: unpaired scenarios dropped (incumbent {len(A_)}, candidate {len(B_)}, paired {n})")
    splits = {A_[s]["split"] for s in ids} | {B_[s]["split"] for s in ids}
    if splits != {"dev"}:
        print(f"NOTE: split(s) {sorted(splits)} — selection belongs on dev")

    cells: dict[str, list[str]] = {"A": [], "B": [], "C": [], "D": []}
    per = []
    for sid in ids:
        a, b = A_[sid], B_[sid]
        cell = {(True, True): "A", (True, False): "B", (False, True): "C", (False, False): "D"}[
            (a["all_pass"], b["all_pass"])]
        cells[cell].append(sid)
        per.append({
            "scenario_id": sid, "class": sid[:3], "category": a["category"], "truth": a["truth"], "cell": cell,
            "incumbent": {"pass": a["all_pass"], "pattern": _fail_pattern(a), "silent": _silent(a),
                          "rc_said": _said(a, "root_cause"), "evidence": a["score"]["required_evidence_recall"],
                          "verifier": a["score"]["verifier_passed"], "no_output": _no_output(a),
                          "out_tok": _inv(a).get("usage", {}).get("output_tokens"), "wall_ms": a["score"]["wall_ms"]},
            "candidate": {"pass": b["all_pass"], "pattern": _fail_pattern(b), "silent": _silent(b),
                          "rc_said": _said(b, "root_cause"), "evidence": b["score"]["required_evidence_recall"],
                          "verifier": b["score"]["verifier_passed"], "no_output": _no_output(b),
                          "out_tok": _inv(b).get("usage", {}).get("output_tokens"), "wall_ms": b["score"]["wall_ms"]},
            "strong_pass": S_[sid]["all_pass"] if S_ else None,
        })

    inc, cand = _arm([A_[s] for s in ids]), _arm([B_[s] for s in ids])
    print(f"R3 migration matrix — incumbent={args.incumbent}  candidate={args.candidate}"
          f"{'  strong-ref=' + args.strong if S_ else ''}  n={n}\n")
    hdr = f"{'metric':<28}{'incumbent':>14}{'candidate':>14}{'delta':>10}"
    print(hdr); print("-" * len(hdr))

    def row(label, ka, kb, fmt=lambda v: str(v), delta=True):
        d = f"{kb - ka:+d}" if delta and isinstance(ka, int) and isinstance(kb, int) else (
            f"{kb - ka:+.3f}" if delta and isinstance(ka, float) else "")
        print(f"{label:<28}{fmt(ka):>14}{fmt(kb):>14}{d:>10}")

    row("strict all-pass", inc["all_pass"], cand["all_pass"], lambda v: f"{v} ({100.0 * v / n:.1f}%)")
    row("root cause correct", inc["rc"], cand["rc"], lambda v: f"{v} ({100.0 * v / n:.1f}%)")
    print(f"{'act | rc':<28}{_pct(inc['act_given_rc'], inc['rc']).strip():>14}{_pct(cand['act_given_rc'], cand['rc']).strip():>14}")
    row("evidence recall (mean)", round(inc["evidence"], 3), round(cand["evidence"], 3), lambda v: f"{v:.3f}")
    row("verifier pass", inc["verifier"], cand["verifier"])
    row("no-output (parse/schema)", inc["no_output"], cand["no_output"])
    row("unsupported claims (total)", inc["unsupported"], cand["unsupported"])
    row("forbidden claims (cases)", inc["forbidden"], cand["forbidden"])
    row("SILENT failures", inc["silent"], cand["silent"])
    row("wall p50 ms", inc["wall_p50"], cand["wall_p50"])
    row("wall p95 ms", inc["wall_p95"], cand["wall_p95"])
    row("input tokens (total)", inc["in_tok"], cand["in_tok"])
    row("output tokens (total)", inc["out_tok"], cand["out_tok"])
    row("stop reasons", dict(inc["stop"]), dict(cand["stop"]), delta=False)
    row("runtime fingerprint", dict(inc["fingerprint"]), dict(cand["fingerprint"]), delta=False)
    print(f"{'server session':<28}{list(inc['session'])}  ->  {list(cand['session'])}")

    print("\nmigration matrix")
    for k, meaning in (("A", "both pass — commoditised / local-safe"), ("B", "incumbent pass / candidate FAIL — regression"),
                       ("C", "incumbent FAIL / candidate pass — rescue"), ("D", "both fail — unresolved by the model swap")):
        print(f"  {k}  {len(cells[k]):>3}  {_pct(len(cells[k]), n)}   {meaning}")

    def breakdown(sids: list[str], title: str, side: str):
        if not sids:
            return
        rows = [p for p in per if p["scenario_id"] in sids]
        print(f"\n{title} ({len(rows)}):")
        print("  by class:      " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(p["class"] for p in rows).items())))
        print("  by root cause: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(p["truth"] for p in rows).items())))
        print(f"  {side} failure pattern: " + ", ".join(
            f"{k} {v}" for k, v in Counter(p[side]["pattern"] for p in rows).most_common()))
        for p in rows:
            i, c = p["incumbent"], p["candidate"]
            print(f"    {p['scenario_id']:<12} truth={p['truth']:<28} incumbent: {i['pattern']:<28} said={i['rc_said']} ev={i['evidence']:.2f} | "
                  f"candidate: {c['pattern']:<28} said={c['rc_said']} ev={c['evidence']:.2f}"
                  + (f" | strong-ref {'pass' if p['strong_pass'] else 'FAIL'}" if S_ else ""))

    breakdown(cells["B"], "B — candidate regressions (review each before believing it)", "candidate")
    breakdown(cells["C"], "C — candidate rescues", "incumbent")
    breakdown(cells["D"], "D — unresolved by either weak model", "candidate")

    # ---- silent-failure analysis -------------------------------------------------
    inc_silent = {p["scenario_id"] for p in per if p["incumbent"]["silent"]}
    cand_silent = {p["scenario_id"] for p in per if p["candidate"]["silent"]}
    print("\nSILENT failures — verifier-clean, schema-valid, wrong (invisible to the R4 gate)")
    print(f"  incumbent  {len(inc_silent)}/{n}   candidate  {len(cand_silent)}/{n}   delta {len(cand_silent) - len(inc_silent):+d}")
    print(f"  incumbent-silent cases the candidate PASSES        {len([s for s in inc_silent if B_[s]['all_pass']])}")
    print(f"  incumbent-silent cases still silent in candidate   {len(inc_silent & cand_silent)}")
    print(f"  incumbent-silent cases the candidate fails LOUDLY  "
          f"{len([s for s in inc_silent if not B_[s]['all_pass'] and not _silent(B_[s])])}  (visible to the gate now)")
    print(f"  NEW silent failures introduced by the candidate    {len(cand_silent - inc_silent)}  {sorted(cand_silent - inc_silent)}")
    if S_:
        inc_fn = [s for s in inc_silent if S_[s]["all_pass"]]
        cand_fn = [s for s in cand_silent if S_[s]["all_pass"]]
        print(f"  routing false negatives (silent AND strong-ref passes): incumbent {len(inc_fn)}  candidate {len(cand_fn)}  delta {len(cand_fn) - len(inc_fn):+d}")
    print("  incumbent silent patterns: " + ", ".join(f"{k} {v}" for k, v in Counter(p["incumbent"]["pattern"] for p in per if p["incumbent"]["silent"]).most_common()))
    print("  candidate silent patterns: " + ", ".join(f"{k} {v}" for k, v in Counter(p["candidate"]["pattern"] for p in per if p["candidate"]["silent"]).most_common()))

    print("\nper class  (incumbent pass / candidate pass / n)")
    by = defaultdict(list)
    for p in per:
        by[p["class"]].append(p)
    for cls in sorted(by):
        ps = by[cls]
        print(f"  {cls} {ps[0]['category']:<24} {sum(1 for p in ps if p['incumbent']['pass'])} / {sum(1 for p in ps if p['candidate']['pass'])} / {len(ps)}   "
              f"cells " + " ".join(f"{k}{sum(1 for p in ps if p['cell'] == k)}" for k in "ABCD"))

    out = Path(args.json_out) if args.json_out else (
        ROOT / "evals" / "reports" / f"migration-{args.incumbent}-vs-{args.candidate}.json")
    out.write_text(json.dumps({
        "incumbent": args.incumbent, "candidate": args.candidate, "strong": args.strong, "n": n,
        "cells": {k: v for k, v in cells.items()},
        "arms": {"incumbent": {k: (dict(v) if isinstance(v, Counter) else v) for k, v in inc.items()},
                 "candidate": {k: (dict(v) if isinstance(v, Counter) else v) for k, v in cand.items()}},
        "silent": {"incumbent": sorted(inc_silent), "candidate": sorted(cand_silent)},
        "per_scenario": per,
    }, indent=2, default=str))
    print(f"\nwritten: {out}")


if __name__ == "__main__":
    main()
