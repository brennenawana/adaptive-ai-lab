# Underwriting Mechanics — How Each Sellable Number Is Produced (2026-08-25)

> Companion to [`UNDERWRITING_TRUST.md`](UNDERWRITING_TRUST.md) (which judges
> the evidence). This file records the machinery. All paths under
> `~/code/wholesaling`.

## The product boundary already exists in code

`services/handoff_approval.py:38-65` defines an `inputs_fingerprint` over
exactly: **`offer_price, assignment_fee, expected_fee, math_version, arv,
arv_confidence, arv_source, condition_confidence`** — the codebase's own answer
to *"what numbers does a buyer's decision rest on."* Adopt this as the eval
scope rather than inventing one. (Do not confuse it with
`deal.inputs_fingerprint`, which is all deal values minus volatile keys,
`mappers.py:493-511`.)

## 1. ARV

One engine, no second formula, **no LLM anywhere in `app/valuation/`**:
`valuation/engine.py:55 compute_arv(subject, sold_comps, params, now)`.

- **Screens** (`_evaluate_comp:231`): non-positive price; same property type;
  build-year window 10/max 15; `comp_sqft_tolerance` **default 0 = OFF**
  (`parameters.py:829`); `comp_block_radius_miles` **default 0 = OFF** (`:840`).
- **Outliers** (`_flag_price_outliers:342`): MAD robust-z > 2.5, needs ≥4
  metrics; `MAD==0` branch flags >50% off consensus.
- **Value** (`_weighted_central_value:432`): weighted mean $/sqft × subject
  sqft, else weighted mean price; weight `1/(1+d)`.
- **Income-space bump** +$20,000 when beds ≥ median+1 or sqft ≥ 1.15× median.
- **Crime haircut** is a separate step (`crime_adjusted_arv:556`): low 1.0 ·
  moderate 0.98 · elevated 0.95 · high 0.90 · severe 0.82.
- **Confidence** (`_arv_confidence:512`): `0.70·count + 0.18·spread +
  0.12·recency`, two multiplicative veto gates, then **×0.55 when no comp
  carries sale-type provenance**.

**Accuracy gate** (`scripts/accuracy_gate.py`): metric is per-market **median
absolute fractional leave-one-out comp error**; threshold `0.05` absolute rise
vs a persisted baseline, `--min-n 50`. Runs **weekly Mon 05:23 UTC only**;
first run seeds and exits 0. **No committed measurement, snapshot, or MAPE
history exists anywhere in the tree** — mechanism live, evidence zero.
`factor_register` `BACKTESTED == 0`.

**Fallbacks and their knife-edges:**
- **JV-as-ARV (FL)** (`opendata/florida_dor.py:306-326`): DOR Just Value
  emitted as one synthetic comp at `distance=0.0`, `sale_date=now`. Measured
  confidence **0.036** (vs 0.531 for 5 tight comps) — far below the 0.35 floor.
  **JV populates a visible ARV that can never price.**
- **Assessed fallback** (`_assessed_fallback_arv:203`): `assessed_value ×
  multiple` (2.0 MI / **1.0 FL**) at confidence **0.35** — and
  `assessed_fallback_confidence == min_arv_confidence == 0.35 exactly`, with
  the check written `<`, so it clears **by zero margin**.
- **AREA-AVERAGE GUARD** (`:148-153`) returns `arv=None` rather than a cohort
  mean (DL-046: 846 Lansing properties once shared one ARV).
- **Null ARV** → `_unpriceable_cash_reason` "no usable ARV" → deal routes NONE;
  `apply_gate` forces HOLD for CASH only (T2/T3 exempt — they underwrite off
  financing terms).

## 2. Condition tier → rehab

`engine.py:712`, formula `:753`: `cost = sqft × tier_multiplier ×
market_cost_per_sqft`, floored at `min_cost` unless the multiplier is 0.
Constants (`parameters.py:126-172`): `market_cost_per_sqft` **50.0 flat** ·
TURNKEY 0.0 · LIGHT 0.20 · MODERATE 0.45 · HEAVY 0.70 · DISTRESSED 1.0 ·
`min_cost` 5000 · `default_sqft` **1200** · `low_confidence_threshold` 0.5.

**`UNKNOWN` is deliberately absent from the table and falls back to the
DISTRESSED multiplier (1.0)** — the most expensive possible assumption.
`rehab_as_of` is pinned to `_REHAB_MODEL_AS_OF = 2025-01-01` with a
"BUMP when recalibrated" instruction that has **never been bumped**.

## 3. Solvers (all `app/underwriting/engine.py`, pure, 60-iteration bisection)

Shared (`underwrite():207-269`): `eff_inc = rent×0.80`; `cf_mo = eff_inc −
piti`; `cash_in = down + closing + extra_cash` (fee never financed);
`coc = cf_mo×12/cash_in`.

- **Cash turnkey** (`type1_turnkey_offer:283`): candidate `list × 0.70`, ×0.90
  when DOM ≥ 150; down 0.20, rate 0.07, 30y; bisect down until `coc ≥ 0.20`.
  §5.13 removed **all price ceilings**.
