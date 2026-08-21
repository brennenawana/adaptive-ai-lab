# CASE-011: A Diagnostic Gate Before an Expensive Experiment

> Real empirical case from the FIS project (Fintech Integration Sandbox), a
> realistic synthetic fintech-operations laboratory used to develop this
> playbook's methodology.

**Source ID:** INT-CASE-011 · **Date range:** 2026-08-19 – 2026-08-21 · **Cited by:**
[04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) ·
[07. Optimization and Intervention Ladder](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md)

## Situation

A forensic reconstruction of a completed 24 h 03 m, four-candidate model-comparison
milestone (R6) found that 41% of its wall clock — 9 h 55 m across 145 cases — had
been spent generating reasoning that hit a fixed 8,192-token cap and was truncated
before an answer could be scored: **zero passes** from that time. The autopsy's
top-ranked recommended next step was a reasoning-budget calibration experiment
("R7"): raise the cap, re-measure, and see whether the truncated cases convert to
passes. Its own honest cost estimate was **18–22 hours of wall clock**. But whether
raising the cap would actually rescue those cases, versus merely produce longer
unconverged output, was an untested hypothesis — a plausible competing explanation
(the reasoning was degenerate or looping, not budget-starved) would make R7's entire
premise false and its 18–22 hours a waste, with a different next milestone (routing
economics) more valuable instead.

## Decision faced

Commit the 18–22 hours to the reasoning-budget experiment on the strength of a
plausible but unverified hypothesis about *why* the cases were failing — or spend a
small, pre-registered amount first to test the hypothesis directly, and let that
result decide.

## Evidence

