"""Prediction ledger — playbook § 7's empirical gate
(docs/current/EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md § 7; M_STAT_IMPLEMENTATION_MAP.md
item 6), against a TEMPORARY ledger file under `tmp_path`.

Nothing here touches `learning/registry/predictions.jsonl` — the live location is never
created or read by this module's default, and no test constructs `PredictionLedger()`
without an explicit path.

What each group defends:

  freeze/read   the happy path round-trips, and every guard on `freeze_prediction`
                (bad interval, empty rationale, duplicate id, non-finite bound) refuses
                with the ledger unchanged;
  evaluate      the happy path round-trips without touching the prediction entry it
                scores, and every guard on `evaluate` (unknown id, double evaluation,
                a caller's inside_interval/abs_error claim that disagrees with the
                ledger's own computation, a non-finite actual) refuses;
  chain         an edit to a written line is caught by `read()`, exactly the way an
                edited `fis_platform.provenance` state-log entry is caught.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform import predictions
from fis_platform.predictions import LedgerIntegrityError, PredictionLedger, PredictionRefused
from fis_platform.provenance import digest

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
CLI = str(REPO_ROOT / "scripts" / "prediction_ledger.py")


def _ledger(tmp_path: Path) -> PredictionLedger:
    return PredictionLedger(tmp_path / "predictions.jsonl")


def _freeze(ledger: PredictionLedger, **over: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "prediction_id": "R7-effect-size", "experiment_id": "R7",
        "metric": "all_pass_delta", "point": 6.0, "interval": (2.0, 10.0),
        "rationale": "prior deltas in this family cluster near +6",
    }
    fields.update(over)
    return ledger.freeze_prediction(**fields)


# ------------------------------------------------------------------ 0. the root

def test_no_ledger_file_exists_until_the_first_freeze(tmp_path):
    ledger = _ledger(tmp_path)
    assert ledger.read() == []
    assert not ledger.path.exists()
    assert "learning/registry" not in str(ledger.path)
    assert str(predictions.DEFAULT_LEDGER_PATH).endswith("learning/registry/predictions.jsonl")


# ------------------------------------------------------------------ 1. freeze -> read

def test_freeze_then_read_roundtrip(tmp_path):
    ledger = _ledger(tmp_path)
    entry = _freeze(ledger)
    assert entry["seq"] == 1
    assert entry["prev_entry_digest"] == ""
    assert entry["kind"] == "prediction"
    assert entry["prediction_id"] == "R7-effect-size"
    assert entry["candidate_id"] is None
    assert entry["interval"] == [2.0, 10.0]
    assert len(entry["entry_digest"]) == 64

    entries = ledger.read()
    assert entries == [entry]

    got = ledger.get("R7-effect-size")
    assert got["prediction"] == entry
    assert got["evaluation"] is None


def test_freeze_and_evaluate_roundtrip(tmp_path):
    ledger = _ledger(tmp_path)
    pred = _freeze(ledger)
    ev = ledger.evaluate("R7-effect-size", 7.0)
    assert ev["seq"] == 2
    assert ev["kind"] == "evaluation"
    assert ev["prev_entry_digest"] == pred["entry_digest"]
    assert ev["actual"] == 7.0
    assert ev["inside_interval"] is True
    assert ev["abs_error"] == pytest.approx(1.0)

    entries = ledger.read()
    assert [e["kind"] for e in entries] == ["prediction", "evaluation"]
    got = ledger.get("R7-effect-size")
    assert got["evaluation"] == ev


def test_evaluate_outside_the_interval_is_recorded_honestly(tmp_path):
    ledger = _ledger(tmp_path)
    _freeze(ledger)
    ev = ledger.evaluate("R7-effect-size", 25.0)
    assert ev["inside_interval"] is False
    assert ev["abs_error"] == pytest.approx(19.0)


# ------------------------------------------------------------------ 2. freeze guards

def test_interval_violating_lo_le_point_le_hi_is_refused(tmp_path):
    ledger = _ledger(tmp_path)
    with pytest.raises(PredictionRefused, match="not within interval"):
        _freeze(ledger, point=15.0, interval=(2.0, 10.0))
    with pytest.raises(PredictionRefused, match="lo > hi"):
        _freeze(ledger, point=5.0, interval=(10.0, 2.0))
    assert ledger.read() == []
    assert not ledger.path.exists()


def test_empty_rationale_is_refused(tmp_path):
    ledger = _ledger(tmp_path)
    with pytest.raises(PredictionRefused, match="non-empty"):
        _freeze(ledger, rationale="")
    with pytest.raises(PredictionRefused, match="non-empty"):
        _freeze(ledger, rationale="   ")
    assert ledger.read() == []


def test_a_non_finite_point_or_bound_is_refused(tmp_path):
    ledger = _ledger(tmp_path)
    with pytest.raises(PredictionRefused, match="finite"):
        _freeze(ledger, point=float("nan"))
    with pytest.raises(PredictionRefused, match="finite"):
        _freeze(ledger, interval=(float("-inf"), 10.0))
    assert ledger.read() == []


def test_blank_ids_are_refused(tmp_path):
    ledger = _ledger(tmp_path)
    with pytest.raises(PredictionRefused, match="non-empty"):
        _freeze(ledger, prediction_id="  ")
    with pytest.raises(PredictionRefused, match="non-empty"):
        _freeze(ledger, experiment_id="")
    assert ledger.read() == []


def test_a_duplicate_prediction_id_is_refused(tmp_path):
    ledger = _ledger(tmp_path)
    first = _freeze(ledger)
    before = ledger.path.read_bytes()
    with pytest.raises(PredictionRefused, match="already frozen"):
        _freeze(ledger, metric="something_else", point=1.0, interval=(0.0, 2.0))
    assert ledger.path.read_bytes() == before, "a refused freeze must not touch the file"
    assert ledger.read() == [first]


# ------------------------------------------------------------------ 3. evaluate guards

def test_evaluate_before_freeze_is_refused(tmp_path):
    ledger = _ledger(tmp_path)
    with pytest.raises(PredictionRefused, match="no prediction"):
        ledger.evaluate("never-frozen", 1.0)
    assert ledger.read() == []
    assert not ledger.path.exists()


def test_double_evaluate_is_refused(tmp_path):
    ledger = _ledger(tmp_path)
    _freeze(ledger)
    ledger.evaluate("R7-effect-size", 7.0)
    before = ledger.path.read_bytes()
    with pytest.raises(PredictionRefused, match="already been evaluated"):
        ledger.evaluate("R7-effect-size", 8.0)
    assert ledger.path.read_bytes() == before, "a refused evaluation must not touch the file"
    assert len(ledger.read()) == 2


def test_a_non_finite_actual_is_refused(tmp_path):
    ledger = _ledger(tmp_path)
    _freeze(ledger)
    with pytest.raises(PredictionRefused, match="finite"):
        ledger.evaluate("R7-effect-size", float("nan"))
    assert len(ledger.read()) == 1


def test_computed_field_mismatch_is_refused(tmp_path):
    """actual=7.0 against interval [2, 10] is inside, and |7 - 6| = 1: a caller claiming
    otherwise is disagreeing with the ledger's own arithmetic, not supplying new fact."""
    ledger = _ledger(tmp_path)
    _freeze(ledger)
    with pytest.raises(PredictionRefused, match="inside_interval"):
        ledger.evaluate("R7-effect-size", 7.0, inside_interval=False)
    with pytest.raises(PredictionRefused, match="abs_error"):
        ledger.evaluate("R7-effect-size", 7.0, abs_error=99.0)
    assert len(ledger.read()) == 1, "a refused evaluation must not be appended"

    # a caller who asserts the CORRECT computed values is not refused
    ev = ledger.evaluate("R7-effect-size", 7.0, inside_interval=True, abs_error=1.0)
    assert ev["inside_interval"] is True and ev["abs_error"] == pytest.approx(1.0)


