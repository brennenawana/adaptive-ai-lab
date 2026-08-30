# SYNTH-08: A Regulated Adverse-Event Triage Assistant

> [Index](../README.md) · [Examples](README.md)

*Synthetic worked example — all names and numbers invented.*

---

## Profile summary

A human safety reviewer reads every recommendation this system makes before
anything happens. That does not make it low-stakes, and believing it does is
the mistake this example exists to head off.

"Aldermere Biosciences" is a mid-size pharmaceutical safety and compliance
team. Its assistant reads incoming adverse-event narratives — intake forms
written by patients and providers — and flags the ones that may require
expedited regulatory reporting. The system recommends. A human decides.
Nothing it produces is submitted anywhere on its own.

| [Project profile](../GLOSSARY.md#project-profile) field | Value |
|---|---|
| Business outcome | Cut time-to-flag on narratives that may need expedited regulatory reporting |
| Task population & volume | ~600 intake narratives/month across three product lines |
| Criticality / failure cost | Missed expedited-reportable case → regulatory-deadline and safety exposure; false positive → reviewer time only (asymmetric cost) |
| Quality / reliability target | Near-ceiling recall on the expedited-reportable class; decision-support only, never the final decision. **Behavioral compatibility declared a requirement** (PROJECT_PROFILE field-4 sub-prompt): recommendations feed the analysts' sign-off workflow, and reviewers must be able to recognize the reasoning — deviation from the incumbent process carries its own operational cost even when adjudicated-correct |
| Latency / SLA | Same-business-day triage |
| Privacy / security / residency | Narratives carry protected personal health information; processing confined to an approved boundary; no such data in any vendor training path |
| Tool / action permissions | Read-only lookup against the product-label database and prior-case history; no write actions; no auto-submission to any regulator |
| Model candidates | Candidate-L (frontier managed API, compliant zero-retention endpoint) vs. Candidate-M (mid-size open-weights, self-hosted inside the approved boundary) |
| Owned / rentable compute | Existing validated-environment GPU capacity; no new purchase considered |
| Staffing / time | 3 FTE, 4-month runway |
| Existing evidence | 2 years of human-reviewed narrative history; no prior automated system |
| Stakes / consequence tolerance | **Tier 3** — safety, compliance, audit |

## Archetype & rigor tier

This is the regulated-decision-support archetype: the system recommends, a
human approves every action, and nothing writes anywhere on its own.

That last fact does not lower the tier. A [stakes tier](../GLOSSARY.md#stakes-tier)
attaches to the *decision's* consequence — here, a possibly missed
expedited-reportable signal. It does not attach to how much autonomy the
system has, or to how small the team is. The failure-cost field alone fixes
this at **Tier 3** before a single model is chosen (rule of proportion,
[00 §6](../00_PRINCIPLES_AND_SCOPE.md)).

So the full Tier-3 artifact set applies: tamper-evident provenance, pass^k
reliability claims, judge calibration wherever a judge is used, staged
shadow→canary with human approval, a rehearsed rollback path, and a periodic
methodology audit.

## The decisive moves

1. **The stakes tier was fixed at intake, before model selection.** The
   failure-cost and regulatory fields on the profile drove the tier call
   directly. No candidate model, harness, or budget question was allowed to
   happen first. Overriding the call would have required a written
   [method decision record](../GLOSSARY.md#method-decision-record); none was
   written, so Tier 3 stands.
2. **Governance was instantiated before the first eval run, not after
   selection.** A [record of record](../GLOSSARY.md#record-of-record) was
   stood up first.
   [Ground-truth isolation](../GLOSSARY.md#ground-truth-isolation) separated
   the expedited/non-expedited gold labels from anything model-facing. A
   [clean-room boundary](../GLOSSARY.md#clean-room-boundary) statement
   excluded protected narratives from any vendor training path. And every
   field of the [trajectory record](../GLOSSARY.md#trajectory-record) was
   classified for privacy sensitivity, with redaction defined before any
   telemetry was collected (chapter 13).
3. **Deterministic verification wherever the field allows it; judge
   calibration where it does not.** Structured fields — product code, event
   date, seriousness criteria — score deterministically, by code. The
   narrative-classification step is not like that, and needed a judge.
   Because unvalidated judges score near chance on objectively verifiable
   tasks [EXT-JUDGE-002], that judge was calibrated against three independent
   human reviewers before it was trusted for anything (chapter 03).
4. **A pass^1 number was not enough to make a reliability claim.** Both
   candidates are stochastic: ask twice, and you may not get the same answer
   twice. So a [pass^k](../GLOSSARY.md#pass-at-k-vs-pass-to-the-k) check on a
   held-out subset was run before any reliability claim was made, rather than
   pass@1 alone [EXT-AGENT-001]. See Outcome for what it found and how the
   design responded (chapter 04).
5. **[DECISION GATE] Shadow-to-canary promotion.** Entry to canary required
   two things: an adjudicated regret rate below its pre-registered ceiling,
   and a passed rollback rehearsal. The regret ceiling is the gate carrying
   veto authority — chapter 10's human-baseline rule.

   Shadow agreement with the analysts is a different quantity, and by default
   it is tracked as a compatibility diagnostic with a pre-registered review
   trigger rather than as a gate. Here, though, the profile *did* declare
   behavioral compatibility a requirement: the recommendations feed a
   sign-off workflow whose reviewers must be able to recognize the reasoning.
   So its floor was also written into the contract as a gate — explicitly,
   rather than assumed.

   All of this ran under the restraint doctrine: the simplest model that
   meets the objective, one declared treatment at a time [EXT-OPS-001C]
   (chapter 10). And
   [observe-only graduation](../GLOSSARY.md#observe-only-graduation) to an
   *automated* flagging action was explicitly not pursued for this
   consequence class — a permanent design choice, not a "not yet."
6. **Rollback was rehearsed before go-live, and the rehearsal caught
   something real.** It surfaced a mismatch between checkpoint version and
   retrieval-index version that would have silently served stale
   product-label context in production. That was fixed pre-promotion. A
   [rollback path](../GLOSSARY.md#rollback-path) nobody has ever exercised is
   a hypothesis, not a path; this one earned its keep before it was needed
   live.

## What was skipped and why

- **Chapter 11's demand-ledger and purchase-trigger machinery.** No hardware
  purchase was on the table — existing validated-environment compute covers
  the volume — so it was legitimately not engaged this cycle.
- **Chapter 09 (training).** The ladder was never exhausted. The gaps found
  in evaluation were specification and context gaps at rungs 2 and 4, closed
  by prompt/workflow and lookup-tool changes, not a demonstrated
  learnable-skill gap. Training was never reached, let alone justified.
- **Learned routing and multi-tier cascades (08).** The volume does not
  justify a second tier. A single verifier-plus-judge pipeline with human
  review is the whole system. Tool-contract discipline for the two read-only
  lookups was still applied in full.
- **Automating the flag-and-submit action.** As in move 5, this is a standing
  refusal for this consequence class, not a deferred item. Expedited-report
  submission stays a human action indefinitely.

## Outcome

The frozen evaluation suite held 500 narratives: 100 oversampled
expedited-reportable positives and 400 general. On the
narrative-classification dimension, judge calibration against human reviewers
improved agreement from κ≈0.54 uncalibrated to κ≈0.81 after two rounds of
criteria refinement. The judge was not trusted until that was reached.

Then the reliability check found what a single-shot number had hidden. On the
expedited-reportable class, pass^1 recall was 96% — but pass^3, meaning all
three sampled attempts agree and are correct, fell to 88%. That is a real
collapse under repetition, not sampling noise. Rather than report the
flattering pass^1 figure, the team changed the design: any case where three
sampled attempts disagree now routes automatically to a human reviewer with
no system recommendation attached, and only cases that are unanimous and
correct on audit carry a system flag at all.

Shadow ran for 6 weeks over 3,400 mirrored narratives: 94% agreement with
human triage, and 0.6% regret cases — instances where the system would have
missed something a human caught. All of them were absorbed by the shadow
design, with zero production impact. The rollback rehearsal's caught defect
cost two days to fix before canary opened. Canary then ran at 8% of real
narrative volume for 4 weeks, still fully human-gated: zero missed
expedited-reportable cases, and agreement holding near the shadow figure.

Full production promotion was deliberately deferred to the next quarter,
pending a second periodic methodology audit (chapter 12), rather than
promoted on canary results alone. Total effort: roughly 3 FTE over 4 months,
with no capital spend.

## Chapter trail

- [00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) — rigor dial,
  rule of proportion
- [01. Project Intake and Decision Context](../01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) —
  stakes-tier intake from the profile's failure-cost field
- [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) — judge
  calibration, deterministic verification
- [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) —
  pass^k reliability claims
- [08. Retrieval, Tools, Workflows, and Routing](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) —
  tool-contract discipline, read-only permissions
- [10. Deployment and Operations](../10_DEPLOYMENT_AND_OPERATIONS.md) —
  shadow → canary promotion gate, rollback rehearsal
- [12. Observability, Learning, and Promotion](../12_OBSERVABILITY_LEARNING_AND_PROMOTION.md) —
  telemetry floor, privacy redaction before harvest, methodology audit
- [13. Governance, Provenance, and Security](../13_GOVERNANCE_PROVENANCE_AND_SECURITY.md) —
  record of record, ground-truth isolation, clean-room boundary

---

> [Index](../README.md) · [Examples](README.md)
