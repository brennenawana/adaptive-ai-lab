# Vendor Recipe Notes

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> Index: [../README.md](../README.md) · Record of record: [sources.yaml](sources.yaml)

Per-recipe adaptation notes for every source classified `FOLLOW` or `ADAPT` in [sources.yaml](sources.yaml). Read this file whenever a chapter cites a `[FOLLOW: SRC-ID]` or `[ADAPT: SRC-ID]` callout and you need to know exactly what the vendor gives you, what it does not, and what to check before you rely on it.

Each entry states: what the source solves, what it does not, what you must validate on your own project before trusting it, and the version-pin or staleness trap a reader of the raw document would not otherwise catch. `REFERENCE`- and `CASE`-classified sources are covered in [sources.yaml](sources.yaml) and the examples library, and are skipped here except where a `REFERENCE`-tier source carries a trap sharp enough to warrant a note — collected in [§ Notable REFERENCE-tier traps](#notable-reference-tier-traps). Every `DEPRECATED`-classified source appears in the standing [§ Deprecation watchlist](#deprecation-watchlist), regardless of trap-worthiness, because the entire point of that section is "don't rediscover this."

**How to read a verdict**, per [GLOSSARY: vendor verdicts](../GLOSSARY.md#vendor-verdicts): **FOLLOW** = mature, apply the vendor's method as documented. **ADAPT** = mechanics sound, decision layer missing — this file states exactly what to substitute. Both carry an as-of date; nothing below is evergreen, and volatile/pre-alpha sources are flagged explicitly.

---

## Evaluation methodology, statistics & judges

### NV-EVALSDK-001 — NeMo Evaluator SDK docs + `nel compare`/`nel gate` tutorials
*FOLLOW · verified 2026-08-21 · ch. 03, 04, 14*

- **Solves:** McNemar's exact test on discordant pairs; a published power/MDE table (10 discordant pairs → ~28% MDE, 1,000 → ~2.8%); `nel gate`'s GO/NO-GO/INCONCLUSIVE verdict with a 95% CI on the paired delta; `INSUFFICIENT_EVIDENCE` below 10 paired items.
- **Does not solve:** does not choose your thresholds (tiers and drop limits are user-supplied); requires **identical prompt templates** across compared runs — it cannot evaluate a prompt change; assumes independent items, with no clustering/ICC correction — pair with [EXT-STATS-001] whenever outcomes cluster.
- **Validate before relying on it:** confirm the doc-tree path resolves to current content at read time; confirm your own suite's clustering structure before trusting the reported MDE as-is.
- **Version/pin & traps:** SDK v0.3.0 (2026-06-03) was still latest at verification. **No pinned `/latest/` doc tree exists** — the URL 308-redirects to `/nightly/`; cite `/nightly/` paths with an as-of date, never `/latest/` as if stable. Distinct from the enterprise NeMo Microservices Evaluator, which shares the name but carries no statistics.

### EXT-AMAZON-LLMSTATS-001 — LLM-Accuracy-Stats (ICLR 2026)
*FOLLOW · verified 2026-08-21 · ch. 03, 04*

- **Solves:** the paired McNemar method `nel compare` productized; usable standalone against lm-eval-format output if you are not on the NeMo stack.
- **Does not solve:** no packaging/CLI beyond the reference implementation; no clustering correction.
- **Validate before relying on it:** confirm your output format matches the reference code's expectations; re-derive the formulas from the paper if adapting to a different harness.
- **Version/pin & traps:** stable citation is arXiv:2602.10144. The code repository was **archived read-only 2026-05-08** — a frozen, usable reference implementation that will not receive fixes.

### EXT-STATS-001 — Miller, "Adding Error Bars to Evals" + McNemar exact power
*FOLLOW · verified 2026-08-21 · ch. 04*

- **Solves:** clustered/paired SE derivations and power/MDE formulas — the single most load-bearing statistics source behind chapter 04's ICC → DEFF → N_eff → MDE chain.
- **Does not solve:** supplies derivations, not a ready-made tool — implement against your own suite.
- **Validate before relying on it:** identify your clustering unit and **estimate its ICC from your own data**; never assume ICC = 0.
- **Version/pin & traps:** arXiv:2411.00640; stable paper citation, low staleness risk.

### EXT-EVAL-004 — EvalGen / "Who Validates the Validators"
*FOLLOW · verified 2026-08-21 · ch. 03*

- **Solves:** the empirical basis for treating [criteria drift](../GLOSSARY.md#criteria-drift) as expected rather than a discipline failure — criteria and ground truth co-evolve as graders see real output.
- **Does not solve:** does not itself prescribe a versioning mechanism — chapter 03's suite-release discipline is the playbook's answer to the finding.
- **Validate before relying on it:** n/a for citation; cite as a finding about the process.
- **Version/pin & traps:** n=9 practitioner study — directional, strong-evidence, not a large-N result. arXiv:2404.12272, stable.

### EXT-EVAL-006 — GSM1k contamination study
*FOLLOW · verified 2026-08-21 · ch. 03*

- **Solves:** quantifies contamination's effect size (up to 8pp accuracy drop on a fresh benchmark; contamination r² = 0.36) — the evidentiary basis for disjoint-seed / private-holdout discipline.
- **Does not solve:** a general contamination-detection method — the paper's own approach (build a genuinely fresh comparison benchmark) is heavy, not a lightweight check you can run on demand.
- **Validate before relying on it:** n/a for citation; if replicating, budget for actually building a fresh comparison set.
- **Version/pin & traps:** arXiv:2405.00332; stable.

### EXT-JUDGE-002 — JudgeBench
*FOLLOW · verified 2026-08-21 · ch. 03*

- **Solves:** the load-bearing evidence for "deterministic grading over judges wherever output is objectively verifiable" — an unvalidated LLM judge scores near chance (~56.6%) on objectively verifiable tasks.
- **Does not solve:** says nothing about judge quality on open-ended/preference tasks — a different domain (see the REFERENCE-tier MT-Bench and κ-deflation studies below).
- **Validate before relying on it:** n/a for citation.
- **Version/pin & traps:** arXiv:2410.12784; numbers verified from the paper's own tables, not a secondary summary.

### EXT-EVAL-002 — OpenAI eval guidance
*FOLLOW · verified 2026-08-21 · ch. 03*

- **Solves:** the objective → dataset → metrics → run → iterate structure, plus explicit guidance to validate a model-grader against human labels before trusting it for cost/latency optimization.
- **Does not solve:** the OpenAI-specific tooling framing does not apply once the hosted product sunsets — see the trap below.
- **Validate before relying on it:** cite the methodology; do not build new work against the hosted platform.
- **Version/pin & traps:** **the hosted OpenAI Evals platform becomes read-only 2026-10-31 and shuts down 2026-11-30.** Cite the methodology as current, never the platform.

### EXT-EVAL-005 — SWE-bench Verified curation
*REFERENCE (downgraded from FOLLOW in this pass) · verified 2026-08-21 · ch. 03*

**Downgrade record:** the publisher's own ~Feb-2026 follow-up ([EXT-EVAL-008] in
sources.yaml) declares the benchmark saturated for frontier-capability claims and
reports flawed test cases in a hard-problem sample. The historical curation figures
below remain valid — and the follow-up itself strengthens chapter 03's point that
instrument validation never ends.

- **Solves:** a documented, numeric example of the payoff of human eval-set curation (1,699 candidate tasks reviewed down to a 500-task verified subset; corrected solve rate moved from 16% to 33.2% once decontaminated) — cite as a worked instance of "curation moves the measured number," not as a live capability claim.
- **Does not solve:** current frontier-capability comparison — the benchmark's own publisher has since reported its remaining headroom as compressed, with a nontrivial share of its hardest-problem sample carrying flawed test cases. Treat it as a case study of the curation process, not a live leaderboard.
- **Validate before relying on it:** before citing a current pass-rate from this suite as a capability claim, re-verify the suite's saturation status.
- **Version/pin & traps:** the original announcement now 403s to automated fetch; cite the SWE-bench GitHub repository or swebench.com instead, which mirror the same figures and remain reachable.

### EXT-EVAL-001 — Anthropic eval-design documentation
*ADAPT · verified 2026-08-21 · ch. 03*

- **Solves:** multidimensional explicit grading criteria, grader-selection by task shape (exact-match / similarity / LLM-judge), and a volume-over-curation heuristic ("more questions with slightly lower signal beats fewer high-quality hand-graded questions").
- **Does not solve:** does not resolve the volume-vs-curation tension against EXT-EVAL-005's curation evidence — chapter 03 keeps both positions visible with a decision rule (grading-signal quality × item cost × stakes tier); it does not pick a silent winner.
- **Validate before relying on it:** check the volume heuristic against your own stakes tier — Tier 3 work may need EXT-EVAL-005-style curation instead.
- **Version/pin & traps:** the docs.anthropic.com host is being retired in favor of platform.claude.com — the URL now 301-redirects; update citations to the new host.

### EXT-EVAL-003 — Hamel Husain, error-analysis-first eval process
*ADAPT · verified 2026-08-21 · ch. 03*

- **Solves:** the bottom-up, error-analysis-first taxonomy-building procedure (read real traces, write open-ended failure notes, synthesize a closed taxonomy) that chapter 03's task-ontology derivation follows.
- **Does not solve:** does not itself supply a stratification or ground-truth-design method past the taxonomy step.
- **Validate before relying on it:** n/a for citation.
- **Version/pin & traps:** **cite the field-guide post (2025-03-24), not the earlier 2024-03-29 "evals" post** — different posts by the same author; the formal bottom-up/top-down framing lives only in the field-guide post.

### EXT-EVAL-007 — BIG-bench canary strings convention
*ADAPT · verified 2026-08-21 · ch. 03, 13*

- **Solves:** the convention (unique marker plus a do-not-train sentence) for excluding published eval content from cooperative scrapers and training corpora — direct input to a [canary string](../GLOSSARY.md#canary-string) policy.
- **Does not solve:** does not stop non-cooperative scrapers; an honor-system convention, not an enforcement mechanism.
- **Validate before relying on it:** confirm which crawlers/aggregators actually honor the convention before treating it as a leakage control rather than a leakage detector.
- **Version/pin & traps:** arXiv:2206.04615 (2022); stable.

### NV-EVALRECIPE-001 — "The Open Evaluation Standard" (evaluation-recipe publication practice)
*ADAPT · verified 2026-08-21 · ch. 04, 13*

- **Solves:** models the practice of publishing a complete evaluation recipe (full configuration) alongside results, framed as "methodological consistency with clear provenance," not bit-wise reproducibility.
- **Does not solve:** **does NOT document a pin-containers/sampling-params/judges discipline, and does NOT document a smoke-test discipline** — two claims once attributed to this source were checked live and are absent under any wording variant tried. Do not cite this source for either.
- **Validate before relying on it:** if you want the pin-everything and smoke-test disciplines this playbook recommends, source them from your own experiment-contract practice (ch. 04), not from this page.
- **Version/pin & traps:** published 2025-12-17; the recipe-publication framing is real and citable — the two corrected claims are a standing trap for anyone reusing an older note about this source.

---

## Experiment design, stopping & measurement validity

### EXT-STOPPING-002 — Clinical-trial adaptive design & DSMB pre-specification
*ADAPT · verified 2026-08-20 · ch. 00, 04*

- **Solves:** the consensus principle behind pre-registration-with-consequences — a pre-registered adaptation rule is executed by a designated party, never improvised by the investigator mid-run.
- **Does not solve:** the specific spending-function machinery (Lan-DeMets alpha-spending, a fixed continuation-probability convention) is **explicitly dropped** in this playbook; those specific numeric conventions could not be verified against this citation. This playbook's own curtailed-exact-counting mechanism (ch. 04) is the adopted substitute, not this paper's spending functions.
- **Validate before relying on it:** if adopting alpha-spending directly, re-derive the spending function from a primary clinical-trials-statistics source — do not import a specific numeric convention from this citation.
- **Version/pin & traps:** PMC3248853; stable, principle-only support.

### EXT-STOPPING-003 — Racing and successive-halving screening (Hoeffding/Bernstein racing, Hyperband, ASHA)
*ADAPT · verified 2026-08-20 · ch. 04, 05*

- **Solves:** the external basis for stratum-balanced racing/successive-halving on the iterate split — a well-studied algorithm family for ranking candidates cheaply.
- **Does not solve:** does not itself guarantee class balance — this playbook's addition is that rungs **must be class-balanced** (Bernstein racing applied at the class level), which the base literature does not require by default.
- **Validate before relying on it:** if implementing a rung schedule, verify your own implementation enforces stratum balance at every rung — a naive port of standard ASHA/Hyperband code will not do this automatically.
- **Version/pin & traps:** 2013–2020 span of foundational papers; stable. NVIDIA's only full HPO methodology publication (TAO Toolkit, REFERENCE-tier) is computer-vision-only, but its ASHA/Hyperband selection logic reads across.

### EXT-AGENT-001 — pass@k estimator + τ-bench pass^k reliability
*ADAPT · verified 2026-08-21 · ch. 03, 04*

- **Solves:** the formal distinction this playbook's reliability vocabulary is built on — [pass-at-k vs pass-to-the-k](../GLOSSARY.md#pass-at-k-vs-pass-to-the-k) — plus the τ-bench evidence that a stochastic agent can score high pass@1 (>60%) and collapse under pass^k (below 25% at k=8) on identical tasks.
- **Does not solve:** supplies no suite or task set of its own — you compute pass^k on your own declared subset.
- **Validate before relying on it:** measure frontier-tier pass^k (e.g., k = 3–5) on a declared subset before making any reliability claim about a stochastic system — pass@1 alone cannot support one.
- **Version/pin & traps:** arXiv:2406.12045 (τ-bench, 2024-06); the pass@k estimator itself dates to Chen et al. 2021 — cite both.

### EXT-DETERM-001 — Nondeterminism / batch-invariance package
*ADAPT · verified 2026-08-21 · ch. 02, 03, 06*

- **Solves:** the mechanism behind measured session/restart nondeterminism (reduction-order and GPU-state sensitivity, KV-cache placement), and the fact that batch-invariant deterministic modes exist in major runtimes but are **opt-in and cost throughput** (documented 25–45% slowdown in one runtime's deterministic mode; a comparable cost in another's).
- **Does not solve:** does not bound *your* system's reproducibility — that requires your own restart/concurrency/cross-host probes (ch. 02), not an assumption that the paper's findings transfer numerically to your stack.
- **Validate before relying on it:** run your own reproducibility probes before scoping a comparability claim; do not assume batch-invariant mode is enabled unless you have verified the flag/config yourself.
- **Version/pin & traps:** primary paper arXiv:2506.09501 (2025-09; the paper's own title frames the mechanism as "numerical sources," not "reduction-order"). Opt-in flag names and compute-capability floors are active-development details — re-verify against your runtime's current release before citing a specific flag.

---

## Fine-tuning, quantization & data

### EXT-FT-001 — RAG-vs-fine-tuning comparison trio
*FOLLOW · verified 2026-08-20 · ch. 07, 09*

- **Solves:** three independent studies agreeing that retrieval/prompt-first is the right default for factual/citation tasks — the external evidence behind the [intervention ladder](../GLOSSARY.md#intervention-ladder)'s ordering.
- **Does not solve:** does not cover the conditions where fine-tuning wins (format/behavior/skill internalization, latency/cost at volume) — argued separately in chapter 09, not from this source.
- **Validate before relying on it:** if your task is not factual/citation-shaped, this trio's conclusion may not transfer — check task shape first.
- **Version/pin & traps:** arXiv:2403.01432 (EMNLP 2024) plus two companion papers; stable.

### EXT-FT-003 — QLoRA
*FOLLOW · verified 2026-08-21 · ch. 09, 11*

- **Solves:** VRAM floor figures for quantized fine-tuning by model size — a sizing input for ch. 09/11.
- **Does not solve:** hyperparameter selection (rank, alpha, target layers) — see EXT-UNSLOTH-001.
- **Validate before relying on it:** cross-check the paper's floors against your actual framework's memory overhead (optimizer states, activation checkpointing) before sizing a purchase.
- **Version/pin & traps:** arXiv:2305.14314; floors cross-checked against EXT-UNSLOTH-001's live docs and matched exactly at last verification.

### EXT-FT-005 — LoRA quality package (LoRA Learns Less/Forgets Less + LoRA Without Regret)
*FOLLOW · verified 2026-08-21 · ch. 09*

- **Solves:** reconciles the LoRA-vs-full-FT quality contradiction by regime — all-layer LoRA approaches full-FT quality at post-training scale, at roughly two-thirds the FLOPs.
- **Does not solve:** does not resolve the question in every regime — the earlier paper's single-model-scope caveat is the boundary condition. Read both papers' scope statements before generalizing past post-training-scale, all-layer LoRA.
- **Validate before relying on it:** outside the papers' tested regime (very small models, partial-layer LoRA), treat the equivalence claim as unverified for your setup.
- **Version/pin & traps:** arXiv:2405.09673 (2024) plus a 2025-09-29 companion piece; stable.

### EXT-FT-006 — Catastrophic forgetting in fine-tuning
*ADAPT · verified 2026-08-21 · ch. 09*

- **Solves:** the evidentiary basis for mandating a **full-suite** regression gate after any fine-tune, never just the target-behavior slice — forgetting is real, its scale-trends are non-obvious, and model merging does not reliably fix it.
- **Does not solve:** does not supply your regression suite — pair with chapter 03's [regression suite vs capability suite](../GLOSSARY.md#regression-suite-vs-capability-suite) distinction.
- **Validate before relying on it:** run your complete regression suite (not a sampled slice), paired (ch. 04), before and after any fine-tune.
- **Version/pin & traps:** arXiv:2308.08747 (2023) plus a 2025 follow-up; stable.

### EXT-UNSLOTH-001 — Unsloth docs
*ADAPT · verified 2026-08-21 · ch. 07, 09*

- **Solves:** the only complete LoRA-vs-QLoRA decision criteria and hyperparameter starting points in this corpus (all-major-linear-layer targeting; rank 8–128, 16/32 typical; alpha ≈ 2×rank) — NVIDIA delegates its own fine-tuning methodology here rather than publishing its own.
- **Does not solve:** sample-size / minimum-n guidance (an open field gap, stated as such in ch. 09); does not validate against your task's eval suite — these are generic starting points, not calibrated defaults.
- **Validate before relying on it:** treat rank/alpha as a [`[PARAMETER]`](../GLOSSARY.md#a-to-h-classification) to sweep on your iterate split, not a fixed value; confirm the VRAM floors against your actual framework.
- **Version/pin & traps:** VRAM floor table matched EXT-FT-003 exactly at last check (9B: 6.5GB QLoRA / 24GB LoRA; 27B: 22GB / 64GB; 70B: 41GB / 164GB, stated as absolute minimums). Multi-GPU support status changed between checks (now "works, better version coming" — was "coming soon" only) — re-verify before depending on it. **Unsloth publishes no dates anywhere on its docs site** — re-check content itself, not a timestamp, each pass.

### NV-RTXAIGARAGE-001 — RTX AI Garage blog (dataset-size thresholds)
*ADAPT · verified 2026-08-21 · ch. 09, 14*

- **Solves:** a concrete, sourced dataset-size threshold for the PEFT-vs-full-FT decision (100–1,000 prompt-sample pairs → PEFT; 1,000+ → full FT).
- **Does not solve:** style-alignment-scale sizing or narrow-behavioral-fix minimums (see the LIMA REFERENCE-tier trap note below) — remains an open field gap.
- **Validate before relying on it:** treat these thresholds as priors for a cold-start parameterization (ch. 01 procedure), not a substitute for your own ablation.
- **Version/pin & traps:** correct host is **blogs.nvidia.com**, not developer.nvidia.com/blog — an easy mis-citation. Published 2025-12-15; thresholds confirmed exact at last check.

### NV-TOOLCALLTUTORIAL-001 — NeMo tool-calling evaluation tutorial
*ADAPT · verified 2026-08-20 · ch. 03, 09*

- **Solves:** a concrete worked split pattern (85/15 train/eval plus an independent golden set) and a data-volume-to-accuracy anchor (500+ synthetic samples reaching ~93% on that specific task) for tool-calling fine-tunes.
- **Does not solve:** generalization to non-tool-calling tasks; no variance/confidence statement around the 93% figure.
- **Validate before relying on it:** treat the 93% figure as this tutorial's own result, not a transferable guarantee — measure on your own tool-calling eval before citing an expected accuracy.
- **Version/pin & traps:** no version/date metadata recorded — re-check the current page before quoting numbers; NeMo doc trees have moved before (see the [Deprecation watchlist](#deprecation-watchlist)).

### NV-FINETUNESTACK-001 — NeMo AutoModel + NeMo RL + NeMo Customizer
*ADAPT · verified 2026-08-21 · ch. 07, 09*

- **Solves:** LoRA-vs-SFT selection guidance (Customizer docs: LoRA for 1–2 GPUs / fast iteration / multiple specialized adapters; full SFT for 4+ GPUs / maximum performance / production).
- **Does not solve:** **early-stopping numeric defaults (val_loss monitor, patience 10, min-delta 0.001) are NOT documented Customizer guidance** — they are code-level defaults in the open-source NeMo training framework; whether the hosted Customizer microservice actually inherits them is unconfirmed.
- **Validate before relying on it:** **do not cite this source for the early-stopping numbers as published vendor doctrine.** If adopting them, cite the framework source directly and treat "Customizer inherits these defaults" as an assumption to verify against your own run logs.
- **Version/pin & traps:** Kubernetes-footprint microservice — weigh the operational cost of the deployment target independent of the methodology question. This early-stopping misattribution is the single most important correction surfaced by live re-verification in this source set.

### NV-QADNEMOTRON-001 — quantization-aware distillation worked example on a current-generation NVIDIA model
*ADAPT · verified 2026-08-21 · ch. 03, 07*

- **Solves:** a concrete, demonstrated quantization-acceptance bar — over 99% median accuracy recovery targeted for PTQ-only shipping; 95–99% is a *deliberate* PTQ design target (not a fallback) when a quantization-aware-distillation recovery stage is planned; a full worked example (96.33% → 99.72% median recovery, 10 of 11 benchmarks improved).
- **Does not solve:** demonstrated practice on the vendor's own model/benchmark suite, not published doctrine applicable by rule to arbitrary tasks — re-derive the acceptance bar against your own task evals.
- **Validate before relying on it:** run the same PTQ → (optional recovery stage) → eval sequence against your own task suite before adopting a numeric bar; do not import the 99% / 95–99% split without re-measuring.
- **Version/pin & traps:** page was 3 days old at verification (published, then checked days later) — re-verify before long-term citation; this is demonstrated-not-doctrine per its `case-study` evidence-strength label.

### NV-NVFP4PLAYBOOK-001 — NVFP4 quantization playbook (DGX Spark)
*ADAPT · verified 2026-08-21 · ch. 07*

- **Solves:** an on-device quantization recipe (roughly two hours for a 35B-class mixture-of-experts model) and a workload-shape rule — a wider-activation format for interactive/low-concurrency decode, a narrower-activation format for higher-concurrency compute-bound serving.
- **Does not solve:** **provides no evaluation procedure or threshold** — the doc's own accuracy guidance is "we recommend running evaluations to verify... acceptable performance," with no dataset, metric, or acceptance bar attached.
- **Validate before relying on it:** supply your own acceptance gate (see NV-QADNEMOTRON-001 above for the demonstrated bar) — this source will not tell you when the quantized artifact is good enough.
- **Version/pin & traps:** **format is Blackwell-only** — an artifact produced with this recipe does not run on non-Blackwell hardware; quantize for the deployment target, not the dev box (ch. 02). File last touched roughly one month before this check — re-verify before relying on stated timings.

---

## Routing & cascades

### NV-SWITCHYARD-001 — NeMo Switchyard
*ADAPT · verified 2026-08-21 · ch. 08, 14*

- **Solves:** escalation-router semantics worth adopting as vocabulary — weak-first, the judge rates the actual completed output (not a prediction), a default confirmation streak before latching, per-session latch, and fail-open behavior where a judge failure **holds** (does not clear) the streak.
- **Does not solve:** **pre-alpha, "Not for production use" per the repository's own warning**; ships two-tier routing only — three-tier routing must be assembled by chaining routes or writing a custom policy selector; an announced trained "prefill router" is not shipped (zero matching paths on the main branch at last check).
- **Validate before relying on it:** treat as reference semantics for your own routing-policy vocabulary, not a production dependency, until the pre-alpha status changes.
- **Version/pin & traps:** a recent release was a substantial redesign (native server rewrite) that removed an earlier CLI/TUI/config-bundle surface — **if adapting example commands from an older reference, verify against the current release, not an older one.** Two-tier field names vary by route type — do not assume one universal field-name pair; check the specific route type's schema.

### EXT-SWITCHYARD-001 — LangChain Switchyard agent-routing benchmark
*ADAPT · verified 2026-08-21 · ch. 08, 11*

- **Solves:** the one quantitative routing-economics rule in this corpus — minimum offload share = judge_cost / (strong_cost − weak_cost) — plus a worked instance (74% cost cut, 93% accuracy retention against a strong-only baseline, mean escalation 6.9% across five runs, range 4.1–9.1%).
- **Does not solve:** the figures are conditioned on one specific weak/strong model pairing and task suite — they do not transfer to a different pairing or task distribution without remeasurement.
- **Validate before relying on it:** recompute the [break-even](../GLOSSARY.md#break-even) for your own weak/strong pairing and judge cost before adopting a target offload share; treat the published numbers as an illustration of the formula, not a target.
- **Version/pin & traps:** published 2026-08-11; all figures reconfirmed verbatim on live re-check.

---

## Inference performance & serving engines

### NV-INFERBENCH-001 — NIM LLM Benchmarking Guide
*FOLLOW · verified 2026-08-21 · ch. 04, 06, 11*

- **Solves:** metric definitions (TTFT, ITL, system-vs-per-user TPS), ISL/OSL sweep design by use case, concurrency-over-request-rate sweeps, and operating-point selection on the latency-throughput curve — the most mature vendor methodology in this corpus, warranting FOLLOW-by-the-book status.
- **Does not solve:** quality/capability evaluation (a separate instrument, ch. 03); the single-user/interactive (concurrency=1) regime, which the guide's sweep design does not isolate on its own — see [operating point](../GLOSSARY.md#operating-point).
- **Validate before relying on it:** confirm which doc version the guide resolves to at read time (it rolls forward); re-run the guide's warmup/concurrency procedure against your own endpoint before trusting absolute numbers.
- **Version/pin & traps:** "latest" resolved to guide v2.0.0 at verification; the earlier GenAI-Perf-based blog series is superseded and its commands no longer apply — use the current AIPerf-based guide only (see the [Deprecation watchlist](#deprecation-watchlist)).

### NV-AIPERF-001 — AIPerf
*FOLLOW · verified 2026-08-21 · ch. 06*

- **Solves:** endpoint-agnostic benchmarking against any OpenAI-compatible endpoint; a drop-in replacement for the deprecated client tool it succeeded; a recent release added agent workloads, an Anthropic Messages endpoint, and accuracy benchmarking.
- **Does not solve:** does not define acceptance thresholds — pair with your own operating-point selection (ch. 06).
- **Validate before relying on it:** confirm your harness's metric definitions match AIPerf's before comparing numbers across tools — metric definitions differ across benchmarking clients and numbers from different tools are not comparable.
- **Version/pin & traps:** v0.12.0 (2026-08-06); pin one tool and one metric-definition set across every tier you measure — mixing clients silently invalidates cross-tier comparisons.

### EXT-PERF-001 — vLLM benchmarks + DistServe goodput concept
*ADAPT · verified 2026-08-20 · ch. 06*

- **Solves:** the [goodput](../GLOSSARY.md#goodput) concept — throughput that meets a stated latency/quality constraint, versus raw throughput.
- **Does not solve:** the source paper's headline figures were not independently re-verified in this pass (the source PDF blocked automated fetch) — treat those specific numbers as unconfirmed; the concept is sound regardless.
- **Validate before relying on it:** re-derive goodput for your own latency/quality bar rather than importing the paper's numbers.
- **Version/pin & traps:** no single tool release to pin — a methodology and concept, not a versioned artifact.

### EXT-PERF-002 — k6 API load-testing taxonomy
*ADAPT · verified 2026-08-21 · ch. 06*

- **Solves:** a clean test-type vocabulary (smoke / average-load / stress / spike / soak / breakpoint) with thresholds-as-SLOs — directly reusable for the multi-tenant/SLA skeleton chapter 06 marks explicitly out of scope for this release.
- **Does not solve:** k6 itself is an HTTP load tool, not an LLM-aware benchmarking client — pair with AIPerf/NIM-guide metric definitions for token-level metrics.
- **Validate before relying on it:** confirm your load-testing tool actually implements all six test types before assuming the taxonomy transfers.
- **Version/pin & traps:** all six categories confirmed present and defined at last check; stable docs.

### EXT-VLLM-001 — vLLM (engine + docs)
*ADAPT · verified 2026-08-21 · ch. 02, 05, 06*

- **Solves:** the de-facto standard open serving engine for the throughput regime; a deterministic batch-invariant mode exists but is opt-in.
- **Does not solve:** determinism is not the default — a comparability claim across runs requires either the batch-invariant flag enabled or an accepted, measured [reproducibility boundary](../GLOSSARY.md#reproducibility-boundary) (ch. 02).
- **Validate before relying on it:** measure your own reproducibility boundary (restart/concurrency/cross-host probes) rather than assuming determinism from engine choice alone.
- **Version/pin & traps:** deterministic mode requires a specific environment flag and a minimum compute capability, and costs throughput versus standard operation — pin the flag state as part of [execution-system identity](../GLOSSARY.md#execution-system) whenever it matters to a comparison.

### NV-MODELOPTRESEARCH-001 — Model Optimizer researcher guide (progressive eval subsets)
*ADAPT · verified 2026-08-21 · ch. 03, 04*

- **Solves:** a binomial margin-of-error table by sample size for progressive/subsetted evaluation (roughly ±8pp at 140 items down to under ±1pp at full scale) plus an explicit first-N ordering-bias warning.
- **Does not solve:** does not itself supply a staged-gate procedure — pair with chapter 04's [screening vs inference](../GLOSSARY.md#screening-vs-inference) discipline to turn the table into a decision rule.
- **Validate before relying on it:** confirm your own corpus's ordering before trusting any first-N subset as representative — first-N selection is biased by construction unless the corpus is pre-shuffled.
- **Version/pin & traps:** table and warning confirmed verbatim at last check; no drift from prior verification.

### NV-MODELOPTQAD-001 — Model Optimizer QAD guide (accuracy-recovery recommendation)
*ADAPT · verified 2026-08-21 · ch. 07*

- **Solves:** states plainly that quantization-aware distillation is the vendor's recommended accuracy-recovery strategy after quantization, and is the only page in its repository that discusses the narrowest-precision format in this context.
- **Does not solve:** this recommendation lives in the accuracy-recovery guide, not the general quantization-method decision page (see the REFERENCE-tier trap note below) — a reader who consults only the decision page will not find it.
- **Validate before relying on it:** read both the decision page and this guide before choosing a quantization-plus-recovery strategy — they are inconsistent in format coverage as of this check.
- **Version/pin & traps:** no version/date metadata on the page; the decision-page lag this entry documents is itself the trap — re-check both pages together each time.

---

## Deployment & operations

### NV-NIMOBSERVABILITY-001 — NIM Logging & Observability reference
*ADAPT · verified 2026-08-21 (page updated 2026-08-19) · ch. 12*

- **Solves:** a documented production-observability floor: Prometheus-compatible
  metrics endpoint passing the serving engine's native metric vocabulary through
  unmodified; OpenTelemetry traces keyed to W3C `traceparent`; structured
  one-JSON-object-per-line logs.
- **Does not solve:** any experimentation telemetry minimum — it is a
  production-serving floor only. Chapter 12 §5.1–5.2 supplies the experimentation
  floor (lifecycle events, per-invocation stats, dual clocks, samplers).
- **Validate before relying on it:** confirm your serving stack actually passes
  engine-native metrics through rather than reinterpreting them; adopt ONE metric
  vocabulary across all tiers.
- **Version/pin & traps:** page updates frequently (last updated the day before
  verification); re-check endpoint/env-var names against your deployed version.

### EXT-OPS-001A — AWS SageMaker shadow testing
*ADAPT · verified 2026-08-21 · ch. 10*

- **Solves:** production-grade traffic-mirroring mechanics — a copy of live inference requests routed to a shadow variant in real time, with only the production variant's response returned to the caller.
- **Does not solve:** **comparison and interpretation of shadow results is left entirely to the user** — no statistics engine is built in.
- **Validate before relying on it:** bring your own paired-comparison design (ch. 02/04) for interpreting shadow-mode output; do not expect the tooling to tell you when a shadow variant is ready.
- **Version/pin & traps:** confirmed live at last check; no page-level revision date exposed.

### EXT-OPS-001B — Azure ML safe rollout (blue-green + mirrored traffic)
*ADAPT · verified 2026-08-21 · ch. 10*

- **Solves:** staged manual traffic shifting (small percentage → all, each step a separate action) plus a distinct mirrored-traffic (shadow) capability.
- **Does not solve:** mirroring is capped at 50% of traffic, limited to one deployment at a time, and **not supported on Kubernetes-based online endpoints** — know which constraint applies to your target before designing a canary around it.
- **Validate before relying on it:** confirm your specific endpoint type supports mirroring before planning a promotion pipeline around it.
- **Version/pin & traps:** last revised 2026-04-24 — recently maintained at last check.

### EXT-OPS-001C — Google SRE Workbook, "Canarying Releases"
*FOLLOW · verified 2026-08-21 · ch. 10, 12*

- **Solves:** the restraint doctrine chapter 10 adopts wholesale — use the simplest model that meets objectives, run exactly one canary at a time, and require canary metrics to be causally attributable to the change under test rather than confounded by unrelated system activity.
- **Does not solve:** does not address AI-specific deltas — nondeterministic outputs, verifier-in-the-loop quality metrics, provider-side model updates mid-canary — those are this playbook's own additions (ch. 10, labeled `inference`).
- **Validate before relying on it:** n/a for the restraint doctrine itself; validate the AI-specific extensions against your own promotion pipeline before trusting them as more than [doctrine-not-yet-exercised](../GLOSSARY.md#doctrine-not-yet-exercised).
- **Version/pin & traps:** a 2018 chapter, phrasing reconfirmed near-verbatim on re-check — durable, low staleness risk despite its age.

---

## Agentic decision framing

### NV-AGENTICBLOGS-001 — "Mastering Agentic Techniques" (Customization + Evaluation posts)
*ADAPT · verified 2026-08-21 · ch. 03, 07, 14*

- **Solves:** the strongest current vendor endorsement of evaluate-first ordering — "start with lightweight methods, invest early in evaluation, and layer in training-based techniques where measurement shows they're needed" — plus a companion post's task-success-rate-over-accuracy framing for agent evaluation.
- **Does not solve:** does not supply the machinery to act on the ordering — no stopping rules, no MDE, no gate mechanics; those are this playbook's own contribution.
- **Validate before relying on it:** n/a for citation; the ordering claim is corroborative, not a substitute for chapter 04's statistics.
- **Version/pin & traps:** the customization post and its companion evaluation post are **two separate URLs, dated one day apart** — cite both explicitly rather than describing the second only as "a companion post."

---

## Legal & licensing

**Standing rule for this entire group:** re-verify against the live terms **at training time**, per project, never against a cached note — provider terms are amended independent of this playbook's release cycle, and the checks below show they move on genuinely different clocks.

### EXT-LEGAL-001 — Anthropic Commercial Terms §D.4 + Usage Policy
*FOLLOW · verified 2026-08-21 · ch. 09, 13*

- **Solves:** states plainly that the Commercial Terms (§D.4) and the separately-versioned Usage Policy both prohibit using model input/output to train competing models without authorization — the load-bearing legality check before any own-trace-harvesting plan touches this provider's outputs.
- **Does not solve:** does not cover any other provider — check each provider in your loop independently.
- **Validate before relying on it:** re-verify at training time, not against this note.
- **Version/pin & traps:** Commercial Terms effective 2025-06-17 (unchanged across checks); Usage Policy effective **2025-09-15** — two separately-dated documents, do not conflate their effective dates.

### EXT-LEGAL-002 — OpenAI Terms of Use + Business Terms
*FOLLOW · verified 2026-08-21 · ch. 09, 13*

- **Solves:** the consumer Terms of Use prohibit using output to develop competing models; the Business Terms carry the same restriction with narrow Permitted Exceptions (non-distributed classifier/embedding models; fine-tuning the provider's own offered services).
- **Does not solve:** the Permitted Exceptions are narrow — do not assume a generic fine-tuning or distillation plan qualifies without reading the exception clause against your specific plan.
- **Validate before relying on it:** confirm which specific document (consumer terms vs Business Terms) governs your account type; re-verify at training time.
- **Version/pin & traps:** **first verified live 2026-08-21 via a text-extraction proxy only — direct fetch of the provider's policy pages returned HTTP 403 in this environment.** The provider maintains multiple parallel dated snapshots alongside a canonical current URL — cite the canonical path, not a dated snapshot, and expect to need a proxy fallback on re-verification.

### EXT-LEGAL-003 — Google Gemini API Additional Terms of Service
*FOLLOW · verified 2026-08-21 · ch. 09, 13*

- **Solves:** states the same category of restriction — output may not be used to develop competing models — for the Gemini API surface.
- **Does not solve:** nothing beyond the Gemini API surface — check separately for any other product from this provider in your loop.
- **Validate before relying on it:** re-verify at training time.
- **Version/pin & traps:** effective date **materially newer** than the other two providers' terms checked in the same pass — provider terms move on independent clocks; do not assume a single as-of date covers every provider in a multi-provider loop.

---

## Governance & process rubric

### EXT-OPS-002 — ML Test Score rubric + "Hidden Technical Debt in ML Systems"
*FOLLOW · verified 2026-08-21 · ch. 12, 13*

- **Solves:** the 28-test rubric this playbook adopts as its periodic methodology self-audit, with the score computed as the **minimum** across the four category sections (not a sum or average) — a system must clear every category to raise its score.
- **Does not solve:** does not itself define AI-specific failure classes beyond the two monitors this playbook borrows directly (training/serving skew; holding out annotated production examples for regression).
- **Validate before relying on it:** score your own system against all 28 tests at least annually or per major release before treating any subscore as representative.
- **Version/pin & traps:** **verify authorship against the primary PDF, not a web summary.** A first-pass automated summary of this paper hallucinated a different author list and venue (misattributing it to an unrelated paper); correct attribution was confirmed only by reading the source document directly.

### EXT-TESTBED-001 — Karpathy neural-net sanity-gate recipe
*FOLLOW · verified 2026-08-20 · ch. 00, 03*

- **Solves:** the consensus practice of correctness-only sanity gates before scaling up a training run — external validation for a fast, cheap integrity check preceding any expensive run.
- **Does not solve:** does not specify what your gates should check — that is the reachability/gold-answer/determinism probe design in chapter 03.
- **Validate before relying on it:** n/a for citation; a well-established, low-risk practice to adopt.
- **Version/pin & traps:** 2019 post, durable practice, low staleness risk.

### NV-GARAK-001 — garak (LLM security probing tool)
*ADAPT · verified 2026-08-20 · ch. 03, 13*

- **Solves:** a z-score-vs-calibration-bag pattern for security/regression baselines — worth copying for internal regression baselines even outside the security-probing use case.
- **Does not solve:** does not itself supply a fine-tuning-forgetting regression suite — a different application of the same statistical pattern.
- **Validate before relying on it:** confirm the calibration-bag composition matches your threat model before trusting a z-score derived from it.
- **Version/pin & traps:** no version/date metadata recorded — re-check current tool behavior before adopting.

### NV-ATIF-001 — agent trajectory interchange format
*ADAPT · verified 2026-08-20 · ch. 12, 13*

- **Solves:** a trajectory interchange format spanning multiple agent tools from one vendor's ecosystem — adopt if trajectories need to move between tools rather than living only in your own event log.
- **Does not solve:** does not itself define what fields belong in a trajectory record for experimentation purposes — chapter 12's minimum [trajectory record](../GLOSSARY.md#trajectory-record) is this playbook's own answer; the format is a wire format, not a field-completeness guarantee.
- **Validate before relying on it:** check field coverage against chapter 12's minimum trajectory record before treating this format as sufficient on its own.
- **Version/pin & traps:** no version/date metadata recorded — re-check before adopting as a long-term storage format.

---

## Notable REFERENCE-tier traps

`REFERENCE`-classified sources are consult-don't-depend by definition and are not given full entries above. The following carry traps sharp enough that a reader relying on the chapter that cites them should know about the gap before they hit it.

- **Quantization decision page vs recovery guide.** A vendor's general quantization-method decision page still says "prioritize the widest-precision format first" and omits the narrowest format entirely, while a *different* page in the same repository (NV-MODELOPTQAD-001, above) recommends the narrowest format with a recovery stage — a reader who stops at the decision page mis-scopes their options. This decision-page-lags-flagship-practice pattern recurred across multiple sources in this review; date-weight vendor decision pages against vendor blog posts, and prefer the more recent one when they conflict.
- **Datacenter-scale cost formulas.** A vendor's inference cost/TCO methodology assumes datacenter-scale hardware ($320K-class 8-GPU servers) — the formula *chain* generalizes to a single-box lab, the absolute dollar figures do not.
- **Production observability ≠ experimentation telemetry.** A vendor's serving observability reference documents a strong *production* minimum (metrics + tracing + structured logs) but states no experimentation-time telemetry floor — chapter 12's [telemetry floor](../GLOSSARY.md#telemetry-floor) fills this gap; do not treat a production baseline as sufficient for pre-production forensics.
- **Buried local-benchmarking guide.** The one real local (single-box) benchmarking method in one vendor's device-playbook ecosystem is buried as an asset inside an unrelated tutorial, carries no acceptance criteria, and pins container versions noted as stale relative to its sibling playbooks — re-pin before use, and do not expect to find it from the playbook catalog's own navigation.
- **Native canary path vs the documented one.** A vendor's canary documentation covers a Kubernetes-ecosystem revision-splitting path in detail; the *native* (non-Kubernetes-ecosystem) upgrade path for the same product is a plain rolling update with rollback described as manual. Do not assume canary/rollback automation exists unless you have specifically adopted the documented path.
- **Registries are not lineage.** Model/artifact registries with real semver and per-version metadata exist, but **no end-to-end dataset → run → checkpoint → eval → deployment lineage is prescribed anywhere**, and hot-refreshed adapter files can be versionless by convention — chapter 13's provenance chain is not satisfied by adopting a registry tool alone.
- **Experiment-tracking dashboards lack tamper evidence.** Mainstream experiment-lineage tooling (metrics dashboards, artifact versioning) provides lineage-by-reference but none of it is tamper-evident — adopt as a mirror/dashboard only, never as the [record of record](../GLOSSARY.md#record-of-record) (ch. 13).
- **Judge-agreement evidence is domain-specific.** One widely-cited judge-agreement study reports strong agreement (~80%) but for open-ended chat preference — the wrong domain for an objectively verifiable task (see EXT-JUDGE-002, above, for that case). A separate, more recent study reports chance-corrected agreement (κ, not raw percent agreement) deflating raw judge-agreement numbers by 33–41 percentage points across a large multi-judge sample — the calibration bar to clear if this playbook's judge-calibration protocol (ch. 03, [doctrine-not-yet-exercised](../GLOSSARY.md#doctrine-not-yet-exercised)) is ever exercised.
- **A style-alignment sample size is not a narrow-fix minimum.** A widely-cited small-sample fine-tuning result is validated for *broad style alignment*, not a narrow behavioral fix — do not import its sample count as a general fine-tuning minimum-n floor. This playbook states the narrow-fix minimum-n question as an open field gap (ch. 09) rather than borrow a number that does not apply.
- **Learned-cascade literature is all learned gates.** The published cascade/router literature this playbook surveys uses learned gates throughout, and at least one of those systems' own out-of-distribution result lands near random — the caution behind this playbook's mandatory leakage audit for any learned router (ch. 08).
- **Sequential testing: background theory only.** Classical sequential-testing theory (SPRT and its always-valid descendants) is citable background, but this playbook's chapter 04 treats i.i.d.-calibrated sequential rules as **`[REJECTED]` conditional** under clustered, execution-ordered data — do not read a citation to this literature as license to adopt a sequential test directly without first running the independence check chapter 04 requires.
- **Deterministic-inference mode has a real throughput cost.** At least one serving engine's deterministic-inference mode carries a documented 25–45% throughput slowdown and is recommended by its own maintainers for debugging/reproducibility, not steady-state serving — budget the cost before enabling it broadly.
- **An integrated lifecycle platform is not an experiment registry.** A vendor's newest integrated evaluate/secure/tune/build platform is the first artifact in this corpus shaped like a small-team control plane, but **no experiment-registry or run-history capability exists** as of this review — watch it, do not depend on it for provenance.
- **A reproducible-environment tool is not a run tracker.** A vendor's reproducible-environment tooling gives real cross-machine portability but **contains no experiment tracking, eval management, or model registry by design** — do not expect it to substitute for chapter 13's record of record.
- **"Privacy router" naming is positioning.** At least one vendor's agent-sandbox product markets a "privacy router," but its documented behavior is cost/quality routing plus credential isolation — not sensitivity-based data splitting. Read the behavior, not the marketing name.
- **Rentable cloud marketplaces document no local on-ramp.** A vendor's rentable multi-provider GPU marketplace is current and real, but no local-hardware on-ramp is documented — a "register a local box" flow brings that box into the console for sharing, it does not migrate a workload out to the cloud.

---

## Deprecation watchlist

Standing record of every source classified `DEPRECATED` in [sources.yaml](sources.yaml). Consult this table before citing an older draft, a cached tutorial, or a search result that predates a supersession — the whole reason this table exists is so nobody has to rediscover a trap already found once.

| Deprecated / superseded | When | Replacement | Trap |
|---|---|---|---|
| A data-flywheel reference-loop blueprint | Apr 2026 | none named (the loop design lives on conceptually in a newer integrated platform's evaluate/tune pillars) | Still cited and linked by other vendor docs and older blog posts; the artifact says "reference only," not "the design is wrong" — the log→curate→tune→judge→human-gate pattern remains worth copying even though the code is withdrawn |
| An LLM-routing blueprint | notice added 2026-07-08 | a newer routing library from the same vendor (see NV-SWITCHYARD-001, above) | The deprecation notice lives only on the repository's `experimental` branch README — which is also that repository's *default* branch, so a casual visitor sees it; the `main` branch (the one the notice's own comparison table treats as production) carries no notice at all |
| A GenAI-benchmarking client tool | deprecation confirmed live 2026-08-21, no specific date on the notice itself | AIPerf (see NV-AIPERF-001, above) | An older four-part benchmarking blog series still shows the deprecated tool's commands, unbannered — do not copy commands from those older posts without checking the current tool's migration guide |
| An RTX fine-tune-to-deploy toolkit | archived 2025-11-21 (final commit 2025-11-24) | none named | Was the only official consumer-GPU fine-tune→deploy workflow from its vendor; died with no successor documented anywhere in the corpus reviewed |
| An earlier post-training alignment library | deprecated 2025-05-15 (archived) | a newer post-training library from the same vendor | Pre-2025 alignment tutorials referencing the older library are superseded along with it — verify any older alignment doc against the current library's API before following it |
| A TensorRT-LLM serving backend for a managed inference microservice | dropped from a production release branch, released May 2026 | a vLLM-based backend for the same microservice | A device-specific playbook corpus still ships a variant using the deprecated backend alongside current playbooks — its presence there does not mean the backend is current for the general product |
| An older model-optimization toolkit name and docs domain | rebrand announced 2025-12-08, effective at the next minor version | the renamed toolkit's current docs domain | The old documentation subsite hard-404s; the old **repository** slug transparently redirects via host-level rename handling — the two behave differently, an easy trap when only one link type is updated |
| An older evaluation-SDK documentation tree (adapters/interceptors/parameters pages) | superseded by the current SDK's docs, restructure confirmed live 2026-08-21 | the current SDK's docs, served from a non-versioned "nightly" path | The nominal "latest" path 308-redirects to the "nightly" path — **there is no separately pinned "latest" doc tree at all**; a specific-version static path 404s. Cite the "nightly" path explicitly with an as-of date, never "latest" as if it were stable |
| An older post-training-quantization example script | superseded at a specific toolkit minor version | a newer example script in the same repository | The old script's directory 404s; the supersession is inferred from the 404 plus the current directory listing — **no in-repo prose migration note exists**, so a reader following an old tutorial link gets a bare 404 with no pointer to the replacement |
| A branded "cloud" product name as a directly-rentable destination | repositioned 2026 | separately-branded rentable marketplace products from the same vendor | Older portability promises ("move seamlessly to the cloud") now name a destination that no longer presents as a rentable product at all — the original brand is now vendor-internal; the actual rentable destinations have no documented local on-ramp (see the REFERENCE-tier trap note above) |

---

## Verification discipline

- Every verdict, date, and quoted phrase in this file was re-verified live against the primary source during this authoring pass (as of 2026-08-21 unless a section states an individual date otherwise). Re-verify volatile and snapshot-tier sources again at the start of the *next* authoring pass before reusing a verdict — a vendor verdict recorded once and never rechecked is itself an unpriced escape hatch (see ch. 00 §9, "unpriced escape hatches").
- **Snapshot-tier sources cite an as-of date at the point of use, always** — most importantly the hardware/cloud price snapshot chapter 11's worked examples draw on: prices verified live during a hardware supply crunch carry a shelf life measured in weeks, not months. A price without a printed as-of date next to it should be treated as untrustworthy regardless of source.
- Prefer a direct fetch of the primary source over any automated summary of it. This pass caught two summarization failures on load-bearing sources — a paper's authors and publication venue misattributed by a first-pass automated summary of a PDF, and a code-repository release timeline misread by two years by the same kind of summary — both caught only by re-reading the primary document directly or cross-checking with an independent tool. Treat any single-pass automated summary of a primary source as a hypothesis to verify, not a citation to ship.
- A source's `classification` field in [sources.yaml](sources.yaml) is the record of record. This file's job is to explain *why* that classification holds and what a reader must still supply on top of it. If the two ever disagree, sources.yaml wins and this file has a bug — flag it rather than trusting whichever you read first.

---

> Index: [../README.md](../README.md) · Record of record: [sources.yaml](sources.yaml)
