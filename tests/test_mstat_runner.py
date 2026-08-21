"""Eval runner integration — M-STAT unit S2 (`evals/runner/run_eval.py`).

No DB, no model inference: every test here drives the extracted, testable pieces
directly (argparse's own `required=True` enforcement runs the real production
parser — through `main()`, whose body raises `SystemExit` from `ap.parse_args()`
before anything reaches the database) — `apply_ordering`'s pure reordering,
`test_look_gate`'s ledger/mirror guards against tmp files, `check_corpus_pinned`'s
digest comparison, the tolerance metric extractors + halt shapes against a tmp
`RunEventLog`, and `curtail_and_exit`'s exact boundary + interval-only report.

  A. --split required                    -> argparse tests
  B. round-robin ordering                 -> apply_ordering / load_manifests tests
  C. machine TEST-look gate               -> test_look_gate tests
  D. pinned corpus identity               -> check_corpus_pinned tests
  E. consequence-bearing tolerances       -> TOLERANCE_METRICS / observe_tolerances /
                                             apply_tolerance_consequence /
                                             reconstruct_tolerance_trackers tests
  F. certainty curtailment                -> curtail_and_exit tests
  G. persist()'s own TEST-write choke     -> _require_test_look_planned_or_spent /
     point (Finding 2)                       persist() tests, no real DB
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evals.runner import run_eval  # noqa: E402
from fis_platform.ordering import round_robin  # noqa: E402
from fis_platform.suite import SUITE_VERSION, SuiteMismatch  # noqa: E402
from fis_platform.telemetry import RunEventLog  # noqa: E402
from fis_platform.test_looks import (  # noqa: E402
    LookRefused, MirrorDivergence, TestLookLedger, default_markdown_path,
)
from fis_platform.tolerances import (  # noqa: E402
    Consequence, CurtailmentPolicy, ToleranceSpec, ToleranceTracker,
)

REAL_REVIEW_REF = "docs/current/TEST_LOOK_LEDGER.md"   # a real, committed file — stands in
                                                        # for the Suite-v4 trigger review doc


# ============================================================== A. --split required

def _run_main_with_argv(monkeypatch: pytest.MonkeyPatch, argv: list[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["run_eval.py", *argv])
    asyncio.run(run_eval.main())


def test_split_missing_exits_with_no_args_at_all(monkeypatch):
    with pytest.raises(SystemExit):
        _run_main_with_argv(monkeypatch, [])


def test_split_missing_exits_even_with_every_other_required_arg_present(monkeypatch, capsys):
    """The real production parser (built inside `main()`), invoked with every OTHER
    required flag present — isolates that `--split` specifically has no default and
    is `required=True`, not merely one of several missing flags."""
    with pytest.raises(SystemExit):
        _run_main_with_argv(monkeypatch, ["--arm", "S2-test", "--model-ref", "local-specialist"])
    assert "--split" in capsys.readouterr().err


# ============================================================ B. round-robin ordering

def _rows(ids: list[str]) -> list[dict]:
    return [{"scenario_id": i} for i in ids]


def test_apply_ordering_yields_the_canonical_round_robin_order():
    ids = [f"S{c:02d}-{s:07d}" for c in range(1, 4) for s in range(1, 5)]   # 3 classes x 4, class-blocked
    ordered = run_eval.apply_ordering(_rows(ids), None)
    assert [r["scenario_id"] for r in ordered] == round_robin(ids)
    assert [r["scenario_id"] for r in ordered] != ids   # not the class-blocked input order


def test_apply_ordering_limit_is_a_class_balanced_prefix():
    ids = [f"S{c:02d}-{s:07d}" for c in range(1, 5) for s in range(1, 4)]   # 4 classes x 3
    prefix = run_eval.apply_ordering(_rows(ids), 4)
    assert len(prefix) == 4
    classes = [r["scenario_id"][:3] for r in prefix]
    assert len(set(classes)) == 4   # 4 distinct classes in a 4-case prefix, none repeated


def test_apply_ordering_none_limit_returns_everything():
    ids = [f"S01-{s:07d}" for s in range(1, 6)]
    assert len(run_eval.apply_ordering(_rows(ids), None)) == 5


def test_load_manifests_has_no_sql_limit_branch_and_no_limit_parameter():
    """The class-blocked decision-prefix path is structurally gone (playbook §4):
    not merely unused, but absent from the CODE (the docstring's own prose
    discussion of why is stripped out before the check, so this pins the SQL/
    control-flow body, not just word choice) — and the parameter that used to
    drive it is gone from the signature too."""
    source = inspect.getsource(run_eval.load_manifests)
    func = ast.parse(source).body[0]
    doc_node = func.body[0]   # the Expr(Constant(str)) docstring statement, by construction
    assert isinstance(doc_node, ast.Expr) and isinstance(doc_node.value.value, str)
    lines = source.splitlines(keepends=True)
    body_only = "".join(lines[:doc_node.lineno - 1] + lines[doc_node.end_lineno:])
    assert "LIMIT" not in body_only
    assert "limit" not in inspect.signature(run_eval.load_manifests).parameters


# ========================================================== C. machine TEST-look gate

def _seeded_ledger(tmp_path: Path) -> TestLookLedger:
    ledger = TestLookLedger(tmp_path / "test_looks.jsonl")
    ledger.seed()
    return ledger


def test_test_look_gate_signature_takes_no_provider_argument():
    """The frontier-bypass closure test: the gate cannot special-case a provider or
    --candidate because it structurally has no parameter for either."""
    params = list(inspect.signature(run_eval.test_look_gate).parameters)
    assert params == ["split", "run_id", "resume", "ledger_path", "mirror_path"]


def test_test_look_gate_returns_none_for_train_and_dev_without_touching_the_ledger(tmp_path):
    ledger_path = tmp_path / "test_looks.jsonl"
    for split in ("train", "dev"):
        assert run_eval.test_look_gate(split, "any-run-id", False, ledger_path=ledger_path) is None
    assert not ledger_path.exists()


def test_test_look_gate_passes_for_a_planned_test_run_id(tmp_path):
    ledger = _seeded_ledger(tmp_path)
    ledger.plan_look(look_no=8, suite_version=SUITE_VERSION, experiment="S2 unit test",
                     arm="x", run_id="S2-planned-test", authorized_by="brennen",
                     trigger_review_ref=REAL_REVIEW_REF)
    got = run_eval.test_look_gate("test", "S2-planned-test", False, ledger_path=ledger.path,
                                  mirror_path=default_markdown_path())
    assert isinstance(got, TestLookLedger)
    assert got.path == ledger.path


def test_test_look_gate_refuses_an_unplanned_run_id(tmp_path):
    ledger = _seeded_ledger(tmp_path)
    with pytest.raises(LookRefused, match="no planned TEST look"):
        run_eval.test_look_gate("test", "S2-never-planned-test", False, ledger_path=ledger.path,
                                mirror_path=default_markdown_path())


def test_test_look_gate_refuses_look_8_planned_with_no_review_ref(tmp_path):
    """`plan_look`'s own refusal, surfaced through the gate: a look #8 entry that
    somehow landed with no `trigger_review_ref` (defense-in-depth — `plan_look`
    itself would already have refused this; the gate re-checks anyway, at
    consumption time, exactly as `require_planned` documents) is fabricated
    directly via `_append` (the `test_mstat_test_looks.py` pattern for exercising a
    guard `plan_look` would normally prevent from ever landing)."""
    ledger = _seeded_ledger(tmp_path)
    ledger._append("planned", {
        "look_no": 8, "suite_version": SUITE_VERSION, "experiment": "S2 unit test", "arm": "x",
        "run_id": "S2-noref-test", "authorized_by": "brennen", "trigger_review_ref": None,
        "planned_at": "2026-08-21T00:00:00+00:00", "code_commit": "deadbee",
    })
    with pytest.raises(LookRefused, match="trigger_review_ref"):
        run_eval.test_look_gate("test", "S2-noref-test", False, ledger_path=ledger.path,
                                mirror_path=default_markdown_path())


def test_test_look_gate_refuses_when_the_mirror_diverges(tmp_path):
    ledger = _seeded_ledger(tmp_path)
    ledger.plan_look(look_no=8, suite_version=SUITE_VERSION, experiment="S2 unit test",
                     arm="x", run_id="S2-divergent-test", authorized_by="brennen",
                     trigger_review_ref=REAL_REVIEW_REF)
    tampered = tmp_path / "TEST_LOOK_LEDGER.md"
    text = default_markdown_path().read_text(encoding="utf-8")
    tampered.write_text(text.replace("| 96 | execution |\n| 2 |", "| 48 | execution |\n| 2 |"))
    with pytest.raises(MirrorDivergence):
        run_eval.test_look_gate("test", "S2-divergent-test", False, ledger_path=ledger.path,
                                mirror_path=tampered)


# ============================================ C2. persist()'s TEST-write choke point
#
# Finding 2: `test_look_gate` fires only from `main()`; a script that imports
# `persist()` directly (`scripts/m0_paired_probe.py` already does) could otherwise
# write a TEST-split `case_scores` row completely unledgered. These tests drive
# `persist()` itself, never `main()`, and prove the guard fires before `conn` is
# touched at all by passing `conn=None` and reading the exception TYPE: `LookRefused`
# (a refusal) is distinguishable from `AttributeError` (the guard passed and execution
# reached `None.cursor()`).


class _StubRecord:
    """A minimal stand-in for a pydantic `Trajectory`/`CaseScore` — only the
    attributes `persist()` actually reads, plus a real `model_dump_json()` so the
    `json.loads(...)` around it has valid JSON to parse."""

    def __init__(self, **fields):
        self.__dict__.update(fields)

    def model_dump_json(self) -> str:
        return json.dumps(dict(self.__dict__), default=str)


class _RecordingConn:
    """A connection stand-in that records every `execute()` call instead of touching
    a database — proves a TRAIN/DEV-seed `persist()` call reaches real SQL (and
    therefore never consulted the TEST-look ledger to get there)."""

    def __init__(self):
        self.executed: list[str] = []
        self.committed = False

    def cursor(self, row_factory=None):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.executed.append(sql)

    def commit(self):
        self.committed = True


def test_persist_test_seed_scenario_with_no_planned_look_refuses_before_any_db_touch(
    tmp_path, monkeypatch):
    monkeypatch.setattr(run_eval, "TEST_LOOK_LEDGER_PATH", tmp_path / "test_looks.jsonl")
    run_eval._test_look_verdict_cache.clear()
    score = SimpleNamespace(scenario_id="S01-3000001")   # seed 3_000_001 -> TEST range
    with pytest.raises(LookRefused, match="no planned or spent TEST look"):
        run_eval.persist(None, "S2-unplanned-persist-test", score, trajectory=None)


def test_persist_test_seed_scenario_with_a_planned_look_passes_the_guard(tmp_path, monkeypatch):
    ledger = _seeded_ledger(tmp_path)
    ledger.plan_look(look_no=8, suite_version=SUITE_VERSION, experiment="S2 unit test",
                     arm="x", run_id="S2-planned-persist-test", authorized_by="brennen",
                     trigger_review_ref=REAL_REVIEW_REF)
    monkeypatch.setattr(run_eval, "TEST_LOOK_LEDGER_PATH", ledger.path)
    run_eval._test_look_verdict_cache.clear()
    score = SimpleNamespace(scenario_id="S01-3000001")
    # The guard passed (no LookRefused); execution reached `conn.cursor()` on
    # conn=None, which is an AttributeError, not a LookRefused -- proving the guard
    # specifically let this run id through rather than the call failing some other way.
    with pytest.raises(AttributeError):
        run_eval.persist(None, "S2-planned-persist-test", score, trajectory=None)


def test_persist_dot_weak_run_id_resolves_to_its_base_run_id_in_the_ledger(tmp_path, monkeypatch):
    ledger = _seeded_ledger(tmp_path)
    ledger.plan_look(look_no=8, suite_version=SUITE_VERSION, experiment="S2 unit test",
                     arm="x", run_id="S2-cascade-persist-test", authorized_by="brennen",
                     trigger_review_ref=REAL_REVIEW_REF)
    monkeypatch.setattr(run_eval, "TEST_LOOK_LEDGER_PATH", ledger.path)
    run_eval._test_look_verdict_cache.clear()
    score = SimpleNamespace(scenario_id="S01-3000001")
    # "S2-cascade-persist-test.weak" is never itself planned -- only its base id is.
    # If the guard checked the literal run_id it would refuse; it passes instead,
    # proving it strips the ".weak" suffix before consulting the ledger.
    with pytest.raises(AttributeError):
        run_eval.persist(None, "S2-cascade-persist-test.weak", score, trajectory=None)


def test_persist_train_and_dev_seed_scenarios_never_consult_the_ledger(tmp_path, monkeypatch):
    # No file at all at this path -- if a TRAIN/DEV-seed persist() call consulted the
    # ledger anyway, TestLookLedger.read() would return [] (missing-file semantics)
    # and the guard would refuse (no planned/spent entry). It doesn't: the insert
    # reaches the stub connection instead, proving TRAIN/DEV never asks the ledger.
    monkeypatch.setattr(run_eval, "TEST_LOOK_LEDGER_PATH", tmp_path / "unconsulted.jsonl")
    run_eval._test_look_verdict_cache.clear()
    conn = _RecordingConn()
    trajectory = _StubRecord(trace_id="trace-1", scenario_id="S01-1000001", case_id="case-1",
                             experiment_arm="E2", workflow="investigate", workflow_version="v1")
    score = _StubRecord(scenario_id="S01-1000001", experiment_arm="E2", all_pass=True)
    run_eval.persist(conn, "S2-train-persist-test", score, trajectory)   # seed 1_000_001 -> TRAIN
    assert len(conn.executed) == 2   # trajectories INSERT + case_scores INSERT
    assert conn.committed is True


# ======================================================= D. pinned corpus identity

def _pin(tmp_path: Path, digest_value: str) -> None:
    manifest_dir = tmp_path / "scenarios" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / f"corpus_v{SUITE_VERSION}.json").write_text(
        json.dumps({"suite_version": SUITE_VERSION, "corpus_digest": digest_value}))


def test_check_corpus_pinned_passes_on_a_match(monkeypatch, tmp_path):
    _pin(tmp_path, "a" * 64)
    monkeypatch.setattr(run_eval, "ROOT", tmp_path)
    run_eval.check_corpus_pinned("a" * 64)   # must not raise


def test_check_corpus_pinned_refuses_a_mismatch(monkeypatch, tmp_path):
    _pin(tmp_path, "a" * 64)
    monkeypatch.setattr(run_eval, "ROOT", tmp_path)
    with pytest.raises(SuiteMismatch, match="mismatch"):
        run_eval.check_corpus_pinned("b" * 64)


def test_check_corpus_pinned_refuses_a_missing_manifest(monkeypatch, tmp_path):
    monkeypatch.setattr(run_eval, "ROOT", tmp_path)
    with pytest.raises(SuiteMismatch, match="no pinned corpus manifest"):
        run_eval.check_corpus_pinned("a" * 64)


# =============================================== E. consequence-bearing tolerances

def _spec(consequence: Consequence, max_violations: int = 0, metric: str = "cap_hit", **kw) -> ToleranceSpec:
    fields = {"spec_id": "s2-tol", "metric": metric, "description": "S2 unit test tolerance",
              "denominator_n": 10, "max_violations": max_violations, "consequence": consequence}
    fields.update(kw)
    return ToleranceSpec(**fields)


def test_cap_hit_metric_fires_only_on_stop_reason_length():
    fn = run_eval.TOLERANCE_METRICS["cap_hit"]
    assert fn({"stop_reason": "length"}) is True
    assert fn({"stop_reason": None}) is False
    assert fn({"stop_reason": "stop"}) is False


def test_case_fail_metric_counts_a_failed_score_and_an_exception_alike():
    fn = run_eval.TOLERANCE_METRICS["case_fail"]
    assert fn({"exception": False, "all_pass": False}) is True
    assert fn({"exception": True, "all_pass": None}) is True    # an exception never scored a pass
    assert fn({"exception": False, "all_pass": True}) is False


def test_exception_metric_fires_only_on_exception():
    fn = run_eval.TOLERANCE_METRICS["exception"]
    assert fn({"exception": True}) is True
    assert fn({"exception": False}) is False


def test_load_tolerance_specs_refuses_an_unknown_metric(tmp_path):
    path = tmp_path / "tol.json"
    path.write_text(json.dumps([{
        "spec_id": "bad", "metric": "not_a_real_metric", "description": "d",
        "denominator_n": 10, "max_violations": 1, "consequence": "ABORT",
    }]))
    with pytest.raises(run_eval.UnknownToleranceMetric, match="not_a_real_metric"):
        run_eval.load_tolerance_specs(path)


def test_load_tolerance_specs_parses_every_supported_metric(tmp_path):
    path = tmp_path / "tol.json"
    path.write_text(json.dumps([
        {"spec_id": f"s-{m}", "metric": m, "description": "d", "denominator_n": 10,
         "max_violations": 1, "consequence": "ABORT"}
        for m in sorted(run_eval.TOLERANCE_METRICS)
    ]))
    specs = run_eval.load_tolerance_specs(path)
    assert [s.metric for s in specs] == sorted(run_eval.TOLERANCE_METRICS)


def _events(tmp_path: Path, run_id: str) -> RunEventLog:
    return RunEventLog(tmp_path / f"{run_id}.events.jsonl", run_id=run_id)


def _lines(tmp_path: Path, run_id: str) -> list[dict]:
    return [json.loads(ln) for ln in (tmp_path / f"{run_id}.events.jsonl").read_text().splitlines()]


def test_observe_tolerances_aborts_at_violation_k_plus_1_and_events_record_it(tmp_path):
    spec = _spec(Consequence.ABORT, max_violations=1)
    tracker = ToleranceTracker(spec)
    trackers = {spec.spec_id: tracker}
    events = _events(tmp_path, "S2-abort-test")
    violation_ctx = {"exception": False, "stop_reason": "length", "all_pass": True}

    run_eval.observe_tolerances(trackers, violation_ctx, events=events)   # violation 1 of <=1: no breach yet
    assert not tracker.breached
    with pytest.raises(SystemExit, match="ABORT"):
        run_eval.observe_tolerances(trackers, violation_ctx, events=events)   # violation 2: breach

    lines = _lines(tmp_path, "S2-abort-test")
    kinds = [ln["event"] for ln in lines]
    assert "tolerance_consequence" in kinds
    consequence_line = next(ln for ln in lines if ln["event"] == "tolerance_consequence")
    assert consequence_line["consequence"] == "ABORT" and consequence_line["at_violation"] == 2
    run_end = next(ln for ln in lines if ln["event"] == "run_end")
    assert run_end["status"] == "aborted-tolerance"


def test_apply_tolerance_consequence_folds_abort_into_candidate_end_run(tmp_path):
    spec = _spec(Consequence.ABORT, max_violations=0)   # first violation itself breaches
    tracker = ToleranceTracker(spec)
    events = _events(tmp_path, "S2-abort-candidate-test")
    captured: dict = {}
    with pytest.raises(SystemExit):
        run_eval.observe_tolerances(
            {spec.spec_id: tracker}, {"exception": False, "stop_reason": "length", "all_pass": True},
            events=events, candidate_end_run=lambda extra: captured.update(extra))
    assert "tolerance_consequence" in captured
    assert captured["tolerance_consequence"]["spec_id"] == spec.spec_id


def test_observe_tolerances_recalibrate_halts_and_prints_the_named_procedure(tmp_path, capsys):
    spec = _spec(Consequence.RECALIBRATE, max_violations=0,
                 recalibration_procedure="re-run the 36-case pilot at cap 8192")
    tracker = ToleranceTracker(spec)
    events = _events(tmp_path, "S2-recal-test")
    with pytest.raises(SystemExit, match="RECALIBRATE"):
        run_eval.observe_tolerances(
            {spec.spec_id: tracker}, {"exception": False, "stop_reason": "length", "all_pass": True},
            events=events)
    assert "re-run the 36-case pilot at cap 8192" in capsys.readouterr().out
    run_end = next(ln for ln in _lines(tmp_path, "S2-recal-test") if ln["event"] == "run_end")
    assert run_end["status"] == "halted-recalibrate"


def test_observe_tolerances_proceed_records_exactly_once_and_never_halts(tmp_path):
    spec = _spec(Consequence.PROCEED_WITH_DECLARED_CEILING, max_violations=0,
                 declared_ceiling="cap 8192", projected_cost="~2h wall")
    tracker = ToleranceTracker(spec)
    trackers = {spec.spec_id: tracker}
    events = _events(tmp_path, "S2-proceed-test")
    ctx = {"exception": False, "stop_reason": "length", "all_pass": True}

    run_eval.observe_tolerances(trackers, ctx, events=events)   # crosses immediately (k=0)
    run_eval.observe_tolerances(trackers, ctx, events=events)   # legal further observation, no 2nd event
    run_eval.observe_tolerances(trackers, ctx, events=events)

    lines = _lines(tmp_path, "S2-proceed-test")
    consequences = [ln for ln in lines if ln["event"] == "tolerance_consequence"]
    assert len(consequences) == 1   # recorded ONCE, per the guard on observe()'s own crossing semantics
    assert consequences[0]["declared_ceiling"] == "cap 8192"
    assert not any(ln["event"] == "run_end" for ln in lines)   # PROCEED never halts the run


def test_reconstruct_tolerance_trackers_refuses_resume_with_an_exception_metric_spec():
    spec = _spec(Consequence.ABORT, metric="exception")
    # conn is never touched: the refusal fires before any query — no DB needed here.
    with pytest.raises(SystemExit, match="restart the run"):
        run_eval.reconstruct_tolerance_trackers(None, "S2-resume-test", [spec])


# ================================================================ F. certainty curtailment

def test_curtailment_fires_one_below_the_boundary_and_not_at_it():
    policy = CurtailmentPolicy(bar=0.5, n_total=10)   # threshold = ceil(5) = 5
    assert policy.should_curtail(0, 6) is True    # remaining=4, 0+4=4 < 5  -> curtail
    assert policy.should_curtail(1, 6) is False   # remaining=4, 1+4=5 == 5 -> NOT curtailed (can still qualify)


def test_curtail_and_exit_writes_an_interval_only_report_with_correct_unrun_classes(tmp_path):
    policy = CurtailmentPolicy(bar=0.5, n_total=10)
    events = _events(tmp_path, "S2-curtail-test")
    remaining = [{"scenario_id": "S02-1000001"}, {"scenario_id": "S01-1000002"},
                 {"scenario_id": "S01-1000003"}]
    curtailed_path = tmp_path / "curtailed_runs.jsonl"

    with pytest.raises(SystemExit, match="curtailed"):
        run_eval.curtail_and_exit(policy, 0, 6, run_id="S2-curtail-test", split="test", arm="X",
                                  remaining_manifests=remaining, events=events,
                                  curtailed_runs_path=curtailed_path)

    reports = [json.loads(ln) for ln in curtailed_path.read_text().splitlines()]
    assert len(reports) == 1
    report = reports[0]
    assert report["curtailed"] is True
    assert report["interval"] == [0, 4]           # [passes, passes + remaining] = [0, 0+4]
    assert report["unrun_classes"] == ["S01", "S02"]   # sorted, deduplicated
    assert "rate" not in report and "estimate" not in report and "pass_rate" not in report

    lines = _lines(tmp_path, "S2-curtail-test")
    assert any(ln["event"] == "curtailed" for ln in lines)
    run_end = next(ln for ln in lines if ln["event"] == "run_end")
    assert run_end["status"] == "curtailed"


def test_curtail_and_exit_folds_the_interval_into_candidate_end_run(tmp_path):
    policy = CurtailmentPolicy(bar=0.9, n_total=4)
    events = _events(tmp_path, "S2-curtail-candidate-test")
    captured: dict = {}
    with pytest.raises(SystemExit):
        run_eval.curtail_and_exit(policy, 0, 4, run_id="S2-curtail-candidate-test", split="dev",
                                  arm="Y", remaining_manifests=[], events=events,
                                  curtailed_runs_path=tmp_path / "curtailed.jsonl",
                                  candidate_end_run=lambda extra: captured.update(extra))
    assert captured == {"curtailed": True, "certain_interval": [0, 0], "unrun_classes": []}
