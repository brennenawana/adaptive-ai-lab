"""R6 metrics — per-run summaries, pairwise overlap, oracles, tier coverage, gates.

Everything reads Postgres by run id (the reports under evals/reports are not the record).
Failure-pattern definitions are imported from scripts/r5_oracles.py so R6 counts the same
things R5 counted ("silent" = verifier-clean and wrong; "no-output" = the scorer emitted a
`produced_output` dimension). Nothing here writes to the database.

    r6_metrics.py summary --run R6-qwen35-dev [--json-out F]
    r6_metrics.py pairwise --a RUN --b RUN
    r6_metrics.py oracle --weak RUN --strong E4-v3-dev
    r6_metrics.py tiers --order RUN1,RUN2,...,STRONG            (cheapest first)
    r6_metrics.py gates --role modern_small --run RUN [--reference-run RUN] [--json-out F]
    r6_metrics.py cap-calibration --run RUN [--tolerance 3]     (§ 6 rule on a pilot run)
    r6_metrics.py quant-select --a RUN --b RUN                  (§ 7 rule)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from statistics import median

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.r6_gates import GATES, GATES_DIGEST, evaluate_gates  # noqa: E402
from fis_platform.suite import require_comparable  # noqa: E402
from scripts.r5_oracles import fail_pattern, no_output  # noqa: E402

DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")
CAP_SET = (4096, 6144, 8192)


# ------------------------------------------------------------------ loading

def load_run(conn, run_id: str) -> dict[str, dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT cs.scenario_id, cs.all_pass, cs.payload AS score, t.payload AS traj,
                      m.split, m.root_cause AS truth
               FROM learning.case_scores cs
               JOIN learning.trajectories t ON t.trace_id = cs.trace_id
               JOIN ground_truth.scenario_manifests m ON m.scenario_id = cs.scenario_id
               WHERE cs.run_id = %s""", (run_id,))
        rows = cur.fetchall()
    if not rows:
        raise SystemExit(f"run {run_id!r} has no persisted scores")
    return {r["scenario_id"]: dict(r) for r in rows}


def _inv(row: dict) -> dict:
    invs = row["traj"].get("model_invocations") or [{}]
    return invs[0]


