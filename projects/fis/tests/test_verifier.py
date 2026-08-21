"""The deterministic verifier, checked directly for the first time (Suite v3).

Two things are pinned. Every mechanical check has a known-good and a known-bad
fixture, so a change to any of them is a deliberate act with a failing test attached.
And `collect_observed_ids` — the anti-fabrication boundary — harvests exactly what a
tool returned: the identifiers, `provider_ref`, and since Suite v3 `idempotency_key`
(`SUITE_V3_RELEASE_CONTRACT.md` § 2D), and nothing that only the answer key knows.
"""

from __future__ import annotations

import pytest

from fis_platform.verification.verifier import (
    VERIFIER_VERSION,
    collect_observed_ids,
    verify,
)
from schemas.routing import GOLD_FEATURE_NAMES
from schemas.scenario import ScenarioManifest
from schemas.tool import ToolCall


def _call(tool: str, status: str = "success", seq: int = 0) -> ToolCall:
    return ToolCall(tool=tool, version=1, args_hash="h", status=status, latency_ms=1, sequence=seq)


CALLS = [_call("get_case", seq=0), _call("get_webhook_history", seq=1),
         _call("get_ledger_entries", seq=2)]

# What get_webhook_history returns for S01's settlement: the retry carries the same
# idempotency key and was deduplicated. Shape from fis_platform/tool_broker/broker.py.
WEBHOOK_RESULT = {"get_webhook_history": {
    "deliveries": [
        {"delivery_id": "dlv_aaaaaaaaaaaa", "provider_event_id": "st-2001000-03",
         "event_type": "settlement.created", "payload_hash": "ph", "idempotency_key":
         "idem-st-2001000-03", "attempt": 1, "status": "processed", "received_at": "t"},
        {"delivery_id": "dlv_bbbbbbbbbbbb", "provider_event_id": "st-2001000-03",
         "event_type": "settlement.created", "payload_hash": "ph", "idempotency_key":
         "idem-st-2001000-03", "attempt": 2, "status": "deduplicated", "received_at": "t"},
    ],
    "normalized_events": [
        {"event_id": "evt_cccccccccccc", "provider_event_id": "st-2001000-03",
         "delivery_id": "dlv_aaaaaaaaaaaa", "normalized_type": "settlement.created",
         "mapping_version": 4, "raw_payload": {"account_id": "acc_2001000_01",
                                               "reference_id": "set_2001000_01"},
         "normalized_state": "settled", "created_at": "t"},
    ],
}}
CASE_RESULT = {"case_id": "case_2001000_01", "category": "webhook_duplicate",
               "subject_ids": {"customer_id": "cus_2001000_01", "card_id": "card_2001000_01"}}


def _output(**over):
    base = {
        "case_id": "case_2001000_01",
        "classification": "webhook_duplicate",
        "root_cause": {"label": "duplicate_webhook_handled", "confidence": 0.8},
        "facts": [
            {"claim": "The provider delivered st-2001000-03 twice with the same idempotency key",
             "source": "tool://get_webhook_history/dlv_aaaaaaaaaaaa",
             "entity_ids": ["dlv_aaaaaaaaaaaa", "dlv_bbbbbbbbbbbb", "idem-st-2001000-03"]},
            {"claim": "Exactly one ledger entry was posted for the settlement",
             "source": "tool://ledger/le_dddddddddddd",
             "entity_ids": ["le_dddddddddddd"]},
        ],
        "hypotheses": [],
        "recommended_next_action": "no_action_required",
        "escalation_required": False,
        "uncertainties": [],
        "summary": "Duplicate delivery was deduplicated; nothing is broken and no action is required.",
    }
    base.update(over)
    return base


LEDGER_RESULT = {"get_ledger_entries": {"accounts": [{"account_id": "acc_2001000_01"}],
                                        "entries": [{"entry_id": "le_dddddddddddd",
                                                     "reference_id": "set_2001000_01"}]}}
