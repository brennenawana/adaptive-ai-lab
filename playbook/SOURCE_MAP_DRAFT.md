# Source Map — Draft

> STATUS: PLANNING ARTIFACT — feeds `references/sources.yaml` and chapter authoring.
> Date: 2026-08-20
> Companion: `PLAYBOOK_BUILD_PLAN.md` (tree, extraction rules, gap register,
> workstreams). Raw statement-level inventory: `planning/evidence_inventory.json`;
> external-source row seeds: `planning/external_sources_{nvidia,methodology}.json`.

## 1. How to read this map

- **Chapter keys** `00`–`14` refer to the proposed tree in `PLAYBOOK_BUILD_PLAN.md` §1.
- **Statement-level classes** (A generic principle · B default/heuristic · C project
  parameter · D vendor recipe, follow · E vendor recipe, adapt · F reference · G case
  study/empirical lesson · H rejected/deprecated) describe *what a document mostly
  yields for the playbook* — its "classification profile."
- **Source-level stances** (FOLLOW / ADAPT / REFERENCE / DEPRECATED / CASE) are what
  `sources.yaml` will carry per source.
- FIS documents are **evidence, not instruction**: their dominant yields are G
  (lessons whose numbers stay quarantined in `examples/`), A/B candidates (subject to
  the promotion rules in BUILD_PLAN §5 — most inventory-A items are expected to land
  as B), and C exemplars (worked values for parameter tables).
- Nothing here is a verified citation yet: every FOLLOW/ADAPT external source gets a
  live re-verification in authoring workstream W1 before its stance is printed.

## 2. Repository sources → chapters

### 2.1 The two research reports (the evidence backbone)

| Doc | Role for the playbook | Chapters | Profile |
|---|---|---|---|
| `docs/research/2026-08-19_NVIDIA_AI_Lab_Playbook_Research.md` | The vendor-recipe map: which NVIDIA procedures are FOLLOW/ADAPT/REFERENCE/DEPRECATED; the "execution mechanics strong, decision layer weak" thesis; the 14-stage lifecycle map; the durable-gap list (§7) that defines what the playbook itself must supply; Appendix C deprecation watchlist → SOURCES.md standing section | 05, 06, 07, 09, 10, 12 + sources.yaml seed | D/E/F/H verdicts + the gap agenda |
| `docs/research/2026-08-20_AI_Lab_Methodology_Hardware_Strategy.md` | The non-vendor methodology: statistics (clustering/MDE/N_eff, curtailment, consequence-bearing tolerances — re-derived on real data), external corroboration for FIS practice (JudgeBench, EvalGen, GSM1k, τ-bench, Miller 2024), economics formulas (break-even, H*, trigger policy), the two-level-lab adjudication, ToS constraints | 03, 04, 07, 09, 11, 13 | A/B candidates with named evidence strengths + G |

Caveat carried from `docs/README.md`: the 08-20 report's §2.3 matrix retains two
stale pre-correction rows suggesting SPRT-style rules; its §2.2/Appendix C
corrections govern. The playbook inherits the *corrected* rules only.

### 2.2 Current normative docs (generalization sources)

| Doc | Role | Chapters | Profile |
|---|---|---|---|
| `docs/current/EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md` | The FIS instantiation of the generic methodology — the single densest A/B-candidate source: splits/looks, static gates, SMOKE-as-state, consequence-bearing tolerances, curtailment guards, cluster-robust reporting, determinism/telemetry rules, KEEP/CHANGE/ADD/REMOVE delta | 00, 02, 03, 04, 12 | A/B candidates + C exemplars |
| `docs/current/EXPERIMENT_CONTRACT_TEMPLATE.md` | Direct ancestor of `templates/EXPERIMENT_CONTRACT.md`; the freeze checklist; "absence is a decision" discipline | 04, templates | Template source |
| `docs/current/AI_SYSTEMS_LAB_MASTER_PLAN.md` | The ladder (§5), lifecycle (§4), policy summaries (§7–8), definition-of-done table (§11) as the pattern for a program-level capability checklist; milestone-gating style | 00, 01, 07, 11, 14 | A/B candidates + G |
| `docs/current/NEXT_STEP_M0.md` | The diagnostic-gate pattern: cheap paired-probe diagnostic deciding an expensive experiment's fate; data-sufficiency precedence over effect size; "completion alone never produces GO" | 07, 04, templates | G → `examples/fis-diagnostic-gate.md` |
| `docs/current/TEST_LOOK_LEDGER.md`, `GPU_HOURS_LEDGER.md` | The consumable-resource-ledger pattern (exposure counting + pre-committed trigger + honest NOT-RUN rows) | 04, 11, templates | Template sources |

