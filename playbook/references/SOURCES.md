# Sources

> Part of the **Adaptive AI Systems Playbook** · [Index](../README.md)
>
> GENERATED from [`sources.yaml`](sources.yaml) by `tools/render_sources.py` —
> do not edit by hand. The YAML file is the record of record; chapters cite
> stable IDs; this page is the human-readable rendering.

90 sources. Verdict counts: FOLLOW 18 · ADAPT 28 · REFERENCE 34 · DEPRECATED 10 · CASE 0

## FOLLOW

*Mature methodology — follow by the book, within the stated scope and as-of date.*

| ID | Source | Claims we cite it for | Strength | Freshness | Verified |
|---|---|---|---|---|---|
| EXT-AMAZON-LLMSTATS-001 | **Amazon Science** — [LLM-Accuracy-Stats (ICLR 2026 paired McNemar method)](https://arxiv.org/abs/2602.10144) | Source method nel compare productized; usable standalone on lm-eval output | strong-evidence | stable | 2026-08-21 |
| EXT-EVAL-002 | **OpenAI** — [OpenAI eval guidance](https://platform.openai.com/docs/guides/evals) | objective→dataset→metrics→run→continuous; validate model-graders against humans | consensus | active | 2026-08-21 |
| EXT-EVAL-004 | **Shankar et al.** — EvalGen / Who Validates the Validators (criteria drift) (`arXiv:2404.12272`) | criteria and ground truth co-evolve; most load-bearing validation of the source project's design | strong-evidence | stable | 2026-08-21 |
| EXT-EVAL-006 | **Zhang et al.** — GSM1k contamination study (`arXiv:2405.00332`) | up to 8pp accuracy drop on fresh benchmark; contamination r²=0.36 | strong-evidence | stable | 2026-08-21 |
| EXT-FT-001 | **Ovadia; Soudani; Balaguer** — RAG-vs-fine-tuning comparison trio (EMNLP 2024, 2403.01432, 2401.08406) (`arXiv:2403.01432`) | three studies agree RAG/prompt-first for factual/citation tasks | strong-evidence | stable | 2026-08-20 |
| EXT-FT-003 | **Dettmers et al.** — QLoRA quantized fine-tuning (`arXiv:2305.14314`) | VRAM floors: 9B~6.5GB, 14B~8.5GB, 27B~22GB, 70B~41GB | strong-evidence | stable | 2026-08-21 |
| EXT-FT-005 | **Biderman; Thinking Machines** — LoRA quality package (LoRA Learns Less/Forgets Less + LoRA Without Regret) (`arXiv:2405.09673`) | all-layer LoRA at post-training scale ~= full FT at ~67% FLOPs | strong-evidence | stable | 2026-08-21 |
| EXT-JUDGE-002 | **Tan et al.** — JudgeBench: LLM judges on objectively verifiable tasks (`arXiv:2410.12784`) | GPT-4o-judge ~56.6% near chance; vindicates the source project's deterministic grading | strong-evidence | stable | 2026-08-21 |
| EXT-LEGAL-001 | **Anthropic** — [Commercial Terms of Service §D.4 + Usage Policy (AUP)](https://www.anthropic.com/legal/commercial-terms) | prohibits training other models on Claude I/O without authorization | consensus | active | 2026-08-21 |
| EXT-LEGAL-002 | **OpenAI** — [OpenAI Terms of Use + Business Terms (output-training restriction)](https://openai.com/policies/terms-of-use) | Consumer ToU: 'Use Output to develop models that compete with OpenAI' is prohibited; Business Terms §3.3(e): may not 'use Output to develop artificial intelligence models that compete' except Permitted Exceptions (§17) | consensus | active | 2026-08-21 |
| EXT-LEGAL-003 | **Google** — [Gemini API Additional Terms of Service (output-training restriction)](https://ai.google.dev/gemini-api/terms) | 'You may not use the Services to develop models that compete with the Services' (Use Restrictions) | consensus | active | 2026-08-21 |
| EXT-OPS-001C | **Google** — [SRE Workbook ch.16 — Canarying Releases (restraint doctrine)](https://sre.google/workbook/canarying-releases/) | 'Use the simplest model that meets your technical and business objectives'; run ONE canary at a time; canary metrics must be causally attributable to the change | consensus | stable | 2026-08-21 |
| EXT-OPS-002 | **Breck et al.; Sculley et al.** — [ML Test Score rubric + Hidden Technical Debt in ML Systems](https://research.google/pubs/whats-your-ml-test-score-a-rubric-for-ml-production-systems/) | 28-test rubric, score=minimum across categories; adopt as annual self-audit | consensus | stable | 2026-08-21 |
| EXT-STATS-001 | **Miller; NCSS** — Miller 2024 'Adding Error Bars to Evals' + McNemar exact power (NCSS PASS ch.150) (`arXiv:2411.00640`) | clustered/paired SEs, power/MDE formulas; largest pure gap in the source project practice | strong-evidence | stable | 2026-08-21 |
| EXT-TESTBED-001 | **Andrej Karpathy** — [Neural-net sanity-gate recipe](https://karpathy.github.io/2019/04/25/recipe/) | correctness-only sanity gates before scaling up | consensus | stable | 2026-08-20 |
| NV-AIPERF-001 | **NVIDIA** — [AIPerf (benchmarking client; GenAI-Perf successor)](https://github.com/ai-dynamo/aiperf) | Endpoint-agnostic benchmarking vs any OpenAI-compatible endpoint; v0.12.0 adds agent workloads, Anthropic Messages endpoint, accuracy benchmarking; drop-in GenAI-Perf replacement | strong-evidence | active | 2026-08-21 |
| NV-EVALSDK-001 | **NVIDIA** — [NeMo Evaluator SDK docs + nel compare/gate tutorials](https://docs.nvidia.com/nemo/evaluator/latest/tutorials/compare) | McNemar paired testing, power/MDE tables, GO/NO-GO gate w/ 95% CIs | strong-evidence | active | 2026-08-21 |
| NV-INFERBENCH-001 | **NVIDIA** — [NIM LLM Benchmarking Guide + inference benchmarking blog series](https://docs.nvidia.com/nim/benchmarking/llm/latest/index.html) | Metrics, ISL/OSL sweeps, operating-point selection, sizing, $/M-token TCO; AIPerf-based | strong-evidence | active | 2026-08-21 |

## ADAPT

*Mechanics sound, decision layer missing — adapt per references/VENDOR_RECIPE_NOTES.md.*

| ID | Source | Claims we cite it for | Strength | Freshness | Verified |
|---|---|---|---|---|---|
| EXT-AGENT-001 | **Chen et al.; Yao et al.** — pass@k estimator (Chen 2021) + τ-bench pass^k reliability (Yao 2406.12045) (`arXiv:2406.12045`) | gpt-4o agent pass^1>60% collapses <25% at pass^8, identical tasks | strong-evidence | stable | 2026-08-21 |
| EXT-DETERM-001 | **Thinking Machines; SGLang; vLLM; llama.cpp** — Nondeterminism/batch-invariance package (Defeating Nondeterminism, arXiv:2506.09501, vLLM & SGLang docs, llama.cpp #4130) (`arXiv:2506.09501`) | reduction-order/GPU-state variance dominant; batch-invariance costs 34-110% throughput | strong-evidence | active | 2026-08-21 |
| EXT-EVAL-001 | **Anthropic** — [Anthropic eval-design documentation (incl. volume-over-curation heuristic)](https://docs.claude.com/en/docs/test-and-evaluate/develop-tests) | multidimensional explicit criteria, grader by task shape, edge-case checklists | consensus | active | 2026-08-21 |
| EXT-EVAL-003 | **Hamel Husain** — [Error-analysis-first eval process (field guide)](https://hamel.dev/blog/posts/field-guide/) | read traces, open-ended failure notes, synthesize taxonomy | heuristic | active | 2026-08-21 |
| EXT-EVAL-007 | **BIG-bench authors** — BIG-bench canary strings convention (`arXiv:2206.04615`) | cooperative-scraper exclusion convention for published task text | heuristic | stable | 2026-08-21 |
| EXT-FT-006 | **Luo et al.** — Catastrophic forgetting in fine-tuning (2308.08747, 2510.17776) (`arXiv:2308.08747`) | forgetting real, scale-trends non-obvious, merging doesn't reliably fix it | strong-evidence | stable | 2026-08-21 |
| EXT-OPS-001A | **AWS** — [SageMaker shadow testing](https://docs.aws.amazon.com/sagemaker/latest/dg/shadow-tests.html) | Mirrors a copy of live inference traffic to a shadow variant in real time; comparison/interpretation left to the user | consensus | stable | 2026-08-21 |
| EXT-OPS-001B | **Microsoft** — [Azure ML safe rollout (blue-green + mirrored traffic)](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-safely-rollout-online-endpoints) | Staged manual traffic shifting (small % → all) plus mirrored/shadow traffic (≤50%, one deployment, documented limits) | consensus | active | 2026-08-21 |
| EXT-PERF-001 | **vLLM project; DistServe (OSDI'24)** — vLLM benchmarks + DistServe goodput concept | inference benchmarking method + goodput concept for serving | strong-evidence | active | 2026-08-20 |
| EXT-PERF-002 | **Grafana (k6)** — [k6 API load-testing taxonomy](https://grafana.com/docs/k6/latest/testing-guides/test-types/) | smoke/load/stress/spike/soak test types; thresholds-as-SLOs | consensus | stable | 2026-08-21 |
| EXT-STOPPING-002 | **Lan & DeMets; PMC/NIH** — Clinical-trial adaptive design & DSMB pre-specification (Lan-DeMets spending, PMC3248853) (`PMC3248853`) | pre-register adaptation rule, DSMB executes it not investigator judgment | consensus | stable | 2026-08-20 |
| EXT-STOPPING-003 | **Loh & Nowozin; Jamieson & Talwalkar; Li et al.** — Racing and successive-halving screening (Hoeffding/Bernstein racing, Hyperband, ASHA) | ASHA-style rungs adopted for TRAIN screening, must be class-balanced | strong-evidence | stable | 2026-08-20 |
| EXT-SWITCHYARD-001 | **LangChain** — [LangChain Switchyard agent-routing benchmark](https://www.langchain.com/blog/switchyard-agent-routing-benchmark) | Break-even rule: min offload=judge_cost/(strong-weak); 74% cost cut, 93% accuracy retained | strong-evidence | snapshot | 2026-08-21 |
| EXT-UNSLOTH-001 | **Unsloth** — [Unsloth docs (NVIDIA-endorsed local fine-tuning path)](https://docs.unsloth.ai) | Only source for LoRA-vs-QLoRA criteria; NVIDIA delegates methodology here | strong-evidence | active | 2026-08-21 |
| EXT-VLLM-001 | **vLLM project** — [vLLM (engine + docs; batch-invariance opt-in)](https://github.com/vllm-project/vllm) | De-facto standard open serving engine; deterministic batch-invariant mode is OPT-IN (VLLM_BATCH_INVARIANT=1, CC>=8.0, reduced performance) | strong-evidence | active | 2026-08-21 |
| NV-AGENTICBLOGS-001 | **NVIDIA** — [Mastering Agentic Techniques: AI Agent Customization + AI Agent Evaluation](https://developer.nvidia.com/blog/mastering-agentic-techniques-ai-agent-customization/) | Evaluate-first ordering; verifiability/resources/maturity framework; TSR over accuracy | consensus | stable | 2026-08-21 |
| NV-ATIF-001 | **NVIDIA / Harbor community** — ATIF (agent trajectory interchange format) | Trajectory interchange format across NAT/Relay/Platform | strong-evidence | active | 2026-08-20 |
| NV-EVALRECIPE-001 | **NVIDIA** — [The Open Evaluation Standard (Nemotron 3 Nano evaluation recipe)](https://huggingface.co/blog/nvidia/nemotron-3-nano-evaluation-recipe) | Publish the complete evaluation recipe alongside results; methodological consistency with clear provenance rather than bit-wise identical outputs | strong-evidence | stable | 2026-08-21 |
| NV-FINETUNESTACK-001 | **NVIDIA** — NeMo AutoModel + NeMo RL + NeMo Customizer (fine-tuning stack) | LoRA-vs-SFT selection guidance (LoRA for 1–2 GPUs / fast iteration / multiple specialized versions); GPU sizing guidance | strong-evidence | active | 2026-08-21 |
| NV-GARAK-001 | **NVIDIA** — garak (LLM security probing tool) | Z-score-vs-calibration-bag pattern for security/regression baselines | strong-evidence | active | 2026-08-20 |
| NV-MODELOPTQAD-001 | **NVIDIA** — [Model Optimizer llm_qat guide (QAD as recommended accuracy-recovery strategy)](https://github.com/NVIDIA/Model-Optimizer/tree/main/examples/llm_qat) | 'QAD is Model Optimizer's recommended strategy for accuracy recovery after quantization' (verbatim); references NVFP4 (which the choosing-quant-methods decision page omits) | strong-evidence | active | 2026-08-21 |
| NV-MODELOPTRESEARCH-001 | **NVIDIA** — [Model Optimizer Researcher Guide (progressive eval subsets)](https://github.com/NVIDIA/Model-Optimizer/blob/main/examples/researcher_guide/README.md) | Binomial margin-of-error table by sample size; first-N ordering-bias warning | strong-evidence | active | 2026-08-21 |
| NV-NIMOBSERVABILITY-001 | **NVIDIA** — [NIM Logging & Observability reference](https://docs.nvidia.com/nim/large-language-models/latest/reference/logging-and-observability.html) | Prometheus /v1/metrics (vLLM passthrough), OTel traces, JSONL logs = production minimum | heuristic | active | 2026-08-21 |
| NV-NVFP4PLAYBOOK-001 | **NVIDIA** — [NVFP4 Quantization playbook (DGX Spark)](https://github.com/NVIDIA/dgx-spark-playbooks/blob/main/nvidia/nvfp4-quantization/README.md) | On-device 35B-MoE to NVFP4 in ~2h; W4A16 vs W4A4 recipe rule | strong-evidence | active | 2026-08-21 |
| NV-QADNEMOTRON-001 | **NVIDIA** — [Developing Nemotron 3.5 Lightning NVFP4 with QAD](https://developer.nvidia.com/blog/developing-nemotron-3-5-lightning-nvfp4-with-qad-using-nvidia-model-optimizer/) | Demonstrated >99% median-recovery PTQ bar; 95-99% deliberate QAD target; worked example | case-study | snapshot | 2026-08-21 |
| NV-RTXAIGARAGE-001 | **NVIDIA** — [RTX AI Garage blog (dataset-size thresholds)](https://blogs.nvidia.com/blog/rtx-ai-garage-fine-tuning/) | Dataset thresholds: 100-1,000 pairs PEFT / 1,000+ full FT | strong-evidence | stable | 2026-08-21 |
| NV-SWITCHYARD-001 | **NVIDIA** — [NeMo Switchyard repo, routing docs, and blog](https://github.com/NVIDIA-NeMo/Switchyard) | Weak/strong escalation router; 4 mechanisms; confirmations=2, fail-open, latch | strong-evidence | volatile | 2026-08-21 |
| NV-TOOLCALLTUTORIAL-001 | **NVIDIA** — NeMo tool-calling evaluation tutorial | 85/15 split + independent xlam golden set; 500+ synthetic samples to ~93% | strong-evidence | stable | 2026-08-20 |

## REFERENCE

*Consult, do not depend on.*

| ID | Source | Claims we cite it for | Strength | Freshness | Verified |
|---|---|---|---|---|---|
| EXT-EVAL-005 | **OpenAI / swebench.com** — [SWE-bench Verified curation](https://github.com/SWE-bench/SWE-bench) | human review 1699→500 tasks; solve rate 16%→33.2% from decontamination | strong-evidence | stable | 2026-08-21 |
| EXT-EVAL-008 | **OpenAI** — [Follow-up: 'Why SWE-bench Verified no longer measures frontier coding capabilities'](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/) | The publisher of the curated benchmark later declared it saturated for frontier claims and reported that a large share of a sampled hard-problem subset had flawed test cases rejecting functionally correct submissions; recommends a successor benchmark | strong-evidence | stable | 2026-08-21 |
| EXT-FT-002 | **Zhou et al.** — LIMA (style-alignment sample size) (`arXiv:2305.11206`) | n=1000 sizing is for broad style alignment, not narrow fixes | research-only | stable | 2026-08-21 |
| EXT-FT-007 | **LoopTool; CurateEvo; Chen et al.** — Error-driven data curation research cluster (LoopTool, CurateEvo, AlpaGasus) (`arXiv:2511.09148`) | promising unreviewed preprints; pattern matches the source project's design, pilot-grade only | research-only | active | 2026-08-20 |
| EXT-HW-001 | **Newegg; NVIDIA; Apple; RunPod; hardware-corner; community threads** — 2026-08-20 hardware/cloud price-verification snapshot | GPU/DRAM/cloud prices verified live amid AI memory crunch, weeks shelf-life | heuristic | snapshot | 2026-08-20 |
| EXT-JUDGE-001 | **Zheng et al. (LMSYS)** — MT-Bench LLM-as-judge agreement study (`arXiv:2306.05685`) | GPT-4-judge ~80% human agreement on open-ended chat preference | strong-evidence | stable | 2026-08-21 |
| EXT-JUDGE-003 | **arXiv:2606.19544 authors** — Reliability without Validity (judge κ-deflation study) (`arXiv:2606.19544`) | chance-corrected κ deflates judge quality 33-41pp; stable judge bias | contested | active | 2026-08-21 |
| EXT-LLAMACPP-001 | **ggml-org** — [llama.cpp (engine)](https://github.com/ggml-org/llama.cpp) | CPU/GPU GGUF engine; very active (multiple releases/day at verification); wide quantization-format support; single-slot serving suits determinism/provenance regimes | strong-evidence | active | 2026-08-21 |
| EXT-OPS-003 | **MLflow; Weights & Biases; DVC** — Experiment lineage tooling docs (MLflow/W&B/DVC) | provide versioning/lineage-by-reference; none has tamper-evidence | heuristic | stable | 2026-08-20 |
| EXT-OPS-004 | **Netflix/Google (Kayenta)** — [Kayenta automated canary analysis](https://github.com/spinnaker/kayenta) | Automated statistical canary judgment — the CEILING of canary automation, explicitly NOT the small-team default (SRE restraint doctrine applies) | heuristic | stable | 2026-08-20 |
| EXT-PERF-003 | **multiple (arXiv authors; ICAIF)** — Serving-sensitivity research cluster (LLM-42, MarginGate, Silent Hyperparameter, LLM Output Drift) (`arXiv:2605.19537`) | backend choice alone moves scores up to 16.6pp; fintech-domain LLM output-drift study (ICAIF) | research-only | active | 2026-08-20 |
| EXT-PYTORCH-SPARKFT-001 | **PyTorch (Meta/PyTorch Foundation)** — PyTorch.org DGX Spark fine-tune case study (synthetic CoT -> TorchTune -> BFCL eval) | Only end-to-end Spark fine-tune experiment with real before/after evaluation | heuristic | snapshot | 2026-08-20 |
| EXT-ROUTE-001 | **FrugalGPT/RouteLLM/AutoMix/HybridLLM authors** — Cascade/learned-router literature (FrugalGPT, RouteLLM, AutoMix, Hybrid LLM) (`arXiv:2305.05176`) | all four use learned gates; the source project's deterministic the deterministic-gate experiment gate is novel | strong-evidence | stable | 2026-08-21 |
| EXT-SGLANG-001 | **SGLang / LMSYS** — [SGLang (engine; deterministic-inference mode)](https://github.com/sgl-project/sglang) | Deterministic mode via Thinking Machines batch-invariant kernels; documented 25–45% slowdown, recommended for debugging/reproducibility | strong-evidence | active | 2026-08-21 |
| EXT-STOPPING-001 | **Wald; Fischer & Ramdas** — Wald SPRT + always-valid sequential testing (incl. confidence sequences, Waudby-Smith & Ramdas 2103.06476) (`arXiv:2410.16076`) | SPRT sequential test; dominated by exact counting on the source project's clustered data | contested | stable | 2026-08-21 |
| EXT-TESTBED-002 | **Microsoft; Kaplan et al.** — Small-to-large transfer literature (muP, scaling laws) (`arXiv:2001.08361`) | transfer validated only for smooth continuous metrics, not discrete pass/fail | strong-evidence | stable | 2026-08-21 |
| EXT-TESTBED-003 | **Maia Polo et al.; Vivek et al.; multiple** — Efficient-eval/small-model-set reliability literature (tinyBenchmarks, Anchor Points, IRT-reliability, test-pyramid) (`arXiv:2607.15190`) | scalable estimators can produce unreliable item/ranking inferences at small N | contested | active | 2026-08-21 |
| NV-COSTTCO-001 | **NVIDIA** — [Benchmarking LLM Inference Costs (cost/TCO blog)](https://developer.nvidia.com/blog/benchmarking-llm-inference-costs-for-smarter-scaling-and-deployment/) | $/M-token formula chain, Pareto precision comparison, datacenter-scale assumptions | heuristic | stable | 2026-08-20 |
| NV-CURATORDESIGNER-001 | **NVIDIA** — NeMo Curator + Data Designer (data curation & synthetic data tooling) | Pretraining-scale cleaning/dedup/decontamination; beta schema-driven synthetic data | heuristic | active | 2026-08-20 |
| NV-DYNAMOAICONFIG-001 | **NVIDIA** — Dynamo profiler + AIConfigurator | Datacenter operating-point automation and sizing; no RTX/GB10 data | heuristic | active | 2026-08-20 |
| NV-LEPTONBREV-001 | **NVIDIA** — DGX Cloud Lepton / Brev | Rentable multi-provider GPU marketplace/console; no local hardware on-ramp documented | heuristic | active | 2026-08-21 |
| NV-LINEAGEREGISTRY-001 | **NVIDIA** — [NGC Private Registry + NeMo Entity Store/Data Store](https://docs.nvidia.com/ngc/gpu-cloud/ngc-private-registry-user-guide/index.html) | Semver + per-version metrics; HF-compatible one-hop base_model/peft lineage fields | heuristic | stable | 2026-08-20 |
| NV-MODELOPTQUANT-001 | **NVIDIA** — [Model Optimizer: Choosing Quantization Methods + hf_ptq README](https://nvidia.github.io/Model-Optimizer/guides/_choosing_quant_methods.html) | Batch-size heuristics; 'FP8 first'; omits NVFP4 entirely | heuristic | stable | 2026-08-21 |
| NV-NAT-001 | **NVIDIA** — NeMo Agent Toolkit (NAT: nat eval, profiler, sizing calculator) | RAGAS/trajectory judges, token/latency profiler, whole-workflow sizing | heuristic | active | 2026-08-20 |
| NV-NEMOCLAW-001 | **NVIDIA** — NemoClaw / OpenShell agent sandbox | Credential-custody wrapper; host-side cost/quality Model Router; demo-grade | heuristic | volatile | 2026-08-20 |
| NV-NEMOPLATFORM-001 | **NVIDIA** — [NeMo Platform repo + docs](https://github.com/NVIDIA-NeMo/nemo-platform) | Integrated evaluate/secure/tune/build; Switchyard under Tune; Studio alpha | heuristic | volatile | 2026-08-21 |
| NV-NEMOTRONCC-LICENSE-001 | **NVIDIA** — Nemotron-CC quality-routing rule + Open Model License | Score >11 vs <=11 quality routing; license permits Nemotron outputs for training | heuristic | stable | 2026-08-20 |
| NV-NIMOPERATORCANARY-001 | **NVIDIA** — [NIM Operator KServe/Knative canary docs](https://docs.nvidia.com/nim-operator/latest/kserve.html) | Knative-revision traffic splitting; rollback mechanics delegated to Knative | heuristic | stable | 2026-08-20 |
| NV-SLMRESEARCH-001 | **NVIDIA Research** — [Small Language Models are the Future of Agentic AI](https://research.nvidia.com/labs/lpr/slm-agents/) | Intellectual backbone of SLM-default/LLM-fallback cascade thesis | heuristic | stable | 2026-08-20 |
| NV-SPARKPERF-001 | **NVIDIA** — [DGX Spark User Performance Guide](https://github.com/NVIDIA/dgx-spark-playbooks/blob/main/nvidia/connect-two-sparks/assets/performance_benchmarking_guide.md) | Offline/online benchmark procedure, 4 engines, ttft/tpot/itl/e2el, concurrency=1 | heuristic | snapshot | 2026-08-20 |
| NV-SPARKPLAYBOOKS-001 | **NVIDIA** — [DGX Spark playbooks corpus (repo + build.nvidia.com/spark)](https://github.com/NVIDIA/dgx-spark-playbooks) | 46 install-verify-cleanup tutorials, no eval playbook, no sequencing | heuristic | volatile | 2026-08-20 |
| NV-TAO-HPO-001 | **NVIDIA** — TAO Toolkit AutoML HPO guidance | Only full HPO methodology NVIDIA publishes: Hyperband/ASHA/BOHB/PBT selection | heuristic | stable | 2026-08-20 |
| NV-TRTLLM-001 | **NVIDIA** — [TensorRT-LLM (engine)](https://github.com/NVIDIA/TensorRT-LLM) | NVIDIA-native engine; active (1.3.0rc-series on NGC 2026-08); NIM has moved its default backend to vLLM | heuristic | active | 2026-08-21 |
| NV-WORKBENCH-001 | **NVIDIA** — [AI Workbench + Claude Code sandbox quickstarts](https://docs.nvidia.com/ai-workbench/user-guide/latest/quickstart/quickstart-claude-sandbox.html) | Git-versioned envs across RTX/Spark/Brev; agent sandboxing; no run/eval tracking by design | heuristic | active | 2026-08-20 |

## DEPRECATED

*Do not adopt. Recorded to prevent re-adoption; supersession is recorded, never deleted.*

| ID | Source | Claims we cite it for | Strength | Freshness | Verified |
|---|---|---|---|---|---|
| NV-DATAFLYWHEEL-001 | **NVIDIA** — [Data Flywheel Blueprint README](https://github.com/NVIDIA-AI-Blueprints/data-flywheel) | log-curate-tune-judge-human-gated promotion loop; 'flashlight, not autopilot' | snapshot | snapshot | 2026-08-21 |
| NV-DGXCLOUD-DEP-001 | **NVIDIA** — 'DGX Cloud' as rentable product | Repositioned as NVIDIA-internal; rentable destination now Lepton/Brev | snapshot | snapshot | 2026-08-21 |
| NV-EVALDOCTREE-DEP-001 | **NVIDIA** — NeMo Evaluator 2025-era doc tree (adapters/interceptors/params) | Superseded by SDK 0.3.x docs | snapshot | snapshot | 2026-08-21 |
| NV-GENAIPERF-DEP-001 | **NVIDIA** — [GenAI-Perf](https://github.com/triton-inference-server/perf_analyzer) | Superseded by AIPerf | snapshot | snapshot | 2026-08-21 |
| NV-LLMPTQ-DEP-001 | **NVIDIA** — llm_ptq example | Superseded by hf_ptq example (ModelOpt 0.46) | snapshot | snapshot | 2026-08-21 |
| NV-LLMROUTER-DEP-001 | **NVIDIA** — [LLM Router blueprint](https://github.com/NVIDIA-AI-Blueprints/llm-router) | Superseded by NeMo Switchyard | snapshot | snapshot | 2026-08-21 |
| NV-MODELOPTRENAME-DEP-001 | **NVIDIA** — TensorRT Model Optimizer (old name/docs domain) | Renamed to NVIDIA Model Optimizer at 0.40, new docs domain | snapshot | snapshot | 2026-08-21 |
| NV-NEMOALIGNER-DEP-001 | **NVIDIA** — NeMo-Aligner | Superseded by NeMo RL | snapshot | snapshot | 2026-08-21 |
| NV-NIMTRTLLM-DEP-001 | **NVIDIA** — NIM TensorRT-LLM backend | Superseded by NIM vLLM backend | snapshot | snapshot | 2026-08-21 |
| NV-RTXAITOOLKIT-DEP-001 | **NVIDIA** — RTX AI Toolkit | Only official RTX fine-tune-to-deploy workflow; died with no successor | snapshot | snapshot | 2026-08-21 |

## CASE

*Internal empirical case studies — narratives live in examples/.*

| ID | Source | Claims we cite it for | Strength | Freshness | Verified |
|---|---|---|---|---|---|

## Deprecation / supersession watchlist

Standing section: things that were current, no longer are, and still get
recommended by stale material. Check here before adopting any vendor recipe.

| ID | What | Trap |
|---|---|---|
| NV-DATAFLYWHEEL-001 | Data Flywheel Blueprint README | Verified live (W1): Apr-2026 deprecation notice verbatim, 'reference only', no successor named. Loop design (log→stratify→tune→judge→human-gated promotion; 'flashlight, not autopilot') remains citable as a design reference. |
| NV-DGXCLOUD-DEP-001 | 'DGX Cloud' as rentable product | Verified (W1): rentable destinations present as DGX Cloud Lepton and Brev; 'DGX Cloud' proper no longer presents as a rentable product. |
| NV-EVALDOCTREE-DEP-001 | NeMo Evaluator 2025-era doc tree (adapters/interceptors/params) | Verified (W1): /latest/ redirects to /nightly/; versioned static doc paths do not exist; 2025-era adapters/interceptors URLs dead. Cite /nightly/ paths with as-of dates. |
| NV-GENAIPERF-DEP-001 | GenAI-Perf | Verified live (W1): perf_analyzer README carries the deprecation warning verbatim, pointing to AIPerf (github.com/ai-dynamo/aiperf, drop-in replacement per its migrating.md). |
| NV-LLMPTQ-DEP-001 | llm_ptq example | Verified (W1): examples/llm_ptq 404s; hf_ptq live. Supersession is inferred from the 404 + directory listing — no in-repo prose migration note exists. |
| NV-LLMROUTER-DEP-001 | LLM Router blueprint | Verified (W1): deprecation notice (added 2026-07-08) lives on the 'experimental' branch README — which IS the default branch, so visitors land on it; 'main' carries no notice. Points to Switchyard. |
| NV-MODELOPTRENAME-DEP-001 | TensorRT Model Optimizer (old name/docs domain) | Verified (W1): rebrand announced 2025-12-08 in README; old GitHub-Pages docs subsite hard-404s; old repo slug transparently redirects (GitHub rename). Update docs links, repo links survive. |
| NV-NEMOALIGNER-DEP-001 | NeMo-Aligner | Verified (W1): deprecated in favor of NeMo RL (github.com/NVIDIA-NeMo/RL). |
| NV-NIMTRTLLM-DEP-001 | NIM TensorRT-LLM backend | Verified (W1, PARTIAL — release-notes level): NIM vLLM backend is the going-forward path; Spark still ships a TRT-LLM playbook alongside. |
| NV-RTXAITOOLKIT-DEP-001 | RTX AI Toolkit | Verified (W1): archived:true; README deprecation line present; no successor named. |

Additional standing traps recorded on active sources: the hosted OpenAI Evals
platform sunsets 2026-11-30 (EXT-EVAL-002); NVIDIA NeMo Evaluator docs `/latest/`
redirects to `/nightly/` with no pinned tree (NV-EVALSDK-001); the Model
Optimizer quantization *decision page* omits NVFP4 while the same repo recommends
it elsewhere (NV-MODELOPTQUANT-001 vs NV-MODELOPTQAD-001) — date-weight vendor
decision pages against the vendor's own current practice.