OBSERVED = collect_observed_ids([CASE_RESULT, WEBHOOK_RESULT, LEDGER_RESULT])


def test_verifier_version_is_recorded():
    assert VERIFIER_VERSION == "3"


# ------------------------------------------------------------ observed-id harvest
def test_harvest_includes_ids_provider_refs_and_idempotency_keys():
    assert {"case_2001000_01", "cus_2001000_01", "card_2001000_01"} <= OBSERVED
    assert {"dlv_aaaaaaaaaaaa", "dlv_bbbbbbbbbbbb", "evt_cccccccccccc", "le_dddddddddddd"} <= OBSERVED
    assert "st-2001000-03" in OBSERVED, "provider_event_id (an *_id key)"
    assert "acc_2001000_01" in OBSERVED, "ids nested in raw_payload are observed too"
    assert "idem-st-2001000-03" in OBSERVED, "Suite v3: the idempotency key the model was shown"


def test_harvest_ignores_non_identifier_fields_and_nulls():
    observed = collect_observed_ids([{"get_webhook_history": {"deliveries": [
        {"delivery_id": "dlv_x", "idempotency_key": None, "status": "processed",
         "payload_hash": "deadbeef", "event_type": "settlement.created", "attempt": 1}]}}])
    assert observed == {"dlv_x"}
    assert "processed" not in observed and "deadbeef" not in observed


def test_gold_only_fields_are_never_harvested_as_observed_ids():
    """The harvest walks tool results only. Even if a manifest were (wrongly) passed
    in, its gold fields carry list/enum values under keys that are not identifier
    keys, so nothing an answer key knows can turn a fabricated citation into an
    observed one — and every gold field name is one the router is forbidden to see."""
    manifest = ScenarioManifest(
        scenario_id="S01-2001000", seed=2001000, split="dev", category="webhook_duplicate",
        root_cause="duplicate_webhook_handled",
        required_evidence=["dlv_aaaaaaaaaaaa", "le_dddddddddddd"],
        acceptable_next_actions=["no_action_required"],
        forbidden_claims=["customer_double_charged"], distractor_event_ids=["auth_x"],
        case_id="case_2001000_01", subject_ids={"customer_id": "cus_2001000_01"},
    ).model_dump(mode="json")
    harvested = collect_observed_ids([manifest])
    # Only the model-facing identifiers the manifest happens to repeat (case, subject,
    # scenario id) come out; none of the gold answers do.
    assert harvested <= {"case_2001000_01", "cus_2001000_01", "S01-2001000"}
    assert "dlv_aaaaaaaaaaaa" not in harvested and "le_dddddddddddd" not in harvested
    assert "duplicate_webhook_handled" not in harvested and "auth_x" not in harvested
    assert {"root_cause", "required_evidence", "forbidden_claims", "acceptable_next_actions",
            "distractor_event_ids"} <= GOLD_FEATURE_NAMES


# ------------------------------------------------------------ verify(): known good
def test_known_good_output_passes_every_check():
    result, parsed = verify(_output(), CALLS, observed_ids=OBSERVED)
    assert parsed is not None
    assert result.passed, result.violations
    assert result.schema_valid
    assert set(result.checks) == {"schema_validation", "citation_required",
                                  "citation_resolves_to_call", "cited_ids_observed",
                                  "known_action_code", "confidence_supported", "facts_present"}


def test_a_cited_idempotency_key_the_tool_returned_is_not_a_fabrication():
    """E4-v2-dev S01-2001000 under Suite v2: 'cites an id no tool returned:
    idem-st-2001000-03' although get_webhook_history had returned exactly that."""
    result, _ = verify(_output(), CALLS, observed_ids=OBSERVED)
    assert result.checks["cited_ids_observed"] is True
    assert not [v for v in result.violations if "no tool returned" in v]


# ------------------------------------------------------------ verify(): known bad
def test_schema_invalid_output_fails_and_stops():
    result, parsed = verify({"case_id": "x"}, CALLS, observed_ids=OBSERVED)
    assert parsed is None and not result.passed and not result.schema_valid
    assert set(result.checks) == {"schema_validation"}