### 2.3 Frozen contracts and final reports (case-study quarry)

| Doc | Role | Chapters | Profile |
|---|---|---|---|
| `docs/R6_EXPERIMENT_CONTRACT.md` + `R6_..._REFRESH_REPORT.md` | Model-selection method under provenance; the cap-tolerance escape-hatch failure; silent-failure-vs-accuracy metric design; per-clause gate verdicts; amendment-log discipline | 04, 05, 08 | G (4+ case studies) |
| `docs/R6_PERFORMANCE_AUTOPSY.md` | The **performance autopsy method** (multi-source critical-path reconstruction, counterfactual costing, clock forensics) → `templates/PERFORMANCE_AUTOPSY.md`; the hardware-counterfactual discipline | 06, 11, 12, templates | G + template source |
| `docs/R5_EXPERIMENT_CONTRACT.md` + `R5_LEARNED_ROUTING_REPORT.md` | The learned-component admission bar: class-identity ceiling, leave-one-class-out, leakage audits; gate-power-per-arm; pre-registration retrospective (its own four failure modes) | 08, 04 | G (leakage audit → generic procedure) |
| `docs/routing-experiments.md` | Standing routing rules as they accreted; R1–R4 records incl. the transport-serialization defect and the deterministic-gate result | 08, 02 | G + B candidates |
| `docs/SUITE_V3_RELEASE_CONTRACT.md` + `_REPORT.md` | The versioned-suite release procedure (ceilings, gold gates, determinism, cross-suite refusal) → `templates/EVAL_SUITE_RELEASE_CONTRACT.md`; defect classes + which detection mechanism found each | 03, templates | G + template source |
| `docs/experiment-log.md`, `docs/OVERNIGHT_STATUS.md` | E-series history: pilot-optimism collapse (E2), ablation of bundled interventions (E6), fluke guards (E6b), token-cap confound (R3/R3b); comparability-status discipline (which numbers may be compared) | examples, 03, 04, 07 | G |
| `docs/HANDOFF.md`, `docs/SETUP-ACTIONS.md` | "Rules that carry" (proto-playbook); operational-state handoff as a document genre → `templates/OPERATIONAL_HANDOFF.md`; environment-gotcha patterns (clock validity, interop mangling) | 12, 02, templates | G + template source |
| `docs/task-ontology.md` | The ontology → cause→action-table procedure (generic); the 12-class instance (C) | 03 | Procedure A/B; instance C |
| `docs/architecture.md`, `docs/clean-room-boundary.md` | Ground-truth isolation (two-layer enforcement), event-driven lifecycle requirement, port/component hygiene; the clean-room boundary as a validity+security pattern (incl. employer-IP hygiene) | 02, 12, 13 | A/B candidates + F |

### 2.4 Reference designs (docs/reference/) and superseded material

