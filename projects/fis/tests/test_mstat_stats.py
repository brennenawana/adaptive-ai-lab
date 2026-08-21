"""M-STAT known-answer tests for fis_platform/stats.py — pure, no DB dependency.

`CASE_LEVEL_FIXTURE` below is a frozen historical snapshot: the 96 paired
(a_pass, b_pass) outcomes for run_ids R6-qwen38-q3km-test (arm A, "Qwen3.8 Q3_K_M")
and R6-bonsai-test (arm B, "Bonsai"), read ONCE (read-only SELECT) from
learning.case_scores while implementing this module and embedded here literally.
This is reading committed history for a known-answer test, never rewriting it — the
values reproduce the per-class pass counts already published in the M-STAT spec
(qwen [7,3,7,8,6,2,0,7,7,0,0,0], bonsai [1,7,0,3,6,1,0,7,2,4,3,0], of 8 per class
S01..S12) and, via `scripts/mstat_stats.py standing-facts`, the ICC/DEFF/N_eff/t/
McNemar figures this file checks against.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.stats import (  # noqa: E402
    EquivalenceRefused,
    StatsError,
    cluster_corrected_mde_pp,
    cluster_robust_paired_t,
    describe_null,
    design_effect,
    effective_n,
    icc1,
    mcnemar_exact,
    mde_pp,
    per_class_means,
    verdict,
)

# Frozen historical snapshot: 96 shared scenarios, run_ids R6-qwen38-q3km-test (A) and
# R6-bonsai-test (B), joined on scenario_id, ordered by scenario_id within class.
# class -> [(a_pass, b_pass), ...] x8.
CASE_LEVEL_FIXTURE: dict[str, list[tuple[bool, bool]]] = {
    "S01": [(True, False), (True, False), (False, False), (True, True), (True, False),
            (True, False), (True, False), (True, False)],
    "S02": [(False, True), (True, True), (True, True), (True, True), (False, True),
            (False, True), (False, True), (False, False)],
    "S03": [(False, False), (True, False), (True, False), (True, False), (True, False),
            (True, False), (True, False), (True, False)],
    "S04": [(True, False), (True, False), (True, False), (True, True), (True, True),
            (True, False), (True, False), (True, True)],
    "S05": [(True, True), (True, False), (True, True), (False, True), (True, True),
            (True, True), (False, False), (True, True)],
    "S06": [(False, False), (False, False), (True, False), (False, False), (False, False),
            (False, True), (True, False), (False, False)],
    "S07": [(False, False), (False, False), (False, False), (False, False), (False, False),
            (False, False), (False, False), (False, False)],
    "S08": [(True, True), (True, True), (True, True), (True, True), (True, True),
            (False, True), (True, True), (True, False)],
    "S09": [(True, False), (True, False), (True, False), (False, False), (True, True),
            (True, True), (True, False), (True, False)],
    "S10": [(False, True), (False, False), (False, False), (False, True), (False, False),
            (False, True), (False, True), (False, False)],
    "S11": [(False, True), (False, False), (False, False), (False, False), (False, True),
            (False, False), (False, True), (False, False)],
    "S12": [(False, False), (False, False), (False, False), (False, False), (False, False),
            (False, False), (False, False), (False, False)],
}

# Known answers, verified re-derivation (see M-STAT spec / scripts/mstat_stats.py).
ICC_KNOWN = 0.475032
DEFF_KNOWN = 4.325221
N_EFF_KNOWN = 22.195
T_KNOWN = 0.9751
DF_KNOWN = 11
MEAN_PP_KNOWN = 13.541667
B_FULL, C_FULL = 27, 14
P_FULL_KNOWN = 0.059584
B_CURT, C_CURT = 27, 11
P_CURT_KNOWN = 0.013853


def _values_by_class() -> dict[str, list[int]]:
    """Case-level d_i = int(a) - int(b) per class, the ICC analysis unit."""
    return {cls: [int(a) - int(b) for a, b in pairs] for cls, pairs in CASE_LEVEL_FIXTURE.items()}


def _pairs_flat() -> dict[str, tuple[bool, bool]]:
    """Flatten the fixture into per_class_means's expected scenario_id -> (a, b) shape."""
    out: dict[str, tuple[bool, bool]] = {}
    for cls, pairs in CASE_LEVEL_FIXTURE.items():
        for i, (a, b) in enumerate(pairs):
            out[f"{cls}-{3000000 + i * 1000}"] = (a, b)
    return out


