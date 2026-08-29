# SCENARIO-05: Hardware Purchase Discipline

> [Index](../README.md) · [Examples](README.md)

**An invented scenario.** The project is fictional; the lesson and the reasoning are the
part to take seriously.
**Illustrates:** [06. Inference Performance and Capacity](../06_INFERENCE_PERFORMANCE_AND_CAPACITY.md) ·
[11. Economics, Hardware, and Cloud](../11_ECONOMICS_HARDWARE_AND_CLOUD.md)

## Situation

Somebody has to approve a hardware order this week, or decline it. The proposal is a
two-card workstation build against a notional $5,000 budget — a second accelerator, and
ideally a bigger one — and the case for it is an honest one: the last evaluation round
took twenty hours, and the single card in the building was busy for nearly all of them.

The buyer would be a legal aid clinic, which is building a tool that reads a new client's
intake notes and filed documents, then drafts the case summary a supervising attorney
currently writes by hand — what is being claimed, what deadlines are live, what evidence
is missing. Client files are confidential and cannot leave the building, so the models run
on the clinic's own hardware rather than a managed API. That hardware is one machine, with
one 16 GB consumer accelerator in it.

That single card had just carried the project's second evaluation round: four candidate
models compared across 432 summary-drafting items, one at a time, twenty hours of wall clock
end to end. Zero errors, zero retries, nothing crashed. It simply took all day and most
of a night, because everything went through one card in a queue. The felt experience of
that round is what produced the proposal: buy more GPU, and rounds like this one get
faster.

