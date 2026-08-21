"""TEST-look ledger — the invariants, against temporary ledger files.

Every test but one builds its own ledger under `tmp_path`; the one exception
(`test_the_live_seeded_ledger_verifies_and_mirrors_the_real_markdown`) reads the real
seeded `learning/registry/test_looks.jsonl` against the real
`TEST_LOOK_LEDGER.md` (FIS root) — read-only, nothing is written.

The invariants (M-STAT unit spec; playbook §1; owner decision 2026-08-21):

  1. the log is hash-chained and append-only; an edited line is caught on the next read;
  2. `seed()` backfills exactly the seven historical Suite-v3 looks, faithfully, once;
  3. `next_look_no` is the single source of "what look comes next", so `plan_look`'s
     sequencing guard doubles as the no-double-planning-of-a-look_no guard;
  4. Suite-v3 look #8+ is refused without a `trigger_review_ref` naming a file that
     exists in the repo right now — re-checked at `require_planned`, not just at plan
     time;
  5. a look is spent at the first executed case, idempotently for its own run_id, and
     refused for any other run_id once spent;
  6. `require_planned` fails closed: no ledger file, no planned entry — no TEST;
  7. the markdown mirror is validated against the machine ledger, never the reverse.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.routing.learn import digest
from fis_platform.test_looks import (
    HISTORICAL_SUITE_VERSION,
    LedgerIntegrityError,
    LookRefused,
    MirrorDivergence,
    TestLookLedger,
    default_markdown_path,
    default_path,
    validate_mirror,
)

REAL_REVIEW_REF = "TEST_LOOK_LEDGER.md"   # a real, committed file — stands in
                                                        # for the Suite-v4 trigger review doc


@pytest.fixture
def ledger(tmp_path: Path) -> TestLookLedger:
    return TestLookLedger(tmp_path / "test_looks.jsonl")


@pytest.fixture
def seeded(ledger: TestLookLedger) -> TestLookLedger:
    ledger.seed()
    return ledger


def _plan8(led: TestLookLedger, *, run_id: str = "R7-pilot-test",
          trigger_review_ref: str | None = REAL_REVIEW_REF, **over) -> dict:
    fields = {"look_no": 8, "suite_version": "3", "experiment": "R7 pilot",
              "arm": "qwen-x", "run_id": run_id, "authorized_by": "brennen",
              "trigger_review_ref": trigger_review_ref}
    fields.update(over)
    return led.plan_look(**fields)


# ------------------------------------------------------------------ 1. seeding

def test_seed_produces_exactly_seven_historical_entries_and_advances_the_counter(ledger):
    written = ledger.seed()
    assert len(written) == 7
    entries = ledger.read()
    assert len(entries) == 7
    assert [e["kind"] for e in entries] == ["historical"] * 7
    assert [e["look_no"] for e in entries] == list(range(1, 8))
    assert [e["seq"] for e in entries] == list(range(1, 8))
    assert all(e["suite_version"] == HISTORICAL_SUITE_VERSION for e in entries)
    assert entries[0]["prev_entry_digest"] == ""
    assert ledger.next_look_no("3") == 8
    assert ledger.next_look_no("4") == 1          # a different suite starts fresh


def test_seed_refuses_to_touch_a_ledger_that_already_exists(seeded):
    before = seeded.path.read_bytes()
    with pytest.raises(LookRefused, match="already exists"):
        seeded.seed()
    assert seeded.path.read_bytes() == before, "a refused seed must not touch the file"


def test_the_seven_historical_rows_match_the_markdown_backfill_exactly(seeded):
    """The specific dates/cases/kinds — copied verbatim, no reinterpretation."""
    entries = seeded.read()
    expected = [
        (1, "2026-08-17", 96, "execution"), (2, "2026-08-17", 96, "execution"),
        (3, "2026-08-17", 96, "execution"), (4, "2026-08-18", 96, "replay"),
        (5, "2026-08-18", 96, "replay"), (6, "2026-08-19", 96, "execution"),
        (7, "2026-08-19", 96, "execution"),
    ]
    got = [(e["look_no"], e["date"], e["cases"], e["look_kind"]) for e in entries]
    assert got == expected


# ------------------------------------------------------------------ 2. the chain

def _rewrite(path: Path, entries: list[dict]) -> None:
    path.write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in entries))


def test_an_edited_entry_breaks_its_own_digest(seeded):
    entries = seeded.read()
    entries[2]["cases"] = 48
    _rewrite(seeded.path, entries)
    with pytest.raises(LedgerIntegrityError, match="the entry was edited"):
        seeded.read()


def test_an_edited_entry_with_a_recomputed_digest_breaks_the_chain_link(seeded):
    entries = seeded.read()
    entries[2]["cases"] = 48
    entries[2]["entry_digest"] = digest({k: v for k, v in entries[2].items() if k != "entry_digest"})
    _rewrite(seeded.path, entries)
    with pytest.raises(LedgerIntegrityError, match="the log was rewritten"):
        seeded.read()


def test_a_non_json_line_is_refused(seeded):
    with seeded.path.open("a", encoding="utf-8") as fh:
        fh.write("not json at all\n")
    with pytest.raises(LedgerIntegrityError, match="not valid JSON"):
        seeded.read()


def test_a_missing_ledger_reads_as_no_entries_not_an_error(ledger):
    assert ledger.read() == []
    assert ledger.next_look_no("3") == 1


# ------------------------------------------------------------------ 3. planning

def test_plan_look_refuses_a_look_no_out_of_sequence(seeded):
    with pytest.raises(LookRefused, match="not the next look"):
        _plan8(seeded, look_no=9)
    with pytest.raises(LookRefused, match="not the next look"):
        _plan8(seeded, look_no=7)


def test_plan_look_refuses_an_empty_authorized_by(seeded):
    with pytest.raises(LookRefused, match="non-empty authorized_by"):
        _plan8(seeded, authorized_by="   ")


def test_look_8_plan_without_trigger_review_ref_is_refused(seeded):
    before = seeded.read()
    with pytest.raises(LookRefused, match="needs a trigger_review_ref"):
        _plan8(seeded, trigger_review_ref=None)
    assert seeded.read() == before, "a refused plan must not touch the log"


def test_look_8_plan_with_a_ref_naming_a_nonexistent_file_is_refused(seeded):
    with pytest.raises(LookRefused, match="does not name an existing file"):
        _plan8(seeded, trigger_review_ref="DOES_NOT_EXIST_REVIEW.md")


def test_look_8_plan_succeeds_with_a_ref_naming_a_real_committed_file(seeded):
    entry = _plan8(seeded)
    assert entry["kind"] == "planned" and entry["look_no"] == 8
    assert entry["trigger_review_ref"] == REAL_REVIEW_REF
    assert seeded.next_look_no("3") == 9


def test_a_look_below_eight_needs_no_trigger_review_ref(ledger):
    # suite "3" has no historical entries here, so look_no 1 is "next" — well below the floor
    entry = ledger.plan_look(look_no=1, suite_version="3", experiment="warm-up",
                             arm="x", run_id="R-warmup-test", authorized_by="brennen")
    assert entry["trigger_review_ref"] is None


def test_look_8_on_a_different_suite_version_needs_no_trigger_review_ref(ledger):
    # the floor is Suite-v3-specific (playbook §1); walk suite "9" up to look #8 to prove it
    for n in range(1, 9):
        entry = ledger.plan_look(look_no=n, suite_version="9", experiment="future-suite",
                                 arm="x", run_id=f"R-future-{n}-test", authorized_by="brennen")
    assert entry["look_no"] == 8 and entry["suite_version"] == "9"
    assert entry["trigger_review_ref"] is None


def test_plan_look_refuses_a_duplicate_run_id(seeded):
    _plan8(seeded, run_id="R7-shared-test")
    with pytest.raises(LookRefused, match="already in the TEST-look ledger"):
        seeded.plan_look(look_no=9, suite_version="3", experiment="R7 pilot 2",
                         arm="qwen-y", run_id="R7-shared-test", authorized_by="brennen",
                         trigger_review_ref=REAL_REVIEW_REF)


def test_no_double_planning_of_the_same_look_no(seeded):
    """The sequencing guard IS the no-double-planning guard: once #8 is planned, the
    next look for suite 3 is #9 — #8 can never be planned again, under any run_id."""
    _plan8(seeded, run_id="R7-first-test")
    with pytest.raises(LookRefused, match="not the next look"):
        _plan8(seeded, look_no=8, run_id="R7-second-test")