# --------------------------------------------------------------------- per_class_means

def test_per_class_means_matches_known_class_means():
    means = per_class_means(_pairs_flat())
    assert set(means) == set(CASE_LEVEL_FIXTURE)
    # cross-check against the case-level fixture directly
    for cls, pairs in CASE_LEVEL_FIXTURE.items():
        expected = sum(int(a) - int(b) for a, b in pairs) / len(pairs)
        assert means[cls] == pytest.approx(expected, abs=1e-9)
    assert means["S01"] == pytest.approx(0.75, abs=1e-9)
    assert means["S07"] == pytest.approx(0.0, abs=1e-9)


def test_per_class_means_refuses_empty_input():
    with pytest.raises(StatsError):
        per_class_means({})


def test_per_class_means_refuses_malformed_id():
    with pytest.raises(StatsError):
        per_class_means({"AB": (True, False)})          # too short for a 3-char class
    with pytest.raises(StatsError):
        per_class_means({"S0!-1000": (True, False)})    # class prefix not alphanumeric
    with pytest.raises(StatsError):
        per_class_means({"": (True, False)})             # empty id


# ------------------------------------------------------------------------------- icc1

def test_icc1_known_answer():
    icc = icc1(_values_by_class())
    assert icc == pytest.approx(ICC_KNOWN, abs=1e-5)


def test_icc1_refuses_unbalanced_groups():
    unbalanced = {"S01": [1, 0, 1], "S02": [1, 0]}
    with pytest.raises(StatsError):
        icc1(unbalanced)


def test_icc1_refuses_fewer_than_two_classes():
    with pytest.raises(StatsError):
        icc1({"S01": [1, 0, 1, 0]})


# ------------------------------------------------------------------- design effect / N_eff

def test_design_effect_and_effective_n_known_answers():
    icc = icc1(_values_by_class())
    deff = design_effect(icc, m=8)
    assert deff == pytest.approx(DEFF_KNOWN, abs=1e-5)
    n_eff = effective_n(96, deff)
    assert n_eff == pytest.approx(N_EFF_KNOWN, abs=0.01)


def test_design_effect_icc_zero_is_deff_one():
    assert design_effect(0.0, m=8) == pytest.approx(1.0)


# ----------------------------------------------------------------- cluster_robust_paired_t

def test_cluster_robust_paired_t_known_answer():
    class_means = per_class_means(_pairs_flat())
    result = cluster_robust_paired_t(class_means)
    assert result["t"] == pytest.approx(T_KNOWN, abs=1e-3)
    assert result["df"] == DF_KNOWN
    assert result["mean_pp"] == pytest.approx(MEAN_PP_KNOWN, abs=1e-3)
    assert result["significant_05"] is False   # |0.9751| < 2.201 (df=11 critical value)


def test_cluster_robust_paired_t_refuses_single_class():
    with pytest.raises(StatsError):
        cluster_robust_paired_t({"S01": 0.5})


# ------------------------------------------------------------------------- mcnemar_exact

def test_mcnemar_exact_known_answers():
    assert mcnemar_exact(B_FULL, C_FULL) == pytest.approx(P_FULL_KNOWN, abs=1e-5)
    assert mcnemar_exact(B_CURT, C_CURT) == pytest.approx(P_CURT_KNOWN, abs=1e-5)


def test_mcnemar_exact_zero_discordant_pairs_is_one():
    assert mcnemar_exact(0, 0) == 1.0


def test_mcnemar_exact_refuses_negative_counts():
    with pytest.raises(StatsError):
        mcnemar_exact(-1, 3)


# ------------------------------------------------------------------------------- MDE

