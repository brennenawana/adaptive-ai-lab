# CASE-007: A Deterministic Cascade Gate Reaches Near-Total Rescue

> Real empirical case from the FIS project (Fintech Integration Sandbox), a
> realistic synthetic fintech-operations laboratory used to develop this
> playbook's methodology.

**Source ID:** INT-CASE-007 · **Date:** 2026-08-16 · **Cited by:**
[08. Retrieval, Tools, Workflows, and Routing](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) ·
[10. Deployment and Operations](../10_DEPLOYMENT_AND_OPERATIONS.md)

## Situation

The project ran a local specialist model (Qwen3-8B Q4_K_M) against a frontier model
(Claude Opus 5) on the same 12-class investigation benchmark and, before building any
routing logic, measured the ceiling. An
[oracle analysis](../GLOSSARY.md#oracle-analysis) on the dev split (n = 48) found:
weak-only strict all-pass 35.4% (17/48), strong-only 91.7% (44/48), a perfect
router's ceiling 93.8% (45/48), and 58.3% (28/48) of cases where the weak model
failed but the strong model would have succeeded — the
"[rescue](../GLOSSARY.md#rescue)able" population any routing layer exists to serve.
Only 6.2% (3/48) of cases were unrecoverable by either tier. Projected economics: a
perfect router would cut reference cost 35% versus strong-only ($3.36 vs $5.16) at
+2pp quality. The oracle analysis made routing's value measurable and finite before a
line of gate logic was written.

## Decision faced

Given that a large share of the value sits in cheaply routing weak-fail cases to the
strong tier, should the [escalation](../GLOSSARY.md#escalation) gate be a learned
classifier or a [deterministic gate](../GLOSSARY.md#deterministic-gate) built only
from checkable output properties? The design chosen read exactly three
production-observable booleans at the decision point — after the weak model's parse
and verify step, before any strong call — and nothing else: whether structured
output was produced, whether the deterministic verifier passed, and whether the
verifier flagged an unsupported claim. No gold label, scenario identity, or
eval-only field was reachable from the gate; a dedicated no-leak test suite enforced
this at the module boundary. Candidate policies were nested by strictness (escalate
on missing output only ⊂ also escalate on any verifier failure), and the selection
rule was pre-registered before any live run: adopt the stricter policy unless it
costs more than 2 additional unnecessary escalations.

## Evidence

**Dev selection (replay).** The looser policy (missing output only) escalated 5/48
(10.4%), rescued 3, 0 unnecessary, all-pass 35.4%, caught 3 of 30 rescueable cases.
The stricter policy (any verifier failure) escalated 11/48 (22.9%), rescued 8, 0
unnecessary, all-pass 45.8%, caught 8 of 30. The stricter policy was adopted — well
inside its 2-unnecessary-escalation budget — and frozen.

**Live dev run** (same server session as its own weak-only control, 48/48 identical
output digests against that control):

| metric | weak-only | cascade | strong-only | oracle |
|---|---|---|---|---|
| strict all-pass | 29.2% (14) | **50.0% (24)** | 91.7% (44) | 91.7% (44) |
| verifier pass | 77.1% | **100%** | 97.9% | 97.9% |
| escalation rate | — | 22.9% (11/48) | 100% | — |
| unnecessary escalations | — | **0/48** | — | — |
| rescue rate | — | **90.9%** (10/11) | — | — |
| cost / attempted case | $0 | **$0.0235** | $0.1074† | $0.0764 |
| cost / successful case | $0 | **$0.0471** | $0.1172† | $0.0833 |
| wall p50 | 12.6 s | 16.9 s | 33.2 s | 42.9 s |

† frontier tokens under-reported by the reference CLI; strong-only cost is a floor.

**Test confirmation** — one run, dev-frozen policy, no re-tuning:

| metric | weak-only | cascade | strong-only | oracle |
|---|---|---|---|---|
| strict all-pass | 29.2% (28) | **49.0% (47)** | 99.0% (95) | 100% (96) |
| escalation rate | — | 21.9% (21/96) | — | — |
| unnecessary escalations | — | **0/96** | — | — |
| rescue rate | — | **90.5%** (19/21) | — | — |
| cost / successful case | $0 | **$0.0464** | $0.0973† | $0.0687 |
| wall p50 | 12.4 s | 14.5 s | 38.2 s | 48.2 s |

Dev's 50.0% estimate generalized to test's 49.0% with no tuning step between the two
splits — one nested threshold, one pre-registered rule.

**What escalation still missed.** 47 of 96 test cases where the weak model's answer
was schema-valid, well-cited, and calibrated — and simply wrong on root cause, or too
terse on evidence. These are [silent failures](../GLOSSARY.md#silent-failure): by
construction, a signal built from checkable output properties cannot see an answer
that is well-formed and confidently incorrect. This residual, not a defect in the
gate, is what motivated the next two milestones on the same track — and neither beat
the deterministic gate. A stronger local model (Nemotron 3.5 Lightning) nearly
eliminated the *silent*-failure family (23→4 of 48) but finished only 40% of cases
before hitting its frozen decode-length budget, so under the same cascade its
economics were worse, not better: cost/success $0.0868 vs $0.0545 at 66.7% vs 22.9%
strong-model calls, failing a pre-registered 6-criterion swap rule on 4 of 6
criteria. A learned router over production-observable trajectory features
([CASE-003](CASE-003_learned-router-leakage.md)) failed its own leakage audit.

**External corroboration.** A literature read of the four major published
cascade/router designs — FrugalGPT's trained regression gate, RouteLLM's
preference-label-trained router, AutoMix's self-verification POMDP, Hybrid LLM's
one-shot predictive router — found none uses a deterministic rule-based gate; this
project's verifier-signal gate sits outside the published design space, justified by
its own measured numbers rather than by precedent [EXT-ROUTE-001].

## What happened

The deterministic gate recovered about a quarter of the weak-to-strong quality gap
(test: 29.2% → 49.0% of a possible 99.0%) at ~22% strong-model calls — 78% fewer than
strong-only — with **zero unnecessary escalations on either split** and a ~90% rescue
rate on everything it did escalate. Cost per successful investigation roughly halved
versus strong-only and median latency was lower — 2.0× on dev (16.9 s vs
33.2 s) and 2.6× on test (14.5 s vs 38.2 s). Because its entire decision
surface was three production-observable booleans, it needed no training data, no
held-out label access, and no [leakage audit](../GLOSSARY.md#leakage-audit) — it was
leakage-immune by construction. It remained the project's production routing
mechanism through both follow-on attempts to close its residual gap.

## The generic lesson

When a task-level verifier already exists — schema validity, citation/evidence
checks, or any other checkable output property — a
[deterministic gate](../GLOSSARY.md#deterministic-gate) built only from those signals
is this playbook's default over a learned gate: auditable by inspection, immune to
the leakage failure mode that can undo learned routers, and, on this evidence, able
to reach near-total rescue with zero unnecessary escalations. Running an
[oracle analysis](../GLOSSARY.md#oracle-analysis) before building any router turns
"should we route at all, and how much can it possibly be worth" into a measured,
falsifiable, priced question instead of an assumption — and correctly bounded
expectations here to a 91.7%→93.8% ceiling, not a leap to near-100%. Neither obvious
next move — a bigger local model, or a learned router — automatically beats a
working deterministic gate; each has to clear its own pre-registered bar (a
cascade-economics swap rule; a leakage audit) before replacing it. A design with no
precedent in the published literature is not by itself evidence of a mistake: it can
mean the published designs assumed a precondition — no usable deterministic
verifier — that does not hold for every task, and the honest response is to state
the gap and let measured numbers carry the claim. Encodes:
[deterministic gate](../GLOSSARY.md#deterministic-gate) and
[oracle analysis](../GLOSSARY.md#oracle-analysis) (chapter 08); shadow/production
promotion discipline (chapter 10).

## What would NOT have worked

The looser policy (escalate only on missing structured output) left most of the
rescueable value on the table: 3 of 30 dev rescues against the stricter policy's 8 of
30, for less than half the escalation cost — proof that the more conservative-looking
choice was not the better one, and exactly why it was pre-registered as a compared
alternative rather than assumed. Swapping to a stronger local model without changing
the escalation budget did not improve the cascade: better completed-case quality was
more than offset by a 60% completion failure rate under the frozen decode budget,
driving 3× the strong-model calls at 60% higher cost per success than the existing
gate. A learned router trained on the same production-observable signals to catch the
residual silent-failure family failed its own pre-registered leakage audit
([CASE-003](CASE-003_learned-router-leakage.md)); promoting it on the strength of its
headline test number alone would have shipped a component that had learned template
identity, not answer correctness.

## References

- [CASE-003](CASE-003_learned-router-leakage.md) — the learned router built to close
  this gate's residual gap, and why it was not adopted in its place.
- [EXT-ROUTE-001] FrugalGPT/RouteLLM/AutoMix/Hybrid LLM cascade literature — none uses
  a deterministic rule-based gate; this gate sits outside that published design
  space.
- Governing chapters: [08](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md),
  [10](../10_DEPLOYMENT_AND_OPERATIONS.md).
- Glossary: [deterministic gate](../GLOSSARY.md#deterministic-gate),
  [oracle analysis](../GLOSSARY.md#oracle-analysis),
  [cascade](../GLOSSARY.md#cascade), [escalation](../GLOSSARY.md#escalation),
  [rescue](../GLOSSARY.md#rescue), [silent failure](../GLOSSARY.md#silent-failure).
