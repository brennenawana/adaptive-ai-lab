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
