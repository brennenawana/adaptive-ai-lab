"""pass^k protocol: SPEC, sample-set validation and the estimator — no execution.

Playbook § 7 / master plan § 7 (M_STAT_IMPLEMENTATION_MAP.md item 13): any reliability
claim about a stochastic arm reports pass^k (k=3-5) on a declared, FROZEN subset, not
pass^1 alone. On TEST the k samples per case spend exactly ONE ledgered look — the
machine ledger's `run_id` — and pass^k is measurement only: no selection decision may
key off it. This module is the protocol's declaration + guard + estimator; drawing the
k samples is out of scope here by design ("protocol code + tests only; the first
measurement is R9's" — implementation map item 13).

No model inference, no database access: every function below is a pure check or a pure
computation over caller-supplied records.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from fis_platform.provenance import digest

__all__ = [
    "PASSK_MIN",
    "PASSK_MAX",
    "PassKSample",
    "PassKSampleRefused",
    "PassKSpec",
    "estimate",
    "validate_samples",
]

# 2 <= k <= 10 is the REPRESENTABLE range this module accepts. The playbook's NORMATIVE
# default for a reliability CLAIM (i.e. what a TEST-split spec should actually use) is
# narrower: k=3-5 (playbook § 7). Values outside 3-5 but inside 2-10 are legal for the
# type (e.g. a cheap rehearsal at k=2) but are not a licensed reliability claim.
PASSK_MIN, PASSK_MAX = 2, 10

_SCENARIO_ID_RE = re.compile(r"^S\d{2}-\d{7}$")


class PassKSpec(BaseModel):
    """A frozen pass^k declaration: which cases, how many draws per case, and which
    ledgered look the draws belong to.

    `split == "test"` is the NORMATIVE ledgered form: it spends exactly ONE machine
    look, named by `look_run_id`, comprising `k` samples per case (playbook § 7). `split`
    also accepts "train" / "dev" for REHEARSAL — dry-running the protocol against a
    scratch subset before it is ever spent on TEST — and `look_run_id` is not required
    there, because a rehearsal consumes no ledgered look. `validate_samples` still
    enforces the "one look" invariant for a rehearsal spec: without a declared
    `look_run_id`, every sample must instead share one common `run_id` with the others.

    `measurement_only: Literal[True]` makes a SELECTION-use spec unrepresentable by the
    type system rather than by a runtime check someone can forget to call. A future
    contract that wants pass^k to inform a selection decision (not just report a
    reliability number) must define that use explicitly in its own field — it is not
    something this spec can be silently repurposed for.
    """

    model_config = ConfigDict(extra="forbid")

    spec_id: str = Field(min_length=1)
    suite_version: str = Field(min_length=1)
    split: Literal["test", "train", "dev"]
    k: int = Field(ge=PASSK_MIN, le=PASSK_MAX)
    scenario_ids: list[str] = Field(min_length=1)
    subset_digest: str = Field(default="", pattern=r"^([0-9a-f]{64})?$")
    look_run_id: str | None = Field(default=None, min_length=1)
    measurement_only: Literal[True]

    @field_validator("scenario_ids")
    @classmethod
    def _check_scenario_ids(cls, ids: list[str]) -> list[str]:
        bad = sorted({s for s in ids if not _SCENARIO_ID_RE.match(s)})
        if bad:
            raise ValueError(
                f"scenario_ids must match {_SCENARIO_ID_RE.pattern!r}; offenders: {bad!r}"
            )
        dupes = sorted({s for s in ids if ids.count(s) > 1})
        if dupes:
            raise ValueError(f"scenario_ids has duplicate id(s): {dupes!r}")
        return ids

    @model_validator(mode="after")
    def _check_consistency(self) -> PassKSpec:
        expected = digest(sorted(self.scenario_ids))
        if not self.subset_digest:
            self.subset_digest = expected
        elif self.subset_digest != expected:
            raise ValueError(
                f"subset_digest {self.subset_digest!r} does not match the digest of the "
                f"declared scenario_ids (expected {expected!r}) — the frozen subset moved "
                "under the spec"
            )
        if self.split == "test" and not self.look_run_id:
            raise ValueError(
                "look_run_id is required when split=='test': the ledgered pass^k look "
                "spends exactly one machine-ledger run, and every TEST spec must name it"
            )
        return self

    @property
    def spec_digest(self) -> str:
        """Digest over every declared field — the frozen identity of this spec. Not a
        stored field: a stored digest would need to exclude itself from its own
        preimage, so it is computed fresh (deterministically) from the model's own
        JSON dump instead."""
        return digest(self.model_dump(mode="json"))


class PassKSample(BaseModel):
    """One of the k draws for one scenario_id. `run_id` is the run that produced this
    draw — checked against the spec's declared look by `validate_samples`."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(pattern=_SCENARIO_ID_RE.pattern)
    sample_index: int = Field(ge=0)
    passed: bool
    run_id: str = Field(min_length=1)


