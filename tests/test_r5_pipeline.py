"""R5 pipeline — the pure functions between a persisted run and a selection verdict.

`test_routing_features_no_gold_leak.py` pins the *extractor* boundary. This file pins
the three layers built on top of it, all of which are pure functions of in-memory
inputs and none of which may touch Postgres:

* **dataset** (`scripts/r5_dataset.py`) — the scorer-echo answer reconstruction (only
  the model's own `said` value, never the `truth` beside it), the gold-removal
  invariance of a *built row* (not just of a snapshot: the builder is where a label
  could leak into `features` by accident), the persisted-body consistency check, the
  R4 signal agreement with `services.ai_orchestrator.cascade`, and the TEST seal;
* **train** (`scripts/r5_train.py`) — the artifact shape contract of § 13, the
  eligibility flag being a *kind* AND a gate, digest stability, and the τ tie rule;
* **replay** (`scripts/r5_replay.py`, `scripts/r5_amend_rule.py`) — the four baseline
  decision modes and the accounting they imply (§ 11), the silent-family bucketing,
  the § 12/§ 12a selection rule, the fail-closed artifact checks of § 13, and the
  mechanical derivation of the § 12a numbers.

Every fixture is built by hand in memory. A row that came out of the database would
prove that today's database agrees with itself, not that the contract holds.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fis_platform.routing.features import (
    FEATURE_ORDER, FEATURE_SCHEMA_VERSION, AnswerFields, snapshot_from,
)
from fis_platform.routing.learn import digest
from schemas import (
    InvestigationResult, LatencyRecord, ModelInvocation, ModelTier, Provider, TokenUsage,
    ToolCall, Trajectory, VerificationResult,
)
from schemas.investigator import Fact, NextAction, RootCause, RootCauseLabel
from scripts import r5_dataset, r5_replay
from scripts.r5_amend_rule import derive
from scripts.r5_dataset import (
    answer_from_echo, answer_from_output, build_rows, dataset_digest, diagnostics,
    guard_split, r4_signals,
)
from scripts.r5_replay import (
    _MUTABLE_FIELDS, apply_rule, classifier_metrics, decisions, evaluate_policy,
    silent_family, verify_artifact,
)
from scripts.r5_train import THRESHOLD_GRID, _pick_threshold, _utility_curve, train_candidate
from services.ai_orchestrator.cascade import (
    EscalationPolicy, should_escalate, signals_from,
)

CLEAN_CHECKS = {
    "schema_validation": True, "citation_required": True, "citation_resolves_to_call": True,
    "cited_ids_observed": True, "known_action_code": True, "confidence_supported": True,
    "facts_present": True,
}

SAID_LABEL = "settlement_amount_mapping_error"
SAID_ACTION = "inspect_mapping_version"


# --------------------------------------------------------------------------- fixtures

def _invocation(**overrides) -> ModelInvocation:
    kwargs = {
        "tier": ModelTier.SPECIALIST,
        "provider": Provider.LOCAL_LLAMACPP,
        "model_id": "qwen3-8b-q4km",
        "canonical_model": "qwen3-8b",
        "prompt_version": "cause_action_directed@1",
        "usage": TokenUsage(input_tokens=12000, output_tokens=900),
        "latency": LatencyRecord(wall_ms=41000, api_ms=40500),
        "stop_reason": "stop",
        "max_tokens": 4096,
        "reasoning_chars": 3000,
        "content_chars": 1000,
    }
    kwargs.update(overrides)
    return ModelInvocation(**kwargs)


def _traj(*, verification: VerificationResult | None = None, error: str | None = None,
          invocations: list[ModelInvocation] | None = None, **eval_fields) -> Trajectory:
    return Trajectory(
        workflow="case_investigation", workflow_version="1", task_type="investigate",
        user="analyst",
        model_invocations=[_invocation()] if invocations is None else invocations,
        tool_calls=[ToolCall(tool="get_case", version=1, args_hash="h1", status="success",
                             latency_ms=3, sequence=0)],
        verification=verification, error=error, **eval_fields,
    )


def _result(label: RootCauseLabel = RootCauseLabel.SETTLEMENT_AMOUNT_MAPPING_ERROR,
            action: NextAction = NextAction.INSPECT_MAPPING_VERSION) -> InvestigationResult:
    return InvestigationResult(
        case_id="CASE-1", classification="ledger_reconciliation",
        root_cause=RootCause(label=label, confidence=0.8),
        facts=[Fact(claim="Settlement set_1 recorded 4210", source="tool://processor/set_1",
                    entity_ids=["set_1"])],
        recommended_next_action=action,
        summary="Settlement and ledger amounts disagree by nine units.",
    )


def _score(*, all_pass=True, verifier_passed=True, produced=True, violations_unsupported=0,
           root_cause_correct=True, recall=1.0, action_ok=True, forbidden=False,
           said_label=SAID_LABEL, truth_label="settlement_amount_mapping_error",
           said_action=SAID_ACTION) -> dict:
    """A scorer payload in the shape `learning.case_scores.payload` persists."""
    dims: list[dict] = []
    if not produced:
        dims.append({"name": "produced_output", "value": 0.0, "passed": False,
                     "detail": "no structured output"})
    else:
        dims.append({"name": "root_cause", "value": 1.0, "passed": root_cause_correct,
                     "detail": f"said {said_label}, truth {truth_label}"})
        dims.append({"name": "next_action", "value": 1.0, "passed": action_ok,
                     "detail": f"said {said_action}"})
    return {
        "all_pass": all_pass, "verifier_passed": verifier_passed,
        "unsupported_claims": violations_unsupported,
        "root_cause_correct": root_cause_correct,
        "required_evidence_recall": recall, "evidence_recall_threshold": 0.8,
        "next_action_acceptable": action_ok, "forbidden_claim_made": forbidden,
        "wall_ms": 41000, "reference_cost_usd": 0.0, "dimensions": dims,
    }


def _db_row(*, sid="S06-2006000", all_pass=True, split="dev", category="ledger",
            score=None, traj=None, answer=None) -> dict:
    """One row in the shape `r5_dataset.load_run` returns."""
    if traj is None:
        traj = _traj(verification=VerificationResult(passed=True, checks=dict(CLEAN_CHECKS)))
    return {
        "scenario_id": sid, "all_pass": all_pass,
        "trace_id": "11111111-2222-3333-4444-555555555555",
        "score": _score(all_pass=all_pass) if score is None else score,
        "traj": traj.model_dump(mode="json") if isinstance(traj, Trajectory) else traj,
        "split": split, "category": category, "answer": answer,
    }


# ============================================================ A. answer_from_echo

class TestAnswerFromEcho:
    """§ 5: only the `said` value is taken; the truth beside it is never read."""

    def test_said_label_and_action_are_reconstructed_and_the_truth_is_not(self):
        score = {"dimensions": [
            {"name": "root_cause", "detail": "said kyc_hold, truth risk_hold"},
            {"name": "next_action", "detail": "said replay_webhook"},
        ]}
        answer = answer_from_echo(score)
        assert answer == AnswerFields(root_cause_label="kyc_hold",
                                      recommended_next_action="replay_webhook")
        # The gold label appeared verbatim in the input and must not survive into the
        # object the extractor is handed.
        assert "risk_hold" not in json.dumps(answer.model_dump())
        assert all("risk_hold" not in str(v) for v in answer.model_dump().values())

    def test_a_no_output_case_has_no_answer_at_all(self):
        score = {"dimensions": [
            {"name": "produced_output", "value": 0.0, "detail": "no structured output"},
            # even if a stale root_cause echo were present, produced_output wins
            {"name": "root_cause", "detail": "said kyc_hold, truth risk_hold"},
        ]}
        assert answer_from_echo(score) is None

    def test_a_malformed_root_cause_echo_yields_no_label_never_the_truth(self):
        score = {"dimensions": [
            {"name": "root_cause", "detail": "truth risk_hold"},          # no "said <x>, "
            {"name": "next_action", "detail": "said replay_webhook"},
        ]}
        answer = answer_from_echo(score)
        assert answer is not None                       # the action still parsed
        assert answer.root_cause_label is None
        assert answer.recommended_next_action == "replay_webhook"

    def test_an_unparseable_echo_on_both_dimensions_is_no_answer(self):
        score = {"dimensions": [{"name": "root_cause", "detail": "truth risk_hold"},
                                {"name": "next_action", "detail": "no action given"}]}
        assert answer_from_echo(score) is None


# ============================================ B. build_rows: gold-removal invariance

class TestBuildRowsGoldRemovalInvariance:
    """The builder is where a label could leak into `features` by accident: it is the
    only place that holds the snapshot and the score at the same time."""

    def test_perturbing_every_label_carrying_column_leaves_features_and_digest_identical(self):
        traj = _traj(verification=VerificationResult(passed=True, checks=dict(CLEAN_CHECKS)))
        truthful = _db_row(
            all_pass=True, split="dev", category="ledger",
            score=_score(all_pass=True, truth_label=SAID_LABEL), traj=traj)
        perturbed = _db_row(
            all_pass=False, split="train", category="webhook_replay",
            score=_score(all_pass=False, truth_label="reversal_race",
                         root_cause_correct=False), traj=traj)

        a, _ = build_rows({truthful["scenario_id"]: truthful}, "RUN-A", None)
        b, _ = build_rows({perturbed["scenario_id"]: perturbed}, "RUN-B", None)
        (a,), (b,) = a, b

        assert a["features"] == b["features"]
        assert a["snapshot_digest"] == b["snapshot_digest"]
        assert a["feature_schema_version"] == b["feature_schema_version"] == FEATURE_SCHEMA_VERSION
        assert set(a["features"]) == set(FEATURE_ORDER)
        # …while everything the label lives in did move.
        assert a["label_safe"] is True and b["label_safe"] is False
        assert a["label_unsafe"] is False and b["label_unsafe"] is True
        assert a["split"] == "dev" and b["split"] == "train"
        assert a["meta"]["category"] != b["meta"]["category"]
        assert a["diag"]["wrong_root_cause"] is False and b["diag"]["wrong_root_cause"] is True
        # the dataset digest DOES move: it is a digest of features + labels + group
        assert dataset_digest([a]) != dataset_digest([b])

    def test_the_group_key_is_the_scenario_class_and_never_a_feature(self):
        row = _db_row(sid="S07-2007000")
        (built,), _ = build_rows({row["scenario_id"]: row}, "RUN", None)
        assert built["group"] == "S07"
        assert "group" not in built["features"] and "S07" not in json.dumps(built["features"])

    def test_a_persisted_answer_body_that_matches_the_echo_is_accepted(self):
        body = _result().model_dump(mode="json")
        row = _db_row(answer=body, score=_score(said_label=SAID_LABEL, said_action=SAID_ACTION))
        built, checks = build_rows({row["scenario_id"]: row}, "RUN", None)
        assert checks == {"echo_checked": 1}
        assert built[0]["features"]["said_label_" + SAID_LABEL] == 1.0
        assert built[0]["answer_structure"] is not None       # exploratory, TRAIN-only

        # and the reconstruction is the thing being validated: echo == body
        assert answer_from_echo(row["score"]) == answer_from_output(body)

    def test_a_persisted_answer_body_that_contradicts_the_echo_is_fatal(self):
        body = _result(label=RootCauseLabel.RISK_HOLD,
                       action=NextAction.ESCALATE_TO_RISK_TEAM).model_dump(mode="json")
        row = _db_row(answer=body)          # echo still says settlement_amount_mapping_error
        with pytest.raises(SystemExit, match="scorer echo .* != persisted answer"):
            build_rows({row["scenario_id"]: row}, "RUN", None)

    def test_the_echo_check_can_be_disabled_but_defaults_on(self):
        body = _result(label=RootCauseLabel.RISK_HOLD,
                       action=NextAction.ESCALATE_TO_RISK_TEAM).model_dump(mode="json")
        row = _db_row(answer=body)
        built, checks = build_rows({row["scenario_id"]: row}, "RUN", None, check_echo=False)
        assert checks == {"echo_checked": 0}
        assert built[0]["features"]["said_label_risk_hold"] == 1.0   # the body wins


# ================================================================= C. R4 agreement

class TestR4Agreement:
    """`escalate = R4 ∨ risk ≥ τ` only measures the residual over R4 if the dataset's
    R4 bit is the cascade's own. Both sides are computed here and compared."""

    def _both(self, score: dict, traj: Trajectory, result: InvestigationResult | None):
        mine = should_escalate(r4_signals(score, traj.model_dump(mode="json")),
                               EscalationPolicy.VERIFIER)
        theirs = should_escalate(signals_from(result, traj), EscalationPolicy.VERIFIER)
        assert mine == theirs, f"dataset {mine} != cascade {theirs}"
        return mine

    def test_no_output(self):
        traj = _traj(verification=None, error="model produced no parseable structured output")
        assert self._both(_score(all_pass=False, produced=False, verifier_passed=False),
                          traj, None) == (True, "no_output")

    def test_verifier_clean(self):
        traj = _traj(verification=VerificationResult(passed=True, checks=dict(CLEAN_CHECKS)))
        assert self._both(_score(), traj, _result()) == (False, None)

    def test_unsupported_claim(self):
        traj = _traj(verification=VerificationResult(
            passed=False, checks=dict(CLEAN_CHECKS, cited_ids_observed=False),
            violations=["cites an id no tool returned: le_999"]))
        assert self._both(_score(all_pass=False, verifier_passed=False,
                                 violations_unsupported=1), traj, _result()) == \
            (True, "unsupported_claims")

    def test_other_verifier_failure(self):
        traj = _traj(verification=VerificationResult(
            passed=False, checks=dict(CLEAN_CHECKS, confidence_supported=False),
            violations=["confidence 0.95 asserted after only 1 successful tool call(s)"]))
        assert self._both(_score(all_pass=False, verifier_passed=False), traj,
                          _result()) == (True, "verifier_failed")

    def test_build_rows_records_the_same_bit_and_the_silent_diagnostic(self):
        traj = _traj(verification=VerificationResult(passed=True, checks=dict(CLEAN_CHECKS)))
        row = _db_row(all_pass=False, traj=traj,
                      score=_score(all_pass=False, root_cause_correct=False))
        (built,), _ = build_rows({row["scenario_id"]: row}, "RUN", {row["scenario_id"]: True})
        assert built["r4_escalate"] is False and built["r4_reason"] is None
        assert built["diag"]["silent"] is True        # verifier-clean and wrong
        assert built["strong_pass"] is True

        traj_bad = _traj(verification=None, error="no parseable output")
        row_bad = _db_row(all_pass=False, traj=traj_bad,
                          score=_score(all_pass=False, produced=False, verifier_passed=False))
        (bad,), _ = build_rows({row_bad["scenario_id"]: row_bad}, "RUN", None)
        assert (bad["r4_escalate"], bad["r4_reason"]) == (True, "no_output")
        assert bad["diag"]["silent"] is False and bad["diag"]["no_output"] is True

    def test_diagnostics_are_a_pure_function_of_the_score_and_the_gate_bit(self):
        d = diagnostics(_score(all_pass=False, recall=0.5, action_ok=False, forbidden=True),
                        r4_escalate=False)
        assert d["unsafe"] and d["evidence_miss"] and d["action_fail"] and d["forbidden_claim"]
        assert d["silent"] is True
        assert diagnostics(_score(all_pass=False, recall=0.5), r4_escalate=True)["silent"] is False


