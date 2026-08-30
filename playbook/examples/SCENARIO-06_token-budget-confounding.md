# SCENARIO-06: Token-Budget Confounding

> [Index](../README.md) · [Examples](README.md)

**An invented scenario.** The project is fictional; the lesson and the reasoning are the
part to take seriously.
**Illustrates:** [00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) · [02. Execution System Model](../02_EXECUTION_SYSTEM_MODEL.md) ·
[05. Model, Runtime, and Harness Selection](../05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md) · [06. Inference Performance and Capacity](../06_INFERENCE_PERFORMANCE_AND_CAPACITY.md) ·
[07. Optimization and the Intervention Ladder](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md) · [09. Training and Data](../09_TRAINING_AND_DATA.md)

## Situation

`max_output_tokens: 4096` — one line in a configuration file, inherited from an earlier
round, sitting between the frozen recipe corpus and the pinned prompt. Nobody had it on
the list of things this experiment was varying. It looked like the kind of setting you fix
so it stops moving, rather than a number anyone was measuring.

The system it governs scales recipes for a catering company. A chef types something like
*"take this braise from 8 portions to 140, we have two 40-quart tilt skillets and one
oven, and one table is coeliac"* and the assistant returns a scaled ingredient list, a
revised method, and notes on equipment and timing. The answers run long, and they have to:
a brigade halfway through a service cannot supply a step the assistant left out.

Behind it is a two-stage arrangement. A small local model answers first. A rule-based
checker then verifies the arithmetic — every ingredient scaled by one consistent factor,
total volume inside the declared equipment capacity, temperatures and times in range.
Anything the checker cannot confirm gets escalated to a much larger, much more expensive
model. Cheap model first, expensive model only when needed. That arrangement is a
cascade, and how often it escalates is most of what it costs to run.

The interesting failure here is not a botched multiplication, which the checker catches.
It is an answer that passes every check and is still wrong — the salt and the leavening
scaled linearly when they should not have, or the gluten-free substitution the chef asked
for quietly dropped out of the method. The project calls those **silent failures**:
verified clean, confidently wrong, and invisible until a service goes out ruined.

The experiment asked one question. Should a new candidate model replace the incumbent in
the first stage? The incumbent is a quantized 8-billion-parameter open-weights model that
answers tersely. The candidate is a similarly sized quantized model tuned to reason out
loud at length before it answers.

Round one ran both on the same 60 development items, with everything else pinned: same
prompt, same recipe corpus, same output format, same checker, greedy decoding, one seed.
A same-session control ran incumbent → candidate → incumbent again inside a single
model-server process, and the two incumbent runs came back byte-identical. So any
difference between the arms was down to the model swap alone.

Or so the design assumed. The one setting nobody had questioned was the line above: the
cap on how many tokens a model may generate per answer, frozen at 4,096 since a previous
round. It was treated as a property of the test rig, like the recipe corpus. It is not.
It is a property of the thing being tested.

## Decision faced

Whether to adopt the candidate, judged against a five-part gate written down *before* the
run: (1) at least 5 more items fully correct, (2) at least 5 fewer silent failures,
(3) no more than 3 items that the incumbent gets right and the candidate gets wrong,
(4) median latency at or under 30 s, (5) cascade economics no worse.

## Evidence

Round one, 60 dev items, cap 4,096:

| | Incumbent | Candidate |
|---|---|---|
| Fully correct | 18 (30.0%) | 15 (25.0%) |
| No usable output | 6 (all format failures) | 37 (34 hit the token cap + 3 format failures) |
| Silent failures (verified clean, still wrong) | 27 | **5** |
| Cascade: correct / escalation rate / cost per success | 46.7% at 23.3%, $0.0545 | 88.3% at 66.7%, $0.0868 |
| Median latency | 16 s | 71 s |

The item-by-item movement: 11 items both models got right, 7 the incumbent got right and
the candidate did not, 4 the reverse, 38 neither. The write-up was blunt about those 7:
*all seven are the 4,096-token cap being hit in the middle of the candidate's reasoning.*

Against the pre-registered gate: the candidate was 3 items *worse* on correctness rather
than 5 better, so criterion 1 failed. It had 7 regressions against a tolerance of 3, so
criterion 3 failed. Its median latency was 71 s against a 30 s bar, so criterion 4
failed. It cost more per success, so criterion 5 failed. Only criterion 2 passed — and it
passed enormously, with 22 fewer silent failures. The verdict, *the candidate does not
qualify and the incumbent stays*, was correct.

But the report flagged its own result as unsafe to read as a statement about the models.
One number was doing all the emotional work: the candidate appeared to cut silent
failures by about 80%, from 27 down to 5. That is the number that makes a team want to
adopt a model anyway, gate or no gate. (A related measure moved with it: silent failures
that a strong reference model got right fell from 25 to 4. The two counts travel
together but are not the same metric.) That number was also about to be shown to be
mostly an artifact.

## What happened

The re-run changed exactly one thing: the cap went from 4,096 to 8,192, **for both
arms**, in the same paired session, same item order. The controls held again — the
candidate reproduced its 26 completed round-one items byte-for-byte, and an incumbent
diagnostic back at 4,096 after the fact showed the larger cap was inert for the incumbent
on all but a single item.

| | Incumbent 8,192 | Candidate 8,192 | Candidate 4,096 (round one) |
|---|---|---|---|
| Fully correct | 19 (31.7%) | **23 (38.3%)** | 15 |
| No usable output | 6 | 14 | 37 |
| Silent failures | 26 | **19** | 5 |
| Output tokens, summed | 78,400 | 301,000 | 214,000 |

