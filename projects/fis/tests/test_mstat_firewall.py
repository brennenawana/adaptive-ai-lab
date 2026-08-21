"""M-STAT S3 — the paired-comparison firewall (playbook §6 guard 3, "curtailment
guard C"): `fis_platform.tolerances.refuse_curtailed`, and its wiring into every
PAIRED entry point (`scripts/r6_metrics.py` pairwise, `scripts/compare_routes.py`,
`scripts/model_migration_matrix.py`, `scripts/r6_analysis.py`,
`scripts/routing_cascade_report.py`, `scripts/r3b_selection_rule.py`).

No DB dependency: `refuse_curtailed` itself is pure I/O over a JSONL file, and the
one integration-shaped test below proves the guard fires before `conn` is ever
touched by passing a connection stand-in that raises on any attribute access.

The known-answer case (`test_curtailment_flips_mcnemar_significance_...`) reproduces,
via `fis_platform.stats.mcnemar_exact`, the measured fact the whole guard exists to
act on: the real R6 TEST composition (b=27, c=14) sits just above alpha=.05
(p=0.059584); dropping exactly the 16 cases (classes S11/S12) a curtailed Bonsai arm
would never have run turns discordant pair c=14 into c=11 and flips the SAME
underlying data across alpha=.05 (p=0.013853) — a conclusion change bought purely by
which cases got compared, not by any new evidence. The test then shows the guard
makes that comparison structurally unreachable once the hypothetical curtailment is
recorded, rather than merely flagging it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform import tolerances  # noqa: E402
from fis_platform.stats import mcnemar_exact  # noqa: E402
from fis_platform.tolerances import (  # noqa: E402
    CurtailedComparisonRefused,
    append_curtailed_run,
    make_curtailment_report,
    refuse_curtailed,
)
from scripts import r3b_selection_rule, r6_analysis, r6_metrics, routing_cascade_report  # noqa: E402

RUN_A = "R6-qwen38-q3km-test"   # the real frozen TEST arms (scripts/mstat_stats.py)
RUN_B = "R6-bonsai-test"

# The real R6 TEST discordant-pair counts and their known McNemar-exact p-values
# (scripts/mstat_stats.py._KNOWN_ANSWERS; verified re-derivation).
B_FULL, C_FULL = 27, 14
P_FULL_KNOWN = 0.059584
B_CURTAILED, C_CURTAILED = 27, 11
P_CURTAILED_KNOWN = 0.013853


def _bonsai_curtailment_report(run_id: str = RUN_B) -> dict:
    """The report a real Bonsai curtailment at case 80 would have written: 31 passes
    of 80 cases done, dropping the last 2 classes (S11, S12) of the 12-class design."""
    return make_curtailment_report(run_id, "test", "bonsai", passes=31, cases_done=80,
                                   n_total=96, bar=0.55, unrun_classes=["S11", "S12"])


# ---------------------------------------------------------------- refuse_curtailed

def test_refuse_curtailed_passes_when_ledger_file_is_missing(tmp_path):
    # A missing file reads as "nothing has ever curtailed" — pass, not an error.
    refuse_curtailed([RUN_A, RUN_B], path=tmp_path / "curtailed_runs.jsonl")


def test_refuse_curtailed_passes_when_ledger_does_not_name_the_runs(tmp_path):
    path = tmp_path / "curtailed_runs.jsonl"
    append_curtailed_run(path, make_curtailment_report("some-other-run", "dev", "arm",
                                                        3, 8, 10, 0.6, []))
    refuse_curtailed([RUN_A, RUN_B], path=path)  # neither RUN_A nor RUN_B is in the ledger


def test_refuse_curtailed_refuses_when_the_first_run_id_is_listed(tmp_path):
    path = tmp_path / "curtailed_runs.jsonl"
    append_curtailed_run(path, _bonsai_curtailment_report(run_id=RUN_A))
    with pytest.raises(CurtailedComparisonRefused) as exc_info:
        refuse_curtailed([RUN_A, RUN_B], path=path)
    assert exc_info.value.run_id == RUN_A
    assert RUN_A in str(exc_info.value)
    assert "guard 3" in str(exc_info.value) and "paired firewall" in str(exc_info.value)


def test_refuse_curtailed_refuses_when_the_second_run_id_is_listed(tmp_path):
    path = tmp_path / "curtailed_runs.jsonl"
    append_curtailed_run(path, _bonsai_curtailment_report(run_id=RUN_B))
    with pytest.raises(CurtailedComparisonRefused) as exc_info:
        refuse_curtailed([RUN_A, RUN_B], path=path)
    assert exc_info.value.run_id == RUN_B


def test_refuse_curtailed_default_path_honors_a_monkeypatched_constant(tmp_path, monkeypatch):
    """`refuse_curtailed`'s default resolves `CURTAILED_RUNS_PATH` INSIDE the function
    body, not as an early-bound parameter default — otherwise repointing the module
    constant (as this test, and every test that follows it, does) would be silently
    ignored by every call site that omits `path`, defeating the point of a default
    that is supposed to mean "the live ledger"."""
    redirected = tmp_path / "curtailed_runs.jsonl"
    monkeypatch.setattr(tolerances, "CURTAILED_RUNS_PATH", redirected)
    refuse_curtailed([RUN_A, RUN_B])  # no file yet at the redirected path -> passes
    append_curtailed_run(redirected, _bonsai_curtailment_report())
    with pytest.raises(CurtailedComparisonRefused):
        refuse_curtailed([RUN_A, RUN_B])  # now finds it via the redirected default


# ------------------------------------------------- known-answer historical case

def test_curtailment_flips_mcnemar_significance_and_the_firewall_refuses_it(tmp_path):
    # Reproduce the measured compositional flip on the real R6 TEST discordant counts.
    p_full = mcnemar_exact(B_FULL, C_FULL)
    p_curtailed = mcnemar_exact(B_CURTAILED, C_CURTAILED)
    assert p_full == pytest.approx(P_FULL_KNOWN, abs=1e-5)
    assert p_curtailed == pytest.approx(P_CURTAILED_KNOWN, abs=1e-5)
    # The SAME data (b=27 unchanged), same alpha — curtailment alone crosses it.
    assert p_full >= 0.05, "full composition should NOT be significant at alpha=.05"
    assert p_curtailed < 0.05, "curtailed composition SHOULD be significant at alpha=.05 " \
                               "-- purely from dropping S11/S12, not from new evidence"

    # Now: the hypothetical curtailed Bonsai arm gets recorded in the ledger, the way a
    # real runner would at the moment it actually curtails. The misleading comparison
    # above is exactly the one the firewall must make unreachable.
    ledger = tmp_path / "curtailed_runs.jsonl"
    append_curtailed_run(ledger, _bonsai_curtailment_report())
    with pytest.raises(CurtailedComparisonRefused) as exc_info:
        refuse_curtailed([RUN_A, RUN_B], path=ledger)
    assert exc_info.value.run_id == RUN_B


# --------------------------------------------------- integration: r6_metrics wiring

class _ExplodingConn:
    """A connection stand-in that raises on ANY attribute access. Standing in for a
    real `psycopg` connection in `pairwise_cmd`'s test proves the guard fires before
    even the first query is issued — not merely before the comparison is computed."""

    def __getattr__(self, name):
        raise AssertionError(
            f"DB access attempted via conn.{name!r} — refuse_curtailed should have "
            "raised before pairwise_cmd ever touched the connection"
        )


def test_r6_metrics_pairwise_cmd_refuses_before_any_db_access(tmp_path, monkeypatch):
    redirected = tmp_path / "curtailed_runs.jsonl"
    monkeypatch.setattr(tolerances, "CURTAILED_RUNS_PATH", redirected)
    append_curtailed_run(redirected, _bonsai_curtailment_report())

    with pytest.raises(CurtailedComparisonRefused) as exc_info:
        r6_metrics.pairwise_cmd(_ExplodingConn(), RUN_A, RUN_B)
    assert exc_info.value.run_id == RUN_B


def test_r6_metrics_pairwise_cmd_does_not_refuse_when_nothing_is_curtailed(tmp_path, monkeypatch):
    # No curtailment recorded -> refuse_curtailed passes, and pairwise_cmd proceeds to
    # touch conn (require_comparable's first query) -- proving the guard is not a
    # blanket refusal, only a refusal keyed on the ledger.
    monkeypatch.setattr(tolerances, "CURTAILED_RUNS_PATH", tmp_path / "curtailed_runs.jsonl")
    with pytest.raises(AssertionError, match="DB access attempted"):
        r6_metrics.pairwise_cmd(_ExplodingConn(), RUN_A, RUN_B)


# ------------------------------------------------ integration: the three FINDING-1 gaps
#
# r6_analysis.py, routing_cascade_report.py and r3b_selection_rule.py each resolve their
# run ids from argv and open their own `psycopg.connect(DSN)` inside `main()`, rather than
# going through a helper that already carries the guard (like r6_metrics.pairwise_cmd).
# Each test below drives the real CLI entry point (`main()`, via a monkeypatched argv) and
# proves the guard fires before `psycopg.connect` is ever called — the fake-`connect` seam
# is the `_ExplodingConn` idea applied one level up the call stack, since these scripts open
# the connection themselves rather than receiving one as an argument.

def _boom_connect(*_args, **_kwargs):
    raise AssertionError(
        "psycopg.connect attempted — refuse_curtailed should have raised before "
        "main() ever opened a DB connection"
    )


def test_r6_analysis_main_refuses_before_any_db_access(tmp_path, monkeypatch):
    redirected = tmp_path / "curtailed_runs.jsonl"
    monkeypatch.setattr(tolerances, "CURTAILED_RUNS_PATH", redirected)
    append_curtailed_run(redirected, _bonsai_curtailment_report(run_id=RUN_B))
    monkeypatch.setattr(r6_analysis.psycopg, "connect", _boom_connect)
    monkeypatch.setattr(
        sys, "argv",
        ["r6_analysis.py", "--split", "dev", "--arm", f"qwen={RUN_A}", "--strong", RUN_B],
    )
    with pytest.raises(CurtailedComparisonRefused) as exc_info:
        r6_analysis.main()
    assert exc_info.value.run_id == RUN_B


def test_routing_cascade_report_main_refuses_before_any_db_access(tmp_path, monkeypatch):
    redirected = tmp_path / "curtailed_runs.jsonl"
    monkeypatch.setattr(tolerances, "CURTAILED_RUNS_PATH", redirected)
    append_curtailed_run(redirected, _bonsai_curtailment_report(run_id=RUN_A))
    monkeypatch.setattr(routing_cascade_report.psycopg, "connect", _boom_connect)
    monkeypatch.setattr(
        sys, "argv",
        ["routing_cascade_report.py", "--weak", RUN_A, "--strong", RUN_B],
    )
    with pytest.raises(CurtailedComparisonRefused) as exc_info:
        routing_cascade_report.main()
    assert exc_info.value.run_id == RUN_A


def test_r3b_selection_rule_main_refuses_before_any_db_access(tmp_path, monkeypatch):
    # All of r3b_selection_rule's run-id args have defaults; naming the Nemotron
    # default in the curtailed ledger exercises the guard without passing any argv.
    redirected = tmp_path / "curtailed_runs.jsonl"
    monkeypatch.setattr(tolerances, "CURTAILED_RUNS_PATH", redirected)
    append_curtailed_run(redirected, _bonsai_curtailment_report(run_id="R3b-nemotron-dev"))
    monkeypatch.setattr(r3b_selection_rule.psycopg, "connect", _boom_connect)
    monkeypatch.setattr(sys, "argv", ["r3b_selection_rule.py"])
    with pytest.raises(CurtailedComparisonRefused) as exc_info:
        r3b_selection_rule.main()
    assert exc_info.value.run_id == "R3b-nemotron-dev"
