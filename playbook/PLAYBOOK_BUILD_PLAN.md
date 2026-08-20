# Playbook Build Plan

> STATUS: PLANNING ARTIFACT — this pass designs the playbook; it does not write it.
> Date: 2026-08-20
> Owner review required before the authoring pass begins (§14).
> Companion: `SOURCE_MAP_DRAFT.md` (evidence → chapter mapping, classifications).

## 0. What is being built

A reusable, project-independent AI systems engineering playbook — the end-to-end,
evidence-driven guide an infrastructure vendor never published: from requirements and
constraints through evaluation, model/runtime selection, experimentation,
optimization, training decisions, serving, economics, deployment, observability, and
continuous improvement. It is the entry point to future projects.

It is extracted from, but not about, this repository. FIS (the Fintech Integration
Sandbox) is **evidence and case-study material**; the playbook must be fully
understandable with `docs/current/` deleted.

The target user arrives with: a concrete product/problem, candidate models, owned
hardware, cloud/API providers, a budget, latency/throughput constraints, data/privacy
restrictions, quality/reliability requirements, expected traffic, available eval
data, a deployment environment, and staffing constraints — and uses the playbook to
derive a defensible path: *what to do next, why, what evidence is needed, what to
measure, what to skip, what should force a stop or change of direction, and when an
expensive intervention is justified.*

---

## 1. Proposed final tree

```
playbook/
  README.md                     what this is, who it is for, how to use it, map of the book
  QUICKSTART.md                 the project navigator: profile → archetype → reading path → first actions
  GLOSSARY.md                   canonical terminology (one home; chapters link, never redefine)
  VERSION                       single version string (see §8)
  CHANGELOG.md                  what changed + WHY + the evidence that forced it

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

  templates/
    PROJECT_PROFILE.md          intake questionnaire → the navigator's input (chapter 01)
    EXPERIMENT_CONTRACT.md      generalized v2 contract (de-FIS'd; consequence clauses, MDE, prediction)
    EVAL_SUITE_RELEASE_CONTRACT.md   versioned suite release (ceilings, gates, cross-suite refusal)
    PERFORMANCE_AUTOPSY.md      post-run forensic template (critical path, counterfactuals, clock validity)
    TEST_LOOK_LEDGER.md         held-out-set exposure ledger + refresh trigger
    COMPUTE_DEMAND_LEDGER.md    GPU/API-hours demand instrument + pre-committed purchase trigger
    PREDICTION_LEDGER.md        pre-run effect estimates vs actuals
    OPERATIONAL_HANDOFF.md      operational state document (what runs where, gotchas, verification commands)
    METHOD_DECISION_RECORD.md   ADR-style record for methodology adoptions/rejections (feeds CHANGELOG)

  references/
    sources.yaml                THE source ledger (record of record; stable IDs; see §7)
    SOURCES.md                  human-readable view generated from sources.yaml
    STATISTICS_FORMULAS.md      derivations + worked calculations (MDE, ICC/DEFF/N_eff, curtailment
                                arithmetic, pass^k, break-even, rent-vs-buy H*)
    VENDOR_RECIPE_NOTES.md      per-recipe adaptation notes & version pins for FOLLOW/ADAPT sources

  examples/
    fis-cap-burn-consequence-tolerances.md     detection ≠ decision; pricing a tolerance breach
    fis-cluster-neff-collapse.md               clustering silently destroys power; measure ICC first
    fis-learned-router-leakage.md              class-identity ceiling; leakage audits for learned parts
    fis-deterministic-cascade-gate.md          rule-based escalation vs the learned-gate literature
    fis-harness-defects-instrument-validation.md  13 defects; ceilings/inversions/disagreement as instruments
    fis-transport-serialization-defect.md      "transparent" proxy reordered JSON keys; verify byte equivalence
    fis-hardware-buy-nothing.md                measured critical path vs intuition; trigger-based purchase
    fis-suite-versioning.md                    criteria drift managed by versioned releases
    fis-pilot-optimism-collapse.md             n=12 → n=96: small-sample headlines run optimistic
    fis-token-cap-confound.md                  an "80% better" model claim shrank to 24% when the cap was isolated
    fis-diagnostic-gate.md                     a ~$4 paired-probe diagnostic decides an 18–22h experiment's fate
    fis-restart-instability-paired-controls.md measure your reproducibility boundary; then pair your controls
    walkthrough-synthetic-project.md           one full navigator pass on a NON-FIS-shaped project (labeled synthetic)

  planning/                     BUILD SCAFFOLDING — not part of the shipped playbook;
    evidence_inventory.json     removed (or archived) at repo extraction. Holds this
                                pass's classified statement inventory (≈450 statements,
                                ~38 case-study candidates, 60-item anti-pattern catalog,
                                external-source rows) for the authoring agents.
```

Changes vs the tentative architecture, with the case for each:

1. **Chapter list and numbering kept** (00–14). The proposed spine is sound:
   lifecycle-ordered, evaluation before experimentation, economics and governance
   first-class. Stability against the owner's draft is a feature; changes below are
   re-scopings, not reshuffles.
