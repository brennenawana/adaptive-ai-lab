# SCENARIO-10: Pilot Optimism Collapse

> [Index](../README.md) · [Examples](README.md)

**An invented scenario.** The project is fictional; the lesson and the reasoning are the
part to take seriously.
**Illustrates:** [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) ·
[04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)

---

## Situation

The working theory was that the model could see what was wrong and simply could not
decide what to do about it. Twelve trail reports said so. Nobody had yet asked what
twelve reports were worth.

The reports come in on a national park's condition form: a visitor describes what they
found out on a trail, in their own words, and the backcountry office decides what happens
next. The assistant under test does two jobs on every report. First it names the
underlying hazard: a washed-out stretch of tread, a footbridge with a failed stringer, a
blowdown across the corridor. Then it picks one field response from a fixed list of
nine — send a crew this week, add it to the fall work list, post an advisory, close the
segment, refer it to the bridge engineer, and so on.

The question in front of the team was whether a mid-size open-weights model they
could run on the office machine was good enough, or whether the job needed a
large hosted model. Both candidates received exactly the same evidence: the
visitor's text plus that segment's maintenance history, assembled once and handed to each
model unchanged. Neither had to go find anything. Any difference between them was a
difference in reasoning, not in retrieval.

The graded corpus was still being written. It would eventually hold 96 reports, eight
from each of twelve hazard families. On the day of the first head-to-head it held
twelve — one per family. Twelve reports is cheap. You can run them, read every
transcript by hand, and change something before lunch. So the first comparison ran on
twelve.

## Decision faced

The pilot said something interesting. Across those twelve reports the local model
named the hazard correctly five times (41.7%) and chose the right field response once
(8.3%). The wrong responses were not scattered, either. The same response — *add it to
the fall work list* — came back for a footbridge with a cracked stringer, a washout that
was actively taking the tread, and a segment that had been closed since June.

Read straight, that is a clean story: the model knows what it is looking at and cannot
act on it. And that story had a week of work attached to it. It would justify finishing
the corpus, running a 96-report confirmation, and aiming an entire prompt-engineering
effort at response selection in particular.

So: was a twelve-case headline strong enough to characterize the model's weakness and
commit the next several days to closing exactly that weakness?

## Evidence

The pilot's own caveat was written into the log before anything was scaled: *"n = 12,
one per family. One report moves any rate by 8.3 points."*

Here is the same local model, on the same fixed evidence, at pilot size and at
confirmation size:

| Metric | 12 reports (pilot) | 96 reports (confirmation) | Change |
|---|---|---|---|
| Hazard named correctly | 41.7% (5/12) | 29.2% (28/96) | **−12.5 pp** |
| Correct field response | 8.3% (1/12) | 13.5% (13/96) | +5.2 pp |
| Both right on the same report | 8.3% (1/12) | 5.2% (5/96) | −3.1 pp |
| Every required history line cited | 83.3% (10/12) | 64.6% (62/96) | −18.7 pp |
| Unsupported claims about the segment | (not counted at 12) | 37 | — |

One reason the pilot ran flattering is worth naming, because it is not special to
trails. Each of the twelve pilot reports was the first one written for its family,
and a first exemplar is the clearest case a person can think of. The eight-per-family
corpus included the muddled ones: two hazards in one message, a visitor placing the
trouble by a landmark that is not on any map, a maintenance history that contradicts
itself. The pilot was never a random sample of the corpus it was standing in for.

A second guard ran five weeks later, on the same project, against a different failure
shape. The corpus had grown to a 48-report development split and a 96-report test
split. Four prompt variants were compared against the current prompt (call it the
control) to see whether any of them recovered the citation discipline that had decayed
at scale. Before the fourth variant was run, the team fixed the rule that would decide
adoption: *adopt a variant only if citation coverage is at least 5 points above
control **and** hazard accuracy is no more than 3 points below it.*

| Prompt | Hazard named | Every required line cited | Both right |
|---|---|---|---|
| Control | 62.5% (30/48) | 70.8% (34/48) | 35.4% (17/48) |
| Variant H | 54.2% (26/48) | 64.6% (31/48) | **39.6% (19/48)** |

Variant H failed the rule on both metrics it was written around. It was also the
best-looking variant in the whole comparison on a metric the rule never mentioned —
both-right, where it led the control by two reports.

