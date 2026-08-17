"""Suite v3 gates that need the BUILT corpus in Postgres.

Skipped when Postgres is down or the corpus in it is not this code's suite (then the
right move is `make migrate corpus`, and `run_eval` refuses to run anyway). Nothing
here calls a model server.
"""

from __future__ import annotations

import json
import os

import psycopg
import pytest

from fis_platform.events.projection import project
from fis_platform.suite import (
    SUITE_VERSION,
    SuiteMismatch,
    corpus_suite,
    require_comparable,
    suite_of_run,
)
from fis_platform.tool_broker.broker import ToolBroker
from fis_platform.verification.verifier import collect_observed_ids
from scenarios.generator.run import build
from services.ai_orchestrator.investigate import _phase_one, _phase_two

OWNER_DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")
TOOLS_DSN = os.environ.get("FIS_TOOLS_DSN",
                           "postgresql://fis_tools:fis_tools_local_dev@127.0.0.1:5433/fis")


def _corpus_ready() -> str | None:
    try:
        with psycopg.connect(OWNER_DSN, connect_timeout=3) as conn:
            suite = corpus_suite(conn)
    except psycopg.Error:
        return "FIS Postgres not running"
    if suite != SUITE_VERSION:
        return f"corpus in the database is suite {suite!r}, code is {SUITE_VERSION!r} — run make migrate corpus"
    return None


_SKIP = _corpus_ready()
pytestmark = pytest.mark.skipif(_SKIP is not None, reason=_SKIP or "")


def _manifests(conn, split="dev"):
    return conn.execute(
        "SELECT scenario_id, seed, case_id FROM ground_truth.scenario_manifests "
        "WHERE split = %s ORDER BY scenario_id", (split,)).fetchall()


def test_projection_matches_the_live_pipeline():
    """The name `projection.py` promised. `run.materialise` asserts id-set equality
    at generation time; this compares the ROWS the two write for every scenario in
    the corpus — status, amount, posted_at, mapping_version — so a consumer that
    wrote the right id with the wrong value would be caught."""
    with psycopg.connect(OWNER_DSN) as conn:
        for split in ("dev", "test", "train"):
            for scenario_id, seed, _ in _manifests(conn, split):
                world, _ = build(scenario_id.split("-")[0], seed)
                proj = project(world.published, world.mapping_versions)

                live_deliveries = {r[0]: r for r in conn.execute(
                    "SELECT delivery_id, status, idempotency_key, attempt FROM webhook.deliveries "
                    "WHERE scenario_id = %s AND provider_event_id = ANY(%s)",
                    (scenario_id, [e.provider_event_id for e in world.published])).fetchall()}
                assert {d["delivery_id"]: (d["delivery_id"], d["status"], d["idempotency_key"], d["attempt"])
                        for d in proj.deliveries} == live_deliveries, scenario_id

                live_events = {r[0]: r for r in conn.execute(
                    "SELECT event_id, mapping_version, normalized_state FROM integration.events "
                    "WHERE scenario_id = %s", (scenario_id,)).fetchall()}
                assert {e["event_id"]: (e["event_id"], e["mapping_version"], e["normalized_state"])
                        for e in proj.events} == live_events, scenario_id

                live_entries = conn.execute(
                    "SELECT entry_id, account_id, direction, amount, reference_id, posted_at "
                    "FROM ledger.entries WHERE scenario_id = %s ORDER BY posting_seq",
                    (scenario_id,)).fetchall()
                assert [(e["entry_id"], e["account_id"], e["direction"], e["amount"],
                         e["reference_id"], e["posted_at"]) for e in proj.entries] == live_entries, (
                    f"{scenario_id}: ledger rows or their posting order differ from the projection")


def test_every_ledger_entry_was_caused_by_a_published_event():
    """No direct ledger writes remain (contract § 2A step 6): every entry id is the
    envelope-derived `le_<12hex>` shape and resolves to a normalized event."""
    with psycopg.connect(OWNER_DSN) as conn:
        bad_shape = conn.execute(
            r"SELECT count(*) FROM ledger.entries WHERE entry_id !~ '^le_[0-9a-f]{12}$'").fetchone()[0]
        orphans = conn.execute(
            "SELECT count(*) FROM ledger.entries e WHERE NOT EXISTS ("
            "  SELECT 1 FROM integration.events ev WHERE ev.event_id = replace(e.entry_id, 'le_', 'evt_'))"
        ).fetchone()[0]
        total = conn.execute("SELECT count(*) FROM ledger.entries").fetchone()[0]
    assert total == 224 + 112 + 336, "one posting per settlement plus S02's double and S07's reversal"
    assert bad_shape == 0 and orphans == 0


def test_s01_fixed_evidence_bundle_shows_the_idempotency_key_and_it_is_observed():
    """Contract § 2D: the key the model is judged on is in the bundle it was shown,
    for every S01 case in the model-facing splits, and the verifier harvests it."""
    with psycopg.connect(OWNER_DSN) as conn, ToolBroker(TOOLS_DSN) as broker:
        for split in ("dev", "test"):
            for scenario_id, seed, case_id in _manifests(conn, split):
                if not scenario_id.startswith("S01-"):
                    continue
                world, _ = build("S01", seed)
                key = world.published[0].idempotency_key
                assert key and key.startswith("idem-")
                case, _ = broker.invoke("get_case", {"case_id": case_id})
                results = [case]
                for tool, args in _phase_one(case):
                    res, _ = broker.invoke(tool, args)
                    results.append({tool: res})
                for tool, args in _phase_two(case, results):
                    res, _ = broker.invoke(tool, args)
                    results.append({tool: res})
                assert key in json.dumps(results, default=str), f"{scenario_id}: key not in bundle"
                assert key in collect_observed_ids(results), f"{scenario_id}: key not harvested"


def test_suite_identity_is_recorded_and_cross_suite_pairing_is_refused():
    with psycopg.connect(OWNER_DSN) as conn:
        assert corpus_suite(conn) == SUITE_VERSION
        # A suite-2 run (R3b) exists in learning.* untouched; pairing it against the
        # current corpus, or with a run from another suite, is refused by default.
        assert suite_of_run(conn, "R3b-qwen-dev") == "2"
        assert suite_of_run(conn, "E2-local-96") == "1"
        with pytest.raises(SuiteMismatch):
            require_comparable(conn, ["R3b-qwen-dev"], against_corpus=True)
        with pytest.raises(SuiteMismatch):
            require_comparable(conn, ["R3b-qwen-dev", "E2-local-96"], against_corpus=False)
        # Same-suite pairing without the corpus join is fine.
        require_comparable(conn, ["R3b-qwen-dev", "R3b-nemotron-dev"], against_corpus=False)
        # Explicit opt-in proceeds (with the printed caveat).
        require_comparable(conn, ["R3b-qwen-dev"], allow_cross_suite=True, against_corpus=True)


def test_runner_refuses_to_reuse_a_run_id_across_suites():
    from evals.runner.run_eval import guard_suite
    with psycopg.connect(OWNER_DSN) as conn:
        with pytest.raises(SuiteMismatch, match="suite-2 scores"):
            guard_suite(conn, "R3b-qwen-dev", "dev", resume=True)
        with pytest.raises(SuiteMismatch, match="suite-2 scores"):
            guard_suite(conn, "R3b-qwen-dev", "dev", resume=False)
        guard_suite(conn, "V3-never-used-run-id", "dev", resume=False)   # fresh id: fine
