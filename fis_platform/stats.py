"""M-STAT: cluster-robust statistics for FIS's paired local-arm comparisons.

R6 shipped a headline (+13.5pp, Qwen3.8 vs Bonsai) read as a difference without ever
checking whether the 12 scenario classes it was measured over are independent. They
are not: the adversarial statistical review (`docs/research/2026-08-20_AI_Lab_
Methodology_Hardware_Strategy.md` Finding 5) measured ICC(1)=0.475 on the real
per-class paired differences, which inflates the naive standard error 2.08x and
collapses the suite's 96 paired cases to an effective N of about 22. Under that
correction the same headline is **not significant** (t=0.98, df=11) — a fact the
uncorrected McNemar-exact p-value (0.0596, itself not below .05) already hinted at
but could not properly explain, because McNemar treats the 96 cases as independent
when they are drawn from 12 correlated classes.

This module is the mechanical, re-derivable version of that finding: pure functions,
no I/O, no model inference, stdlib + no scipy/numpy (a normative owner decision —
the ANOVA/t/binomial arithmetic FIS needs has closed forms; a dependency would buy
convenience at the cost of a result nobody here can re-derive by hand). Every
function fails closed (`StatsError`, a `SystemExit` subclass, per house style —
see `fis_platform/provenance.py`) rather than silently computing on malformed,
unbalanced, or under-registered input.

Vocabulary and formulas follow `playbook/04_EXPERIMENT_DESIGN_AND_STATISTICS.md`
§4 (primary/secondary statistic), §7 (decision gates — the INCONCLUSIVE/equivalence
tripwire `describe_null` enforces) and §8 (ICC/DEFF/N_eff/MDE formulas, verdict
vocabulary), with full derivations in `playbook/references/STATISTICS_FORMULAS.md`.

    per_class_means      -> per-class mean paired difference d_i = pass(A) - pass(B)
    icc1                 -> one-way random-effects ANOVA ICC(1) on those d_i
    design_effect / effective_n
    cluster_robust_paired_t  -> PRIMARY statistic (playbook §4): t-test on class means
    mcnemar_exact         -> SECONDARY, anti-conservative under clustering
    mde_pp / cluster_corrected_mde_pp
    verdict / describe_null  -> the CONFIRMED/REFUTED/INCONCLUSIVE/RANKED vocabulary,
                                and the fail-closed refusal of unlicensed equivalence claims
"""

from __future__ import annotations

import re
import statistics as _statistics
from collections.abc import Mapping, Sequence
from math import comb, sqrt

__all__ = [
    "VERDICTS",
    "EquivalenceRefused",
    "StatsError",
    "cluster_corrected_mde_pp",
    "cluster_robust_paired_t",
    "describe_null",
    "design_effect",
    "effective_n",
    "icc1",
    "mcnemar_exact",
    "mde_pp",
    "per_class_means",
    "verdict",
]


class StatsError(SystemExit):
    """A statistics function refused rather than compute on malformed, empty,
    unbalanced, or otherwise untrustworthy input. Fail-closed, per house style
    (`fis_platform/provenance.py`'s `RegistryIntegrityError`/`TransitionRefused`):
    a wrong number that looks like a number is worse than a loud refusal."""


class EquivalenceRefused(StatsError):
    """`describe_null` refused to license an equivalence/"competitive" reading.

    Playbook §7 (global tripwires) / §8 (descriptive vocabulary): a null result
    below its design's MDE is INCONCLUSIVE, never "equivalence" — pre-registration
    fixes who chose the words and when, it cannot supply resolving power the data
    lack. Only a pre-registered term backed by an equivalence margin ±d and a
    passed TOST-style check is licensed to describe such a result."""


# --------------------------------------------------------------- per_class_means

_CLASS_RE = re.compile(r"^[A-Za-z0-9]{3}$")