# ================================================================= D. train_candidate

def _train_rows(n: int = 60) -> list[dict]:
    """`n` rows in exactly the shape `r5_dataset.build_rows` writes.

    The label is `output_tokens >= 500` with two flipped cases, so the candidates have
    real signal (the point is the artifact contract, not the learner's accuracy — that
    is `test_routing_learn.py`'s job) without being perfectly separable.
    """
    base = snapshot_from(
        _traj(verification=VerificationResult(passed=True, checks=dict(CLEAN_CHECKS))),
        AnswerFields(root_cause_label=SAID_LABEL, recommended_next_action=SAID_ACTION),
    ).features
    rows = []
    for i in range(n):
        out_tok = 200 + 40 * (i % 15)                     # 200 … 760
        unsafe = out_tok >= 500
        if i in (3, 44):                                   # a little label noise
            unsafe = not unsafe
        f = dict(base)
        f["output_tokens"] = float(out_tok)
        f["content_chars"] = float(3 * out_tok)
        f["budget_used"] = round(out_tok / 4096, 6)
        f["wall_ms"] = float(20000 + 37 * i)
        f["api_ms"] = float(19000 + 31 * i)
        f["n_tool_calls"] = float(3 + i % 4)
        f["tool_latency_ms_total"] = float(11 * (i % 7))
        sid = f"S{i % 4 + 1:02d}-{2000000 + i}"
        rows.append({
            "scenario_id": sid, "run_id": "R5-fake-train", "trace_id": f"trace-{i}",
            "split": "train", "group": sid[:3], "local_model": "qwen3-8b",
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "snapshot_digest": "0" * 64,
            "features": f,
            "label_safe": not unsafe, "label_unsafe": unsafe,
            "r4_escalate": i % 17 == 0, "r4_reason": "no_output" if i % 17 == 0 else None,
            "strong_pass": None,
            "diag": {"unsafe": unsafe, "silent": unsafe and i % 17 != 0},
            "meta": {"category": ["ledger", "webhook", "kyc", "risk"][i % 4]},
            "answer_structure": None,
        })
    return rows