def _p(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    k = max(0, min(len(s) - 1, int(round(q * (len(s) - 1)))))
    return s[k]


# ------------------------------------------------------------------ per-run summary

def summarize(rows: dict[str, dict]) -> dict:
    ids = sorted(rows)
    n = len(ids)
    scores = [rows[s]["score"] for s in ids]
    walls = [float(sc["wall_ms"]) for sc in scores]
    apis = [float(sc.get("api_ms") or 0) for sc in scores]
    out_tok, in_tok, tps, reasoning, cap_hits = [], [], [], [], 0
    stops: Counter = Counter()
    for s in ids:
        inv = _inv(rows[s])
        u = inv.get("usage") or {}
        o, i = int(u.get("output_tokens") or 0), int(u.get("input_tokens") or 0)
        out_tok.append(o)
        in_tok.append(i)
        stops[str(inv.get("stop_reason"))] += 1
        if inv.get("stop_reason") == "length":
            cap_hits += 1
        api = float((inv.get("latency") or {}).get("api_ms") or 0)
        if api > 0 and o > 0:
            tps.append(o / (api / 1000.0))
        reasoning.append(int(inv.get("reasoning_chars") or 0))
    patterns = Counter(fail_pattern(rows[s]["score"], rows[s]["all_pass"]) for s in ids)
    silent = [s for s in ids if fail_pattern(rows[s]["score"], rows[s]["all_pass"]).startswith("silent")]
    noout = [s for s in ids if no_output(rows[s]["score"])]
    ev_ok = sum(1 for sc in scores if sc["required_evidence_recall"] >= sc.get("evidence_recall_threshold", 0.8))
    rc_ok = sum(1 for sc in scores if sc["root_cause_correct"])
    fails_rc = [s for s in ids if not rows[s]["all_pass"] and not rows[s]["score"]["root_cause_correct"]]
    fails_ev = [s for s in ids if not rows[s]["all_pass"] and rows[s]["score"]["root_cause_correct"]
                and rows[s]["score"]["required_evidence_recall"] < rows[s]["score"].get("evidence_recall_threshold", 0.8)]
    return {
        "n": n,
        "all_pass": sum(1 for s in ids if rows[s]["all_pass"]),
        "root_cause_correct": rc_ok,
        "action_acceptable": sum(1 for sc in scores if sc["next_action_acceptable"]),
        "evidence_ok": ev_ok,
        "evidence_recall_mean": round(sum(sc["required_evidence_recall"] for sc in scores) / n, 4),
        "verifier_passed": sum(1 for sc in scores if sc["verifier_passed"]),
        "no_output": len(noout),
        "cap_hits": cap_hits,
        "schema_or_parse_failures": len([s for s in noout if _inv(rows[s]).get("stop_reason") != "length"]),
        "silent": len(silent),
        "silent_ids": silent,
        "fail_patterns": dict(sorted(patterns.items())),
        "root_cause_failures": len(fails_rc),
        "evidence_failures": len(fails_ev),
        "stop_reasons": dict(stops),
        "p50_wall_ms": int(median(walls)),
        "p95_wall_ms": int(_p(walls, 0.95)),
        "p50_api_ms": int(median(apis)),
        "output_tokens_sum": sum(out_tok),
        "output_tokens_p50": int(median(out_tok)),
        "input_tokens_sum": sum(in_tok),
        "tokens_per_s_median": round(median(tps), 1) if tps else None,
        "reasoning_chars_mean": int(sum(reasoning) / n),
        "by_class": {cls: sum(1 for s in ids if s[:3] == cls and rows[s]["all_pass"])
                     for cls in sorted({s[:3] for s in ids})},
        "gpu_mem_used_mib": _gpu_mem(rows),
        "runtime_context": _rc(rows),
    }


def _rc(rows: dict[str, dict]) -> dict:
    """The provenance fields R6 stamps on every trajectory (first row; they are constant per run)."""
    any_row = next(iter(rows.values()))
    ctx = any_row["traj"].get("runtime_context") or {}
    keys = ("candidate_id", "artifact_id", "artifact_sha256", "runtime_id", "runtime_digest",
            "execution_system_digest", "generation_config_digest", "server_args_digest",
            "git_head", "corpus_digest", "max_tokens", "llamacpp_build", "model_path",
            "local_server_session", "gpu_mem_used_mib_start", "gpu_mem_used_mib_now", "gpu_mem_used_mib_end")
    return {k: ctx.get(k) for k in keys if k in ctx}


def _gpu_mem(rows: dict[str, dict]) -> int | None:
    """Resident GPU memory while the candidate was served alone: the max of the start/end
    samples the runner records (nvidia-smi memory.used, MiB). None for historical runs."""
    vals = []
    for r in rows.values():
        ctx = r["traj"].get("runtime_context") or {}
        for k in ("gpu_mem_used_mib_start", "gpu_mem_used_mib_now", "gpu_mem_used_mib_end"):
            try:
                vals.append(int(ctx[k]))
            except (KeyError, ValueError, TypeError):
                pass
    return max(vals) if vals else None


# ------------------------------------------------------------------ pairwise / oracles

def pairwise(a: dict[str, dict], b: dict[str, dict]) -> dict:
    ids = sorted(set(a) & set(b))
    both = [s for s in ids if a[s]["all_pass"] and b[s]["all_pass"]]
    a_only = [s for s in ids if a[s]["all_pass"] and not b[s]["all_pass"]]
    b_only = [s for s in ids if b[s]["all_pass"] and not a[s]["all_pass"]]
    neither = [s for s in ids if not a[s]["all_pass"] and not b[s]["all_pass"]]
    return {"n": len(ids), "both_pass": len(both), "a_only": len(a_only), "b_only": len(b_only),
            "both_fail": len(neither), "a_only_ids": a_only, "b_only_ids": b_only,
            "a_dominates_b": len(b_only) == 0 and len(a_only) > 0,
            "b_dominates_a": len(a_only) == 0 and len(b_only) > 0}


def post_answer_oracle(weak: dict[str, dict], strong: dict[str, dict]) -> dict:
    ids = sorted(set(weak) & set(strong))
    local_safe = [s for s in ids if weak[s]["all_pass"]]
    rescueable = [s for s in ids if not weak[s]["all_pass"] and strong[s]["all_pass"]]
    unresolved = [s for s in ids if not weak[s]["all_pass"] and not strong[s]["all_pass"]]
    return {"n": len(ids), "local_safe": len(local_safe), "rescueable": len(rescueable),
            "unresolved": len(unresolved), "oracle_all_pass": len(local_safe) + len(rescueable),
            "oracle_utilization": round(len(rescueable) / len(ids), 4) if ids else None,
            "unresolved_ids": unresolved}


def tier_coverage(order: list[tuple[str, dict[str, dict]]]) -> dict:
    """`order` = [(label, rows), ...] cheapest first, strong last. For every case the first
    tier that passes; a tier's `unique_rescue` = cases it is the first to pass."""
    ids = sorted(set.intersection(*(set(r) for _, r in order)))
    first: Counter = Counter()
    per_case = {}
    for s in ids:
        tier = "unresolved"
        for label, rows in order:
            if rows[s]["all_pass"]:
                tier = label
                break
        first[tier] += 1
        per_case[s] = tier
    return {"n": len(ids), "order": [lbl for lbl, _ in order], "first_pass_by_tier": dict(first),
            "coverage": len(ids) - first["unresolved"], "per_case": per_case}


# ------------------------------------------------------------------ TRAIN rules (§ 6, § 7)

def cap_calibration(rows: dict[str, dict], tolerance: int = 3) -> dict:
    """§ 6: from one pilot run at cap 8192 decide every smaller cap."""
    per_cap = {}
    for c in CAP_SET:
        capped = [s for s in sorted(rows) if _inv(rows[s]).get("stop_reason") == "length"
                  or int((_inv(rows[s]).get("usage") or {}).get("output_tokens") or 0) >= c]
        per_cap[c] = {"capped": len(capped), "ids": capped, "ok": len(capped) <= tolerance}
    chosen = next((c for c in CAP_SET if per_cap[c]["ok"]), CAP_SET[-1])
    return {"rule": "docs/R6_EXPERIMENT_CONTRACT.md § 6", "tolerance": tolerance, "n": len(rows),
            "per_cap": per_cap, "chosen_cap": chosen,
            "none_met_tolerance": not any(v["ok"] for v in per_cap.values())}


def quant_select(a_label: str, a: dict[str, dict], b_label: str, b: dict[str, dict]) -> dict:
    """§ 7: quality first, then reliability, cap hits, latency, artifact size (caller passes
    the size tie-break as label order: `b` is the smaller artifact)."""
    sa, sb = summarize(a), summarize(b)
    steps = []

    def decide(key, better):
        va, vb = sa[key], sb[key]
        steps.append({"criterion": key, a_label: va, b_label: vb})
        if va == vb:
            return None
        return a_label if better(va, vb) else b_label

    for key, better in (("all_pass", lambda x, y: x > y), ("no_output", lambda x, y: x < y),
                        ("cap_hits", lambda x, y: x < y), ("p50_wall_ms", lambda x, y: x < y)):
        w = decide(key, better)
        if w:
            return {"winner": w, "decided_by": key, "steps": steps}
    steps.append({"criterion": "smaller_artifact", "winner": b_label})
    return {"winner": b_label, "decided_by": "smaller_artifact", "steps": steps}


# ------------------------------------------------------------------ CLI

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("summary"); p.add_argument("--run", required=True); p.add_argument("--json-out")
    p = sub.add_parser("pairwise"); p.add_argument("--a", required=True); p.add_argument("--b", required=True)
    p = sub.add_parser("oracle"); p.add_argument("--weak", required=True); p.add_argument("--strong", required=True)
    p = sub.add_parser("tiers"); p.add_argument("--order", required=True, help="comma-separated run ids, cheapest first")
    p = sub.add_parser("gates"); p.add_argument("--role", required=True, choices=["modern_small", "modern_strong", "efficiency"])
    p.add_argument("--run", required=True); p.add_argument("--reference-run"); p.add_argument("--json-out")
    p = sub.add_parser("cap-calibration"); p.add_argument("--run", required=True); p.add_argument("--tolerance", type=int, default=3)
    p = sub.add_parser("quant-select"); p.add_argument("--a", required=True); p.add_argument("--b", required=True)
    p.add_argument("--a-label", default="Q3_K_M"); p.add_argument("--b-label", default="UD-Q3_K_XL")
    args = ap.parse_args()

    with psycopg.connect(DSN) as conn:
        if args.cmd == "summary":
            out = summarize(load_run(conn, args.run)); out["run_id"] = args.run
        elif args.cmd == "pairwise":
            require_comparable(conn, [args.a, args.b])
            out = pairwise(load_run(conn, args.a), load_run(conn, args.b)); out.update({"a": args.a, "b": args.b})
        elif args.cmd == "oracle":
            require_comparable(conn, [args.weak, args.strong])
            out = post_answer_oracle(load_run(conn, args.weak), load_run(conn, args.strong))
            out.update({"weak": args.weak, "strong": args.strong})
        elif args.cmd == "tiers":
            runs = [r.strip() for r in args.order.split(",") if r.strip()]
            require_comparable(conn, runs)
            out = tier_coverage([(r, load_run(conn, r)) for r in runs])
            out.pop("per_case")
        elif args.cmd == "gates":
            m = summarize(load_run(conn, args.run))
            ref = None
            if args.reference_run:
                ref = summarize(load_run(conn, args.reference_run)); ref["label"] = args.reference_run
            out = evaluate_gates(args.role, m, ref)
            out["run_id"] = args.run
            out["metrics"] = {k: m[k] for k in ("all_pass", "no_output", "p50_wall_ms", "gpu_mem_used_mib")}
            out["gates"] = GATES
        elif args.cmd == "cap-calibration":
            out = cap_calibration(load_run(conn, args.run), args.tolerance); out["run_id"] = args.run
        elif args.cmd == "quant-select":
            out = quant_select(args.a_label, load_run(conn, args.a), args.b_label, load_run(conn, args.b))
            out.update({"a": args.a, "b": args.b})
        else:  # pragma: no cover
            raise SystemExit(2)
    out["gates_digest"] = GATES_DIGEST
    text = json.dumps(out, indent=2, default=str)
    print(text)
    if getattr(args, "json_out", None):
        Path(args.json_out).write_text(text + "\n")


if __name__ == "__main__":
    main()
