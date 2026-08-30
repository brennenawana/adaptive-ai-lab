# 12. Observability, Learning, and Promotion

> Part of the **Adaptive AI Systems Playbook** v0.1.1 ·
> [← Previous](11_ECONOMICS_HARDWARE_AND_CLOUD.md) · [Index](README.md) · [Next →](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md)
> **Reading time:** ~20 min. **Prerequisites:** [02](02_EXECUTION_SYSTEM_MODEL.md), [03](03_EVALUATION_FOUNDATION.md), [04](04_EXPERIMENT_DESIGN_AND_STATISTICS.md), [06](06_INFERENCE_PERFORMANCE_AND_CAPACITY.md), [08](08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md).

## 1. Purpose and when to read this

A long run finished overnight. In the morning somebody asks a fair question about it: did
any of those requests get cut off mid-answer, or did every one of them stop because the
model was finished?

Which answer you can give was settled before the run started, and it is too late now to
change it. Either something wrote a finish reason beside every request while the requests
were happening — in which case you answer in about a minute — or nothing did, and the
answer is not merely awkward to obtain. It is gone. The requests are over, the process
that served them has exited, and no amount of money or cleverness rebuilds a field that
nobody wrote.

That asymmetry is what this chapter turns on. Recording the field costs a few bytes and
one decision taken in advance. Not recording it costs everything the field would have
explained, permanently — and the bill arrives at the moment someone needs the answer,
which is always after the only opportunity to pay it cheaply has closed.