def test_a_key_no_tool_returned_is_a_fabrication():
    out = _output(facts=[
        {"claim": "The provider delivered st-2001000-03 twice with the same idempotency key",
         "source": "tool://get_webhook_history/dlv_aaaaaaaaaaaa",
         "entity_ids": ["idem-st-9999999-01"]},
        {"claim": "Exactly one ledger entry was posted for the settlement",
         "source": "tool://ledger/le_dddddddddddd", "entity_ids": ["le_dddddddddddd"]},
    ])
    result, _ = verify(out, CALLS, observed_ids=OBSERVED)
    assert result.checks["cited_ids_observed"] is False
    assert any("idem-st-9999999-01" in v for v in result.violations)


def test_a_fabricated_entity_id_is_caught():
    out = _output(facts=[
        {"claim": "The ledger holds an entry le_999 for this settlement",
         "source": "tool://ledger/le_999", "entity_ids": ["le_999"]},
        {"claim": "The webhook was delivered twice for the settlement",
         "source": "tool://get_webhook_history/dlv_aaaaaaaaaaaa", "entity_ids": ["dlv_aaaaaaaaaaaa"]},
    ])
    result, _ = verify(out, CALLS, observed_ids=OBSERVED)
    assert not result.passed
    assert "cites an id no tool returned: le_999" in result.violations


def test_citation_to_a_service_never_called_is_caught():
    calls = [_call("get_case"), _call("get_ledger_entries", seq=1)]      # no webhook call
    result, _ = verify(_output(), calls, observed_ids=OBSERVED)
    assert result.checks["citation_resolves_to_call"] is False
    assert any("never successfully called" in v for v in result.violations)


def test_failed_calls_do_not_count_as_called():
    calls = [_call("get_case"), _call("get_webhook_history", status="error", seq=1),
             _call("get_ledger_entries", seq=2)]
    result, _ = verify(_output(), calls, observed_ids=OBSERVED)
    assert result.checks["citation_resolves_to_call"] is False


def test_tool_name_and_service_name_are_both_accepted_in_citations():
    out = _output(facts=[
        {"claim": "Delivery dlv_aaaaaaaaaaaa was processed once", "source": "tool://webhook/dlv_aaaaaaaaaaaa",
         "entity_ids": ["dlv_aaaaaaaaaaaa"]},
        {"claim": "Entry le_dddddddddddd was posted once", "source": "tool://get_ledger_entries/le_dddddddddddd",
         "entity_ids": ["le_dddddddddddd"]},
    ])
    result, _ = verify(out, CALLS, observed_ids=OBSERVED)
    assert result.checks["citation_resolves_to_call"] is True, result.violations


def test_overconfidence_with_too_little_work_is_caught():
    out = _output(root_cause={"label": "duplicate_webhook_handled", "confidence": 0.95},
                  facts=[{"claim": "The webhook was delivered twice for the settlement",
                          "source": "tool://get_webhook_history/dlv_aaaaaaaaaaaa",
                          "entity_ids": ["dlv_aaaaaaaaaaaa"]}])
    result, _ = verify(out, [_call("get_webhook_history")], observed_ids=OBSERVED)
    assert result.checks["confidence_supported"] is False
    assert any("asserted after only 1" in v for v in result.violations)


def test_observed_ids_none_skips_the_fabrication_check_only():
    result, _ = verify(_output(), CALLS, observed_ids=None)
    assert "cited_ids_observed" not in result.checks
    assert result.passed


@pytest.mark.parametrize("bad_source", ["ledger/le_1", "tool://Ledger/le_1", "tool://ledger"])
def test_malformed_citations_are_rejected_by_the_schema_before_the_verifier(bad_source):
    out = _output(facts=[{"claim": "Some claim of substance", "source": bad_source, "entity_ids": []}])
    result, parsed = verify(out, CALLS, observed_ids=OBSERVED)
    assert parsed is None and not result.schema_valid
