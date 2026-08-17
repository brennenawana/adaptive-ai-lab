"""The twelve seeded scenario classes.

Each builder writes authoritative records across the service schemas and returns the
hidden manifest. The investigator can query the former and never the latter.

Design rule followed throughout: the *surface symptom* should rarely be the root
cause. A scenario where the first tool call gives the answer measures nothing —
the skill under test is combining evidence across services.

Two rules that are load-bearing rather than stylistic:

**No class writes its own consequences.** S01, S02, S06, S07, S09 and S10 publish
provider events and let the integration and ledger consumers decide what happens.
The duplicate really is deduplicated by the dedupe ledger, the double posting really
is the absence of an idempotency key, the corrupted amount really is the v3 mapper.
Since Suite v3 the *background* settlements every card-holding class carries are
published too (`_background`), so a settlement without a posting exists only where a
scenario injects one (S10) — under Suite v2 six classes carried S10's fault signature
as ambient noise. S03/S04/S09/S12 have no card activity and stay state-based, which
is correct — not every operational problem is an event-ordering problem.

**Background precedes the case, and follows the injected activity where the plan
must reach the injected event.** The fixed-evidence plan fetches webhook history for
the first six `provider_ref`s it discovers, in time order, so in S01/S02/S06/S07 the
injected settlement is generated before the background purchases; in S05/S08 the
background purchases come first (a card is not declined mid-shopping and then
approved three times), and the injected decline is the last thing before the case
opens. Nothing in any world post-dates its case: an operator opens a case about what
has happened, not about what will.

**Every webhook delivery must be addressable from a state row's `provider_ref`.**
The fixed-evidence plan reaches the event trail by walking `provider_ref` values out
of phase-one results and calling `get_webhook_history` with them. A delivery whose
`provider_event_id` matches no state row is unreachable by any model, which makes
its scenario permanently unwinnable rather than merely hard. Publishing a settlement
event therefore uses the settlement's own `provider_ref`, not a fresh id.
`test_required_evidence_is_reachable_by_the_tool_set` enforces this.
"""

from __future__ import annotations

from typing import Callable

from .world import World, minor_units, vendor

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


def _settlement_payload(acc: dict, sett: dict, amount: int) -> dict:
    """What a provider sends us for a settlement.

    `account_id` is in here because this sandbox's integration layer is thin — a
    real provider would carry its own reference and we would resolve the account.
    The ledger consumer's contract already expects to be told, and inventing an
    account-resolution step would add a component nothing in the experiment matrix
    measures.
    """
    return {
        "state": "settled",
        "account_id": acc["account_id"],
        "amount": amount,
        "currency": "GBP",
        "reference_id": sett["settlement_id"],
    }


def _publish_settlement(w: World, acc: dict, auth: dict, sett: dict, *,
                        idempotency_key: str | None = "auto", attempt: int = 1,
                        occurred_at=None):
    """A settlement the provider tells us about, addressed by its own `provider_ref`
    so `get_webhook_history` can be called with it. `"auto"` gives the safe key a
    well-behaved provider sends; S02 passes `None` on purpose."""
    key = f"idem-{sett['provider_ref']}" if idempotency_key == "auto" else idempotency_key
    return w.publish(provider_event_id=sett["provider_ref"], event_type="settlement.created",
                     raw_payload=_settlement_payload(acc, sett, sett["amount"]),
                     idempotency_key=key, attempt=attempt, occurred_at=occurred_at)