Half of what follows is a mature published discipline and half of it is not, and knowing
which half is which tells you what you have to build yourself. Production observability —
metrics, request tracing, structured logs for a deployed serving stack — is well
documented, and vendors ship most of the machinery. The *experimentation* telemetry that
every earlier chapter quietly depends on is not documented anywhere a vendor ships it: the
[performance autopsy](GLOSSARY.md#performance-autopsy) (06), the
[look ledger](GLOSSARY.md#look-ledger) (04), and the
[reproducibility-boundary](GLOSSARY.md#reproducibility-boundary) probes (02) all need
records that no product writes for you by default. This chapter supplies the missing
minimum: what to instrument before a long or expensive run, the durable record every task
execution must leave behind, the discipline that keeps a growing telemetry pipeline honest
about its own correctness, and the loop that carries production evidence back into the lab.

One word in the title needs narrowing, because the book uses it for two different things.
Chapter 10 promotes a whole *system* along a deployment pipeline: offline, then
[shadow](GLOSSARY.md#shadow-deployment), then canary, then rollout. This chapter is about
the promotion a single learned or automated *component* goes through, and it is best read
as three positions rather than four stages:

- **Observed.** The component runs and its decisions are recorded and scored, but nothing
  downstream acts on them.
- **Trusted.** It has passed [observe-only graduation](GLOSSARY.md#observe-only-graduation)
  (08) — the gate that says its recorded decisions were good enough, on evidence that
  survived a [leakage audit](GLOSSARY.md#leakage-audit) — and is now allowed to act.
- **Unattended.** It goes on acting without a person reading its output. That is a licence
  rather than a destination, and licences expire.

Chapter 08 issues the licence. This chapter is about the ongoing evidence that keeps it
valid and the trigger that takes it back.

Read this chapter:

- Before authorizing any run whose telemetry you would regret not having — a multi-hour
  experiment, a milestone-defining comparison, anything a future performance autopsy will
  be asked to explain.
- When standing up production observability for the first time (§5.4, §10).
- When a learned, routed, or automated component has graduated past observe-only (08) and
  now needs a monitoring plan for as long as it keeps running (§5.7, §7).
- When you are closing the loop from production failures back into the evaluation suite
  (03) or the training data (09).

## 2. Inputs required

- **The project's frozen [execution system](GLOSSARY.md#execution-system) identity** (02).
  Telemetry that is not scoped to a specific runtime, model, host, and configuration is
  not comparable to anything, including itself a month later.
- **The [rigor dial](GLOSSARY.md#rigor-dial) and
  [stakes tier](GLOSSARY.md#stakes-tier)** from the
  [project profile](GLOSSARY.md#project-profile) (00 §6, 01). These set how much of this
  chapter's artifact set is mandatory for you rather than optional (§6).
- **Any existing experiment contract** (04) whose runs this telemetry will have to explain.
  The contract tells you which fields somebody is already counting on.
- **The deployment-stage inventory from chapter 10** — offline, shadow, canary,
  production. The trajectory record carries a deployment-stage field, and that field needs
  a defined vocabulary to hold.
- **Privacy and residency constraints** from the project profile (01) and the
  [clean-room boundary](GLOSSARY.md#clean-room-boundary) (13). These gate what the
  telemetry floor is permitted to capture at all, so they are an input rather than a later
  review.

## 3. Decisions this chapter supports

- What must be instrumented before a long or expensive run is authorized at all.
- What minimum record one task execution has to leave behind, and where each of its fields
  comes from.
- How to split storage into separate planes, so that retention, privacy, and promotion
  rules attach to the right bucket instead of the loosest one.
- What production observability baseline to adopt at deployment — and, just as
  importantly, what that baseline does *not* give you.
- Whether the telemetry pipeline is itself trustworthy. Somebody has to check the checker.
- In what order a production failure re-enters the lab.
- Whether an automated or learned component still holds its licence to run unattended, or
  whether a de-automation trigger has fired.
- When the next periodic self-audit of your own methodology is due.

## 4. Normative principles

**[PRINCIPLE] — Telemetry precedes spend.** (case-study + inference)
You are about to start something that will occupy a machine for eight hours. The
instrumentation question — what should this write down? — feels like a detail you can
settle later, once you know whether the run produced anything interesting. It is not
settleable later. A [performance autopsy](GLOSSARY.md#performance-autopsy) cannot be
retrofitted: once a session ends, its per-invocation timings, finish reasons, and server
lifecycle are either captured or gone forever. A completed run that never emitted them
produces a bill with no receipt — every hour it spent was real, and nothing downstream can
attribute it, defend it, or learn from it. So the instrumentation decision has to be made
*before* the run it will need to explain.
The experience behind this rule comes from one project, whose records are not published
here; the scenarios linked below are invented illustrations of the same shape rather than
the evidence for it. Preserved per-invocation telemetry — finish reasons, dual clocks,
session identity — is what lets a later counterfactual-costing analysis attribute a cost
bucket and refute an intuitive hardware purchase after the fact;
[SCENARIO: SCENARIO-05] walks that reasoning through. A dual-clock stamp on every span is
what surfaces a systematic clock-skew artifact that would otherwise silently bias every
latency a project publishes; [SCENARIO: SCENARIO-12] walks that one through. Land the floor
(§5.1) before authorizing the run, not during its postmortem.

**[PRINCIPLE] — Every span carries two clocks and a declared authority.** (strong-evidence)
Chapter 02 establishes [dual-clock telemetry](GLOSSARY.md#dual-clock-telemetry) and the
[authoritative clock](GLOSSARY.md#authoritative-clock) declaration as requirements for a
measurement to be valid at all. This chapter restates them as an *instrumentation*
requirement, for a mechanical reason: both are only useful if they are captured at write
time, and neither can be reconstructed at read time.
Here is what they buy. A virtualized or power-managed host — a container, a VM, a
WSL2-class compatibility layer — can let its monotonic clock drift against realtime while
everything appears to be running normally. Nothing surfaces that drift except comparing
the two stamps against each other, and a clock that was only sampled once has nothing to
be compared with [SCENARIO: SCENARIO-12].

**[PRINCIPLE] — A measurement pipeline nobody audits is a pipeline nobody should trust.**
(strong-evidence)
You test the code that does the work. The code that measures the work usually gets no
tests at all, which is backwards, because a defect there corrupts every number the project
has published rather than one feature. So the same discipline applies to it:
cross-source consistency checks, injected synthetic events with a known expected shape,
and regression tests over the telemetry pipeline itself.
The generic form of this is well established outside this playbook. A mature production-ML
test rubric scores whether training-time and serving-time computation agree, among its
minimum tests, and takes the *minimum* across categories as the overall score rather than
an average that would let one weak leg hide behind three strong ones [EXT-OPS-002].
A telemetry defect discovered after publication invalidates every number computed through
it while it was broken. Treat a telemetry-pipeline change exactly like a
[suite release](GLOSSARY.md#suite-release) — versioned, with a stated cutover, never a
silent in-place patch. That is 03's [criteria-drift](GLOSSARY.md#criteria-drift) discipline
pointed at the instrument instead of at the eval.

**[DEFAULT] — Separate data planes by who writes, who reads, and what governs retention.**
(heuristic)
A project accumulates at least five distinct kinds of state, and they are tempting to keep
in one store: authoritative business data, retrieval and knowledge content, working task
state, trajectory records (this chapter), and learned or mutated assets. They differ in
who may write them, who may read them, how long they may be kept, and what privacy class
governs them (13).
Collapse them into one undifferentiated store and you get one retention policy, one access
rule, and one privacy classification silently governing all five — in practice the least
restrictive of the five, which is exactly backwards. §5.3 gives the separation table.

**[PRINCIPLE] — Failures re-enter the lab in ladder order, never straight to training.**
(consensus)
A production failure is evidence, and evidence gets triaged the same way the
[intervention ladder](GLOSSARY.md#intervention-ladder) (07) triages any measured gap.
First as an evaluation candidate: does the suite already know about this failure mode, and
if not, why not? Then, in ladder order, as a retrieval or context fix. Only later as
training data.
Holding out annotated production examples for regression testing is a named, mature
practice [EXT-OPS-002]. Routing a failure straight into a fine-tuning run skips every
cheaper rung, and the ladder requires evidence before a rung may be skipped.

**[DEFAULT] — An automated component's license to run unattended is conditional, not
permanent.** (inference)
[Observe-only graduation](GLOSSARY.md#observe-only-graduation) (08) is a staged *entry*
condition. Passing it once tells you the component was good enough on the population it
was measured against, on the day it was measured. It guarantees nothing about whether the
input distribution, the escalation rate, or the verifier-pass rate stays where it was.
So the same leakage-audit and shadow-period discipline that earned the right to act has to
keep being paid for as long as the component keeps acting — as a pre-registered monitoring
plan carrying [consequence-bearing tolerances](GLOSSARY.md#consequence-bearing-tolerance)
that can pull the component back to observe-only. §5.7 gives the monitoring table.
*status: doctrine — not yet exercised (see §5.7 for what validation would look like)*

**[PRINCIPLE] — Ground truth joins the record; it does not live in it.** (strong-evidence)
[Gold labels](GLOSSARY.md#gold-labels) score outcomes. They never select, route, or tune
anything on held-out data — that is 04's boundary rule.
At the telemetry layer, that rule has a specific shape. A production routing or gate
decision is logged with only the fields that were actually observable at decision time:
the decision itself, a feature digest, the threshold, a risk score, plus a join
identifier. Never the outcome label. Ground truth is joined afterwards, in a separate
analysis layer. Written that way, the decision record can never become a path by which an
answer key reaches a model-facing surface (13's
[ground-truth isolation](GLOSSARY.md#ground-truth-isolation)).

## 5. Default procedure

### 5.1 Land the telemetry floor before the run, not after

The [telemetry floor](GLOSSARY.md#telemetry-floor) is the set of things that must already
be recording before you start anything long or expensive. It is a floor rather than a wish
list because of the asymmetry in §1: each row below costs almost nothing to write while
the run is happening, and cannot be obtained at any price once it is over.

| Event class | Minimum fields | Why it's on the floor |
|---|---|---|
| Run/phase lifecycle | Start and end events emitted automatically by the runner (never left to a manually invoked command); the end line written from a signal/exit handler so an interrupted run still leaves a record of where it stopped; planned vs. completed item counts | An unattended run has no other way to prove where it got to before it stopped |
| Per-invocation | Invocation ID, prompt/decode token counts, TTFT, finish reason, cap-hit/truncation flag, retry flag, error, artifact reference, runtime/engine digest | Feeds the performance autopsy (06) and the budget-calibration procedure (07); a missing finish reason makes truncation invisible after the fact |
| Tool/retrieval calls | Call start/end, tool identity, success flag, result reference | Otherwise tool time can only be inferred as leftover idle gaps between other spans — a poor substitute |
| Harness/orchestration spans | Sub-task start/end, critical-path flag, associated code-change identifiers as events | Without this, harness overhead and workload time are indistinguishable in cost-bucket attribution |
| Resource sampling | Periodic GPU/host utilization, memory, CPU on any run above a stated length threshold | Spot samples cannot support a utilization claim; only a timeseries can |
| Server/engine lifecycle | Start, model-load-start, loaded, stop — tagged with host and session identity | Ties every span back to the [frozen execution-system identity](GLOSSARY.md#frozen-identity) it ran under (02) |
| Dual clocks | Realtime *and* monotonic stamp on every span, plus periodic realtime-vs-monotonic offset samples | Virtualization and power-management clock skew stays invisible until something cross-checks the two (02, [SCENARIO: SCENARIO-12]) |
| Config snapshot | The full execution-system configuration captured per run, not referenced by pointer | A pointer to "current config" breaks the moment configuration changes; a snapshot survives it |
| Record timestamps | An explicit inserted-at stamp written by the application, not left to the database's own commit-time default | A long-open transaction can misdate a stored event relative to when it actually happened, corrupting sequence-dependent analysis |

**MUST**: server/engine logs append across restarts. A log that truncates on restart
silently destroys exactly the sessions a forensic reconstruction needs most (§9).
**SHOULD**: at Tier 1, the floor MAY be trimmed to run/phase, per-invocation, and
dual-clock rows only (§6); at Tier 2+ the full table is mandatory.

### 5.2 The minimum trajectory record

A [trajectory record](GLOSSARY.md#trajectory-record) is what you keep about one task
execution so that somebody can still understand it later. The test it has to pass is
whether a reader who was not there can replay the execution in their head from the record
alone. The list is long because that test is demanding.

Every task execution MUST produce a record carrying at least these fields. This is the
normative field set; a project MAY extend it, but MUST NOT ship fewer fields at Tier 2+
(§6).

| Field | Captures | Cross-reference |
|---|---|---|
| Task/trace ID | The identifier tying every span of one task execution together | — |
| Execution-system identity | Model/artifact/adapter, runtime/provider, hardware/host, harness, config digest | [execution system](GLOSSARY.md#execution-system) (02) |
| Artifact references | Content hashes for every artifact involved (weights, adapters, prompts, tool definitions) | 13 provenance |
| Prompt/context | What actually entered the model's context, not the template that generated it | 08 [context policy](GLOSSARY.md#context-policy) |
| Retrieval results | What was retrieved, from where, with what score/rank | 08 |
| Tool calls and results | Every call, its arguments, and its result (or failure) | 08 [tool contract](GLOSSARY.md#tool-contract) |
| Permissions in force | The permission/role set active at call time | 13 least-privilege |
| Output | The raw model/system output, before any downstream parsing | — |
| Component provenance | For each model-generated component in the record — each tier's attempt, the escalation tier's response, any judge verdict, any synthetic label — the generating model/provider identity and the terms class in force; MUST at Tier 2+ for any cascade or judge-mediated path, because training admissibility is decided per component (09 §5) and this field is what makes that decision executable | 09 §4–§5, 13 provenance |
| Verification outcome | The deterministic check or judge verdict applied to the output | 03, 04 |
| Final outcome | The task-level result after any cascade/escalation (08) resolved | 08 [rescue](GLOSSARY.md#rescue) |
| Latency | Per-phase and end-to-end, tagged to the authoritative clock declared for that metric | 06 |
| Token counts | Prompt, decode/output, reasoning (where distinguishable) | 06, 07 budget calibration |
| Cost | Computed from the pricing/amortization model in force at execution time | 11 |
| Clock stamps | Both realtime and monotonic, on the record and on its component spans | [dual-clock telemetry](GLOSSARY.md#dual-clock-telemetry) |
| Runtime/harness versions | Pinned identifiers, never "latest" | 02, 05 |
| Capability config | Generation/reasoning budget, sampling parameters, structured-output mode in force | 07 |
| Mutations | Any self-modifying or self-generated capability the system produced or invoked during the task | 13 governance |
| Human feedback | Any human annotation, correction, or approval attached to this execution | 10 human-approval gates |
| Deployment stage | offline / shadow / canary / production, at time of execution | 10 |

**[DEFAULT]** (heuristic) Large or sensitive payloads — raw prompts, full retrieved
documents, complete tool responses — SHOULD live in a separate, lower-cost store keyed by
reference from the record itself, rather than inline. That keeps the record cheap to query,
and it makes redaction (13) tractable field-by-field instead of payload-by-payload.

### 5.3 Data-plane separation

| Data plane | Typical content | Writes | Reads | Retention | Privacy class (illustrative) |
|---|---|---|---|---|---|
| Authoritative business data | Systems-of-record facts the task is about | The business system(s) of record | Retrieval layer (read-only), reporting | Governed by the business system, not this project | Set by data owner |
| Retrieval/knowledge | Indexed documents, embeddings, retrieval metadata | Ingestion pipeline | Retrieval layer, evaluators | Refresh-cycle bound; versioned like a suite (03) | Inherits source document's class |
| Working/task state | In-flight task state, scratch memory, intermediate results | The running task | The running task only | Short — cleared at task completion unless retained for debugging | Least durable, tightest access |
| Trajectory records | This chapter's minimum record (§5.2) | The harness/runner at execution time | Analytics, autopsy (06), harvesting (§5.6), audit (13) | Set by stakes tier + regulatory constraint (13) | Per-field classification (13 PII rules) |
| Learned/mutated assets | Adapters, routers, prompts, self-generated capabilities | Training/promotion pipeline (09, 08) | Serving layer, provenance registry (13) | Version-retained indefinitely (lineage) | Governed by license (13) + provenance |

Never let one plane's access rule stand in for another's. A read permission on retrieval
content says nothing at all about a read permission on trajectory PII.

### 5.4 Production observability baseline

**[ADAPT: NV-NIMOBSERVABILITY-001]** (verified live 2026-08-21; page last updated
2026-08-19). Three mechanics here are worth following as they are written.

- A Prometheus-compatible metrics endpoint that exposes the serving engine's own metric
  vocabulary unmodified rather than a reinterpreted one. The verified pattern passes the
  backend's native metrics straight through instead of rewriting them.
- OpenTelemetry tracing keyed to a W3C `traceparent` header, so a single request can be
  followed across every hop it makes.
- Structured logs, one JSON object per line.

What is missing, and why this is ADAPT rather than FOLLOW: the source documents no
experimentation minimum. It is a production-serving floor and nothing more. Supply the
experimentation floor yourself, from §5.1 and §5.2, and do not assume production
observability alone is sufficient before a long experimental run.

**SHOULD**: adopt one metric vocabulary across every serving tier — dev, shadow, canary,
production. Two dashboards that each define "requests per second" their own way cannot be
compared, and that is the same trap as comparing two performance-benchmark tools with
different metric definitions (06).

**[DEFAULT]** (heuristic) — the adapter rule. Treat every vendor-specific observability
integration as an adapter that feeds your own canonical trajectory schema (§5.2), never as
the schema itself. And when a vendor tool does not reliably expose a signal you need,
record that signal as explicitly *unavailable* rather than reverse-engineering undocumented
internals to fill the gap (§9).

**[ADAPT: NV-ATIF-001]** — if trajectories need to leave the local store, for cross-team
sharing or a multi-tool pipeline, a standard interchange format is worth adopting over a
bespoke export. What's missing: it is an interchange format across tools, not a canonical
local schema. Keep §5.2's table as the schema of record, and use the interchange format
only at the boundary where trajectories actually cross a tool or organizational boundary.

### 5.5 Telemetry-pipeline correctness

Who audits the instruments' instruments. Five checks:

1. **Cross-source consistency checks.** Compare the same fact from two independent sources
   on every run — realtime against monotonic clock offset, client-measured against
   server-reported token counts, an events stream against a preserved log — and alert when
   they diverge past a pre-registered tolerance.
2. **Synthetic-span injection.** Periodically push a known synthetic task through the full
   pipeline and verify that every expected field arrives with the expected shape. A
   synthetic span that goes missing is the pipeline's own reachability ceiling (03), turned
   inward on itself.
3. **Clock-skew probes.** Sample the realtime/monotonic offset on a cadence that is
   independent of any experiment, so skew is caught before it contaminates a comparison
   rather than after (02).
4. **Telemetry regression tests.** Run these checks inside the same integrity-gate
   machinery that protects the eval suite — [static integrity
   gates](GLOSSARY.md#static-integrity-gates) (03), full-pipeline rather than sampled,
   because they exist to catch exactly the defects a sampled check would miss.
5. **Version telemetry-pipeline changes like a suite release.** A schema or collection
   change gets a version, a changelog entry, and — at Tier 2+ — an explicit statement of
   which prior numbers it invalidates and which stay comparable.

**[STOP CONDITION]** A telemetry defect is discovered in already-published numbers: treat
it exactly like a discovered instrument defect in an eval suite (03). Halt reliance on the
affected numbers, do not quietly patch and continue, record the defect and the affected
range, and re-verify before the numbers are used in a decision again.

### 5.6 Production failure harvesting

Your production system is producing, for free and continuously, the one dataset your
evaluation suite does not have: real failures, on real inputs, drawn from the actual
population you serve. Every item in it is a case your current system demonstrably gets
wrong, and it arrived without anyone having to imagine it. No other feedback loop available
to you is worth as much per item.

[Failure harvesting](GLOSSARY.md#failure-harvesting) is what turns that stream into
improvements. The instinct on seeing a pile of real failures is to train on them, and the
entire discipline is in refusing to do that first.

1. **Hold out a stream of annotated production examples specifically for regression
   testing** — a named, mature pattern [EXT-OPS-002] — kept separate from the suites you
   use for capability claims ([regression suite vs. capability
   suite](GLOSSARY.md#regression-suite-vs-capability-suite), 03).
2. **Apply the project's privacy filter (13) before anything from production crosses into
   the lab's stores.** This **MUST** happen before harvesting, not as a later cleanup pass
   (13).
3. **Triage every harvested failure against the [canonical failure
   taxonomy](GLOSSARY.md#canonical-failure-taxonomy) (03).** Is it already representable in
   the current suite (an eval gap, RC-1)? Is it a retrieval or context gap (RC-3)? Or is it
   a candidate for training data (RC-10) — which it becomes only once the ladder's cheaper
   rungs are evidenced exhausted (07, 09)?
4. **Route in ladder order**, per the principle above: eval-suite candidate first, then
   retrieval/context fix, only then training-data candidate. And a harvested record becomes
   a training-data candidate only after component-level provenance qualification (09 §5).
   A trajectory that embeds a managed-provider output — an escalation tier's response, a
   provider-generated label — is not training-admissible just because you own the record it
   sits in.
5. **Feed routed items into the relevant chapter's intake** — 03 for suite refresh, 09 for
   training data — with the trajectory record (§5.2) attached as provenance.

### 5.7 Drift and monitoring of automated/learned components

*status: doctrine — not yet exercised (see below for what validation would look like)*

This is where the third position from §1 is either renewed or revoked. A component running
unattended is doing so on evidence that was collected once, and the four monitors below
exist to notice when that evidence has quietly stopped describing reality.

| Monitor | What it catches | Pre-registered response |
|---|---|---|
| Input distribution vs. eval distribution | The served population has drifted from the population the [learned router](GLOSSARY.md#learned-router)/component was measured on | RECALIBRATE (re-run the [leakage audit](GLOSSARY.md#leakage-audit)/graduation gate) or ABORT to observe-only |
| Escalation/routing rate | A [cascade](GLOSSARY.md#cascade)'s escalation share has moved materially off its measured baseline | Re-derive the [break-even](GLOSSARY.md#break-even) (08, 11); investigate before assuming cost or quality moved |
| Verifier-pass rate | The verifier itself may be drifting, not only the traffic — P2 (03) applied post-deployment | Treat as a possible instrument defect (RC-1) first, per 03 |
| Per-stratum outcome rates | Aggregate health can hide a stratum silently failing | Stratum-level alert threshold, never aggregate-only |

Every threshold above is a
[consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance) (04):
pre-registered, with a named ABORT / RECALIBRATE / PROCEED-WITH-DECLARED-CEILING response
attached before any data arrives. It is not a number on a dashboard that somebody is
trusted to notice.

The graduation-reversal condition — de-automation — is the same tolerance read backwards.
When it fires, the component reverts to observe-only automatically. Not when someone
remembers to intervene.

Validation status: this playbook has no internal execution record of a component running
long enough past graduation to exercise a drift trigger. What would validate this design: a
graduated component instrumented per the table above, run past at least one pre-registered
threshold (or one full recalibration cycle), with the response executed and recorded as
evidence.

### 5.8 Periodic methodology audit

**[FOLLOW: EXT-OPS-002]** — a rubric-based self-audit, scored as the *minimum* across
categories rather than the average. This is a mature, external, consensus practice, and the
scoring choice is the point of it: a system's overall test-and-monitoring maturity is only
as good as its weakest category, and an average would let three strong categories conceal
one absent one.

Run it annually or at every major release. At Tier 3, run it before every high-consequence
promotion (10). Score categories SHOULD mirror this chapter's structure: telemetry-floor
completeness, data-plane hygiene, production-observability coverage, telemetry-pipeline
correctness, failure-harvesting throughput, and drift-monitoring coverage of automated
components.

### 5.9 Closing the loop back to chapter 03

The [look ledger](GLOSSARY.md#look-ledger)'s refresh trigger (03, 04) and §5.6's harvesting
output are the same loop seen from its two ends. Production evidence becomes suite-refresh
input; the refreshed suite becomes new held-out evidence; the refreshed suite ships and
starts generating new production evidence.

This is the second structural rule of the default lifecycle (00 §5): the loop closes back
into evaluation, in ladder order, before it closes into training.

## 6. Project adaptation parameters

| Tier | Adds beyond the never-skippable floor (00 §6), here |
|---|---|
| **1 — Exploratory** | Land run-lifecycle, per-invocation, and dual-clock telemetry (§5.1) even for smoke-scale runs; the trajectory record MAY omit human-feedback/deployment-stage fields not yet applicable; no drift monitoring required (nothing is automated yet) |
| **2 — Consequential** (default) | Full §5.1 floor + full §5.2 trajectory record; data-plane separation (§5.3) enforced; production observability baseline (§5.4) at first deployment; failure harvesting (§5.6) active; drift monitoring (§5.7) mandatory for any graduated component |
| **3 — High-stakes/regulated** | All of Tier 2, plus: telemetry-pipeline correctness checks (§5.5) run as static integrity gates rather than spot checks; periodic methodology audit (§5.8) before every high-consequence promotion; trajectory records feed the tamper-evident [record of record](GLOSSARY.md#record-of-record) (13); privacy filtering (13) audited, not merely applied |

**[PARAMETER]** items. State the value *and* the reasoning that calibrated it wherever it
is set. Never ship a bare number.

- **Resource-sampler interval** — calibrate against run length and the granularity the
  autopsy will need. A run measured in minutes needs a tighter interval than one measured
  in days.
- **Retention window per data plane** — calibrate against the project's regulatory and
  residency constraints (01) and the clean-room boundary (13). Never default to
  "indefinite" without a stated reason.
- **Telemetry-completeness threshold** (§8) — calibrate against how much missing telemetry
  the downstream autopsy or decision can actually tolerate. State it as a
  consequence-bearing tolerance, not a vague aspiration.
- **Drift-monitoring thresholds** (§5.7) — calibrate against the component's blast radius
  and the stakes tier of the decisions it affects. A routing layer feeding a Tier-3
  decision needs a tighter trigger than a Tier-1 exploratory one.
- **Failure-harvesting sample rate** (§5.6) — calibrate against production volume and the
  stratification needs of the suite it feeds (03).
- **Methodology-audit cadence** (§5.8) — calibrate against release cadence and stakes tier.
  Annual is the floor; per-major-release or per-high-consequence-promotion at Tier 3.

## 7. Decision gates and stopping conditions

**[DECISION GATE] Telemetry-floor gate.** Before authorizing a long or expensive run,
verify that §5.1's floor is landed — spot-check it with the completeness metric (§8). If it
is not landed, you have two honest options: land it first, or run the work as a
[diagnostic run kind](GLOSSARY.md#diagnostic-run-kind) (04), ledgered and non-promotable,
rather than as a run whose results you intend to act on.

**[STOP CONDITION] Telemetry defect discovered post-hoc.** (§5.5) Halt use of the affected
published numbers. Do not patch silently. Version the fix, and re-verify before any of
those numbers is reused in a decision.

**[DECISION GATE] Automation graduation reversal.** (§5.7) A pre-registered drift trigger
fires, and the component reverts to observe-only automatically. Continuing to run it
unattended past a fired trigger is the anti-pattern this gate exists to prevent (§9).

**[STOP CONDITION] Harvested-failure backlog past its triage SLA.** (§5.6) An unclassified
backlog older than a pre-registered age threshold blocks new automation promotions for the
affected surface until it is triaged. An un-audited failure stream is not evidence that
nothing is wrong; it is an absence of evidence either way.

**[DECISION GATE] Periodic audit below threshold.** (§5.8) A methodology self-audit score
below the pre-registered minimum blocks the next Tier-3 promotion (10) until remediated.

## 8. Metrics and formulas

**Telemetry completeness.** How much of the floor is actually arriving.

```
Completeness = F_pop / F_req
```

where `F_pop` is the count of required fields actually populated in a sampled record (or
run), and `F_req` is the count of fields the project's frozen telemetry-floor definition
(§5.1, §5.2) requires. Expressed as a percentage.

*Worked example (illustrative).* A project defines a 20-field required floor. A spot-check
of a smoke run finds 18 populated — two are silently null because of a harness defect.
Completeness = 18/20 = 90%. The floor requires 100% on required fields before a run is
trusted for its intended decision, so 90% triggers RECALIBRATE: fix the harness before
authorizing the long run this floor exists to explain. That is the same ABORT /
RECALIBRATE / PROCEED-WITH-DECLARED-CEILING vocabulary as any other
[consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance) (04).

**Drift statistics — reference only.** No formula is prescribed here. Detecting population
shift — comparing a monitored feature's production-time distribution against its
measured-time distribution — is a standard statistical problem with several admissible
standard tools, such as a distributional-distance statistic chosen to match the feature's
type. *status: doctrine — not yet exercised* — this playbook has no internal execution
record for any specific choice. Pick one appropriate to the feature type, and pre-register
its threshold as a consequence-bearing tolerance (§5.7).

Clock-skew measurement and the MDE / effective-N machinery are defined in chapters 02 and
04 respectively. This chapter consumes them and does not redefine them.

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition stated per item)

- **The dashboard as record of record** (condition: whenever a trace-visualization or
  metrics UI is treated as the sole store of trajectories or evaluation results). A
  dashboard MAY mirror the record. It never replaces it (13).
- **Success-gated trajectory storage** (condition: whenever raw or failure-path output is
  persisted only after successful parsing). The population you most need to study is the
  failures, and that is exactly the population a success-gated store drops.
- **Truncating logs across restarts** (condition: whenever a long-running process's logs
  reset instead of append on restart). Forensic reconstruction depends on precisely the
  sessions this destroys first.
- **Retrofitting telemetry during the postmortem** (condition: always). Forensics cannot be
  reconstructed from data that was never captured. "We'll add it during the writeup" is a
  decision not to have the data.
- **Activity telemetry substituting for outcome telemetry** (condition: whenever token
  counts, tool-call counts, or self-reported completion stand in for a verified outcome).
  These are diagnostic signals and they are trivially inflated, so optimizing them directly
  is a textbook Goodhart failure. Keep activity and verified-outcome telemetry in separate
  columns, never blended into one score.
- **Ground truth inline in the decision record** (condition: whenever a production routing
  or gate log stores the outcome label at write time instead of joining it afterwards).
  This is exactly the leakage surface that
  [ground-truth isolation](GLOSSARY.md#ground-truth-isolation) (13) and the gold-label
  boundary (04) exist to prevent, reintroduced one layer down.
- **Automation running past a fired drift trigger** (condition: whenever a pre-registered
  monitoring threshold has fired and the component has not reverted to observe-only).
  [Observe-only graduation](GLOSSARY.md#observe-only-graduation) (08) is conditional;
  treating it as a one-time achievement is the failure mode §5.7 exists to close.
- **Undocumented internals scraped to fill a vendor gap** (condition: whenever a vendor
  tool does not reliably expose a needed signal and the response is reverse-engineering
  rather than declaring it unavailable). An undocumented internal can change without notice
  and silently break the pipeline it was patched into. Record the gap instead (§5.4's
  adapter rule).

## 10. Vendor recipes

The structural finding of this playbook (00 §10) shows up here in its sharpest form.
Production observability is vendor-mature. The experimentation floor and the
drift-monitoring layer are not, and this chapter supplies both.

**[ADAPT: NV-NIMOBSERVABILITY-001]** — production observability mechanics (§5.4): metrics
endpoint, distributed tracing, structured logs. Verified live 2026-08-21 (page last updated
2026-08-19). ADAPT because the source states no experimentation minimum; the decision layer
this playbook adds is exactly §5.1 and §5.2.

**[REFERENCE: NV-DATAFLYWHEEL-001]** — deprecated April 2026, with no successor named as of
verification (2026-08-21). Do not adopt the artifact. The *shape* of the loop it
demonstrated remains a usable design reference for §5.6 and §5.8: log production examples,
stratify them, run a comparison across baseline and adapted candidates, score that
comparison with a judge, and gate promotion on a human. Its own README described it as
"flashlight, not autopilot", which is the right posture.
The trap worth carrying away: the source's own deprecation notice was not consistently
reflected in the vendor's other documentation, which kept cross-linking and promoting it
after the notice went up. Verify a source's deprecation status at the source, rather than
letting inbound links imply currency.

**[FOLLOW: EXT-OPS-002]** — the self-audit rubric (§5.8): mature, consensus, verified
2026-08-21. Min-across-categories scoring, and its production-failure-harvesting pattern
underwrites §5.6.

**[ADAPT: NV-ATIF-001]** — trajectory interchange format (§5.4), current and active as of
2026-08-21. Adopt at interchange boundaries only. It is not a substitute for the canonical
schema in §5.2.

## 11. Worked examples

- [SCENARIO-05](examples/SCENARIO-05_hardware-purchase-discipline.md) — an invented case in
  which telemetry preserved while a long evaluation round was running is what later lets a
  performance autopsy (06) reconstruct where the hours went and run the counterfactual that
  refutes an intuitive hardware purchase. None of that reconstruction is available unless
  §5.1's floor was already landed when the round happened.
- [SCENARIO-12](examples/SCENARIO-12_restart-instability-paired-controls.md) — an invented
  case in which dual-clock stamps surface a systematic clock-skew artifact that had been
  silently biasing every published latency. The fix follows directly from having captured
  both clocks, not from anyone suspecting the skew in advance.
- *Illustrative* — the completeness calculation in §8 (a 20-field floor, 18 populated, 90%
  completeness, RECALIBRATE before the long run it exists to explain).

## 12. Outputs and artifacts

- A landed telemetry floor (§5.1), verified via the completeness check (§8), before the
  next long or expensive run.
- An instantiated trajectory-record schema (§5.2) — the store or log format the project
  actually writes.
- A data-plane separation map (§5.3), feeding chapter 13's privacy classification.
- A deployed production observability baseline (§5.4) — metrics endpoint, tracing,
  structured logs.
- A versioned telemetry-pipeline correctness test suite (§5.5), run alongside the eval
  suite's integrity gates.
- A failure-harvesting backlog with ladder-order triage (§5.6), feeding 03 and 09.
- A drift-monitoring plan with pre-registered consequence-bearing tolerances (§5.7) for
  every graduated automated or learned component.
- A periodic methodology audit record (§5.8), feeding CHANGELOG.md and any
  [method decision records](GLOSSARY.md#method-decision-record) it triggers.

## 13. Sources

| ID | Role here |
|---|---|
| [NV-NIMOBSERVABILITY-001] | Production observability mechanics (metrics/tracing/logs); ADAPT — no experimentation minimum stated |
| [EXT-OPS-002] | Min-across-categories self-audit rubric; production-failure-harvesting pattern |
| [NV-DATAFLYWHEEL-001] | Deprecated harvesting-loop design, cited as a design reference with an explicit deprecation trap |
| [NV-ATIF-001] | Trajectory interchange format, for cross-boundary trajectory sharing only |

Gap dispositions in this chapter:

**G5 (post-deployment drift monitoring of learned/routed components):
COVERED-AS-DOCTRINE-NOT-YET-EXERCISED** (§4, §5.7, §7). The monitoring design and its
consequence-bearing thresholds are stated in full. No internal execution record exists for
a component running past a fired trigger, and that is marked explicitly wherever it
matters.

**G12 (telemetry-pipeline correctness): COVERED** (§5.5 procedure, §7 stop condition, §9
anti-pattern). The cross-source consistency checking and multi-source forensic
reconstruction behind it come from one project's practice, whose records are not published
here; [SCENARIO: SCENARIO-05] and [SCENARIO: SCENARIO-12] are invented illustrations of
the same reasoning rather than the evidence for it.

---

> [← Previous](11_ECONOMICS_HARDWARE_AND_CLOUD.md) · [Index](README.md) · [Next →](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md)
