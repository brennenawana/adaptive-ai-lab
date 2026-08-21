# Pass-2 Authoring Conventions (build scaffolding — NOT part of the shipped playbook)

Binding for every file authored in this pass. Deviations are defects.
Authority chain: PASS2_AUTHORING_SPEC.md > PLAYBOOK_BUILD_PLAN.md > SOURCE_MAP_DRAFT.md.

## 1. Product identity

- Name: **Adaptive AI Systems Playbook**. Version: **0.1.0** (file `VERSION`).
- Location: `playbook/`. Self-contained: a reader with ONLY `playbook/` must be able
  to use everything. Links into `../docs/` are FORBIDDEN in shipped files (the only
  exception: nothing — even case studies must carry their evidence inline, citing
  internal-case source IDs, not repo paths).
- Audience: a competent engineer starting an AI system project, who does NOT know
  this repository. Client-shareable, potentially public prose. No secrets, no private
  paths, no proprietary assumptions.

## 2. File tree (authoritative)

```
playbook/
  README.md  QUICKSTART.md  GLOSSARY.md  VERSION  CHANGELOG.md
  00_PRINCIPLES_AND_SCOPE.md
  01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md
  02_EXECUTION_SYSTEM_MODEL.md
  03_EVALUATION_FOUNDATION.md
  04_EXPERIMENT_DESIGN_AND_STATISTICS.md
  05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md
  06_INFERENCE_PERFORMANCE_AND_CAPACITY.md
  07_OPTIMIZATION_AND_INTERVENTION_LADDER.md
  08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md
  09_TRAINING_AND_DATA.md
  10_DEPLOYMENT_AND_OPERATIONS.md
  11_ECONOMICS_HARDWARE_AND_CLOUD.md
  12_OBSERVABILITY_LEARNING_AND_PROMOTION.md
  13_GOVERNANCE_PROVENANCE_AND_SECURITY.md
  14_DECISION_TREES_AND_CHECKLISTS.md
  templates/PROJECT_PROFILE.md  templates/EXPERIMENT_CONTRACT.md
  templates/EVAL_SUITE_RELEASE_CONTRACT.md  templates/PERFORMANCE_AUTOPSY.md
  templates/TEST_LOOK_LEDGER.md  templates/COMPUTE_DEMAND_LEDGER.md
  templates/PREDICTION_LEDGER.md  templates/OPERATIONAL_HANDOFF.md
  templates/METHOD_DECISION_RECORD.md
  references/sources.yaml  references/SOURCES.md
  references/STATISTICS_FORMULAS.md  references/VENDOR_RECIPE_NOTES.md
  examples/README.md
  examples/CASE-001_consequence-bearing-tolerances.md
  examples/CASE-002_clustered-eval-effective-n.md
  examples/CASE-003_learned-router-leakage.md
  examples/CASE-004_harness-defects.md
  examples/CASE-005_hardware-purchase-discipline.md
  examples/CASE-006_token-budget-confounding.md
  examples/CASE-007_deterministic-cascade-gate.md
  examples/CASE-008_transport-serialization-defect.md
  examples/CASE-009_suite-versioning-criteria-drift.md
  examples/CASE-010_pilot-optimism-collapse.md
  examples/CASE-011_diagnostic-gate.md
  examples/CASE-012_restart-instability-paired-controls.md
  examples/WALKTHROUGH_rag-document-qa.md          (synthetic, non-FIS-shaped, full navigator pass)
  examples/SYNTH-01_api-only-assistant.md
  examples/SYNTH-02_private-local-deployment.md
  examples/SYNTH-03_high-throughput-extraction.md
  examples/SYNTH-04_tool-calling-agent.md
  examples/SYNTH-05_cost-reduction-routing.md
  examples/SYNTH-06_training-rejected.md
  examples/SYNTH-07_training-justified.md
  examples/SYNTH-08_high-stakes-audited-deployment.md
  examples/SYNTH-09_inconclusive-result.md
  examples/SYNTH-10_hardware-rent-vs-buy.md
  planning/   (scaffolding — never referenced by shipped files)
```

## 3. THE PORTABILITY BOUNDARY (hard rule)

Project-specific material may appear ONLY inside `examples/CASE-*.md` files (which
identify the source project — call it "the FIS project (Fintech Integration Sandbox),
a realistic synthetic fintech-operations laboratory" on first use — and preserve real
numbers). EVERYWHERE ELSE (README, QUICKSTART, GLOSSARY, chapters 00–14, templates/,
references/, SYNTH-*, WALKTHROUGH), the following are BANNED:

- The strings: FIS, Fintech Integration Sandbox, fintech (any casing).
- Experiment/milestone series names: R0–R9, E0–E8, E6b, M0, M-STAT, H0–H3, D0–D5,
  Suite v1/v2/v3/v4.