def test_evaluation_preserves_the_original_prediction_bytes(tmp_path):
    ledger = _ledger(tmp_path)
    _freeze(ledger)
    lines_before = ledger.path.read_text().splitlines()
    assert len(lines_before) == 1

    ledger.evaluate("R7-effect-size", 7.0)

    lines_after = ledger.path.read_text().splitlines()
    assert len(lines_after) == 2
    assert lines_after[0] == lines_before[0], "the prediction line must be byte-identical"
    assert json.loads(lines_after[1])["kind"] == "evaluation"


# ------------------------------------------------------------------ 4. the chain

def _rewrite(path: Path, entries: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in entries))


def test_an_edited_field_is_caught_on_read(tmp_path):
    ledger = _ledger(tmp_path)
    _freeze(ledger)
    ledger.evaluate("R7-effect-size", 7.0)
    entries = ledger.read()
    entries[0]["point"] = 999.0                     # edited without recomputing entry_digest
    _rewrite(ledger.path, entries)
    with pytest.raises(LedgerIntegrityError, match="the entry was edited"):
        ledger.read()


def test_an_edit_with_a_recomputed_digest_still_breaks_the_chain(tmp_path):
    ledger = _ledger(tmp_path)
    _freeze(ledger)
    ledger.evaluate("R7-effect-size", 7.0)
    entries = ledger.read()
    entries[0]["point"] = 999.0
    entries[0]["entry_digest"] = digest({k: v for k, v in entries[0].items()
                                         if k != "entry_digest"})
    _rewrite(ledger.path, entries)
    with pytest.raises(LedgerIntegrityError, match="the ledger was rewritten"):
        ledger.read()


