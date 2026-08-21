"""The TEST-look ledger: the single source of truth for TEST-look accounting.

TEST is spent, not merely observed. A held-out split loses its statistical validity the
moment a decision was made after seeing it — and "how many times has anyone looked"
turns out to be exactly the kind of fact a spreadsheet forgets under pressure. Before
this module, `docs/current/TEST_LOOK_LEDGER.md` was the only place that count lived,
hand-edited, with nothing in code that read or wrote it (M-STAT audit, item 7): a
frontier-arm TEST run could spend a look the markdown file would never learn about.

**Authority model (owner decision 2026-08-21; playbook §1;
`docs/current/TEST_LOOK_LEDGER.md` header):** this module's file —
`learning/registry/test_looks.jsonl` — is the record of record. The markdown table is
its generated / mechanically validated human-readable mirror; divergence between them
fails validation (`validate_mirror`). Every TEST execution path, local or frontier, must
consult `require_planned` fail-closed before running a single case, and a look is spent
at the *first executed case*, not the last (playbook §1) — `record_spend` is what a
runner calls there.

Ledger shape, in the style of `provenance.py`'s `state.jsonl` (not the pydantic
`_Record` pattern — a look is a fact about accounting, not an artifact with derived
identity fields): one JSONL file, hash-chained. Every entry is
`{seq, prev_entry_digest, kind, ...kind-specific fields..., entry_digest}`; `seq` runs
1..n with no gaps, `prev_entry_digest` must equal the previous entry's `entry_digest`,
and `entry_digest` is `fis_platform.routing.learn.digest()` (§13's canonical-JSON
sha256) over the entry with `entry_digest` itself removed. `read()` recomputes and
checks all three on every call, so an edited line is caught the instant anything reads
the ledger.

Three entry kinds:

  `historical`  the seven Suite-v3 looks that predate this ledger, backfilled once by
                `seed()` from `docs/current/TEST_LOOK_LEDGER.md`'s table, verbatim — no
                reinterpretation of a decision already made.
  `planned`     appended at contract-freeze time (`plan_look`): a look_no is reserved
                for one run_id, by a named authorizer. Suite v3 look #8 and beyond
                additionally require `trigger_review_ref` to name a real, currently
                existing file — the Suite-v4 refresh-trigger review (owner decision
                2026-08-21 §0.3: M-STAT ships the gate, never performs the review).
  `spent`       appended by the runner at the first executed case (`record_spend`),
                referencing the planned entry it spends. Idempotent for its own run_id
                (a crashed-and-resumed run must not be refused for reporting the spend
                it already recorded); refused for any other run_id once a look_no is
                spent.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fis_platform.routing.learn import digest
from fis_platform.suite import git_head

__all__ = [
    "HISTORICAL_SUITE_VERSION",
    "LedgerIntegrityError",
    "LookRefused",
    "MirrorDivergence",
    "TestLookLedger",
    "default_markdown_path",
    "default_path",
    "validate_mirror",
]

_ROOT = Path(__file__).resolve().parents[1]

# The look_no at and beyond which Suite v3 requires the Suite-v4 trigger review
# (playbook §1: "Look #8 requires the Suite-v4 trigger review first").
TRIGGER_REVIEW_FLOOR = 8
HISTORICAL_SUITE_VERSION = "3"

MIRROR_SOURCE = "docs/current/TEST_LOOK_LEDGER.md backfill"

# The seven Suite-v3 looks, copied verbatim from docs/current/TEST_LOOK_LEDGER.md's
# table (owner decision 2026-08-21: seeded faithfully, no reinterpretation of a
# decision already made). Order is the ledger order — dates 2026-08-17/17/17/18/18/19/19.
_HISTORICAL_LOOKS: tuple[dict[str, Any], ...] = (
    {"look_no": 1, "date": "2026-08-17", "experiment": "Suite v3 baselines",
     "arm_run": "Qwen3-8B V3-qwen-96", "cases": 96, "look_kind": "execution"},
    {"look_no": 2, "date": "2026-08-17", "experiment": "Suite v3 baselines",
     "arm_run": "Nemotron V3-nemotron-96", "cases": 96, "look_kind": "execution"},
    {"look_no": 3, "date": "2026-08-17", "experiment": "Suite v3 baselines",
     "arm_run": "frontier E4-v3-96", "cases": 96, "look_kind": "execution"},
    {"look_no": 4, "date": "2026-08-18", "experiment": "R5 learned routing",
     "arm_run": "Qwen tree policy (offline replay)", "cases": 96, "look_kind": "replay"},
    {"look_no": 5, "date": "2026-08-18", "experiment": "R5 learned routing",
     "arm_run": "Nemotron lr_core policy (offline replay)", "cases": 96, "look_kind": "replay"},
    {"look_no": 6, "date": "2026-08-19", "experiment": "R6 refresh",
     "arm_run": "Qwen3.8-27B Q3_K_M qwen38-27b-q3km", "cases": 96, "look_kind": "execution"},
    {"look_no": 7, "date": "2026-08-19", "experiment": "R6 refresh",
     "arm_run": "Bonsai-27B bonsai-27b", "cases": 96, "look_kind": "execution"},
)


def _now() -> str:
    """UTC, seconds resolution — the precision every other R-series record uses."""
    return datetime.now(UTC).isoformat(timespec="seconds")


class LookRefused(SystemExit):
    """A guard on TEST-look accounting said no: an unplanned run, a look out of
    sequence, a double-plan of the same look_no, a duplicate run_id, or a Suite-v3
    look #8+ with no valid trigger-review reference. The ledger is left unchanged —
    every guard here runs before `_append`, never after."""


class LedgerIntegrityError(SystemExit):
    """The chain does not verify: a line is not JSON, `seq` has a gap, `prev_entry_digest`
    does not match, or an entry's content no longer digests to its own `entry_digest`.
    Read paths fail closed on it, exactly like `R6Registry.read_state`."""


class MirrorDivergence(SystemExit):
    """`docs/current/TEST_LOOK_LEDGER.md` disagrees with the machine ledger, or is
    missing a row the machine ledger already has. The machine ledger is authoritative
    (owner decision 2026-08-21; playbook §1) — this exists so that disagreement is a
    refusal, not a fact two files quietly hold differently forever."""


def _append_line(path: Path, obj: dict[str, Any]) -> None:
    """The only writer of `test_looks.jsonl`. Opens "a" — never truncates, never
    rewrites a line already there (same discipline as `provenance.py`'s `_append_line`,
    reimplemented locally so this ledger owns its own write path end to end)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, sort_keys=True) + "\n")