- Scenario-class IDs S01–S12; the 12-class ontology; case counts 288/144/48/96/36 as
  suite sizes; "12 classes".
- Model names from the project: Qwen (any variant), Nemotron, Bonsai, GPT-OSS.
- Project hardware identities: "RTX 5080 Laptop", and specific GPU model numbers
  (3090/4090/5090/5080, A6000, DGX Spark) — EXCEPT inside
  `references/VENDOR_RECIPE_NOTES.md` and chapter vendor-recipe callouts where a
  vendor product is itself the subject, and in clearly as-of-dated market-snapshot
  illustrations in chapter 11.
- Project-measured numbers as defaults: N_eff ≈ 22, ICC 0.475/0.398, 8–12% clock
  skew, 353–496 GB/s, 23/48 restart flips, 47/96, 93/96, 15/36, 9h55m, 24.1 h,
  8192/12288 as "the" caps, ~$150/mo trigger, 38 GPU-hours, $4 benchmark.
  Generic text states the PROCEDURE and links `[CASE: CASE-xxx]` for the measured
  instance. Neutral illustrations use invented round numbers clearly labeled
  "illustrative".
- Project infrastructure identities: port numbers (5433/4222/8082), NATS, database
  schema names (`learning.*`, `ground_truth`), repo paths, WSL2-as-our-machine
  (naming WSL2/virtualization as a *generic example* of a clock-validity hazard is
  allowed; its measured skew number is not), `--candidate`, `make reachability`
  (generalize to "an executable integrity-gate command").
- Superseded Pass-1 phrase "the FIS instance as one worked value" → replaced by:
  "one neutral illustrative value or synthetic worked example; project-specific
  empirical values stay in the case-study library."

Methodology vocabulary invented in the source project but defined generically in
GLOSSARY.md (execution system, consequence-bearing tolerance, certainty curtailment,
class-identity ceiling, reachability ceiling, look ledger, pass^k, SMOKE tier,
performance autopsy, prediction ledger, …) is the PRODUCT, not a leak — use freely.

## 4. Chapter skeleton (chapters 00–13; 14 and front matter exempt)

Every chapter uses exactly these H2 sections, in order. A section may be omitted only
by writing it with body "N/A — <reason>". Use `## N. <Title>` numbering.

1. Purpose and when to read this
2. Inputs required
3. Decisions this chapter supports
4. Normative principles
5. Default procedure
6. Project adaptation parameters
7. Decision gates and stopping conditions
8. Metrics and formulas
9. Failure modes and anti-patterns
10. Vendor recipes
11. Worked examples
12. Outputs and artifacts
13. Sources

Chapter header block (before section 1):

```markdown
# NN. <Chapter Title>

> Part of the **Adaptive AI Systems Playbook** v0.1.0 ·
> [← Previous](<prev file>) · [Index](README.md) · [Next →](<next file>)
> **Reading time:** ~N min. **Prerequisites:** <chapters or "none">.
```

Footer: repeat the nav line.

## 5. Callouts, labels, and language

Badges start a block, bold, bracketed:

- `**[PRINCIPLE]** (evidence: <strength>)` — A-class. Override requires a written,
  recorded reason (a METHOD_DECISION_RECORD).
- `**[DEFAULT]** (evidence: <strength>)` — B-class. State what to calibrate against.
- `**[PARAMETER]**` — C-class. State how to measure/choose it. Never ship a numeric
  value as if universal.
- `**[DECISION GATE]**` — a named go/no-go point; state inputs, rule, outcomes.
- `**[STOP CONDITION]**` — a tripwire; state trigger and required response.
- `**[FOLLOW: <SRC-ID>]**` — D-class vendor recipe, follow by the book; state scope +
  as-of date.
- `**[ADAPT: <SRC-ID>]**` — E-class; state exactly what is missing and what to
  substitute (details in references/VENDOR_RECIPE_NOTES.md).
- `**[REFERENCE: <SRC-ID>]**` — F-class pointer.
- `**[CASE: CASE-00N]**` — G-class link into examples/; numeric results stay there.
- `**[REJECTED]** (condition: <when this holds>)` — H-class; the condition is
  mandatory. H is reserved for generically-wrong practices.

Evidence strengths: `consensus` / `strong-evidence` / `heuristic` / `contested` /
`case-study` / `inference`.

Unexercised doctrine marker (verbatim, own line, italic):
`*status: doctrine — not yet exercised (see §<chapter ref> for what validation would look like)*`
— required on: judge-calibration protocol, shadow/canary process, harness-comparison
method, and any other procedure with no internal or cited external execution record.

RFC-2119 style: **MUST** (violating it invalidates the claim/decision), **SHOULD**
(default; deviation needs a recorded reason), **MAY** (genuinely optional). Use
deliberately and sparingly; do not decorate ordinary prose.

