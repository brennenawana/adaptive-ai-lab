# SCENARIO-04: Harness Defects

> [Index](../README.md) · [Examples](README.md)

**An invented scenario.** The project is fictional; the lesson and the reasoning are the
part to take seriously.
**Illustrates:** [00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) (P1, P2) ·
[02. Execution System Model](../02_EXECUTION_SYSTEM_MODEL.md) ·
[03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md)

## Situation

A city bike-share operator collects a few hundred fault reports a day. *Brakes feel
soft. Wouldn't unlock. Battery died halfway home.* Today a mechanic reads the report,
pulls up that bike's history, works out what is actually broken, and books the right
repair. The operator wants a model to do that first pass.

The evaluation copies the mechanic's job. Each test item hands the system one fault
report. The system calls a fixed set of tools — ride history, dock lock-and-charge
logs, parts-replacement records, on-bike sensor telemetry. It names one root cause from
a closed list of ten fault types. It cites the record IDs its diagnosis rests on. It
recommends one repair from a sanctioned list.

Three pieces of software decide whether the answer was right, and this is where the
trouble lives. A rule-based scorer checks the answer's shape. A second checker — the
verifier — confirms that every cited record ID was actually returned by a tool call
rather than invented. A third flags unsafe claims: asserting a severed cable or a
failed brake the evidence does not support.

Three systems ran the identical items with the identical tools and the identical fixed
evidence plan: two small open-weights models and one much stronger frontier model. Any
gap between them was supposed to be a gap in reasoning, nothing else.

Over ten days the corpus grew from a 10-item pilot to 240 seeded scenarios (120 train
/ 40 dev / 80 test), across three generations of the harness.

## Decision faced

Several times in those ten days, a fault type or a system scored badly, or scored
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
| 2 | Pilot | The verifier rejected citations that named the maintenance ticket rather than the underlying part record | Hand review of all 10 traces | 8 of 10 *correct* citations were scored as inventions |
| 3 | Pilot | The fixed tool plan never fetched the dock lock-and-charge logs | Hand review of the same traces | The evidence needed to answer was structurally out of reach for 3 of the 10 fault types |
| 4 | Scale-up (10→240) | Record IDs (a counter plus three random digits) collided between scenarios of the same fault type | A uniqueness test written for the scale-up | Would have spliced one scenario's evidence into another's |
| 5 | Scale-up | Scenario keys collided across splits — two different seeds rendered the same id | The same uniqueness test | Would have silently defeated the disjoint train/test seed ranges meant to prevent leakage |
| 6 | Corpus rebuild | Sensor telemetry was unreachable by any tool call, for the whole pre-rebuild corpus (0 of 260 snapshots) | [Reachability ceiling](../GLOSSARY.md#reachability-ceiling) measured per fault type by replaying the evidence plan through the real tools | 4 of 10 fault types capped below the 0.8 pass threshold — ceilings of 0.250–0.500 — no matter how good the model was |
| 7 | Corpus rebuild | A "shared-dock" fault type was defined, but every tool was keyed by a single bike id, and a shared event clock scattered the cluster across a month | Ceiling review of a 0.000 root-cause rate on every item in that type | The fault type was unwinnable in principle, not merely hard |
| 8 | Rebaseline | Ride history came back sorted by trip start time, with the internal sequence number never exposed — and one fault type's signature turns on exactly that ordering | Weak-beats-strong [inversion](../GLOSSARY.md#inversion-check): on that type's 8 test items the frontier system scored 1 (12.5%) and a *smaller* local model scored 3 | Frontier score on that type went from 1 of 8 to 8 of 8 once rows were returned in sequence order with the sequence number included |
| 9 | Rebaseline | The unsafe-claim flagger was a bare substring match with no handling of negation | Reading the frontier system's 6 flagged "unsafe claims" against its own well-cited reasoning — implausible on its face | All 6 were denials ("the hub is **not** reporting a lock fault"); corrected all-pass rose from 90.0% as scored (72 of 80) to 97.5% (78 of 80) |
| 10 | Second suite release | Background fleet activity was generated but never published through the real event pipeline, leaving one fault type's fingerprint sitting as unlabeled noise inside six other types | Cross-arm disagreement review; deferred rather than patched mid-baseline | Fixed by publishing every background event through the real pipeline instead of writing it straight to storage |
| 11 | Second release | A battery fault type drew the reported charge level and the dock's last delivered charge independently; in 3 of that type's 24 worlds the reported level exceeded anything the dock had ever supplied | The same review | Briefly made a forbidden hypothesis genuinely consistent with the world in those items |
| 12 | Second release | The negation bug generalized: a lookback-only window, a dead boundary guard, and cues lost at the start of a sentence or a field | The same review, plus one surviving real false positive replayed against the fix | Replaced with a documented, bidirectional same-sentence rule, versioned inside the scorer |
| 13 | Second release | The verifier harvested most observed-id fields, but not the one key a required tool handed straight back to the model | The same review | A correct citation of evidence the model had genuinely been shown was scored as a fabrication |

Rows 4 and 5 are worth keeping separate from the other eleven. They were caught by an
ordinary engineering invariant test, not by a statistical signal. The other eleven only
became visible once the suite had enough fault types and enough competing systems to
expose a ceiling, an inversion, or a disagreement.

## What happened

Not one of the thirteen was fixed by changing a model, a prompt, or a generation
budget. Each was a reproducible property of the measuring instrument, and each was
fixed at the instrument.

The corpus had an invariant of its own: every fault type must be answerable from
evidence the tools actually return. That invariant was violated across the entire
corpus for a full release cycle, and the resulting scores looked exactly like a weak
model. After the fixes, the measured reachability ceiling is 1.000 for all ten fault
types.

The second suite release, which closed defects 10 through 13, shipped 134 new automated
tests: 58 corpus-wide scenario invariants, 30 negation fixtures for the unsafe-claim
flagger, 15 verifier fixtures, 6 database-gated corpus checks, 3 reference-sanity
checks, and 22 revised pipeline tests. Every one of them guards an invariant these
defects had broken.

The release gates were explicit. The measured per-type reachability ceiling had to be
1.000, with zero capped types, on both the dev and test splits. And the suite had to
pass a [frontier-saturation check](../GLOSSARY.md#frontier-saturation-check): the
strongest available system runs the corpus to completion, and no change is made to the
suite afterwards. It passed 40 of 40 on the dev sanity split. A suite that the
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

Chapter 03 turns this into
[static integrity gates](../GLOSSARY.md#static-integrity-gates) that run on the full
corpus, always, and are protected from being subsetted for speed — precisely because
they are the instruments that catch instrument defects. The release discipline that
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
several fault types, a scorer with corrected negation handling everywhere, and a larger
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
