"""Machine-checkable experiment-contract representation
(`projects/fis/EXPERIMENT_CONTRACT_TEMPLATE.md` v2; M-STAT implementation map,
Prediction/statistics items). A contract is not "reviewed and trusted" any more
than a model artifact is trusted by its filename — R6's own escape hatch read as a
sentence a human agreed to and never enforced. `ContractSpec` is the field-level
schema a contract document must satisfy before its freeze; `validate_contract_spec`
is the fail-closed entry point, and `scripts/contract_check.py` is its CLI.

Field requirements are CONDITIONAL on `experiment_type` (template §1-13): an
INFERENTIAL contract needs the full statistical plan (MDE, effective N, primary/
secondary statistic, curtailment policy, TEST-look declaration); a SCREENING
contract ranks candidates on TRAIN and never claims MDE or effective N; DIAGNOSTIC
and MEASUREMENT contracts carry only the common core (and DIAGNOSTIC is forbidden
from planning a TEST look at all — no TEST spend for a diagnostic).

Design: this module deliberately keeps "is field X required, GIVEN this
experiment_type" OUT of `ContractSpec`'s own pydantic validators and inside
`_type_conditional_problems`, a plain function over the RAW input dict. If that
logic instead lived in a `ContractSpec` `model_validator(mode="after")`, pydantic
would only run it once every field has ALREADY individually parsed without error —
so a spec with both a structural typo (e.g. a bad `corpus_digest`) AND a missing
type-required field (e.g. no `mde_pp`) would report only the structural problem on
the first pass, and the type-required problem would surface only on a SECOND
validation attempt after the first is fixed. `validate_contract_spec` runs both
passes unconditionally and merges every problem from both into one
`ContractSpecError`, so a contract author sees the whole rejection at once — the
same reason `fis_platform.provenance`'s payload-key check
(`missing = [k for k in keys if k not in payload]`) collects before it raises.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from fis_platform.provenance import digest
from fis_platform.tolerances import ToleranceSpec

__all__ = [
    "ArtifactLineageEntry",
    "ContractSpec",
    "ContractSpecError",
    "CurtailmentPolicySpec",
    "DescriptiveTerm",
    "ExperimentType",
    "TestLookSpec",
    "VERDICTS",
    "validate_contract_spec",
]

_HEX64 = re.compile(r"^[0-9a-f]{64}$")

VERDICTS = ("CONFIRMED", "REFUTED", "INCONCLUSIVE", "RANKED")
Verdict = Literal["CONFIRMED", "REFUTED", "INCONCLUSIVE", "RANKED"]


class ExperimentType(str, Enum):
    INFERENTIAL = "INFERENTIAL"
    SCREENING = "SCREENING"
    DIAGNOSTIC = "DIAGNOSTIC"
    MEASUREMENT = "MEASUREMENT"


class ContractSpecError(SystemExit):
    """A contract spec is missing or has invalid fields. Lists EVERY problem found
    (see the module docstring), not just the first — fail-closed and fixable in one
    pass, matching every other refusal in this codebase (`TransitionRefused`,
    `PredictionRefused`, `PassKSampleRefused`)."""


# ------------------------------------------------------------------- nested shapes

class ArtifactLineageEntry(BaseModel):
    """One artifact this contract's measurement traces to."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DescriptiveTerm(BaseModel):
    """One entry of the pre-registered descriptive vocabulary (playbook §7): the
    ONLY thing that licenses a descriptive reading of a null result (e.g. R6's "47
    vs 48 = competitive", where "competitive" was defined here, in advance, as
    within +/-4 — never inferred from the null itself after the fact)."""

    model_config = ConfigDict(extra="forbid")

    term: str = Field(min_length=1)
    definition: str = Field(min_length=1)


