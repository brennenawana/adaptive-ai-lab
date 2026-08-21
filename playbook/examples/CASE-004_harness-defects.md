# CASE-004: Harness Defects as Instrument Findings

> Real empirical case from the FIS project (Fintech Integration Sandbox), a
> realistic synthetic fintech-operations laboratory used to develop this
> playbook's methodology.
>
> Source: [INT-CASE-004] · Dates: 2026-08-15 – 2026-08-18 · Cited by:
> [chapter 00](../00_PRINCIPLES_AND_SCOPE.md) (P1, P2) ·
> [chapter 02](../02_EXECUTION_SYSTEM_MODEL.md) ·
> [chapter 03](../03_EVALUATION_FOUNDATION.md)

## Situation

FIS evaluates investigator systems on a synthetic fintech-operations task: given a
customer-support case (a declined card, a duplicate charge, a reconciliation
mismatch), the system calls a fixed tool set, diagnoses the root cause from a
closed 12-class taxonomy (`S01`–`S12`), cites the entity IDs its diagnosis rests
on, and recommends one sanctioned next action. A deterministic scorer checks the
output schema, a verifier checks that every cited ID was actually observed
through a tool call rather than invented, and a forbidden-claim detector
penalizes asserting harm (`insufficient_funds`, `fraud_confirmed`, …) the
evidence does not support. Two weaker local arms and one frontier arm ran the
identical scenarios under the same fixed evidence plan, so any score gap was
meant to isolate reasoning quality, not tool access.

Between the first 12-case pilot (2026-08-15) and the third corpus release,
"Suite v3" (2026-08-17/18), the corpus grew from 12 to 288 seeded scenarios
(144 train / 48 dev / 96 test) across three generations of the harness.

## Decision faced