| Doc | Role | Chapters | Profile |
|---|---|---|---|
| Canonical Architecture v1 (HTML) | Reference production topology: two planes, five memory types, specialization ladder, phased rollout. **F-class by decision B7** — one strong worked pattern, not normative. Pre-implementation prescription: no measured outcomes | 02, 08, 10, 12 | F (+ A/B candidates where later evidence confirmed) |
| MSI / FIS Sandbox Guide (HTML) | Scenario/tool-contract design patterns; experiment-matrix design; origin of the 12-class instance. Flag: prescribes a runtime default later practice reversed (see §4) | 03, 08 | F/G; parts superseded |
| H0–H3 Harness Roadmap, D0 Telemetry Plan (HTML) | Harness-comparison science and developer-agent telemetry as **designed-not-validated** methodology (`status: doctrine — not yet exercised`); D0's telemetry floor partially absorbed by M0 | 05, 08, 12 | F (inference) |
| MacBook Hybrid Deployment Guide (HTML) | Different machine; a few generic hybrid local/cloud routing ideas only | 08, 11 | F (thin) |
| `docs/superseded/*` | Executed launch plans — provenance only; the *supersession discipline itself* (README status headers, path map, "historical plans are never instructions") is a G-lesson for 13 | 13 | H/G |

### 2.5 Non-doc repository sources

| Source | Role | Chapters |
|---|---|---|
| `learning/registry/` (hash-chained ledgers, state machines), fail-closed runner code | Reference implementation of provenance/fail-closed patterns cited by 13 and templates; the SMOKE state; `--candidate` refusal style | 13, 04 |
| Postgres `learning.*` schema, `scenarios/` generator + manifests | Reference implementation: trajectory persistence, corpus digesting, seeded generation with disjoint ranges | 03, 12 |
| `Makefile` verification targets (`make reachability` etc.) | The "static integrity gates as executable commands" pattern | 03, 12 |

## 3. External source families → chapters

Family-level here; row-level seeds in `planning/external_sources_*.json`; final
per-source records in `references/sources.yaml` after W1 re-verification. Stances
below are the research reports' verdicts, inherited pending W1.

### 3.1 NVIDIA families (from the 2026-08-19 audit)

