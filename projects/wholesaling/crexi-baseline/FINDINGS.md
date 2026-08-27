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
