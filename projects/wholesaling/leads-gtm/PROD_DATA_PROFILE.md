# Prod Data Profile — Sellable-Lead Readiness (2026-08-25)

> Read-only SQL profile of the production database (`gphfopnfwsehgobfslfb`),
> run under no-write/no-PII constraints for the lead-sale go-to-market
> question: *how many sellable leads exist today, and where is the count
> lost?* Aggregates only. Freshness uses `listing.last_seen_at` (there is no
> `property.observed_at`).

## Headline

**~100 of 22,026 properties (0.45%) are complete, sellable leads today**
under a reasonable definition (address+state · observed ≤90d · ARV ·
condition-or-rehab · computed price · reachable contact).

| Step | Filter | Remaining | Lost |
|---|---|---|---|
| 0 | All properties | 22,026 | — |
| 1 | + address & state | 22,026 | 0 |
| 2 | + observed ≤90 days | 14,652 | 7,374 |
| 3 | + has ARV | 9,381 | 5,271 |
| 4 | + condition tier or rehab estimate | 5,797 | 3,584 |
| 5 | + **computed price** | 516 | **5,281** |
| 6 | + reachable contact | **100** | 416 |

## Book composition

22,026 properties (16,952 archived / 5,074 active). MI 16,430 · FL 2,760 ·
OH 470 · CA 207 · TX 183 · NY 180 · long tail across 41 more states.
Types: single_family 14,806 · land 2,682 · duplex 2,483 · multifamily 2,055.
Sources: opendata 13,566 · crexi 4,179 · redfin 3,293 · rentcast 983 ·
manual 5.

Freshness: `listing.last_seen_at` only goes back to 2026-06-12, so ">90 days"
is structurally empty — a young column, not a clean book. 7,349 properties
(mostly archived) have no `last_seen_at` at all.

## Underwriting completeness (latest row per property)

| Field | Have | Base | % |
|---|---|---|---|
| Any valuation row | 16,271 | 22,026 | 74% |
| ARV | 10,283 | 22,026 | 47% |
| Rehab estimate | 12,044 | 22,026 | 55% |
| Rent estimate | 16,043 | 22,026 | 73% |
| Any deal row | 16,205 | 22,026 | 74% |
| Strategy assessment present | 16,156 | 16,205 | 99.7% |
| **Priced target** (`strategy_assessment->>'target_price'`) | 1,163 | 16,205 | **7%** |
| Formal `deal.offer_price` | 684 | 16,205 | 4% |

**Why pricing is the chokepoint — and why it may be the wrong metric.**
Strategy verdicts split `pass` 11,782 / `park` 2,959 / `conditional_pursue`
1,420. A `target_price` **key** exists on nearly every deal, but its **value**
is populated essentially only for `conditional_pursue`. So the pipeline prices
only what *we* would buy. See §"Strategic implication".

## Condition coverage — completeness is largely nominal

| condition_tier | n | | condition_source | n |
|---|---|---|---|---|
| moderate | 13,486 | | heuristic | 13,987 |
| null | 7,523 | | vision (LLM) | 405 |
| unknown (explicit) | 626 | | dlba_program | 103 |
| distressed | 178 | | operator (human) | 8 |
| turnkey | 104 | | | |
| light | 56 | | | |
| heavy | 53 | | | |

66% carry a tier, but **only 405 (1.8%) came from actual image analysis**;
13,987 are `heuristic` — and the heuristic's modal output is `moderate`,
which is also the single most common tier in the book. For an internal
pipeline that is a defensible placeholder. **For a sold lead it is a
confident-looking value that was never measured** — precisely the
silent-failure class (P11). Step 4 of the funnel above therefore overstates
real condition coverage by roughly an order of magnitude.

## Contact reachability

| | n (of 22,001 with a listing) |
|---|---|
| Linked listing agent | 6,097 |
| Agent phone on file | 4,782 |
| **Agent phone validated** | **0** |
| Agent email on file | 5,155 |
| Agent email validated | 1,176 |
| Reachable (validated email or phone) | 1,176 (5.3%) |

`agent.phone_validated` is `TRUE` for **zero of 10,431 agents** despite 9,200
having phones — phone validation is unpopulated/unimplemented, not merely
sparse. Reachability today is email-validation-only.

## Pipeline position

`lifecycle_stage`: guardrail 14,347 (65%) · source 3,478 · enrich 2,343 ·
lost 677 · route 616 · generate 505 · send 41 · followup 17 · nurture 2.
`deal.status`: new 11,649 · held 4,531 · rejected 19 · called 11.
The book is stalled at gate-review; combined route+generate+send is 1,162 (5%).

## Strategic implication (for the lead-sale model)

The funnel's dominant loss (5,797 → 516) is **not missing data — it is our own
buy-box rejecting inventory**. `pass`/`park` verdicts mean *we* would not
pursue; they say nothing about whether a lead buyer with a different buy box,
different capital cost, or different market would want it. In a
pursue-it-ourselves model, filtering hard is correct. **In a sell-the-lead
model, the pass/park population is potentially the inventory, not the
discard** — and pricing it requires a buyer-relative valuation, not our MAO.

That reframes the immediate research question from "why is our pricing
coverage low" to **"what does a lead buyer need stated, and can we state it
honestly for the 5,797 properties that already have ARV + condition?"**

## Data-integrity notes for any eval built on this book

- No `property.observed_at`; freshness must come from `listing.last_seen_at`,
  whose history starts 2026-06-12.
- `deal.offer_price` is a formal-offer field (684 rows), **not** the computed
  price; the real priced output is JSON at
  `deal.strategy_assessment->>'target_price'`.
- Condition completeness must be sliced by `condition_source` or it is
  misleading (see above).
- Any sampling frame for an eval should be drawn from the 5,797 at step 4
  (has ARV + some condition signal), stratified by `condition_source`,
  state, and property type.
