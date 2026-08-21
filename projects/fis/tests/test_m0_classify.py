"""M0 — frozen paired order + truncation classification rubric (NEXT_STEP_M0.md § 6-B).

The paired-order test hardcodes the ENTIRE expected schedule: the AB/BA assignment is
pre-registered evidence, so the test is a byte-exact restatement, not a re-derivation
through the same code path.

The rubric fixtures are synthetic by necessity (no historical reasoning text exists —
R6 persisted only lengths) and cover all four outcome classes plus the pre-declared
edges: length-stop-that-passes (a rescue), completed-unparseable (e), cut-inside-the-
answer (convergent by pre-declaration), and empty-everything (no_reasoning).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.m0_classify import (
    CONTROL_CAP,
    PRIMARY_CASES,
    TREATMENT_TARGET_CAP,
    classify_treatment,
    paired_order,
    truncation_shape,
)

# The pre-registered schedule, restated literally (NEXT_STEP_M0.md § 6-B: lexicographic
# by scenario_id; even 0-based index → AB control-first; odd → BA treatment-first).
EXPECTED_SCHEDULE = [
    ("S02-1001001", "AB"), ("S02-1002001", "BA"), ("S05-1002004", "AB"),
    ("S06-1001005", "BA"), ("S07-1000006", "AB"), ("S07-1001006", "BA"),
    ("S07-1002006", "AB"), ("S08-1002007", "BA"), ("S10-1000009", "AB"),
    ("S10-1001009", "BA"), ("S11-1000010", "AB"), ("S11-1001010", "BA"),
    ("S11-1002010", "AB"), ("S12-1000011", "BA"), ("S12-1001011", "AB"),
]


def test_primary_population_is_the_pre_registered_fifteen():
    assert len(PRIMARY_CASES) == 15
    assert len(set(PRIMARY_CASES)) == 15
    assert sorted(PRIMARY_CASES) == list(PRIMARY_CASES)
    assert {sid[:3] for sid in PRIMARY_CASES} == {"S02", "S05", "S06", "S07", "S08",
                                                  "S10", "S11", "S12"}
    # every seed in the TRAIN range (1,00x,xxx seeds — never 2M dev / 3M test)
    assert all(sid.split("-")[1].startswith("100") for sid in PRIMARY_CASES)
    assert (CONTROL_CAP, TREATMENT_TARGET_CAP) == (8192, 12288)


def test_paired_order_is_the_pre_registered_schedule_exactly():
    assert paired_order() == EXPECTED_SCHEDULE


def test_paired_order_is_deterministic_and_input_order_free():
    shuffled = tuple(reversed(PRIMARY_CASES))
    assert paired_order(shuffled) == EXPECTED_SCHEDULE
    assert paired_order() == paired_order()


# ------------------------------------------------------------------ fixtures

def _convergent_text() -> str:
    """Progressive reasoning: new evidence ids and a new hypothesis to the end."""
    parts = []
    for i in range(60):
        parts.append(
            f"Step {i}: entry led_00{i}12{i} posted at offset {i * 37} suggests the "
            f"mapping version v{i} changed; webhook wh_9{i}83{i} arrived after event "
            f"evt_5{i}77 so the ordering matters here and points away from a simple "
            f"duplicate_webhook_handled reading toward account {i * 991 + 100003}.")
    parts.append("Late finding: ledger sequence 88231 vs 88230 inverted — this is a "
                 "reversal_race signature, seen first at posting_seq 77120 just now.")
    return " ".join(parts)


def _degenerate_text() -> str:
    """A verbatim loop: the same paragraph re-emitted, no new material at the tail."""
    para = ("The webhook was delivered twice so the settlement may be a duplicate. "
            "But the ledger shows one entry. The webhook was delivered twice so the "
            "settlement may be a duplicate_webhook_handled case. Checking again. ")
    return para * 80


def test_convergent_fixture_classifies_convergent():
    shape = truncation_shape(_convergent_text())
    assert shape.verdict == "convergent"
    assert shape.tail_new_evidence          # new ids keep appearing
    assert shape.distinct_hypotheses >= 2


def test_degenerate_fixture_classifies_degenerate():
    shape = truncation_shape(_degenerate_text())
    assert shape.verdict == "degenerate"
    assert len(shape.fired) >= 2
    assert shape.dup_rate > 0.5
    assert shape.tail_novelty < 0.10
    assert not shape.tail_new_evidence and not shape.tail_new_hypothesis


def test_cut_inside_answer_is_convergent_by_pre_declaration():
    shape = truncation_shape(None, content_text='{"case_id": "CASE-9", "root')
    assert shape.verdict == "convergent"
    assert shape.reasoning_chars == 0 and shape.content_chars > 0


def test_empty_everything_is_no_reasoning_not_a_silent_bin():
    assert truncation_shape(None, None).verdict == "no_reasoning"
    assert truncation_shape("", "").verdict == "no_reasoning"


def test_rubric_is_deterministic():
    a, b = truncation_shape(_degenerate_text()), truncation_shape(_degenerate_text())
    assert (a.dup_rate, a.tail_novelty, a.fired, a.verdict) == \
           (b.dup_rate, b.tail_novelty, b.fired, b.verdict)


# ------------------------------------------------------------------ outcome classes

def test_pass_is_a_rescue_whatever_the_stop_reason():
    for stop in ("stop", "length", None):
        cls, shape = classify_treatment(stop_reason=stop, passed=True, parseable=True,
                                        reasoning_text="r", content_text=None)
        assert cls == "a" and shape is None


def test_parseable_complete_fail_is_b():
    cls, _ = classify_treatment(stop_reason="stop", passed=False, parseable=True,
                                reasoning_text="r", content_text=None)
    assert cls == "b"


def test_still_truncated_splits_c_and_d_by_the_rubric():
    cls_c, shape_c = classify_treatment(stop_reason="length", passed=False,
                                        parseable=False,
                                        reasoning_text=_convergent_text(),
                                        content_text=None)
    cls_d, shape_d = classify_treatment(stop_reason="length", passed=False,
                                        parseable=False,
                                        reasoning_text=_degenerate_text(),
                                        content_text=None)
    assert (cls_c, shape_c.verdict) == ("c", "convergent")
    assert (cls_d, shape_d.verdict) == ("d", "degenerate")


def test_completed_unparseable_is_the_pre_declared_e_edge():
    cls, shape = classify_treatment(stop_reason="stop", passed=False, parseable=False,
                                    reasoning_text="r", content_text="not json")
    assert cls == "e" and shape is None