Two things moved at once, and they point in opposite directions.

**The ranking reversed.** At 4,096 the incumbent led by 3 correct items. At 8,192 the
candidate led by 4. The apparent "the candidate is worse" signal was mostly unfinished
answers scored as failures.

**The headline safety advantage mostly evaporated.** The silent-failure gap shrank from
roughly 80% to 27% (26 versus 19) once both arms had room to finish. The earlier gap was
largely unfinished reasoning being counted as *not yet wrong* instead of wrong.

Replaying round one's 34 cap-truncated candidate items at the larger budget resolved them
into 8 that became correct, 15 that turned out to be failures (14 of them silent), and 11
that still ran out of tokens at 8,192. So the same cap had been manufacturing both
illusions at once: it made a capable model look unreliable, and it made an unreliable
model look safe.

One setting had been quietly doing the work everyone was attributing to the models. That
is a confound, and this one was now gone. Even so, the candidate still did **not**
qualify. The re-run's pre-registered gate failed on completion (46 of 60 items produced usable output, against
a threshold of 52), on residual silent failures (19, against a tolerance of 8), and on
the regression cell (7 items the incumbent got right and the candidate did not, against a
tolerance of 5). It passed on raw correct count and on cascade cost per success — $0.0508
at a 43.3% escalation rate, against the incumbent's $0.0545 — while median latency, at
4.4 times the incumbent's, stayed well outside the 30 s bar. The incumbent remained
incumbent, but now for reasons that had nothing to do with the cap. The 4,096 limit is
why round one looked the way it did. It is not why the candidate does not qualify: the
candidate still cannot finish 11 of 60 items inside 8,192 tokens.

The budget question was settled by running the same comparison twice, changing one
setting, for both models. The adoption question was settled separately, by the gate, on
the corrected numbers.

## The generic lesson

A shared generation budget is not a neutral harness setting when the candidates differ in
how much they write. It is a variable, and it has to be calibrated or isolated before any
model-comparison claim built on top of it is trusted.

A cap that is roomy for a terse model and tight for a verbose one converts a
budget-exhaustion problem — [RC-8](../GLOSSARY.md#canonical-failure-taxonomy) in the
canonical failure taxonomy — into what reads as a difference in capability or
reliability. It does this in both directions, which is what makes it nasty. Unfinished
answers scored as failures make a capable model look weak. Unfinished *reasoning* scored
as "no claim made" makes an unreliable model look careful.

That is why the distinction between **no output** and **wrong output** has to survive
into every table you publish. A model that produced nothing and a model that produced a
confident mistake are not both "a failure" for the purpose of deciding anything. Round
one's tables kept them apart, which is the only reason the confound was visible at all.

The decoding budget belongs to the [execution system](../GLOSSARY.md#execution-system)
exactly as much as the model weights do. A
[comparability claim](../GLOSSARY.md#comparability-claim) between two arms is valid only
once every factor except the one under test is pinned identically. The
[paired design](../GLOSSARY.md#paired-design) used here — one factor changed, changed for
both arms, same session, same item order — is the pattern that isolates it correctly.
Chapter 07's [intervention ladder](../GLOSSARY.md#intervention-ladder) gives
generation-budget calibration its own rung, rung 5, separate from model and runtime
selection, for exactly this reason: a budget confound has to be cleared before a
model-comparison result at any other rung means anything, in either direction.

**How this lands on your project.** Open your eval results and find the column that
counts failures. If truncated answers and wrong answers are pooled in it, split them
today — that one change is most of the diagnostic. Then check the maximum output length
your harness allows, and the longest answer each candidate actually produced. If any
candidate is bumping the ceiling on more than a handful of items, your comparison is
measuring the ceiling. Re-run at double the cap, for every arm, and see whether your
ranking survives. If it does, you have learned that the cap was not load-bearing, which
is worth knowing too.

## What would NOT have worked

**Reading round one at face value in either direction.** "The candidate cuts silent
failures by 80%, adopt it" would have adopted a model largely for an artifact of its
truncations. "The candidate loses on correctness and floods the cascade with
escalations, reject it" would have rejected it for the same unexamined reason. Both
readings were available from that one table. Neither was safe until the budget was
isolated.

**Raising the cap for the candidate only.** Giving the verbose model room to finish while
leaving the terse one at 4,096 does not produce a valid comparison. It trades one
confound for a second, deliberately introduced one, and it stops being a model comparison
at all. The re-run changed the cap for both arms in the same paired session precisely to
avoid this.

**Concluding from the re-run that the budget question is closed and the candidate wins.**
Also wrong. With matched budgets and a genuine 4-item lead on correctness, the candidate
still failed the pre-registered gate on completion, on residual silent failures, and on
the regression cell — at 3.8 times the generated tokens and 4.4 times the median latency
of the incumbent. The reversal was informative. It was the gate, not the reversal, that
decided adoption.

## References

- [NV-EVALSDK-001] — a published evaluation SDK's comparison and gating tooling; the
  external analogue of this scenario's core requirement, refusing to compare two arms
  once a configuration factor differs between them.
- Governing chapters: [04](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md),
  [05](../05_MODEL_RUNTIME_AND_HARNESS_SELECTION.md),
  [07](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md).
- Glossary: [execution system](../GLOSSARY.md#execution-system),
  [comparability claim](../GLOSSARY.md#comparability-claim),
  [paired design](../GLOSSARY.md#paired-design),
  [canonical failure taxonomy](../GLOSSARY.md#canonical-failure-taxonomy),
  [intervention ladder](../GLOSSARY.md#intervention-ladder).

---

[Index](../README.md) · [Glossary](../GLOSSARY.md)