- **Cash distressed flip** (`type1_distressed_flip:433`): `all_in = P + fee +
  2500 + 2500 + rehab`; `holding = all_in × 0.015 × 4`; `commission = 0.06 ×
  ARV`; bisect until `profit ≥ 0`. **Requires ARV and rehab both non-null.**
  No exit transfer tax subtracted.
- **Seller finance** (`type2_contract_basis:566` + builder `router.py:599-810`):
  `purchase = list × 1.10` (the premium *is* the interest, 0% stated); payment
  linear in the bar; AFR floor `financed × 0.045/12`; balloon 6y, refi at LTV
  0.75.
- **Mortgage takeover** (`type3_down_payment:666`): down **$0** when list >
  $130k and inherited rate > 0.05. `inherited_monthly_pi:139` resolves
  (1) recorded payment, (2) re-amortize `initial_loan_amount`, (3) current
  balance — **re-amortizing a seasoned balance understates payment and inflates
  CoC/fee**.

## 4. Strategy routing — fully deterministic

`routing/router.py:1000 route()`. Since §5.13 (2026-06-11) every property is
underwritten for **all three** structures with a menu on `Deal.structures` and
**primary always cash**. Hard pre-guards → `_none_deal`: excluded states
IL/WA/NJ/SC/OR · LAND · mobile/manufactured by address token ·
`_lacks_structure_evidence` → `HOLD_NO_STRUCTURE_EVIDENCE` · nominal-price DLBA
· short-sale watch.

**Condition picks the math, never viability** (`_build_structures:1358`):
`tier is DISTRESSED` → flip/ARV math, else turnkey rent/return.

The displayed strategy is **not** `deal.deal_type` (an emission-lane field) —
it is `strategy_assessment->>'recommended'`, whose deterministic baseline is
`routing/baseline_assessment.py:377` with `target_price` = the router's own
solve.

## 5. Versioning

Two systems coexist: the superseded hash (`config/math_version.py`, still
stamping) and the layered manifest (`config/underwriting_version.py`), whose
docstring records the measured 2026-08-04 prod failure — coverage gaps,
all-or-nothing granularity (#1504 marked ~3,600 deals stale for a 73-deal
outcome), **8 coexisting versions, 8.7% at head**.

Four layers: VALUATION · UNDERWRITING (incl. `area_costs.py`, `taxes.py`) ·
ROUTING · REFDATA (the CSVs). `layer_digest` sha256[:16], CRLF-normalized;
`MANIFEST` append-only with **frozen literal digests, never live calls**. CI
drift guard `tests/test_underwriting_version.py:62` asserts `drifted_layers()
== []` and `:142` proves the guard can fire.

**`freeze_status` is not a column** — it is a request flag on
`POST /api/admin/reunderwrite`; `services/reunderwrite.py:507,554-559` captures
each deal's status and property `lifecycle_stage` pre-recompute and restores
them after, so **nothing reaches a send/pitch queue whatever the gate decides**.

## 6. Gates and holds

Taxonomy CI-locked at `analytics/gate_reasons.py:49-97`.

- **Pre-pricing** (`workers/routing.py`): `DISTRESS_SALE_LIEN_RISK` ·
  `list_price is None` → hold (never route off a fabricated $0) ·
  **`HOLD_AREA_COSTS_MISSING`** when county millage or insurance band is
  unresolvable · `HOA_ELIGIBLE_DUES_UNKNOWN`.
- **Router**: `_unpriceable_cash_reason:410-447` (non-positive offer;
  DISTRESSED `arv<=0`; DISTRESSED rehab None; negative flip profit; TURNKEY
  `effective_income<=0`; CoC unreachable). `impossible:sub_payoff` when offer <
  `balance×1.05`. **Credibility floors**: ARV confidence < **0.35** →
  `hold:arv_low_confidence`; TURNKEY rent confidence < 0.35 →
  `non_offerable:basis_unverified`.
- **Guardrail gate** (`guardrails/gate.py:690`) — sanity bounds are **terminal
  REJECTs, never bypassable**: offer > list · offer > **1.10 × ARV** ·
  price-to-annual-rent > **40.0** or < **1.0**. HOLDs: no validated agent email
  on Type-1 EMAIL · `condition_confidence < 0.5` · Type-3 `mortgage_confidence
  < 0.5`.
- **Overlays** (`guardrails/apply.py`): `condition_confidence is None` ·
  delisted · no contact · `NO_ARV_HOLD_REASON` **CASH only** ·
  `AREA_COSTS_HOLD_REASON` CASH backstop against
  `{None, "param-estimate", "unresolved"}`.

## 7. AI inputs that reach an emitted offer — exactly two

