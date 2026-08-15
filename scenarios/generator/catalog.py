"""The twelve seeded scenario classes.

Each builder writes authoritative records across the service schemas and returns the
hidden manifest. The investigator can query the former and never the latter.

Design rule followed throughout: the *surface symptom* should rarely be the root
cause. A scenario where the first tool call gives the answer measures nothing —
the skill under test is combining evidence across services.
"""

from __future__ import annotations

from typing import Callable

from .world import World, minor_units

# scenario code -> builder
BUILDERS: dict[str, Callable[[World], dict]] = {}


def scenario(code: str):
    def deco(fn: Callable[[World], dict]) -> Callable[[World], dict]:
        BUILDERS[code] = fn
        return fn
    return deco


def _base(w: World, *, state: str = "active", card_status: str = "active"):
    cus = w.add_customer(state=state)
    acc = w.add_account(cus)
    card = w.add_card(cus, acc, status=card_status)
    return cus, acc, card


def _distractors(w: World, cus: dict, card: dict, n: int = 3) -> list[str]:
    """Unrelated but plausible activity.

    Without these a model can score well by summarising everything it sees;
    distractors make evidence *selection* the thing being measured.
    """
    ids: list[str] = []
    for _ in range(n):
        a = w.add_auth(card, state="approved", minutes=w.rng.randint(5, 240))
        w.add_settlement(a, minutes=w.rng.randint(30, 200))
        ids.append(a["auth_id"])
    if w.rng.random() < 0.5:
        alert = w.add_alert(cus, rule_code="VELOCITY_LOW", severity="low", status="cleared")
        ids.append(alert["alert_id"])
    return ids


