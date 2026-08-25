# Ingestion State — Code Survey + Live Prod Verification (2026-08-25)

> Survey of the ingestion half against `main @ ea05e9e4`, with prod probes run
> 2026-08-25. Scoped to the lead-sale pivot: ingestion coverage and freshness
> are now product supply.

## ⚠ HEADLINE: ingestion is silently dead in 6 of 8 markets

**Over the last 3 days, 6 of 8 markets ingested zero listings across 82 runs
each — every run stamped `succeeded`.**

| Market | Runs | Listings ingested |
|---|---|---|
| Holland MI · Muskegon MI · Tampa FL · Gainesville FL · Jacksonville FL | 82 each | **0** |
| Lansing MI | 82 ok + 29 failed | **0** |
| Grand Rapids MI | — | 224 |
| Detroit MI | — | 41,283 rows, but only **27 new** listings |

**Why nothing alerted — three compounding causes:**

1. Those 6 markets write **no `source_health` rows at all**; 3 days of
   `source_health` contains only Detroit and Grand Rapids. The volume and
   completeness detectors have nothing to compare against and **structurally
   cannot fire**.
2. `is_volume_anomaly` (`observability/source_health.py:114`) returns False
   when the trailing median is below `source_volume_min_baseline=20` — a
   market pinned at 0 forever is never flagged.
3. `coverage_ratio` is NULL on every prod row: the Redfin `gis` JSON
   denominator is WAF-403'd from the runner (`providers/scraping/redfin.py:1687`),
   so the absolute-coverage metric is dead in production.

**Related live signals:** `data-discovery` has **0 successes in its last 1000
runs** (back to 2026-08-09), killed at the 25-minute cap; new alerts are
suppressed because one open issue per workflow already exists (**#1463, open
since 2026-07-18**). The live-shape canary is red on 6 consecutive runs with
proven drift (`[DRIFT] bsa: empty sales page`, `[DRIFT] kent_parcels:
geometry coverage 0%`). `kent_opendata` returned 0 across 35 runs while Redfin
returned 245 for the same market.

**Known cause for one market:** `Gainesville FL` is in `_MARKET_RUNS`
(`scripts/cloud_nightly.py:361`) but absent from `_REDFIN_REGIONS`
(`redfin.py:84-103`), so it falls back to a text `location=` param the code
itself annotates as *"unknown market → best-effort text location (likely 400 →
degrades to empty)"* (`:1644`). Inverse gap: Miami has a region id but is not
in the matrix.

## Sources

Composition root for cron is the per-market builder table `_MARKET_RUNS`
(`cloud_nightly.py:338`, 8 markets), **not** `provider_from_settings`. All
sources fan through `MultiSourceProvider` (`providers/registry.py:507`), merged
per-field by confidence (`:416-445`: manual 1.0 · rentcast/crexi/composite 0.90
· opendata 0.88 · cis 0.70 · realtor 0.62 · zillow 0.60 · **redfin 0.58**).

| Source | Adapter | Provides | Cost | Trigger |
|---|---|---|---|---|
| Redfin gis-csv | `redfin.py:1716/:1754` | 19 CSV cols; **no APN, no description, no photos, no list date** (`listed_at` derived `today−DOM`, `:334`) | free | every cron |
| Redfin detail | `redfin.py:1896/:488/:951` | listing agent, photos, remarks | free | enrichment only |
| Crexi API | `providers/crexi/` | MF for-sale + brokers/phones + prose + subject record (owner, mortgage amt/rate/lender, tax, equity, FEMA, 4 histories) | **paid flat sub** | 6h cron |
| Detroit OpenData | `opendata/detroit.py:528` | DLBA listings, parcel/assessment, assessor comps | free | source+enrich |
| County ArcGIS/BS&A | `opendata/county.py:288`, `kent.py:160`, `scraping/bsa.py`, `eagleweb.py`, `tyler_selfservice.py` | parcels, owner+mailing, assessed, deed comps | free | enrich |
| FL DOR cadastral | `opendata/florida_dor.py:119` | statewide parcel; **JV used as ARV** | free | mirror sweep |
| Off-market mirror | `scripts/offmarket_sweep.py:116` | county in-band parcels + owner/mailing | free | Mon 08:17Z |
| Crime / FMR rent | `opendata/crime.py`, `rent/fmr.py:179` | crime rating, HUD FMR ceiling | free | enrich |
| Zillow/Realtor/RentCast/BatchData | — | — | — | **dormant** (`scraper_enabled_sources=()`, keys None) |

