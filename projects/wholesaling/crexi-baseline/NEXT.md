# NEXT — the single source of truth for "what do I do now"

> If you read one file, read this one. Updated at every checkpoint.
> Last updated: 2026-08-28 (F-B14 settled; targeting decision packet delivered).

## The arc (your mental model is correct)

```
PHASE 1  harvest defect classes from real listings        <- done (16 classes)
PHASE 2  freeze a baseline: one measured run over a       <- INGEST half done and
         defined corpus, numbers not anecdotes               its denominator now SETTLED;
                                                             value-route half outstanding
PHASE 3  iterate: change ONE thing, re-run, measure       <- BLOCKED on the operator's
         the delta against the frozen baseline               targeting decision
```

Phase 3 is the point. Phases 1–2 exist only to make Phase 3's numbers mean
something.

## ACTIVE GOAL: none — `GOAL_COVERAGE.md` is COMPLETE. Waiting on an operator decision.

Both phases done, 2026-08-28. **Nothing was fixed** — that was the instruction.

### Phase 1 — F-B14 is SETTLED: CONFIRMED, 43.9% coverage loss

The pre-registered falsifier was tested and **did not fire**.

```
whole-state population, ENUMERATED (price-partitioned)   3496
whole-state total_count reported by Crexi                3496   exact match
county-partition union (frozen baseline)                 1962
  intersection                                           1962   <- strict SUBSET
  whole-state only                                       1534   43.9% of scope
  county-union only                                         0
```

Ruled out along the way: the pagination caps (`PAGE_WINDOW=1500`, `SAFE_WINDOW=1400`)
explain nothing — verified live, and the server's real rule is `offset < 1500`, not
the `offset + count < 1500` its own error message claims. Delisting explains nothing —
all 1,534 are `On-Market` and 0 were activated after the frozen run.

**The mechanism is NOT the one the ingest session predicted.** `counties` is a
case-insensitive but otherwise **literal string match** on the record's own county
field: `"Duval County"` returns 25, `"Duval"` returns 107, `"St. Lucie County"` 10 vs
`"St Lucie County"` 25. The filter *is* a payload-county match — that is exactly why
it misses, because Crexi's county field is un-normalized. And **939 of 3,496 records
carry no county string at all**, so no county key of any spelling reaches them.

> County partitioning cannot cover the scope. It is not a longer-county-list problem.

### Phase 2 — the targeting decision packet exists

`runs/coverage_report_FL.txt` (also JSON: `runs/targeting_packet_FL.json`). It has the
compound-type census over the corrected 3,496 denominator, the sub-type census with its
honest denominator, the cost of five candidate policies in listings and in detail
fetches, 3 judgeable examples per type set with address / ask / **units** / sub-type /
description, and the listings-vs-comps inconsistency stated plainly.

### THE NEXT ACTION — an operator decision, then one code change

