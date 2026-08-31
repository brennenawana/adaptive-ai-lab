"""SE-1 verdict computation, exactly as pre-registered in contract §9.

Primary: arm C vs arm A on TEST. Per-task score for an evolved arm = mean over
its 3 seeds; arm A is a single evaluation. Paired bootstrap over tasks, 1,000
resamples, one-sided, alpha = 0.05, effect floor +5 points.
Secondary (RANKED, not confirmatory): C vs B vs A on accuracy and on
cost-per-completed-task. Also reconciles runs/spend.json from the per-run
ledgers (SE-1 §18 Amendment 2).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rig import config, stats  # noqa: E402

RUNS = config.RUNS_DIR


def per_task(run_id: str) -> dict:
    data = json.loads((RUNS / run_id / "eval_test.json").read_text())
    return {str(r["id"]): r["soft"] for r in data["per_task"]}


def arm_scores(eval_ids: list) -> dict:
    seeds = [per_task(e) for e in eval_ids]
    ids = sorted(seeds[0])
    return {tid: sum(s[tid] for s in seeds) / len(seeds) for tid in ids}


def ledger_spend(run_id: str) -> float:
    led = RUNS / run_id / "ledger.jsonl"
    if not led.exists():
        return 0.0
    return sum(json.loads(l).get("usd", 0)
               for l in led.read_text().splitlines()
               if '"api_call"' in l)


def main():
    a = per_task("eval-A-s1-test")
    b = arm_scores(["eval-B-s1-test", "eval-B-s2-test", "eval-B-s3-test"])
    c = arm_scores(["eval-C-s1-test", "eval-C-s2-test", "eval-C-s3-test"])
    ids = sorted(a)
    assert sorted(b) == ids == sorted(c), "task id mismatch across arms"

    mean = lambda d: sum(d.values()) / len(d)
    primary = stats.paired_bootstrap([a[t] for t in ids], [c[t] for t in ids])
    secondary_cb = stats.paired_bootstrap([b[t] for t in ids], [c[t] for t in ids])
    secondary_ba = stats.paired_bootstrap([a[t] for t in ids], [b[t] for t in ids])

    delta_pp = primary["delta"] * 100
    confirmed = primary["p_one_sided"] < 0.05 and delta_pp >= 5.0
    refuted = delta_pp <= 0 or (primary["ci95"][1] * 100) < 5.0
    verdict = "CONFIRMED" if confirmed else ("REFUTED" if refuted else "INCONCLUSIVE")

    # Costs: evolution (discovery) per arm, and TEST inference per arm.
    evo = {"B": sum(ledger_spend(f"B-s{s}") for s in (1, 2, 3)),
           "C": sum(ledger_spend(f"C-s{s}") for s in (1, 2, 3)),
           "A": ledger_spend("A-s1")}
    test_inf = {"A": ledger_spend("eval-A-s1-test"),
                "B": sum(ledger_spend(f"eval-B-s{s}-test") for s in (1, 2, 3)),
                "C": sum(ledger_spend(f"eval-C-s{s}-test") for s in (1, 2, 3))}
    solved = {"A": sum(a.values()), "B": sum(b.values()) * 3 / 3,
              "C": sum(c.values())}
    econ = {}
    for arm in ("A", "B", "C"):
        n_evals = 1 if arm == "A" else 3
        per_eval_solved = solved[arm]
        econ[arm] = {
            "evolution_usd": round(evo[arm], 2),
            "test_inference_usd_per_eval": round(test_inf[arm] / n_evals, 2),
            "solved_per_100": round(per_eval_solved, 1),
            "inference_usd_per_solved_task": round(
                (test_inf[arm] / n_evals) / max(per_eval_solved, 1e-9), 4),
        }

    out = {
        "contract": "SE1",
        "computed_at": "2026-08-31",
        "n_tasks": len(ids),
        "test_means": {"A": round(mean(a), 4), "B": round(mean(b), 4),
                       "C": round(mean(c), 4)},
        "per_seed_test": {
            "B": [round(mean(per_task(f"eval-B-s{s}-test")), 3) for s in (1, 2, 3)],
            "C": [round(mean(per_task(f"eval-C-s{s}-test")), 3) for s in (1, 2, 3)],
        },
        "primary_C_vs_A": {**primary, "delta_pp": round(delta_pp, 2)},
        "secondary_C_vs_B": {**secondary_cb,
                             "delta_pp": round(secondary_cb["delta"] * 100, 2)},
        "secondary_B_vs_A": {**secondary_ba,
                             "delta_pp": round(secondary_ba["delta"] * 100, 2)},
        "verdict_primary": verdict,
        "effect_floor_pp": 5.0,
        "economics": econ,
    }
    (RUNS / "VERDICT.json").write_text(json.dumps(out, indent=2))

    # Spend reconciliation from ledgers (authoritative), Amendment 2.
    recon = {"global": 0.0, "phases": {}, "runs": {}, "reconciled_from_ledgers": True}
    for d in sorted(RUNS.iterdir()):
        led = d / "ledger.jsonl"
        if not d.is_dir() or not led.exists():
            continue
        rows = [json.loads(l) for l in led.read_text().splitlines()]
        for r in rows:
            if r.get("kind") != "api_call":
                continue
            usd = r.get("usd", 0)
            recon["global"] += usd
            recon["phases"][r.get("phase", "?")] = \
                recon["phases"].get(r.get("phase", "?"), 0) + usd
            recon["runs"][d.name] = recon["runs"].get(d.name, 0) + usd
    recon = json.loads(json.dumps(recon), parse_float=lambda x: round(float(x), 4))
    (RUNS / "spend.json").write_text(json.dumps(recon, indent=2))

    print(json.dumps({k: out[k] for k in
                      ("test_means", "per_seed_test", "primary_C_vs_A",
                       "secondary_C_vs_B", "verdict_primary", "economics")},
                     indent=2))
    print("reconciled program total:", round(recon["global"], 2))


if __name__ == "__main__":
    main()
