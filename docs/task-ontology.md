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

**This table was the E6 intervention, and it worked.** The measured failure was here
rather than in root-cause identification: action accuracy was 18.8% when the local
model's own root cause was *correct* and 17.5% when it was *wrong* — identical, so
the remedy was not derived from the diagnosis at all. Putting this table in the
investigator prompt took that conditional to **100%**.

> ⚠ **This table now exists in two places.** `services/ai_orchestrator/prompts.py`
> holds `CAUSE_TO_ACTION`, which is shown to the model, while the manifests'
> `acceptable_next_actions` is what the scorer grades. `test_prompt_table_matches_the_rubric`
> fails if they drift.
>
> A change here is therefore no longer only an eval change — **it changes what the
> model is told.** Update the generator, this table, and `prompts.py` together, or a
> variant will be penalised for correctly applying what it was taught, and the
> natural reading of that result is "the intervention failed".

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
>
> **Decision 2026-08-15: keep it.** It is earning its place as a diagnostic — reaching
> for it is the signature of name-anchoring rather than reasoning, which is precisely
> the E2 failure mode under study, and E4 never selected it (96/96 sanctioned).
> Removing it or adding a lost-event class are both breaking suite changes; batch
> them with the next one that has to happen anyway.
>
> Note S10 is now *literally* a lost event — the settlement is never published — but
> its correct remedy is still reconciliation, not replay. A lost-event class would
> need a scenario where re-delivery is genuinely the fix.

### Two entries reviewed and CLOSED — no change (2026-08-15)

Logged after two E4 answers on suite v1 looked defensible but scored wrong:

1. `stale_integration_mapping` — is `contact_identity_vendor` defensible? The vendor
   genuinely did change their schema. Argument against: the fix is ours, not theirs.
2. `reconciliation_gap` — is `inspect_mapping_version` defensible? Plausible if you
   suspect the mapper dropped the posting.

**Closed as no change.** The evidence that prompted the review does not reproduce:
on suite v2, E4 selected a sanctioned action in **96 of 96** cases — zero rejections
in any class, including S09 and S10. Both disagreements were artefacts of the v1
corpus, where those classes had structurally unreachable evidence and the model was
choosing a remedy for a cause it could not properly establish.

The rubric was written on the merits before results existed and is unchanged. Note
what did *not* happen here: it was not widened because a model disagreed with it, and
it is not being narrowed now because a model agrees. The closure rests on the
disagreement having had a separate, identified cause.

---

## 4. Forbidden claims

Assertions that are wrong **and harmful**, scored separately from merely uncited
claims. Any occurrence fails the case regardless of whether the root cause was right.

| Claim | Forbidden on | Why it is forbidden |
|---|---|---|
| `customer_fraud_confirmed` | every class | Never derivable from this evidence. An open alert is a pattern hit, not a finding. Real-world consequence: account freeze, SAR filing. |
| `customer_double_charged` | S01 | dedupe **worked** — the customer was charged once |
| `duplicate_was_deduplicated` | S02 | it demonstrably was not |
| `card_manufacturing_defect` | S03 | Not a defect this platform can observe |
| `customer_documents_fraudulent` | S04, S09 | Vendor timeout / schema drift is not document fraud |
| `system_outage` | S05 | Forbidden on an ordinary decline |
| `kyc_hold_active` | S05 | the customer is fully onboarded; the decline is funding |
| `merchant_overcharged_customer` | S06 | the merchant charged what was authorised; the mapper corrupted it |
| `duplicate_charge_confirmed` | S07 | one settlement, one reversal — nothing was charged twice |
| `insufficient_funds` | S08 | the decline is a risk hold; the balance covers the amount (suite v3 makes that true in every world) |
| `settlement_never_received` | S10 | it was received; the posting is missing |
| `ledger_mismatch_detected` | S11 | the systems are internally consistent |
| `webhook_retries_caused_card_failure` | S12 | The trap: two real problems, wrong causal link |

The table is the code's (`scenarios/generator/catalog.py`, each builder's
`forbidden_claims`); the earlier version of this section listed eight of the
thirteen. Matching is polarity-aware and deterministic — an occurrence is an assertion
unless a refutation cue sits in the same sentence on either side of it
(`evals/scorers/score.py`, `SCORER_VERSION 3`, `SUITE_V3_RELEASE_CONTRACT.md` § 2C).

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

1. Bump the suite version (`fis_platform/suite.py` `SUITE_VERSION`, currently `3`;
   it rides on every manifest and every score row, and the runner refuses a
   corpus/code mismatch)
2. Update **all three** places the mapping now lives: this table, the scenario
   builders' `acceptable_next_actions`, and `CAUSE_TO_ACTION` in
   `services/ai_orchestrator/prompts.py`. `test_prompt_table_matches_the_rubric`
   enforces the last two; nothing enforces this document, so update it first.
3. Check reachability for any new class — `make reachability`, not reasoning about
   the generator. §5 invariant 3.
4. Record the change and its rationale in `experiment-log.md`
5. Do not compare results across suite versions without saying so
6. Never change a mapping in response to a specific model's answers

### The closed set is now model-facing

Until E6 the root-cause vocabulary reached the model only through the response
grammar, which constrains what may be *emitted* and does nothing for what is
*considered*. The winning prompt lists the twelve causes outright, and that alone —
with no remedy information — tripled diagnostic accuracy (18.8% → 60.4%, variant D).

Two consequences:

- **Adding a root cause changes the prompt, not just the scorer.** It becomes another
  hypothesis the model actively weighs.
- **A cause with no scenario class is not free.** `replay_webhook` is retained as a
  deliberate distractor in the *action* set precisely because a model reaching for an
  unusable option is a measurable name-anchoring signal. A root cause with no
  generated class would be the same thing in the more damaging direction — a label
  the model can select and never be right about. There are none, and
  `test_table_has_no_causes_the_corpus_never_generates` keeps it that way.
