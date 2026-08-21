"""Consequence-bearing tolerances + certainty curtailment (playbook §5, §6; M-STAT
implementation map items 1 and 11; `playbook/examples/CASE-001_consequence-bearing-
tolerances.md`).

R6's cap-calibration tolerance was pre-registered, was measured breaching 5x
(15/36 cap-hits against a <=3/36 bar), and its own written escape hatch said
"freeze the ceiling cap and record the rate" — so the milestone proceeded through
DEV and TEST on a configuration everyone could see was truncating, and nobody had
to write down the 9h55m of zero-scoring generation that cost before it was spent.
Detection was never the gap; the tolerance had no consequence attached. This module
is the fix: a tolerance is not allowed to resolve into a silent default. It must
resolve into one of three named, pre-registered outcomes (`Consequence`), and the
runner enforces that fail-closed, in the same style as the existing execution-system
`--candidate` refusal.

Part A — `ToleranceSpec` / `ToleranceTracker` / `ConsequenceAction`: curtailed exact
counting against a pre-registered tolerance ``<= k violations of n``. This is
DELIBERATELY NOT a hypothesis test: no SPRT, no error-rate claim. SPRT was measured
(research 2026-08-20 §2.2) to inflate its nominal 5% error to ~11% under this
project's class-clustered violation sequences (ICC 0.398), and count-to-k dominated
it on the real pilot data. `ToleranceTracker` counts exactly to `max_violations + 1`
and dispatches the registered consequence exactly once when it gets there — no
distributional assumption, nothing "significant", just an integer crossing a
pre-registered integer.

Part B — `CurtailmentPolicy` / certainty curtailment (playbook §6): abort a DEV/TEST
arm the instant its remaining cases cannot possibly reach the pre-registered pass
bar — `passes + cases_remaining < ceil(bar * n_total)` — with three guards enforced
by shape rather than by caller discipline:

  guard 1 (spend semantics)   curtailment's only admissible outcome is irreversible
                              rejection of the arm — the split is already spent, so
                              there is no "curtail now, finish later".
  guard 2 (interval-only)     `make_curtailment_report` has no point-estimate field.
                              A curtailed arm reports the CERTAIN interval
                              `[passes, passes+remaining]/N` plus its unrun classes —
                              never a rate, because a rate implies the unrun cases
                              would have gone the observed way, which is exactly the
                              assumption curtailment was invoked to avoid making.
  guard 3 (paired firewall)   `refuse_curtailed` reads the curtailed-runs ledger this
                              module's append/read helpers write and read, and is the
                              one check every PAIRED entry point calls on its run ids
                              before any computation or DB query — measured: curtailing
                              flips a McNemar p from 0.0596 to 0.0139 purely
                              compositionally when a curtailed arm is let into a paired
                              comparison. The full set of guarded entry points:

                                `scripts/r6_metrics.py`            pairwise_cmd, and the
                                                                    oracle/tiers/gates
                                                                    CLI subcommands
                                `scripts/r6_analysis.py`            arm run ids, before
                                                                    pairwise/
                                                                    post_answer_oracle/
                                                                    dominance_matrix
                                `scripts/routing_cascade_report.py` weak/strong/cascade
                                                                    run ids, before the
                                                                    paired oracle cells
                                `scripts/r3b_selection_rule.py`     all five compared run
                                                                    ids, before the
                                                                    cell-B regression
                                                                    logic
                                `scripts/compare_routes.py`         --a/--b
                                `scripts/model_migration_matrix.py` incumbent/candidate/
                                                                    strong
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from fis_platform.provenance import digest

_ROOT = Path(__file__).resolve().parents[1]

# The one place the live curtailed-runs ledger location is named (the `predictions.
# DEFAULT_LEDGER_PATH` pattern). No environment variable, no CLI flag that relocates
# it — a ledger the paired-comparison firewall reads from a caller-chosen location is
# a bypass, not a guard.
CURTAILED_RUNS_PATH = _ROOT / "learning" / "registry" / "curtailed_runs.jsonl"

__all__ = [
    "CURTAILED_RUNS_PATH",
    "Consequence",
    "ConsequenceAction",
    "CurtailedComparisonRefused",
    "CurtailmentPolicy",
    "ToleranceBreach",
    "ToleranceSpec",
    "ToleranceTracker",
    "append_curtailed_run",
    "make_curtailment_report",
    "read_curtailed_runs",
    "refuse_curtailed",
]


# --------------------------------------------------------------- Part A: tolerances

class Consequence(str, Enum):
    """The only three legal resolutions of a breached tolerance (playbook §5). There
    is deliberately no fourth "record and proceed" member — that silent default is
    the R6 defect this module exists to close."""

    ABORT = "ABORT"
    RECALIBRATE = "RECALIBRATE"
    PROCEED_WITH_DECLARED_CEILING = "PROCEED_WITH_DECLARED_CEILING"


class ToleranceSpec(BaseModel):
    """One pre-registered tolerance: at most `max_violations` violations of
    `metric` in `denominator_n` cases, before `consequence` fires.

    A tolerance with no consequence is unrepresentable BY TYPE (`consequence` is a
    required `Consequence` field, not `Consequence | None`) — there is no
    constructor call that produces an unpriced escape hatch. The two consequences
    that need extra commitment before they can be chosen are validated fail-closed
    at construction, not deferred to breach time, so a contract cannot freeze with
    a promise it has not actually written down yet:

      RECALIBRATE   requires a non-empty `recalibration_procedure` — only a
                    PRE-REGISTERED procedure may be invoked; "we'll figure out a
                    new cap" is not a procedure.
      PROCEED_WITH_DECLARED_CEILING
                    requires BOTH a non-empty `declared_ceiling` and a non-empty
                    `projected_cost` — the exact pair R6's escape hatch omitted.
                    "No unpriced escape hatches" is the rule this enforces.

    `spec_digest` is a computed property (digest over the model's own JSON dump, the
    `PassKSpec.spec_digest` / `predictions.py` pattern) rather than a stored
    self-referential field: a stored digest would need to exclude itself from its
    own preimage, so it is simpler to compute fresh every time and never risk it
    going stale.
    """

    model_config = ConfigDict(extra="forbid")

    spec_id: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    description: str = Field(min_length=1)
    denominator_n: int = Field(gt=0)
    max_violations: int = Field(ge=0)
    consequence: Consequence
    recalibration_procedure: str | None = None
    declared_ceiling: str | None = None
    projected_cost: str | None = None

    @model_validator(mode="after")
    def _consequence_commitments(self) -> ToleranceSpec:
        if self.consequence is Consequence.RECALIBRATE:
            if not (self.recalibration_procedure or "").strip():
                raise ValueError(
                    f"tolerance {self.spec_id!r}: consequence RECALIBRATE requires a "
                    "non-empty recalibration_procedure — only a pre-registered "
                    "procedure may be invoked, never an ad-hoc one chosen at breach time"
                )
        elif self.consequence is Consequence.PROCEED_WITH_DECLARED_CEILING:
            missing = [name for name, value in (
                ("declared_ceiling", self.declared_ceiling),
                ("projected_cost", self.projected_cost),
            ) if not (value or "").strip()]
            if missing:
                raise ValueError(
                    f"tolerance {self.spec_id!r}: consequence PROCEED_WITH_DECLARED_CEILING "
                    f"requires non-empty {missing} — no unpriced escape hatches (the R6 "
                    "defect: '5x cap-hit breach, escape hatch said proceed, unpriced, "
                    "9h55m of zero-scoring generation followed')"
                )
        return self

    @property
    def spec_digest(self) -> str:
        return digest(self.model_dump(mode="json"))


class ToleranceBreach(SystemExit):
    """Raised by `ToleranceTracker.observe` when called again after an ABORT
    consequence has already been dispatched. ABORT means the run halted and
    returned to design (playbook §5) — there is structurally no such thing as "one
    more observation" after that, so the tracker refuses rather than silently
    keep counting past a run that, by the contract's own rule, no longer exists.

    Carries `spec` and `count` (the violation count at breach) so a caller that
    catches this for cleanup/logging does not have to re-derive them.
    """

    def __init__(self, spec: ToleranceSpec, count: int) -> None:
        self.spec = spec
        self.count = count
        super().__init__(
            f"tolerance {spec.spec_id!r} already breached at {count} violation(s) "
            f"of a <={spec.max_violations} bar (consequence {spec.consequence.value} "
            "already dispatched) — ABORT prevents continuation structurally; "
            "refusing further observe()"
        )


class ToleranceTracker:
    """Curtailed exact counting against a pre-registered `ToleranceSpec`.

    NOT a hypothesis test — see the module docstring. `observe(is_violation)` is
    called once per case; it returns `None` on every call except the ONE call where
    the violation count crosses from `<= max_violations` to `max_violations + 1`,
    on which it returns `spec.consequence` (returned exactly once, never again,
    because the crossing itself can only happen once for a monotonically
    increasing counter).

    After that crossing, further behavior depends on which consequence fired:
      ABORT                              any further `observe()` raises
                                          `ToleranceBreach` — the run halted.
      RECALIBRATE / PROCEED_WITH_..._CEILING
                                          the run is licensed to continue (under the
                                          registered procedure / declared ceiling),
                                          so further `observe()` calls are legal —
                                          they just never return the consequence a
                                          second time.
    """

    def __init__(self, spec: ToleranceSpec) -> None:
        self.spec = spec
        self.violations = 0
        self.cases_observed = 0
        # (violations, cases_observed) at the instant the consequence dispatched —
        # frozen there so `to_consequence_action` reports WHEN it fired even if
        # `observe` is (legally, for RECALIBRATE/PROCEED) called many more times
        # afterward.
        self._breach_snapshot: tuple[int, int] | None = None

    @property
    def breached(self) -> bool:
        """True once the violation count has crossed `max_violations` — i.e. the
        (k+1)-th violation has been observed."""
        return self.violations > self.spec.max_violations

    @property
    def aborted(self) -> bool:
        """True once breached AND the registered consequence is ABORT — the state
        that makes further `observe()` illegal."""
        return self.breached and self.spec.consequence is Consequence.ABORT

    def observe(self, is_violation: bool) -> Consequence | None:
        """Record one case's outcome. Returns the consequence exactly once, on the
        call whose violation count first exceeds `max_violations`; `None` on every
        other call. Raises `ToleranceBreach` if called after ABORT already fired."""
        if self.aborted:
            raise ToleranceBreach(self.spec, self.violations)
        was_breached = self.breached
        self.cases_observed += 1
        if is_violation:
            self.violations += 1
        if not was_breached and self.breached:
            self._breach_snapshot = (self.violations, self.cases_observed)
            return self.spec.consequence
        return None

    @classmethod
    def from_persisted(
        cls, spec: ToleranceSpec, violations_iterable: Any,
    ) -> ToleranceTracker:
        """Reconstruct tracker state from already-persisted case outcomes (the
        resume path: a run restarted mid-phase reads its own recorded rows back
        instead of re-deciding from nothing).

        Replays each recorded outcome through `observe`, in order — so a tracker
        built from a persisted prefix that already crossed the tolerance is BORN
        breached (and, for ABORT, born aborted): reconstructing it is exactly as
        strict as living through it would have been. If the persisted prefix
        somehow contains rows recorded after an ABORT crossing (which should never
        happen structurally, since ABORT halts the run), replay raises
        `ToleranceBreach` on the first such row rather than silently accepting it.
        """
        tracker = cls(spec)
        for is_violation in violations_iterable:
            tracker.observe(bool(is_violation))
        return tracker

    def to_consequence_action(self) -> ConsequenceAction:
        """The `ConsequenceAction` record for what this tracker decided, for the
        runner to persist to events/ledger. `at_violation`/`cases_observed` report
        the snapshot taken AT the moment the consequence dispatched — not whatever
        `self.violations`/`self.cases_observed` have grown to since, if `observe`
        was legally called again afterward (RECALIBRATE / PROCEED). Refuses if the
        tracker has not breached — there is nothing to record yet."""
        if self._breach_snapshot is None:
            raise ValueError(
                f"tolerance {self.spec.spec_id!r} has not breached "
                f"({self.violations} of a <={self.spec.max_violations} bar) — "
                "nothing to record"
            )
        at_violation, cases_observed = self._breach_snapshot
        return ConsequenceAction(
            spec_id=self.spec.spec_id,
            spec_digest=self.spec.spec_digest,
            consequence=self.spec.consequence,
            at_violation=at_violation,
            cases_observed=cases_observed,
            declared_ceiling=self.spec.declared_ceiling,
            projected_cost=self.spec.projected_cost,
            recalibration_procedure=self.spec.recalibration_procedure,
        )


class ConsequenceAction(BaseModel):
    """What actually happened when a tolerance breached — the record the runner
    writes to events/ledger. `spec_digest` is carried alongside `spec_id` so a
    later reader can tell whether the spec that fired is the same one that was
    frozen, without a registry lookup."""

    model_config = ConfigDict(extra="forbid")

    spec_id: str = Field(min_length=1)
    spec_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    consequence: Consequence
    at_violation: int = Field(gt=0)
    cases_observed: int = Field(ge=0)
    declared_ceiling: str | None = None
    projected_cost: str | None = None
    recalibration_procedure: str | None = None


# ------------------------------------------------------- Part B: certainty curtailment

class CurtailmentPolicy:
    """Certainty curtailment (playbook §6): abort a DEV/TEST arm the instant its
    remaining cases cannot possibly reach the pre-registered pass bar.

    `bar` is the fraction of `n_total` cases the arm must pass (0, 1]; `n_total` is
    the split size. Exact integer arithmetic via `math.ceil` — no normal
    approximation, no continuity correction, assumption-free: an arm is curtailed
    the moment even a clean sweep of every remaining case could not reach the bar.
    """

    def __init__(self, bar: float, n_total: int) -> None:
        if not (0 < bar <= 1):
            raise ValueError(f"curtailment bar must be in (0, 1], got {bar!r}")
        if n_total <= 0:
            raise ValueError(f"curtailment n_total must be > 0, got {n_total!r}")
        self.bar = bar
        self.n_total = n_total

    @property
    def threshold(self) -> int:
        """`ceil(bar * n_total)` — the minimum pass count that still qualifies."""
        return math.ceil(self.bar * self.n_total)

    def should_curtail(self, passes: int, cases_done: int) -> bool:
        """`passes + (n_total - cases_done) < ceil(bar * n_total)` — true iff even a
        clean sweep of every remaining case cannot reach the threshold. Exactly AT
        the threshold (`passes + remaining == threshold`) is NOT curtailed: the arm
        can still, in principle, exactly qualify."""
        remaining = self.n_total - cases_done
        return passes + remaining < self.threshold

    def certain_interval(self, passes: int, cases_done: int) -> tuple[int, int]:
        """The CERTAIN pass-count interval `[passes, passes + remaining]` — the
        range the final pass count is guaranteed to land in given only what has
        already been observed, with no assumption about how the unrun cases would
        have gone. This is guard 2 (interval-only reporting) applied at the
        arithmetic level; `make_curtailment_report` applies it at the report level."""
        remaining = self.n_total - cases_done
        return passes, passes + remaining


def make_curtailment_report(
    run_id: str, split: str, arm: str, passes: int, cases_done: int, n_total: int,
    bar: float, unrun_classes: list[str],
) -> dict[str, Any]:
    """The record of a curtailment decision — INTERVAL ONLY (guard 2, playbook §6).

    Deliberately has NO point-estimate key (no "rate", "pass_rate", "estimate" or
    similar field): a curtailed arm's remaining cases were never run, so a rate
    would silently assume they would have gone the way the observed prefix did —
    exactly the assumption curtailment exists to avoid making. What this reports
    instead is the CERTAIN interval `[passes, passes + remaining] / n_total`
    (`CurtailmentPolicy.certain_interval`) plus which scenario classes never ran,
    and `curtailed: True` so a downstream reader (in particular the paired-
    comparison tools — guard 3) can recognize and refuse this run without having to
    infer curtailment from the interval shape.
    """
    policy = CurtailmentPolicy(bar=bar, n_total=n_total)
    lo, hi = policy.certain_interval(passes, cases_done)
    return {
        "run_id": run_id,
        "split": split,
        "arm": arm,
        "passes": passes,
        "cases_done": cases_done,
        "n_total": n_total,
        "bar": bar,
        "interval": [lo, hi],
        "unrun_classes": list(unrun_classes),
        "curtailed": True,
    }


def append_curtailed_run(path: Path, report: dict[str, Any]) -> None:
    """Append one curtailment report to an append-only JSONL file at `path`.

    `path` is an explicit argument with no default — unlike `refuse_curtailed`, which
    defaults to reading `CURTAILED_RUNS_PATH` (the live location), this function never
    defaults to writing it; actually curtailing a real run and recording that fact is
    the runner's explicit decision to make, not something an omitted keyword argument
    should do for it. Opens `"a"` — never truncates, never rewrites a line already on
    disk (the `provenance._append_line` / `predictions._append_line` recipe).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(report, sort_keys=True) + "\n")