1. **Condition tier → rehab → cash offer** (load-bearing). Prompt
   `vision/bench/extended.py:201-244` → `condition_analysis.py:467-477` writes
   `property.condition_tier/_confidence`; model
   `google/gemini-3.1-flash-lite-preview`. **Validation is enum + [0,1] clamp
   only** (`extended.py:260-267`) — no plausibility bound. Overwrite is guarded
   by `should_overwrite` (higher confidence wins) plus human-attested refusal —
   **both skipped when `request.force`** (`condition_analysis.py:774,780`), and
   `vision_force_reassess` overwrites unconditionally. **No feature flag** on
   the queue path; no prompt version recorded.
2. **Extracted gross rent → SF payment + offerability.** `listing_income.py`
   tier 1 — **the strongest validation in the tree** (`:153-197`): confidence
   floor 0.35; per-unit band $200–$15,000 (catches annual-as-monthly); an
   anti-hallucination check that the gross's digits **literally appear in the
   source text** (or are a sum of appearing per-unit rents, or appear as
   `gross×12`); confidence capped 0.8; falls through to a deterministic regex
   tier on failure. **Ungated and unbudgeted by design** — the only LLM number
   reaching an offer with no flag.

**Displayed but never multiplied — and this is the trap:** dive-authored
`target_price`/`walk_price`/`concession_cap` are validated **type-only, with no
bounds and no cross-check against the router's solve**
(`services/strategy_assessment.py:23-30`). They **overwrite** the deterministic
baseline (`_OVERWRITABLE_KINDS = {framework_dossier, router_baseline}`), and
~16,032 of 16,108 prod deals carry `router_baseline`. Consequence:
`frontend/.../DealPanel.tsx:775` shows `target_price` **instead of** the
router's `offer_price`, demoting the deterministic solve to Diagnostics.

**Not AI**: ARV, comp selection, the rehab formula, rent tiers 2-4, tax
parsing, voice (contract forbids offer terms/ARV/rent), and LLM outreach email
figures (solved deterministically).

## 9. Buyer-visible outputs

`valuation`: `arv`, `arv_source/_confidence/_as_of`, `comp_set`,
`rent_estimate`, `rent_fmr_ceiling`, `rent_source/_confidence/_as_of`,
`rehab_estimate`, `rehab_source/_confidence/_as_of`, `math_version` — all
nullable. `deal`: `deal_type`, `terms`, `structures`, `offer_price`,
`assignment_fee`, `coc`, `underwriting_version`, `data_quality`,
`strategy_assessment`, `expected_fee/split_pct/realized_fee`.

**No `noi`, `cap_rate` (outside stated carry), `spread`, `margin`, `mao`, or
`max_offer` field exists.** Nearest analogues: `estimated_flip_profit`,
`assignment_fee`, `walk_price`. **No CSV export exists** anywhere in backend or
frontend — relevant if leads are to be delivered as files.

**Trust labels** (`services/deal_review.py:103-151`) are the sleeper finding:
`_REAL_COMP_PROVIDERS = frozenset({"rentcast"})` and `_REAL_RENT_PREFIXES =
("rentcast",)` — **on the free key-free path every ARV and rent already labels
ESTIMATED**; rehab is always `DERIVED`; `_RECORDED_MORTGAGE_SOURCES` is an
**empty frozenset**, so every mortgage figure is `is_estimate=True`. The system
already knows it is estimating nearly everything.

## 10. Known defects (beyond the FL run)

- **HOA guard built but DORMANT**: the Redfin map collapses condo/townhouse to
  `SINGLE_FAMILY`, so no row is flagged `hoa_eligible` and real condos price at
  **$0 HOA** (~$300-500/mo omitted → offer too high).
- **ARV coverage** (`Docs/DATA_LEAK_AUDIT.md`, prod 2026-06-12): only **28.7%**
  of 8,009 properties had a valid ARV; of those 91.4% were raw sale-price means
  and **71.7% shared a handful of identical market-average ARVs**. DL-061:
  57.8% of deals permanently held on the condition default; DL-065: 93.3% lack
  sqft → 6,037 valuations on the 1,200 default.
- **Mirage cases** that motivated the credibility floors: Bradenton — a $627k
  cash offer off an **$18,339/mo per-sqft "rent"** at confidence 0.3;
  305 S Ohio — $226k at 35%-of-list over a **0.27-confidence ARV**.
- **Still live**: 237 SW Higgins, a 2006 commercial NNN condo priced off
  residential comps.
- **MF income**: real in-place rents in `leaseEventHistory` are in a Crexi doc
  **we already fetch** but parse transiently and drop; listing
  `netOperatingIncome`/`capRate` are **not read at all**.
- **Operator mandate** (`DEAL_STRATEGY_FRAMEWORK.md:6-14`): the engine's math
  is *"back-of-the-napkin… Hard-coded constants mis-price real cases"*; every
  asset has 1–3 case-specific gating variables that decide the deal before
  return math matters; value-add assets warrant a **RANGE** (income floor ↔
  retail ceiling) because a point estimate *"hides which buyer the number
  belongs to."* **This is the strongest existing argument for what a sold lead
  should actually state.**
