# CASE-009: Suite Versioning Under Criteria Drift

> Real empirical case from the FIS project (Fintech Integration Sandbox), a
> realistic synthetic fintech-operations laboratory used to develop this
> playbook's methodology.
>
> Source: [INT-CASE-009] · Dates: 2026-08-15 – 2026-08-18 · Cited by:
> [chapter 00](../00_PRINCIPLES_AND_SCOPE.md) (P6) ·
> [chapter 03](../03_EVALUATION_FOUNDATION.md) ·
> [chapter 13](../13_GOVERNANCE_PROVENANCE_AND_SECURITY.md)

## Situation

FIS's evaluation criteria — the root-cause taxonomy, the required-evidence
list per scenario, the forbidden-claim list, and the scoring/verification
logic that reads model output against them — are meant to be frozen before
any model result is read. [CASE-004](CASE-004_harness-defects.md) records
what happened when that instrument was checked: thirteen defects, four of
which lived in the scenario generator and the scorer/verifier logic itself
(a class's fault signature leaking into other classes as unlabeled activity;
a declined-transaction class whose amount and balance could contradict each
other; a forbidden-claim detector with a polarity bug; a verifier that failed
to recognize a key the model had actually been shown). All four were found
the same way — by reading real model traces and noticing the evaluation
disagreed with itself across arms — not by inspecting the specification in
the abstract. This case is about what the project did with that fact, not
about the defects themselves.

## Decision faced

Four confirmed defects sat in the live scoring and generation logic while two
prior baseline rounds' worth of scores had already been reported under it.
The team had to choose between two ways to close them: edit the scorer,
verifier, and generator in place and re-run — fast, but it silently
invalidates every previously reported number and makes each fix
indistinguishable, after the fact, from a fix chosen because a specific
model's answer looked wrong — or freeze a new, numbered release through a
pre-registered, gated process that keeps the old numbers as history and
refuses, by tooling, to let anything compare across the boundary. The second
path costs a full re-baseline of all three arms on both the calibration and
confirmation splits before a single one of the four fixes can be credited.

## Evidence

**The governing rule, written before any fix was implemented:** every entry
in the release's changelist was required to answer exactly two questions —
*what simulator, evidence, scorer, or verifier invariant was wrong under the
prior version?* and *how does the change make the benchmark more faithful to
its own declared task semantics?* — with the explicit constraint that no
change may be justified by, or chosen after looking at, any model's score.

**The four defects closed by this release** (technical detail in
[CASE-004](CASE-004_harness-defects.md)): unpublished background scenario
activity carrying one class's fault signature into six others as noise; a
declined-transaction class whose amount and balance were drawn independently
(3 of 24 generated worlds had the decline exceed the balance, which made a
forbidden hypothesis briefly consistent with the world); a forbidden-claim
polarity bug in the scorer; and a verifier gap that scored one legitimate
citation type as fabrication.

**The versioning mechanism that made the release enforceable, not just
documented:** a suite-version identifier recorded on every generated
scenario and every scored result row going forward; prior versions' rows
relabeled and backfilled but never deleted or rewritten; a canonical digest
computed over the regenerated corpus and checked identical across two
independent regenerations; and six separate analysis tools changed to group
results by `(run, suite version)` and refuse by default to pair rows from
different versions — an explicit override prints a non-comparability caveat
whenever it is used.

**The release gate, run once and recorded:** the automated test count went
from 202 to 368 (69 new corpus-wide scenario invariants, 32 forbidden-claim
polarity fixtures, 17 verifier fixtures, plus database-gated corpus checks);
the measured per-class reachability ceiling was required to be 1.000 with
zero capped classes on both the 48-case calibration split and the 96-case
confirmation split; and the strongest available arm was required to complete
a full sanity pass (48/48) with the rule, fixed in advance, that if anything
in the suite changed after that pass, the gates and the sanity run would
both be repeated rather than the result kept.

**What stayed frozen throughout:** the root-cause taxonomy, the action set,
and the cause-to-action mapping did not change version — this was a
benchmark-fidelity revision, not a scope change, and the release record
draws that line explicitly.

## What happened