# ------------------------------------------------------------------ 4. spending

def test_plan_and_spend_roundtrip(seeded):
    planned = _plan8(seeded)
    assert seeded.is_spent(planned["run_id"]) is False
    spent = seeded.record_spend(planned["run_id"], "TEST-scn-0001")
    assert spent["kind"] == "spent" and spent["look_no"] == 8
    assert spent["first_scenario_id"] == "TEST-scn-0001"
    assert seeded.is_spent(planned["run_id"]) is True


def test_spend_is_idempotent_for_the_same_run_id(seeded):
    planned = _plan8(seeded)
    first = seeded.record_spend(planned["run_id"], "TEST-scn-0001")
    again = seeded.record_spend(planned["run_id"], "TEST-scn-0001")
    assert first == again
    # only one spent entry landed — idempotent means no-op, not a second append
    assert sum(1 for e in seeded.read() if e["kind"] == "spent") == 1


def test_spend_refuses_a_run_id_with_no_planned_look(seeded):
    with pytest.raises(LookRefused, match="no planned TEST look"):
        seeded.record_spend("R7-never-planned-test", "TEST-scn-0001")


def test_second_spend_under_a_different_run_id_is_refused(seeded):
    """Two planned entries sharing a look_no is a state `plan_look`'s sequencing guard
    prevents in normal operation, but a defensive check in `record_spend` still catches
    it (e.g. a race between two concurrent `plan` invocations) — set up directly via
    the private `_append` the way `test_r6_state_machine.py` fabricates tamper states."""
    a = seeded._append("planned", {
        "look_no": 8, "suite_version": "3", "experiment": "R7 pilot", "arm": "qwen-a",
        "run_id": "R7-a-test", "authorized_by": "brennen",
        "trigger_review_ref": REAL_REVIEW_REF, "planned_at": "2026-08-21T00:00:00+00:00",
        "code_commit": "deadbee",
    })
    b = seeded._append("planned", {
        "look_no": 8, "suite_version": "3", "experiment": "R7 pilot", "arm": "qwen-b",
        "run_id": "R7-b-test", "authorized_by": "brennen",
        "trigger_review_ref": REAL_REVIEW_REF, "planned_at": "2026-08-21T00:00:01+00:00",
        "code_commit": "deadbee",
    })
    assert a["run_id"] != b["run_id"] and a["look_no"] == b["look_no"] == 8
    seeded.record_spend("R7-a-test", "TEST-scn-0001")
    with pytest.raises(LookRefused, match="already spent by run_id 'R7-a-test'"):
        seeded.record_spend("R7-b-test", "TEST-scn-0002")


