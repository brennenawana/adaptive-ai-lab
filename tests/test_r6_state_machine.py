"""R6 candidate state machine — the invariants, against a TEMPORARY registry root.

Nothing here touches `learning/registry/r6`, the database, or any model server. Every
test builds its own registry under `tmp_path` and its own 20-byte "artifact".

The R5 lesson generalised (contract § 12–14, adversarial finding 2026-08-18): a
protocol that depends on a human remembering the order of operations is a protocol that
has already been broken once. So the invariants are mechanical:

  1. only the edges in `TRANSITIONS` exist; DEV_REJECTED / TEST_EVALUATED / WITHDRAWN are
     terminal, and WITHDRAWN is reachable ONLY before any DEV look;
  2. what was frozen stays frozen — the execution system, the contract revision and the
     gates are quoted back at every later edge and must match;
  3. at most one quant per FAMILY may spend a DEV evaluation, and one a TEST look;
  4. DEV and TEST results are written exactly once, and the log that records them is
     append-only and hash-chained, so an edit is detected on the next read;
  5. `require_state` refuses before any model is loaded, and writes nothing;
  6. no command relocates the root, and no function removes state.

Every transition here passes `require_clean_tree=False`: these tests run inside the
repo, which is dirty during development. The clean-tree guard itself is tested with a
monkeypatched `git_head`.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform import provenance
from fis_platform.provenance import (
    CONTRACT_FROZEN,
    DEV_EVALUATED,
    DEV_QUALIFIED,
    DEV_REJECTED,
    REGISTERED,
    SMOKE,
    SMOKE_CASES_PER_CLASS,
    SMOKE_TOTAL_CASES,
    SMOKE_VIOLATION_RULE,
    SMOKE_VIOLATION_RULE_DIGEST,
    TERMINAL_STATES,
    TEST_EVALUATED,
    TEST_UNLOCKED,
    TRAIN_COMPATIBLE,
    TRANSITIONS,
    WITHDRAWN,
    ExecutionSystem,
    IllegalTransition,
    ModelArtifact,
    R6Registry,
    RegistryIntegrityError,
    RuntimeIdentity,
    ServerArgs,
    TransitionRefused,
    begin_run,
    default_root,
    end_run,
    require_state,
    smoke_case_flags,
    smoke_case_selection,
    write_smoke_result,
)
from fis_platform.routing.learn import digest
from fis_platform.suite import SUITE_VERSION
from scripts import r6_registry

CONTRACT_REV = "a" * 40
CONTRACT_COMMIT = "37742a7"
GATES = "g" * 64
DEV_RESULT = {"run": "dev", "n": 48, "all_pass": 30}
TEST_RESULT = {"run": "test", "n": 96, "all_pass": 60}
ORDER = [TRAIN_COMPATIBLE, CONTRACT_FROZEN, DEV_EVALUATED, DEV_QUALIFIED, TEST_UNLOCKED,
         TEST_EVALUATED]


@pytest.fixture
def reg(tmp_path: Path) -> R6Registry:
    return R6Registry(tmp_path / "registry", git_checks=False)


def _artifact(tmp_path: Path, slug: str, *, family: str = "qwen35.9b",
              role: str = "modern_small", **over: Any) -> ModelArtifact:
    blob = f"weights-of-{slug}".encode()
    path = tmp_path / f"{slug}.gguf"
    path.write_bytes(blob)
    fields: dict[str, Any] = {
        "slug": slug, "role": role, "family": family,
        "base_model_repo": f"base/{family}",
        "quantizer_or_derivative_repo": "unsloth/Qwen3.5-9B-GGUF",
        "source_revision": "99a1b218", "source_url": f"https://example/{slug}.gguf",
        "filename": path.name, "quantization": "Q4_K_M",
        "quantization_measured": {"Q4_K": 64}, "size_bytes": len(blob),
        "sha256": hashlib.sha256(blob).hexdigest(), "gguf_metadata_digest": "b" * 64,
        "gguf_summary": {"n_tensors": 2}, "license": "apache-2.0", "license_source": "gguf",
        "architecture": "qwen35", "base_model_lineage": "Qwen3.5-9B",
        "local_path": str(path),
    }
    fields.update(over)
    return ModelArtifact(**fields)


def _runtime(tag: str = "c") -> RuntimeIdentity:
    # registered_at pinned: two fixture runtimes built in different wall-clock seconds
    # would otherwise digest differently and put_runtime would (correctly) refuse the second.
    return RuntimeIdentity(engine="llama.cpp-upstream",
                           git_rev="9b05354ec6fb58b4e665e9a39ebc40285c015638",
                           binaries={"llama-server": tag * 64}, build_info_expected="b1-9b05354",
                           registered_at="2026-08-18T00:00:00+00:00")


def _register_only(reg: R6Registry, tmp_path: Path, slug: str = "qwen35-9b-q4km", *,
                   family: str = "qwen35.9b", role: str = "modern_small",
                   runtime: RuntimeIdentity | None = None) -> str:
    """`register_candidate` and nothing else — the candidate is left at SMOKE, its
    real initial state (playbook §3). Most tests want a candidate already promoted
    to REGISTERED; use `_candidate` for that. SMOKE-specific tests use this."""
    artifact = _artifact(tmp_path, slug, family=family, role=role)
    runtime = runtime or _runtime()
    reg.put_artifact(artifact)
    reg.put_runtime(runtime)
    return reg.register_candidate(slug, artifact, runtime, family, role)


def _run_id(candidate_id: str, split: str) -> str:
    return f"R6-{candidate_id.split('@')[0]}-{split}"


def _smoke_run_id(candidate_id: str) -> str:
    return f"R6-{candidate_id.split('@')[0]}-train-smoke"


def _smoke_case_ids() -> list[str]:
    """36 canonical SMOKE case ids (12 classes x `SMOKE_CASES_PER_CLASS`), in
    round-robin order — fixture-only, the same shape `smoke_case_selection` would
    carve out of a live TRAIN corpus, without needing one here."""
    ids = [f"S{c:02d}-{1000000 + s:07d}" for c in range(1, 13) for s in range(SMOKE_CASES_PER_CLASS)]
    return smoke_case_selection(ids)


def _smoke_cases(canonical: list[str], violations: int) -> list[dict[str, Any]]:
    """One evidence dict per canonical id, in order. The first `violations` cases carry
    a non-success tool status (so each mechanically derives exactly one violation flag);
    the rest are clean — a real, self-consistent SMOKE result, never a hand-typed count."""
    cases = []
    for i, sid in enumerate(canonical):
        bad = i < violations
        case = {
            "scenario_id": sid, "trace_id": f"trace-{i:04d}",
            "tool_call_statuses": ["denied"] if bad else ["success"],
            "n_model_invocations": 1, "all_pass": not bad,
        }
        case["violations"] = smoke_case_flags(case)
        cases.append(case)
    return cases


def _smoke_result_record(cid: str, run_id: str, canonical: list[str],
                         cases: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(len(c["violations"]) for c in cases)
    return {
        "candidate_id": cid, "smoke_run_id": run_id, "split": "train",
        "suite_version": SUITE_VERSION, "corpus_digest": "c" * 64, "ordering": "round_robin",
        "violation_rule_version": SMOKE_VIOLATION_RULE["version"],
        "violation_rule_digest": SMOKE_VIOLATION_RULE_DIGEST,
        "case_ids": canonical, "smoke_case_digest": digest(canonical),
        "cases": cases, "total_violations": total, "eligible": total == 0,
    }


def _pass_smoke(reg: R6Registry, cid: str, *, run_id: str | None = None,
                violations: int = 0, **over: Any) -> dict[str, Any]:
    """Run and pass the fixed 36-case SMOKE population through the real evidence path
    (`write_smoke_result` + `begin_run`/`end_run`), then transition SMOKE -> REGISTERED.
    `violations` builds that many genuinely-violating cases into the PERSISTED result
    (so a real mechanical derivation backs the payload, not a hand-typed int); `over`
    perturbs the TRANSITION payload only (e.g. a mismatched smoke_case_digest, a bad
    ordering label) without touching the underlying evidence."""
    run_id = run_id or _smoke_run_id(cid)
    canonical = _smoke_case_ids()
    case_digest = digest(canonical)
    cases = _smoke_cases(canonical, violations)
    record = _smoke_result_record(cid, run_id, canonical, cases)
    result_digest = write_smoke_result(reg, cid, run_id, record)
    begin_run(reg, cid, "train", run_id, SMOKE_TOTAL_CASES, kind="smoke",
             extra={"smoke_case_digest": case_digest})
    end_run(reg, cid, run_id, cases_done=SMOKE_TOTAL_CASES, wall_s=1.0,
           extra={"smoke_result_digest": result_digest, "smoke_case_digest": case_digest})
    payload = {"smoke_run_id": run_id, "smoke_cases": SMOKE_TOTAL_CASES,
              "smoke_violations": violations, "smoke_case_digest": case_digest,
              "ordering": "round_robin"}
    payload.update(over)
    return reg.transition(cid, REGISTERED, payload, require_clean_tree=False)


def _candidate(reg: R6Registry, tmp_path: Path, slug: str = "qwen35-9b-q4km", *,
               family: str = "qwen35.9b", role: str = "modern_small",
               runtime: RuntimeIdentity | None = None) -> str:
    """Registered AND promoted past a clean SMOKE pass to REGISTERED — the starting
    point every test written before SMOKE existed assumes."""
    cid = _register_only(reg, tmp_path, slug, family=family, role=role, runtime=runtime)
    _pass_smoke(reg, cid)
    return cid


def _contract_spec_path_and_digest(reg: R6Registry, cid: str) -> tuple[str, str]:
    """Write a minimal, valid INFERENTIAL `ContractSpec` (fis_platform.contract_spec)
    naming `cid`, under the SAME tmp tree the registry lives in, and return a path
    relative to `provenance._ROOT` (so it resolves without touching the real repo)
    plus the spec's own digest. Item G's CONTRACT_FROZEN payload guard needs both.

    INFERENTIAL, not SCREENING (Finding 3, playbook §7): the CONTRACT_FROZEN branch
    requires the validated spec's `experiment_type` to be INFERENTIAL — the state
    machine's CONTRACT_FROZEN -> DEV -> TEST path is the promotable inferential path,
    and a SCREENING/DIAGNOSTIC/MEASUREMENT spec must never freeze onto it. So every
    fixture that walks a candidate through CONTRACT_FROZEN (`_step`/`_walk`, and every
    test file that imports them) needs the full INFERENTIAL field set, not just the
    SCREENING minimum a pre-Finding-3 spec got away with.
    """
    from fis_platform.contract_spec import validate_contract_spec

    identity = reg.read_identity(cid)
    data: dict[str, Any] = {
        "spec_version": 1,
        "experiment_id": f"R6-{cid.split('@')[0]}",
        "experiment_type": "INFERENTIAL",
        "question": "does this candidate beat the incumbent on DEV/TEST",
        "suite_version": "v3",
        "corpus_digest": "c" * 64,
        "split_permissions": ["dev", "test"],
        "ordering_policy": "round_robin",
        "authoritative_clocks": {"wall": "server"},
        "state_machine": "R6",
        "artifact_lineage": [{"artifact_id": identity["artifact_id"],
                              "sha256": identity["artifact_sha256"]}],
        "candidates": [cid],
        "tolerances": [{"spec_id": "t1", "metric": "cap_hits", "description": "cap breach",
                        "denominator_n": 36, "max_violations": 3, "consequence": "ABORT"}],
        "execution_system_digests": {"local": "e" * 64},
        "expected_discordance_range": [0.05, 0.2],
        "clustering_unit": "scenario_class",
        "effective_n": 22.0,
        "mde_pp": 5.0,
        "primary_statistic": "cluster_robust_paired_t",
        "secondary_statistic": "mcnemar_exact",
        "allowed_verdicts": ["CONFIRMED", "REFUTED", "INCONCLUSIVE"],
        "prediction_ref": "R7-candidate-prediction",
        "curtailment_policy": {"enabled": False,
                               "disable_justification": "fixture — curtailment machinery not exercised here"},
        "test_look": {"planned": False},
    }
    spec = validate_contract_spec(data)
    abs_path = reg.root.parent / f"contract_spec_{cid.split('@')[0]}.json"
    abs_path.write_text(json.dumps(data))
    rel = os.path.relpath(abs_path, provenance._ROOT)
    return rel, spec.contract_spec_digest


def _contract_spec_path_and_digest_of_type(
    reg: R6Registry, cid: str, experiment_type: str) -> tuple[str, str]:
    """Like `_contract_spec_path_and_digest`, but for a non-INFERENTIAL
    `experiment_type` — used only to prove the CONTRACT_FROZEN guard refuses
    SCREENING/DIAGNOSTIC specs (Finding 3's negative tests). SCREENING and
    DIAGNOSTIC each need a slightly different minimal field set (SCREENING ranks,
    never infers — no `expected_discordance_range` etc.; DIAGNOSTIC needs almost
    nothing beyond the common core), so this only supports the two the tests use."""
    from fis_platform.contract_spec import validate_contract_spec

    identity = reg.read_identity(cid)
    data: dict[str, Any] = {
        "spec_version": 1,
        "experiment_id": f"R6-{cid.split('@')[0]}",
        "experiment_type": experiment_type,
        "question": "does this candidate rank favourably on TRAIN" if experiment_type == "SCREENING"
                    else "is this candidate's execution system stable",
        "suite_version": "v3",
        "corpus_digest": "c" * 64,
        "split_permissions": ["train"],
        "ordering_policy": "round_robin",
        "authoritative_clocks": {"wall": "server"},
        "state_machine": "R6",
        "artifact_lineage": [{"artifact_id": identity["artifact_id"],
                              "sha256": identity["artifact_sha256"]}],
    }
    if experiment_type == "SCREENING":
        data["candidates"] = [cid]
        data["tolerances"] = [{"spec_id": "t1", "metric": "cap_hits", "description": "cap breach",
                               "denominator_n": 36, "max_violations": 3, "consequence": "ABORT"}]
        data["allowed_verdicts"] = ["RANKED"]
    spec = validate_contract_spec(data)
    abs_path = reg.root.parent / f"contract_spec_{cid.split('@')[0]}_{experiment_type.lower()}.json"
    abs_path.write_text(json.dumps(data))
    rel = os.path.relpath(abs_path, provenance._ROOT)
    return rel, spec.contract_spec_digest


def _execution_system(reg: R6Registry, candidate_id: str, ctx: int = 16384) -> ExecutionSystem:
    identity = reg.read_identity(candidate_id)
    server = ServerArgs(argv=["/opt/bin/llama-server", "--port", "8090", "-c", str(ctx),
                              "-ngl", "99", "--flash-attn", "on", "--jinja"])
    return ExecutionSystem(
        artifact_id=identity["artifact_id"], artifact_sha256=identity["artifact_sha256"],
        gguf_metadata_digest=identity["gguf_metadata_digest"],
        runtime_id=identity["runtime_id"], runtime_digest=identity["runtime_digest"],
        server_args_digest=server.server_args_digest, server_args_material=server.material,
        genconfig_id="gc@0123456789ab", generation_config_digest="f" * 64, ctx=ctx)


def _payload(reg: R6Registry, cid: str, to: str) -> dict[str, Any]:
    system = _execution_system(reg, cid)
    if to == TRAIN_COMPATIBLE:
        return {"execution_system": system.model_dump(mode="json"),
                "train_run_ids": [_run_id(cid, "train")], "pilot_record_digest": "p" * 64,
                "calibration": {"k": 3}}
    if to == CONTRACT_FROZEN:
        spec_path, spec_digest = _contract_spec_path_and_digest(reg, cid)
        return {"contract_path": "docs/R6_EXPERIMENT_CONTRACT.md",
                "contract_revision": CONTRACT_REV, "contract_commit": CONTRACT_COMMIT,
                "gates_digest": GATES, "execution_system_digest": system.record_digest,
                "contract_spec_path": spec_path, "contract_spec_digest": spec_digest}
    if to == DEV_EVALUATED:
        return {"dev_run_id": _run_id(cid, "dev"), "dev_result": DEV_RESULT,
                "contract_revision": CONTRACT_REV,
                "execution_system_digest": system.record_digest}
    if to in (DEV_QUALIFIED, DEV_REJECTED):
        return {"gate_evaluation": {"qualified": to == DEV_QUALIFIED, "gates_digest": GATES},
                "gates_digest": GATES,
                "dev_result_digest": digest(DEV_RESULT), "contract_revision": CONTRACT_REV}
    if to == TEST_UNLOCKED:
        return {"test_run_id": _run_id(cid, "test"), "dev_result_digest": digest(DEV_RESULT),
                "contract_revision": CONTRACT_REV,
                "execution_system_digest": system.record_digest,
                "artifact_sha256_now": reg.read_identity(cid)["artifact_sha256"]}
    if to == TEST_EVALUATED:
        return {"test_run_id": _run_id(cid, "test"), "test_result": TEST_RESULT}
    return {"reason": "runtime-incompatible on TRAIN (loader refuses the quant)",
            "reason_category": "runtime_incompatibility"}


def _step(reg: R6Registry, cid: str, to: str, **over: Any) -> dict[str, Any]:
    payload = _payload(reg, cid, to)
    payload.update(over)
    return reg.transition(cid, to, payload, require_clean_tree=False)


def _finished_run(reg: R6Registry, cid: str, split: str, run_id: str, n: int,
                  extra: dict[str, Any] | None = None) -> None:
    """A run that started AND finished with every planned case — what DEV_EVALUATED /
    TEST_EVALUATED require to see in the ledger."""
    begin_run(reg, cid, split, run_id, n, extra)
    end_run(reg, cid, run_id, cases_done=n, wall_s=1.0)


def _walk(reg: R6Registry, cid: str, target: str) -> str:
    """Drive a candidate along the canonical path up to and including `target`."""
    for state in ORDER:
        if state == DEV_EVALUATED:
            _finished_run(reg, cid, "dev", _run_id(cid, "dev"), 48)
        if state == TEST_EVALUATED:
            _finished_run(reg, cid, "test", _run_id(cid, "test"), 96)
        _step(reg, cid, state)
        if state == target:
            return cid
    return cid


# ------------------------------------------------------------------ 0. the root

def test_registry_root_is_the_temporary_one_and_the_canonical_tree_is_never_named(reg, tmp_path):
    assert reg.root == tmp_path / "registry"
    for path in (reg.head_file, reg.ledger_file, reg.phases_file, reg.candidates_dir,
                 reg.models_dir, reg.state_file("x@0"), reg.dev_result_file("x@0")):
        assert "learning/registry/r6" not in str(path)
        assert str(tmp_path) in str(path)
    assert str(default_root()).endswith("learning/registry/r6")   # named in exactly one place


# ------------------------------------------------------------------ 1. the legal path

def test_the_happy_path_walks_registered_to_test_evaluated(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    assert reg.current_state(cid) == REGISTERED
    identity = reg.read_identity(cid)
    assert identity["candidate_id"] == cid and identity["family"] == "qwen35.9b"

    _walk(reg, cid, TEST_EVALUATED)
    assert reg.current_state(cid) == TEST_EVALUATED

    entries = reg.read_state(cid)
    states = [e["to"] for e in entries if e["kind"] == "transition"]
    assert states == [SMOKE, REGISTERED, *ORDER]
    assert [e["seq"] for e in entries] == list(range(1, len(entries) + 1))
    assert entries[0]["from"] is None and entries[0]["prev_entry_digest"] == ""
    assert [e["kind"] for e in entries].count("run") == 2

    # results are on disk once, and the log stores only their digests
    assert json.loads(reg.dev_result_file(cid).read_text()) == DEV_RESULT
    assert json.loads(reg.test_result_file(cid).read_text()) == TEST_RESULT
    dev_entry = next(e for e in entries if e["to"] == DEV_EVALUATED)
    assert dev_entry["payload"]["dev_result_digest"] == digest(DEV_RESULT)
    assert "dev_result" not in dev_entry["payload"]

    head = json.loads(reg.head_file.read_text())
    assert head[cid] == {"seq": len(entries), "entry_digest": entries[-1]["entry_digest"]}


def test_the_transition_table_is_the_shape_the_contract_describes():
    assert set(TERMINAL_STATES) == {DEV_REJECTED, TEST_EVALUATED, WITHDRAWN}
    assert [s for s, nxt in TRANSITIONS.items() if WITHDRAWN in nxt] == \
        [SMOKE, REGISTERED, TRAIN_COMPATIBLE]
    assert TRANSITIONS[SMOKE] == (REGISTERED, WITHDRAWN)
    assert TRANSITIONS[DEV_QUALIFIED] == (TEST_UNLOCKED,)
    assert TRANSITIONS[TEST_UNLOCKED] == (TEST_EVALUATED,)
    assert not any(SMOKE in nxt for s, nxt in TRANSITIONS.items() if s != SMOKE), \
        "no edge exists INTO SMOKE — it is only an initial state"


def test_a_historical_chain_that_begins_at_registered_still_reads_and_transitions(reg, tmp_path):
    """SMOKE is new; candidates registered before it existed have chains that begin
    directly at REGISTERED (no SMOKE entry at all). Chain checks are content-based
    (seq/prev-digest/entry-digest, HEAD.json), and `TRANSITIONS[REGISTERED]` is
    unchanged, so a synthetic old-style chain still `read_state()`s cleanly and can
    still transition legally from its current state — how it got to REGISTERED never
    matters to what it may do next."""
    cid = _register_only(reg, tmp_path)      # identity/artifact/runtime files exist
    entry = {"seq": 1, "kind": "transition", "prev_entry_digest": "", "from": None,
             "to": REGISTERED, "at": "2026-01-01T00:00:00+00:00", "code_commit": "abc1234",
             "tree_clean": True, "payload": {"note": "pre-SMOKE historical registration"}}
    entry["entry_digest"] = digest(entry)
    reg.state_file(cid).write_text(json.dumps(entry, sort_keys=True) + "\n")
    reg.head_file.write_text(json.dumps({cid: {"seq": 1, "entry_digest": entry["entry_digest"]}}))

    entries = reg.read_state(cid)
    assert len(entries) == 1
    assert entries[0]["to"] == REGISTERED and entries[0]["from"] is None
    assert reg.current_state(cid) == REGISTERED

    _step(reg, cid, TRAIN_COMPATIBLE)
    assert reg.current_state(cid) == TRAIN_COMPATIBLE


# ------------------------------------------------------------------ 2. illegal edges

@pytest.mark.parametrize("reach, target", [
    (REGISTERED, DEV_EVALUATED),
    (REGISTERED, CONTRACT_FROZEN),
    (REGISTERED, TEST_UNLOCKED),
    (TRAIN_COMPATIBLE, DEV_EVALUATED),
    (TRAIN_COMPATIBLE, TEST_UNLOCKED),
    (CONTRACT_FROZEN, DEV_QUALIFIED),
    (CONTRACT_FROZEN, TEST_UNLOCKED),
    (DEV_EVALUATED, TEST_UNLOCKED),
    (DEV_EVALUATED, WITHDRAWN),
    (DEV_QUALIFIED, WITHDRAWN),
    (DEV_QUALIFIED, DEV_EVALUATED),
    (DEV_REJECTED, TEST_UNLOCKED),
    (DEV_REJECTED, DEV_QUALIFIED),
    (TEST_UNLOCKED, DEV_EVALUATED),
    (TEST_UNLOCKED, TEST_UNLOCKED),
    (TEST_EVALUATED, TEST_UNLOCKED),
    (TEST_EVALUATED, DEV_EVALUATED),
    (TEST_EVALUATED, WITHDRAWN),
    (WITHDRAWN, TRAIN_COMPATIBLE),
    (WITHDRAWN, DEV_EVALUATED),
])
def test_only_the_table_s_edges_exist(reg, tmp_path, reach, target):
    cid = _candidate(reg, tmp_path)
    if reach == WITHDRAWN:
        _step(reg, cid, WITHDRAWN)
    elif reach == DEV_REJECTED:
        _walk(reg, cid, DEV_EVALUATED)
        _step(reg, cid, DEV_REJECTED)
    elif reach != REGISTERED:
        _walk(reg, cid, reach)
    assert reg.current_state(cid) == reach

    before = reg.state_file(cid).read_bytes()
    with pytest.raises(IllegalTransition, match="is not a legal transition"):
        _step(reg, cid, target)
    assert reg.state_file(cid).read_bytes() == before, "a refused edge must not touch the log"


def test_an_unknown_state_is_not_a_state(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    with pytest.raises(IllegalTransition, match="is not a state"):
        reg.transition(cid, "PROBABLY_FINE", {}, require_clean_tree=False)


# ------------------------------------------------------------------ 3. what was frozen stays frozen

def test_contract_freeze_refuses_an_execution_system_that_moved(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, TRAIN_COMPATIBLE)
    other = _execution_system(reg, cid, ctx=8192)      # a re-served model at another -c
    with pytest.raises(TransitionRefused, match="execution_system_digest"):
        _step(reg, cid, CONTRACT_FROZEN, execution_system_digest=other.record_digest)
    assert reg.current_state(cid) == TRAIN_COMPATIBLE


def test_train_compatible_refuses_an_execution_system_for_another_candidate(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    stranger = _execution_system(reg, cid).model_dump(mode="json")
    stranger["artifact_id"] = "someone-else@0123456789ab"
    stranger.pop("record_digest")
    with pytest.raises(TransitionRefused, match="execution system names artifact"):
        _step(reg, cid, TRAIN_COMPATIBLE, execution_system=stranger)


def test_train_compatible_refuses_a_tampered_execution_system(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    forged = _execution_system(reg, cid).model_dump(mode="json")
    forged["ctx"] = 4096                                # digest now describes the old ctx
    with pytest.raises(TransitionRefused, match="does not verify"):
        _step(reg, cid, TRAIN_COMPATIBLE, execution_system=forged)


def test_train_compatible_refuses_runs_that_are_not_train_runs(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="not TRAIN run ids"):
        _step(reg, cid, TRAIN_COMPATIBLE, train_run_ids=[_run_id(cid, "dev")])
    with pytest.raises(TransitionRefused, match="non-empty list"):
        _step(reg, cid, TRAIN_COMPATIBLE, train_run_ids=[])


def test_dev_and_test_refuse_a_contract_revision_that_moved(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, CONTRACT_FROZEN)
    _finished_run(reg, cid, "dev", _run_id(cid, "dev"), 48)
    with pytest.raises(TransitionRefused, match="contract_revision"):
        _step(reg, cid, DEV_EVALUATED, contract_revision="b" * 40)
    _step(reg, cid, DEV_EVALUATED)
    _step(reg, cid, DEV_QUALIFIED)
    with pytest.raises(TransitionRefused, match="contract_revision"):
        _step(reg, cid, TEST_UNLOCKED, contract_revision="b" * 40)
    assert reg.current_state(cid) == DEV_QUALIFIED


def test_contract_freeze_insists_on_a_content_revision_not_a_commit(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, TRAIN_COMPATIBLE)
    with pytest.raises(TransitionRefused, match="40-hex git blob sha"):
        _step(reg, cid, CONTRACT_FROZEN, contract_revision=CONTRACT_COMMIT)


# ------------------------------------- 3b. the prospective contract-spec freeze hook

def test_contract_freeze_requires_a_contract_spec(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, TRAIN_COMPATIBLE)
    payload = _payload(reg, cid, CONTRACT_FROZEN)
    del payload["contract_spec_path"]
    del payload["contract_spec_digest"]
    with pytest.raises(TransitionRefused, match="missing"):
        reg.transition(cid, CONTRACT_FROZEN, payload, require_clean_tree=False)
    assert reg.current_state(cid) == TRAIN_COMPATIBLE


def test_contract_freeze_refuses_a_spec_path_that_does_not_exist(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, TRAIN_COMPATIBLE)
    with pytest.raises(TransitionRefused, match="does not exist"):
        _step(reg, cid, CONTRACT_FROZEN, contract_spec_path="no-such-spec.json")


def test_contract_freeze_refuses_a_contract_spec_digest_mismatch(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, TRAIN_COMPATIBLE)
    with pytest.raises(TransitionRefused, match="contract_spec_digest"):
        _step(reg, cid, CONTRACT_FROZEN, contract_spec_digest="f" * 64)
    assert reg.current_state(cid) == TRAIN_COMPATIBLE


def test_contract_freeze_refuses_a_spec_that_does_not_validate(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, TRAIN_COMPATIBLE)
    bad_path = reg.root.parent / f"bad_spec_{cid.split('@')[0]}.json"
    bad_path.write_text(json.dumps({"spec_version": 1, "experiment_type": "SCREENING"}))
    rel = os.path.relpath(bad_path, provenance._ROOT)
    with pytest.raises(TransitionRefused, match="does not validate"):
        _step(reg, cid, CONTRACT_FROZEN, contract_spec_path=rel,
              contract_spec_digest="0" * 64)


def test_contract_freeze_refuses_a_spec_that_does_not_name_this_candidate(reg, tmp_path):
    from fis_platform.contract_spec import validate_contract_spec

    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, TRAIN_COMPATIBLE)
    identity = reg.read_identity(cid)
    data = {
        # INFERENTIAL (not SCREENING): the experiment_type guard (Finding 3) runs
        # BEFORE the candidate-membership check below, so this spec has to clear
        # experiment_type first in order to actually exercise "not listed".
        "spec_version": 1, "experiment_id": "R6-someone-else", "experiment_type": "INFERENTIAL",
        "question": "q", "suite_version": "v3", "corpus_digest": "c" * 64,
        "split_permissions": ["dev", "test"], "ordering_policy": "round_robin",
        "authoritative_clocks": {"wall": "server"}, "state_machine": "R6",
        "artifact_lineage": [{"artifact_id": identity["artifact_id"],
                              "sha256": identity["artifact_sha256"]}],
        "candidates": ["someone-else@000000000000"],
        "tolerances": [{"spec_id": "t1", "metric": "m", "description": "d",
                        "denominator_n": 36, "max_violations": 3, "consequence": "ABORT"}],
        "execution_system_digests": {"local": "e" * 64},
        "expected_discordance_range": [0.05, 0.2],
        "clustering_unit": "scenario_class",
        "effective_n": 22.0,
        "mde_pp": 5.0,
        "primary_statistic": "cluster_robust_paired_t",
        "secondary_statistic": "mcnemar_exact",
        "allowed_verdicts": ["CONFIRMED", "REFUTED", "INCONCLUSIVE"],
        "prediction_ref": "R7-someone-else-prediction",
        "curtailment_policy": {"enabled": False,
                               "disable_justification": "fixture — curtailment machinery not exercised here"},
        "test_look": {"planned": False},
    }
    spec = validate_contract_spec(data)
    abs_path = reg.root.parent / f"other_spec_{cid.split('@')[0]}.json"
    abs_path.write_text(json.dumps(data))
    rel = os.path.relpath(abs_path, provenance._ROOT)
    with pytest.raises(TransitionRefused, match="not listed"):
        _step(reg, cid, CONTRACT_FROZEN, contract_spec_path=rel,
              contract_spec_digest=spec.contract_spec_digest)


def test_contract_freeze_refuses_a_screening_spec(reg, tmp_path):
    """Finding 3 (playbook §7): the CONTRACT_FROZEN branch requires the validated
    spec's `experiment_type` to be INFERENTIAL. A SCREENING spec validates fine on
    its own terms (it ranks candidates on TRAIN, never claims an MDE or effective N)
    but must never freeze onto the promotable DEV -> TEST path — screening runs
    under its own TRAIN-only protocol."""
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, TRAIN_COMPATIBLE)
    spec_path, spec_digest = _contract_spec_path_and_digest_of_type(reg, cid, "SCREENING")
    with pytest.raises(TransitionRefused, match="INFERENTIAL"):
        _step(reg, cid, CONTRACT_FROZEN, contract_spec_path=spec_path,
              contract_spec_digest=spec_digest)
    assert reg.current_state(cid) == TRAIN_COMPATIBLE


def test_contract_freeze_refuses_a_diagnostic_spec(reg, tmp_path):
    """Same guard, DIAGNOSTIC: a stability-probe contract must never freeze onto the
    promotable path either — diagnostic work runs under its own `diagnostic` run
    kind and is explicitly forbidden from ever planning a TEST look."""
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, TRAIN_COMPATIBLE)
    spec_path, spec_digest = _contract_spec_path_and_digest_of_type(reg, cid, "DIAGNOSTIC")
    with pytest.raises(TransitionRefused, match="INFERENTIAL"):
        _step(reg, cid, CONTRACT_FROZEN, contract_spec_path=spec_path,
              contract_spec_digest=spec_digest)
    assert reg.current_state(cid) == TRAIN_COMPATIBLE


def test_a_historical_contract_frozen_entry_without_a_spec_still_reads_cleanly(reg, tmp_path):
    """Write-time only (item G): the freeze-hook guard runs inside `_validate_payload`,
    which `read_state()` never calls — a historical CONTRACT_FROZEN entry recorded
    before this guard existed (no contract_spec_path/contract_spec_digest at all)
    verifies exactly as cleanly as one recorded today."""
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, TRAIN_COMPATIBLE)
    entries = reg.read_state(cid)
    train_es_digest = entries[-1]["payload"]["execution_system_digest"]
    old_payload = {"contract_path": "docs/R6_EXPERIMENT_CONTRACT.md",
                   "contract_revision": CONTRACT_REV, "contract_commit": CONTRACT_COMMIT,
                   "gates_digest": GATES, "execution_system_digest": train_es_digest}
    entry = {"seq": len(entries) + 1, "kind": "transition",
             "prev_entry_digest": entries[-1]["entry_digest"], "from": TRAIN_COMPATIBLE,
             "to": CONTRACT_FROZEN, "at": "2026-01-01T00:00:00+00:00",
             "code_commit": "abc1234", "tree_clean": True, "payload": old_payload}
    entry["entry_digest"] = digest(entry)
    with reg.state_file(cid).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    head = json.loads(reg.head_file.read_text())
    head[cid] = {"seq": entry["seq"], "entry_digest": entry["entry_digest"]}
    reg.head_file.write_text(json.dumps(head))

    read_entries = reg.read_state(cid)
    assert read_entries[-1]["to"] == CONTRACT_FROZEN
    assert "contract_spec_path" not in read_entries[-1]["payload"]
    assert reg.current_state(cid) == CONTRACT_FROZEN


def test_the_unlock_refuses_an_artifact_whose_bytes_moved(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, DEV_QUALIFIED)
    with pytest.raises(TransitionRefused, match="the file moved under the experiment"):
        _step(reg, cid, TEST_UNLOCKED, artifact_sha256_now="9" * 64)
    assert reg.current_state(cid) == DEV_QUALIFIED


def test_test_evaluation_must_name_the_run_the_unlock_was_spent_on(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, TEST_UNLOCKED)
    with pytest.raises(TransitionRefused, match="test_run_id"):
        _step(reg, cid, TEST_EVALUATED, test_run_id="R6-something-else-test")


def test_a_rewritten_dev_result_is_caught_when_the_gates_are_applied(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, DEV_EVALUATED)
    reg.dev_result_file(cid).write_text(json.dumps({"run": "dev", "n": 48, "all_pass": 44}))
    with pytest.raises(RegistryIntegrityError, match="rewritten after it was recorded"):
        _step(reg, cid, DEV_QUALIFIED)


def test_the_gates_digest_must_be_the_frozen_one(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, DEV_EVALUATED)
    with pytest.raises(TransitionRefused, match="gates_digest"):
        _step(reg, cid, DEV_QUALIFIED, gates_digest="h" * 64)


def test_withdrawing_needs_a_reason(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="needs a reason"):
        _step(reg, cid, WITHDRAWN, reason="  ")
    _step(reg, cid, WITHDRAWN)
    assert reg.current_state(cid) == WITHDRAWN


# ------------------------------------- 3c. the structured elimination-rule guard

def test_withdrawing_requires_a_reason_category(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    payload = _payload(reg, cid, WITHDRAWN)
    del payload["reason_category"]
    with pytest.raises(TransitionRefused, match="missing"):
        reg.transition(cid, WITHDRAWN, payload, require_clean_tree=False)


def test_withdrawing_refuses_an_unknown_reason_category(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="reason_category"):
        _step(reg, cid, WITHDRAWN, reason_category="vibes")


@pytest.mark.parametrize("category", ["runtime_incompatibility", "infrastructure_failure"])
def test_withdrawing_on_a_non_comparative_category_needs_only_reason_and_category(
        reg, tmp_path, category):
    """Unchanged by Finding 4: these two non-comparative categories need no
    `authorized_by` — only `owner_decision` was strengthened (below)."""
    cid = _candidate(reg, tmp_path)
    _step(reg, cid, WITHDRAWN, reason=f"withdrawn for {category}", reason_category=category)
    assert reg.current_state(cid) == WITHDRAWN


def test_withdrawing_owner_decision_without_authorized_by_is_refused(reg, tmp_path):
    """Finding 4: `owner_decision` is a legitimate non-comparative category, but a
    bare reason string let a below-MDE selection loss hide under it uncontested.
    Strengthening, not a doctrine change: an owner decision must name the owner."""
    cid = _candidate(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="authorized_by"):
        _step(reg, cid, WITHDRAWN, reason="withdrawn for owner_decision",
              reason_category="owner_decision")
    assert reg.current_state(cid) == REGISTERED


def test_withdrawing_owner_decision_with_empty_authorized_by_is_refused(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="authorized_by"):
        _step(reg, cid, WITHDRAWN, reason="withdrawn for owner_decision",
              reason_category="owner_decision", authorized_by="   ")
    assert reg.current_state(cid) == REGISTERED


def test_withdrawing_owner_decision_with_authorized_by_is_accepted(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _step(reg, cid, WITHDRAWN, reason="withdrawn for owner_decision",
          reason_category="owner_decision", authorized_by="brennen")
    assert reg.current_state(cid) == WITHDRAWN


def test_pilot_selection_loss_requires_the_comparative_fields(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="missing"):
        _step(reg, cid, WITHDRAWN, reason="lost the pilot",
              reason_category="pilot_selection_loss")


def test_pilot_selection_loss_below_the_pilots_own_mde_is_refused(reg, tmp_path):
    """The corrected UD-Q3_K_XL precedent (playbook §4): withdrawn historically at a
    margin below the pilot's own MDE. That is now structurally refused."""
    cid = _candidate(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="below the pilot's own MDE"):
        _step(reg, cid, WITHDRAWN, reason="lost the pilot",
              reason_category="pilot_selection_loss", pilot_margin_cases=5, pilot_n=36,
              pilot_mde_cases=9, evidence_run_ids=[_run_id(cid, "train")])
    assert reg.current_state(cid) == REGISTERED


def test_pilot_selection_loss_at_or_above_the_mde_is_allowed(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _step(reg, cid, WITHDRAWN, reason="lost the pilot", reason_category="pilot_selection_loss",
         pilot_margin_cases=9, pilot_n=36, pilot_mde_cases=9,
         evidence_run_ids=[_run_id(cid, "train")])
    assert reg.current_state(cid) == WITHDRAWN


def test_pilot_selection_loss_evidence_citing_a_smoke_run_is_refused(reg, tmp_path):
    cid = _candidate(reg, tmp_path)          # its own SMOKE run is already ledgered
    smoke_id = _smoke_run_id(cid)
    with pytest.raises(TransitionRefused, match="SMOKE cannot justify elimination"):
        _step(reg, cid, WITHDRAWN, reason="lost the pilot", reason_category="pilot_selection_loss",
              pilot_margin_cases=20, pilot_n=36, pilot_mde_cases=9,
              evidence_run_ids=[smoke_id])
    assert reg.current_state(cid) == REGISTERED


@pytest.mark.parametrize("field, value", [
    ("pilot_margin_cases", -1), ("pilot_n", 0), ("pilot_mde_cases", 0),
])
def test_pilot_selection_loss_rejects_out_of_range_numbers(reg, tmp_path, field, value):
    cid = _candidate(reg, tmp_path)
    kwargs = {"pilot_margin_cases": 9, "pilot_n": 36, "pilot_mde_cases": 9,
             "evidence_run_ids": [_run_id(cid, "train")]}
    kwargs[field] = value
    with pytest.raises(TransitionRefused):
        _step(reg, cid, WITHDRAWN, reason="lost the pilot",
              reason_category="pilot_selection_loss", **kwargs)


def test_pilot_selection_loss_requires_non_empty_evidence_run_ids(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="evidence_run_ids"):
        _step(reg, cid, WITHDRAWN, reason="lost the pilot",
              reason_category="pilot_selection_loss", pilot_margin_cases=9, pilot_n=36,
              pilot_mde_cases=9, evidence_run_ids=[])


def test_a_historical_withdrawn_entry_with_reason_only_still_reads_cleanly(reg, tmp_path):
    """Write-time only (item E): the historical UD withdrawal is untouched evidence — a
    synthetic OLD-style WITHDRAWN entry (reason only, no reason_category) still
    `read_state()`s cleanly, because payload SHAPE is a write-time guard, never a
    read-time one."""
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, TRAIN_COMPATIBLE)
    entries = reg.read_state(cid)
    old_payload = {"reason": "runtime-incompatible on TRAIN (loader refuses the quant)"}
    entry = {"seq": len(entries) + 1, "kind": "transition",
             "prev_entry_digest": entries[-1]["entry_digest"], "from": TRAIN_COMPATIBLE,
             "to": WITHDRAWN, "at": "2026-01-01T00:00:00+00:00", "code_commit": "abc1234",
             "tree_clean": True, "payload": old_payload}
    entry["entry_digest"] = digest(entry)
    with reg.state_file(cid).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    head = json.loads(reg.head_file.read_text())
    head[cid] = {"seq": entry["seq"], "entry_digest": entry["entry_digest"]}
    reg.head_file.write_text(json.dumps(head))

    read_entries = reg.read_state(cid)
    assert read_entries[-1]["to"] == WITHDRAWN
    assert read_entries[-1]["payload"] == old_payload
    assert reg.current_state(cid) == WITHDRAWN


# ------------------------------------------------------------------ 4. one quant per family

def test_a_second_quant_of_the_same_family_cannot_spend_the_dev_evaluation(reg, tmp_path):
    first = _candidate(reg, tmp_path, "qwen35-9b-q4km")
    second = _candidate(reg, tmp_path, "qwen35-9b-q5km")            # same family, other quant
    _walk(reg, first, DEV_EVALUATED)
    _walk(reg, second, TRAIN_COMPATIBLE)
    # the guard now fires at the FREEZE (before any DEV inference), and again in require_state
    with pytest.raises(TransitionRefused, match=f"candidate '{first}' of family"):
        _step(reg, second, CONTRACT_FROZEN)
    assert reg.current_state(second) == TRAIN_COMPATIBLE
    with pytest.raises(TransitionRefused, match="of family"):
        require_state(reg, second, "dev", _run_id(second, "dev"))
    # a DIFFERENT family is unaffected
    third = _candidate(reg, tmp_path, "nemotron-30b-iq4xs", family="nemotron.30b")
    _walk(reg, third, DEV_EVALUATED)
    assert reg.current_state(third) == DEV_EVALUATED


def test_only_one_candidate_per_family_reaches_test(reg, tmp_path, monkeypatch):
    first = _candidate(reg, tmp_path, "qwen35-9b-q4km")
    second = _candidate(reg, tmp_path, "qwen35-9b-q5km")
    _walk(reg, first, TEST_UNLOCKED)
    # force `second` past the DEV family guard so the TEST guard is the one under test
    monkeypatch.setattr(R6Registry, "family_members",
                        lambda self, family, states, exclude: [])
    _walk(reg, second, DEV_QUALIFIED)
    monkeypatch.undo()
    with pytest.raises(TransitionRefused, match="one TEST look per family"):
        _step(reg, second, TEST_UNLOCKED)


def test_the_same_artifact_and_runtime_cannot_be_registered_twice(reg, tmp_path):
    artifact = _artifact(tmp_path, "qwen35-9b-q4km")
    runtime = _runtime()
    reg.put_artifact(artifact)
    reg.put_runtime(runtime)
    reg.register_candidate("qwen35-9b-q4km", artifact, runtime)
    with pytest.raises(TransitionRefused, match="already binds this artifact"):
        reg.register_candidate("qwen35-9b-again", artifact, runtime)


def test_registration_refuses_an_artifact_whose_bytes_do_not_match_the_record(reg, tmp_path):
    runtime = _runtime()
    reg.put_runtime(runtime)

    wrong_size = _artifact(tmp_path, "qwen35-9b-q4km", size_bytes=999)
    reg.put_artifact(wrong_size)
    with pytest.raises(TransitionRefused, match="bytes, the record says"):
        reg.register_candidate("qwen35-9b-q4km", wrong_size, runtime)

    wrong_sha = _artifact(tmp_path, "qwen35-9b-other", sha256="e" * 64)
    reg.put_artifact(wrong_sha)
    with pytest.raises(TransitionRefused, match="hashes to"):
        reg.register_candidate("qwen35-9b-other", wrong_sha, runtime)
    # …and the byte check can be skipped explicitly, which is the only way past it
    assert reg.register_candidate("qwen35-9b-other", wrong_sha, runtime, verify_bytes=False)


def test_an_unregistered_artifact_or_runtime_cannot_back_a_candidate(reg, tmp_path):
    artifact = _artifact(tmp_path, "qwen35-9b-q4km")
    runtime = _runtime()
    with pytest.raises(TransitionRefused, match="is not in the registry"):
        reg.register_candidate("qwen35-9b-q4km", artifact, runtime)
    reg.put_artifact(artifact)
    with pytest.raises(TransitionRefused, match="is not in the registry"):
        reg.register_candidate("qwen35-9b-q4km", artifact, runtime)


def test_a_record_cannot_be_overwritten_by_a_different_one(reg, tmp_path):
    artifact = _artifact(tmp_path, "qwen35-9b-q4km")
    reg.put_artifact(artifact)
    reg.put_artifact(artifact)                                   # idempotent
    moved = _artifact(tmp_path, "qwen35-9b-q4km", notes="re-labelled")
    with pytest.raises(RegistryIntegrityError, match="refusing to overwrite"):
        reg.put_artifact(moved)


# ------------------------------------------------------------------ 5. write-once results

def test_the_dev_result_is_written_exactly_once(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, CONTRACT_FROZEN)
    reg.dev_result_file(cid).parent.mkdir(parents=True, exist_ok=True)
    reg.dev_result_file(cid).write_text(json.dumps({"planted": True}))
    _finished_run(reg, cid, "dev", _run_id(cid, "dev"), 48)
    with pytest.raises(TransitionRefused, match="DEV is evaluated once"):
        _step(reg, cid, DEV_EVALUATED)
    assert json.loads(reg.dev_result_file(cid).read_text()) == {"planted": True}


def test_the_dev_transition_must_match_the_run_the_ledger_saw(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, CONTRACT_FROZEN)
    with pytest.raises(TransitionRefused, match="the run ledger records DEV runs"):
        _step(reg, cid, DEV_EVALUATED)                      # no ledger entry at all
    _finished_run(reg, cid, "dev", _run_id(cid, "dev"), 48)
    with pytest.raises(TransitionRefused, match="the run ledger records DEV runs"):
        _step(reg, cid, DEV_EVALUATED, dev_run_id="R6-other-dev")
    assert not reg.dev_result_file(cid).exists(), "a refused DEV must not leave a result"


# ------------------------------------------------------------------ 6. the chain

def _rewrite(path: Path, entries: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in entries))


