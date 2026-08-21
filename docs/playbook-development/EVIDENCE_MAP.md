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
`docs/history/playbook-v0.1/planning/pass2/w1_verification.json`, agent
`taxonomies-local`).

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

## 4. Independent-audit dispositions (v0.1.1, 2026-08-21)

An external independent audit (run on another model against committed v0.1.0,
`3565e6b`) raised seven candidate findings. Each was independently re-verified —
repository text read directly, mathematics re-derived, volatile external claims
checked against the 2026-08-21 source-ledger verifications — before any edit. The
audit's having raised an issue was never used as evidence.

| # | Finding | Verdict | Severity after review | Action |
|---|---|---|---|---|
| 1 | "Own trajectory" treated as presumptively training-safe; 09 §5 claimed harvesting own traces "sidesteps the provider-output restriction entirely" | CONFIRMED — a cascade trajectory (the playbook's own default architecture, ch. 08) embeds the escalation tier's managed-provider outputs; ownership of the record ≠ training rights to its components | MAJOR | Component-level provenance qualification written into 09 §5 step 4 and §9; swept to 12 (harvesting), 14 (train-or-not tree + training-entry checklist), GLOSSARY (failure harvesting) |
| 2 | Ch. 11 Q0 hard-ruled managed APIs OUT on any hard privacy constraint, vs the navigator's "no compliant managed surface satisfies it" test | CONFIRMED — a literal contradiction with QUICKSTART node 5 / 05 §5.2; converts an admissibility filter into a self-hosting mandate | MAJOR | 11 Q0 rewritten to the shared admissible-surface test; 11 §8 owned-tier row and 14 §3.4 aligned |
| 3 | "More clusters, not more items per cluster" too absolute | PARTIALLY CONFIRMED — derivation: N_eff = km/(1+(m−1)ICC) is strictly increasing in m for ICC<1 (∂N_eff/∂m = k(1−ICC)/(1+(m−1)ICC)² > 0), saturating at k/ICC; linear and unbounded in k; equal to k at ICC=1. The absolute phrasing was wrong; the practical preference for clusters is right | MINOR (wording, but in normative statistics text) | Saturation-accurate wording in 04 §8 (two spots), formulary §2/§3b/§14, CASE-002 generic lesson, source-ledger claim row |
| 4 | "One change crosses a promotion stage at a time" forbids legitimate whole-system A/B promotion | PARTIALLY CONFIRMED — ch. 02 already frames comparisons at the execution-system level; 10's wording over-restricted. Invariant restated as one **declared treatment** at a time; component-attribution claims still require ch. 04 isolation | MAJOR (wording) | 10 §4 principle rewritten; SYNTH-08 phrasing aligned |
| 5 | Human-agreement floor as an unconditional promotion gate rewards imitation of the incumbent over adjudicated correctness | PARTIALLY CONFIRMED — the variant's own adjudication asymmetry already implied it; the AND-gate contradicted it | MAJOR | 10 §5: veto authority = adjudicated regret ceiling; agreement = compatibility diagnostic with a pre-registered review trigger, gating only when the profile declares interchangeability a requirement; Table 10.1 row, §12 outputs, SYNTH-08 aligned |
| 6 | "Opt-in in every major open serving engine" over-broad | PARTIALLY CONFIRMED — the ledger verified deterministic/batch-invariant modes for two engines (2026-08-21); others were not verified for such modes; "every" outran the evidence | MINOR | 02 §5 and §9 narrowed to ledger-verified engines + probe-don't-infer; other mentions were already hedged |
| 7 | v0.1.0 release summary said 16/3/1 G-dispositions; authoritative is 15/4/1 | CONFIRMED (bookkeeping) — mechanical enumeration: 15 COVERED; 4 DOCTRINE (G3, G5, G8, G10); 1 OUT-OF-SCOPE (G9). No shipped file carried the wrong count (commit-message/report erratum only); no gap reclassified | MINOR | Erratum recorded in CHANGELOG 0.1.1; this table is the standing correction |

No finding was rejected outright; none required reversing a v0.1.0 decision — all
seven sharpened rules in their originally intended direction.

After the seven corrections were applied, two bounded post-edit adversarial reviews
(scientific consistency; practitioner portability across seven routing profiles) ran
against the touched material. They confirmed the corrections' substance (all math
re-derived independently, including CASE-002's k/ICC = 25.3 ≈ 2.1× class count at
the measured ICC) and caught sweep gaps — a stale chapter-14 deployment line, the
05 §5.2 / 02 §5 Step 4 passages cited as co-authorities but not yet carrying the
admissibility test, an 11 Q0-vs-§8 internal contradiction (resolved by splitting
Q0 into Q0a managed-admissibility / Q0b full-custody), a missing component-provenance
field in 12 §5.2's trajectory record, and a missing profile carrier for the
behavioral-compatibility declaration — all fixed before tagging v0.1.1.
