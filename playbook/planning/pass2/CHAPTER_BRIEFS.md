# Pass-2 Chapter Briefs (build scaffolding)

Read together with AUTHORING_CONVENTIONS.md (skeleton, callouts, taxonomy, rigor
dial, portability boundary). Per chapter: scope, must-cover list, assigned G-gaps
(each ends COVERED / COVERED-AS-DOCTRINE-NOT-YET-EXERCISED / EXPLICITLY-OUT-OF-SCOPE-FOR-0.1,
stated in-chapter in a visible "Gap dispositions" note inside section 13 or the
relevant section), main source IDs, case links. Evidence pointers name repo docs the
DRAFTER may read for extraction — never cite repo paths in shipped text.

Global content sources every drafter may consult:
- playbook/planning/evidence_inventory.json (statements/antipatterns/cases keyed by doc set)
- docs/research/2026-08-19_NVIDIA_AI_Lab_Playbook_Research.md (vendor map)
- docs/research/2026-08-20_AI_Lab_Methodology_Hardware_Strategy.md (methodology/statistics/economics)
- docs/current/* (the project instantiation — extract procedures, quarantine numbers)
- playbook/planning/pass2/w1_verification.json (live source-verification results; cite as-of dates from it)

Chapter lengths: target 250–450 lines each (04, 03, 07 may run to ~550). Depth over
padding; every section earns its place or is reasoned N/A.

---

## 00_PRINCIPLES_AND_SCOPE (authored by lead — brief for reference)

Normative core: evaluate-first; evidence before intervention; the ladder (short
form); decision-quality over speed; frozen instruments + pre-registration;
fail-closed enforcement; INCONCLUSIVE legitimacy; measurement validity before
comparison; consumable held-out data; proportionality (rigor dial owner section);
what this playbook is not. Gap G2 (rigor sizing) primary home with 01.

## 01_PROJECT_INTAKE_AND_DECISION_CONTEXT

Scope: fuzzy request → PROJECT_PROFILE → decision context → archetype → first
actions. LABEL: much of this chapter is playbook synthesis — mark `(inference)`
honestly (thin-chapter rule).
Must cover:
- The intake question set (mirror templates/PROJECT_PROFILE.md's ~20 fields; spec
  list: business outcome, task population, criticality/failure cost,
  quality/reliability target, latency/throughput/SLA, privacy/security/residency,
  data/knowledge availability, tool/action permissions, model candidates, owned
  compute, rentable compute, managed APIs, capex budget, recurring budget,
  utilization/growth, staffing/time, deployment environment, observability,
  regulatory/compliance, existing evidence, stakes/consequence tolerance).
- "What decision will this evidence drive?" as the first question of any work item.
- Requirement → evaluation claim formulation (hand off to 03).
- Constraints inventory → hard vs soft constraints; kill criteria at intake.
- Archetype selection preview (the QUICKSTART tree is normative; summarize, link).
- Cold-start parameterization (G4 primary home): setting thresholds/gates with no
  incumbent and no history — procedure: (1) anchor on task consequence (rigor dial),
  (2) borrow external reference points as PRIORS clearly labeled non-binding, (3)
  run a calibration pilot sized for direction (not inference), (4) pre-register how
  the first real data will revise the parameter (amendment legitimacy, 04), (5)
  never let a placeholder threshold silently become policy (anti-pattern).
- Stakes/rigor-dial capture (G2 with 00).
- First-sprint contract: every archetype's first sprint ends at a frozen contract
  for the first real experiment (Tier-2+) or a written lightweight plan (Tier-1).
Gaps: G2 (with 00) COVERED; G4 COVERED.
Sources: EXT-EVAL-001/002 (criteria docs), EXT-OPS-002 (test rubric framing),
NV-AGENTICBLOGS-001 (evaluate-first), internal INT-CASE-011 (diagnostic-first).
Cases: CASE-011, CASE-005; WALKTHROUGH + SYNTH-01/02/08 as worked examples.

## 02_EXECUTION_SYSTEM_MODEL

Scope: the measurement-validity foundation.
Must cover:
- ExecutionSystem definition (verbatim from spec): model + artifact/quantization/
  adapter + runtime/provider + hardware/host + harness + context policy +
  retrieval/knowledge + tools + workflow + generation/reasoning budget +
  verifier/grader + environment. A comparison claim is about the frozen execution
  system unless one factor is explicitly isolated. Never collapse
  model/runtime/provider/harness/hardware into one label (anti-pattern:
  "the model got better" when the runtime changed).
- Frozen identity: pinning (artifact hashes, build digests, config, host identity),
  what change forces a new identity.
- Reproducibility boundaries are MEASURED then scoped: probe design (restart probe,
  concurrency probe, cross-host probe, provider-redeploy probe); scope comparability
  claims to the measured boundary (session/host/provider). Teach the probe, not any
  particular boundary conclusion. [CASE: CASE-012]
- Nondeterminism mechanisms (EXT-DETERM-001): batch/reduction-order variance,
  GPU-state sensitivity, KV-cache placement; batch-invariant modes cost throughput
  (opt-in in major runtimes as of verification date).
- Contemporaneous paired control requirement for causal claims across measured
  instability boundaries.
- Cross-node/rented placement: a rented instance holding one session per arm can
  satisfy a session-scoped rule; pre-register placement; verify artifact digests on
  the remote host.
- Quantize for the deployment target, not the dev box (vendor-format portability
  traps; e.g., formats locked to one GPU generation) [ADAPT: NV-NVFP4PLAYBOOK-001].
- Environment hazards: clock validity (virtualization skew — generic statement, e.g.
  containers/VMs/WSL2-class layers can skew monotonic vs realtime clocks; measure
  with dual stamps), interop mangling, PATH/binary resolution across layers.
Gaps: none primary.
Sources: EXT-DETERM-001, NV-EVALRECIPE-001 (pin containers/params/judges),
NV-WORKBENCH-001, EXT-PERF-003 (backend choice moves scores).
Cases: CASE-012, CASE-008.
Evidence: methodology report §2.1 nondeterminism package; HANDOFF gotchas;
playbook §8 (generalize).

## 03_EVALUATION_FOUNDATION

Scope: requirement → trustworthy, versioned eval. The instrument chapter.
Must cover:
- Requirement → evaluation claim → task ontology DERIVATION (G1 primary): procedure
  from external practice: (1) error-analysis-first — read real traces/tickets/logs,
  open-ended failure notes [EXT-EVAL-003]; (2) synthesize a closed category set with
  an explicit symptom-vs-root-cause split; (3) stratify by root-cause class not
  symptom; (4) define per-category evidence requirements; (5) expect criteria drift
  — criteria and ground truth co-evolve [EXT-EVAL-004]; version, don't mutate.
- THE canonical failure taxonomy (conventions §7) — normative statement lives here:
  categories-are-symptoms table pattern, RC-1..RC-12, cause→intervention mapping
  (07 consumes). Include a "deliberately ambiguous symptom" teaching point: some
  symptoms map to multiple causes by design; disambiguation via evidence IS the
  capability under test.
- Corpus design: representative sampling; stratification; distractor design
  (an action/label valid for no case is a measurable name-anchoring probe);
  absence-detection cases (correct answer = "nothing is wrong") to price
  confabulation; forbidden-claim scoring (harm-weighted assertions fail a case).
- Ground-truth design: generator-derived vs human-annotated vs judge-mediated;
  gold labels score but never choose (G16 with 04/13).
- Instrument validation: reachability/solvability ceilings MEASURED per stratum
  (a class scoring near zero is a ceiling problem until proven otherwise);
  weak-beats-strong inversion checks; cross-arm disagreement review; gold-answer
  gates; determinism checks; frontier-saturation check. Static integrity gates run
  full-corpus, protected from subsetting. [CASE: CASE-004]
- Non-generator instruments (G3): when there is no code-driven generator — human
  annotation protocols (dual-label + adjudication, agreement stats), sampled-audit
  ceilings (you cannot replay reachability; you can audit solvability on a sample),
  judge-mediated ground truth (only with the calibration protocol below). Mark
  which parts are doctrine-not-exercised.
- Deterministic graders vs LLM judges: decision rule by task shape — objectively
  verifiable output ⇒ deterministic grading MUST be preferred (judges ≈ chance on
  verifiable tasks [EXT-JUDGE-002]); open-ended/preference ⇒ judge with calibration.
- THE judge-calibration protocol (W7 deliverable, doctrine-not-exercised): sampling
  design vs human anchor set; chance-corrected agreement (κ, not raw %) with
  deflation warning [EXT-JUDGE-003]; bias audits (position, length, self-preference,
  style); rubric stability across paraphrase; domain-transfer check before reuse;
  drift monitoring + recalibration triggers; report κ + CI, never raw agreement
  alone. Include the MT-Bench domain caveat [EXT-JUDGE-001].
- Leakage/contamination: split isolation (disjoint generation seeds/sources),
  private held-out sets, canary strings for anything published [EXT-EVAL-007],
  contamination checks [EXT-EVAL-006]; train/eval separation.
- Suite versioning: versioned releases with release contracts
  (templates/EVAL_SUITE_RELEASE_CONTRACT.md), cross-suite comparison refusal,
  refresh triggers from the look ledger; criteria drift managed by release, never
  in-place edits [CASE: CASE-009].
- Volume-vs-curation contradiction (G20 part): present both positions
  [EXT-EVAL-001 vs EXT-EVAL-005] + decision rule (grading signal quality × item
  cost × stakes tier).
- Regression vs capability suites distinction.
Gaps: G1 COVERED; G3 COVERED (parts doctrine); G16 shared (state the boundary rule
here, mechanics in 04); G19 cross-ref (instrument-validation half; primary in 08);
G20 volume-vs-curation COVERED.
Sources: EXT-EVAL-001..007, EXT-JUDGE-001..003, NV-EVALSDK-001,
NV-TOOLCALLTUTORIAL-001, EXT-TESTBED-001/003, NV-GARAK-001 (calibration-bag
z-score pattern).
Cases: CASE-004, CASE-009, CASE-003.

## 04_EXPERIMENT_DESIGN_AND_STATISTICS

Scope: contracts, splits, statistics, stopping. The decision-quality chapter.
Must cover (statistics canon: conventions §9; derivations live in
references/STATISTICS_FORMULAS.md — statements + usage here):
- Splits and look discipline: iterate/qualify/confirm split roles (do NOT prescribe
  sizes — G18 honesty: generic sizing comes from power analysis, not tradition);
  spend semantics (a held-out split is spent at the first executed case);
  look ledger; refresh triggers.
- Experiment contracts: pre-registration, freeze (commit-before-run), amendment log
  append-only; the contract executes, the owner does not improvise mid-run (DSMB
  principle [EXT-STOPPING-002]); roles (scientific owner vs executor).
- Consequence-bearing tolerances (THE portable invention): every pre-registered
  tolerance names ABORT / RECALIBRATE / PROCEED-WITH-DECLARED-CEILING (+ projected
  cost), enforced fail-closed in the runner; evaluated by curtailed exact counting.
  A tolerance without a consequence is an unpriced escape hatch (H-class
  anti-pattern) [CASE: CASE-001].
- Screening vs inference; elimination rule (no candidate withdrawn on a margin below
  the pilot's own MDE); racing/ASHA stratum-balanced [EXT-STOPPING-003].
- Curtailment: certainty curtailment + three guards; interval-only partial
  reporting; paired-comparison firewall. Speed-rationale anti-pattern.
- Sequential testing [REJECTED conditional]: i.i.d.-calibrated sequential rules
  inadmissible under clustered, ordered execution; independence check first
  [EXT-STOPPING-001] [CASE: CASE-002].
- Clustering: unit identification, ICC → DEFF → N_eff → MDE chain [EXT-STATS-001];
  cluster-robust paired inference primary under material clustering; McNemar
  secondary anti-conservative; power grows with number of clusters, not
  replications within clusters (suite-design consequence).
- MDE statement + INCONCLUSIVE verdict + pre-registered descriptive vocabulary;
  MDE ≤ discordance constraint; null ≠ equivalence [CASE: CASE-010 pilot optimism].
- Paired designs: same-item cross-arm comparisons use paired SEs (free power).
- pass^k for stochastic arms [EXT-AGENT-001]; execution-order design (interleaved/
  round-robin ordering so prefixes are representative — measurement-neutral).
- Prediction ledger (templates/PREDICTION_LEDGER.md).
- Amendment legitimacy (G15): rule distinguishing pre-registered-procedure-derived
  amendments from post-hoc threshold shopping: legitimate iff (1) the amendment
  procedure itself was pre-registered, (2) derived only from iterate-split evidence
  via formulas fixed at freeze, (3) committed before any qualify/confirm execution,
  (4) direction-of-benefit analyzed and disclosed, (5) a skeptical-reader note is
  mandatory when an amendment moves in the direction of permitting a pass.
- Gold-label usage boundary (G16): gold labels/ground truth may SCORE outcomes and
  fit pre-registered calibration procedures on the iterate split; they may never be
  readable by the system under test at inference time, and never select/route/tune
  anything on qualify/confirm splits. State as an operational rule with an
  enforcement note (role/permission isolation, 13).
- Diagnostics inside vs outside the fail-closed machinery (G17): default = extend
  the state machine with a non-promotable diagnostic run kind (results ledgered,
  cryptographically non-promotable) rather than running outside the record; a
  relaxed unrecorded lane is the defect class provenance exists to prevent.
  Trade-off table.
- Verdict vocabulary: CONFIRMED / REFUTED / INCONCLUSIVE / RANKED.
- Contemporaneous paired controls under session nondeterminism (with 02).
Gaps: G15 COVERED, G16 COVERED, G17 COVERED, G18 COVERED (all statistical
generality carried by external sources, stated).
Sources: EXT-STATS-001, EXT-STOPPING-001/002/003, EXT-AGENT-001,
NV-EVALSDK-001 (as productized McNemar/power/INCONCLUSIVE — FOLLOW ops),
EXT-AMAZON-LLMSTATS-001, NV-MODELOPTRESEARCH-001 (progressive subsets + ordering
bias).
Cases: CASE-001, CASE-002, CASE-010, CASE-011.

## 05_MODEL_RUNTIME_AND_HARNESS_SELECTION

Scope: design-time selection (the gap no vendor fills).
Must cover:
- Bounded candidate-set construction across (spec list): capability, family
  diversity, size, quantization, context, tool use, structured output, licensing,
  data policy, deployability, hardware fit, APIs, runtime compatibility, serving
  ecosystem, fine-tuning support, observability, cost, latency, complexity,
  reproducibility. Procedure: profile-derived hard filters → diversity-aware
  shortlist (3–6) → screening protocol (04) → frozen comparison.
- Screening protocol integration (04's rules; selection metric must be resolvable
  at pilot MDE).
- Runtime/engine selection: NO universal winner (G20 primary for the
  runtime-criterion contradiction). Teach the regime criterion: determinism/
  provenance regime (single-slot, pinned builds, grammar enforcement, wide
  quantization formats) vs throughput regime (continuous batching, tensor
  parallel, production metrics vocabulary) vs managed-provider regime (no
  weight custody; provider-redeploy reproducibility hazard) vs hybrid. Map common
  engines to regimes as EXAMPLES with as-of date, not verdicts.
- Harness/agent-framework selection and evaluation:
  *status: doctrine — not yet exercised* — dimension checklist (tool-call fidelity,
  context management, trajectory observability, determinism hooks, permission
  model, cost overhead, version churn), same-eval-different-harness comparison
  design, harness version pinned as part of execution-system identity.
- When selection is premature vs overdue (eval trust precedes selection; selection
  precedes optimization).
- Model-diversity principle: silent-failure profile differs across families —
  complementary arms enable rescue routing (08).
Gaps: G20 runtime-criterion COVERED.
Sources: NV-SERVINGSTACKS family (w1), NV-NAT-001, NV-NEMOPLATFORM-001,
EXT-DETERM-001, NV-INFERBENCH-001.
Cases: CASE-006 (confound in selection), CASE-007 (complementarity).

## 06_INFERENCE_PERFORMANCE_AND_CAPACITY

Scope: performance measurement methodology; capability evals stay separate.
Must cover:
- FOLLOW the vendor-mature core [FOLLOW: NV-INFERBENCH-001]: metric definitions
  (TTFT, ITL/TPOT, e2e latency, system vs per-user TPS), use-case ISL/OSL pairs,
  warmup, request-count discipline, concurrency-over-request-rate sweeps,
  latency-throughput curve, operating-point selection. AIPerf-class client tools;
  one tool + one metric-definition set across all tiers (definitions differ across
  tools; numbers are not comparable).
- What vendors omit (playbook IP): single-user/interactive regime (concurrency=1
  profiles), clock validity (dual clocks: realtime + monotonic; authoritative clock
  per metric declared in contracts), effective-bandwidth accounting
  (achieved vs spec; memory-bandwidth-bound decode arithmetic: tokens/s ≈
  effective_BW / bytes_per_token_pass — worked neutral example), capacity fit
  probes (context/cap fits VRAM before an experiment depends on it), k6-style test
  taxonomy labels [ADAPT: EXT-PERF-002], goodput concept [REFERENCE: EXT-PERF-001].
- The performance autopsy (templates/PERFORMANCE_AUTOPSY.md): standing post-run
  forensic procedure — multi-source timing reconstruction, critical-path
  identification, counterfactual costing ("what would N nodes / faster GPU have
  saved"), clock-forensics cross-checks, cost-bucket attribution [CASE: CASE-005].
- Finding-vs-waste decision test (G14 primary): a dominant cost bucket is a FINDING
  (object of study) iff it is task-intrinsic and moves the decision the experiment
  serves; it is WASTE (overhead to eliminate) iff it is harness/infrastructure
  friction orthogonal to the question. Test: (1) does the bucket change the
  measured comparison? (2) would eliminating it change the decision or only the
  bill? (3) is it reproducible across the deployment target? Route findings to the
  contract's analysis plan; route waste to engineering backlog with a priced
  ticket.
- Multi-tenant/SLA behavior (G9): EXPLICITLY-OUT-OF-SCOPE-FOR-0.1 as validated
  methodology — state the scope boundary, give the k6+SLO-threshold skeleton +
  vendor pointers as REFERENCE, mark doctrine.
- Prompt-vs-decode split; percentile discipline (p50/p95/p99); power measurement
  pointer to 11.
Gaps: G14 COVERED; G9 EXPLICITLY-OUT-OF-SCOPE-FOR-0.1 (skeleton + pointers only).
Sources: NV-INFERBENCH-001, NV-SPARKPERF-001 (concurrency=1 template, REFERENCE),
EXT-PERF-001/002/003, NV-DYNAMOAICONFIG-001.
Cases: CASE-005, CASE-006.

## 07_OPTIMIZATION_AND_INTERVENTION_LADDER

Scope: the operational hinge — "you have a measured gap; select the intervention."
Must cover:
- The ladder operationally (conventions §7): per rung — what it fixes (RC classes),
  evidence required to descend, what blocks movement, cost class, cheap diagnostic
  first.
- Diagnostic gates: cheap paired probes that decide an expensive experiment's fate
  BEFORE it runs; design pattern: (1) name the hypothesis the expensive experiment
  assumes, (2) find the cheapest observable that discriminates it, (3) pre-register
  decision bands (GO / re-scope / DROP) with data-sufficiency precedence — an
  underpowered diagnostic returns INCONCLUSIVE, never GO; completion alone never
  produces GO, (4) run paired/controlled, (5) the diagnostic's verdict binds
  [CASE: CASE-011].
- Generation/reasoning-budget calibration as a PROCEDURE (rung 5): pilot the
  generation-length distribution on the iterate split → set cap above a
  pre-registered quantile (e.g., p99) with headroom → truncation-rate tolerance
  WITH consequence → truncation telemetry (finish reasons persisted) → convert-or-
  close experiment at larger budgets when truncation bounds outcomes; beware the
  selection effect (cases that complete at a small cap are the easier ones;
  conversion at a larger cap is an upper bound, not a given) [CASE: CASE-006].
- Prompt/workflow optimization discipline: one factor per arm, controlled variants,
  pre-registered adoption rules (fluke guards), hypothesis-space enumeration before
  variant spam.
- Quantization with acceptance gates [ADAPT: NV-QADNEMOTRON-001,
  NV-MODELOPTQUANT-001, NV-NVFP4PLAYBOOK-001]: recovery-vs-higher-precision gate on
  YOUR task evals (vendor demonstrated practice: >99% median recovery to ship
  PTQ-only; 95–99% deliberate when a recovery stage is planned — as-of-dated,
  demonstrated-not-doctrine); escalation ladder (disable KV-cache quant → partial/
  mixed precision → weight-only alternatives → quantization-aware recovery);
  format portability trap (deployment target rule, 02); vendor decision-page lag
  callout (date-weight vendor guidance; a vendor's decision page can lag its own
  flagship practice by ~a year — G20 item).
- When to stop optimizing: opportunity-cost test; the ladder's evidence bar for
  descending to training (09) — a residual, taxonomy-identified gap that cheaper
  rungs demonstrably cannot close + data that demonstrably contains the skill.
- Finding-vs-waste cross-ref (06, G14); G17 cross-ref (04).
Gaps: G14 shared (COVERED with 06).
Sources: NV-AGENTICBLOGS-001 (evaluate-first), NV-QADNEMOTRON-001,
NV-MODELOPTQUANT-001, NV-MODELOPTRESEARCH-001, EXT-FT-001 (ladder direction),
EXT-STOPPING-003.
Cases: CASE-011, CASE-006, CASE-001.

## 08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING

Scope: context/retrieval/tools engineering + multi-tier routing.
Must cover:
- Evidence reachability as a designed property: every fact the task requires must
  be reachable through the deployed tool set from what the system can know at call
  time (two-phase addressing trap: evidence addressed by an identifier the system
  cannot learn without another call); reachability MEASURED not argued (03's
  ceiling machinery); tool results must not cross task/tenant boundaries.
- Tool-contract design (G19 primary): schema explicitness; deterministic result
  ordering (sort keys stated); cohort/tenant keying; pagination/limit semantics;
  addressability (selectors the caller can actually know); byte-level transport
  fidelity (serialization layers can reorder/reformat and break grammar-constrained
  consumers — verify byte equivalence through proxies) [CASE: CASE-008];
  permissioning (least privilege; ground-truth isolation 13); versioning of tool
  contracts as part of execution-system identity.
- Context policy: budget allocation, retrieval integration, context-rot hygiene;
  structured evidence presentation.
- Routing/cascade design: deterministic verifier gates vs learned routers —
  decision rule: a deterministic gate on verifiable output signals is the DEFAULT
  when a task-level verifier exists (published literature is all learned gates;
  a verifier-gated deterministic cascade is a validated pattern [CASE: CASE-007]);
  escalation semantics vocabulary [ADAPT: NV-SWITCHYARD-001]: weak-first,
  judge-on-actual-output, confirmation streaks, latching, fail-open vs fail-closed
  choice per consequence class.
- Learned-router admission bar (leakage audits): class/group-identity ceiling —
  features that encode WHICH stratum an item belongs to, not the intended signal;
  leave-one-group-out validation mandatory; OOD caution [EXT-ROUTE-001 RouteLLM];
  observe-only before action (G13) [CASE: CASE-003].
- Routing economics: break-even rule (minimum offload share ≈ gate_cost /
  (strong_cost − weak_cost), worked neutral example) [ADAPT: EXT-SWITCHYARD-001];
  false-negative cost accounting (un-escalated failures are the expensive ones);
  oracle analysis (perfect-routing upper bound before building a router);
  when routing is NOT worth it (low volume, small cost delta, weak verifier).
- Routing-input taxonomy (G11 primary): unify inputs into task-intrinsic features
  (content, class, complexity signals) × system-state features (queue depth,
  budget burn, tier health) × policy features (stakes tier, SLA, permissions);
  which inputs are admissible at which decision points (gold-label boundary!);
  document as a table.
- Multi-tier (3+) routing: compose two-tier edges with explicit escalation
  semantics per edge; each edge carries its own break-even.
- Graduation criteria observe-only → automated action (G13 primary): a learned or
  automated routing/mutation component graduates only when (1) leakage audit
  passed, (2) observe-only shadow period with measured agreement/regret,
  (3) pre-registered promotion gate on qualify split, (4) rollback path defined
  (10), (5) post-deployment monitoring plan exists (12). Table with thresholds as
  PARAMETERs.
Gaps: G11 COVERED, G13 COVERED, G19 COVERED.
Sources: NV-SWITCHYARD-001, EXT-SWITCHYARD-001, EXT-ROUTE-001, NV-SLMRESEARCH-001,
NV-NEMOCLAW-001 (REFERENCE).
Cases: CASE-003, CASE-007, CASE-008, CASE-004.

## 09_TRAINING_AND_DATA

Scope: the last rung. HONESTY RULE: state plainly that the playbook's own project
record has not yet exercised training (the ladder never reached it — itself a
methodology success); doctrine here = external literature + vendor mechanics +
playbook inference, labeled per source.
Must cover:
- Evidence threshold to train at all (from 07): taxonomy-identified residual gap
  (RC-10); cheaper rungs exhausted with evidence; training data demonstrably
  contains the skill; economics close (11).
- Rig-first principle: de-risk the PIPELINE (train→merge→quantize→serve→eval loop,
  end-to-end on a toy config with full provenance) before the model experiment;
  provenance schema must represent self-produced artifacts (dataset digest, base
  artifact, hyperparameters, seed, adapter hash, pipeline digests) BEFORE first
  training run.
- RAG/context-vs-training direction [EXT-FT-001]: strong-evidence for
  factual/citation tasks → retrieval first; conditions where FT wins (format/
  behavior/skill internalization, latency/cost at volume).
- Data: own-trace harvesting (system's own successful/failed trajectories scored
  against own ground truth); LEGALITY: provider-output training restrictions
  (verified as-of date; e.g., Anthropic Commercial Terms restrict training
  competing models on outputs without authorization [EXT-LEGAL-001]) — check the
  CURRENT terms of every provider in the loop, at training time, and record the
  check; model-license review for base weights (G7, with 13); contamination:
  training data must not touch qualify/confirm splits (canary + provenance);
  curation quality-over-quantity [heuristic; EXT-FT-007 research-only].
- Minimum-n: NO universal folklore — treat sample size as an ABLATION (pre-
  registered ladder, e.g., small/medium/large rungs against the iterate split under
  one-look discipline); LIMA's n≈1,000 is style-alignment scope, not a narrow-fix
  minimum [EXT-FT-002 caveat] — field gap stated.
- Method defaults [FOLLOW: EXT-FT-003/004/005 as-of-dated]: LoRA/QLoRA VRAM floors
  (cite ranges, as-of); all-linear-layer LoRA, moderate rank, α≈2r, LR ~10× full-FT
  as starting points (PARAMETER, calibrate); LoRA-vs-full-FT quality regimes
  contradiction kept visible (reconciled by regime, state the boundary).
- Forgetting: full-suite regression gate MANDATORY (never just the target slice)
  [EXT-FT-006]; merging does not reliably fix forgetting.
- Post-tune evaluation: paired stats vs base (04); deployment gate (10); seeds +
  provenance; RL evidence bar (higher: verifier quality + reward-hacking audit —
  doctrine-not-exercised, brief).
- Rejection criteria: when training is refused (SYNTH-06) and when justified
  (SYNTH-07).
Gaps: G7 shared with 13 (COVERED); minimum-n field gap stated.
Sources: EXT-FT-001..007, EXT-LEGAL-001, NV-FINETUNESTACK-001, EXT-UNSLOTH-001,
NV-RTXAIGARAGE-001, NV-CURATORDESIGNER-001, NV-TOOLCALLTUTORIAL-001.
Cases: CASE-011 (gate before spend), CASE-006 (budget-before-weights lesson).

## 10_DEPLOYMENT_AND_OPERATIONS

Scope: promotion to production. THINNEST internal record: distinguish established
SRE/progressive-delivery practice (consensus, external) from AI-specific doctrine
(inference / doctrine-not-exercised). Say so at the top.
Must cover:
- Promotion pipeline: offline confirm → shadow (mirrored traffic, no user impact;
  comparison design) → canary (small real fraction) → progressive rollout →
  steady state; each stage's entry/exit gates.
- SRE restraint doctrine [ADAPT: EXT-OPS-001]: simplest canary model that meets
  objectives; ONE canary at a time; causally attributable metric set (small);
  aggregation window ≪ canary duration; no over-invested canary statistics.
- AI-specific deltas (inference, labeled): nondeterminism → paired-shadow designs
  compare distributions not cases; quality metrics need verifier-in-the-loop or
  sampled human audit; execution-system identity must be pinned per stage
  (a provider-side model update mid-canary invalidates it).
- Rollback as a DESIGNED path (G10 primary): pre-deployment rollback rehearsal;
  what triggers rollback (pre-registered thresholds with consequences — 04's
  machinery applied to ops); state/version compatibility (in-flight requests,
  cache/KV state, adapter versions); incident-response runbook skeleton (detect →
  freeze promotions → rollback decision owner → comms → postmortem feeding 12);
  doctrine-not-exercised marker.
- One-change-at-a-time promotion; human approval gates by stakes tier.
- Serving-stack promotion notes: keep vendor mechanics as REFERENCE (KServe/Knative
  revision splitting exists; many native paths are plain rolling updates with
  manual rollback — verify your stack's actual rollback story before relying on
  it; as-of-dated).
- Multi-tenant/SLA (G9): out-of-scope-for-0.1 statement mirrored from 06.
- Security/privacy gates at promotion (13 cross-ref); human approval (rigor tier).
Gaps: G10 COVERED-AS-DOCTRINE-NOT-YET-EXERCISED; G9 EXPLICITLY-OUT-OF-SCOPE-FOR-0.1.
Sources: EXT-OPS-001, EXT-OPS-002, NV-NIMOPERATORCANARY-001, NV-DGXCLOUD-DEP-001
(destination churn caution).
Cases: CASE-007 (the production routing pattern), CASE-012 (identity pinning).

## 11_ECONOMICS_HARDWARE_AND_CLOUD

Scope: local vs cloud vs API as a measured decision.
Must cover (all formulas: symbols, units, neutral worked example; NO current prices
as doctrine; snapshot prices only as-of-dated illustrations; re-verify at order
time — prices in a supply-crunch regime are floors with weeks of shelf life):
- Decision structure: existing hardware vs purchase vs rental vs managed inference
  vs frontier APIs vs hybrid — decision tree keyed on: privacy/residency
  constraints, demand (measured GPU-hours/month), latency needs, capacity needs
  (VRAM/context), budget structure (capex vs opex), staffing.
- Demand ledger BEFORE capital (templates/COMPUTE_DEMAND_LEDGER.md): GPU-hours/
  month + spend, honest NOT-RUN rows; within-run utilization ≠ fleet demand
  (anti-pattern: justifying purchase from busy-percentage during runs).
- Pre-committed purchase trigger: define the trigger BEFORE wanting the hardware
  (e.g., K consecutive months above spend X, or a committed always-on serving
  requirement); on trigger, buy the benchmark-chosen minimal configuration; a
  cheap rented benchmark on the pinned artifact measures the one number the
  purchase turns on [CASE: CASE-005].
- Rent-vs-buy break-even: H* = (P − S) / (L·52·(R − TDP_kW·e)) hours/week — define
  symbols (price, salvage, lifetime years, rental rate, power draw, electricity),
  worked neutral example; honest-utilization warning.
- Amortization + energy/ops; cost/request, cost/successful task, expected
  cost/solve (cost ÷ pass-rate — ties economics to evals); latency-dollar
  trade-off; routing break-even (08 cross-ref); parallel-node critical-path
  benefit (marginal node value = overlap captured; measure the critical path
  before buying parallelism — second node can be worth hours, third can be worth
  zero) [CASE: CASE-005]; capacity-vs-bandwidth constraint classes
  (capacity-bound: fit/residency/context; bandwidth-bound: serial decode; they
  buy different hardware).
- Cloud tiers: secure vs community/preemptible; data-exposure pricing (private
  corpus on rented hosts — policy by stakes tier); per-milestone rental pattern.
- Market-snapshot discipline: benchmark provenance (community numbers carry
  25–55% run-to-run spread — verify methodology), price-bubble discipline
  (deliberately-unspent-capital is an active decision), vendor TCO assumptions
  (datacenter formulas assume datacenter scale — G-lesson).
- API economics: $/M-token chains [REFERENCE: NV-COSTTCO-001], caching, budget
  caps as consequence-bearing tolerances.
Gaps: none primary (hardware policy = B/C classes per plan §5 B8).
Sources: EXT-HW-001 (snapshot, as-of), NV-COSTTCO-001, EXT-SWITCHYARD-001,
NV-LEPTONBREV-001, EXT-FT-003/004 (VRAM floors → sizing).
Cases: CASE-005; SYNTH-10.

## 12_OBSERVABILITY_LEARNING_AND_PROMOTION

Scope: experimentation telemetry floor (vendors document production, not
experimentation) + the learning loop.
Must cover:
- The experimentation telemetry floor (playbook IP): run lifecycle events
  (signal-safe start/end), per-invocation stats (prompt/decode token counts, TTFT,
  finish reason), dual-clock stamps + authoritative-clock declaration, server/
  engine logs preserved, resource samplers on long runs, config snapshot per run.
  Rationale: post-run forensics (06 autopsy) is impossible without it; land the
  floor BEFORE long runs.
- The generic minimum trajectory record (spec list, as a table): task/trace ID,
  execution-system identity, artifact refs, prompt/context, retrieval results,
  tool calls+results, permissions in force, output, verification outcome, final
  outcome, latency, token counts, cost, clock stamps, runtime/harness versions,
  capability config, mutations, human feedback, deployment stage.
- Data-plane separation: authoritative business data ≠ RAG knowledge ≠ working
  state ≠ trajectories ≠ learned assets — separation table (who writes, who reads,
  retention, privacy class).
- Production observability baseline [ADAPT: NV-NIMOBSERVABILITY-001]: metrics
  endpoint + engine metric vocabulary, distributed tracing (W3C traceparent),
  structured logs; adopt ONE metric vocabulary across tiers.
- Telemetry-pipeline correctness (G12 primary): who audits the instruments'
  instruments — cross-source consistency checks (two clocks, client-vs-server
  token counts, events-vs-logs reconciliation), synthetic-span injection,
  clock-skew probes, telemetry regression tests; a telemetry defect discovered
  post-hoc invalidates published numbers → treat telemetry changes like suite
  changes (versioned).
- Production failure harvesting: hold out annotated production examples for
  regression [EXT-OPS-002 Monitor-7]; failure → eval candidate → (ladder order)
  retrieval fix → training data candidate; privacy filter before harvest (G6, 13).
- Drift + monitoring of learned/routed components (G5 primary,
  doctrine-not-exercised): monitor input distribution vs eval distribution,
  escalation/routing rates, verifier-pass rates, per-stratum outcomes; retraining/
  recalibration triggers pre-registered (thresholds with consequences);
  graduation-reversal (de-automation) condition.
- Periodic methodology audit: rubric-based self-audit (minimum-across-categories
  scoring) [ADAPT: EXT-OPS-002] annually or per-major-release.
- The improvement loop closure back to 03 (suite refresh triggers).
Gaps: G5 COVERED-AS-DOCTRINE-NOT-YET-EXERCISED; G12 COVERED.
Sources: NV-NIMOBSERVABILITY-001, EXT-OPS-002, NV-DATAFLYWHEEL-001 (deprecated
loop design, REFERENCE with trap note), NV-ATIF-001.
Cases: CASE-005 (telemetry made the autopsy possible), CASE-012 (clock forensics).

## 13_GOVERNANCE_PROVENANCE_AND_SECURITY

Scope: the record of record + what must never be reachable.
Must cover:
- Provenance: tamper-evident record of record (hash-chained append-only registry;
  frozen contracts bound by content hash; append-only amendment logs); execution-
  system digests; dashboards (MLflow/W&B-class) MAY mirror, never replace
  [REFERENCE: EXT-OPS-003 — none of the mainstream tools documents
  tamper-evidence]; lineage chain dataset→run→artifact→eval→deployment.
- Fail-closed runners: unregistered/unfrozen work refuses to run at Tier 2+;
  diagnostic run kinds ledgered non-promotable (G17 cross-ref 04).
- Ground-truth isolation: answer keys unreachable from any model-facing surface —
  two-layer enforcement (permission/role isolation + reachability tests);
  gold-label boundary (04 G16) enforced structurally.
- Clean-room boundary: what must never enter the system (proprietary third-party
  material, unlicensed data, secrets); employer-IP hygiene for consultants.
- Data legality: training-data authorization (provider-output restrictions
  [EXT-LEGAL-001], as-of-dated, re-verify per project); model-license review for
  base weights (G7 primary): license identity recorded at acquisition (content
  hash + license text snapshot), permitted-use check (commercial, fine-tune,
  redistribute, output ownership), attribution obligations, license-change watch.
- PII/privacy in telemetry & trajectories (G6 primary,
  doctrine-not-exercised where unexercised): classification of trajectory fields
  by privacy class; collection minimization; redaction/pseudonymization before
  harvest (12); retention limits; residency constraints from PROJECT_PROFILE;
  subject-rights implications of append-only records (design: hash-chain the
  RECORD, store payloads separably deletable).
- Tool-calling security threat model (G8 primary, doctrine-not-exercised):
  prompt injection via tool outputs/retrieved content; least-privilege tool
  permissions; write-action gating (human approval by stakes tier); sandbox/
  credential custody; audit trail of tool invocations; injection red-teaming
  [REFERENCE: NV-GARAK-001]; secrets never in prompts/logs.
- Publication hygiene: canary strings in anything published; no eval-set text in
  public artifacts; benchmark-provenance honesty.
- Auditability: everything above must be demonstrable to a third party (audit
  = replay the chain).
Gaps: G6 COVERED (parts doctrine), G7 COVERED, G8 COVERED-AS-DOCTRINE-NOT-YET-
EXERCISED.
Sources: EXT-LEGAL-001, EXT-OPS-003, NV-LINEAGEREGISTRY-001, NV-GARAK-001,
EXT-EVAL-007, NV-WORKBENCH-001, NV-NEMOTRONCC-LICENSE-001.
Cases: CASE-003 (leakage), CASE-009 (record discipline), CASE-001 (fail-closed).

## 14_DECISION_TREES_AND_CHECKLISTS (authored by lead)

Curated operational condensation of 00–13 — NOT independent authority; every gate/
tree/checklist carries its source-chapter reference. Release consistency check: a
table mapping every entry → source chapter+section, verified each release.

## Front matter (lead-authored; briefs for completeness)

- README: what/who/15-min quickstart/lifecycle map/"I need to…" navigation/
  project-type reading paths/templates/vendor recipes/references/version+changelog.
- QUICKSTART: profile → archetype tree (routes on FACTS: named profile fields) →
  per-archetype: entry path, skippable-at-start, mandatory templates by rigor tier,
  first three actions, global tripwires ([STOP CONDITION] list). Default lifecycle
  diagram (spec's 14-step flow). First three actions visible without reading the
  book.
- GLOSSARY: canonical definitions; chapters link, never redefine.
- CHANGELOG: 0.1.0 entry — what/why/evidence.

## references/

- STATISTICS_FORMULAS.md: derivations + worked neutral calculations for: SE for
  binary scores; clustered SE / ICC estimation (ANOVA + paired-difference forms);
  DEFF/N_eff; MDE (McNemar discordant-pair form + cluster-robust form; the
  MDE ≤ pd constraint); paired-difference SEs; power for proportions; curtailment
  arithmetic (certainty bound + count-to-k); pass@k unbiased estimator vs pass^k
  (with collapse illustration); sequential-admissibility conditions (why i.i.d.
  calibration breaks under clustered ordered data — α-inflation mechanism);
  break-even formulas (routing offload; rent-vs-buy H*); binomial margin-of-error
  by sample size (progressive-subset table pattern); prediction-interval scoring.
  Every derivation: assumptions box + "when this breaks".
- VENDOR_RECIPE_NOTES.md: per-recipe adaptation notes for every FOLLOW/ADAPT
  source (what it solves, what it does not, required project validation, version
  pins, as-of dates, deprecation traps) — from w1_verification.json + the source
  seed rows. Standing deprecation-watchlist section.
