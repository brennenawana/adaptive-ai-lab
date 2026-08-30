# 06. Inference Performance and Capacity

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [← Previous](05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md) · [Index](README.md) · [Next →](07_OPTIMIZATION_AND_INTERVENTION_LADDER.md)
> **Reading time:** ~20 min. **Prerequisites:** 02 (execution system), 05 (runtime/harness selection).

## 1. Purpose and when to read this

An evaluation round starts after lunch and is finished by the time somebody sits down
the next morning. What that produces is one number — wall clock — with no line items
underneath it.

Ask where the hours went and the room fills with opinions. The card is too small. The
model is too slow. The harness is doing something silly between requests. One of those
might even be right. None of them was measured, and the cheapest opinion to act on is
usually the one that ends in a hardware purchase.

This chapter is about **how fast and how much** — latency, throughput, and capacity for
a [frozen execution system](GLOSSARY.md#frozen-identity). It is not about whether that
system is any *good*. Capability and quality claims belong to chapters 03 and 04. The
claims here are about milliseconds, tokens/second, and gigabytes, and they stay in their
own lane.

Two ideas carry most of the chapter.

The first: **"how fast is it?" has no answer until you choose where to stand.** Latency
and throughput trade against each other, so a system does not have *a* speed — it has a
curve, and you pick a position on it. That chosen position is the
[operating point](GLOSSARY.md#operating-point), and choosing it deliberately is most of
§5.

The second: **a big pile of time is not automatically a wasted pile of time.** Time
spent discovering something real about the system under study is a *finding*. Time
burned on friction that has nothing to do with the question is *waste*. They look
identical on a timeline, they get opposite treatment, and telling them apart is a
procedure rather than a judgment call (§9).

Read this once you have a candidate [execution system](GLOSSARY.md#execution-system)
worth timing: after runtime/harness selection (05), before committing to an operating
point, sizing hardware (11), or spending a long run against a fixed context/budget
configuration.

One thing to say plainly at the top. Published inference-performance methodology is
genuinely mature — vendor benchmarking guidance for metric definitions and sweep
procedure is as close to FOLLOW-BY-THE-BOOK as this playbook gets anywhere. Use it. What
that guidance omits is where this chapter adds its own material: the single-user regime,
clock validity, effective-bandwidth accounting, capacity fit checks before an expensive
run, and a standing forensic procedure for where an expensive run's time actually went.

## 2. Inputs required

- A [frozen execution system](GLOSSARY.md#frozen-identity) (05): model artifact,
  quantization, runtime/engine, hardware/host, context policy, generation settings.
- The workload profile — expected input/output token shapes, expected concurrency
  regime, latency targets — from [PROJECT_PROFILE](templates/PROJECT_PROFILE.md) (01).
- The deployment target's actual hardware specs: memory capacity, memory bandwidth,
  compute. The development box's specs are not a substitute unless it is the same
  machine (02's quantize-for-the-deployment-target rule applies here too).
- The [telemetry floor](GLOSSARY.md#telemetry-floor) (12), landed *before* any run whose
  numbers these procedures will have to explain. Post-run forensics cannot be
  retrofitted: a run that did not record enough cannot be reconstructed afterwards, at
  any price.

## 3. Decisions this chapter supports

- The [operating point](GLOSSARY.md#operating-point) — concurrency, batch, budget — that
  a system is declared to run at.
- Whether a proposed context length and generation cap will physically fit the
  deployment hardware, checked *before* an expensive experiment is committed to it.
- Whether a measured performance number explains an experiment's wall-clock or dollar
  cost, or merely correlates with it — feeding chapter 04's cost accounting and chapter
  07's opportunity-cost test.
- Capacity and bandwidth inputs to hardware sizing and rent-vs-buy analysis (11).
- Whether a dominant cost bucket uncovered during or after a run is a **finding** to
  study or **waste** to eliminate (§9, G14).

## 4. Normative principles

**[PRINCIPLE] Performance and capability stay on separate ledgers.** (evidence:
strong-evidence) A latency figure and a quality figure are both properties of the same
[execution system](GLOSSARY.md#execution-system). Neither substitutes for the other, and
neither is valid outside the [frozen identity](GLOSSARY.md#frozen-identity) it was
measured on. The temptation runs in both directions — a faster configuration feels like
a better one, and a slower one feels like it must be doing more thinking. Reading a
latency change as a quality signal, or the reverse, is the same error inverted. Note how
easily the two get entangled: backend/engine choice alone has been shown to move quality
scores by double-digit percentage points independent of the model [EXT-PERF-003], so the
swap that changed your latency may well have changed your scores too. A change in either
forces re-declaring the identity (02) before any prior number is trusted again.

**[PRINCIPLE] Capacity and bandwidth are different physical constraints; measure
both.** (evidence: strong-evidence — first-principles) Capacity is a threshold: a
configuration either fits in the accelerator's memory or it does not. Bandwidth is a
rate: it sets how fast tokens come out, regardless of how much memory is left unused. So
a model that "fits comfortably" can still be running flat against its bandwidth ceiling.
*Does it fit* and *is it fast* are answers to two different questions, and neither can be
inferred from the other — which is why both get measured. [SCENARIO: SCENARIO-05].

**[PRINCIPLE] A large cost bucket is not automatically waste.** (evidence: inference —
first-principles; full test in §9) Say most of a run's wall clock went into one activity.
The reflex is to call that a problem and engineer it away. But if the activity is
intrinsic to the task, and if it changes the comparison the experiment exists to make,
then it is *evidence about the system under study* — it belongs in the analysis plan,
not the backlog. Treating it as overhead before anyone has looked at what it means
discards the finding along with the inefficiency. [SCENARIO: SCENARIO-06].

**[PRINCIPLE] Measure the metric that will govern the decision, on the tool that will
be reused.** (evidence: strong-evidence) Two benchmarking clients can both report a
field named for time-to-first-token and mean different measurement windows, or different
percentile treatments, by it. Metric definitions are not standardized across clients. So
numbers from different tools, or different definition versions, are not comparable even
when the labels match. Pin one client and one definition set across every measurement
tier of a project [NV-INFERBENCH-001].

## 5. Default procedure

### 5.1 The vendor-mature core — FOLLOW BY THE BOOK

**[FOLLOW: NV-INFERBENCH-001]** (scope: LLM inference benchmarking on an
OpenAI-compatible endpoint; as-of 2026-07-20, live-reverified 2026-08-21) This is the
one place in this playbook where vendor methodology is mature enough to follow without a
decision layer bolted on. Use it as written:

1. **Fix metric definitions before measuring anything.** You need four, and two of them
   share a name. TTFT (time to first token) is how long a user stares at nothing.
   ITL/TPOT (inter-token latency / time per output token) is how fast text arrives once
   it starts. End-to-end request latency is the whole request, start to finish. Then the
   pair that gets conflated: *system* throughput is aggregate tokens/second across all
   concurrent requests, while *per-user* throughput is tokens/second as experienced by
   one request under load — a server can improve the first while making the second
   worse. Record which definition set is in force; do not assume it matches another
   tool's.
2. **Define ISL/OSL pairs per use case.** How long the inputs are and how long the
   outputs are — input-sequence-length and output-sequence-length distributions — are
   properties of your workload, not tool defaults. A chat use case, a
   long-document-summarization use case, and a code-generation use case have materially
   different ISL/OSL shapes and must be measured separately.
3. **Warm up before measuring.** Discard the first requests of a session — cold cache,
   JIT/graph-capture effects, cold model load — from the measured window. The vendor
   guide's own warmup-then-measure discipline applies regardless of engine.
4. **Discipline the request count.** Measure enough requests per operating point that
   percentile estimates are stable. A common rule of thumb is a fixed multiple of the
   concurrency level, not a fixed absolute count.
5. **Sweep concurrency, not request rate, as the primary axis.** Concurrency —
   simultaneous in-flight requests — is the controllable variable that traces out the
   latency-throughput curve. Request-rate sweeps are a secondary view, useful once the
   curve is known.
6. **Plot the latency-throughput curve and select an operating point from it.** Do not
   pick a single concurrency value by guesswork. Sweep from 1 through past the system's
   saturation point, plot latency (percentiles) against throughput, and declare the
   [operating point](GLOSSARY.md#operating-point) as the highest throughput that still
   satisfies the stated latency constraint. Throughput counted only where that
   constraint is met has a name — [goodput](GLOSSARY.md#goodput) [EXT-PERF-001] — and it
   is the quantity the choice is really about, because raw throughput can climb while
   the share of responses anyone can use falls. Pin the chosen point; it is part of the
   execution-system identity going forward.

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
of the box and stays current with engine changes. **[DEFAULT]** (evidence:
strong-evidence, following directly from the metric-definition warning in §4) Pin
**one** client and **one** metric-definition set across every tier of a project —
exploratory runs, capacity planning, and pre-deployment sizing must not silently mix
tools.

### 5.2 What the vendor-mature core omits

The FOLLOW procedure above is written for a datacenter-scale reader with many
concurrent users. Four things a small-lab or single-tenant reader needs are not in it.

**A. The single-user/interactive regime.** Concurrency=1 is not a degenerate corner of
the sweep. It is its own operating point, and for an interactive assistant with one
session per user it is frequently the only one that matters. Measure TTFT and per-token
latency at concurrency=1 explicitly. They do not extrapolate cleanly from a
many-request sweep's tail.

**B. Clock validity.** Record **dual clock stamps** — realtime and monotonic — on every
measured span, and declare an **authoritative clock per metric** before publishing a
number ([dual-clock telemetry](GLOSSARY.md#dual-clock-telemetry),
[authoritative clock](GLOSSARY.md#authoritative-clock)). Here is why that is worth the
trouble. A virtualized or power-managed host can let a monotonic timer drift materially
against realtime while everything appears to run normally. Nothing surfaces the drift
except cross-checking the two stamps against each other, and one clock cannot
cross-check itself. **[DEFAULT]** (evidence: case-study; single-project origin, capped
per the A–H taxonomy) Declare the authoritative clock and record both stamps before
trusting any latency figure. [SCENARIO: SCENARIO-12] is what that looks like when it
fires: both stamps were being written, the two disagreed, and a systematic skew that had
been quietly biasing every latency the project had published came out. A run
instrumented with a single clock produces the same biased numbers and no way to notice —
which is why the floor is landed before the run, not reached for afterwards.

**C. Effective-bandwidth accounting.** Vendor spec-sheet bandwidth is a ceiling, not an
expectation. Decode-bound serving is bound by the bandwidth *achieved*, not the
bandwidth advertised — the [effective bandwidth](GLOSSARY.md#effective-bandwidth) — and
the ratio between the two is a measured property of your stack, never assumed to sit
near 100%. §8 gives the arithmetic and a worked example.

**D. A fit probe before an expensive run depends on a configuration.** Before committing
an expensive run to a specific context length and generation cap, probe that the
configuration actually fits the deployment accelerator's memory: weights, KV cache at
the target context length, and runtime overhead, all together. **[DEFAULT]** (evidence:
heuristic; corroborated in spirit by the general correctness-before-scale discipline of
cheap sanity gates before an expensive run [EXT-TESTBED-001]) Run the probe and record
its result as a named artifact before any run whose science depends on the configuration
fitting. §8 gives the check; §7 states it as a stop condition.

### 5.3 The performance autopsy — a standing post-run procedure

An expensive run should come back with a receipt, not just a total. Any run expensive
enough to matter gets a forensic reconstruction of where its wall clock went — whether
or not anything looked wrong, because "nothing looked wrong" is exactly the condition
under which a silent cost sits unexamined for months. Template:
[templates/PERFORMANCE_AUTOPSY.md](templates/PERFORMANCE_AUTOPSY.md).

**[DEFAULT] The autopsy procedure.** (evidence: case-study; single-project origin,
capped per the A–H taxonomy; the method — multi-source reconstruction with explicit
evidentiary labeling — generalizes even though its one exercised instance does not)

1. **Reconstruct the timeline from multiple sources.** Pull timing from every
   independent source that recorded it — lifecycle events, per-invocation telemetry,
   server/engine logs, database timestamps, commit times, orchestration transcripts —
   and lay them against each other. No single source is trusted alone; where two
   disagree, that disagreement is itself a result. Label every figure by how you know
   it: directly measured, derived by arithmetic, or estimated.
2. **Find the critical path.** Wall time splits into two kinds. Some of it actually
   gated completion — serial dependencies, contention, a single-slot policy that let
   only one thing run at a time. The rest happened for free inside another activity's
   window. Only critical-path time is a candidate for "a fix would have saved this," and
   confusing the two is how projects buy speed-ups that change nothing.
3. **Attribute the critical path to cost buckets.** Use a standard, run-to-run-comparable
   set: task-intrinsic workload, infrastructure/tooling overhead, implementation and
   debugging, human/orchestration review, documentation. The same buckets every time is
   what makes two autopsies comparable at all.
4. **Cost the counterfactuals.** For each candidate intervention — more hardware, a
   faster device, a smaller budget, parallel execution across independent execution
   systems — compute what it would have saved *given the measured bottleneck*, never
   given headline specs. A hardware upgrade that misses the actual bottleneck resource
   can make a workload slower, not faster (§8's arithmetic). [SCENARIO: SCENARIO-05].
5. **Cross-check the clocks.** Compare every monotonic-derived figure against an
   independent realtime source. A systematic skew invalidates every prior number
   computed the same way, uniformly, until corrected.
6. **Apply the finding-vs-waste test (§9)** to every dominant bucket before recommending
   anything about it.
7. **Write the missing-evidence section.** It is mandatory, and it names explicitly what
   could not be reconstructed and why. An autopsy that hides its own blind spots teaches
   the next one to hide them too.
8. **Feed the reconstruction gaps into the telemetry floor (12).** Whatever had to be
   inferred because nobody recorded it is next run's telemetry requirement — not next
   autopsy's forensic challenge.

If you have never done one, start with the run you finished most recently. Pull whatever
timing sources already exist for it and work steps 1 through 3 — timeline, critical path,
buckets. A partial autopsy that names what it could not reconstruct (step 7) is worth far
more than no autopsy, because that list of gaps is exactly the instrumentation to land
before the next expensive run (step 8).

### 5.4 Multi-tenant / concurrent-SLA serving — explicitly out of scope for v0.1

Everything above characterizes a system serving one workload stream at a time: an
interactive session, or a swept-but-still-single-tenant benchmark. Real production
serving under many simultaneous tenants with per-tenant SLA commitments is a distinct
discipline — admission control, fairness across tenants, SLO-threshold alerting under
sustained concurrent load, burn-down accounting against an error budget — and this
playbook does not yet validate a methodology for it. **This is stated explicitly rather
than left silent** (mirrored in chapter 10, which owns the production-serving side of
the same gap). What follows is a skeleton and pointers, not a procedure to follow:

- **Load-test taxonomy** (adapt it, don't invent your own labels):
  **[ADAPT: EXT-PERF-002]** k6's test-type vocabulary — smoke (does it work at all),
  average-load (expected steady state), stress (find the breaking point), spike (sudden
  burst), soak (sustained duration, catches leaks and drift), breakpoint (deliberate
  push past capacity) — generalizes cleanly from HTTP APIs to inference-serving
  endpoints. What is missing for inference specifically: SLO thresholds must be
  expressed in the metric vocabulary of §5.1 — TTFT/ITL/percentile latency under
  concurrency — not generic request-duration, so substitute your contract's
  latency/quality thresholds for k6's generic pass/fail threshold syntax.
- **Sizing automation pointer:** **[REFERENCE: NV-DYNAMOAICONFIG-001]** — datacenter
  operating-point automation and sizing tooling exists and is mature for datacenter
  deployments. It has no data for workstation-class accelerators and should not be
  treated as validating a small-lab sizing claim.
- **Doctrine status:** *status: doctrine — not yet exercised (see this section for
  what validation would look like: an admission-control policy, a per-tenant fairness
  metric, and a burn-down-against-error-budget procedure, measured against real
  concurrent multi-tenant traffic before any SLA claim is made from it)*.

## 6. Project adaptation parameters

| Parameter | What it governs | How to set it |
|---|---|---|
| **ISL/OSL distribution per use case** | Which workload shape the sweep characterizes | Measure it from real or representative traffic; a generic benchmark's shape is not yours |
| **Concurrency sweep range** | How much of the latency-throughput curve you see | From 1 through past measured saturation; include concurrency=1 explicitly if any interactive use case exists |
| **Warmup request count** | Keeps cold-start effects out of the measurement | Enough requests to reach steady per-token latency. Verify by inspecting the discarded window — a fixed count that worked elsewhere does not transfer |
| **Request-count multiplier** | Percentile stability at each operating point | A fixed multiple of concurrency is a common starting rule; check that percentile estimates have converged before trusting them |
| **Latency constraint for operating-point selection** | Which point on the curve you choose | From the use case's actual UX/SLA requirement (01) — not from whatever the curve happens to offer |
| **Percentile set reported** | What "typical" and "tail" mean for this workload | p50/p95/p99 as a floor; add p999 for high-request-volume services where rare tail events matter operationally |
| **Authoritative clock per metric** | Which timestamp source a published number is computed from | Declared in the experiment contract (04) before the run; re-declared if the host or virtualization layer changes |
| **Generation cap / reasoning budget** | Where truncation starts bounding outcomes | Calibrated by the dedicated procedure in chapter 07 (rung 5), not here. This chapter only verifies that the chosen cap *fits* (§8) |
| **Fit-probe margin** | How much headroom below capacity counts as "fits" | Project-set. Leave enough for KV-cache growth at the context length production will actually use, not the benchmark's |

## 7. Decision gates and stopping conditions

**[DECISION GATE] Operating-point selection.** Inputs: the swept latency-throughput
curve (§5.1) and the use case's latency constraint (01). Rule: choose the highest
throughput point that satisfies the constraint, and pin it as part of the
execution-system identity (02). Outcome: a named, recorded operating point — rather than
a default concurrency value that nobody chose on purpose.

**[DECISION GATE] Finding-vs-waste classification (G14).** Inputs: a dominant cost
bucket, from an autopsy (§5.3) or a live run. Rule and procedure: §9. Outcome: the
bucket is routed either to the experiment's analysis plan (04) as evidence, or to the
engineering backlog as a priced ticket. It is never left unclassified.

**[STOP CONDITION] Fit probe fails.** If the fit probe (§5.2.D, §8) shows the target
context length and generation cap do not fit the deployment accelerator's memory with
the project's declared margin: **ABORT or RECALIBRATE** before committing the expensive
run. Reduce context or cap, change the operating configuration, or change target
hardware — then re-probe. Never discover this from an out-of-memory failure hours into a
run.

**[STOP CONDITION] Telemetry floor not landed.** If the run is long or expensive enough
to warrant a performance autopsy and the [telemetry floor](GLOSSARY.md#telemetry-floor)
(12) is not yet in place — dual-clock stamps, per-invocation stats, preserved logs,
resource sampling — land it first. A performance autopsy cannot be retrofitted onto a
run that did not record enough to reconstruct.

**[STOP CONDITION] Cross-tool or cross-definition comparison.** If two performance
numbers being compared came from different benchmarking clients, or different
metric-definition sets, or an unpinned tool version, the comparison is invalid.
Re-measure both on the pinned tool and definition set before drawing any conclusion
from them.

**[STOP CONDITION] Multi-tenant SLA claim from single-tenant data.** A claim about
behavior under concurrent multi-tenant load may not be supported by single-user or
single-stream sweep data (§5.4 — out of scope for v0.1). Re-scope the claim to what was
actually measured, or run the (currently unvalidated) multi-tenant procedure and label
it doctrine-not-yet-exercised.

## 8. Metrics and formulas

**Effective-bandwidth decode arithmetic.**

Generating one token at a time means reading a lot of memory per token, so for a
decode-bound (memory-bandwidth-bound) serving workload, achieved throughput is roughly
the accelerator's *effective* memory bandwidth — achieved, not spec-sheet — divided by
the bytes that have to be moved per output token:

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

That last sentence is the one that saves money. A bigger card is not automatically a
faster card, and the arithmetic above tells you which one you are buying.

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

Notice which term moved. The weights never changed. Raising the context length is what
consumed the budget, and that is the term people forget when they raise a cap late in a
project.

**Percentile discipline.** Report p50 (typical case), p95 and p99 (tail — the
experience a meaningful minority of requests actually get) at minimum; report the
sample count each percentile is computed from, since small samples make p99 estimates
unstable regardless of the true distribution.

**Power/energy accounting.** Out of scope here — see chapter 11's amortization,
energy/ops, and cost-per-request formulas, which consume this chapter's throughput and
operating-point outputs as inputs.

## 9. Failure modes and anti-patterns

**The finding-vs-waste decision test (G14).** A run spent most of its wall clock in one
place. Before anyone optimizes it away, decide which of two things it is —
[finding vs waste](GLOSSARY.md#finding-vs-waste):

- It is a **finding** — an object of study, routed to the experiment's analysis plan —
  if it is task-intrinsic and changes the comparison the experiment serves.
- It is **waste** — overhead to eliminate, routed to the engineering backlog as a priced
  ticket — if it is harness or infrastructure friction, orthogonal to the question being
  asked.

The distinction is not cosmetic. Eliminating waste buys you time. Eliminating a finding
destroys the measurement you were taking, and it usually looks like good engineering
while it happens. Ask all three questions before classifying:

1. **Does the bucket change the measured comparison?** If removing it would change which
   arm looks better, it is signal about the arms, not overhead.
2. **Would eliminating it change the decision, or only the bill?** If the experiment's
   conclusion is unchanged either way, it is closer to waste; if the conclusion depends
   on it, it is a finding regardless of size.
3. **Is it reproducible across the deployment target?** A bucket that exists only
   because of a development-box artifact — a proxy hop, a debug flag, a dev-only
   serialization layer — is waste even if it is large. A bucket that will recur in
   production is a finding even if it is inconvenient.

*Illustrative worked example:* a run shows two dominant buckets. Bucket A —
long-form generation length — is 60% of wall time and differs sharply between two
candidate models. Bucket B — request serialization/retry overhead — is 15% of wall
time and identical across both arms. Test A: changes which arm wins (1: yes), the
decision depends on it (2: yes), recurs at the deployment target (3: yes) —
**A is a finding**, feeding chapter 07's generation-budget calibration. Test B:
changes neither arm's standing (1: no) nor the decision (2: no), and is a fixable
harness property (3: no) — **B is waste**, routed to the backlog with a priced
ticket.

Two of this chapter's invented scenarios turn on this classification, from opposite
ends. In [SCENARIO: SCENARIO-05] the dominant bucket is serial model decoding
on a single card — task-intrinsic, not harness friction, and therefore the thing every
hardware counterfactual has to be costed against rather than something to engineer away.
In [SCENARIO: SCENARIO-06] the dominant bucket is generation truncating at the cap, and
it turns out to be the finding that drives the next budget-calibration experiment —
not overhead to optimize away.

**[REJECTED]** (condition: always — these are generically wrong)

- **Single-clock latency reporting.** Publishing latency from one clock source without
  cross-validating against an independent realtime source, especially on a
  virtualized or power-managed host. Any systematic skew invalidates every number
  computed the same way, silently and uniformly.
- **Capacity-implies-bandwidth.** Inferring that a workload runs "comfortably" because
  the model fits in memory, without separately measuring achieved bandwidth against the
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
- **Treating every dominant bucket as waste by default** — or the mirror error, treating
  every dominant bucket as a sacred "finding" to avoid the engineering work of removing
  genuine overhead. Apply the three-question test above instead of a reflex in either
  direction.
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
- [SCENARIO: SCENARIO-05](examples/SCENARIO-05_hardware-purchase-discipline.md) — a
  performance autopsy reconstructed where a long evaluation round's hours actually went,
  and its counterfactual costing — measured against the workload's real bottleneck
  resource rather than vendor spec — reversed an intuitive hardware-purchase instinct.
  The candidate device's advertised size said "upgrade"; its bandwidth said otherwise.
  This is the case behind chapter 11's per-milestone-rental and purchase-trigger
  discipline.
- [SCENARIO-12](examples/SCENARIO-12_restart-instability-paired-controls.md) — dual
  clock stamps on every span surfaced a systematic skew on a virtualized host that had
  been biasing every latency figure the project published. Nothing looked wrong from the
  outside; only the disagreement between the two stamps showed it. The clock-validity
  requirement in §5.2.B is what that scenario is arguing for.
- [SCENARIO: SCENARIO-06](examples/SCENARIO-06_token-budget-confounding.md) — a
  generation-cap constraint was initially read as a quality difference between two
  candidates. Isolating the cap as its own factor showed most of the apparent gap was a
  capacity artifact, not a capability one — the finding-vs-waste test (§9) applied in
  reverse: what looked like noise to explain away was actually the dominant true signal,
  and what looked like a capability story was largely a budget story. Feeds chapter 07's
  generation/reasoning-budget calibration procedure directly.

## 12. Outputs and artifacts

- A recorded [operating point](GLOSSARY.md#operating-point): concurrency, latency
  constraint satisfied, throughput achieved, pinned as execution-system identity (02).
- A fit-probe result (pass/fail, with margin) for any context/cap configuration an
  expensive experiment depends on, recorded before that experiment runs.
- A completed performance autopsy ([templates/PERFORMANCE_AUTOPSY.md](templates/PERFORMANCE_AUTOPSY.md))
  for any run expensive enough to warrant one, with every dominant bucket classified
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