def test_an_edited_entry_breaks_its_own_digest(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, CONTRACT_FROZEN)
    entries = reg.read_state(cid)
    entries[1]["payload"]["pilot_record_digest"] = "0" * 64
    _rewrite(reg.state_file(cid), entries)
    with pytest.raises(RegistryIntegrityError, match="the entry was edited"):
        reg.read_state(cid)


def test_an_edited_entry_with_a_recomputed_digest_breaks_the_chain(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, CONTRACT_FROZEN)
    entries = reg.read_state(cid)
    entries[1]["payload"]["pilot_record_digest"] = "0" * 64
    entries[1]["entry_digest"] = digest({k: v for k, v in entries[1].items()
                                         if k != "entry_digest"})
    _rewrite(reg.state_file(cid), entries)
    with pytest.raises(RegistryIntegrityError, match="the log was rewritten"):
        reg.read_state(cid)


def test_a_truncated_log_is_caught_by_head(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, CONTRACT_FROZEN)
    entries = reg.read_state(cid)
    _rewrite(reg.state_file(cid), entries[:-1])
    with pytest.raises(RegistryIntegrityError, match="truncated or replaced"):
        reg.read_state(cid)


def test_a_tampered_identity_is_caught(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    identity = json.loads(reg.identity_file(cid).read_text())
    identity["family"] = "some-other-family"
    reg.identity_file(cid).write_text(json.dumps(identity))
    with pytest.raises(RegistryIntegrityError, match="refusing to trust it"):
        reg.read_identity(cid)


# ------------------------------------------------------------------ 7. the clean-tree guard

def test_a_dirty_tree_refuses_the_edges_that_produce_evidence(reg, tmp_path, monkeypatch):
    cid = _candidate(reg, tmp_path)
    payload = _payload(reg, cid, TRAIN_COMPATIBLE)
    monkeypatch.setattr(provenance, "git_head", lambda: "37742a7-dirty")
    monkeypatch.setattr(provenance, "dirty_paths_outside_registry", lambda: ["evals/runner/run_eval.py"])
    with pytest.raises(TransitionRefused, match="not reproducible evidence"):
        reg.transition(cid, TRAIN_COMPATIBLE, payload)
    # a "-dirty" head whose only modified paths are the registry's own bookkeeping is the
    # normal state at the moment a transition is recorded (the ledger is tracked): allowed.
    monkeypatch.setattr(provenance, "dirty_paths_outside_registry", list)
    entry = reg.transition(cid, TRAIN_COMPATIBLE, payload)
    assert entry["tree_clean"] is True and entry["code_commit"] == "37742a7-dirty"
    monkeypatch.setattr(provenance, "git_head", lambda: "")
    with pytest.raises(TransitionRefused, match="git unavailable"):
        reg.transition(cid, CONTRACT_FROZEN, _payload(reg, cid, CONTRACT_FROZEN))

    monkeypatch.setattr(provenance, "git_head", lambda: "37742a7")
    entry = reg.transition(cid, CONTRACT_FROZEN, _payload(reg, cid, CONTRACT_FROZEN))   # default: clean required
    assert entry["tree_clean"] is True and entry["code_commit"] == "37742a7"


def test_allow_dirty_is_honoured_only_before_any_evidence_exists():
    assert r6_registry.require_clean_tree_for(TRAIN_COMPATIBLE, allow_dirty=True) is False
    assert r6_registry.require_clean_tree_for(WITHDRAWN, allow_dirty=True) is False
    assert r6_registry.require_clean_tree_for(TRAIN_COMPATIBLE, allow_dirty=False) is True
    for state in (CONTRACT_FROZEN, DEV_EVALUATED, DEV_QUALIFIED, TEST_UNLOCKED, TEST_EVALUATED):
        assert r6_registry.require_clean_tree_for(state, allow_dirty=False) is True
        with pytest.raises(TransitionRefused, match="only honoured for"):
            r6_registry.require_clean_tree_for(state, allow_dirty=True)


# ------------------------------------------------------------------ 8. require_state

def test_require_state_allows_train_from_registered_and_after_the_freeze(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    ctx = require_state(reg, cid, "train", _run_id(cid, "train"), False)
    assert ctx["state"] == REGISTERED and ctx["execution_system"] is None
    _walk(reg, cid, CONTRACT_FROZEN)
    ctx = require_state(reg, cid, "train", _run_id(cid, "train") + "-probe", False)
    assert ctx["state"] == CONTRACT_FROZEN
    assert ctx["execution_system"]["artifact_sha256"] == ctx["identity"]["artifact_sha256"]
    assert ctx["contract_revision"] == CONTRACT_REV and ctx["gates_digest"] == GATES


def test_require_state_refuses_dev_before_the_contract_is_frozen(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="DEV runs only against a frozen contract"):
        require_state(reg, cid, "dev", _run_id(cid, "dev"), False)
    _walk(reg, cid, TRAIN_COMPATIBLE)
    with pytest.raises(TransitionRefused, match="DEV runs only against a frozen contract"):
        require_state(reg, cid, "dev", _run_id(cid, "dev"), False)


def test_require_state_allows_dev_once_and_resumes_only_the_same_run(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, CONTRACT_FROZEN)
    run_id = _run_id(cid, "dev")
    assert require_state(reg, cid, "dev", run_id, False)["state"] == CONTRACT_FROZEN
    begin_run(reg, cid, "dev", run_id, 48)
    with pytest.raises(TransitionRefused, match="already run DEV"):
        require_state(reg, cid, "dev", run_id, False)
    assert require_state(reg, cid, "dev", run_id, True)["resume"] is True
    with pytest.raises(TransitionRefused, match="already run DEV"):
        require_state(reg, cid, "dev", run_id + "-2", True)


def test_require_state_seals_test_until_the_unlock(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, DEV_QUALIFIED)
    with pytest.raises(TransitionRefused, match="TEST is sealed until the unlock"):
        require_state(reg, cid, "test", _run_id(cid, "test"), False)
    _step(reg, cid, TEST_UNLOCKED)
    with pytest.raises(TransitionRefused, match="unlock was spent on"):
        require_state(reg, cid, "test", "R6-elsewhere-test", False)
    assert require_state(reg, cid, "test", _run_id(cid, "test"), False)["state"] == TEST_UNLOCKED


def test_require_state_refuses_run_ids_that_do_not_name_their_split(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    with pytest.raises(TransitionRefused, match="does not name its split"):
        require_state(reg, cid, "train", "R6-qwen35-9b-warmup", False)
    with pytest.raises(TransitionRefused, match="split must be one of"):
        require_state(reg, cid, "holdout", "R6-qwen35-9b-holdout", False)


def test_require_state_refuses_a_run_id_another_candidate_already_used(reg, tmp_path):
    first = _candidate(reg, tmp_path, "qwen35-9b-q4km")
    second = _candidate(reg, tmp_path, "nemotron-30b-iq4xs", family="nemotron.30b")
    begin_run(reg, first, "train", "R6-shared-train", 144)
    with pytest.raises(TransitionRefused, match="one run id, one candidate"):
        require_state(reg, second, "train", "R6-shared-train", False)


def test_require_state_writes_nothing(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, CONTRACT_FROZEN)
    before = {p: p.read_bytes() for p in sorted(reg.root.rglob("*")) if p.is_file()}
    require_state(reg, cid, "dev", _run_id(cid, "dev"), False)
    after = {p: p.read_bytes() for p in sorted(reg.root.rglob("*")) if p.is_file()}
    assert before == after


def test_the_ledger_records_a_start_and_an_end_line_per_run(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, CONTRACT_FROZEN)
    run_id = _run_id(cid, "dev")
    started = begin_run(reg, cid, "dev", run_id, 48, {"port": 8090})
    assert started["payload"]["port"] == 8090       # `extra` lands on the chained entry
    end_run(reg, cid, run_id, 48, 1234.5, {"errors": 0})
    lines = [ln for ln in reg.read_ledger(cid) if ln["run_id"] == run_id]
    assert [ln["event"] for ln in lines] == ["start", "end"]
    assert lines[0]["planned_cases"] == 48 and lines[0]["split"] == "dev"
    assert lines[1]["cases_done"] == 48 and lines[1]["wall_s"] == 1234.5
    assert lines[1]["errors"] == 0 and lines[1]["finished_at"] >= lines[0]["started_at"]
    assert reg.ledger_run_ids(cid, "dev") == [run_id]
    with pytest.raises(TransitionRefused, match="cannot end before it began"):
        end_run(reg, cid, "R6-never-started-dev", 1, 1.0)


def test_a_run_entry_does_not_move_the_state(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, CONTRACT_FROZEN)
    entry = begin_run(reg, cid, "dev", _run_id(cid, "dev"), 48)
    assert entry["kind"] == "run" and entry["from"] == entry["to"] == CONTRACT_FROZEN
    assert reg.current_state(cid) == CONTRACT_FROZEN
    reg.read_state(cid)                                    # the run entry is in the chain


# ------------------------------------------------------------------ 9. no way back

def test_no_command_can_relocate_the_root_or_erase_state():
    """The state is monotonic by construction, not by convention: there is no writer of
    state.jsonl or ledger.jsonl that truncates, and nothing reads a root from the
    environment. (A run that dies after an unlock leaves the unlock spent — by design;
    a human decides what to do about it.)"""
    for module in (provenance, r6_registry):
        src = Path(module.__file__).read_text()
        assert "REGISTRY_ROOT" not in src
        assert "os.environ" not in src and "getenv" not in src
        assert not any(name.startswith(("reset", "withdraw_test", "clear", "delete"))
                       for name in dir(module))
        for line in src.splitlines():
            if "state.jsonl" in line or "ledger.jsonl" in line:
                assert "write_text" not in line and '"w"' not in line, line
    src = Path(provenance.__file__).read_text()
    assert src.count('path.open("a", encoding="utf-8")') == 1, "one append-only writer"
    assert "_append_line(path" in src and "_append_line(registry.ledger_file" in src


# ------------------------------------------------------------------ 10. audit follow-ups (review A)

def test_a_deleted_candidate_cannot_be_recreated_or_ignored(reg, tmp_path):
    import shutil
    cid = _candidate(reg, tmp_path)
    shutil.rmtree(reg.candidate_dir(cid))
    with pytest.raises(RegistryIntegrityError, match="cannot vanish"):
        reg.candidate_ids()
    with pytest.raises((RegistryIntegrityError, TransitionRefused)):
        _candidate(reg, tmp_path)          # same slug/artifact/runtime -> same id -> refused


def test_dev_and_test_results_need_a_finished_full_run(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, CONTRACT_FROZEN)
    begin_run(reg, cid, "dev", _run_id(cid, "dev"), 48)               # started, never ended
    with pytest.raises(TransitionRefused, match="no ledger end line"):
        _step(reg, cid, DEV_EVALUATED)
    end_run(reg, cid, _run_id(cid, "dev"), cases_done=40, wall_s=1.0)   # ended short
    with pytest.raises(TransitionRefused, match="partial runs are not recorded"):
        _step(reg, cid, DEV_EVALUATED)
    assert reg.current_state(cid) == CONTRACT_FROZEN


def test_the_family_key_cannot_be_dodged_with_a_new_family_for_the_same_base_model(reg, tmp_path):
    _candidate(reg, tmp_path, "qwen35-9b-q4km", family="qwen35.9b")
    art = _artifact(tmp_path, "qwen35-9b-q5km", family="other.family",
                    base_model_repo="base/qwen35.9b")
    reg.put_artifact(art)
    with pytest.raises(TransitionRefused, match="shares base_model_repo"):
        reg.register_candidate("qwen35-9b-q5km", art, _runtime(), "other.family", "modern_small")


def test_freeze_requires_the_committed_contract_blob_when_git_checks_are_on(reg, tmp_path, monkeypatch):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, TRAIN_COMPATIBLE)
    reg.git_checks = True
    monkeypatch.setattr(provenance, "contract_blob_sha", lambda path: "c" * 40)
    with pytest.raises(TransitionRefused, match="not the blob committed at HEAD"):
        _step(reg, cid, CONTRACT_FROZEN)                       # payload carries CONTRACT_REV
    monkeypatch.setattr(provenance, "contract_blob_sha", lambda path: CONTRACT_REV)
    _step(reg, cid, CONTRACT_FROZEN)
    # after the freeze, DEV requires the committed contract to be the frozen blob (+ appends)
    monkeypatch.setattr(provenance, "registry_ahead_of_git_only_by_appends", list)
    monkeypatch.setattr(provenance, "committed_contract_extends", lambda blob, path=None: False)
    with pytest.raises(TransitionRefused, match="rules changed after the freeze"):
        require_state(reg, cid, "dev", _run_id(cid, "dev"))
    monkeypatch.setattr(provenance, "committed_contract_extends", lambda blob, path=None: True)
    require_state(reg, cid, "dev", _run_id(cid, "dev"))
    monkeypatch.setattr(provenance, "registry_ahead_of_git_only_by_appends", lambda: ["ledger.jsonl: truncated"])
    with pytest.raises(TransitionRefused, match="not append-only"):
        require_state(reg, cid, "dev", _run_id(cid, "dev"))


def test_capture_server_args_matches_exact_tokens_only(tmp_path):
    proc = tmp_path / "proc"
    for pid, argv in {"100": ["grep", "llama-server", "--port", "8085"],
                      "200": ["/x/llama-server", "-m", "m.gguf", "--port", "8085", "-c", "8192"],
                      "300": ["/x/llama-server", "--port", "80850"]}.items():
        (proc / pid).mkdir(parents=True)
        (proc / pid / "cmdline").write_bytes("\0".join(argv).encode() + b"\0")
    got = provenance.capture_server_args(8085, proc=proc)
    assert got is not None and got.material == ["-c", "8192"]
    assert provenance.capture_server_args(9999, proc=proc) is None
    assert provenance.llama_server_pids(proc) == ["200", "300"]
    (proc / "400").mkdir(); (proc / "400" / "cmdline").write_bytes(b"/y/llama-server\0--port\08085\0")
    with pytest.raises(TransitionRefused, match="claim --port 8085"):
        provenance.capture_server_args(8085, proc=proc)


def test_untracked_files_outside_the_registry_count_as_dirty(monkeypatch):
    monkeypatch.setattr(provenance, "git_head", lambda: "abc1234")
    monkeypatch.setattr(provenance.subprocess, "run",
                        lambda *a, **k: type("R", (), {"stdout": "?? evals/runner/dotenv.py\n M learning/registry/r6/ledger.jsonl\n"})())
    _commit, clean, dirty = provenance.tree_state()
    assert clean is False and dirty == ["evals/runner/dotenv.py"]


def test_a_resumed_full_run_counts_all_its_end_lines(reg, tmp_path):
    cid = _candidate(reg, tmp_path)
    _walk(reg, cid, CONTRACT_FROZEN)
    rid = _run_id(cid, "dev")
    begin_run(reg, cid, "dev", rid, 48)
    end_run(reg, cid, rid, cases_done=44, wall_s=1.0)          # interrupted
    end_run(reg, cid, rid, cases_done=4, wall_s=1.0)           # resumed, same run id
    _step(reg, cid, DEV_EVALUATED)                              # 44 + 4 == 48 -> accepted
    assert reg.current_state(cid) == DEV_EVALUATED


def test_the_dev_verdict_is_the_gate_functions_not_the_operators(reg, tmp_path):
    from fis_platform.r6_gates import GATES_DIGEST, evaluate_gates
    cid = _candidate(reg, tmp_path)                            # role modern_small
    _walk(reg, cid, TRAIN_COMPATIBLE)
    _step(reg, cid, CONTRACT_FROZEN, gates_digest=GATES_DIGEST)   # frozen under the REAL gates
    _finished_run(reg, cid, "dev", _run_id(cid, "dev"), 48)
    metrics = {"all_pass": 30, "no_output": 2, "p50_wall_ms": 20000}
    dev_result = {"metrics": metrics, "summary": {"n": 48}}
    _step(reg, cid, DEV_EVALUATED, dev_result=dev_result)
    ev = evaluate_gates("modern_small", metrics)
    assert ev["qualified"] is True
    forged = dict(ev, qualified=False)
    kw = {"gates_digest": GATES_DIGEST, "dev_result_digest": digest(dev_result)}
    with pytest.raises(TransitionRefused, match="does not support"):
        _step(reg, cid, DEV_QUALIFIED, gate_evaluation=forged, **kw)
    with pytest.raises(TransitionRefused, match="does not support"):
        _step(reg, cid, DEV_REJECTED, gate_evaluation=ev, **kw)
    wrong_digest = dict(ev, gates_digest="e" * 64)
    with pytest.raises(TransitionRefused, match="produced under gates"):
        _step(reg, cid, DEV_QUALIFIED, gate_evaluation=wrong_digest, **kw)
    # an operator claiming REJECTED against metrics that qualify is refused by re-derivation
    lying = dict(ev, qualified=False)
    with pytest.raises(TransitionRefused, match="re-applying the frozen gates"):
        _step(reg, cid, DEV_REJECTED, gate_evaluation=lying, **kw)
    _step(reg, cid, DEV_QUALIFIED, gate_evaluation=ev, **kw)
    assert reg.current_state(cid) == DEV_QUALIFIED and ev["gates_digest"] == GATES_DIGEST