Citations: inline stable IDs in brackets `[EXT-STATS-001]`, human-readable only in
references/SOURCES.md. Every ID cited anywhere MUST exist in sources.yaml.

Links: relative within playbook/ (`[GLOSSARY](GLOSSARY.md)`,
`[CASE-002](examples/CASE-002_clustered-eval-effective-n.md)`,
`templates/EXPERIMENT_CONTRACT.md`). Glossary terms: link on first use per chapter
(`[execution system](GLOSSARY.md#execution-system)`); GLOSSARY anchors are
kebab-case of the term.

Format preferences: tables, numbered procedures, checklists, decision trees
(indented text trees or mermaid), worked calculations. Prose only where the *why*
carries decision weight. No marketing tone. No "simply"/"just".

## 6. The A–H taxonomy and extraction rules (recap — binding)

A principle · B default · C parameter · D vendor-FOLLOW · E vendor-ADAPT ·
F reference · G case lesson · H rejected.

1. Numbers do not travel; procedures travel.
2. A-class needs external corroboration or explicit first-principles support stated
   in place — never "the source project did it and it worked".
3. Single-project singletons cap at B.
4. Rejections carry conditions.
5. Vendor verdicts carry as-of dates + freshness.
6. Contradictions stay visible with a project-level decision rule (ch. 05 §
   runtime criterion; ch. 03 volume-vs-curation; ch. 09 LoRA regimes; ch. 07 vendor
   decision-page lag).
7. Evidence strength explicit on every PRINCIPLE/DEFAULT.
8. Unexercised doctrine labeled.
9. Inventory classifications are candidates; final call is made here.

## 7. Canonical failure taxonomy (owner decision 9 — THE single generic taxonomy)

Defined normatively in chapter 03 §5/§6 and GLOSSARY; used identically by 07 (ladder),
14 (trees), and templates. **Symptom ≠ diagnosis**: user-visible failure categories
are symptoms; every diagnosis lands in exactly one root-cause class below; every class
maps to its likely next interventions (the ladder rung).

| # | Root-cause class | One-line meaning | Primary intervention rung |
|---|---|---|---|
| RC-1 | Measurement/instrument defect | The eval, ground truth, or grader is wrong (unreachable required evidence, wrong gold, grader polarity, ceiling below threshold) | Rung 0 — fix the instrument; no other result is interpretable |
| RC-2 | Infrastructure/runtime defect | Serving stack, transport, configuration, or environment corrupts execution (serialization, nondeterminism, resource faults) | Rung 1 |
| RC-3 | Missing/unreachable evidence | Facts needed for the task are absent from context and unreachable via retrieval/tools | Rung 2 |
| RC-4 | Tool/API contract defect | Schema, addressing, ordering, or permission mismatch between system and tools | Rung 3 |
| RC-5 | Output/format enforcement gap | Correct content lost to parsing/structure/grammar failures | Rung 3 |
| RC-6 | Task-specification gap | The system was never told (instructions, decomposition, workflow, examples) | Rung 4 |
| RC-7 | Verification gap | The verifier/grader passes failures silently (silent failure) | Rung 4 |
| RC-8 | Capacity/budget exhaustion | Context window, reasoning/generation budget, or truncation bounds the outcome | Rung 5 |
| RC-9 | Routing/escalation mismatch | Work sent to the wrong tier, or escalation policy mis-set | Rung 6 |
| RC-10 | Capability gap — learnable | The model lacks task-specific skill/knowledge that demonstrably exists in obtainable training data | Rung 7 |
| RC-11 | Capability gap — fundamental | The model class cannot do it at any budget | Rung 8 |
| RC-12 | Architecture mismatch | The system topology is wrong for the task shape | Rung 9 |

The intervention ladder (normative order; ch. 00 short form, ch. 07 operational):

```
Rung 0  instrument integrity        (RC-1)   — always first; free-standing gate
Rung 1  infrastructure/runtime      (RC-2)
Rung 2  evidence/retrieval/context  (RC-3)
Rung 3  tool contracts & output enforcement (RC-4, RC-5)
Rung 4  specification & verification (prompt/workflow/verifier) (RC-6, RC-7)
Rung 5  generation/reasoning budget calibration (RC-8)
Rung 6  routing/escalation          (RC-9)
Rung 7  fine-tuning                 (RC-10)
Rung 8  larger/different model      (RC-11)
Rung 9  architectural redesign      (RC-12)
```

Descending a rung requires evidence the cheaper rungs are exhausted or inapplicable
(diagnosis, not impatience). Rungs 1–6 order MAY be locally re-sequenced when a
diagnosis clearly identifies the cause class; rung 0's priority and "never train
(rung 7+) around defects at rungs 0–4" are normative.