| # | Family (anchor sources) | Stance | Chapters | Freshness |
|---|---|---|---|---|
| N1 | **Inference benchmarking methodology** — NIM LLM Benchmarking Guide (2026-07-20), AIPerf, 2025 blog series (metric definitions, concurrency sweeps, operating-point selection) | **FOLLOW** (the one mature vendor methodology) | 06 | active (GenAI-Perf commands deprecated — trap) |
| N2 | **Evaluator SDK operational discipline** — dry-run → limit-samples pilot → parallel/cached/resume; `nel compare`/`nel gate` statistics (McNemar, power tables, INCONCLUSIVE) | FOLLOW (ops discipline) / ADAPT (stats layer — verify fit to own output formats; cannot evaluate prompt changes) | 03, 04 | active |
| N3 | **Quantization** — Model Optimizer (PTQ/NVFP4/AWQ/QAD), choosing-quant-methods page, NVFP4 Spark playbook, QAD blog (2026-08-17), researcher-guide progressive subsets | ADAPT (mechanics strong; acceptance gate re-based on task evals; >99%-recovery is demonstrated practice, not doctrine; decision page lags flagship format by a year) | 07 | volatile (API churn; NVFP4-on-consumer status shifts monthly) |
| N4 | **Routing/cascade** — Switchyard (pre-alpha, 2026-08-11) escalation semantics; SLM-agents position paper; LangChain break-even benchmark (partner) | ADAPT (semantics vocabulary + break-even formula; two-tier only; pre-alpha, reference semantics not production dependency) | 08 | volatile |
| N5 | **Serving playbooks** — vLLM/SGLang/TRT-LLM/llama.cpp/NIM/Dynamo; engine-selection rule absent everywhere | ADAPT/REFERENCE (mechanics yes; selection criterion is playbook IP — G20) | 05, 10 | active |
| N6 | **Fine-tuning mechanics** — NeMo AutoModel, Customizer control docs (LoRA-vs-SFT rules, early-stopping defaults), Unsloth (partner), RTX Garage dataset thresholds, tool-calling tutorial (split + golden set) | ADAPT (mechanics; decision rules and eval-gates are the playbook's) | 09 | active |
| N7 | **Data tooling** — NeMo Curator (pretraining-scale), Data Designer (beta) | REFERENCE | 09 | active |
| N8 | **Observability** — NIM Logging & Observability, `vllm:*` metric vocabulary, W3C traceparent, DCGM/dcgm-exporter, Triton metrics surface | ADAPT (production floor documented; experimentation minimum is playbook IP) | 12 | active |
| N9 | **Feedback-loop design** — Data Flywheel Blueprint (deprecated 2026-04): log→stratify→tune→judge→human-gated promotion, "flashlight not autopilot" | DEPRECATED artifact / ADAPT loop design | 12, 09 | frozen (withdrawn; still cross-promoted — trap) |
| N10 | **Agent/harness tooling** — NeMo Agent Toolkit (`nat eval`, profiler), ATIF trajectory standard, garak z-score-vs-calibration-bag pattern, SkillEvaluator | ADAPT/REFERENCE (no harness-selection method; no variance treatment — playbook supplies) | 05, 08, 12 | active |
| N11 | **Environment/sandboxing** — AI Workbench (incl. Claude Code sandboxing, no experiment tracking by design), NemoClaw/OpenShell (demo-grade) | REFERENCE | 13, 02 | active |
| N12 | **Reproducibility pattern** — Nemotron Open Evaluation Standard (pin containers/params/judges; publish recipes; smoke discipline) | ADAPT (formalized into contract/execution-system chapters) | 02, 03 | stable |
| N13 | **Integrated lifecycle watch-items** — NeMo Platform, Switchyard prefill router, GB10 observability fixes | REFERENCE (quarterly watch; the audit's §10 open questions become sources.yaml watch flags) | 00, 12 | volatile |
| N14 | **Enterprise deploy mechanics** — NIM Operator KServe canary path, Dynamo rollouts (Future Work), NGC/Entity Store registries (one-hop lineage) | REFERENCE (mechanism documented, methodology delegated — the gap 10 fills) | 10, 13 | active |
| N15 | **Spark corpus** — 46 playbooks + User Performance Guide + Porting Guide | REFERENCE (activate on Spark-class purchase; perf-guide method transfers conceptually) | 06, 05 | active |
| N16 | **Deprecation watchlist** (audit Appendix C: flywheel, llm-router, GenAI-Perf, RTX AI Toolkit, NeMo-Aligner, TRT-LLM-backend, renamed ModelOpt docs, restructured Evaluator docs, llm_ptq, "DGX Cloud") | DEPRECATED register → SOURCES.md standing section | all | stable (as a register) |

### 3.2 Non-NVIDIA methodology families (from the 2026-08-20 study)

| # | Family (anchor sources) | Stance / strength | Chapters |
|---|---|---|---|
| X1 | **Eval reporting statistics** — Miller 2024 "Adding Error Bars to Evals" (SEs, clustered SEs, paired differences, power/MDE); NCSS/PASS McNemar power; Amazon LLM-Accuracy-Stats | FOLLOW (strong-evidence; the 04 backbone) | 04 |
| X2 | **Sequential/adaptive stopping** — clinical-trial adaptive-design doctrine (pre-specify the rule; DSMB executes), SPRT (conditional admissibility — i.i.d. check first), racing/Hoeffding-Bernstein, ASHA/Hyperband (Li et al.), confidence sequences | ADAPT (with the FIS-derived admissibility conditions; consensus for the pre-specification doctrine) | 04, 07 |
| X3 | **Eval construction practice** — Anthropic/OpenAI eval guides (consensus), Husain error-analysis-first, EvalGen criteria-drift (strong-evidence), SWE-bench Verified curation, GSM1k leakage, BIG-bench canary strings | ADAPT (the requirement→trusted-suite procedure is assembled here + FIS practice; volume-vs-curation tension kept visible) | 03 |
| X4 | **Judge literature** — Zheng MT-Bench (domain-limited), JudgeBench (judges ≈ chance on verifiable tasks — strong-evidence), "Reliability without Validity" κ-deflation | Evidence base for grader-choice rules + the W7 calibration protocol | 03 |
| X5 | **Stochastic-system evaluation** — pass@k (Chen), τ-bench pass^k collapse, Thinking Machines batch-invariance, reduction-order nondeterminism (arXiv:2506.09501), vLLM/SGLang determinism docs, llama.cpp maintainer notes | ADAPT (pass^k as reliability metric; nondeterminism mechanisms inform 02's probe design) | 02, 04 |
| X6 | **Fine-tuning decisions & mechanics** — Ovadia/Soudani/Balaguer (RAG-vs-FT direction), LIMA (scope caveat: no minimum-n source exists for narrow fixes — declared gap), QLoRA (Dettmers) + verified VRAM floors, Biderman vs LoRA-without-Regret (regime reconciliation), forgetting literature, AlpaGasus; LoopTool/CurateEvo (research-only) | ADAPT / REFERENCE per item; minimum-n as an ablation is playbook IP | 09 |
| X7 | **Legal/ToS constraints** — Anthropic Commercial Terms §D.4 + AUP (verified live 2026-08-20): no training on frontier outputs without authorization | FOLLOW (normative constraint; re-verify each authoring pass; OpenAI equivalent NOT verified — flag) | 09, 13 |
| X8 | **Cascade/routing literature** — FrugalGPT, RouteLLM (OOD caution), AutoMix, Hybrid LLM (all learned gates; deterministic gate unprecedented → FIS novelty claim) | REFERENCE (design space + the admission bar for learned routers) | 08 |
| X9 | **Progressive delivery & ops** — SageMaker shadow testing, Azure safe rollout, Kayenta (ceiling), Google SRE Workbook ch.16 restraint doctrine, ML Test Score (annual audit rubric; Monitor-3/Monitor-7), Sculley tech-debt | ADAPT (SRE restraint + ML Test Score as the 10/12 backbone) | 10, 12 |
| X10 | **Load/perf testing taxonomy** — k6 test-type labels, DistServe goodput (PDF unverified — flag) | ADAPT (labels), REFERENCE | 06 |
| X11 | **Lineage/tracking tools** — MLflow/W&B/DVC (no tamper-evidence — the hash-chained-registry justification) | REFERENCE (dashboards, never the record of record) | 13, 12 |
| X12 | **Small-testbed/transfer literature** — muP, scaling laws, tinyBenchmarks/Anchor Points, IRT-in-few-model-regimes caveat, Karpathy sanity gates | REFERENCE (grounds the realism-over-miniature decision and its conditions) | 03, 04 |
| X13 | **Market/pricing snapshot 2026-08** — GPU/cloud/DRAM prices, memory-crunch narrative, community decode benchmarks (hardware-corner, llama.cpp threads; provenance-corrected) | REFERENCE, freshness=snapshot (stale by design; the *re-verify-at-order-time rule* is the durable content) | 11 |

## 4. Contested pairs / unresolved tensions (kept visible — BUILD_PLAN §5.6)

1. **Eval volume vs curation**: Anthropic "more questions, lower-signal grading" vs
   SWE-bench-Verified/FIS curation. → 03 presents as a sized decision with the
   trade-off rule.
2. **LoRA quality regimes**: Biderman "learns less" vs LoRA-without-Regret ≈ full FT —
   reconciled by regime; 09 must state the regime boundary, not a winner.
3. **NVIDIA internal lag**: choosing-quant-methods "FP8 first" (no NVFP4 mention) vs
   NVFP4 flagship positioning. → 07 callout: decision pages can lag a vendor's own
   practice by a year; date-weight vendor guidance.
4. **Local runtime default**: Canonical Architecture (llama.cpp primary) vs MSI guide
   (vLLM primary) vs later FIS practice (pinned llama.cpp for determinism/provenance
   on owned hardware; vLLM deferred to a throughput profile). → 05 needs the
   *criterion* (determinism/provenance regime vs throughput regime), not a winner.
5. **Two failure taxonomies** (13-category discovery vs 9-category failure) + the
   operating task-ontology root causes. → one canonical taxonomy with mapping
   (BUILD_PLAN §11 Q9).
6. **Spark decode benchmark provenance**: community-thread 38.55 tok/s vs higher
   LMSYS engine numbers (25–55% run-to-run spread). → 11 case material on
   benchmark-provenance discipline.
7. **Fine-tunable-size claims**: 70B / 120B / 200B mutually inconsistent across
   NVIDIA-endorsed materials. → 09 callout on vendor sizing claims.
8. **SPRT**: external doctrine vs FIS rejection under measured clustering. → 04
   carries the conditional rule (BUILD_PLAN §5.4), not the verdict.
9. **Amendment legitimacy** (R5's self-flagged tension): TRAIN-derived amendment vs
   post-hoc threshold-shopping — commit order alone does not distinguish. → G15.

## 5. Verification flags (live re-check required in authoring pass W1)

**Volatile stances** (may have moved since 2026-08-20): Switchyard (pre-alpha),
NeMo Platform, Model Optimizer APIs/docs URLs, NVFP4-on-SM120 kernel status, GB10
observability fixes, AIPerf, Evaluator SDK version, llama.cpp sm_120 bugs, every
price in X13.

**Never verified by the research passes** (inherited flags): FDA 2019 adaptive-design
guidance (fetch blocked; doctrine taken from secondary sources), Jennison & Turnbull
primary text, OpenAI current ToS text, Kayenta's exact statistical test, DistServe
PDF headline figures, true eBay sold prices, GMKtec 128GB SKU, NCCL-over-PCIe penalty
magnitude, an NVIDIA-authored P2P statement, dual-GPU thermal claim (first-principles
only), conditional-power ~0.2 convention (dropped for exactly this reason),
build.nvidia.com catalog metadata (JS pages; verified only via GitHub mirror).

**Internal stale-row caveat**: 08-20 report §2.3 retains two pre-correction SPRT rows
(see §2.1).

## 6. Coverage check — where the evidence is thin

Density: ● strong · ◐ medium · ○ thin. "Thin" chapters lean on external synthesis
and the gap register (BUILD_PLAN §12); they are where authoring risk concentrates.

| Ch | Internal evidence | External evidence | Thin spots |
|---|---|---|---|
| 00 | ● playbook/master plan | ◐ evaluate-first endorsements | rigor dial (G2) |
| 01 | ○ implicit in practice | ○ | **mostly new synthesis**; intake fields, archetypes, cold-start (G4) |
| 02 | ● digests, determinism findings | ◐ nondeterminism literature | — |
| 03 | ● suite releases, ontology, ceilings | ● eval literature | ontology *derivation* (G1); non-generator instruments (G3) |
| 04 | ● contracts + corrected stats | ● Miller/sequential doctrine | all generality is external (G18); amendment rule (G15) |
| 05 | ◐ R6 method, screening | ◐ catalogs only | harness selection (doctrine-only); engine criterion (G20) |
| 06 | ● autopsy, dual clocks | ● NIM/AIPerf FOLLOW | multi-tenant/concurrency (G9) |
| 07 | ● ladder enforced twice; M0 pattern | ◐ quantization ADAPT | finding-vs-waste test (G14) |
| 08 | ● R4/R5, tool contracts | ◐ cascade lit., Switchyard | routing-input taxonomy (G11); graduation criteria (G13) |
| 09 | ○ roadmap/rig design only — **nothing trained yet; label honestly** | ● FT literature + ToS | minimum-n (field gap); curation at small scale |
| 10 | ○ doctrine only | ◐ SRE/cloud-vendor patterns | **thinnest chapter**; rollback runbooks (G10); vendor corpus ABSENT here too |
| 11 | ● hardware study, formulas, triggers | ◐ snapshot prices | all numbers snapshot-dated by design |
| 12 | ◐ telemetry floor, harvesting design | ◐ NIM observability, ML Test Score | pipeline correctness (G12); drift (G5) |
| 13 | ● provenance, clean-room, isolation | ◐ lineage-tool gap analysis | license review (G7); threat model (G8); PII (G6) |
| 14 | derived from 00–13 | — | consistency discipline (BUILD_PLAN §11 Q8) |