DMETA = {"run_id": "R5-fake-train", "dataset_digest": "d" * 64,
         "local_model": "qwen3-8b", "local_model_short": "qwen"}


@pytest.fixture(scope="module")
def trained() -> dict:
    rows = _train_rows()
    return {p: train_candidate("lr_full", "logistic", list(FEATURE_ORDER), rows,
                               eligible_kind=True, dataset_meta=DMETA, protocol=p)
            for p in ("grouped", "stratified")}


class TestTrainCandidate:

    @pytest.mark.parametrize("protocol", ["grouped", "stratified"])
    def test_the_artifact_carries_everything_section_13_requires(self, trained, protocol):
        a = trained[protocol]
        assert a["policy_id"] == ("r5-qwen-lr_full-v1" if protocol == "grouped"
                                  else "r5-qwen-lr_full-stratified-v1")
        assert a["protocol"] == protocol
        assert a["family"] == "logistic" and a["feature_source"] == "features"
        assert a["feature_schema_version"] == FEATURE_SCHEMA_VERSION
        assert a["feature_names"] == list(FEATURE_ORDER)
        assert a["threshold"] in THRESHOLD_GRID and a["threshold_grid"] == THRESHOLD_GRID
        assert a["hyperparameter"] in a["hyperparameter_grid"]
        assert a["router"]["family"] == "logistic"
        assert a["router"]["standardizer"] is not None       # § 13: preprocessing pinned
        assert a["router"]["feature_names"] == list(FEATURE_ORDER)
        assert len(a["artifact_digest"]) == 64
        assert a["train_run_id"] == "R5-fake-train"
        assert a["train_dataset_digest"] == "d" * 64
        assert a["train_n_all"] == 60
        assert a["train_n_accepted"] == 60 - sum(1 for i in range(60) if i % 17 == 0)
        assert a["dev_selection"] is None

    @pytest.mark.parametrize("protocol", ["grouped", "stratified"])
    def test_both_cv_protocols_are_always_reported(self, trained, protocol):
        cv = trained[protocol]["cv"]
        for key in ("grouped_oof", "stratified4_oof", "primary_oof"):
            assert set(cv[key]) >= {"roc_auc", "pr_auc", "brier", "log_loss", "base_rate", "n"}
        # the protocol's own CV is the one that drove hp/τ/gate
        assert cv["primary_oof"] == cv["grouped_oof" if protocol == "grouped" else "stratified4_oof"]
        assert len(cv["utility_curve"]) == 11
        assert [c["threshold"] for c in cv["utility_curve"]] == THRESHOLD_GRID
        assert cv["at_threshold"]["threshold"] == trained[protocol]["threshold"]

    def test_the_utility_curve_counts_catches_and_unnecessary_on_the_accepted_subset(self):
        y = [1, 1, 0, 0]
        p = [0.9, 0.4, 0.7, 0.1]
        curve = _utility_curve(y, p, n_all=8)
        at_50 = next(c for c in curve if c["threshold"] == 0.50)
        assert at_50["escalated"] == 2 and at_50["catches"] == 1
        assert at_50["unnecessary"] == 1 and at_50["utility"] == 0
        assert at_50["escalation_rate_all"] == 2 / 8
        assert at_50["unnecessary_rate_all"] == 1 / 8
        assert at_50["unnecessary_rate_safe"] == 1 / 2
        assert at_50["catch_rate"] == 1 / 2 and at_50["precision"] == 1 / 2

    def test_ties_in_utility_go_to_the_larger_threshold(self):
        """Contract § 10: "ties → the larger τ" — the conservative end of the grid."""
        curve = [{"threshold": t, "utility": 7 if t in (0.40, 0.60, 0.75) else 2}
                 for t in THRESHOLD_GRID]
        assert _pick_threshold(curve) == 0.75
        assert _pick_threshold([{"threshold": t, "utility": 0} for t in THRESHOLD_GRID]) == 0.80

    def test_eligibility_is_kind_and_gate_never_numbers_alone(self):
        rows = _train_rows()
        good = train_candidate("lr_full", "logistic", list(FEATURE_ORDER), rows,
                               eligible_kind=True, dataset_meta=DMETA, protocol="stratified")
        assert good["train_gate"]["passed"] is True         # the fixture has real signal
        assert good["eligible"] is True

        exploratory = train_candidate("lr_full", "logistic", list(FEATURE_ORDER), rows,
                                      eligible_kind=False, dataset_meta=DMETA,
                                      protocol="stratified")
        assert exploratory["train_gate"] == good["train_gate"]      # identical numbers
        assert exploratory["cv"]["primary_oof"] == good["cv"]["primary_oof"]
        assert exploratory["eligible_kind"] is False
        assert exploratory["eligible"] is False                     # kind vetoes the gate

    @pytest.mark.parametrize("protocol", ["grouped", "stratified"])
    def test_the_artifact_digest_is_stable_across_identical_calls(self, trained, protocol):
        rows = _train_rows()
        again = train_candidate("lr_full", "logistic", list(FEATURE_ORDER), rows,
                                eligible_kind=True, dataset_meta=DMETA, protocol=protocol)
        assert again["artifact_digest"] == trained[protocol]["artifact_digest"]
        assert again["router"] == trained[protocol]["router"]
        # and it is the digest of the artifact minus the fields the freeze step adds
        assert again["artifact_digest"] == digest(
            {k: v for k, v in again.items() if k not in ("artifact_digest", "dev_selection")})

    def test_the_two_protocols_are_different_artifacts(self, trained):
        assert trained["grouped"]["artifact_digest"] != trained["stratified"]["artifact_digest"]
        assert trained["grouped"]["policy_id"] != trained["stratified"]["policy_id"]

    def test_a_freshly_trained_artifact_passes_the_replay_fail_closed_check(self, trained):
        for a in trained.values():
            verify_artifact(a)          # no exception: train and replay agree on § 13