**The diagnostic milestone was designed, in writing, before any of its own data
existed.** Its governing document froze, in advance: a primary population of the
**15 distinct TRAIN cases** where the frozen candidate execution system itself had
produced a cap-truncated stop on the historical run (independently cross-checked
against the registry's own frozen calibration record — an exact match); a
**contemporaneous, same-session [paired design](../GLOSSARY.md#paired-design)** —
each of the 15 cases run twice, once at the historical cap and once at a raised,
fit-certified cap, inside **one** server session, in a pre-registered counterbalanced
order — because the project's own prior measurement had shown case outcomes can flip
across a mere server restart, so a historical-vs-new comparison across sessions
would have confounded the cap change with ordinary session instability
[CASE: CASE-012]; and a fully specified go/re-scope/drop decision rule, with
numeric bands fixed before inference began.

**The decision rule had explicit precedence built in.** Before the primary metric
(rescue rate) was even consulted, a **data-sufficiency gate** had to pass: if fewer
than 10 of the 15 historical cap-hits reconfirmed in the new session, the result was
defined as INCONCLUSIVE/RE-SCOPE *regardless of the rescue rate* — and, critically,
was pre-declared as something that could **never** be read as evidence to drop the
follow-on experiment (a low reconfirmation count means the historical premise itself
is unstable, not that extra budget fails to help). Only once that gate passed did
frozen bands apply to the primary metric: material rescue (≥ ≈30% of reconfirmed
cases) → strong go-ahead; a middle band → re-scope; low rescue (< ≈10%) → drop the
follow-on experiment and promote a different milestone instead. A separate rubric
for classifying ambiguous outcomes (four categories: passed, completed-but-wrong,
still-truncated-but-converging, still-truncated-and-degenerate) was itself frozen
and committed to version control **before any treatment-arm data existed**, using
mechanical signals (repetition rate, tail-content novelty, distinct-hypothesis
count, evidence accumulation) rather than post-hoc judgment.

**The diagnostic's own non-goals were stated up front and held.** No cap was to be
*selected*, no contract frozen, no fine-tuning performed, no new evaluation-suite
version cut, no hardware purchased — the raised cap used in the probe was explicitly
a diagnostic instrument, not a calibrated choice; the real experiment, if it ran,
would perform its own calibration under its own contract. The probe also spent
**zero entries** of the project's held-out-evidence [look](../GLOSSARY.md#look)
ledger: it ran entirely on the TRAIN split, preserving DEV/TEST exposure for the
real experiment.

## What happened

The paired probe ran 31 generations (15 pairs plus one session-integrity check) in
one continuous server session over ≈3 hours of wall clock.

| Metric | Result |
|---|---|
| Historical population (`n_hist_cap`) | 15 |
| Reconfirmed at the historical cap (`n_control_reconfirmed`) | **15/15 (100%)** — every control reproduced the cap-hit at exactly the historical token count |
| Rescues at the raised cap (`n_rescue`) | **9** |
| **Primary rescue rate (`f_rescue`)** | **9/15 = 60%** |
| Completed but still wrong (`n_wrong_complete`) | 1 (6.7%) |
| Still truncated at the raised cap | 5 — classified **convergent: 5, degenerate: 0** |
| Pass rate given completion | 9/10 = **90%** |

The data-sufficiency gate passed at its maximum (15 of 15, not merely the required
10), so the bands applied directly: 60% cleared the ≈30% strong-go-ahead threshold
by a wide margin. Several details sharpened the read rather than just confirming
the headline number. Every single rescue needed **strictly more** than the
historical cap to pass — the smallest rescued case needed several hundred tokens
beyond it, the largest needed roughly 3,400 tokens beyond it — showing the budget
was the *binding* constraint, not an incidental correlate. The 9 rescues split
almost evenly across the pre-registered counterbalanced order (4 vs. 5), so no
ordering or prompt-cache artifact was driving the result, even though the expected
cache effect *was* visible in raw latency on the second arm of each pair — exactly
the confound the counterbalancing existed to average out. The frozen mechanical
rubric fired zero degenerate-loop indicators on all five still-truncated cases, and
an independently recorded manual read — performed as a check after the rubric ran,
never used to override it — agreed with it on all five: four of the five had already
left their reasoning and begun constructing their final answer.

A separate, independent adversarial pass re-derived every load-bearing number
directly from the primary database record — population, pairing, session identity,
caps, execution order, all nine passes — and returned a verdict of no defect found
that would change the recommendation.

Applying the frozen rule mechanically produced one row: **strong go-ahead for the
reasoning-budget experiment**, recorded as a *recommendation to the human scientific
owner* rather than an autonomous trigger — the diagnostic's own governing document
required a hard stop once its report was written, with the follow-on experiment
needing its own separate authorization regardless of the diagnostic's result. A
secondary, zero-decision-weight scan of a much larger historical population (145
known truncated cases) was run purely for descriptive context and was explicitly
barred, by the same pre-registration, from influencing the verdict.

One planned work package — a small rented-GPU benchmark, meant to ride along on the
same milestone — could not execute (no rental credentials existed in the lab
environment) and was recorded as an honest incomplete item rather than skipped
silently or approximated [CASE: CASE-005].

## The generic lesson

**Portable rule: before committing to an expensive experiment whose premise rests
on an unverified hypothesis, run a cheap, fully [pre-registered](../GLOSSARY.md#pre-registration)
[diagnostic gate](../GLOSSARY.md#diagnostic-gate) designed explicitly to decide
that experiment's fate — with go/re-scope/drop bands fixed in advance, before any
of the diagnostic's own data exists to shade them.** Five properties made this
instance load-bearing rather than a formality:

1. **Completion is not success; a diagnostic gate must never let completion alone
   produce a go-ahead.** Only a task-relevant, deterministic outcome (here: a
   scorer pass) validates the premise — this case's one wrong-but-complete result
   kept that distinction from being theoretical.
2. **Data sufficiency has precedence over the primary metric**, and poor
   sufficiency must never be interpretable as evidence *for* the negative outcome.
   Freezing this precedence before data existed keeps a plausible misreading ("few
   cases reconfirmed, so the hypothesis must be wrong") permanently off the table,
   whether or not the gate ends up binding.
3. **When the underlying system has a measured instability boundary, a diagnostic
   comparing an intervention to history must use a [contemporaneous paired
   control](../GLOSSARY.md#contemporaneous-paired-control) within one session**,
   not a before/after comparison across sessions — reusing the reproducibility
   finding of [CASE: CASE-012].
4. **Freeze the rubric for ambiguous outcomes before seeing the data**, and record
   an independent manual read *alongside* it, never instead of it, as a check —
   this converts a judgment call into an auditable, pre-committed procedure.
5. **A diagnostic gate produces a recommendation, not an autonomous action** — the
   larger follow-on spend stays with the accountable owner even when the
   diagnostic's numbers are unambiguous.

Point 1 corroborates the general "evaluate before you invest, and measure
verifiable success over surface completion" ordering documented independently in
agentic-system engineering practice [NV-AGENTICBLOGS-001]; the broader pattern of a
correctness-only sanity gate run before any expensive scale-up is likewise
consensus practice outside this project [EXT-TESTBED-001]. Point 5 — a pre-declared
rule executed mechanically rather than by after-the-fact investigator judgment — is
the same discipline documented for interim analyses in clinical-trial adaptive
design [EXT-STOPPING-002]. This case is why chapter 07 defines the diagnostic gate
as a named step on the [intervention ladder](../GLOSSARY.md#intervention-ladder)
before descending to the next rung, and why chapter 04 requires every
consequence-bearing threshold — including a diagnostic's own go/re-scope/drop
bands — to name its consequence and its data-sufficiency precedence before any data
collection begins.

## What would NOT have worked

- **Committing straight to the 18–22 hour experiment on the plausible-sounding
  hypothesis alone:** the diagnostic existed because "it probably just needed more
  budget" was untested, and the credible alternative (degenerate looping) would
  have made the full spend worthless if true.
- **Reading raw completion rate as the decision signal:** the wrong-but-complete
  case shows why the frozen rule barred completion from producing a go-ahead alone.
- **A historical-vs-new comparison without a same-session paired control:** the
  project's own measured restart instability would have confounded the budget
  change with ordinary session-to-session noise.
- **Treating a low reconfirmation count as license to drop the follow-on
  experiment:** the frozen rule explicitly forbids this inference — the actual
  result (maximum possible reconfirmation) shows the gate mattering as designed
  even though it did not end up binding.
- **Silently skipping or approximating the missing rented-GPU benchmark:** it was
  recorded as an honest incomplete work package instead.

## References

- [CASE: CASE-012] Restart instability and paired controls — the reproducibility
  measurement that motivated the same-session paired-control design used here.
- [CASE: CASE-005] Hardware purchase discipline — the companion work package (the
  rented-GPU benchmark) that could not execute and was recorded incomplete.
- [NV-AGENTICBLOGS-001] NVIDIA, "Mastering Agentic Techniques" — evaluate-first
  ordering and verifiable success over surface completion.
- [EXT-TESTBED-001] Karpathy, neural-net sanity-gate recipe — correctness-only
  gates before scaling up.
- [EXT-STOPPING-002] Lan & DeMets; adaptive clinical-trial design — pre-registered
  rules executed mechanically rather than by investigator judgment.
- Governing chapters: [04](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md),
  [07](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md).
- Glossary: [diagnostic gate](../GLOSSARY.md#diagnostic-gate),
  [pre-registration](../GLOSSARY.md#pre-registration),
  [paired design](../GLOSSARY.md#paired-design),
  [contemporaneous paired control](../GLOSSARY.md#contemporaneous-paired-control),
  [look](../GLOSSARY.md#look).