## Schedules (all ingest on `RUNNER_SCRAPE || self-hosted`)

| Workflow | Cron UTC | Notes |
|---|---|---|
| `data-discovery.yml:17` | `*/15` | sourcing only; 25-min cap; **0 successes in 1000 runs** |
| `data-enrich.yml:22` | `5,20,35,50 * * * *` | `ENRICH_MAX_PER_RUN=15`, `REINGEST_MAX_PER_RUN=25` |
| `data-finalize.yml:24` | `0 7 * * *` | 10 finalize steps + dedup sweep |
| **`cloud-nightly.yml:16`** | **`*/5`** | header says "SUPERSEDED … kept disabled" — **the schedule is live**, separate concurrency group, so it runs *concurrently* with discovery+enrich as a 4th property writer (the INC-001 contention pattern) |
| `crexi-ingest.yml:51` | `41 1,7,13,19` | `cron-mini`; **no states in profile ⇒ exits 0 no-op** |
| `crexi-harvest.yml:45` | `23 9 * * 2` | |
| `offmarket-sweep.yml:29` | `17 8 * * 1` | mirror-only; promoters default 0 |
| `canary.yml:14` | 3×/wk | **exit 2 (blocked) coerced to green** (`:56`) |
| `cloud-refresh-matrix.yml` | none | dormant |

**Never scheduled anywhere:** `fleet_health_canary.py`,
`market_coverage_audit.py`, `audit_data_integrity.py`, `audit_ground_truth.py`.

## Identity and dedup

`resolve_canonical_property` (`persistence/repositories.py:750`), first match
wins: `LIVE_SELF` → `ALIAS` (16 hops, cycle-safe) → `MLS` (state-namespaced) →
`PARCEL` (+ veto) → `ADDR` (`addr:street|unit|city|state|zip5`) →
`ADDR_ZIPLESS` → `FUZZY` (difflib ≥0.88, house-no+ZIP+unit exact, audited to
`property_merge_audit`) → `NEW`. Vetoes (`registry.py:1875`): year_built ±30,
sqft ratio 0.5, beds Δ3.

DB backstop: materialized `property.norm_address_key` + partial UNIQUE
(migration `0051`) — **computed only in `mappers.property_values:99`; the
manual upsert path leaves it NULL.**

