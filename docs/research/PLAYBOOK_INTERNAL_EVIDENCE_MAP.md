# Playbook Internal Evidence Map (maintainer document — NOT part of the shipped playbook)

> STATUS: MAINTAINER REFERENCE. Date: 2026-08-21.
> Maps the generic rules of `playbook/` (Adaptive AI Systems Playbook v0.1.0) to their
> FIS evidence, external corroboration, and final A–H classification — so future
> maintainers can audit why each rule earned its class without FIS knowledge leaking
> into the shipped text. The shipped playbook must remain fully usable without this
> file.

## 1. Canonical-taxonomy mapping (owner decision 9)

The playbook defines ONE generic root-cause taxonomy (RC-1…RC-12, chapter 03 +
GLOSSARY), derived from the operating task-ontology's cause→action discipline (the
only taxonomy with measured usage) and generalized against the intervention-ladder
diagnosis list. The two historical taxonomies map into it as follows (both extracted
verbatim from the reference HTMLs on 2026-08-21; see
`playbook/planning/pass2/w1_verification.json`, agent `taxonomies-local`).

### Canonical Architecture v1 — 13-category discovery taxonomy → RC

| Historical category | Maps to | Note |
|---|---|---|
| ROUTING_FAILURE | RC-9 | |
| RETRIEVAL_FAILURE | RC-3 | retrieval miss (fact exists) |
| MISSING_KNOWLEDGE | RC-3 | absence (fact does not exist in system) — RC-3 covers both; the playbook distinguishes them inside RC-3's diagnosis procedure |
| STALE_DATA | RC-2 | upstream/authoritative-data defect treated as infrastructure/data-plane correctness |
| TOOL_FAILURE | RC-2 | tool executed wrongly (runtime defect) |
| TOOL_SCHEMA_FAILURE | RC-4 | contract mismatch |
| PERMISSION_FAILURE | RC-4 | permissions are part of the tool contract |
| PROMPT_FAILURE | RC-6 | |
| MODEL_REASONING_FAILURE | RC-10 | right evidence, wrong reasoning — learnable-gap candidate after cheaper rungs excluded |
| MODEL_CAPABILITY_FAILURE | RC-11 | |
| BAD_RUBRIC | RC-1 | the eval is wrong |
| NOVEL_TASK | RC-1/RC-12 | instrument coverage gap first (expand ontology/evals); architecture mismatch when structural |
| UNKNOWN | — | not a class; a pending-diagnosis state. The playbook makes "undiagnosed" a workflow state, not a taxonomy member |

### MSI guide — 9-category failure taxonomy → RC

| Historical category | Maps to | Note |
|---|---|---|
| Routing | RC-9 | |
| Tool selection | RC-6 | model not told/guided to use the tool (spec gap); if the tool was unusable, RC-4 |
| Tool result | RC-2 | "fix service; do not train around it" — verbatim ancestor of the never-train-around-defects rule |
| Evidence synthesis | RC-10 | prompt first (RC-6 check), then learnable gap |
| Schema | RC-5 | |
| Unsupported claim | RC-7 | verification gap (silent-failure class) |
| Knowledge | RC-3 | |
| Capability | RC-11 | with RC-9 escalation as the operational response |
| Novel scenario | RC-1 | "expand ontology/evals before training" — instrument first |

Both historical taxonomies conflate instrument, infrastructure, and capability
causes at different grain; RC-1…RC-12 separates them so each class has exactly one
primary ladder rung. Nothing in either historical taxonomy failed to map.

## 2. Generic rule → FIS evidence → external corroboration → class

The load-bearing extractions (chapter § references are to the shipped playbook).