The release ran in a fixed order: implement each of the four fixes with its
own tests, one at a time; build the versioning and non-comparability
infrastructure; regenerate the corpus and pass every gate; run the frontier
sanity pass; freeze and tag; re-baseline all three arms on the calibration
split; run the descriptive cross-arm analyses; run the confirmation split
exactly once per arm; publish the report. One further correction surfaced
*during* the sanity pass itself — a residual edge case in how three classes'
(S06, S07, S10) injected events were keyed, so the key never discriminated the
injected event from a real one — and even that was handled by regenerating the
corpus from scratch and restarting the sanity pass, not by patching the
in-flight result. The discipline held under the pressure of a pass already
under way.

Every prior-version score row survived, labeled by its version, and remains
queryable — but the comparison tooling itself refuses to place a prior-version
row next to a new one without an explicit flag, and prints the reason when
that flag is used. The project's own analysis of the resulting jump in scores
states plainly why a raw before/after subtraction was not published as a
model-quality number: the same model on the same case now faces a
different generated world in several classes, a scorer with corrected
polarity in every class, and a larger set of evidence the verifier will
recognize as observed — the delta mixes at least three effects, and none of
them is the model changing. The new version's numbers are reported as a new
reference point, not as an improvement over the old ones.

This was not the first time the project deferred a criteria change rather
than making it live: a full baseline round earlier, two model answers had
looked defensible under a stricter reading than the written rubric used, and
rather than loosen the rubric in response, the team logged it as a candidate
for review *before* the next frozen release — which is exactly the version
this release turned out to be.

## The generic lesson

Criteria drift — the empirical finding that evaluation criteria cannot be
fully specified before seeing real outputs, and instead co-evolve with them
[EXT-EVAL-004] — is not a discipline failure to be engineered away. It is a
property of the process, observed here across four independent defects found
only by reading real traces. What this case demonstrates is the licensed
response: neither "specify everything perfectly up front" (the four defects
show this was not achieved even under a frozen contract) nor "edit the live
suite whenever a defect turns up" (which would silently invalidate every
number already reported under the old rule) — but a
[suite release](../GLOSSARY.md#suite-release): a written changelist whose
only admissible justification is a stated invariant violation, never a
model's score; a versioning mechanism that makes non-comparability a
tooling-enforced property rather than a documentation note
([cross-suite refusal](../GLOSSARY.md#cross-suite-refusal)); and unmodified,
labeled retention of every prior version. [CASE-004](CASE-004_harness-defects.md)'s
thirteen findings *are* criteria drift caught by instrument rather than by
anecdote — the same defects would otherwise have been folklore ("the S07
class always seemed odd") rather than a dated, gated, reproducible fix.

Chapter 03 defines [criteria drift](../GLOSSARY.md#criteria-drift) and the
suite-release discipline normatively, encoded generically in
[templates/EVAL_SUITE_RELEASE_CONTRACT.md](../templates/EVAL_SUITE_RELEASE_CONTRACT.md)
(suite identity and what changed vs. the prior version, ground-truth gates,
the cross-suite refusal requirement, the release checklist). Chapter 13
covers the [record of record](../GLOSSARY.md#record-of-record) angle this
case also exercises: superseded material is dated and kept, never silently
rewritten.

## What would NOT have worked

Patching the scorer, verifier, or generator in place the moment each defect
was noticed — considered and rejected by the release's own governing rule,
which structurally excludes justifying a change by a model's score: a mid-run
fix chosen after seeing a specific answer is not distinguishable, after the
fact, from tuning the instrument to that answer.

Publishing the pre/post score difference as a model-improvement number —
explicitly rejected in the project's own analysis, for the reason given
above: the delta conflates the model, the world the model was evaluated
against, and the scorer's rules, and isolates none of them.

Loosening the action rubric immediately after the earlier round's two
defensible-but-wrong answers, rather than logging it for a versioned
release — rejected at the time, and the review it was logged for is the
release this case describes; the candidate was still pending when the
release shipped, evaluated on its own merits rather than in response to any
single case.

## References

- [INT-CASE-009] — this case's entry in the source ledger.
- [EXT-EVAL-004] — EvalGen / "Who Validates the Validators" (Shankar et al.):
  the practitioner-study evidence that criteria and ground truth co-evolve as
  outputs are seen, and the source of "criteria drift" as this playbook uses
  the term.
- [CASE-004](CASE-004_harness-defects.md) — the technical content of the
  defects this release closed, and the detection mechanisms that found them.

---

[Index](../README.md) · [Glossary](../GLOSSARY.md)
