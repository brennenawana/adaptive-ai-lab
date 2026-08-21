# Adaptive AI Systems Playbook

**Version 0.1.0** · [Changelog](CHANGELOG.md) · [Glossary](GLOSSARY.md) ·
[Quickstart](QUICKSTART.md)

An evidence-driven, project-independent engineering playbook for building AI
systems: from requirements and constraints through evaluation, model/runtime
selection, experimentation, optimization, training decisions, serving, economics,
deployment, observability, and continuous improvement.

It exists to answer, for a concrete project: **what should I do next, why, what
evidence do I need, what should I measure, what can I skip, what should force me to
stop or change direction, and when is an expensive intervention justified?**

## Who this is for

An engineer or small team arriving with: a product or problem, candidate models,
some owned or rentable compute, cloud/API providers, a budget, latency and quality
constraints, data/privacy restrictions, and limited staffing — who needs a
defensible path rather than a pile of vendor tutorials. Vendor material tells you
how to *execute* each stage; the decision layer — stop, promote, select, buy,
trust — is what this playbook supplies, with every rule carrying its evidence and
its [strength label](GLOSSARY.md#evidence-strength-labels).

Everything here is self-contained: no external project context, no private
infrastructure, no proprietary assumptions. Real empirical evidence appears as
[case studies](examples/README.md); one source project's numbers never appear as
your defaults.

## 15-minute start

1. Read [00 — Principles and Scope](00_PRINCIPLES_AND_SCOPE.md) §4 (the twelve
   principles) and §6 (the rigor dial). *(~7 min)*
2. Open [QUICKSTART](QUICKSTART.md); fill
   [templates/PROJECT_PROFILE.md](templates/PROJECT_PROFILE.md). *(~10 min)*
3. Take the archetype route it gives you — it names your first three actions and
   the chapters you may skip for now.

Your first sprint ends at a frozen
[experiment contract](templates/EXPERIMENT_CONTRACT.md) (Tier 2+) or a written
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

| # | Chapter | One line |
|---|---|---|
| 00 | [Principles and Scope](00_PRINCIPLES_AND_SCOPE.md) | The normative core; the intervention ladder; the rigor dial |
| 01 | [Project Intake and Decision Context](01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) | Fuzzy request → profile → decision context → first actions |
| 02 | [Execution System Model](02_EXECUTION_SYSTEM_MODEL.md) | What "the same system" means; measured reproducibility boundaries |
| 03 | [Evaluation Foundation](03_EVALUATION_FOUNDATION.md) | Requirement → trusted, versioned eval; the canonical failure taxonomy; graders and judges |
| 04 | [Experiment Design and Statistics](04_EXPERIMENT_DESIGN_AND_STATISTICS.md) | Contracts, looks, tolerances with consequences, clustering, MDE, INCONCLUSIVE |
| 05 | [Model, Runtime, and Harness Selection](05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md) | Bounded candidate sets; runtime regimes, not runtime winners |
| 06 | [Inference Performance and Capacity](06_INFERENCE_PERFORMANCE_AND_CAPACITY.md) | The one FOLLOW-grade vendor methodology, plus what vendors omit |
| 07 | [Optimization and the Intervention Ladder](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) | You have a measured gap — select the intervention; diagnostic gates first |
| 08 | [Retrieval, Tools, Workflows, and Routing](08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) | Evidence reachability, tool contracts, cascades, the learned-router admission bar |
| 09 | [Training and Data](09_TRAINING_AND_DATA.md) | The last rung: evidence bar, legality, rig-first, forgetting gates |
| 10 | [Deployment and Operations](10_DEPLOYMENT_AND_OPERATIONS.md) | Shadow/canary with restraint; rollback as a designed path |
| 11 | [Economics, Hardware, and Cloud](11_ECONOMICS_HARDWARE_AND_CLOUD.md) | Rent vs buy vs API as a measured decision; demand ledgers and triggers |
| 12 | [Observability, Learning, and Promotion](12_OBSERVABILITY_LEARNING_AND_PROMOTION.md) | The experimentation telemetry floor; harvesting production back into the lab |
| 13 | [Governance, Provenance, and Security](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md) | The record of record; what must never be reachable; legality |
| 14 | [Decision Trees and Checklists](14_DECISION_TREES_AND_CHECKLISTS.md) | Every gate and checklist from 00–13, condensed and cross-referenced |

Reading contracts: **02 before any cross-run comparison**; **04 gates every
selection/intervention experiment**; **11 is consulted three times** (intake,
capacity, deployment), not read once; **13 is instantiated at intake** for Tier-3
work; **12 closes the loop back to 03**.

## "I need to…"

| I need to… | Go to |
|---|---|
| know what to do first on a new project | [QUICKSTART](QUICKSTART.md) |
| decide if I can trust my eval | [03](03_EVALUATION_FOUNDATION.md) §instrument validation; [templates/EVAL_SUITE_RELEASE_CONTRACT.md](templates/EVAL_SUITE_RELEASE_CONTRACT.md) |
| compare two models/configs defensibly | [04](04_EXPERIMENT_DESIGN_AND_STATISTICS.md); [templates/EXPERIMENT_CONTRACT.md](templates/EXPERIMENT_CONTRACT.md) |
| understand why my numbers moved between runs | [02](02_EXECUTION_SYSTEM_MODEL.md) |
| fix an underperforming system | [07](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) (diagnose first: [03](03_EVALUATION_FOUNDATION.md) §taxonomy) |
| decide whether to fine-tune | [07](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) §evidence bar → [09](09_TRAINING_AND_DATA.md) |
| cut API costs with routing | [08](08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) + [11](11_ECONOMICS_HARDWARE_AND_CLOUD.md) §break-even |
| decide whether to buy hardware | [11](11_ECONOMICS_HARDWARE_AND_CLOUD.md); [templates/COMPUTE_DEMAND_LEDGER.md](templates/COMPUTE_DEMAND_LEDGER.md) |
| benchmark serving performance | [06](06_INFERENCE_PERFORMANCE_AND_CAPACITY.md) |
| grade open-ended outputs with a judge | [03](03_EVALUATION_FOUNDATION.md) §judge calibration |
| ship to production safely | [10](10_DEPLOYMENT_AND_OPERATIONS.md); gates in [14](14_DECISION_TREES_AND_CHECKLISTS.md) |
| set up telemetry before a long run | [12](12_OBSERVABILITY_LEARNING_AND_PROMOTION.md) §telemetry floor |
| prove my results to an auditor | [13](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md) |
| find a formula | [references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md) |
| check whether a vendor recipe is still current | [references/SOURCES.md](references/SOURCES.md) + [references/VENDOR_RECIPE_NOTES.md](references/VENDOR_RECIPE_NOTES.md) |

## Project-type reading paths

Six archetypes, routed by profile facts in [QUICKSTART](QUICKSTART.md): greenfield
API-only (A), local/private mandate (B), existing system underperforming (C), cost
reduction (D), high-stakes/compliance (E), lab bootstrap (F) — each with entry
chapters, skippable chapters, mandatory templates, and first three actions.
Worked passes: [examples/WALKTHROUGH_rag-document-qa.md](examples/WALKTHROUGH_rag-document-qa.md)
(full), [examples/SYNTH-01…10](examples/README.md) (compact, one per shape).

## Templates

Nine, in [templates/](templates/): [PROJECT_PROFILE](templates/PROJECT_PROFILE.md) ·
[EXPERIMENT_CONTRACT](templates/EXPERIMENT_CONTRACT.md) ·
[EVAL_SUITE_RELEASE_CONTRACT](templates/EVAL_SUITE_RELEASE_CONTRACT.md) ·
[PERFORMANCE_AUTOPSY](templates/PERFORMANCE_AUTOPSY.md) ·
[TEST_LOOK_LEDGER](templates/TEST_LOOK_LEDGER.md) ·
[COMPUTE_DEMAND_LEDGER](templates/COMPUTE_DEMAND_LEDGER.md) ·
[PREDICTION_LEDGER](templates/PREDICTION_LEDGER.md) ·
[OPERATIONAL_HANDOFF](templates/OPERATIONAL_HANDOFF.md) ·
[METHOD_DECISION_RECORD](templates/METHOD_DECISION_RECORD.md).
Each: purpose, when to use, required sections ("delete no section — write N/A +
reason"), and a filled miniature example. The three ledgers are the least obvious
and most portable: adopt them even if you adopt nothing else.

## Vendor recipes and references

- [references/SOURCES.md](references/SOURCES.md) — every source this playbook
  cites, with verdicts (FOLLOW / ADAPT / REFERENCE / DEPRECATED), strengths, and
  verification dates. Generated from
  [references/sources.yaml](references/sources.yaml), the record of record.
- [references/VENDOR_RECIPE_NOTES.md](references/VENDOR_RECIPE_NOTES.md) — what
  each FOLLOW/ADAPT recipe solves, what it doesn't, and what you must validate;
  plus the standing deprecation watchlist.
- [references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md) — every
  formula with assumptions, units, a worked example, and "when this breaks".

## Evidence and honesty

Methodological statements carry [A–H classes](GLOSSARY.md#a-to-h-classification)
rendered as callout badges, plus evidence-strength labels. Procedures without an
execution record carry `status: doctrine — not yet exercised`. Real project
evidence lives in [examples/](examples/README.md) as CASE studies (where the
source project is identified and its numbers are preserved); generic chapters link
to cases and remain readable without them.

## Version

`VERSION` = 0.1.0. Semver interpretation and the 1.0 gate (two materially
different project instantiations through frozen executed contracts) are defined in
the [CHANGELOG](CHANGELOG.md) header.
