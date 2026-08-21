# 06. Inference Performance and Capacity

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [← Previous](05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md) · [Index](README.md) · [Next →](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md)
> **Reading time:** ~20 min. **Prerequisites:** 02 (execution system), 05 (runtime/harness selection).

## 1. Purpose and when to read this

This chapter is about **how fast and how much** — latency, throughput, and capacity
for a [frozen execution system](GLOSSARY.md#frozen-identity) — not about whether the
system is *right*. Capability and quality claims belong to chapters 03/04; this
chapter's claims are about milliseconds, tokens/second, and gigabytes, and stay in
their own lane. Read it once you have a candidate
[execution system](GLOSSARY.md#execution-system) worth timing: after runtime/harness
selection (05), before committing to an operating point, sizing hardware (11), or
spending a long run against a fixed context/budget configuration.

Published inference-performance methodology is genuinely mature — vendor benchmarking
guidance for metric definitions and sweep procedure is as close to FOLLOW-BY-THE-BOOK
as this playbook gets anywhere. What that guidance omits — the single-user regime,
clock validity, effective-bandwidth accounting, capacity fit checks before an
expensive run, and a standing forensic procedure for where an expensive run's time
actually went — is this chapter's own contribution.

## 2. Inputs required

- A [frozen execution system](GLOSSARY.md#frozen-identity) (05): model artifact,
  quantization, runtime/engine, hardware/host, context policy, generation settings.
- The workload profile — expected input/output token shapes, expected concurrency
  regime, latency targets — from [PROJECT_PROFILE](templates/PROJECT_PROFILE.md) (01).
- The deployment target's actual hardware specs (memory capacity, memory bandwidth,
  compute), not the development box's, unless they are the same machine (02's
  quantize-for-the-deployment-target rule applies here too).
- The [telemetry floor](GLOSSARY.md#telemetry-floor) (12) landed *before* any run this
  chapter's procedures depend on — post-run forensics cannot be retrofitted.

## 3. Decisions this chapter supports

- The [operating point](GLOSSARY.md#operating-point) (concurrency/batch/budget) a
  system is declared to run at.
- Whether a proposed context length and generation cap will physically fit the
  deployment hardware *before* an expensive experiment is committed to it.
- Whether a measured performance number explains, or merely correlates with, an
  experiment's wall-clock or dollar cost — feeding chapter 04's cost accounting and
  chapter 07's opportunity-cost test.
- Capacity and bandwidth inputs to hardware sizing and rent-vs-buy analysis (11).
- Whether a dominant cost bucket uncovered during or after a run is a **finding** to
  study or **waste** to eliminate (§9, G14).

## 4. Normative principles

**[PRINCIPLE] Performance and capability stay on separate ledgers.** (evidence:
strong-evidence) A performance number and a quality number are both properties of the
same [execution system](GLOSSARY.md#execution-system), but neither substitutes for the
other, and neither is valid outside the [frozen identity](GLOSSARY.md#frozen-identity)
it was measured on. Backend/engine choice alone has been shown to move quality scores
by double-digit percentage points independent of the model [EXT-PERF-003] — reading a
latency change as a quality signal, or the reverse, is the same error inverted. A
change in either forces re-declaring the identity (02) before any prior number is
trusted again.

**[PRINCIPLE] Capacity and bandwidth are different physical constraints; measure
both.** (evidence: strong-evidence — first-principles) Capacity is a threshold
constraint — a configuration either fits the accelerator's memory or it does not.
Bandwidth is a rate constraint — it sets decode speed regardless of remaining
capacity headroom. A model that "fits comfortably" can still run near its bandwidth
ceiling; neither can be inferred from the other, so both must be measured.
[CASE: CASE-005].

**[PRINCIPLE] A large cost bucket is not automatically waste.** (evidence: inference —
first-principles; full test in §9) If a dominant bucket is task-intrinsic and changes
the comparison the experiment exists to make, it is *evidence about the system under
study*, belonging in the analysis plan, not the backlog. Treating it as overhead to
engineer away before anyone has looked at what it means discards the finding along
with the inefficiency. [CASE: CASE-006].

**[PRINCIPLE] Measure the metric that will govern the decision, on the tool that will
be reused.** (evidence: strong-evidence) Metric definitions are not standardized
across benchmarking clients — the same field name can mean different windows or
percentile treatments. Numbers from different tools, or different definition
versions, are not comparable even when the labels match. Pin one client and one
definition set across every measurement tier of a project [NV-INFERBENCH-001].

## 5. Default procedure

### 5.1 The vendor-mature core — FOLLOW BY THE BOOK

**[FOLLOW: NV-INFERBENCH-001]** (scope: LLM inference benchmarking on an
OpenAI-compatible endpoint; as-of 2026-07-20, live-reverified 2026-08-21) This is the
one place in this playbook where vendor methodology is mature enough to follow without
a decision layer bolted on. Use it as written:

1. **Fix metric definitions before measuring anything.** TTFT (time to first token),
   ITL/TPOT (inter-token latency / time per output token), end-to-end request latency,
   system throughput (aggregate tokens/second across all concurrent requests) vs
   per-user throughput (tokens/second experienced by one request under load). Record
   which definition set is in force; do not assume it matches another tool's.
2. **Define ISL/OSL pairs per use case.** Input-sequence-length and output-sequence-
   length distributions are workload properties, not tool defaults — a chat use case,
   a long-document-summarization use case, and a code-generation use case have
   materially different ISL/OSL shapes and must be measured separately.
3. **Warm up before measuring.** Discard the first requests of a session (cold cache,
   JIT/graph-capture effects, cold model load) from the measured window; the vendor
   guide's own warmup-then-measure discipline applies regardless of engine.
4. **Discipline the request count.** Measure enough requests per operating point that
   percentile estimates are stable — a common rule of thumb is a fixed multiple of the
   concurrency level, not a fixed absolute count.
5. **Sweep concurrency, not request rate, as the primary axis.** Concurrency
   (simultaneous in-flight requests) is the controllable variable that traces out the
   latency-throughput curve; request-rate sweeps are a secondary view once the curve
   is known.
6. **Plot the latency-throughput curve and select an operating point from it.** Do not
   pick a single concurrency value by guesswork. Sweep from 1 through past the
   system's saturation point, plot latency (percentiles) against throughput, and
   declare the [operating point](GLOSSARY.md#operating-point) as the highest
   throughput that still satisfies the stated latency constraint. Pin that point; it
   is part of the execution-system identity going forward.

```
latency (p95) ^        x  x         <- saturation: latency climbs steeply
              |    x  x
              |  x           chosen operating point: highest throughput
              |x              still inside the latency constraint
              +----------------------------------> throughput (tok/s)
```

**[FOLLOW: NV-AIPERF-001]** (scope: benchmarking client; v0.12.0, 2026-08-06,
verified live 2026-08-21) Use an endpoint-agnostic, actively maintained client rather
than a bespoke script — it implements the sweep/warmup/percentile discipline above out
of the box and stays current with engine changes. **[DEFAULT]** (evidence: strong-
evidence, following directly from the metric-definition warning in §4) Pin **one**
client and **one** metric-definition set across every tier of a project — exploratory
runs, capacity planning, and pre-deployment sizing must not silently mix tools.

### 5.2 What the vendor-mature core omits

The FOLLOW procedure above assumes a datacenter-scale, many-concurrent-user reader.
Four things a small-lab or single-tenant reader needs are not in it:

**A. The single-user/interactive regime.** Concurrency=1 is not a degenerate case of
the sweep — it is its own operating point, and often the *only* one that matters for
an interactive assistant with one session per user. Measure TTFT and per-token
latency at concurrency=1 explicitly; they do not extrapolate cleanly from a
many-request sweep's tail.

**B. Clock validity.** Record **dual clock stamps** — realtime and monotonic — on
every measured span, and declare an **authoritative clock per metric** before
publishing a number ([dual-clock telemetry](GLOSSARY.md#dual-clock-telemetry),
[authoritative clock](GLOSSARY.md#authoritative-clock)). Virtualized/power-managed
hosts can let a monotonic timer drift materially against realtime while appearing to
run normally — invisible until cross-checked against an independent realtime source.
**[DEFAULT]** (evidence: case-study; single-project origin, capped per the A–H
taxonomy) Declare the authoritative clock and record both stamps before trusting any
latency figure. [CASE: CASE-005] found this the hard way, by forensic reconstruction
after the fact — landing the dual-clock floor before the run is strictly cheaper.

**C. Effective-bandwidth accounting.** Vendor spec-sheet bandwidth is a ceiling, not
an expectation. Decode-bound serving is bound by *achieved* bandwidth, and the ratio
between achieved and spec is a measured stack property, never assumed near 100%.
§8 gives the arithmetic and a worked example.

**D. A fit probe before an expensive run depends on a configuration.** Before
committing an expensive run to a specific context length and generation cap, probe
that the configuration actually fits the deployment accelerator's memory — weights,
KV cache at the target context length, and runtime overhead together. **[DEFAULT]**
(evidence: heuristic; corroborated in spirit by the general correctness-before-scale
discipline of cheap sanity gates before an expensive run [EXT-TESTBED-001]) Run the
probe and record its result as a named artifact before any run whose science depends
on the configuration fitting. §8 gives the check; §7 states it as a stop condition.

### 5.3 The performance autopsy — a standing post-run procedure

Any run expensive enough to matter deserves a forensic reconstruction of where its
wall clock went, whether or not anything looked wrong. Template:
[templates/PERFORMANCE_AUTOPSY.md](templates/PERFORMANCE_AUTOPSY.md).

**[DEFAULT] The autopsy procedure.** (evidence: case-study; single-project origin,
capped per the A–H taxonomy; the method — multi-source reconstruction with explicit
evidentiary labeling — generalizes even though its one exercised instance does not)

1. **Multi-source timing reconstruction.** Pull timing from every independent source
   that recorded it — lifecycle events, per-invocation telemetry, server/engine logs,
   database timestamps, commit times, orchestration transcripts — cross-validated
   against each other, never trusting one source alone. Label every figure by
   evidentiary strength (directly measured / derived by arithmetic / estimated).
2. **Critical-path identification.** Separate wall time that actually gated
   completion (serial dependencies, contention, single-slot policies) from work that
   happened for free inside another activity's window. Only critical-path time is a
   candidate for "a fix would save this."
3. **Cost-bucket attribution.** Decompose the critical path into a standard,
   run-to-run-comparable bucket set: task-intrinsic workload, infrastructure/tooling
   overhead, implementation/debugging, human/orchestration review, documentation.
4. **Counterfactual costing.** For each candidate intervention (more hardware, a
   faster device, a smaller budget, parallel execution across independent execution
   systems), compute what it would have saved *given the measured bottleneck*, never
   given headline specs — a hardware upgrade that misses the actual bottleneck
   resource can make a workload slower, not faster (§8's arithmetic).
   [CASE: CASE-005].
5. **Clock-forensics cross-checks.** Compare every monotonic-derived figure against
   an independent realtime source; a systematic skew invalidates every prior number
   computed the same way, uniformly, until corrected.
6. **Apply the finding-vs-waste test (§9)** to every dominant bucket before
   recommending anything about it.
7. **Mandatory missing-evidence section**, naming explicitly what could not be
   reconstructed and why — silently omitting an autopsy's own blind spots teaches the
   wrong lesson to the next one.
8. **Feed reconstruction gaps into the telemetry floor (12)** — whatever had to be
   inferred because it wasn't recorded is next run's telemetry requirement, not next
   autopsy's forensic challenge.

### 5.4 Multi-tenant / concurrent-SLA serving — explicitly out of scope for v0.1

Everything above characterizes a system serving one workload stream at a time (an
interactive session, or a swept-but-still-single-tenant benchmark). Real production
serving under many simultaneous tenants with per-tenant SLA commitments is a distinct
discipline — admission control, fairness across tenants, SLO-threshold alerting under
sustained concurrent load, and burn-down accounting against an error budget — and this
playbook does not yet validate a methodology for it. **This is stated explicitly
rather than left silent** (mirrored in chapter 10, which owns the production-serving
side of the same gap). What is provided is a skeleton and pointers, not a procedure to
follow:

- **Load-test taxonomy** (adapt, don't invent your own labels):
  **[ADAPT: EXT-PERF-002]** k6's test-type vocabulary — smoke (does it work at all),
  average-load (expected steady state), stress (find the breaking point),
  spike (sudden burst), soak (sustained duration, catches leaks/drift), breakpoint
  (deliberate push past capacity) — generalizes cleanly from HTTP APIs to
  inference-serving endpoints. What's missing for inference specifically: SLO
  thresholds must be expressed in the metric vocabulary of §5.1 (TTFT/ITL/percentile
  latency under concurrency), not generic request-duration; substitute your
  contract's latency/quality thresholds for k6's generic pass/fail threshold syntax.
- **Sizing automation pointer:** **[REFERENCE: NV-DYNAMOAICONFIG-001]** — datacenter
  operating-point automation and sizing tooling exists and is mature for datacenter
  deployments; it has no data for workstation-class accelerators and should not be
  treated as validating a small-lab sizing claim.
- **Doctrine status:** *status: doctrine — not yet exercised (see this section for
  what validation would look like: an admission-control policy, a per-tenant fairness
  metric, and a burn-down-against-error-budget procedure, measured against real
  concurrent multi-tenant traffic before any SLA claim is made from it)*.

## 6. Project adaptation parameters

| Parameter | What it governs | How to set it |
|---|---|---|
| **ISL/OSL distribution per use case** | Which workload shape the sweep characterizes | Measure from real or representative traffic; do not reuse a generic benchmark's shape |
| **Concurrency sweep range** | Coverage of the latency-throughput curve | From 1 through past measured saturation; include concurrency=1 explicitly if any interactive use case exists |
| **Warmup request count** | Excludes cold-start effects from measurement | Enough requests to reach steady per-token latency; verify by inspecting the discarded window, don't assume a fixed count transfers |
| **Request-count multiplier** | Percentile stability at each operating point | A fixed multiple of concurrency is a common starting rule; verify percentile estimates have converged before trusting them |
| **Latency constraint for operating-point selection** | Which point on the curve is chosen | From the use case's actual UX/SLA requirement (01), not from what the curve happens to offer |
| **Percentile set reported** | What "typical" and "tail" mean for this workload | p50/p95/p99 as a floor; add p999 for high-request-volume services where rare tail events matter operationally |
| **Authoritative clock per metric** | Which timestamp source a published number is computed from | Declared in the experiment contract (04) before the run; re-declared if the host/virtualization layer changes |
| **Generation cap / reasoning budget** | Where truncation begins to bound outcomes | Calibrated by the dedicated procedure in chapter 07 (rung 5), not set here — this chapter only verifies the chosen cap *fits* (§8) |
| **Fit-probe margin** | How much headroom below capacity counts as "fits" | Project-set; leave enough margin for KV-cache growth under the actual context length used in production, not just the benchmark's |

## 7. Decision gates and stopping conditions

**[DECISION GATE] Operating-point selection.** Inputs: the swept latency-throughput
curve (§5.1) and the use case's latency constraint (01). Rule: choose the highest
throughput point that satisfies the constraint; pin it as part of the execution-system
identity (02). Outcome: a named, recorded operating point, not a default concurrency
value nobody chose deliberately.

**[DECISION GATE] Finding-vs-waste classification (G14).** Inputs: a dominant cost
bucket from an autopsy (§5.3) or a live run. Rule and procedure: §9. Outcome: routed
either to the experiment's analysis plan (04) as evidence, or to the engineering
backlog as a priced ticket — never left unclassified.

**[STOP CONDITION] Fit probe fails.** If the fit probe (§5.2.D, §8) shows the target
context length and generation cap do not fit the deployment accelerator's memory with
the project's declared margin: **ABORT or RECALIBRATE** before committing the
expensive run — reduce context/cap, change the operating configuration, or change
target hardware, and re-probe. Never discover this from an out-of-memory failure hours
into a run.

**[STOP CONDITION] Telemetry floor not landed.** If the run is long or expensive
enough to warrant a performance autopsy and the [telemetry floor](GLOSSARY.md#telemetry-floor)
(12) — dual-clock stamps, per-invocation stats, preserved logs, resource sampling — is
not yet in place: land it first. A performance autopsy cannot be retrofitted onto a
run that did not record enough to reconstruct.

**[STOP CONDITION] Cross-tool or cross-definition comparison.** If two performance
numbers being compared came from different benchmarking clients, or different metric-
definition sets, or an unpinned tool version: the comparison is invalid. Re-measure
both on the pinned tool/definition set before drawing any conclusion.

**[STOP CONDITION] Multi-tenant SLA claim from single-tenant data.** A claim about
behavior under concurrent multi-tenant load may not be supported by single-user or
single-stream sweep data (§5.4 — out of scope for v0.1). Re-scope the claim to what
was actually measured, or run the (currently unvalidated) multi-tenant procedure and
label it doctrine-not-yet-exercised.

## 8. Metrics and formulas

**Effective-bandwidth decode arithmetic.**

For a decode-bound (memory-bandwidth-bound) serving workload, achieved throughput is
approximately the accelerator's *effective* (achieved, not spec-sheet) memory
bandwidth divided by the bytes that must be moved per output token:

```
tokens_per_second ≈ effective_bandwidth_bytes_per_s / bytes_moved_per_token
```

- `effective_bandwidth_bytes_per_s` — the memory bandwidth actually achieved during
  decode, measured (not assumed) as `bytes_moved_per_token × measured_tokens_per_second`
  from a real run; units: bytes/second.
- `bytes_moved_per_token` — bytes read from memory per generated token: at minimum the
  active weight bytes touched per forward pass, plus KV-cache read/write bytes at the
  current sequence position; units: bytes/token.

*Worked example (illustrative, invented round numbers):* a quantized model artifact
touches 20 GB of weight bytes per token-generation pass at the context length in use.
An accelerator with a vendor-spec memory bandwidth of 900 GB/s is measured, during a
real decode run, to sustain 600 GB/s of effective bandwidth (an MBU — memory-bandwidth
utilization — of 600/900 ≈ **67%**). Achieved throughput: 600 GB/s ÷ 20 GB/token ≈
**30 tokens/second**. Doubling the achieved bandwidth (a faster accelerator, or a
smaller artifact) roughly doubles throughput; doubling VRAM capacity with no bandwidth
change does not move this number at all — capacity and bandwidth are independent
levers (§4).

**Capacity fit check.**

```
weights_bytes + kv_cache_bytes(context_length, batch) + runtime_overhead_bytes
   ≤ accelerator_memory_bytes − declared_margin
```

- `kv_cache_bytes(context_length, batch)` scales with context length and concurrent
  sequences; it is the term most often underestimated when a cap is raised after the
  fact.
- `declared_margin` — the project's chosen headroom (§6) for driver/runtime overhead
  and to avoid running at 100% occupancy.

*Worked example (illustrative):* accelerator memory 24 GB, declared margin 2 GB
(budget: 22 GB). At a 4,000-token context: weights 12 GB + KV cache 4 GB + overhead
2 GB = 18 GB — **fits**, 4 GB of budget headroom remains. Raising the context to
8,000 tokens with KV cache scaling to 8 GB: 12 + 8 + 2 = 22 GB — **fits exactly**, zero
headroom; RECALIBRATE margin or reduce context before committing an expensive run to
this point. Raising further to a context whose KV cache reaches 12 GB: 12 + 12 + 2 =
26 GB — **does not fit**; the fit probe (§5.2.D) catches this before the run starts,
not after it fails partway through.

**Percentile discipline.** Report p50 (typical case), p95 and p99 (tail — the
experience a meaningful minority of requests actually get) at minimum; report the
sample count each percentile is computed from, since small samples make p99 estimates
unstable regardless of the true distribution.

**Power/energy accounting.** Out of scope here — see chapter 11's amortization,
energy/ops, and cost-per-request formulas, which consume this chapter's throughput and
operating-point outputs as inputs.

## 9. Failure modes and anti-patterns

**The finding-vs-waste decision test (G14).** A dominant cost bucket found in a live
run or a performance autopsy is a **finding** — an object of study, routed to the
experiment's analysis plan — if it is task-intrinsic and changes the comparison the
experiment serves. It is **waste** — overhead to eliminate, routed to the engineering
backlog as a priced ticket — if it is harness/infrastructure friction orthogonal to
the question being asked. Apply all three tests before classifying:

1. **Does the bucket change the measured comparison?** If removing it would change
   which arm looks better, it is signal about the arms, not overhead.
2. **Would eliminating it change the decision, or only the bill?** If the experiment's
   conclusion is unchanged either way, it is closer to waste; if the conclusion
   depends on it, it is a finding regardless of size.
3. **Is it reproducible across the deployment target?** A bucket that only exists
   because of a development-box artifact (a proxy hop, a debug flag, a dev-only
   serialization layer) is waste even if it happens to be large; a bucket that will
   recur in production is a finding even if it is inconvenient.

*Illustrative worked example:* a run shows two dominant buckets. Bucket A —
long-form generation length — is 60% of wall time and differs sharply between two
candidate models. Bucket B — request serialization/retry overhead — is 15% of wall
time and identical across both arms. Test A: changes which arm wins (1: yes), the
decision depends on it (2: yes), recurs at the deployment target (3: yes) —
**A is a finding**, feeding chapter 07's generation-budget calibration. Test B:
changes neither arm's standing (1: no) nor the decision (2: no), and is a fixable
harness property (3: no) — **B is waste**, routed to the backlog with a priced
ticket. [CASE: CASE-005] and [CASE: CASE-006] both turned on this classification: a
dominant truncation-time bucket that was the finding driving the next
budget-calibration experiment, not overhead to optimize away.

**[REJECTED]** (condition: always — these are generically wrong)

- **Single-clock latency reporting.** Publishing latency from one clock source without
  cross-validating against an independent realtime source, especially on a
  virtualized or power-managed host. Any systematic skew invalidates every number
  computed the same way, silently and uniformly.
- **Capacity-implies-bandwidth.** Inferring a workload runs "comfortably" because the
  model fits in memory, without separately measuring achieved bandwidth against the
  workload's actual decode throughput. Fitting is a threshold property; speed is a
  rate property (§4).
- **Cross-tool metric comparison.** Comparing throughput or latency numbers produced
  by different benchmarking clients, or the same client's differently defined metric
  fields, as if the labels alone guaranteed comparability.
- **Sizing from spec-sheet bandwidth.** Using a vendor's peak bandwidth figure as the
  expected achieved throughput input to a capacity or cost projection, instead of a
  measured effective-bandwidth figure from a real run on the actual workload.
- **Skipping the fit probe because the earlier run "felt fine."** A configuration that
  fit at one context length is not evidence a larger context/cap combination will fit;
  KV-cache growth is often the term that gets forgotten.
- **Treating every dominant bucket as waste by default**, or the mirror error —
  treating every dominant bucket as sacred "the finding" to avoid doing the
  engineering work of removing genuine overhead. Apply the three-question test (above)
  instead of a reflex in either direction.
- **Reading a multi-tenant SLA guarantee out of single-user sweep data** (§5.4, §7).
- **Two telemetry sins that defeat an autopsy before it starts** (full treatment in
  chapter 12): poll-based completion detection, which adds per-boundary latency an
  autopsy will misattribute to the workload unless accounted for explicitly; and
  log files that truncate on process restart, which destroy the forensic record a
  later autopsy needs. Prefer event/signal-driven completion hooks and append-only
  logs on any run this chapter's procedures depend on.

## 10. Vendor recipes

| Verdict | Source | Scope | As-of | What it solves | What it does not |
|---|---|---|---|---|---|
| **[FOLLOW]** | [NV-INFERBENCH-001] | LLM inference benchmarking methodology | pub. 2026-07-20, verified 2026-08-21 | Metric definitions, ISL/OSL sweep design, warmup, concurrency-sweep discipline, operating-point selection | Single-user regime, clock validity, capacity-vs-bandwidth, multi-tenant SLA — §5.2/§5.4 supply these |
| **[FOLLOW]** | [NV-AIPERF-001] | Endpoint-agnostic benchmarking client | v0.12.0, verified 2026-08-21 | Implements the sweep/warmup/percentile procedure against any OpenAI-compatible endpoint, across engines | Does not decide the operating point or ISL/OSL shape — project inputs |
| **[REFERENCE]** | [NV-SPARKPERF-001] | Local single-box benchmarking procedure across several serving engines, concurrency=1 template | not independently re-verified (REFERENCE stance) | A concrete offline/online benchmark procedure and single-user template usable as a checklist | No acceptance criteria, no expected numbers, no accuracy component; may pin stale containers — verify before reuse |
| **[ADAPT]** | [EXT-PERF-002] | Load-test type vocabulary (smoke/load/stress/spike/soak/breakpoint) | verified 2026-08-21 | A mature, generic taxonomy for structuring load tests and threshold-as-SLO practice | Not inference-specific — substitute §5.1's metric vocabulary for its generic thresholds |
| **[REFERENCE]** | [EXT-PERF-001] | Serving-throughput method + the *goodput* concept | 2024 | Throughput subject to a latency/quality constraint is the number that matters operationally | Headline figures not independently re-verified; concept reference only |
| **[REFERENCE]** | [EXT-PERF-003] | Serving-configuration sensitivity research | 2025/26, research-only | Corroborates that backend choice alone moves quality scores — evidentiary basis for §4 | Research-only maturity |
| **[REFERENCE]** | [NV-DYNAMOAICONFIG-001] | Datacenter-scale operating-point automation/sizing | verified 2026-08-20 | Mature automation for datacenter-scale sizing decisions | No workstation-class data — do not treat as validating a small-lab claim (§5.4, cross-ref 11) |

## 11. Worked examples

- **Effective-bandwidth and capacity-fit arithmetic** — §8, illustrative worked
  calculations.
- **Finding-vs-waste applied to two cost buckets** — §9, illustrative worked
  classification.
- [CASE: CASE-005](examples/CASE-005_hardware-purchase-discipline.md) — a
  performance autopsy's multi-source reconstruction uncovered a systematic clock
  discrepancy that had silently understated every previously published latency, and
  its counterfactual costing (measured against the workload's actual bottleneck
  resource, not vendor spec) reversed an intuitive hardware-purchase instinct — the
  case behind chapter 11's per-milestone-rental and purchase-trigger discipline.
- [CASE: CASE-006](examples/CASE-006_token-budget-confounding.md) — a generation-cap
  constraint was initially read as a quality difference between two candidates;
  isolating the cap as its own factor showed most of the apparent gap was a capacity
  artifact, not a capability one — the finding-vs-waste test (§9) applied in reverse:
  what looked like noise to explain away was actually the dominant true signal, and
  what looked like a capability story was largely a budget story. Feeds chapter 07's
  generation/reasoning-budget calibration procedure directly.

## 12. Outputs and artifacts

- A recorded [operating point](GLOSSARY.md#operating-point): concurrency, latency
  constraint satisfied, throughput achieved, pinned as execution-system identity (02).
- A fit-probe result (pass/fail, with margin) for any context/cap configuration an
  expensive experiment depends on, recorded before that experiment runs.
- A completed performance autopsy ([templates/PERFORMANCE_AUTOPSY.md](templates/PERFORMANCE_AUTOPSY.md))
  for any run expensive enough to warrant one, every dominant bucket classified
  finding-or-waste (§9) and routed accordingly.
- Effective-bandwidth/MBU figures for the deployment target, feeding chapter 11's
  hardware sizing and rent-vs-buy analysis; percentile latency/throughput figures at
  the operating point, feeding chapter 04's cost accounting and 11's cost-per-request/
  cost-per-solve formulas.
- Waste-classified findings as priced backlog tickets; finding-classified buckets as
  analysis-plan entries (04) or generation-budget-calibration triggers (07).

## 13. Sources

| ID | Role here |
|---|---|
| [NV-INFERBENCH-001] | The FOLLOW-BY-THE-BOOK vendor-mature benchmarking core: metrics, sweep procedure, operating-point selection |
| [NV-AIPERF-001] | FOLLOW benchmarking client; pin-one-tool corroboration |
| [NV-SPARKPERF-001] | REFERENCE local single-box benchmark template (concurrency=1) |
| [EXT-PERF-002] | ADAPT load-test taxonomy for the out-of-scope multi-tenant skeleton (§5.4) |
| [EXT-PERF-001] | REFERENCE goodput concept |
| [EXT-PERF-003] | REFERENCE/research corroboration that backend choice alone moves quality scores — evidentiary basis for §4's separation principle |
| [NV-DYNAMOAICONFIG-001] | REFERENCE datacenter sizing automation; explicit scope limit (no workstation data) |
| [EXT-TESTBED-001] | Corroboration for cheap-sanity-gate-before-scale reasoning behind the fit probe (§5.2.D) |
| [INT-CASE-005] | Performance autopsy + counterfactual hardware costing case |
| [INT-CASE-006] | Generation-cap/capacity confound case, feeding the finding-vs-waste test |

**Gap dispositions in this chapter:**

- **G14 (finding-vs-waste decision test): COVERED** — §9, the three-question test with
  a worked classification, and the decision gate in §7.
- **G9 (multi-tenant capacity/SLA behavior): EXPLICITLY-OUT-OF-SCOPE-FOR-0.1** — §5.4
  states the scope boundary explicitly, gives an adapted load-test taxonomy and vendor
  pointers as REFERENCE only, and marks the gap `doctrine — not yet exercised`. This
  disposition is mirrored in chapter 10, which owns the production-serving side of the
  same boundary.

---

> [← Previous](05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md) · [Index](README.md) · [Next →](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md)
