# 05. Model, Runtime, and Harness Selection

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [← Previous](04_EXPERIMENT_DESIGN_AND_STATISTICS.md) · [Index](README.md) · [Next →](06_INFERENCE_PERFORMANCE_AND_CAPACITY.md)
> **Reading time:** ~18 min. **Prerequisites:** 00, 02, 03, 04.

## 1. Purpose and when to read this

This chapter answers a question published methodology largely leaves to catalogs and
marketing: given a project profile, a trusted evaluation, and a bounded budget, which
**model candidates**, which **runtime/serving engine**, and which **agent harness**
actually enter your experiments? A structured audit of current vendor material found
design-time model comparison and runtime-engine selection both documented as
"measured, not decided" — benchmarking tools and catalogs exist, but no shortlisting
procedure against a requirement and no engine decision rule are published anywhere in
that corpus. This is the gap no vendor fills, and it is exactly the gap that turns an
unbounded universe of models, quantizations, runtimes, and harnesses into a short,
defensible list worth spending evaluation budget on.

Read this chapter after you have a [project profile](GLOSSARY.md#project-profile)
(01) and a trusted [evaluation instrument](03_EVALUATION_FOUNDATION.md) (03) — not
before. Selection without a trusted instrument only launders instrument noise into a
false "winner" (P2). Read it before you freeze the first
[experiment contract](GLOSSARY.md#experiment-contract) (04): the contract's candidate
list and execution-system identity are this chapter's outputs. Re-read it whenever a
new model, runtime release, or harness version appears mid-project — the same hard
filters and regime criterion apply to a re-shortlisting, not a fresh invention.

**Premature** selection compares candidates against an unvalidated instrument,
producing a ranking that changes the moment the instrument is fixed — a wasted
look, not evidence (P1, P2). **Overdue** selection is indefinite postponement of a
frozen shortlist once a trusted evaluation and hard-filter set both exist — a
project that never freezes a candidate list never fields a system to measure. §7's
gates and tripwires operationalize both boundaries.

## 2. Inputs required

- A completed [project profile](GLOSSARY.md#project-profile) (01): task shape,
  quality/reliability target, latency/throughput needs, privacy/residency
  constraints, data/knowledge availability, tool/action permissions, owned/rentable
  compute, capex/opex budget, deployment environment, regulatory constraints.
- A trusted evaluation instrument (03) capable of scoring candidates on the task —
  including its measured [reachability ceiling](GLOSSARY.md#reachability-ceiling)
  and any known stratum weaknesses.
- The [rigor dial](GLOSSARY.md#rigor-dial) / [stakes tier](GLOSSARY.md#stakes-tier)
  from 00 §6, which sets how much selection rigor is mandatory versus optional.
- Chapter 04's screening machinery ([MDE](GLOSSARY.md#mde),
  [elimination rule](GLOSSARY.md#elimination-rule),
  [screening vs inference](GLOSSARY.md#screening-vs-inference)) — this chapter
  produces the candidates that machinery screens; it does not re-derive the
  statistics.

## 3. Decisions this chapter supports

- Which model candidates enter the frozen experiment (04) at all, and which are
  filtered before spending any evaluation budget.
- Which runtime/serving engine executes each candidate, and under what regime —
  determinism/provenance, throughput, vendor-optimized, managed-provider, or hybrid.
- Whether and which agent/harness framework wraps a candidate, and how that choice is
  evaluated (a doctrine-only procedure at this writing — see §5).
- Whether design-time selection work is currently premature, on schedule, or overdue
  relative to eval trust and the project timeline.

## 4. Normative principles

**[PRINCIPLE] Bounded, profile-derived candidate-set construction.**
(inference — playbook synthesis; corroborated by an explicit gap in the audited
vendor corpus, where design-time model comparison is documented "no procedure" and
runtime-engine selection is documented "measured, not decided, no decision rules
anywhere")
The candidate universe (every model family, size, quantization, and license
combination) is unbounded; the project profile is what bounds it. Hard filters
derived from the profile — not preference, not leaderboard rank — decide which
candidates are even eligible before any evaluation budget is spent. §5 gives the
procedure.

**[PRINCIPLE] No universal runtime winner — select by measured regime fit.**
(strong-evidence)
Runtime/serving engines optimize for structurally different regimes: bit-identical
provenance for internal comparisons is not the same problem as maximum tokens/second
under production concurrency, and neither is the same problem as offloading weight
custody to a managed provider. External corroboration: independently, the
nondeterminism/batch-invariance literature shows deterministic execution modes are
opt-in and cost throughput in the engines that ship them
[EXT-DETERM-001], and a separate research cluster on serving sensitivity finds
backend choice alone — holding the model fixed — can move measured quality scores
materially, not merely speed [EXT-PERF-003]. This is the resolution to the
contested pair between "use the fast throughput engine" and "use the
determinism-friendly engine": there is no context-free answer, only a regime match.
§5 gives the criterion table.

**[PRINCIPLE] Runtime and harness are part of the frozen execution system.**
(strong-evidence — direct application of chapter 02's execution-system definition)
A [comparability claim](GLOSSARY.md#comparability-claim) is only as good as its
[frozen identity](GLOSSARY.md#frozen-identity); runtime, harness version, and
hardware are named components of that identity (02), not incidental deployment
detail. Swapping any of them mid-comparison without re-measuring is the
"the model got better/worse" anti-pattern from 00 §9, and the empirical basis is
concrete: backend choice alone has been shown to move quality scores by double-digit
percentage points [EXT-PERF-003].

**[PRINCIPLE] Eligibility gates run before selection, and never bend task
semantics to fit a candidate.** (inference — first-principles corollary of
02's frozen-instrument/comparability requirement)
A candidate that cannot meet a hard filter (license, context length, tool-call
support, deployability) is ineligible; the fix is a thin serving adapter at most,
never a change to what the task requires. Changing the yardstick to fit one
candidate breaks the comparison for every other candidate measured against the
original yardstick.

**[DEFAULT] Model diversity — complementary failure profiles, not just individual
scores.** (case-study)
A candidate that leads on an aggregate score can still lose on strata another
candidate handles cleanly, because different model families tend to fail
differently and often silently (a confidently wrong answer, not a refusal —
[silent failure](GLOSSARY.md#silent-failure)). Before declaring one candidate
dominant, check pairwise pass-set overlap and unique-success counts, not the
aggregate alone [SCENARIO: SCENARIO-07]. This is what makes a downstream
[cascade](GLOSSARY.md#cascade) worth building at all: a second arm earns its keep
by [rescuing](GLOSSARY.md#rescue) cases the first arm fails, which requires the
failure sets to be genuinely different, not a strict subset. Chapter 08 is where
this principle becomes a routing system.

**[DEFAULT] Eval trust precedes selection; selection precedes optimization.**
(consensus — restated from 00 P1 and the default lifecycle, 00 §5)
Do not select against an unvalidated instrument (P1, P2); do not spend the
optimization ladder's budget (07) on a candidate set that was never properly
shortlisted. Selection sits structurally between "the instrument is trustworthy" and
"now improve the winner."

## 5. Default procedure

### 5.1 Candidate-set construction

| Step | Action | Notes |
|---|---|---|
| 1 | Derive **hard filters** from the project profile | Pass/fail only — see the filter table below |
| 2 | Apply hard filters to the full candidate universe | Ineligible candidates are dropped, not adapted-around |
| 3 | Build a **diversity-aware shortlist of 3–6 survivors** | Span families, not only sizes/quantizations of one family — [PARAMETER], calibrate to budget and stakes tier |
| 4 | Bake off near-duplicate configurations cheaply | E.g., multiple quantizations of one base model — a cheap comparison on the iterate split before paying full screening cost for each |
| 5 | Freeze the shortlist | Content-hash it into the experiment contract (04) before running the screening protocol |
| 6 | Run the screening protocol (04) | Selection metric MUST be resolvable at the pilot's own MDE; apply the elimination rule |
| 7 | Gate any "efficiency" candidate jointly | Quality floor **AND** resource-ratio improvement — resource savings alone never promotes a candidate |
| 8 | Break remaining ties with a pre-registered ladder | E.g., pass-count → silent-failure rate → capacity-cap-hit rate → latency → size, with latency/size as tie-breaks only, never the primary criterion |
| 9 | Confirm the winner on the confirmation split (04) | Record the decision and its evidence |

**Hard-filter dimensions** (derive each from the project profile; mark N/A
explicitly rather than skipping):

| Dimension | What it filters | Typical source in the profile |
|---|---|---|
| Capability | Can the family do the task shape at all (reasoning, tool use, long-context, multimodal)? | Task population, quality target |
| Licensing / data policy | Commercial-use rights, output-ownership terms, redistribution, training-on-outputs restrictions | Regulatory/compliance, data policy |
| Deployability / [execution surface](GLOSSARY.md#execution-surface) | Local/self-hosted vs managed API vs subscription-agent surface | Privacy/residency, deployment environment |
| Hardware fit | Weights + KV-cache + runtime-buffer headroom on owned/rentable compute — not weights alone | Owned compute, rentable compute |
| Context length | Required context window at the task's realistic evidence volume | Task population, retrieval design (08) |
| Tool use / structured output | Reliable function-calling and schema-constrained output where the workflow needs them | Tool/action permissions |
| Runtime compatibility | Which serving engines actually run this artifact/quantization combination | Owned compute, deployability |
| Fine-tuning support | Whether a training path exists if the ladder (07) ever reaches rung 7 | Existing evidence, staffing |
| Observability | Whether the surface exposes the telemetry floor (12) at all | Observability |
| Cost / latency / complexity | Recurring budget, SLA, operational headcount to run it | Recurring budget, latency/SLA, staffing |
| Reproducibility | Whether the execution surface supports a frozen, pinned identity (02) | — (derived, not asked directly) |

A dimension that eliminates every candidate is a signal the profile itself needs
revisiting (01), not a reason to quietly relax the filter.

### 5.2 Runtime/serving-engine selection — the regime criterion

There is no universal best runtime. Select the **regime** the project profile
requires, then choose an engine within that regime — never the reverse.

| Regime | Optimizes for | Typical properties | As-of-dated examples (2026-08-21 — examples, not verdicts) |
|---|---|---|---|
| **Determinism / provenance** | Bit-identical-enough comparisons; byte-level provenance; broad/legacy quantization-format support | Single-slot serving, pinned builds, grammar/structured-output enforcement | [EXT-LLAMACPP-001] |
| **Throughput** | Maximum tokens/s or requests/s under concurrency | Continuous batching, tensor/pipeline parallel, production metrics vocabulary | [EXT-VLLM-001], [EXT-SGLANG-001] |
| **Vendor-optimized / production contract** | Vendor-compiled kernels on supported hardware, enterprise support surface | Ahead-of-time compilation, enterprise serving contract | [NV-TRTLLM-001] |
| **Managed-provider** | No weight custody; someone else's infrastructure | Provider-redeploy is a [reproducibility-boundary](GLOSSARY.md#reproducibility-boundary) hazard — a silent backend change can invalidate a running comparison | (execution surface, not a named engine) |
| **Hybrid** | Different regimes at different tiers of one system | E.g., a determinism-regime local specialist escalating to a managed-provider tier | — |

Decision procedure:

1. From the project profile, answer: does any planned comparison require
   session-scoped, near-bit-identical reproducibility? Does the deployment need
   production-scale concurrency/throughput? Does a **written**
   privacy/residency/security requirement prohibit every managed configuration
   that satisfies the project's retention, residency, tenancy, and data-handling
   requirements — including in-tenant/VPC-scoped, no-retention, region-bound
   ones — for some or all traffic? (If a compliant managed configuration exists,
   the constraint narrows *which* surfaces are admissible; it does not mandate
   self-hosting — the same test as QUICKSTART step 3 node 5 and 11 Q0a.) Is
   there a committed enterprise support requirement?
2. Map the answers to a primary regime (or a hybrid split across tiers of a
   [cascade](GLOSSARY.md#cascade), 08).
3. Within the chosen regime, evaluate specific engines with chapter 06's
   performance-characterization methodology — regime selection narrows the field;
   it does not replace measurement.
4. Even within the throughput regime, a determinism sub-mode may exist as an
   opt-in cost: batch-invariant execution modes are documented in major throughput
   engines as of the verification date, at a measured throughput cost
   [EXT-DETERM-001]. Decide explicitly whether that cost is worth paying for a
   given comparison; do not assume the default mode is deterministic.
5. The chosen engine, version, and launch configuration MUST be recorded as part
   of the execution-system identity (02) — never as an incidental deployment note.

**[STOP CONDITION]** A runtime, engine version, or launch configuration changed
between two measurements being compared, and no re-measurement has been run. Treat
the prior comparability claim as void until re-measured (P5).

### 5.3 Harness/agent-framework selection

*status: doctrine — not yet exercised (see the comparison design below in this
section for what validation would look like)*

A harness (agent framework, orchestration layer, coding-agent CLI) wraps a model
with a system prompt, tool schemas, memory/context management, and its own
observability surface. It is part of the execution system (02) exactly like the
model and the runtime, and it needs the same selection discipline — but no internal
or cited external execution record exists for a harness comparison run under this
playbook's discipline. What follows is the procedure to run one, not a validated
result.

**Dimension checklist** (evaluate each harness candidate against the task, not in
the abstract):

| Dimension | What to check |
|---|---|
| Tool-call fidelity | Correct schema adherence, argument construction, and error handling across the tool set |
| Context management | How the harness allocates/truncates/summarizes context under the task's realistic evidence volume |
| Trajectory observability | Whether every tool call, retrieval, and intermediate step is logged in enough detail to reconstruct a run (12) |
| Determinism hooks | Whether the harness exposes seed/temperature control, or introduces its own nondeterminism on top of the model's |
| Permission model | Whether tool/action permissions can be scoped per task, per tenant, per stakes tier (13) |
| Cost overhead | Tokens and wall-clock spent by the harness's own scaffolding (system prompt, tool schemas, memory files) versus the task |
| Version churn | Release cadence and breaking-change history — a harness that changes weekly needs a pinning and re-validation policy |

**Comparison design:** compare harnesses via a same-model, same-task
cross-harness experiment — same repository/task set, same underlying model, same
reasoning configuration, only the harness varied. Where model equality across
harnesses is not achievable (e.g., a harness bundles a fixed model), the result is
an execution-system comparison, not a harness comparison — label it that way rather
than attributing the delta to the harness alone.

**Isolate harness overhead from model capability.** When benchmarking a model
*through* an agent or subscription-CLI harness for a model-selection decision,
either strip the harness's default wrapping (system prompt, tool schemas, memory
files) down to a bare completion call, or explicitly scope the result as an
execution-system comparison that includes the harness. Otherwise the measurement
captures the harness's scaffolding overhead and reports it as if it were the
model's own capability or cost — an instance of the frozen-execution-system
principle above, applied specifically to selection-stage benchmarking.

**Harness version is part of execution-system identity** (02): it MUST be pinned
exactly as model artifact and runtime build are pinned; a harness upgrade
mid-comparison is the same reproducibility hazard as a runtime upgrade.

### 5.4 The first baseline execution system

*status: doctrine — not yet exercised (see this subsection for what validation
would look like)*

The lifecycle's "simplest credible baseline" step is not another candidate for
§5.1's shortlist — it is the first end-to-end system that shortlist has anything to
be screened against. Build it before running the screening protocol (§5.1 step 6),
on the cheapest candidate that survives hard filtering, with nothing more than:

1. **An output schema.** The exact structure the task requires — shape, required
   fields, allowed value ranges — fixed before any prompt is written, not inferred
   after the fact from whatever the model happens to emit.
2. **A deterministic verifier for that schema.** A parser/validator that mechanically
   accepts or rejects an output against the schema, with no model-in-the-loop
   judgment in this check; chapter 03's RC-1 instrument-defect discipline applies to
   the verifier itself.
3. **A context policy.** What evidence the task receives, in what order, up to what
   budget — a stated rule, not whatever happens to fit.

Nothing else: no retrieval, no tool use, no routing, no fine-tuning — those are
chapters 07/08/09's job once a diagnosed gap justifies climbing to them (the
lifecycle order, 00 §5). Pin this combination — model, prompt, schema, verifier,
context policy — as a [frozen identity](GLOSSARY.md#frozen-identity) (02) *before*
it is scored against the evaluation instrument (03): a baseline that can still
change between "build it" and "score it" produces a comparability claim about
nothing in particular. Its scored result enters the screening comparison (§5.1 step
6) as an ordinary row, not an exempt reference point.

## 6. Project adaptation parameters

| Parameter | What to calibrate | Guidance |
|---|---|---|
| Shortlist size | How many candidates survive hard filtering into screening | 3–6 is a starting range; smaller for Tier-1/low-budget projects, larger when family diversity is itself a project goal (rescue routing, 08) |
| Hard-filter set | Which profile dimensions are pass/fail versus scored | Derive from §5.1's table; document any dimension marked N/A and why |
| Regime weighting | How heavily determinism vs throughput vs managed-provider needs are weighted when a project's needs span regimes | Tier and stakes-dependent (00 §6); a Tier-3 audit requirement pulls toward the determinism/provenance regime even at some throughput cost |
| Harness dimension weights | Relative importance of the seven checklist dimensions in §5.3 | Task- and stakes-tier dependent; document the weighting before scoring, not after |
| Tie-break ladder order | Which secondary criterion breaks a tie after quality | Latency-sensitive deployments order latency before size; cost-sensitive deployments the reverse — pre-register either way |
| "Start small" default | How many logical tiers/models to field on day one | Starting with a small number of logical tiers (e.g., one general-purpose worker before adding a router or escalation tier) and proving the workflow, trajectory schema, and eval harness on it is a strong default before adding a second model for a measured reason — calibrate against how well-understood the task already is |

## 7. Decision gates and stopping conditions

**[DECISION GATE] Shortlist freeze.**
*Inputs:* hard-filtered candidate pool, diversity check, budget for screening.
*Rule:* the shortlist is content-hash frozen into the experiment contract before
any screening run begins; a candidate not in the frozen list requires a new
amendment, not a silent addition.
*Outcomes:* proceed to screening (04), or return to §5.1 if the pool is empty or
insufficiently diverse.

**[DECISION GATE] Runtime regime.**
*Inputs:* project profile answers from §5.2 step 1.
*Rule:* pick the regime (or hybrid split) before evaluating specific engines; do
not let an engine's popularity substitute for a regime match.
*Outcomes:* regime and candidate engine(s) recorded in the execution-system
identity (02).

**[STOP CONDITION] Selection continuing without a trusted evaluation.** Global
tripwire #1 from 00 §7, applied here directly: no shortlist ranking, no runtime
choice justified by "it scored better," is meaningful until the instrument
(03) is trusted.

**[STOP CONDITION] Selection stalling past the project's first-sprint contract
deadline (01).** Indefinite re-shortlisting without freezing is a selection-stage
version of the "relaxed lane" anti-pattern (00 §9) — a way to keep deferring a
committed decision.

**[STOP CONDITION] A margin-based elimination is about to happen below the
screening pilot's own MDE.** Applies the elimination rule (04,
[GLOSSARY](GLOSSARY.md#elimination-rule)) at the selection stage specifically:
neither candidate is dropped on a margin the design cannot resolve.

## 8. Metrics and formulas

The statistical machinery that decides whether a screening margin is resolvable
(MDE, [effective N](GLOSSARY.md#effective-n), the elimination rule) belongs to
chapter 04 and [references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md);
this chapter only states how it is *used* at the selection stage:

> A candidate is eliminated on a measured margin only if that margin exceeds the
> screening design's own MDE at the stated α and power. A margin below MDE is
> [INCONCLUSIVE](GLOSSARY.md#inconclusive) for elimination purposes — both
> candidates proceed, the decision defers to the qualification split, or the
> selection metric changes to one the design can resolve.

*Illustrative worked example (invented round numbers).* A screening pilot's design
has an MDE of 18 percentage points at its chosen N and clustering correction. Two
candidates measure 6 points apart on the pilot. Since 6 < 18, the margin is
INCONCLUSIVE for elimination: neither candidate is dropped on this evidence alone.

**Selection scorecard (non-statistical criteria only).** Once quality is settled by
the statistical machinery — or tied within MDE — cost, latency, and complexity
differences are resolved with a simple pre-registered weighted score, never used to
override a quality decision the statistics could resolve:

```
score(candidate) = Σ_i  w_i · normalized_criterion_i(candidate)
```

where each `normalized_criterion_i` is scaled to a common range (e.g., 0–1, with a
stated direction of "better") and the weights `w_i` sum to 1 and are fixed **before**
any candidate is scored — the same pre-registration discipline as a statistical
contract (04), applied to a non-statistical tie-break.

*Illustrative worked example (invented round numbers, two candidates A and B,
weights fixed in advance: capability 0.4, cost 0.2, latency 0.2, complexity 0.1,
reproducibility 0.1):*

| Criterion | Weight | A (normalized) | B (normalized) |
|---|---|---|---|
| Capability | 0.4 | 0.90 | 0.85 |
| Cost | 0.2 | 0.40 | 0.80 |
| Latency | 0.2 | 0.60 | 0.70 |
| Complexity | 0.1 | 0.70 | 0.90 |
| Reproducibility | 0.1 | 0.90 | 0.60 |
| **Weighted score** | | **0.70** | **0.79** |

Here B wins the scorecard despite A's higher capability score — legitimate only
because capability was already established as tied within MDE before the scorecard
ran; the scorecard never substitutes for that check.

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition: always — these are generically wrong)

- **Leaderboard-driven family choice.** Choosing a model family by generic
  leaderboard rank instead of your own task's tool-call correctness and
  structured-output reliability. Restates 00 §9's benchmark-worship rejection,
  specific to the selection stage.
- **A permanent runtime default.** Declaring one engine the standing choice without
  re-checking the regime match as project needs (concurrency, determinism
  requirements, deployment target) change. There is no universal winner (§4).
- **Unstripped-harness benchmarking attributed to the model.** Running a
  model-selection benchmark through an agent/subscription CLI's default wrapping
  and reporting the result as the model's own capability or cost, rather than as an
  execution-system (harness-inclusive) measurement.
- **Aggregate-score dominance claims.** Declaring one candidate dominant from an
  aggregate score without checking pairwise pass-set overlap and unique-success
  counts first (§4).
- **Resource-savings-only promotion.** Promoting an "efficiency" candidate
  (smaller, cheaper, faster) on resource savings alone, without the joint quality
  floor.
- **Bending task semantics to fit a candidate.** Modifying what the task requires,
  rather than accepting a candidate's ineligibility or adding a thin serving
  adapter (§4).

**[SCENARIO: SCENARIO-06]** A generation-length (decoding budget) cap shared across
compared arms confounded a design-time model comparison: an apparent quality gap
shrank substantially once the operational constraint was isolated in its own
one-factor experiment. Before attributing any selection-stage delta to "the model,"
verify no shared operational constraint — context length, decoding budget, timeout
— is capping one arm disproportionately. Cross-references chapter 04's
one-factor-per-arm discipline and chapter 07's generation-budget calibration
procedure.

**[SCENARIO: SCENARIO-07]** A deterministic cascade gate over two locally-served
candidates achieved near-complete rescue with negligible unnecessary escalation —
outside the design space of the published learned-router literature — because the
two arms' failure sets were genuinely complementary rather than nested. The
selection-stage lesson: measuring pairwise complementarity during shortlisting is
what makes a downstream cascade (08) worth building at all.

## 10. Vendor recipes

| Verdict | Source | Scope | As-of |
|---|---|---|---|
| **[REFERENCE: EXT-VLLM-001]** | vLLM | Throughput-regime default candidate; de facto standard open serving engine; deterministic batch-invariant mode is opt-in and reduces performance | 2026-08-21 |
| **[REFERENCE: EXT-SGLANG-001]** | SGLang | Throughput-capable engine with a documented deterministic mode (batch-invariant kernels), at a documented slowdown — a throughput-regime engine with an opt-in determinism sub-mode | 2026-08-21 |
| **[REFERENCE: EXT-LLAMACPP-001]** | llama.cpp | Determinism/provenance-regime default candidate: single-slot serving, wide quantization-format support, very active release cadence — pin the exact build, not just a version name | 2026-08-21 |
| **[REFERENCE: NV-TRTLLM-001]** | TensorRT-LLM | Vendor-optimized regime; note that a major NVIDIA-managed serving product's default backend has moved toward vLLM as of this verification — treat vendor-optimized-engine defaults as time-stamped facts, not durable rankings | 2026-08-21 |
| **[REFERENCE: NV-NAT-001]** | NeMo Agent Toolkit | Agent-harness tooling (eval runner, profiler, sizing calculator) — explicitly documented as lacking harness-selection guidance and variance/CI treatment for stochastic agents; corroborates the doctrine-not-exercised status of §5.3 | 2026-08-20 |
| **[REFERENCE: NV-NEMOPLATFORM-001]** | NeMo Platform | Integrated evaluate/secure/tune/build lifecycle platform, actively developed; watch item for a future experiment-registry capability, currently absent; does not yet supply a selection method | 2026-08-21 |
| **[ADAPT: EXT-DETERM-001]** | Nondeterminism/batch-invariance package | Adapt into the regime decision (§5.2 step 4) and into chapter 02's reproducibility-boundary probes; do not adopt a specific engine's default mode without checking whether it matches the regime you selected | 2026-08-21 |

## 11. Worked examples

*Illustrative scenario (invented, non-project-specific).* A team is building a
document-summarization assistant with a data-residency constraint (no managed API
for source documents) and a memory ceiling that rules out the largest local
model class.

1. **Hard filters (§5.1):** licensing permits commercial fine-tuning; execution
   surface restricted to local/self-hosted; hardware fit caps the weight class
   with explicit KV-cache/runtime-buffer headroom, not just weights; context
   length covers the longest realistic document; structured output required for
   the citation schema.
2. **Shortlist and bake-off:** four candidates survive, spanning three families
   deliberately rather than quantizations of one base model; two quantizations of
   one family are compared cheaply on the iterate split first, and the weaker one
   is dropped before full screening.
3. **Regime (§5.2):** the residency constraint rules out the managed-provider
   regime entirely; session-scoped reproducibility needs during screening make the
   determinism/provenance regime primary, with a throughput-regime engine held in
   reserve for the eventual production deployment.
4. **Screening and tie-break (04, §8):** the three remaining candidates run the
   pilot; two are separated by a margin below the pilot's MDE and both proceed,
   deferred to the qualification split rather than eliminated. On the confirmation
   split, quality resolves statistically and the scorecard is not needed.

Further worked examples from the case library: [SCENARIO-06](examples/SCENARIO-06_token-budget-confounding.md)
(a confound that inflated an apparent selection-stage quality gap) and
[SCENARIO-07](examples/SCENARIO-07_deterministic-cascade-gate.md) (complementary arms
enabling a cascade).

## 12. Outputs and artifacts

- A frozen candidate shortlist, content-hash bound into
  [templates/EXPERIMENT_CONTRACT.md](templates/EXPERIMENT_CONTRACT.md) (04).
- Runtime engine, version, and launch configuration recorded as part of the
  execution-system identity (02).
- Harness identity and version (once a harness is used) recorded the same way,
  including the dimension-checklist results from §5.3 if a harness comparison was
  run.
- The first baseline execution system's frozen identity (§5.4): output schema,
  deterministic verifier, context policy, and model/prompt pin, recorded the same
  way as any other execution-system identity (02), before it is scored.
- Any deviation from this chapter's defaults (regime choice against the criterion,
  shortlist size, tie-break order) recorded in
  [templates/METHOD_DECISION_RECORD.md](templates/METHOD_DECISION_RECORD.md) with
  its evidence and review date.

## 13. Sources

| ID | Role here |
|---|---|
| [EXT-DETERM-001] | Batch-invariance/nondeterminism package — grounds the regime criterion and the determinism-sub-mode cost note |
| [EXT-PERF-003] | Backend choice alone moves quality scores — grounds "runtime is part of frozen identity, not a performance-only knob" |
| [EXT-VLLM-001] | Throughput-regime example engine, as-of-dated |
| [EXT-SGLANG-001] | Throughput-regime example engine with opt-in determinism mode, as-of-dated |
| [EXT-LLAMACPP-001] | Determinism/provenance-regime example engine, as-of-dated |
| [NV-TRTLLM-001] | Vendor-optimized-regime example engine, as-of-dated |
| [NV-NAT-001] | Agent-harness tooling; documents the harness-selection gap this chapter's §5.3 fills as doctrine |
| [NV-NEMOPLATFORM-001] | Integrated lifecycle platform, watch item, not yet a selection method |

**Gap dispositions in this chapter:** **G20 (contradictions register), the
runtime-selection contested pair: COVERED** — resolved by the regime criterion in
§5.2 (determinism/provenance vs throughput vs vendor-optimized vs managed-provider
vs hybrid), with engines named only as as-of-dated examples, never as a winner. The
harness/agent-framework selection method (§5.3) is
**COVERED-AS-DOCTRINE-NOT-YET-EXERCISED**: the full procedure is stated, and no
internal or cited external execution record exists for it yet.

---

> [← Previous](04_EXPERIMENT_DESIGN_AND_STATISTICS.md) · [Index](README.md) · [Next →](06_INFERENCE_PERFORMANCE_AND_CAPACITY.md)
