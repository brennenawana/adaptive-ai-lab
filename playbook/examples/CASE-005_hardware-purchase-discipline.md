# CASE-005: Hardware Purchase Discipline Against an Intuitive Upgrade

> Real empirical case from the FIS project (Fintech Integration Sandbox), a
> realistic synthetic fintech-operations laboratory used to develop this
> playbook's methodology.

**Source ID:** INT-CASE-005 · **Date range:** 2026-08-18 – 2026-08-21 · **Cited by:**
[06. Inference Performance and Capacity](../06_INFERENCE_PERFORMANCE_AND_CAPACITY.md) ·
[11. Economics, Hardware, and Cloud](../11_ECONOMICS_HARDWARE_AND_CLOUD.md)

## Situation

The project's single owned GPU (a laptop RTX 5080, 16 GB, ~896 GB/s vendor-spec
bandwidth) had just carried a 24 h 03 m, four-candidate model-comparison milestone
(R6) as the sole inference node, one case at a time. On the felt experience of that
milestone — one card, fully loaded, arms queued behind each other for a full day —
the obvious next move was to buy more GPU: a draft proposal circulated for a
dual-RTX-3090-plus-NVLink workstation build against a notional ~$5,000 budget, on the
reasoning that a second (and ideally a bigger) card would make milestones like R6
faster. Before any order was placed, the project instead commissioned a forensic
reconstruction of exactly where R6's 24 hours went (an internal performance autopsy,
built from run-ledger timestamps, database insert times, surviving server session
logs, and git commit times) and an independent adversarial review of the draft
hardware recommendation.

## Decision faced

Whether to commit ~$5,000–$8,000 of capital to a dual-GPU workstation now, on the
intuition that more/bigger GPUs would speed up milestones shaped like R6 — or to
defer any purchase pending a measured answer to what R6's wall clock actually
depended on, and let that measurement (not the intuition) select the hardware and
the timing.

## Evidence

**What R6's 24 h 03 m actually was (MEASURED).** 93.4% of it (22 h 28 m) was serial,
single-slot model decode on the one owned GPU, which ran busy 93% of the full 24 h
window with zero HTTP errors, zero retries, and zero unplanned restarts across 516
cases. Two real constraints were identified, not one: **(1) one card forces arm
serialization** — 8.8 GPU-hours belonging to three non-dominant candidate chains had
to queue behind the 13 h 40 m dominant chain, and because that dominant chain alone
already exceeds the alternative arms' combined length, a **second node of any
speed** absorbs the entire queue (24.1 h → ≈15.25 h; the second node carries 4.87 h
of slack). **(2) 16 GB is a capacity ceiling**, not a speed ceiling — the largest
candidate used 96% of the card, blocking co-residency and constraining how large a
future context/reasoning-budget experiment could safely go.

**The counterfactual that killed the intuitive purchase (from the same autopsy,
explicit arithmetic).** Modeling a DGX Spark (128 GB unified memory, 273 GB/s) as a
*replacement* for the 5080 gave a net-negative result: 24 h → an estimated 38–50 h,
because 273 GB/s is *below* the 353–496 GB/s the existing card was already achieving
on this bandwidth-bound decode workload — replacing the card would have roughly
doubled the milestone, not shortened it. Added as a *second* node instead, the same
unit saved 5–6 h (24 h → ≈18–19 h, 22%). The optimistic upper bound for adding *any*
second node with perfect overlap was 8.5–9.5 h saved (24 h → ≈14.5–15.5 h, 35–40%).

**The adversarial review that refuted the draft dual-GPU purchase specifically.** An
independent reviewer ran an exhaustive placement search over the autopsy's 13
measured run windows and found the **second purchased GPU saves 0.0 minutes** on
R6's measured critical path — one added node already reaches the 13 h 40 m floor
with 4.87 h of slack, so a second addition has nothing left to absorb. The same
review re-priced the dual-3090 build at verified market rates to **$5,800–$7,890**
(the platform and RAM, not the GPUs, broke the $5,000 budget), and found the
project's utilization argument had conflated within-run busyness (93% GPU-busy
during one 24 h run) with sustained fleet demand: total program-to-date usage was
**≈38 lifetime GPU-hours across five days** (≈$19 at rented-3090 rates) — not the
kind of number that justifies owning idle capital. A provenance-for-ownership
argument (that owning hardware protects reproducibility) was dropped on the
project's own measured evidence: reproducibility here is **session-scoped, not
host-scoped** — 23 of 48 case outcomes had been measured to flip across a mere
server restart [CASE: CASE-012] — so a rented instance holding one session per
arm satisfies the same rule exactly as well as an owned card. A separate worry
(Ampere-generation GPUs losing driver support) was checked and found to be noise:
the current CUDA release line lists no Ampere deprecations.