def _repo_path(ref: str) -> Path:
    """`ref` resolved against the repo root when relative. `trigger_review_ref` names a
    file "in the repo" (playbook §1), not a path relative to whatever directory a
    runner or test happens to be invoked from."""
    p = Path(ref)
    return p if p.is_absolute() else _ROOT / p


def _require_trigger_review(suite_version: str, look_no: int, trigger_review_ref: str | None) -> None:
    """Suite v3 look #8+ needs a non-empty `trigger_review_ref` naming a file that
    exists in the repo *right now* (playbook §1; owner decision 2026-08-21 §0.3:
    M-STAT implements only this gate, never the review itself). Called from both
    `plan_look` and `require_planned` — re-checked at consumption time, not just at
    plan time, so a review doc deleted or renamed after planning still blocks the run
    instead of a stale reference quietly surviving in a frozen payload."""
    if suite_version != HISTORICAL_SUITE_VERSION or look_no < TRIGGER_REVIEW_FLOOR:
        return
    if not trigger_review_ref or not trigger_review_ref.strip():
        raise LookRefused(
            f"look #{look_no} on suite {suite_version!r} needs a trigger_review_ref (the "
            "Suite-v4 refresh-trigger review, playbook §1) and none was given")
    resolved = _repo_path(trigger_review_ref)
    if not resolved.exists():
        raise LookRefused(
            f"look #{look_no} on suite {suite_version!r}: trigger_review_ref "
            f"{trigger_review_ref!r} does not name an existing file (resolved to {resolved})")