# ==================================================== E. replay: baselines and rules

# sid, label_safe, strong_pass, r4_escalate
_SPLIT = [
    ("S01-1", True,  True,  False),
    ("S02-2", False, True,  False),      # silent R4 routing FN
    ("S03-3", False, False, False),      # accepted failure the strong arm cannot fix
    ("S04-4", True,  False, True),       # R4 unnecessary escalation
    ("S05-5", False, True,  True),       # R4 rescue
    ("S06-6", True,  True,  False),
]


def _replay_rows() -> list[dict]:
    rows = []
    for sid, safe, strong, r4 in _SPLIT:
        rows.append({
            "scenario_id": sid, "label_safe": safe, "label_unsafe": not safe,
            "strong_pass": strong, "r4_escalate": r4, "group": sid[:3],
            "diag": {"wrong_root_cause": not safe, "evidence_miss": False,
                     "action_fail": False},
        })
    return rows


def _local_rows() -> dict[str, dict]:
    return {sid: {"score": {"wall_ms": 1000 * (i + 1)},
                  "traj": {"model_invocations": [{"usage": {"output_tokens": 100 * (i + 1)}}]}}
            for i, (sid, *_) in enumerate(_SPLIT)}


def _strong_rows() -> dict[str, dict]:
    return {sid: {"score": {"wall_ms": 100 * (i + 1), "reference_cost_usd": 0.01 * (i + 1)}}
            for i, (sid, *_) in enumerate(_SPLIT)}


