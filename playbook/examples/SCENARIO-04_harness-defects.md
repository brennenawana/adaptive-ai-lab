# SCENARIO-04: Harness Defects

> [Index](../README.md) · [Examples](README.md)

**An invented scenario.** The project is fictional; the lesson and the reasoning are the
part to take seriously.
**Illustrates:** [00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) · [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) ·
[08. Retrieval, Tools, Workflows, and Routing](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md)

## Situation

On one of the ten root-cause classes, the frontier system scored 1 of 8 test items and a
much smaller local model scored 3. No fact about model quality explains that. A weaker
system beating a stronger one on a whole class of problem is not a result — it is a lead,
and where it leads is almost never the model.

The class belongs to a regional water utility that gets a few hundred billing complaints
a day. *My bill tripled and nothing changed. The meter reads higher than my own reading.
There's water in the alley.* An investigator opens the account, pulls the meter reads and
the pressure logs, works out what actually happened, and books the right response — a
re-read, a leak crew, a corrected bill. The utility wants a model to do that first pass.

The evaluation copies the investigator's job. Each test item hands the system one
complaint. The system calls a fixed set of tools — meter read history, pressure-sensor
logs, work-order history, the service-line map. It names one root cause from a closed
list of ten. It cites the record IDs its finding rests on. It recommends one response
from a sanctioned list.

Three pieces of software decide whether the answer was right, and this is where the
trouble lives. A rule-based scorer checks the answer's shape. A second checker — the
verifier — confirms that every cited record ID was actually returned by a tool call
rather than invented. A third flags unsafe claims: asserting a burst main or a
contaminated supply the evidence does not support.

Three systems ran the identical items with the identical tools and the identical fixed
evidence plan: two small open-weights models and one much stronger frontier model. Any
gap between them was supposed to be a gap in reasoning, nothing else.

Over ten days the corpus grew from a 10-item pilot to 240 seeded scenarios (120 train
/ 40 dev / 80 test), across three generations of the harness.

## Decision faced

Several times in those ten days, a root-cause class or a system scored badly, or scored
strangely, and someone had to pick where the next hour went. One option is the
appealing one: change the prompt, swap the model, raise the generation budget. The
other option is dull. Go and audit the test.

