# GOAL — settle the denominator (F-B14), then build the targeting decision packet, then STOP

> Session goal file. Self-contained: this file plus `SEARCH_PARAMETERS.md` and
> `STATE.md` in the same directory. Nothing else.
> Supersedes `GOAL_INGEST.md` (complete) and `GOAL_BASELINE.md` (paused).

## Why this scope

The ingest baseline is frozen, but **F-B14** says the county-partitioned sweep
reached only **1,965 of 3,496** in-scope listings (**56%**). Until that is
settled every rate we have is computed over the wrong denominator, so no
improvement can be measured honestly. Nothing else should start first.

Second, the biggest lever on ingest quality is **not a code fix** — it is a
targeting policy only the operator can set (is `"Office, Multifamily"` a deal? an
SFR portfolio? an RV park?). Your job is to make that decision cheap to make, not
to make it.

## Hard constraints

- **`~/code/wholesaling` is READ-ONLY.** `git -C ~/code/wholesaling status` must
  be clean at the end. All instrumentation is seam-wrapping in the lab repo.
- Invoke everything through `./rig/run.sh`. Never bypass it — running from
  `~/code/wholesaling/backend` silently re-enables the **production** R2 mirror.
- Branch `project/wholesaling-intake`. Commit and push at each phase. Update
  `NEXT.md` first, then `STATE.md`.
- **Phase 1 needs LIVE Crexi calls.** Record them into a cassette. Stay clear of
  the prod cron: 01:41 / 07:41 / 13:41 / 19:41 UTC. Bound every sweep.
- **`db.sh restore pre_ingest_baseline` before any replay** — the ingest is
  stateful; an `--apply` pass stamps the cursor and the next run takes the
  incremental branch with an unrecorded request body.

## Phase 1 — settle F-B14

**Question:** does the county-partition union actually miss ~44% of the FL
multifamily book, or is the whole-state `total_count` an inflated denominator?

**Probe (bounded, live, recorded):** run a **whole-state paged sweep** for
`types=["Multifamily"], states=["FL"]` — no county scoping — collecting asset
ids until exhaustion or a stated page cap. Compare that id set against the
**union of the 56 county sweeps** already in the frozen trace.

Report:
- |whole-state| , |county-union| , |intersection| , |whole-state only| ,
  |county-union only|
- whether `total_count` (3,496 / 3,480 observed earlier) matches |whole-state|
- for a sample of assets present whole-state but absent from every county sweep:
  what county does the payload claim, and was that county swept?

**Pre-registered hypothesis (from the ingest session — do not revise it):** the
gap is Crexi's county index, not delisting. Asset `2297949`'s payload says
Brevard yet it returns under Orange and Osceola filters.

**Pre-registered falsifier:** if the whole-state paged sweep returns
approximately the same 1,965 assets, then the whole-state `total_count` is
inflated and **F-B14 is a reporting artefact, not a coverage loss.** Record that
outcome plainly if it happens — it is the cheaper world and equally valuable.

**Also determine:** the `SAFE_WINDOW = 1400` pagination cap (`crexi_ingest.py:61`)
and the 1,499-offset ceiling (`assets_search.py:180`) — does either silently
truncate a whole-state sweep? That would explain a gap without any county-index
theory.

## Phase 2 — the targeting decision packet

Produce the evidence the operator needs to set targeting policy. **Do not decide
it.** Over the in-scope FL multifamily population (use the frozen trace plus the
Phase-1 sweep):

1. **Compound-type census.** Every distinct `types` combination containing
   Multifamily, with counts. How many are `Land, Multifamily`? `Office,
   Multifamily`? etc. Include 2–3 real examples per combination (address, ask,
   units, first line of description) so the operator can judge.
2. **Sub-type census.** Every distinct `property_sub_type` with counts, flagged
   where it looks out of scope for a 2–4 unit MF buy-box (`Single Family Rental
   Portfolio`, `RV Park`, `Apartment/Condo`, empty).
3. **The cost of each policy.** For each candidate rule, how many listings would
   be admitted/excluded, and how many *detail fetches* (3 requests each) would be
   saved or spent.
4. **The inconsistency.** State plainly that the comps harvester substring-matches
   and KEEPS compound types (`harvester.py:141-149`) while the listings harvester
   exact-matches and DROPS them (`listing_filters.py:106-108`) — two code paths
   disagreeing about what multifamily is. Do not fix it; surface it as a
   decision.

## Bookkeeping correction (do this)

`rig/defects.py` records **F-B15** as high-severity with rationale "config
documents substrings; code does set membership." That is now known to be
**deliberate**: `listing_harvester.py:116-122` says *"Strict per operator choice
— compound types like 'Land, Multifamily' are excluded"*, and
`test_crexi_listings.py:160` / `test_crexi_ingest_service.py:127` lock it in.

Re-classify F-B15 honestly: the exact-match is intentional; what is open is
whether the *policy* is right, and the listings/comps inconsistency. Keep the id.

## STOP CONDITION

When Phase 1 has a verdict and Phase 2's packet exists, **STOP and hand back.**

Do NOT: change the type gate, add sub-type filtering, add a do-not-refetch
marker, or touch F-B10/F-B11/F-B8/F-B2. Every one of those waits on the
operator's targeting decision.

Report: the F-B14 verdict against its hypothesis and falsifier, the decision
packet, and a recommended first change — as a recommendation.

## Settled — do not revisit (FINDINGS.md F-B9)

- Seeding a rehab estimate (inert, 0.05% of the book).
- "Making the gate reachable" (a tautology; the router declines to price).
