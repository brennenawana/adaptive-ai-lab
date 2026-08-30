# SYNTH-10: A Hardware Purchase That Correctly Waits

> [Index](../README.md) · [Examples](README.md)

*Synthetic worked example — all names and numbers invented.*

---

## Profile summary

The rule was written down before anybody wanted the hardware, which is the
only moment such a rule is worth anything. Buy when the rolling three-month
average utilization reaches the break-even point — not when a month feels
busy.

"Copperfield Labs" is an internal ML-platform team. It runs one roughly
two-hour regression evaluation every night for a document-classification
pipeline, plus the occasional multi-day fine-tuning sprint. Its rented cloud
GPU spend had started to feel steady enough that someone kept proposing a
workstation-class GPU purchase.

| [Project profile](../GLOSSARY.md#project-profile) field | Value |
|---|---|
| Business outcome | Predictable compute cost for nightly regression evals plus occasional fine-tuning experiments |
| Task population & volume | One ~2-hour nightly eval run; 1–2 multi-day fine-tuning sprints per quarter, cadence uncertain |
| Owned compute | None dedicated — shared development machines only |
| Rentable compute | On-demand cloud GPU instances, secure tier |
| Capex budget | Modest, requires justification before spend |
| Recurring budget | Currently variable rented spend, tracked informally until this project |
| Utilization / growth expectations | Eval frequency growing; training cadence still uncertain |
| Staffing / time | One engineer, part-time on infrastructure |
| Privacy / security / residency | No regulated data; rented secure-tier cloud is admissible |
| Stakes / consequence tolerance | **Tier 2** — a real budget decision, reversible, internal |

## Archetype & rigor tier

This is the rent-versus-buy archetype from chapter 11's decision tree. No
privacy mandate forces local ownership. Demand is real but not yet proven
sustained. And the decision is a reversible capital question, not a safety or
compliance one.

That places it at **Tier 2** — enough rigor to require a demand ledger and a
pre-committed trigger, not enough to require anything from chapter 13's
Tier-3 set.

## The decisive moves

1. **The demand ledger opened before any purchase conversation started.**
   Every GPU-hour was logged monthly from the beginning — rented hours and
   any incidental local use alike — including honest NOT-RUN rows for jobs
   that were planned but blocked. That last part is what stops a busy crunch
   week from being misread later as sustained demand
   ([demand ledger](../GLOSSARY.md#demand-ledger), chapter 11).
2. **The purchase trigger was written down before anyone wanted the
   hardware.** The pre-committed rule: the
   [purchase trigger](../GLOSSARY.md#purchase-trigger) fires only if the
   rolling 3-month average utilization reaches or exceeds the rent-vs-buy
   break-even threshold H*. Never off a single month, however busy that month
   was.
3. **H* was computed with the standard formula — symbols and units stated —
   before a single month of ledger data was looked at.** H\* is the number of
   hours per week you would have to keep the hardware busy, sustained, for
   owning it to beat renting the same capability
   ([break-even](../GLOSSARY.md#break-even)):

   `H* = (P − S) / (L · 52 · (R − TDP_kW · e))`  [hours/week]

   where P = purchase price ($), S = salvage value after L years ($), L =
   expected service life (years), R = rental rate for an equivalent instance
   ($/hour), TDP_kW = sustained power draw (kW), e = electricity price
   ($/kWh).

   Worked example (illustrative, invented): P = $4,000, S = $800, L = 3,
   R = $2.10/hr, TDP_kW = 0.45, e = $0.14/kWh.
   TDP_kW · e = $0.063/hr → R − TDP_kW·e = $2.037/hr → L · 52 = 156 weeks.
   H* = (4,000 − 800) / (156 × 2.037) = 3,200 / 317.8 ≈ **10.1 hours/week**.
4. **[STOP CONDITION]** fired mid-project, and it held. After one crunch
   month — the numbers are below — a team member proposed buying immediately.
   This is the global tripwire on hardware-purchase decisions made without
   the demand ledger's own trigger ([00 §7](../00_PRINCIPLES_AND_SCOPE.md)).
   The proposal was held for the quarter-end ledger review rather than argued
   on the spot.
5. **The ledger made the call, not the anecdote.** At quarter-end the rolling
   3-month average sat well under H*. The trigger did not fire. The team
   correctly did not buy. Renting continues, and the same pre-committed
   trigger stands for reassessment next quarter — it was never loosened
   after failing to fire once, which is the part that usually goes wrong.
6. **The benchmark-first rule was recorded for whenever the trigger does
   fire.** On trigger, the team buys only the benchmark-chosen minimal
   configuration: a cheap rented benchmark on the actual pinned workload
   sizes the purchase. And any price used to justify the spend gets
   re-verified at order time, rather than trusted from whenever it was first
   quoted. Hardware and cloud prices in a tight supply market are floors with
   a shelf life of weeks, not fixed numbers [EXT-HW-001].

## What was skipped and why

- **Parallel-node and critical-path analysis (11).** Current jobs are
  single-GPU-bound, so the marginal-node-value question — does a second GPU
  actually shorten the critical path, or just add idle capacity — does not
  arise yet. It is deferred until a job is demonstrably parallelizable.
- **The capacity-versus-bandwidth hardware-class comparison.** Nothing here
  is a bandwidth-bound serving workload. A single mid-tier high-VRAM GPU
  would cover both the eval and the fine-tuning use cases, so the
  serving-class hardware comparison was not engaged.
- **The local-only-mandate branch of the decision tree.** No regulated data
  is in scope, so the privacy-forced-ownership path never applies, and rented
  secure-tier capacity stays admissible throughout.

## Outcome

Four months of ledger data (illustrative, invented): Month 1, 14 GPU-hours,
$46; Month 2, a fine-tuning crunch sprint, 61 GPU-hours, $198; Month 3, 19
GPU-hours, $62; Month 4, 16 GPU-hours, $52 — the last of these including one
honestly logged NOT-RUN row for an 8-hour job blocked two days by a
data-pipeline defect.

As weekly averages, that is roughly 3.2, 14.1, 4.4, and 3.7 hours/week. Only
Month 2 cleared the 10.1 hr/week H* threshold at all, and one busy month is
not a rolling three-month average — the pre-committed trigger never fired.

Total rented spend across the period: $358, against a $4,000 purchase that
would have sat mostly idle. The team kept renting, kept the ledger running,
and left the trigger exactly as pre-committed for the next quarterly review.
The purchase correctly does not happen yet.

## Chapter trail

- [01. Project Intake and Decision Context](../01_PROJECT_INTAKE_AND_DECISION_CONTEXT.md) —
  profile fields: owned/rentable compute, capex vs. recurring budget
- [00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) — the global
  tripwire on purchase decisions made without the ledger/trigger
- [11. Economics, Hardware, and Cloud](../11_ECONOMICS_HARDWARE_AND_CLOUD.md) —
  demand ledger, purchase trigger, rent-vs-buy break-even, benchmark-first
  rule, market-snapshot discipline
- [14. Decision Trees and Checklists](../14_DECISION_TREES_AND_CHECKLISTS.md) —
  the rent-vs-buy decision tree

---

> [Index](../README.md) · [Examples](README.md)