| Generic rule (playbook home) | FIS evidence | External corroboration | Class |
|---|---|---|---|
| Evaluate first; eval infrastructure before optimization/training (00 P1) | E-series/R-series ordering; ladder enforced twice (E6 → no QLoRA; R6 → budget before weights) | NVIDIA agentic-customization blog (verified 2026-08-21); Anthropic/OpenAI eval guides | A |
| Instrument outranks score; measure ceilings/inversions/disagreement (00 P2, 03) | 13 harness defects; reachability ceilings S01 0.25→1.000 post-fix | SWE-bench Verified (16%→33.2% from curation) | A |
| Intervention ladder with evidence bars (00 P3, 07) | E6 prompt fix (+3.9× diagnosis conditional); R6 budget-not-weights | Ovadia/Soudani/Balaguer RAG-first trio; NVIDIA evaluate-first | A (order), B (rung procedures) |
| Consequence-bearing tolerances (04 §7) | R6 cap-tolerance escape hatch: 15/36 breach → "proceed, recorded" → 9h55m zero-scoring | Clinical-trial pre-specification doctrine (rule executes, not investigator) | A |
| Curtailed exact counting over SPRT under clustered ordering (04) | Replay on 4 real pilot sequences: count-to-4 dominates; SPRT α inflates ~2.2× at ICC 0.398 | SPRT admissibility conditions (i.i.d. calibration); conditional rejection form | A (conditional rule), H (i.i.d. sequential under clustering) |
| Certainty curtailment + 3 guards; decision-quality-not-speed (04) | Measured value 0.51h/24h; Bonsai fires at case 80; firewall flip p=0.0596→0.0139 | Exact-arithmetic argument (assumption-free) | B (default-on clause) |
| Cluster-robust primary inference; ICC→DEFF→N_eff→MDE; INCONCLUSIVE (04) | TEST ICC 0.475 → DEFF 4.33 → N_eff≈22; +13.5pp headline not significant (t=0.98, df=11) | Miller 2024 (clustered SEs up to 3.05× naive); NCSS McNemar power | A (procedure), C (any specific ICC/N) |
| Elimination rule: no withdrawal below pilot MDE (04) | UD-Q3_K_XL withdrawn at McNemar p≈0.22–0.48 on cap-confounded metric (corrected precedent) | Power-analysis first principles | B |
| Look ledger + spend semantics + refresh trigger (04, 03) | 7 TEST looks counted; look #8 gated on Suite-v4 trigger review | GSM1k overfitting-by-exposure; held-out hygiene consensus | A (principle), C (thresholds) |
| Round-robin/stratum-interleaved ordering (04) | 5.4× prefix accuracy on real data | Survey-sampling first principles | B |
| pass^k for stochastic reliability claims (04) | Frontier arm known non-reproducible; pass^1-only reporting flagged | τ-bench pass^k collapse (>60%→<25% at k=8) | B |
| Reproducibility boundary measured then scoped (02) | 23/48 outcomes flip across restart; 12/12 bit-identical within session; same-session rule | Thinking Machines batch-invariance; reduction-order nondeterminism (2506.09501) | A (procedure); the session-scoped conclusion is C |
| Execution-system identity; never collapse model/runtime/harness (02) | R3/R3b budget confound; Switchyard key-order defect | 'Silent Hyperparameter' (backend moves scores ≤16.6pp); Nemotron eval-recipe pinning ethos | A |
| Byte-equivalence through transport layers (08, 02) | R1/R0.1 JSON-key-reorder → grammar failure | ML Test Score Monitor-3 (training/serving skew) — instance unpublished | B |
| Deterministic grading on verifiable tasks; judge calibration protocol otherwise (03) | All-deterministic scorer/verifier; no judge in FIS | JudgeBench (judges ≈ chance on verifiable); κ-deflation study | A (scoped); judge protocol = doctrine-not-exercised |
| Ontology derivation via error-analysis-first (03, G1) | Ontology pre-existed the lab (gap); change discipline measured (E6 cause→action 18.8%→100% conditional) | Husain field guide; EvalGen criteria drift | B (procedure is external+synthesis) |
| Deliberate ambiguity, distractors, absence cases, forbidden claims (03) | 3 ambiguous categories ~50% lookup ceiling; replay_webhook distractor; S11 false-positive class; 13 forbidden claims | τ-bench task-design practice; harm-weighted scoring argument | B |
| Deterministic gate default when verifier exists (08) | R4: rescue ~100%, 0 unnecessary, 93/96 at 49% frontier utilization | All four published cascades are learned gates — novelty; break-even from LangChain benchmark | B (default), G (novelty claim) |
| Leakage audit / class-identity ceiling / LOGO (08) | R5 null: features encoded template identity; nothing passed LOGO | RouteLLM OOD near-random caution | A (audit requirement) |
| SMOKE-as-registry-state; no relaxed lane (04, 13) | R6 guards; relaxed-tier proposal rejected in adversarial review | Fail-closed first-principles argument | A (general form), C (36-case composition) |
| Demand ledger + pre-committed purchase trigger + benchmark-first (11) | ~38 lifetime GPU-hours vs 93% within-run busy; $4 benchmark design; trigger ~$150/mo ×3mo | Honest-utilization break-even arithmetic | B (defaults), C (every threshold/price) |
| Critical-path before parallelism purchases (11, 06) | +1 node saves 8.8h, +2 saves 0.0 min (exhaustive placement search) | Critical-path first principles | B |
| Performance autopsy as standing procedure (06) | R6 autopsy: 93.4% serial decode, 41% cap-burn, clock skew found forensically | Vendor benchmarking guides stop at metrics; no vendor autopsy method exists | B |
| Dual clocks + authoritative clock (06, 12) | WSL2 monotonic skew 8–12% found by cross-check | Virtualization clock pathologies (general) | B |
| Telemetry floor before long runs (12) | M0 telemetry floor motivated by autopsy gaps; reasoning text discarded at local.py:148 pre-M0 | NIM observability = production-only; experimentation floor absent from vendor corpus | B |
| Ground-truth isolation, two-layer (13) | fis_tools role holds no grant on ground_truth; reachability tests | Structural least-privilege argument | A |
| Hash-chained record of record; dashboards mirror only (13) | learning/registry ledgers; contract blob binding | MLflow/W&B/DVC lack tamper evidence (verified gap) | B |
| Own-trace training only; provider-ToS check at training time (09, 13) | R5/R6 TRAIN trajectories ground-truth-scored (compliant design); nothing trained yet | Anthropic §D.4 + AUP (verified live); OpenAI (proxy-verified); Gemini (verified) | A (check), C (each provider's terms) |
| Full-suite forgetting gate for FT (09) | none (not exercised) | Luo et al. forgetting; merging unreliable | B, doctrine-not-exercised |
| Rig-first training de-risk (09) | FT-rig design (adversary-endorsed); ModelArtifact gap found | Pipeline-risk first principles | B, doctrine-not-exercised |
| Shadow/canary restraint; one canary; causal metrics (10) | none (pre-production) | SRE Workbook ch.16 (verified quotes); SageMaker/Azure mechanics | A (external consensus), doctrine-not-exercised internally |
| Suite versioning + cross-suite refusal (03) | v1→v2→v3 releases; tooling refuses cross-suite | EvalGen criteria drift | A |
| Canary strings in published eval content (03, 13) | Mechanism lands at M-STAT; activation only at the next versioned suite release — never a mutation of frozen Suite v3 (owner decision 2026-08-21) | BIG-bench canary convention | B |

## 3. Classification-audit notes

- The Pass-1 evidence inventory assigned A generously (263/395 in early doc sets).
  Final shipped classes follow BUILD_PLAN §5 rules 2–3: single-project singletons
  cap at B; A requires external corroboration or first-principles argument in place.
  The table above records where each load-bearing rule landed and why.
- W1 corrected attributions (2026-08-21), reflected in `playbook/references/sources.yaml`:
  NV-EVALRECIPE-001 does NOT carry container/param/judge-pinning or smoke-discipline
  claims (restricted to recipe publication + methodological-consistency); the NeMo
  Customizer early-stopping defaults are code-level, not published doc guidance
  (NV-FINETUNESTACK-001); the OpenAI Evals platform sunsets 2026-11-30; OpenAI ToS
  verified via text-proxy only; Nemotron eval-recipe pinning discipline is instead
  taught as a playbook DEFAULT backed by nondeterminism literature.
- FIS numerics ship ONLY inside `playbook/examples/CASE-*.md`; this map is the only
  other place they appear, and it is not part of the shipped playbook.