def test_mde_pp_monotone_in_pd_and_n():
    small_pd = mde_pp(pd=0.15, n=96)
    large_pd = mde_pp(pd=0.30, n=96)
    assert small_pd < large_pd   # larger discordance -> larger resolvable MDE

    small_n = mde_pp(pd=0.30, n=200)
    large_n = mde_pp(pd=0.30, n=48)
    assert small_n < large_n     # more items -> smaller (tighter) MDE


def test_mde_pp_reproduces_documented_figures_within_precision_boundary():
    # TEST(96) pd=.30 doc figure 15.5pp, closed form ~15.7pp
    assert mde_pp(pd=0.30, n=96) == pytest.approx(15.5, abs=2.0)
    # DEV(48) pd=.30 doc figure 21.6pp, closed form ~22.1pp
    assert mde_pp(pd=0.30, n=48) == pytest.approx(21.6, abs=2.0)


def test_cluster_corrected_mde_equals_unclustered_times_sqrt_deff():
    pd, n, deff = 0.4270833333333333, 96, DEFF_KNOWN
    corrected = cluster_corrected_mde_pp(pd, n, deff)
    manual = mde_pp(pd, n) * (deff ** 0.5)
    assert corrected == pytest.approx(manual, abs=1e-9)
    equivalent = mde_pp(pd, n / deff)
    assert corrected == pytest.approx(equivalent, abs=1e-6)
    # doc figure ~37pp cluster-corrected at realized pd, closed form ~38.9pp
    assert corrected == pytest.approx(37.0, abs=3.0)


def test_mde_pp_refuses_unsupported_operating_point():
    with pytest.raises(StatsError):
        mde_pp(pd=0.3, n=96, alpha=0.10)
    with pytest.raises(StatsError):
        mde_pp(pd=0.3, n=96, power=0.90)


# --------------------------------------------------------------------------- verdict

def test_verdict_confirmed_when_significant_crosses_mde_and_sign_matches():
    v = verdict(delta_pp=20.0, mde_pp=10.0, p_primary=0.01, alpha=0.05, direction_predicted=1)
    assert v == "CONFIRMED"


def test_verdict_refuted_when_significant_and_sign_opposes_prediction():
    v = verdict(delta_pp=-20.0, mde_pp=10.0, p_primary=0.01, alpha=0.05, direction_predicted=1)
    assert v == "REFUTED"


def test_verdict_inconclusive_when_null_below_mde():
    # R6's actual headline: not significant cluster-robustly (t=0.98, df=11)
    v = verdict(delta_pp=13.5, mde_pp=38.9, p_primary=0.36, alpha=0.05, direction_predicted=1)
    assert v == "INCONCLUSIVE"


def test_verdict_inconclusive_when_significant_but_below_mde():
    # significant p-value but the effect is smaller than the design's own MDE
    v = verdict(delta_pp=5.0, mde_pp=10.0, p_primary=0.01, alpha=0.05, direction_predicted=1)
    assert v == "INCONCLUSIVE"


def test_verdict_inconclusive_when_no_direction_predicted():
    v = verdict(delta_pp=20.0, mde_pp=10.0, p_primary=0.01, alpha=0.05, direction_predicted=0)
    assert v == "INCONCLUSIVE"


# ---------------------------------------------------------------------- describe_null

def test_describe_null_refuses_unregistered_term():
    with pytest.raises(EquivalenceRefused):
        describe_null(5.0, 38.9, descriptive_vocabulary=None, term=None)
    with pytest.raises(EquivalenceRefused):
        describe_null(5.0, 38.9, descriptive_vocabulary=[{"term": "competitive", "definition": "x"}],
                      term="equivalent")           # not the pre-registered term
    with pytest.raises(EquivalenceRefused):
        describe_null(5.0, 38.9, descriptive_vocabulary=[], term="competitive")  # empty vocab


def test_describe_null_licenses_a_registered_term():
    vocab = [{"term": "gross-gate-only", "definition": "not resolved below the design's MDE; "
                                                          "no comparative claim is made"}]
    result = describe_null(5.0, 38.9, descriptive_vocabulary=vocab, term="gross-gate-only")
    assert "gross-gate-only" in result
    assert "not resolved below the design's MDE" in result
