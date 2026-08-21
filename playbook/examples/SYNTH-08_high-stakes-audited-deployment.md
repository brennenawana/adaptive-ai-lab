# SYNTH-08: A Regulated Adverse-Event Triage Assistant

> [Index](../README.md) · [Examples](README.md)

*Synthetic worked example — all names and numbers invented.*

---

## Profile summary

"Aldermere Biosciences," a mid-size pharmaceutical safety/compliance team,
builds a decision-support assistant that triages incoming adverse-event
narratives (patient and provider intake forms) and flags candidates that may
require expedited regulatory reporting. The system recommends; a human safety
reviewer decides. Nothing it produces is ever submitted anywhere on its own.

| [Project profile](../GLOSSARY.md#project-profile) field | Value |
|---|---|
| Business outcome | Cut time-to-flag on narratives that may need expedited regulatory reporting |
| Task population & volume | ~600 intake narratives/month across three product lines |
| Criticality / failure cost | Missed expedited-reportable case → regulatory-deadline and safety exposure; false positive → reviewer time only (asymmetric cost) |
| Quality / reliability target | Near-ceiling recall on the expedited-reportable class; decision-support only, never the final decision |
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
human approves every action, and nothing writes anywhere on its own — and
that last fact does not lower the tier. [Stakes tier](../GLOSSARY.md#stakes-tier)
attaches to the *decision's* consequence, here a possibly missed
expedited-reportable signal, not to how much autonomy the system has or how
small the team is. The failure-cost field alone is enough to fix this at
**Tier 3** before a single model is chosen (rule of proportion,
[00 §6](../00_PRINCIPLES_AND_SCOPE.md)). The full Tier-3 artifact set
therefore applies: tamper-evident provenance, pass^k reliability claims,
judge calibration wherever a judge is used, staged shadow→canary with human
approval, a rehearsed rollback path, and a periodic methodology audit.

## The decisive moves

1. **Stakes tier fixed at intake, before model selection.** The failure-cost
   and regulatory fields on the profile drove the tier call directly; no
   candidate model, harness, or budget question was allowed to happen first.
   Overriding it would need a written
   [method decision record](../GLOSSARY.md#method-decision-record); none was
   written, so Tier 3 stands.
2. **Governance instantiated before the first eval run, not after
   selection.** A [record of record](../GLOSSARY.md#record-of-record) was
   stood up first; [ground-truth isolation](../GLOSSARY.md#ground-truth-isolation)
   separated the expedited/non-expedited gold labels from anything
   model-facing; a [clean-room boundary](../GLOSSARY.md#clean-room-boundary)
   statement excluded protected narratives from any vendor training path;
   every field of the [trajectory record](../GLOSSARY.md#trajectory-record)
   was classified for privacy sensitivity, with redaction defined before any
   telemetry was collected (chapter 13).
3. **Deterministic verification where the field allows it, judge calibration
   where it does not.** Structured fields (product code, event date,
   seriousness criteria) score deterministically. The narrative-classification
   step needed a judge; because unvalidated judges score near chance on
   objectively verifiable tasks [EXT-JUDGE-002], the judge was calibrated
   against three independent human reviewers before it was trusted for
   anything (chapter 03).
4. **A pass^1 number was not enough for a reliability claim.** Both
   candidates are stochastic. A [pass^k](../GLOSSARY.md#pass-at-k-vs-pass-to-the-k)
   check on a held-out subset, not just pass@1, was run before any
   reliability claim was made [EXT-AGENT-001] — see Outcome for what it
   found and how the design responded (chapter 04).
5. **[DECISION GATE] Shadow-to-canary promotion.** Entry to canary required
   all of: measured shadow agreement above a pre-registered floor, regret
   rate below a pre-registered ceiling, and a passed rollback rehearsal —
   following the restraint doctrine of running the simplest model that meets
   the objective, one change at a time [EXT-OPS-001C] (chapter 10).
   [Observe-only graduation](../GLOSSARY.md#observe-only-graduation) to an
   *automated* flagging action was explicitly not pursued for this
   consequence class — a permanent design choice, not a "not yet."
6. **Rollback rehearsed before go-live, and it caught something real.** The
   rehearsal surfaced a checkpoint/retrieval-index version mismatch that
   would have silently served stale product-label context in production. It
   was fixed pre-promotion. A [rollback path](../GLOSSARY.md#rollback-path)
   that has never been exercised is a hypothesis, not a path — this one
   earned its keep before it was ever needed live.

## What was skipped and why

- **Chapter 11's demand-ledger / purchase-trigger machinery.** No hardware
  purchase was on the table — existing validated-environment compute covers
  the volume — so it was legitimately not engaged this cycle.
- **Chapter 09 (training).** The ladder was not exhausted: the gaps found in
  evaluation were specification and context gaps (rungs 2 and 4), closed by
  prompt/workflow and lookup-tool changes, not a demonstrated learnable-skill
  gap. Training was never reached, let alone justified.
- **Learned routing / multi-tier cascades (08).** Volume does not justify a
  second tier; a single verifier-plus-judge pipeline with human review is the
  whole system. Tool-contract discipline for the two read-only lookups was
  still applied in full.
- **Automating the flag-and-submit action.** As in move 5, this is a standing
  refusal for this consequence class, not a deferred item — expedited-report
  submission stays a human action indefinitely.

## Outcome

The frozen evaluation suite held 500 narratives (100 oversampled
expedited-reportable positives, 400 general). Judge calibration against
human reviewers on the narrative-classification dimension improved agreement
from κ≈0.54 uncalibrated to κ≈0.81 after two rounds of criteria refinement —
the judge was not trusted until this was reached. On the
expedited-reportable class, pass^1 recall was 96%, but pass^3 (all three
sampled attempts agree and are correct) fell to 88% — a real collapse under
repetition, not just sampling noise. Rather than report the flattering pass^1
figure, the team changed the design: any case where three sampled attempts
disagree routes automatically to a human reviewer with no system
recommendation attached, and only unanimous-and-correct-on-audit cases carry
a system flag at all.

Shadow ran for 6 weeks over 3,400 mirrored narratives: 94% agreement with
human triage, 0.6% regret cases (the system would have missed something a
human caught) — all absorbed by the shadow design with zero production
impact. The rollback rehearsal's caught defect cost two days to fix before
canary opened. Canary then ran at 8% of real narrative volume for 4 weeks,
still fully human-gated: zero missed expedited-reportable cases, agreement
holding near the shadow figure. Full production promotion was deliberately
deferred to the next quarter, pending a second periodic methodology audit
(chapter 12) rather than promoted on canary results alone. Total effort:
roughly 3 FTE over 4 months; no capital spend.

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
