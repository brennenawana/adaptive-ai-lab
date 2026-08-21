"""M-STAT standing-facts regeneration — makes the playbook's quoted cluster-robust
numbers (`docs/research/2026-08-20_AI_Lab_Methodology_Hardware_Strategy.md`
Finding 5) mechanically re-derivable from the committed R6 TEST data instead of
living only as prose.

    mstat_stats.py standing-facts [--json-out artifacts/mstat_standing_facts.json]

Reads (read-only SELECT) `learning.case_scores` for the two frozen R6 TEST arms
(R6-qwen38-q3km-test = arm A, R6-bonsai-test = arm B), joins on `scenario_id`,
and recomputes: per-class paired-difference means, ICC(1), design effect, N_eff,
the cluster-robust paired t (PRIMARY, playbook §4/§8), McNemar exact
(SECONDARY, anti-conservative under clustering), the curtailment-firewall
reproduction (drop classes S11/S12 — the historical class-blocked order's last 16
cases, simulating Bonsai curtailed at case 80), and closed-form MDEs. All
arithmetic is `fis_platform.stats` — this script only loads, joins, and reports.

Every computed headline number is checked against a verified re-derivation
(`_KNOWN_ANSWERS` below) before the artifact is written: a DB drift from the
values this module was built and reviewed against is a STOP condition, not
something to fudge past.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.stats import (  # noqa: E402
    StatsError,
    cluster_corrected_mde_pp,
    cluster_robust_paired_t,
    design_effect,
    effective_n,
    icc1,
    mcnemar_exact,
    mde_pp,
    per_class_means,
)

ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")

RUN_A = "R6-qwen38-q3km-test"   # Qwen3.8 Q3_K_M — arm A
RUN_B = "R6-bonsai-test"        # Bonsai — arm B
CURTAILED_DROP_CLASSES = ("S11", "S12")   # last 16 cases in class-blocked ORDER BY scenario_id

# The doc-quoted targets this artifact reproduces
# (docs/research/2026-08-20_AI_Lab_Methodology_Hardware_Strategy.md Finding 5, line 94).
EXPECTED = {
    "icc": 0.475, "deff": 4.33, "n_eff": 22, "t": 0.98, "headline_pp": 13.5,
    "pd": 0.427, "mcnemar_full": 0.0596, "mcnemar_curtailed": 0.0139,
}

# A verified re-derivation (M-STAT spec) this script's computed values must match before
# the artifact is written. A DB drift from these is a STOP condition — see main().
_KNOWN_ANSWERS = {
    "icc": (0.475032, 1e-5),
    "deff": (4.325221, 1e-5),
    "n_eff": (22.195, 0.01),
    "t": (0.9751, 0.001),
    "grand_mean_pp": (13.541667, 1e-3),
    "b": (27, 0),
    "c": (14, 0),
    "n_discordant": (41, 0),
    "pd": (0.427083, 1e-5),
    "mcnemar_full_p": (0.059584, 1e-5),
    "curtailed_b": (27, 0),
    "curtailed_c": (11, 0),
    "mcnemar_curtailed_p": (0.013853, 1e-5),
}

PRECISION_NOTE = (
    "The doc-quoted MDE figures (TEST 10.9-15.5pp, DEV 21.6pp at pd=.30, ~37pp "
    "cluster-corrected at the realized pd=0.427 — "
    "docs/research/2026-08-20_AI_Lab_Methodology_Hardware_Strategy.md lines 66/84/94) were "
    "derived by 20-100k-replicate Monte Carlo simulation of the exact (McNemar) test. "
    "fis_platform.stats.mde_pp's closed-form normal approximation reproduces them within "
    "~1-2pp (TEST pd=.30: 15.7 vs 15.5; DEV pd=.30: 22.1 vs 21.6; cluster-corrected at "
    "realized pd: ~38.9 vs ~37) and is the committed, mechanically reproducible definition "
    "going forward; the simulation and the closed form are not expected to match exactly."
)


# ------------------------------------------------------------------------- loading

def load_pass_map(conn, run_id: str) -> dict[str, bool]:
    """`{scenario_id: all_pass}` for one run — read-only SELECT, nothing else."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT scenario_id, all_pass FROM learning.case_scores WHERE run_id = %s",
                    (run_id,))
        rows = cur.fetchall()
    if not rows:
        raise SystemExit(f"run {run_id!r} has no persisted case_scores rows")
    return {r["scenario_id"]: bool(r["all_pass"]) for r in rows}


