"""Machine-checkable experiment-contract spec (fis_platform/contract_spec.py) +
scripts/contract_check.py CLI.

Every test builds its input as a raw dict (the shape `validate_contract_spec`
actually takes — a JSON-decoded contract document), not a `ContractSpec(...)` call,
so these tests exercise the same path a real `contract_check.py` invocation does.
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.contract_spec import ContractSpec, ContractSpecError, validate_contract_spec  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI = REPO_ROOT / "scripts" / "contract_check.py"


def _hex64(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _tolerance(spec_id: str = "cap-tolerance") -> dict:
    return {
        "spec_id": spec_id,
        "metric": "cap_hit_rate",
        "description": "output-cap tolerance, TRAIN pilot",
        "denominator_n": 36,
        "max_violations": 3,
        "consequence": "ABORT",
    }


def _valid_inferential() -> dict:
    """A fully-valid INFERENTIAL contract, matching every §-required field."""
    return {
        "spec_version": 1,
        "experiment_id": "R7-modern-strong-vs-efficiency",
        "experiment_type": "INFERENTIAL",
        "question": "does the modern_strong candidate beat the efficiency candidate on TEST?",
        "suite_version": "v3",
        "corpus_digest": _hex64("suite-v3-corpus"),
        "split_permissions": {"train": True, "dev": True, "test": True},
        "ordering_policy": "round_robin",
        "authoritative_clocks": {"wall_ms": "realtime", "api_ms": "monotonic"},
        "state_machine": "r6-v1+smoke",
        "artifact_lineage": [
            {"artifact_id": "qwen3-8b@abc123456789", "sha256": _hex64("qwen3-8b-weights")},
            {"artifact_id": "nemotron@def987654321", "sha256": _hex64("nemotron-weights")},
        ],
        "candidates": ["qwen3-8b", "nemotron"],
        "execution_system_digests": {
            "qwen3-8b": _hex64("qwen3-8b-execution-system"),
            "nemotron": _hex64("nemotron-execution-system"),
        },
        "tolerances": [_tolerance()],
        "expected_discordance_range": [0.30, 0.50],
        "clustering_unit": "scenario_class",
        "effective_n": 22.0,
        "mde_pp": 37.0,
        "primary_statistic": "cluster_robust_paired_t",
        "secondary_statistic": "mcnemar_exact",
        "descriptive_vocabulary": [
            {"term": "competitive", "definition": "within +/-4 cases of one another"},
        ],
        "allowed_verdicts": ["CONFIRMED", "REFUTED", "INCONCLUSIVE"],
        "prediction_ref": "pred-r7-001",
        "curtailment_policy": {"enabled": True, "bar": 0.6, "disable_justification": None},
        "test_look": {"planned": True, "look_no": 1, "trigger_review_ref": None},
    }


def _valid_screening() -> dict:
    d = _valid_inferential()
    for key in ("execution_system_digests", "expected_discordance_range", "clustering_unit",
               "effective_n", "mde_pp", "primary_statistic", "secondary_statistic",
               "prediction_ref", "curtailment_policy", "test_look"):
        d.pop(key, None)
    d["experiment_type"] = "SCREENING"
    d["allowed_verdicts"] = ["RANKED", "INCONCLUSIVE"]
    return d


def _valid_diagnostic() -> dict:
    d = _valid_inferential()
    for key in ("candidates", "execution_system_digests", "tolerances",
               "expected_discordance_range", "clustering_unit", "effective_n", "mde_pp",
               "primary_statistic", "secondary_statistic", "allowed_verdicts",
               "prediction_ref", "curtailment_policy", "test_look"):
        d.pop(key, None)
    d["experiment_type"] = "DIAGNOSTIC"
    d["artifact_lineage"] = []      # allowed empty for DIAGNOSTIC
    return d


def _valid_measurement() -> dict:
    d = _valid_diagnostic()
    d["experiment_type"] = "MEASUREMENT"
    return d


# ---------------------------------------------------------------- happy paths

def test_fully_valid_inferential_validates_and_digests_deterministically():
    data = _valid_inferential()
    spec = validate_contract_spec(data)
    assert isinstance(spec, ContractSpec)
    d1 = spec.contract_spec_digest
    spec2 = validate_contract_spec(copy.deepcopy(data))
    assert spec2.contract_spec_digest == d1
    assert len(d1) == 64 and all(c in "0123456789abcdef" for c in d1)


def test_valid_screening_validates():
    spec = validate_contract_spec(_valid_screening())
    assert spec.experiment_type.value == "SCREENING"
    assert "RANKED" in spec.allowed_verdicts


def test_valid_diagnostic_validates_with_empty_artifact_lineage():
    spec = validate_contract_spec(_valid_diagnostic())
    assert spec.experiment_type.value == "DIAGNOSTIC"
    assert spec.artifact_lineage == []


def test_valid_measurement_validates():
    spec = validate_contract_spec(_valid_measurement())
    assert spec.experiment_type.value == "MEASUREMENT"


def test_different_specs_digest_differently():
    a = validate_contract_spec(_valid_inferential())
    b_data = _valid_inferential()
    b_data["mde_pp"] = 40.0
    b = validate_contract_spec(b_data)
    assert a.contract_spec_digest != b.contract_spec_digest


# ---------------------------------------------------------------- inferential requirements

def test_inferential_missing_mde_pp_refused_with_mde_named_in_the_error():
    data = _valid_inferential()
    del data["mde_pp"]
    with pytest.raises(ContractSpecError, match="mde_pp"):
        validate_contract_spec(data)


def test_inferential_missing_multiple_fields_lists_all_of_them_at_once():
    data = _valid_inferential()
    del data["mde_pp"]
    del data["effective_n"]
    del data["candidates"]
    del data["prediction_ref"]
    with pytest.raises(ContractSpecError) as exc_info:
        validate_contract_spec(data)
    msg = str(exc_info.value)
    for field in ("mde_pp", "effective_n", "candidates", "prediction_ref"):
        assert field in msg, f"{field!r} missing from combined error message:\n{msg}"


def test_inferential_missing_field_and_bad_structural_field_both_reported_together():
    """The core guarantee this design exists for: a structural typo (bad corpus_digest)
    and a type-required-field omission (missing tolerances) must both show up in ONE
    ContractSpecError, not one-at-a-time across repeated validation attempts."""
    data = _valid_inferential()
    data["corpus_digest"] = "not-64-hex"
    del data["tolerances"]
    with pytest.raises(ContractSpecError) as exc_info:
        validate_contract_spec(data)
    msg = str(exc_info.value)
    assert "corpus_digest" in msg
    assert "tolerances" in msg


def test_inferential_missing_artifact_lineage_refused():
    data = _valid_inferential()
    data["artifact_lineage"] = []
    with pytest.raises(ContractSpecError, match="artifact_lineage"):
        validate_contract_spec(data)


def test_inferential_ranked_verdict_refused():
    data = _valid_inferential()
    data["allowed_verdicts"] = ["CONFIRMED", "RANKED"]
    with pytest.raises(ContractSpecError, match="RANKED"):
        validate_contract_spec(data)


def test_missing_consequence_on_a_nested_tolerance_is_unrepresentable():
    data = _valid_inferential()
    bad_tolerance = _tolerance()
    del bad_tolerance["consequence"]
    data["tolerances"] = [bad_tolerance]
    with pytest.raises(ContractSpecError, match="consequence"):
        validate_contract_spec(data)


# ---------------------------------------------------------------- screening requirements

def test_screening_requires_candidates_and_tolerances_but_not_mde():
    data = _valid_screening()
    del data["candidates"]
    del data["tolerances"]
    with pytest.raises(ContractSpecError) as exc_info:
        validate_contract_spec(data)
    msg = str(exc_info.value)
    assert "candidates" in msg and "tolerances" in msg
    assert "mde_pp" not in msg   # never required for SCREENING


def test_screening_with_confirmed_refused():
    data = _valid_screening()
    data["allowed_verdicts"] = ["RANKED", "CONFIRMED"]
    with pytest.raises(ContractSpecError, match="CONFIRMED"):
        validate_contract_spec(data)


def test_screening_with_refuted_refused():
    data = _valid_screening()
    data["allowed_verdicts"] = ["RANKED", "REFUTED"]
    with pytest.raises(ContractSpecError, match="REFUTED"):
        validate_contract_spec(data)


def test_screening_without_ranked_refused():
    data = _valid_screening()
    data["allowed_verdicts"] = ["INCONCLUSIVE"]
    with pytest.raises(ContractSpecError, match="RANKED"):
        validate_contract_spec(data)


# ---------------------------------------------------------------- diagnostic / measurement

def test_diagnostic_with_planned_test_look_refused():
    data = _valid_diagnostic()
    data["test_look"] = {"planned": True, "look_no": 1, "trigger_review_ref": None}
    with pytest.raises(ContractSpecError, match="test_look"):
        validate_contract_spec(data)


def test_diagnostic_with_test_look_planned_false_is_fine():
    data = _valid_diagnostic()
    data["test_look"] = {"planned": False, "look_no": None, "trigger_review_ref": None}
    spec = validate_contract_spec(data)
    assert spec.test_look.planned is False


def test_diagnostic_with_no_test_look_at_all_is_fine():
    data = _valid_diagnostic()
    assert "test_look" not in data
    validate_contract_spec(data)   # must not raise


def test_measurement_requires_only_the_common_core():
    data = _valid_measurement()
    # nothing conditional is present at all; must still validate.
    for key in ("candidates", "tolerances", "mde_pp", "curtailment_policy", "test_look"):
        assert key not in data
    validate_contract_spec(data)


# ---------------------------------------------------------------- curtailment_policy / test_look

def test_curtailment_disabled_without_justification_refused():
    data = _valid_inferential()
    data["curtailment_policy"] = {"enabled": False, "bar": None, "disable_justification": None}
    with pytest.raises(ContractSpecError, match="disable_justification"):
        validate_contract_spec(data)


def test_curtailment_disabled_with_justification_is_fine():
    data = _valid_inferential()
    data["curtailment_policy"] = {
        "enabled": False, "bar": None,
        "disable_justification": "SCREENING-only pilot, TRAIN split, no DEV/TEST spend at risk",
    }
    validate_contract_spec(data)   # must not raise


def test_curtailment_enabled_without_bar_refused():
    data = _valid_inferential()
    data["curtailment_policy"] = {"enabled": True, "bar": None, "disable_justification": None}
    with pytest.raises(ContractSpecError, match="bar"):
        validate_contract_spec(data)


def test_look_no_8_without_trigger_review_ref_refused():
    data = _valid_inferential()
    data["test_look"] = {"planned": True, "look_no": 8, "trigger_review_ref": None}
    with pytest.raises(ContractSpecError, match="trigger_review_ref"):
        validate_contract_spec(data)


def test_look_no_8_with_trigger_review_ref_is_fine():
    data = _valid_inferential()
    data["test_look"] = {
        "planned": True, "look_no": 8,
        "trigger_review_ref": "suite-v4-trigger-review-2026-08-21",
    }
    spec = validate_contract_spec(data)
    assert spec.test_look.look_no == 8


def test_look_no_below_8_needs_no_trigger_review_ref():
    data = _valid_inferential()
    data["test_look"] = {"planned": True, "look_no": 7, "trigger_review_ref": None}
    validate_contract_spec(data)   # must not raise


def test_planned_true_without_look_no_refused():
    data = _valid_inferential()
    data["test_look"] = {"planned": True, "look_no": None, "trigger_review_ref": None}
    with pytest.raises(ContractSpecError, match="look_no"):
        validate_contract_spec(data)


# ---------------------------------------------------------------- extra='forbid'

def test_unknown_top_level_field_refused():
    data = _valid_inferential()
    data["totally_unexpected_field"] = "x"
    with pytest.raises(ContractSpecError):
        validate_contract_spec(data)


# ---------------------------------------------------------------- contract_check.py CLI

def test_cli_exits_0_and_prints_digest_for_a_valid_spec(tmp_path):
    path = tmp_path / "valid.json"
    path.write_text(json.dumps(_valid_inferential()), encoding="utf-8")
    result = subprocess.run([sys.executable, str(CLI), str(path)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("OK ")
    digest_str = result.stdout.strip().split()[1]
    assert len(digest_str) == 64


def test_cli_exits_1_and_prints_problems_for_an_invalid_spec(tmp_path):
    data = _valid_inferential()
    del data["mde_pp"]
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    result = subprocess.run([sys.executable, str(CLI), str(path)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "mde_pp" in result.stderr


def test_cli_exits_2_on_missing_file(tmp_path):
    result = subprocess.run([sys.executable, str(CLI), str(tmp_path / "nope.json")],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 2


def test_cli_exits_2_on_bad_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not valid json", encoding="utf-8")
    result = subprocess.run([sys.executable, str(CLI), str(path)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 2


def test_cli_exits_2_on_bad_usage():
    result = subprocess.run([sys.executable, str(CLI)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 2
