Build Adaptive AI Systems Playbook v0.1.0 exactly from the committed Pass-1
architecture and evidence plan.

This is a documentation, synthesis, research, and methodology-authoring mission.

The result must be a self-contained, reusable, project-independent AI systems
engineering playbook that serves as the entry point to future AI projects.

It should answer: what should I do next, why, what evidence do I need, what should I
measure, what can I skip, what should force me to stop/change direction, and when is
an expensive intervention justified?

Then STOP.

===============================================================================
READ FIRST / AUTHORITY
===============================================================================

Read:
1. playbook/PLAYBOOK_BUILD_PLAN.md
2. playbook/SOURCE_MAP_DRAFT.md
3. playbook/planning/ as needed
4. docs/research/2026-08-19_NVIDIA_AI_Lab_Playbook_Research.md
5. docs/research/2026-08-20_AI_Lab_Methodology_Hardware_Strategy.md
6. docs/current/AI_SYSTEMS_LAB_MASTER_PLAN.md
7. docs/current/EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md
8. docs/current/EXPERIMENT_CONTRACT_TEMPLATE.md

Verify HEAD contains c93ac13 or a descendant and the Pass-1 artifacts exist.

PLAYBOOK_BUILD_PLAN.md is authoritative for:
- architecture and chapter boundaries;
- dependency graph;
- terminology/callouts;
- generic-vs-project extraction rules;
- source/citation design;
- templates;
- navigator;
- versioning;
- G1-G20 gap register;
- W1-W9 workstreams;
- definition of done.

SOURCE_MAP_DRAFT.md is the authoritative starting evidence/source map.

Where older illustrative structure conflicts with Pass 1, follow Pass 1 unless an
explicit owner decision below overrides it.

===============================================================================
PRODUCT
===============================================================================

Name: Adaptive AI Systems Playbook
Version: 0.1.0
Location: playbook/

Keep it under playbook/ through 0.x. Do not split into a standalone repo in this pass.

A future engineer must be able to copy/use playbook/ without needing FIS history,
docs/current, experiment databases, or repository-specific runtime state.

===============================================================================
FOUNDATIONAL MODEL
===============================================================================

Use:

ExecutionSystem =
    model
  + artifact / quantization / adapter
  + runtime / provider
  + hardware / host
  + harness
  + context policy
  + retrieval / knowledge
  + tools
  + workflow
  + generation / reasoning budget
  + verifier / grader
  + environment

A comparison claim is about the frozen execution system unless the experiment
explicitly isolates one factor.

Do not collapse model/runtime/provider/harness/hardware into one ambiguous label.

Teach users to measure reproducibility boundaries across sessions, restarts, hosts,
concurrency, and providers rather than assuming them.

===============================================================================
FIS / PROJECT-SPECIFIC BOUNDARY
===============================================================================

FIS is valid empirical evidence and a good dedicated case study.

FIS is NOT part of the generic methodology's identity.

Generic/normative material must not contain FIS-specific terminology, experiment
series, milestone names, project-specific model results, machine assumptions, numeric
thresholds, or FIS-specific architecture except for neutral links to dedicated cases.

This applies to:
- README.md
- QUICKSTART.md
- GLOSSARY.md
- chapters 00-14
- templates/
- references/STATISTICS_FORMULAS.md
- references/VENDOR_RECIPE_NOTES.md
- generic synthetic examples

Extract project evidence into generic:
- principle;
- default;
- project parameter;
- formula;
- decision rule;
- stopping condition;
- anti-pattern;
- procedure.

FIS MAY and SHOULD appear under playbook/examples/ as real empirical case studies.

Use neutral stable filenames/titles such as:
- CASE-001_consequence-bearing-tolerances.md
- CASE-002_clustered-eval-effective-n.md
- CASE-003_learned-router-leakage.md
- CASE-004_harness-defects.md
- CASE-005_hardware-purchase-discipline.md
- CASE-006_token-budget-confounding.md

Inside each case, identify FIS and preserve the real experiment details.

Every case must separate:
1. WHAT HAPPENED IN THIS PROJECT
2. THE GENERIC LESSON

Generic chapters may link to CASE IDs but remain readable without opening them.