def _round6(obj):
    """Recursively round every float to 6 decimals, for a stable committed artifact."""
    if isinstance(obj, float):
        return round(obj, 6)
    if isinstance(obj, dict):
        return {k: _round6(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round6(v) for v in obj]
    return obj


# ------------------------------------------------------------------------- computation

def compute_standing_facts(a: dict[str, bool], b: dict[str, bool]) -> dict:
    shared = sorted(set(a) & set(b))
    if len(shared) != 96:
        raise SystemExit(f"expected exactly 96 shared scenario_ids between {RUN_A!r} and "
                          f"{RUN_B!r}, got {len(shared)} "
                          f"(a-only {len(set(a) - set(b))}, b-only {len(set(b) - set(a))})")

    pairs = {sid: (a[sid], b[sid]) for sid in shared}
    class_d_means = per_class_means(pairs)
    values_by_class: dict[str, list[int]] = {}
    for sid in shared:
        values_by_class.setdefault(sid[:3], []).append(int(a[sid]) - int(b[sid]))
    if sorted(values_by_class) != sorted(class_d_means):
        raise SystemExit("internal inconsistency: per_class_means and values_by_class disagree "
                          "on the class set")

    icc = icc1(values_by_class)
    deff = design_effect(icc, m=8)
    n_eff = effective_n(96, deff)
    t_result = cluster_robust_paired_t(class_d_means)

    b_count = sum(1 for sid in shared if a[sid] and not b[sid])
    c_count = sum(1 for sid in shared if b[sid] and not a[sid])
    n_discordant = b_count + c_count
    pd_realized = n_discordant / len(shared)
    p_full = mcnemar_exact(b_count, c_count)

    curtailed_ids = [sid for sid in shared if sid[:3] not in CURTAILED_DROP_CLASSES]
    if len(curtailed_ids) != 96 - 16:
        raise SystemExit(f"curtailment reproduction expected to drop exactly 16 cases "
                          f"(classes {CURTAILED_DROP_CLASSES}), dropped "
                          f"{96 - len(curtailed_ids)}")
    curtailed_b = sum(1 for sid in curtailed_ids if a[sid] and not b[sid])
    curtailed_c = sum(1 for sid in curtailed_ids if b[sid] and not a[sid])
    p_curtailed = mcnemar_exact(curtailed_b, curtailed_c)

    mde = {
        "test_unclustered_n96_pd015": mde_pp(pd=0.15, n=96),
        "test_unclustered_n96_pd030": mde_pp(pd=0.30, n=96),
        "dev_unclustered_n48_pd030": mde_pp(pd=0.30, n=48),
        "cluster_corrected_realized_pd_n96": cluster_corrected_mde_pp(pd_realized, 96, deff),
    }

    computed = {
        "n_shared": len(shared),
        "per_class_d_mean": class_d_means,
        "icc": icc,
        "deff": deff,
        "n_eff": n_eff,
        "cluster_robust_t": t_result,
        "grand_mean_pp": t_result["mean_pp"],
        "b": b_count,
        "c": c_count,
        "n_discordant": n_discordant,
        "pd": pd_realized,
        "mcnemar_full_p": p_full,
        "curtailed": {
            "dropped_classes": list(CURTAILED_DROP_CLASSES),
            "n": len(curtailed_ids),
            "b": curtailed_b,
            "c": curtailed_c,
            "n_discordant": curtailed_b + curtailed_c,
            "p": p_curtailed,
        },
        "mde_pp": mde,
    }

    match = {
        "icc": {"computed": icc, "expected": EXPECTED["icc"], "delta": icc - EXPECTED["icc"]},
        "deff": {"computed": deff, "expected": EXPECTED["deff"], "delta": deff - EXPECTED["deff"]},
        "n_eff": {"computed": n_eff, "expected": EXPECTED["n_eff"],
                  "delta": n_eff - EXPECTED["n_eff"]},
        "t": {"computed": t_result["t"], "expected": EXPECTED["t"],
              "delta": t_result["t"] - EXPECTED["t"]},
        "headline_pp": {"computed": t_result["mean_pp"], "expected": EXPECTED["headline_pp"],
                        "delta": t_result["mean_pp"] - EXPECTED["headline_pp"]},
        "pd": {"computed": pd_realized, "expected": EXPECTED["pd"],
               "delta": pd_realized - EXPECTED["pd"]},
        "mcnemar_full": {"computed": p_full, "expected": EXPECTED["mcnemar_full"],
                         "delta": p_full - EXPECTED["mcnemar_full"]},
        "mcnemar_curtailed": {"computed": p_curtailed, "expected": EXPECTED["mcnemar_curtailed"],
                              "delta": p_curtailed - EXPECTED["mcnemar_curtailed"]},
    }

    return {
        "run_ids": {"a": RUN_A, "b": RUN_B},
        "computed": computed,
        "expected": EXPECTED,
        "match": match,
        "precision_note": PRECISION_NOTE,
    }


def check_known_answers(computed: dict) -> list[str]:
    """Compare the headline computed values against the verified re-derivation this
    script was built against. Returns a list of mismatch descriptions (empty = OK)."""
    flat = {
        "icc": computed["icc"], "deff": computed["deff"], "n_eff": computed["n_eff"],
        "t": computed["cluster_robust_t"]["t"], "grand_mean_pp": computed["grand_mean_pp"],
        "b": computed["b"], "c": computed["c"], "n_discordant": computed["n_discordant"],
        "pd": computed["pd"], "mcnemar_full_p": computed["mcnemar_full_p"],
        "curtailed_b": computed["curtailed"]["b"], "curtailed_c": computed["curtailed"]["c"],
        "mcnemar_curtailed_p": computed["curtailed"]["p"],
    }
    problems = []
    for key, (expected, tol) in _KNOWN_ANSWERS.items():
        got = flat[key]
        if abs(got - expected) > tol:
            problems.append(f"{key}: got {got!r}, verified re-derivation says {expected!r} "
                            f"(tolerance {tol})")
    return problems


# ------------------------------------------------------------------------- reporting

def print_summary(facts: dict) -> None:
    c = facts["computed"]
    print("=" * 100)
    print(f"M-STAT standing facts — {facts['run_ids']['a']} (A) vs {facts['run_ids']['b']} (B), "
          f"n={c['n_shared']} shared scenarios, 12 classes x 8")
    print("=" * 100)
    print(f"\n  {'class':<8}{'d_mean':>10}")
    for cls in sorted(c["per_class_d_mean"]):
        print(f"  {cls:<8}{c['per_class_d_mean'][cls]:>10.4f}")

    t = c["cluster_robust_t"]
    print(f"\n  grand mean (paired diff)   {c['grand_mean_pp']:>10.4f} pp")
    print(f"  ICC(1)                     {c['icc']:>10.6f}")
    print(f"  DEFF (m=8)                 {c['deff']:>10.6f}")
    print(f"  N_eff (n=96)               {c['n_eff']:>10.3f}")
    print(f"  cluster-robust t (PRIMARY) t={t['t']:.4f}  df={t['df']}  "
          f"significant_05={t['significant_05']}")
    print(f"  b (A-only) = {c['b']}   c (B-only) = {c['c']}   n_discordant = {c['n_discordant']}"
          f"   pd = {c['pd']:.6f}")
    print(f"  McNemar exact, full        p = {c['mcnemar_full_p']:.6f}  (SECONDARY, "
          f"anti-conservative under clustering)")
    curt = c["curtailed"]
    print(f"  curtailment firewall: drop {curt['dropped_classes']} -> n={curt['n']}  "
          f"b'={curt['b']} c'={curt['c']}  p' = {curt['p']:.6f}")

    mde = c["mde_pp"]
    print("\n  MDE (closed-form, pp):")
    print(f"    TEST n=96, pd=.15         {mde['test_unclustered_n96_pd015']:>8.3f}")
    print(f"    TEST n=96, pd=.30         {mde['test_unclustered_n96_pd030']:>8.3f}")
    print(f"    DEV  n=48, pd=.30         {mde['dev_unclustered_n48_pd030']:>8.3f}")
    print(f"    cluster-corrected @ realized pd={c['pd']:.4f}, DEFF={c['deff']:.4f}: "
          f"{mde['cluster_corrected_realized_pd_n96']:>8.3f}")

    print(f"\n  {'field':<20}{'computed':>14}{'expected':>12}{'delta':>12}")
    for key, m in facts["match"].items():
        print(f"  {key:<20}{m['computed']:>14.6f}{m['expected']:>12.6f}{m['delta']:>12.6f}")

    print(f"\n  precision note: {facts['precision_note']}\n")


# ------------------------------------------------------------------------------- CLI

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("standing-facts",
                       help="regenerate artifacts/mstat_standing_facts.json from the live DB")
    p.add_argument("--json-out", default=str(ROOT / "artifacts" / "mstat_standing_facts.json"))
    args = ap.parse_args()

    if args.cmd != "standing-facts":  # pragma: no cover
        raise SystemExit(2)

    try:
        with psycopg.connect(DSN) as conn:
            a = load_pass_map(conn, RUN_A)
            b = load_pass_map(conn, RUN_B)
        facts = compute_standing_facts(a, b)
    except StatsError as exc:
        raise SystemExit(f"stats computation refused: {exc}") from exc

    problems = check_known_answers(facts["computed"])
    if problems:
        print("STOP — computed values disagree with the verified re-derivation this script "
              "was built and reviewed against. Not writing the artifact:", file=sys.stderr)
        for p_ in problems:
            print(f"  - {p_}", file=sys.stderr)
        raise SystemExit(1)

    print_summary(facts)

    out_path = Path(args.json_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(_round6(facts), indent=2, sort_keys=True) + "\n")
    print(f"written: {out_path}")


if __name__ == "__main__":
    main()