class TestEvaluatePolicy:
    """Contract § 11 accounting, on the four baseline decision modes."""

    def _eval(self, mode: str) -> dict:
        rows = _replay_rows()
        return evaluate_policy(rows, _strong_rows(), _local_rows(),
                               decisions(rows, None, None, mode))

    def test_local_only_never_escalates_and_pays_no_strong_cost(self):
        m = self._eval("local")
        assert m["n"] == 6 and m["escalated"] == 0 and m["utilization"] == 0.0
        assert m["all_pass"] == 3                     # the three safe cases
        assert m["unnecessary"] == 0 and m["rescued_needed"] == 0 and m["rescue_rate"] is None
        assert m["accepted_fail"] == 3                # S02, S03, S05
        assert m["routing_fn"] == 2                   # accepted ∧ ¬safe ∧ strong pass
        assert m["cost_total"] == 0.0 and m["cost_per_attempt"] == 0.0
        assert m["wall_p50_ms"] == 3500 and m["wall_p95_ms"] == 6000     # local wall only
        assert m["local_output_tokens"] == sum(100 * (i + 1) for i in range(6))

    def test_strong_only_escalates_everything_and_all_pass_is_the_strong_arm(self):
        m = self._eval("strong")
        assert m["escalated"] == 6 and m["utilization"] == 1.0
        assert m["all_pass"] == sum(1 for _, _, sp, _ in _SPLIT if sp)   # 4
        assert m["routing_fn"] == 0 and m["accepted_fail"] == 0
        assert m["unnecessary"] == 3                  # every safe case was escalated
        assert m["rescued_needed"] == 2               # S02, S05
        assert m["rescue_rate"] == 2 / 6
        assert m["cost_total"] == pytest.approx(sum(0.01 * (i + 1) for i in range(6)))
        # wall = local + strong on every case
        assert m["wall_p50_ms"] == 3850 and m["wall_p95_ms"] == 6600
        # the weak stage is always paid, escalated or not
        assert m["local_output_tokens"] == sum(100 * (i + 1) for i in range(6))

    def test_r4_pays_the_strong_arm_only_on_the_cases_it_escalated(self):
        m = self._eval("r4")
        assert m["escalated"] == 2 and m["utilization"] == 2 / 6
        assert m["all_pass"] == 3                     # S01, S06 local + S05 strong
        assert m["unnecessary"] == 1                  # S04 was already safe
        assert m["rescued_needed"] == 1               # S05
        assert m["rescue_rate"] == 0.5
        assert m["routing_fn"] == 1                   # S02 stayed local and strong could fix it
        assert m["accepted_fail"] == 2                # S02, S03
        assert m["cost_total"] == pytest.approx(0.04 + 0.05)
        assert m["cost_per_attempt"] == pytest.approx(0.09 / 6)
        assert m["cost_per_success"] == pytest.approx(0.09 / 3)
        # walls: 1000, 2000, 3000, 4400, 5500, 6000
        assert m["wall_p50_ms"] == 3700 and m["wall_p95_ms"] == 6000

    def test_the_oracle_escalates_exactly_the_cases_the_strong_arm_would_rescue(self):
        m = self._eval("oracle")
        assert m["escalated"] == 2                    # S02, S05
        assert m["all_pass"] == 5                     # safe ∨ (unsafe ∧ strong pass)
        assert m["unnecessary"] == 0                  # by construction
        assert m["routing_fn"] == 0
        assert m["rescued_needed"] == 2 and m["rescue_rate"] == 1.0
        assert m["accepted_fail"] == 1                # S03: nobody can fix it

    def test_a_learned_decision_is_r4_or_the_threshold(self):
        rows = _replay_rows()
        risk = {"S01-1": 0.9, "S02-2": 0.7, "S03-3": 0.1,
                "S04-4": 0.0, "S05-5": 0.0, "S06-6": 0.49}
        esc = decisions(rows, risk, 0.50, "learned")
        assert esc == {"S01-1": True, "S02-2": True, "S03-3": False,
                       "S04-4": True, "S05-5": True, "S06-6": False}
        # τ is a >= comparison, and R4's own escalations survive any risk score
        assert decisions(rows, dict.fromkeys(risk, 0.50), 0.50, "learned")["S03-3"] is True
        assert decisions(rows, dict.fromkeys(risk, 0.0), 0.50, "learned")["S04-4"] is True

    def test_an_unknown_mode_is_a_programming_error(self):
        with pytest.raises(ValueError):
            decisions(_replay_rows(), None, None, "wishful")