Nothing was ordered. Instead the project did two things first. It reconstructed exactly
where those twenty hours went, from run-ledger timestamps, database insert times,
surviving server logs, and commit times — a
[performance autopsy](../GLOSSARY.md#performance-autopsy). And it sent the draft
hardware proposal to an independent reviewer whose job was to try to kill it.

## Decision faced

Commit $5,000 to $8,000 of capital to a two-card workstation now, on the intuition that
more and bigger GPUs speed up rounds shaped like this one. Or defer every purchase until
there is a measured answer to a narrower question: what was the twenty hours actually
made of, and which part of it would a second card have touched?

## Evidence

**What the twenty hours actually were (measured).** 92.0% of the wall clock — 18 h 24 m
of 20 h 00 m — was serial, single-slot model decoding on the one owned card. The card
was busy for 92% of the window, with no failed requests and no unplanned restarts across
all 432 cases. That measurement found two real constraints, not one.

*One card forces the candidates to queue.* The four candidate chains were 11 h 30 m,
2 h 46 m, 2 h 12 m, and 1 h 56 m of GPU time. The longest chain alone (11 h 30 m) is
longer than the other three put together (6 h 54 m). That longest chain is the round's
critical path — the run of work that nothing else can get ahead of, and the thing any
speed-up has to shorten to count. So a second node of *any* speed absorbs the whole
queue, and the round's floor becomes that chain: 20 h 00 m drops to about 13 h 06 m,
with the second node finishing 4 h 36 m early.

*16 GB is a capacity ceiling, not a speed ceiling.* The largest candidate occupied 94%
of the card's memory. That blocks two models being resident at once, and it caps how
large a future context or reasoning-budget experiment can safely go. This is a real
limit, and it is a different limit from "the round takes too long."

**The counterfactual that killed the intuitive purchase.** A 128 GB unified-memory
desktop box was on the shortlist, quoted at $4,999. Its memory bandwidth is 273 GB/s.
The owned card's spec sheet claims about 900 GB/s, and the autopsy measured it actually
achieving 350–490 GB/s on this decode workload. So the shiny new box is *slower* than
the card the project already owns, on the one thing this workload is bound by. Bought as
a **replacement**, it turns a 20-hour round into an estimated 25–35 hours. Bought as a
**second node** instead, the same box carries the three short chains while the long one
runs at home, and the round lands at roughly 13–14 hours — saving 6 to 7 of the 6 h 54 m
that is theoretically available to *any* second node. The lesson inside the lesson: as a
second node its slowness barely matters, because the long chain sets the floor. As a
replacement it is a disaster.

**The adversarial review, which refuted the actual proposal.** The independent reviewer
ran an exhaustive placement search over the autopsy's 11 measured run windows, trying
every way of splitting the work across nodes. The finding: the **second purchased card
saves 0.0 minutes**. One added node already reaches the 11 h 30 m floor with 4 h 36 m of
slack left over, so a second addition has nothing left to absorb.

The same review re-priced the two-card build at verified market rates: **$5,400 to
$7,300**. The cards were not what broke the budget — the motherboard, power supply, and
RAM needed to seat two of them did.

It also caught a reasoning error in the proposal's utilization argument. "The card was
92% busy" is true, and it is about one twenty-hour run. Sustained demand is a different
quantity, and it was measured too: **about 31 GPU-hours in the project's entire
lifetime, spread over six working days** — roughly $16 of rented capacity. Within-run
busyness and fleet demand are both real numbers. Only the second one belongs in a
purchase decision.

Two secondary arguments were checked and dropped. The proposal claimed that owning
hardware protects reproducibility. The project's own measurement says otherwise: its
[reproducibility boundary](../GLOSSARY.md#reproducibility-boundary) is *session*-scoped,
not host-scoped — roughly half of one split's case outcomes had already been measured to
flip across a plain restart of the model server
([SCENARIO-12](SCENARIO-12_restart-instability-paired-controls.md)). A rented instance
holding one session per candidate satisfies that rule exactly as well as an owned card
does. A separate worry — that older-generation cards would lose driver support — was
checked against the current release notes and found to be noise.

**The verified market, as of the week the proposal was reviewed (shelf life: weeks)
[EXT-HW-001].**

| Item | Verified price | Note |
|---|---|---|
| Current-flagship 32 GB consumer card, new | $4,700 (out of stock) – $6,900; in-stock floor $4,899 | The only genuine bandwidth upgrade in range; still rising |
| Previous-flagship 24 GB card, used | $3,600–$4,200 graded | Appreciating; poor value at this price |
| Two-generations-old 24 GB card, used | $1,450–$1,860 graded | Roughly the owned card's spec bandwidth, +4%; unmeasured in practice |
| 128 GB unified-memory desktop box | $4,999 (was $4,699 about a week earlier) | 273 GB/s — a bandwidth *downgrade* for this workload |
| Rented 24 GB card | $0.22/hr community tier · $0.50/hr secure tier | — |
| Rented 32 GB flagship | $0.69/hr community tier | — |

**The break-even, worked.** Take a $2,100 single-card node against renting the secure
tier at $0.50/hr, with electricity at $0.184/kWh and the machine drawing about 450 W.
Over a three-year life, ownership only wins above roughly **32 hours per week,
sustained**. The project's total measured usage to date is 31 hours — not per week, in
total, ever.

## What happened

No purchase. Instead, a staged plan in which each stage has a written trigger.

| Stage | Trigger | Content |
|---|---|---|
| 0 (now) | none — do it immediately | Rent both candidate card types for about two hours each (≈$2.50) to measure the one number the purchase turns on: is a desktop-class card of the same generation 1.0× or 1.4× the owned laptop card's real decode rate? Open the GPU-hours ledger. |
| 1 (standing practice) | none — every round | Rent the second node per round: the three short chains are 6 h 54 m of GPU time, ≈$3.50 at the secure tier. Captures the entire measured overlap saving, for no capital, cheaper than any purchase in this budget. |
| 2 (the purchase) | Three consecutive months of rented spend above ≈$150/mo, **or** a committed always-on serving tier | Buy exactly **one** card — whichever type the Stage-0 benchmark selects — on a minimal host, ≈$2,100–$2,750 all in, with a memory-temperature acceptance test before it enters service. |
| 3 (bandwidth) | After the generation-budget experiment settles, and street price ≤ ≈$2,500 (or rented need proven) | A flagship-class bandwidth upgrade, if the long decode chain still governs the critical path by then. |

Committed spend across the next three rounds comes to under $20. About **$4,985 of the
notional $5,000 stays uncommitted**, inside a documented and still-rising price bubble.
That was recorded as the decision the evidence supported, not as inaction.

Then the plan hit a wall, and how that was handled matters. The Stage-0 rented benchmark
could not run: no rental account or API credentials existed anywhere in the clinic, and
creating one needed the human owner. It was recorded rather than quietly skipped or filled in
with an estimate — the project's [fail-closed](../GLOSSARY.md#fail-closed) rule. The
[demand ledger](../GLOSSARY.md#demand-ledger)'s opening rows for both rented card types
carry an honest zero — 0 GPU-hours, $0 spend — with the reason written in the notes
column. The monthly rollup that reads the purchase trigger therefore showed $0 of rented
spend, far below the ≈$150/mo line, and the purchase stayed correctly deferred. Note
that this particular gap could not have changed the outcome either way: no result from a
two-hour benchmark could have fired that month's trigger. The ledger says so, in
writing, which is the point.

## The generic lesson

Before you spend money on hardware, replace the intuition — *more and bigger GPUs will
help* — with a measured counterfactual on your actual workload's critical path. Then
gate the purchase behind a written
[purchase trigger](../GLOSSARY.md#purchase-trigger) fed by a running
[demand ledger](../GLOSSARY.md#demand-ledger), never behind how attractive the purchase
feels. Four things made this decisive rather than merely cautious.

1. A reconstruction of the real critical path can refute a purchase *outright*, in a way
   a spec-sheet estimate never can. Here it went all the way to "the second card saves
   0.0 minutes."
2. Within-run busyness and sustained demand are different quantities, and both were true
   at once: 92% busy for one round, about 31 GPU-hours in six days of existence. Only
   the second belongs in a capital decision. That is what a demand ledger is for, honest
   zeroes included —
   [templates/COMPUTE_DEMAND_LEDGER.md](../templates/COMPUTE_DEMAND_LEDGER.md).
3. Rent first, let a cheap benchmark pick the part, and gate the buy on a trigger. This
   converts "should we buy hardware" from one judgement call into a few falsifiable
   conditions — and it prices the deferred option honestly, per-round rental against the
   ownership [break-even](../GLOSSARY.md#break-even), rather than pretending owned
   hardware is free once bought.
4. When a planned measurement cannot run, record the gap. An absence with a stated reason
   is auditable and keeps the trigger's arithmetic honest. A silent omission or a
   plausible-looking substitute does neither.

One narrower point, worth having in your pocket. An ownership argument built on
reproducibility is only as strong as the project's own measured
[reproducibility boundary](../GLOSSARY.md#reproducibility-boundary). Where that boundary
turns out to be session-scoped rather than host-scoped, it does not favour ownership at
all.

**How this lands on your project.** If you are about to buy an accelerator, write down
the longest single job in your last big run and how long it took. If one chain is longer
than everything else combined, a second card cannot take you below that chain, and a
third card buys you nothing at all. Then write down two numbers separately: how busy the
card was during that run, and how many GPU-hours you have used in the last month. Divide
the hardware's price by your rental rate. If the answer is more hours than you have ever
used, rent this round and open a ledger instead.

## What would NOT have worked

- **Buying the two-card build now, because "one card was maxed out, so two will help."**
  Refuted by exhaustive placement search: the second card adds zero minutes to the
  measured critical path of a workload this shape. And the platform needed to seat both
  cards broke the budget by itself.
- **Buying the big unified-memory box to replace the existing card.** Refuted by the same
  arithmetic. Its bandwidth is below what the owned card already achieves on this
  workload, so the swap would have made the round 25–75% longer.
- **Reading "92% GPU-busy" as evidence of purchase-worthy demand.** This is the exact
  reasoning error the demand ledger exists to catch. The honest fleet-demand figure for
  the same period was 31 hours across six days.
- **Justifying ownership on reproducibility grounds.** Dropped under review, because the
  project's measured reproducibility boundary is session-scoped, and a rented instance
  satisfies that as well as an owned one.
- **Quietly dropping the rented benchmark when the credentials turned out to be missing,
  or substituting an estimate for it.** The ledger recorded the gap instead, and the
  purchase stayed deferred on a number that was honestly zero rather than plausibly
  wrong.

## References

- [EXT-HW-001] — hardware and cloud price-verification snapshot; as-of dated, re-verify
  at order time.
- [SCENARIO-12](SCENARIO-12_restart-instability-paired-controls.md) — the session-scoped
  reproducibility measurement that undercuts the ownership-for-provenance argument.
- [SCENARIO-11](SCENARIO-11_diagnostic-gate.md) — the cheap diagnostic round inside
  which the Stage-0 rented benchmark was attempted and recorded incomplete.
- Governing chapters: [06](../06_INFERENCE_PERFORMANCE_AND_CAPACITY.md),
  [11](../11_ECONOMICS_HARDWARE_AND_CLOUD.md).
- Glossary: [purchase trigger](../GLOSSARY.md#purchase-trigger),
  [demand ledger](../GLOSSARY.md#demand-ledger),
  [break-even](../GLOSSARY.md#break-even),
  [performance autopsy](../GLOSSARY.md#performance-autopsy),
  [reproducibility boundary](../GLOSSARY.md#reproducibility-boundary),
  [fail-closed](../GLOSSARY.md#fail-closed).

---

[Index](../README.md) · [Glossary](../GLOSSARY.md)
