"""R6 gates and TRAIN rules are pure functions of recorded metrics — pin them.

Nothing here touches the database or the registry: rows are synthesized in the shape
`scripts/r6_metrics.load_run` returns (score payload + trajectory payload)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.r6_gates import GATES, GATES_DIGEST, evaluate_gates  # noqa: E402
from fis_platform.routing.learn import digest  # noqa: E402
from scripts.r6_metrics import (  # noqa: E402
    cap_calibration, pairwise, post_answer_oracle, quant_select, summarize, tier_coverage,
)


def _row(sid: str, *, all_pass: bool, rc=True, ev=1.0, act=True, ver=True, out_tok=1000,
         stop="stop", wall=10000, no_output=False, unsupported=0) -> dict:
    dims = [{"name": "root_cause", "value": 1.0 if rc else 0.0, "passed": rc, "detail": ""}]
    if no_output:
        dims.append({"name": "produced_output", "value": 0.0, "passed": False, "detail": "none"})
    score = {"all_pass": all_pass, "root_cause_correct": rc, "required_evidence_recall": ev,
             "evidence_recall_threshold": 0.8, "next_action_acceptable": act,
             "verifier_passed": ver, "unsupported_claims": unsupported,
             "forbidden_claim_made": False, "wall_ms": wall, "api_ms": wall - 100,
             "dimensions": dims}
    traj = {"model_invocations": [{"usage": {"input_tokens": 3000, "output_tokens": out_tok},
                                   "stop_reason": stop, "latency": {"api_ms": wall - 100},
                                   "reasoning_chars": 10}],
            "runtime_context": {"gpu_mem_used_mib_start": "7000", "gpu_mem_used_mib_end": "7100"}}
    return {"scenario_id": sid, "all_pass": all_pass, "score": score, "traj": traj,
            "split": "dev", "truth": "x"}


def _run(passes: dict[str, bool], **kw) -> dict:
    return {sid: _row(sid, all_pass=ok, **kw) for sid, ok in passes.items()}


# ---------------------------------------------------------------- gates (§ 11)

def test_gates_digest_is_the_digest_of_the_constants():
    assert GATES_DIGEST == digest(GATES)
    assert GATES["modern_small"]["all_pass_min"] == 22
    assert GATES["modern_strong"]["all_pass_min"] == 23
    assert GATES["efficiency"]["all_pass_min"] == 20


def test_historical_qwen3_8b_dev_would_not_qualify_as_modern_small():
    v = evaluate_gates("modern_small", {"all_pass": 17, "no_output": 1, "p50_wall_ms": 12864})
    assert v["qualified"] is False and v["clauses"]["all_pass"]["ok"] is False


def test_modern_small_needs_all_three_clauses():
    ok = evaluate_gates("modern_small", {"all_pass": 22, "no_output": 8, "p50_wall_ms": 38592})
    assert ok["qualified"] is True
    for bad in ({"all_pass": 21, "no_output": 0, "p50_wall_ms": 1},
                {"all_pass": 30, "no_output": 9, "p50_wall_ms": 1},
                {"all_pass": 30, "no_output": 0, "p50_wall_ms": 38593}):
        assert evaluate_gates("modern_small", bad)["qualified"] is False


def test_historical_nemotron_dev_qualifies_as_modern_strong_by_the_first_clause_only():
    v = evaluate_gates("modern_strong", {"all_pass": 23, "no_output": 12, "p50_wall_ms": 53840.5})
    assert v["qualified"] is True
    assert v["clauses"]["all_pass_ge_nemotron"]["ok"] and not v["clauses"]["alternative_branch"]["ok"]


def test_modern_strong_alternative_branch():
    fast = evaluate_gates("modern_strong", {"all_pass": 21, "no_output": 12, "p50_wall_ms": 40380})
    reliable = evaluate_gates("modern_strong", {"all_pass": 21, "no_output": 6, "p50_wall_ms": 99999})
    neither = evaluate_gates("modern_strong", {"all_pass": 22, "no_output": 7, "p50_wall_ms": 40381})
    too_low = evaluate_gates("modern_strong", {"all_pass": 20, "no_output": 0, "p50_wall_ms": 1})
    assert fast["qualified"] and reliable["qualified"]
    assert not neither["qualified"] and not too_low["qualified"]


def test_efficiency_gate_is_relative_to_the_reference_system():
    ref = {"p50_wall_ms": 60000, "gpu_mem_used_mib": 15000, "label": "ref"}
    ok = evaluate_gates("efficiency", {"all_pass": 20, "no_output": 0, "p50_wall_ms": 75000,
                                       "gpu_mem_used_mib": 9750}, ref)
    assert ok["qualified"] is True
    slow = evaluate_gates("efficiency", {"all_pass": 30, "no_output": 0, "p50_wall_ms": 75001,
                                         "gpu_mem_used_mib": 5000}, ref)
    fat = evaluate_gates("efficiency", {"all_pass": 30, "no_output": 0, "p50_wall_ms": 1000,
                                        "gpu_mem_used_mib": 9751}, ref)
    weak = evaluate_gates("efficiency", {"all_pass": 19, "no_output": 0, "p50_wall_ms": 1000,
                                         "gpu_mem_used_mib": 1000}, ref)
    assert not slow["qualified"] and not fat["qualified"] and not weak["qualified"]
    with pytest.raises(KeyError):
        evaluate_gates("efficiency", {"all_pass": 30, "no_output": 0, "p50_wall_ms": 1,
                                      "gpu_mem_used_mib": 1})
    with pytest.raises(KeyError):
        evaluate_gates("modern_small", {"all_pass": 30, "no_output": 0})   # p50 missing


# ---------------------------------------------------------------- summaries / overlap

def test_summary_counts_no_output_cap_hits_and_silent_failures():
    rows = {
        "S01-1": _row("S01-1", all_pass=True),
        "S01-2": _row("S01-2", all_pass=False, rc=False),                       # silent:root_cause
        "S02-1": _row("S02-1", all_pass=False, ev=0.5),                         # silent:evidence_only
        "S02-2": _row("S02-2", all_pass=False, no_output=True, stop="length", out_tok=8192, rc=False),
        "S03-1": _row("S03-1", all_pass=False, no_output=True, stop="stop", rc=False),   # schema/parse
        "S03-2": _row("S03-2", all_pass=False, ver=False, unsupported=1),
    }
    s = summarize(rows)
    assert (s["n"], s["all_pass"], s["no_output"], s["cap_hits"], s["schema_or_parse_failures"]) == (6, 1, 2, 1, 1)
    assert s["silent"] == 2 and s["fail_patterns"]["silent:root_cause"] == 1
    assert s["fail_patterns"]["verifier-fail(unsupported)"] == 1
    assert s["gpu_mem_used_mib"] == 7100
    assert s["by_class"] == {"S01": 1, "S02": 0, "S03": 0}


def test_pairwise_and_dominance():
    a = _run({"c1": True, "c2": True, "c3": False, "c4": False})
    b = _run({"c1": True, "c2": False, "c3": True, "c4": False})
    p = pairwise(a, b)
    assert (p["both_pass"], p["a_only"], p["b_only"], p["both_fail"]) == (1, 1, 1, 1)
    assert not p["a_dominates_b"] and not p["b_dominates_a"]
    c = _run({"c1": True, "c2": True, "c3": True, "c4": False})
    assert pairwise(c, a)["a_dominates_b"] is True


def test_oracle_and_tier_coverage():
    weak = _run({"c1": True, "c2": False, "c3": False})
    mid = _run({"c1": True, "c2": True, "c3": False})
    strong = _run({"c1": True, "c2": True, "c3": False})
    o = post_answer_oracle(weak, strong)
    assert (o["local_safe"], o["rescueable"], o["unresolved"]) == (1, 1, 1)
    t = tier_coverage([("weak", weak), ("mid", mid), ("strong", strong)])
    assert t["first_pass_by_tier"] == {"weak": 1, "mid": 1, "unresolved": 1}
    assert t["coverage"] == 2


# ---------------------------------------------------------------- TRAIN rules (§ 6, § 7)

def test_cap_calibration_picks_the_smallest_cap_within_tolerance():
    rows = {f"c{i}": _row(f"c{i}", all_pass=True, out_tok=tok)
            for i, tok in enumerate([500, 900, 4096, 5000, 6143, 6144, 7000, 100, 200, 300])}
    r = cap_calibration(rows, tolerance=3)
    # >= 4096: 5 cases; >= 6144: 2 cases; >= 8192: 0 -> 6144 is the smallest within 3
    assert r["per_cap"][4096]["capped"] == 5 and r["per_cap"][6144]["capped"] == 2
    assert r["chosen_cap"] == 6144 and r["none_met_tolerance"] is False
    rows["c99"] = _row("c99", all_pass=False, out_tok=8192, stop="length", no_output=True, rc=False)
    rows["c98"] = _row("c98", all_pass=False, out_tok=8192, stop="length", no_output=True, rc=False)
    rows["c97"] = _row("c97", all_pass=False, out_tok=8192, stop="length", no_output=True, rc=False)
    rows["c96"] = _row("c96", all_pass=False, out_tok=8192, stop="length", no_output=True, rc=False)
    r = cap_calibration(rows, tolerance=3)
    assert r["chosen_cap"] == 8192 and r["none_met_tolerance"] is True


def test_quant_selection_is_quality_first_then_tie_breaks():
    a = _run({"c1": True, "c2": True, "c3": False})
    b = _run({"c1": True, "c2": False, "c3": False})
    assert quant_select("A", a, "B", b)["winner"] == "A"
    # equal quality, B has fewer no-output
    a2 = _run({"c1": True, "c2": False}); a2["c2"] = _row("c2", all_pass=False, no_output=True, rc=False)
    b2 = _run({"c1": True, "c2": False}); b2["c2"] = _row("c2", all_pass=False, rc=False)
    assert quant_select("A", a2, "B", b2)["decided_by"] == "no_output"
    assert quant_select("A", a2, "B", b2)["winner"] == "B"
    # everything equal -> smaller artifact (B)
    same_a = _run({"c1": True}); same_b = _run({"c1": True})
    assert quant_select("A", same_a, "B", same_b)["decided_by"] == "smaller_artifact"
    # latency tie-break before size
    fast = _run({"c1": True}, wall=5000); slow = _run({"c1": True}, wall=9000)
    assert quant_select("A", slow, "B", fast)["winner"] == "B"
    assert quant_select("A", fast, "B", slow)["winner"] == "A"