class TestClassifierMetrics:
    def test_metrics_are_computed_on_the_r4_accepted_subset_only(self):
        rows = _replay_rows()
        risk = {"S01-1": 0.1, "S02-2": 0.9, "S03-3": 0.6,
                "S04-4": 0.99, "S05-5": 0.99, "S06-6": 0.2}
        c = classifier_metrics(rows, risk, 0.50)
        assert c["n_accepted"] == 4                    # S04 and S05 are R4's, not the router's
        assert c["unsafe_in_accepted"] == 2            # S02, S03
        assert (c["tp"], c["fp"], c["fn"], c["tn"]) == (2, 0, 0, 2)
        assert c["unsafe_recall"] == 1.0 and c["unsafe_precision"] == 1.0
        assert c["base_rate"] == 0.5
        assert c["roc_auc"] == 1.0

    def test_an_empty_accepted_subset_reports_no_classifier_instead_of_crashing(self):
        """Regression: `brier` raises on an empty list; a split R4 escalates entirely must
        yield "no accepted subset" (None metrics), not crash the replay — least of all
        after a TEST unlock has been consumed."""
        rows = [{"scenario_id": "S01-1", "label_unsafe": True, "label_safe": False,
                 "r4_escalate": True}]
        c = classifier_metrics(rows, {"S01-1": 0.9}, 0.50)
        assert c["n_accepted"] == 0
        assert c["roc_auc"] is None and c["pr_auc"] is None and c["brier"] is None
        assert c["base_rate"] is None


class TestSilentFamily:
    """§ 11's three buckets: `wrong_root_cause` first, then evidence-only, then other."""

    @staticmethod
    def _row(sid, *, safe, strong, r4, **diag):
        d = {"wrong_root_cause": False, "evidence_miss": False, "action_fail": False}
        d.update(diag)
        return {"scenario_id": sid, "label_safe": safe, "label_unsafe": not safe,
                "strong_pass": strong, "r4_escalate": r4, "diag": d}

    def test_kinds_and_the_caught_remaining_split(self):
        rows = [
            self._row("A", safe=False, strong=True, r4=False, wrong_root_cause=True),
            self._row("B", safe=False, strong=True, r4=False, evidence_miss=True),
            self._row("C", safe=False, strong=True, r4=False, evidence_miss=True,
                      action_fail=True),                       # evidence AND action → other
            self._row("D", safe=False, strong=True, r4=False),  # nothing flagged → other
            self._row("E", safe=True, strong=True, r4=False),   # safe: a new unnecessary
            self._row("F", safe=False, strong=False, r4=False),  # unsafe but unrescuable
            self._row("G", safe=False, strong=True, r4=True, wrong_root_cause=True),
        ]
        escalate = {"A": True, "B": True, "C": False, "D": False,
                    "E": True, "F": True, "G": True}
        s = silent_family(rows, escalate)
        assert s["r4_fn"] == 4                       # A, B, C, D — G is not R4-accepted
        assert s["caught"] == 2 and s["caught_ids"] == ["A", "B"]
        assert s["caught_by_kind"] == {"root_cause": 1, "evidence": 1}
        assert s["remaining"] == 2 and s["remaining_ids"] == ["C", "D"]
        assert s["remaining_by_kind"] == {"other": 2}
        assert s["new_unnecessary"] == 1 and s["new_unnecessary_ids"] == ["E"]

    def test_a_wrong_root_cause_dominates_an_evidence_miss(self):
        rows = [self._row("A", safe=False, strong=True, r4=False,
                          wrong_root_cause=True, evidence_miss=True)]
        s = silent_family(rows, {"A": True})
        assert s["caught_by_kind"] == {"root_cause": 1}


# ------------------------------------------------------------------ selection rule

def _cand(pid, *, eligible=True, fn=10, util=0.35, all_pass=25, unnecessary=3,
          escalated=17, cps=0.02, wall=41000) -> dict:
    return {"policy_id": pid, "eligible": eligible, "system": {
        "routing_fn": fn, "utilization": util, "all_pass": all_pass,
        "unnecessary": unnecessary, "escalated": escalated,
        "cost_per_success": cps, "wall_p50_ms": wall}}


R4_DEV = {"routing_fn": 16, "utilization": 0.30, "all_pass": 20}
RULE = {"per_model": {"qwen": {
    "grouped": {"delta_util": None, "e_max": None, "absolute_cap": 0.50},
    "stratified": {"delta_util": 0.20, "e_max": 6, "absolute_cap": None},
}}}


