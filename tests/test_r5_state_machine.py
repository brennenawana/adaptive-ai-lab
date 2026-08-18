"""R5 selection / freeze / TEST-unlock state machine — the invariants, against a TEMPORARY
registry root. Nothing here touches `learning/registry/r5`, the database, or any TEST row.

Invariants (contract § 12–14; adversarial finding 2026-08-18):

  1. at most one DEV-selected/frozen policy may exist per local model;
  2. a TEST unlock binds to exactly the policy the selection record froze;
  3. a second policy for the same model fails closed before freeze and before unlock;
  4. fake / incomplete lineage is not eligible for freeze or unlock;
  5. the exactly-once TEST state is monotonic and has no reset path through the
     experiment commands.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.routing.features import FEATURE_ORDER, FEATURE_SCHEMA_VERSION  # noqa: E402
from fis_platform.routing.learn import (  # noqa: E402
    LogisticRegression, RouterModel, Standardizer, canonical_json, digest,
)
from scripts import r5_replay  # noqa: E402
from scripts.r5_replay import (  # noqa: E402
    DEFAULT_RUNS, TRAIN_RUNS, Registry, begin_test_unlock, freeze_selection, verify_artifact,
)

TRAIN_DIGEST = "d" * 64


def _artifact(policy_id: str, model: str = "qwen", *, candidate: str = "lr_full",
              protocol: str = "grouped", eligible: bool = True, train_run: str | None = None,
              train_digest: str = TRAIN_DIGEST, source: str = "features") -> dict:
    names = list(FEATURE_ORDER[:6])
    X = [[float(i), float(i % 2), 1.0, 2.0, 3.0, 4.0] for i in range(12)]
    y = [i % 2 for i in range(12)]
    st = Standardizer().fit(X)
    lr = LogisticRegression(l2=1.0).fit(st.transform(X), y)
    router = RouterModel(family="logistic", feature_names=names, standardizer=st, model=lr)
    art = {
        "policy_id": policy_id, "candidate": candidate, "protocol": protocol, "family": "logistic",
        "eligible_kind": True, "eligible": eligible,
        "local_model": "qwen3-8b" if model == "qwen" else "nemotron-3.5-lightning",
        "feature_schema_version": FEATURE_SCHEMA_VERSION, "feature_source": source,
        "feature_names": names, "hyperparameter": 1.0, "threshold": 0.6,
        "threshold_grid": [0.6], "router": router.to_dict(),
        "train_run_id": train_run if train_run is not None else TRAIN_RUNS[model],
        "train_dataset_digest": train_digest, "cv": {"at_threshold": {}},
        "dev_selection": None,
    }
    art["artifact_digest"] = digest({k: v for k, v in art.items() if k not in r5_replay._MUTABLE_FIELDS})
    return art


def _result(policy_id: str, protocol: str = "grouped") -> dict:
    return {"policy_id": policy_id, "protocol": protocol,
            "system": {"escalated": 20, "cost_per_success": 0.05, "wall_p50_ms": 1000, "routing_fn": 5,
                       "utilization": 0.4, "unnecessary": 1, "all_pass": 40}}


def _verdict(policy_id: str, ok: bool, protocol: str = "grouped") -> dict:
    return {"policy_id": policy_id, "protocol": protocol, "eligible": True, "pass": ok,
            "K": 4, "delta_util": 0.2, "e_max": 6, "R1_fn_reduction": ok, "R2_no_collapse": ok,
            "R2_under_skeleton_caps": ok, "R3_quality": ok}


@pytest.fixture
def reg(tmp_path: Path) -> Registry:
    r = Registry(tmp_path / "registry")
    r.candidates.mkdir(parents=True)
    return r


def _freeze(reg: Registry, winner: dict | None, arts=None, model="qwen"):
    arts = arts if arts is not None else ([winner] if winner else [])
    results = [_result(a["policy_id"], a["protocol"]) for a in arts]
    verdicts = [_verdict(a["policy_id"], winner is not None and a["policy_id"] == winner["policy_id"],
                         a["protocol"]) for a in arts]
    dev_local, dev_strong = DEFAULT_RUNS["dev"][model]
    return freeze_selection(reg, model, arts, results, verdicts, winner,
                            "grouped" if winner else None, dev_local, dev_strong)


DS_META = {"dataset_digest": TRAIN_DIGEST}


def _unlock(reg: Registry, policy_id: str, model: str = "qwen", runs=None, meta=DS_META):
    local, strong = runs or DEFAULT_RUNS["test"][model]
    return begin_test_unlock(reg, policy_id, model, local, strong, dataset_meta=meta)


# ------------------------------------------------------------------ 1. one frozen policy per model

def test_registry_root_is_the_temporary_one_and_the_canonical_tree_is_never_named(reg, tmp_path):
    assert reg.root == tmp_path / "registry"
    assert "learning/registry/r5" not in str(reg.unlock_file)


def test_freeze_writes_one_selection_record_and_only_the_winner_artifact(reg):
    win = _artifact("r5-qwen-lr_full-v1")
    lose = _artifact("r5-qwen-lr_core-v1", candidate="lr_core")
    rec = _freeze(reg, win, [win, lose])
    assert rec["winner"] == "r5-qwen-lr_full-v1"
    assert reg.selection_file("qwen").exists()
    assert reg.frozen_artifact("r5-qwen-lr_full-v1").exists()
    assert not reg.frozen_artifact("r5-qwen-lr_core-v1").exists()       # losers are never frozen
    frozen = json.loads(reg.frozen_artifact("r5-qwen-lr_full-v1").read_text())
    assert frozen["dev_selection"]["result"] == "PASS"
    verify_artifact(frozen)                                              # digest survives the freeze fields
    assert sorted(p.name for p in reg.frozen.glob("r5-qwen-*.json")) == ["r5-qwen-lr_full-v1.json"]


def test_a_second_selection_for_the_same_model_fails_closed(reg):
    _freeze(reg, _artifact("r5-qwen-lr_full-v1"))
    with pytest.raises(SystemExit, match="already happened"):
        _freeze(reg, _artifact("r5-qwen-lr_core-v1", candidate="lr_core"))
    # and a null selection cannot be "upgraded" later either
    reg2 = Registry(reg.root.parent / "reg2"); reg2.candidates.mkdir(parents=True)
    _freeze(reg2, None, [_artifact("r5-qwen-lr_full-v1")])
    assert json.loads(reg2.selection_file("qwen").read_text())["winner"] is None
    with pytest.raises(SystemExit, match="already happened"):
        _freeze(reg2, _artifact("r5-qwen-lr_full-v1"))


def test_a_stray_frozen_artifact_for_the_model_blocks_selection(reg):
    reg.frozen.mkdir(parents=True)
    reg.frozen_artifact("r5-qwen-tree-v1").write_text("{}")
    with pytest.raises(SystemExit, match="frozen artifacts already exist"):
        _freeze(reg, _artifact("r5-qwen-lr_full-v1"))


def test_models_are_independent(reg):
    _freeze(reg, _artifact("r5-qwen-lr_full-v1"))
    _freeze(reg, _artifact("r5-nemotron-lr_full-v1", model="nemotron"), model="nemotron")
    assert reg.selection_file("qwen").exists() and reg.selection_file("nemotron").exists()


# ------------------------------------------------------------------ 2/3. unlock binds to the recorded winner

def test_unlock_binds_to_the_recorded_winner_only(reg):
    win = _artifact("r5-qwen-lr_full-v1")
    _freeze(reg, win, [win, _artifact("r5-qwen-lr_core-v1", candidate="lr_core")])
    # a losing candidate, even hand-frozen with a PASS stamp and a valid digest, is refused
    forged = dict(_artifact("r5-qwen-lr_core-v1", candidate="lr_core"))
    forged["local_model_short"] = "qwen"
    forged["dev_selection"] = {"result": "PASS", "dev_local_run": "V3-qwen-dev", "dev_strong_run": "E4-v3-dev"}
    reg.frozen_artifact("r5-qwen-lr_core-v1").write_text(canonical_json(forged) + "\n")
    verify_artifact(forged)                                              # it IS a valid artifact…
    with pytest.raises(SystemExit, match="names 'r5-qwen-lr_full-v1' as its winner"):
        _unlock(reg, "r5-qwen-lr_core-v1")                               # …but not the selected one
    art = _unlock(reg, "r5-qwen-lr_full-v1")
    assert art["policy_id"] == "r5-qwen-lr_full-v1"


def test_unlock_without_a_selection_record_is_refused_even_with_a_perfect_frozen_file(reg):
    art = _artifact("r5-qwen-lr_full-v1")
    art["local_model_short"] = "qwen"
    art["dev_selection"] = {"result": "PASS", "dev_local_run": "V3-qwen-dev", "dev_strong_run": "E4-v3-dev"}
    reg.frozen.mkdir(parents=True)
    reg.frozen_artifact(art["policy_id"]).write_text(canonical_json(art) + "\n")
    with pytest.raises(SystemExit, match="no DEV selection record"):
        _unlock(reg, "r5-qwen-lr_full-v1")


def test_unlock_refuses_a_frozen_file_whose_digest_moved_after_selection(reg):
    win = _artifact("r5-qwen-lr_full-v1")
    _freeze(reg, win)
    frozen = json.loads(reg.frozen_artifact(win["policy_id"]).read_text())
    frozen["threshold"] = 0.3                                            # tamper…
    frozen["artifact_digest"] = digest({k: v for k, v in frozen.items() if k not in r5_replay._MUTABLE_FIELDS})
    reg.frozen_artifact(win["policy_id"]).write_text(canonical_json(frozen) + "\n")   # …with a self-consistent digest
    with pytest.raises(SystemExit, match="!= the digest the selection record froze"):
        _unlock(reg, win["policy_id"])


def test_unlock_refuses_a_tampered_frozen_file_whose_digest_no_longer_verifies(reg):
    win = _artifact("r5-qwen-lr_full-v1")
    _freeze(reg, win)
    frozen = json.loads(reg.frozen_artifact(win["policy_id"]).read_text())
    frozen["threshold"] = 0.3
    reg.frozen_artifact(win["policy_id"]).write_text(canonical_json(frozen) + "\n")
    with pytest.raises(SystemExit, match="digest mismatch"):
        _unlock(reg, win["policy_id"])


def test_unlock_refuses_the_wrong_model_and_the_wrong_test_runs(reg):
    win = _artifact("r5-qwen-lr_full-v1")
    _freeze(reg, win)
    with pytest.raises(SystemExit, match="no DEV selection record for nemotron"):
        _unlock(reg, win["policy_id"], model="nemotron")
    with pytest.raises(SystemExit, match="not the contract's"):
        _unlock(reg, win["policy_id"], runs=("V3-qwen-dev", "E4-v3-dev"))     # DEV runs offered as TEST


# ------------------------------------------------------------------ 4. lineage

def test_freeze_refuses_an_ineligible_or_off_source_winner(reg):
    bad = _artifact("r5-qwen-prior_category-v1", candidate="prior_category", eligible=True, source="prior")
    with pytest.raises(SystemExit, match="claims eligibility"):
        _freeze(reg, bad)


def test_unlock_refuses_wrong_train_run_and_wrong_dataset_digest(reg):
    off_run = _artifact("r5-qwen-lr_full-v1", train_run="R5-qwen-train-OTHER")
    _freeze(reg, off_run)
    with pytest.raises(SystemExit, match="lineage: trained on"):
        _unlock(reg, off_run["policy_id"])

    reg2 = Registry(reg.root.parent / "reg2"); reg2.candidates.mkdir(parents=True)
    win = _artifact("r5-qwen-lr_full-v1")
    _freeze(reg2, win)
    with pytest.raises(SystemExit, match="lineage: artifact trained on dataset"):
        _unlock(reg2, win["policy_id"], meta={"dataset_digest": "e" * 64})


def test_unlock_refuses_when_no_committed_dataset_meta_exists(reg, monkeypatch):
    win = _artifact("r5-qwen-lr_full-v1")
    _freeze(reg, win)
    monkeypatch.setattr(Registry, "dataset_meta", lambda self, model: reg.root / "missing.meta.json")
    with pytest.raises(SystemExit, match="no committed TRAIN dataset meta"):
        begin_test_unlock(reg, win["policy_id"], "qwen", *DEFAULT_RUNS["test"]["qwen"])


def test_unlock_refuses_a_winner_selected_on_non_contract_dev_runs(reg):
    win = _artifact("r5-qwen-lr_full-v1")
    results = [_result(win["policy_id"])]
    verdicts = [_verdict(win["policy_id"], True)]
    freeze_selection(reg, "qwen", [win], results, verdicts, win, "grouped", "V3-qwen2-dev", "E4-v3-dev")
    with pytest.raises(SystemExit, match="not the contract's DEV runs"):
        _unlock(reg, win["policy_id"])


# ------------------------------------------------------------------ 5. exactly once, monotonic

def test_test_unlock_is_exactly_once_per_policy_and_per_model(reg):
    win = _artifact("r5-qwen-lr_full-v1")
    _freeze(reg, win)
    _unlock(reg, win["policy_id"])
    with pytest.raises(SystemExit, match="already had its one TEST replay"):
        _unlock(reg, win["policy_id"])
    # even if someone forged a second selection record naming another policy, the
    # per-model unlock is spent
    sel = json.loads(reg.selection_file("qwen").read_text())
    other = _artifact("r5-qwen-lr_core-v1", candidate="lr_core")
    other["local_model_short"] = "qwen"
    other["dev_selection"] = {"result": "PASS", "dev_local_run": "V3-qwen-dev", "dev_strong_run": "E4-v3-dev"}
    reg.frozen_artifact(other["policy_id"]).write_text(canonical_json(other) + "\n")
    sel["winner"], sel["winner_artifact_digest"] = other["policy_id"], other["artifact_digest"]
    reg.selection_file("qwen").write_text(json.dumps(sel))
    with pytest.raises(SystemExit, match="qwen has already had its one TEST replay"):
        _unlock(reg, other["policy_id"])


def test_unlock_record_is_append_only_and_binds_the_selection_record_digest(reg):
    win = _artifact("r5-qwen-lr_full-v1")
    _freeze(reg, win)
    _unlock(reg, win["policy_id"])
    rec = json.loads(reg.unlock_file.read_text())["unlocks"]
    assert len(rec) == 1
    assert rec[0]["artifact_digest"] == win["artifact_digest"]
    assert rec[0]["selection_record_digest"] == digest(json.loads(reg.selection_file("qwen").read_text()))
    assert rec[0]["model"] == "qwen"


def test_the_module_has_no_function_that_removes_or_rewrites_an_unlock():
    """The only writers of test_unlock.json append; there is no withdraw/reset path a
    normal experiment command could reach. (A build failure after the unlock leaves the
    unlock consumed — by design; a human decides.)"""
    src = Path(r5_replay.__file__).read_text()
    assert src.count("unlock_file.write_text") == 1, "exactly one writer of the unlock record"
    for word in ("withdraw", "rollback", "reset_unlock", "remove_unlock", "unlocks\"] = ["):
        assert word not in src, word
    assert not any(n.startswith(("withdraw", "reset", "clear")) for n in dir(r5_replay))
