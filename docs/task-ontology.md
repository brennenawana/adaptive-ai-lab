# Task Ontology

The closed vocabulary of the investigation workflow: what a case can be about, what
can have caused it, what may be recommended, and which claims are out of bounds.

This document is **normative**. `schemas/investigator.py` and the scenario manifests
must agree with it; where they disagree, this is the bug report.

Writing it down is not bookkeeping. Two of the four design bugs found on 2026-08-15
(unreachable required evidence; ID collisions) existed precisely because the mapping
below was implicit — held in the generator's code rather than stated anywhere that
could be checked against.

---

## 1. Case categories

What an operator sees when the case is opened. Note the deliberate many-to-many
relationship with root cause: **the category is the symptom, not the diagnosis.**

| Category | Operator's presenting complaint | Root causes that can produce it |
|---|---|---|
| `webhook_duplicate` | An event appears twice in the delivery log | `duplicate_webhook_handled` |
| `double_posting` | Customer charged twice for one purchase | `missing_idempotency` |
| `card_not_working` | Card will not activate or is refused everywhere | `kyc_hold`, `compound_failure` |
| `onboarding_delay` | Signup stalled at verification | `provider_outage`, `stale_integration_mapping` |
| `declined_transaction` | Card declined at checkout | `processor_decline`, `risk_hold` |
| `ledger_reconciliation` | Daily totals disagree with the processor | `settlement_amount_mapping_error`, `reconciliation_gap` |
| `balance_dispute` | Refunded transaction appears to be charged again | `reversal_race` |
| `risk_review` | Monitoring raised an alert | `false_positive_alert` |

**Three categories are deliberately ambiguous** (`card_not_working`,
`onboarding_delay`, `declined_transaction`, `ledger_reconciliation`). A model that
learns "category → cause" as a lookup will score ~50% on them. Disambiguating
requires reading evidence across services, which is the capability under test.

---

## 2. Root causes

Closed set. Scored by exact match, so a new member is a **breaking change** to the
eval suite and requires a suite version bump.

| Label | The actual defect | Where the evidence lives |
|---|---|---|
| `duplicate_webhook_handled` | Provider sent twice; dedupe worked. **Nothing is broken.** | webhook + integration + ledger |
| `missing_idempotency` | Same event processed twice; two ledger effects | webhook + ledger |
| `kyc_hold` | Onboarding blocked on an incomplete verification | identity + processor |
| `provider_outage` | Identity vendor timing out across many customers | identity (clustered) |
| `processor_decline` | Ordinary decline. Everything else healthy | processor + ledger |
| `settlement_amount_mapping_error` | Amount corrupted during normalization | processor + ledger + integration |
| `reversal_race` | Reversal landed before a delayed settlement | processor + ledger (out of order) |
| `risk_hold` | Alert restricted the card; the decline is downstream | risk + processor |
| `stale_integration_mapping` | Provider changed a value; our mapper didn't | integration (raw ≠ normalized) |
| `reconciliation_gap` | Settlement exists, ledger posting absent | processor + ledger (absence) |
| `false_positive_alert` | Alert fired; systems are internally consistent | risk + ledger |
| `compound_failure` | Two real problems; one explains the symptom | identity + webhook |
| `unknown` | Escape hatch. Always scores as incorrect | — |

### Diagnostic asymmetries worth naming

- **`duplicate_webhook_handled` vs `missing_idempotency`** differ by exactly one
  fact: whether an idempotency key was present and whether there are one or two
  downstream effects. Same surface, opposite verdicts.
- **`processor_decline` vs `risk_hold`** both present as a decline. The decline
  code (`51_INSUFFICIENT_FUNDS` vs `62_RESTRICTED_CARD`) plus the presence of an
  open alert separates them.
- **`reconciliation_gap`** requires noticing an **absence**. No record says
  "posting missing" — the model must observe that a settlement has no matching
  ledger reference.
- **`false_positive_alert`** requires concluding nothing is wrong. If the model
  cannot do this, the metric rewards confabulation.

---

## 3. Next actions

Closed set, scored by membership in the scenario's `acceptable_next_actions`.

| Action | Means | Appropriate when |
|---|---|---|
| `no_action_required` | Close the case; system behaved correctly | dedupe worked; ordinary decline; false positive |
| `open_reconciliation_review` | Finance investigates a money discrepancy | ledger and processor disagree on an amount or a posting |
| `inspect_mapping_version` | Engineering checks the normalization layer | raw provider payload disagrees with normalized state |
| `replay_webhook` | Re-deliver a provider event | an event was genuinely lost — **not** merely duplicated |
| `contact_identity_vendor` | Raise with the KYC provider | vendor-side timeouts or schema change |
| `request_kyc_documents` | Ask the customer for documents | verification pending on customer action |
| `escalate_to_risk_team` | Human risk review | an alert needs a disposition decision |
| `release_risk_hold_review` | Review whether a restriction should lift | hold appears unwarranted |
| `escalate_to_engineering` | Raise a code defect | systematic bug affecting more than this case |

### Cause → sanctioned action

**This table is the E6 intervention.** The measured E2 failure is here, not in
root-cause identification: the local 8B scored 41.7% on cause but 8.3% on action,
selecting `replay_webhook` for a mapping error, a risk hold, and a KYC failure.
It has no model of which remedies attach to which defects.

