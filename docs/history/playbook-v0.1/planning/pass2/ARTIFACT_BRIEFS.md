# Pass-2 Artifact Briefs: templates, case studies, synthetic examples (scaffolding)

Read with AUTHORING_CONVENTIONS.md. Templates and SYNTH files are GENERIC (portability
boundary applies in full). CASE files are the ONE place project-specific material is
allowed — and required.

## A. Templates (playbook/templates/)

Every template ships with, in order:
1. Title + one-line purpose; nav line (`Index: ../README.md · Governing chapter: ../NN_...md`).
2. **When to use / when not to** (2–6 bullets).
3. **Rigor-tier applicability** (which stakes tiers require it; from conventions §8).
4. The template body itself: stable numbered H2 sections with `[...]` placeholders and
   inline guidance in italics. Stable headings — machine-checkable front matter may be
   added in a later version; do NOT add YAML now.
5. **"Delete no section"** rule stated: absence is a decision — write `N/A — <reason>`.
6. **Miniature filled example**: a compact, clearly-synthetic filled instance
   (invented project, round numbers, labeled "Illustrative example — synthetic").
7. Links to governing chapters.

No project-specific defaults anywhere. Sizes/thresholds appear only as `[...]`
placeholders with guidance on how to choose (linking chapters), never pre-filled.

### templates/EXPERIMENT_CONTRACT.md (governing: 04; also 02, 07)
The generalized v2 contract. Required sections (adapt names, keep all content):
1 Question, decision driven, and prediction register (pre-run effect estimate +
interval per primary metric); explicit non-goals. 2 Frozen scientific baseline
(suite version, corpus/scorer/verifier identities, incumbents that must not move).
3 Artifacts (every model artifact by content hash + upstream identity; self-produced
artifacts by their training-provenance record). 4 Execution systems & node placement
(pinned builds/config/hosts; which arm runs where; rented-node rules: single session
per arm, digests verified remotely). 5 Manipulated variable & controlled variables
(ONE factor per arm unless factorial pre-registered). 6 Split protocol (roles of
iterate/qualify/confirm splits; execution ordering = stratum-interleaved; any
screening rungs stratum-balanced; look-ledger entry planned at freeze). 7 Calibration
rules (iterate split only) — consequence-bearing: parameter | procedure | tolerance |
consequence on breach (ABORT/RECALIBRATE/PROCEED-WITH-DECLARED-CEILING) | projected
cost if PROCEED; curtailed exact counting; "a tolerance without a consequence fails
contract review". 8 Candidate selection & elimination rules (selection metric;
elimination-rule compliance: no withdrawal below pilot MDE — state the pilot MDE;
sub-MDE handling choice). 9 Feasibility probes (stability/context-fit/memory).
10 Statistical plan (clustering unit; expected discordance; cluster-corrected MDE +
effective N at α/power; primary = cluster-robust paired inference, secondary =
McNemar labeled anti-conservative; verdict readings written BEFORE data; pass^k plan
if any arm stochastic). 11 Generation/runtime configuration per arm (frozen).
12 Qualification gates (numeric, fixed from historical data only; each gate names
its consequence). 13 Confirmation protocol (one look; certainty-curtailment clause
default-on with the three guards copied in; disabling requires written
justification). 14 Run states & integrity controls (fail-closed requirements,
contract binding by content hash, ground-truth isolation, diagnostic run kinds
non-promotable). 15 Telemetry requirements (dual clocks + authoritative clock per
metric; lifecycle events; per-invocation stats; logs preserved; resource sampler
threshold). 16 Analysis plan (tables, replays, economics incl. routing break-even
where claimed, cost accounting to the demand ledger). 17 Roles (scientific owner
interprets; executor runs the rules; the contract executes — no mid-run
improvisation). 18 Amendment log (append-only after freeze; amendment-legitimacy
rules from ch.04 §amendments referenced). End with the FREEZE CHECKLIST (all-true
before any iterate-split inference): committed before first call; every tolerance
has a consequence; MDE+effective-N+verdict readings written; prediction register
filled; look ledger updated; node placement + authoritative clocks declared; smoke
pass recorded; elimination threshold stated.
Miniature example: a prompt-variant experiment on an invented "invoice-triage"
project (Tier 2), ~40 lines.

