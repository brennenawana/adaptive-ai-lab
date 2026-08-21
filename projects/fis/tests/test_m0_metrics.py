"""M0 — the frozen decision rule applied mechanically (NEXT_STEP_M0.md § 7, rev 4).

The properties the mission's adversarial checklist interrogates, as tests:

  * the precedence gate is applied FIRST: n_control_reconfirmed < 10 yields
    RE-SCOPE/INCONCLUSIVE regardless of f_rescue — even at f_rescue = 100%, and
    NEVER a DROP — even at f_rescue = 0%;
  * f_rescue is UNDEFINED at denominator 0, never coerced to 0%;
  * high completion with low rescue does NOT produce a GO;
  * non-reconfirming controls are excluded from every rate and listed separately;
  * DROP requires BOTH the gate passed and f_rescue < 10%.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.m0_classify import PRIMARY_CASES, paired_order
from scripts.m0_metrics import compute

ORDER = dict(paired_order())


def _rows(spec: dict[str, tuple[bool, str]]) -> list[dict[str, str]]:
    """spec: scenario_id -> (reconfirmed, treatment_class)."""
    rows = []
    for sid in PRIMARY_CASES:
        reconfirmed, cls = spec[sid]
        rows.append({
            "scenario_id": sid, "order": ORDER[sid],
            "reconfirmed": str(reconfirmed), "treatment_class": cls,
            "control_stop_reason": "length" if reconfirmed else "stop",
            "control_pass": "False" if reconfirmed else "True",
            "control_output_tokens": "8192", "input_tokens_equal": "True",
        })
    return rows


def _spec(reconfirmed_n: int, classes: str) -> dict[str, tuple[bool, str]]:
    """First `reconfirmed_n` cases reconfirm with the given class string (cycled);
    the rest do not reconfirm (their treatment class is descriptive-only 'a')."""
    out = {}
    for i, sid in enumerate(PRIMARY_CASES):
        if i < reconfirmed_n:
            out[sid] = (True, classes[i % len(classes)])
        else:
            out[sid] = (False, "a")
    return out


def test_precedence_gate_fires_before_bands_even_at_perfect_rescue():
    res = compute(_rows(_spec(9, "a")))          # 9 reconfirm, all rescued
    assert res["metrics"]["n_control_reconfirmed"] == 9
    assert res["metrics"]["f_rescue"] == 1.0
    assert "INCONCLUSIVE" in res["decision"]["row"]
    assert "DROP" not in res["decision"]["row"]


def test_precedence_gate_never_supports_drop_at_zero_rescue():
    res = compute(_rows(_spec(9, "d")))          # 9 reconfirm, zero rescue
    assert "DROP" not in res["decision"]["row"]
    assert "INCONCLUSIVE" in res["decision"]["row"]


def test_f_rescue_undefined_at_zero_denominator_never_zero_percent():
    res = compute(_rows(_spec(0, "a")))
    assert res["metrics"]["f_rescue"] == "UNDEFINED"
    assert res["metrics"]["f_complete"] == "UNDEFINED"
    assert "DROP" not in res["decision"]["row"]


def test_go_band_requires_thirty_percent_rescue():
    res = compute(_rows(_spec(15, "aab")))       # 10 rescues of 15 ≈ 67%
    assert res["decision"]["row"] == "STRONG R7 GO"
    res = compute(_rows(_spec(15, "abbbb")))     # 3 of 15 = 20% → RE-SCOPE
    assert res["decision"]["row"] == "R7 RE-SCOPE"


def test_high_completion_low_rescue_is_never_go():
    # every reconfirmed case completes, but only 1 of 15 passes: f_complete = 100%,
    # f_rescue ≈ 7% — the frozen rule lands on DROP consideration, never GO.
    res = compute(_rows(_spec(15, "abbbbbbbbbbbbbb")))
    assert res["metrics"]["f_complete"] == 1.0
    assert res["decision"]["row"] != "STRONG R7 GO"


def test_drop_requires_gate_passed_and_under_ten_percent():
    res = compute(_rows(_spec(15, "bcd" * 5)))   # 0 rescues of 15 reconfirmed
    assert res["metrics"]["f_rescue"] == 0.0
    assert res["decision"]["row"] == "R7 DROP / R9 MOVES UP"


def test_non_reconfirming_controls_are_listed_not_counted():
    res = compute(_rows(_spec(12, "a")))
    m = res["metrics"]
    assert m["n_control_reconfirmed"] == 12
    assert len(m["non_reconfirmed_cases"]) == 3
    assert m["n_rescue"] == 12                  # the 3 descriptive rows never count
    assert m["f_rescue"] == 1.0


def test_still_truncated_split_and_edge_class_reported():
    res = compute(_rows(_spec(15, "acdae")))
    m = res["metrics"]
    assert m["n_still_truncated"] == m["n_still_truncated_convergent"] + \
           m["n_still_truncated_degenerate"]
    assert m["n_completed_unparseable_edge"] >= 1
