# 12. Observability, Learning, and Promotion

> Part of the **Adaptive AI Systems Playbook** v0.1.0 ·
> [← Previous](11_ECONOMICS_HARDWARE_AND_CLOUD.md) · [Index](README.md) · [Next →](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md)
> **Reading time:** ~20 min. **Prerequisites:** [02](02_EXECUTION_SYSTEM_MODEL.md), [03](03_EVALUATION_FOUNDATION.md), [04](04_EXPERIMENT_DESIGN_AND_STATISTICS.md), [06](06_INFERENCE_PERFORMANCE_AND_CAPACITY.md), [08](08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md).

## 1. Purpose and when to read this

Vendors document one half of this chapter well and leave the other half almost entirely to the reader. Production observability — metrics, tracing, structured logs for a deployed serving stack — is a mature, published discipline. The *experimentation* telemetry that every earlier chapter quietly depends on — the [performance autopsy](GLOSSARY.md#performance-autopsy) (06), the [look ledger](GLOSSARY.md#look-ledger) (04), the [reproducibility-boundary](GLOSSARY.md#reproducibility-boundary) probes (02) — is not documented anywhere a vendor ships it. This chapter supplies the missing minimum: what to instrument before a long or expensive run, the durable record every task execution must leave behind, the discipline that keeps a growing telemetry pipeline honest about its own correctness, and the loop that carries production evidence back into the lab.

"Promotion" in this chapter's title is narrower than chapter 10's promotion pipeline (offline → shadow → canary → rollout), which promotes a *system*. This chapter is about what happens after a learned or automated *component* has already cleared [observe-only graduation](GLOSSARY.md#observe-only-graduation) (08) — the ongoing evidence that keeps that graduation valid, and the trigger that pulls it back when it stops being valid.

Read this chapter:

- Before authorizing any run whose telemetry you would regret not having — a multi-hour experiment, a milestone-defining comparison, anything a future performance autopsy will need to explain.
- When standing up production observability for the first time (§5.4, §10).
- When a learned/routed/automated component has graduated past observe-only (08) and needs an ongoing monitoring plan (§5.7, §7).
- When closing the loop from production failures back into the evaluation suite (03) or training data (09).

## 2. Inputs required

- The project's frozen [execution system](GLOSSARY.md#execution-system) identity (02) — telemetry unscoped to it is not comparable to anything.
- The [rigor dial](GLOSSARY.md#rigor-dial) / [stakes tier](GLOSSARY.md#stakes-tier) from the [project profile](GLOSSARY.md#project-profile) (00 §6, 01) — it sets how much of this chapter's artifact set is mandatory (§6).
- Any existing experiment contract (04) whose runs this telemetry needs to explain.
- The deployment-stage inventory from chapter 10 (offline / shadow / canary / production) — the trajectory record's deployment-stage field depends on it.
- Privacy/residency constraints from the project profile (01) and the [clean-room boundary](GLOSSARY.md#clean-room-boundary) (13) — they gate what the telemetry floor is allowed to capture at all.

## 3. Decisions this chapter supports

- What MUST be instrumented before a long or expensive run is authorized.
- What minimum record a single task execution must leave behind, and where its fields come from.
- How to separate data planes so retention, privacy, and promotion rules attach to the right bucket.
- What production observability baseline to adopt at deployment, and what it does *not* give you.
- Whether the telemetry pipeline itself is trustworthy — who checks the checker.
- In what order a production failure re-enters the lab.
- Whether an automated/learned component keeps its license to run unattended, or a de-automation trigger has fired.
- When a periodic methodology self-audit is due.

## 4. Normative principles

**[PRINCIPLE] — Telemetry precedes spend.** (case-study + inference)
The instrumentation decision has to be made *before* the run it will need to explain, because a [performance autopsy](GLOSSARY.md#performance-autopsy) cannot be retrofitted: once a session ends, its per-invocation timings, finish reasons, and server lifecycle are either captured or gone forever. A completed run that never emitted them produces a bill with no receipt — every hour it spent is real, but nothing downstream can attribute it, defend it, or learn from it. Preserved per-invocation telemetry (finish reasons, dual clocks, session identity) is what let a later counterfactual-costing analysis attribute a cost bucket and refute an intuitive hardware purchase after the fact [CASE: CASE-005]; a dual-clock stamp on every span is what surfaced a systematic clock-skew artifact that would otherwise have silently biased every published latency in the project [CASE: CASE-012]. Land the floor (§5.1) before authorizing the run, not during its postmortem.

**[PRINCIPLE] — Every span carries two clocks and a declared authority.** (strong-evidence)
Chapter 02 establishes [dual-clock telemetry](GLOSSARY.md#dual-clock-telemetry) and the [authoritative clock](GLOSSARY.md#authoritative-clock) declaration as measurement-validity requirements; this chapter restates them as an *instrumentation* requirement, because they are only useful if captured at write time — they cannot be reconstructed at read time. Virtualized and power-managed hosts (containers, VMs, WSL2-class layers) can silently skew a monotonic clock against realtime; the skew is invisible until something cross-checks the two, and nothing can cross-check a clock that was only sampled once [CASE: CASE-012].

**[PRINCIPLE] — A measurement pipeline nobody audits is a pipeline nobody should trust.** (strong-evidence)
The discipline that tests code has to apply to the code that measures it: cross-source consistency checks, injected synthetic events with a known expected shape, and regression tests over the telemetry pipeline itself. The generic analog is well established outside this playbook — a mature production-ML test rubric scores whether training-time and serving-time computation agree, among its minimum tests, and takes the *minimum* across categories as the overall score rather than an average that lets one weak leg hide behind three strong ones [EXT-OPS-002]. A telemetry defect discovered after publication invalidates every number computed through it while it was broken; treat a telemetry-pipeline change exactly like a [suite release](GLOSSARY.md#suite-release) — versioned, with a stated cutover, never a silent in-place patch (03's [criteria-drift](GLOSSARY.md#criteria-drift) discipline, applied to the instrument rather than the eval).

**[DEFAULT] — Separate data planes by who writes, who reads, and what governs retention.** (heuristic)
A project accumulates at least five distinct kinds of state that are tempting to store together and dangerous to: authoritative business data, retrieval/knowledge content, working/task state, trajectory records (this chapter), and learned/mutated assets. They differ in who may write them, who may read them, how long they may be retained, and what privacy class governs them (13). Collapsing them into one undifferentiated store means one retention policy, one access rule, and one privacy classification silently governs all five — usually the least restrictive one, which is exactly backwards. §5.3 gives the separation table.

**[PRINCIPLE] — Failures re-enter the lab in ladder order, never straight to training.** (consensus)
A production failure is evidence, and evidence is triaged the same way the [intervention ladder](GLOSSARY.md#intervention-ladder) (07) triages any measured gap: first as an evaluation candidate (does the suite already know about this failure mode?), then — in ladder order — as a retrieval/context fix, and only later as training data. Holding out annotated production examples for regression testing is a named, mature practice [EXT-OPS-002]; routing a failure straight to a fine-tuning run skips every cheaper rung the ladder requires evidence to skip.

**[DEFAULT] — An automated component's license to run unattended is conditional, not permanent.** (case-study + inference)
[Observe-only graduation](GLOSSARY.md#observe-only-graduation) (08) is a staged *entry* condition; passing it once guarantees nothing about whether the input distribution, escalation rate, or verifier-pass rate stays where it was measured. The same leakage-audit and shadow-period discipline that earns automated action has to keep being paid for as long as the component keeps acting — as a pre-registered monitoring plan carrying [consequence-bearing tolerances](GLOSSARY.md#consequence-bearing-tolerance) that can pull the component back to observe-only. §5.7 gives the monitoring table.
*status: doctrine — not yet exercised (see §5.7 for what validation would look like)*

**[PRINCIPLE] — Ground truth joins the record; it does not live in it.** (strong-evidence)
[Gold labels](GLOSSARY.md#gold-labels) score outcomes; they never select, route, or tune anything on held-out data (04's boundary rule). At the telemetry layer this means a production routing or gate decision is logged with only the fields actually observable at decision time — the decision, the feature digest, the threshold, a risk score — plus a join identifier, never the outcome label itself. Ground truth is joined afterward, in a separate analysis layer, so the decision record can never become a path by which an answer key reaches a model-facing surface (13's [ground-truth isolation](GLOSSARY.md#ground-truth-isolation)).

## 5. Default procedure

### 5.1 Land the telemetry floor before the run, not after

| Event class | Minimum fields | Why it's on the floor |
|---|---|---|
| Run/phase lifecycle | Start and end events emitted automatically by the runner (never left to a manually invoked command); the end line written from a signal/exit handler so an interrupted run still leaves a record of where it stopped; planned vs. completed item counts | An unattended run has no other way to prove where it got to before it stopped |
| Per-invocation | Invocation ID, prompt/decode token counts, TTFT, finish reason, cap-hit/truncation flag, retry flag, error, artifact reference, runtime/engine digest | Feeds the performance autopsy (06) and the budget-calibration procedure (07); a missing finish reason makes truncation invisible after the fact |
| Tool/retrieval calls | Call start/end, tool identity, success flag, result reference | Tool time is otherwise only inferable as leftover idle time between other spans — a poor substitute |
| Harness/orchestration spans | Sub-task start/end, critical-path flag, associated code-change identifiers as events | Without this, harness overhead and workload time are indistinguishable in cost-bucket attribution |
| Resource sampling | Periodic GPU/host utilization, memory, CPU on any run above a stated length threshold | Spot samples cannot support a utilization claim; only a timeseries can |
| Server/engine lifecycle | Start, model-load-start, loaded, stop — tagged with host and session identity | Ties every span back to the [frozen execution-system identity](GLOSSARY.md#frozen-identity) it ran under (02) |
| Dual clocks | Realtime *and* monotonic stamp on every span, plus periodic realtime-vs-monotonic offset samples | Virtualization/power-management clock skew is invisible until cross-checked (02, [CASE: CASE-012]) |
| Config snapshot | The full execution-system configuration captured per run, not referenced by pointer | A pointer to "current config" breaks the moment configuration changes; a snapshot survives it |
| Record timestamps | An explicit inserted-at stamp written by the application, not left to the database's own commit-time default | A long-open transaction can misdate a stored event relative to when it actually happened, corrupting sequence-dependent analysis |

**MUST**: server/engine logs append across restarts; a log that truncates on restart silently destroys exactly the sessions a forensic reconstruction needs most (§9). **SHOULD**: at Tier 1, the floor MAY be trimmed to run/phase, per-invocation, and dual-clock rows only (§6); at Tier 2+ the full table is mandatory.

### 5.2 The minimum trajectory record

Every task execution MUST produce a record carrying at least these fields. This is the normative field set for the [trajectory record](GLOSSARY.md#trajectory-record); a project MAY extend it, but MUST NOT ship fewer fields at Tier 2+ (§6).

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

**[DEFAULT]** (heuristic) Large or sensitive payloads — raw prompts, full retrieved documents, complete tool responses — SHOULD live in a separate, lower-cost store keyed by reference from the record itself, rather than inline. This keeps the record cheap to query and makes redaction (13) tractable field-by-field instead of payload-by-payload.

### 5.3 Data-plane separation

| Data plane | Typical content | Writes | Reads | Retention | Privacy class (illustrative) |
|---|---|---|---|---|---|
| Authoritative business data | Systems-of-record facts the task is about | The business system(s) of record | Retrieval layer (read-only), reporting | Governed by the business system, not this project | Set by data owner |
| Retrieval/knowledge | Indexed documents, embeddings, retrieval metadata | Ingestion pipeline | Retrieval layer, evaluators | Refresh-cycle bound; versioned like a suite (03) | Inherits source document's class |
| Working/task state | In-flight task state, scratch memory, intermediate results | The running task | The running task only | Short — cleared at task completion unless retained for debugging | Least durable, tightest access |
| Trajectory records | This chapter's minimum record (§5.2) | The harness/runner at execution time | Analytics, autopsy (06), harvesting (§5.6), audit (13) | Set by stakes tier + regulatory constraint (13) | Per-field classification (13 PII rules) |
| Learned/mutated assets | Adapters, routers, prompts, self-generated capabilities | Training/promotion pipeline (09, 08) | Serving layer, provenance registry (13) | Version-retained indefinitely (lineage) | Governed by license (13) + provenance |

Never let one plane's access rule stand in for another's: a read permission on retrieval content says nothing about a read permission on trajectory PII.

### 5.4 Production observability baseline

**[ADAPT: NV-NIMOBSERVABILITY-001]** (verified live 2026-08-21; page last updated 2026-08-19). Mechanics worth following as-is: a Prometheus-compatible metrics endpoint exposing the serving engine's own metric vocabulary unmodified rather than a reinterpreted one (the verified pattern passes through the backend's native metrics rather than rewriting them); OpenTelemetry tracing keyed to a W3C `traceparent` header so one request correlates across every hop; structured, one-JSON-object-per-line logs. What's missing, and why this is ADAPT rather than FOLLOW: the source documents no experimentation minimum — it is a production-serving floor only. Supply the experimentation floor yourself from §5.1/§5.2; do not assume production observability alone is sufficient before a long experimental run. **SHOULD**: adopt one metric vocabulary across every serving tier (dev, shadow, canary, production) — comparing dashboards that define "requests per second" differently is the same trap as comparing performance-benchmark tools with different metric definitions (06).

**[DEFAULT]** (heuristic) — the adapter rule: treat every vendor-specific observability integration as an adapter feeding your own canonical trajectory schema (§5.2), never as the schema itself. If a vendor tool doesn't reliably expose a signal you need, record that signal as explicitly *unavailable* rather than reverse-engineering undocumented internals to fill the gap (§9).

**[ADAPT: NV-ATIF-001]** — if trajectories need to leave the local store (cross-team sharing, multi-tool pipelines), a standard interchange format is worth adopting over a bespoke export. What's missing: it is an interchange format across tools, not a canonical local schema — keep §5.2's table as the schema of record, and use the interchange format only at the boundary where trajectories actually cross a tool or organizational boundary.

### 5.5 Telemetry-pipeline correctness

Who audits the instruments' instruments:

1. **Cross-source consistency checks**: compare the same fact from two independent sources on every run — realtime vs. monotonic clock offset, client-measured vs. server-reported token counts, an events stream vs. a preserved log — and alert on divergence beyond a pre-registered tolerance.
2. **Synthetic-span injection**: periodically run a known synthetic task through the full pipeline and verify every expected field arrives with the expected shape; a synthetic span that goes missing is the pipeline's own reachability ceiling (03) turned inward on itself.
3. **Clock-skew probes**: sample the realtime/monotonic offset on a cadence independent of any experiment, so skew is caught before it contaminates a comparison, not after (02).
4. **Telemetry regression tests**: run these checks inside the same integrity-gate machinery that protects the eval suite — [static integrity gates](GLOSSARY.md#static-integrity-gates) (03), full-pipeline rather than sampled, because they exist to catch exactly the defects a sampled check would miss.
5. **Version telemetry-pipeline changes like a suite release**: a schema or collection change gets a version, a changelog entry, and — at Tier 2+ — an explicit statement of which prior numbers it invalidates and which stay comparable.

**[STOP CONDITION]** A telemetry defect is discovered in already-published numbers: treat it exactly like a discovered instrument defect in an eval suite (03). Halt reliance on the affected numbers, do not quietly patch and continue, record the defect and the affected range, and re-verify before the numbers are used in a decision again.

### 5.6 Production failure harvesting

1. Hold out a stream of annotated production examples specifically for regression testing — a named, mature pattern [EXT-OPS-002] — kept separate from the suites used for capability claims ([regression suite vs. capability suite](GLOSSARY.md#regression-suite-vs-capability-suite), 03).
2. Apply the project's privacy filter (13) before anything from production crosses into the lab's stores. **MUST** happen before harvesting, not as a later cleanup pass (13).
3. Triage every harvested failure against the [canonical failure taxonomy](GLOSSARY.md#canonical-failure-taxonomy) (03): is it already representable in the current suite (an eval gap, RC-1), a retrieval/context gap (RC-3), or a candidate for training data (RC-10) only after the ladder's cheaper rungs are evidenced exhausted (07, 09)?
4. Route in ladder order (the Principle above): eval-suite candidate first, then retrieval/context fix, only then training-data candidate.
5. Feed routed items into the relevant chapter's intake (03 for suite refresh, 09 for training data) with the trajectory record (§5.2) attached as provenance.

### 5.7 Drift and monitoring of automated/learned components

*status: doctrine — not yet exercised (see below for what validation would look like)*

| Monitor | What it catches | Pre-registered response |
|---|---|---|
| Input distribution vs. eval distribution | The served population has drifted from the population the [learned router](GLOSSARY.md#learned-router)/component was measured on | RECALIBRATE (re-run the [leakage audit](GLOSSARY.md#leakage-audit)/graduation gate) or ABORT to observe-only |
| Escalation/routing rate | A [cascade](GLOSSARY.md#cascade)'s escalation share has moved materially off its measured baseline | Re-derive the [break-even](GLOSSARY.md#break-even) (08, 11); investigate before assuming cost or quality moved |
| Verifier-pass rate | The verifier itself may be drifting, not only the traffic — P2 (03) applied post-deployment | Treat as a possible instrument defect (RC-1) first, per 03 |
| Per-stratum outcome rates | Aggregate health can hide a stratum silently failing | Stratum-level alert threshold, never aggregate-only |

Each threshold above is a [consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance) (04): pre-registered, with a named ABORT/RECALIBRATE/PROCEED-WITH-DECLARED-CEILING response, not a dashboard number someone is trusted to notice. The graduation-reversal (de-automation) condition is the same tolerance read backwards: when it fires, the component reverts to observe-only automatically, not by someone remembering to intervene.

Validation status: this playbook has no internal execution record of a component running long enough past graduation to exercise a drift trigger. What would validate this design: a graduated component instrumented per the table above, run past at least one pre-registered threshold (or one full recalibration cycle), with the response executed and recorded as evidence.

### 5.8 Periodic methodology audit

**[FOLLOW: EXT-OPS-002]** — a rubric-based self-audit scored as the *minimum* across categories, not an average: a mature, external, consensus practice (a system's overall test-and-monitoring maturity is only as good as its weakest category). Run it annually or at every major release; at Tier 3, run it before every high-consequence promotion (10). Score categories SHOULD mirror this chapter's structure: telemetry-floor completeness, data-plane hygiene, production-observability coverage, telemetry-pipeline correctness, failure-harvesting throughput, and drift-monitoring coverage of automated components.

### 5.9 Closing the loop back to chapter 03

The [look ledger](GLOSSARY.md#look-ledger)'s refresh trigger (03, 04) and §5.6's harvesting output are the same loop viewed from two ends: production evidence becomes suite-refresh input, becomes new held-out evidence, becomes new production evidence once the refreshed suite ships. This is the second structural rule of the default lifecycle (00 §5): the loop closes, in ladder order, back into evaluation before it closes into training.

## 6. Project adaptation parameters

| Tier | Adds beyond the never-skippable floor (00 §6), here |
|---|---|
| **1 — Exploratory** | Land run-lifecycle, per-invocation, and dual-clock telemetry (§5.1) even for smoke-scale runs; the trajectory record MAY omit human-feedback/deployment-stage fields not yet applicable; no drift monitoring required (nothing is automated yet) |
| **2 — Consequential** (default) | Full §5.1 floor + full §5.2 trajectory record; data-plane separation (§5.3) enforced; production observability baseline (§5.4) at first deployment; failure harvesting (§5.6) active; drift monitoring (§5.7) mandatory for any graduated component |
| **3 — High-stakes/regulated** | All of Tier 2, plus: telemetry-pipeline correctness checks (§5.5) run as static integrity gates rather than spot checks; periodic methodology audit (§5.8) before every high-consequence promotion; trajectory records feed the tamper-evident [record of record](GLOSSARY.md#record-of-record) (13); privacy filtering (13) audited, not merely applied |

**[PARAMETER]** items — state the value and its calibration reasoning wherever it is set, never ship a bare number:

- **Resource-sampler interval** — calibrate against run length and the granularity the autopsy will need; a run measured in minutes needs a tighter interval than one measured in days.
- **Retention window per data plane** — calibrate against the project's regulatory/residency constraints (01) and the clean-room boundary (13); never default to "indefinite" without a stated reason.
- **Telemetry-completeness threshold** (§8) — calibrate against how much missing telemetry the downstream autopsy or decision can tolerate; state it as a consequence-bearing tolerance, not a vague aspiration.
- **Drift-monitoring thresholds** (§5.7) — calibrate against the component's blast radius and the stakes tier of the decisions it affects; a routing layer feeding a Tier-3 decision needs a tighter trigger than a Tier-1 exploratory one.
- **Failure-harvesting sample rate** (§5.6) — calibrate against production volume and the stratification needs of the suite it feeds (03).
- **Methodology-audit cadence** (§5.8) — calibrate against release cadence and stakes tier; annual is the floor, per-major-release or per-high-consequence-promotion at Tier 3.

## 7. Decision gates and stopping conditions

**[DECISION GATE] Telemetry-floor gate.** Before authorizing a long/expensive run: verify §5.1's floor is landed (spot-check via the completeness metric, §8). If it is not, either land it first, or run the work as a [diagnostic run kind](GLOSSARY.md#diagnostic-run-kind) (04) — ledgered, non-promotable — rather than as a run whose results you intend to act on.

**[STOP CONDITION] Telemetry defect discovered post-hoc.** (§5.5) Halt use of the affected published numbers; do not patch silently; version the fix; re-verify before reuse in a decision.

**[DECISION GATE] Automation graduation reversal.** (§5.7) A pre-registered drift trigger fires → the component reverts to observe-only automatically. Continuing to run it unattended past a fired trigger is the anti-pattern this gate exists to prevent (§9).

**[STOP CONDITION] Harvested-failure backlog past its triage SLA.** (§5.6) An unclassified backlog past a pre-registered age threshold blocks new automation promotions for the affected surface until triaged — an un-audited failure stream is not evidence that nothing is wrong.

**[DECISION GATE] Periodic audit below threshold.** (§5.8) A methodology self-audit score below the pre-registered minimum blocks the next Tier-3 promotion (10) until remediated.

## 8. Metrics and formulas

**Telemetry completeness.** Completeness = F_pop / F_req, where F_pop is the count of required fields actually populated in a sampled record (or run) and F_req is the count of fields the project's frozen telemetry-floor definition (§5.1, §5.2) requires. Expressed as a percentage.

*Worked example (illustrative).* A project defines a 20-field required floor. A spot-check of a smoke run finds 18 populated — two silently null because of a harness defect. Completeness = 18/20 = 90%. The floor requires 100% on required fields before a run is trusted for its intended decision; 90% triggers RECALIBRATE (fix the harness) before the long run this floor exists to explain is authorized — the same ABORT/RECALIBRATE/PROCEED-WITH-DECLARED-CEILING vocabulary as any other [consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance) (04).

**Drift statistics — reference only.** No formula is prescribed here. Population-shift detection (comparing a monitored feature's production-time distribution to its measured-time distribution) is a standard statistical problem with several admissible standard tools (e.g., a distributional-distance statistic chosen to match the feature's type). *status: doctrine — not yet exercised* — this playbook has no internal execution record for any specific choice; pick one appropriate to the feature type and pre-register its threshold as a consequence-bearing tolerance (§5.7).

Clock-skew measurement and the MDE/effective-N machinery are defined in chapters 02 and 04 respectively; this chapter consumes them and does not redefine them.

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition stated per item)

- **The dashboard as record of record** (condition: whenever a trace-visualization or metrics UI is treated as the sole store of trajectories or evaluation results). A dashboard MAY mirror the record; it never replaces it (13).
- **Success-gated trajectory storage** (condition: whenever raw/failure-path output is persisted only after successful parsing). The population you most need to study — the failures — is exactly the population a success-gated store drops.
- **Truncating logs across restarts** (condition: whenever a long-running process's logs reset instead of append on restart). Forensic reconstruction depends on exactly the sessions this destroys first.
- **Retrofitting telemetry during the postmortem** (condition: always). Forensics cannot be reconstructed from data that was never captured; "we'll add it during the writeup" is a decision not to have the data.
- **Activity telemetry substituting for outcome telemetry** (condition: whenever token counts, tool-call counts, or self-reported completion stand in for a verified outcome). These are diagnostic signals, trivially inflated, and optimizing them directly is a textbook Goodhart failure; keep activity and verified-outcome telemetry in separate columns, never blended into one score.
- **Ground truth inline in the decision record** (condition: whenever a production routing/gate log stores the outcome label at write time rather than joining it afterward). This is exactly the leakage surface [ground-truth isolation](GLOSSARY.md#ground-truth-isolation) (13) and the gold-label boundary (04) exist to prevent, reintroduced at the telemetry layer.
- **Automation running past a fired drift trigger** (condition: whenever a pre-registered monitoring threshold has fired and the component has not reverted to observe-only). [Observe-only graduation](GLOSSARY.md#observe-only-graduation) (08) is conditional; treating it as a one-time achievement is the failure mode §5.7 exists to close.
- **Undocumented internals scraped to fill a vendor gap** (condition: whenever a vendor tool doesn't reliably expose a needed signal and the response is reverse-engineering rather than declaring it unavailable). An undocumented internal can change without notice and silently break the pipeline it was patched into; record the gap instead (§5.4's adapter rule).

## 10. Vendor recipes

The structural finding of this playbook (00 §10) applies here in its sharpest form: production observability is vendor-mature; the experimentation floor and the drift-monitoring layer are not — this chapter supplies both.

**[ADAPT: NV-NIMOBSERVABILITY-001]** — production observability mechanics (§5.4): metrics endpoint, distributed tracing, structured logs. Verified live 2026-08-21 (page last updated 2026-08-19). ADAPT because the source states no experimentation minimum; the decision layer this playbook adds is exactly §5.1/§5.2.

**[REFERENCE: NV-DATAFLYWHEEL-001]** — deprecated April 2026, no successor named as of verification (2026-08-21); do not adopt the artifact. The loop *shape* it demonstrated — log production examples → stratify → run a comparison across baseline and adapted candidates → judge-scored comparison → human-gated promotion, described in its own README as "flashlight, not autopilot" — remains a usable design reference for §5.6/§5.8's harvesting-and-audit loop. Trap: the source's own deprecation notice was not consistently reflected in the vendor's other documentation, which kept cross-linking and promoting it after the notice went up — verify a source's own deprecation notice directly rather than trusting inbound links to imply currency.

**[FOLLOW: EXT-OPS-002]** — the self-audit rubric (§5.8): mature, consensus, verified 2026-08-21; min-across-categories scoring, and its production-failure-harvesting pattern underwrites §5.6.

**[ADAPT: NV-ATIF-001]** — trajectory interchange format (§5.4), current/active as of 2026-08-21; adopt at interchange boundaries only. It is not a substitute for the canonical schema in §5.2.

## 11. Worked examples

- [CASE-005](examples/CASE-005_hardware-purchase-discipline.md) — preserved per-invocation telemetry (finish reasons, session/host identity, dual clocks) is what let a later performance autopsy (06) reconstruct the timeline and run the counterfactual that refuted an intuitive hardware purchase; none of that reconstruction would have been possible without §5.1's floor already landed at the time the run happened.
- [CASE-012](examples/CASE-012_restart-instability-paired-controls.md) — dual-clock stamps surfaced a systematic clock-skew artifact that had been silently biasing every published latency; the fix followed directly from having captured both clocks, not from suspecting the skew in advance.
- *Illustrative* — the completeness calculation in §8 (a 20-field floor, 18 populated, 90% completeness, RECALIBRATE before the long run it exists to explain).

## 12. Outputs and artifacts

- A landed telemetry floor (§5.1), verified via the completeness check (§8), before the next long/expensive run.
- An instantiated trajectory-record schema (§5.2) — the store/log format the project actually writes.
- A data-plane separation map (§5.3), feeding chapter 13's privacy classification.
- A deployed production observability baseline (§5.4) — metrics endpoint, tracing, structured logs.
- A versioned telemetry-pipeline correctness test suite (§5.5), run alongside the eval suite's integrity gates.
- A failure-harvesting backlog with ladder-order triage (§5.6), feeding 03 and 09.
- A drift-monitoring plan with pre-registered consequence-bearing tolerances (§5.7) for every graduated automated/learned component.
- A periodic methodology audit record (§5.8), feeding CHANGELOG.md and any [method decision records](GLOSSARY.md#method-decision-record) it triggers.

## 13. Sources

| ID | Role here |
|---|---|
| [NV-NIMOBSERVABILITY-001] | Production observability mechanics (metrics/tracing/logs); ADAPT — no experimentation minimum stated |
| [EXT-OPS-002] | Min-across-categories self-audit rubric; production-failure-harvesting pattern |
| [NV-DATAFLYWHEEL-001] | Deprecated harvesting-loop design, cited as a design reference with an explicit deprecation trap |
| [NV-ATIF-001] | Trajectory interchange format, for cross-boundary trajectory sharing only |
| [INT-CASE-005], [INT-CASE-012] | Empirical case evidence: telemetry enabling the autopsy; dual-clock skew discovery |

Gap dispositions in this chapter: **G5 (post-deployment drift monitoring of learned/routed components): COVERED-AS-DOCTRINE-NOT-YET-EXERCISED** (§4, §5.7, §7 — the monitoring design and its consequence-bearing thresholds are stated in full; no internal execution record exists for a component running past a fired trigger, marked explicitly). **G12 (telemetry-pipeline correctness): COVERED** (§5.5 procedure, §7 stop condition, §9 anti-pattern — grounded in executed cross-source consistency checking and multi-source forensic reconstruction, [CASE: CASE-005], [CASE: CASE-012]).

---

> [← Previous](11_ECONOMICS_HARDWARE_AND_CLOUD.md) · [Index](README.md) · [Next →](13_GOVERNANCE_PROVENANCE_AND_SECURITY.md)
