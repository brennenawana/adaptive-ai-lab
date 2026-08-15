"""The investigation workflow: classify -> authorize -> gather -> generate -> verify -> capture.

Two evidence modes, and the distinction is the backbone of the experiment matrix:

  AGENTIC       the model chooses tools itself, iteratively. Measures tool strategy
                AND reasoning together.
  FIXED_EVIDENCE the orchestrator gathers evidence with a deterministic policy and
                hands the identical bundle to whichever model is under test.
                Measures reasoning ALONE.

E4's question is "what is the capability ceiling given the same evidence" — the
guide's own framing is "replay the same evidence to a stronger model". That only
works in FIXED_EVIDENCE mode. Running E2 agentic and E4 agentic would confound a
reasoning difference with a tool-strategy difference and answer neither question.
"""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any

from fis_platform.model_gateway import GenerationRequest, Message, ModelGateway
from fis_platform.tool_broker.broker import ToolBroker
from fis_platform.tool_broker.definitions import openai_tool_specs
from fis_platform.verification.verifier import collect_observed_ids, verify
from schemas.common import ModelTier, new_trace_id, utc_now
from schemas.investigator import InvestigationResult
from schemas.trajectory import ModelInvocation, Trajectory

WORKFLOW = "fintech_case_investigation"
WORKFLOW_VERSION = "1.0.0"
PROMPT_VERSION = "1"


class EvidenceMode(StrEnum):
    AGENTIC = "agentic"
    FIXED_EVIDENCE = "fixed_evidence"


SYSTEM_PROMPT = """You are an operations investigator for Northstar Bank.

Given a case, determine the most likely root cause from the evidence available.

Rules:
- Separate facts from hypotheses. A fact is something a tool result directly shows;
  anything inferred, suspected or probable is a hypothesis, not a fact.
- Every fact must cite its source as tool://<tool_name>/<entity_id>, where
  <tool_name> is the tool the evidence came from and <entity_id> is the specific
  record id. For example: tool://get_ledger_entries/le_001539
- Put the specific record ids you relied on in each fact's entity_ids list.
- Do not assert customer fraud, or any conclusion the evidence does not directly
  support. An open alert is a pattern match, not a finding.
- The surface symptom is often not the root cause. A decline may be caused by an
  upstream risk hold; an inactive card may be waiting on identity verification.
- "Nothing is wrong" is a legitimate conclusion when the authoritative systems agree.
- Set confidence honestly. Low confidence with correct reasoning is better than
  high confidence you cannot support.

Respond only via the provided schema."""


def _phase_one(case: dict[str, Any]) -> list[tuple[str, dict]]:
    """Everything reachable from the case's subject ids alone.

    Keyed off customer_id wherever possible rather than the specific id the case
    happens to name: a case that mentions only an account still needs that
    customer's cards, and vice versa. An earlier version keyed strictly off the
    named subject and made required evidence unreachable for four scenario classes
    — which measured the harness, not the model.
    """
    subj = case.get("subject_ids") or {}
    plan: list[tuple[str, dict]] = []
    cid = subj.get("customer_id")

    if cid:
        plan += [
            ("get_customer", {"customer_id": cid}),
            ("get_verifications", {"customer_id": cid}),
            ("get_risk_alerts", {"customer_id": cid}),
            ("get_processor_activity", {"customer_id": cid}),
            ("get_ledger_entries", {"customer_id": cid}),
        ]
    else:
        if card := subj.get("card_id"):
            plan.append(("get_processor_activity", {"card_id": card}))
        if acct := subj.get("account_id"):
            plan.append(("get_ledger_entries", {"account_id": acct}))
    return plan


