"""The eight read-only tools, per the guide's §12 contract table.

Descriptions are written to state WHEN to reach for each tool, not just what it
returns — ToolDefinition enforces that, because trigger conditions in the description
are the single biggest lever on tool-selection accuracy.
"""

from __future__ import annotations

from schemas.tool import ToolDefinition, ToolKind

_STR = {"type": "string"}


def _obj(props: dict, required: list[str]) -> dict:
    return {"type": "object", "properties": props, "required": required,
            "additionalProperties": False}


TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="get_case", version=1, kind=ToolKind.READ, owning_service="case_service",
        description=(
            "Fetch a case: category, subject ids, summary, status and timestamps. "
            "Use this first on every investigation — it names the customer, account "
            "or card the rest of your queries need."
        ),
        input_schema=_obj({"case_id": _STR}, ["case_id"]),
        output_schema=_obj({"case_id": _STR, "category": _STR, "subject_ids": {"type": "object"},
                            "summary": _STR, "status": _STR, "opened_at": _STR}, ["case_id"]),
        verifiers=["case_exists", "ids_well_formed"],
    ),
    ToolDefinition(
        name="get_customer", version=1, kind=ToolKind.READ, owning_service="customer_service",
        description=(
            "Fetch a customer profile and onboarding state. Use when the case concerns "
            "account access, onboarding progress, or you need to confirm the customer "
            "referenced by a card or account."
        ),
        input_schema=_obj({"customer_id": _STR}, ["customer_id"]),
        output_schema=_obj({"customer_id": _STR, "onboarding_state": _STR, "country": _STR},
                           ["customer_id"]),
        verifiers=["customer_matches_case"],
    ),
    ToolDefinition(
        name="get_verifications", version=1, kind=ToolKind.READ,
        owning_service="identity_service",
        description=(
            "List KYC/identity verification steps for a customer with statuses and "
            "reason codes. Use this whenever onboarding is incomplete, a card is not "
            "activated, or the customer disputes a verification outcome."
        ),
        input_schema=_obj({"customer_id": _STR}, ["customer_id"]),
        output_schema={"type": "array", "items": {"type": "object"}},
        verifiers=["status_time_consistent"],
    ),
    ToolDefinition(
        name="get_processor_activity", version=1, kind=ToolKind.READ,
        owning_service="processor_sim",
        description=(
            "Authorizations, reversals and settlements for a card. Use when the case "
            "involves a decline, a disputed charge, or an amount that needs comparing "
            "against the ledger."
        ),
        input_schema=_obj({"card_id": _STR}, ["card_id"]),
        output_schema=_obj({"authorizations": {"type": "array"}, "settlements": {"type": "array"}},
                           []),
        verifiers=["amount_currency_valid", "ids_well_formed"],
    ),
    ToolDefinition(
        name="get_ledger_entries", version=1, kind=ToolKind.READ, owning_service="ledger_service",
        description=(
            "Ledger postings and balances for an account. Use when the case involves a "
            "reconciliation variance, a balance dispute, or you need the authoritative "
            "amount to compare against a processor settlement."
        ),
        input_schema=_obj({"account_id": _STR, "limit": {"type": "integer"}}, ["account_id"]),
        output_schema=_obj({"account": {"type": "object"}, "entries": {"type": "array"}}, []),
        verifiers=["debits_credits_valid", "references_resolve"],
    ),
    ToolDefinition(
        name="get_risk_alerts", version=1, kind=ToolKind.READ, owning_service="risk_service",
        description=(
            "Risk and AML alerts for a customer with rule codes, severity and "
            "disposition. Use when a card or account is restricted, or before "
            "concluding that a decline was purely a processor decision."
        ),
        input_schema=_obj({"customer_id": _STR}, ["customer_id"]),
        output_schema={"type": "array", "items": {"type": "object"}},
        verifiers=["alert_ids_valid"],
    ),
    ToolDefinition(
        name="get_webhook_history", version=1, kind=ToolKind.READ,
        owning_service="webhook_gateway",
        description=(
            "Delivery attempts for a provider event id: attempt number, dedupe status, "
            "idempotency key. Use when a duplicate, missing or repeated downstream "
            "effect is suspected, or when an event seems to have been processed twice."
        ),
        input_schema=_obj({"provider_event_id": _STR}, ["provider_event_id"]),
        output_schema=_obj({"deliveries": {"type": "array"}, "normalized_events": {"type": "array"}},
                           []),
        verifiers=["idempotency_state_valid"],
    ),
    ToolDefinition(
        name="search_runbooks", version=1, kind=ToolKind.SEARCH,
        owning_service="knowledge_service",
        description=(
            "Search synthetic operational runbooks and policies. Use when you need the "
            "documented procedure for a case category, or to confirm which next action "
            "is sanctioned before recommending it."
        ),
        input_schema=_obj({"query": _STR, "category": _STR}, ["query"]),
        output_schema={"type": "array", "items": {"type": "object"}},
        verifiers=["citation_valid"],
    ),
]

BY_NAME: dict[str, ToolDefinition] = {t.name: t for t in TOOLS}


def openai_tool_specs() -> list[dict]:
    """Render to the OpenAI/Anthropic function-calling shape the model sees."""
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.input_schema,
            },
        }
        for t in TOOLS
    ]
