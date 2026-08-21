"""Prediction ledger — playbook § 7's empirical gate, as an append-only, hash-chained log.

    "Prediction ledger: each contract records a pre-run effect-size point estimate +
    interval; predicted-vs-actual is scored in the report. A handful of entries (~5)
    make the 'is this experiment worth DEV?' gate empirical."
    (projects/fis/PLAYBOOK_ADAPTATION.md § 7)

The rule this module enforces is narrower than "record a number": a prediction that can
be edited after the actual is known is not evidence of anything, so once a prediction
entry lands it is frozen exactly the way an R6 state-log entry is frozen — the file is
opened `"a"` and never rewritten, and every entry closes over its own bytes with an
`entry_digest` chained to the one before it (`fis_platform.provenance.R6Registry._append`
/ `.read_state` is the model this follows). An edit to a written line, or a truncation of
the file, changes what `read()` recomputes and is refused rather than silently accepted.

Two entry kinds share one chain:

    prediction   {seq, prev_entry_digest, kind, prediction_id, experiment_id,
                  candidate_id, metric, point, interval, rationale, frozen_at,
                  code_commit, entry_digest} — written once per `prediction_id`.
    evaluation   {seq, prev_entry_digest, kind, prediction_id, actual, inside_interval,
                  abs_error, evaluated_at, code_commit, entry_digest} — written once per
                  `prediction_id`, by the experiment's report step, after `prediction_id`
                  already has a prediction entry. `inside_interval` and `abs_error` are
                  always computed by this module from the frozen point/interval and
                  `actual`; a caller may additionally assert either value, and a mismatch
                  is refused rather than silently corrected, so a report-generation bug
                  is caught instead of quietly overwritten.

This is deliberately prospective only. M0, R5 and R6 predate the § 7 rule and are never
backfilled into this ledger: a "prediction" written after the result is known is not a
prediction, and inventing one for a historical experiment would make every future entry
in this file worth exactly as little. `freeze_prediction` has no "as of" argument and no
way to backdate `frozen_at` — the only timestamp it can write is now.

The default live location is `learning/registry/predictions.jsonl` (`DEFAULT_LEDGER_PATH`),
named in exactly one place the way `fis_platform.provenance.default_root` names the R6
registry root. Every function on `PredictionLedger` takes the path explicitly through the
constructor rather than reading it from an environment variable or a CLI-relocatable
root, for the same reason the R6 registry root is not relocatable: a ledger you can point
somewhere else is a reset button. Tests construct `PredictionLedger(tmp_path / "p.jsonl")`.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from fis_platform.provenance import digest
from fis_platform.suite import git_head

__all__ = [
    "DEFAULT_LEDGER_PATH",
    "LedgerIntegrityError",
    "PredictionLedger",
    "PredictionRefused",
]

_ROOT = Path(__file__).resolve().parents[1]

# The one place the live location is named. No environment variable, no CLI flag that
# relocates it — see the module docstring.
DEFAULT_LEDGER_PATH = _ROOT / "learning" / "registry" / "predictions.jsonl"


def _now() -> str:
    """UTC, seconds resolution — the precision every other R-series record uses."""
    return datetime.now(UTC).isoformat(timespec="seconds")


class LedgerIntegrityError(SystemExit):
    """The ledger file does not verify: a chain link, a `seq`, or an entry's own digest
    disagrees with what is recorded. Every read path fails closed on this rather than
    return a shorter or silently-repaired history."""


class PredictionRefused(SystemExit):
    """A freeze/evaluate guard said no. The ledger file is unchanged."""


def _non_blank(value: str, field: str) -> str:
    if not value.strip():
        raise ValueError(f"{field} must be non-empty (whitespace does not count)")
    return value


class _PredictionInput(BaseModel):
    """Validates one prediction BEFORE anything is written — the same
    validate-then-append shape as `fis_platform.provenance._Record`, applied to the
    domain rule here (lo <= point <= hi, a rationale that says something) instead of to a
    digest."""

    model_config = ConfigDict(extra="forbid")

    prediction_id: str
    experiment_id: str
    candidate_id: str | None = None
    metric: str
    point: float
    interval: tuple[float, float]
    rationale: str

    @model_validator(mode="after")
    def _bounds_and_content(self) -> _PredictionInput:
        _non_blank(self.prediction_id, "prediction_id")
        _non_blank(self.experiment_id, "experiment_id")
        _non_blank(self.metric, "metric")
        _non_blank(self.rationale, "rationale")
        lo, hi = self.interval
        for name, value in (("point", self.point), ("interval lo", lo), ("interval hi", hi)):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value!r}")
        if lo > hi:
            raise ValueError(f"interval [{lo}, {hi}] has lo > hi")
        if not (lo <= self.point <= hi):
            raise ValueError(f"point {self.point} is not within interval [{lo}, {hi}]")
        return self


def _append_line(path: Path, obj: dict[str, Any]) -> None:
    """The only writer of the ledger file. Opens `"a"` — never truncates, never rewrites
    a line already on disk. (Same recipe as `fis_platform.provenance._append_line`,
    duplicated in three lines rather than imported: that name is private to `provenance`
    and this module's only writer should not be reachable through a symbol someone could
    monkeypatch expecting it to touch the R6 state log instead.)"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, sort_keys=True) + "\n")


