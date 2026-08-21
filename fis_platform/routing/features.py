"""R5 — the production-observable feature boundary for learned silent-failure routing.

`projects/fis/R5_EXPERIMENT_CONTRACT.md` § 5–6 is the governing document. This module is the
*only* place where a routing feature vector may be produced, and it exists so that the
boundary between "what a production deployment can see at the decision point" and "what
the eval harness knows afterwards" is a piece of code with tests rather than a habit.

Three properties are load-bearing, in decreasing order of how badly a violation would
corrupt the R5 result:

1. **Explicit allowlist.** `FEATURE_ORDER` names every feature that may exist. A name
   outside it is a schema error, not a warning — a learned router that quietly gained a
   58th feature would still produce a number, and the number would look like a routing
   result. Additions bump `FEATURE_SCHEMA_VERSION`, which every frozen router artifact
   records (§ 13) so replay fails closed on a mismatch.
2. **Gold cannot enter, even by name.** `FORBIDDEN_FEATURE_NAMES` is the manifest's gold
   fields plus the scorer's vocabulary; those names are rejected before the allowlist
   check so the error says *why*. `snapshot_from` reads only
   `model_invocations[0]`, `verification`, `tool_calls` and `error` off the trajectory —
   never `scenario_id`, `experiment_arm`, `runtime_context`, `case_id`, `router`,
   `human_feedback`, `failure_class` or `business_outcome` — and its signature has no
   score or manifest parameter, so a leak cannot be introduced at the call site either.
3. **Deterministic serialization.** `canonical_json()` emits the features in
   `FEATURE_ORDER` with ratios rounded to six decimals, and `digest` is its sha256. Two
   extractions of the same trajectory therefore produce the same digest on any machine,
   which is what makes the routing telemetry of § 15 auditable after the fact.

This package inherits the import ban of `tests/test_routing_no_gold_leak.py`: it may not
import `evals.scorers`, `schemas.scenario`, `scenarios.generator` or anything
`ground_truth*`. `_UNSUPPORTED_MARKERS` is imported from the R4 cascade rather than
restated here, deliberately: if the router's notion of "unsupported claim" drifted from
the incumbent gate's, the comparison between them would stop being a comparison.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

from pydantic import field_validator, model_validator

from schemas.common import FrozenBase
from schemas.investigator import InvestigationResult, NextAction, RootCauseLabel
from schemas.routing import GOLD_FEATURE_NAMES
from schemas.trajectory import Trajectory
from services.ai_orchestrator.cascade import _UNSUPPORTED_MARKERS

# Bumped whenever FEATURE_ORDER or the meaning of any feature changes. Frozen router
# artifacts record it and refuse to replay against a different extractor (§ 13).
FEATURE_SCHEMA_VERSION = "1"

# The generation budget every record written before `ModelInvocation.max_tokens` existed
# ran with (see the field's comment on the schema). Hardcoded rather than imported from
# the orchestrator's DEFAULT_MAX_TOKENS: `budget_used` is part of a frozen feature
# schema, so changing the orchestrator default must not silently redefine an existing
# feature's denominator.
_LEGACY_MAX_TOKENS = 4096

# Verifier check keys, in the order `verifier.py` writes them. An absent check is 0 —
# `cited_ids_observed` is only recorded when the run observed any ids at all, and "not
# evaluated" is a different state from "evaluated and passed".
_VERIFIER_CHECKS: tuple[str, ...] = (
    "schema_validation",
    "citation_required",
    "citation_resolves_to_call",
    "cited_ids_observed",
    "known_action_code",
    "confidence_supported",
    "facts_present",
)

# Violation texts the verifier emits verbatim; matched by prefix so a change to the
# message tail (the offending id/source) does not change the count.
_FABRICATED_ID_PREFIX = "cites an id no tool returned"
_UNCALLED_SERVICE_PREFIX = "cites a service that was never successfully called"
_SCHEMA_ERROR_RE = re.compile(r"schema invalid: (\d+) error\(s\)")

# Tools whose presence is a shape signal about the trajectory, not about the answer key.
_WEBHOOK_HISTORY_TOOL = "get_webhook_history"
_VERIFICATIONS_TOOL = "get_verifications"

_FAMILY_A: tuple[str, ...] = (
    "produced_output",
    "stop_length",
    "input_tokens",
    "output_tokens",
    "reasoning_chars",
    "content_chars",
    "reasoning_share",
    "output_per_input",
    "budget_used",
    "wall_ms",
    "api_ms",
)

_FAMILY_B: tuple[str, ...] = (
    "verifier_passed",
    "schema_valid",
    "checks_evaluated",
    *(f"check_{name}" for name in _VERIFIER_CHECKS),
    "n_violations",
    "n_unsupported_claims",
    "n_fabricated_ids",
    "n_uncalled_services",
    "schema_error_count",
    "no_output_error",
)

_FAMILY_C: tuple[str, ...] = (
    "n_tool_calls",
    "n_tool_success",
    "n_tool_errors",
    "n_unique_tools",
    "n_webhook_history_calls",
    "n_verification_calls",
    "n_repeated_calls",
    "tool_latency_ms_total",
)

_FAMILY_D: tuple[str, ...] = (
    "answer_present",
    *(f"said_label_{label.value}" for label in RootCauseLabel),
    *(f"said_action_{action.value}" for action in NextAction),
)

#: The allowlist, families A–D in contract order. Position is part of the contract:
#: canonical JSON, digests and every frozen router artifact's coefficient vector are
#: indexed by it.
FEATURE_ORDER: tuple[str, ...] = _FAMILY_A + _FAMILY_B + _FAMILY_C + _FAMILY_D

FEATURE_FAMILIES: dict[str, tuple[str, ...]] = {
    "A": _FAMILY_A,
    "B": _FAMILY_B,
    "C": _FAMILY_C,
    "D": _FAMILY_D,
}

#: Names that are a schema error even if someone added them to FEATURE_ORDER. The
#: manifest's gold fields (`GOLD_FEATURE_NAMES`) plus the scorer's and the split
#: layer's vocabulary — a feature called `strict_all_pass` or `frontier_pass` is the
#: label, and a router fed the label reports the label's accuracy, not a routing result.
FORBIDDEN_FEATURE_NAMES: frozenset[str] = GOLD_FEATURE_NAMES | frozenset({
    "strict_all_pass", "all_pass", "score", "scorer", "frontier", "strong", "split",
    "category", "class", "seed", "scenario_id", "gold", "manifest", "evidence_recall",
    "truth",
})

#: Everything the manifest calls an expectation. A prefix rule rather than a list,
#: because the gold fields most likely to be invented later are named `expected_*`.
_FORBIDDEN_PREFIX = "expected_"


def is_forbidden_feature_name(name: str) -> bool:
    """True for any name that may never be a routing feature, listed or not."""
    return name in FORBIDDEN_FEATURE_NAMES or name.startswith(_FORBIDDEN_PREFIX)


def _canonical_json(feature_schema_version: str, features: dict[str, float]) -> str:
    """The one serialization. Fixed key order, no whitespace, ratios at six decimals.

    A list of pairs rather than an object: JSON objects have no ordering guarantee once
    they round-trip through another language's parser, and the digest must survive that.
    """
    payload = {
        "feature_schema_version": feature_schema_version,
        "features": [[name, round(float(features[name]), 6)] for name in FEATURE_ORDER],
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


class AnswerFields(FrozenBase):
    """The only two things the router may read off the model's answer (§ 5).

    Kept as plain strings, not enums, because for the frozen Suite v3 arms these are
    reconstructed in the dataset layer from the scorer's verbatim `said <label>` echo —
    an unrecognised value must extract to "matches no one-hot", never to a crash.
    """

    root_cause_label: str | None = None
    recommended_next_action: str | None = None

    @classmethod
    def from_result(cls, result: InvestigationResult) -> AnswerFields:
        return cls(
            root_cause_label=result.root_cause.label.value,
            recommended_next_action=result.recommended_next_action.value,
        )


class RoutingFeatureSnapshot(FrozenBase):
    """One decision point's features, taken where R4 decides (§ 5).

    The header fields (`feature_schema_version`, `local_model`, `digest`) are not
    features and are not fed to any classifier; they exist so a decision recorded in
    `learning.routing_decisions` can be tied back to the exact extractor and vector.
    """

    feature_schema_version: str = FEATURE_SCHEMA_VERSION
    local_model: str | None = None
    features: dict[str, float]
    digest: str

    @field_validator("features")
    @classmethod
    def _allowlisted_finite_and_complete(cls, v: dict[str, float]) -> dict[str, float]:
        leaked = sorted(k for k in v if is_forbidden_feature_name(k))
        if leaked:
            raise ValueError(
                f"forbidden routing feature {leaked}: these are eval labels or gold "
                "manifest fields; a router may be scored by them, never fed them"
            )
        unlisted = sorted(set(v) - set(FEATURE_ORDER))
        if unlisted:
            raise ValueError(
                f"feature name outside the FEATURE_ORDER allowlist {unlisted}; add it to "
                f"the contract and bump FEATURE_SCHEMA_VERSION (currently "
                f"{FEATURE_SCHEMA_VERSION!r}) rather than widening the vector in place"
            )
        missing = [name for name in FEATURE_ORDER if name not in v]
        if missing:
            raise ValueError(
                f"incomplete feature vector, missing {missing}; every allowlisted "
                "feature is always present so the vector's positions are stable"
            )
        bad = sorted(k for k, val in v.items() if not math.isfinite(float(val)))
        if bad:
            raise ValueError(f"non-finite feature value for {bad}; features are finite floats")
        return {k: float(val) for k, val in v.items()}

    @model_validator(mode="before")
    @classmethod
    def _fill_digest(cls, data: Any) -> Any:
        """Compute the digest when the caller did not, so it can never be stale."""
        if not isinstance(data, dict) or data.get("digest"):
            return data
        try:
            digest = cls.compute_digest(data["features"])
        except (AttributeError, KeyError, TypeError, ValueError):
            digest = ""     # the features validator will say what is actually wrong
        return {**data, "digest": digest}

    @model_validator(mode="after")
    def _digest_matches_features(self) -> RoutingFeatureSnapshot:
        expected = _sha256(_canonical_json(self.feature_schema_version, self.features))
        if self.digest != expected:
            raise ValueError(
                f"digest {self.digest!r} does not match the features it claims to "
                f"summarise (expected {expected!r})"
            )
        return self

    @staticmethod
    def compute_digest(features: dict[str, float],
                       version: str = FEATURE_SCHEMA_VERSION) -> str:
        """sha256 of the canonical JSON — the identity of this feature vector."""
        return _sha256(_canonical_json(version, features))

    def ordered_values(self) -> list[float]:
        """The vector as a classifier consumes it: FEATURE_ORDER, positionally."""
        return [self.features[name] for name in FEATURE_ORDER]

    def canonical_json(self) -> str:
        return _canonical_json(self.feature_schema_version, self.features)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ratio(numerator: float, denominator: float) -> float:
    """Ratios are 0 when undefined, and rounded where they are stored (contract § 6)."""
    if not denominator:
        return 0.0
    return round(numerator / denominator, 6)


def snapshot_from(trajectory: Trajectory,
                  answer: AnswerFields | InvestigationResult | None) -> RoutingFeatureSnapshot:
    """Extract the R5 snapshot at the R4 decision point.

    Inputs are exactly what a production deployment holds after `investigate()` returns
    and before any strong call: the local stage's invocation, the deterministic
    verifier's verdict, the tool calls, the no-output error, and the answer's own
    `root_cause.label` / `recommended_next_action`. No other trajectory field is read,
    and there is deliberately no parameter through which a score or a manifest could be
    passed in.
    """
    inv = trajectory.model_invocations[0] if trajectory.model_invocations else None
    v = trajectory.verification
    if isinstance(answer, InvestigationResult):
        answer = AnswerFields.from_result(answer)

    features: dict[str, float] = {}

    # --- A: model / runtime -------------------------------------------------
    # `produced_output` is "a schema-valid InvestigationResult came back". R4 derives the
    # same bit from `result is not None`; the two coincide because `verify()` returns
    # parsed=None exactly when schema_valid is False, and `investigate()` leaves
    # verification=None when nothing parsed at all.
    features["produced_output"] = float(v is not None and v.schema_valid)
    if inv is None:
        features.update({name: 0.0 for name in _FAMILY_A if name != "produced_output"})
    else:
        reasoning_chars = float(inv.reasoning_chars or 0)
        content_chars = float(inv.content_chars or 0)
        input_tokens = float(inv.usage.input_tokens)
        output_tokens = float(inv.usage.output_tokens)
        features["stop_length"] = float(inv.stop_reason == "length")
        features["input_tokens"] = input_tokens
        features["output_tokens"] = output_tokens
        features["reasoning_chars"] = reasoning_chars
        features["content_chars"] = content_chars
        features["reasoning_share"] = _ratio(reasoning_chars, reasoning_chars + content_chars)
        features["output_per_input"] = _ratio(output_tokens, input_tokens)
        features["budget_used"] = _ratio(output_tokens, inv.max_tokens or _LEGACY_MAX_TOKENS)
        features["wall_ms"] = float(inv.latency.wall_ms)
        features["api_ms"] = float(inv.latency.api_ms or 0)

    # --- B: verifier --------------------------------------------------------
    violations = list(v.violations) if v else []
    checks = dict(v.checks) if v else {}
    features["verifier_passed"] = float(v is not None and v.passed)
    features["schema_valid"] = float(v is not None and v.schema_valid)
    features["checks_evaluated"] = float(len(checks))
    for name in _VERIFIER_CHECKS:
        features[f"check_{name}"] = float(checks.get(name) is True)
    features["n_violations"] = float(len(violations))
    features["n_unsupported_claims"] = float(
        sum(1 for m in violations if any(k in m for k in _UNSUPPORTED_MARKERS))
    )
    features["n_fabricated_ids"] = float(
        sum(1 for m in violations if m.startswith(_FABRICATED_ID_PREFIX))
    )
    features["n_uncalled_services"] = float(
        sum(1 for m in violations if m.startswith(_UNCALLED_SERVICE_PREFIX))
    )
    features["schema_error_count"] = float(_schema_error_count(violations))
    features["no_output_error"] = float(trajectory.error is not None)

    # --- C: tool trajectory -------------------------------------------------
    calls = list(trajectory.tool_calls)
    seen: set[tuple[str, str]] = set()
    repeated = 0
    for call in calls:
        key = (call.tool, call.args_hash)
        if key in seen:
            repeated += 1
        seen.add(key)
    features["n_tool_calls"] = float(len(calls))
    features["n_tool_success"] = float(sum(1 for c in calls if c.status == "success"))
    # Anything that is not a success cost a turn and returned no evidence — timeout and
    # denied are errors from the router's point of view, not a third state.
    features["n_tool_errors"] = float(sum(1 for c in calls if c.status != "success"))
    features["n_unique_tools"] = float(len({c.tool for c in calls}))
    features["n_webhook_history_calls"] = float(
        sum(1 for c in calls if c.tool == _WEBHOOK_HISTORY_TOOL)
    )
    features["n_verification_calls"] = float(sum(1 for c in calls if c.tool == _VERIFICATIONS_TOOL))
    features["n_repeated_calls"] = float(repeated)
    features["tool_latency_ms_total"] = float(sum(c.latency_ms for c in calls))

    # --- D: answer echo -----------------------------------------------------
    label = answer.root_cause_label if answer else None
    action = answer.recommended_next_action if answer else None
    features["answer_present"] = float(answer is not None and label is not None)
    for known_label in RootCauseLabel:
        features[f"said_label_{known_label.value}"] = float(label == known_label.value)
    for known_action in NextAction:
        features[f"said_action_{known_action.value}"] = float(action == known_action.value)

    return RoutingFeatureSnapshot(
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        local_model=inv.canonical_model if inv else None,
        features=features,
        digest=RoutingFeatureSnapshot.compute_digest(features),
    )


def _schema_error_count(violations: list[str]) -> int:
    """The N of the verifier's "schema invalid: N error(s)"; 0 when it did not say so."""
    for message in violations:
        match = _SCHEMA_ERROR_RE.search(message)
        if match:
            return int(match.group(1))
    return 0


__all__ = [
    "FEATURE_FAMILIES",
    "FEATURE_ORDER",
    "FEATURE_SCHEMA_VERSION",
    "FORBIDDEN_FEATURE_NAMES",
    "AnswerFields",
    "RoutingFeatureSnapshot",
    "is_forbidden_feature_name",
    "snapshot_from",
]