2. **07 re-scoped, not renamed.** The intervention ladder (infrastructure →
   evidence/retrieval → prompt/workflow → routing → training → bigger model) is the
   playbook's central decision spine, not one chapter's content. Its short normative
   statement lives in 00; **07 is the operational hinge**: "you have a measured gap —
   select the intervention," covering diagnostic-first gating (the M0 pattern),
   budget/cap calibration, prompt/workflow iteration, quantization with acceptance
   gates, and the evidence bar for moving down a rung. 08 and 09 are deep dives of
   rungs 4 and 5. Without this re-scope, 07 conflates the decision hierarchy with
   quantization mechanics.
3. **GLOSSARY.md added.** The methodology's power is partly its vocabulary (execution
   system, look, spend semantics, curtailment, consequence-bearing tolerance, N_eff,
   reachability ceiling, silent failure). Terms must be defined once and linked, or
   fifteen chapters will drift.
4. **references/ is structured**, not a link dump: a machine-readable source ledger
   (§7), a statistics formulary (04 stays readable; derivations move here), and
   vendor-recipe adaptation notes (the ADAPT classification needs a place to say
   *what* to adapt).
5. **examples/ is a case-study library with a fixed format** (§9), not loose prose.
   Every FIS number the generic chapters must quarantine gets its narrative home here.
6. **templates/ carries the ledgers** (test-look, compute-demand, prediction) as
   first-class templates. These are among the most portable and least obvious
   artifacts the lab invented; a user who adopts nothing else should be able to adopt
   these.

## 2. Purpose of every chapter file