def read_curtailed_runs(path: Path) -> list[dict[str, Any]]:
    """Every curtailment report appended to `path`, in file order. A missing file
    reads as no curtailed runs (nothing has curtailed yet), not an error."""
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


class CurtailedComparisonRefused(SystemExit):
    """A run named in `refuse_curtailed`'s ledger was passed into a paired comparison.

    Guard 3 (playbook §6, "paired firewall"): a curtailed arm never enters a paired
    comparison. Measured on real R6 TEST data (`scripts/mstat_stats.py`), dropping the
    16 cases (classes S11/S12) that a curtailed Bonsai arm would never have run flips
    the Qwen3.8-vs-Bonsai McNemar exact p-value from 0.059584 to 0.013853 — the SAME
    underlying data, made to cross alpha=.05 purely by which cases got compared. The
    comparison this run would have entered is refused outright, before it is computed,
    because a number flagged as "maybe misleading" still sits in front of the reader —
    only unreachable is safe.
    """

    def __init__(self, run_id: str, path: Path) -> None:
        self.run_id = run_id
        self.path = path
        super().__init__(
            f"paired comparison refused: run {run_id!r} is recorded as curtailed in "
            f"{path} — guard 3 (playbook §6 paired firewall): a curtailed arm never "
            "enters a paired comparison (measured: curtailment flips a McNemar p from "
            "0.059584 to 0.013853 purely compositionally, scripts/mstat_stats.py)"
        )


