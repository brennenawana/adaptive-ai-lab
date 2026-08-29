# SCENARIO-11: A Diagnostic Gate Before an Expensive Experiment

> [Index](../README.md) · [Examples](README.md)

**An invented scenario.** The project is fictional; the lesson and the reasoning are the
part to take seriously.
**Illustrates:** [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) ·
[07. Optimization and Intervention Ladder](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md)

---

## Situation

A chess site publishes tactics puzzles, and wants each new puzzle rated before it goes
live. The rating job has two parts: name the tactical motif, and place the puzzle in a
difficulty band. The band is checkable — the site already knows, from years of play
data, what share of players solve each puzzle, so the correct band is a fact, not an
opinion. A model that reasons through the position before answering is a natural fit.

A four-candidate model comparison had just finished. It took 24 hours and 3 minutes of
wall clock. Afterwards someone reconstructed where that time actually went, and found
something unpleasant: about 41% of it — 9 hours 55 minutes, spread over 145 puzzles —
had been spent generating reasoning that ran into a fixed 8,192-token ceiling and got
cut off before the model ever wrote an answer. Ten hours of compute. Zero scored
passes from any of it.

The obvious next move was to raise the ceiling and re-measure: do those cut-off
puzzles turn into passes when the model is allowed to think longer? The team costed
that experiment honestly at **18 to 22 hours** of wall clock.

The trouble is that "it just needed more room to think" was a guess. There was a
competing explanation with the same symptom. A model that is stuck — circling the same
three candidate lines, restating the position, going nowhere — also runs out of tokens.
If that was what was happening, raising the ceiling buys longer nonsense, the 18 to 22
hours produce nothing, and a different piece of work (sending easy puzzles to a cheaper
model instead) was the better use of the week.

## Decision faced

Commit 18 to 22 hours on the strength of a plausible but untested story about *why*
those puzzles failed — or spend a small, pre-registered amount first to test the story
directly, and let that result decide.

## Evidence

**The probe was designed in writing before any of its own data existed.** That is the
part that makes it a gate rather than a warm-up. Five things were frozen in the
document:

**Who is in it.** The 15 distinct training-split puzzles where the frozen candidate had
recorded a ceiling-truncated stop during the historical run. The list was pulled from
the run's stored finish reasons and cross-checked against the separate record of that
run's configuration — the two agreed exactly.