Supersede the Pass-1 phrase "the FIS instance as one worked value" with:
"one neutral illustrative value or synthetic worked example; project-specific
empirical values stay in the case-study library."

Do not use FIS numbers as generic defaults.

Before release, search every file outside playbook/examples/ for FIS/project-specific
identifiers. Every hit must be removed/generalized or explicitly justified as a
neutral case-study navigation reference.

If useful, create a non-portable maintainer map outside the shipped playbook:
docs/research/PLAYBOOK_INTERNAL_EVIDENCE_MAP.md
mapping generic rule -> FIS evidence -> external corroboration -> classification.

===============================================================================
GENERIC EXTRACTION / EVIDENCE RULES
===============================================================================

Use the A-H taxonomy:
A generic normative principle
B generic default/heuristic
C project parameter
D vendor recipe — FOLLOW
E vendor recipe — ADAPT
F reference
G case study / empirical lesson
H rejected / deprecated

Binding rules:
1. Numbers do not travel; procedures travel.
2. A-class requires external corroboration or explicit first-principles support.
3. Single-project singletons cap at B until validated elsewhere.
4. Rejections carry CONDITIONS, not project-specific verdicts.
5. Vendor verdicts carry as-of dates and freshness sensitivity.
6. Contradictions stay visible and get project-specific decision rules.
7. Evidence strength is explicit.
8. Designed-but-unexercised methodology is labeled honestly.
9. Raw inventory classifications are candidates, not final authority.

Evidence-strength labels:
consensus / strong-evidence / heuristic / contested / case-study / inference

===============================================================================
OWNER DECISIONS — PASS-1 OPEN QUESTIONS RESOLVED
===============================================================================

1. JUDGE-BASED GRADING
Include it in 0.1.0.
Where not internally exercised, mark:
    status: doctrine — not yet exercised
Write a real literature-grounded protocol covering agreement, validity, bias,
human anchoring, rubric stability, domain transfer, and recalibration.

2. PUBLICATION INTENT
Write client-shareable and potentially public-later prose.
No secrets, sensitive IDs, private-path dependencies, or proprietary assumptions.

3. STANDALONE REPO
Deferred. Stay under playbook/ in 0.x.

4. TEMPLATE ENFORCEMENT
Markdown templates now. Use stable structured headings so machine-checkable front
matter can be added later. Do not build a general enforcement framework now.

5. CANONICAL ARCHITECTURE
Keep the existing Canonical Architecture as F-class reference in 0.x, not a universal
topology.

6. SOURCE RENDERING
references/sources.yaml is the record of record.
A small deterministic SOURCES.md generator/validator is allowed if simple/local.
Do not build a documentation platform.

7. NAME
Adaptive AI Systems Playbook.

8. CHAPTER 14
Curated operational condensation of 00-13, not an independent normative authority.
Add a release consistency check mapping every gate/checklist to its source chapter.

9. CANONICAL FAILURE TAXONOMY
Define ONE generic taxonomy.
Start from the cause->action taxonomy because it has measured use, but challenge and
generalize it against external evidence.
Map older competing historical taxonomies into it.
Every root cause should map to likely next interventions.

10. RIGOR DIAL
Add proportionality by project stakes/consequence tolerance.
PROJECT_PROFILE captures stakes.
QUICKSTART uses them to scale required artifacts/validation.

Never-skippable floor:
- state the decision/problem and claim;
- preserve enough execution-system/artifact provenance to identify what produced a result;
- define evaluation/ground-truth boundary before making a quality claim;
- predeclare consequences for decision-driving thresholds/tolerances;
- treat held-out evidence as consumable and record exposure;
- retain outcome evidence.

Higher-stakes projects add stronger suite/statistics/provenance/security/reliability/
shadow-canary/human-approval/rollback controls.

W9 must validate the final rigor mechanism against synthetic project profiles.

===============================================================================
PROJECT ENTRY / QUICKSTART
===============================================================================

PROJECT_PROFILE must cover at least:
- business/problem outcome;
- task population;
- criticality/failure cost;
- quality/reliability target;
- latency/throughput/SLA;
- privacy/security/data residency;
- data/knowledge availability;
- tool/action permissions;
- model candidates;
- owned compute;
- rentable compute;
- managed APIs;
- capex budget;
- recurring cloud/API budget;
- utilization/growth;
- staffing/time;
- deployment environment;
- observability;
- regulatory/compliance;
- existing evidence;
- stakes/consequence tolerance.

