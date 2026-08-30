# Performance Autopsy

> A long run finished. You know the total it cost and nothing about where that
> total went — and the proposals arrive anyway: a bigger card, a different
> runtime, a second node. Every one of them is a guess about a bottleneck nobody
> has located.
>
> This template locates it. Rebuild the timeline from several independent
> telemetry sources, work out which phases actually gated completion, attribute
> the cost across buckets, price the counterfactuals against the measured
> bottleneck, and confirm the clocks agree — before any of this run's cost or
> latency numbers is trusted for a capacity, operating-point, or hardware
> decision. See [performance autopsy](../GLOSSARY.md#performance-autopsy).
>
> Index: [../README.md](../README.md) · Governing chapter:
> [06. Inference Performance and Capacity](../06_INFERENCE_PERFORMANCE_AND_CAPACITY.md)

## When to use / when not to

- **MUST** use this before any run's cost, latency, or throughput number is
  written into a report, into an
  [experiment contract](EXPERIMENT_CONTRACT.md)'s economics analysis, or into a
  [compute demand ledger](COMPUTE_DEMAND_LEDGER.md) entry that will argue toward a
  [purchase trigger](../GLOSSARY.md#purchase-trigger).
- **SHOULD** use it whenever a run's cost or latency is surprising or disputed —
  before proposing hardware, a config change, or a schedule change to fix it. §7's
  counterfactuals are the check against buying compute to fix a bottleneck that is
  not compute.
- It is worth doing when nothing looked wrong, too. "Nothing looked wrong" is
  exactly the condition under which a silent cost sits unexamined for months.
- **MUST NOT** be attempted on a run whose
  [telemetry floor](../GLOSSARY.md#telemetry-floor) was not met. Post-run
  forensics cannot be retrofitted onto telemetry that was never collected. State
  the gap as a limitation (§2) and fix the instrumentation before the next run —
  do not fill §3 and §4 with reconstruction dressed up as measurement.
- **Do not** use it for interactive, single-call latency spot-checks with no
  decision attached. An informal note is enough at Tier 1 (see below).

If you have never done one, start with the run you finished most recently. Pull
whatever timing sources already exist and work §3 through §5 — timeline, critical
path, buckets. A partial autopsy that names what it could not reconstruct is worth
far more than none, because that list of gaps is exactly the instrumentation to
land before the next expensive run.

## Rigor-tier applicability

| Tier | Requirement |
|---|---|
| Tier 1 — Exploratory | Optional. An informal note of what a run cost is sufficient unless a decision is being made from it. |
| Tier 2 — Consequential (default) | **MUST** be completed whenever a run's cost or latency result feeds an [operating-point](../GLOSSARY.md#operating-point) decision, a capacity claim, or an entry toward a purchase trigger. |
| Tier 3 — High-stakes/regulated | **MUST** be completed as Tier 2, plus: retained in the tamper-evident [record of record](../GLOSSARY.md#record-of-record); revisited at the periodic methodology audit; any counterfactual used to justify spend is reviewed by someone other than its author. |

---

## 1. Run Identity and Question

*Which run this is, and what decision the autopsy exists to serve.*

- **Run ID / link to raw telemetry:** [identifier or link]
- **Execution system:** [the full
  [execution system](../GLOSSARY.md#execution-system) behind this run — model,
  runtime, hardware, harness, config. A cost or latency number is comparable only
  within one frozen identity, so a vague answer here makes every number below
  incomparable to anything]
- **The question this autopsy answers:** [state it as a decision question. "Is
  this run's cost task-intrinsic or fixable, and does the answer justify a second
  node?" — not "how long did it take"]
- **Date / window:** [date/time range]

## 2. Telemetry Sources Inventoried

*What you actually have to work from, and — mandatory — what you do not. An
autopsy that hides its own blind spots teaches the next one to hide them too.*

- **Sources available:** [list what exists for this run: lifecycle events,
  per-invocation stats, server/engine logs, resource sampler,
  [dual-clock telemetry](../GLOSSARY.md#dual-clock-telemetry) stamps]
- **Gaps:** [what is missing, and what it blocks downstream. Be specific about the
  consequence: "no resource sampler for minutes 40–55, so §5's GPU-idle
  attribution for that window is inferred from wall-clock gaps rather than
  measured" tells the next reader how far to trust that row. Every gap here is
  next run's telemetry requirement, not next autopsy's forensic challenge]

## 3. Timeline Reconstruction

*Where the wall clock went, assembled from more than one source. No single source
is trusted on its own.*

- **Per-phase wall clock, by [authoritative clock](../GLOSSARY.md#authoritative-clock):**
  [table: phase | start | end | duration | clock used. Label each figure by how
  you know it — directly measured, derived by arithmetic, or estimated]
- **Cross-source consistency check:** [do independent sources — client-side timing
  vs. server logs, say — agree within a stated tolerance? Where two disagree, that
  disagreement is itself a result, not noise to average away]

## 4. Critical Path

*Only some of the elapsed time actually gated completion. The rest happened for
free, inside somebody else's window. Confusing the two is how projects buy
speed-ups that change nothing.*

- **The dominant serial chain:** [the sequence of phases that, end to end, bounds
  the run's total wall clock — the only phases whose speedup would shorten the run
  at all]
- **Slack per branch:** [for every phase NOT on the critical path, how much it
  could grow before it became the bottleneck. This is the number that says whether
  optimizing a given phase is worth anything]

## 5. Cost-Bucket Attribution

*Where the money and the minutes landed, and which of them you are allowed to want
back.*

- **Buckets:** [compute / wait / overhead, or your own breakdown — attribute the
  run's total cost or wall clock across them. Use the same bucket set every time:
  two autopsies with different buckets cannot be compared]
- **Finding-vs-waste verdict per bucket:** [for each bucket, one of two verdicts. A
  **finding** is task-intrinsic, worth studying, and moves the decision the
  experiment serves. **Waste** is harness or infrastructure friction orthogonal to
  the question. See [finding vs waste](../GLOSSARY.md#finding-vs-waste). The test
  matters because eliminating a finding destroys the measurement you were taking.
  Route waste to an engineering fix; route findings into the next experiment
  contract or capacity plan]

## 6. Clock Validity

*A machine has more than one clock and they do not always agree. Check, rather
than assume, before trusting any duration above.*

- **Realtime-vs-monotonic delta:** [measured, not assumed — state it per phase or
  per host]
- **Skew found?** [yes/no + magnitude. A nonzero, materially-sized skew invalidates
  any duration computed from the wrong clock, uniformly, until corrected.
  Virtualized and shared environments make this a measured property rather than a
  given [EXT-DETERM-001] — if a correction is needed, restate above which numbers
  used which clock]

## 7. Counterfactuals

*This is the section that changes what you buy next. Show the arithmetic for each
one; do not assert it. Every counterfactual is scoped by §4 and §5 — speeding up
something off the critical path, or something that is waste rather than
compute-bound, saves nothing real, and a hardware upgrade aimed at the wrong
resource can make a workload slower.*

- **What N parallel nodes would have saved:** [arithmetic against the critical
  path in §4 — parallelizing off-critical-path work saves nothing]
- **What a faster device would have saved:** [arithmetic against the compute-bound
  finding buckets in §5]
- **What a smaller generation/reasoning budget would have saved:** [arithmetic
  shown; note any quality cost this trade would carry, even if it is unmeasured
  here]
- **What a different quantization/precision would have saved:** [arithmetic
  against measured
  [effective bandwidth](../GLOSSARY.md#effective-bandwidth) if the run is
  decode-bound — the spec-sheet figure will overpromise. State the accuracy
  question as a separate, unresolved cost; see
  [goodput](../GLOSSARY.md#goodput) [EXT-PERF-001]]

## 8. Actions

- [table: finding → action → owner. Waste-bucket findings route to an engineering
  fix. Task-intrinsic findings route into the next
  [experiment contract](EXPERIMENT_CONTRACT.md) or capacity plan. Do not let a
  real finding get closed as a bug ticket, and do not let harness friction get
  written up as a research result. Anything §2 could not reconstruct becomes a
  telemetry requirement for the next run, with an owner like everything else]

## Delete No Section

Every numbered section above **MUST** appear in a filled autopsy. If a section
genuinely does not apply, write the section header with the body `N/A — [reason]`
rather than omitting it. Absence is a decision; a reader needs to see that the
decision was made, not guess whether it was skipped.

---

## Miniature Filled Example

*Illustrative example — synthetic. Invented project: a nightly document-extraction
batch run that took 40% longer than the prior week, triggering a proposal to add a
second GPU node before anyone checked why. Tier 2.*

**§1 Identity:** `batch-run-2026-08-19`. Execution system: extraction model build
4.2 / inference runtime 2.3 / single GPU node A / batch harness 1.1. Question: is
the slowdown compute-bound (buy hardware) or overhead (fix the harness)? Window:
2026-08-19 22:00–2026-08-20 05:40 UTC.

**§2 Telemetry:** Lifecycle events, per-item stats, server logs, resource sampler
(30s interval), dual clocks all present. Gap: no per-item queue-wait timestamp
between 22:00–23:10 (a log-rotation bug mid-run) — §3 for that window is
reconstructed from item counts, not timestamps.

**§3 Timeline:** Load/warm-up 8 min. Steady-state processing 6h 40min. Teardown
4 min. Cross-check: server-log item count and client-side completion count agree to
within 3 of 12,000 items.

**§4 Critical path:** Steady-state processing is the entire critical path; load and
teardown are fixed, small, and not addressable by parallelism.

**§5 Cost buckets:** Compute (GPU busy) 71% of wall clock — **finding**,
task-intrinsic. Queue wait (single-worker serialization) 24% — **waste**, a harness
concurrency cap left at 1. Misc overhead 5% — waste, negligible.

**§6 Clock validity:** Realtime-vs-monotonic delta measured under 200ms across the
run; no material skew.

**§7 Counterfactuals:** Raising the harness concurrency cap from 1 to 4 (same
single node) would reclaim most of the queue-wait bucket: 24% × 6h48m ≈ 98 minutes
recoverable without new hardware. A second GPU node would address only the 71%
compute bucket, and only after the concurrency fix lands and is re-measured — its
projected saving on today's numbers is smaller than the concurrency fix's.

**§8 Actions:** Finding: concurrency cap of 1 is a config default, not a measured
limit → action: raise to 4, re-run, owner: platform engineering, due next run.
Finding: the compute bucket is real and task-intrinsic → action: log it as a demand
ledger data point, not grounds for an immediate purchase, owner: project lead.
Second-node purchase deferred pending re-measurement.

---

**Governing chapter:** [06. Inference Performance and Capacity](../06_INFERENCE_PERFORMANCE_AND_CAPACITY.md)

**Related templates:** [COMPUTE_DEMAND_LEDGER.md](COMPUTE_DEMAND_LEDGER.md)
(purchase-trigger evidence) ·
[EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md) (§16 analysis-plan economics)

**See also:** [SCENARIO-05](../examples/SCENARIO-05_hardware-purchase-discipline.md)
— an invented clinic whose autopsy showed the proposed second card would have saved
nothing, and whose pre-written purchase trigger kept the capital unspent

[Index](../README.md) · [Glossary](../GLOSSARY.md)
