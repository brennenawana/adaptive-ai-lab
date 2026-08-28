# What we ask Crexi for — and how far to trust the answer

> Code-verified 2026-08-27. Answers the operator's questions: what are the
> search parameters, where do they come from, what are we targeting, how
> accurate is Crexi's search, and what do we store / re-fetch.

## 1. The exact request

Every sweep page is one `POST /assets/search` with this complete body:

```json
{"count":100,"offset":0,"includeUnpriced":true,
 "sortOrder":"updatedOn","sortDirection":"Descending",
 "types":["Multifamily"],"states":["FL"]}
```

That is all of it. **No bbox, no unit key, no updated-since key, no sub-type.**

| key | source |
|---|---|
| `types` | config `property_types` = `("multifamily",)` → Title-Cased by `_CANONICAL_TYPES` (`assets_search.py:41-61`) |
| `states` | `--states FL` (CLI **overrides** config) |
| `includeUnpriced` | default **true** (`--exclude-unpriced` flips it) |
| `sortOrder` / `sortDirection` | **hardcoded** (`assets_search.py:90-91`) |
| `counties` | never set by normal scoping — injected **only** by the backfill partitioner, from a committed Census file, not config |
| `askingPriceMin/Max`, `occupancyMin/Max` | config; currently null |

`count` is the page size (100); `offset` is loop state.

## 2. Where the parameters come from — and a caveat about our baseline

`get_effective_scrape_config` returns the **active `scrape_profile` row**, else
falls back to `DEFAULT_SCRAPE_CONFIG` (`scrape_profile_service.py:39-51`).

- **Live prod profile (v2):** `states=["FL"]`, `property_types=["multifamily"]`,
  `unit_min=2`, `unit_max=4`, no price/occupancy bounds, 2 areas.
- **Our local baseline DB has ZERO `scrape_profile` rows** → it used
  `DEFAULT_SCRAPE_CONFIG`, whose `states` is `()`. An unseeded environment is a
  **no-op** (`scripts/crexi_ingest.py:176-178`); only `--states FL` made our run
  produce anything. So the baseline's parameters were a code default plus a CLI
  flag, not an operator-configured profile.

`scope_fingerprint` hashes the body minus offset/count, so changing types,
states, price, occupancy, or includeUnpriced invalidates the watermark and
forces a full re-sweep (`crexi_ingest.py:108-119, 276-282`).

## 3. What is filtered where

**Server-side (Crexi):** states · counties · types (**ANY-match**) · price ·
occupancy · includeUnpriced · sort · pagination. That is the entire server
filter surface.

**Explicitly NOT server-side:**
- **No unit filter.** `assets_search.py:12-13`: *"There is NO unit-count filter —
  the 2-4u gate stays client-side after the detail fetch."*
- **No updated-since filter.** The delta is a sorted early-stop at the watermark.

**Client-side (us):** the stub type gate (before any detail fetch), the unpriced
drop, and the full strict gate after the 3-call detail fetch (unit band,
sub-type, tenancy, price-per-unit, year, sqft, lot, stories, DOM, OZ, OM).

## 4. The compound-type problem — the operator's hypothesis, confirmed

**Crexi's `types` filter is ANY-match**, documented at `assets_search.py:10-11`:
*"types (ANY-match, so compound-type listings come back too)."* A listing tagged
`["Land","Multifamily"]` **does** return for a Multifamily query — exactly as
suspected, including land marketed *for* multifamily development.

The returned list is immediately flattened — `", ".join(item["types"])` → the
string `"Land, Multifamily"` (`assets_search.py:245-252`; the list is never
preserved). Our gate then does **exact set-membership on that joined string**
(`listing_filters.py:106-108`), so every compound type is dropped.

**This is deliberate, not a bug.** `listing_harvester.py:116-122`: *"Strict per
operator choice — compound types like 'Land, Multifamily' are excluded (exact
match against the lower-cased set)."* Locked by tests at
`test_crexi_listings.py:160` and `test_crexi_ingest_service.py:127`.

So the type gate is currently the **only** protection against the land-plot
problem — and it is indiscriminate: it also discards legitimate compounds. It
cost **555 of 1,962 swept assets (28.3%)** in the baseline.

**A real inconsistency:** the *comps* harvester matches by **substring** and
therefore **keeps** compound types (`harvester.py:141-149`), while the
*listings* harvester matches exactly and drops them. The two Crexi paths
disagree about what a multifamily property is.

**`property_sub_type` is the unused signal.** It is captured, normalized, and
stored — and never filtered on (`property_sub_types` defaults to `()`).
Observed in our 100 stored rows:

| sub_type | n |
|---|---|
| Apartment Building, Duplex/Triplex/Quadruplex | 36 |
| Apartment Building | 24 |
| Apartment Building, Duplex/Triplex/Quadruplex, Fourplex | 15 |
| **Single Family Rental Portfolio** | 7 |
| *(empty)* | 6 |
| **Single Family Rental Portfolio, RV Park, Apartment Building** | 2 |
| Apartment/Condo variants | 3 |

We are storing SFR portfolios and an RV park in a 2–4-unit multifamily ingest.

## 5. Storage and re-ingest economy — the operator's procedural concern

**Non-strict listings ARE stored, by design.** `strict` controls only the
counter and photo mirroring (`crexi_ingest.py:386-396`); every type-matched,
detail-fetched listing is upserted regardless of the unit band
(`crexi_ingest.py:12-15, 397`).

**There is NO "known uninteresting, do not re-fetch" mechanism.**

The only economy is freshness: a stub is skipped when its `updatedOn` ≤ the
stored `source_updated_on` (`crexi_ingest.py:322-331`). Consequence:

> A listing we have already rejected pays a **full 3-request detail fetch**
> (`get_property_asset` + `get_asset_brokers` + `get_asset_gallery`) **every time
> its `updatedOn` moves at all** — a price edit, a description edit, a DOM tick.
> It is then re-normalized, re-fails the filter, and is re-upserted anyway.
> Forever.

That is the waste the operator anticipated, quantified: 3 requests per rejected
listing per update, with no suppression path.

## 6. How much to trust the result set

Not fully — and this is already the top open defect (**F-B14**): county
partitions reached **1,965 of 3,496** in-scope listings (**56%**). Every
downstream rate is therefore a rate over the wrong denominator.

Additional structure worth knowing: partitioning fires only on a full sweep and
only when `total_count > 1400`; counties come from a committed Census gazetteer
(FL 67 entries) and an unknown state falls back to price-bisection; zero-count
counties are skipped.

## Recommendations (recommendations, not actions)

1. **Settle F-B14 first** — a denominator that is 56% of scope invalidates every
   other rate. One live probe: whole-state paged sweep vs the county union.
2. **Decide the targeting question explicitly** — it is an operator call, not a
   code fix: is `"Office, Multifamily"` a deal? Is a `Single Family Rental
   Portfolio`? An `RV Park`? Today the answer is implicit in an exact-match
   string test and inconsistent between two code paths.
3. **`property_sub_type` is the lever** for "don't store what we don't want" —
   already captured, already stored, never used.
4. **A do-not-refetch marker** is the lever for "don't waste time re-ingesting."
   None exists; the freshness check cannot express "known uninteresting."
