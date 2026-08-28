# GOAL — validate the capped single-sweep, fix the fallback partition key, then STOP

> Self-contained: this file plus `SEARCH_PARAMETERS.md`, `runs/coverage_report_FL.txt`
> and `STATE.md`. Nothing else. Supersedes `GOAL_COVERAGE.md` (complete).

## What was just established

- **F-B14 confirmed**: county partitioning reached 1,962 of 3,496 (**44% lost**),
  because Crexi's county field is un-normalized (`"Duval"` 107 vs `"Duval County"`
  25) and **939 listings carry no county string at all**.
- **The cause of partitioning at all**: Crexi refuses `offset + count >= 1500`,
  so any population over ~1,499 must be split.
- **Measured live**: FL multifamily by price cap —

  | cap | in scope | vs 1,499 |
  |---|---|---|
  | none | 3,498 | must partition |
  | ≤ $1,000,000 | 1,754 | must partition |
  | **≤ $800,000** | **1,374** | **one sweep** |
  | ≤ $600,000 | 846 | one sweep |

- **Operator direction**: target state + price cap (~$800k, not luxury); if a
  scope exceeds the ceiling, fall back to another partition strategy.
- **Correction to the operator's plan**: a minimum-bedroom filter is **not
  available**. The search stub carries only `asking_price`, `has_price`,
  `status`, `type_str`, `updated_on` — no beds, no units, no sub-type. Bed data
  barely exists post-fetch either (3/100 raw payloads). The land-plot lever is
  `type_str`, which IS pre-fetch and free.

## The key insight to act on

`crexi_ingest.py:180-182` **already implements** "if the scope is too big, use
another strategy": it partitions when `total_count > SAFE_WINDOW (1400)`.

The bug is not the absence of a fallback — it is that **the fallback key is
county**, which cannot cover the scope. The product already ships a working
alternative: `_price_bisect` (`crexi_ingest.py:205-224`), proven on this exact
scope at 3,496/3,496 in 14 bands / 77 requests.

So the change is narrow: **make price the fallback partition key instead of
county.** No new mechanism, no operator policy decision.

## Hard constraints

- `~/code/wholesaling` is **READ-ONLY**. `git -C ~/code/wholesaling status` clean
  at the end. Prove the change as a rig-side patch; deliver a work order, not an
  edit.
- Everything through `./rig/run.sh`. Never bypass it (production R2 hazard).
- Live calls: bound them, record to a cassette, stay clear of the prod cron
  (01:41 / 07:41 / 13:41 / 19:41 UTC).
- `db.sh restore pre_ingest_baseline` before any replay — the ingest is stateful.
- Branch `project/wholesaling-intake`; `NEXT.md` first, then `STATE.md`.

## Phase 1 — does the capped single sweep actually work?

`total_count` said 1,374. That is a probe, not an enumeration. Verify:

1. Run a real paged sweep for `states=("FL",) types=("multifamily",)
   asking_price_max=800_000`, no county scoping, and **enumerate distinct asset
   ids**. Does it reach 1,374? Any silent truncation?
2. **Settle the unpriced question.** `include_unpriced` defaults True. With
   `asking_price_max` set, are unpriced listings still returned, or silently
   dropped? The coverage report shows real unpriced MF in scope (a 10-unit in
   Marathon, a 67-unit on Miami Beach). Losing them invisibly is the same class
   of failure as F-B14. Measure it: compare counts with `include_unpriced`
   True vs False at the same cap, and check whether any enumerated asset has
   `has_price=False`.
3. Report the **headroom**: 1,374 of 1,499 is 8%. State how much growth the cap
   absorbs before partitioning is forced.

## Phase 2 — prove price-as-fallback

As a **rig-side patch** (not a product edit), make the partitioner use
`_price_bisect` instead of `counties_for_state` when
`total_count > SAFE_WINDOW`. Then:

1. Run it against the **uncapped** FL scope (3,498) and confirm it enumerates
   the full population — the previous session measured 3,496/3,496 in 14 bands /
   77 requests; reproduce or refute that.
2. Compare the resulting id set against the frozen county-union baseline
   (`runs/ingest_trace_FL_replay1.jsonl`, 1,962 ids). Confirm the county set is
   a strict subset.
3. Carry the previous session's caveat forward and settle it: every tail band
   returned a near-constant ~47–52, consistent with unpriced records appearing
   in **every** band. If true, price bisection double-counts or mis-attributes
   unpriced listings — quantify it before recommending price as the only key.

## Phase 3 — the work order, then STOP

Write a work order for the wholesaling repo (spec, measurement, acceptance)
covering: price as the fallback partition key, and the scrape-profile change to
set `price_max`. **Do not implement it.**

Do NOT touch: the type gate, sub-type filtering, a do-not-refetch marker,
F-B10/F-B11/F-B8/F-B2. The type/sub-type policy is an operator decision with its
evidence already in `runs/coverage_report_FL.txt` §3.

## Settled — do not revisit

- F-B14 (confirmed, 43.9% loss; mechanism is un-normalized county strings).
- Seeding a rehab estimate; "making the gate reachable" (FINDINGS.md F-B9).
- Minimum-bedroom filtering (no bed/unit data pre-fetch; see above).