| File | Purpose | Decisions it supports |
|---|---|---|
| `00_PRINCIPLES_AND_SCOPE.md` | The normative core: evaluate-first; evidence before intervention; the ladder (short form); decision-quality over speed; frozen instruments; pre-registration; fail-closed enforcement; INCONCLUSIVE as a legitimate verdict; what this playbook is not (no vendor marketing, no benchmark worship) | Whether this playbook fits your project at all; the non-negotiables |
| `01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md` | Turn a fuzzy request into a PROJECT_PROFILE: the decision each piece of evidence will drive; constraints inventory (privacy, latency, budget, traffic, staffing); requirement → evaluation claim formulation; project archetype selection | What kind of project this is; which chapters/templates apply; the first three actions |
| `02_EXECUTION_SYSTEM_MODEL.md` | The measurement-validity foundation: an "execution system" = model artifact + runtime build + config + host, pinned as one identity; reproducibility boundaries are *measured, then scoped* (restart probes, session rules); comparability claims never cross an unmeasured boundary; cross-node/rented placement rules; quantize for the deployment target | What counts as "the same system"; when two numbers may be compared; when a change requires a new frozen identity |
| `03_EVALUATION_FOUNDATION.md` | Requirement → task ontology → stratified scenario corpus → ground-truth design → instrument validation (reachability ceilings, gold-answer gates, saturation checks) → versioned suite release with cross-suite refusal → leakage protection (split isolation, canaries) → grader choice (deterministic vs calibrated judge) | Whether your eval can be trusted; suite size/shape; grader type; when to refresh the suite |
| `04_EXPERIMENT_DESIGN_AND_STATISTICS.md` | Splits and look discipline; experiment contracts (pre-registration, freeze, amendment logs); consequence-bearing tolerances; screening vs inference; elimination rules; curtailment with guards; clustering, ICC → DEFF → N_eff → MDE; paired designs; pass^k; prediction ledger; verdict vocabulary | Whether an experiment is worth running; when to stop; what a result may claim |
| `05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md` | Design-time selection (the gap no vendor fills): shortlisting against the profile; screening protocols; runtime/engine choice by measured fit; agent-harness selection and evaluation (largely designed-not-validated — labeled as such); when selection is premature vs overdue | Which candidates enter experiments; which runtime serves; which harness executes |
| `06_INFERENCE_PERFORMANCE_AND_CAPACITY.md` | The measurement methodology (vendor-mature: metric definitions, sweeps, operating points — FOLLOW), plus what vendors omit: single-user regimes, clock validity, dual-clock telemetry, effective-bandwidth accounting, capacity fit probes, and the **performance autopsy** as a standing post-run procedure | Operating point; capacity plan; whether performance explains an experimental cost; what a run actually spent |
| `07_OPTIMIZATION_AND_INTERVENTION_LADDER.md` | The operational ladder: diagnostic gates before expensive interventions (cheap paired probes that decide a big experiment's fate); token/reasoning-budget calibration as a procedure; prompt/workflow optimization discipline; quantization with acceptance gates and escalation ladders; the evidence bar for each rung | Which intervention to try next; when an expensive intervention is justified; when to stop optimizing |
| `08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md` | Context/retrieval/tool-contract engineering; multi-tier routing and cascades; deterministic verifier gates vs learned routers; the leakage-audit bar any learned component must pass; routing economics (break-even); escalation semantics | Cascade topology; gate type; whether a learned router is admissible; what escalation costs |
| `09_TRAINING_AND_DATA.md` | The last rung: rig-first (de-risk the pipeline before the model); data provenance and ToS/licensing constraints; own-trace harvesting; minimum-n as an ablation, not folklore; LoRA/QLoRA defaults; full-suite forgetting gates; post-tune evaluation | Whether to train at all; data legality; training design; acceptance |
| `10_DEPLOYMENT_AND_OPERATIONS.md` | Promotion to production: shadow/canary with restraint (small causal metric set, one canary at a time); rollback as a designed path; serving stack choice; progressive-delivery patterns where vendors stop at mechanics | Ship/no-ship; rollout shape; rollback criteria |
| `11_ECONOMICS_HARDWARE_AND_CLOUD.md` | Local vs cloud vs API as a measured decision: demand ledgers before capital; break-even formulas with honest utilization; trigger-based purchasing; price-volatility discipline (re-verify at order time); renting parallel capacity per-milestone; TCO framing for small labs (the gap vendor TCO ignores) | Buy/rent/API; when a purchase trigger is allowed to fire; what a milestone should cost |
| `12_OBSERVABILITY_LEARNING_AND_PROMOTION.md` | The experimentation telemetry floor (vendors document production, not experimentation): run lifecycle events, per-invocation stats, clock validity, resource samplers; production failure harvesting back into evals/training data; the continuous-improvement loop; periodic self-audits (ML-Test-Score-style) | What must be instrumented before a long run; how production feeds the lab |
| `13_GOVERNANCE_PROVENANCE_AND_SECURITY.md` | Tamper-evident provenance (hash-chained registries, frozen contracts, append-only records); fail-closed runners; ground-truth isolation (answer keys unreachable from model-facing surfaces); clean-room boundaries; legal/ToS constraints on data and outputs; publication hygiene (canaries) | What the record of record is; what must never be executable/reachable; what is legal to train on |
| `14_DECISION_TREES_AND_CHECKLISTS.md` | The operational condensation: every gate, tree, and checklist from 00–13 in one place, cross-referenced; printed-page usable | Fast recall during execution; contract freeze checklists; go/no-go trees |

## 3. Consistent chapter design

Every chapter (00–13) uses the same skeleton. 14 and the front-matter files are exempt.

1. **Purpose / when to read this**
2. **Inputs required** (from PROJECT_PROFILE or earlier chapters' outputs)
3. **Decisions this chapter supports**
4. **Normative principles** `[PRINCIPLE]`
5. **Recommended default procedure** `[DEFAULT]`
6. **Project adaptation parameters** `[PARAMETER]` — a table: parameter, how to
   measure/choose it, the FIS instance as one worked value (linked, never inlined as
   a default)
7. **Decision gates / stopping conditions**
8. **Metrics and formulas** (statements here; derivations in `references/STATISTICS_FORMULAS.md`)
9. **Failure modes / anti-patterns** `[REJECTED]` items live here with their conditions
10. **Vendor recipes** `[FOLLOW …]` / `[ADAPT …]` callouts with source IDs
11. **Worked examples** — links into `examples/`, one line each on what it shows
12. **Outputs / artifacts produced** (which templates this chapter instantiates)
13. **Sources** — source-ledger IDs used, with one-line roles

Rules: a section may be omitted only as "N/A — <reason>" (absence is a decision, not
an omission — the contract-template discipline applied to the book itself). Chapters
target operational use: tables and procedures over essay; prose only where the
*why* carries decision weight.

## 4. Chapter dependency / navigation graph

```
                    ┌──────────────────────────────────────────────┐
                    │ 00 principles ── read once, binds everything │
                    └──────────────────────────────────────────────┘
  ENTRY: QUICKSTART → 01 intake ─┬─→ 03 evaluation ──→ 04 experiments/stats ─┐
                                 │        ▲                       ▲          │
                                 │        └── 02 execution-system ┘          │
                                 │        (measurement validity: read before │
                                 │         trusting any number)              │
                                 │                                           ▼
                                 │                          05 selection ⇄ 06 performance
                                 │                                           │
                                 │                                           ▼
                                 │                          07 intervention ladder
                                 │                             ├─→ 08 retrieval/tools/routing
                                 │                             └─→ 09 training & data
                                 │                                           │
                                 └───────────── 11 economics ◄───────────────┤
                                     (consulted at 01, 05/06, 10)            ▼
                                                            10 deployment → 12 observability/learning
                                                                                   │ (loop back to 03:
                                                                                   ▼  harvested failures)
                                                            13 governance ── underpins all; instantiated at 01
                                                            14 trees/checklists ── generated from all
```

Reading contracts the graph implies:
- **02 → before any cross-run comparison.** 03/04 explicitly require 02's outputs.
- **04 gates 05–09**: no selection/intervention experiment without a contract.
- **11 is consulted, not sequenced** — budget questions arise at intake, at capacity
  planning, and at deployment; the chapter is written to be entered three times.
- **12 closes the loop to 03**: harvested production failures become eval candidates
  (suite refresh triggers), then training data candidates (09), in ladder order.
- **13 is instantiated at intake** (provenance from day one), then referenced.

## 5. Generic-vs-project extraction rules

The core discipline of the authoring pass. Every methodological statement carried
into the playbook is classified (A–H, per the planning taxonomy) and rendered under
these rules:

1. **Numbers never travel; procedures travel.** No FIS numeral (12 classes, 36/48/96,
   N_eff≈22, 8192/12288 caps, $150/mo, GPU model conclusions, WSL2 clock behavior)
   appears in a generic chapter except inside a `[CASE]` callout or as one worked
   value in a parameter table, linked to `examples/`.
2. **A-class (normative) requires** external corroboration (consensus or
   strong-evidence literature) **or** a first-principles argument stated in the
   chapter — never "FIS did it and it worked."
3. **Single-project singletons cap at B (default/heuristic)** until instantiated on a
   materially different project. The CHANGELOG promotes B→A with the evidence named.
4. **Rejections carry their conditions, not their verdicts.** FIS's rejections were
   evidence-conditional: SPRT was dominated *under measured class clustering on
   class-blocked ordering*; a parallel relaxed tier was rejected *because it punches a
   hole in fail-closed provenance*; hardware purchase was rejected *at measured
   demand ≈ 38 lifetime GPU-hours mid price-bubble*. The generic playbook states the
   conditional rule ("if your per-item outcomes cluster, sequential tests calibrated
   i.i.d. inflate α — check ICC first"), and reserves H-class for things that are
   wrong *generically* (e.g., unpriced tolerance escape hatches; speed rationales for
   stopping rules; judges on verifiable tasks without calibration; promoting sub-MDE
   margins to decisions).
5. **Vendor verdicts (FOLLOW/ADAPT/REFERENCE/DEPRECATED) carry as-of dates** and a
   freshness sensitivity; every FOLLOW/ADAPT source gets live re-verification in the
   authoring pass (workstream W1) before its verdict is printed.
6. **Contradictions stay visible.** Where credible sources disagree (volume-vs-
   curation in eval construction; LoRA-vs-full-FT quality regimes), the playbook
   presents the tension and a decision rule for choosing per project — it never
   silently resolves.
7. **Evidence-strength labels** (consensus / strong-evidence / heuristic / contested /
   case-study / inference) attach to every principle and default. A recent paper is
   never rendered as law.
8. **Designed-but-unexercised methodology is labeled.** Doctrine FIS wrote but never
   ran (shadow/canary process, harness-comparison science, judge calibration
   protocol) enters chapters with an explicit `status: doctrine — not yet exercised`
   marker, so the playbook never claims validation it doesn't have.
9. **The raw inventory's classifications are candidates, not verdicts.** The
   evidence-inventory agents assigned A-class generously (263 of 395 statements in
   the first seven document sets); rules 2–3 govern final assignment during
   authoring, and the expected outcome is that a large share of inventory-A items
   land as B (defaults) with their FIS validation cited as case-study evidence.

### The biggest boundary decisions (for owner review)

| # | Question | Proposed resolution |
|---|---|---|
| B1 | **Deterministic grading**: FIS-vindicated, but only for objectively-verifiable tasks | A-class *scoped to verifiable-output domains*; the judge branch (calibration protocol: κ-corrected, bias-audited, human-anchored) must be written as a real procedure even though FIS never exercised it — most client projects will need it. Gap workstream W8. |
| B2 | **Same-session / frozen execution system**: is session-scoped comparability generic? | The *procedure* is generic (measure your reproducibility boundary with restart/concurrency probes, then scope claims to it); the session-scoped *conclusion* is FIS's measured instance. Chapter 02 teaches the probe, not the boundary. |
| B3 | **Cluster-robust statistics**: primary inference generically, or FIS-specific? | Generic A-class *procedure*: identify the clustering unit; measure ICC; report N_eff and MDE before freezing; INCONCLUSIVE below MDE. Which test is primary is B-class (depends on structure). N_eff≈22 is the cautionary case study. |
| B4 | **The intervention ladder**: normative everywhere? | A-class with documented-override provision (00). The *order* is defended by external evidence + two FIS enforcement episodes; specific rung procedures are B. |
| B5 | **Consequence-bearing tolerances**: portable as-is? | Yes — A-class, the single most portable invention in the record. Every pre-registered tolerance names ABORT / RECALIBRATE / PROCEED-WITH-DECLARED-CEILING + projected cost, enforced fail-closed. |
| B6 | **One-look splits + look ledger**: generic? | Principle A (held-out data is a consumable resource; exposure is ledgered; refresh is triggered); sizes/split names C. |
| B7 | **Two-plane architecture, five memory types, event-driven requirement** | F-class reference architecture (one strong worked pattern), *not* normative. A client system can comply with the methodology without this topology. |
| B8 | **Hardware policy** | Trigger-based purchase + demand ledger + break-even = B-class defaults; every price/threshold C-class snapshot with re-verify-at-order-time rule. |
| B9 | **SMOKE-as-registry-state** | A-class principle in the general form: *cheap tiers must live inside the fail-closed machinery and be non-promotable*; 36-case composition is C. |
| B10 | **Fintech/task ontology** | The 12-class ontology is C/G; the *procedure* (root-cause taxonomy → cause→action table → stratified classes → per-class ceilings) is the generic content of 03. |

## 6. Terminology / callout system

Defined once in `GLOSSARY.md`; used identically in every chapter:

**Inline callout badges** (start of a block):
- `[PRINCIPLE]` — A-class; override requires a written, ledgered reason.
- `[DEFAULT]` — B-class; calibrate before relying on it; the block states *what to
  calibrate against*.
- `[PARAMETER]` — C-class; the block states how to measure/choose it.
- `[FOLLOW: <SRC-ID>]` — D-class vendor recipe; follow the cited procedure by the
  book; the callout states scope and as-of date.
- `[ADAPT: <SRC-ID>]` — E-class; the callout states exactly what is missing and what
  to substitute (details in `references/VENDOR_RECIPE_NOTES.md`).
- `[REFERENCE: <SRC-ID>]` — F-class pointer.
- `[CASE: <example-id>]` — G-class; links into `examples/`; numeric results stay there.
- `[REJECTED]` — H-class; states the *condition* under which the rejection holds (§5.4).

**Evidence-strength suffix** on `[PRINCIPLE]`/`[DEFAULT]`: `(consensus)`,
`(strong-evidence)`, `(heuristic)`, `(contested)`, `(case-study)`, `(inference)`.

**Status marker** for unexercised doctrine: `status: doctrine — not yet exercised`.

Glossary seed list (canonical definitions): execution system · frozen identity ·
look / spend semantics · consequence-bearing tolerance · curtailed exact counting ·
certainty curtailment · reachability ceiling · silent failure · gross gate vs fine
ranking · ICC / DEFF / effective N / MDE · INCONCLUSIVE · screening vs inference ·
intervention ladder · diagnostic gate · cascade / escalation / rescue · leakage audit
/ class-identity ceiling · pass^k · demand ledger · purchase trigger · fail-closed ·
record of record · canary string · clean-room boundary · performance autopsy.

## 7. Source / citation design

**Record of record:** `references/sources.yaml` — one entry per stable source ID.
`references/SOURCES.md` is generated from it (script or by hand each release; never
edited directly). Chapters cite IDs inline (`[NV-BENCH-001]`); human-readable links
live only in SOURCES.md, so link maintenance is centralized.

```yaml
- id: NV-BENCH-001            # ORG-TOPIC-NNN; never reused, never renumbered
  org: NVIDIA
  title: NIM for LLMs Benchmarking Guide
  url: https://docs.nvidia.com/nim/benchmarking/llm/latest/index.html
  type: official-docs          # official-docs|official-blog|official-repo|paper|third-party|partner|standard|internal-case
  pub_date: 2026-07-20         # publication or last-update as known
  last_verified: 2026-08-19    # last live fetch that confirmed the claim we cite it for
  tool_version: AIPerf-era     # where applicable
  maturity: mature             # mature|current|new|pre-alpha|deprecated|unmaintained
  classification: FOLLOW       # FOLLOW|ADAPT|REFERENCE|DEPRECATED|CASE
  evidence_strength: consensus # consensus|strong-evidence|heuristic|contested|case-study|inference
  claims: metric definitions (TTFT/ITL/TPS), concurrency sweeps, operating-point selection
  chapters: ["06"]
  freshness: active            # volatile (re-verify before each cite)|active (quarterly)|stable|snapshot
  superseded_by: null          # or a source id
  notes: GenAI-Perf commands in the 2025 blog series are deprecated; method survives
```

Rules:
- FIS-internal evidence gets IDs too (`FIS-R6-AUTOPSY`, `FIS-R5-REPORT`, …,
  `type: internal-case`) so case citations survive any future repo split.
- `freshness: volatile` sources may not be cited as FOLLOW without a `last_verified`
  inside the current authoring pass (workstream W1).
- `snapshot` sources (prices, market states) are citable only with their as-of date
  printed at the point of use.
- Supersession is recorded, never deleted — the deprecation watchlist pattern from
  the NVIDIA research becomes a standing section of SOURCES.md.

## 8. Versioning policy

`VERSION` holds a semver string. Adopted interpretation (per the tentative proposal,
confirmed):

- **0.x** — being generalized/validated; FIS is the only instantiation.
- **1.0** — gated on successful instantiation on **at least two materially different
  project types** (different task shape, different grading regime, or different
  deployment surface than FIS — e.g., a RAG-heavy document QA product, or an
  API-cost-reduction engagement). "Instantiation" = the navigator + templates carried
  the project to at least one frozen, executed experiment contract without needing
  FIS knowledge.
- **MAJOR** — normative methodology change or compatibility break (a PRINCIPLE
  changes meaning; a template's required sections change incompatibly).
- **MINOR** — new method, chapter, template, or supported execution surface;
  a B→A promotion.
- **PATCH** — clarification, source refresh, link fix, non-normative example.

CHANGELOG entries record **what changed, why, and the evidence that caused it** —
three columns, mandatory. A `METHOD_DECISION_RECORD` (template) is written for every
adoption/rejection of a method; the CHANGELOG links it. Source-ledger `last_verified`
sweeps are recorded as PATCH entries.

## 9. Proposed templates and examples

**Templates** (each ships with: purpose header, required-sections list, a filled
miniature example, and "delete no section — write N/A + reason"):
PROJECT_PROFILE · EXPERIMENT_CONTRACT · EVAL_SUITE_RELEASE_CONTRACT ·
PERFORMANCE_AUTOPSY · TEST_LOOK_LEDGER · COMPUTE_DEMAND_LEDGER · PREDICTION_LEDGER ·
OPERATIONAL_HANDOFF · METHOD_DECISION_RECORD (list rationale in §1 tree table).

**Examples** — fixed format per case study: *Situation → Decision faced → Evidence →
What happened → The generic rule extracted → What would NOT have worked (where the
record shows it) → Links (source IDs, chapters)*. Seed set of twelve in §1, selected
from ~38 candidates in the inventory (`planning/evidence_inventory.json`,
`case_studies`); the remainder stay available as inline `[CASE]` one-liners. FIS
numerics live here and only here. The synthetic walkthrough is clearly labeled
fictional and exists to prove the navigator runs without FIS context.

## 10. Project navigator design

**Flow:** `PROJECT_PROFILE` (template, ~20 structured fields mirroring the target
user's arrival state) → archetype selection (decision tree in QUICKSTART) → per-
archetype route: ordered chapter path, required templates, first three actions, and
the gates that must exist before any spend.

```
PROJECT_PROFILE inputs
    ↓  (01 intake: constraints → decision context)
project constraints  →  task/eval model (03)          ← 02 read alongside: what
    ↓                                                    "the same system" means
candidate execution systems (05, fed by 06 capacity + 11 budget)
    ↓
experimental sequence (04 contracts; 07 diagnostic gates first)
    ↓
performance/economics characterization (06 + 11)
    ↓
system intervention choice (07 → 08 | 09)
    ↓
deployment gate (10, with 13 provenance standing)
    ↓
production learning loop (12 → back to 03)
```

**Draft archetypes** (validated/extended in workstream W4; each is a row in
QUICKSTART with: entry chapters, skippable chapters, mandatory templates, first
actions):

| Archetype | Signature profile facts | Entry path (first 3 chapters) | Typically skippable at start |
|---|---|---|---|
| A. Greenfield product, API-models-only | no owned hardware; frontier API budget; quality bar unclear | 01 → 03 → 04 | 06, 09, 11-hardware |
| B. Local/private deployment mandate | privacy/data restrictions dominate; owned or planned hardware | 01 → 02 → 03 (06 early) | 09 until ladder reached |
| C. Existing system underperforming | a system exists; failures observed; no trusted eval | 01 → 03 (eval first!) → 07 diagnostic gates | 05 (selection premature) |
| D. Cost reduction of an API-heavy system | traffic + spend known; quality bar established | 01 → 08 (cascade/routing) → 11 | 09; 03 only to verify eval trust |
| E. High-stakes / compliance-bound | audit requirements; reliability claims needed | 01 → 13 → 03 → 04 (pass^k early) | — |
| F. Lab/methodology bootstrap | building an evaluation capability itself | 00 → 03 → 04 → 12 | 10 until a client system exists |

Mechanism notes: the tree keys on profile *fields*, not vibes ("do you have a
trusted eval for this task? no → 03 before anything"; "is any comparison across
machines/sessions planned? yes → 02 now"). Every archetype ends its first sprint at
the same place: a frozen contract for the first real experiment. QUICKSTART also
carries the global tripwires ("stop and re-plan if…") so a user who reads nothing
else still inherits the stopping discipline.

## 11. Unresolved design questions (owner input wanted)

1. **Judge-based grading depth** (B1): the calibration protocol must be written
   without FIS validation. Accept `doctrine — not yet exercised` status, or defer the
   judge branch to 0.2 and scope 0.1 to verifiable-output tasks only?
2. **Publication intent**: is the playbook eventually public/client-facing? Affects
   canary strings in examples, disclosure of FIS specifics, and tone. Current
   assumption: client-shareable, repo-private.
3. **Standalone repo timing**: build under `playbook/` now, extract to its own repo
   at 1.0. Confirm, or extract at 0.1?
4. **Template enforceability**: markdown-only templates, or markdown + machine-
   checkable front-matter (YAML) so future runners can enforce freeze checklists?
   Current lean: markdown now, front-matter reserved (don't build tooling this pass).
5. **The Canonical Architecture's status** (B7): F-class reference or promoted to a
   recommended default topology? Current lean: F-class in 0.x.
6. **SOURCES.md generation**: hand-maintained vs a small script in the playbook repo.
   Current lean: hand-maintained until it hurts; the yaml is the record either way.
7. **Name**: does the playbook get a product name, or stay "AI Systems Engineering
   Playbook"? (Affects README/title only.)
8. **Chapter 14 generation discipline**: written by hand (risk: drift from chapters)
   or assembled mechanically from tagged gates in 00–13? Current lean: hand-written
   with a per-release consistency check against the chapters' gate sections.
9. **Canonical failure taxonomy** (inventory finding): the record carries two
   unreconciled taxonomies — the Canonical Architecture's 13-category discovery
   taxonomy and the MSI guide's 9-category failure taxonomy — and the operating
   task-ontology's root-cause set. The playbook must define ONE canonical taxonomy
   (03 + GLOSSARY) with an explicit mapping, not silently pick. Proposal to review
   in authoring: derive from the task-ontology's cause→action table (the only one
   with measured usage) and map the other two to it.
10. **The rigor dial** (inventory finding): the record never states how much
   instrument-validation/provenance investment a smaller or lower-stakes project
   warrants — as written, the methodology reads all-or-nothing. Proposed: a
   proportionality section in 00 + a PROJECT_PROFILE field (stakes/consequence
   tolerance) that the navigator uses to scale the mandatory-artifact set. Where
   should the floor sit (what is never skippable)? Current lean: consequence-bearing
   tolerances, look discipline, and provenance-of-record are floor; ceilings/ICC
   measurement scale with stakes.

## 12. Gap register (from the evidence inventory)

Subjects the playbook needs that the repository record does not supply (or supplies
only as an unexamined assumption). Full detail in `planning/evidence_inventory.json`
(`gaps_noticed` per document set). Each gap is assigned a home chapter and a
workstream; "silent absence" is the failure mode this register exists to prevent.

| # | Gap | Chapters | Fed by |
|---|---|---|---|
| G1 | **Requirement → task ontology derivation.** FIS's ontology pre-existed the lab; the record covers changing it, never deriving it from a stakeholder requirement. The front half of 03 must come from external practice (error-analysis-first, criteria-drift literature) plus a written derivation procedure. | 03, 01 | W2, W5 |
| G2 | **Proportionality / rigor sizing.** No criteria for scaling validation investment to project stakes (see §11 Q10). | 00, 01 | W9 |
| G3 | **Instruments without a synthetic generator.** Human-annotated gold, inter-rater agreement, judge-graded domains — the reachability/determinism apparatus assumes a code-driven generator. | 03 | W7, W8 |
| G4 | **Cold-start parameterization.** Setting selection thresholds, eligibility gates, and utilization caps with no incumbent system and no prior evidence base. | 01, 04, 08 | W2 |
| G5 | **Post-deployment monitoring of learned/routed components** — drift detection, retraining triggers, routing-quality regression. Absent from FIS *and* every vendor corpus surveyed. | 10, 12 | W2, W8 |
| G6 | **Privacy/PII in production telemetry & trajectory capture.** Clean-room doctrine covers the sandbox; capturing real-user trajectories is uncovered. | 12, 13 | W8 |
| G7 | **Model-license compliance for acquired weights** (content-hash provenance exists; license review does not). | 13 | W8 |
| G8 | **Security threat model for tool-calling surfaces** (prompt injection via tool outputs; guardrails) beyond DB-role isolation. | 13 | W8 |
| G9 | **Multi-tenant capacity, concurrency, and SLA burn under real traffic** — all FIS latency data is single-user. | 06, 10 | W8 |
| G10 | **Rollback / incident-response runbook mechanics.** Stages are named everywhere (shadow→canary→gate→rollback); trigger thresholds and procedures nowhere, vendors included. | 10 | W2 |
| G11 | **Unified routing-input taxonomy** — task features × live resource state × policy; the record has three partial versions that never met. | 08 | W2 |
| G12 | **Telemetry-pipeline correctness validation** (who audits the instruments' instruments). | 12 | W2 |
| G13 | **Graduation criteria: observe-only → automated action** for routers/self-modifying harnesses. | 08, 12 | W2 |
| G14 | **"Cost bucket = finding vs waste" decision test** — when is a dominant time/cost bucket the object of study vs overhead to eliminate? R6 answered by fiat. | 06, 07 | W2 |
| G15 | **Amendment legitimacy rule** — distinguishing a TRAIN-derived threshold amendment from post-hoc threshold-shopping, beyond commit order (R5's self-flagged tension). | 04 | W2 |
| G16 | **Operational definition of "gold labels may score but never choose"** (fit/tune vs inference-time reads — currently implicit practice). | 04, 08, 13 | W2 |
| G17 | **Diagnostics inside vs outside the fail-closed state machine** — the record shows one choice (extend narrowly), not the tradeoff. | 04, 07 | W2 |
| G18 | **All statistical generality comes from outside the historical record** (confirmed independently by four document sets flagging absent power/MDE methodology — only the 2026-08 research supplies it). | 04 | W3 |
| G19 | **Tool-contract design as a first-class subject** (sort order, cohort keying, evidence reachability): currently smeared across 03/08. Decision: home in 08, instrument-validation half cross-referenced from 03. | 08, 03 | W6 |
| G20 | **Contradictions register** (kept visible per §5.6): local-runtime default (llama.cpp vs vLLM — needs the *criterion*, not a winner); eval volume-vs-curation; the two failure taxonomies (§11 Q9). | 05, 03 | W1, W2 |

## 13. Research workstreams for the authoring pass

| ID | Workstream | Scope | Depends on |
|---|---|---|---|
| W1 | **Vendor re-verification** | Live re-fetch of every FOLLOW/ADAPT source and the deprecation watchlist (AIPerf/NIM guide, Evaluator SDK compare/gate, Switchyard, NeMo Platform, Model Optimizer, serving playbooks, observability docs). Aug-2026 statuses are weeks old and several sources are pre-alpha/volatile. Update sources.yaml `last_verified`, flip verdicts where reality moved. | sources.yaml seeded (this pass) |
| W2 | **Decision-rule inventory** | Enumerate every point where the playbook must supply a decision rule no vendor publishes (stop, promote, buy, select, refresh, escalate); draft each rule from FIS evidence + the non-NVIDIA literature; mark each rule's evidence strength. This is the playbook's core IP — treat as its own deliverable feeding 04/05/07/10/11/14. | SOURCE_MAP |
| W3 | **Statistics formulary** | Generalize the FIS statistical machinery into parameterized procedures with worked calculations: ICC estimation for arbitrary clustering structures, N_eff/MDE, curtailment arithmetic, paired designs, pass^k, sequential-rule admissibility conditions (when i.i.d. tools are safe). External statistical review pass desirable. | — |
| W4 | **Navigator validation** | Dry-run QUICKSTART + PROJECT_PROFILE against 4–5 synthetic profiles including at least two materially non-FIS shapes (RAG document QA; high-traffic API cost reduction; judge-graded creative task). Failure to route cleanly = architecture bug found before authoring hardens. | 01/QUICKSTART drafts |
| W5 | **Case-study write-ups** | The eight `examples/` files from the FIS record, in the fixed format, numerics quarantined here. | SOURCE_MAP |
| W6 | **Template generalization** | De-FIS the contract template, suite-release contract, autopsy schema, ledgers, handoff doc; write miniature filled examples for each. | B-decisions §5 |
| W7 | **Judge-calibration protocol** | Write the κ-corrected, bias-audited, human-anchored protocol from the literature (JudgeBench, reliability/validity work) as doctrine-not-exercised; needed for archetypes with non-verifiable outputs. | Q1 resolution |
| W8 | **Declared-gap subjects** | Decide include-from-external-sources vs declare-out-of-scope-0.x for: multi-tenant/high-concurrency serving (G9), guardrails/agent security (G8), PII in telemetry (G6), model-license compliance (G7), non-generator instruments (G3), post-deployment drift monitoring (G5), streaming UX metrics, team/staffing patterns, data-labeling operations at scale. Write the scope statement either way (silent absence is the failure mode). | owner review |
| W9 | **The rigor dial** | Design the proportionality mechanism (§11 Q10): stakes/consequence-tolerance profile field → scaled mandatory-artifact set, with an explicit never-skippable floor. Validated against the W4 synthetic profiles (at least one deliberately low-stakes). | Q10 resolution |

Model economy for authoring (consistent with this pass): main-model architecture and
adjudication; Sonnet for bounded per-chapter drafting against this plan + SOURCE_MAP;
Haiku for mechanical URL/date sweeps in W1; adversarial verification pass on 00/04/07
(the normative core) before 0.1 tags.

The statement-level raw material for chapter drafting — ~450 classified statements,
the 60-item anti-pattern catalog (each chapter's "failure modes" section draws from
it), and ~38 case-study candidates — is preserved in
`planning/evidence_inventory.json`, keyed by source document set.

## 14. Definition of done

**This planning pass** is done when: this plan + SOURCE_MAP_DRAFT are committed;
owner has reviewed §5's boundary decisions and §11's questions; authoring-pass
workstreams are approved/amended.

**Playbook 0.1** (first authored version) is done when:
- All 15 chapters exist in the §3 skeleton with every section present or reasoned N/A;
- every FIS numeral in chapters 00–14 sits inside a `[CASE]`/parameter-table context
  (checked by grep for the quarantine list, §5.1);
- sources.yaml covers every citation; every FOLLOW/ADAPT source has `last_verified`
  within the authoring window (W1);
- all nine templates ship with filled miniature examples;
- the twelve case studies + synthetic walkthrough exist;
- every G-row in §12 is either covered in its home chapter or carries a written
  out-of-scope statement (W8);
- QUICKSTART routes all W4 synthetic profiles to defensible paths without FIS
  knowledge;
- `playbook/` has zero references into `docs/` that a reader must follow to
  understand a chapter (links out are annotations, not dependencies);
- CHANGELOG records the 0.1 evidence base.

**Playbook 1.0** per §8: two materially different project instantiations carried
through at least one frozen executed contract each, with METHOD_DECISION_RECORDs for
every rule the projects forced to change.