QUICKSTART must route by facts, not vibes.

Default lifecycle:
define decision/problem
-> trustworthy eval substrate
-> integrity/ceiling
-> simplest credible baseline
-> frozen execution-system identity
-> candidate characterization
-> failure diagnosis
-> intervention choice
-> capability/quality eval
-> performance characterization
-> economics
-> shadow/canary
-> promote/rollback
-> production evidence back into learning

A new user must know the first three actions without reading the whole book.

===============================================================================
INTERVENTION LADDER
===============================================================================

Before training, diagnose whether the dominant cause is:
- infrastructure/runtime/tool correctness;
- missing/unreachable evidence;
- retrieval/context;
- tool/API contract or permissions;
- schema/output enforcement;
- prompt/workflow;
- verifier/grader;
- routing/escalation;
- generation/reasoning budget;
- adapter/fine-tuning;
- larger/different model;
- architectural redesign.

Align final ladder with the canonical failure taxonomy.

Teach:
- evidence required to descend a rung;
- what blocks movement;
- cheap diagnostic gates;
- finding-vs-waste decisions;
- when optimization should stop.

Do not train around broken infrastructure.

===============================================================================
EVALUATION / EXPERIMENT DESIGN
===============================================================================

Be especially rigorous on:
- requirement -> evaluation claim;
- ontology derivation;
- representative sampling;
- synthetic and human-annotated instruments;
- reachability/solvability ceilings;
- ground truth;
- deterministic vs model graders;
- judge calibration;
- leakage/contamination;
- TRAIN/DEV/TEST or analogous split discipline;
- suite versioning and criteria drift;
- regression vs capability suites;
- stochastic systems/pass^k;
- clustering;
- paired comparison;
- effective N;
- MDE/power;
- INCONCLUSIVE;
- descriptive vs inferential claims;
- held-out look accounting;
- contemporaneous causal controls under runtime/session nondeterminism;
- prediction ledgers;
- stopping/curtailment;
- consequence-bearing tolerances;
- suite refresh triggers;
- cold-start parameterization;
- amendment legitimacy;
- gold-label usage boundary.

Do not prescribe project-specific split sizes.

Generalize the Experiment Contract template with:
question, decision, prediction, baseline, execution-system identity, manipulated
variable, controlled variables, artifacts, split protocol, calibration, consequence
tolerances, selection/elimination, feasibility, statistics, clustering unit, MDE,
generation/runtime settings, qualification gates, confirmation protocol, amendments,
provenance, telemetry, analysis, economics, roles, freeze checklist.

Include generic examples for model, quantization, prompt/workflow, retrieval,
reasoning-budget, routing, fine-tuning, and hardware/runtime experiments.

===============================================================================
PERFORMANCE / VENDOR RECIPES
===============================================================================

Keep capability/quality experiments separate from performance experiments.

Where NVIDIA guidance is mature, label it FOLLOW BY THE BOOK and point to the current
primary source.

Cover:
TTFT, ITL/TPOT, latency, token distributions, throughput, system/per-user TPS,
concurrency, request-rate sweeps, warmup, percentiles, operating points, capacity,
memory capacity vs bandwidth, prompt vs decode, multi-tenant/SLA behavior, clock
validity, effective bandwidth, performance autopsy, power/TCO.

Create a centralized vendor-recipe catalog with:
stable ID, vendor, title, primary URL, verified date, relevant version, maturity,
FOLLOW/ADAPT/REFERENCE/DEPRECATED, what it solves, what it does not solve, required
project validation, chapters, freshness.

W1 must live-reverify all load-bearing FOLLOW/ADAPT sources, especially NVIDIA
benchmarking, Evaluator SDK, Model Optimizer, Switchyard, NeMo Platform, serving
stacks, fine-tuning mechanics, observability, and deprecations.

Prefer primary sources. Do not use aggregators when primary sources exist.

===============================================================================
MODEL/RUNTIME/HARNESS SELECTION
===============================================================================