class CurtailmentPolicySpec(BaseModel):
    """§12's certainty-curtailment clause. `enabled=True` is the default-on
    standing rule and requires `bar` (the pass fraction `CurtailmentPolicy`
    curtails against); `enabled=False` requires a non-empty
    `disable_justification` — curtailment may be turned off, but never silently
    (template §12: "disabling curtailment requires a written justification here").
    These rules are type-independent: they apply to this object whenever it is
    present, regardless of which `ExperimentType` the contract declares."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool
    bar: float | None = None
    disable_justification: str | None = None

    @model_validator(mode="after")
    def _check(self) -> CurtailmentPolicySpec:
        if self.enabled:
            if self.bar is None:
                raise ValueError("curtailment_policy.enabled=True requires bar")
            if not (0 < self.bar <= 1):
                raise ValueError(f"curtailment_policy.bar must be in (0, 1], got {self.bar!r}")
        elif not (self.disable_justification or "").strip():
            raise ValueError(
                "curtailment_policy.enabled=False requires a non-empty "
                "disable_justification (template §12) — curtailment may be disabled, "
                "never silently"
            )
        return self


class TestLookSpec(BaseModel):
    """This contract's TEST-look declaration (template §5's ledger entry, §12's
    look). `planned=True` requires `look_no`; `look_no >= 8` requires a non-empty
    `trigger_review_ref` — the Suite-v4 trigger review must be linked before an 8th
    look on the current suite may be planned (playbook §1, §16). Type-independent:
    these rules apply whenever this object is present, in any `ExperimentType`."""

    model_config = ConfigDict(extra="forbid")

    planned: bool
    look_no: int | None = Field(default=None, ge=1)
    trigger_review_ref: str | None = None

    @model_validator(mode="after")
    def _check(self) -> TestLookSpec:
        if self.planned and self.look_no is None:
            raise ValueError("test_look.planned=True requires look_no")
        if self.look_no is not None and self.look_no >= 8 and not (self.trigger_review_ref or "").strip():
            raise ValueError(
                f"test_look.look_no={self.look_no} >= 8 requires a non-empty "
                "trigger_review_ref (the Suite-v4 trigger review, playbook §16, must "
                "be linked before look #8+ on the current suite may be planned)"
            )
        return self


# ------------------------------------------------------------------------ ContractSpec

class ContractSpec(BaseModel):
    """Machine-checkable rendering of one `EXPERIMENT_CONTRACT_TEMPLATE.md` v2
    document. Field SHAPE (patterns, literals, nested-object internal rules,
    numeric bounds) is enforced here, always, on whichever fields are present.
    Field PRESENCE conditional on `experiment_type` is enforced by
    `_type_conditional_problems` / `validate_contract_spec`, NOT by this class's
    own validators — see the module docstring for why. Prefer
    `validate_contract_spec` over constructing this directly; direct construction
    skips the type-conditional presence checks.
    """

    model_config = ConfigDict(extra="forbid")

    # ---- common core: required for every experiment_type ----
    spec_version: Literal[1]
    experiment_id: str = Field(min_length=1)
    experiment_type: ExperimentType
    question: str = Field(min_length=1)
    suite_version: str = Field(min_length=1)
    corpus_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    split_permissions: dict[str, bool] | list[str]
    ordering_policy: Literal["round_robin"]
    authoritative_clocks: dict[str, str] = Field(min_length=1)
    state_machine: str = Field(min_length=1)
    artifact_lineage: list[ArtifactLineageEntry] = Field(default_factory=list)

    # ---- conditional on experiment_type; see _type_conditional_problems ----
    candidates: list[str] | None = Field(default=None, min_length=1)
    execution_system_digests: dict[str, str] | None = Field(default=None, min_length=1)
    tolerances: list[ToleranceSpec] | None = Field(default=None, min_length=1)
    expected_discordance_range: list[float] | None = Field(default=None, min_length=2, max_length=2)
    clustering_unit: Literal["scenario_class"] | None = None
    effective_n: float | None = Field(default=None, gt=0)
    mde_pp: float | None = Field(default=None, gt=0)
    primary_statistic: Literal["cluster_robust_paired_t"] | None = None
    secondary_statistic: Literal["mcnemar_exact"] | None = None
    descriptive_vocabulary: list[DescriptiveTerm] = Field(default_factory=list)
    allowed_verdicts: list[Verdict] = Field(default_factory=list)
    prediction_ref: str | None = None
    curtailment_policy: CurtailmentPolicySpec | None = None
    test_look: TestLookSpec | None = None

    @field_validator("execution_system_digests")
    @classmethod
    def _check_execution_system_digests(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        if v is None:
            return v
        bad = {k: val for k, val in v.items() if not _HEX64.match(val)}
        if bad:
            raise ValueError(f"execution_system_digests values must be 64-hex digests; bad: {bad!r}")
        return v

    @model_validator(mode="after")
    def _check_shape(self) -> ContractSpec:
        if self.expected_discordance_range is not None:
            lo, hi = self.expected_discordance_range
            if not (0 <= lo <= hi <= 1):
                raise ValueError(
                    "expected_discordance_range must be [lo, hi] with 0 <= lo <= hi <= 1, "
                    f"got {self.expected_discordance_range!r}"
                )
        return self

    @property
    def contract_spec_digest(self) -> str:
        """Digest over the spec's own JSON dump — computed fresh, never stored (the
        `ToleranceSpec.spec_digest` / `PassKSpec.spec_digest` pattern). This is the
        digest a future R7 freeze commit records in the CONTRACT_FROZEN payload."""
        return digest(self.model_dump(mode="json"))


# ------------------------------------------------------------------ type-conditional

def _present(data: dict[str, Any], key: str) -> bool:
    return key in data and data[key] is not None


def _nonempty(data: dict[str, Any], key: str) -> bool:
    v = data.get(key)
    return v is not None and hasattr(v, "__len__") and len(v) > 0


# Fields required (non-empty) for INFERENTIAL beyond the common core and beyond
# candidates/tolerances (shared with SCREENING, checked separately below).
_INFERENTIAL_ONLY_NONEMPTY = (
    "execution_system_digests", "expected_discordance_range", "allowed_verdicts",
)
_INFERENTIAL_ONLY_SCALAR = (
    "clustering_unit", "effective_n", "mde_pp", "primary_statistic",
    "secondary_statistic", "prediction_ref", "curtailment_policy", "test_look",
)


def _type_conditional_problems(data: dict[str, Any]) -> list[str]:
    """Every "is field X required, given experiment_type" and "is field X's
    CONTENT valid, given experiment_type" problem in `data` — a plain function over
    the raw input dict (not a parsed `ContractSpec`) so it can run independently of,
    and be merged with, `ContractSpec`'s own structural validation. See the module
    docstring for why this split exists.

    Unknown/missing `experiment_type` reports nothing here — `ContractSpec`'s own
    (always-on) field validation reports that on its own.
    """
    problems: list[str] = []
    raw_type = data.get("experiment_type")
    etype = raw_type.value if isinstance(raw_type, ExperimentType) else str(raw_type or "").upper()
    if etype not in {t.value for t in ExperimentType}:
        return problems

    if etype in ("INFERENTIAL", "SCREENING"):
        # template §3: artifact_lineage "may be empty only for MEASUREMENT/DIAGNOSTIC"
        if not _nonempty(data, "artifact_lineage"):
            problems.append(f"artifact_lineage: required (non-empty) for {etype}")
        if not _nonempty(data, "candidates"):
            problems.append(f"candidates: required (non-empty) for {etype}")
        if not _nonempty(data, "tolerances"):
            problems.append(f"tolerances: required (non-empty) for {etype}")

    if etype == "INFERENTIAL":
        for field in _INFERENTIAL_ONLY_NONEMPTY:
            if not _nonempty(data, field):
                problems.append(f"{field}: required for INFERENTIAL")
        for field in _INFERENTIAL_ONLY_SCALAR:
            if not _present(data, field):
                problems.append(f"{field}: required for INFERENTIAL")

    allowed_verdicts = data.get("allowed_verdicts")
    if isinstance(allowed_verdicts, list) and allowed_verdicts:
        av = set(allowed_verdicts)
        if etype != "SCREENING" and "RANKED" in av:
            problems.append("allowed_verdicts: RANKED is only permitted for SCREENING")
        if etype == "SCREENING":
            if "RANKED" not in av:
                problems.append("allowed_verdicts: SCREENING must include RANKED (it ranks, never infers)")
            if "CONFIRMED" in av or "REFUTED" in av:
                problems.append(
                    "allowed_verdicts: SCREENING must exclude CONFIRMED/REFUTED (it ranks, never infers)"
                )

    if etype == "DIAGNOSTIC":
        test_look = data.get("test_look")
        if isinstance(test_look, dict) and test_look.get("planned"):
            problems.append(
                "test_look.planned: must be false or absent for DIAGNOSTIC (no TEST spend)"
            )

    return problems


def _format_problems(problems: list[str]) -> str:
    uniq = list(dict.fromkeys(problems))  # stable de-dup: the two passes can flag the same field
    lines = "\n".join(f"  - {p}" for p in uniq)
    return f"contract spec invalid ({len(uniq)} problem(s)):\n{lines}"


def validate_contract_spec(data: dict[str, Any]) -> ContractSpec:
    """Validate `data` (a JSON-decoded contract spec) against `ContractSpec`,
    type-conditional on `experiment_type`. Raises `ContractSpecError` listing EVERY
    missing or invalid field found — both `ContractSpec`'s own structural problems
    and `_type_conditional_problems`'s presence/content problems — not just the
    first. Returns the validated `ContractSpec` on success.
    """
    problems = _type_conditional_problems(data)
    spec: ContractSpec | None = None
    try:
        spec = ContractSpec.model_validate(data)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"]) or "<root>"
            problems.append(f"{loc}: {err['msg']}")
    if problems:
        raise ContractSpecError(_format_problems(problems))
    assert spec is not None
    return spec
