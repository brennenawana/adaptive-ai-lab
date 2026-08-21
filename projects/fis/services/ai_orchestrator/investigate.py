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

import hashlib
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

from .prompts import DEFAULT_PROMPT, PROMPTS

WORKFLOW = "fintech_case_investigation"
WORKFLOW_VERSION = "1.0.0"
PROMPT_VERSION = "1"

# The generation budget every arm was baselined with (E2 … R4, R3). It is a
# decoding-config factor, not a model property: R3 showed the candidate weak arm
# still inside `<think>` at this cap on 29/48 dev cases, and R3b varies exactly this
# number for both weak arms. Callers that do not say otherwise get the historical
# value, so every recorded run stays reproducible from its make target.
DEFAULT_MAX_TOKENS = 4096


class EvidenceMode(StrEnum):
    AGENTIC = "agentic"
    FIXED_EVIDENCE = "fixed_evidence"


# Kept as a module-level name because callers and tests import it. The registry in
# `prompts.py` is the source of truth; this is its default entry.
SYSTEM_PROMPT = PROMPTS[DEFAULT_PROMPT]


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


def _phase_two(case: dict[str, Any], results: list[Any],
               limit: int = 6) -> list[tuple[str, dict]]:
    """Follow what phase one discovered into evidence that is not addressable yet.

    Two hops, for two different reasons:

    * **Webhook and integration evidence** is addressed by `provider_event_id`,
      which is not knowable until a settlement, authorization or verification has
      been read. Without this hop S01/S02 (duplicate delivery), S06, S07 and S09
      (stale mapping) can never reach their required evidence.
    * **Vendor clustering** is addressed by vendor, and is invisible to every
      customer-keyed query. Without it S04 cannot be distinguished from an ordinary
      KYC hold by any amount of reasoning.

    Both are the same failure if left out: evidence that exists, is required, and is
    unreachable — which measures the harness rather than the model.
    """
    refs: list[str] = []
    vendors: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "provider_ref" and isinstance(v, str):
                    refs.append(v)
                elif k == "vendor" and isinstance(v, str):
                    vendors.append(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(results)

    def dedupe(xs: list[str]) -> list[str]:
        out: list[str] = []
        for x in xs:
            if x not in out:
                out.append(x)
        return out

    plan = [("get_webhook_history", {"provider_event_id": r})
            for r in dedupe(refs)[:limit]]

    if cid := (case.get("subject_ids") or {}).get("customer_id"):
        plan += [("get_verifications", {"customer_id": cid, "vendor": v, "window_hours": 2})
                 for v in dedupe(vendors)[:2]]
    return plan


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
    prompt_ref: str = DEFAULT_PROMPT,
    user: str = "eval-runner",
    runtime_context: dict[str, str] | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
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
        runtime_context=dict(runtime_context or {}),
    )

    # Resolved here rather than defaulted in the signature so an unknown ref fails
    # loudly at the start of a run instead of silently scoring 96 cases against the
    # baseline prompt and reporting them as the variant.
    if prompt_ref not in PROMPTS:
        raise KeyError(f"unknown prompt {prompt_ref!r}; known: {sorted(PROMPTS)}")
    system_prompt = PROMPTS[prompt_ref]

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
        for tool, args in _phase_two(case, results):
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
            system=system_prompt,
            messages=transcript,
            json_schema=schema if mode is EvidenceMode.FIXED_EVIDENCE else None,
            tools=openai_tool_specs() if mode is EvidenceMode.AGENTIC else None,
            max_tokens=max_tokens,
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
            stop_reason=resp.stop_reason, routing=resp.routing,
            runtime_fingerprint=resp.runtime_fingerprint,
            max_tokens=max_tokens,
            reasoning_chars=resp.reasoning_chars,
            content_chars=len(resp.text) if resp.text else 0,
            # M0/WP-A: reasoning text whenever the adapter exposes it; the raw answer
            # text only when the strict-grammar parse produced no object — a parsed
            # answer is already persisted in learning.model_outputs, an unparseable
            # one (the cap-hit population) would otherwise leave no record at all.
            reasoning_text=resp.reasoning_content,
            content_text=(resp.text or None) if resp.structured is None else None,
            timings=resp.timings,
        ))

        if resp.is_error:
            if (resp.error or "").startswith("api_error_status="):
                # An upstream API failure (5xx/429 through the CLI) is not a model
                # answer. Raise so the runner skips the case unpersisted and --resume
                # retries it, instead of scoring a transient outage as a no-output.
                raise RuntimeError(f"upstream API error on {model_ref}: {resp.error}")
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

    # Digest of the model's raw text, so two arms can be compared for exact
    # equivalence after the fact (R1: direct path vs routed path) without persisting
    # the output itself. Greedy decoding on the same backend should reproduce this.
    if resp and resp.text:
        traj.output_digest = hashlib.sha256(resp.text.encode("utf-8")).hexdigest()

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