Open dedup defects: **no UNIQUE on `property.parcel_id`** (DL-139, issue #190);
`parcel:` and `addr:` key types never union; agent identity forks between
`<email>||` and `<name>||` ids (cleanup shipped, prevention did not).

## Persistence and conflict rules

`upsert_property` (`repositories.py:345`) gates each structural column against
`field_sources` via `fact_policy.effective_confidence` — a strictly-lower
confidence write is **skipped**; accepted changes append a
`field_provenance_event`. `upsert_listing` (`:1429`) refuses (a) an older
`listed_at` regressing price/status, (b) a weaker source overwriting
`list_price`. **`last_seen_at` is stamped only for on-market rows**
(`sourcing.py:611`) — the freshness column the lead funnel depends on.

## Freshness and lifecycle

TTLs (`services/lifecycle_classify.py:109`): LISTING **7d** · VALUATION 14 ·
OWNER 180 · AGENT_CONTACT 90 · MORTGAGE 180 · CONDITION 45.
Freshness ages off `_listing_observed_at` = MAX(`last_seen_at`, `updated_at`,
`listed_at`) since commit `98be3243`. Delist: on-market unseen >48h →
`feed_dropout`, **suppressed whenever a volume anomaly fired** so a block can't
mass-delist. Crexi is excluded from delist (swept `sort=updatedOn`) and
reconciled by a single-asset liveness probe instead.
Tiered re-source (`orchestration/refresh_tiers.py:70`): HOT 1h / WARM 24h /
COLD 168h.

## AI in the ingestion path

1. **Listing income extract** (`services/listing_income.py:138`) — route
   `EXTRACT: (CODEX, CLAUDE_SDK, GENSERVER)`, i.e. codex `gpt-5.6-terra` /
   claude_sdk `claude-opus-4-8`. Parses Crexi `marketing_description` prose →
   `valuation.rent_*`. **The only lane with no feature flag and no budget** —
   deliberately *free-transport-only* so it cannot bill (`routes.py:29-34`).
   Output re-validated against source text (digit-appearance
   anti-hallucination), confidence capped 0.8, 3 deterministic fallback tiers.
2. **Condition vision** (`vision/condition_vision.py:100`) — `grok-4.3` @
   `api.x.ai/v1`. Code defaults `vision_enabled=False`, **but the cron
   overrides**: `cloud_nightly.py:777-788` sets `vision_enabled = bool(VISION_API_KEY
   or XAI_API_KEY)` and the secret is wired into four workflows. **Adding the
   repo secret *is* the switch.** Falls back to a text heuristic on failure.
3. **Condition-analysis queue** — `google/gemini-3.1-flash-lite-preview`,
   `grid_512_3x3`, $5 cap; dispatch-only; no deterministic fallback.
4. **Deep-dive research** — Agent SDK `claude-opus-4-8`, flag off, ~$8/run.

**No HOA enrichment exists at all** — captured only at ingest from Redfin's
`HOA/MONTH`; `hoa_eligible` is never set True anywhere, so the routing HOA
guard (`workers/routing.py:411`) is **dead code**. Prod HOA coverage: 178
properties (0.8%).

## Data-quality controls that exist

Ingest bounds (`providers/normalization.py:225`): `PRICE_MIN=1000`, sqft
100..1e6, year 1700..2100; out-of-envelope values are nulled, not stored.
Anomaly detectors wired after sourcing: volume, completeness drift, coverage
ratio, dead source, dedup canary, delist spike, essential-coverage-loss.
Migration drift checked at run start but `abort_on_drift=False` — **warns and
continues**. 363 test files including `test_durable_identity.py` (25 cases),
`test_source_health.py` (44).

Corpus audits exist and are **all unscheduled**: `data_integrity.py`,
`ground_truth.py` (**seed is empty**), `market_coverage_audit.py`,
`fleet_health_canary.py`.

## Prod book snapshot (2026-08-25)

22,026 properties / 5,074 un-archived; 1,696 enriched in 7d. Parcel 79% ·
geo 94% · condition 66% · sqft 33% · year_built 36% · **HOA 0.8%**.
Listings 24,765: opendata 15,853 (only 24 on-market — parcel-mined) · crexi
4,264 (3,741 on-market, 1,423 seen in 48h) · redfin 3,515 (1,497 on-market all
seen in 48h, 2,007 `feed_dropout`) · rentcast 1,128 (all dropped).
`listing_agent_id` on 6,413/24,765 — MI redfin **1,026/3,515** vs crexi
**4,264/4,264**, the WAF gap in one number.

## Other open failure modes

- **INC-001 lock contention, ingest half still open**: discovery/enrich/crexi
  bulk-UPDATE `property`; prod role has `lock_timeout=0`,
  `statement_timeout=2min`, so a contended UPDATE waits 2 min then
  `QueryCanceled` and rolls back the drain. Fix is mid-stage batched commits;
  `commit_chunk_size=0` and no workflow sets it.
- **Schema drift on release**: Actions schedules run from the default branch,
  so merging a release runs new code against the old prod schema within
  minutes (proved 2026-08-13: `UndefinedColumn: property.roof_age_years`
  across every market). Two-Alembic-heads collisions have occurred 4×.
- Tyler parser anchored to an exact HTML entity (silent `[]`); BS&A pagination
  treats a swallowed error as end-of-results; ArcGIS raises immediately on 429;
  `record_provider_call` has **zero call sites**, so the digest reports
  "Provider err rate: 0.0%" as measured truth.
- **No raw payload retention for Redfin** — only offmarket parcels and Crexi
  keep source bytes, so a parser regression cannot be replayed.
- `Docs/DATA_LEAK_AUDIT.md`: 173 confirmed findings (26 critical / 52 high)
  with **no per-finding status column** — `✓` means verified, not fixed.
