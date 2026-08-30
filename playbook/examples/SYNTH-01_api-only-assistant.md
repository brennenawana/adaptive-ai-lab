# SYNTH-01: API-Only Support Assistant

> [Index](../README.md) · [Examples](README.md)

*Synthetic worked example — all names and numbers invented.*

---

## Profile summary

One customer asks where their order is. A script can take that answer, check it against
the order record, and mark it right or wrong. The next customer asks whether a jacket
runs small, and no script will ever tell you whether the reply was any good. Both land in
the same chat queue at an outdoor-gear retailer. Before this project can choose between
three managed-API models, it has to be able to grade both kinds of answer — and there is
no hardware anywhere in scope to complicate the choice.

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

Four facts do the routing. There is no compute to own or rent. There are three
managed-API candidates. There is no incumbent automated system to diagnose or repair.
And the task mixes sub-questions a script can check — order status, policy citation —
with genuinely open-ended ones like tone and helpfulness. Nothing in QUICKSTART's tree
fires before the final branch, so this is the **API-only greenfield**
[archetype](../GLOSSARY.md#archetype), QUICKSTART's A: runtime and hardware chapters stay
closed at intake, and the project goes straight to building an evaluation it can trust.

Stakes tier is **Tier 2 (Consequential)**. The assistant is customer-visible and moves a
real business metric, which rules out Tier 1. The launch scope is read-only and every
wrong answer can be corrected by hand, which keeps the blast radius reversible. Rigor
attaches to the decision rather than to the project, so a later phase that lets the
assistant issue refunds on its own would escalate *that* decision — not the whole
project — to Tier-3 artifacts at the point it is proposed.

## The decisive moves

1. **Eval before model choice.** The evaluate-first principle
   ([00 §4](../00_PRINCIPLES_AND_SCOPE.md), P1) is applied literally. The first third of
   the six-week runway goes into reading the 400 historical transcripts and turning them
   into a [task ontology](../GLOSSARY.md#task-ontology) — the list of what customers
   actually ask and how each kind of question fails (chapter 03's error-analysis-first
   procedure). No candidate model is called until that exists. You cannot select against
   an eval that does not yet exist.
2. **Grader split by task shape.** Order-status and policy-citation items are checkable
   by code: does the cited policy clause exist, and does it match the order record? Those
   get a [deterministic grader](../GLOSSARY.md#deterministic-gate). Tone and helpfulness
   are not checkable by code, so they go to an LLM judge under chapter 03's decision
   rule. That rule runs in one direction only — a judge never takes work a script could
   have done.
3. **[DECISION GATE] Judge calibration, round 1, fails.** Before the judge is trusted for
   anything, it grades a 60-item anchor set that humans have already labeled, and the two
   sets of labels are compared. They agree 84% of the time, which sounds strong. On its
   own it is not: two raters who both say "helpful" most of the time will agree often by
   luck alone, so the number that counts is the one that subtracts the agreement luck
   would have produced anyway. That corrected figure — chapter 03's
   [judge-calibration protocol](../03_EVALUATION_FOUNDATION.md) (§5.7) warns how far it
   falls below raw agreement — comes in under the pre-registered bar of κ = 0.65. The
   team does **not** ship the judge on raw agreement. The rubric turned out to conflate
   "helpful" with "polite", so it is split into two dimensions and a round-2 calibration
   is run before the judge scores anything that feeds a decision. This is the gate the
   archetype exists to force: an open-ended metric is inadmissible until it has passed
   calibration, not until it looks plausible.
4. **Frozen, paired candidate comparison.** The three managed-API candidates are compared
   under one [experiment contract](../GLOSSARY.md#experiment-contract) (chapter 04): the
   same items for every candidate, the [clustering unit](../GLOSSARY.md#clustering-unit)
   declared as the question template, and the [MDE](../GLOSSARY.md#mde) — the smallest
   true difference this design can detect — stated before any data is collected. A cheap
   screening pass narrows three candidates to one (chapter 04's
   [screening vs inference](../GLOSSARY.md#screening-vs-inference) split). Only the
   frozen comparison licenses the launch decision.
5. **Observe-only before any write action.** Tool permissions stay read-only at launch. A
   future refund-write capability already has its path pre-registered —
   [observe-only graduation](../GLOSSARY.md#observe-only-graduation) (chapters 08 and
   10): the assistant would propose the refund, a human agent would decide, and agreement
   between the two would be measured over a shadow period before anything executed on its
   own. Pre-registered is all it is. It is not built and not scheduled for this release.
6. **Economics entered late, not first.** Cost per resolved ticket (chapter 11) is
   computed only after the frozen comparison and after the judge passes calibration. It
   is one input to the launch decision alongside CSAT — never the reason to skip the
   eval.

## What was skipped and why

- **Chapter 06 (inference performance/capacity):** there is no owned or rented inference
  to characterize, because the provider owns serving. Revisited only if provider-side
  latency becomes the binding constraint after launch.
- **Chapter 09 (training/data):** no [RC-10](../GLOSSARY.md#canonical-failure-taxonomy)
  evidence exists yet, and the ladder has not been descended past its prompt and workflow
  rungs, so fine-tuning is not on the table (00 §4 P3).
- **Chapter 11 hardware/demand-ledger machinery:** no compute is owned or rented. The
  [demand ledger](../GLOSSARY.md#demand-ledger) and
  [purchase trigger](../GLOSSARY.md#purchase-trigger) have nothing to describe on an
  API-only project.
- **Tier-3 governance machinery** (tamper-evident record of record, pass^k reliability
  claims): the Tier-2 signature does not require it. A frozen experiment contract and a
  versioned suite carry this decision.

## Outcome

The mid-tier candidate wins the frozen comparison, inside the interval the contract
predicted. The large candidate does look better on the policy-citation stratum, but that
edge does not clear the design's MDE, and it is not adopted on that margin (chapter 04's
[elimination rule](../GLOSSARY.md#elimination-rule)). Round-2 judge calibration clears
κ = 0.71. At launch the assistant handles an estimated 27% of conversations fully
autonomously, read-only, at a projected API spend of about $2,200/month against a $3,000
budget line. The refund-write capability stays in the pre-registered observe-only queue
for a later release.

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