Teach bounded candidate-set construction across:
capability, model-family diversity, size, quantization, context, tool use, structured
output, licensing, data policy, deployability, hardware fit, APIs, runtime
compatibility, serving ecosystem, fine-tuning support, observability, cost, latency,
complexity, reproducibility.

Do not choose a universal runtime winner.
Teach criteria for determinism/provenance, throughput, managed-provider, and hybrid
regimes.

Unexercised harness-comparison doctrine must be labeled.

===============================================================================
ECONOMICS / HARDWARE / CLOUD / API
===============================================================================

Teach existing hardware vs purchase vs rental vs managed inference vs frontier APIs
vs hybrid.

Include formulas/neutral examples for:
rent-vs-buy, amortization, utilization, energy/ops, GPU-hours/month, cost/request,
cost/successful task, expected cost/solve, routing break-even, latency-dollar
tradeoff, parallel-node critical-path benefit, capacity-vs-bandwidth constraints.

Do not hard-code current GPU prices as doctrine.
Snapshot prices require as-of dates.
Require re-verification at purchase time.
Teach demand-ledger + precommitted purchase-trigger discipline.

===============================================================================
TRAINING / DATA
===============================================================================

Training comes late.

Cover:
evidence threshold, SFT vs LoRA/QLoRA vs full tune, RAG/context vs training,
data legality/licensing, own-trace data, contamination, train/eval separation,
sample-size ablations, provenance, seeds, merge/quantize/serve, forgetting,
post-tune comparison, deployment gate, RL evidence bar, and rejection criteria.

Do not invent universal minimum-n folklore.

State clearly that the internal project has not yet exercised training.
Separate external literature, vendor mechanics, playbook inference, and internally
exercised evidence.

===============================================================================
RETRIEVAL / TOOLS / ROUTING
===============================================================================

Cover:
retrieval/context, tool-contract design, evidence reachability, deterministic gates,
learned routing, local/private/frontier tiers, escalation cost, false-negative cost,
oracle analysis, leakage/class identity, OOD/leave-group-out validation,
routing-input taxonomy, break-even economics, fail-open/fail-closed, multi-tier
routing, observe-only -> automated-action graduation, and when routing is not worth it.

===============================================================================
DEPLOYMENT / OBSERVABILITY / GOVERNANCE
===============================================================================

Deployment is thin internally: distinguish established SRE/progressive-delivery
practice from AI-specific doctrine.

Cover shadow, canary, causal metrics, one-change-at-a-time, promotion gates, rollback,
incident response, multi-tenant/SLA behavior, security/privacy gates, human approval.

Define a generic minimum trajectory record covering task/trace, execution system,
artifact, prompt/context, retrieval, tools, permissions, output, verification,
outcome, latency, tokens, cost, clocks, runtime/harness version, capability config,
mutations, human feedback, deployment stage.

Separate authoritative data, RAG knowledge, working state, trajectories, learned assets.

Cover telemetry-pipeline correctness, PII/privacy, production-failure harvesting,
drift, retraining/routing triggers, and periodic methodology audits.

Governance must cover frozen contracts, append-only records, hashes, lineage, privacy,
PII, secrets, permissions, training authorization, model-license review, tool-calling
threat models, prompt injection, ground-truth isolation, rollback, human approval,
publication/canary hygiene, and auditability.

===============================================================================
G1-G20 GAP REGISTER IS BINDING
===============================================================================

Every G1-G20 item must finish as exactly one of:
COVERED
COVERED-AS-DOCTRINE-NOT-YET-EXERCISED
EXPLICITLY-OUT-OF-SCOPE-FOR-0.1

Silent omission is forbidden.

Pay special attention to:
G1 ontology derivation
G2 rigor sizing
G3 non-generator instruments
G4 cold-start parameterization
G5 post-deployment drift
G6 privacy/PII trajectories
G7 model-license compliance
G8 tool-calling security
G9 multi-tenant capacity/SLA
G10 rollback/incident mechanics
G11 routing-input taxonomy
G12 telemetry-pipeline correctness
G13 automation graduation
G14 finding-vs-waste
G15 amendment legitimacy
G16 gold-label boundary
G17 diagnostics inside/outside fail-closed state
G18 statistical generality
G19 tool-contract design
G20 contradictions register