def per_class_means(pairs: Mapping[str, tuple[bool, bool]]) -> dict[str, float]:
    """Per-class mean of the paired difference `d_i = int(a_pass) - int(b_pass)`.

    `pairs` maps `scenario_id -> (a_pass, b_pass)`; `class = scenario_id[:3]`
    (FIS's scenario-class convention, e.g. "S01-3000000" -> class "S01"). Refuses
    (`StatsError`) an empty input, any scenario_id too short to carry a 3-character
    class prefix, and any class prefix that is not exactly 3 alphanumeric
    characters — a malformed id silently truncated to a wrong class is a wrong
    number that looks right.
    """
    if not pairs:
        raise StatsError("per_class_means: no scenario pairs given — refusing to report an "
                          "empty comparison")
    by_class: dict[str, list[int]] = {}
    for sid, outcome in pairs.items():
        if not isinstance(sid, str) or len(sid) < 3:
            raise StatsError(f"per_class_means: malformed scenario_id {sid!r} — need a string "
                              "of length >= 3 to take a 3-character class prefix")
        cls = sid[:3]
        if not _CLASS_RE.match(cls):
            raise StatsError(f"per_class_means: malformed scenario_id {sid!r} — class prefix "
                              f"{cls!r} is not exactly 3 alphanumeric characters")
        try:
            a_pass, b_pass = outcome
        except (TypeError, ValueError) as exc:
            raise StatsError(f"per_class_means: {sid!r} maps to {outcome!r}, not an "
                              "(a_pass, b_pass) pair") from exc
        by_class.setdefault(cls, []).append(int(bool(a_pass)) - int(bool(b_pass)))

    means: dict[str, float] = {}
    for cls in sorted(by_class):
        d_values = by_class[cls]
        if not d_values:
            raise StatsError(f"per_class_means: class {cls!r} has no scenarios — refusing to "
                              "report an empty class")
        means[cls] = sum(d_values) / len(d_values)
    return means


# --------------------------------------------------------------------------- ICC(1)

def icc1(values_by_class: Mapping[str, Sequence[float]]) -> float:
    """One-way random-effects ANOVA ICC(1) — playbook §8's estimation form.

    `k` classes, balanced `m` items per class (the FIS design is balanced m=8;
    unbalanced input is refused "for now" rather than silently handled by an
    unweighted or Satterthwaite approximation this module does not implement),
    `N = k*m`:

        MSB = SSB / (k - 1)                    (between-class mean square)
        MSW = SSW / (N - k)                    (within-class mean square)
        ICC = (MSB - MSW) / (MSB + (m - 1)*MSW)

    `values_by_class` values MUST be the case-level analysis-unit values — for a
    paired comparison, the per-case paired difference `d_i` (playbook §8: "estimate
    ICC on the actual analysis unit... do not borrow a marginal-arm ICC for a
    paired analysis"), typically `per_class_means`'s per-class *lists*, not its
    per-class *means*.
    """
    if len(values_by_class) < 2:
        raise StatsError(f"icc1: need at least 2 classes, got {len(values_by_class)}")
    sizes = {cls: len(vals) for cls, vals in values_by_class.items()}
    if any(n == 0 for n in sizes.values()):
        empty = sorted(c for c, n in sizes.items() if n == 0)
        raise StatsError(f"icc1: class(es) with no values: {empty}")
    distinct_sizes = set(sizes.values())
    if len(distinct_sizes) != 1:
        raise StatsError(f"icc1: refusing unbalanced classes (the FIS design is balanced m=8) — "
                          f"class sizes {sizes}")
    m = distinct_sizes.pop()
    if m < 2:
        raise StatsError(f"icc1: need at least 2 items per class to estimate within-class "
                          f"variance, got m={m}")

    k = len(values_by_class)
    n_total = k * m
    all_values = [v for vals in values_by_class.values() for v in vals]
    grand_mean = sum(all_values) / n_total

    class_means = {cls: sum(vals) / m for cls, vals in values_by_class.items()}
    ssb = sum(m * (class_means[cls] - grand_mean) ** 2 for cls in values_by_class)
    ssw = sum((v - class_means[cls]) ** 2 for cls, vals in values_by_class.items() for v in vals)

    msb = ssb / (k - 1)
    msw = ssw / (n_total - k)
    denom = msb + (m - 1) * msw
    if denom == 0:
        # every value identical, in every class: zero total variance. ICC is
        # conventionally 0 here (no between-class structure to attribute anything to).
        return 0.0
    return (msb - msw) / denom


