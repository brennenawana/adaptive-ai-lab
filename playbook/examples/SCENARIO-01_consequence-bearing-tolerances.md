# SCENARIO-01: Consequence-Bearing Tolerances

> [Index](../README.md) · [Examples](README.md)

**An invented scenario.** The project is fictional; the lesson and the reasoning are the
part to take seriously.
**Illustrates:** [00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) ·
[04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) ·
[07. Optimization and Intervention Ladder](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md)

---

## Situation

A farm-equipment dealership runs a service-diagnosis assistant for its technicians. A
technician types the symptom — *"combine loses hydraulic pressure after twenty minutes,
no fault code"* — and the assistant reads the machine's service bulletins and writes a
numbered diagnostic plan, each step citing the bulletin it came from. The plans are long.
A thorough one runs several thousand tokens.

The team was in its second evaluation round, comparing four locally hosted candidate
models. One was new: a 27B dense open-weights model, quantized to fit the shop's single
16 GiB accelerator.

Any long-output system needs a **generation cap** — the most tokens the model is allowed
to produce before the runner cuts it off. Set it too low and correct answers get sliced
off mid-sentence and scored as failures. Set it too high and every run burns wall-clock
time nobody needed to spend. So the cap is a real experimental parameter, and the round's
frozen [experiment contract](../GLOSSARY.md#experiment-contract) pre-registered how to
choose it, before anyone touched the validation or test splits:

- Run a 40-case pilot on the training split — stratified across the 10 fault families,
  four cases each — once, at the manifest ceiling of 6,144 tokens. Greedy decoding, fixed
  seed. A shorter cap's output is a prefix of the ceiling run's output, so one run at the
  ceiling settles every smaller cap.
- For each candidate cap `c` in `{2048, 4096, 6144}`, count the pilot cases that hit it:
  output length ≥ `c`, or the runner stopping for length.
- Require at most **3 of 40** cases capped (≤ 7.5%).
- Freeze the smallest cap that meets that tolerance.

And then one more clause, written in good faith at contract time: *"if no cap meets the
tolerance, freeze 6144 and record the truncation rate."*

That clause is what this scenario is about.

## Decision faced

A pre-registered tolerance had been breached. Could it be allowed to resolve itself by
falling through to a pre-written default — freeze the ceiling, note the number, carry on?
Or did a breach that size have to force somebody to make an explicit, priced decision:
abort the candidate, recalibrate the pilot, or proceed with the cost stated in advance?

The timing is what makes this expensive. The cap was frozen *before* the round's two
costliest phases ran on it.

## Evidence

The pilot's cap table for the selected quantization:

| cap | pilot cases capped (of 40) | rate |
|---|---|---|
| 2048 | 35 | 87.5% |
| 4096 | 27 | 67.5% |
| 6144 | 18 | 45.0% |

No cap met the ≤ 3/40 tolerance. Not one, not close.

Note what did *not* go wrong here. There was no bug. There was no contract violation. The
rule fired exactly as written, hit its escape hatch exactly as written, and froze cap
6,144 with the 45.0% truncation rate recorded — as designed.

The size of the breach is worth stating plainly, because it is easy to skim past a
percentage. Eighteen actual cap-hits against a ceiling of three is a **6× breach** on the
pilot's own units: 45.0% against a 7.5% bar. Detection was never the gap. The tolerance
detected the problem perfectly. It just had no consequence attached to the detection.

## What happened

The round proceeded automatically at cap 6,144, through validation and test, on the frozen
configuration. And the pilot had not been a fluke — truncation was this candidate's
steady-state failure shape:

| split | cap-hits with no scorable answer | share of that split's failures |
|---|---|---|
| training pilot (40) | 18 (45.0%) | — |
| validation (60) | 28 (46.7%) | 28 of 30 |
| test (120) | 57 (47.5%) | 57 of 59 |

Across the whole round, the performance autopsy measured 19h 40m of wall clock. Of that,
**7h 52m — about 40% — was cap-hit generation that scored zero. 103 cases, 0 passes.** The
27B model decoded at roughly 26 tokens per second and accounted for 62% of the round's
wall clock on its own.

None of this made it a bad candidate. It qualified. Under the project's unchanged
deterministic verifier gate it became the strongest local substrate the team had measured:
98 of 120 on the cascade, and only 3 test answers that were confidently wrong while
looking perfectly clean — [silent failures](../GLOSSARY.md#silent-failure) — against the
incumbent's 29. The decision to proceed may well have been the right one.

The defect is not that the round proceeded. **It is that proceeding happened without
anyone deciding to pay for it.** Those 7h 52m were real compute, spent on a configuration
everyone could see was truncating at six times the pre-registered limit, and no human ever
had to write down that cost before it was spent.

The fix adopted afterward was not "add a stopping rule." It was narrower than that, and it
closed the specific hole the escape hatch left open. Every pre-registered tolerance now
names its breach consequence, chosen from three:

- **ABORT** — the candidate leaves the round.
- **RECALIBRATE** — the pilot is redesigned, and the redesign's own cost is stated.
- **PROCEED-WITH-DECLARED-CEILING** — go ahead, with the projected cost written down
  *before* proceeding.

The runner enforces this itself. A tolerance with no consequence written next to it now
refuses to start — the same way the runner already refuses to start when the requested
execution system does not match the manifest. The check defaults to stopping rather than
to continuing, which is what [fail-closed](../GLOSSARY.md#fail-closed) means. A tolerance
is no longer allowed to resolve into a default. It has to resolve into a decision.

## The generic lesson

**A pre-registered threshold with no named breach consequence is an unpriced escape
hatch.** It will fire exactly as designed and still let an arbitrarily large breach
through — because "record it and continue" is itself a consequence. It is just one nobody
chose.

That is the whole trap. Writing the threshold *feels* like installing a control. It isn't.
A threshold is a detector. A control is a detector plus a consequence, and the consequence
has to be picked while you still don't know which way the number will land. Pick it
afterward and you are no longer setting a policy, you are rationalizing a result.

A [consequence-bearing tolerance](../GLOSSARY.md#consequence-bearing-tolerance) closes
this by requiring one of three named outcomes for every calibration or qualification
parameter, decided before the breach is observed: ABORT, RECALIBRATE, or
PROCEED-WITH-DECLARED-CEILING with its cost stated in writing.

This is not heavier process for its own sake. The tolerance in this scenario already
existed and already ran correctly. The fix adds **one sentence per tolerance** — and then
makes the runner, rather than a reviewer's memory, the thing that stops an unpriced
proceed.

This is why chapter 00's [never-skippable floor](../GLOSSARY.md#never-skippable-floor)
carries "predeclare consequences for decision-driving thresholds and tolerances" at every
stakes tier, and why the experiment-contract template in chapter 04 requires a consequence
column on every calibration rule, with the note that *a tolerance without a consequence
fails contract review*. It also grounds rung 5 of the
[intervention ladder](../GLOSSARY.md#intervention-ladder) in chapter 07. A capacity
parameter like a generation cap is exactly the kind of tolerance this discipline targets,
because a truncation breach is silent and cumulative rather than a single visible crash.

## What would NOT have worked

**A generic stopping rule would not have saved much, and reaching for one is itself the
anti-pattern.** The instinct is obvious: "if we'd cut the arm short automatically, we'd
have saved most of that 7h 52m." Replaying the real data says otherwise.
[Certainty curtailment](../GLOSSARY.md#certainty-curtailment) only fires on *hopeless*
arms — arms that can no longer reach their bar no matter what the remaining cases do. This
candidate was sitting near its qualification bar, not hopeless. Replayed against the
actual test arms, curtailment's measured saving was **0.4h of 19h 40m, about 2%** — not
the ~8h the instinct promises. The waste was a decision-quality problem, not a
futility-detection problem. A stopping rule adopted to fix it would have been solving the
wrong problem while looking like progress.

**A sequential test fares worse.** The natural upgrade is a sequential probability ratio
test that watches the pilot case by case and stops as soon as the evidence is decisive.
Replayed on the four real pilot sequences, it wrongly accepted the null at case 10 on an
arm that finished at 11/40 capped, and never fired at all on an arm that finished at 5/40.
The reason is structural: cap-hits are clustered by fault family (measured
[ICC](../GLOSSARY.md#icc) 0.36) and the pilot was ordered in family blocks, so consecutive
cases are not independent draws. That inflates the test's nominal 5% error rate to roughly
12%. [Sequential-rule admissibility](../GLOSSARY.md#sequential-rule-admissibility) fails
here, and [curtailed exact counting](../GLOSSARY.md#curtailed-exact-counting) — halt at the
4th cap-hit, an exact count that makes no distributional claim at all — dominates it on
this data.

**"Just raise the cap" is not a free recalibration either.** At the frozen context length,
the 27B model already occupies 15.1–15.2 GiB of the 16 GiB accelerator with an 8-bit KV
cache. A larger cap may not fit at all without giving something else up. That is precisely
why RECALIBRATE has to be a named, costed option rather than an assumed one — the obvious
remedy has its own price, and that price also needs writing down before it is chosen.

**How this lands on your project.** Open the document where your thresholds live — the
experiment contract, the eval config, the runbook, the Slack thread that stands in for
all three. For each number in it, read the sentence immediately after. If that sentence
says what happens when the number is breached, and names who pays, you have a control. If
it says "log a warning," "record the rate," "flag for review," or nothing at all, you have
a detector with a default attached, and the default will win. Pick ABORT, RECALIBRATE, or
PROCEED-WITH-DECLARED-CEILING for each one today, while you still don't know which way the
number will land. Then make something other than your own memory enforce it.

## References

- [EXT-STOPPING-001] Wald SPRT / always-valid sequential testing — the rejected
  alternative; dominated by curtailed exact counting on clustered pilot data of this
  shape.
- [EXT-STOPPING-002] Lan & DeMets; clinical-trial adaptive-design pre-specification — the
  general principle consequence-bearing tolerances instantiate: pre-register the
  adaptation *rule*, never the outcome.
- Governing chapters: [00](../00_PRINCIPLES_AND_SCOPE.md),
  [04](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md),
  [07](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md).
- Glossary: [consequence-bearing tolerance](../GLOSSARY.md#consequence-bearing-tolerance),
  [curtailed exact counting](../GLOSSARY.md#curtailed-exact-counting),
  [certainty curtailment](../GLOSSARY.md#certainty-curtailment),
  [sequential-rule admissibility](../GLOSSARY.md#sequential-rule-admissibility),
  [fail-closed](../GLOSSARY.md#fail-closed),
  [intervention ladder](../GLOSSARY.md#intervention-ladder),
  [never-skippable floor](../GLOSSARY.md#never-skippable-floor).
- Related: [SCENARIO-02](SCENARIO-02_clustered-eval-effective-n.md) — the same clustering
  that breaks the sequential test above also decides what a suite can resolve at all.

---

> [Index](../README.md) · [Examples](README.md)