Do not fill gaps with unsupported confidence.

===============================================================================
THIN-CHAPTER HONESTY
===============================================================================

01, 09, and especially 10 are thin internally.

Therefore:
- 01 may synthesize intake/navigator methodology but must label playbook inference;
- 09 must state internal training is not yet exercised;
- 10 must distinguish established SRE practice from AI-specific doctrine;
- any other thin W8 subject gets the same treatment.

Thoroughness must not imply false validation.

===============================================================================
SOURCE SYSTEM / TEMPLATES
===============================================================================

references/sources.yaml is canonical.

Each source needs:
stable ID, org/vendor, title, URL, type, pub/update date, last verified date,
version, maturity, classification, evidence strength, claims, chapters, freshness,
supersession notes.

Chapters cite stable IDs.
SOURCES.md is the human-readable rendering.
Volatile FOLLOW/ADAPT sources require verification in this pass.
Snapshot prices print as-of dates.

Ship at least:
PROJECT_PROFILE
EXPERIMENT_CONTRACT
EVAL_SUITE_RELEASE_CONTRACT
PERFORMANCE_AUTOPSY
TEST_LOOK_LEDGER
COMPUTE_DEMAND_LEDGER
PREDICTION_LEDGER
OPERATIONAL_HANDOFF
METHOD_DECISION_RECORD

Each template:
purpose, when to use, required sections, N/A+reason discipline, miniature neutral
example, links to governing chapters.

No FIS-specific defaults in templates.

===============================================================================
CASE STUDIES / GENERIC EXAMPLES
===============================================================================

Pass-1 §1 + §14 case-study requirement governs over stale W5 "eight examples".

Create the planned empirical case-study set using neutral CASE-### filenames, plus a
non-FIS synthetic end-to-end walkthrough.

Empirical case format:
Situation
Decision faced
Evidence
What happened
Generic lesson
What would not have worked
References

FIS details are allowed inside case studies only.

Also include generic/synthetic worked examples spanning:
API-only assistant
private/local system
RAG-heavy system
high-throughput extraction/classification
tool-calling agent
cost-reduction/routing
training rejected
training justified
high-stakes/audited deployment
statistically INCONCLUSIVE result
hardware rent-vs-buy

===============================================================================
W1-W9 RESEARCH ORCHESTRATION
===============================================================================

Execute the committed workstreams:
W1 vendor re-verification
W2 decision-rule inventory
W3 statistics formulary
W4 navigator validation
W5 case-study write-ups
W6 template generalization
W7 judge calibration
W8 declared-gap subjects
W9 rigor dial

Main Fable owns architecture, classification adjudication, contradictions,
high-stakes decision rules, final normative prose, consistency, and definition of done.

Use Sonnet as the default substantive subagent.
Use Haiku for mechanical URL/date/version/deprecation work.

Do not have multiple agents independently resummarize the full repo.
Use playbook/planning/ inventories to reduce repeated context.

Each research subagent returns compact:
claim/question
source IDs
evidence strength
generic rule or gap
project parameter if any
chapter target
caveats/contradictions
recommended classification

Use Fable/Opus only for selective load-bearing adversarial review.

===============================================================================
W4 NAVIGATOR VALIDATION
===============================================================================

Dry-run QUICKSTART + PROJECT_PROFILE against at least 4-5 materially different
synthetic profiles, including:
- RAG document QA;
- API-only greenfield;
- high-traffic API cost reduction;
- judge-graded/open-ended;
- local/private deployment;
- high-stakes audited agent;
- deliberately low-stakes project for rigor-dial validation.

For each, verify:
- first three actions are sensible;
- chapters/templates are minimal but sufficient;
- expensive interventions are not premature;
- eval trust precedes optimization;
- governance rises with stakes;
- rigor scales without losing the floor;
- first sprint ends at a frozen first real experiment contract.

Routing failure is an architecture defect. Fix it.

===============================================================================
ADVERSARIAL REVIEWS
===============================================================================

A. Scientific/methodological:
Challenge 00/03/04/07/09 for unsupported universals, bad statistics, invalid stopping,
loss of INCONCLUSIVE, weak tolerances, premature training, weak judge calibration,
and unconditionalized rejections.

