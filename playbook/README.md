# Adaptive AI Systems Playbook

**Version 0.1.1** · [Changelog](CHANGELOG.md) · [Glossary](GLOSSARY.md) ·
[Quickstart](QUICKSTART.md)

A playbook for building AI systems, written to be used on a project you already
have. It runs from requirements and constraints through evaluation, model and
runtime selection, experimentation, optimization, training decisions, serving,
economics, deployment, observability, and continuous improvement.

It exists to answer one question, over and over, for a concrete project: **what
should I do next?** Along with the questions that turn out to be the same question —
why that and not something else, what evidence do I need, what should I measure,
what can I skip, what should force me to stop or change direction, and when is an
expensive intervention justified.

## Who this is for

An engineer, or a small team, holding a product or a problem plus some subset of:
candidate models, owned or rentable compute, cloud and API providers, a budget,
latency and quality constraints, data and privacy restrictions, and not enough
people. What that team usually lacks is not instructions. Vendor documentation
already tells you how to *execute* each stage, and there is a lot of it.

What is missing is the layer above: stop or continue, promote or roll back, select
this model or that one, buy the hardware or rent it, trust this number or go measure
it again. That decision layer is what this book supplies. Every rule in it carries
the evidence behind it and a
[strength label](GLOSSARY.md#evidence-strength-labels) saying how far that evidence
goes.

Everything here stands alone: no external project context, no private
infrastructure, no proprietary assumptions. The worked examples in
[examples/](examples/README.md) are invented — they illustrate the reasoning, and
they are never the evidence for a rule. No single project's numbers are handed to
you as defaults.

## The first twenty minutes

1. Read [00 — Principles and Scope](00_PRINCIPLES_AND_SCOPE.md) §4 (the twelve
   principles) and §6 (the rigor dial). *(~7 min)*
2. Open [QUICKSTART](QUICKSTART.md) and fill in
   [templates/PROJECT_PROFILE.md](templates/PROJECT_PROFILE.md). *(~10 min)*
3. Take the archetype route it gives you. It names your first three actions and the
   chapters you may leave closed for now.

Your first sprint ends at a frozen
[experiment contract](templates/EXPERIMENT_CONTRACT.md) (Tier 2+), or a written
lightweight plan (Tier 1). Everything routes there.

## The lifecycle

```
define decision/problem (01) → trustworthy eval substrate (03) → integrity/ceilings (03)
→ simplest credible baseline (05) → frozen execution-system identity (02)
→ candidate characterization (05/06) → failure diagnosis (03/07)
→ intervention choice (07 → 08|09) → capability/quality eval (04)
→ performance characterization (06) → economics (11) → shadow/canary (10)
→ promote / rollback (10) → production evidence back into learning (12 → 03)
```

## The book

Each chapter exists to get one kind of decision made. The right-hand column names it.

| # | Chapter | The decision it helps you make |
|---|---|---|
| 00 | [Principles and Scope](00_PRINCIPLES_AND_SCOPE.md) | How much rigor this project actually owes, and which rung of the intervention ladder you are allowed to reach for |
| 01 | [Project Intake and Decision Context](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) | What a fuzzy request is really asking for — and what to do in the first week |
| 02 | [Execution System Model](02_EXECUTION_SYSTEM_MODEL.md) | Whether two numbers came from the same system, and may therefore be compared |
| 03 | [Evaluation Foundation](03_EVALUATION_FOUNDATION.md) | Whether your eval can be trusted yet, and what kind of failure you are looking at |
| 04 | [Experiment Design and Statistics](04_EXPERIMENT_DESIGN_AND_STATISTICS.md) | Whether a difference you measured is real, and what happens when it isn't |
| 05 | [Model, Runtime, and Harness Selection](05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md) | Which handful of candidates to test, and which class of runtime to commit to |
| 06 | [Inference Performance and Capacity](06_INFERENCE_PERFORMANCE_AND_CAPACITY.md) | Whether this system can carry your load — and what the benchmark left out |
| 07 | [Optimization and the Intervention Ladder](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) | Which fix to try, given a measured gap — and how to test that cheaply first |
| 08 | [Retrieval, Tools, Workflows, and Routing](08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) | Whether to add retrieval, tools, or a cascade — and whether a learned router earns its place |
| 09 | [Training and Data](09_TRAINING_AND_DATA.md) | Whether to fine-tune at all: the evidence bar, the legal check, the forgetting gate |
| 10 | [Deployment and Operations](10_DEPLOYMENT_AND_OPERATIONS.md) | Whether to ship it, how far to expose it, and how you get back if it goes wrong |
| 11 | [Economics, Hardware, and Cloud](11_ECONOMICS_HARDWARE_AND_CLOUD.md) | Rent, buy, or call an API — decided on measured demand rather than on a hunch |
| 12 | [Observability, Learning, and Promotion](12_OBSERVABILITY_LEARNING_AND_PROMOTION.md) | What to record before a long run, and how production failures become next quarter's eval |
| 13 | [Governance, Provenance, and Security](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md) | What you must be able to prove later, and what must never be reachable |
| 14 | [Decision Trees and Checklists](14_DECISION_TREES_AND_CHECKLISTS.md) | Any of the above, fast — every gate and checklist from 00–13, condensed |

A few chapters do not sit still in that order, and it is worth knowing which:
**02 comes before any cross-run comparison**; **04 gates every selection or
intervention experiment**; **11 gets consulted three times** — at intake, at
capacity, at deployment — rather than read once; **13 is instantiated at intake**
for Tier-3 work; and **12 closes the loop back to 03**.

## "I need to…"

| I need to… | Go to |
|---|---|
| start a new project and not know where to begin | [QUICKSTART](QUICKSTART.md) |
| work out whether my eval is any good | [03](03_EVALUATION_FOUNDATION.md) §instrument validation; [templates/EVAL_SUITE_RELEASE_CONTRACT.md](templates/EVAL_SUITE_RELEASE_CONTRACT.md) |
| compare two models or two configs, defensibly | [04](04_EXPERIMENT_DESIGN_AND_STATISTICS.md); [templates/EXPERIMENT_CONTRACT.md](templates/EXPERIMENT_CONTRACT.md) |
| work out why the numbers moved when nothing changed | [02](02_EXECUTION_SYSTEM_MODEL.md) |
| fix something that is already live and not good enough | [07](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) — diagnose first: [03](03_EVALUATION_FOUNDATION.md) §taxonomy |
| decide whether it is time to fine-tune | [07](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) §evidence bar → [09](09_TRAINING_AND_DATA.md) |
| get the API bill down without wrecking quality | [08](08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) + [11](11_ECONOMICS_HARDWARE_AND_CLOUD.md) §break-even |
| decide whether to buy a GPU | [11](11_ECONOMICS_HARDWARE_AND_CLOUD.md); [templates/COMPUTE_DEMAND_LEDGER.md](templates/COMPUTE_DEMAND_LEDGER.md) |
| find out how fast this thing actually serves | [06](06_INFERENCE_PERFORMANCE_AND_CAPACITY.md) |
| grade open-ended outputs with a model as the judge | [03](03_EVALUATION_FOUNDATION.md) §judge calibration |
| ship to production without breaking anything | [10](10_DEPLOYMENT_AND_OPERATIONS.md); gates in [14](14_DECISION_TREES_AND_CHECKLISTS.md) |
| set up logging before I kick off a long run | [12](12_OBSERVABILITY_LEARNING_AND_PROMOTION.md) §telemetry floor |
| prove to an auditor that my results are what I say | [13](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md) |
| find a formula | [references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md) |
| check whether a vendor recipe is still current | [references/SOURCES.md](references/SOURCES.md) + [references/VENDOR_RECIPE_NOTES.md](references/VENDOR_RECIPE_NOTES.md) |

## Project-type reading paths

Projects come in six shapes here, and [QUICKSTART](QUICKSTART.md) sorts you into one
of them by reading facts off your profile: greenfield API-only (A), local or private
mandate (B), existing system underperforming (C), cost reduction (D),
high-stakes/compliance (E), lab bootstrap (F). Each shape gets its own entry
chapters, skippable chapters, mandatory templates, and first three actions.

To see it run before you run it:
[examples/WALKTHROUGH_rag-document-qa.md](examples/WALKTHROUGH_rag-document-qa.md)
is one full pass; [examples/SYNTH-01…10](examples/README.md) are compact passes, one
per shape.

## Templates

Nine of them, in [templates/](templates/): [PROJECT_PROFILE](templates/PROJECT_PROFILE.md) ·
[EXPERIMENT_CONTRACT](templates/EXPERIMENT_CONTRACT.md) ·
[EVAL_SUITE_RELEASE_CONTRACT](templates/EVAL_SUITE_RELEASE_CONTRACT.md) ·
[PERFORMANCE_AUTOPSY](templates/PERFORMANCE_AUTOPSY.md) ·
[TEST_LOOK_LEDGER](templates/TEST_LOOK_LEDGER.md) ·
[COMPUTE_DEMAND_LEDGER](templates/COMPUTE_DEMAND_LEDGER.md) ·
[PREDICTION_LEDGER](templates/PREDICTION_LEDGER.md) ·
[OPERATIONAL_HANDOFF](templates/OPERATIONAL_HANDOFF.md) ·
[METHOD_DECISION_RECORD](templates/METHOD_DECISION_RECORD.md).

Each one gives you its purpose, when to use it, its required sections ("delete no
section — write N/A + reason"), and a filled-in miniature example.

If you adopt nothing else from this book, adopt the three ledgers. They are the
least obvious of the nine and the most portable: one records every look you take at
held-out data, one records what you predicted before each run and scores it against
what happened, and one records the compute you actually used, kept up before any
purchase decision.

## Vendor recipes and references

- [references/SOURCES.md](references/SOURCES.md) — every source this playbook cites,
  each with a verdict (FOLLOW / ADAPT / REFERENCE / DEPRECATED), its strengths, and
  the date it was last verified. Generated from
  [references/sources.yaml](references/sources.yaml), which is the record of record.
- [references/VENDOR_RECIPE_NOTES.md](references/VENDOR_RECIPE_NOTES.md) — for each
  FOLLOW or ADAPT recipe: what it solves, what it does not, and what you have to
  validate yourself. Plus the standing deprecation watchlist.
- [references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md) — every
  formula, with its assumptions, its units, a worked example, and a note on when it
  breaks.

## Evidence and honesty

You should be able to tell, at a glance, how much weight any statement here can
carry. Three markers do that work.

Methodological statements carry an [A–H class](GLOSSARY.md#a-to-h-classification),
rendered as a callout badge, alongside an evidence-strength label. A procedure that
has been written down but never actually run carries
`status: doctrine — not yet exercised` — said plainly rather than quietly omitted.
And the illustrations in [examples/](examples/README.md) are invented scenarios: they
show the reasoning working, and a chapter that cites one still rests on its sources,
not on the scenario. Every generic chapter reads fine if you skip them.

## Version

`VERSION` = 0.1.1. What the version numbers mean here — and what 1.0 is gated on
(two materially different project instantiations carried through frozen executed
contracts) — is set out at the top of the [CHANGELOG](CHANGELOG.md).