Historical note (for the internal evidence map only, never shipped text): the source
project's operating cause→action table is the measured ancestor; its Canonical
Architecture "discovery taxonomy" and MSI "failure taxonomy" map into RC-1…RC-12 —
mapping recorded in docs/research/PLAYBOOK_INTERNAL_EVIDENCE_MAP.md.

## 8. The rigor dial (owner decision 10)

Three stakes tiers, captured in PROJECT_PROFILE field "stakes / consequence
tolerance", used by QUICKSTART to scale mandatory artifacts. Defined normatively in
00 §(proportionality) + 01; enforced by templates.

**Floor (NEVER skippable, any tier):**
1. State the decision the work drives and the claim to be evidenced.
2. Preserve enough execution-system/artifact provenance to identify what produced
   any result you might act on.
3. Define the evaluation/ground-truth boundary before making a quality claim.
4. Predeclare consequences for decision-driving thresholds/tolerances.
5. Treat held-out evidence as consumable; record exposure.
6. Retain outcome evidence (raw outputs or equivalent).

| Tier | Name | Signature | Adds on top of floor |
|---|---|---|---|
| Tier 1 | Exploratory | internal, reversible, low blast radius | lightweight profile; pinned notes-grade provenance; smoke-scale evals allowed for direction (never for adoption claims) |
| Tier 2 | Consequential (default) | business decisions, customer-visible behavior | frozen experiment contracts; versioned suites + integrity gates; MDE/effective-N statements + INCONCLUSIVE; look ledger; prediction ledger; demand ledger before purchases |
| Tier 3 | High-stakes / regulated | safety, money movement, compliance, audit | tamper-evident provenance (hash-chained record of record); security/threat-model review; pass^k reliability claims; judge calibration where judges used; shadow→canary with human approval; rollback runbook; periodic methodology audit |

Rule of proportion: rigor attaches to the DECISION's consequence, not the project's
prestige. A Tier-1 project making a Tier-3 decision (e.g., "ship to production")
escalates that decision to the higher tier's artifact set.

## 9. Statistics canon (chapter 04 + STATISTICS_FORMULAS must agree)

- Clustered outcomes: identify clustering unit → estimate ICC → DEFF = 1+(m−1)·ICC →
  N_eff = N/DEFF → MDE at α=.05, power .80. Cluster-robust paired inference primary
  (t on per-cluster means, df = clusters−1) when clustering is material; McNemar
  exact secondary, labeled anti-conservative under clustering.
- MDE ≤ discordance constraint; report MDE in every contract; INCONCLUSIVE below MDE
  (never "equivalent"). Pre-registered descriptive vocabulary is the licensed
  alternative.
- Paired designs whenever same-items cross-arm; paired SEs, not two-sample.
- Screening ≠ inference. Racing/successive-halving on iterate-split only,
  stratum-balanced rungs; ranks, never inference claims.
- Stopping: consequence-bearing tolerances evaluated by curtailed exact counting
  (halt at violation k+1) — no hypothesis test; certainty curtailment
  (passes + remaining < ⌈bar·N⌉) with three guards (spend semantics, interval-only
  reporting, paired-comparison firewall). Stopping rules exist for decision quality;
  a speed rationale for a stopping rule is an anti-pattern (H-class).
- Sequential tests calibrated i.i.d. (SPRT et al.) are **[REJECTED]** *conditional*:
  inadmissible when outcomes cluster within ordered groups (α inflates); admissible
  only after an explicit independence check of the execution order.
- pass^k for reliability claims about stochastic systems; pass@k ≠ pass^k.
- Prediction ledger: pre-run estimate + interval per primary metric, scored after.

## 10. Source ID scheme

Existing seeds (playbook/planning/external_sources_*.json) keep their IDs
(NV-*, EXT-*). New internal-case sources: `INT-CASE-00N` matching CASE files.
New sources invented during authoring: `<ORG>-<TOPIC>-NNN` style, never renumber.
sources.yaml is the record of record; SOURCES.md is generated (script:
references/tools/render_sources.py) — never hand-edit SOURCES.md.

## 11. Voice and honesty rules

- Thin subjects say so: 01 labels navigator methodology `(inference)` where it is
  playbook synthesis; 09 states plainly that the playbook's maintainers have not yet
  exercised training internally (doctrine assembled from literature + vendor
  mechanics); 10 distinguishes established SRE practice (consensus) from AI-specific
  doctrine (inference/doctrine-not-exercised).
- Never imply validation that does not exist. Never soften a rejection into vagueness
  — state its condition.
- Contradiction sections present both sides + the decision rule; they never pick a
  silent winner.
- Every formula: define symbols, give units, one neutral worked example with round
  invented numbers.
