# 07. Optimization and the Intervention Ladder

> Part of the **Adaptive AI Systems Playbook** v0.1.0 ·
> [← Previous](06_INFERENCE_PERFORMANCE_AND_CAPACITY.md) · [Index](README.md) ·
> [Next →](08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md)
> **Reading time:** ~35 min. **Prerequisites:** 00 (principles — the ladder in short
> form), 03 (evaluation foundation — the [canonical failure taxonomy](GLOSSARY.md#canonical-failure-taxonomy)
> this chapter operationalizes), 04 (experiment design — the statistics a diagnostic
> gate borrows), 06 (performance characterization — where a capacity gap is first
> measured).

## 1. Purpose and when to read this

You arrive here with a *diagnosed* gap: chapter 03's taxonomy told you which
root-cause class (RC-1…RC-12) is responsible, or chapter 06's performance work told
you a capacity ceiling is binding. This chapter is the operational hinge between
diagnosis and action — it turns "the system underperforms on category X" into "here
is the next thing to change, here is what it costs, and here is the evidence that
justifies paying that cost before you pay it."

Read this chapter when:
- A measured gap has a diagnosed root-cause class and you need to pick the
  intervention.
- An expensive experiment (a training run, a larger model, an architectural change)
  is being proposed and you need to know whether it has earned the right to run yet.
- You are setting a generation/reasoning budget, deciding whether to quantize, or
  choosing between prompt/workflow variants.

Do not read this chapter to *find* a root cause — that is chapter 03's job. This
chapter assumes the diagnosis is already in hand and asks only "given this diagnosis,
what next, at what cost, on what evidence."

## 2. Inputs required

- A root-cause class from the [canonical failure taxonomy](GLOSSARY.md#canonical-failure-taxonomy)
  (RC-1…RC-12) — not a symptom description. If you have only a symptom, return to
  chapter 03.
- A [frozen execution-system](GLOSSARY.md#execution-system) identity (chapter 02):
  every rung below assumes the thing you are measuring has not silently changed
  underneath the comparison.
- Your project's [stakes tier](GLOSSARY.md#stakes-tier) (chapter 00/01) — it sets how
  much pre-registration and record-keeping the diagnostic and adoption procedures in
  this chapter require.
- For budget calibration: a generation-length sample from the
  [iterate split](GLOSSARY.md#screening-vs-inference).
- For a diagnostic gate ahead of an expensive experiment: the expensive experiment's
  own draft hypothesis, however informal, and access to a small paired sample of the
  population it would run on.

## 3. Decisions this chapter supports

- Which rung of the ladder to work at next, given a diagnosis.
- Whether an expensive experiment (training, a larger/different model, an
  architectural change) has earned the right to run, before it runs.
- What generation/reasoning budget to set, and what to do when truncation still
  bounds outcomes at a larger budget.
- Whether to quantize an artifact, to what precision, and what evidence a quantized
  artifact must clear before it ships.
- When to stop optimizing at a rung and either accept the current gap or descend
  further.

## 4. Normative principles

**[PRINCIPLE] Descend the ladder on evidence, not on the calendar.**
(strong-evidence *for the evidenced subset* — rung 0 first, and rungs 2–4 before
rung 7 on knowledge/citation tasks [EXT-FT-001]; **inference** for the relative
ordering of rungs 3–6 and 8–9, which is a cost ordering argued from first
principles, not an empirical finding)
The [intervention ladder](GLOSSARY.md#intervention-ladder) — instrument integrity →
infrastructure/runtime → evidence/retrieval/context → tool contracts & output
enforcement → specification & verification → generation/reasoning budget →
routing/escalation → fine-tuning → larger/different model → architectural redesign —
is chapter 00's P3, restated for this chapter's job: the diagnosis names the rung, not
habit, not what worked last project, not what is currently fashionable. §5.1
operationalizes each rung; §7 states the descent gate. The scope note in the label is
load-bearing: what external evidence supports is rung 0's primacy and the
retrieval/prompt-before-training edge on factual tasks. The rest of the order is a
*cost* argument — cheaper diagnoses first — which is why §5.1 permits rungs 1–6 to be
locally re-sequenced on a clear diagnosis while rung 0's priority and the
never-train-around-defects rule are not locally overridable.

**[PRINCIPLE] A costly experiment earns its cost only after a cheap diagnostic clears
it.** (inference — first-principles; case-study corroboration, n=1) Before
committing to an expensive experiment, isolate the
cheapest observable that would tell you the experiment's core assumption is false, and
measure that first. First-principles argument: an expensive experiment's assumed
mechanism is almost always testable on a small paired sample at a fraction of the
cost — running the expensive version first spends the larger budget to learn
something the small one would have told you for free. The corroboration is weaker than
the argument and is labelled as such: vendor guidance to "start lightweight, invest
early in evaluation, and layer in training-based techniques where measurement shows
they're needed" [NV-AGENTICBLOGS-001] is a framing statement, not a study; and one
internal case shows a diagnostic run at a small fraction of an expensive experiment's
cost correctly gating the decision to proceed [CASE: CASE-011] — a single instance,
not a base rate. §5.2 gives the design pattern.

**[PRINCIPLE] Never train (rung 7+) around a defect at rungs 0–4.** (strong-evidence)
Restated here because it is the single most common shortcut this chapter exists to
block: a capability gap that is actually a broken instrument, a serialization defect,
an unreachable fact, a missing tool contract, or an unspecified task will not be fixed
by fine-tuning, and fine-tuning around it burns the most expensive rung on a problem
a cheaper rung would have closed. Corroborated by the RAG/prompt-first literature for
knowledge tasks [EXT-FT-001] and by vendor guidance placing evaluation and
lightweight methods before training-based ones [NV-AGENTICBLOGS-001].

**[PRINCIPLE] Completion is not correctness.** (inference — first-principles,
corroborated by case evidence) A proxy that correlates with the true outcome under one
regime (a fixed budget) need not stay correlated once you start optimizing the thing
that regime was holding constant (the budget itself) — the classic failure of
optimizing a proxy instead of the target. A generation that finishes without
truncating is not thereby a generation that is *right*; only the deterministic scorer
(or calibrated judge, chapter 03) gets to say that. An internal case shows a
generation-cap confound inflating a model-comparison headline until the budget factor
was isolated [CASE: CASE-006], and the direct anti-pattern — letting a completion
proxy alone justify a go decision — recurs often enough to name explicitly (§9).

## 5. Default procedure

### 5.1 The ladder, operationally

Chapter 03 defines the twelve root-cause classes normatively; this table is their
operational form — what each rung fixes, roughly what it costs, what to check first
before spending at that rung, and **two separate evidence bars that must never be
conflated**:

- **Entry evidence (this rung is indicated)** — what licenses you to *start* work at
  the rung. It is a diagnosis, not an achievement.
- **Exit evidence (this rung is exhausted)** — what licenses you to *stop* work at the
  rung and descend past it. This is the column the descent gate in §7 binds on.

A rung whose entry evidence is absent is **inapplicable**, not exhausted (example: no
routing decision exists because the system has exactly one tier). Inapplicability
satisfies the exit requirement **only** when it is recorded as a finding with the
evidence that established it — a rung is never cleared by silence.

**Cost class** (illustrative ordinal — calibrate the actual units to your own
accounting, §6):

| Class | Rough shape |
|---|---|
| C0 | Configuration or instrumentation change only; no re-run of the system under test |
| C1 | An engineering change plus a re-run on the iterate split (hours) |
| C2 | An engineering change plus a pilot on the iterate split and a limited confirmation (hours to a day) |
| C3 | A frozen experiment with training or rented-hardware spend (days, priced GPU-hours) |
| C4 | A new candidate-selection cycle or a redesign (days to weeks, re-derives part of the execution system) |

| Rung | Fixes (RC class) | Cost class | Entry evidence (this rung is indicated) | Exit evidence (this rung is exhausted) | Cheap diagnostic first |
|---|---|---|---|---|---|
| 0 — instrument integrity | RC-1 measurement/instrument defect | C0–C1 | Always entered first: no integrity evidence exists yet for the current suite version and execution-system identity, or RC-1 is the diagnosis | Static integrity gates green: measured [reachability ceilings](GLOSSARY.md#reachability-ceiling), no [inversions](GLOSSARY.md#inversion-check), gold-answer gate passed, determinism verified (ch. 03) | The integrity gates *are* the diagnostic; there is no cheaper check |
| 1 — infrastructure/runtime | RC-2 infrastructure/runtime defect | C1 | Restart, concurrency, host, transport, or configuration variance is implicated: results move without the system under test moving | [Reproducibility boundary](GLOSSARY.md#reproducibility-boundary) measured (ch. 02) and the gap persists inside it; byte-level transport fidelity verified end to end through every serving, proxy, and serialization hop [CASE: CASE-008] | Restart/concurrency/cross-host probes (ch. 02); byte-equivalence check through every proxy [CASE: CASE-008] |
| 2 — evidence/retrieval/context | RC-3 missing/unreachable evidence | C1–C2 | Failure cases lack, in context, a fact the task requires, and the fact is plausibly obtainable | [Evidence reachability](GLOSSARY.md#evidence-reachability) audited per stratum and cleared (ch. 08) — the required evidence is demonstrably reachable and the gap persists | Reachability replay against the real tool broker, not the generator's assumptions |
| 3 — tool contracts & output enforcement | RC-4 tool/API contract defect, RC-5 output/format enforcement gap | C1–C2 | The failure sample shows schema, addressing, ordering, or permission mismatches, or correct content lost to parsing/structure failures | [Tool contract](GLOSSARY.md#tool-contract) audit passed; schema/grammar conformance of the **tool-emitted payload** verified against its declared contract; gap persists with contracts clean | Contract schema validation against the actually emitted payload (byte corruption *introduced by the transport itself* is rung 1's, not this rung's — see the discriminator note below) |
| 4 — specification & verification | RC-6 task-specification gap, RC-7 verification gap | C1–C2 | Failures look like the system was never told what to do, or the verifier is passing known-bad outputs | Controlled, single-factor prompt/workflow variants (§5.4) show no further pre-registered gain; verifier coverage checked against known silent-failure modes | One factor per arm against a pre-registered adoption rule, not an unstructured sweep |
| 5 — generation/reasoning budget | RC-8 capacity/budget exhaustion | C2 | Truncation-rate tolerance breached even at the pre-registered headroom quantile, **and** a diagnostic (§5.2/§5.3) shows the residual truncation is where the gap actually lives | The cap has been re-derived from the **current artifact's own** iterate-split length distribution (§5.3 step 1–2); the truncation rate sits inside its pre-registered tolerance at that quantile; **and** the truncation-linked gap did not close — a paired cap-raise diagnostic (§5.2) returned a rescue fraction whose *interval* sits at or below the RE-SCOPE/DROP band | The paired cap-raise diagnostic (§5.2/§5.3) — never a bare "raise the cap and see" |
| 6 — routing/escalation | RC-9 routing/escalation mismatch | C2 | [Oracle analysis](GLOSSARY.md#oracle-analysis) (ch. 08) shows a meaningful ceiling gain; a routing [break-even](GLOSSARY.md#break-even) is achievable; a deterministic gate is insufficient | **Either** the oracle headroom was captured — a gate or router was built and the residual gap persists under a paired comparison (ch. 08) — **or** oracle analysis shows the remaining between-tier headroom is below the decision's materiality bar, including the case where no offload share breaks even at any threshold (ch. 08 §8) | The paired-oracle opportunity map between tiers, before any router is built (ch. 08) |
| 7 — fine-tuning | RC-10 learnable capability gap | C3 | Taxonomy-identified residual gap **and** every rung above satisfies its own **Exit evidence** cell (or carries a recorded inapplicability finding) **and** training data demonstrably contains the skill **and** economics close (ch. 11) | The rung's own pre-registered acceptance gate returned **CONFIRMED** or **REFUTED** under chapter 04 (frozen contract, paired same-item comparison against the untuned base, MDE stated before the run). **INCONCLUSIVE does not exhaust the rung** — it re-scopes it; a REFUTED result is the evidence that reclassifies RC-10 → RC-11 (ch. 09) | Rig-first pipeline de-risking on a toy config (ch. 09) before any real training spend |
| 8 — larger/different model | RC-11 fundamental capability gap | C3–C4 | A pre-registered transfer/ceiling test shows the residual failure is not predictable from anything short of the model's own weights — fine-tuning demonstrably insufficient, not merely untried | The rung's own pre-registered acceptance gate (candidate vs incumbent, frozen, paired, MDE stated, ch. 04/05) returned **CONFIRMED** or **REFUTED**; INCONCLUSIVE does not exhaust the rung | A candidate-characterization pass (ch. 05/06) before committing to a new base model |
| 9 — architectural redesign | RC-12 architecture mismatch | C4 | A staged, one-variable-at-a-time run of the whole ladder (no-model baseline → tools → retrieval → capability-ceiling model → routing → verifier tuning → fine-tune) shows the residual gap tracks the *topology*, not any single component | The redesign's own pre-registered acceptance gate against the incumbent topology returned **CONFIRMED** or **REFUTED** under chapter 04. There is no rung below: a REFUTED result returns the decision to its owner (accept the gap, re-scope the task, or stop), it does not license another descent | Re-run the cheapest end-to-end baseline on the *proposed* topology before redesigning around it |

**Transport-vs-contract discriminator (RC-2 vs RC-4).** Byte-level fidelity is
diagnosed at exactly one rung depending on *where the corruption originates*: when the
serving stack, a proxy, or the serialization layer alters bytes independently of any
tool, it is RC-2 and belongs at **rung 1** — this is the shape [CASE: CASE-008]
teaches. When the payload a tool emits does not match its declared schema, addressing,
ordering, or permission contract, it is RC-4 and belongs at **rung 3**. The
discriminating test is cheap: replay the identical payload through the transport with
the tool held fixed. If the bytes change, it is rung 1's.

Rungs 1–6 **MAY** be locally re-sequenced when a diagnosis clearly identifies the
cause class out of order (chapter 00 P3's override provision); rung 0's priority and
the never-train-around-defects rule are not locally overridable without a written
[method decision record](GLOSSARY.md#method-decision-record). Re-sequencing changes the
*order* in which rungs are worked; it does not waive any rung's exit evidence.

**A dominant cost or time bucket at any rung is a [finding, not automatically
waste](GLOSSARY.md#finding-vs-waste)** (normatively defined in chapter 06, applied
here): before treating a rung's expense as overhead to cut, ask whether it is
task-intrinsic and moves the decision the ladder work serves. If so, it is the object
of study — route it to the diagnostic gate below, not to an optimization backlog.

### 5.2 Diagnostic gates: deciding before you spend

A **[diagnostic gate](GLOSSARY.md#diagnostic-gate)** is a cheap, pre-registered probe
that decides an expensive experiment's fate *before* the expensive experiment runs.
It is the mechanism that makes "earn the cost before you pay it" (§4) executable
rather than aspirational. Design pattern:

1. **Name the hypothesis the expensive experiment assumes.** State it as a claim that
   could be false — e.g., "additional generation budget converts truncated failures
   into passes" (not "let's try a bigger budget and see").
2. **Find the cheapest observable that discriminates it.** Not a proxy that merely
   correlates with success under the current regime (§4) — the actual
   decision-relevant signal. For a budget question, that is *pass rate on the
   deterministic scorer*, not completion rate.
3. **Pre-register decision bands — GO / RE-SCOPE / DROP — with data-sufficiency
   precedence, before running anything.** Fix a minimum sample-sufficiency floor
   (`n_min`). **Size `n_min` from the interval width needed to separate the bands, not
   from a bare count**: the smallest `n` at which the primary metric's 95% interval,
   evaluated at the effect you expect, sits wholly on one side of the GO threshold
   (chapter 04's MDE machinery; §8 works the arithmetic). A floor chosen for
   convenience produces a design that cannot resolve its own bands, which is the
   sub-MDE-promotion anti-pattern (chapter 00 §9) wearing a pre-registration's
   clothes. The precedence rule, applied in order:

   ```
   if reconfirmed_sample < n_min:
       verdict = INCONCLUSIVE / RE-SCOPE, regardless of the point estimate.
       (An underpowered diagnostic tells you the premise is unmeasured,
        not that it is false — it can never license DROP, and a favorable
        point estimate below n_min can never license GO either (§9).)
   else:
       apply the pre-registered effect-size bands (GO / RE-SCOPE / DROP),
       reading each band against the metric's INTERVAL, not its point estimate.
       A band the interval straddles yields INCONCLUSIVE / RE-SCOPE.
   ```

   **Always report the interval alongside the point estimate**, and read the bands
   against it. A diagnostic gate that licenses spend is an inferential device and is
   held to chapter 04's standard. A project **MAY** instead run the gate deliberately
   as a *screening* device — cheaper, and legitimate for ordering candidate
   interventions — but then it **MUST** print its verdict as **RANKED** under chapter
   04's [screening-vs-inference](GLOSSARY.md#screening-vs-inference) rule, still report
   the interval, and attach no inferential claim to the result.

   **Completion alone never produces GO.** A completion-only metric may appear as
   diagnostic context, but only the primary, pre-registered discriminating metric can
   license a GO (§4's completion-is-not-correctness principle, operationalized).
4. **Run it paired and controlled.** Use a [contemporaneous paired
   control](GLOSSARY.md#contemporaneous-paired-control) — both arms in the same
   session/window, everything but the intervention held fixed, order pre-registered
   and counterbalanced ([round-robin ordering](GLOSSARY.md#round-robin-ordering) or
   an explicit AB/BA assignment) — whenever the comparison would otherwise cross a
   measured [reproducibility boundary](GLOSSARY.md#reproducibility-boundary) (chapter
   02). A historical-vs-new comparison cannot carry a causal claim across an
   unmeasured instability boundary.
5. **The diagnostic's verdict is the recommendation that binds, absent a documented
   override.** At stakes tiers 2+, run the diagnostic as a
   [diagnostic run kind](GLOSSARY.md#diagnostic-run-kind) — ledgered inside the
   [fail-closed](GLOSSARY.md#fail-closed) record, cryptographically non-promotable
   (chapter 04's default; the *relaxed lane* that runs a diagnostic outside the
   record is the anti-pattern the record exists to prevent, chapter 00 §9). The bands
   are judgment bands, not a hypothesis test with automatic execution: a human
   decision owner reads the result and, absent a written override, follows the
   pre-registered consequence — exactly the discipline a
   [consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance)
   enforces (chapter 04) [CASE: CASE-001].

This pattern generalizes directly: [CASE: CASE-011] is a diagnostic gate run under this
design — a cheap paired probe with pre-registered bands and a sufficiency floor taking
precedence over the primary metric, deciding a much larger experiment's fate before it
was allowed to run. Read it as the source of the pattern, and apply step 3's interval
requirement to your own instance: whether *any* given probe separates its bands is a
property of that probe's `n` and observed rate, and must be computed, never inherited.

### 5.3 Generation/reasoning-budget calibration (rung 5)

A procedure, not a number to copy from another project or model generation
(§6 — output-length distributions shift across model families and versions; a cap
calibrated on one is not valid evidence for another [CASE: CASE-006]).

1. **Pilot the generation-length distribution on the iterate split.** Record the full
   distribution of tokens actually generated per case, not just the mean.
2. **Set the cap above a pre-registered quantile** (illustrative default: p99) **with
   explicit headroom.** State the quantile and the headroom multiplier in the
   experiment contract; both are project **[PARAMETER]**s calibrated per §6.
3. **Define a truncation-rate tolerance with a named consequence** — ABORT /
   RECALIBRATE / PROCEED-WITH-DECLARED-CEILING (chapter 04) — not a bare "we'll keep
   an eye on it." An untargeted tolerance is the unpriced-escape-hatch anti-pattern
   (chapter 00 §9) applied to budgets.
4. **Persist truncation telemetry** — finish reasons, per-invocation token counts —
   as part of the [telemetry floor](GLOSSARY.md#telemetry-floor) (chapter 12), landed
   *before* the run it would otherwise be reconstructed from.
5. **When truncation still bounds outcomes at the chosen cap, run the diagnostic
   gate (§5.2), not an assumption.** Do not infer that a larger cap will convert
   truncations to passes; measure it on a paired sample before committing to the
   larger budget as a design decision.
6. **State the selection-effect caveat wherever a rescue/conversion rate is
   reported.** Cases that complete inside a smaller budget are systematically the
   easier ones; a rescue rate measured at a larger budget is an upper bound on how
   much of the *harder*, still-truncated population would convert, not a given
   [CASE: CASE-006].

### 5.4 Prompt/workflow optimization discipline (rung 4)

- **One factor per arm.** A variant that changes the prompt *and* the output schema
  *and* the retrieval call is not a controlled comparison; isolate the factor under
  test.
- **Enumerate the hypothesis space before generating variants.** You **SHOULD** list
  the candidate changes and the mechanism each is supposed to fix *before* writing
  them, so the comparison set is a deliberate design, not accumulated trial-and-error.
  Screening/racing discipline (chapter 04's iterate-split, stratum-balanced rungs
  [EXT-STOPPING-003]) applies directly when the variant set is larger than a handful.
- **Pre-register the adoption rule before seeing results** — the margin and the
  metric that would justify keeping a variant — so a fluke result cannot retroactively
  justify itself.
- **A variant that changes the execution system is a new identity** (chapter 02):
  compare it under the same paired-control discipline as any other execution-system
  change, not as a free-form "try it and see."

### 5.5 Quantization acceptance gates (a cross-cutting deployment lever)

*status: doctrine — not yet exercised (see §7 for what validation would look like)*

This playbook has no internal execution record of a quantization acceptance gate. The
recovery-bar *shape* below is adapted from one vendor's demonstrated practice on its
own benchmark suite [NV-QADNEMOTRON-001]; the escalation ladder is inference from that
vendor's stated recovery step [NV-MODELOPTQAD-001]; and the statistical binding in
this subsection is chapter 04's general standard applied here, not a validated
quantization-specific procedure. Treat the bar number as a starting reference to
calibrate (§6), and the procedure as doctrine to be exercised and then revised.

Quantization does not sit *on* the capability ladder — it changes the artifact's
footprint and cost, not the diagnosis. It **MUST NOT** be used to paper over a
capability gap diagnosed elsewhere on the ladder, and it **MUST** be gated by the
same evaluation instrument (chapter 03) you use for every other quality claim, never
by an academic benchmark that is not your task.

**[ADAPT: NV-QADNEMOTRON-001] [ADAPT: NV-MODELOPTQUANT-001]** Recovery-vs-higher-
precision acceptance gate, on your own task evals: define a recovery percentage —

```
recovery% = task_score(quantized artifact) / task_score(higher-precision baseline) × 100
```

as-of 2026-08-21, one vendor's demonstrated practice targets **>99% median recovery**
across a benchmark suite to ship a post-training-quantized (PTQ)-only artifact, and
treats **95–99%** as a *deliberate* PTQ design target — evidence the artifact was
pushed hard enough to bank size/latency gains — when a further recovery stage is
already planned [NV-QADNEMOTRON-001]. This is a demonstrated internal practice from
one vendor's own flagship release, not published doctrine — adopt the *shape* of the
gate (a stated recovery bar, measured on your evals, with an escalation path below
it), and calibrate the bar itself against your own stakes tier (§6).

**The imported number is a different statistic from the one you will compute.** The
vendor's ">99%" is a **median across a benchmark suite** of per-benchmark recovery
ratios — a robust central tendency over many tasks. A project computing recovery on a
*single aggregate task score* is computing one ratio, not the median of many, and a
single ratio carries far more sampling noise than the vendor's median does. If you want
the vendor's statistic, compute per-stratum recovery ratios and take their median (and
report the spread); if you want a single aggregate, say so and set the bar against
*that* statistic's own resolvable margin, below.

**[DECISION GATE] Quantization acceptance is a chapter-04 comparison, not a ratio of
two point estimates.** A ship/no-ship decision on a quantized artifact **MUST** be run
under the same standard as any other adoption decision (chapter 04):

1. **Paired on the same items.** Score the quantized artifact and the higher-precision
   baseline on the *identical* eval items, in a
   [contemporaneous paired control](GLOSSARY.md#contemporaneous-paired-control) design.
   Two separately-collected aggregate scores are not a comparison.
2. **Effective N, not raw N.** Identify the [clustering unit](GLOSSARY.md#clustering-unit)
   (scenario family, document, session), estimate ICC, and carry
   [N_eff](GLOSSARY.md#effective-n) forward — quantization evals are almost always
   clustered.
3. **MDE stated before the run.** Compute the design's
   [MDE](GLOSSARY.md#mde) on the paired difference at α=.05, power .80 (chapter 04 §8).
   If the MDE is larger than the accuracy loss you care about, the design cannot answer
   the question — enlarge it, or re-scope the bar to a margin the design resolves,
   *before* running.
4. **Report an interval.** State a confidence interval on the recovery ratio, or
   equivalently on the paired score difference. A bare "97.0%" is not a result.
5. **Verdict from the closed set.** **CONFIRMED** (the interval clears the
   pre-registered bar), **REFUTED** (the interval falls wholly below it), or
   **[INCONCLUSIVE](GLOSSARY.md#inconclusive)** (the interval spans the bar, or the
   paired difference sits inside the MDE band).

**A recovery point estimate inside the MDE band is INCONCLUSIVE, not a ship.** This is
the specific failure this gate exists to prevent: a 2- or 3-point aggregate difference
read as "97% recovery, close enough" by a design that could not have resolved a 7-point
difference. INCONCLUSIVE **MUST** carry a pre-registered consequence like any other
tolerance (chapter 04): the default **SHOULD** be *do not ship the more aggressive
artifact* — escalate down the ladder below, or enlarge the design — because an
unresolved accuracy question resolves in favour of the incumbent, not the candidate.
§8 works the arithmetic end to end.

**Escalation ladder below the bar** (each step attempted before the next):

1. Disable KV-cache quantization (cheapest reversal; recovers accuracy at some memory
   cost).
2. Partial or mixed precision (quantize fewer layers/tensors).
3. Weight-only quantization alternatives at the same nominal precision.
4. Quantization-aware recovery — as-of 2026-08-21, one vendor names this its
   *recommended* strategy for accuracy recovery after quantization
   [ADAPT: NV-MODELOPTQAD-001].

**Format portability trap** (chapter 02): a quantization format tied to one GPU
generation's numeric hardware support will not execute on a different generation.
**[PRINCIPLE] Quantize for the deployment target, not the development box.**
(strong-evidence, [ADAPT: NV-NVFP4PLAYBOOK-001]) If the artifact might ever run on a
different hardware generation than it was quantized on, choose a portable format even
at some efficiency cost, or plan a re-quantization step per target.

**Vendor decision-page lag — a contradiction kept visible, with a decision rule.**
The same vendor's own "how do I choose a quantization method" decision page recommends
prioritizing an older, higher-precision format first and does not mention the newer
low-precision format at all [NV-MODELOPTQUANT-001]; the vendor's flagship release
demonstrates and recommends that newer format [NV-QADNEMOTRON-001], and the vendor's
own recovery guide references it [NV-MODELOPTQAD-001]. What the ledger supports,
stated exactly: **the flagship demonstration is dated 2026-08-17; the decision page
carries no publication date and still omits the format as of the 2026-08-21
verification.** The size of the lag is therefore *unknown* — the page cannot be dated,
so it cannot be aged. Both are genuine, current vendor sources; they disagree because
they were written for different audiences and are maintained on different cadences.
**Decision rule:** prefer the most recently dated first-party demonstration (a release
blog, benchmark table, or flagship-model writeup) over an undated or older decision
page. Where a page is undated, treat it as **unverifiable for currency** — not as
fresh, and not as stale by an assumed amount — and record the as-of date (or the
absence of one) for whichever source you follow in your own
[method decision record](GLOSSARY.md#method-decision-record).

## 6. Project adaptation parameters

None of the following ship with a universal value — state each one, with its
rationale, in the relevant experiment contract or diagnostic pre-registration.

| Parameter | What it governs | How to set it |
|---|---|---|
| Cost-class units (§5.1) | What "cheap" vs "expensive" means in your accounting | Pick the unit that actually constrains you (engineer-hours, wall clock, priced GPU-hours) and hold it fixed across the ladder |
| Diagnostic decision bands (§5.2 step 3) | GO / RE-SCOPE / DROP thresholds on the primary metric | Derive from what magnitude of effect would actually change the downstream decision — not a round number borrowed from elsewhere |
| Sufficiency floor `n_min` (§5.2 step 3) | Below this, the verdict is INCONCLUSIVE regardless of effect size | Set from the *interval width* needed to separate the GO band from the RE-SCOPE/DROP band at the expected effect (chapter 04's MDE machinery; worked in §8) — never from a bare count or the population's convenient size |
| Budget quantile and headroom multiplier (§5.3 step 2) | Where the generation cap sits relative to the measured length distribution | Higher quantile / larger headroom trades wasted budget for a lower truncation rate; state the trade explicitly |
| Truncation-rate tolerance + consequence (§5.3 step 3) | When a budget is judged to be under-provisioned | Set jointly with the stakes tier — a Tier-3 system tolerates less silent truncation than a Tier-1 exploration |
| Recovery-vs-precision bar (§5.5) | What accuracy loss a quantized artifact may carry | Calibrate to your own task evals and stakes tier; a vendor's demonstrated bar is a starting reference, not a transferable threshold. Set it against a margin your design can actually resolve — if the bar sits inside the design's MDE, the bar is unmeasurable and the gate is decorative |
| Quantization comparison design (§5.5) | N_eff, MDE, and the interval the acceptance gate is read against | Derive as for any adoption decision (chapter 04): clustering unit → ICC → DEFF → N_eff → MDE, pre-registered before the quantized artifact is scored |
| INCONCLUSIVE consequence for quantization (§5.5) | What happens when the recovery interval spans the bar | Pre-register it; the default **SHOULD** be "do not ship the more aggressive artifact" — an unresolved accuracy question resolves in favour of the incumbent |

## 7. Decision gates and stopping conditions

**[DECISION GATE] Rung descent.** Moving to a costlier rung requires the **"Exit
evidence (this rung is exhausted)"** column of §5.1 — *not* the entry column — to be
satisfied for every rung above the target, or an explicit recorded **inapplicability
finding** for that rung (§5.1: entry evidence absent, with the evidence that
established its absence). Reading the entry column as a descent bar is the specific
misreading this split exists to prevent: a rung's entry condition being *false* is
exactly the case where descent is legitimate, so requiring it would block the
legitimate path and license nothing. "We tried the cheap thing once" satisfies neither
column.

For rungs 7–9 the exit bar is the rung's own pre-registered acceptance gate returning
**CONFIRMED** or **REFUTED** under chapter 04. An **INCONCLUSIVE** result at rungs 7–9
does not exhaust the rung and does not license the next descent — it says the design
could not resolve the question, which is a reason to re-scope the design, never a
reason to spend more at the rung below.

**[DECISION GATE] Diagnostic-gate verdict** (§5.2):

```
reconfirmed sample < n_min?
  ├── yes → INCONCLUSIVE / RE-SCOPE (never DROP; never GO)
  └── no  → apply pre-registered effect-size bands to the metric's INTERVAL
              ├── interval wholly ≥ GO threshold     → proceed to the expensive experiment
              ├── interval straddles a band boundary → INCONCLUSIVE / RE-SCOPE:
              │                                        enlarge the sample, or re-scope
              │                                        the bands to a resolvable margin
              ├── interval wholly inside RE-SCOPE    → re-scope the expensive experiment
              │                                        to what the probe shows converts
              └── interval wholly ≤ DROP threshold   → do not run it; move to the next rung
```

**[STOP CONDITION]** A completion-only or otherwise proxy metric is about to license a
GO decision with no primary, pre-registered discriminating metric behind it (§4, §5.2
step 3).

**[STOP CONDITION]** A diagnostic's reconfirmed sample is below its pre-registered
sufficiency floor and the result is being read as DROP evidence anyway. Insufficient
reconfirmation is evidence the *premise is unmeasured*, never evidence the
intervention fails.

**[STOP CONDITION] — the opportunity-cost test for stopping optimization at a rung.**
Stop working a rung and either accept the current gap or descend further when *either*:
(a) the rung's **exit evidence** (§5.1) is satisfied — including a diagnostic gate
(§5.2) showing the rung's headroom is exhausted at the current evidence bar — or (b)
the engineering and evaluation cost of continuing at this rung exceeds the value the
residual gap represents to the decision the work serves — whichever binds first. Case
(b) licenses *stopping work*, not *descending*: descent still requires (a), or a
recorded inapplicability finding, for every rung above the target. Descent past rung 6
to fine-tuning additionally requires the full rung-7 **entry** bar in §5.1: a
taxonomy-identified residual gap, every rung above satisfying its own exit cell (or
recorded inapplicable), data that demonstrably contains the skill, and economics that
close (chapter 11) — never opportunity cost alone.

**[STOP CONDITION]** A quantization recovery figure is about to be read as a pass or a
failure with no N, no interval, and no pre-run MDE behind it (§5.5). A ratio of two
point estimates is not an acceptance test; a recovery estimate whose interval spans the
pre-registered bar is INCONCLUSIVE, and the pre-registered INCONCLUSIVE consequence
applies (§5.5, §6).

**[STOP CONDITION]** A quantized artifact is below its pre-registered recovery bar and
is being shipped anyway without exhausting the escalation ladder (§5.5) or without a
written method decision record documenting the exception.

**Validating §5.5's unexercised doctrine.** The quantization gate carries a
doctrine-not-yet-exercised marker (§5.5). What would retire it: one full execution —
a pre-registered paired comparison with N_eff, MDE, interval and verdict recorded
before the artifact is scored; the observed recovery interval and the verdict it
produced; whether the escalation ladder's steps recovered accuracy in the order stated;
and whether the calibrated bar survived contact with a real deployment decision.
Record the result as a case study and revise this subsection from it.

## 8. Metrics and formulas

**Rescue fraction** (the primary diagnostic-gate metric, §5.2):

```
f_rescue = n_rescue / n_reconfirmed
```
where `n_reconfirmed` is the count of primary-population cases that reconfirm the
triggering condition under the contemporaneous control, and `n_rescue` is the count
of those that pass the deterministic scorer under the treatment. **Undefined, and
reported as UNDEFINED (never coerced to 0), when `n_reconfirmed = 0`.**

`f_rescue` is a proportion, so it carries a proportion's interval. At the small `n` a
cheap diagnostic runs at, use a score (Wilson) interval rather than the Wald form — the
formulary's own caveat retires Wald once `n·p̂` or `n·(1−p̂)` falls below about 10
([references/STATISTICS_FORMULAS.md](references/STATISTICS_FORMULAS.md)):

```
center = (p̂ + z²/(2n)) / (1 + z²/n)
hw     = z/(1 + z²/n) × √( p̂(1−p̂)/n + z²/(4n²) )
95% CI = center ± hw

p̂ = f_rescue (proportion); n = n_reconfirmed (count); z = 1.96 at 95%
```

*Worked example (illustrative, invented numbers).* A primary population of 25 cases
that historically hit a capacity ceiling is re-run under a contemporaneous paired
control. 20 of the 25 reconfirm the ceiling in the new session
(`f_reconfirm = 20/25 = 80%`). Of the 20 reconfirmed cases, the treatment arm (raised
budget) passes the deterministic scorer on 9: `f_rescue = 9/20 = 45%`. The
pre-registered GO band is `f_rescue ≥ 30%`.

The interval decides, not the point estimate. At `p̂=0.45, n=20`:
`center = (0.45 + 0.096)/1.192 = 0.458`; `hw = (1.96/1.192) × √(0.01238 + 0.00240)
= 1.644 × 0.1216 = 0.200` → **95% CI ≈ [25.8%, 65.8%]**. The lower bound sits *below*
the 30% GO threshold, so the interval straddles the band boundary: the verdict is
**INCONCLUSIVE / RE-SCOPE**, not GO. The design cannot separate 45% from 30% at
`n=20` — reading it as GO would promote a sub-resolution margin to a spending decision
(chapter 00 §9).

**Data sufficiency, computed against the band rather than guessed.** Solving the same
interval for the smallest `n` whose lower bound clears 30% at an expected `p̂≈0.45`
gives `n ≈ 40` (at `n=40`, CI ≈ [30.7%, 60.2%]; at `n=35` the lower bound is 29.8% and
still fails). So the correct pre-registered floor here is `n_min ≈ 40` reconfirmed
cases — a floor of `n_min = 12` chosen as a round number would have licensed exactly
the false GO above. Since the primary population is only 25 cases, this design cannot
reach its own floor: the honest moves are to widen the primary population, to
re-scope the GO band to a margin 20 cases can resolve, or to declare the probe a
*screening* device and print **RANKED** with the interval attached and no inferential
claim (§5.2 step 3).

**Overrides are written, never implied.** A decision owner **MAY** override a
pre-registered band, but only via a written override recorded in the diagnostic run's
ledger entry (§5.2 step 5). "Absent contradictory evidence, call it GO" is an unpriced
escape hatch (chapter 00 §9), not an override.

**Selection-effect caveat (mandatory wherever a rescue rate is reported, §5.3 step 6).**
The 45% is conditioned on the 20 cases that *reconfirmed* the ceiling — not on the 25
the expensive experiment would run on, and not on the general population. Cases that
stopped reconfirming are a differently-composed subset, and cases that already complete
inside the smaller budget are systematically the easier ones. Report `f_rescue` as a
rate on the reconfirmed subset with the subset's definition attached; it is an upper
bound on what the harder, still-truncated remainder would convert, never a population
rescue rate [CASE: CASE-006].

**Quantization recovery** (§5.5):
```
recovery% = task_score(quantized) / task_score(higher-precision baseline) × 100
```
*Worked example (illustrative, invented numbers) — the design check comes first.* An
eval suite of 400 items, clustered by scenario family (20 families, m=20 items each),
measured ICC = 0.10 → `DEFF = 1 + (20−1)×0.10 = 2.9` → `N_eff = 400/2.9 ≈ 138`.
Expected paired discordance `pd = 0.10`. Chapter 04's paired MDE:
`MDE ≈ (1.96+0.84) × √(0.10/138) ≈ 0.075` — **this design resolves a 7.5-point paired
difference and no smaller one.**

Now the measurement. Baseline task score 82.0% (328/400); PTQ-only quantized score
79.5% (318/400), scored on the identical items → `recovery = 79.5 / 82.0 × 100 ≈
97.0%`. Paired difference = 2.5 points, with
`SE = √(pd/N_eff) = √(0.10/138) ≈ 0.027` → 95% CI on the difference ≈ **[−2.8, +7.8]
points**, i.e. recovery ≈ **[90.5%, 103.4%]**.

*Verdict:* **INCONCLUSIVE.** The 2.5-point observed difference is well inside the
design's own 7.5-point MDE, and the recovery interval spans both the 99% PTQ-only-ship
bar and the 95% floor of the deliberate-PTQ band. The point estimate "97.0%" looks like
it lands neatly inside the 95–99% band; the design cannot actually place it there. The
pre-registered INCONCLUSIVE consequence applies: do not ship the more aggressive
artifact — take the next escalation step (§5.5), or enlarge the design.

*What "enlarge the design" costs, stated so the trade is visible.* Resolving a
2.5-point paired difference at `pd = 0.10` needs
`N_eff ≥ pd × ((1.96+0.84)/0.025)² ≈ 0.10 × 112² ≈ 1,254` — about 3,600 items at this
DEFF, or the same items redistributed across many more (smaller) clusters, which buys
N_eff far more cheaply than adding items inside the existing 20 families. If neither is
affordable, the honest response is to *change the question*: pre-register a bar at a
margin the affordable design resolves (here, ~7.5 points ≈ a 91% recovery floor) and
accept that finer distinctions are outside this instrument's reach.

**Truncation rate** (§5.3): fraction of invocations whose finish reason indicates the
generation was cut off by the budget rather than completing naturally — computed per
run and tracked against the pre-registered tolerance.

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition: always — these are generically wrong)

- **Completion-as-success proxy**: treating a finished (non-truncated) generation as
  evidence of correctness and letting that alone justify a GO or adoption decision,
  without scoring against ground truth [CASE: CASE-006].
- **Training around a defect at rungs 0–4**: escalating to fine-tuning or a larger
  model when the diagnosed root cause is an instrument, infrastructure, evidence,
  tool-contract, or specification defect. The most expensive rung cannot fix a
  problem a cheaper one owns.
- **Underpowered diagnostic read as GO**: a favorable point estimate from a
  diagnostic gate whose reconfirmed sample is below its pre-registered sufficiency
  floor, treated as license to proceed anyway.
- **Insufficient reconfirmation read as DROP evidence**: treating a low
  reconfirmation rate as proof the intervention does not work, rather than as proof
  the historical premise is unmeasured in the current session.
- **A generation-budget cap copied from another project or an earlier model
  generation**: output-length distributions shift across model families and
  versions; a cap not re-derived from the current artifact's own iterate-split
  distribution is a placeholder wearing a number's clothes [CASE: CASE-006].
- **Variant spam**: generating many prompt/workflow variants without first
  enumerating the hypothesis space each is meant to test, or without a pre-registered
  adoption rule — turns rung 4 into an unstructured search with no fluke guard.
- **Unpriced quantization exceptions**: shipping a quantized artifact below its
  recovery bar without either exhausting the escalation ladder (§5.5) or writing a
  method decision record stating why the exception is acceptable.
- **Recovery percentage as an acceptance test on its own**: reading
  `task_score(quantized)/task_score(baseline)` as pass or fail with no N, no paired
  design, no pre-run MDE, and no interval — then shipping (or rejecting) an artifact on
  a difference the design could never have resolved (§5.5, §8).
- **Importing a vendor's median-across-benchmarks bar as a bar on one aggregate
  score**: the two are different statistics with different noise, and swapping them
  silently makes a loose gate look strict (§5.5).
- **Reading the ladder's entry column as a descent bar**: treating "this rung is
  indicated" as "this rung is exhausted" (§5.1) — it inverts the gate, since a rung's
  entry condition being false is precisely when descending past it is legitimate.
- **Descending on an INCONCLUSIVE result at rungs 7–9**: an unresolved acceptance gate
  says the design could not answer the question, which is a reason to fix the design,
  never a licence to spend at the rung below (§7).
- **Aging an undated source**: assigning a lag or a staleness estimate to vendor
  material that carries no publication date. Undated is *unverifiable for currency* —
  neither fresh nor stale by any stated amount (§5.5).

## 10. Vendor recipes

The quantization acceptance-gate mechanics, the escalation ladder, and the
decision-page-lag contradiction are all treated in full in §5.5 — this section is the
source-attribution summary.

| Vendor material | Verdict | What it supplies | What it omits |
|---|---|---|---|
| [NV-QADNEMOTRON-001] | ADAPT | A demonstrated recovery-bar shape (>99% PTQ-only; 95–99% deliberate) from a real flagship release, as-of 2026-08-21 | It is one vendor's internal practice on its own benchmark suite, not doctrine for yours |
| [NV-MODELOPTQAD-001] | ADAPT | Names quantization-aware recovery as the vendor's recommended top-of-ladder recovery step | No acceptance threshold of its own — pairs with the recovery-bar source above |
| [NV-MODELOPTQUANT-001] | REFERENCE (see §5.5 contradiction) | Batch-size heuristics; an older-format-first bias | Omits the newer low-precision format the vendor's own flagship release uses. **This page carries no publication date — treat it as undatable, and therefore unverifiable for currency** |
| [NV-NVFP4PLAYBOOK-001] | ADAPT | The format-portability trap in concrete form: a format tied to one hardware generation | No acceptance-gate procedure — "we recommend running evaluations" with no threshold |
| [NV-AGENTICBLOGS-001] | ADAPT | The evaluate-first, lightweight-before-training ordering this chapter's rung sequence instantiates | A framework, not a per-rung evidence bar — that is this chapter's addition |
| [NV-MODELOPTRESEARCH-001] | ADAPT | Margin-of-error-by-sample-size tables and a first-N ordering-bias warning, useful when screening many prompt/workflow or quantization variants on a subset | No decision rule for *when* a subset is trustworthy enough to act on — pair with chapter 04's MDE machinery |
| [EXT-FT-001] | FOLLOW | Retrieval/prompt-first evidence for factual/citation tasks, validating rungs 2–4 before rung 7 | Does not address budget, routing, or quantization rungs |
| [EXT-STOPPING-003] | ADAPT | Racing/successive-halving screening discipline (§5.4), reused from chapter 04/05 | Assumes stratum-balanced rungs; does not itself define your adoption rule |

## 11. Worked examples

- [CASE-011](examples/CASE-011_diagnostic-gate.md) — a cheap paired probe,
  pre-registered with data-sufficiency precedence, gated an experiment an order of
  magnitude more expensive than the probe itself.
- [CASE-006](examples/CASE-006_token-budget-confounding.md) — isolating a
  generation-budget factor shrank a claimed model-vs-model gap substantially, and
  surfaced the selection-effect caveat that a completion-based rescue estimate is an
  upper bound, not a given.
- [CASE-001](examples/CASE-001_consequence-bearing-tolerances.md) — the general
  failure mode §5.2 step 5 and §5.3 step 3 exist to close: a detected tolerance
  breach with no named consequence is not a control.
- See §8 for fully worked illustrative-number calculations of the rescue fraction and
  the quantization recovery percentage. Both worked examples end in **INCONCLUSIVE**
  on purpose: they are the two places in this chapter where a plausible-looking point
  estimate is most likely to be promoted past what its design can resolve, so the
  arithmetic that catches it is shown in full.

## 12. Outputs and artifacts

- A **diagnostic-gate pre-registration** (hypothesis, discriminating metric, decision
  bands, sufficiency floor *with the interval-width derivation that produced it*,
  pairing/counterbalancing design, and whether the gate is inferential or a screening
  device printing RANKED) recorded before the probe runs, as a
  [diagnostic run kind](GLOSSARY.md#diagnostic-run-kind) inside the fail-closed record
  (chapters 04, 13).
- A **rung-diagnosis log entry**: the RC class, the rung selected, and — for every rung
  *above* it — the §5.1 **exit evidence** that cleared it or the recorded
  inapplicability finding that excused it. Feeds the [record of
  record](GLOSSARY.md#record-of-record) (chapter 13) and, where an effect was
  predicted in advance, the [prediction ledger](GLOSSARY.md#prediction-ledger)
  (chapter 04).
- A **budget-calibration record**: the measured length distribution, the chosen
  quantile and headroom, the truncation tolerance and its consequence, and
  confirmation that truncation telemetry is live (chapter 12) before the cap is used
  in an experiment that depends on it.
- A **quantization acceptance-gate report**: the pre-run design statement (clustering
  unit, ICC, DEFF, N_eff, MDE, the pre-registered bar and its INCONCLUSIVE
  consequence), then the result — recovery percentage **with its interval** against
  your own task evals, the CONFIRMED / REFUTED / INCONCLUSIVE verdict, which escalation
  step (if any) was needed, and the format-portability check against the deployment
  target.
- Any principle override or vendor-guidance-freshness call, as a [method decision
  record](templates/METHOD_DECISION_RECORD.md).

## 13. Sources

| ID | Role here |
|---|---|
| [NV-AGENTICBLOGS-001] | Evaluate-first, lightweight-before-training ordering this chapter's rung sequence instantiates (verified live 2026-08-21) |
| [NV-QADNEMOTRON-001] | Demonstrated quantization recovery-bar practice (verified live 2026-08-21) |
| [NV-MODELOPTQAD-001] | Quantization-aware recovery named as the vendor's recommended top-of-ladder step (verified live 2026-08-21) |
| [NV-MODELOPTQUANT-001] | The decision-page half of the §5.5 vendor-lag contradiction (verified live 2026-08-21) |
| [NV-NVFP4PLAYBOOK-001] | Format-portability trap (verified live 2026-08-21) |
| [NV-MODELOPTRESEARCH-001] | Progressive-evaluation-subset margin-of-error tables for screening variants (verified live 2026-08-21) |
| [EXT-FT-001] | Retrieval/prompt-first ladder-ordering evidence for rungs 2–4 vs. rung 7 |
| [EXT-STOPPING-003] | Racing/successive-halving screening discipline reused in §5.4 |
| [INT-CASE-011] | Diagnostic-gate case evidence |
| [INT-CASE-006] | Budget-confound and completion-is-not-correctness case evidence |
| [INT-CASE-001] | Consequence-bearing-tolerance case evidence underlying §5.2 step 5 and §5.3 step 3 |

**Gap dispositions in this chapter:** **G14 (finding-vs-waste decision test):
COVERED** — normatively defined in chapter 06; applied here to a rung's dominant cost
bucket (§5.1) and to the stop-optimizing test (§7).

---

> [← Previous](06_INFERENCE_PERFORMANCE_AND_CAPACITY.md) · [Index](README.md) ·
> [Next →](08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md)