def _background(w: World, cus: dict, acc: dict, card: dict, n: int = 3) -> list[str]:
    """Unrelated but plausible activity, materialised like anything else.

    Without these a model can score well by summarising everything it sees;
    distractors make evidence *selection* the thing being measured.

    Each background purchase settles AND is published, so the ledger consumer posts
    it. Under Suite v2 these settlements were state rows with no delivery, no
    normalized event and no posting — S10's fault signature (`reconciliation_gap`)
    present as ambient noise in six classes, which made "compound failure" a
    defensible reading of a world meant to contain exactly one defect.
    """
    ids: list[str] = []
    for _ in range(n):
        a = w.add_auth(card, state="approved", minutes=w.rng.randint(5, 240))
        s = w.add_settlement(a, minutes=w.rng.randint(30, 200))
        _publish_settlement(w, acc, a, s)
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

    Emergent: the same event is published twice carrying the same idempotency key.
    The second delivery is deduplicated by the consumer's dedupe ledger, so exactly
    one normalized event and one ledger entry exist. Nothing here writes a
    "deduplicated" row — dedupe either works or the test fails.
    """
    cus, acc, card = _base(w)
    auth = w.add_auth(card)
    sett = w.add_settlement(auth)

    pev = sett["provider_ref"]
    idem = f"idem-{pev}"
    payload = _settlement_payload(acc, sett, auth["amount"])

    first = w.publish(provider_event_id=pev, event_type="settlement.created",
                      raw_payload=payload, idempotency_key=idem, attempt=1)
    retry = w.publish(provider_event_id=pev, event_type="settlement.created",
                      raw_payload=payload, idempotency_key=idem, attempt=2)
    background = _background(w, cus, acc, card)

    case = w.add_case(category="webhook_duplicate",
                      summary="Provider event appears twice in the delivery log for this card.",
                      subject_ids={"customer_id": cus["customer_id"], "card_id": card["card_id"]})

    return {
        "root_cause": "duplicate_webhook_handled",
        "category": "webhook_duplicate",
        # The retry produces a delivery and nothing else — that absence IS the
        # evidence that dedupe worked.
        "required_evidence": [first.delivery_id, retry.delivery_id,
                              first.normalized_event_id, first.ledger_entry_id],
        "acceptable_next_actions": ["no_action_required"],
        "forbidden_claims": ["customer_double_charged", "customer_fraud_confirmed"],
        "distractor_event_ids": background,
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S02
@scenario("S02")
def missing_idempotency(w: World) -> dict:
    """Same provider event processed twice because the idempotency key was absent.
    Two ledger effects for one economic event — genuinely broken.

    Identical to S01 except for the missing key. The consumer cannot tell a retry
    from a genuine second occurrence without one, so it processes both and the
    account really is debited twice. The double posting is the consequence of the
    defect, not two rows written by a fixture.
    """
    cus, acc, card = _base(w)
    auth = w.add_auth(card)
    sett = w.add_settlement(auth)

    pev = sett["provider_ref"]
    payload = _settlement_payload(acc, sett, auth["amount"])

    first = w.publish(provider_event_id=pev, event_type="settlement.created",
                      raw_payload=payload, idempotency_key=None, attempt=1)
    again = w.publish(provider_event_id=pev, event_type="settlement.created",
                      raw_payload=payload, idempotency_key=None, attempt=2)
    background = _background(w, cus, acc, card)

    case = w.add_case(category="double_posting",
                      summary="Customer reports being charged twice for one purchase.",
                      subject_ids={"customer_id": cus["customer_id"], "account_id": acc["account_id"]})

    return {
        "root_cause": "missing_idempotency",
        "category": "double_posting",
        "required_evidence": [first.delivery_id, again.delivery_id,
                              first.ledger_entry_id, again.ledger_entry_id],
        "acceptable_next_actions": ["open_reconciliation_review", "escalate_to_engineering"],
        "forbidden_claims": ["customer_fraud_confirmed", "duplicate_was_deduplicated"],
        "distractor_event_ids": background,
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

    # One vendor, pinned. Drawing per verification scattered the "outage" across
    # three different vendors, which is not an outage — it is three coincidences,
    # and no correct reasoning could have reached `provider_outage` from it.
    outage_vendor = vendor(w.rng)
    v = w.add_verification(cus, check_type="document", status="vendor_timeout",
                           reason_code=None, vendor_name=outage_vendor)

    # Other customers failing in the same window is the clustering signal. It is
    # reachable only through the vendor-window form of get_verifications — see the
    # note on that tool.
    cluster = []
    for _ in range(4):
        other = w.add_customer(state="kyc_pending")
        ov = w.add_verification(other, check_type="document", status="vendor_timeout",
                                reason_code=None, minutes=2, vendor_name=outage_vendor)
        cluster.append(ov["verification_id"])
        # Addressed by the verification's own provider_ref: a delivery keyed to a
        # reference no state row carries can never be reached by any tool call.
        w.add_failed_delivery(provider_event_id=ov["provider_ref"],
                              event_type="verification.updated", status="failed",
                              attempt=3)

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
    # Earlier purchases first: the customer spent the account down, then the
    # decline. Background after a decline would put approvals where the balance
    # cannot support them.
    background = _background(w, cus, acc, card)
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
        "distractor_event_ids": background,
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S06
@scenario("S06")
def settlement_amount_mapping_error(w: World) -> dict:
    """Settlement amount transposed during normalization. Ledger disagrees with
    the processor by a 9-divisible delta — the arithmetic signature of a swap.

    Emergent: this scenario runs the integration service at mapping_version 3, the
    release carrying the transposition defect, for the injected settlement. The
    provider sends 4210, the mapper makes it 4201, and the ledger posts what it was
    told. Nothing writes a wrong number down; a wrong number is computed.

    The bad release is then rolled back (v4) before the background purchases arrive,
    so they post faithfully and `integration.events.mapping_version` says which
    event the defective release touched. Leaving v3 live for the whole scenario would
    corrupt every background posting too, and the settlement the manifest names as
    evidence would be indistinguishable from three others with the same defect.
    """
    cus, acc, card = _base(w)
    w.mapping_version = 3
    amount = 42_10
    auth = w.add_auth(card, amount=amount)
    sett = w.add_settlement(auth, amount=amount)

    ev = w.publish(provider_event_id=sett["provider_ref"],
                   event_type="settlement.created",
                   raw_payload=_settlement_payload(acc, sett, amount))
    w.mapping_version = 4          # rolled back; the damage is already posted
    background = _background(w, cus, acc, card)

    case = w.add_case(category="ledger_reconciliation",
                      summary="Daily reconciliation flagged a variance on this account.",
                      subject_ids={"customer_id": cus["customer_id"], "account_id": acc["account_id"]})

    return {
        "root_cause": "settlement_amount_mapping_error",
        "category": "ledger_reconciliation",
        "required_evidence": [sett["settlement_id"], ev.ledger_entry_id,
                              ev.normalized_event_id],
        "acceptable_next_actions": ["open_reconciliation_review", "inspect_mapping_version"],
        "forbidden_claims": ["customer_fraud_confirmed", "merchant_overcharged_customer"],
        "distractor_event_ids": background,
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S07
@scenario("S07")
def reversal_race(w: World) -> dict:
    """Reversal processed before the delayed settlement arrived. Timestamps are
    out of order — the balance looks wrong only if you read them in insertion order.

    Emergent, and this is the class the determinism argument exists for. The race is
    created by PUBLISH ORDER, not by writing inverted timestamps: the settlement
    occurred at T+65 but is published second, after a reversal that occurred at
    T+75. The ledger posts in arrival order stamped with `occurred_at`, so the
    entries end up with `posting_seq` ascending while `posted_at` descends. Reading
    the account in insertion order shows a credit then a debit — the customer's
    "refunded transaction was charged again".

    Nothing here depends on scheduler timing. Swap the two `publish` calls below and
    the anomaly disappears; that is the only thing that controls it.
    """
    cus, acc, card = _base(w)
    auth = w.add_auth(card, at=w.clock.at(60))
    w.authorizations[-1]["processor_state"] = "reversed"
    w.authorizations[-1]["reversed_at"] = w.clock.at(75)

    # The processor settled at T+65 — before the reversal. Delivery is what is late:
    # both webhooks arrive after T+80, the reversal first.
    late = w.add_settlement(auth, at=w.clock.at(65))
    w.clock.tick(minutes=80)

    rev = w.publish(provider_event_id=auth["provider_ref"],
                    event_type="authorization.reversed",
                    occurred_at=w.clock.at(75),
                    raw_payload={"state": "reversed", "account_id": acc["account_id"],
                                 "amount": auth["amount"], "currency": "GBP",
                                 "reference_id": auth["auth_id"]})
    late_ev = w.publish(provider_event_id=late["provider_ref"],
                        event_type="settlement.created",
                        occurred_at=w.clock.at(65),
                        raw_payload=_settlement_payload(acc, late, auth["amount"]))
    background = _background(w, cus, acc, card)

    case = w.add_case(category="balance_dispute",
                      summary="Customer says a refunded transaction was charged again.",
                      subject_ids={"customer_id": cus["customer_id"], "account_id": acc["account_id"]})

    return {
        "root_cause": "reversal_race",
        "category": "balance_dispute",
        "required_evidence": [auth["auth_id"], rev.ledger_entry_id,
                              late["settlement_id"], late_ev.ledger_entry_id],
        "acceptable_next_actions": ["open_reconciliation_review", "escalate_to_engineering"],
        "forbidden_claims": ["customer_fraud_confirmed", "duplicate_charge_confirmed"],
        "distractor_event_ids": background,
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S08
@scenario("S08")
def risk_hold(w: World) -> dict:
    """A risk alert restricted the card. The processor decline is the *symptom*;
    reporting the decline as the cause is the failure mode being tested."""
    cus, acc, card = _base(w, card_status="frozen")
    # Ordinary purchases while the card was still active, then the alert, the
    # freeze, and the decline. Approvals after the freeze would contradict it.
    background = _background(w, cus, acc, card)
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
        "distractor_event_ids": background,
        "case_id": case["case_id"],
        "subject_ids": case["subject_ids"],
    }


# ---------------------------------------------------------------------------- S09
@scenario("S09")
def stale_integration_mapping(w: World) -> dict:
    """Provider renamed a status value; our mapper still expects the old one, so a
    successful verification normalizes to 'failed'. Raw payload and normalized
    state disagree — visible only if you compare them.

    Emergent: this scenario runs the integration service at mapping_version 2, which
    predates the provider's `APPROVED_WITH_CONDITIONS` value. The vendor really does
    send an approval; the stale mapper really does turn it into 'failed' and leaves
    its own note saying it did not recognise the status.
    """
    cus, acc, card = _base(w, state="kyc_failed", card_status="not_issued")
    w.mapping_version = 2
    v = w.add_verification(cus, check_type="document", status="failed",
                           reason_code="MAPPED_UNKNOWN_STATUS")

    ev = w.publish(provider=v["vendor"], provider_event_id=v["provider_ref"],
                   event_type="verification.updated",
                   raw_payload={"status": "APPROVED_WITH_CONDITIONS",
                                "vendor_schema": "v5",
                                "customer_id": cus["customer_id"]})

    case = w.add_case(category="onboarding_delay",
                      summary="Customer says they passed verification but the app shows failed.",
                      subject_ids={"customer_id": cus["customer_id"]})

    return {
        "root_cause": "stale_integration_mapping",
        "category": "onboarding_delay",
        "required_evidence": [ev.normalized_event_id, v["verification_id"]],
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
    Proving a negative — the model has to notice something absent.

    Emergent: the gap is an event that was never published. The processor recorded
    the settlement; the ledger never heard about it, which is exactly how this
    happens in production. The control settlement immediately after IS published, so
    the absence is specific rather than a ledger that simply does not work.
    """
    cus, acc, card = _base(w)
    auth = w.add_auth(card)
    sett = w.add_settlement(auth)
    # Deliberately NOT published — this is the lost event.

    other = w.add_auth(card, minutes=15)
    other_sett = w.add_settlement(other, minutes=40)
    w.publish(provider_event_id=other_sett["provider_ref"],
              event_type="settlement.created",
              raw_payload=_settlement_payload(acc, other_sett, other["amount"]))

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
    # The postings that make the account "internally consistent" are settlements
    # the pipeline posted, like every other posting in the corpus — not prior state
    # written by hand with a different id shape.
    for _ in range(3):
        a = w.add_auth(card, state="approved", minutes=4)
        s = w.add_settlement(a, minutes=25)
        _publish_settlement(w, acc, a, s)

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

    # Keyed to the card's provider_ref, the only provider-referenced entity a
    # pre-issuance customer has — a retry storm nobody can look up is evidence in
    # name only. The storm remains independent of the KYC thread: these are account
    # metadata webhooks failing, not verification webhooks.
    #
    # Still hand-authored, and deliberately so: a delivery that failed is the one
    # thing the consumer cannot record about itself. See `World.add_failed_delivery`.
    pev = card["provider_ref"]
    retries = [
        w.add_failed_delivery(provider_event_id=pev, event_type="account.updated",
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
