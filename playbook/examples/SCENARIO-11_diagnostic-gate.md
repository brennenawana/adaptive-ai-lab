# SCENARIO-11: A Diagnostic Gate Before an Expensive Experiment

> [Index](../README.md) · [Examples](README.md)

**An invented scenario.** The project is fictional; the lesson and the reasoning are the
part to take seriously.
**Illustrates:** [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) ·
[07. Optimization and Intervention Ladder](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md)

---

## Situation

Two readings of the same ten hours of compute. One: the model ran out of room to think,
and giving it more turns those failures into passes. The other: the model was going
nowhere — circling the same three candidate lines, restating the position — and more room
buys longer nonsense. Nothing in the evidence separates them, because a model that is
stuck and a model that is merely slow run out of tokens in exactly the same way.

Those hours came out of a four-candidate model comparison at a chess site that publishes
tactics puzzles and wants each new one rated before it goes live. The rating job has two
parts: name the tactical motif, and place the puzzle in a difficulty band. The band is
checkable — the site knows from years of play data what share of players solve each
puzzle, so the correct band is a fact, not an opinion. A model that reasons through the
position before answering is a natural fit.

The comparison cost 24 hours and 3 minutes of wall clock. Afterwards someone reconstructed
where that time actually went, and found something unpleasant: about 41% of it — 9 hours
55 minutes, spread over 145 puzzles — had gone into reasoning that ran into a fixed
8,192-token ceiling and was cut off before the model ever wrote an answer. Ten hours of
compute. Zero scored passes from any of it.

The obvious next move was to raise the ceiling and re-measure: do those cut-off puzzles
turn into passes when the model is allowed to think longer? That experiment was costed
honestly at **18 to 22 hours** of wall clock. And if the second reading is the right one,
those 18 to 22 hours produce nothing, and a different piece of work — sending easy puzzles
to a cheaper model — was the better use of the week.

## Decision faced

Commit 18 to 22 hours on the strength of a plausible but untested story about *why*
those puzzles failed — or spend a small, pre-registered amount first to test the story
directly, and let that result decide.

## Evidence

**The probe was designed in writing before any of its own data existed.** That is the
part that makes it a gate rather than a warm-up. The document froze all of this:

**Who is in it.** The 15 distinct training-split puzzles where the model under test, at
the pinned configuration that run used, had stopped by hitting the ceiling — pulled from
the run's stored finish reasons, and cross-checked against the separate record of that
run's configuration, which agreed exactly.