class TestApplyRule:

    def test_k_is_a_quarter_of_the_incumbent_blind_spot_with_a_floor_of_three(self):
        for fn_r4, expected_k in ((16, 4), (12, 3), (4, 3), (0, 3), (21, 6)):
            _, verdicts = apply_rule("qwen", RULE, {**R4_DEV, "routing_fn": fn_r4},
                                     [_cand("p")], "stratified")
            assert verdicts[0]["K"] == expected_k == max(3, math.ceil(0.25 * fn_r4))

    def test_a_candidate_that_clears_r1_r2_and_r3_wins(self):
        winner, (v,) = apply_rule("qwen", RULE, R4_DEV,
                                  [_cand("good", fn=12, util=0.45, all_pass=25,
                                         unnecessary=6)], "stratified")
        assert (v["R1_fn_reduction"], v["R2_no_collapse"], v["R3_quality"]) == (True, True, True)
        assert v["pass"] is True and winner["policy_id"] == "good"
        assert (v["K"], v["delta_util"], v["e_max"]) == (4, 0.20, 6)

    @pytest.mark.parametrize("kwargs,failing", [
        ({"fn": 13}, "R1_fn_reduction"),          # 13 > 16 - 4
        ({"unnecessary": 7}, "R2_no_collapse"),   # 7 > E_max 6
        ({"util": 0.51}, "R2_no_collapse"),       # > R4 util 0.30 + Δ_util 0.20
        ({"all_pass": 20}, "R3_quality"),         # must strictly exceed R4
    ])
    def test_each_criterion_can_veto_on_its_own(self, kwargs, failing):
        passing = {"fn": 12, "util": 0.45, "all_pass": 25, "unnecessary": 6}
        _, (v,) = apply_rule("qwen", RULE, R4_DEV,
                             [_cand("c", **{**passing, **kwargs})], "stratified")
        assert v[failing] is False and v["pass"] is False

    def test_an_ineligible_candidate_is_reported_but_never_selected(self):
        winner, (v,) = apply_rule("qwen", RULE, R4_DEV,
                                  [_cand("expl", eligible=False, fn=0, util=0.31,
                                         all_pass=48, unnecessary=0)], "stratified")
        assert v["R1_fn_reduction"] and v["R2_no_collapse"] and v["R3_quality"]
        assert v["pass"] is False and winner is None

    def test_null_amendment_numbers_make_r2_unpassable(self):
        """A protocol with no eligible TRAIN candidate records Δ_util / E_max as null;
        nothing can pass R2 then, by construction (§ 12a)."""
        winner, (v,) = apply_rule("qwen", RULE, R4_DEV,
                                  [_cand("perfect", fn=0, util=0.30, all_pass=48,
                                         unnecessary=0)], "grouped")
        assert v["delta_util"] is None and v["e_max"] is None
        assert v["R1_fn_reduction"] and v["R3_quality"]
        assert v["R2_no_collapse"] is False and v["pass"] is False and winner is None

    def test_a_missing_protocol_entry_is_refused_not_defaulted(self):
        with pytest.raises(SystemExit, match="no stratified entry for nemotron"):
            apply_rule("nemotron", RULE, R4_DEV, [_cand("c")], "stratified")

    def test_a_rule_entry_without_absolute_cap_keeps_the_section_12_fifty_percent_cap(self):
        """Regression: a MISSING `absolute_cap` key is the § 12 primary reading (0.50);
        only an explicit `null` — written by r5_amend_rule.py for the § 12a-2 secondary
        protocol — lifts the cap. A rule entry written before the key existed must not
        silently select a policy the § 12 cap forbids (fail closed, not open)."""
        r4 = {"routing_fn": 16, "utilization": 0.45, "all_pass": 20}
        over_fifty = _cand("over50", fn=8, util=0.60, all_pass=30, unnecessary=5)

        head_shape = {"per_model": {"qwen": {"stratified": {"delta_util": 0.20, "e_max": 6}}}}
        winner, (v,) = apply_rule("qwen", head_shape, r4, [over_fifty], "stratified")
        assert v["R2_no_collapse"] is False and v["pass"] is False and winner is None
        assert v["R2_under_skeleton_caps"] is False

        uncapped = {"per_model": {"qwen": {"stratified": {
            "delta_util": 0.20, "e_max": 6, "absolute_cap": None}}}}
        winner, (v2,) = apply_rule("qwen", uncapped, r4, [over_fifty], "stratified")
        assert v2["R2_no_collapse"] is True and v2["pass"] is True     # explicit null lifts it
        assert v2["R2_under_skeleton_caps"] is False                   # …and the § 12 reading is shown beside it

    def test_tie_break_is_escalations_then_cost_per_success_then_wall(self):
        base = {"fn": 12, "util": 0.45, "all_pass": 25, "unnecessary": 6}
        winner, _ = apply_rule("qwen", RULE, R4_DEV, [
            _cand("many", escalated=20, cps=0.001, wall=1, **base),
            _cand("few", escalated=15, cps=0.09, wall=99999, **base),
        ], "stratified")
        assert winner["policy_id"] == "few"                       # fewer frontier calls

        winner, _ = apply_rule("qwen", RULE, R4_DEV, [
            _cand("dear", escalated=15, cps=0.09, wall=1, **base),
            _cand("cheap", escalated=15, cps=0.01, wall=99999, **base),
        ], "stratified")
        assert winner["policy_id"] == "cheap"                     # then cost/success

        winner, _ = apply_rule("qwen", RULE, R4_DEV, [
            _cand("slow", escalated=15, cps=0.01, wall=99999, **base),
            _cand("fast", escalated=15, cps=0.01, wall=1000, **base),
        ], "stratified")
        assert winner["policy_id"] == "fast"                      # then wall p50


# ------------------------------------------------------------------ § 13 fail-closed

def _artifact(**over) -> dict:
    a = {
        "policy_id": "r5-qwen-lr_core-v1", "candidate": "lr_core", "protocol": "grouped",
        "family": "logistic", "eligible_kind": True, "eligible": True,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_source": "features",
        "feature_names": ["output_tokens", "n_violations"],
        "hyperparameter": 1.0, "threshold": 0.60, "threshold_grid": THRESHOLD_GRID,
        "router": {"family": "logistic", "feature_names": ["output_tokens", "n_violations"],
                   "standardizer": {"means": [500.0, 0.0], "stds": [100.0, 1.0],
                                    "constant": [False, True]},
                   "model": {"kind": "logistic", "l2": 1.0, "max_iter": 100, "tol": 1e-8,
                             "intercept": 0.0, "coef": [1.0, 0.0], "n_iter": 4,
                             "converged": True}},
        "local_model": "qwen3-8b", "dev_selection": None,
    }
    a.update(over)
    a["artifact_digest"] = digest({k: v for k, v in a.items() if k not in _MUTABLE_FIELDS})
    return a


class TestVerifyArtifact:
    """§ 13: replay fails closed rather than producing a number that looks like a result."""

    def test_a_well_formed_artifact_verifies(self):
        verify_artifact(_artifact())

    def test_a_foreign_feature_schema_version_is_refused(self):
        with pytest.raises(SystemExit, match="artifact schema 2 != extractor"):
            verify_artifact(_artifact(feature_schema_version="2"))

    def test_a_name_outside_the_allowlist_over_production_features_is_refused(self):
        with pytest.raises(SystemExit, match="features outside the allowlist"):
            verify_artifact(_artifact(feature_names=["output_tokens", "local_gpu_temp_c"]))

    def test_eligibility_over_a_non_production_feature_source_is_refused(self):
        """`prior` is the analysis-only category comparator; it may be reported, never
        selected, whatever its TRAIN numbers say."""
        with pytest.raises(SystemExit, match="claims eligibility"):
            verify_artifact(_artifact(feature_source="prior", candidate="prior_category",
                                      feature_names=["category_ledger", "category_kyc"]))
        # …and the same artifact marked exploratory is fine
        verify_artifact(_artifact(feature_source="prior", candidate="prior_category",
                                  eligible=False, eligible_kind=False,
                                  feature_names=["category_ledger", "category_kyc"]))

    def test_a_candidate_outside_the_section_9_list_may_not_claim_eligibility(self):
        with pytest.raises(SystemExit, match="claims eligibility"):
            verify_artifact(_artifact(candidate="lr_answer"))

    def test_a_tampered_digest_is_refused(self):
        a = _artifact()
        a["artifact_digest"] = "0" * 64
        with pytest.raises(SystemExit, match="artifact digest mismatch"):
            verify_artifact(a)

        b = _artifact()
        b["threshold"] = 0.30            # a real edit, digest left as it was
        with pytest.raises(SystemExit, match="artifact digest mismatch"):
            verify_artifact(b)

    def test_the_freeze_step_may_add_its_own_fields_without_breaking_the_digest(self):
        a = _artifact()
        a["local_model_short"] = "qwen"
        a["dev_selection"] = {"result": "PASS"}
        verify_artifact(a)               # § 13: the frozen copy keeps its TRAIN digest