B. Practitioner portability:
Can a new engineer derive defensible first 3-5 milestones from project requirements,
models, hardware, cloud/API options, budget, and constraints without knowing FIS?

C. Internal consistency:
Do QUICKSTART, PROJECT_PROFILE, chapter 14, and templates encode the same methodology?

Fix BLOCKER/MAJOR findings or document why unresolved.

===============================================================================
DOCUMENT UX / VERSIONING
===============================================================================

README must include:
what this is
who it is for
15-minute quickstart
lifecycle map
"I need to..." navigation
project-type reading paths
templates
vendor recipes
references
version/changelog

Every chapter:
previous / index / next
links to templates, references, cases

Prefer tables, procedures, formulas, checklists, decision trees, examples over walls
of prose.

Use MUST / SHOULD / MAY deliberately.

Recommended callouts:
[PRINCIPLE]
[DEFAULT]
[PARAMETER]
[DECISION GATE]
[STOP CONDITION]
[FOLLOW: SRC-ID]
[ADAPT: SRC-ID]
[REFERENCE: SRC-ID]
[CASE: CASE-ID]
[REJECTED]

VERSION = 0.1.0

CHANGELOG records what changed, why, and evidence/rationale.
METHOD_DECISION_RECORD accompanies substantive method adoption/rejection.

1.0 requires at least two materially different project instantiations through a frozen,
executed experiment contract without relying on FIS knowledge.

===============================================================================
VALIDATION / DEFINITION OF DONE
===============================================================================

Pass-1 §14 definition of done governs, modified only by this FIS-boundary override.

Before completion verify:
- all 15 chapters exist;
- every section exists or is reasoned N/A;
- all internal links work;
- all load-bearing FOLLOW/ADAPT sources were live reverified;
- sources.yaml covers every citation;
- SOURCES.md agrees with sources.yaml;
- no deprecated vendor tool is presented as current;
- vendor mechanics are separated from decision methodology;
- formulas have units and neutral worked examples;
- all nine templates exist with miniature filled examples;
- planned empirical CASE-### set exists;
- non-FIS synthetic walkthrough exists;
- every G1-G20 item has an explicit disposition;
- QUICKSTART passed W4 validation;
- rigor dial passed low/high-stakes profiles;
- FIS numerics are quarantined to cases;
- generic chapters contain no unjustified FIS methodology;
- generic methodology does not depend on docs/;
- thin chapters expose uncertainty;
- GLOSSARY does not drift;
- QUICKSTART, PROJECT_PROFILE, chapter 14, and templates agree;
- VERSION and CHANGELOG agree;
- existing repo tests remain green if tooling/scripts were added.

Run portability search outside playbook/examples/ for known project-specific
identifiers and resolve every hit.

The stale W5 phrase "eight examples" does not override §1 + §14.

===============================================================================
ROOT REPO INTEGRATION / COMMIT
===============================================================================

Do not replace/rewrite docs/current.

Minimal index changes may explain:
playbook/ = reusable methodology
docs/current/ = project-specific application
historical reports = empirical evidence/provenance

Do not create competing normative authorities.

Commit the complete playbook and minimal navigation/tooling changes.
Do not mix M0/R-series execution, model inference, training, hardware procurement, or
experimental-state mutation into this commit.

Push if the active workflow is authorized to do so.

===============================================================================
FINAL RESPONSE / STOP
===============================================================================

Report:
- playbook version;
- final file tree;
- number of primary external sources reverified;
- major FOLLOW recipes;
- major ADAPT recipes;
- major non-vendor methodology sources;
- G1-G20 disposition summary;
- biggest generic-vs-project transformations;
- case studies created;
- W4 synthetic profiles and architecture fixes;
- rigor-dial outcome;
- adversarial review findings/fixes;
- doctrine-not-yet-exercised / remaining limitations;
- validation checks;
- commit SHA;
- push status.

Then STOP.

Do not execute M0 or any project experiment.
Do not start R7/R9/M-STAT.
Do not train/fine-tune.
Do not purchase hardware.
Do not mutate experimental state.
Do not update project milestone state on the owner's behalf.
