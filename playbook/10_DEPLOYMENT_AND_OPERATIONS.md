# 10. Deployment and Operations

> Part of the **Adaptive AI Systems Playbook** v0.1.0 ·
> [← Previous](09_TRAINING_AND_DATA.md) · [Index](README.md) · [Next →](11_ECONOMICS_HARDWARE_AND_CLOUD.md)
> **Reading time:** ~14 min. **Prerequisites:** 02, 03, 04, 06; 09 if the candidate
> being promoted came off the training rung.

## 1. Purpose and when to read this

Read this chapter once a candidate has a [frozen execution system](GLOSSARY.md#execution-system),
has cleared its evaluation gates (03, 04), has a measured performance/capacity
profile at its intended [operating point](GLOSSARY.md#operating-point) (06), and the
economics close (11). It answers one question: how does that candidate earn real
traffic, in what shape, and how do you get back out if it goes wrong.

**Read this honestly, per this playbook's own rule (conventions on voice and
honesty).** This chapter is a deliberate mix of two very different kinds of claim,
and they are labeled apart everywhere below:

1. **Established SRE and progressive-delivery practice** — staged rollout,
   [shadow](GLOSSARY.md#shadow-deployment) traffic,
   [canary](GLOSSARY.md#canary-deployment) restraint, mirrored comparison. This is
   decades-old production
   discipline outside AI systems entirely, carried here as `consensus` evidence
   with named external sources (§10). Follow it by the book.
2. **AI-specific doctrine** — what changes when the thing being promoted is a
   stochastic generator rather than a deterministic function, and what a rollback
   actually has to undo for a system with in-flight generation state. This half is
   carried at `inference` strength or explicitly marked
   `status: doctrine — not yet exercised`: this playbook's own record has named the
   promotion pipeline as a sequence of stages without a rehearsed rollback
   procedure or pre-registered trigger thresholds behind it (gap disposition G10,
   §13). You get the full procedure; you also get an honest account of what has and
   has not been exercised.

## 2. Inputs required

- A [frozen execution system](GLOSSARY.md#frozen-identity) that passed the
  promotion gate of a frozen [experiment contract](GLOSSARY.md#experiment-contract) (04).
- A versioned [suite release](GLOSSARY.md#suite-release) result the candidate
  cleared, including the [static integrity gates](GLOSSARY.md#static-integrity-gates) (03).
- A performance/capacity profile at the intended operating point, from the
  [performance autopsy](GLOSSARY.md#performance-autopsy) discipline (06).
- An economics decision that the candidate is worth serving at its measured cost (11).
- The project's [stakes tier](GLOSSARY.md#stakes-tier) (00, 01) — it sets which
  parts of this chapter are mandatory versus optional.
- If the candidate came off the training rung: forgetting-gate results and
  adapter/base [provenance](GLOSSARY.md#provenance) (09), and a model-license
  check (13).

## 3. Decisions this chapter supports

- Ship or don't ship: the promotion go/no-go.
- What shape the rollout takes for this stakes tier — direct swap, shadow-only,
  shadow-then-canary, or a fully staged progressive rollout.
- What triggers a rollback, who decides, and what the rollback mechanically has to
  undo.
- Where a human approval gate sits in the pipeline.

## 4. Normative principles

**[PRINCIPLE] Staged promotion.** (consensus)
No candidate goes from passing its offline suite straight to full traffic. The
default sequence — offline confirm → shadow → canary → progressive rollout →
steady state — is standard practice across managed ML platforms
[EXT-OPS-001A], [EXT-OPS-001B] and general production engineering
[EXT-OPS-001C]. Each stage has an entry gate (what must be true to start it) and an
exit gate (what must be true to advance); §5 gives the default table.

**[PRINCIPLE] Restraint over instrumentation.** (consensus)
"Use the simplest model that meets your technical and business objectives"; run
exactly one canary at a time; every canary metric must be causally attributable to
the change under test, not confounded by unrelated system activity; the
aggregation window must be much shorter than the canary's total duration so a
regression is visible before the canary ends
[EXT-OPS-001C]. A small lab's default is manual mirrored comparison plus a small,
named, causally-attributable metric set — not a bespoke statistical canary judge.
Building the judge is a scale decision (§10), not a starting point.

**[PRINCIPLE] Execution-system identity is pinned per stage.** (strong-evidence)
A [comparability claim](GLOSSARY.md#comparability-claim) about a promotion candidate
is only as good as the [frozen identity](GLOSSARY.md#frozen-identity) behind it (02).
A provider-side model or runtime redeploy in the middle of a canary silently creates
a new execution system; the canary's accumulated evidence about the *old* one no
longer applies, and continuing to compare against it is invalid regardless of how
much traffic has already been served.

**[PRINCIPLE] Compare distributions, not cases, under measured nondeterminism.** (inference)
Where the [reproducibility boundary](GLOSSARY.md#reproducibility-boundary) is not
strict case-by-case identity — the common case for LLM serving
[EXT-DETERM-001] — a shadow or canary comparison against the incumbent is a
comparison of outcome *distributions*, evaluated with the same clustered/paired
statistical machinery as any other experiment (04), not a demand that every
individual case match. Treating a single differing output as a regression, on a
system that was never shown to reproduce case-by-case even against a frozen copy of
*itself*, manufactures false alarms. [CASE: CASE-012] is the internal precedent for
measuring the boundary before trusting a comparison across it.

**[PRINCIPLE] Rollback is a designed, rehearsed path.** (inference — first-principles;
*status: doctrine — not yet exercised*, see §5)
A rollback that has never been exercised is a hypothesis about what would happen,
not a path. This playbook's own operating record has named the pipeline stages
(shadow → canary → gate → rollback) without a trigger threshold, an owner, or a
rehearsal behind them — precisely the gap this principle exists to close (G10).
State ownership, mechanics, and a rehearsal cadence *before* the first real
promotion, not after the first incident.

**[PRINCIPLE] One change crosses a promotion stage at a time.** (consensus, corollary
of P5/02)
Promoting a model change and an infrastructure change in the same canary destroys
the causal attributability the restraint doctrine requires — a regression cannot be
assigned to either change alone. Sequence them.

**[PRINCIPLE] Human approval gates scale with stakes tier.** (inference, from the
[rigor dial](GLOSSARY.md#rigor-dial), 00 §6)
Tier 1 may advance a stage on a single owner's sign-off; Tier 2 names an approver
role distinct from the person who ran the promotion; Tier 3 requires human approval
at every stage advance from shadow onward, plus the security/threat-model review of
13. §6 gives the parameter table.

## 5. Default procedure

**Table 10.1 — the promotion pipeline (default sequence).**

| Stage | Entry gate | What runs | Exit gate | User-visible? |
|---|---|---|---|---|
| Offline confirm | Frozen contract passed its confirm-split verdict (04); static integrity gates green (03) | Nothing new — this stage *is* the evidence chapters 03–04 already produced | CONFIRMED verdict recorded; execution-system identity hashed and pinned (02) | No |
| Shadow | Offline confirm passed; execution system pinned; [telemetry floor](GLOSSARY.md#telemetry-floor) live (12) | Real production requests are mirrored to the candidate; only the incumbent's response reaches the user | Outcome-distribution comparison (paired where items repeat) shows no regression beyond the pre-registered tolerance | No — mirrored only |
| Shadow — human-baseline variant (no automated incumbent) | Offline confirm passed; execution system pinned; telemetry floor live (12); the human process's own outcomes captured as the comparator | Candidate runs alongside the current human process; candidate output logged, never acted on; the human process continues unchanged | Measured shadow **agreement rate** at or above a pre-registered floor **and regret rate** at or below a pre-registered ceiling (defined below), both read through §8's clustered/paired machinery, with every disagreement case resolved by a pre-registered adjudication procedure | No — logged only |
| Canary | Shadow exit gate passed; rollback rehearsed (§5 below) | A small, pre-declared real-traffic fraction is served by the candidate | The causal metric set stays within its [consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance) for the full aggregation window; no unresolved rollback trigger fired | Yes — small fraction |
| Progressive rollout | Canary exit gate passed; approver sign-off per §4/§6 | Traffic fraction increases in pre-declared steps, one step at a time | Each step's tolerance holds before the next step starts | Yes — increasing fraction |
| Steady state | Full rollout complete | Normal production observability (12) | N/A — this is the resting state until the next promotion | Yes — full |

Every exit gate above is a **[DECISION GATE]**-shaped check, not a vibe: name the
metric, the pre-registered threshold, and the named consequence (ABORT the stage /
hold and re-measure / advance) before the stage starts, exactly as 04 requires for
any other decision-driving threshold.

**The human-baseline shadow variant, in full (for greenfield / no-incumbent
deployments).** Some promotions have no automated incumbent to mirror against — a
new capability entering a process a human previously ran alone, reached via the
routing tree's "no incumbent" branch. "No regression beyond tolerance" is undefined
without a comparator; the comparator here is the current human process, and it needs
its own metric pair rather than the incumbent row's outcome-distribution comparison:

- **Agreement rate**: the share of paired cases (same item, candidate output vs. the
  human process's actual output) where the two match, or fall inside a
  pre-registered equivalence band for non-binary outputs — read with the same
  [MDE](GLOSSARY.md#mde)/[INCONCLUSIVE](GLOSSARY.md#inconclusive) discipline as any
  other comparison (04, §8 below); an agreement read below its own MDE is
  INCONCLUSIVE, not a pass.
- **Regret rate** (defined for this human-baseline case): the share of cases where
  the candidate's output, had it been acted on instead of the human's, would
  plausibly have produced a worse outcome than the human's actual decision —
  adjudicated against the same [ground-truth](GLOSSARY.md#gold-labels) boundary
  chapter 03 uses for the task, never against the human's decision by default. The
  human process is a comparator here, not automatically gold; a case where the
  candidate is right and the human process was wrong is not a regret case, and
  conflating the two overstates the human baseline's reliability.
- **Disagreement adjudication**: every case where candidate and human diverge is
  routed to a pre-registered adjudication procedure — who reviews it, against what
  standard, and how the adjudicated verdict is counted toward the regret rate —
  decided *before* the shadow period starts (P7, chapter 00), not improvised case by
  case as disagreements arrive.
- **Clustering**: the human operator/clinician/analyst identity is a
  [clustering unit](GLOSSARY.md#clustering-unit) for both statistics (04) — a shadow
  run measured mostly against one unusually strict or lenient rater is not evidence
  about "the human process" in general; the effective N and MDE must account for it.

Exit gate for this variant: agreement rate resolves above its pre-registered floor
**and** regret rate resolves below its pre-registered ceiling, both at or beyond the
design's own MDE — an underpowered shadow period holds and extends rather than
advancing on a favorable but INCONCLUSIVE read.

*status: doctrine — not yet exercised* — the shadow→canary sequence above composes
individually-consensus mechanics (SageMaker/Azure-style mirroring, SRE-style
restraint) into one pipeline; the composition itself, and the trigger thresholds
that make each exit gate real rather than aspirational, have no internal execution
record behind them yet. Treat the table as the procedure to run, not as a validated
result.

**Rollback rehearsal procedure (do this before the first real canary, not during
the first incident):**

1. Identify every piece of state a rollback has to undo: in-flight requests
   mid-generation, any KV-cache or session state pinned to the candidate,
   adapter/LoRA version references held by callers, cached tool-call results keyed
   to the candidate's execution-system identity, and — separately from all of the
   above, because rolling back the model does not undo it — **side effects already
   committed to an external system of record** (a note written into a record store,
   a submitted transaction, a downstream system updated by a write-capable tool
   call under 13's tool-permission gate). For each write-capable integration, name
   what a rollback must do to a side effect already committed: retract it, amend it
   with a stated correction, or flag it for human review — and who is notified when
   that path fires. A rollback that only reverts the serving system is incomplete
   for any candidate with write access to something outside it.
2. Write the rollback as an executable command or script, not a paragraph of prose
   — the same [fail-closed](GLOSSARY.md#fail-closed) discipline 13 requires of the
   promotion path applies to the exit.
3. Run it against a non-production copy of the pipeline and time it. If the
   candidate is stateful (multi-turn sessions, cached context), verify a rollback
   mid-session does not corrupt or silently truncate in-flight state.
4. Record the rehearsal (who, when, what was verified) as part of the
   [operational handoff](templates/OPERATIONAL_HANDOFF.md) artifact (§12).
5. Re-rehearse whenever the execution system's identity changes materially (new
   runtime, new adapter format, new serving stack) — a rollback rehearsed against
   last quarter's stack is not evidence about this quarter's stack.

**Incident-response runbook skeleton** (*status: doctrine — not yet exercised*):

```
detect            — the trigger that fired (§7), or a human report
  → freeze         — halt any promotion in progress; no new stage advances
  → decide         — the named rollback owner (§6) executes or explicitly waives
  → rollback        — run the rehearsed command; verify exit state
  → communicate     — stakeholders per the stakes tier's comms requirement
  → postmortem      — feeds 12's failure harvesting and the look/prediction ledgers
```

Freeze-before-rollback matters: a rollback decided under pressure while other
promotions are still advancing compounds the incident instead of containing it.

## 6. Project adaptation parameters

| Parameter | What it governs | How to set it |
|---|---|---|
| Canary traffic fraction | How much real exposure the candidate gets before wider rollout | Small enough that a regression's blast radius is acceptable at your stakes tier; large enough to be statistically informative on your causal metric set. Calibrate against the metric's own [MDE](GLOSSARY.md#mde) (04), not intuition. |
| Aggregation window | How often the causal metric set is re-evaluated during a canary | Must be ≪ the canary's total planned duration (EXT-OPS-001C) — set it so a regression surfaces well before the canary would otherwise complete. |
| Causal metric set | What the canary is judged on | Small, named, each metric argued causally attributable to the change (not to unrelated system load). Add a metric only with an argument for its attributability. |
| Rollback owner | Who decides and executes | Named role, not "whoever is online" — distinct from the promotion's author at Tier 2+ (separation of duties mirrors 04's scientific-owner/executor split). |
| Approval-gate composition | Who signs off at each stage advance | Tier 1: single owner. Tier 2: named approver role distinct from the runner. Tier 3: human approval at every advance from shadow onward, plus 13's security review before canary. |
| State-compatibility scope | What the rollback rehearsal must check | Enumerate per §5 step 1 for your own architecture — in-flight requests, session/KV state, adapter version pins, cached tool results, and side effects already committed to any external system of record. |
| Shadow comparison sample | How much mirrored traffic before a shadow verdict | Sized against the same-item [paired design](GLOSSARY.md#paired-design)'s MDE (04) if items repeat across arms; otherwise against the clustered/unpaired design the outcome distribution requires. |

## 7. Decision gates and stopping conditions

**[DECISION GATE] Stage advance.** Inputs: the current stage's exit-gate metric(s)
against their pre-registered tolerance. Rule: tolerance held for the full
aggregation window → advance; tolerance breached → execute the named consequence
(§8); tolerance underpowered at this traffic level → hold and extend, never
advance on an [INCONCLUSIVE](GLOSSARY.md#inconclusive) read. Outcomes: ADVANCE /
HOLD / ROLLBACK.

**[STOP CONDITION] Global tripwires for this chapter** (in addition to 00's list):

1. A provider-side or infrastructure redeploy is detected mid-canary — freeze; the
   execution-system identity changed (§4).
2. A pre-registered rollback trigger fired and the response is a discussion about
   whether to honor it rather than executing it (mirrors 00's stop condition 4 —
   the consequence is not optional once triggered).
3. A second canary is about to start while one is already running (§4 restraint
   doctrine).
4. A promotion is about to advance on a metric read that is below its own MDE (04)
   — an inconclusive shadow/canary read is not a pass.
5. The rollback for this execution system has never been rehearsed and a canary is
   about to start anyway.

**Out of scope for v0.1 — multi-tenant / concurrent-load SLA behavior during
promotion (gap disposition G9: EXPLICITLY-OUT-OF-SCOPE-FOR-0.1).**
Everything above assumes a canary or shadow comparison under whatever concurrency
the current production traffic happens to present. How a candidate's SLA holds up
as *concurrent multi-tenant load* is deliberately ramped during rollout — the
question of capacity/queueing behavior under real contention, not just outcome
quality — is not validated methodology in this release; 06 states the same
boundary for offline capacity testing. The skeleton, marked
*status: doctrine — not yet exercised*, for whoever needs it next: run a
k6-style load-test taxonomy [EXT-PERF-002] (smoke → average-load → stress →
spike → soak) against the canary's traffic slice with SLO thresholds (e.g., p95
latency, error rate) as automated hold/rollback conditions, layered on top of the
quality-outcome gates above rather than replacing them; consult
[NV-NIMOPERATORCANARY-001] for what a Kubernetes-native rollout mechanism does and
does not automate, and [EXT-OPS-004] for the automated-judgment ceiling if the
operation eventually justifies building one.

## 8. Metrics and formulas

**Causal metric set design.** For each candidate metric, require an explicit answer
to: *if this metric moves, can the movement be attributed to the change under
test rather than to something else happening in the system at the same time?*
[EXT-OPS-001C]. Metrics that fail this test (e.g., system-wide resource usage
during a canary that shares infrastructure with unrelated workloads) are dropped
from the causal set; they may still be watched, but they do not gate the decision.

**Distributional shadow/canary comparison.** Use the same clustered/paired
inference machinery as any other comparison (04): identify the
[clustering unit](GLOSSARY.md#clustering-unit), compute
[effective N](GLOSSARY.md#effective-n), state the [MDE](GLOSSARY.md#mde) the
canary's traffic volume actually supports, and report
[INCONCLUSIVE](GLOSSARY.md#inconclusive) rather than a pass when the volume seen so
far cannot resolve the question. This is not a new formula — it is the ch.04
formula set applied to an operational, rather than experimental, decision.

**Rollback trigger as a consequence-bearing tolerance (illustrative worked
example).** A rollback trigger is a
[consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance) applied
operationally: name the count, the window, and the consequence before the canary
starts.

> *Illustrative, invented numbers — calibrate against your own severity
> definitions and traffic volume, never copy these:* tolerance = at most 2
> severity-1 outcomes per 1,000 canary requests within a rolling 1-hour
> aggregation window (§4, §6). On the 3rd severity-1 outcome
> inside one window: **ABORT** the canary and execute the rehearsed rollback. Below
> that count: **PROCEED**. A tolerance that names no consequence for its breach is
> the unpriced-escape-hatch anti-pattern 00 already rejects — it applies here
> exactly as it applies to any other experiment.

**Performance/capacity metrics** (TTFT, ITL, system vs per-user throughput,
operating point selection) are defined and measured per 06; this chapter consumes
that profile at the chosen operating point, it does not redefine it.

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition: always — these are generically wrong)

- **Over-invested canary statistics for a team the scale doesn't justify.**
  Building a Kayenta-class automated statistical judge before the traffic volume
  and team size justify its build/maintenance cost inverts the restraint doctrine
  (§4); [EXT-OPS-004] is explicitly cited as the ceiling of canary automation, not
  the default — a small lab's default is manual mirroring plus a small causal
  metric set.
- **Per-case parity as the shadow-comparison bar.** Flagging any single differing
  output as a regression on a system whose reproducibility boundary was never
  measured to be case-by-case identity manufactures false alarms and trains
  operators to ignore the alarm (§4; [CASE: CASE-012]).
- **Mistaking a native rolling update for a real canary.** Many serving stacks'
  default upgrade path is a plain rolling update with rollback undocumented or
  manual; verify what your specific serving stack's rollback story actually is
  before relying on it as your safety net — do not assume canary semantics a
  vendor's native path does not provide [REFERENCE: NV-NIMOPERATORCANARY-001].
- **An unrehearsed rollback.** A [rollback path](GLOSSARY.md#rollback-path) that
  has never been executed against a non-production copy is a hypothesis, not a
  path.
- **Multiple simultaneous canaries.** Confounds attribution for all of them at once
  (§4, [EXT-OPS-001C]).
- **Bundling an infrastructure change into a model-promotion canary.** Same
  confound, different axis (§4 one-change-at-a-time).
- **"The model got better" applied to a promotion decision when the runtime,
  provider, quantization, or harness changed underneath it.** The general
  anti-pattern from 00, at its highest-stakes point of application: a promotion
  decision made on a comparability claim that quietly crossed a
  [frozen identity](GLOSSARY.md#frozen-identity) boundary.
- **Skipping the postmortem.** A rollback or incident that does not feed the
  [failure harvesting](GLOSSARY.md#failure-harvesting) loop (12) repeats itself with
  better tooling next time and no more evidence than last time.

## 10. Vendor recipes

| Verdict | Source | Scope | As-of |
|---|---|---|---|
| **[FOLLOW: EXT-OPS-001C]** | Google SRE Workbook, ch.16 Canarying Releases | Restraint doctrine: simplest model that meets objectives; one canary at a time; causally attributable metrics; aggregation window ≪ canary duration | Verified 2026-08-21; stable, mature |
| **[ADAPT: EXT-OPS-001A]** | AWS SageMaker shadow testing | Mirrors live inference traffic to a shadow variant in real time; only the production variant's response reaches the caller. Substitute: SageMaker builds no comparison/interpretation engine — the analysis in §8 is your job, on your metrics. | Verified 2026-08-21 |
| **[ADAPT: EXT-OPS-001B]** | Azure ML safe rollout (blue-green + mirrored traffic) | Staged manual traffic shifting (small % → all), plus mirrored/shadow traffic capped at 50% of live traffic, one deployment at a time, not available on every endpoint type. Substitute: the stage-advance decision rule (§7) — Azure documents the mechanism, not when to trust it. | Verified 2026-08-21 |
| **[ADAPT: NV-NIMOPERATORCANARY-001]** | NIM Operator + KServe/Knative | Knative-revision traffic splitting for canary rollout; rollback mechanics are delegated to Knative. The *native* NIM Operator upgrade path (outside KServe mode) is a plain rolling update — rollback is manual. Substitute: verify which path your deployment actually uses before assuming canary semantics. | Verified 2026-08-20 |
| **[REFERENCE: EXT-OPS-004]** | Kayenta (Netflix/Google automated canary analysis) | The *ceiling* of canary automation — full automated statistical judgment. Explicitly not the small-team starting point (§4, §9); consult only once traffic/team scale justifies the build. | Verified 2026-08-20 — existence-proof only, its exact statistical test not independently re-verified this pass |

**Deprecation watch (as-of 2026-08-21):** vendor serving/deployment paths churn
under you. Two examples worth naming so a stale assumption doesn't survive a
redeploy: a major NIM serving backend has moved its default away from
TensorRT-LLM toward vLLM — pin your serving backend explicitly in the execution-
system identity (02) rather than trusting "the default"
[NV-NIMTRTLLM-DEP-001]; the only official end-to-end local fine-tune-to-deploy
workflow one major vendor shipped was discontinued with no successor named — do
not build a local/private-deployment [archetype](GLOSSARY.md#archetype)'s
promotion path around a single vendor's packaging tool without a fallback
[NV-RTXAITOOLKIT-DEP-001]. A rented
deployment destination's own product name and positioning can also change under
you — verify the current identity of any rented serving destination before pinning
it into a contract or a runbook [NV-DGXCLOUD-DEP-001].

## 11. Worked examples

- [CASE-007](examples/CASE-007_deterministic-cascade-gate.md) — the deterministic
  verifier-gated cascade that chapter 08 develops was, in the source project's
  record, a *production-topology* decision: promoting a
  [cascade](GLOSSARY.md#cascade) does not require promoting a
  [learned router](GLOSSARY.md#learned-router). The lesson for this chapter is that
  the pipeline of §5 applies to topology decisions as well as single-model swaps —
  a cascade gate is itself a component with its own execution-system identity to
  pin and its own shadow/canary comparison to run before it is trusted with real
  traffic.
- [CASE-012](examples/CASE-012_restart-instability-paired-controls.md) — the
  internal precedent for §4's distributional-comparison principle: restarting the
  serving process by itself changed outcomes that had been stable moments before,
  on an otherwise-unchanged execution system. The response was not to chase
  case-by-case parity but to measure the reproducibility boundary and scope
  comparisons — including any shadow/canary comparison — to what was actually
  measured to hold.

## 12. Outputs and artifacts

- A recorded promotion decision (go/no-go, rollout shape, stage-by-stage
  entry/exit results) into
  [templates/OPERATIONAL_HANDOFF.md](templates/OPERATIONAL_HANDOFF.md), covering
  at minimum: pinned execution-system identity; the causal metric set and its
  tolerances (or, for a no-incumbent promotion, the agreement/regret thresholds and
  the disagreement-adjudication procedure, §5); the rollback owner, mechanics,
  external-system-of-record retraction/amendment path, and rehearsal log; on-call
  contact; known limitations; the security/privacy gate result at this stakes tier
  (13).
- A rehearsed, versioned rollback runbook, re-rehearsed on execution-system
  identity change (§5).
- Any principle override or restraint-doctrine deviation as a
  [method decision record](templates/METHOD_DECISION_RECORD.md).
- Postmortems and rollback events feeding 12's failure-harvesting loop and the
  [look ledger](GLOSSARY.md#look-ledger) and [prediction ledger](GLOSSARY.md#prediction-ledger) (04).

## 13. Sources

| ID | Role here |
|---|---|
| [EXT-OPS-001A] | SageMaker shadow testing — ADAPT: mirroring mechanics, comparison is the operator's job |
| [EXT-OPS-001B] | Azure ML safe rollout — ADAPT: staged manual traffic shifting + capped mirroring |
| [EXT-OPS-001C] | Google SRE Workbook ch.16 — FOLLOW: the restraint doctrine (§4, §9) |
| [EXT-OPS-004] | Kayenta — REFERENCE: the automation ceiling, not the default |
| [NV-NIMOPERATORCANARY-001] | KServe/Knative canary mechanics; native-path rollback caution |
| [NV-DGXCLOUD-DEP-001] | Rented-destination naming/positioning churn caution |
| [NV-NIMTRTLLM-DEP-001] | Serving-backend default churn — pin explicitly |
| [NV-RTXAITOOLKIT-DEP-001] | Single-vendor local deploy-packaging path discontinued with no successor |
| [EXT-OPS-002] | ML Test Score rubric — Monitor-7 pattern behind the postmortem→failure-harvesting link into 12 |
| [EXT-PERF-002] | k6 load-test taxonomy — the out-of-scope multi-tenant/SLA skeleton (§7) |
| [EXT-DETERM-001] | Nondeterminism as a measured property — grounds §4's distributional-comparison principle |
| [INT-CASE-007], [INT-CASE-012] | Internal case evidence, §11 |

**Gap dispositions in this chapter:**
- **G10 (rollback / incident-response runbook mechanics): COVERED-AS-DOCTRINE-NOT-YET-EXERCISED.**
  §1 states the split up front; §5 gives the full rollback-rehearsal procedure and
  incident-response runbook skeleton, both carrying the
  `status: doctrine — not yet exercised` marker; §13 records that this playbook's
  own operating history has named the pipeline stages without a rehearsed
  procedure behind them.
- **G9 (multi-tenant capacity/concurrency/SLA burn under real traffic): EXPLICITLY-OUT-OF-SCOPE-FOR-0.1.**
  Stated in §7, mirroring the identical scope boundary chapter 06 states for
  offline capacity testing — this chapter adds only the promotion-time skeleton
  (k6-style thresholds as hold/rollback conditions) as doctrine, not as validated
  methodology.

---

> [← Previous](09_TRAINING_AND_DATA.md) · [Index](README.md) · [Next →](11_ECONOMICS_HARDWARE_AND_CLOUD.md)
