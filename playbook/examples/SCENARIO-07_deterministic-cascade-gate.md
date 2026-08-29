# SCENARIO-07: Deterministic Cascade Gate

> [Index](../README.md) · [Examples](README.md)

**An invented scenario.** The project is fictional; the lesson and the reasoning are the
part to take seriously.
**Illustrates:** [08. Retrieval, Tools, Workflows, and Routing](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md) ·
[10. Deployment and Operations](../10_DEPLOYMENT_AND_OPERATIONS.md)

## Situation

*Continue current dose.* That is the entire prescriber note, and the pharmacy's record
holds two different current doses for this patient — one from a clinic visit in March, one
from a hospital discharge in June. Below it in the queue sits a prescription for a 90-day
supply of a drug this patient's plan pays for 30 days at a time.

Neither can be filled exactly as written, so both land on the clarification desk of a
mail-order pharmacy. Something has to read the prescription, that patient's dispensing
history for the past year, the active medication list, and the plan's rules for the drug,
then write one short record: what is actually unresolved, which record lines show it, and
what the pharmacist should do next. About 9,000 clarifications a month.

Two models could do the job. A small open-weights model — a quantized 8B — running on a
machine the team already owned, free at the margin and often wrong. And a hosted frontier
model, reliable, billed at roughly $0.09 per clarification. Sending every clarification to
the hosted model would cost about $810 a month.