def test_an_unknown_entry_kind_is_refused(tmp_path):
    ledger = _ledger(tmp_path)
    _freeze(ledger)
    entries = ledger.read()
    entries[0]["kind"] = "prophecy"
    entries[0]["entry_digest"] = digest({k: v for k, v in entries[0].items()
                                         if k != "entry_digest"})
    _rewrite(ledger.path, entries)
    with pytest.raises(LedgerIntegrityError, match="not 'prediction' or 'evaluation'"):
        ledger.read()


# ------------------------------------------------------------------ 5. get()

def test_get_on_an_unknown_prediction_is_refused(tmp_path):
    ledger = _ledger(tmp_path)
    _freeze(ledger)
    with pytest.raises(PredictionRefused, match="no prediction"):
        ledger.get("someone-else")


# ------------------------------------------------------------------ 6. code_commit

def test_code_commit_defaults_to_git_head_and_can_be_overridden(tmp_path, monkeypatch):
    ledger = _ledger(tmp_path)
    monkeypatch.setattr(predictions, "git_head", lambda: "abc1234")
    entry = _freeze(ledger)
    assert entry["code_commit"] == "abc1234"
    ev = ledger.evaluate("R7-effect-size", 7.0, code_commit="def5678")
    assert ev["code_commit"] == "def5678"


# ------------------------------------------------------------------ 7. CLI

def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([PYTHON, CLI, *args], capture_output=True, text=True,
                          cwd=str(REPO_ROOT), check=False)


def test_cli_freeze_evaluate_show_verify_roundtrip(tmp_path):
    path = str(tmp_path / "predictions.jsonl")
    r = _run_cli("--path", path, "freeze", "--prediction-id", "R7-cli",
                "--experiment-id", "R7", "--metric", "all_pass_delta", "--point", "6",
                "--lo", "2", "--hi", "10", "--rationale", "cli smoke test")
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["prediction_id"] == "R7-cli"

    r = _run_cli("--path", path, "evaluate", "--prediction-id", "R7-cli", "--actual", "7")
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["inside_interval"] is True

    r = _run_cli("--path", path, "verify")
    assert r.returncode == 0, r.stderr
    assert "2 entries OK" in r.stdout

    r = _run_cli("--path", path, "show", "--prediction-id", "R7-cli")
    assert r.returncode == 0, r.stderr
    shown = json.loads(r.stdout)
    assert shown["prediction"]["prediction_id"] == "R7-cli"
    assert shown["evaluation"]["actual"] == 7.0


def test_cli_refuses_a_second_evaluation_and_leaves_the_file_unchanged(tmp_path):
    path = tmp_path / "predictions.jsonl"
    _run_cli("--path", str(path), "freeze", "--prediction-id", "R7-cli",
             "--experiment-id", "R7", "--metric", "m", "--point", "6",
             "--lo", "2", "--hi", "10", "--rationale", "cli smoke test")
    _run_cli("--path", str(path), "evaluate", "--prediction-id", "R7-cli", "--actual", "7")
    before = path.read_bytes()
    r = _run_cli("--path", str(path), "evaluate", "--prediction-id", "R7-cli", "--actual", "8")
    assert r.returncode == 2
    assert "already been evaluated" in r.stderr
    assert path.read_bytes() == before