class PassKSampleRefused(SystemExit):
    """`validate_samples` refused a sample set against its spec. SystemExit-based (not
    a plain exception a caller can accidentally swallow with `except Exception`): a
    pass^k estimate computed over a partial, duplicated or misattributed sample set
    would misreport the very reliability figure this protocol exists to protect, so the
    refusal is loud by construction rather than by caller discipline."""


def validate_samples(spec: PassKSpec, samples: list[PassKSample]) -> None:
    """Fail-closed structural check, run before any arithmetic touches `samples`.

    Refuses (raises `PassKSampleRefused`) unless ALL of the following hold:
      * every sample's scenario_id is in `spec.scenario_ids` (nothing outside the
        frozen subset);
      * every scenario_id in `spec.scenario_ids` has EXACTLY `spec.k` samples (a case
        short a draw, or carrying an extra one, is refused rather than silently
        counted as whatever samples happen to exist);
      * each case's sample_index values are exactly {0, ..., k-1} once each (catches a
        duplicated index paired with a missing one, which the count check alone would
        not see if the case's total sample count still happens to equal k);
      * every sample's run_id matches `spec.look_run_id` when the spec declares one
        (the ONE ledgered look invariant — a stray run_id is a sample that did not
        come from the look this spec is measuring); when the spec is a rehearsal with
        no declared look, every sample must instead share ONE common run_id with the
        others, so the same invariant holds even before a look is ledgered.

    Returns None on success. Raises on the FIRST violated category checked, in the
    order above; a caller fixing violations one at a time will not be surprised by a
    later category once the first is resolved.
    """
    subset = set(spec.scenario_ids)

    outside = sorted({s.scenario_id for s in samples} - subset)
    if outside:
        raise PassKSampleRefused(
            f"sample(s) for scenario_id(s) outside the declared subset: {outside!r}"
        )

    run_ids = {s.run_id for s in samples}
    if spec.look_run_id is not None:
        stray = sorted(run_ids - {spec.look_run_id})
        if stray:
            raise PassKSampleRefused(
                f"sample run_id(s) {stray!r} do not match the spec's declared look "
                f"{spec.look_run_id!r} — every sample must belong to the one ledgered look"
            )
    elif len(run_ids) > 1:
        raise PassKSampleRefused(
            f"samples carry {len(run_ids)} distinct run_id(s) {sorted(run_ids)!r} but the "
            "rehearsal spec declares no look_run_id — even a rehearsal's samples must "
            "share one run_id"
        )

    by_case: dict[str, list[PassKSample]] = {sid: [] for sid in spec.scenario_ids}
    for s in samples:
        by_case[s.scenario_id].append(s)

    missing = [(sid, len(ss)) for sid, ss in by_case.items() if len(ss) < spec.k]
    if missing:
        raise PassKSampleRefused(
            f"scenario_id(s) with fewer than k={spec.k} samples: {missing!r}"
        )
    extra = [(sid, len(ss)) for sid, ss in by_case.items() if len(ss) > spec.k]
    if extra:
        raise PassKSampleRefused(
            f"scenario_id(s) with more than k={spec.k} samples: {extra!r}"
        )

    bad_index = [sid for sid, ss in by_case.items()
                 if sorted(s.sample_index for s in ss) != list(range(spec.k))]
    if bad_index:
        raise PassKSampleRefused(
            f"scenario_id(s) whose sample_index values are not exactly "
            f"0..{spec.k - 1} each once (a duplicated index alongside a missing one "
            f"reads as the right COUNT but the wrong SET): {bad_index!r}"
        )


def estimate(spec: PassKSpec, samples: list[PassKSample]) -> dict[str, Any]:
    """The pass^k point estimate (playbook § 7): the fraction of cases where ALL k
    samples passed — a case solved reliably, not on one lucky draw.

    Calls `validate_samples` first and lets it raise: a pass^k number computed over a
    mis-shaped sample set (a missing draw, a stray run_id, a case outside the frozen
    subset) would misreport reliability rather than merely fail to report it, so this
    function refuses exactly the inputs `validate_samples` refuses — the two can never
    disagree about what a valid sample set is.

    Returns a dict with:
      per_case      {scenario_id: bool} — True iff all k samples for that case passed
      pass_k        fraction of cases with per_case[id] True (the headline figure)
      pass_1_mean   mean single-sample pass rate over every draw, for context only —
                    NOT itself a pass^k claim (it is the more optimistic number pass^k
                    is deliberately more conservative than)
      n_cases       len(spec.scenario_ids)
      k             spec.k
    """
    validate_samples(spec, samples)

    by_case: dict[str, list[PassKSample]] = {sid: [] for sid in spec.scenario_ids}
    for s in samples:
        by_case[s.scenario_id].append(s)

    per_case = {sid: all(s.passed for s in ss) for sid, ss in by_case.items()}
    n_cases = len(spec.scenario_ids)
    pass_k = sum(per_case.values()) / n_cases
    pass_1_mean = sum(1 for s in samples if s.passed) / len(samples)

    return {
        "per_case": per_case,
        "pass_k": pass_k,
        "pass_1_mean": pass_1_mean,
        "n_cases": n_cases,
        "k": spec.k,
    }