def design_effect(icc: float, m: int) -> float:
    """Kish design effect: `DEFF = 1 + (m - 1) * ICC` (playbook §8). `ICC=0` recovers
    `DEFF=1` (no correction needed)."""
    if m < 1:
        raise StatsError(f"design_effect: m (average cluster size) must be >= 1, got {m}")
    return 1 + (m - 1) * icc


def effective_n(n: int, deff: float) -> float:
    """`N_eff = N / DEFF` (playbook §8) — the number of statistically independent
    pairs a clustered suite of size `n` actually carries."""
    if deff <= 0:
        raise StatsError(f"effective_n: deff must be > 0, got {deff}")
    return n / deff


# ------------------------------------------------------------- cluster-robust t

# Two-sided Student's t critical values at alpha=0.05, df 1..30. Standard table
# (e.g. NIST/SEMATECH e-Handbook of Statistical Methods §1.3.6.7.2, or any
# introductory statistics reference — these are the textbook values, not
# project-specific). df=11 -> 2.201, cited in the M-STAT spec as the check value.
_T_CRIT_05: dict[int, float] = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
    8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145,
    15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 21: 2.080,
    22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048,
    29: 2.045, 30: 2.042,
}


def cluster_robust_paired_t(class_means: Mapping[str, float]) -> dict[str, float | int | bool]:
    """Cluster-robust paired t-test on per-class means. **This is the PRIMARY
    statistic** (playbook §4: "cluster-robust paired inference (a t-test on
    per-cluster means, df = clusters - 1) is the primary statistic"; §8's verdict
    vocabulary reads verdicts off this test, not off McNemar).

    One-sample t of the `k` class means against 0:

        t  = mean(class_means) / (sd_sample(class_means) / sqrt(k))
        df = k - 1

    `sd_sample` uses the `n-1` (sample) denominator. `significant_05` looks
    `|t|` up against the embedded two-sided alpha=.05 critical-value table
    (df 1..30); a `df` outside that range is refused rather than approximated.

    Returns `{"t", "df", "mean_pp", "significant_05"}`; `mean_pp` is the grand
    mean of the class means in percentage points (the input `class_means` are
    fractional paired differences, e.g. `per_class_means`'s output).
    """
    k = len(class_means)
    if k < 2:
        raise StatsError(f"cluster_robust_paired_t: need at least 2 classes, got {k}")
    values = list(class_means.values())
    mean = _statistics.mean(values)
    df = k - 1
    sd = _statistics.stdev(values)  # n-1 denominator
    if sd == 0:
        t = 0.0 if mean == 0 else (float("inf") if mean > 0 else float("-inf"))
    else:
        t = mean / (sd / sqrt(k))
    crit = _T_CRIT_05.get(df)
    if crit is None:
        raise StatsError(f"cluster_robust_paired_t: no embedded two-sided alpha=.05 critical "
                          f"value for df={df} (table covers df 1..30)")
    return {"t": t, "df": df, "mean_pp": mean * 100, "significant_05": abs(t) >= crit}


# ------------------------------------------------------------------- McNemar exact

def mcnemar_exact(b: int, c: int) -> float:
    """Standard two-sided exact binomial McNemar test on discordant pairs.

    **SECONDARY under clustering** (playbook §4: "McNemar exact on discordant
    pairs is secondary, MUST be labeled anti-conservative under clustering
    [EXT-STATS-001]") — it treats every discordant pair as an independent
    Bernoulli trial, which is exactly the assumption FIS's measured class ICC
    violates, so it understates the true p-value (over-states significance)
    whenever outcomes cluster by scenario class. Report it alongside, never in
    place of, `cluster_robust_paired_t`.

    `b` = A-pass/B-fail count, `c` = B-pass/A-fail count. No mid-p adjustment, no
    continuity correction:

        n = b + c
        p = min(1, 2 * sum_{i=0}^{min(b,c)} C(n, i) / 2**n)     n == 0 -> p = 1.0
    """
    if b < 0 or c < 0:
        raise StatsError(f"mcnemar_exact: b and c must be non-negative discordant-pair counts, "
                          f"got b={b} c={c}")
    n = b + c
    if n == 0:
        return 1.0
    lo = min(b, c)
    tail = sum(comb(n, i) for i in range(lo + 1))
    return min(1.0, 2 * tail / 2**n)