**How each puzzle is measured.** Each of the 15 was run twice inside **one** server
session: once at the historical 8,192-token ceiling, once at a raised 16,384-token
ceiling. Both arms, same session, same day, order counterbalanced and written down in
advance — a [paired design](../GLOSSARY.md#paired-design). The reason is not
fastidiousness. This team had already measured its own
[reproducibility boundary](../GLOSSARY.md#reproducibility-boundary) and found what
[SCENARIO-12](SCENARIO-12_restart-instability-paired-controls.md) describes: restarting
the server process alone can flip a meaningful share of per-item outcomes. Comparing
fresh runs against last week's history would have mixed the ceiling change together
with ordinary session-to-session drift, and no arithmetic afterwards can separate them.

**What counts as a decision.** Bands, fixed before data: rescue at least ~30% of the
reconfirmed puzzles → go ahead with the full experiment; a middle band → re-scope it;
under ~10% → drop it and promote the routing work instead.

**What has to be true before the bands are even consulted.** A data-sufficiency floor
took precedence over the primary number: if fewer than 10 of the 15 historical
truncations reproduced in the fresh session, the result was INCONCLUSIVE and the probe
would be re-scoped, *whatever* the rescue rate said. And one inference was ruled out in
advance and permanently: a low reconfirmation count may **never** be read as evidence
to drop the experiment. Few reproductions would mean the historical premise was
unstable — not that extra thinking room fails to help. Writing that down before the
data existed is what keeps it off the table later, when someone is tired and would like
the cheap answer.

**How ambiguous outputs get classified.** A four-way rubric — passed; finished but
wrong; still truncated and converging; still truncated and stuck — decided by
mechanical signals: repetition rate, how much new content appears in the last stretch of
output, how many distinct candidate lines are under consideration, whether the analysis
is still accumulating anything. The rubric was committed to version control before a
single raised-ceiling generation had run.

**The probe's non-goals were stated and held.** No ceiling was to be *selected*, no
contract frozen, no training done, no new evaluation-suite version cut. The 16,384
figure was a diagnostic instrument, not a calibrated choice; the real experiment would
calibrate its own. The probe ran entirely on the training split, spending zero entries
from the [look](../GLOSSARY.md#look) ledger, and was recorded under the project's
diagnostic run kind: ledgered and non-promotable. It can inform a decision. It can
never qualify a model.

## What happened

The probe ran 31 generations — 15 pairs, plus one session-integrity check — in a single
continuous server session, in **2 hours 10 minutes**.

| Measure | Result |
|---|---|
| Historical population | 15 puzzles |
| Reconfirmed at the old ceiling | **15 / 15 (100%)** — every control hit the ceiling again, at the same token count |
| Rescued at the raised ceiling | **9** |
| **Rescue rate** | **9 / 15 = 60%** (95% interval ≈ 41%–85%) |
| Finished but still wrong | 1 (6.7%) |
| Still truncated | 5 — converging: 5, stuck: 0 |
| Pass rate among puzzles that finished | 9 / 10 = **90%** |

The sufficiency floor passed at its maximum: 15 of 15, not the 10 required. So the
bands applied, and 60% cleared the ~30% go-ahead threshold comfortably. The interval
matters as much as the point estimate here — 15 items is not many, and the honest range
around 60% runs from about 41% to about 85%. Even the low end of that range clears the
band. That is what licensed acting on fifteen cases, and it is a calculation you have
to run for your own probe rather than inherit from this one.

Three details sharpened the read rather than merely agreeing with it. Every rescued
puzzle needed **strictly more** than the old ceiling to pass — the tightest by a few
hundred tokens, the loosest by about 3,400. The ceiling was the binding constraint, not
a bystander that happened to correlate with hard puzzles. The nine rescues split almost
evenly across the counterbalanced order, four one way and five the other, so ordering
and prompt caching were not driving the result — though the cache effect *was* plainly
visible in the raw latency of each pair's second arm, which is exactly the confound the
counterbalancing existed to average out. And the frozen rubric fired zero stuck-loop
indicators on the five puzzles still truncated; a human read them afterwards as a check,
never as an override, and agreed on all five — four had already stopped working the
position and started writing their answer.

A separate adversarial pass re-derived every load-bearing number straight from the
primary run records — population, pairing, session identity, ceilings, execution order,
all nine passes — and found nothing that would change the recommendation.

Applying the frozen rule produced one line: **go ahead with the reasoning-budget
experiment.** It went to the human owner as a recommendation, not as a trigger. The
probe's governing document required a hard stop once its report was written, and the
18-to-22-hour experiment needed its own authorization no matter how clean the probe's
numbers looked. A larger descriptive scan over all 145 historically truncated puzzles
was run for context, carried zero decision weight, and was barred in advance from
touching the verdict.

One planned side task — a rented-GPU throughput benchmark meant to ride along the same
week — could not run, because the lab had no rental account. It was written up as an
honest incomplete item rather than skipped quietly or estimated from memory.

## The generic lesson

**Before committing to an expensive experiment whose premise rests on an unverified
story, run a cheap, fully [pre-registered](../GLOSSARY.md#pre-registration)
[diagnostic gate](../GLOSSARY.md#diagnostic-gate) whose only job is to decide that
experiment's fate — with go / re-scope / drop bands fixed before any of the
diagnostic's own data exists to shade them.** Here, roughly two hours decided the fate
of twenty. Five properties are what made it a real gate rather than a ritual:

1. **Finishing is not succeeding.** A gate must never let "the model produced an
   answer" alone produce a go-ahead. Only a task-relevant, checkable outcome validates
   the premise. This probe's one finished-but-wrong puzzle is why that distinction is
   not theoretical.
2. **Data sufficiency outranks the primary metric**, and a shortage of data must never
   be readable as evidence *for* the negative outcome. Freeze that precedence before
   the data lands, and a tempting misreading — "hardly anything reproduced, so the idea
   must be wrong" — is off the table permanently, whether or not the floor ends up
   binding.
3. **If the system has a measured instability boundary, the diagnostic must pair inside
   it** — both arms in one session, order pre-registered — rather than comparing fresh
   results against history. That is a
   [contemporaneous paired control](../GLOSSARY.md#contemporaneous-paired-control),
   and it is the direct consequence of
   [SCENARIO-12](SCENARIO-12_restart-instability-paired-controls.md).
4. **Freeze the rubric for ambiguous outcomes before you see any.** Record a human read
   alongside it as a check, never instead of it. That converts a judgment call into an
   auditable procedure that existed before the thing it judged.
5. **A diagnostic gate produces a recommendation, not an action.** The larger spend
   stays with the person accountable for it, even when the probe's numbers are
   unambiguous.

### How this lands on your project

Look at the biggest thing on your plan for the next fortnight and ask what has to be
true for it to be worth doing. Usually there is exactly one load-bearing assumption,
and usually it is a story about *why* something is failing. Then ask what the cheapest
honest test of that one assumption would cost. If the answer is under a tenth of the
main job, you have found a gate worth running — and the discipline that makes it worth
anything is writing down the numbers that would make you drop the main job, *before*
you run the probe. A probe designed after you know the result is just the expensive
experiment with extra steps.

## What would NOT have worked

- **Committing straight to the 18-to-22-hour experiment on the plausible story alone.**
  The probe existed because "it probably just needed more room to think" was untested,
  and the credible alternative would have made the whole spend worthless.
- **Reading the completion rate as the signal.** One puzzle finished and was still
  wrong. Under a completion-based rule that puzzle counts as a win, and the gate is
  measuring the wrong thing.
- **Comparing fresh runs against the historical ones without a same-session pair.** The
  measured restart instability would have been folded into the effect and could not be
  separated out afterwards.
- **Treating a low reconfirmation count as permission to drop the experiment.** The
  frozen rule forbade that inference outright. The floor did not end up binding — 15 of
  15 reproduced — which is exactly when it is cheapest to notice that the rule was
  right to exist.
- **Quietly dropping the benchmark that could not run.** It went into the record as an
  incomplete work package, so the next reader knows it is missing rather than assuming
  it was fine.

## References

- [SCENARIO-12](SCENARIO-12_restart-instability-paired-controls.md) — the
  reproducibility measurement that forced the same-session paired design used here.
- [NV-AGENTICBLOGS-001] "Mastering Agentic Techniques" — evaluate-first ordering, and
  verifiable success over surface completion.
- [EXT-TESTBED-001] Karpathy's neural-net sanity-gate recipe — correctness-only gates
  run before anything scales up.
- [EXT-STOPPING-002] Lan & DeMets; adaptive clinical-trial design — pre-registered rules
  executed mechanically rather than by investigator judgment in the moment.
- Governing chapters: [04](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md),
  [07](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md).
- Glossary: [diagnostic gate](../GLOSSARY.md#diagnostic-gate),
  [pre-registration](../GLOSSARY.md#pre-registration),
  [paired design](../GLOSSARY.md#paired-design),
  [contemporaneous paired control](../GLOSSARY.md#contemporaneous-paired-control),
  [look](../GLOSSARY.md#look).

---

> [Index](../README.md) · [Examples](README.md)