At several points in this timeline a class or arm scored badly, or
surprisingly, and the team had to choose where to spend the next unit of
effort: the more attractive-looking work of tuning the model-facing side
(prompt, model, budget), or auditing the instrument first. The project's own
precedence rule — no score is trusted until reachability, inversions, and
cross-arm disagreement have been checked; this is
[RC-1](../GLOSSARY.md#canonical-failure-taxonomy) in the canonical failure
taxonomy and always ranks first — forced the second choice every time. This
case is the record of what that discipline found: thirteen harness/scenario
defects, each initially indistinguishable from a weak model, none of them
fixed by touching the model.

## Evidence

| # | Milestone | Defect | Found by | Measured effect |
|---|---|---|---|---|
| 1 | Pilot (n=12) | Grammar compiler rejected `minLength`/`maxLength` in the output schema | Every local call returned HTTP 400 | 0% of local calls completed until fixed |
| 2 | Pilot (n=12) | Verifier rejected citations that named the tool rather than the underlying service | Manual review of all 12 traces | 11 of 12 *correct* citations scored as fabrications |
| 3 | Pilot (n=12) | Fixed-evidence tool plan never fetched the webhook/delivery history at all | Manual trace review | Required evidence structurally unreachable for 4 of 12 classes |
| 4 | Scale-up (12→288) | Entity IDs (counter + 3 random digits) collided across same-class scenarios | Dedicated uniqueness test written for the scale-up | Would have spliced one scenario's evidence into another's |
| 5 | Scale-up | Scenario primary key collided across splits — two different seeds from two different splits rendered the same id | Same uniqueness test | Would have silently defeated the disjoint train/test seed ranges meant to prevent leakage |
| 6 | Corpus regeneration | Webhook-delivery evidence unreachable by any tool call for the entire pre-regeneration corpus (0 of 312 deliveries) | Measured [reachability ceiling](../GLOSSARY.md#reachability-ceiling) per class, replayed against the built corpus | 5 of 12 classes capped below the 0.8 pass threshold — ceilings of 0.250–0.500 — regardless of model quality |
| 7 | Corpus regeneration | A "cross-customer clustering" class was defined but every tool was keyed by single-customer id, and the shared event clock let a per-customer backdate scatter the cluster across a month | Ceiling review of a 0.000 root-cause rate across every case in that class | The class was unwinnable in principle, not merely hard |
| 8 | Rebaseline | Ledger-entry evidence was returned sorted by `posted_at` (stamped from `occurred_at` — true event time, deliberately not arrival time, so it would not itself hide reordering) with `posting_seq` never exposed, which is exactly what one class's fault signature hinges on revealing | Weak-beats-strong [inversion](../GLOSSARY.md#inversion-check): the frontier arm scored 12.5% on that class while the *weaker* local arm scored higher | Frontier score on the class went 0.125 → 1.000 once entries were returned in posting order with `posting_seq` included |
| 9 | Rebaseline | Forbidden-claim detector was a bare substring match with no negation handling | Reviewing the frontier arm's 7 flagged "forbidden claims" against its own well-cited reasoning — implausible on its face for that arm | All 7 were refutations (e.g. "…not caused by insufficient funds"); corrected all-pass rose from 91.7% (as scored) to 99.0% |
| 10 | Suite v3 | Background scenario activity was generated but never published through the event pipeline, leaving one class's fault fingerprint present as unlabeled ambient noise in six other classes | Cross-arm disagreement review, deferred rather than patched mid-baseline | Fixed by publishing every background event through the real pipeline instead of writing it directly |
| 11 | Suite v3 | A declined-transaction class drew its amount and the account balance independently; in 3 of 24 worlds the declined amount exceeded the available balance | Same review | Briefly made a forbidden hypothesis *data-consistent* with the world in those cases |
| 12 | Suite v3 | Forbidden-claim polarity bug generalized: a lookback-only window, a dead boundary guard, and lost cues at the start of a sentence or field | Same review; one persisted real false positive replayed against the fix | Replaced with a documented, bidirectional same-sentence rule, versioned in the scorer |
| 13 | Suite v3 | The verifier harvested most observed-id fields but not the one key a required tool response returned directly to the model | Same review | A correct citation of evidence the model had actually been shown was scored as fabrication |

Rows 4–5 were caught by an ordinary engineering invariant test, not by a
statistical signal — worth keeping distinct from the other eleven, which were
only visible once the suite had enough classes and enough arms to expose a
per-class ceiling, an inversion, or a disagreement between arms.

## What happened

None of the thirteen defects were fixed by changing a model, a prompt, or a
generation budget. Each was a scored, reproducible property of the evaluation
instrument, and each was fixed at the instrument. The task ontology's own
evidence-reachability invariant states the discipline plainly, from direct
experience: it was violated across the entire corpus for one release cycle,
and "the scores looked like a weak model" — after the fix, the measured
reachability ceiling is 1.000 for all twelve classes.

The Suite v3 release, which closed defects 10–13, added 166 new automated
tests (69 corpus-wide scenario invariants, 32 forbidden-claim polarity
fixtures, 17 verifier fixtures, 5 database-gated corpus checks, 2
reference-sanity checks, and a set of revised pipeline tests), all
protecting exactly the invariants these defects had violated. Release gates
required the measured per-class reachability ceiling to be 1.000 with zero
capped classes on both the dev and test splits, and required a
[frontier-saturation check](../GLOSSARY.md#frontier-saturation-check): the
strongest available arm had to run to completion on the corpus with no
suite change following it. It passed at 48/48 on the sanity split. A suite
the strongest arm cannot approach its own measured ceiling on is
presumptively broken; by the release gate, this one no longer was — on the
96-case confirmation split the frontier arm's corrected all-pass rate reached
99.0%, essentially saturating the instrument.

## The generic lesson

Validate the instrument before crediting or blaming the model — this
playbook's [P2](../00_PRINCIPLES_AND_SCOPE.md). Concretely, three signals
catch most instrument defects, and none of them require inspecting failures
by hand at scale: measure the per-stratum
[reachability ceiling](../GLOSSARY.md#reachability-ceiling) against the built
corpus, not argued from the generator; check for weak-beats-strong
[inversions](../GLOSSARY.md#inversion-check) per stratum; and review
cross-arm or cross-run disagreement before accepting a surprising number in
either direction. All three are statistical properties of a large-enough
evaluation — they exist because the suite has many cases, many classes, and
multiple arms, which is why breadth in an evaluation corpus is not padding.
A small minority of instrument defects (here, two of thirteen) are instead
ordinary engineering bugs, caught by ordinary invariant and uniqueness tests
— worth having regardless, but a different mechanism from the other three.

Chapter 03 operationalizes this as
[static integrity gates](../GLOSSARY.md#static-integrity-gates) that run on
the full corpus, always, and are protected from subsetting precisely because
they are the instruments that catch instrument defects; the release
discipline that closed defects 10–13 is generalized in
[templates/EVAL_SUITE_RELEASE_CONTRACT.md](../templates/EVAL_SUITE_RELEASE_CONTRACT.md),
which requires per-stratum ceilings to be measured and printed and a
frontier-saturation check before any suite is released. [CASE-009] is the
governance side of the same release: how the fixes for defects 10–13 were
batched into one pre-registered, versioned release rather than patched in
place.

External corroboration for the scale of the effect: a large-scale benchmark
curation effort found that trimming a task set from 1,699 to 500 human-vetted
tasks moved the measured solve rate from 16% to 33.2% [EXT-EVAL-005] — a
comparable share of an apparent capability gap turning out to be the
instrument, not the systems under test.

## What would NOT have worked

Patching the forbidden-claim detector immediately once defect 9 surfaced, with
a quick negation-guard heuristic, was considered and rejected: a negation
guard is itself a heuristic that can produce false *negatives*, and for a
harm-weighted metric a false negative — a real forbidden claim scored clean —
is the dangerous direction. The reported number was corrected; the detector
itself was deliberately left for a scoped semantics decision rather than a
same-day patch.

Fixing defects 10–13 one at a time, in place, as each was noticed mid-baseline,
was rejected in favor of batching them into one pre-registered release with a
written changelist, because a mid-run fix chosen after seeing a model's output
is not distinguishable, after the fact, from tuning the instrument to that
model's answers. The release's own governing rule states it directly: no
change is justified by, or chosen after looking at, any model's score.

Treating the pre- and post-fix score deltas as a model-quality signal would
also not have worked, and was explicitly rejected in the project's own release
analysis: the same model on the same seed faces a different world in several
classes, a scorer with corrected polarity in every class, and a larger
observable-evidence set after these fixes — the delta mixes at least three
effects, none of which is the model changing.

## References

- [INT-CASE-004] — this case's entry in the source ledger.
- [EXT-EVAL-005] — SWE-bench Verified curation: external corroboration that
  benchmark curation, not model improvement, explains a comparable share of an
  apparent capability gap.
- [CASE-009](CASE-009_suite-versioning-criteria-drift.md) — the versioning and
  release-governance process that closed defects 10–13 in this case.

---

[Index](../README.md) · [Glossary](../GLOSSARY.md)
