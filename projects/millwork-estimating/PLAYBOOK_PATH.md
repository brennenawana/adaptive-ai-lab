# High-Level Playbook Path

This is the project's current implementation path for the Adaptive AI Systems
Playbook. It is intentionally **frontier-first, evaluation-first, and
human-in-the-loop**. Local inference and fine-tuning remain available, but neither is
a prerequisite for useful work.

## 0. Discovery boundary — now

Goal: understand the real workflow without pretending public examples are client
ground truth.

Actions:
1. Preserve the prospect-supplied process description as a primary source.
2. Build a public surrogate corpus to learn document classes and likely schemas.
3. Request a very small example set: drawings, completed takeoff, Bid Recap,
   proposal, and job-cost summary if readily available.
4. Prefer one coherent completed project chain over unrelated examples.
5. Resolve privacy/API admissibility before sending real client documents to any
   managed model.

**Stop condition:** do not make claims about automating this company's estimate
accuracy from surrogate documents alone.

## 1. Profile the decision and task population

Complete the project profile with the client and turn the prose workflow into a task
ontology. Likely task families:

- bid Go/No-Go evidence extraction;
- revision/document completeness;
- room/sheet coverage;
- scope-item detection;
- quantity/takeoff;
- material/finish classification;
- spec/qualification extraction;
- labor/install calculation;
- estimate sanity checks;
- exclusions/questions;
- proposal assembly;
- estimate-to-actual variance analysis.

For each family define failure cost and whether deterministic ground truth is possible.

## 2. Build the evaluation substrate before optimizing

Historical completed projects should become the primary corpus. Split by **project**,
not by individual line item, so near-duplicate sheets/details from one job cannot leak
across evaluation partitions.

Candidate measurements:

| Dimension | Example metric |
|---|---|
| Scope coverage | recall of commercially material scope items / missed-scope count |
| Quantity | absolute/relative error within item-specific tolerance; signed bias |
| Materials/finishes | classification accuracy + unresolved/abstention quality |
| Source grounding | correct sheet/page/detail/spec reference rate |
| Qualifications | recall of material exclusions/questions + false-positive burden |
| Arithmetic | exact deterministic agreement |
| Proposal fields | exact match / approved-value consistency |
| Human burden | review minutes, edits/item, accepted unchanged rate |
| Correction severity | none / minor / major / missed scope / dollar-impact class |
| Commercial outcome | estimate-vs-actual variance where comparable |

Do not collapse these into one score too early. A system can have excellent average
quantity error and still miss one expensive scope item.

First baseline should include the incumbent human process where feasible. Human-human
agreement on ambiguous items is itself useful: it gives a ceiling/uncertainty estimate
rather than pretending every disagreement has a single obvious gold label.

## 3. Freeze a capable baseline execution system

The first serious AI baseline should clear the capability floor rather than optimize
for cheap tokens.

Default hypothesis:

```text
strong frontier multimodal model
+ revision-aware document ingestion
+ bounded retrieval/navigation
+ structured tool contracts
+ deterministic estimating/calculation tools
+ explicit source provenance
+ verifier / coverage checks
+ human approval
```

Start with one strong production-plausible model or a very small bounded frontier set.
Do not spend the first month building routing, local serving, or training pipelines.
Record the complete execution-system identity: model/version, provider, harness,
context policy, tools, workflow, generation/reasoning budget, verifier, and input
revision set.

## 4. Improve workflows and agent skills experimentally

Once the eval exists, treat **skills, process, tools, context policy, and workflow
topology** as candidate interventions even if the underlying model is unchanged.

Examples:
- room-by-room coverage skill;
- cross-sheet reference-following skill;
- finish-schedule reconciliation skill;
- takeoff schema/tool contract;
- spec requirement extractor;
- deterministic quantity/labor calculator;
- exclusion/question generator;
- estimate verifier;
- proposal assembler.

For consequential comparisons, freeze one factor at a time when practical and
predeclare what result changes the decision. Prefer paired evaluation on the same
projects/items.

## 5. Shadow the human workflow before asking for autonomy

Build an estimator copilot first.

```text
AI proposes
   ↓
human reviews source evidence
   ↓
accept / edit / reject / missed-scope label
   ↓
correction + review time stored
   ↓
approved artifact continues downstream
```

This phase should answer two business questions:

1. Does the system reduce estimator time?
2. Does it preserve or improve commercially material quality?

A useful optimization objective is therefore not "maximum automation" but something
like:

> minimize human review minutes subject to no increase in commercially material error.