**The verified market, as of 2026-08-20 (shelf life: weeks) [EXT-HW-001].**

| Item | Verified price | Note |
|---|---|---|
| RTX 5090 32 GB new | $4,699 (OOS) – $6,900; in-stock floor $4,899 | Only true bandwidth upgrade in range; rising |
| RTX 4090 24 GB used | $3,600–4,200 (graded) | Appreciating, poor value now |
| RTX 3090 24 GB used | $1,450–1,860 (graded) | ≈ laptop-spec bandwidth +4%, unmeasured in practice |
| DGX Spark 128 GB | $4,999 (was $4,699 ≈1 week earlier) | 273 GB/s — a bandwidth *downgrade* here |
| Rented 3090 (RunPod) | $0.22/hr Community · $0.50/hr Secure | — |
| Rented 5090 (RunPod) | $0.69/hr Community | — |

**The break-even arithmetic (worked).** For a $2,050 single-3090 node against
rented Secure-tier 3090 at $0.50/hr and $0.184/kWh electricity, the ownership
break-even is **H\* ≈ 17–20 hours/week, sustained, for three years** — far above the
≈38 total lifetime hours measured to date.

## What happened

The project adopted a staged, trigger-based plan instead of any immediate purchase:

| Stage | Trigger | Content |
|---|---|---|
| 0 (immediate) | none — do now | Rent a 3090 and a 5090 (~$4, ≈2 h each) to measure the one unmeasured number the purchase decision actually turns on: is the desktop 3090's real decode 1.0× or 1.4× the laptop's? Start the GPU-hours ledger. |
| 1 (every milestone) | none — standing practice | Rent the second node per milestone (≈$4.40–4.66 for the non-dominant chains on a Secure 3090/A6000) — captures the full measured overlap saving with zero capital, cheaper than any in-budget purchase this month. |
| 2 (the purchase) | 3 consecutive months of rented spend > ≈$150/mo, **or** a committed always-on client-serving tier | Buy exactly **one** GPU — the type the Stage-0 benchmark selects (default: used 3090) — on a minimal host (≈$2,050–2,700 total), with a memory-junction-temperature acceptance test before it enters service. |
| 3 (bandwidth) | Post-reasoning-budget experiment, and street price ≤ ≈$2,500 (or rented need proven) | A 5090-class bandwidth upgrade, if the dominant decode chain still governs after the budget question is settled. |

**≈$4,400 of the notional $5,000 was deliberately left unspent**, inside a
documented, still-rising price bubble — framed explicitly as the decision the
evidence supported, not as inaction.

The Stage-0 benchmark was scheduled to run inside the project's next milestone
(a cheap diagnostic, [CASE: CASE-011]), but the rented-GPU work package could
not execute: no GPU-rental account or API credentials existed anywhere in the lab
environment, and creating one required the human owner. Per the project's
fail-closed rule, this was **recorded, not silently skipped or substituted**: the
compute-demand ledger's opening rows for both the rented 3090 and the rented 5090
carry an explicit honest zero — 0 GPU-hours, $0 spend, with the reason stated in
the notes column — rather than an approximated or omitted line. The monthly rollup
that reads the purchase trigger showed $0 of rented spend for the month, "far below
the ≈$150/mo line," and the purchase decision stayed correctly deferred — an
outcome this particular incompleteness could not have changed either way, since no
result from that benchmark could have fired the trigger this month.

## The generic lesson