The obvious design is to let the small model try first and hand the hard ones to the
big one. That shape has a name — a [cascade](../GLOSSARY.md#cascade) — and the part that
decides which clarifications get handed up is the gate.

Before writing any gate, the team asked a narrower question: **how much is a gate worth at
its absolute best?** Imagine a magic gate that already knows which model will succeed on
each clarification and always picks that one. It cannot exist, but you can compute what it
would have scored, because you have both models' answers on a fixed set of cases. That is
an [oracle analysis](../GLOSSARY.md#oracle-analysis): two runs and some arithmetic.

On the 60-case development split, with a strict pass meaning *correct issue named,
complete cited evidence, correct recommended action*:

- small model alone: **38.3%** (23/60)
- hosted model alone: **90.0%** (54/60)
- the magic gate's ceiling: **93.3%** (56/60)
- clarifications the small model failed and the hosted model would have got right — the
  [rescueable](../GLOSSARY.md#rescue) population, the only thing a gate exists to
  serve: **55.0%** (33/60)
- clarifications neither model gets right: **6.7%** (4/60)

Two facts fall out. The most a perfect router could add over always using the hosted model
is 3.3 points. And it would get there paying for 33 hosted calls instead of 60 — $2.97
against $5.40 on this split, a 45% cut. So routing was worth building, and worth *only that
much*: a more useful thing to know than "routing sounds promising."

## Decision faced

The value sits in cheaply spotting the clarifications the small model got wrong. Two ways
to spot them.

**Train a classifier** on past runs to predict "this answer is probably wrong" — a learned
gate. **Or write a rule** over things the system can already check about the answer, with
nothing learned in it at all — a [deterministic gate](../GLOSSARY.md#deterministic-gate).

The team already had a verifier: a plain program that checks every cited record line
exists, checks it carries the date, quantity or strength the answer claims, and flags any
assertion with nothing cited behind it. So the rule had three yes/no facts at the decision
point — after the small model's answer is parsed and verified, before any hosted call:

1. Did it produce a parseable answer at all?
2. Did the verifier pass?
3. Did the verifier flag a claim with no supporting record?

Nothing else was reachable. Not the reference answer, not the case's identity in the test
set, not any field that exists only inside the evaluation. A dedicated test suite enforced
that at the module boundary, so a future edit could not quietly widen the gate's view.

Two candidate policies, one nested inside the other:

- **Loose** — escalate only when there is no parseable answer.
- **Strict** — escalate on *any* verifier failure, which includes the loose case.

The choice rule was fixed in writing before any run
([pre-registration](../GLOSSARY.md#pre-registration)): adopt the strict policy unless it
costs more than 2 additional *unnecessary* escalations — escalations of clarifications the
small model had already answered correctly, where the hosted call buys nothing but spend.

## Evidence

**Selecting the policy, on stored answers.** Replayed against the development split's saved
outputs, the loose policy escalated 6/60 (10.0%), rescued 4 of the 33 rescueable cases,
made 0 unnecessary escalations, and lifted the strict pass rate to 45.0%. The strict policy
escalated 14/60 (23.3%), rescued 11, also made 0 unnecessary escalations, and reached
56.7% — well inside its budget of 2. It was adopted and frozen.

**Running it live.** The cascade ran against its own small-model control in one server
session and reproduced that control's outputs exactly on all 60 cases. The rescue count
moved by one from the replay because the hosted model does not reproduce: the replay reused
stored answers, the live run bought fresh ones.

| metric | small only | cascade | hosted only | oracle ceiling |
|---|---|---|---|---|
| strict pass | 38.3% (23) | **58.3% (35)** | 90.0% (54) | 93.3% (56) |
| verifier pass | 76.7% (46) | **100%** | 96.7% (58) | — |
| hosted calls | 0 | 23.3% (14/60) | 100% | 55.0% (33/60) |
| unnecessary escalations | — | **0/60** | — | — |
| rescue rate | — | **85.7%** (12/14) | — | — |
| cost / clarification | $0 | **$0.021** | $0.090 | $0.050 |
| cost / successful clarification | $0 | **$0.036** | $0.100 | $0.053 |
| wall p50 | 9.4 s | 12.1 s | 26.5 s | n/a† |

† Not runnable: reaching the oracle's answer requires both models on every case.

**Confirming it, once, on held-out data** — 120 cases, frozen policy, no retuning:

| metric | small only | cascade | hosted only | oracle ceiling |
|---|---|---|---|---|
| strict pass | 37.5% (45) | **56.7% (68)** | 91.7% (110) | 95.0% (114) |
| hosted calls | 0 | 21.7% (26/120) | 100% | 60.8% (73/120) |
| unnecessary escalations | — | **0/120** | — | — |
| rescue rate | — | **88.5%** (23/26) | — | — |
| cost / successful clarification | $0 | **$0.034** | $0.098 | $0.058 |
| wall p50 | 9.4 s | 11.6 s | 27.9 s | n/a |

The development estimate of 58.3% landed at 56.7% on data the policy had never seen, with
no tuning step in between. One threshold, chosen by one rule, written down first.

**What the gate could not see.** 49 of the 120 held-out clarifications were failures the
gate left alone: parseable, every citation real, verifier clean — and simply naming the
wrong issue, calling something a dosing discrepancy when the record shows a lapsed prior
authorization. These are [silent failures](../GLOSSARY.md#silent-failure). From where the
gate stands, a well-formed confident wrong answer looks exactly like a well-formed
confident right one, so a rule built from checkable properties cannot catch them. That
residual is a limit of the signal, not a bug in the rule.

**Two attempts to close it, both refused.** A 27B dense open-weights model in place of the
8B nearly eliminated the silent-failure family — 49 down to 12 — but finished only 63% of
clarifications inside the frozen generation budget, so the cascade escalated 55.8% of
traffic instead of 21.7%. Quality rose about 5 points; cost per successful clarification
went from $0.034 to $0.081. It failed the pre-registered swap rule on 4 of its 6 criteria.
A learned gate trained on the same signals scored competitively and then failed its
[leakage audit](../GLOSSARY.md#leakage-audit) — the failure mode
[SCENARIO-03](SCENARIO-03_learned-router-leakage.md) takes apart in full.

**Where this sits in the literature.** The four best-known published cascade and router
designs all use a *learned* gate [EXT-ROUTE-001]. None uses a deterministic rule over
verifier output. Worth stating plainly rather than hiding: this design has no published
precedent, and its case rests on its own measured numbers.

## What happened

The rule shipped. On held-out data it closed a bit over a third of the gap between the two
models — 37.5% to 56.7% against a hosted-only 91.7% — paying for 21.7% of the hosted calls,
at about a third of hosted-only's cost per success and under half its median wall time.
Zero unnecessary escalations on both splits, and 86% to 89% of escalations succeeded.

At 9,000 clarifications a month that is about $176 against $810. Note that the oracle ceiling
would have cost *more* than the shipped gate — about $493 — because a perfect router chases
every rescueable case. The ceiling prices the best quality available, not the cheapest
system.

Because the gate's whole decision surface was three booleans a program computes, it needed
no training data, no access to held-out labels, and no leakage audit. It could not leak.
You can read it in one screen and know what it will do.

## The generic lesson

**Measure the ceiling before you build the router.** An oracle analysis turns "should we
route, and how much could it possibly be worth" from an assumption into a priced,
falsifiable number, for the cost of two runs you wanted anyway. Here it capped expectations
at a 3.3-point gain over hosted-only — not a leap toward perfection — before a line of gate
logic existed.

**If you already have a verifier, start with a rule, not a model.** A gate built only from
checkable properties of the output is this playbook's default over a learned one: you can
audit it by reading it, it cannot learn something it was not supposed to see, and on this
evidence it rescued nearly everything it escalated while wasting nothing.

**Neither obvious upgrade beats a working rule for free.** A bigger local model and a
learned router are both reasonable next moves. Each has to clear a bar written down in
advance — a swap rule on cascade economics, a leakage audit — before it replaces something
that already works.

**A design with no precedent is not automatically a mistake.** It can mean the published
designs assumed something untrue of your task — here, that no usable deterministic verifier
exists. Say so, and let the measured numbers carry the claim.

**How this lands on your project.** If you are considering routing, do the oracle
arithmetic this week: run both tiers on one fixed set of cases, count how many the cheap
tier fails and the expensive tier would have saved, and price it. If that number is small,
you just saved yourself a router. If it is large, ask what your system already checks about
its own output — schema validity, a citation that resolves, a test that runs, a total that
reconciles. Those checks are a gate. Try them before you train anything, and write down in
advance what would make you replace them.

## What would NOT have worked

**The more cautious-looking policy.** Escalating only on missing output — the choice that
touches the least traffic — left most of the value unclaimed: 4 of 33 rescueable cases
against the strict policy's 11, to save 8 hosted calls out of 60. This is why it was
pre-registered as a compared alternative rather than assumed safer.

**Swapping in the bigger local model on its quality numbers.** Its completed answers were
genuinely better. It also failed to finish 37% of clarifications inside the frozen
generation budget, which drove 2.6× the hosted calls and 2.4× the cost per success. On the
metric that mattered — cost per *successful* clarification — it was worse, and the
pre-registered swap rule
caught what a headline accuracy comparison would not have.

**Promoting the learned gate on its headline test score.** It looked competitive. It had
learned to recognize which kind of clarification it was reading rather than whether the
answer was right, and only its leakage audit surfaced that.

## References

- [SCENARIO-03](SCENARIO-03_learned-router-leakage.md) — a learned gate over
  production-observable signals, and the audit that refuses it.
- [EXT-ROUTE-001] Cascade and learned-router literature — all four major published designs
  use a learned gate; a deterministic verifier-signal gate sits outside that design space.
- Governing chapters: [08](../08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md),
  [10](../10_DEPLOYMENT_AND_OPERATIONS.md).
- Glossary: [deterministic gate](../GLOSSARY.md#deterministic-gate),
  [oracle analysis](../GLOSSARY.md#oracle-analysis),
  [cascade](../GLOSSARY.md#cascade), [escalation](../GLOSSARY.md#escalation),
  [rescue](../GLOSSARY.md#rescue), [silent failure](../GLOSSARY.md#silent-failure),
  [leakage audit](../GLOSSARY.md#leakage-audit).

---

> [Index](../README.md) · [Examples](README.md)
