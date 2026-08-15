"""Deterministic verifier.

Guide's boundary: reject "missing citations, invalid IDs, impossible amounts,
unsupported facts, unknown action codes, or schemas that do not validate. It should
not attempt to judge every reasoning nuance."

So every check here is mechanical and needs no model. Anything requiring judgement
belongs in the scorer (against ground truth) or a rubric — not here. That separation
matters: the verifier runs in production where no answer key exists.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import ValidationError

from schemas.investigator import InvestigationResult, NextAction
from schemas.tool import ToolCall
from schemas.trajectory import VerificationResult

_SOURCE_RE = re.compile(r"^tool://(?P<service>[a-z_]+)/(?P<ref>[A-Za-z0-9_./:-]+)$")

# Which service a tool's evidence is attributed to, for citation checking.
_TOOL_SERVICE = {
    "get_case": "case",
    "get_customer": "customer",
    "get_verifications": "identity",
    "get_processor_activity": "processor",
    "get_ledger_entries": "ledger",
    "get_risk_alerts": "risk",
    "get_webhook_history": "webhook",
    "search_runbooks": "knowledge",
}


def verify(
    raw_output: Any,
    tool_calls: list[ToolCall],
    *,
    observed_ids: set[str] | None = None,
) -> tuple[VerificationResult, InvestigationResult | None]:
    """Run every deterministic check.

    `observed_ids` is the set of entity ids the tools actually returned this run. It
    is what turns "cites a plausible-looking id" into "cites an id we actually saw" —
    the difference between a citation and a fabrication.
    """
    checks: dict[str, bool] = {}
    violations: list[str] = []
    observed_ids = observed_ids or set()

    # 1. schema -------------------------------------------------------------
    parsed: InvestigationResult | None = None
    try:
        parsed = (
            raw_output if isinstance(raw_output, InvestigationResult)
            else InvestigationResult.model_validate(raw_output)
        )
        checks["schema_validation"] = True
    except ValidationError as exc:
        checks["schema_validation"] = False
        violations.append(f"schema invalid: {exc.error_count()} error(s); "
                          f"first: {exc.errors()[0].get('msg')}")
        # Nothing downstream can be checked without a parsed object.
        return VerificationResult(passed=False, checks=checks, violations=violations,
                                  schema_valid=False), None

    # 2. every fact carries a well-formed citation --------------------------
    bad_sources = [f.source for f in parsed.facts if not _SOURCE_RE.match(f.source)]
    checks["citation_required"] = not bad_sources
    violations += [f"malformed citation: {s}" for s in bad_sources]

    # 3. citations point at something we actually called --------------------
    # Accept BOTH the service name and the tool name in the middle segment.
    # Models naturally cite the tool they invoked ("tool://get_ledger_entries/le_1"),
    # which is at least as informative as the service. Rejecting it would penalise
    # correct behaviour and inflate the unsupported-claim rate with harness noise.
    succeeded = [c for c in tool_calls if c.status == "success"]
    called_refs = {c.tool for c in succeeded} | {
        s for c in succeeded if (s := _TOOL_SERVICE.get(c.tool))
    }
    uncalled = [
        f.source for f in parsed.facts
        if (m := _SOURCE_RE.match(f.source)) and m.group("service") not in called_refs
    ]
    checks["citation_resolves_to_call"] = not uncalled
    violations += [
        f"cites a service that was never successfully called: {s}" for s in uncalled
    ]

    # 4. cited entity ids were actually observed ----------------------------
    # This is the anti-fabrication check. A model that invents "le_999" produces a
    # perfectly well-formed citation; only cross-referencing what the tools returned
    # catches it.
    if observed_ids:
        fabricated = []
        for f in parsed.facts:
            for eid in f.entity_ids:
                if eid not in observed_ids:
                    fabricated.append(eid)
        checks["cited_ids_observed"] = not fabricated
        violations += [f"cites an id no tool returned: {e}" for e in fabricated]

    # 5. action code is in the closed set -----------------------------------
    checks["known_action_code"] = parsed.recommended_next_action in set(NextAction)

    # 6. confidence is calibrated to having done the work -------------------
    # High confidence with almost no evidence gathered is a reliable overreach
    # signal, and it is mechanical enough to belong here rather than in a rubric.
    successful_calls = sum(1 for c in tool_calls if c.status == "success")
    overconfident = parsed.root_cause.confidence >= 0.9 and successful_calls < 2
    checks["confidence_supported"] = not overconfident
    if overconfident:
        violations.append(
            f"confidence {parsed.root_cause.confidence} asserted after only "
            f"{successful_calls} successful tool call(s)"
        )

    # 7. facts must not be empty of substance -------------------------------
    checks["facts_present"] = len(parsed.facts) >= 1

    return (
        VerificationResult(
            passed=all(checks.values()),
            checks=checks,
            violations=violations,
            schema_valid=True,
        ),
        parsed,
    )


def collect_observed_ids(results: list[Any]) -> set[str]:
    """Walk tool results and harvest every id-looking value.

    Deliberately permissive about shape — tool payloads are nested dicts and lists,
    and a missed id would produce a false fabrication violation, which is worse than
    an occasional missed catch.
    """
    found: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, str) and (k.endswith("_id") or k == "provider_ref"):
                    found.add(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for r in results:
        walk(r)
    return found
