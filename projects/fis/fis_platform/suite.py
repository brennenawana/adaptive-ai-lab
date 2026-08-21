"""Suite identity — the one place the benchmark's version is defined.

`SUITE_VERSION` names the corpus + tool contract + scorer + verifier a score was
measured against. Every manifest the generator writes and every score row the runner
persists carries it, and every tool that pairs two runs checks it, because scenario
ids are seed-derived and therefore IDENTICAL across suite versions: without the
column, a v2 score row silently joins a v3 manifest and a v2 rate silently sits next
to a v3 rate in the same table (`SUITE_V3_RELEASE_CONTRACT.md` § 2E).

Bumping this is a breaking change to the eval suite (`task-ontology.md` § 6): the
corpus is regenerated, `make reachability` is run, and nothing from the previous
version is compared to anything from the new one without saying so.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

SUITE_VERSION = "3"

# Root-cause set, action set and cause->action mapping. Unchanged since suite v1 —
# suite bumps so far were corpus/tool/scorer/verifier changes, not ontology changes.
ONTOLOGY_VERSION = "1"

# Runs scored before suite identity was persisted (migration 006 backfills these as
# suite 1; every other pre-006 row is suite 2). Kept here so the list lives with the
# constant it explains, and so `compare.py` no longer needs its own copy.
SUITE_V1_RUNS = frozenset({
    "E2-local-96", "E2-local-specialist-test", "E4-claude-frontier-test",
    "SMOKE-local-specialist-dev",
})

_ROOT = Path(__file__).resolve().parents[1]


def git_head() -> str:
    """`<short sha>` or `<short sha>-dirty`; empty string if git is unavailable.
    Telemetry only — recorded on every trajectory's runtime_context so a run can be
    tied to the code that produced it without reading prose."""
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=_ROOT,
                             capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                               cwd=_ROOT, capture_output=True, text=True, timeout=5,
                               check=True).stdout.strip()
        return f"{sha}-dirty" if dirty else sha
    except Exception:  # noqa: BLE001 — telemetry only
        return ""


class SuiteMismatch(SystemExit):
    """Raised (as a clean exit) when a tool is asked to mix suite versions."""


def suite_of_run(conn, run_id: str) -> str | None:
    """The suite version every persisted score of `run_id` carries; None if the run
    has no rows. A run whose rows disagree is corrupt and is refused outright."""
    rows = conn.execute(
        "SELECT DISTINCT suite_version FROM learning.case_scores WHERE run_id = %s",
        (run_id,),
    ).fetchall()
    versions = sorted({r[0] for r in rows}, key=lambda v: (v is None, v))
    if not versions:
        return None
    if len(versions) > 1:
        raise SuiteMismatch(f"run {run_id!r} mixes suite versions {versions} — refusing to read it")
    return versions[0]


def corpus_suite(conn) -> str | None:
    """The suite version the manifests in the database were generated for."""
    rows = conn.execute(
        "SELECT DISTINCT suite_version FROM ground_truth.scenario_manifests"
    ).fetchall()
    versions = sorted({r[0] for r in rows}, key=lambda v: (v is None, v))
    if not versions:
        return None
    if len(versions) > 1:
        raise SuiteMismatch(f"the corpus mixes suite versions {versions} — regenerate with --reset")
    return versions[0]


def require_comparable(conn, run_ids: list[str], *, allow_cross_suite: bool = False,
                       against_corpus: bool = True) -> dict[str, str | None]:
    """Refuse to pair runs from different suites, or to read a run against a corpus
    of a different suite, unless the caller explicitly opted in — in which case the
    caveat is printed so it lands in the transcript next to the numbers.

    `against_corpus` is True for tools that join `ground_truth.scenario_manifests`
    (root cause, category, split come from the CURRENT corpus, which is only the
    corpus those scores were measured against if the suite matches).
    """
    suites = {rid: suite_of_run(conn, rid) for rid in run_ids}
    problems = []
    distinct = {s for s in suites.values() if s is not None}
    if len(distinct) > 1:
        problems.append(f"runs span suite versions {dict(sorted(suites.items()))}")
    if against_corpus:
        corpus = corpus_suite(conn)
        stale = {rid: s for rid, s in suites.items() if s is not None and s != corpus}
        if stale:
            problems.append(f"corpus is suite {corpus!r} but {stale} were scored on another suite "
                            "— their manifests (root cause, category) would come from a corpus "
                            "they were never measured against")
    if problems:
        msg = "; ".join(problems)
        if not allow_cross_suite:
            raise SuiteMismatch(
                f"NOT COMPARABLE: {msg}. Cross-suite numbers answer different questions and "
                "must not be subtracted; pass --allow-cross-suite to proceed with the caveat printed."
            )
        print(f"!! CROSS-SUITE COMPARISON ({msg}). Read the numbers as structural, not causal.\n")
    return suites
