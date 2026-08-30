# SCENARIO-03: Learned-Router Leakage Behind a Group-Identity Ceiling

> [Index](../README.md) · [Examples](README.md)

**An invented scenario.** The project is fictional; the lesson and the reasoning are the
part to take seriously.
**Illustrates:** [03. Evaluation Foundation](../03_EVALUATION_FOUNDATION.md) · [08. Retrieval, Tools, Workflows, and Routing](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) ·
[13. Governance, Provenance, and Security](../13_GOVERNANCE_PROVENANCE_AND_SECURITY.md)

---

## Situation

The argument had two sides and both of them were right about something. One side wanted a
small classifier that reads a finished answer and predicts *this one is probably wrong,
send it up to the expensive model.* The other side objected that the only dependable
signal for "wrong" is the correct answer, that production never has the correct answer,
and that whatever such a classifier ends up learning will therefore not be the thing
anyone thinks they are buying.

The system being argued over triages service-disruption reports for a city transit agency.
An operator files free text — *"southbound held 11 minutes at Tenth and Vine, doors would
not close, no alarm"* — and an assistant reads it alongside the vehicle telemetry log, the
schedule-adherence feed, and the maintenance history, then produces a structured root-cause
classification with citations to the records it used.

An earlier round had frozen a two-stage arrangement. A small local model answers first. A
gate reads the verifier's output and hands the case up to a frontier model only on
production-observable structural failure — malformed output, a missing citation, a
citation pointing at a record that does not exist. Cheap model first, expensive model only
when needed: that is a weak-to-strong [cascade](../GLOSSARY.md#cascade), handing a case up
is [escalation](../GLOSSARY.md#escalation), and because the rule is a fixed check with no
model in it, this one is a [deterministic gate](../GLOSSARY.md#deterministic-gate).

The gate closed about a quarter of the quality gap. It left the larger share untouched:
**53 of 112 test cases where the local model's answer was well-formed, properly cited,
verifier-clean, and simply wrong.** A structural gate cannot see those by construction —
there is nothing structurally wrong to detect. They are
[silent failures](../GLOSSARY.md#silent-failure).

So the next round took the first position seriously enough to test it. Could a small
classifier — trained only on things visible in production, never on the correct answer —
look at a local model's attempt and flag it for escalation before anyone knows whether it
is wrong? A component like that is a [learned router](../GLOSSARY.md#learned-router).

The team's own frozen contract named the risk up front, before anything was trained. The
test suite is built from 14 incident templates, 8 cases each. A router could learn *which
template this is* instead of *whether this particular answer is wrong* — and a naively
validated version of that router would still look good.

## Decision faced

Should the deterministic gate be replaced or supplemented by a learned router over a
46-feature snapshot of production-observable signals, to catch the verifier-clean failures
the structural gate cannot see?

The contract was frozen in two commits, both before any candidate was scored on the
validation split: a skeleton (feature allowlist, grouping, cross-validation protocol,
candidate families, threshold grid, test-unlock mechanics), then a numeric amendment.

The admissibility bar was explicit and it is the whole hinge of this scenario. A candidate
earns eligibility only by clearing a pre-registered score floor under
**leave-one-group-out cross-validation** — hold out an entire template, train on the other
thirteen, and see whether the router transfers to a template it has never seen. That is
the [leakage audit](../GLOSSARY.md#leakage-audit) protocol, and it was chosen precisely
because the feature set could not exclude template identity outright.

The score is AUC: a number from 0 to 1 for how well a classifier ranks the cases it should
flag above the ones it should not. Perfect ranking is 1.0. Random guessing is 0.5. The
pre-registered floor was 0.60.

## Evidence

**The feature contract.** 46 named features: 9 model/runtime, 13 verifier, 7 tool
trajectory, 17 answer echo. An explicit forbidden list barred every gold field, plus
`split`, `template`, `category`, `seed`, and any incident identifier. 38 dedicated
leak-guard unit tests and 51 pipeline tests ran before any validation replay, alongside a
five-lens adversarial audit.

**What the audit found anyway.** Three features that are entirely legitimate and entirely
production-observable — the number of feed lookups, the number of maintenance-history
queries, and the prompt token count — turn out to be *constant within a template*. Given
the fixed evidence bundle each template assembles, they do not vary. A nearest-neighbour
classifier over just those three recovered the template for **50 of 56** validation cases.
Behavioural features clustered the same way: output length and reasoning length are largely
template properties.

Nothing in the allowlist *names* the template. Bundle size and tool-call shape
reconstruct it anyway. That is indirect [leakage](../GLOSSARY.md#leakage), and a
name-level allowlist cannot catch it.

**The comparator that makes the whole thing legible.** Build the dumbest possible model:
predict wrong/right from the template alone, with no trajectory signal at all. That is the
[group-identity ceiling](../GLOSSARY.md#class-identity-ceiling). It scored training
stratified AUC **0.88** for the incumbent local model and **0.91** for the challenger. The
best *eligible* learned candidate reached 0.89 for the incumbent — 0.01 above the ceiling —
and never exceeded it for the challenger.

**The primary protocol — leave-one-group-out, pooled out-of-fold AUC:**

| local model | logistic (all features) | logistic (core) | gradient tree | eligibility floor |
|---|---|---|---|---|
| incumbent | 0.27 | 0.31 | 0.48 | 0.60 |
| challenger | 0.22 | 0.26 | 0.19 | 0.60 |

No candidate cleared the floor for either model. Per-fold AUC on eight of the incumbent's
mixed templates, logistic-all-features: 0.00, 0.12, 0.55, 0.50, 0.83, 0.61, 0.50, 0.00 —
mean **0.39**. Below 0.50 is worse than a coin flip. Nothing transferred to a held-out
template.

The labels were also clustered enough to blunt the test's own power: P(wrong | template)
ran from 0.12 to 1.0, and the minority label had n ≤ 1 in 9 of the 12 mixed templates.

**Two amendments, both disclosed as moving toward a pass.** After training cross-validation
and before any validation replay, the contract was amended twice. A secondary
deployment-matched protocol was registered — seed-stratified, not grouped — because the
primary protocol's pooled score is provably biased toward the null when labels are
group-clustered. And the a-priori escalation caps were replaced with training-derived
ones: 58% of the incumbent's verifier-clean subset was wrong, so even a perfectly-ranked
router needed about 34% escalation, and the original caps would have rejected volume rather
than degeneracy. Both are recorded as audit-driven amendments in the direction of a pass,
per this playbook's [amendment legitimacy](../GLOSSARY.md#amendment-legitimacy) rule.

**Under the secondary protocol,** the frozen incumbent router reached test strict all-pass
**67.9%** (76 of 112) against the deterministic gate's 52.7% (59 of 112), at 33.9%
escalation (38 of 112). The pre-registered test reading asked for at least 12 pp over the
deterministic gate at no more than 40% escalation. A 15.2-pp gain at 33.9% escalation
formally meets it.

Then the same look was checked against a random baseline. Because 47 of the 112 are cases
the frontier model fixes, escalating **any** 38 at random recovers about 16 on expectation.
The router recovered 17. Hypergeometric **p ≈ 0.41**. The reading had almost no power to
tell the router apart from a coin.

The challenger's router — 69.6% against its own gate's 66.1%, a 3.6-pp gain — did not come
close to its own reading.

**The post-hoc check that settled it.** On the same opened look: escalate every case from
the four templates the local model historically failed most. No trajectory features. No
model. Just "these four kinds of incident go straight to the big model." That rule
escalated 32 cases, 28 of which were genuinely wrong, and recovered **25 of the 53** — more
than the frozen router's 17, with fewer escalations and only 4 wasted.

## What happened

The honest read went into the round's own report. The router learned *which templates the
local model fails on* — a task-difficulty prior wearing the costume of a correctness
signal. It says nothing reusable about any individual answer, which is what the team
believed they were buying. A thin genuine within-template signal did exist for the
challenger, in answer length and reasoning share, but not enough to clear the
leave-one-group-out floor.

So the deterministic gate stayed as the system's routing mechanism. Future work was pointed
at targeted specialization on the templates that fail systematically. A template-difficulty
router was kept only as an interim gate, and described in writing as a difficulty prior
rather than a validated content router.

Even on cost alone the router lost: 48% more per successful case and 2.2× the median
latency, for a gain indistinguishable from escalating at random.

## The generic lesson

**A learned component trained on features that correlate with a grouping can learn the
grouping instead of the thing you wanted.** Template, class, session, document, customer,
region — if outcomes cluster inside it, a classifier will happily discover it and report
excellent numbers.

Three practices turn that from a hidden failure into a visible one.

**Validate by holding out whole groups.** Leave-one-group-out cross-validation asks the
only question that matters at deployment: does this transfer to a group it has never seen?
Pooled cross-validation under group-clustered labels is optimistic by construction, so it
cannot answer that, however carefully it is run.

**Always build the group-identity ceiling comparator.** Predict the label from group
membership alone. That number is what your router must beat, and beating it by 0.01 is not
beating it. Without that comparator you have no way to tell a router that understands
answers from a router that has memorized which templates are hard — and both produce the
same AUC.

**Treat a name-level feature allowlist as necessary, not sufficient.** Excluding gold
fields and identifiers is table stakes. It does not stop a legitimate, production-available
feature from acting as a proxy for the identity you excluded — bundle size, tool-call
count, and prompt length all did here. Only an adversarial feature-provenance review, one
that actively tries to reconstruct the group from the allowed features, surfaces that.

Two more habits made the final number readable. A single held-out confirmation can clear a
pre-registered bar with p ≈ 0.4 against a random baseline of the same size, so compute
that baseline *from the same look*. And disclose amendments that move toward a pass,
rather than presenting the eventually-frozen protocol as if it had been the only one
considered.

## What would NOT have worked

**Trusting the deployment-matched protocol on its own.** It is exactly the protocol under
which every candidate looked strong, with training AUC up to 0.92, and one reached a formal
test pass. Had the grouped protocol not been registered first, the round would have shipped
a router.

**Reading the test result as evidence, without the baseline.** 67.9% against 52.7% is a
15-point gain. It looks like a win in a slide. Without the random-escalation comparison
computed from the same look, nobody would have seen that random escalation does
statistically as well.

**Relaxing the escalation caps quietly.** The cap change was correct on the merits. Making
it without recording that it was training-evidence-driven, and which direction it pushed
the verdict, would have destroyed the one fact that made the final result interpretable.

**Assuming the clustering only hurts the router.** It also blunts the test that judges the
router: with the minority label at n ≤ 1 in most mixed templates, several folds had almost
no signal in either direction. [SCENARIO-02](SCENARIO-02_clustered-eval-effective-n.md)
covers what the same clustering does to a plain model-versus-model comparison.

**How this lands on your project.** If you have a classifier, router, reranker, guardrail,
or scoring model in your stack, ask what your evaluation items were generated from —
templates, source documents, customers, sessions. That is your grouping. Then run two
things this week. First, train the dumbest possible model that uses *only* group
membership and record its score; that is your bar. Second, re-validate your real model
with entire groups held out, not random rows. If the gap between the two is small, or the
held-out-group score collapses toward chance, your component has learned which group it is
looking at. It may still be useful — knowing which cases are historically hard is worth
something — but call it what it is, price it against the lookup table that does the same
job for free, and never claim it generalizes to a group it has never seen.

## References

- [EXT-ROUTE-001] FrugalGPT / RouteLLM / AutoMix / Hybrid-LLM cascade literature.
  RouteLLM's near-random out-of-distribution result without task-specific augmentation is
  the closest external caution to what this scenario measures directly.
- Governing chapters: [03](../03_EVALUATION_FOUNDATION.md),
  [08](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md).
- Glossary: [leakage audit](../GLOSSARY.md#leakage-audit),
  [class-identity ceiling](../GLOSSARY.md#class-identity-ceiling),
  [learned router](../GLOSSARY.md#learned-router),
  [amendment legitimacy](../GLOSSARY.md#amendment-legitimacy),
  [silent failure](../GLOSSARY.md#silent-failure),
  [cascade](../GLOSSARY.md#cascade), [escalation](../GLOSSARY.md#escalation),
  [deterministic gate](../GLOSSARY.md#deterministic-gate).
- Related: [SCENARIO-02](SCENARIO-02_clustered-eval-effective-n.md) — the clustered-power
  arithmetic behind the weak folds above.

---

> [Index](../README.md) · [Examples](README.md)