# ------------------------------------------------------------------ 5. require_planned

def test_require_planned_refuses_with_no_ledger_file(ledger):
    with pytest.raises(LookRefused, match="no TEST-look ledger"):
        ledger.require_planned("3", "R7-anything-test")


def test_require_planned_refuses_a_run_id_with_no_planned_look(seeded):
    with pytest.raises(LookRefused, match="no planned TEST look"):
        seeded.require_planned("3", "R7-never-planned-test")


def test_require_planned_returns_the_planned_entry(seeded):
    planned = _plan8(seeded)
    got = seeded.require_planned("3", planned["run_id"])
    assert got == planned


def test_require_planned_re_checks_the_trigger_review_even_after_planning(seeded, tmp_path):
    """A review doc that existed at plan time but was later deleted/renamed must still
    block the run — the whole point of re-checking at consumption time."""
    review = tmp_path / "review.md"
    review.write_text("R7 trigger review\n")
    planned = _plan8(seeded, trigger_review_ref=str(review))
    assert seeded.require_planned("3", planned["run_id"])["look_no"] == 8
    review.unlink()
    with pytest.raises(LookRefused, match="does not name an existing file"):
        seeded.require_planned("3", planned["run_id"])


def test_require_planned_writes_nothing(seeded):
    _plan8(seeded)
    before = seeded.path.read_bytes()
    seeded.require_planned("3", "R7-pilot-test")
    assert seeded.path.read_bytes() == before


# ------------------------------------------------------------------ 6. mirror validation

def test_mirror_validation_passes_on_the_real_markdown_vs_the_seeded_ledger(seeded):
    assert validate_mirror(seeded.path, default_markdown_path()) is None


def test_mirror_validation_fails_when_a_field_is_tampered(seeded, tmp_path):
    tampered = tmp_path / "TEST_LOOK_LEDGER.md"
    text = default_markdown_path().read_text(encoding="utf-8")
    tampered.write_text(text.replace("| 96 | execution |\n| 2 |", "| 48 | execution |\n| 2 |"))
    with pytest.raises(MirrorDivergence, match="disagrees with"):
        validate_mirror(seeded.path, tampered)


def test_mirror_validation_fails_when_the_markdown_has_a_row_with_no_machine_counterpart(seeded, tmp_path):
    tampered = tmp_path / "TEST_LOOK_LEDGER.md"
    text = default_markdown_path().read_text(encoding="utf-8")
    extra_row = "| 99 | 2026-08-20 | phantom | phantom arm | 96 | execution |\n"
    tampered.write_text(text + extra_row)
    with pytest.raises(MirrorDivergence, match="row #99 has no counterpart"):
        validate_mirror(seeded.path, tampered)


def test_mirror_validation_fails_when_the_markdown_file_is_missing(seeded, tmp_path):
    with pytest.raises(MirrorDivergence, match="no markdown mirror"):
        validate_mirror(seeded.path, tmp_path / "nope.md")


def test_mirror_validation_tolerates_machine_entries_newer_than_the_markdown(seeded):
    """Planned/spent entries beyond the seven historical rows must not fail validation —
    the mirror is updated by humans/tools later (playbook §1)."""
    _plan8(seeded)
    assert validate_mirror(seeded.path, default_markdown_path()) is None


# ------------------------------------------------------------------ 7. the live file (read-only)

def test_the_live_seeded_ledger_verifies_and_mirrors_the_real_markdown():
    """The one test against the real, committed `learning/registry/test_looks.jsonl` —
    read-only. This is the file `scripts/test_look_ledger.py seed` produced once."""
    path = default_path()
    assert path.exists(), "the live ledger must already be seeded (run `seed` once)"
    live = TestLookLedger(path)
    entries = live.read()
    assert len(entries) >= 7
    assert [e["look_no"] for e in entries[:7]] == list(range(1, 8))
    assert all(e["kind"] == "historical" for e in entries[:7])
    assert validate_mirror(path, default_markdown_path()) is None