Two reports out of 48 is 4.2 points. The team had already worked out what this
suite could resolve: because reports cluster by hazard family, and there are only
twelve families, the effective sample is far smaller than 48, and a paired-difference
analysis put the development split's resolving power at roughly 16–22 percentage
points ([MDE](../GLOSSARY.md#mde); see also
[SCENARIO-02](SCENARIO-02_clustered-eval-effective-n.md)). A 4.2-point swing sits deep
inside that noise floor. It is exactly the number that gets cherry-picked when no rule
was fixed in advance.

## What happened

The pilot's headline was optimistic, and by a lot. Hazard accuracy fell 12.5 points
when the sample grew eightfold. A single case at twelve had been worth 8.3 points,
precisely as the log had flagged before anyone acted on the number.

The pilot's *qualitative* claim survived, though, and this is the part worth being
careful about. At 96 reports, naming the hazard (29.2%) still ran ahead of choosing
the response (13.5%). The ordering the pilot pointed at was real. Its magnitude was
not: at twelve reports naming led response five to one, and at 96 it led by roughly two
to one. A pilot can tell you which way a gap points. It cannot tell you how wide the
gap is.

Two details cut against a tidy reading. Response accuracy moved *up* between the pilot
and the confirmation, not down — noise does not politely degrade every number in the
direction your story predicts. And one failure mode was invisible at twelve by
construction: citation discipline fell nearly nineteen points, with 37 unsupported
claims appearing only once the harder reports entered the sample. The pilot could not
have found that, because the reports that produce it were not in the pilot.

Back in the pilot week, the same discipline ran in the other direction. The large
hosted model was deliberately **not** re-run at 96 reports. The park's condition form
was about to be replaced, which would regenerate every report text in the corpus and
invalidate any comparison built on it. Spending the hosted model's budget on a baseline
that was about to be thrown away was recorded as waste, not as thoroughness.

And the pre-registered adoption rule did its job on variant H. Nothing about H's
both-right number was wrong as a measurement. What made it dangerous was that it was
the number a post-hoc read would have reached for.

## The generic lesson

1. **Before running a pilot, say out loud what one flipped case is worth.** It is
   `100/n` percentage points — 8.3 at twelve cases, 2.1 at 48, 1.0 at 96. Write that
   number next to the result. A pilot headline is directional. It is a hypothesis, not
   a finding.
2. **Expect the point estimate to move when you scale.** Only claims about direction
   or shape ("naming the hazard is easier than choosing the response") survive a pilot.
   Claims about magnitude wait for a split sized to resolve them
   ([MDE](../GLOSSARY.md#mde)).
3. **Check whether your pilot is a sample or a showcase.** Pilot items assembled by
   hand, one per category, tend to be the cleanest instance of each category. That
   biases the headline upward before any statistics are involved.
4. **Fix the adoption rule before you run the comparison that will decide.** Which
   metric, what threshold, in which direction —
   [pre-registered](../GLOSSARY.md#pre-registration), written down, dated
   ([elimination rule](../GLOSSARY.md#elimination-rule)). Picking the winning metric
   after seeing the results is cherry-picking, and from the inside it is
   indistinguishable from good judgment.
5. **When a candidate fails the rule but looks best on some other metric, that is the
   rule working.** It is not evidence the rule was miscalibrated. Record the discarded
   number for the audit trail and do not act on it.
6. **Not measuring is the same discipline.** A number about to be invalidated by other
   work is not worth buying. Treat a corpus that is about to be regenerated, or a suite
   about to be superseded, as provisional, and spend your measurement budget elsewhere.

### How this lands on your project

Find the most recent decision you made from a small run — a spot check, a demo set, a
handful of cases you eyeballed. Divide 100 by the number of items in it. That is what
one case was worth, and it is usually bigger than the difference you acted on. Then
look at what you are running next: is the rule for adopting the winner written down
anywhere yet? If it is not, write it now, before the results land. It takes ten
minutes, and it is the only version of that rule that can protect you — the one you
write afterwards will already know which candidate you are hoping for.

## What would NOT have worked

- **Planning around the pilot's 41.7%.** It was 12.5 points optimistic against
  confirmation — a swing larger than most of the effects this project was built to
  detect.
- **Adopting variant H for its both-right rate.** That was a two-report margin on a
  suite that could not resolve anything under about 16 points, on a variant that
  declined on both metrics the rule was written to check.
- **Reading the pilot's five-to-one gap as the size of the problem.** The ordering
  held. The ratio did not, and the prompt program was scoped against the ratio.
- **Re-running the hosted model at 96 reports "to be thorough" before the form
  change.** The comparison was days from being invalid regardless. The spend would
  have bought a number nobody could use.

## References

- [EXT-STATS-001] Miller, "Adding Error Bars to Evals" (arXiv:2411.00640) — the
  paired-difference power reasoning behind the "two-case swing is inside the noise"
  finding.
- [EXT-STOPPING-002] Lan & DeMets; adaptive clinical-trial design — a decision rule
  fixed in advance and executed mechanically, rather than by the investigator's
  judgment after the fact.
- [NV-MODELOPTRESEARCH-001] Model Optimizer researcher guidance — binomial
  margin-of-error by sample size, corroborating how wide a small-n point estimate's
  error bars really are.
- Governing chapters: [03](../03_EVALUATION_FOUNDATION.md),
  [04](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md).
- Templates: [EXPERIMENT_CONTRACT](../templates/EXPERIMENT_CONTRACT.md) (prediction
  register; candidate selection and elimination rules),
  [PREDICTION_LEDGER](../templates/PREDICTION_LEDGER.md).
- Glossary: [MDE](../GLOSSARY.md#mde),
  [pre-registration](../GLOSSARY.md#pre-registration),
  [elimination rule](../GLOSSARY.md#elimination-rule).

---

> [Index](../README.md) · [Examples](README.md)
