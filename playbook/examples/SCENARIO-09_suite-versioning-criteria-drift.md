# SCENARIO-09: Suite Versioning Under Criteria Drift

> [Index](../README.md) · [Examples](README.md)

**An invented scenario.** The project is fictional; the lesson and the reasoning are the
part to take seriously.
**Illustrates:** [00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) ·
[03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) ·
[13. Governance, Provenance, and Security](../13_GOVERNANCE_PROVENANCE_AND_SECURITY.md)

## Situation

The evaluation had been disagreeing with itself between runs. Reading the transcripts is
what surfaced why: four defects, none of them in the documentation or the rubric, all of
them in the generator and the scorer themselves — the machinery that manufactures the
truth, and the machinery that checks against it. Not one was found by re-reading the
specification.

The suite those defects sit in belongs to a city building department, which is testing an
assistant that pre-checks permit applications. Someone submits plans for a deck, a sign, a
kitchen remodel. The assistant reads the submission and answers three things: what is blocking
approval, which section of the municipal code says so, and what the applicant has to do
next. If it works, it saves counter staff a first pass on a few hundred applications a
week.

To test it, the team built a suite that generates fake applications with known defects
planted in them — an expired contractor licence, a setback that violates the zoning table,
a fee that came up short — and scores the assistant's answer against what was planted.

That suite has four moving parts, and all four are supposed to be frozen before anyone
looks at a model's score: the list of defect types, the list of evidence an answer must
cite for each application type, the list of claims an answer is forbidden to make, and the
code that reads an answer and decides whether it passed.

The four defects came out of an audit of that suite — the kind
[SCENARIO-04](SCENARIO-04_harness-defects.md) walks through in a different setting — which
found thirteen problems in all.

This scenario is not about those four defects. It is about what the team did next.

## Decision faced

Four confirmed bugs sat in live scoring and generation code. Two full baseline rounds had
already been run and reported under that code.

**Option one: fix them in place.** Edit the generator, edit the scorer, re-run. It is a
day's work. It also voids every number already circulated, and makes each fix permanently
indistinguishable from one chosen *because a particular model's answer looked wrong*. Six
months later nobody can tell the difference, including the people who made the change.

**Option two: freeze a new numbered release of the suite.** Old numbers stay on the record,
labeled with the version that produced them. New numbers start a new series. The tooling
itself refuses to put a number from one series next to a number from the other. This costs
a complete re-baseline of all three model arms across both splits before a single one of
the four fixes can be credited with anything.

They took option two.

## Evidence

**The rule, written before any fix was implemented.** Every entry in the release's
changelist had to answer exactly two questions. *What invariant of the generator, the
evidence set, the scorer, or the verifier was wrong under the previous version?* And *how
does this change make the suite more faithful to the task it claims to measure?* With one
hard constraint: **no change may be justified by, or chosen after looking at, any model's
score.**

That constraint is the whole design. Everything else in the release is machinery for making
it enforceable.

**The four defects closed:**

- Filler records in the generated case files carried one defect type's signature into five
  other application types as unlabeled noise, so a correct answer on those types could be
  scored wrong.
- The fee-shortfall type drew the fee owed and the fee paid independently. In 4 of 30
  generated applications the payment exceeded the fee owed — which made a claim on the
  forbidden list briefly *true* of that world.
- The forbidden-claim detector had a polarity bug. It credited the claim it was written to
  penalize.
- The verifier treated one legitimate citation form as fabrication: a code section cited by
  its post-amendment number, which is the number printed in the code the model was shown.

**The versioning machinery, so the release was enforced rather than merely documented.** A
suite-version identifier stamped on every generated application and every scored result row
from that point on. Prior versions' rows relabeled and backfilled — never deleted, never
rewritten. A canonical digest computed over the regenerated corpus and confirmed identical
across two independent regenerations from scratch. And six analysis tools changed to group
results by *(run, suite version)* and to refuse, by default, to place rows from different
versions side by side. There is an override flag. Using it prints a non-comparability
warning into the output.

