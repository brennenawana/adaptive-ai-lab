# Leads Go-To-Market — Scoped Research (2026-08-25)

Speed-run research pass for the pivot to **selling leads** instead of pursuing
deals. Scope deliberately narrowed to **ingestion** (supply) and
**underwriting** (the product). Three parallel surveys, code-verified and
prod-probed.

| Doc | What it answers |
|---|---|
| [INGESTION_STATE.md](INGESTION_STATE.md) | Where leads come from, on what schedule, with what identity/dedup and freshness rules — and what is actually running in prod |
| [UNDERWRITING_TRUST.md](UNDERWRITING_TRUST.md) | Whether the numbers we would sell can be trusted, and on what evidence |
| [UNDERWRITING_MECHANICS.md](UNDERWRITING_MECHANICS.md) | How each number is produced: ARV, condition→rehab, the solvers, routing, versioning, gates |
| [PROD_DATA_PROFILE.md](PROD_DATA_PROFILE.md) | How many sellable leads exist today and where the funnel loses them |
| [EVAL_CORPUS_DESIGN.md](EVAL_CORPUS_DESIGN.md) | Why the eval corpus must be a pinned fresh pull, and what that can/cannot prove |
| [INFERENCE_ECONOMICS.md](INFERENCE_ECONOMICS.md) | Open-weight models, platform choice, and whether visibility suffices for the playbook |

## The three findings that decide the go-to-market

**1. Supply is broken before quality even matters.** Six of eight markets
ingested **zero listings across 82 runs each over three days, every run
stamped `succeeded`** — and three compounding mechanisms guarantee silence: no
`source_health` rows are written for those markets (detectors have nothing to
compare), `is_volume_anomaly` returns False below a baseline of 20 (a market
pinned at 0 is never flagged), and `coverage_ratio` is NULL everywhere because
the coverage denominator is WAF-blocked. `data-discovery` has 0 successes in
1000 runs. You cannot sell leads from markets that are not ingesting.

**2. The product is the unproven half.** The solver is the best-tested code in
the repo (26+11+3 invariants, a genuine closed-form differential oracle, nine
seeds, CI that structurally cannot skip it) — and it is proven only *given
inputs*. The pricing harness hands the solver its carrying costs from a
hard-coded table, so `area_costs.py` and the `HOLD_AREA_COSTS_MISSING` gate are
never exercised, which makes the FL sample's **5×–6.7× tax+insurance
understatement structurally invisible** to all 330 cases. A buyer purchases
ARV, rehab, carrying costs, and a price — every one an *input*.

**3. Only ~100 of 22,026 properties (0.45%) are complete sellable leads**, and
the funnel's dominant loss is **our own buy box**, not missing data: strategy
verdicts resolve `pass` 11,782 / `park` 2,959 / `conditional_pursue` 1,420, and
pricing populates essentially only for `conditional_pursue`. In a
pursue-it-ourselves model, filtering hard was correct; **in a sell-the-lead
model the pass/park pile is plausibly the inventory.** Separately, condition
completeness is nominal — 66% carry a tier but only **1.8%** came from image
analysis; the rest is a heuristic whose modal output is "moderate."

## What this implies for sequencing

Ordered by what blocks what, not by appeal:

1. **Restore and instrument supply** (ingestion). Nothing downstream matters if
   6/8 markets produce nothing. The alerting gap is as important as the outage:
   the detectors are well-built and structurally unable to fire on a
   zero-volume market.
2. **Decide the product definition** — what a buyer must be told, and what
   "we don't know" is allowed to look like. This is a business decision, not a
   measurement, and it gates the eval design.
3. **Evaluate inputs, not the solver** — carrying costs first (the one
   measured error), then ARV, then condition/rehab. Building a solver eval
   would re-prove the strongest thing in the codebase while leaving the known
   5×–6.7× error untouched.
4. **Re-price the pass/park population** against a buyer-relative frame, if the
   business decision in (2) says that inventory is in scope.

Everything here is observation. No change has been made to the wholesaling
repo, and nothing is armed.
