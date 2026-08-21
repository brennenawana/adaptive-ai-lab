#!/usr/bin/env python3
"""Build references/sources.yaml from Pass-1 seed rows + W1 verification patches.

Deterministic. Re-run after editing PATCHES/ADDITIONS. Scaffolding — not shipped.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # playbook/
SEEDS = [ROOT / 'planning/external_sources_nvidia.json',
         ROOT / 'planning/external_sources_methodology.json']
OUT = ROOT / 'references/sources.yaml'

V = '2026-08-21'   # W1 live-verification date
RP = '2026-08-20'  # research-pass inherited date

# id -> field overrides (merged over seed row)
PATCHES = {
  'NV-INFERBENCH-001': dict(last_verified=V, evidence_strength='strong-evidence',
    notes="Verified live (W1): AIPerf-based; TTFT/ITL/TPS definitions, concurrency sweeps, ISL/OSL pairs, operating-point selection all present verbatim. 'latest' resolves to guide v2.0.0. 2025 blog series' GenAI-Perf commands deprecated, unbannered."),
  'NV-GENAIPERF-DEP-001': dict(last_verified=V, url='https://github.com/triton-inference-server/perf_analyzer',
    notes="Verified live (W1): perf_analyzer README carries the deprecation warning verbatim, pointing to AIPerf (github.com/ai-dynamo/aiperf, drop-in replacement per its migrating.md)."),
  'NV-EVALSDK-001': dict(last_verified=V, evidence_strength='strong-evidence',
    notes="Verified live (W1): compare (McNemar exact on discordant pairs, power table 10~28%/1000~2.8%, MDE reported, INCONCLUSIVE when underpowered, identical-prompt-template requirement) and quality-gate (tiers, 95% CI on paired delta, INSUFFICIENT_EVIDENCE <10 items, GO/NO-GO/INCONCLUSIVE exit codes) confirmed verbatim. SDK v0.3.0 (2026-06-03) still latest. CITATION PATH: /latest/ 308-redirects to /nightly/ — no pinned doc tree."),
  'NV-MODELOPTQUANT-001': dict(last_verified=V,
    notes="Verified live (W1): 'prioritizing using FP8 first' verbatim; NVFP4 STILL ABSENT from this decision page (present in the same repo's llm_qat guide, NV-MODELOPTQAD-001) — the decision-page-lags-flagship trap stands as of 2026-08-21."),
  'NV-LLMPTQ-DEP-001': dict(last_verified=V,
    notes="Verified (W1): examples/llm_ptq 404s; hf_ptq live. Supersession is inferred from the 404 + directory listing — no in-repo prose migration note exists."),
  'NV-MODELOPTRESEARCH-001': dict(last_verified=V, evidence_strength='strong-evidence',
    notes="Verified live (W1): margin-of-error table (±8.3pp @140 → ±0.9pp full) and first-N ordering-bias warning confirmed verbatim."),
  'NV-MODELOPTRENAME-DEP-001': dict(last_verified=V,
    notes="Verified (W1): rebrand announced 2025-12-08 in README; old GitHub-Pages docs subsite hard-404s; old repo slug transparently redirects (GitHub rename). Update docs links, repo links survive."),
  'NV-SWITCHYARD-001': dict(last_verified=V, tool_version='v0.2.0 (2026-08-10)',
    notes="Verified live (W1): still pre-alpha 'Not for production use'; escalation semantics confirmed (weak-first, judge on actual output, confirmations=2, per-session latch, fail-open, judge failure HOLDS streak). PRECISION: capable_target/efficient_target two-tier schema belongs to the stage_router route type. v0.2.0 was a substantial redesign (native Rust server) — do not cite v0.1.0-era CLI. Prefill router still unshipped (zero 'prefill' paths on main)."),
  'EXT-SWITCHYARD-001': dict(last_verified=V, evidence_strength='strong-evidence',
    notes="Verified live (W1): break-even rule and all figures verbatim (74% cost cut, 93% accuracy retention 80.0/86.0, escalation mean 6.9% over 5 runs, range 4.1–9.1%). Scope: 145-task agent suite, one weak/strong pairing — numbers are conditioned on that setup."),
  'NV-LLMROUTER-DEP-001': dict(last_verified=V, url='https://github.com/NVIDIA-AI-Blueprints/llm-router',
    notes="Verified (W1): deprecation notice (added 2026-07-08) lives on the 'experimental' branch README — which IS the default branch, so visitors land on it; 'main' carries no notice. Points to Switchyard."),
  'NV-NEMOPLATFORM-001': dict(last_verified=V,
    notes="Verified live (W1): active; pillars Secure/Evaluate/Tune/Build + synthetic data; Switchyard under Tune; driven from coding agents. Experiment-registry/run-history capability STILL ABSENT — the watch item stands."),
  'NV-DATAFLYWHEEL-001': dict(last_verified=V,
    notes="Verified live (W1): Apr-2026 deprecation notice verbatim, 'reference only', no successor named. Loop design (log→stratify→tune→judge→human-gated promotion; 'flashlight, not autopilot') remains citable as a design reference."),
  'NV-NIMOBSERVABILITY-001': dict(last_verified=V, pub_date='2026-08-19', classification='ADAPT',
    notes="Verified live (W1, page updated 2026-08-19): Prometheus /v1/metrics with unmodified vLLM-native metric passthrough, OTel spans via OTEL_EXPORTER_OTLP_TRACES_ENDPOINT, JSONL logs via NIM_JSONL_LOGGING. Classified ADAPT: production mechanics documented and adoptable; the experimentation telemetry minimum is missing and is supplied by chapter 12."),
  'NV-AGENTICBLOGS-001': dict(last_verified=V, evidence_strength='consensus',
    notes="Verified live (W1): 'The most successful teams start with lightweight methods, invest early in evaluation, and layer in training-based techniques where measurement shows they're needed.' Companion evaluation post (2026-05-19): developer.nvidia.com/blog/mastering-agentic-techniques-ai-agent-evaluation/ — TSR over accuracy, instrument from day one."),
  'NV-QADNEMOTRON-001': dict(last_verified=V, evidence_strength='case-study',
    notes="Verified live (W1): '>99% median accuracy recovery is targeted when performing PTQ only'; '95–99% ... when combined with QAD'; PTQ 96.33% → QAD 99.72% worked example — all verbatim. Demonstrated practice, not documented doctrine."),
  'NV-NVFP4PLAYBOOK-001': dict(last_verified=V,
    notes="Verified live (W1, file updated 2026-07-27): W4A16 interactive/low-concurrency vs W4A4 high-concurrency recipe rule verbatim; 'we recommend running evaluations' with no procedure/threshold. Format is Blackwell-only — quantize for the deployment target."),
  'NV-EVALRECIPE-001': dict(last_verified=V,
    claims='Publish the complete evaluation recipe alongside results; methodological consistency with clear provenance rather than bit-wise identical outputs',
    notes="Verified live (W1) WITH CORRECTION: two claims previously attributed here (pin containers/sampling-params/judges; smoke-test discipline) are NOT on the live page — do not cite this source for them. Confirmed: full-recipe publication; 'the purpose of open evaluation is not to force bit-wise identical outputs, but to deliver methodological consistency with clear provenance'. A --dry-run flag is mentioned in passing only."),
  'NV-FINETUNESTACK-001': dict(last_verified=V,
    claims='LoRA-vs-SFT selection guidance (LoRA for 1–2 GPUs / fast iteration / multiple specialized versions); GPU sizing guidance',
    notes="Verified (W1) WITH CORRECTION: Customizer docs carry LoRA-vs-SFT guidance, but the early-stopping defaults (val_loss, patience 10, min-delta 0.001) are NOT in the Customizer docs — they exist in NeMo's OSS training-framework code. Cite as code-level defaults, not published vendor guidance. K8s footprint."),
  'EXT-UNSLOTH-001': dict(last_verified=V, url='https://docs.unsloth.ai',
    notes="Verified live (W1): VRAM floors exact match (9B 6.5GB QLoRA/24GB LoRA; 27B 22GB/64GB; 70B 41GB/164GB — stated as absolute minimums); all-major-linear-layers LoRA targeting, rank 8–128 guidance, alpha=2r. CHANGE: multi-GPU now 'works but a much better version is coming' (no longer just 'coming soon'). Unsloth publishes no dates — staleness undatable from the page."),
  'NV-RTXAIGARAGE-001': dict(last_verified=V, pub_date='2025-12-15', url='https://blogs.nvidia.com/blog/rtx-ai-garage-fine-tuning/',
    notes="Verified live (W1) WITH CORRECTIONS: correct host is blogs.nvidia.com (not developer.nvidia.com/blog); published 2025-12-15. Thresholds confirmed exact: PEFT 100–1,000 prompt-sample pairs; full fine-tuning 1,000+."),
  'EXT-LEGAL-001': dict(last_verified=V, evidence_strength='consensus', pub_date='CT eff. 2025-06-17; AUP eff. 2025-09-15',
    url='https://www.anthropic.com/legal/commercial-terms',
    notes="Verified live (W1), both pages directly fetchable. §D.4 verbatim: customers 'may not ... access the Services to build a competing product or service, including to train competing AI models...'. AUP separately prohibits 'utilization of inputs and outputs to train an AI model' (model scraping/distillation) absent authorization. Re-verify every authoring pass and per project."),
  'EXT-STATS-001': dict(last_verified=V, notes="arXiv 2411.00640 verified resolving, title 'Adding Error Bars to Evals' (W1). Drives clustered/paired SE and power/MDE machinery in ch.04."),
  'EXT-EVAL-004': dict(last_verified=V), 'EXT-EVAL-006': dict(last_verified=V),
  'EXT-JUDGE-002': dict(last_verified=V), 'EXT-JUDGE-001': dict(last_verified=V),
  'EXT-JUDGE-003': dict(last_verified=V), 'EXT-AGENT-001': dict(last_verified=V),
  'EXT-DETERM-001': dict(last_verified=V), 'EXT-FT-002': dict(last_verified=V),
  'EXT-FT-005': dict(last_verified=V), 'EXT-FT-006': dict(last_verified=V),
  'EXT-ROUTE-001': dict(last_verified=V), 'EXT-EVAL-007': dict(last_verified=V),
  'EXT-STOPPING-001': dict(last_verified=V), 'EXT-TESTBED-002': dict(last_verified=V),
  'EXT-TESTBED-003': dict(last_verified=V), 'EXT-FT-003': dict(last_verified=V),
  'NV-RTXAITOOLKIT-DEP-001': dict(last_verified=V,
    notes="Verified (W1): archived:true; README deprecation line present; no successor named."),
  'NV-NEMOALIGNER-DEP-001': dict(last_verified=V,
    notes="Verified (W1): deprecated in favor of NeMo RL (github.com/NVIDIA-NeMo/RL)."),
  'NV-NIMTRTLLM-DEP-001': dict(last_verified=V,
    notes="Verified (W1, PARTIAL — release-notes level): NIM vLLM backend is the going-forward path; Spark still ships a TRT-LLM playbook alongside."),
  'NV-DGXCLOUD-DEP-001': dict(last_verified=V,
    notes="Verified (W1): rentable destinations present as DGX Cloud Lepton and Brev; 'DGX Cloud' proper no longer presents as a rentable product."),
  'NV-EVALDOCTREE-DEP-001': dict(last_verified=V,
    notes="Verified (W1): /latest/ redirects to /nightly/; versioned static doc paths do not exist; 2025-era adapters/interceptors URLs dead. Cite /nightly/ paths with as-of dates."),
  'EXT-OPS-002': dict(last_verified=V, url='https://research.google/pubs/whats-your-ml-test-score-a-rubric-for-ml-production-systems/',
    notes="Verified from the PDF itself (W1): 28 tests; final score = MINIMUM across the 4 sections; Monitor-3 = training/serving compute the same values; Monitor-7 = prediction-quality regression via held-out production examples. NOTE: a first-pass WebFetch summarization hallucinated wrong authors/venue — verified against page images; cite Breck, Cai, Nielsen, Salib, Sculley, IEEE Big Data 2017."),
  'EXT-PERF-002': dict(last_verified=V, url='https://grafana.com/docs/k6/latest/testing-guides/test-types/',
    notes="Verified live (W1): smoke / average-load / stress / spike / soak / breakpoint all present with definitions."),
  'EXT-EVAL-001': dict(last_verified=V, url='https://docs.claude.com/en/docs/test-and-evaluate/develop-tests',
    notes="Verified live (W1): multidimensional explicit criteria, grader-by-task-shape, edge-case checklists; volume heuristic ('prefer higher volume with slightly lower signal') present. The volume-vs-curation tension stays visible in ch.03."),
  'EXT-EVAL-002': dict(last_verified=V, url='https://platform.openai.com/docs/guides/evals',
    notes="Verified live (W1) WITH PLATFORM SUNSET: the hosted OpenAI Evals platform 'will become read-only for existing users on October 31, 2026' and 'is scheduled to shut down on November 30, 2026'. The methodology content (objective→dataset→metrics→run→iterate; validate model graders against humans) remains citable; do NOT present the platform as current tooling."),
  'EXT-EVAL-005': dict(last_verified=V, url='https://github.com/SWE-bench/SWE-bench',
    classification='REFERENCE',
    notes="W1 WITH DOWNGRADE (FOLLOW→REFERENCE): the historical curation figures (1,699 reviewed → 500 kept; 16%→33.2%) are corroborated via the SWE-bench repo + swebench.com and remain valid as the eval-curation case study. But the publisher's own ~Feb-2026 follow-up (EXT-EVAL-008) declares the benchmark saturated for frontier claims and reports flawed test cases in a hard-problem sample — cite this source ONLY for the historical curation lesson, never as a currently-recommended live benchmark. openai.com pages 403-blocked; secondary corroboration."),
  'EXT-EVAL-003': dict(last_verified=V, url='https://hamel.dev/blog/posts/field-guide/', pub_date='2025-03-24',
    notes="Verified live (W1): the error-analysis-first / bottom-up taxonomy process is the field-guide post (2025-03-24) — cite it, not the older evals post."),
  'EXT-AMAZON-LLMSTATS-001': dict(last_verified=V, url='https://arxiv.org/abs/2602.10144',
    notes="Verified (W1): stable citation is arXiv:2602.10144 (ICLR 2026). Code repo amazon-science/LLM-Accuracy-Stats archived read-only 2026-05-08 — usable, unmaintained."),
  'NV-LEPTONBREV-001': dict(last_verified=V),
  # Not re-verified this pass (stable/REFERENCE or snapshot-by-design) — annotate.
  'NV-SPARKPERF-001': dict(notes="Buried asset in the connect-two-sparks playbook; no thresholds; pins stale containers. Not re-verified in authoring pass (REFERENCE stance)."),
  'NV-SPARKPLAYBOOKS-001': dict(), 'NV-COSTTCO-001': dict(), 'NV-SLMRESEARCH-001': dict(),
  'NV-WORKBENCH-001': dict(), 'NV-CURATORDESIGNER-001': dict(), 'NV-TOOLCALLTUTORIAL-001': dict(),
  'NV-DYNAMOAICONFIG-001': dict(), 'NV-NIMOPERATORCANARY-001': dict(), 'NV-LINEAGEREGISTRY-001': dict(),
  'NV-GARAK-001': dict(), 'NV-NAT-001': dict(), 'NV-ATIF-001': dict(), 'NV-NEMOCLAW-001': dict(),
  'NV-NEMOTRONCC-LICENSE-001': dict(), 'EXT-PYTORCH-SPARKFT-001': dict(), 'NV-TAO-HPO-001': dict(),
  'EXT-STOPPING-002': dict(), 'EXT-STOPPING-003': dict(), 'EXT-FT-001': dict(), 'EXT-FT-007': dict(),
  'EXT-TESTBED-001': dict(url='https://karpathy.github.io/2019/04/25/recipe/'),
  'EXT-OPS-003': dict(), 'EXT-PERF-001': dict(),
  'EXT-PERF-003': dict(claims='backend choice alone moves scores up to 16.6pp; fintech-domain LLM output-drift study (ICAIF)'),
  'EXT-HW-001': dict(notes="2026-08-20 price snapshot — stale by design; the durable content is the re-verify-at-order-time rule. Every price cited from here MUST print its as-of date."),
}

# Fully new rows.
ADDITIONS = [
  dict(id='NV-MODELOPTQAD-001', org='NVIDIA', title='Model Optimizer llm_qat guide (QAD as recommended accuracy-recovery strategy)',
       url='https://github.com/NVIDIA/Model-Optimizer/tree/main/examples/llm_qat', type='official-repo',
       pub_date='', last_verified=V, maturity='current', classification='ADAPT', evidence_strength='strong-evidence',
       claims="'QAD is Model Optimizer's recommended strategy for accuracy recovery after quantization' (verbatim); references NVFP4 (which the choosing-quant-methods decision page omits)",
       chapters=['07'], freshness='active',
       notes='Added during W1: the QAD-recommendation line lives here, not on the decision page — cite this for the recovery-strategy recommendation.'),
  dict(id='EXT-LEGAL-002', org='OpenAI', title='OpenAI Terms of Use + Business Terms (output-training restriction)',
       url='https://openai.com/policies/terms-of-use', type='legal', pub_date='Business Terms eff. 2026-01-01',
       last_verified=V, maturity='current', classification='FOLLOW', evidence_strength='consensus',
       claims="Consumer ToU: 'Use Output to develop models that compete with OpenAI' is prohibited; Business Terms §3.3(e): may not 'use Output to develop artificial intelligence models that compete' except Permitted Exceptions (§17)",
       chapters=['09', '13'], freshness='active',
       notes='First verification 2026-08-21 — via text-extraction proxy only (direct fetch 403-blocked; archive.org unreachable). Content confirmed; treat as verified-with-caveat and re-verify per project.'),
  dict(id='EXT-LEGAL-003', org='Google', title='Gemini API Additional Terms of Service (output-training restriction)',
       url='https://ai.google.dev/gemini-api/terms', type='legal', pub_date='eff. 2026-03-23 (rev. 2026-04-28)',
       last_verified=V, maturity='current', classification='FOLLOW', evidence_strength='consensus',
       claims="'You may not use the Services to develop models that compete with the Services' (Use Restrictions)",
       chapters=['09', '13'], freshness='active',
       notes='Verified live 2026-08-21, directly fetchable. Materially newer effective date than the Anthropic/OpenAI documents — vendor terms move on different clocks; check each provider at training time.'),
  dict(id='EXT-VLLM-001', org='vLLM project', title='vLLM (engine + docs; batch-invariance opt-in)',
       url='https://github.com/vllm-project/vllm', type='official-repo', pub_date='', last_verified=V,
       maturity='mature', classification='ADAPT', evidence_strength='strong-evidence',
       claims='De-facto standard open serving engine; deterministic batch-invariant mode is OPT-IN (VLLM_BATCH_INVARIANT=1, CC>=8.0, reduced performance)',
       chapters=['05', '06', '02'], freshness='active', notes='Verified active (W1). Throughput-regime default candidate in ch.05 regime table.'),
  dict(id='EXT-SGLANG-001', org='SGLang / LMSYS', title='SGLang (engine; deterministic-inference mode)',
       url='https://github.com/sgl-project/sglang', type='official-repo', pub_date='', last_verified=V,
       maturity='mature', classification='REFERENCE', evidence_strength='strong-evidence',
       claims='Deterministic mode via Thinking Machines batch-invariant kernels; documented 25–45% slowdown, recommended for debugging/reproducibility',
       chapters=['05', '02'], freshness='active', notes='Verified active (W1); deterministic blog lmsys.org/blog/2025-09-22-sglang-deterministic/ live.'),
  dict(id='EXT-LLAMACPP-001', org='ggml-org', title='llama.cpp (engine)',
       url='https://github.com/ggml-org/llama.cpp', type='official-repo', pub_date='', last_verified=V,
       maturity='mature', classification='REFERENCE', evidence_strength='strong-evidence',
       claims='CPU/GPU GGUF engine; very active (multiple releases/day at verification); wide quantization-format support; single-slot serving suits determinism/provenance regimes',
       chapters=['05', '02'], freshness='active', notes='Verified active (W1): release b10545 dated 2026-08-21.'),
  dict(id='NV-TRTLLM-001', org='NVIDIA', title='TensorRT-LLM (engine)',
       url='https://github.com/NVIDIA/TensorRT-LLM', type='official-repo', pub_date='', last_verified=V,
       maturity='current', classification='REFERENCE', evidence_strength='heuristic',
       claims='NVIDIA-native engine; active (1.3.0rc-series on NGC 2026-08); NIM has moved its default backend to vLLM',
       chapters=['05'], freshness='active', notes='Verified active (W1).'),
  dict(id='NV-AIPERF-001', org='NVIDIA', title='AIPerf (benchmarking client; GenAI-Perf successor)',
       url='https://github.com/ai-dynamo/aiperf', type='official-repo', pub_date='v0.12.0 2026-08-06',
       last_verified=V, maturity='current', classification='FOLLOW', evidence_strength='strong-evidence',
       claims='Endpoint-agnostic benchmarking vs any OpenAI-compatible endpoint; v0.12.0 adds agent workloads, Anthropic Messages endpoint, accuracy benchmarking; drop-in GenAI-Perf replacement',
       chapters=['06'], freshness='active', notes='Verified active (W1). Pin one tool + one metric-definition set across tiers.'),
  dict(id='EXT-EVAL-008', org='OpenAI', title="Follow-up: 'Why SWE-bench Verified no longer measures frontier coding capabilities'",
       url='https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/', type='official-blog',
       pub_date='~2026-02 (per third-party citation)', last_verified=V, maturity='current',
       classification='REFERENCE', evidence_strength='strong-evidence',
       claims='The publisher of the curated benchmark later declared it saturated for frontier claims and reported that a large share of a sampled hard-problem subset had flawed test cases rejecting functionally correct submissions; recommends a successor benchmark',
       chapters=['03'], freshness='stable',
       notes='Discovered during W1 (2026-08-21); direct fetch 403-blocked, content corroborated via secondary citation — flagged as not first-party-verified. Doubly instructive for ch.03: even a human-curated suite carried instrument defects found only later — instrument validation never ends; and benchmark verdicts age (freshness discipline).'),
  dict(id='EXT-OPS-004', org='Netflix/Google (Kayenta)', title='Kayenta automated canary analysis',
       url='https://github.com/spinnaker/kayenta', type='official-repo', pub_date='2018', last_verified=RP,
       maturity='mature', classification='REFERENCE', evidence_strength='heuristic',
       claims='Automated statistical canary judgment — the CEILING of canary automation, explicitly NOT the small-team default (SRE restraint doctrine applies)',
       chapters=['10'], freshness='stable',
       notes='Exact statistical test not independently verified (inherited flag from research pass) — cite as existence proof only.'),
]

# Split EXT-OPS-001 umbrella into three verifiable rows.
OPS_SPLIT = [
  dict(id='EXT-OPS-001A', org='AWS', title='SageMaker shadow testing',
       url='https://docs.aws.amazon.com/sagemaker/latest/dg/shadow-tests.html', type='official-docs',
       pub_date='', last_verified=V, maturity='mature', classification='ADAPT', evidence_strength='consensus',
       claims='Mirrors a copy of live inference traffic to a shadow variant in real time; comparison/interpretation left to the user',
       chapters=['10'], freshness='stable', notes='Verified live (W1).'),
  dict(id='EXT-OPS-001B', org='Microsoft', title='Azure ML safe rollout (blue-green + mirrored traffic)',
       url='https://learn.microsoft.com/en-us/azure/machine-learning/how-to-safely-rollout-online-endpoints',
       type='official-docs', pub_date='2026-02-08 (rev. 2026-04-24)', last_verified=V, maturity='mature',
       classification='ADAPT', evidence_strength='consensus',
       claims='Staged manual traffic shifting (small % → all) plus mirrored/shadow traffic (≤50%, one deployment, documented limits)',
       chapters=['10'], freshness='active', notes='Verified live (W1).'),
  dict(id='EXT-OPS-001C', org='Google', title='SRE Workbook ch.16 — Canarying Releases (restraint doctrine)',
       url='https://sre.google/workbook/canarying-releases/', type='official-docs', pub_date='2018',
       last_verified=V, maturity='mature', classification='FOLLOW', evidence_strength='consensus',
       claims="'Use the simplest model that meets your technical and business objectives'; run ONE canary at a time; canary metrics must be causally attributable to the change",
       chapters=['10', '12'], freshness='stable', notes='Verified live (W1), phrasing near-verbatim.'),
]

CASES = [
  ('INT-CASE-001', 'consequence-bearing tolerances', 'A pre-registered tolerance whose escape hatch carried no priced consequence let a measured multiple-of-tolerance calibration breach proceed into a large share of a milestone wall clock scoring zero; the fix is naming ABORT/RECALIBRATE/PROCEED-WITH-DECLARED-CEILING per tolerance, enforced fail-closed', ['04', '07', '00']),
  ('INT-CASE-002', 'clustered eval effective N', 'Stratum-clustered outcomes silently collapsed a held-out suite to a small fraction of its nominal item count; the headline model comparison was not significant cluster-robustly; independent strata grow effective N without bound while within-stratum replications saturate at k/ICC', ['04', '03']),
  ('INT-CASE-003', 'learned-router leakage', 'A learned router scored well until a leave-one-group-out audit showed features encoded WHICH template an item was (class-identity ceiling); nothing beat the ceiling; the deterministic gate was retained', ['08', '03', '04']),
  ('INT-CASE-004', 'harness defects as instrument findings', 'A double-digit count of harness/scenario defects initially indistinguishable from model weakness was found by three statistical detection mechanisms: measured reachability ceilings, weak-beats-strong inversions, cross-arm disagreement review', ['03', '02']),
  ('INT-CASE-005', 'hardware purchase discipline', 'A measured critical path refuted an intuitive multi-GPU purchase (the second device saved nothing); the demand ledger showed trivial sustained demand; adopted: rented per-milestone nodes + a pre-committed purchase trigger', ['11', '06']),
  ('INT-CASE-006', 'token-budget confounding', 'A generation-cap confound inflated a model-comparison headline; isolating the budget factor shrank the claimed gap dramatically; caps must be calibrated with consequence-bearing tolerances and reported as measurement ceilings', ['07', '04', '05']),
  ('INT-CASE-007', 'deterministic cascade gate', 'A deterministic verifier-gated cascade achieved near-perfect rescue with zero unnecessary escalations — outside the published learned-gate design space (FrugalGPT/RouteLLM/AutoMix/HybridLLM)', ['08', '10']),
  ('INT-CASE-008', 'transport serialization defect', "A 'transparent' proxy reordered JSON keys, breaking a grammar-constrained consumer; found only by byte-equivalence verification; training/serving-skew class (ML Test Score Monitor-3)", ['08', '02', '12']),
  ('INT-CASE-009', 'suite versioning under criteria drift', 'Eval criteria drifted as outputs were seen (external: EvalGen); versioned suite releases with cross-suite comparison refusal made the drift explicit and auditable instead of silent', ['03', '13']),
  ('INT-CASE-010', 'pilot optimism collapse', 'Small-sample pilot headlines ran optimistic; scaling from the pilot to the full confirmation set collapsed the effect; pre-registered adoption rules with fluke guards caught cherry-picks', ['04', '03']),
  ('INT-CASE-011', 'diagnostic gate before an expensive experiment', 'A cheap paired-probe diagnostic (a fraction of a day) was pre-registered to decide a multi-day experiment\'s fate, with data-sufficiency precedence: completion alone never produces GO', ['07', '04']),
  ('INT-CASE-012', 'restart instability and paired controls', 'A large share of item outcomes flipped across a mere server restart; reproducibility was measured, then scoped by rule (same-session comparisons; contemporaneous paired controls for causal claims)', ['02', '04']),
]

import re

# Portability boundary: shipped text (sources.yaml / SOURCES.md) must not carry
# project-specific identifiers or measured numbers; those live in examples/CASE-*.
SANITIZE = [
    (r"\bFIS's\b", "the source project's"),
    (r"\bFIS\b", "the source project"),
    (r"count-to-4( at TRAIN)?", "curtailed exact counting"),
    (r"N_eff\s*[≈~]\s*22 finding", "effective-N collapse finding (CASE-002)"),
    (r"\bR6\b", "a frozen model-comparison experiment"),
    (r"\bR5\b", "a learned-routing experiment"),
    (r"\bR4\b", "the deterministic-gate experiment"),
    (r"\bR7\b", "a budget-calibration experiment"),
    (r"\bE6b?\b", "a prompt-variant experiment"),
    (r"Suite v[0-9]", "a versioned suite"),
    (r"beyond NATS events", "beyond its event-bus records"),
]

def esc(s: str) -> str:
    s = str(s)
    for pat, rep in SANITIZE:
        s = re.sub(pat, rep, s)
    return s.replace('"', "'")

def emit(row: dict) -> str:
    lines = [f"- id: {row['id']}"]
    def add(k, v):
        if v is None or v == '':
            lines.append(f"  {k}: null")
        elif isinstance(v, list):
            lines.append(f"  {k}: [{', '.join(repr(str(x)) for x in v)}]")
        else:
            lines.append(f'  {k}: "{esc(v)}"')
    add('org', row.get('org', ''))
    add('title', row.get('title', ''))
    add('url', row.get('url') or None)
    add('type', row.get('type', ''))
    add('pub_date', row.get('pub_date') or None)
    add('last_verified', row.get('last_verified') or None)
    if row.get('tool_version'):
        add('tool_version', row['tool_version'])
    add('maturity', row.get('maturity', ''))
    add('classification', row.get('classification', ''))
    add('evidence_strength', row.get('evidence_strength', ''))
    add('claims', row.get('claims', ''))
    add('chapters', row.get('chapters', []))
    add('freshness', row.get('freshness', ''))
    add('superseded_by', row.get('superseded_by') or None)
    add('notes', row.get('notes', ''))
    return '\n'.join(lines)

def default_strength(row):
    c = row.get('classification', '')
    return {'FOLLOW': 'strong-evidence', 'ADAPT': 'strong-evidence',
            'REFERENCE': 'heuristic', 'DEPRECATED': 'snapshot', 'CASE': 'case-study'}.get(c, 'heuristic')

rows = []
seen = set()
for seed in SEEDS:
    for row in json.load(open(seed)):
        rid = row['id']
        if rid == 'EXT-OPS-001':
            continue  # replaced by the A/B/C split
        if rid == 'EXT-FT-004':
            continue  # merged into EXT-UNSLOTH-001 (same docs site)
        row = dict(row)
        row['chapters'] = sorted({c[:2] for c in row.get('chapters', [])})
        row.setdefault('evidence_strength', default_strength(row))
        row.setdefault('last_verified', RP)
        if rid in PATCHES:
            row.update({k: v for k, v in PATCHES[rid].items() if v != ''})
        elif row.get('classification') in ('FOLLOW', 'ADAPT'):
            print(f"WARN: FOLLOW/ADAPT source {rid} has no W1 patch", file=sys.stderr)
        if rid not in seen:
            rows.append(row); seen.add(rid)

for row in OPS_SPLIT + ADDITIONS:
    rows.append(row); seen.add(row['id'])

CASE_FILES = {
    'INT-CASE-001': 'CASE-001_consequence-bearing-tolerances.md',
    'INT-CASE-002': 'CASE-002_clustered-eval-effective-n.md',
    'INT-CASE-003': 'CASE-003_learned-router-leakage.md',
    'INT-CASE-004': 'CASE-004_harness-defects.md',
    'INT-CASE-005': 'CASE-005_hardware-purchase-discipline.md',
    'INT-CASE-006': 'CASE-006_token-budget-confounding.md',
    'INT-CASE-007': 'CASE-007_deterministic-cascade-gate.md',
    'INT-CASE-008': 'CASE-008_transport-serialization-defect.md',
    'INT-CASE-009': 'CASE-009_suite-versioning-criteria-drift.md',
    'INT-CASE-010': 'CASE-010_pilot-optimism-collapse.md',
    'INT-CASE-011': 'CASE-011_diagnostic-gate.md',
    'INT-CASE-012': 'CASE-012_restart-instability-paired-controls.md',
}

for cid, short, claim, chapters in CASES:
    rows.append(dict(id=cid, org='internal (source project)', title=f'Case study: {short}',
        url=f"examples/{CASE_FILES[cid]}", type='internal-case', pub_date='2026-08',
        last_verified='2026-08-21', maturity='mature', classification='CASE',
        evidence_strength='case-study', claims=claim, chapters=chapters, freshness='stable',
        notes='Internal empirical case from the playbook\'s source project; full narrative in the examples/ file this row points to.'))

# Sync each row's `chapters` field with the chapters that ACTUALLY cite it, so the
# metadata reflects real usage (union of seed intent and observed citations).
CHAPTER_FILES = sorted(ROOT.glob('[01][0-9]_*.md'))
cite_re = re.compile(r'\[((?:NV|EXT|INT)-[A-Z0-9-]+-\d{3})\]')
actual = {}
for ch in CHAPTER_FILES:
    code = ch.name[:2]
    for m in cite_re.finditer(ch.read_text(errors='replace')):
        actual.setdefault(m.group(1), set()).add(code)
for row in rows:
    used = actual.get(row['id'], set())
    row['chapters'] = sorted(set(row.get('chapters', [])) | used)

header = f"""# Adaptive AI Systems Playbook — source ledger (RECORD OF RECORD)
# =================================================================
# One entry per stable source ID. IDs are never reused or renumbered.
# references/SOURCES.md is GENERATED from this file (references/tools/render_sources.py)
# — never hand-edit SOURCES.md.
#
# Fields: id, org, title, url, type (official-docs|official-blog|official-repo|paper|
#   third-party|partner|standard|legal|internal-case), pub_date, last_verified,
#   [tool_version], maturity (mature|current|new|pre-alpha|deprecated|unmaintained),
#   classification (FOLLOW|ADAPT|REFERENCE|DEPRECATED|CASE),
#   evidence_strength (consensus|strong-evidence|heuristic|contested|case-study|
#   inference|research-only|snapshot), claims, chapters, freshness (volatile|active|
#   stable|snapshot), superseded_by, notes.
#
# Rules (PLAYBOOK_BUILD_PLAN §7): volatile sources may not be cited as FOLLOW without
# a last_verified inside the current authoring pass; snapshot sources are citable only
# with their as-of date printed at the point of use; supersession is recorded, never
# deleted.
#
# Generated by planning/pass2/build_sources.py on 2026-08-21 from the Pass-1 seed rows
# + the W1 live re-verification (playbook/planning/pass2/w1_verification.json).

sources:
"""

body = '\n'.join('  ' + emit(r).replace('\n', '\n  ') for r in rows)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(header + body + '\n')
print(f"wrote {OUT} with {len(rows)} sources")
ids = [r['id'] for r in rows]
assert len(ids) == len(set(ids)), 'duplicate ids'
import yaml
d = yaml.safe_load(OUT.read_text())
print('yaml parses OK,', len(d['sources']), 'entries')