# ------------------------------------------------------------------ § 12a derivation

def _report_candidate(pid, *, eligible, esc_rate, unn_rate) -> dict:
    return {"policy_id": pid, "eligible": eligible, "threshold": 0.60,
            "cv": {"at_threshold": {"escalation_rate_all": esc_rate,
                                    "unnecessary_rate_all": unn_rate,
                                    "catches": 10, "unnecessary": 3}}}


class TestDeriveAmendment:
    """§ 12a: the numbers are a computation over committed TRAIN artifacts, not a
    number typed after looking at anything."""

    def test_delta_util_and_e_max_follow_the_pre_registered_formulas(self):
        report = {"candidates": [
            _report_candidate("a", eligible=True, esc_rate=0.10, unn_rate=0.02),
            _report_candidate("b", eligible=True, esc_rate=0.4305555555555556,
                              unn_rate=0.0763888888888889),
            _report_candidate("c", eligible=False, esc_rate=0.99, unn_rate=0.99),
        ]}
        got = derive(report)
        assert got["eligible_candidates"] == ["a", "b"]       # the ineligible one is ignored
        assert got["delta_util"] == round(min(0.20, 1.5 * 0.4305555555555556), 6) == 0.20
        assert got["e_max"] == math.ceil(1.5 * 0.0763888888888889 * 48) == 6
        assert got["derivation"]["max_oof_escalation_rate_all"] == 0.4305555555555556
        assert len(got["inputs"]) == 3                        # every candidate is recorded

    def test_the_cap_only_binds_when_the_formula_exceeds_it(self):
        report = {"candidates": [_report_candidate("a", eligible=True, esc_rate=0.10,
                                                   unn_rate=0.01)]}
        got = derive(report)
        assert got["delta_util"] == round(1.5 * 0.10, 6) == 0.15
        assert got["e_max"] == math.ceil(1.5 * 0.01 * 48) == 1

    def test_no_eligible_candidate_means_null_numbers(self):
        report = {"candidates": [
            _report_candidate("a", eligible=False, esc_rate=0.10, unn_rate=0.02)]}
        got = derive(report)
        assert got == {"eligible_candidates": [], "delta_util": None, "e_max": None,
                       "absolute_cap": 0.50, "inputs": got["inputs"]}
        assert got["inputs"][0]["policy_id"] == "a"

    def test_the_secondary_protocol_drops_the_a_priori_caps(self):
        """§ 12a-2: for the SECONDARY protocol the 1.5× TRAIN slack is applied WITHOUT
        the 20 pp cap and without an absolute utilization cap; the PRIMARY protocol keeps
        both. Pinned per protocol so a change to either reading is a visible diff."""
        report = {"candidates": [_report_candidate("a", eligible=True,
                                                   esc_rate=0.4305555555555556,
                                                   unn_rate=0.0763888888888889)]}
        strat = derive(report, "stratified")
        assert strat["delta_util"] == round(1.5 * 0.4305555555555556, 6) == 0.645833
        assert strat["absolute_cap"] is None
        assert strat["e_max"] == 6                     # E_max is unchanged by the protocol
        assert derive(report, "grouped")["absolute_cap"] == 0.50


# ================================================================= F. the TEST seal

class TestGuardSplit:
    """§ 14: TEST labels are unreadable until an unlock record names the run."""

    def test_a_dev_run_passes(self):
        guard_split("dev", "V3-qwen-dev", allow_test=False)
        guard_split("train", "R5-qwen-train", allow_test=False)

    def test_a_test_run_is_refused_without_allow_test(self):
        with pytest.raises(SystemExit, match="sealed for learned-policy work"):
            guard_split("test", "V3-qwen-96", allow_test=False)

    def test_allow_test_alone_is_not_enough(self, monkeypatch, tmp_path):
        monkeypatch.setattr(r5_dataset, "UNLOCK_FILE", tmp_path / "test_unlock.json")
        with pytest.raises(SystemExit, match="no unlock record exists"):
            guard_split("test", "V3-qwen-96", allow_test=True)

    def test_an_unlock_record_that_names_another_run_does_not_open_this_one(
            self, monkeypatch, tmp_path):
        unlock = tmp_path / "test_unlock.json"
        unlock.write_text(json.dumps({"unlocks": [
            {"policy_id": "r5-qwen-lr_full-v1", "local_run": "V3-nemotron-96"}]}))
        monkeypatch.setattr(r5_dataset, "UNLOCK_FILE", unlock)
        with pytest.raises(SystemExit, match="is not named by any unlock"):
            guard_split("test", "V3-qwen-96", allow_test=True)

    def test_an_unlock_record_naming_the_run_opens_it(self, monkeypatch, tmp_path):
        unlock = tmp_path / "test_unlock.json"
        unlock.write_text(json.dumps({"unlocks": [
            {"policy_id": "r5-qwen-lr_full-v1", "local_run": "V3-qwen-96"}]}))
        monkeypatch.setattr(r5_dataset, "UNLOCK_FILE", unlock)
        guard_split("test", "V3-qwen-96", allow_test=True)

    def test_the_replay_and_dataset_layers_name_the_same_unlock_file(self):
        assert r5_dataset.UNLOCK_FILE == r5_replay.Registry().unlock_file