**The decision (yours, not the rig's):** which of P0–P4 in
`runs/coverage_report_FL.txt` §3 is the buy-box? Read §1's examples first — the
drop set contains a 4-unit at $494k in Jacksonville *and* an auto shop.

**The recommended first change, once that is answered — and it is NOT the type gate.**
Replace county partitioning with price-band partitioning in `backfill_partitions`.
Reasons, in order:

1. It needs **no operator decision** and no underwriting judgement. The type policy
   does, and blocks on you.
2. It is **already proven to work on this exact scope**: `_price_bisect` — the
   product's own fallback function, unmodified — enumerated 3,496 of 3,496 in 14
   bands, 77 requests, 0 warnings, 0 truncation.
3. It is worth **+1,003 admitted listings** even under today's unchanged type gate
   (2,410 vs 1,407) — comparable to the type policy's +1,086, and additive with it.
   The two defects are near-independent: 34.6% of the missed are compound vs 28.3%
   of the reached.
4. Until it lands, **every rate in the frozen baseline is over a 56.1% denominator.**

Caveat to carry into that change: the product itself warns that unpriced listings
"don't attach to price bands reliably" (`crexi_ingest.py:175-178`). Our probe found no
loss (3,496 = 3,496), but the tail bands each returned a constant ~47-52, which is
consistent with unpriced records appearing in *every* band. That wants a deliberate
check before it becomes the only partition key.

### Explicitly NOT done, on instruction

Did not change the type gate, did not add sub-type filtering, did not add a
do-not-refetch marker, did not touch F-B10 / F-B11 / F-B8 / F-B2. All wait on the
targeting decision.

## Phase 1 is done when

- [x] rig runs the real pass locally, safely, offline
- [x] provenance ledger distinguishes script / LLM / API / default
- [x] both arms reproducible (AI cassette landed)
- [x] ≥8 defect classes with evidence chains
- [ ] **defect classes mapped to the playbook's RC taxonomy** (RC-1…RC-12) —
      the only remaining item, ~30 min, needed so Phase 3 picks the right
      intervention rung

## Phase 2 is done when

A frozen baseline exists: corpus digest + per-field producer mix + per-defect
rate + the manifest (git SHA, alembic head, arm, cassette digests). That is the
number every later change is measured against.

**Ingest half: DONE, and its denominator is now correct.**
`runs/ingest_trace_FL_record.jsonl` + `runs/ingest_funnel_FL.txt`, manifest inline,
10/10 counters reconciled, fingerprint `3c15972614b09973` reproduced 3x offline.

**Read those rates against 3,496, not 1,962** (F-B14, settled 2026-08-28). The funnel
table itself is unchanged and still correct for what it measured; only the denominator
moved:

| | as the table reports it | over the true scope |
|---|---|---|
| reached by the sweep | 1,962 / 1,962 = 100% | **56.1%** |
| admitted by the type gate | 1,407 / 1,962 = 71.7% | **40.2%** |
| strict 2-4u matches | 90 / 1,962 = 4.6% | **2.6%** |

Value-route half: still the `trace.py` / `provenance.py` outputs, unchanged.

## Phase 3 (value-route lane): the first experiment is already chosen

Unblocked and independent of the targeting decision, which only gates the INGEST lane.

**Fix F-B4** (`_numbers_in` cannot parse `$400k`) → re-run → measure how many
listings move rent above the 0.35 confidence floor.

Pre-registered, because it must be stated before we look:
- **Prediction:** F-B4 affects ~6% of descriptions and ~25% of successful
  extractions. Expect single-digit percentage-point movement locally.
- **Business stake:** in prod, 3,286 cards die at `non_offerable:basis_unverified`
  on rent conf 0.30 < 0.35, and 93% of them already carry a usable description.
- **Consequence if it doesn't move the needle:** F-B4 is real but not the
  binding constraint; move to the tier-1 generator being OFF in prod (0 rows of
  `crexi:marketing_desc:llm` ever), which is a config/wiring issue, not a parse bug.

## Standing queue (do NOT start these before Phase 2 closes)

0. **F-B14's fix — price-band partitioning.** Ready to specify, deliberately not
   written: `GOAL_COVERAGE.md` said settle-then-stop. See "THE NEXT ACTION" above.
1. F-B8 — map `sale_event_name` → the ARV provenance field. **Underwriting
   change**, needs operator sign-off + before/after measurement.
2. F-B2 — persist `comp_set` (already computed, dropped at write time).
3. Condition: 98% of dead cards have photos and NULL condition tier.

## Things ruled OUT (don't revisit without new evidence)

- **Seeding a rehab estimate** — inert on this book (0.05%); see F-B9.
- **"Making the gate reachable"** — a tautology; the gate runs fine, the router
  declines to price. See F-B9.

## Update discipline

Whoever finishes a checkpoint updates THIS file first, then STATE.md. If this
file is stale, that is the bug — not the reader's confusion.
