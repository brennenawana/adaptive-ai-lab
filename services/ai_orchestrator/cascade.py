"""R4 — deterministic weak→strong cascade.

    request
      -> weak / local model
      -> production-available checks
           parse or schema failure  -> strong
           verifier failure          -> strong
           unsupported claim         -> strong
           checks pass               -> accept the weak result

Not learned routing. The gate reads only what a production deployment would have:
whether the weak model produced a schema-valid object, and what the deterministic
verifier said about it. Root cause, required evidence, scenario id — anything the
scorer knows — is never consulted; `RouterDecision.features` is filled from the
verifier alone and `test_routing_no_gold_leak.py` keeps it that way.

The three named signals are nested (an unsupported claim IS a verifier violation;
no output IS a verifier failure), so the policies are the natural prefixes of that
nesting: escalate on nothing (weak only), on parse/schema failure only, or on any
verifier failure. That is deliberately the whole policy space for R4 — the point is
to measure how much of the oracle a gate this simple recovers, not to chase it.

The strong stage re-runs `investigate()` with the strong model on the same case: in
FIXED_EVIDENCE mode the plan is deterministic, so it sees the identical bundle the
weak stage saw. The returned trajectory is the strong stage's, with the weak stage's
model invocation prepended so cost, tokens and wall time cover both stages, and the
decision recorded on `Trajectory.router`. The weak stage's own trajectory is returned
alongside so an eval can score "would the weak result have passed" — that is how
unnecessary escalations and false accepts are counted after the fact.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fis_platform.model_gateway import ModelGateway
from fis_platform.tool_broker.broker import ToolBroker
from schemas.investigator import InvestigationResult
from schemas.trajectory import RouterDecision, Trajectory

from .investigate import EvidenceMode, investigate
from .prompts import DEFAULT_PROMPT


class EscalationPolicy(StrEnum):
    NONE = "none"          # weak only — the control
    PARSE = "parse"        # escalate only when the weak model produced no usable object
    VERIFIER = "verifier"  # escalate on any deterministic verifier failure (incl. parse)


# Substrings the scorer uses to count a verifier violation as an unsupported claim.
# Reused verbatim rather than redefined, so the router's notion of "unsupported"
# is the scorer's — a routing signal that drifted from the metric would look like a
# routing result.
_UNSUPPORTED_MARKERS = ("citation", "never successfully called", "no tool returned")


@dataclass(frozen=True)
class EscalationSignals:
    produced_output: bool     # a schema-valid InvestigationResult came back
    verifier_passed: bool
    unsupported_claims: int
    violations: tuple[str, ...]

    def as_features(self) -> dict[str, float]:
        return {
            "produced_output": float(self.produced_output),
            "verifier_passed": float(self.verifier_passed),
            "unsupported_claims": float(self.unsupported_claims),
        }


def signals_from(result: InvestigationResult | None, traj: Trajectory) -> EscalationSignals:
    v = traj.verification
    violations = tuple(v.violations) if v else ()
    unsupported = sum(1 for m in violations if any(k in m for k in _UNSUPPORTED_MARKERS))
    return EscalationSignals(
        produced_output=result is not None,
        verifier_passed=bool(v and v.passed) and result is not None,
        unsupported_claims=unsupported,
        violations=violations,
    )


def should_escalate(sig: EscalationSignals, policy: EscalationPolicy) -> tuple[bool, str | None]:
    if policy is EscalationPolicy.NONE:
        return False, None
    if not sig.produced_output:
        return True, "no_output"
    if policy is EscalationPolicy.PARSE:
        return False, None
    if sig.unsupported_claims:
        return True, "unsupported_claims"
    if not sig.verifier_passed:
        return True, "verifier_failed"
    return False, None


@dataclass
class CascadeOutcome:
    result: InvestigationResult | None
    trajectory: Trajectory            # what the cascade returned (weak's or strong's)
    weak_result: InvestigationResult | None
    weak_trajectory: Trajectory       # always the weak stage, for after-the-fact scoring
    decision: RouterDecision


async def investigate_cascade(
    case_id: str,
    *,
    gateway: ModelGateway,
    broker: ToolBroker,
    weak_ref: str,
    strong_ref: str,
    policy: EscalationPolicy,
    experiment_arm: str,
    mode: EvidenceMode = EvidenceMode.FIXED_EVIDENCE,
    scenario_id: str | None = None,
    weak_prompt_ref: str = DEFAULT_PROMPT,
    strong_prompt_ref: str = DEFAULT_PROMPT,
    runtime_context: dict[str, str] | None = None,
) -> CascadeOutcome:
    ctx = dict(runtime_context or {})
    ctx["cascade_policy"] = policy.value

    weak_result, weak_traj = await investigate(
        case_id, gateway=gateway, broker=broker, model_ref=weak_ref,
        experiment_arm=experiment_arm, mode=mode, scenario_id=scenario_id,
        prompt_ref=weak_prompt_ref, runtime_context={**ctx, "stage": "weak"},
    )
    sig = signals_from(weak_result, weak_traj)
    escalate, reason = should_escalate(sig, policy)
    decision = RouterDecision(
        selected_specialist=strong_ref if escalate else weak_ref,
        confidence=1.0,                       # a deterministic gate is never unsure
        escalated=escalate,
        escalation_reason=reason,
        features=sig.as_features(),
    )
    weak_traj.router = decision

    if not escalate:
        return CascadeOutcome(weak_result, weak_traj, weak_result, weak_traj, decision)

    # The weak stage's tool calls are dropped from the merged record deliberately:
    # the strong stage re-gathers the same deterministic bundle, and counting the
    # plan twice would double tool_calls_total for every escalated case.
    weak_calls = list(broker.calls)
    broker.calls.clear()
    strong_result, strong_traj = await investigate(
        case_id, gateway=gateway, broker=broker, model_ref=strong_ref,
        experiment_arm=experiment_arm, mode=mode, scenario_id=scenario_id,
        prompt_ref=strong_prompt_ref, runtime_context={**ctx, "stage": "strong"},
    )
    broker.calls[:0] = weak_calls   # restore for anyone inspecting the broker afterwards

    strong_traj.model_invocations = weak_traj.model_invocations + strong_traj.model_invocations
    strong_traj.router = decision
    strong_traj.runtime_context["weak_trace_id"] = str(weak_traj.trace_id)
    strong_traj.runtime_context["stage"] = "cascade"
    return CascadeOutcome(strong_result, strong_traj, weak_result, weak_traj, decision)