### templates/PROJECT_PROFILE.md (governing: 01; consumed by QUICKSTART)
~20 structured fields (exact list in CHAPTER_BRIEFS 01 / spec): business outcome;
task population & volume; criticality/failure cost; quality/reliability target;
latency/throughput/SLA; privacy/security/data residency; data & knowledge
availability; tool/action permissions; model candidates; owned compute; rentable
compute; managed APIs; capex budget; recurring budget; utilization/growth
expectations; staffing/time; deployment environment; observability constraints;
regulatory/compliance; existing evidence (evals, incumbent systems, logs);
stakes/consequence tolerance (Tier 1/2/3 with the tier definitions summarized).
Each field: what it asks, why it matters (one line), which chapters consume it.
End: "derived outputs" block — archetype (from QUICKSTART tree), stakes tier,
mandatory-artifact set, first three actions. Miniature example: a small
document-QA assistant profile, ~25 lines.

### templates/EVAL_SUITE_RELEASE_CONTRACT.md (governing: 03)
Sections: 1 Suite identity & version; what changed vs prior version + why (criteria
drift made explicit). 2 Corpus identity (generation determinism/digest or
annotation-batch identity). 3 Ontology/taxonomy version + change discipline
(breaking-change rules). 4 Ground-truth gates (gold answers verified; per-stratum
solvability/reachability ceilings MEASURED and printed; frontier-saturation check).
5 Grader identity (deterministic scorer/verifier versions; judge + calibration
record if any). 6 Split design (strata, sizes, disjointness/leakage protections,
canary strings present). 7 Static integrity gates (executable commands; full-corpus
rule). 8 Baseline re-measurement plan (which arms re-baseline on the new suite).
9 Cross-suite refusal statement (tooling refuses cross-version comparison).
10 Release checklist. Miniature example ~20 lines.

### templates/PERFORMANCE_AUTOPSY.md (governing: 06)
Sections: 1 Run identity & question (what did this run cost and why). 2 Telemetry
sources inventoried (events, logs, samplers, clocks — with gaps stated). 3 Timeline
reconstruction (per-phase wall clock by authoritative clock; cross-source
consistency checks). 4 Critical path (the dominant serial chain; slack per branch).
5 Cost-bucket attribution (compute/wait/overhead; finding-vs-waste verdict per
bucket, ch.06 §test). 6 Clock validity (realtime-vs-monotonic deltas; skew found?).
7 Counterfactuals (what would N parallel nodes / faster device / smaller budget /
different quant have saved — arithmetic shown). 8 Actions (each: finding → action →
owner; route waste to engineering, findings to contracts). Miniature example ~20
lines (invented batch run).

