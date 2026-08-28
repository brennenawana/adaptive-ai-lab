# What we ask Crexi for — and how far to trust the answer

> Code-verified 2026-08-27; §4 and §6 updated 2026-08-28 with live-probe results
> (F-B14 settled). Answers the operator's questions: what are the
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
Observed across **250** detail-fetched assets that **passed today's exact-match
type gate** (150 from the ingest cassette + 100 stored rows):

| sub_type | n |
|---|---|
| Apartment Building, Duplex/Triplex/Quadruplex | 128 |
| Apartment Building, Duplex/Triplex/Quadruplex, Fourplex | 40 |
| Apartment Building | 34 |
| **(empty)** | 9 |
| **Single Family Rental Portfolio** | 9 |
| **Apartment Building, Apartment/Condo** | 7 |
| **Apartment Building, Duplex/Triplex/Quadruplex, Apartment/Condo** | 6 |
| Apartment Building, Duplex/Triplex/Quadruplex, Other | 4 |
| **Apartment Building, Single Family Rental Portfolio** | 3 |
| **Apartment Building, Duplex/Triplex/Quadruplex, Apartment/Condo, Fourplex** | 3 |
| **Single Family Rental Portfolio, Apartment Building** | 2 |
| **Single Family Rental Portfolio, RV Park, Apartment Building** | 2 |
| **Student Housing, Apartment Building** | 1 |
| **vacation rental** | 1 |
| Apartment Building, Duplex/triplex/quadruplex, Townhome | 1 |

**43 of 250 (17.2%) are out of scope for a 2–4-unit buy-box** (bold above).
We are storing SFR portfolios, an RV park, student housing and a vacation rental in a
2–4-unit multifamily ingest.

**Two caveats that keep this honest.**

*(a) A sub-type rule cannot save a single request.* Sub-type lives in the DETAIL
document (`summaryDetails` → `SubType`), not in the `/assets/search` feed — so the value
only arrives **after** the 3-call fetch a sub-type filter would be trying to prevent. It
can stop storage and downstream value-route work, nothing more. **Type policy is the
only lever on the fetch bill.** For the same reason this census cannot be projected onto
the 3,496.

*(b) This sample is biased by construction*, so it says nothing about what admitting
compounds would bring in: every asset in it already passed the exact-match gate. A
separate bounded 45-asset fetch of COMPOUND listings — the only sub-type data that has
ever existed for them — is reported apart in `runs/coverage_report_FL.txt` §2. In that
(tiny, non-random) sample 14 of 42 are flagged out of scope, and the units split is
20 NULL / 17 five-plus / 5 in-band / 3 single-unit.

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

## 6. How much to trust the result set — SETTLED 2026-08-28

**The scope is 3,496 FL multifamily listings. The sweep reaches 1,962 of them (56.1%).**
That was F-B14, filed as suspected; it is now confirmed by direct enumeration and the
mechanism is known. Full write-up in `FINDINGS.md`; the readable report is
`runs/coverage_report_FL.txt`.

**`total_count` is honest.** A price-band partitioning of the identical scope enumerated
**3,496 distinct ids**, matching the reported `total_count` exactly, in 14 bands with no
truncation. The county-partition union is a *strict subset* of it. The pre-registered
falsifier — "the whole-state count is inflated" — was tested and did not fire.

**Why the county filter loses 43.9%.** `counties` is a **case-insensitive but otherwise
literal string match** on the county value stored on the record — not a geo lookup, not
normalized. Probed live:

| filter value | `totalCount` |
|---|---|
| `"Duval County"` | 25 |
| `"Duval"` / `"DUVAL"` / `"duval"` | 107 |
| `"St. Lucie County"` | 10 |
| `"St Lucie County"` | 25 |
| `"Volusia County"` / `"Volusia"` | 51 / 98 |
| `"Belize"` | 4 |

Our `counties` values come from a committed **Census gazetteer**, which supplies exactly
one canonical form (`"X County"`). That is the wrong key for every record Crexi stored
any other way. Worse: **939 of the 3,496 carry no county string at all**, so no county
key of any spelling reaches them.

> County partitioning cannot cover this scope, and no longer county list fixes it.
> Price bisection already covers it — 3,496/3,496, using the product's own
> `_price_bisect`, unmodified, in 77 requests.

**The pagination caps are not the cause**, and one of them is misdocumented. The server
enforces **`offset < 1500`**, not the `offset + count < 1500` its own 400 message (and
`assets_search.py:14-16`) claims — `offset=1499, count=1` succeeds. `SAFE_WINDOW = 1400`
is only ever compared against `total_count` to decide *whether* to partition; it never
truncates a sweep in progress. Delisting is excluded too: all 1,534 missed listings are
`On-Market`.

**Read every baseline rate against 3,496, not 1,962.** The type gate is 40.2% of scope,
not 71.7% of swept; strict 2-4u matches are 2.6% of scope, not 4.6%.

## Recommendations (recommendations, not actions)

1. ~~**Settle F-B14 first**~~ — **DONE 2026-08-28** (§6). The naive form of that probe
   would have lied: a whole-state paged sweep truncates at 1,499 by our own arithmetic
   (`assets_search.py:180-182`), so "far fewer than 3,496 came back" is guaranteed
   before the first call. The replacement for county partitioning is **price-band
   partitioning**, and it is the recommended first change: no operator decision needed,
   already proven on this scope, worth +1,003 admitted listings under today's unchanged
   type gate.
2. **Decide the targeting question explicitly** — it is an operator call, not a
   code fix: is `"Office, Multifamily"` a deal? Is a `Single Family Rental
   Portfolio`? An `RV Park`? Today the answer is implicit in an exact-match
   string test and inconsistent between two code paths.
3. **`property_sub_type` is the lever** for "don't store what we don't want" —
   already captured, already stored, never used.
4. **A do-not-refetch marker** is the lever for "don't waste time re-ingesting."
   None exists; the freshness check cannot express "known uninteresting."
