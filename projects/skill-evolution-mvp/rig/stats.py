"""Paired bootstrap over tasks (paper App. C: 1,000 resamples), stdlib only,
per lab convention. Verdict vocabulary matches fis_platform/stats.py."""

import random

VERDICTS = ("CONFIRMED", "REFUTED", "INCONCLUSIVE", "RANKED")


def paired_bootstrap(scores_a: list[float], scores_b: list[float],
                     n_boot: int = 1000, seed: int = 20260830) -> dict:
    """H1: mean(b) > mean(a), paired by task. Returns point delta, one-sided
    p, and a 95% percentile CI on the delta."""
    assert len(scores_a) == len(scores_b) and scores_a, "paired inputs required"
    n = len(scores_a)
    deltas = [b - a for a, b in zip(scores_a, scores_b)]
    point = sum(deltas) / n
    rng = random.Random(seed)
    boot = []
    for _ in range(n_boot):
        s = sum(deltas[rng.randrange(n)] for _ in range(n)) / n
        boot.append(s)
    boot.sort()
    p_one_sided = sum(1 for x in boot if x <= 0) / n_boot
    lo = boot[int(0.025 * n_boot)]
    hi = boot[int(0.975 * n_boot) - 1]
    return {"n_tasks": n, "delta": point, "p_one_sided": p_one_sided,
            "ci95": [lo, hi], "n_boot": n_boot, "seed": seed}