| Root cause | Sanctioned actions |
|---|---|
| `duplicate_webhook_handled` | `no_action_required` |
| `missing_idempotency` | `open_reconciliation_review`, `escalate_to_engineering` |
| `kyc_hold` | `request_kyc_documents`, `no_action_required` |
| `provider_outage` | `contact_identity_vendor`, `escalate_to_engineering` |
| `processor_decline` | `no_action_required` |
| `settlement_amount_mapping_error` | `open_reconciliation_review`, `inspect_mapping_version` |
| `reversal_race` | `open_reconciliation_review`, `escalate_to_engineering` |
| `risk_hold` | `escalate_to_risk_team`, `release_risk_hold_review` |
| `stale_integration_mapping` | `inspect_mapping_version`, `escalate_to_engineering` |
| `reconciliation_gap` | `open_reconciliation_review`, `escalate_to_engineering` |
| `false_positive_alert` | `no_action_required`, `release_risk_hold_review` |
| `compound_failure` | `request_kyc_documents`, `escalate_to_engineering` |

> **`replay_webhook` is sanctioned for NO current root cause.** It exists because a
> genuinely-lost-event scenario belongs in the ontology and is not yet generated. Its
> presence in the enum with no valid use makes it a pure distractor — which is why a
> model anchoring on names rather than reasoning reaches for it.

### Two entries under review (`BAD_RUBRIC` candidates)

Logged 2026-08-15, **not yet changed**, because altering a rubric after seeing model
answers is tuning against the test set. To be decided before the next frozen suite:

1. `stale_integration_mapping` — is `contact_identity_vendor` defensible? The vendor
   genuinely did change their schema. Argument against: the fix is ours, not theirs.
2. `reconciliation_gap` — is `inspect_mapping_version` defensible? Plausible if you
   suspect the mapper dropped the posting.

---

## 4. Forbidden claims

Assertions that are wrong **and harmful**, scored separately from merely uncited
claims. Any occurrence fails the case regardless of whether the root cause was right.

| Claim | Why it is forbidden |
|---|---|
| `customer_fraud_confirmed` | Never derivable from this evidence. An open alert is a pattern hit, not a finding. Real-world consequence: account freeze, SAR filing. |
| `customer_double_charged` | Forbidden on `S01` specifically, where dedupe **worked** |
| `duplicate_was_deduplicated` | Forbidden on `S02`, where it demonstrably was not |
| `customer_documents_fraudulent` | Vendor timeout / schema drift is not document fraud |
| `webhook_retries_caused_card_failure` | The S12 trap: two real problems, wrong causal link |
| `settlement_never_received` | S10 — it was received; the posting is missing |
| `card_manufacturing_defect` | Not a defect this platform can observe |
| `system_outage` | Forbidden on ordinary declines |

The unifying principle: **each is a claim that would trigger a costly or harmful
real-world action if believed.** That is what makes them worth failing a case over,
rather than deducting a fraction.

---

## 5. Evidence requirements

Each scenario's `required_evidence` lists entity IDs the investigator must surface.
Recall threshold is 0.8 by default.

Invariants, all test-enforced:

1. **Every required ID must be generated by that scenario** — otherwise 100% recall
   is unreachable and the class is silently capped
   (`test_required_evidence_actually_exists_in_the_world`). Since the event
   migration this checks ids the *pipeline* will produce too, by replaying the real
   consumer logic through `fis_platform.events.projection`.
2. **Every required ID must be reachable by the tool set.** The evidence plan is
   two-phase because webhook and integration evidence is addressed by
   `provider_event_id`, which is unknowable until a settlement or verification has
   been read (`test_required_evidence_is_reachable_by_the_tool_set`).
3. **Reachability must be demonstrated against the built corpus**, not just argued
   from the generator — `make reachability` replays the real plan through the real
   broker and prints the recall ceiling per class.

> Adding a scenario class means checking all three. Violating (2) produces a
> plausible but permanently unwinnable case — the failure mode that has cost the
> most time on this project.

**Invariant 2 was violated by the entire corpus until 2026-08-15**, and (1) passed
throughout, which is why (3) now exists. Every required id existed; the deliveries
among them were addressed by a `provider_event_id` no state row carried, so no tool
call could return them. Measured ceilings were S01 0.25, S02/S09/S12 0.50, S04 0.333
— five of twelve classes unable to pass a 0.8 threshold whatever the model did. The
scores looked like a weak model. Post-fix the ceiling is 1.000 for all twelve.

A tool that selects by anything other than a scenario-unique entity id inherits a
further obligation: results must not cross scenario boundaries. `get_verifications`
v2 selects by vendor and time, which is why scenarios now occupy disjoint slots on
the timeline. See `architecture.md` § Evidence reachability.

---

## 6. Changing this ontology

Any change to the root-cause set, action set, or cause→action mapping is a
**breaking change to the eval suite**:

1. Bump the suite version (`EvalRun.suite_version`)
2. Record the change and its rationale in `experiment-log.md`
3. Do not compare results across suite versions without saying so
4. Never change a mapping in response to a specific model's answers
