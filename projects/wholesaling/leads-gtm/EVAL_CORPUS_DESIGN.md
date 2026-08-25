# Eval Corpus Design — Why Fresh Pulls, and What They Can and Cannot Prove

> Method decision, 2026-08-25. Supersedes the sampling-frame note in
> `PLAYBOOK_PATH.md §4` (which proposed drawing from the existing 5,797
> step-4 properties). Governed by playbook P5 (measurement validity before
> comparison) and ch. 02 (execution-system identity).

## The operator's hypothesis, and why it is correct

*"Evaluate from fresh data pulls — the database is in disarray in terms of how
each property was processed."*

**Confirmed, by the codebase's own measurement.** `config/underwriting_version.py`'s
docstring records the prod failure of 2026-08-04: **8 coexisting underwriting
versions with only 8.7% of the book at head**. Every stored `arv`,
`condition_tier`, `offer_price`, and `rehab_estimate` was produced by whichever
code version happened to be deployed when that row was last touched — plus
whichever *inputs* existed at that moment.

In playbook terms, the stored book is not one instrument, it is a **mixture of
unknown instruments**. Scoring it would cross an unmeasured
[reproducibility boundary](playbook ch. 02) — the exact condition global
tripwire 3 says to stop on. A pooled accuracy number over that book would
measure the deployment history, not the system.

Supporting evidence, same direction:
- `math_version` (superseded) and the layered manifest both still stamp rows,
  so a single book contains rows versioned by two different schemes.
- `rehab_as_of` is pinned to `2025-01-01` with a never-executed "BUMP when
  recalibrated" instruction — rows are stamped with a date that no longer
  tracks the model.
- Fixes shipped *after* most rows were written: universal T+I defaults removed,
  the AFR seller-carry floor, the 5-tier income ladder, the ARV/rent
  credibility floors, the freshness `observed_at` fix (`98be3243`).
- Known historical contamination: 71.7% of valid ARVs once shared a handful of
  identical market-average values; 6,037 valuations ran on the 1,200-sqft
  default.

**Decision: the evaluation corpus is produced by a fresh, pinned re-pull and
re-underwrite — not read out of the existing book.**

## The qualification that matters most

**A fresh pull gives you a valid *instrument*. It does not give you *ground
truth*.**

Re-running the current code on fresh data tells you what today's system
outputs, under a known identity. It cannot tell you whether those outputs are
*right* — comparing the system to itself is circular, and it is exactly how the
existing goldens ended up pinning drift rather than correctness (they "were
derived by running the shipped engine once").

Every number the lead product sells therefore needs an **independent
reference**, gathered separately from the pipeline:

| Number | Independent reference candidate |
|---|---|
| Taxes + insurance | County millage lookup + a real quote/band for the parcel — the one error already measured (5×–6.7×) |
| ARV | Desk comps by a human, or subsequent actual sale price where available |
| Rent | Actual listed rents / lease evidence, not our own FMR tier |
| Condition | Human label from the same photos (the `vision_golden_label` pattern) |
| Price/structure | Deterministic recomputation is fine — this half is already proven |

The FL n=6 run is the template: independent desk research versus pipeline
output. It found the errors precisely *because* the reference did not come from
the pipeline. Scale that method; do not replace it with a self-comparison.

## What the existing book is still good for

The old rows are not worthless — they are the wrong tool for scoring, and the
right tool for two other jobs:

1. **Error analysis / failure harvesting** (ch. 03 §5.1 requires real observed
   failures to derive the ontology). Mirage cases, sub-payoff offers, the
   $18,339/mo "rent", the identical-ARV cohorts — all come from the historical
   book and all remain valid as *failure specimens*.
2. **Coverage and completeness questions** — how much of the book has an ARV at
   all, HOA at 0.8%, condition-source mix. These are facts about the data
   estate, not quality claims about a model.

The rule: **the old book tells you what goes wrong; the fresh pull tells you
how often, under a known instrument.**

## Design constraints for the fresh pull

1. **Pin the execution system before pulling.** Record the commit SHA, the
   `underwriting_version` vector for all four layers, model ids for both AI
   inputs (condition vision, income extraction), and the REFDATA CSV digests.
   Without this the fresh pull becomes tomorrow's disarray.
2. **Isolate from the crons — this is a live hazard, not a theoretical one.**
   `cloud-nightly.yml` runs `*/5` (despite a header claiming it is disabled and
   kept out of service), `data-discovery` `*/15`, `data-enrich` at
   `5,20,35,50`, `crexi-ingest` every 6h — four concurrent writers to
   `property`. An eval reading or re-underwriting rows while those run will
   have its corpus mutated mid-measurement, and the INC-001 lock-contention
   pattern is still open on the ingest side. Either pause the schedules for the
   window, or snapshot the sample to an eval-scoped table first.
3. **Prefer the reunderwrite freeze path for the pricing half.**
   `services/reunderwrite.py:507,554-559` already captures and restores each
   deal's status and property `lifecycle_stage`, so a recompute cannot push
   anything toward a send/pitch queue — and the `inputs_fingerprint` no-op
   guard means a version bump alone will not dirty the book.
4. **Supply constrains where a fresh pull is even possible.** With ingestion
   dead in 6 of 8 markets, only **Detroit and Grand Rapids** (Redfin) and the
   **Crexi MF lane** (4,264 listings, 3,741 on-market, 1,423 seen in 48h) can
   currently produce fresh rows. Either fix supply first, or scope the first
   eval to the lanes that are actually alive and say so explicitly.
5. **Stratify the sample deliberately** — by market, property type, condition
   source (heuristic vs vision), and ARV source (comps vs assessed-fallback vs
   FL JV). Pooling these hides exactly the differences that matter; the JV lane
   in particular produces a *visible* ARV at confidence 0.036 that can never
   price.
6. **Size for a stated MDE, before pulling** (ch. 04). The FL run's n=6 was
   enough to expose a 5×–6.7× systematic error, and nowhere near enough to
   estimate a rate. Decide which claim the first eval must support and size for
   that, not for convenience.
7. **Hold the sample out properly.** Once pulled and referenced, it is spent on
   each look; ledger it (P8).

## Consequence for the plan

`PLAYBOOK_PATH.md §4` action 1 is amended: the first eval's corpus is a
**pinned fresh pull over a stratified sample from currently-live lanes**, with
independently gathered references, not a query over the existing book. The
condition surface remains the first *AI* target, but the first **product**
target is carrying costs (taxes + insurance) — the one error already measured
and the one the entire existing test suite is structurally blind to.