class TestLookLedger:
    """The machine append-only, hash-chained TEST-look ledger at `path`.

    `path` is an explicit constructor argument, never a default that reaches outside
    the caller's control (`R6Registry(root)`'s discipline) — the live ledger is
    `default_path()` and nothing else, so a ledger built under `tmp_path` in a test can
    never be confused with it.
    """

    __test__ = False   # pytest: this is a ledger, not a test class — the name just starts with "Test"

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    # ---------------------------------------------------------------- read + verify
    def read(self) -> list[dict[str, Any]]:
        """The verified chain: every entry's `entry_digest` is recomputed, every
        `prev_entry_digest` must match the previous entry, and `seq` must be 1..n with
        no gaps. A ledger that does not exist reads as `[]` here — "no file yet" and
        "file exists but fails to verify" are different failures, and callers that must
        fail closed on a missing file (`require_planned`) check for it themselves,
        because what a missing ledger means depends on who is asking.
        """
        if not self.path.exists():
            return []
        lines = [ln for ln in self.path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        entries: list[dict[str, Any]] = []
        prev = ""
        for i, ln in enumerate(lines, start=1):
            try:
                e = json.loads(ln)
            except json.JSONDecodeError as exc:
                raise LedgerIntegrityError(f"{self.path}: line {i} is not valid JSON: {exc}") from exc
            if e.get("seq") != i:
                raise LedgerIntegrityError(
                    f"{self.path}: entry {i} claims seq {e.get('seq')!r} — the log has a gap")
            if e.get("prev_entry_digest") != prev:
                raise LedgerIntegrityError(
                    f"{self.path}: entry seq {i} chains to "
                    f"{str(e.get('prev_entry_digest'))[:12]}… but seq {i - 1} digests to "
                    f"{prev[:12] or '(genesis)'}… — the log was rewritten")
            body = {k: v for k, v in e.items() if k != "entry_digest"}
            recomputed = digest(body)
            if recomputed != e.get("entry_digest"):
                raise LedgerIntegrityError(
                    f"{self.path}: entry seq {i} digests to {recomputed[:12]}… but records "
                    f"{str(e.get('entry_digest'))[:12]}… — the entry was edited")
            prev = e["entry_digest"]
            entries.append(e)
        return entries

    def _append(self, kind: str, fields: dict[str, Any]) -> dict[str, Any]:
        entries = self.read()
        entry = {
            "seq": len(entries) + 1,
            "prev_entry_digest": entries[-1]["entry_digest"] if entries else "",
            "kind": kind,
            **fields,
        }
        entry["entry_digest"] = digest(entry)
        _append_line(self.path, entry)
        return entry

    # ---------------------------------------------------------------- seed
    def seed(self) -> list[dict[str, Any]]:
        """Create the ledger with the seven historical Suite-v3 looks, faithfully
        (owner decision 2026-08-21) — no reinterpretation. Refuses if the file already
        exists: reseeding a live ledger would either duplicate history (naive append)
        or silently no-op (guard against dupes), and both hide a mistake better caught
        by a human deciding what "the file is already there" means before anything
        writes."""
        if self.path.exists():
            raise LookRefused(
                f"{self.path} already exists — seed refuses to touch a live ledger; "
                "move it aside first if a reseed is really intended")
        written = []
        for look in _HISTORICAL_LOOKS:
            fields = {**look, "suite_version": HISTORICAL_SUITE_VERSION, "source": MIRROR_SOURCE}
            written.append(self._append("historical", fields))
        return written

    # ---------------------------------------------------------------- accounting
    def next_look_no(self, suite_version: str) -> int:
        """1 + the highest `look_no` any entry — historical, planned, or spent — has
        used for `suite_version`. The single place "what look comes next" is computed,
        so `plan_look`'s sequencing guard and a human asking "what's next" can never
        disagree, and planning a look_no a second time is refused by the same
        mechanism that enforces sequencing: once #8 is planned, the next look for
        suite 3 is #9, never #8 again."""
        nos = [e["look_no"] for e in self.read() if e.get("suite_version") == suite_version]
        return max(nos, default=0) + 1

    def is_spent(self, run_id: str) -> bool:
        return any(e["kind"] == "spent" and e["run_id"] == run_id for e in self.read())

    def plan_look(self, *, look_no: int, suite_version: str, experiment: str, arm: str,
                 run_id: str, authorized_by: str, trigger_review_ref: str | None = None,
                 planned_at: str | None = None, code_commit: str | None = None) -> dict[str, Any]:
        """Append a planned look at contract-freeze time. Fail-closed guards, in order:

          1. `look_no` must equal `next_look_no(suite_version)` — sequential, and (see
             `next_look_no`) this is also the no-double-planning guard;
          2. `authorized_by` must be non-empty — a look nobody is named as authorizing
             is not a plan, it is a guess;
          3. Suite v3 look #8+ needs a `trigger_review_ref` naming a file that exists
             right now (`_require_trigger_review`);
          4. `run_id` must not already appear anywhere in the ledger — one run_id, one
             look, ever.
        """
        entries = self.read()
        expected = self.next_look_no(suite_version)
        if look_no != expected:
            raise LookRefused(
                f"look_no {look_no} is not the next look for suite {suite_version!r} "
                f"(expected {expected}) — refusing to plan out of sequence")
        if not authorized_by or not authorized_by.strip():
            raise LookRefused("plan_look needs a non-empty authorized_by")
        _require_trigger_review(suite_version, look_no, trigger_review_ref)
        if any(e["kind"] in ("planned", "spent") and e.get("run_id") == run_id for e in entries):
            raise LookRefused(f"run_id {run_id!r} is already in the TEST-look ledger — "
                              "one run_id, one look")
        fields = {
            "look_no": look_no, "suite_version": suite_version, "experiment": experiment,
            "arm": arm, "run_id": run_id, "authorized_by": authorized_by,
            "trigger_review_ref": trigger_review_ref,
            "planned_at": planned_at or _now(),
            "code_commit": code_commit if code_commit is not None else git_head(),
        }
        return self._append("planned", fields)

    def record_spend(self, run_id: str, first_scenario_id: str, *,
                     spent_at: str | None = None, code_commit: str | None = None) -> dict[str, Any]:
        """Append the spend at the FIRST executed case (playbook §1: a split is spent
        at the first executed case, not the last). Idempotent for `run_id`: a runner
        that crashes right after spending and resumes must be able to call this again
        with the same run_id and get the existing entry back, not a refusal. A second
        spend of the same `look_no` under a DIFFERENT run_id is refused — that would be
        two runs claiming to have spent the same look."""
        entries = self.read()
        planned = next((e for e in entries if e["kind"] == "planned" and e["run_id"] == run_id), None)
        if planned is None:
            raise LookRefused(f"run_id {run_id!r} has no planned TEST look — spend refused "
                              "(fail closed: no plan, no TEST)")
        existing = next((e for e in entries
                         if e["kind"] == "spent" and e["look_no"] == planned["look_no"]), None)
        if existing is not None:
            if existing["run_id"] != run_id:
                raise LookRefused(
                    f"look #{planned['look_no']} was already spent by run_id "
                    f"{existing['run_id']!r} — refusing a second spend under {run_id!r}")
            return existing               # same run_id: resume, not a second spend
        fields = {
            "look_no": planned["look_no"], "run_id": run_id,
            "suite_version": planned["suite_version"], "first_scenario_id": first_scenario_id,
            "spent_at": spent_at or _now(),
            "code_commit": code_commit if code_commit is not None else git_head(),
        }
        return self._append("spent", fields)

    def require_planned(self, suite_version: str, run_id: str) -> dict[str, Any]:
        """The planned entry a TEST run must exist against before any case executes.
        Fail-closed on three things: no ledger file at all ("no ledger, no TEST"), no
        planned entry for this `(suite_version, run_id)`, or — re-checked here, not
        only at plan time — a Suite-v3 look #8+ whose `trigger_review_ref` no longer
        names a real file. The runner's TEST gate calls this before the first case, so
        silent divergence between "what was planned" and "what is true right now" is
        impossible.
        """
        if not self.path.exists():
            raise LookRefused(f"no TEST-look ledger at {self.path} — fail closed: no ledger, no TEST")
        planned = next((e for e in self.read()
                        if e["kind"] == "planned" and e["suite_version"] == suite_version
                        and e["run_id"] == run_id), None)
        if planned is None:
            raise LookRefused(f"no planned TEST look for run_id {run_id!r} on suite "
                              f"{suite_version!r} — TEST refused until a look is planned")
        _require_trigger_review(suite_version, planned["look_no"], planned["trigger_review_ref"])
        return planned


# ------------------------------------------------------------------------ mirror

_MD_ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*$")
_MD_KIND_RE = re.compile(r"^(execution|replay)\b")


def _parse_markdown_rows(markdown_path: Path) -> dict[int, dict[str, Any]]:
    """The `| # | Date | Experiment | Arm / run | Cases | Kind |` table of
    `TEST_LOOK_LEDGER.md`, keyed by look_no. The Kind cell may carry a trailing prose
    note (row #3's R4-replay aside); only the leading `execution`/`replay` token is
    data — the rest is a human annotation, not part of what this validates."""
    if not markdown_path.exists():
        raise MirrorDivergence(f"no markdown mirror at {markdown_path}")
    rows: dict[int, dict[str, Any]] = {}
    for line in markdown_path.read_text(encoding="utf-8").splitlines():
        m = _MD_ROW_RE.match(line.strip())
        if not m:
            continue
        look_no_s, date, _experiment, _arm, cases_s, kind_cell = m.groups()
        km = _MD_KIND_RE.match(kind_cell.strip())
        if not km:
            continue          # header ("# | Date | ...") and separator ("---") rows land here too
        rows[int(look_no_s)] = {"date": date.strip(), "cases": int(cases_s), "kind": km.group(1)}
    return rows


def validate_mirror(ledger_path: Path, markdown_path: Path) -> None:
    """The machine ledger is authoritative (owner decision 2026-08-21; playbook §1), so
    this only ever fails in the direction of "the mirror disagrees" or "the mirror is
    missing a row the machine already has" — never the reverse. Two checks:

      * every markdown row's look_no must have SOME machine counterpart (any kind —
        a planned or spent look #8+ satisfies a future mirror row for it, once a human
        adds one);
      * every `historical` machine entry must have a markdown row at its look_no, and
        that row's date/cases/kind must match exactly.

    Planned/spent machine entries with no markdown row yet are fine — the mirror is
    updated by humans/tools later, after the machine ledger already moved (playbook
    §1). Raises `MirrorDivergence` on any disagreement; returns `None` otherwise.
    """
    entries = TestLookLedger(ledger_path).read()
    md_rows = _parse_markdown_rows(markdown_path)
    machine_look_nos = {e["look_no"] for e in entries if "look_no" in e}

    for look_no in md_rows:
        if look_no not in machine_look_nos:
            raise MirrorDivergence(
                f"{markdown_path}: row #{look_no} has no counterpart in {ledger_path}")

    for e in entries:
        if e["kind"] != "historical":
            continue
        look_no = e["look_no"]
        md = md_rows.get(look_no)
        if md is None:
            raise MirrorDivergence(
                f"{ledger_path}: historical look #{look_no} has no row in {markdown_path}")
        machine = {"date": e["date"], "cases": e["cases"], "kind": e["look_kind"]}
        if machine != md:
            raise MirrorDivergence(
                f"{markdown_path} row #{look_no} disagrees with {ledger_path}: "
                f"machine={machine} mirror={md}")


def default_path() -> Path:
    """`<repo>/learning/registry/test_looks.jsonl` — the canonical ledger, named in
    exactly one place. No environment variable relocates it, matching
    `provenance.default_root()`'s reasoning: a relocatable ledger is a reset button
    with extra steps. Tests construct `TestLookLedger(tmp_path / "...")` explicitly."""
    return _ROOT / "learning" / "registry" / "test_looks.jsonl"


def default_markdown_path() -> Path:
    """`<repo>/docs/current/TEST_LOOK_LEDGER.md` — the human-readable mirror `verify`
    checks the ledger against."""
    return _ROOT / "docs" / "current" / "TEST_LOOK_LEDGER.md"