**The release gate, run once and recorded.** The automated test count went from 186 to 349:
78 new corpus-wide invariants checked across every generated application, 41 fixtures
pinning the forbidden-claim detector's polarity, 22 verifier fixtures, and 22 database-gated
corpus checks. The measured
[reachability ceiling](../GLOSSARY.md#reachability-ceiling) — can a perfect answerer, given
only what the model is given, actually score full marks? — was required to be 1.000 with
zero capped application types on both the 40-case calibration split and the 80-case
confirmation split. And the strongest available model arm had to complete a clean sanity
pass, 40 of 40, with a rule fixed in advance: **if anything in the suite changes after that
pass, the gates and the sanity pass are both re-run rather than the result kept.**

**What deliberately did not change.** The defect taxonomy, the set of actions an answer may
recommend, and the mapping between them kept their existing version. This release fixed
the suite's fidelity to the task it already claimed to measure. It did not change what the
task is. The release record draws that line explicitly: blurring it is how a suite quietly
becomes a different suite while keeping its name.

## What happened

The release ran in a fixed order. Implement each of the four fixes with its own tests, one
at a time. Build the versioning and refusal machinery. Regenerate the corpus and clear
every gate. Run the sanity pass. Freeze and tag. Re-baseline all three arms on the
calibration split. Run the descriptive cross-arm analyses. Run the confirmation split
exactly once per arm. Publish.

One more problem surfaced *during* the sanity pass. Three application types keyed their
planted record in a way that did not distinguish it from an ordinary record, so the scorer
could credit an answer for finding the wrong thing. The rule held: the corpus was
regenerated from scratch and the sanity pass restarted, rather than the in-flight result
patched and kept. That is the moment the discipline actually cost something, and it is the
only moment that tells you whether the discipline is real.

Every result row from the earlier versions survived, labeled, and is still queryable. What
changed is that the comparison tooling will not pair an old row with a new one without an
explicit flag, and says why whenever the flag is used.

The scores went up. The strongest arm scored 68% on the calibration split under the
previous version and 79% under release 3 of the suite. That 11-point difference was **not**
published as a model improvement, and the release report says why in plain terms: the same
model, on the same application, now faces a differently generated world in several types, a
scorer whose polarity is corrected in every type, and a verifier that recognizes a citation
form it used to reject. The difference mixes at least three effects and isolates none of
them. One of those three is not the model. The new numbers were published as a new
reference point, and the old series was left where it was.

This was not the first deferral. A full round earlier, two model answers had looked
defensible under a stricter reading of the rubric than the rubric actually used. Rather
than loosen the rubric in response, the team logged it as a candidate for review at the
next frozen release — which is the release this scenario describes.

## The generic lesson

**Criteria drift is not a discipline failure.** You cannot fully specify evaluation
criteria before seeing real outputs. Criteria and reference answers co-evolve as graders
look at actual behavior — this is a measured finding about how evaluation work goes, not a
sign that somebody was sloppy [EXT-EVAL-004]. Four independent defects here were found only
by reading transcripts, under a suite that was already contract-frozen.

Two responses suggest themselves and both are wrong. "Specify everything perfectly up
front" did not happen here and does not happen. "Edit the live suite whenever a defect
turns up" invalidates every number already reported, and destroys your ability to prove
later that you were not tuning the test to the answer.

The licensed third response is a [suite release](../GLOSSARY.md#suite-release): a written
changelist whose only admissible justification is a stated invariant violation, never a
model's score; a version stamp that makes non-comparability a property of the *tooling*
rather than a footnote in a document
([cross-suite refusal](../GLOSSARY.md#cross-suite-refusal)); and unmodified, labeled
retention of everything the previous version produced. Chapter 03 defines
[criteria drift](../GLOSSARY.md#criteria-drift) and this discipline normatively; the
generic form is in
[templates/EVAL_SUITE_RELEASE_CONTRACT.md](../templates/EVAL_SUITE_RELEASE_CONTRACT.md).
Chapter 13 covers the other half — superseded material is dated and kept, never quietly
overwritten ([record of record](../GLOSSARY.md#record-of-record)).

There is a quieter benefit worth naming. Instrument defects that get patched in place
become folklore: *that permit type always seemed weird.* The same defects, closed through a
dated and gated release, become a fact anyone can reproduce.

**How this lands on your project.** Ask one question about your own evaluation: if you
fixed a scorer bug this afternoon, would last month's reported numbers still be labeled in
a way that says they came from a different instrument? If not, you have one series of
numbers quietly spanning two instruments and no way to separate them now. Three things fix
that, and none takes a week. Stamp a version on every generated item and every result row.
Make your comparison script refuse to mix versions unless someone passes a flag. Keep a
changelist where each entry names the invariant that was broken. All three are cheap in
advance and unrecoverable afterwards.

## What would NOT have worked

**Patching each defect the moment it was noticed.** Rejected by the release's own governing
rule. A mid-run fix chosen after seeing a specific answer cannot be distinguished, after the
fact, from tuning the instrument to that answer — not by an outside reviewer, and not by the
person who made it.

**Publishing the 68% → 79% difference as a model improvement.** Explicitly rejected in the
release report. The difference conflates the model, the world the model was evaluated
against, and the rules used to score it, and isolates none of the three.

**Loosening the rubric after the two defensible-but-wrong answers.** Rejected at the time
and logged instead. The review it was logged for is this release, where the candidate was
weighed on its own merits rather than in response to the two answers that raised it.

## References

- [EXT-EVAL-004] EvalGen / "Who Validates the Validators" (Shankar et al.) — the
  practitioner-study evidence that criteria and reference answers co-evolve as outputs are
  seen, and the source of "criteria drift" as this playbook uses the term.
- [SCENARIO-04](SCENARIO-04_harness-defects.md) — how defects like these are detected in
  the first place, and why they impersonate model weakness until they are.
- Governing chapters: [00](../00_PRINCIPLES_AND_SCOPE.md),
  [03](../03_EVALUATION_FOUNDATION.md),
  [13](../13_GOVERNANCE_PROVENANCE_AND_SECURITY.md).
- Template: [EVAL_SUITE_RELEASE_CONTRACT](../templates/EVAL_SUITE_RELEASE_CONTRACT.md).
- Glossary: [criteria drift](../GLOSSARY.md#criteria-drift),
  [suite release](../GLOSSARY.md#suite-release),
  [cross-suite refusal](../GLOSSARY.md#cross-suite-refusal),
  [record of record](../GLOSSARY.md#record-of-record),
  [reachability ceiling](../GLOSSARY.md#reachability-ceiling).

---

> [Index](../README.md) · [Examples](README.md)
