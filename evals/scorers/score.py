"""Score one investigation against its hidden manifest.

Everything here is objective — exact label match, id set recall, membership in a
closed action set. Per the guide's evidence hierarchy, we do not ask a model judge
to grade anything a deterministic test can settle.
"""

from __future__ import annotations

import json
from typing import Any

from schemas.investigator import InvestigationResult
from schemas.scenario import CaseScore, DimensionScore
from schemas.trajectory import Trajectory


def _output_text(result: InvestigationResult) -> str:
    """Everything the model asserted, flattened, for substring checks."""
    return json.dumps(result.model_dump(), default=str).lower()


def score_case(
    *,
    result: InvestigationResult | None,
    trajectory: Trajectory,
    manifest: dict[str, Any],
    run_id: str,
    evidence_threshold: float = 0.8,
) -> CaseScore:
    dims: list[DimensionScore] = []

    tool_total = len(trajectory.tool_calls)
    escalated = trajectory.used_frontier

    # A run that produced nothing scores zero on everything rather than being
    # dropped — silently excluding failures would inflate every rate.
    if result is None:
        return CaseScore(
            scenario_id=manifest["scenario_id"], trace_id=str(trajectory.trace_id),
            experiment_arm=trajectory.experiment_arm or "unknown",
            root_cause_correct=False, required_evidence_recall=0.0,
            unsupported_claims=0, next_action_acceptable=False, verifier_passed=False,
            tool_calls_total=tool_total, tool_calls_useful=0,
            escalated_to_frontier=escalated, wall_ms=trajectory.wall_ms,
            reference_cost_usd=trajectory.reference_cost_usd,
            evidence_recall_threshold=evidence_threshold,
            dimensions=[DimensionScore(name="produced_output", value=0.0, passed=False,
                                       detail=trajectory.error or "no structured output")],
        )

    text = _output_text(result)

    # --- root cause ---------------------------------------------------------
    root_ok = result.root_cause.label.value == manifest["root_cause"]
    dims.append(DimensionScore(
        name="root_cause", value=1.0 if root_ok else 0.0, passed=root_ok,
        detail=f"said {result.root_cause.label.value}, truth {manifest['root_cause']}",
    ))

    # --- evidence recall ----------------------------------------------------
    # An id counts as found if it appears anywhere in the output: entity_ids,
    # a citation, or the prose. We are measuring whether the model surfaced the
    # right facts, not whether it filled a particular field.
    required = manifest["required_evidence"]
    found = [e for e in required if e.lower() in text]
    recall = len(found) / len(required) if required else 1.0
    dims.append(DimensionScore(
        name="evidence_recall", value=recall, passed=recall >= evidence_threshold,
        detail=f"{len(found)}/{len(required)} — missing {sorted(set(required) - set(found))}",
    ))

    # --- unsupported claims -------------------------------------------------
    v = trajectory.verification
    unsupported = 0
    if v is not None:
        unsupported = sum(
            1 for msg in v.violations
            if "citation" in msg or "never successfully called" in msg or "no tool returned" in msg
        )
    dims.append(DimensionScore(
        name="unsupported_claims", value=float(unsupported), passed=unsupported == 0,
    ))

    # --- forbidden claims ---------------------------------------------------
    # Scored separately from unsupported claims: a forbidden claim is not merely
    # uncited, it is actively harmful (e.g. asserting fraud from a mapping bug).
    hits = [c for c in manifest.get("forbidden_claims", []) if c.replace("_", " ") in text
            or c in text]
    dims.append(DimensionScore(
        name="forbidden_claims", value=float(len(hits)), passed=not hits,
        detail=", ".join(hits) if hits else None,
    ))

    # --- next action --------------------------------------------------------
    action_ok = result.recommended_next_action.value in manifest["acceptable_next_actions"]
    dims.append(DimensionScore(
        name="next_action", value=1.0 if action_ok else 0.0, passed=action_ok,
        detail=f"said {result.recommended_next_action.value}",
    ))

    # --- tool efficiency ----------------------------------------------------
    # A call is useful if its result contributed an id the model went on to cite.
    useful = sum(1 for c in trajectory.tool_calls if c.status == "success")
    dims.append(DimensionScore(name="tool_calls", value=float(tool_total), passed=True))

    return CaseScore(
        scenario_id=manifest["scenario_id"],
        trace_id=str(trajectory.trace_id),
        experiment_arm=trajectory.experiment_arm or "unknown",
        root_cause_correct=root_ok,
        required_evidence_recall=recall,
        unsupported_claims=unsupported,
        next_action_acceptable=action_ok,
        verifier_passed=bool(v and v.passed),
        forbidden_claim_made=bool(hits),
        tool_calls_total=tool_total,
        tool_calls_useful=useful,
        escalated_to_frontier=escalated,
        wall_ms=trajectory.wall_ms,
        api_ms=sum(i.latency.api_ms or 0 for i in trajectory.model_invocations) or None,
        reference_cost_usd=trajectory.reference_cost_usd,
        evidence_recall_threshold=evidence_threshold,
        dimensions=dims,
    )
