# SYNTH-01: API-Only Support Assistant

> [Index](../README.md) · [Examples](README.md)

*Synthetic worked example — all names and numbers invented.*

---

## Profile summary

The [project profile](../GLOSSARY.md#project-profile) fields that route this
project (template: [PROJECT_PROFILE](../templates/PROJECT_PROFILE.md)):

| Field | Value |
|---|---|
| Business outcome | Deflect first-line chat-support volume for an outdoor-gear retailer; hold a CSAT proxy at or above the human-agent baseline |
| Task population & volume | ~40,000 chat conversations/month; open-ended natural-language questions about order status, product fit, and return policy |
| Criticality / failure cost | Moderate, reversible — a wrong policy answer costs a manual correction, not an irreversible action |
| Quality / reliability target | Policy answers must be citation-grounded; tone and helpfulness held to a judged bar |
| Latency / throughput / SLA | Interactive chat; first-token latency in the low seconds |
| Privacy / security / residency | Order data must never surface across customers; no residency mandate |
| Data & knowledge availability | Help-center articles, the return-policy document, a read-only order-lookup API; ~400 unlabeled historical transcripts |
| Tool / action permissions | Read-only order lookup at launch; no refunds or account writes |
| Model candidates | Three managed-API models spanning small/mid/large tiers; no open-weights candidates in scope |
| Owned / rentable compute | None — explicitly out of scope |
| Managed APIs | The only execution surface |
| Capex / recurring budget | No capex; a capped monthly API-spend line |
| Staffing / time | Two engineers, part-time, a six-week runway to first release |
| Deployment environment | Existing chat widget, managed cloud |
| Existing evidence | Historical transcripts only; no prior eval, no incumbent automated system |
| Stakes / consequence tolerance | Tier 2 — customer-visible, business-consequential, reversible |

## Archetype & rigor tier

The routing facts: no owned or rentable compute, three managed-API candidates, no
incumbent system, and a task domain that mixes objectively checkable sub-questions
(order status, policy citation) with genuinely open-ended ones (tone,
helpfulness). That combination fires the **API-only greenfield**
[archetype](../GLOSSARY.md#archetype) — the QUICKSTART route that skips
runtime/hardware chapters at intake and drops the project straight into building a
trustworthy eval.

Stakes tier is **Tier 2 (Consequential)**: the system is customer-visible and drives
a real business metric, but the launch scope (read-only, human-correctable) keeps
blast radius reversible. Per the rule of proportion, a later phase adding
autonomous refund actions would escalate *that* decision — not the whole
project — to Tier-3 artifacts at the point it is proposed.

## The decisive moves

1. **Eval before model choice.** The evaluate-first principle
   ([00 §4](../00_PRINCIPLES_AND_SCOPE.md)) is applied literally: the first third
   of the six-week runway builds a [task ontology](../GLOSSARY.md#task-ontology)
   from the 400 historical transcripts (error-analysis-first, chapter 03) before
   any candidate model is called. No model is selected against an eval that does
   not yet exist.
2. **Grader split by task shape.** Order-status and policy-citation items get a
   [deterministic grader](../GLOSSARY.md#deterministic-gate) (does the cited
   policy clause exist and match the order record); tone/helpfulness items are
   genuinely open-ended and are routed to an LLM judge under chapter 03's
   decision rule — never the reverse.
3. **[DECISION GATE] Judge calibration, round 1, fails.** The judge is checked
   against a 60-item human-labeled anchor set before it is trusted for anything.
   Raw agreement looks strong (84%), but chance-corrected agreement (the
   deflation warning in chapter 03's
   [judge-calibration protocol](../03_EVALUATION_FOUNDATION.md)) comes in under
   the pre-registered bar of κ = 0.65. The team does **not** ship the judge on
   raw agreement: the rubric had conflated "helpful" with "polite", so it is
   split into two dimensions and a round-2 calibration is run before the judge
   scores anything that feeds a decision. This is the gate the archetype exists
   to force — an open-ended metric is inadmissible until it has passed
   calibration, not until it looks plausible.
4. **Frozen, paired candidate comparison.** The three managed-API candidates are
   compared under one [experiment contract](../GLOSSARY.md#experiment-contract)
   (chapter 04): same items, [clustering unit](../GLOSSARY.md#clustering-unit) =
   question template, [MDE](../GLOSSARY.md#mde) stated before data. A screening
   pass (chapter 04's [screening vs inference](../GLOSSARY.md#screening-vs-inference)
   split) narrows three candidates to one; only the frozen comparison licenses
   the launch decision.
5. **Observe-only before any write action.** Tool permissions stay read-only at
   launch; an [observe-only graduation](../GLOSSARY.md#observe-only-graduation)
   path (chapters 08 and 10) is pre-registered for a future refund-write
   capability, gated on a shadow period with measured agreement against human
   agent decisions — not built or scheduled for this release.
6. **Economics entered late, not first.** Cost per resolved ticket
   (chapter 11) is computed only after the frozen comparison and the judge
   pass, as one input to the launch decision alongside CSAT — never as the
   reason to skip the eval.

## What was skipped and why

- **Chapter 06 (inference performance/capacity):** no owned or rented inference
  to characterize — the provider owns serving. Revisited only if provider-side
  latency becomes the binding constraint post-launch.
- **Chapter 09 (training/data):** no [RC-10](../GLOSSARY.md#canonical-failure-taxonomy)
  evidence exists yet; the ladder has not been descended past prompt/workflow
  rungs, so fine-tuning is not on the table (00 §4 P3).
- **Chapter 11 hardware/demand-ledger machinery:** no compute is owned or
  rented; the [demand ledger](../GLOSSARY.md#demand-ledger) and
  [purchase trigger](../GLOSSARY.md#purchase-trigger) do not apply to an
  API-only project.
- **Tier-3 governance machinery** (tamper-evident record of record, pass^k
  reliability claims): the Tier-2 signature does not require it; a frozen
  experiment contract and a versioned suite carry the decision.

## Outcome

The mid-tier candidate wins the frozen comparison within its predicted interval;
the large candidate's edge on the policy-citation stratum does not clear the
design's MDE and is not adopted on that margin (chapter 04's
[elimination rule](../GLOSSARY.md#elimination-rule)). Round-2 judge calibration
clears κ = 0.71. Launch handles an estimated 27% of conversations fully
autonomously (read-only), at a projected API spend of about $2,200/month against
a $3,000 budget line, with the refund-write capability left in the
pre-registered observe-only queue for a later release.

## Chapter trail

[00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) ·
[01. Project Intake and Decision Context](../01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) ·
[03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) ·
[04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) ·
[08. Retrieval, Tools, Workflows, and Routing](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) ·
[10. Deployment and Operations](../10_DEPLOYMENT_AND_OPERATIONS.md) ·
[11. Economics, Hardware, and Cloud](../11_ECONOMICS_HARDWARE_AND_CLOUD.md) ·
[GLOSSARY](../GLOSSARY.md)

---

> [Index](../README.md) · [Examples](README.md)