def _read_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


class PredictionLedger:
    """One append-only, hash-chained JSONL file mixing `prediction` and `evaluation`
    entries. See the module docstring for the chain rule and the entry shapes.

    `path` is required and explicit — see the module docstring on why there is no
    default-searching constructor.
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    # -------------------------------------------------------------- read

    def read(self) -> list[dict[str, Any]]:
        """The verified chain: every entry's digest is recomputed, every
        `prev_entry_digest` must equal the previous entry's `entry_digest` (the empty
        string for the first entry), and `seq` must run 1..n with no gaps. A missing file
        reads as an empty ledger (nothing has been frozen yet) rather than an error — the
        first `freeze_prediction` call is what creates it.

        Fails closed (`LedgerIntegrityError`) on any disagreement: that is what makes an
        edited or truncated file an error instead of a shorter or different history being
        read back as if nothing had happened.
        """
        entries = _read_lines(self.path)
        prev = ""
        for i, e in enumerate(entries, start=1):
            if e.get("kind") not in ("prediction", "evaluation"):
                raise LedgerIntegrityError(
                    f"entry seq {e.get('seq')!r} has kind {e.get('kind')!r}, not "
                    "'prediction' or 'evaluation' — this ledger was written by something else")
            if e.get("seq") != i:
                raise LedgerIntegrityError(
                    f"entry {i} claims seq {e.get('seq')!r} — the ledger has a gap")
            if e.get("prev_entry_digest") != prev:
                raise LedgerIntegrityError(
                    f"entry seq {i} chains to {str(e.get('prev_entry_digest'))[:12]}… but "
                    f"seq {i - 1} digests to {prev[:12] or '(genesis)'}… — the ledger was rewritten")
            body = {k: v for k, v in e.items() if k != "entry_digest"}
            recomputed = digest(body)
            if recomputed != e.get("entry_digest"):
                raise LedgerIntegrityError(
                    f"entry seq {i} digests to {recomputed[:12]}… but records "
                    f"{str(e.get('entry_digest'))[:12]}… — the entry was edited")
            prev = e["entry_digest"]
        return entries

    def get(self, prediction_id: str) -> dict[str, Any]:
        """`{"prediction": <entry>, "evaluation": <entry or None>}` for one id. Refuses
        if no prediction with this id was ever frozen."""
        entries = self.read()
        prediction = next((e for e in entries if e["kind"] == "prediction"
                           and e["prediction_id"] == prediction_id), None)
        if prediction is None:
            raise PredictionRefused(f"no prediction {prediction_id!r} on the ledger {self.path}")
        evaluation = next((e for e in entries if e["kind"] == "evaluation"
                           and e["prediction_id"] == prediction_id), None)
        return {"prediction": prediction, "evaluation": evaluation}

    # -------------------------------------------------------------- write

    def freeze_prediction(self, *, prediction_id: str, experiment_id: str, metric: str,
                          point: float, interval: tuple[float, float] | list[float],
                          rationale: str, candidate_id: str | None = None,
                          code_commit: str | None = None) -> dict[str, Any]:
        """Append one prediction entry. Frozen the instant it lands: nothing in this
        module ever rewrites a written line, so an edit after the fact is reachable only
        by hand-editing the file, and the next `read()` catches that.

        Refuses (`PredictionRefused`, ledger unchanged): `prediction_id` already frozen
        (a prediction is written once — a revised estimate gets a new id, so the old one
        stays legible as what was actually predicted first); a non-finite point/interval
        bound; an interval with lo > hi; a point outside its own interval; an empty or
        whitespace-only `prediction_id`, `experiment_id`, `metric`, or `rationale`.
        """
        try:
            lo, hi = interval
            validated = _PredictionInput(
                prediction_id=prediction_id, experiment_id=experiment_id,
                candidate_id=candidate_id, metric=metric, point=point,
                interval=(lo, hi), rationale=rationale,
            )
        except (ValidationError, ValueError, TypeError) as exc:
            raise PredictionRefused(f"prediction {prediction_id!r} refused: {exc}") from exc

        entries = self.read()      # verify the existing chain before trusting it enough to extend
        if any(e["kind"] == "prediction" and e["prediction_id"] == validated.prediction_id
               for e in entries):
            raise PredictionRefused(
                f"prediction_id {validated.prediction_id!r} is already frozen on {self.path} — "
                "a prediction is written once; register a new id for a revised estimate")

        entry: dict[str, Any] = {
            "seq": len(entries) + 1,
            "prev_entry_digest": entries[-1]["entry_digest"] if entries else "",
            "kind": "prediction",
            "prediction_id": validated.prediction_id,
            "experiment_id": validated.experiment_id,
            "candidate_id": validated.candidate_id,
            "metric": validated.metric,
            "point": validated.point,
            "interval": [validated.interval[0], validated.interval[1]],
            "rationale": validated.rationale,
            "frozen_at": _now(),
            "code_commit": code_commit if code_commit is not None else git_head(),
        }
        entry["entry_digest"] = digest(entry)
        _append_line(self.path, entry)
        return entry

    def evaluate(self, prediction_id: str, actual: float, *,
                inside_interval: bool | None = None, abs_error: float | None = None,
                code_commit: str | None = None) -> dict[str, Any]:
        """Append one evaluation entry scoring an existing prediction, without touching
        the prediction entry itself — the file is append-only, so there is no other way
        to change it.

        `inside_interval` and `abs_error` are always computed here from the frozen
        point/interval and `actual`. If the caller also passes either value (e.g. a
        report step that computed its own score and wants the ledger to confirm it), a
        disagreement is refused rather than silently overwritten with the correct value,
        so a scoring bug in the caller gets seen instead of buried under a quietly-correct
        ledger entry.

        Refuses (`PredictionRefused`, ledger unchanged): no prediction with this id has
        been frozen yet; this prediction has already been evaluated once (an evaluation
        is written once, exactly like the prediction it scores); a non-finite `actual`;
        a caller-supplied `inside_interval` or `abs_error` that disagrees with what this
        ledger computes.
        """
        if not math.isfinite(actual):
            raise PredictionRefused(f"actual={actual!r} is not finite")
        actual = float(actual)

        entries = self.read()
        prediction = next((e for e in entries if e["kind"] == "prediction"
                           and e["prediction_id"] == prediction_id), None)
        if prediction is None:
            raise PredictionRefused(
                f"no prediction {prediction_id!r} on {self.path} — evaluate() can only "
                "score a prediction that was frozen first")
        if any(e["kind"] == "evaluation" and e["prediction_id"] == prediction_id
               for e in entries):
            raise PredictionRefused(
                f"prediction {prediction_id!r} has already been evaluated on {self.path} — "
                "an evaluation is written once, exactly like the prediction it scores")

        lo, hi = prediction["interval"]
        computed_inside = lo <= actual <= hi
        computed_error = abs(actual - prediction["point"])
        if inside_interval is not None and bool(inside_interval) != computed_inside:
            raise PredictionRefused(
                f"prediction {prediction_id!r}: caller claims inside_interval="
                f"{inside_interval!r} but actual={actual} against interval [{lo}, {hi}] "
                f"computes {computed_inside} — refusing to record a disagreeing claim")
        if abs_error is not None and round(float(abs_error), 12) != round(computed_error, 12):
            raise PredictionRefused(
                f"prediction {prediction_id!r}: caller claims abs_error={abs_error!r} but "
                f"|{actual} - {prediction['point']}| computes {computed_error} — refusing "
                "to record a disagreeing claim")

        entry: dict[str, Any] = {
            "seq": len(entries) + 1,
            "prev_entry_digest": entries[-1]["entry_digest"],
            "kind": "evaluation",
            "prediction_id": prediction_id,
            "actual": actual,
            "inside_interval": computed_inside,
            "abs_error": computed_error,
            "evaluated_at": _now(),
            "code_commit": code_commit if code_commit is not None else git_head(),
        }
        entry["entry_digest"] = digest(entry)
        _append_line(self.path, entry)
        return entry