**Portable rule: before committing capital to hardware, replace the intuition
("more/bigger GPUs will help") with a measured critical-path counterfactual of the
actual workload, and gate any purchase behind a pre-committed [purchase
trigger](../GLOSSARY.md#purchase-trigger) fed by a running
[demand ledger](../GLOSSARY.md#demand-ledger) — never behind the purchase's own
appeal.** Four things made this case decisive rather than merely cautionary:

1. A [performance autopsy](../GLOSSARY.md#performance-autopsy) that reconstructs the
   real critical path (not a spec-sheet estimate) can refute an intuitive purchase
   outright — here, exhaustively, down to "the second GPU saves 0.0 minutes."
2. Within-run busyness and sustained demand are different quantities and must be
   measured separately: 93% GPU-busy during one milestone and ≈38 lifetime
   GPU-hours across a working week are both true, and only the second one belongs
   in a purchase decision. This is exactly what a demand ledger (with honest
   NOT-RUN rows) is for — chapter 11;
   [templates/COMPUTE_DEMAND_LEDGER.md](../templates/COMPUTE_DEMAND_LEDGER.md).
3. A rent-first, benchmark-selected, trigger-gated staging turns "buy hardware" from
   a one-time judgment call into a small number of pre-committed, falsifiable
   conditions — and prices the deferred option honestly (per-milestone rental cost)
   against the ownership break-even, rather than assuming ownership is free once
   bought.
4. When a planned measurement cannot run (missing credentials, in this case), a
   [fail-closed](../GLOSSARY.md#fail-closed) demand ledger records the gap as an
   incomplete work package with an honest zero, not a silent omission or an
   uncontrolled proxy substitute — the absence is itself informative and auditable,
   and it keeps the trigger's arithmetic honest.

A fifth, narrower point: an ownership argument built on reproducibility (owning the
hardware "protects" comparability) is only as strong as the project's own measured
[reproducibility boundary](../GLOSSARY.md#reproducibility-boundary). Where that
boundary is session-scoped rather than host-scoped, it does not favor ownership at
all — a rented instance holding one session per arm satisfies the same rule.

## What would NOT have worked

- **Buying the dual-GPU build now, on the strength of "one card was maxed out, so
  two will help":** refuted by exhaustive placement search — the second GPU adds
  zero minutes to the measured critical path of a workload shaped like R6, and the
  platform required to seat it alone exceeded the notional budget.
- **Buying a DGX Spark to replace the existing card:** refuted by the same
  counterfactual arithmetic — its bandwidth is *below* what the existing card
  already achieves on this workload, so replacing it would have roughly doubled the
  milestone.
- **Reading the 93% GPU-busy figure as evidence of purchase-worthy demand:** this
  was the precise reasoning error the demand ledger exists to catch; the honest
  fleet-demand figure for the same period was ≈38 hours across five days.
- **Justifying ownership on reproducibility grounds:** dropped under review, because
  the project's own measured reproducibility boundary is session-scoped, which a
  rented instance satisfies just as well as owned hardware.
- **Silently omitting the rented-GPU benchmark when credentials were missing, or
  substituting an approximate number for it:** the fail-closed ledger recorded the
  gap explicitly instead, and the purchase decision remained correctly deferred
  either way.

## References

- [EXT-HW-001] 2026-08-20 hardware/cloud price-verification snapshot (Newegg,
  NVIDIA, Apple, RunPod, and community sources; as-of-dated, re-verify at order
  time).
- [CASE: CASE-012] Restart instability and paired controls — the session-scoped
  reproducibility measurement that undercuts the ownership-for-provenance argument.
- [CASE: CASE-011] Diagnostic gate before an expensive experiment — the milestone
  inside which the Stage-0 rented-GPU benchmark was attempted and recorded
  incomplete.
- Governing chapters: [06](../06_INFERENCE_PERFORMANCE_AND_CAPACITY.md),
  [11](../11_ECONOMICS_HARDWARE_AND_CLOUD.md).
- Glossary: [purchase trigger](../GLOSSARY.md#purchase-trigger),
  [demand ledger](../GLOSSARY.md#demand-ledger),
  [break-even](../GLOSSARY.md#break-even),
  [performance autopsy](../GLOSSARY.md#performance-autopsy),
  [reproducibility boundary](../GLOSSARY.md#reproducibility-boundary),
  [fail-closed](../GLOSSARY.md#fail-closed).