**How each puzzle is measured.** Each of the 15 was run twice inside **one** server
session: once at the historical 8,192-token ceiling, once at a raised 16,384-token
ceiling. Both arms, same session, order counterbalanced and written down in advance — a
[paired design](../GLOSSARY.md#paired-design). This team had already measured how far
its own results could be trusted to repeat — its
[reproducibility boundary](../GLOSSARY.md#reproducibility-boundary) — and found what
[SCENARIO-12](SCENARIO-12_restart-instability-paired-controls.md) describes: a server
restart alone can flip a meaningful share of per-item outcomes. Comparing fresh runs
against last week's history would have mixed the ceiling change with ordinary
session-to-session drift, and no arithmetic afterwards separates the two.

**What counts as a decision.** Bands, fixed before data: rescue at least ~30% of the
reconfirmed puzzles → go ahead with the full experiment; a middle band → re-scope it;
under ~10% → drop it and promote the routing work instead.

**What has to be true before the bands are even consulted.** A data-sufficiency floor
outranked the primary number: if fewer than 10 of the 15 historical truncations
reproduced in the fresh session, the result was INCONCLUSIVE and the probe would be
re-scoped, *whatever* the rescue rate said. One inference was also ruled out in advance,
permanently: a low reconfirmation count may **never** be read as evidence to drop the
experiment. Few reproductions would mean the historical premise was unstable — not that
extra thinking room fails to help. Writing that down before the data existed keeps it
off the table later, when someone is tired and would like the cheap answer.

**How ambiguous outputs get classified.** A four-way rubric — passed; finished but
wrong; still truncated and converging; still truncated and stuck — decided by mechanical
signals: repetition rate, how much new content appears in the last stretch of output, how
many candidate lines are still in play. It was committed to version control before a
single raised-ceiling generation had run.

**What the probe was not allowed to do.** No ceiling was to be *selected*, no contract
frozen, no training done, no new evaluation-suite version cut. The 16,384 figure was a
diagnostic instrument, not a calibrated choice. The probe ran entirely on the training
split, spending zero entries from the [look](../GLOSSARY.md#look) ledger, and was
recorded as a diagnostic run: logged like every other run, and permanently marked as
something that can inform a decision but can never qualify a model.

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

The sufficiency floor passed at its maximum: 15 of 15, not the 10 required. So the bands
applied, and 60% cleared the ~30% go-ahead threshold comfortably. The interval matters
as much as the point estimate here. Fifteen items is not many, and the honest range
around 60% runs from about 41% to about 85% — but even its low end clears the band. That
is what licensed acting on fifteen cases, and it is a calculation to run for your own
probe, never inherited from this one.

Three details sharpened the read rather than merely agreeing with it. Every rescued
puzzle needed **strictly more** than the old ceiling to pass — the tightest by a few
hundred tokens, the loosest by about 3,400 — so the ceiling was the binding constraint,
not a bystander that happened to correlate with hard puzzles. The nine rescues split
almost evenly across the counterbalanced order, four one way and five the other, so
ordering and prompt caching were not driving the result; the cache effect *was* plainly
visible in each pair's second-arm latency, which is exactly the confound the
counterbalancing existed to average out. And the frozen rubric fired zero stuck-loop
indicators on the five puzzles still truncated. A human read those five afterwards as a
check, never as an override, and agreed on all of them: four had already stopped working
the position and started writing their answer.

A separate adversarial pass re-derived every load-bearing number straight from the
primary run records — population, pairing, session identity, ceilings, execution order,
all nine passes — and found nothing that changed the recommendation.

Applying the frozen rule produced one line: **go ahead with the reasoning-budget
experiment.** It went to the human owner as a recommendation, not as a trigger. The
probe's governing document required a hard stop once its report was written, and the
18-to-22-hour experiment needed its own authorization however clean the probe looked. A
descriptive scan over all 145 historically truncated puzzles ran for context, carried
zero decision weight, and was barred in advance from touching the verdict.

## The generic lesson

**Before committing to an expensive experiment whose premise rests on an unverified
story, run a cheap, fully [pre-registered](../GLOSSARY.md#pre-registration)
[diagnostic gate](../GLOSSARY.md#diagnostic-gate) whose only job is to decide that
experiment's fate — with go / re-scope / drop bands fixed before any of the
diagnostic's own data exists to shade them.** Here, roughly two hours decided the fate
of twenty. Five properties are what made it a real gate rather than a ritual:

1. **Finishing is not succeeding.** A gate must never let "the model produced an
   answer" alone produce a go-ahead. Only a task-relevant, checkable outcome validates
   the premise. The one finished-but-wrong puzzle is why that distinction is not
   theoretical.
2. **Data sufficiency outranks the primary metric**, and thin data must never be
   readable as evidence *for* the negative outcome. Freeze that precedence before the
   data lands and a tempting misreading — "hardly anything reproduced, so the idea must
   be wrong" — is off the table permanently.
3. **If the system has a measured instability boundary, the diagnostic must pair inside
   it** — both arms in one session, order pre-registered — rather than comparing fresh
   results against history. That is a
   [contemporaneous paired control](../GLOSSARY.md#contemporaneous-paired-control),
   and it follows directly from
   [SCENARIO-12](SCENARIO-12_restart-instability-paired-controls.md).
4. **Freeze the rubric for ambiguous outcomes before you see any.** Record a human read
   alongside it as a check, never instead of it. That turns a judgment call into a
   procedure that existed before the thing it judged.
5. **A diagnostic gate produces a recommendation, not an action.** The larger spend
   stays with the person accountable for it, even when the numbers are unambiguous.

### How this lands on your project

Look at the biggest thing on your plan for the next fortnight and ask what has to be
true for it to be worth doing. Usually there is exactly one load-bearing assumption, and
usually it is a story about *why* something is failing. Then price the cheapest honest
test of that one assumption. If it comes in under a tenth of the main job, you have
found a gate worth running — and what makes it worth anything is writing down the
numbers that would make you drop the main job *before* you run the probe. A probe
designed after you know the result is the expensive experiment with extra steps.

## What would NOT have worked

- **Committing straight to the 18-to-22-hour experiment.** The story was untested, and
  the credible alternative would have made the whole spend worthless.
- **Reading the completion rate as the signal.** One puzzle finished and was still
  wrong. A completion-based rule scores that as a win.
- **Comparing fresh runs against the historical ones without a same-session pair.** The
  measured restart instability would have folded into the effect, with no way to
  separate them afterwards.
- **Treating a low reconfirmation count as permission to drop the experiment.** The
  frozen rule forbade that inference outright. The floor did not end up binding — 15 of
  15 reproduced — which is the cheapest moment to notice a rule was right to exist.

## References

- [SCENARIO-12](SCENARIO-12_restart-instability-paired-controls.md) — the
  reproducibility measurement that forced the same-session paired design used here.
- [NV-AGENTICBLOGS-001] "Mastering Agentic Techniques" — evaluate-first ordering;
  verifiable success over surface completion.
- [EXT-TESTBED-001] Karpathy's neural-net sanity-gate recipe — correctness-only gates
  before anything scales up.
- [EXT-STOPPING-002] Lan & DeMets; adaptive clinical-trial design — pre-registered rules
  executed mechanically, not by investigator judgment in the moment.
- Governing chapters: [04](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md),
  [07](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md).
- Glossary: [diagnostic gate](../GLOSSARY.md#diagnostic-gate),
  [pre-registration](../GLOSSARY.md#pre-registration),
  [paired design](../GLOSSARY.md#paired-design),
  [contemporaneous paired control](../GLOSSARY.md#contemporaneous-paired-control),
  [look](../GLOSSARY.md#look).

---

> [Index](../README.md) · [Examples](README.md)