The project's precedence rule forced the dull option every time. No score is believed
until three questions have been answered. Could a careful human score full marks on
this item with the tools the system had? Did any weaker system beat a stronger one
somewhere it should not have? Do the three systems disagree in a way that makes no
sense? This is the first root cause in the
[canonical failure taxonomy](../GLOSSARY.md#canonical-failure-taxonomy) — RC-1,
measurement or instrument defect — and it always ranks first, ahead of every
explanation that blames the model.

What follows is what that discipline turned up: thirteen defects in the test rig, each
one initially indistinguishable from a weak model, and not one of them fixed by
touching a model.

## Evidence

| # | When | What was wrong | How it surfaced | Measured effect |
|---|---|---|---|---|
| 1 | Pilot (n=10) | The schema compiler rejected the length constraints in the output format | Every local call came back an HTTP error | 0 of 10 local calls produced any output at all until fixed |
| 2 | Pilot | The verifier rejected citations that named the work order rather than the underlying meter-read record | Hand review of all 10 traces | 8 of 10 *correct* citations were scored as inventions |
| 3 | Pilot | The fixed tool plan never fetched the pressure-sensor logs at all | Hand review of the same traces | The evidence needed to answer was structurally out of reach for 3 of the 10 root causes |
| 4 | Scale-up (10→240) | Record IDs (a counter plus three random digits) collided between scenarios of the same root cause | A uniqueness test written for the scale-up | Would have spliced one scenario's evidence into another's |
| 5 | Scale-up | Scenario keys collided across splits — two different seeds rendered the same id | The same uniqueness test | Would have silently defeated the disjoint train/test seed ranges meant to prevent leakage |
| 6 | Corpus rebuild | Night-flow sensor readings were unreachable by any tool call, for the whole pre-rebuild corpus (0 of 260 readings) | [Reachability ceiling](../GLOSSARY.md#reachability-ceiling) measured per root cause by replaying the evidence plan through the real tools | 4 of 10 root causes capped below the 0.8 pass threshold — ceilings of 0.250–0.500 — no matter how good the model was |
| 7 | Corpus rebuild | A "shared service line" root cause was defined, but every tool was keyed by a single account id, and a shared event clock scattered the affected properties across a month | Ceiling review of a 0.000 correct-diagnosis rate on every item in that class | The class was unwinnable in principle, not merely hard |
| 8 | Rebaseline | Meter reads came back sorted by reading date, with the utility's internal read-sequence number never exposed — and one root cause's whole signature is an out-of-order estimated read | Weak-beats-strong [inversion](../GLOSSARY.md#inversion-check): on that class's 8 test items the frontier system scored 1 (12.5%) and a *smaller* local model scored 3 | Frontier score on that class went from 1 of 8 to 8 of 8 once reads were returned in sequence order with the sequence number included |
| 9 | Rebaseline | The unsafe-claim flagger was a bare substring match with no handling of negation | Reading the frontier system's 6 flagged "unsafe claims" against its own well-cited reasoning — implausible on its face | All 6 were denials ("the pressure log does **not** show a main break"); corrected all-pass rose from 90.0% as scored (72 of 80) to 97.5% (78 of 80) |
| 10 | Second suite release | Background neighbourhood consumption was generated but never published through the real event pipeline, leaving one root cause's fingerprint sitting as unlabeled noise inside six other classes | Cross-arm disagreement review; deferred rather than patched mid-baseline | Fixed by publishing every background event through the real pipeline instead of writing it straight to storage |
| 11 | Second release | A high-consumption class drew the billed volume and the meter's maximum flow rate independently; in 3 of that class's 24 worlds the billed volume exceeded anything the meter could physically have passed | The same review | Briefly made a forbidden hypothesis genuinely consistent with the world in those items |
| 12 | Second release | The negation bug generalized: a lookback-only window, a dead boundary guard, and cues lost at the start of a sentence or a field | The same review, plus one surviving real false positive replayed against the fix | Replaced with a documented, bidirectional same-sentence rule, versioned inside the scorer |
| 13 | Second release | The verifier harvested most observed-id fields, but not the one key a required tool handed straight back to the model | The same review | A correct citation of evidence the model had genuinely been shown was scored as a fabrication |

Rows 4 and 5 are worth keeping separate from the other eleven. They were caught by an
ordinary engineering invariant test, not by a statistical signal. The other eleven only
became visible once the suite had enough root-cause classes and enough competing systems to
expose a ceiling, an inversion, or a disagreement.

## What happened

Not one of the thirteen was fixed by changing a model, a prompt, or a generation
budget. Each was a reproducible property of the measuring instrument, and each was
fixed at the instrument.

The corpus had an invariant of its own: every root-cause class must be answerable from
evidence the tools actually return. That invariant was violated across the entire
corpus for a full release cycle, and the resulting scores looked exactly like a weak
model. After the fixes, the measured reachability ceiling is 1.000 for all ten root-cause
classes.

The second suite release, which closed defects 10 through 13, shipped 134 new automated
tests: 58 corpus-wide scenario invariants, 30 negation fixtures for the unsafe-claim
flagger, 15 verifier fixtures, 6 database-gated corpus checks, 3 reference-sanity
checks, and 22 revised pipeline tests. Every one of them guards an invariant these
defects had broken.

The release gates were explicit. The measured per-class reachability ceiling had to be
1.000, with zero capped classes, on both the dev and test splits. And the strongest available
system had to run the whole corpus to completion, with no change made to the suite
afterwards — a
[frontier-saturation check](../GLOSSARY.md#frontier-saturation-check). It passed 40 of 40 on the dev sanity split. A suite that the
strongest available system cannot get near its own measured ceiling on is presumed
broken. By the release gate, this one was not: on the 80-item confirmation split the
frontier system's corrected all-pass rate reached 98.8%, close to saturating the
instrument.

## The generic lesson

Prove the instrument before you credit or blame the model — [P2](../00_PRINCIPLES_AND_SCOPE.md).

Three signals catch most instrument defects, and none of them requires reading failures
by hand at scale. Measure the [reachability ceiling](../GLOSSARY.md#reachability-ceiling)
for each stratum against the corpus you actually built, by replaying the evidence plan
through the real tools — never argued from the generator's intent. Check each stratum
for [inversions](../GLOSSARY.md#inversion-check), where a systematically weaker system
beats a stronger one. Review cross-system and cross-run disagreement before you accept
a surprising number in *either* direction — a suspiciously good result is as diagnostic
as a bad one.

All three are statistical properties of a large-enough evaluation. They exist because
the suite has many items, many strata, and more than one system under test. That is why
breadth in an evaluation corpus is not padding — it is what makes the corpus able to
audit itself. A minority of instrument defects (here, two of thirteen) are instead
plain engineering bugs, caught by plain invariant and uniqueness tests. Worth having,
but a different mechanism from the other three.

Chapter 03 turns this into checks that run on the full
corpus, always, and are protected from being trimmed down for speed — precisely because
they are the instruments that catch instrument defects. It calls them
[static integrity gates](../GLOSSARY.md#static-integrity-gates). The release discipline that
closed defects 10 through 13 is generalized in
[templates/EVAL_SUITE_RELEASE_CONTRACT.md](../templates/EVAL_SUITE_RELEASE_CONTRACT.md),
which requires per-stratum ceilings to be measured and printed, and a
frontier-saturation check run, before any suite is released.
[SCENARIO-09](SCENARIO-09_suite-versioning-criteria-drift.md) is the governance half of
the same story: how these fixes were batched into one pre-registered release instead of
being patched in place.

For a sense of scale, from outside this scenario: a large benchmark-curation effort
found that trimming a task set from 1,699 tasks to 500 human-vetted ones moved the
measured solve rate from 16% to 33.2% [EXT-EVAL-005]. A comparable share of an apparent
capability gap turned out to be the instrument, not the systems being measured.

**How this lands on your project.** Take the worst-scoring stratum in your eval and
answer one item yourself, by hand, using only the tools your system is given. If you
cannot score full marks, your number is measuring your test. Then sort your per-stratum
scores by system strength and look for any stratum where a weaker system wins; that
stratum is a bug report. Then look for any item every system fails identically, and
suspect the item before the models. Three checks, an afternoon, and they run before you
spend a week on prompts.

## What would NOT have worked

**Patching the unsafe-claim flagger the moment defect 9 surfaced.** A quick
negation guard was considered and rejected. A negation guard is itself a heuristic, and
it can produce false *negatives* — a real unsafe claim scored clean. For a metric whose
whole purpose is catching harm, that is the dangerous direction to be wrong in. The
reported number was corrected immediately; the flagger's semantics were deliberately
left for a scoped decision rather than a same-day patch.

**Fixing defects 10 through 13 one at a time, in place, as each was noticed.** They were
batched into one pre-registered release with a written changelist instead. A fix chosen
mid-run, after seeing a model's output, is not distinguishable afterwards from tuning
the test until that model does better on it. The release's own rule says so directly:
no change to the instrument is justified by, or chosen after looking at, any model's
score.

**Reading the before-and-after score jump as a model-quality signal.** This was
explicitly rejected. The same model on the same seed now faces a changed world in
several root-cause classes, a scorer with corrected negation handling everywhere, and a larger
set of observable evidence. The difference mixes at least three effects, and none of
them is the model changing.

## References

- [EXT-EVAL-005] — benchmark re-curation: outside corroboration that curation, not
  model improvement, explains a comparable share of an apparent capability gap.
- [SCENARIO-09](SCENARIO-09_suite-versioning-criteria-drift.md) — the versioning and
  release governance that closed defects 10–13 here.
- Governing chapters: [00](../00_PRINCIPLES_AND_SCOPE.md),
  [02](../02_EXECUTION_SYSTEM_MODEL.md), [03](../03_EVALUATION_FOUNDATION.md).
- Glossary: [reachability ceiling](../GLOSSARY.md#reachability-ceiling),
  [inversion check](../GLOSSARY.md#inversion-check),
  [frontier-saturation check](../GLOSSARY.md#frontier-saturation-check),
  [static integrity gates](../GLOSSARY.md#static-integrity-gates),
  [canonical failure taxonomy](../GLOSSARY.md#canonical-failure-taxonomy).

---

[Index](../README.md) · [Glossary](../GLOSSARY.md)