### templates/TEST_LOOK_LEDGER.md (governing: 04, 03)
Purpose: held-out exposure accounting. Counting convention (a look = one arm's
outcomes on the held-out split read for a decision/report, incl. offline replays;
analyses within an already-counted look don't recount). Columns: # | date |
experiment | arm/run | items | kind (execution/replay) | notes. Standing-consequences
block (what is already spent for what). Refresh-trigger block: pre-registered look
count / exposure condition that forces the suite-refresh review BEFORE the next
look; the refresh design rule (add strata before replications when outcomes
cluster). Miniature example ~10 rows.

### templates/COMPUTE_DEMAND_LEDGER.md (governing: 11)
Purpose: the demand instrument for purchase decisions. Columns: date | milestone/
project | node (owned/rented + device class) | purpose | device-hours (authoritative
clock stated) | spend | notes (honest NOT-RUN rows required). Monthly rollup table
(the trigger reads this). Purchase-trigger block: the pre-committed trigger
condition (template placeholder + guidance), what fires on trigger (benchmark-chosen
minimal config), and the re-verify-prices-at-order-time rule. Miniature example.

### templates/PREDICTION_LEDGER.md (governing: 04)
Purpose: calibration of "is this experiment worth running?". Columns: date |
experiment | primary metric | predicted (point + interval) | actual | inside
interval? | surprise notes. Scoring block: coverage rate; systematic bias notes;
the ~handful-of-entries rule before the gate becomes empirical. Miniature example.

### templates/OPERATIONAL_HANDOFF.md (governing: 12, 02)
Purpose: the operational-state document a new operator (or future you) needs.
Sections: system inventory (what runs where: services, ports, versions — placeholders);
execution-system identities in force; environment gotchas & their workarounds (each:
symptom → cause → rule); verification commands (executable, with expected output);
data stores & their roles (authoritative/RAG/working/trajectories/learned); active
experiments & their states; standing rules in force; contacts/ownership. Miniature
example ~20 lines.

### templates/METHOD_DECISION_RECORD.md (governing: 00; feeds CHANGELOG)
ADR-style: ID & date; status (proposed/adopted/rejected/superseded); context (the
decision forced); decision; evidence (with source IDs / case links); consequences
(incl. what becomes harder); review date; supersedes/superseded-by. Miniature
example: adopting cluster-robust primary inference.

## B. Case studies (playbook/examples/CASE-*.md) — project material ALLOWED

Fixed format (H2 sections): **Situation** / **Decision faced** / **Evidence** /
**What happened** / **The generic lesson** / **What would NOT have worked** /
**References**. The first four sections are WHAT HAPPENED IN THIS PROJECT (real
numbers, real names, real dates); "The generic lesson" is the extraction (state the
portable rule + which chapters/templates encode it); "What would NOT have worked"
only where the record shows it. Header: title; then a one-line frame: "Real
empirical case from the FIS project (Fintech Integration Sandbox), a realistic
synthetic fintech-operations laboratory used to develop this playbook's
methodology." + source ID (INT-CASE-00N) + date range + links to the chapters that
cite it. ~120–200 lines each. Cite external corroborating sources by ID where the
lesson has literature support. Numbers here are REQUIRED — this is where they live.
Do not fabricate: extract from the named evidence docs; if a specific number is not
in the record you read, write "(not recorded)" rather than inventing.

| ID | File | Core evidence to read |
|---|---|---|
| CASE-001 | consequence-bearing-tolerances | docs/R6_EXPERIMENT_CONTRACT.md (§6 calibration + escape hatch), docs/R6_MODERN_LOCAL_SPECIALIST_REFRESH_REPORT.md, research 08-20 §2.2 Findings 1–2, docs/current/AI_SYSTEMS_LAB_MASTER_PLAN.md §3 |
| CASE-002 | clustered-eval-effective-n | research 08-20 §2.2 Finding 5 + §2.1 Miller block, docs/current/EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md §7 |
| CASE-003 | learned-router-leakage | docs/R5_LEARNED_ROUTING_REPORT.md, docs/R5_EXPERIMENT_CONTRACT.md, research 08-20 §2.1 cascade block |
| CASE-004 | harness-defects | docs/SUITE_V3_RELEASE_REPORT.md, docs/task-ontology.md §5, docs/experiment-log.md, research 08-20 §1 + Appendix A |
| CASE-005 | hardware-purchase-discipline | research 08-20 §3 (incl. §3.5 + Appendix C hardware adversary), docs/R6_PERFORMANCE_AUTOPSY.md |
| CASE-006 | token-budget-confounding | docs/experiment-log.md (R3/R3b entries), research 08-19 §4 token-budget row, research 08-20 §2.2 Finding 4 |
| CASE-007 | deterministic-cascade-gate | docs/routing-experiments.md (R4), research 08-20 §2.1 cascade literature block (novelty claim) |
| CASE-008 | transport-serialization-defect | docs/routing-experiments.md (R1/R0.1), research 08-20 §2.1 (ML Test Score Monitor-3 framing) |
| CASE-009 | suite-versioning-criteria-drift | docs/SUITE_V3_RELEASE_CONTRACT.md + SUITE_V3_RELEASE_REPORT.md, research 08-20 §2.1 EvalGen block |
| CASE-010 | pilot-optimism-collapse | docs/experiment-log.md (E2 pilot→full), research 08-20 §2.1 (fluke guards, E6b) |
| CASE-011 | diagnostic-gate | docs/current/NEXT_STEP_M0.md, docs/current/AI_SYSTEMS_LAB_MASTER_PLAN.md §10 (M0 row) |
| CASE-012 | restart-instability-paired-controls | docs/HANDOFF.md, docs/experiment-log.md, docs/current/EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md §8, research 08-20 §2.1 nondeterminism block |

## C. Synthetic worked examples (playbook/examples/SYNTH-*.md) — GENERIC ONLY

Purpose: show the playbook applied to materially different project shapes. Every
project, company, number is INVENTED (state so in a header line: "Synthetic worked
example — all names and numbers invented."). ~90–150 lines each. Format (H2):
**Profile summary** (the PROJECT_PROFILE fields that matter, compact table) /
**Archetype & rigor tier** (which QUICKSTART route fires and why — by profile FACTS)
/ **The decisive moves** (3–6 numbered decisions with the chapter rules they apply)
/ **What was skipped and why** (legitimately, per tier/archetype) / **Outcome**
(plausible, modest; include costs/effort at round numbers) / **Chapter trail** (the
links used). Each SYNTH must exercise at least one gate/tripwire meaningfully.

| ID | File | Shape & the point it proves |
|---|---|---|
| SYNTH-01 | api-only-assistant | Greenfield support assistant on managed APIs only; eval-first bootstrap; judge needed (open-ended) → calibration protocol path; skips 06/09/11-hardware at start |
| SYNTH-02 | private-local-deployment | Privacy-mandated on-prem document processing; 02 identity + reproducibility probes early; runtime regime choice (determinism); capacity fit probes |
| SYNTH-03 | high-throughput-extraction | Millions of structured extractions/day; deterministic grading; operating-point selection + goodput; cost/successful-task economics drives model size down |
| SYNTH-04 | tool-calling-agent | Internal ops agent with write actions; tool-contract design (G19), permission gating, injection threat model (13); observe-only graduation before automation |
| SYNTH-05 | cost-reduction-routing | Existing frontier-API system, quality bar established; oracle analysis → deterministic gate cascade → break-even; TRIPWIRE: learned router fails leakage audit and is refused |
| SYNTH-06 | training-rejected | Team wants to fine-tune; diagnosis lands RC-3 (unreachable evidence) + RC-6 (spec gap); ladder rungs 2+4 close the gap; training refused with the evidence stated |
| SYNTH-07 | training-justified | Narrow format-adherence gap survives rungs 0–6; data demonstrably contains the skill; rig-first; minimum-n ablation; full-suite forgetting gate passes; ToS check done |
| SYNTH-08 | high-stakes-audited-deployment | Regulated decision support (Tier 3); 13 instantiated at intake; pass^k reliability; shadow→canary with human approval; rollback rehearsal |
| SYNTH-09 | inconclusive-result | A/B of two candidates lands inside MDE; INCONCLUSIVE verdict written; pre-registered descriptive vocabulary licenses "competitive"; decision made on cost instead; suite-refresh trigger noted |
| SYNTH-10 | hardware-rent-vs-buy | Demand ledger vs purchase impulse; H* break-even worked with invented numbers; trigger defined; benchmark-first; the purchase correctly does NOT happen yet |

## D. examples/README.md — written by the lead in the edit pass; agents skip it.
