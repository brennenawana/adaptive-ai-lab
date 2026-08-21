"""SMOKE, made operational end-to-end (M-STAT closeout): the runner lane
(`evals/runner/run_eval.py --smoke`) that executes the fixed 36-case population, the
machine-derived violation record (`fis_platform.provenance.smoke_case_flags` /
`write_smoke_result` / `validate_smoke_result`), and the SMOKE->REGISTERED gate
strengthened to bind a transition to the PERSISTED result rather than trust a
caller-supplied count.

Everything M-STAT's state machine already proved (SMOKE's edges, the `smoke` run
kind, `smoke_case_selection`) is covered by `test_mstat_smoke_state.py` /
`test_r6_state_machine.py`; this file covers the residual: is there a runner lane
that can PRODUCE a SMOKE result, and does the gate actually derive its verdict from
that result rather than from whatever the payload claims?

No model inference, no DB: every test here drives real APIs against a temporary
registry (`git_checks=False`, the house pattern) or the extracted, testable pieces of
the runner (`validate_smoke_args`, `smoke_case_flags`) directly. The one exception is
the invariants section, which reads (never writes) the real canonical registry and
`learning/registry/test_looks.jsonl` to prove this work left them untouched.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_r6_state_machine import (  # noqa: E402
    _candidate,
    _pass_smoke,
    _register_only,
    _smoke_case_ids,
    _smoke_cases,
    _smoke_result_record,
    _smoke_run_id,
    _step,
)

from evals.runner import run_eval  # noqa: E402
from fis_platform.ordering import round_robin  # noqa: E402
from fis_platform.provenance import (  # noqa: E402
    REGISTERED,
    SMOKE,
    SMOKE_TOTAL_CASES,
    TRAIN_COMPATIBLE,
    WITHDRAWN,
    R6Registry,
    TransitionRefused,
    begin_run,
    end_run,
    smoke_case_flags,
    write_smoke_result,
)
from fis_platform.routing.learn import digest  # noqa: E402
from scripts import r6_registry  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def reg(tmp_path: Path) -> R6Registry:
    return R6Registry(tmp_path / "registry", git_checks=False)


# ============================================================= A. validate_smoke_args

def _parse(argv: list[str]):
    return run_eval.build_arg_parser().parse_args(argv)


def _base_argv(**over: str) -> list[str]:
    argv = ["--arm", "E2", "--model-ref", "local-specialist", "--split", "train",
           "--candidate", "c1", "--smoke", "--run-id", "R6-c1-train-smoke"]
    for k, v in over.items():
        flag = "--" + k.replace("_", "-")
        argv += [] if v is None else [flag] if v is True else [flag, str(v)]
    return argv


def test_validate_smoke_args_refuses_without_candidate():
    args = _parse(["--arm", "E2", "--model-ref", "local-specialist", "--split", "train",
                   "--smoke", "--run-id", "R6-x-train-smoke"])
    with pytest.raises(SystemExit, match="requires --candidate"):
        run_eval.validate_smoke_args(args)


def test_validate_smoke_args_refuses_dev_split():
    args = _parse(_base_argv(split="dev"))
    with pytest.raises(SystemExit, match="TRAIN-only"):
        run_eval.validate_smoke_args(args)


def test_validate_smoke_args_refuses_test_split():
    args = _parse(_base_argv(split="test"))
    with pytest.raises(SystemExit, match="TRAIN-only"):
        run_eval.validate_smoke_args(args)


def test_validate_smoke_args_refuses_limit():
    args = _parse(_base_argv(limit="5"))
    with pytest.raises(SystemExit, match="--limit"):
        run_eval.validate_smoke_args(args)


def test_validate_smoke_args_refuses_scenario_ids_file(tmp_path):
    ids_file = tmp_path / "ids.txt"
    ids_file.write_text("S01-1000000\n")
    args = _parse(_base_argv(scenario_ids_file=str(ids_file)))
    with pytest.raises(SystemExit, match="scenario-ids-file"):
        run_eval.validate_smoke_args(args)


def test_validate_smoke_args_refuses_escalate_to():
    args = _parse(_base_argv(escalate_to="claude-x"))
    with pytest.raises(SystemExit, match="escalate-to"):
        run_eval.validate_smoke_args(args)


def test_validate_smoke_args_refuses_tolerance_spec(tmp_path):
    spec = tmp_path / "tol.json"
    spec.write_text("[]")
    args = _parse(_base_argv(tolerance_spec=str(spec)))
    with pytest.raises(SystemExit, match="tolerance-spec"):
        run_eval.validate_smoke_args(args)


def test_validate_smoke_args_refuses_curtail_bar():
    args = _parse(_base_argv(curtail_bar="0.5"))
    with pytest.raises(SystemExit, match="curtail-bar"):
        run_eval.validate_smoke_args(args)


def test_validate_smoke_args_refuses_a_run_id_without_smoke():
    args = _parse(_base_argv(run_id="R6-c1-train-warmup"))
    with pytest.raises(SystemExit, match="must contain 'smoke'"):
        run_eval.validate_smoke_args(args)


def test_validate_smoke_args_passes_for_valid_train_and_candidate():
    args = _parse(_base_argv())
    run_eval.validate_smoke_args(args)   # must not raise


def test_validate_smoke_args_is_a_no_op_without_smoke():
    args = _parse(["--arm", "E2", "--model-ref", "local-specialist", "--split", "test"])
    run_eval.validate_smoke_args(args)   # --smoke not passed: nothing to check, must not raise


# =========================================================== B. smoke_case_flags

def test_smoke_case_flags_all_success_one_invocation_is_clean():
    case = {"tool_call_statuses": ["success", "success"], "n_model_invocations": 1}
    assert smoke_case_flags(case) == []


def test_smoke_case_flags_one_denied_status_flags():
    case = {"tool_call_statuses": ["success", "denied"], "n_model_invocations": 1}
    assert smoke_case_flags(case) == ["tool_call_status_not_success"]


def test_smoke_case_flags_zero_invocations_flags():
    case = {"tool_call_statuses": ["success"], "n_model_invocations": 0}
    assert smoke_case_flags(case) == ["zero_model_invocations"]


def test_smoke_case_flags_both_fire_together():
    case = {"tool_call_statuses": ["error"], "n_model_invocations": 0}
    assert smoke_case_flags(case) == ["tool_call_status_not_success", "zero_model_invocations"]


# =========================================================== C. write_smoke_result

_CID = "cand@0123456789ab"
_RUN_ID = "R6-cand-train-smoke"


def test_write_smoke_result_valid_roundtrip(reg):
    canonical = _smoke_case_ids()
    cases = _smoke_cases(canonical, 0)
    record = _smoke_result_record(_CID, _RUN_ID, canonical, cases)
    result_digest = write_smoke_result(reg, _CID, _RUN_ID, record)
    assert result_digest == digest(record)
    path = reg.smoke_result_file(_CID, _RUN_ID)
    assert path.exists()
    on_disk = json.loads(path.read_text())
    assert on_disk["total_violations"] == 0
    assert on_disk["eligible"] is True
    assert len(on_disk["case_ids"]) == SMOKE_TOTAL_CASES


def test_write_smoke_result_refuses_wrong_candidate(reg):
    canonical = _smoke_case_ids()
    record = _smoke_result_record("other@fedcba987654", _RUN_ID, canonical,
                                  _smoke_cases(canonical, 0))
    with pytest.raises(TransitionRefused, match="candidate_id"):
        write_smoke_result(reg, _CID, _RUN_ID, record)


def test_write_smoke_result_refuses_wrong_split(reg):
    canonical = _smoke_case_ids()
    record = _smoke_result_record(_CID, _RUN_ID, canonical, _smoke_cases(canonical, 0))
    record["split"] = "dev"
    with pytest.raises(TransitionRefused, match="split must be 'train'"):
        write_smoke_result(reg, _CID, _RUN_ID, record)


def test_write_smoke_result_refuses_35_cases(reg):
    canonical = _smoke_case_ids()[:35]
    record = _smoke_result_record(_CID, _RUN_ID, canonical, _smoke_cases(canonical, 0))
    with pytest.raises(TransitionRefused, match="exactly 36"):
        write_smoke_result(reg, _CID, _RUN_ID, record)


def test_write_smoke_result_refuses_wrong_class_balance(reg):
    """36 cases total, but a subset/altered population: 4 of class S01, 2 of S02,
    3 of every other class — still 36, still round-robin, but not 12 classes x 3."""
    counts = {1: 4, 2: 2}
    ids = [f"S{c:02d}-{1000000 + s:07d}" for c in range(1, 13) for s in range(counts.get(c, 3))]
    canonical = round_robin(ids)
    assert len(canonical) == SMOKE_TOTAL_CASES
    record = _smoke_result_record(_CID, _RUN_ID, canonical, _smoke_cases(canonical, 0))
    with pytest.raises(TransitionRefused, match="12 classes"):
        write_smoke_result(reg, _CID, _RUN_ID, record)


def test_write_smoke_result_refuses_non_round_robin_order(reg):
    canonical = _smoke_case_ids()
    shuffled = list(reversed(canonical))
    assert shuffled != canonical   # sanity: reversal is not a no-op here
    record = _smoke_result_record(_CID, _RUN_ID, shuffled, _smoke_cases(shuffled, 0))
    with pytest.raises(TransitionRefused, match="round-robin"):
        write_smoke_result(reg, _CID, _RUN_ID, record)


def test_write_smoke_result_refuses_smoke_case_digest_mismatch(reg):
    canonical = _smoke_case_ids()
    record = _smoke_result_record(_CID, _RUN_ID, canonical, _smoke_cases(canonical, 0))
    record["smoke_case_digest"] = "f" * 64
    with pytest.raises(TransitionRefused, match="smoke_case_digest"):
        write_smoke_result(reg, _CID, _RUN_ID, record)


def test_write_smoke_result_refuses_recorded_violations_inconsistent_with_recompute(reg):
    canonical = _smoke_case_ids()
    cases = _smoke_cases(canonical, 0)
    # Tamper ONE case's stored violations without changing its raw evidence — the
    # aggregate total_violations (computed below, after tampering) will happen to
    # agree, isolating the PER-CASE recompute check from the aggregate one.
    cases[0]["violations"] = ["tool_call_status_not_success"]
    record = _smoke_result_record(_CID, _RUN_ID, canonical, cases)
    with pytest.raises(TransitionRefused, match="recomputes to"):
        write_smoke_result(reg, _CID, _RUN_ID, record)


def test_write_smoke_result_refuses_total_violations_mismatch(reg):
    canonical = _smoke_case_ids()
    cases = _smoke_cases(canonical, 1)   # one genuine, internally-consistent violation
    record = _smoke_result_record(_CID, _RUN_ID, canonical, cases)
    record["total_violations"] = 0       # tamper the aggregate only
    with pytest.raises(TransitionRefused, match="total_violations"):
        write_smoke_result(reg, _CID, _RUN_ID, record)


def test_write_smoke_result_refuses_eligible_mismatch(reg):
    canonical = _smoke_case_ids()
    record = _smoke_result_record(_CID, _RUN_ID, canonical, _smoke_cases(canonical, 0))
    record["eligible"] = False           # total_violations is 0; eligible must be True
    with pytest.raises(TransitionRefused, match="eligible"):
        write_smoke_result(reg, _CID, _RUN_ID, record)


def test_write_smoke_result_refuses_overwrite(reg):
    canonical = _smoke_case_ids()
    record = _smoke_result_record(_CID, _RUN_ID, canonical, _smoke_cases(canonical, 0))
    write_smoke_result(reg, _CID, _RUN_ID, record)
    with pytest.raises(TransitionRefused, match="already exists"):
        write_smoke_result(reg, _CID, _RUN_ID, record)


# =========================================================== D. the gate, end-to-end

def test_gate_succeeds_with_a_valid_persisted_zero_violation_result(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    entry = _pass_smoke(reg, cid)
    assert entry["to"] == REGISTERED and entry["from"] == SMOKE
    assert reg.current_state(cid) == REGISTERED


def test_gate_refuses_missing_result_file(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    run_id = _smoke_run_id(cid)
    canonical = _smoke_case_ids()
    case_digest = digest(canonical)
    begin_run(reg, cid, "train", run_id, SMOKE_TOTAL_CASES, kind="smoke",
             extra={"smoke_case_digest": case_digest})
    end_run(reg, cid, run_id, cases_done=SMOKE_TOTAL_CASES, wall_s=1.0,
           extra={"smoke_result_digest": "z" * 64, "smoke_case_digest": case_digest})
    payload = {"smoke_run_id": run_id, "smoke_cases": SMOKE_TOTAL_CASES,
              "smoke_violations": 0, "smoke_case_digest": case_digest,
              "ordering": "round_robin"}
    with pytest.raises(TransitionRefused, match="no SMOKE result file"):
        reg.transition(cid, REGISTERED, payload, require_clean_tree=False)
    assert reg.current_state(cid) == SMOKE


def test_gate_refuses_end_line_without_smoke_result_digest(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    run_id = _smoke_run_id(cid)
    canonical = _smoke_case_ids()
    case_digest = digest(canonical)
    record = _smoke_result_record(cid, run_id, canonical, _smoke_cases(canonical, 0))
    write_smoke_result(reg, cid, run_id, record)
    begin_run(reg, cid, "train", run_id, SMOKE_TOTAL_CASES, kind="smoke",
             extra={"smoke_case_digest": case_digest})
    end_run(reg, cid, run_id, cases_done=SMOKE_TOTAL_CASES, wall_s=1.0,
           extra={"smoke_case_digest": case_digest})   # no smoke_result_digest
    payload = {"smoke_run_id": run_id, "smoke_cases": SMOKE_TOTAL_CASES,
              "smoke_violations": 0, "smoke_case_digest": case_digest,
              "ordering": "round_robin"}
    with pytest.raises(TransitionRefused, match="carries no smoke_result_digest"):
        reg.transition(cid, REGISTERED, payload, require_clean_tree=False)


def test_gate_refuses_a_result_file_edited_after_the_run(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    run_id = _smoke_run_id(cid)
    canonical = _smoke_case_ids()
    case_digest = digest(canonical)
    record = _smoke_result_record(cid, run_id, canonical, _smoke_cases(canonical, 0))
    result_digest = write_smoke_result(reg, cid, run_id, record)
    begin_run(reg, cid, "train", run_id, SMOKE_TOTAL_CASES, kind="smoke",
             extra={"smoke_case_digest": case_digest})
    end_run(reg, cid, run_id, cases_done=SMOKE_TOTAL_CASES, wall_s=1.0,
           extra={"smoke_result_digest": result_digest, "smoke_case_digest": case_digest})
    path = reg.smoke_result_file(cid, run_id)
    tampered = json.loads(path.read_text())
    tampered["corpus_digest"] = "e" * 64   # any post-hoc edit, digest not updated
    path.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n")
    payload = {"smoke_run_id": run_id, "smoke_cases": SMOKE_TOTAL_CASES,
              "smoke_violations": 0, "smoke_case_digest": case_digest,
              "ordering": "round_robin"}
    with pytest.raises(TransitionRefused, match="was edited after the run"):
        reg.transition(cid, REGISTERED, payload, require_clean_tree=False)


def test_gate_refuses_payload_zero_when_the_persisted_result_derives_one(reg, tmp_path):
    """THE core test: the caller's payload claims smoke_violations=0, but the
    persisted, digest-bound result mechanically derives 1 — the gate must refuse
    regardless of what the payload says. A caller cannot override the derivation."""
    cid = _register_only(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="does not equal"):
        _pass_smoke(reg, cid, violations=1, smoke_violations=0)
    assert reg.current_state(cid) == SMOKE


def test_gate_refuses_a_nonzero_derived_count_even_when_the_payload_matches_it(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="cannot open REGISTERED work"):
        _pass_smoke(reg, cid, violations=1)   # payload smoke_violations defaults to 1 too
    assert reg.current_state(cid) == SMOKE


def test_gate_refuses_ledger_lines_of_the_wrong_run_kind(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    run_id = _smoke_run_id(cid)
    canonical = _smoke_case_ids()
    case_digest = digest(canonical)
    record = _smoke_result_record(cid, run_id, canonical, _smoke_cases(canonical, 0))
    result_digest = write_smoke_result(reg, cid, run_id, record)
    # begin/end as an ORDINARY eval run (kind defaults to "eval"), not kind="smoke".
    begin_run(reg, cid, "train", run_id, SMOKE_TOTAL_CASES,
             extra={"smoke_case_digest": case_digest})
    end_run(reg, cid, run_id, cases_done=SMOKE_TOTAL_CASES, wall_s=1.0,
           extra={"smoke_result_digest": result_digest, "smoke_case_digest": case_digest})
    payload = {"smoke_run_id": run_id, "smoke_cases": SMOKE_TOTAL_CASES,
              "smoke_violations": 0, "smoke_case_digest": case_digest,
              "ordering": "round_robin"}
    with pytest.raises(TransitionRefused, match="no SMOKE ledger start line"):
        reg.transition(cid, REGISTERED, payload, require_clean_tree=False)


def test_gate_refuses_another_candidates_smoke_run(reg, tmp_path):
    cid_a = _register_only(reg, tmp_path, "qwen35-9b-q4km")
    cid_b = _register_only(reg, tmp_path, "qwen38-27b-y", family="qwen38.27b",
                           role="modern_strong")
    run_id_a = _smoke_run_id(cid_a)
    canonical = _smoke_case_ids()
    case_digest = digest(canonical)
    record = _smoke_result_record(cid_a, run_id_a, canonical, _smoke_cases(canonical, 0))
    result_digest = write_smoke_result(reg, cid_a, run_id_a, record)
    begin_run(reg, cid_a, "train", run_id_a, SMOKE_TOTAL_CASES, kind="smoke",
             extra={"smoke_case_digest": case_digest})
    end_run(reg, cid_a, run_id_a, cases_done=SMOKE_TOTAL_CASES, wall_s=1.0,
           extra={"smoke_result_digest": result_digest, "smoke_case_digest": case_digest})
    payload = {"smoke_run_id": run_id_a, "smoke_cases": SMOKE_TOTAL_CASES,
              "smoke_violations": 0, "smoke_case_digest": case_digest,
              "ordering": "round_robin"}
    with pytest.raises(TransitionRefused, match="no SMOKE ledger start line"):
        reg.transition(cid_b, REGISTERED, payload, require_clean_tree=False)
    assert reg.current_state(cid_b) == SMOKE


# =========================================================== E. invariants

def test_smoke_run_never_justifies_train_compatible_adoption(reg, tmp_path):
    cid = _candidate(reg, tmp_path)          # already promoted past its own SMOKE pass
    smoke_id = _smoke_run_id(cid)
    with pytest.raises(TransitionRefused, match="never justify adoption"):
        _step(reg, cid, TRAIN_COMPATIBLE, train_run_ids=[smoke_id])
    assert reg.current_state(cid) == REGISTERED


def test_smoke_run_never_justifies_withdrawal_evidence(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    smoke_id = _smoke_run_id(cid)
    with pytest.raises(TransitionRefused, match="SMOKE cannot justify elimination"):
        _step(reg, cid, WITHDRAWN, reason="lost the pilot", reason_category="pilot_selection_loss",
              pilot_margin_cases=20, pilot_n=36, pilot_mde_cases=9,
              evidence_run_ids=[smoke_id])
    assert reg.current_state(cid) == REGISTERED


def test_test_looks_ledger_still_has_exactly_seven_entries():
    """Read-only: this closeout never touches `learning/registry/test_looks.jsonl`."""
    path = ROOT / "learning" / "registry" / "test_looks.jsonl"
    lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
    assert len(lines) == 7


def test_historical_registry_still_verifies():
    """Read-only: re-derive every digest in the CANONICAL `learning/registry/r6` tree
    and confirm nothing about this closeout corrupted or altered it."""
    from fis_platform.provenance import default_root
    rc = r6_registry.cmd_verify(None, R6Registry(default_root()))
    assert rc == 0


# =========================================================== F. smoke-eligibility CLI

def test_smoke_eligibility_derives_the_transition_payload(reg, tmp_path, capsys):
    cid = _register_only(reg, tmp_path)
    run_id = _smoke_run_id(cid)
    canonical = _smoke_case_ids()
    case_digest = digest(canonical)
    record = _smoke_result_record(cid, run_id, canonical, _smoke_cases(canonical, 0))
    write_smoke_result(reg, cid, run_id, record)

    import argparse
    args = argparse.Namespace(candidate=cid, run_id=run_id)
    rc = r6_registry.cmd_smoke_eligibility(args, reg)
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["eligible"] is True
    assert out["transition_payload"] == {
        "smoke_run_id": run_id, "smoke_cases": SMOKE_TOTAL_CASES, "smoke_violations": 0,
        "smoke_case_digest": case_digest, "ordering": "round_robin",
    }


def test_smoke_eligibility_refuses_a_missing_result(reg, tmp_path):
    cid = _register_only(reg, tmp_path)
    import argparse
    args = argparse.Namespace(candidate=cid, run_id=_smoke_run_id(cid))
    with pytest.raises(TransitionRefused, match="no SMOKE result"):
        r6_registry.cmd_smoke_eligibility(args, reg)


def test_smoke_eligibility_derives_nonzero_violations_faithfully(reg, tmp_path, capsys):
    cid = _register_only(reg, tmp_path)
    run_id = _smoke_run_id(cid)
    canonical = _smoke_case_ids()
    record = _smoke_result_record(cid, run_id, canonical, _smoke_cases(canonical, 2))
    write_smoke_result(reg, cid, run_id, record)

    import argparse
    args = argparse.Namespace(candidate=cid, run_id=run_id)
    r6_registry.cmd_smoke_eligibility(args, reg)
    out = json.loads(capsys.readouterr().out)
    assert out["eligible"] is False
    assert out["transition_payload"]["smoke_violations"] == 2


def test_gate_refuses_disagreeing_end_line_digests(reg, tmp_path):
    """A re-appended smoke end line (cases_done=0 keeps the completeness sum at 36)
    may not re-bind the result file to a different digest — every end line carrying
    a smoke_result_digest must agree (adversarial-review Q3 hardening)."""
    cid = _register_only(reg, tmp_path)
    run_id = _smoke_run_id(cid)
    canonical = _smoke_case_ids()
    case_digest = digest(canonical)
    record = _smoke_result_record(cid, run_id, canonical, _smoke_cases(canonical, 0))
    result_digest = write_smoke_result(reg, cid, run_id, record)
    begin_run(reg, cid, "train", run_id, SMOKE_TOTAL_CASES, kind="smoke",
              extra={"smoke_case_digest": case_digest})
    end_run(reg, cid, run_id, cases_done=SMOKE_TOTAL_CASES, wall_s=1.0,
            extra={"smoke_result_digest": result_digest, "smoke_case_digest": case_digest,
                   "smoke_violations": 0})
    # The laundering attempt: a second end line, sum-neutral, binding a chosen digest.
    end_run(reg, cid, run_id, cases_done=0, wall_s=0.0,
            extra={"smoke_result_digest": "f" * 64, "smoke_case_digest": case_digest,
                   "smoke_violations": 0})
    payload = {"smoke_run_id": run_id, "smoke_cases": SMOKE_TOTAL_CASES,
               "smoke_violations": 0, "smoke_case_digest": case_digest,
               "ordering": "round_robin"}
    with pytest.raises(TransitionRefused, match="disagree on"):
        reg.transition(cid, REGISTERED, payload, require_clean_tree=False)
    assert reg.current_state(cid) == SMOKE