# ----------------------------------------------------------------------------- MDE

# z_{1-alpha/2} at alpha=.05 (two-sided) and z_{power} at power=.80 — the two
# standard-normal quantiles this module cites and no others, since stdlib has no
# inverse-normal-CDF and this is not the module to add one.
_Z_ALPHA_2SIDED_05 = 1.959964   # Phi^-1(0.975)
_Z_POWER_80 = 0.841621          # Phi^-1(0.80)


def mde_pp(pd: float, n: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """Closed-form normal-approximation minimum detectable effect for a paired
    binary comparison, in percentage points (playbook §8):

        MDE ~= (z_{1-alpha/2} + z_power) * sqrt(pd / n)          (then *100 for pp)

    `pd` is the expected discordance rate (share of item-pairs where the arms
    disagree); `n` is the (effective) sample size — pass raw N for the unclustered
    MDE, or `N_eff` directly for a pre-clustered figure (see
    `cluster_corrected_mde_pp` for the usual clustered path).

    Only the pre-registered operating point alpha=.05/power=.80 is supported: the
    two z-constants above are embedded literally (no scipy/numpy per the owner's
    stdlib-only decision, and stdlib has no inverse-normal-CDF to compute others
    from). A different alpha/power needs its own cited z-value before this
    function can serve it, and is refused rather than silently approximated.

    **Precision boundary, stated once here.** The normative docs' quoted MDE
    figures — TEST(96) 10.9-15.5pp and DEV(48) 21.6pp at pd=.30, and ~37pp
    cluster-corrected at the realized pd=0.427
    (`docs/research/2026-08-20_AI_Lab_Methodology_Hardware_Strategy.md` lines
    66, 84, 94) — were derived by 20-100k-replicate Monte Carlo simulation of the
    *exact* (McNemar) test, not this closed form. This closed form reproduces
    them within ~1-2pp (TEST pd=.30: 15.7 vs 15.5; DEV pd=.30: 22.1 vs 21.6;
    cluster-corrected at realized pd: ~38.9 vs ~37) and is the committed,
    mechanically reproducible definition going forward — cite this boundary
    whenever this function's output is compared against those doc figures.
    """
    if alpha != 0.05 or power != 0.80:
        raise StatsError(f"mde_pp: only alpha=0.05/power=0.80 is supported (got alpha={alpha}, "
                          f"power={power}) — the embedded z-constants cover only that operating "
                          "point; stdlib has no inverse-normal-CDF to derive another")
    if pd < 0:
        raise StatsError(f"mde_pp: pd (discordance rate) must be >= 0, got {pd}")
    if n <= 0:
        raise StatsError(f"mde_pp: n must be > 0, got {n}")
    z = _Z_ALPHA_2SIDED_05 + _Z_POWER_80
    return z * sqrt(pd / n) * 100


def cluster_corrected_mde_pp(pd: float, n: float, deff: float, alpha: float = 0.05,
                              power: float = 0.80) -> float:
    """`mde_pp(pd, n) * sqrt(deff)` — equivalently `mde_pp(pd, n / deff)`, since
    `N_eff = n / deff` (playbook §8). The clustered MDE a design with design
    effect `deff` can actually resolve; see `mde_pp`'s docstring for the
    simulation-vs-closed-form precision boundary this inherits."""
    if deff <= 0:
        raise StatsError(f"cluster_corrected_mde_pp: deff must be > 0, got {deff}")
    return mde_pp(pd, n, alpha=alpha, power=power) * sqrt(deff)


# ------------------------------------------------------------------- verdict vocabulary

VERDICTS = ("CONFIRMED", "REFUTED", "INCONCLUSIVE", "RANKED")


def verdict(*, delta_pp: float, mde_pp: float, p_primary: float, alpha: float = 0.05,
            direction_predicted: int = 0) -> str:
    """Read a verdict off the pre-registered primary test (playbook §8's verdict
    vocabulary table). Returns one of `CONFIRMED`, `REFUTED`, `INCONCLUSIVE`
    (never `RANKED`, which is a screening-comparison outcome this function does
    not produce — see `VERDICTS`):

    - **CONFIRMED**: `p_primary < alpha` AND `abs(delta_pp) >= mde_pp` AND the
      sign of `delta_pp` matches `direction_predicted`.
    - **REFUTED**: `p_primary < alpha` AND the sign of `delta_pp` opposes
      `direction_predicted`.
    - **INCONCLUSIVE**: every other case — including a significant result with
      no direction predicted (`direction_predicted == 0`), and any non-significant
      result regardless of how large `delta_pp` looks. Per §8: "INCONCLUSIVE ...
      the one every non-crossing result takes, whatever the size of the observed
      effect."

    `direction_predicted` is `+1` (predicted A > B), `-1` (predicted A < B), or
    `0` (no directional prediction — the run can then only ever be CONFIRMED or
    INCONCLUSIVE... in fact never CONFIRMED either, since sign-matching an
    undeclared direction is undefined; it lands INCONCLUSIVE).
    """
    if direction_predicted not in (-1, 0, 1):
        raise StatsError(f"verdict: direction_predicted must be -1, 0, or +1, got "
                          f"{direction_predicted!r}")
    significant = p_primary < alpha
    sign = 1 if delta_pp > 0 else (-1 if delta_pp < 0 else 0)
    if significant and abs(delta_pp) >= mde_pp and direction_predicted != 0 and sign == direction_predicted:
        return "CONFIRMED"
    if significant and direction_predicted != 0 and sign == -direction_predicted:
        return "REFUTED"
    return "INCONCLUSIVE"


def describe_null(delta_pp: float, mde_pp: float,
                   descriptive_vocabulary: list[dict[str, str]] | None = None,
                   term: str | None = None) -> str:
    """Describe a null (non-crossing) result — REFUSING any equivalence or
    "competitive" reading unless it is licensed by a pre-registered term.

    Playbook §7 (global tripwires) / §8 (descriptive vocabulary): a null below
    its design's MDE is **INCONCLUSIVE, never equivalence**. Pre-registration
    fixes who chose the words and when; it cannot supply resolving power the data
    lack. Raises `EquivalenceRefused` when `term is None` or when
    `descriptive_vocabulary` is empty/`None` or does not contain `term` — the
    caller's only correct move on refusal is to report INCONCLUSIVE with the
    interval and `mde_pp`, not to reach for descriptive language.

    `descriptive_vocabulary` is `[{"term": ..., "definition": ...}, ...]`,
    pre-registered *before data* (§8): each entry MUST NOT itself assert
    equivalence or direction — enforcing that content constraint is the
    contract-authoring step's job, not this function's; this function only
    enforces that the term used was one of the pre-registered ones.
    """
    if term is None or not descriptive_vocabulary:
        raise EquivalenceRefused(
            f"describe_null: refusing an equivalence/descriptive reading of delta={delta_pp:+.2f}pp "
            f"(MDE={mde_pp:.2f}pp) — no pre-registered descriptive_vocabulary/term given. A null "
            "below MDE is INCONCLUSIVE; report it with its interval and MDE, not descriptive "
            "language.")
    registered = {entry["term"]: entry["definition"] for entry in descriptive_vocabulary}
    if term not in registered:
        raise EquivalenceRefused(
            f"describe_null: term {term!r} is not in the pre-registered descriptive_vocabulary "
            f"(known terms: {sorted(registered)}) — pre-registration fixes who chose the words "
            "and when, it cannot supply resolving power the data lack. Report INCONCLUSIVE "
            "instead.")
    return (f"{term}: {registered[term]} "
            f"(delta={delta_pp:+.2f}pp, MDE={mde_pp:.2f}pp — design could not resolve this)")