Autonomy can be earned per subtask. Deterministic arithmetic may earn autonomy long
before ambiguous drawing interpretation or final pricing.

## 6. Use the intervention ladder on diagnosed failures

Follow playbook chapter 07 rather than jumping from "model missed something" to
"fine-tune it."

Project interpretation of the ladder:

0. **Instrument integrity** — bad labels, broken measurement, stale revisions,
   invalid scales, leakage, scorer defects.
1. **Infrastructure/runtime** — provider/runtime/serialization/reproducibility issues.
2. **Evidence/retrieval/context** — required drawing/spec/detail was not reachable.
3. **Tool contracts/output enforcement** — wrong schema, units, tool addressing,
   parsing, or structured-output failure.
4. **Specification/verification** — workflow/skill unclear; missing coverage or
   correctness checks.
5. **Generation/reasoning budget** — task is capable but bounded by context/output or
   reasoning budget.
6. **Routing/escalation** — only if oracle analysis shows a cheaper/specialist tier can
   preserve quality and a gate/router can capture the headroom.
7. **Fine-tuning** — only for a residual learnable capability gap after the cheaper
   defects are cleared and labeled data contains the needed skill.
8. **Larger/different model** — when residual capability is fundamentally model-bound.
9. **Architecture redesign** — when evidence says topology, not a component, is the
   binding limitation.

Fine-tuning around missing evidence, a bad takeoff schema, stale drawings, or a broken
verifier is explicitly blocked.

## 7. Local models: use as experimental proxies only after transfer is measured

Local inference may become strategically valuable for high-volume R&D, but the wrong
proxy can create a tuning loop where engineering effort compensates for a capability
deficit that the frontier production model does not have.

Therefore local proxy adoption needs its own evidence gate.

For the same intervention set, compare:

```text
Δ local proxy
Δ frontier production target
```

Measure at least:
- sign agreement: did the intervention help/hurt both?;
- rank agreement across candidate workflows;
- adoption-decision agreement at the project threshold;
- error-taxonomy overlap;
- magnitude correlation where meaningful.

Classify portability by intervention. Deterministic calculators and coverage logic may
transfer nearly perfectly; exact prompt wording or reasoning tricks may not.

**Decision rule:** use local models for high-volume experiments only in intervention
classes where transfer is empirically adequate. If transfer is poor, stop optimizing
the local model and run that class directly on the frontier target.

The local model does **not** need the same absolute score as the frontier model. It
needs to predict the direction/ranking of system improvements.

## 8. Fine-tuning / LoRA is an earned experiment, not a milestone

A fine-tuning experiment becomes reasonable when all are true:

- the residual failure is repeated and taxonomy-consistent;
- required evidence is already present/reachable;
- tool contracts and verification are clean;
- prompt/workflow/skill improvements have been exhausted to a declared bar;
- enough high-quality labeled corrections exist;
- training data actually contains the target behavior;
- a paired untuned baseline and MDE/adoption rule are frozen;
- expected economics justify the experiment.

Possible uses could include highly repetitive scope classification, company-specific
material/finish conventions, or standardized takeoff behavior. But the evidence may
also say no training is needed; that is a successful finding, not a failure of the
project.

## 9. Production pilot

Only after shadow evidence clears the adoption bar:

- canary on a bounded set of real bids;
- final estimator approval remains mandatory;
- source provenance and execution-system identity retained;
- rollback path is simple;
- monitor correction severity and review time, not merely model success rate;
- never auto-submit a proposal during the initial pilot.

The first production win may be partial: e.g. document setup + scope coverage +
draft takeoff + deterministic recap population, while the estimator retains final
scope/pricing judgment.

## 10. Close the learning loop

Long-term advantage comes from proprietary outcome evidence:

```text
historical bid package
      ↓
AI + human estimate
      ↓
submitted proposal
      ↓
won/lost project
      ↓
actual material / labor / install / change orders
      ↓
variance + correction labels
      ↓
next evaluation suite
```

This can reveal whether errors come from quantities, pricing, labor assumptions,
installation, scope gaps, revisions, or commercial strategy. It also creates the data
needed to decide whether routing, local proxies, fine-tuning, or a different model is
actually valuable.

## Near-term first three actions

1. Obtain one sanitized completed-project chain if the prospect is comfortable
   sharing it.
2. Convert that project into a small traceable evaluation pilot before building a
   broad automation product.
3. Run one capable frontier baseline through the full document→takeoff→recap review
   path and classify failures before choosing the next intervention.
