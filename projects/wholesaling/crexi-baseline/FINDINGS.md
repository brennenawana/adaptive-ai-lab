# Crexi Baseline — Findings

Append-only. Each finding carries the evidence chain that produced it.

---

## F-B1 · The anti-mirage guard silently destroys correct LLM extractions

**Severity: high — decision-flipping, silent, and indistinguishable from the LLM being off.**

Found on the **first property examined**, via a one-at-a-time loop (operator's
method) rather than a batch. Classification: **RC-7, in-system verification gap**
(the system's own verifier rejects a good output).

### The property

`asset_id=2660435` — 1821 NE 26th Ave, Fort Lauderdale FL. 3 units, ask
**$7,900,000**, built 2026, 11,050 sqft. The marketing description states its own
income:

> "6% Cap Rate. Three luxury 4BR + den townhomes … the units now generate
> **$552,000 in combined** [annual rent]"

$552,000/yr = **$46,000/mo**.

### What each arm produced — identical output, opposite causes

| Arm | `_try_llm_extract` | `_validate_facts` | final |
|---|---|---|---|
| **A** (LLM off) | `None` | not reached | `market_median` **$5,382/mo** conf 0.3 |
| **B** (LLM on) | **`gross=46000.0, confidence=0.6`** ✅ correct | **`accepted: false`** ❌ | `market_median` **$5,382/mo** conf 0.3 |

**The LLM read the listing correctly and got the exact stated figure.** The
validator then threw it away.

### Why it was rejected

`app/services/listing_income.py:171-172`

```python
per_unit_hi = (units or 4) * _MAX_UNIT_RENT   # 3 * 15_000 = 45_000
if not (_MIN_UNIT_RENT <= gross <= per_unit_hi):
    return None                                # 46_000 > 45_000  -> REJECT
```

Rejected by **$1,000 on a $45,000 ceiling — 2.2% over**.

`_MAX_UNIT_RENT = 15_000` (`:54`) exists, per the docstring, to catch "a $68,400
'gross' that is really annual." It does that. It also rejects genuine luxury
multifamily, and the Crexi FL book is full of it.

### Why it matters — the error flips the verdict

| basis | price ÷ annual rent | gate sanity bound (`>40` = REJECT) |
|---|---|---|
| stated $552k/yr | **14.3×** | passes — a plausible asset |
| system $5,382/mo | **122.3×** | absurd |

The 8.5× understatement moves the asset from "worth underwriting" to
"nonsensical." It never surfaces as a rejection only because
`MF_REVIEW_HOLD_REASON` fires first (`deal_type=NONE`, so there is no offer for
the sanity bound to test) — the wrong number is simply carried forward as the
listing's rent.

### Why nobody would notice

Nothing records that a correct extraction was discarded. `IncomeSignal` keeps
only the winning tier; `_validate_facts` returns `None` and the reason is
computed and thrown away in the same expression. Arm A and Arm B are
**byte-identical in output** — so from outside, a working LLM whose answer is
being destroyed looks exactly like a disabled LLM.

This is why the tier decision needs persisting (the survey's telemetry gap): it
is not an observability nicety, it is the difference between "the LLM doesn't
help" and "the LLM helps and we throw it away."

### Evidence

Reproduce with `rig/run.sh income_probe2.py 2660435` under each arm; the probe
wraps `_try_llm_extract` / `_validate_facts` without touching product code.

### Not yet known

- **Materiality**: how many listings hit this band. n=1 proves existence, not rate.
- Whether a raised/derived ceiling reintroduces the annual-as-monthly mirages the
  band was built to stop. The anti-hallucination digit check (`:180-188`) already
  provides independent protection, so the band may be over-determined — but that
  is a hypothesis to test, not a fix to ship.

---

## F-B2 · `comp_set` is NULL on every valuation — the ARV is unauditable

**Severity: high for a lead product.** `arv_source` advertises the comp count
(`comps:crexi:n=114`, `n=50`, `n=29`) while `valuation.comp_set` is **NULL on
all four valuations produced**. The number a buyer would pay for cannot be
traced to the comparables that produced it.

```
 address                     | arv        | arv_source                    | comp_set
 1352 Holly Heights Dr       | 1176343.4  | comps:crexi:n=114;...         | NULL
 305 SE 12th Ave             | 1090369.56 | comps:crexi:n=29;...          | NULL
 1602 S 17th Avenue # 3 #1-3 | 821790.14  | comps:crexi:n=50;...          | NULL
```

Correcting my own first read: the ARV **is** genuinely comp-derived — the counts
are real and the values are not anchored to the ask. The defect is provenance,
not fabrication. But "which comps?" is the first question a lead buyer asks, and
today the answer is not stored.

**Sharpened by the trace harness (2026-08-27):** the in-memory `Valuation`
object *does* carry the comp set — 61 comps for asset 2659977, 41 for 2659939 —
while the corresponding `valuation.comp_set` rows are NULL. So the evidence is
computed and then **dropped at persist time**. This is a write-path defect, not a
missing computation, which makes it a cheap fix: persist what the object already
holds.

---

## F-B3 · ARV confidence clusters at or below its own credibility floor

Of the three valuations that produced an ARV:

| property | arv_confidence | vs the 0.35 floor |
|---|---|---|
| 1352 Holly Heights Dr | 0.303 | **below** → `hold:arv_low_confidence` |
| 1602 S 17th Avenue | 0.331 | **below** → `hold:arv_low_confidence` |
| 305 SE 12th Ave | 0.362 | barely above |

Two of three ARVs are **structurally unable to price a cash deal** — they are
computed, stored, and displayed, but sit under the threshold the router requires
to trust them. The fourth property produced no ARV at all despite 110 comps
fetched (cause not yet diagnosed).

n=3. This corroborates the mechanics survey's note that FL cash structures rest
on ARVs below the floor; it does not yet establish a rate.

---

## F-B4 · The anti-hallucination check cannot read `$400k` notation

**Severity: high — silently discards correct extractions. Measured at 6% of
descriptions, all of them income-bearing.**

`_numbers_in` (`listing_income.py:752-760`) collects integers with
`\$?\s?([0-9][0-9,]{2,})(?:\.[0-9]{2})?` — **no handling for a K/M suffix**. So
`"$400k"` yields `400`, never `400000`; `_appears(400000, …)` is False, and the
extraction is rejected as a possible hallucination.

Two confirmed cases, both correct extractions destroyed:

| asset | description says | LLM extracted | why rejected |
|---|---|---|---|
| 1775854 | *"produced over **$400k** in rentals a year"* | $33,333.33/mo (= 400,000 ÷ 12) ✅ | `400000` not in `_numbers_in` |
| 1817625 | *"ANNUAL NET GROSS INCOME **$103K**"* | $8,583.33/mo (= 103,000 ÷ 12) ✅ | `103000` not in `_numbers_in` |

Measured over the 97 stored descriptions: **6 (6%) use `$NNNk`/`$NNNM` money
notation, and all 6 also mention income/rent.** In every one, the full value
fails to reach `_numbers_in()`:

```
asset 2583640  $4.57M -> 4,570,000   in _numbers_in? False
asset 1775854  $400k  ->   400,000   in _numbers_in? False
asset 1883740  $80K   ->    80,000   in _numbers_in? False
asset 1928826  $15K   ->    15,000   in _numbers_in? False
asset 2655164  $130K  ->   130,000   in _numbers_in? False
asset 1817625  $103K  ->   103,000   in _numbers_in? False
```

The `gross * 12` fallback (`:186-187`) exists precisely for annual figures and
would have accepted both — it fails only because the *text* side of the
comparison never parsed the abbreviation.

### Measured on n=40 (sweep complete)

| | count | of what |
|---|---|---|
| listings swept (Arm B, all with descriptions) | 40 | |
| LLM extracted an actual number | **8** | 20% of listings |
| → validator **accepted** | 6 | 75% of extractions |
| → validator **rejected** | **2** | **25% of extractions** |
| correctly rejected (`gross=None`, no income stated) | 32 | working as designed |
| rejections caused by the band (F-B1) | **0** | F-B1 did not recur in 40 |

**Both wrongful kills in the sample are F-B4 (K/M notation)** — assets 1775854
and 1817625. So the honest materiality statement is: **F-B4 discards roughly a
quarter of every income figure the LLM successfully finds**, and it is the
dominant validator defect. F-B1 is real but rarer — it did not appear once in 40.

(Both wrongful-kill assets have `units=None`, so their band ceiling was
`4 × 15,000 = 60,000` and neither gross came near it — independently confirming
the K/M parse, not the band, is the cause.)

**Tier distribution (the telemetry that does not exist in prod):**

| tier | n | share |
|---|---|---|
| `market_median` (tier 4 fallback) | 21 | **52%** |
| `none` (no signal at all) | 13 | 32% |
| `llm_extract` (tier 1) | 6 | 15% |

Over half the book is priced off a coarse market median — the exact pattern the
MF income-ladder work was built to eliminate. Fixing F-B4 moves cases from the
52% bucket into tier 1.

**Latency:** median **7.6s** per listing for income resolution alone (max 14.8s),
all of it the LLM call. Over FL's 1,511 type-matched listings that is ~3.2 hours
of income extraction on top of comp fetching.

### Correction to an earlier overstatement

I first reported "the validator rejected 11 of 15 (73%)" as alarming. That was
wrong: **11 of those 13 rejections had `gross=None, conf=0.0`** — the LLM
correctly reporting that the description states no income, which the validator
is right to reject. The honest figure is that of the extractions carrying an
actual number, a small minority are wrongly killed — by F-B4 (6% of
descriptions) and F-B1 (rarer). The validator is mostly working.

---

## Cross-cutting observation: throughput

Four listings took ~7 minutes of wall clock, dominated by comp fetching at
`crexi_requests_per_second = 2.0` (110, 87, and 206 cumulative new comps). At
that rate a full pass over FL's 1,511 type-matched listings is on the order of
**12–40 hours**. Relevant to any plan that treats a full re-pass as routine.


---

## F-B8 · One unmapped field suppresses every Crexi ARV below its own usability floor

**Severity: highest of the session. 100% of Crexi ARVs affected; moves 58% of the
book from usable to unusable, and separately disables a comp-exclusion rule.**

### The chain

1. Crexi normalization populates `sale_event_name` from the payload's `eventName`
   (`providers/crexi/normalize.py:105`). It is present on **846/846** comps:
   `Sold` (828) and **`Sold: Multi APN Sale` (18)** — the latter is precisely a
   multi-parcel *package* sale.
2. The engine's provenance check reads a **different field**:
   `_comp_set_has_sale_type_provenance` (`valuation/engine.py:331-339`) tests
   `comp.exclusion_reason`, which the Crexi path never sets.
3. It therefore returns False on every Crexi comp set, and
   `engine.py:170-172` applies `confidence x 0.55` plus the
   `;no_flip_package_signal` note.

**Measured on the 25-listing walk: 24/24 ARVs (100%) carry the haircut.**

### Effect 1 — ARV confidence is suppressed below the floor it is judged against

| | below the 0.35 credibility floor | confidence range |
|---|---|---|
| observed (post-haircut) | **18/24 (75%)** | 0.167 – 0.391 |
| implied (pre-haircut) | 4/24 (17%) | 0.304 – 0.711 |

The haircut alone moves **14 of 24 valuations (58%)** from usable to unusable.
Note the observed maximum, **0.391**: nothing in the sample clears the floor by
any margin, because the ceiling itself has been multiplied down.

This is why F-B3 looked like a distribution problem. It is not — it is one
constant.

### Effect 2 — the package-deal exclusion cannot fire at all

The same unmapped field means the engine's step-6 exclusion for package sales
never sees Crexi's `Sold: Multi APN Sale` comps. Per the engine's own comment,
that means "a market-priced retail flip would be admitted, inflating ARV."
**18 of 846 comps (2%)** are labelled package sales in the source data and are
currently admitted as ordinary comparables.

So the two effects push in opposite directions: confidence is suppressed while
the value itself may be inflated.

### Why this is a mapping gap, not a bug in the haircut

The haircut is **correct behavior given a False answer** — without sale-type
provenance you genuinely cannot exclude retail flips or package deals, and less
confidence is the right response. The comment at `engine.py:160-168` says it was
written for "RentCast, West-MI county" payloads that carry no such field.

The defect is that for the Crexi lane the signal **does exist** and is simply not
mapped onto the field the engine reads — so a value designed to *vary* has become
a *constant*, and the 0.35 floor was never re-derived for a lane where the
penalty always fires.

### What this does NOT license

Mapping `sale_event_name` → the provenance field would raise ARV confidence
across the entire book and change which deals can price. That is an underwriting
change, not a bug fix, and it needs the operator's judgment plus a
before/after measurement — not a quiet patch. The honest statement is: **the
current ARV confidence for Crexi is not measuring comp quality, it is mostly
measuring one missing mapping.**

---

## F-B9 · The blocker is RENT CONFIDENCE, not rehab — and the raw material is already ingested

Adversarial verification (3 independent lenses, all code+prod grounded) of the
proposal *"seed a rehab estimate so routing can price a deal and the gate becomes
reachable."*

### Verdict: don't seed rehab — but not for the reason I first gave

**Seeding rehab is INERT, not merely unwise.** `estimated_rehab` is read at
exactly one general site, `router.py:428`, nested under the DISTRESSED guard at
`router.py:422`. Turnkey terms never carry it (`_build_type1_turnkey_terms`,
`router.py:260-298`) and `type1_turnkey_offer` takes **no rehab parameter at
all** (`underwriting/engine.py:283-292`). Crexi properties have NULL
`condition_tier`, so routing synthesizes UNKNOWN (`workers/routing.py:275-281`),
UNKNOWN is not DISTRESSED, and `router.py:1389/1395` sends every one down the
turnkey **rent/CoC** path.

Prod: **4,116 of 4,193** Crexi properties have `condition_tier` NULL; only **5**
are distressed and **2** of those MF-held. A rehab seed is load-bearing for
**0.05%** of the book and cannot change `deal_type` on a single held card.

### I was wrong: the gate is NOT unreachable by design

I hypothesized `MF_REVIEW_HOLD` was terminal by design. **Refuted on three
independent lines:**

1. `guardrails/gate.py` contains no `property_type` / `MULTIFAMILY` check;
   `guardrail.py:56-57` filters on `deal_type is NONE`, not property type;
   `underwriting/engine.py:321-328` says `is_single_family` "no longer selects a
   price ceiling (§5.13)" — small MF and SFH share one solver.
2. **Prod: 123 Crexi deals are at `deal_type='cash'`** (122 held at the gate, 1
   called), with ordinary gate verdicts — "Kill switch engaged" (72), "no
   validated listing-agent email" (47). The gate demonstrably runs on this book.
3. The "MF underwriting is a parked operator decision" comment
   (`crexi_value_route.py:102-111`) was **retracted by the repo one day later**
   in commit `ddd9794d`: *"The ~850 held MF cards exist because rent never
   reaches the router"* — and `listing_income.py` was built to fix precisely
   that. Only the stale `Docs/PAID_API_DECISIONS.md:427-431` still says "parked."

**I reasoned from a stale comment the codebase had already superseded.** This is
the exact failure mode this project catalogues (`feedback-code-is-authority`):
docs lag reality; verify against code.

### "The gate never runs" is a tautology, not a finding

Given `guardrail.py:56-57`, "the gate never runs" ≡ "`deal_type is NONE`" ≡ "the
router could not price it." It carries no information beyond the input failure,
and it misdirects attention at the guardrail subsystem, which is behaving as
designed. Note the ordering: `_hold_for_mf_review` is called in the **elif** of
`if res.qualified` (`crexi_value_route.py:542-547`) — the MF hold is the residual
branch for a deal the router already declined to price, **not** something applied
instead of the gate.

### The correct finding

| rent_source | n | avg conf | outcome |
|---|---|---|---|
| `crexi:rental_market` (tier 4) | 3,350 | **0.30** | **0 clear the floor** |
| `crexi:marketing_desc:regex` (tier 2) | 617 | 0.59 | 125 reached CASH |
| `crexi:marketing_desc:llm` (tier 1) | **0** | — | **never produced a row in prod** |

`type1.min_rent_confidence` = **0.35** (`parameters.py:799-812`). So **3,286
cards die at `router.py:512-519`** with `non_offerable:basis_unverified` because
0.30 < 0.35.

**Of those 3,286: 3,045 (93%) already carry a marketing_description ≥200 chars,
2,746 (84%) already carry ≥3 photos, 3,227 (98%) have NULL condition.** The raw
material to lift rent above the floor is **already in the database and has never
been read.**

### Why this is squarely an ingestion-quality question

Tier 1 has produced **zero rows in production**. The defects already found in
this workstream — **F-B4** (`_numbers_in` cannot parse `$400k`, discarding ~25%
of successful extractions) and **F-B1** (the per-unit band) — are defects in the
exact tier that would rescue those 3,286 cards. Fixing extraction accuracy is
the lever; seeding rehab is not.

Secondary: 122 of the 123 cards that *do* price are held on `condition_tier IS
NULL` (`guardrails/apply.py:195-201`). Condition is the second gate — also an
unread-input problem (98% of the dead cards have photos), not a rehab problem.

### Correction to my own prong (b)

I said seeding rehab "fabricates an unmeasured input," full stop. **Overstated.**
The repo ships a *sanctioned* rehab model (`valuation/engine.py:748-775`) with
provenance, confidence capped to the condition signal, and a named hold — and
runs it on the non-Crexi lane via `_refresh_rehab` (`recompute.py:167-174`). A
*derived, labeled, low-confidence* rehab is doctrinally permissible; a hand-typed
unblocking number is not (`property_edit.py:138-141` rejects those outright).
The estimator simply has nothing to run on here: it returns early when
`condition_signal is None` (`recompute.py:161-166`), which is 4,116/4,193 rows.

---

# Ingest-lane findings (2026-08-27)

First instrumented pass over the ingest half. Evidence for every number below is
`runs/ingest_trace_FL_record.jsonl` (1,962 per-asset records, funnel fingerprint
`3c15972614b09973`, reproduced identically three times) and its rendered report
`runs/ingest_funnel_FL.txt`. All ten derived populations reconcile exactly against
`IngestStats`; a mismatch would have exited 1 rather than printed a table.

Scope of the sample: steps 1–6 are measured over **all 1,962 swept assets**; steps
7–11 over the **newest-updated 150** the `--max-fetch` cap admitted.

---

## F-B14 · A partitioned full sweep reaches 56% of its own scope, and no counter says so

**Severity: high — silent under-collection at the very top of the funnel.**

`backfill_partitions` splits a too-big state into one scope per county. Measured on FL:

| probe | listings |
|---|---|
| whole-state scope (`count=1`, identical filters) | **3,496** |
| sum over all 67 county partitions | **1,965** (56.2%) |
| unreachable through any partition | **1,531** (43.8%) |

**It is not a missing-county-name bug.** The 11 counties probing zero are all small
rural ones (Calhoun, Dixie, Gadsden, Hamilton, Holmes, Jefferson, Lafayette, Liberty,
Union, Wakulla, Washington). And every one of the 56 non-zero partitions swept
*exactly* its probe count — 0 truncated, 0 short. The partitioner is internally
consistent. Its union is simply not the scope.

**Corroborated per-asset.** Of the 100 listings this rig had already ingested from
this exact scope, 89 came back and **11 did not appear in any partition** — all
`status=Active`, all Broward County, a partition that probed 446 and returned all 446.

**Why no counter shows it.** `backfill_partitions` warns only when a single county
exceeds `SAFE_WINDOW` or a state has no county reference — neither fired. And
`crexi_ingest.py:298-299` sets `stats.total_in_scope` only when `len(scopes) == 1`, so it is
`None` *exactly when partitioning happened*, i.e. exactly when the gap exists. The
aggregate cannot display the discrepancy that two probe families make obvious.

**Not diagnosed** (needs a live probe; deliberately out of scope for the baseline):
whether the cause is Crexi's county index differing from the payload county, or
genuine delisting since the earlier pass. The filter-leak evidence in F-B16 favours
the former.

---

## F-B15 · The type gate exact-matches a JOINED compound type string

**Severity: high — 28.3% of the sweep dropped before any detail fetch.**

`ListingFilters.stub_type_ok` is `(stub_type or "").strip().lower() in self.property_types`
— set membership against `("multifamily",)`. But `AssetStub.type_str` is
`", ".join(item.get("types") or [])` (`assets_search.py:249`), a *compound* string.

Measured: **555 of 1,962 swept assets (28.3%) died at the type gate, and 555 of those
555 (100%) carry `Multifamily` inside a compound type string.** Top forms:

```
 93  Land, Multifamily          20  Multifamily, Mixed Use, Land
 55  Multifamily, Land          17  Retail, Multifamily
 27  Office, Multifamily        16  Multifamily, Hospitality
```
137 distinct compound strings in total.

The `ScrapeConfig` field documents itself as *"Property-type **substrings** to keep"*
(`scrape_config.py:73-76`); the implementation is exact set membership. The
documented contract and the code disagree, and the disagreement is worth 28% of the
sweep.

**This is not automatically a bug to fix.** `"Land, Multifamily"` is plausibly a land
listing with MF zoning, which nobody wants. `"Office, Multifamily"` mixed-use might
be. **Whether these should be kept is an underwriting call, not a code call** — what
is a code fact is that the decision is currently being made by string equality
against a join, not by anyone's intent.

---

## F-B10 · Unit counts stated only in prose → `units` NULL → disqualified downstream

**Severity: high — and the raw material is already stored.**

Of the 150 fetched + normalized listings:

| units | n | % |
|---|---|---|
| mapped from `summaryDetails["Units"]` | 114 | 76.0% |
| **stated in the name/description only** | **30** | **20.0%** |
| absent from the payload entirely | 6 | 4.0% |
| parse failure (`_as_int` could not read a present Units row) | 0 | 0% |

`normalize_listing:70` reads `units` from exactly one place: `_as_int(summary.get("Units"))`.
When Crexi omits that summary row, the count is lost — even though the description says
it outright. Of the 30, **23 (15.3% of the sample) state an in-band 2–4 count**
("duplex", "fourplex", "4-unit"); the other 7 state an out-of-band count and would stay
non-strict either way.

Spot-checked 10/10 against the stored description: every match is a subject-property
claim, not a reference to a neighbouring building —
*"Exceptional income-producing duplex located in…"*, *"This well-maintained duplex
offers two 1-bedroom, 1-bathroom units"*, *"income-producing fourplex… features 4 units"*.

**Blast radius.** Strict matches would move **90/150 (60.0%) → 113/150 (75.3%)**.

**Correction to the GOAL's framing of step 9.** The GOAL lists the strict unit-band
filter as an ingest DROP with "unknown units DROPPED". **It is not a drop at ingest.**
`crexi_ingest.py:386-389` computes `strict` and uses it for exactly two things: the
`strict_matches` counter and whether to mirror photos. The row is appended to `rows`
and upserted regardless — the module docstring says so outright. Non-strict listings
are **stored**; the unit band drops them later, in the value route's qualification
step. So F-B10's fix belongs in `listing_normalize`, and its *measurable effect* shows
up one lane downstream. The 29/100 NULL-units figure from the prior sample is confirmed
(24.0% here) — but its consequence was mislocated.

---

## F-B11 · Three fields are NULL on 100% of ingested listings, by construction

**Severity: medium — two configurable filters are silently unusable.**

`tenancy_type`, `occupancy_rate_percent` and `neighborhood` are NULL on **150/150**.
Not a data-quality rate: `normalize_listing` reads all three from the *search stub*
(`stub["tenancy"]`, `stub["occupancyDetails"]`, `addr["neighborhood"]`), and
`to_search_stub()` does not emit any of them. Its own docstring concedes it:
*"Fields this feed doesn't carry (tenancy/occupancy details) are simply absent."*

Consequences, both latent:

1. `ListingFilters.tenancy_types` is an explicit-narrowing gate — unknown ⇒ drop. If an
   operator ever sets it, it drops **100% of the book**, silently.
2. `occupancy_min`/`occupancy_max` are pushed to the **server** by `scope_for_state`
   *and* retained as a client-side gate on a field that is always NULL. The two halves
   of one filter therefore disagree by construction: the server narrows, the client-side
   check is a no-op (numeric refinements are forgiving on unknowns).

---

## F-B16 · Cross-partition dedupe: order-dependent in code, inert on this data

**The GOAL's second lead — confirmed as a hazard, refuted as a live problem.**

`stubs.setdefault` means the winner of a duplicate is whichever partition ran first.
Measured: **2 of 1,962 assets (0.1%)** appear in more than one partition —
`2297949` in Brevard/Orange/Osceola (3), `2657687` in Miami-Dade/Palm Beach (2).

- **Winner is stable.** Partition order is `counties_for_state()`, a committed
  *alphabetical* Census list, so `setdefault`'s choice is deterministic for a given
  scope. All three runs produced the identical funnel fingerprint, which includes each
  duplicate's winning partition.
- **Winner is immaterial.** Checked directly against the frozen cassette: the stub
  payloads are **byte-identical** across every partition that returned them. Whichever
  one `setdefault` keeps, the stored data is the same.

**What the duplicates actually expose is a server-side filter leak.** Asset `2297949`
carries `county="Brevard County"` in its own payload and is still returned under
`counties=["Orange County"]` and `counties=["Osceola County"]`. Crexi's county filter
is demonstrably not a payload-county match — which is the leading hypothesis for F-B14.

---

## F-B12 · The plausibility envelopes never run on the Crexi path

**Severity: low here, but it invalidates an assumption.**

The GOAL asked for fields "nulled by plausibility bounds"
(`providers/normalization.py:225`). **Measured: zero, because this path never calls
them.** `plausible_price` / `sqft` / `year_built` / `units` / `latlng` have exactly one
caller — `registry._sanitize_record` (`registry.py:1629`), the MLS/registry merge
boundary — and it operates on `Property`/`Listing`, not `CrexiListing`. The Crexi
ingest reaches no such boundary, so `crexi_listings` can hold values the rest of the
system would reject.

Counterfactual on this sample: 1 of 150 (`2375589`, `building_sqft`) would be nulled.
Small — but "the sanity bounds protect this table" was an assumption, and it is false.

`clamp_to_column_limits` **does** run (it is called inside `listing_row`). It fired on
nothing here: 0 strings truncated, 0 integers nulled for exceeding int4.

---

## F-B13 · A normalization drop is invisible in every counter

**Severity: low — 0 occurrences here, structural nonetheless.**

`if listing is None: continue` (`crexi_ingest.py:383-384`) sits *before*
`stats.fetched += 1`. An asset whose normalization returns None is therefore not in
`fetched`, not in `fetch_errors`, and not in any other counter — it costs three HTTP
requests and vanishes. 0 of 150 this pass, so this is a latent observability hole, not
an occurring loss. Worth recording because "0" and "uncounted" look identical from the
aggregate, which is the whole reason this trace exists.

Related and confirmed: `stats.fetched` does not mean "detail fetched". It is
incremented after the normalize-None check, so it counts **successful normalizations**.
The reconciliation names it `fetched (== normalized ok)` for that reason.

---

## What this corpus cannot speak to — by construction, not by sampling

Recorded in the same spirit as F-B9's correction: a zero that was never given a chance
to be non-zero is not a measurement.

- **The UPDATE path never executed.** All 150 upserts were INSERTs. Of the 100
  pre-existing listings, 89 were economy-skipped and 11 never reappeared (F-B14). So
  the `ON CONFLICT` branch, the `is_sold` sticky-True rule and the enrichment-column
  protection are untested here. `upsert_listing_rows` also applies **no confidence
  gate** of any kind — the GOAL's "which fields were skipped because a lower-confidence
  source lost" names a mechanism that does not exist on this path. Column-level skips
  are structural (enrichment columns are simply absent from the `SET` list).
- **The fetch-error breaker** (`_FETCH_ERROR_BREAKER=5`): 0 fetch errors.
- **The unpriced skip** (step 5): inactive — the scope runs `include_unpriced=True`.
- **Price bisection** (`_price_bisect`): no FL county exceeded `SAFE_WINDOW=1400`, so
  every partition is a plain county scope and no price band was ever cut. This also
  means the *only* configuration in which cross-partition duplicates could carry
  differing payloads was never reached.
- **1,168 of 1,962 swept assets (59.5%)** never reached a gate: `--max-fetch 150`
  bounded the run, and the run correctly flagged itself `truncated` and withheld
  `backfilled_at`.

---

## Operational finding: the ingest is STATEFUL, so a cassette alone is not reproducible

Found while proving Phase 1. An `--apply` pass stamps `scrape_cursor`, so the *next*
run reads a watermark, takes the incremental branch (`scopes = [scope]` — one
whole-state sweep, no partitions) and issues a search body that was never recorded.
The DB is an **input to the request shape**, not just an output.

Consequence: reproducing this baseline requires `./rig/db.sh restore pre_ingest_baseline`
*before* every replay. Verified: with the restore, three runs produce identical
records; without it, the run dies on a cassette miss (which is the correct behaviour —
it fails closed rather than phoning home).

---

# 2026-08-28 — F-B14 SETTLED, and F-B15 re-classified

Two sessions are involved here. The ingest session **authored** F-B14 and a
pre-registered hypothesis; this session **audited** it. That distinction matters for
reading what follows: the claim survived, its stated mechanism did not.

## F-B14 · SETTLED — CONFIRMED as a real coverage loss (43.9%), and the mechanism is the opposite of the one predicted

**Verdict: the pre-registered falsifier was tested and did NOT fire.**

> Falsifier as written: *"if the whole-state paged sweep returns approximately the
> same 1,965 assets, then the whole-state `total_count` is inflated and F-B14 is a
> reporting artefact, not a coverage loss."*

| set | n |
|---|---|
| whole-state population, **enumerated** (price-partitioned) | **3,496** |
| whole-state `total_count` reported by Crexi | **3,496** — exact match |
| county-partition union (frozen baseline) | 1,962 |
| intersection | **1,962** |
| whole-state only | **1,534 (43.9%)** |
| county-union only | **0** |

The county union is a *strict subset*. `total_count` is not inflated by one listing:
a price-band partitioning of the identical server-side scope enumerated 3,496 distinct
ids with zero truncation and zero warnings. Every rate the frozen baseline reports over
`swept` is a rate over 56.1% of the population.

### Why the obvious probe would have lied

"Run a whole-state paged sweep and count" cannot settle this, and running it naively
would have produced a *confidently wrong* confirmation. `assets_search.py:180-182`
computes `size = min(page_size, PAGE_WINDOW - 1 - offset)` and returns `truncated` at
`size <= 0`, so a whole-state sweep stops at **1,499 ids regardless of the population**.
"The sweep returned far fewer than 3,496" is guaranteed in advance and carries no
information — it measures our own client and reports it as Crexi's coverage.

Three arms were run instead, each able to falsify on its own.

**Arm 1 — two windows, opposite ends.** Page whole-state twice, `Descending` then
`Ascending`. Each is capped at 1,499, but the *overlap* is the measurement and no
pagination cap can manufacture it.

```
newest-1499 window   1499      oldest-1499 window   1499
overlap                 0      union                2998
```

Perfectly **disjoint**. The reachable population is ≥ 2,998 — already 1.5× the county
union — established without trusting `total_count` at all. Had the population really
been ~1,965, the two windows would have overlapped by ~1,033.

**Arm 2 — the pagination ceiling, ruled out as an explanation.** Also: the constant
the code believes in is wrong.

```
offset=1498 count=1  -> OK   (sum 1499)
offset=1499 count=1  -> OK   (sum 1500)   <- the documented rule says this must 400
offset=1500 count=1  -> 400  "Offset + Count must be less than 1500"
```

The server's actual rule is **`offset < 1500`**; `count` is not in the check, despite
the error text (and despite `assets_search.py:14-16`, which encodes the message rather
than the behaviour). Our `PAGE_WINDOW - 1 - offset` arithmetic is therefore slightly
*more* conservative than the API requires — it collects 1,499 where 1,599 was available.
Immaterial to F-B14, and noted only so the next reader does not re-derive it.

`SAFE_WINDOW = 1400` (`crexi_ingest.py:61`) is a different constant with a different
job: it is only ever compared against `total_count` to decide *whether to partition*.
It never truncates a sweep in progress. **Neither cap explains the gap.**

**Arm 3 — an independent partition key.** Re-partition the same scope by asking price
using the product's own `_price_bisect`: 14 bands, 0 warnings, every band complete.
Union = 3,496 = `total_count`. County partitioning loses 43.9% of a scope that price
partitioning enumerates completely.

### The mechanism — and where the pre-registered hypothesis went wrong

> Hypothesis as written: *"the gap is Crexi's county index, not delisting. Asset
> `2297949`'s payload says Brevard yet it returns under Orange and Osceola filters."*

**The conclusion is right — it is the county index, and delisting is fully excluded**
(0 of the 1,534 were activated after the frozen run; all are live in the same feed).
**The stated mechanism is backwards, and its exhibit is misread.**

Asset `2297949` returns under `Brevard County` — it is that partition's *winner*. It
*also* returns under Orange and Osceola. So the exhibit demonstrates the index being
**over**-inclusive for 2 assets in the whole book (F-B16), which is the opposite failure
mode from losing 1,534. It cannot support "the filter is not a payload-county match".

The filter is very nearly the *opposite* of that. Splitting the population by the raw
form of `locations[].county` in the payload:

| raw county string form | reached by a county sweep | missed | miss rate |
|---|---|---|---|
| `"Duval County"` — Title + suffix | 1,949 | 33 | **2%** |
| `"Duval"` — Title, no suffix | 4 | 448 | **99%** |
| `"MANATEE"` — all caps | 9 | 114 | **93%** |

Probed live, one `count=1` request per variant:

```
counties=['Duval County']       -> 25        counties=['Volusia County']    -> 51
counties=['Duval']              -> 107       counties=['Volusia']           -> 98
counties=['DUVAL']              -> 107       counties=['Manatee County']    -> 22
counties=['duval']              -> 107       counties=['MANATEE']           -> 27
counties=['St. Lucie County']   -> 10        counties=['Putnam County']     -> 2
counties=['St Lucie County']    -> 25        counties=['Putnam']            -> 13
counties=['St Lucie']           -> 0         counties=['Other Florida County'] -> 6
                                             counties=['Belize']            -> 4
```

**`counties` is a case-insensitive but otherwise LITERAL string match** on the county
value stored on the record. Not a geo lookup, not normalized. The suffix matters, the
period in `St.` matters, case does not. `"Belize"` is a filterable Florida county value.

So the correct statement is: *the county filter matches the record's county string
exactly, and that is precisely why it misses* — because Crexi's own county field is
un-normalized. Our committed Census gazetteer supplies the one canonical form
(`"X County"`), which is the wrong key for every record entered any other way.

Where the 1,534 went:

| | n |
|---|---|
| payload carries **no county string at all** | **939** (61%) |
| payload names a county that **was** swept (wrong string form) | 526 |
| payload names a county that was not swept | 69 |
| activated after the frozen run (new stock, not a miss) | **0** |

The 939 are the load-bearing number: **no county key of any spelling can reach them.**
County partitioning is not fixable by a better county list — it is structurally
incapable of covering the scope. Price bisection already covers it, today, in 77
requests.

Every one of the 56 non-zero county partitions swept exactly its probe count (0
truncated, 0 short), confirming the earlier session's finding that the partitioner is
internally consistent. Its union is simply not the scope.

### What this does to the frozen baseline's rates

| | over `swept` (as reported) | over the true scope |
|---|---|---|
| reached by the sweep | 1,962 / 1,962 = 100% | 1,962 / 3,496 = **56.1%** |
| admitted by the type gate | 1,407 / 1,962 = 71.7% | 1,407 / 3,496 = **40.2%** |
| strict 2-4u matches | 90 / 1,962 = 4.6% | 90 / 3,496 = **2.6%** |

The funnel fingerprint `3c15972614b09973` is unchanged and still correct *for what it
measured*; what changes is the denominator it should be read against.

**F-B14 and F-B15 are largely independent.** The miss set is only mildly type-biased
(34.6% compound among the missed vs 28.3% among the reached), so closing the coverage
hole and changing the type policy are additive, not overlapping.

**Evidence:** `runs/coverage_verdict_FL.json`, `runs/coverage_report_FL.txt`,
`runs/coverage_{window,price,ceiling,variants,examples}_FL.jsonl`, cassette
`runs/cassettes/coverage_fl.jsonl`. Probe: `rig/coverage_probe.py` (170 live requests
total, budget-capped). Derivation: `rig/coverage_report.py` (no network).

---

## F-B15 · RE-CLASSIFIED — the exact match is deliberate; the policy and the inconsistency are what is open

The original write-up filed this at **high severity** with the rationale *"the
`ScrapeConfig` field documents itself as 'Property-type substrings to keep'
(`scrape_config.py:73-76`); the implementation is exact set membership. The documented
contract and the code disagree."*

**That rationale is withdrawn.** The exact match is deliberate and documented at the
call site — `listing_harvester.py:116-122`: *"Strict per operator choice — compound
types like 'Land, Multifamily' are excluded (exact match against the lower-cased
set)"* — and it is locked by `test_crexi_listings.py:160` and
`test_crexi_ingest_service.py:127`. Code that does what its docstring and its tests
say is not a defect. The stale prose in `scrape_config.py` is a doc-comment nit, not a
43%-of-a-funnel finding.

**The id is kept** (traces already tag observations with it) and re-pointed at what is
genuinely open, now at severity `policy`:

1. **Is the policy right?** It costs **1,086 of 3,496 (31.1%)** over the corrected
   denominator. A bounded example fetch (below) shows the drop set contains real 2-4
   unit multifamily *and* offices *and* raw land — the rule is indiscriminate in both
   directions.
2. **Two code paths disagree about what multifamily is**, and nobody chose that.

Sizing and evidence are in the decision packet: `runs/coverage_report_FL.txt`.