def _phase_two(results: list[Any], limit: int = 6) -> list[tuple[str, dict]]:
    """Follow provider references discovered in phase one into the event trail.

    Webhook and integration evidence is addressed by provider_event_id, which is
    not knowable until a settlement or authorization has been read. Without this
    hop, S01/S02 (duplicate delivery) and S09 (stale mapping) can never reach
    their required evidence.
    """
    refs: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "provider_ref" and isinstance(v, str):
                    refs.append(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(results)
    seen: list[str] = []
    for r in refs:
        if r not in seen:
            seen.append(r)
    return [("get_webhook_history", {"provider_event_id": r}) for r in seen[:limit]]


async def investigate(
    case_id: str,
    *,
    gateway: ModelGateway,
    broker: ToolBroker,
    model_ref: str,
    experiment_arm: str,
    mode: EvidenceMode = EvidenceMode.FIXED_EVIDENCE,
    scenario_id: str | None = None,
    max_tool_rounds: int = 8,
    user: str = "eval-runner",
) -> tuple[InvestigationResult | None, Trajectory]:
    traj = Trajectory(
        trace_id=new_trace_id(),
        workflow=WORKFLOW,
        workflow_version=WORKFLOW_VERSION,
        task_type="ops.investigate",
        user=user,
        case_id=case_id,
        scenario_id=scenario_id,
        experiment_arm=experiment_arm,
        permissions_snapshot={"read_only": True},
    )

    # --- gather -------------------------------------------------------------
    case, case_call = broker.invoke("get_case", {"case_id": case_id})
    if case_call.status != "success":
        traj.tool_calls = list(broker.calls)
        traj.error = f"case lookup failed: {case}"
        return None, traj

    results: list[Any] = [case]
    transcript: list[Message] = []

    if mode is EvidenceMode.FIXED_EVIDENCE:
        for tool, args in _phase_one(case):
            res, _ = broker.invoke(tool, args)
            results.append({tool: res})
        # Second hop: provider refs only exist once phase one has run.
        for tool, args in _phase_two(results):
            res, _ = broker.invoke(tool, args)
            results.append({tool: res})

        bundle = json.dumps(results, indent=2, default=str)
        transcript.append(Message(
            role="user",
            content=(
                f"Case {case_id}.\n\nEvidence gathered from the platform:\n\n{bundle}\n\n"
                "Determine the root cause."
            ),
        ))
    else:
        transcript.append(Message(
            role="user",
            content=(
                f"Investigate case {case_id}. Use the available tools to gather "
                f"evidence before concluding.\n\nCase record:\n{json.dumps(case, default=str, indent=2)}"
            ),
        ))

    schema = InvestigationResult.model_json_schema()

    # --- generate (with a tool loop in agentic mode) ------------------------
    resp = None
    for _round in range(max_tool_rounds if mode is EvidenceMode.AGENTIC else 1):
        req = GenerationRequest(
            model_ref=model_ref,
            system=SYSTEM_PROMPT,
            messages=transcript,
            json_schema=schema if mode is EvidenceMode.FIXED_EVIDENCE else None,
            tools=openai_tool_specs() if mode is EvidenceMode.AGENTIC else None,
            max_tokens=4096,
            trace_id=str(traj.trace_id),
            purpose="investigate",
        )
        resp = await gateway.generate(req)

        manifest = gateway.registry.resolve(model_ref)
        traj.model_invocations.append(ModelInvocation(
            tier=manifest.tier, provider=manifest.provider,
            model_id=resp.model_id, canonical_model=resp.canonical_model,
            quantization=manifest.quantization, prompt_version=PROMPT_VERSION,
            usage=resp.usage, cost=resp.cost, latency=resp.latency,
        ))

        if resp.is_error:
            traj.error = resp.error
            traj.tool_calls = list(broker.calls)
            return None, traj

        if not resp.tool_calls:
            break

        # Execute what the model asked for and feed the results back.
        transcript.append(Message(role="assistant", content=resp.text or ""))
        for tc in resp.tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            res, _ = broker.invoke(name, args)
            results.append({name: res})
            transcript.append(Message(
                role="user",
                content=f"Result of {name}:\n{json.dumps(res, default=str)[:4000]}",
            ))

    traj.tool_calls = list(broker.calls)

    # --- verify -------------------------------------------------------------
    payload: Any = resp.structured if resp and resp.structured else None
    if payload is None and resp and resp.text:
        try:
            payload = json.loads(resp.text)
        except json.JSONDecodeError:
            payload = None

    if payload is None:
        traj.error = "model produced no parseable structured output"
        traj.verification = None
        return None, traj

    payload.setdefault("case_id", case_id)
    verification, parsed = verify(payload, traj.tool_calls,
                                  observed_ids=collect_observed_ids(results))
    traj.verification = verification
    return parsed, traj