def refuse_curtailed(run_ids: Iterable[str], path: Path | None = None) -> None:
    """Refuse (`CurtailedComparisonRefused`) if any of `run_ids` is recorded in the
    curtailed-runs ledger at `path` — guard 3 (playbook §6): a curtailed arm never
    enters a paired comparison (see `CurtailedComparisonRefused` for the measured
    p-value flip this exists to make structurally unreachable).

    `path` defaults to `CURTAILED_RUNS_PATH`, the live ledger location, so a caller
    checking real run ids gets the real answer without having to name the file itself
    — but the default is resolved from the module global INSIDE this function body
    (`path is None` -> read `CURTAILED_RUNS_PATH` then), not bound into the parameter
    at import time. A plain `path: Path = CURTAILED_RUNS_PATH` default would freeze the
    Path object the moment this module is first imported, so a test (or a future
    caller) that repoints `tolerances.CURTAILED_RUNS_PATH` at a tmp ledger would be
    silently ignored by every call site that omits `path` — exactly the kind of bypass
    guard 3 exists to prevent, just self-inflicted via a Python default-argument
    gotcha instead of a caller decision. A missing ledger reads as "nothing has ever
    curtailed" (`read_curtailed_runs`'s own contract) — the overwhelmingly common case
    — so this costs one `Path.exists()` and nothing else when no curtailment has
    happened.

    Every PAIRED entry point — `scripts/r6_metrics.py` (pairwise_cmd and the oracle/
    tiers/gates CLI subcommands), `scripts/r6_analysis.py`, `scripts/
    routing_cascade_report.py`, `scripts/r3b_selection_rule.py`, `scripts/
    compare_routes.py`, `scripts/model_migration_matrix.py` — calls this on its run
    ids before any computation or DB query, so the check that a run must clear before
    it can be paired cannot be skipped by a caller who forgets to ask (see the module
    docstring's guard-3 list for the full set).
    """
    if path is None:
        path = CURTAILED_RUNS_PATH
    curtailed_ids = {row["run_id"] for row in read_curtailed_runs(path) if "run_id" in row}
    for run_id in run_ids:
        if run_id in curtailed_ids:
            raise CurtailedComparisonRefused(run_id, Path(path))