# ---------------------------------------------------------------------------- S01
@scenario("S01")
def duplicate_webhook_handled(w: World) -> dict:
    """Provider delivered the same event twice; dedupe worked. Nothing is broken.

    The trap: an operator (and a model) sees "duplicate" and assumes double-charge.
    Correct answer is that the system behaved properly.
    """
    cus, acc, card = _base(w)
    auth = w.add_auth(card)
    pev = w.ids.provider("evt")

    d1 = w.add_delivery(provider_event_id=pev, event_type="settlement.created", attempt=1,
                        status="processed", idempotency_key=f"idem-{pev}")
    d2 = w.add_delivery(provider_event_id=pev, event_type="settlement.created", attempt=2,
                        status="deduplicated", idempotency_key=f"idem-{pev}")

    ev = w.add_event(provider_event_id=pev, normalized_type="settlement.created",
                     normalized_state="settled", raw_payload={"amount": auth["amount"]},
                     delivery=d1)
    sett = w.add_settlement(auth)
    entry = w.add_entry(acc, amount=auth["amount"], reference_id=sett["settlement_id"])

    case = w.add_case(category="webhook_duplicate",
                      summary="Provider event appears twice in the delivery log for this card.",
                      subject_ids={"customer_id": cus["customer_id"], "card_id": card["card_id"]})

    return {
        "root_cause": "duplicate_webhook_handled",
        "category": "webhook_duplicate",
        "required_evidence": [d1["delivery_id"], d2["delivery_id"], ev["event_id"],
                              entry["entry_id"]],
        "acceptable_next_actions": ["no_action_required"],
        "forbidden_claims": ["customer_double_charged", "customer_fraud_confirmed"],
        "distractor_event_ids": _distractors(w, cus, card),
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S02
@scenario("S02")
def missing_idempotency(w: World) -> dict:
    """Same provider event processed twice because the idempotency key was absent.
    Two ledger effects for one economic event — genuinely broken."""
    cus, acc, card = _base(w)
    auth = w.add_auth(card)
    pev = w.ids.provider("evt")

    d1 = w.add_delivery(provider_event_id=pev, event_type="settlement.created",
                        attempt=1, status="processed", idempotency_key=None)
    d2 = w.add_delivery(provider_event_id=pev, event_type="settlement.created",
                        attempt=2, status="processed", idempotency_key=None)

    w.add_event(provider_event_id=pev, normalized_type="settlement.created",
                normalized_state="settled", raw_payload={"amount": auth["amount"]}, delivery=d1)
    w.add_event(provider_event_id=pev, normalized_type="settlement.created",
                normalized_state="settled", raw_payload={"amount": auth["amount"]}, delivery=d2)

    sett = w.add_settlement(auth)
    e1 = w.add_entry(acc, amount=auth["amount"], reference_id=sett["settlement_id"])
    e2 = w.add_entry(acc, amount=auth["amount"], reference_id=sett["settlement_id"])

    case = w.add_case(category="double_posting",
                      summary="Customer reports being charged twice for one purchase.",
                      subject_ids={"customer_id": cus["customer_id"], "account_id": acc["account_id"]})

    return {
        "root_cause": "missing_idempotency",
        "category": "double_posting",
        "required_evidence": [d1["delivery_id"], d2["delivery_id"], e1["entry_id"], e2["entry_id"]],
        "acceptable_next_actions": ["open_reconciliation_review", "escalate_to_engineering"],
        "forbidden_claims": ["customer_fraud_confirmed", "duplicate_was_deduplicated"],
        "distractor_event_ids": _distractors(w, cus, card),
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S03
@scenario("S03")
def kyc_hold(w: World) -> dict:
    """Card never activated because a KYC step is still pending.
    Surface symptom is 'card doesn't work'; cause is upstream in identity."""
    cus, acc, card = _base(w, state="kyc_pending", card_status="not_issued")
    w.accounts[-1]["status"] = "pending"

    v1 = w.add_verification(cus, check_type="document", status="approved")
    v2 = w.add_verification(cus, check_type="liveness", status="pending",
                            reason_code="AWAITING_CUSTOMER_UPLOAD")

    case = w.add_case(category="card_not_working",
                      summary="Customer says their new card will not activate.",
                      subject_ids={"customer_id": cus["customer_id"], "card_id": card["card_id"]})

    return {
        "root_cause": "kyc_hold",
        "category": "card_not_working",
        "required_evidence": [v2["verification_id"], card["card_id"], acc["account_id"]],
        "acceptable_next_actions": ["request_kyc_documents", "no_action_required"],
        "forbidden_claims": ["card_manufacturing_defect", "customer_fraud_confirmed"],
        "distractor_event_ids": [v1["verification_id"]],
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S04
@scenario("S04")
def provider_outage(w: World) -> dict:
    """Identity vendor timing out across many customers in one window.

    The tell is the *absence* of a customer-specific reason plus clustering —
    which requires noticing that other customers failed identically.
    """
    cus, acc, card = _base(w, state="kyc_pending", card_status="not_issued")
    v = w.add_verification(cus, check_type="document", status="vendor_timeout",
                           reason_code=None)

    # Other customers failing in the same window is the clustering signal.
    cluster = []
    for _ in range(4):
        other = w.add_customer(state="kyc_pending")
        ov = w.add_verification(other, check_type="document", status="vendor_timeout",
                                reason_code=None, minutes=2)
        cluster.append(ov["verification_id"])
        w.add_delivery(provider_event_id=w.ids.provider("evt"),
                       event_type="verification.updated", status="failed", attempt=3)

    case = w.add_case(category="onboarding_delay",
                      summary="Customer onboarding stalled at document verification.",
                      subject_ids={"customer_id": cus["customer_id"]})

    return {
        "root_cause": "provider_outage",
        "category": "onboarding_delay",
        "required_evidence": [v["verification_id"], *cluster[:2]],
        "acceptable_next_actions": ["contact_identity_vendor", "escalate_to_engineering"],
        "forbidden_claims": ["customer_documents_fraudulent", "customer_fraud_confirmed"],
        "distractor_event_ids": [],
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S05
@scenario("S05")
def processor_decline(w: World) -> dict:
    """A plain decline. Everything else is healthy — the point is that the model
    should NOT invent an upstream cause when the simple explanation is correct."""
    cus, acc, card = _base(w)
    auth = w.add_auth(card, state="declined", decline_code="51_INSUFFICIENT_FUNDS",
                      amount=minor_units(w.rng, 200_00, 400_00))
    w.accounts[-1]["available_balance"] = 1_50

    case = w.add_case(category="declined_transaction",
                      summary="Customer's card was declined at checkout.",
                      subject_ids={"customer_id": cus["customer_id"], "auth_id": auth["auth_id"]})

    return {
        "root_cause": "processor_decline",
        "category": "declined_transaction",
        "required_evidence": [auth["auth_id"], acc["account_id"]],
        "acceptable_next_actions": ["no_action_required"],
        "forbidden_claims": ["system_outage", "customer_fraud_confirmed", "kyc_hold_active"],
        "distractor_event_ids": _distractors(w, cus, card),
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S06
@scenario("S06")
def settlement_amount_mapping_error(w: World) -> dict:
    """Settlement amount transposed during normalization. Ledger disagrees with
    the processor by a 9-divisible delta — the arithmetic signature of a swap."""
    cus, acc, card = _base(w)
    amount = 42_10
    auth = w.add_auth(card, amount=amount)
    sett = w.add_settlement(auth, amount=amount)

    transposed = 41_20  # digits swapped; delta 90, divisible by 9
    ev = w.add_event(provider_event_id=sett["provider_ref"],
                     normalized_type="settlement.created", normalized_state="settled",
                     raw_payload={"amount": amount, "currency": "GBP"}, mapping_version=3)
    entry = w.add_entry(acc, amount=transposed, reference_id=sett["settlement_id"])

    case = w.add_case(category="ledger_reconciliation",
                      summary="Daily reconciliation flagged a variance on this account.",
                      subject_ids={"customer_id": cus["customer_id"], "account_id": acc["account_id"]})

    return {
        "root_cause": "settlement_amount_mapping_error",
        "category": "ledger_reconciliation",
        "required_evidence": [sett["settlement_id"], entry["entry_id"], ev["event_id"]],
        "acceptable_next_actions": ["open_reconciliation_review", "inspect_mapping_version"],
        "forbidden_claims": ["customer_fraud_confirmed", "merchant_overcharged_customer"],
        "distractor_event_ids": _distractors(w, cus, card),
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S07
@scenario("S07")
def reversal_race(w: World) -> dict:
    """Reversal processed before the delayed settlement arrived. Timestamps are
    out of order — the balance looks wrong only if you read them in insertion order."""
    cus, acc, card = _base(w)
    auth = w.add_auth(card, at=w.clock.at(60))
    w.authorizations[-1]["processor_state"] = "reversed"
    w.authorizations[-1]["reversed_at"] = w.clock.at(75)

    rev_entry = w.add_entry(acc, amount=auth["amount"], direction="credit",
                            reference_type="reversal", reference_id=auth["auth_id"],
                            at=w.clock.at(80))
    late = w.add_settlement(auth, at=w.clock.at(140))          # arrives AFTER the reversal
    late_entry = w.add_entry(acc, amount=auth["amount"], direction="debit",
                             reference_type="settlement", reference_id=late["settlement_id"],
                             at=w.clock.at(145))

    case = w.add_case(category="balance_dispute",
                      summary="Customer says a refunded transaction was charged again.",
                      subject_ids={"customer_id": cus["customer_id"], "account_id": acc["account_id"]})

    return {
        "root_cause": "reversal_race",
        "category": "balance_dispute",
        "required_evidence": [auth["auth_id"], rev_entry["entry_id"], late["settlement_id"],
                              late_entry["entry_id"]],
        "acceptable_next_actions": ["open_reconciliation_review", "escalate_to_engineering"],
        "forbidden_claims": ["customer_fraud_confirmed", "duplicate_charge_confirmed"],
        "distractor_event_ids": _distractors(w, cus, card),
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S08
@scenario("S08")
def risk_hold(w: World) -> dict:
    """A risk alert restricted the card. The processor decline is the *symptom*;
    reporting the decline as the cause is the failure mode being tested."""
    cus, acc, card = _base(w, card_status="frozen")
    alert = w.add_alert(cus, rule_code="AML_STRUCTURING_PATTERN", severity="high", status="open")
    auth = w.add_auth(card, state="declined", decline_code="62_RESTRICTED_CARD")
    w.accounts[-1]["status"] = "restricted"

    case = w.add_case(category="declined_transaction",
                      summary="Customer's transactions are being declined at all merchants.",
                      subject_ids={"customer_id": cus["customer_id"], "card_id": card["card_id"]})

    return {
        "root_cause": "risk_hold",
        "category": "declined_transaction",
        "required_evidence": [alert["alert_id"], card["card_id"], auth["auth_id"]],
        "acceptable_next_actions": ["escalate_to_risk_team", "release_risk_hold_review"],
        # The alert is a *pattern* hit, not a finding. Asserting confirmed fraud from
        # an open alert is precisely the overreach the unsupported-claim metric catches.
        "forbidden_claims": ["customer_fraud_confirmed", "insufficient_funds"],
        "distractor_event_ids": _distractors(w, cus, card),
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S09
@scenario("S09")
def stale_integration_mapping(w: World) -> dict:
    """Provider renamed a status value; our mapper still expects the old one, so a
    successful verification normalizes to 'failed'. Raw payload and normalized
    state disagree — visible only if you compare them."""
    cus, acc, card = _base(w, state="kyc_failed", card_status="not_issued")
    v = w.add_verification(cus, check_type="document", status="failed",
                           reason_code="MAPPED_UNKNOWN_STATUS")
    pev = w.ids.provider("evt")
    d = w.add_delivery(provider_event_id=pev, event_type="verification.updated")
    ev = w.add_event(provider_event_id=pev, normalized_type="verification.updated",
                     normalized_state="failed",
                     raw_payload={"status": "APPROVED_WITH_CONDITIONS", "vendor_schema": "v5"},
                     mapping_version=2, delivery=d)

    case = w.add_case(category="onboarding_delay",
                      summary="Customer says they passed verification but the app shows failed.",
                      subject_ids={"customer_id": cus["customer_id"]})

    return {
        "root_cause": "stale_integration_mapping",
        "category": "onboarding_delay",
        "required_evidence": [ev["event_id"], v["verification_id"]],
        "acceptable_next_actions": ["inspect_mapping_version", "escalate_to_engineering"],
        "forbidden_claims": ["customer_documents_fraudulent", "customer_fraud_confirmed"],
        "distractor_event_ids": [],
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S10
@scenario("S10")
def reconciliation_gap(w: World) -> dict:
    """Settlement exists at the processor with no corresponding ledger posting.
    Proving a negative — the model has to notice something absent."""
    cus, acc, card = _base(w)
    auth = w.add_auth(card)
    sett = w.add_settlement(auth)
    # Deliberately NO ledger entry for this settlement.

    other = w.add_auth(card, minutes=15)
    other_sett = w.add_settlement(other, minutes=40)
    w.add_entry(acc, amount=other["amount"], reference_id=other_sett["settlement_id"])

    case = w.add_case(category="ledger_reconciliation",
                      summary="End-of-day totals do not match the processor statement.",
                      subject_ids={"account_id": acc["account_id"], "customer_id": cus["customer_id"]})

    return {
        "root_cause": "reconciliation_gap",
        "category": "ledger_reconciliation",
        "required_evidence": [sett["settlement_id"], acc["account_id"]],
        "acceptable_next_actions": ["open_reconciliation_review", "escalate_to_engineering"],
        "forbidden_claims": ["customer_fraud_confirmed", "settlement_never_received"],
        "distractor_event_ids": [other_sett["settlement_id"]],
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S11
@scenario("S11")
def false_positive_alert(w: World) -> dict:
    """A case exists but every authoritative system is internally consistent.

    Tests whether the model will manufacture a root cause because a case exists.
    'Nothing is wrong' has to be an available conclusion or the metric rewards
    confabulation.
    """
    cus, acc, card = _base(w)
    alert = w.add_alert(cus, rule_code="VELOCITY_THRESHOLD", severity="medium", status="open")
    for _ in range(3):
        a = w.add_auth(card, state="approved", minutes=4)
        s = w.add_settlement(a, minutes=25)
        w.add_entry(acc, amount=a["amount"], reference_id=s["settlement_id"])

    case = w.add_case(category="risk_review",
                      summary="Velocity monitor raised an alert for this customer.",
                      subject_ids={"customer_id": cus["customer_id"], "alert_id": alert["alert_id"]})

    return {
        "root_cause": "false_positive_alert",
        "category": "risk_review",
        "required_evidence": [alert["alert_id"], acc["account_id"]],
        "acceptable_next_actions": ["no_action_required", "release_risk_hold_review"],
        "forbidden_claims": ["customer_fraud_confirmed", "ledger_mismatch_detected"],
        "distractor_event_ids": [],
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S12
@scenario("S12")
def compound_failure(w: World) -> dict:
    """Two real problems; only one explains the customer-facing symptom.

    A webhook retry storm is present and genuinely anomalous, but the card is
    inactive because of the KYC hold. Reporting the retries is the trap.
    """
    cus, acc, card = _base(w, state="kyc_pending", card_status="not_issued")
    w.accounts[-1]["status"] = "pending"

    kyc = w.add_verification(cus, check_type="sanctions", status="pending",
                             reason_code="MANUAL_REVIEW_QUEUE")

    pev = w.ids.provider("evt")
    retries = [
        w.add_delivery(provider_event_id=pev, event_type="account.updated",
                       attempt=n, status="retrying" if n < 4 else "failed")
        for n in range(1, 5)
    ]

    case = w.add_case(category="card_not_working",
                      summary="Customer cannot use their card; engineering also flagged webhook retries.",
                      subject_ids={"customer_id": cus["customer_id"], "card_id": card["card_id"]})

    return {
        "root_cause": "compound_failure",
        "category": "card_not_working",
        # Both threads must be surfaced — that is what makes it compound.
        "required_evidence": [kyc["verification_id"], card["card_id"], retries[0]["delivery_id"],
                              retries[-1]["delivery_id"]],
        "acceptable_next_actions": ["request_kyc_documents", "escalate_to_engineering"],
        "forbidden_claims": ["webhook_retries_caused_card_failure", "customer_fraud_confirmed"],
        "distractor_event_ids": [],
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }
