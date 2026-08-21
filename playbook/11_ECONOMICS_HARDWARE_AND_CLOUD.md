# 11. Economics, Hardware, and Cloud

> Part of the **Adaptive AI Systems Playbook** v0.1.0 ·
> [← Previous](10_DEPLOYMENT_AND_OPERATIONS.md) · [Index](README.md) · [Next →](12_OBSERVABILITY_LEARNING_AND_PROMOTION.md)
> **Reading time:** ~18 min. **Prerequisites:** 01 (project profile budget/privacy
> fields), 06 (performance characterization — operating point, effective bandwidth).

## 1. Purpose and when to read this

This chapter turns "should we own hardware, rent it, or use a managed/frontier API"
from an intuition into a measured decision. It is deliberately written to be entered
**three times** in the [default lifecycle](00_PRINCIPLES_AND_SCOPE.md#5-default-procedure):
once at intake (rough shape — capex vs opex, privacy constraints), once at capacity
planning (after chapter 06 has measured the workload's actual bottleneck), and once
at deployment (steady-state serving economics, chapter 10). Each visit uses the same
machinery on progressively better evidence.

Read this chapter when: a hardware purchase is being discussed at any dollar amount;
a project is choosing between local inference, rented GPUs, managed inference, or a
frontier API; a routing/cascade layer's cost case needs a number attached
(cross-reference [chapter 08](08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md)); or a
capital request needs a written justification that will survive scrutiny.

## 2. Inputs required

- The [project profile](GLOSSARY.md#project-profile)'s budget fields: capex vs opex
  structure, recurring-spend ceiling, staffing/time for owned infrastructure,
  privacy/residency constraints, deployment environment
  ([templates/PROJECT_PROFILE.md](templates/PROJECT_PROFILE.md), chapter 01).
- A measured workload characterization from
  [chapter 06](06_INFERENCE_PERFORMANCE_AND_CAPACITY.md): the chosen
  [operating point](GLOSSARY.md#operating-point), measured
  [effective bandwidth](GLOSSARY.md#effective-bandwidth), and whether the workload
  is capacity-bound or bandwidth-bound (§8). Economics priced against a marketing
  spec sheet instead of a measured bottleneck is guessing with extra steps.
- A [demand ledger](GLOSSARY.md#demand-ledger) — existing entries, or the decision
  to start one now (§5). Every formula in §8 takes it as a parameter.
- A [performance autopsy](GLOSSARY.md#performance-autopsy) for any completed
  milestone, if one exists — the source of critical-path data for the
  parallel-node question (§8, §11).
- The project's [stakes tier](GLOSSARY.md#stakes-tier) — governs which cloud tiers
  are admissible for which data (§8).

## 3. Decisions this chapter supports

- Own vs rent vs managed inference vs frontier API vs hybrid, at each of the three
  lifecycle entry points named in §1.
- Whether, and when, a hardware purchase is justified — and what to buy if it is.
- Whether an additional parallel compute node actually shortens a milestone's wall
  clock, and by how much.
- Whether a routing/cascade layer (chapter 08) pays for its own gate cost.
- Which cloud tier is admissible for a given workload's data.

## 4. Normative principles

**[PRINCIPLE] Demand before capital.** (evidence: case-study + inference)
No capital hardware decision is made from within-run impressions ("the GPU was busy
all week"). A [demand ledger](GLOSSARY.md#demand-ledger) — sustained GPU-hours and
spend per period, including honest NOT-RUN rows — is the evidence base, built
*before* the capital conversation, not to justify a decision already made.
First-principles argument: a capital purchase is the least reversible resource
decision in the lifecycle (P4, [00 §4](00_PRINCIPLES_AND_SCOPE.md#4-normative-principles));
without a ledger the only available evidence is recency-biased memory of the last
busy week, which systematically overstates sustained demand. [CASE: CASE-005]
measured this gap directly: within-run utilization was high, but lifetime sustained
demand was a small fraction of what an intuitive purchase would have implied.

**[PRINCIPLE] The purchase trigger is pre-committed, not discovered.** (evidence:
inference)
The [purchase trigger](GLOSSARY.md#purchase-trigger) — the condition that fires a
hardware purchase, e.g. K consecutive periods of rented spend above a threshold,
or a signed always-on serving commitment — is defined *before* anyone wants the
hardware, and does not move afterward. This is
[P7](00_PRINCIPLES_AND_SCOPE.md#4-normative-principles) (pre-registration with
consequences) applied to capital: a threshold chosen after the desire already
exists is a rationalization wearing a control's clothes. [CASE: CASE-005] recorded
the corollary anti-pattern by name (§9): a trigger that moves because one
favorable benchmark appeared has already failed at its one job.

**[PRINCIPLE] Match hardware to the measured bottleneck, not the spec sheet.**
(evidence: strong-evidence)
Evaluate a candidate device against the workload's *measured* constraint —
[capacity or bandwidth](#8-metrics-and-formulas) — not aggregate marketing numbers.
A device can be more expensive, newer, and still make the workload slower if it
misses the actual bottleneck. This is [P2 and P5](00_PRINCIPLES_AND_SCOPE.md#4-normative-principles)'s
measurement-validity argument applied to a purchase claim instead of a
model-comparison claim: an unmeasured comparison is not a comparison. [CASE:
CASE-005] found exactly this inversion — a capacity-comparable candidate device was
rejected once compared on the workload's actual bandwidth bottleneck.

**[PRINCIPLE] Measure the critical path before buying parallelism.** (evidence:
inference)
A parallel node's value is the wall-clock overlap it captures, not a fixed
multiplier on throughput; a third node can be worth zero. First-principles
argument: if a milestone decomposes into K independent chains that each run
serially on one device, wall clock is bounded below by the *longest* chain
assigned to any one device — once the longest chain has a device to itself,
additional devices cannot shorten wall clock further. [CASE: CASE-005]'s measured
critical-path reconstruction is the demonstrated instance: an intuitive
second-device purchase saved nothing, because the critical path was bound
elsewhere.

**[DEFAULT] Market-snapshot discipline.** (evidence: heuristic)
Every cited price, benchmark number, or vendor TCO figure is a snapshot: it carries
a stated as-of date and an assumed shelf life, re-verified before it drives spend —
especially in a documented shortage or price-crunch regime, where a multi-week-old
number can already be wrong in either direction
[REFERENCE: EXT-HW-001, as of 2026-08-20]. A number without a date attached is
folklore with a currency symbol on it.

**[DEFAULT] Cloud-tier admissibility follows the stakes tier.** (evidence:
inference, cross-ref [rigor dial](GLOSSARY.md#rigor-dial))
Which cloud tier (community/preemptible, secure/dedicated, owned) is admissible is
set by the data a workload touches and the project's
[stakes tier](GLOSSARY.md#stakes-tier) ([00 §6](00_PRINCIPLES_AND_SCOPE.md#6-project-adaptation-parameters--the-rigor-dial)),
not by whichever tier is cheapest this week (table, §8).

## 5. Default procedure

1. **Establish the demand ledger** before any capital conversation starts. Use
   [templates/COMPUTE_DEMAND_LEDGER.md](templates/COMPUTE_DEMAND_LEDGER.md); record
   every period, including periods where planned rental could not execute (record
   the blocking reason — an absent account or credential is a finding, not a reason
   to skip the row).
2. **Classify the workload's constraint** using chapter 06's measured bandwidth and
   capacity data: capacity-bound, bandwidth-bound, or both (§8). This determines
   which hardware classes are even candidates before any price is considered.
3. **Walk the decision tree** below, using the project profile's privacy/residency,
   budget-structure, and staffing fields plus the ledger's demand history.
4. **If renting:** choose a cloud tier by the §8 admissibility table and rent
   per-milestone — rent for the run, log it in the ledger, release it. Chapter 02's
   comparability rules (frozen identity, artifact digests on the remote host) apply
   to a rented session exactly as they would to owned hardware.
5. **If the purchase trigger has fired** (§7): buy the minimal configuration chosen
   by a cheap benchmark run on the *actual* pinned artifact — not the largest
   configuration the budget allows. [CASE: CASE-005]'s pattern: a small rented
   benchmark on the pinned artifact measures the one number the purchase decision
   turns on, before any capital moves.
6. **Re-enter this chapter** at capacity planning (real chapter-06 bottleneck data)
   and again at deployment (chapter 10's steady-state serving volume) — the tree is
   re-walked with better evidence each time, not re-litigated from scratch.

**Decision tree** (keyed on project-profile facts):

```
Q0  Hard privacy/residency constraint (contractual/regulatory) on this workload?
     YES → owned or secure/dedicated-tier rented hardware only; managed/frontier
           APIs and community/preemptible tiers are OUT.  → go to Q2.
     NO  → continue.

Q1  Does a quality- and cost-adequate managed API / hosted-inference offering
     already exist for the task, per a trusted evaluation (chapter 03)?
     YES, demand is low/unmeasured → managed/frontier API; re-enter at capacity
         planning once demand is measured.
     NO, or cost/latency/control is inadequate at measured demand → continue.

Q2  Capacity-bound, bandwidth-bound, or both (chapter 06, §8)? Fixes which
     hardware classes are candidates at all.

Q3  Demand ledger, for the candidate class, vs the rent-vs-buy break-even H* (§8)?
     Below H*, or no sustained history yet → rent per-milestone; do not buy on a
         projection.
     At/above H*, sustained for the pre-registered window → PURCHASE TRIGGER
         condition met (§7) → buy the benchmark-chosen minimal configuration.

Q4  Budget structure and staffing (project profile): capital available? capex or
     opex preferred? staffing time to own infrastructure? A fired trigger with no
     capital stays rented/opex; a capex preference never fires the trigger early
     (§9) — the trigger decides, not the preference.
```

Most real projects land on a **hybrid**: an always-on low-tier component (owned or
reserved), burst/training capacity (rented per-milestone), and a managed/frontier
fallback for tasks the owned tier cannot cover economically or at all.

## 6. Project adaptation parameters

| Parameter | What it is | How to calibrate it |
|---|---|---|
| Purchase-trigger threshold (K periods, spend X) | The pre-committed condition that fires a buy decision | Set once, before any hardware desire exists, from the org's opex tolerance and the ledger's review cadence; record in the project profile or a [method decision record](templates/METHOD_DECISION_RECORD.md) |
| Break-even inputs (P, S, L, R, TDP, e) | The six inputs to H\* (§8) | P/S from a dated quote; L from vendor warranty plus expected obsolescence; R from a current rental listing; TDP from vendor spec or measured draw; e from your actual electricity rate |
| Demand-ledger review cadence | How often the ledger is read for a decision | At minimum monthly once any rented spend exists; every milestone always gets a row |
| Cloud-tier policy by stakes tier | Which tier is admissible for which data class | Derive from the project profile's privacy/residency and stakes-tier fields; §8's table is a starting default, not a universal rule |
| Operating point for cost calculations | The latency/throughput point economics is priced at | Selected in chapter 06; never price a best-case throughput number the deployment will not actually run at |
| Staffing overhead for owned hardware | The time cost of maintaining owned infrastructure | Estimate from actual ops staffing budget; folds into O in the amortization formula (§8) |

## 7. Decision gates and stopping conditions

**[DECISION GATE] Purchase trigger.**
Inputs: the demand ledger's record of K consecutive qualifying periods above
threshold X, or a signed always-on-serving commitment (both set in §6, before this
gate is ever consulted in anger). Rule: fired → proceed to a benchmark-chosen
minimal-configuration purchase (§5). Not fired → continue renting, regardless of
any single favorable benchmark or accumulated impatience.
Outcomes: **FIRED** (buy) / **NOT-FIRED** (rent and keep ledgering).

**[DECISION GATE] Rent-vs-buy break-even.**
Inputs: H\* (§8) for the candidate configuration vs the ledger's measured or
credibly projected sustained hours/week. Rule: below H\* → renting dominates on
cost alone (privacy/latency/staffing factors from §4/§8 still apply on top).
At/above H\*, sustained → capital *may* be justified on cost, but the
purchase-trigger gate above still has to fire — cost dominance does not bypass
pre-registration.
Outcomes: **RENT** / **CANDIDATE-FOR-TRIGGER**.

**[STOP CONDITION]** A hardware purchase is being justified from a within-run
busy-percentage figure instead of the demand ledger (§9 anti-pattern 1) → stop;
populate or consult the ledger first.

**[STOP CONDITION]** A cited price, benchmark number, or vendor TCO figure has no
as-of date, or its stated shelf life has expired → stop; re-verify before it drives
a decision (§4).

**[STOP CONDITION]** A private, held-out, or regulated corpus is about to be placed
on a community/preemptible or otherwise shared-tenancy host → stop; apply the
stakes-tier cloud policy (§8).

## 8. Metrics and formulas

**Capacity-bound vs bandwidth-bound.** These are separate constraint classes that
buy *different* hardware; conflating them is the single most common purchase
mistake this chapter guards against.

| Constraint class | What binds | "Fits" looks like | What to buy |
|---|---|---|---|
| Capacity-bound | Model weights, adapters, context, or multi-model residency must physically fit | Capacity (VRAM/unified memory) ≥ working set, with headroom for context growth | More memory: a larger-capacity card, unified-memory box, or pooled multi-GPU capacity |
| Bandwidth-bound | Serial autoregressive decode throughput on an already-resident model | Effective bandwidth ([chapter 06](06_INFERENCE_PERFORMANCE_AND_CAPACITY.md#8-metrics-and-formulas)) ≥ the throughput the operating point requires | Higher-bandwidth hardware, possibly at *smaller* capacity than a capacity-bound fix would suggest |

A device chosen on capacity headroom alone can still be a bandwidth downgrade for a
decode-bound workload, and vice versa — measure both axes (chapter 06) before
comparing candidates.

**Cloud-tier admissibility by stakes tier.**

| Tier | Description | Admissible for |
|---|---|---|
| Community / preemptible | Shared tenancy, interruptible, cheapest | Tier 1 exploratory iteration on non-sensitive or synthetic data; screening runs that tolerate a restart |
| Secure / dedicated | Non-preemptible, isolated tenancy | Tier 2+ default; anything touching a private corpus, held-out evaluation data, or customer content |
| Owned (on-prem) | Full custody | Tier 3 default whenever residency is a hard constraint (Q0, §5), or sustained demand exceeds H\* |

**Rent-vs-buy [break-even](GLOSSARY.md#break-even) (H\*).**

```
H* = (P − S) / (L · 52 · (R − TDP_kW · e))         [hours/week]
```

- `P` — purchase price of the hardware (USD)
- `S` — expected salvage/resale value at disposal (USD)
- `L` — expected useful life (years)
- `52` — weeks per year (constant)
- `R` — rental rate for equivalent capability (USD/hour)
- `TDP_kW` — sustained power draw under the target workload (kW)
- `e` — electricity price (USD/kWh)
- `H*` — the sustained utilization, in hours/week, above which owning is cheaper
  than renting over the amortization horizon

*Worked example (illustrative, invented round numbers):* P = $2,000, S = $400,
L = 3 years, R = $0.50/hr, TDP = 0.35 kW, e = $0.15/kWh.
`TDP·e = 0.35 × 0.15 = $0.0525/hr`; `R − TDP·e = $0.4475/hr`;
`H* = 1,600 / (3 × 52 × 0.4475) = 1,600 / 69.81 ≈ 22.9 hours/week`.
Below ~23 sustained hours/week, renting wins; at or above, owning wins — *given*
these six inputs. Change any input and re-solve; do not memorize the answer.

**Amortized owned cost per hour** (same symbols, plus `H_used` = total hours the
hardware is actually put to work over its life, and `O` = other marginal ops cost
per hour, e.g. prorated maintenance/staffing):

```
cost_per_hour_owned = (P − S) / H_used + TDP_kW · e + O          [USD/hour]
```

*Worked example, same inputs, O = $0:* at h = 20 hr/week (below H\*, `H_used` =
3,120 hr), `cost_per_hour_owned ≈ 0.513 + 0.0525 ≈ $0.565/hr` — *more* than the
$0.50/hr rental rate, so renting wins, consistent with H\* ≈ 23. At h = 30 hr/week
(above H\*, `H_used` = 4,680 hr), `cost_per_hour_owned ≈ 0.342 + 0.0525 ≈ $0.394/hr`
— *less* than renting, so owning wins. The two formulas agree, as they must.

**Cost per successful task / expected cost per solve** — ties economics directly
to your evaluation's measured outcome rate (chapters 03/04), because a cheaper
request that fails more often is not necessarily a cheaper solve:

```
cost_per_solve = cost_per_request / pass_rate                    [USD/solved task]
```

*Worked example (illustrative):* Candidate A costs $0.010/request at a 90%
measured pass rate → `cost_per_solve = 0.010/0.90 ≈ $0.0111`. Candidate B costs
$0.004/request at a 40% measured pass rate → `cost_per_solve = 0.004/0.40 = $0.010`.
B looks 2.5× cheaper per request; on cost per solved task it is only marginally
cheaper than A — the comparison that actually matters for a budget.

**Routing break-even** (full derivation and the false-negative-cost extension live
in [chapter 08](08_RETRIEVAL_TOOLS_WORKFLOWS_AND_ROUTING.md); stated here for
economics literacy) [ADAPT: EXT-SWITCHYARD-001]:

```
min_offload_share ≈ gate_cost / (strong_cost − weak_cost)        [dimensionless, 0–1]
```

*Worked example (illustrative):* gate_cost = $0.001/item, strong_cost = $0.020/item,
weak_cost = $0.002/item → `min_offload_share ≈ 0.001/0.018 ≈ 0.056` — roughly 5.6%
of volume must be handled by the cheap tier alone for the cascade's added gate cost
to pay for itself on cost alone. This is a floor, not the whole case: an
un-escalated failure has its own cost (chapter 08).

**API/managed-inference cost control.** $/M-token chains
[REFERENCE: NV-COSTTCO-001] apply directly to metered API spend (re-derive their
constants per §9). Two levers beyond the raw rate: prompt/context caching cuts
repeated-context cost on multi-turn or RAG-heavy workloads — verify your
provider's actual cache-hit accounting before pricing it in; and a spend ceiling
on any API budget is a [consequence-bearing tolerance](GLOSSARY.md#consequence-bearing-tolerance)
(chapter 04) — pre-register ABORT / RECALIBRATE / PROCEED-WITH-DECLARED-CEILING
for an overrun, enforced in the calling code, not a silent cutoff discovered at
the invoice.

**Marginal parallel-node value.** Not a closed-form formula — a scheduling
question: with K independent serial chains and N devices, added wall-clock savings
from the (N+1)th device equal the overlap it captures, bounded above by zero once
the longest chain already has a device to itself. Worked as a table in §11.

## 9. Failure modes and anti-patterns

**[REJECTED]** (condition: always)

- **Justifying a purchase from within-run busy-percentage.** A device saturated
  *during an active experiment* measures that run, not whether sustained fleet
  demand needs more of it. Only the demand ledger answers the fleet question.
  [CASE: CASE-005].
- **Reactive purchase-trigger adjustment.** Moving, loosening, or firing an
  already-defined trigger because one favorable benchmark appeared, or because
  waiting has become unpleasant. A trigger that moves with mood is not a trigger.
- **Buying capacity or bandwidth without first classifying the constraint.** A
  capacity fix does nothing for a bandwidth-bound workload, and vice versa.
  [CASE: CASE-005] measured exactly this mismatch on a real candidate device.

**[REJECTED]** (condition: applying a vendor $/M-token or TCO formula chain to a
small-lab or local-hardware decision without re-deriving its inputs) Vendor TCO
chains typically assume large multi-GPU server capex and datacenter-scale
sustained utilization and power/cooling contracts — one widely cited chain assumes
an $320K-class 8-GPU server as its baseline unit
[REFERENCE: NV-COSTTCO-001, as of 2026-08-20]. The *formula chain* (§8 style)
travels; its published constants do not.

**[REJECTED]** (condition: buying during a documented price spike or shortage
without a fired, pre-committed trigger) Deliberately not spending capital during a
price bubble is an active decision this playbook licenses, not a deferral. A
trigger exists precisely so "prices might drop soon" and "prices might keep
rising" both stay irrelevant — only the pre-registered condition fires it.

**[REJECTED]** (condition: treating a single community benchmark thread's numbers
as verified performance without checking its methodology disclosure)
Community-reported decode/throughput numbers for nominally identical hardware can
disagree substantially between threads once methodology (warm-up, quantization,
concurrency, driver version) is checked [REFERENCE: EXT-HW-001, as of 2026-08-20].
Cross-check a second independently-disclosed source, or run the cheap benchmark
yourself (§5) rather than trusting one thread.

## 10. Vendor recipes

**[REFERENCE: NV-COSTTCO-001]** ($/M-token TCO formula chain; as of 2026-08-20).
The formula *shape* (amortized hardware + power + utilization → $/M-token) is
worth adapting; its worked constants assume datacenter-scale hardware and
near-saturated utilization and do not transfer without re-derivation (§9).

**[REFERENCE: NV-LEPTONBREV-001]** (rentable multi-provider GPU
marketplace/console; as of 2026-08-21). One source of current rental-rate inputs
(`R` in §8); as of verification it documents no path for migrating a workload
started there back onto locally-owned hardware — confirm the current
on-ramp/off-ramp story before committing a recurring workload to it.

**[REFERENCE: NV-DYNAMOAICONFIG-001]** (datacenter operating-point sizing
automation; as of 2026-08-20). A second, independent instance of the
vendor-TCO-assumes-datacenter-scale caveat above; does not cover small-lab or
single-card hardware classes.

**[ADAPT: EXT-SWITCHYARD-001]** (routing break-even rule and worked figures; as
of 2026-08-21). The break-even *formula* (§8) is what transfers; its published
cost-cut and accuracy figures are conditioned on one weak/strong pairing and task
suite and are not general constants — recompute `gate_cost`, `strong_cost`,
`weak_cost` on your own arms.

**[FOLLOW: EXT-FT-003]** + **[ADAPT: EXT-UNSLOTH-001]** (QLoRA/LoRA VRAM-floor
guidance; as of 2026-08-21). Use the published VRAM-floor guidance, cross-checked
against current runtime documentation, to size the capacity-bound constraint (§8)
before renting or buying training hardware. Full method defaults live in
[chapter 09](09_TRAINING_AND_DATA.md); this chapter only consumes the *sizing*
conclusion.

**[REFERENCE: NV-DGXCLOUD-DEP-001]** (rentable-cloud product naming; as of
2026-08-21). Vendor rentable-product identities in this space move fast — a name
that denoted a directly rentable service at one point can be repositioned; verify
the current product name and rental path at order time.

## 11. Worked examples

**Illustrative market-snapshot template.** A real snapshot needs more than a price
— it needs the columns below, every one dated. The table itself is an invented
template, not current pricing:

| Hardware/cloud class (illustrative) | Illustrative capability spec | Illustrative purchase price | Illustrative rental rate | As-of date |
|---|---|---|---|---|
| Entry consumer-class card | ~24 GB capacity, ~1.0 TB/s bandwidth class | $2,000 | $0.50/hr secure · $0.25/hr community | *(none — invented)* |
| High-bandwidth consumer-class card | ~32 GB capacity, ~1.8 TB/s bandwidth class | $5,000 | $1.00/hr secure · $0.65/hr community | *(none — invented)* |
| Unified-memory capacity box | ~128 GB capacity, ~0.3 TB/s bandwidth class | $5,000 | not commonly rented as a discrete unit | *(none — invented)* |
| Professional/workstation card | ~48 GB capacity, ~0.9 TB/s bandwidth class | $5,500 | $0.55/hr secure | *(none — invented)* |

Every figure above is invented and round, chosen only to demonstrate the columns a
real snapshot needs — it carries no as-of date because it was never observed. A
real snapshot MUST carry one and a stated re-verify-at-order-time trigger (§4)
[REFERENCE: EXT-HW-001].

**Marginal node value — a critical-path worked example (illustrative).** A
milestone decomposes into three independent chains, each bound to run serially on
one device:

| Assignment | Chain(s) per device | Milestone wall clock | Saved vs prior row |
|---|---|---|---|
| 1 device | A(14h) + B(5h) + C(4h) all serial | 23h | — |
| 2 devices | A(14h) alone · B(5h)+C(4h)=9h | max(14, 9) = 14h | 9h |
| 3 devices | A(14h) alone · B(5h) alone · C(4h) alone | max(14, 5, 4) = 14h | **0h** |

The second device captures the entire 9-hour overlap available. The third device
saves nothing, because Chain A alone already bounds the critical path at 14 hours
— no number of additional devices shortens a milestone below its longest single
chain. This is the generic shape of [CASE: CASE-005]'s measured finding: a second
purchased device can be worth most of a workday; a second-again device can be worth
minutes.

Further reading: [CASE-005](examples/CASE-005_hardware-purchase-discipline.md)
(the full measured critical-path and demand-ledger narrative behind §4's
principles) and [SYNTH-10](examples/SYNTH-10_hardware-rent-vs-buy.md) (a synthetic
end-to-end rent-vs-buy walkthrough using this chapter's decision tree and
formulas).

## 12. Outputs and artifacts

- [templates/COMPUTE_DEMAND_LEDGER.md](templates/COMPUTE_DEMAND_LEDGER.md),
  populated and reviewed at the cadence set in §6.
- A recorded purchase-trigger definition (threshold, review window), in the
  project profile or a
  [method decision record](templates/METHOD_DECISION_RECORD.md) if it deviates
  from a prior default.
- A dated rent-vs-buy break-even (H\*) computation with the current six inputs
  (§8), re-run whenever any input materially changes.
- A dated market-price snapshot with a stated shelf life, re-verified at order
  time — never carried forward as doctrine (§4, §9).
- A recorded cloud-tier assignment per workload, checked against §8's
  admissibility table.
- A cost-per-successful-task figure per candidate configuration, feeding chapter
  12's telemetry and any routing/cascade cost case in chapter 08.

## 13. Sources

| ID | Role here |
|---|---|
| [EXT-HW-001] | Market-snapshot discipline; as-of-dated price/benchmark verification (2026-08-20) |
| [NV-COSTTCO-001] | $/M-token TCO formula chain; datacenter-scale-assumption caveat |
| [NV-DYNAMOAICONFIG-001] | Second independent instance of the datacenter-scale-assumption caveat |
| [EXT-SWITCHYARD-001] | Routing break-even formula (full treatment in chapter 08) |
| [NV-LEPTONBREV-001] | Rentable GPU marketplace reference; rental-rate input source |
| [NV-DGXCLOUD-DEP-001] | Rentable-cloud product-naming churn caution |
| [EXT-FT-003], [EXT-UNSLOTH-001] | VRAM-floor guidance for sizing training/fine-tuning capacity (full defaults in chapter 09) |
| [INT-CASE-005] | Empirical case backing the four normative principles (§4) |

Gap dispositions in this chapter: no G-item is assigned to chapter 11 as primary.
Hardware/cloud policy is carried entirely as [DEFAULT]/[PARAMETER]-class material —
trigger-based purchase, demand ledger, and break-even are B-class defaults; every
price or threshold cited here is a C-class snapshot carrying its own
re-verify-at-order-time rule (§4, §9).

---

> [← Previous](10_DEPLOYMENT_AND_OPERATIONS.md) · [Index](README.md) · [Next →](12_OBSERVABILITY_LEARNING_AND_PROMOTION.md)
