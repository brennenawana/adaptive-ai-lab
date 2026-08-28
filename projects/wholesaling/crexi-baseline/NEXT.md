# NEXT — the single source of truth for "what do I do now"

> If you read one file, read this one. Updated at every checkpoint.
> Last updated: 2026-08-27 (ingest baseline COMPLETE — all three phases).

## The arc (your mental model is correct)

```
PHASE 1  harvest defect classes from real listings        <- WE ARE HERE (nearly done)
PHASE 2  freeze a baseline: one measured run over a       <- next
         defined corpus, numbers not anecdotes
PHASE 3  iterate: change ONE thing, re-run, measure       <- the payoff
         the delta against the frozen baseline
```

Phase 3 is the point. Phases 1–2 exist only to make Phase 3's numbers mean
something.

## ACTIVE GOAL: `GOAL_COVERAGE.md`

Ingest baseline is FROZEN (fingerprint 3c15972614b09973, 1,962 records).
Next: settle F-B14 (the sweep reached 56% of its own scope, so every rate is
over the wrong denominator), then build the targeting decision packet for the
operator. `GOAL_INGEST.md` complete; `GOAL_BASELINE.md` paused.

## SCOPE CORRECTION 2026-08-27

The instrumentation built so far covers the **value-route / analysis** lane only
(24 seams: income, ARV, linkage, routing, gate). The **ingest** lane — sweep,
filter, normalize, identity, upsert — has **zero** coverage, and that is the half
this project is about. Operator redirected scope back to ingest.

**Active goal file: `GOAL_INGEST.md`.** `GOAL_BASELINE.md` (value-route) is
paused, not cancelled — the F-B4 experiment stays queued behind the ingest
baseline.

## THE NEXT ACTION (one thing)

**`GOAL_INGEST.md` is DONE — all three phases.** The baseline is frozen at funnel
fingerprint `3c15972614b09973`; the table is `runs/ingest_funnel_FL.txt`, the
write-ups are the ingest section of `FINDINGS.md`, and 7 new defect classes
(F-B10…F-B16) are in `rig/defects.py`.

**Nothing has been fixed. That was the instruction, and it holds until the
operator picks the experiment.**

**Recommended first ingest experiment — F-B14 (partition coverage).** Not the
biggest-looking number, the one everything else is conditional on: a sweep that
reaches 56% of its own scope makes every downstream rate a rate over the wrong
denominator. It is also the cheapest to settle — one live probe comparing a
whole-state paged sweep against the county union. Pre-register before looking:

- **Prediction:** the 1,531 gap is Crexi's county index, not delisting. Evidence:
  asset 2297949's payload says Brevard and it is still returned under Orange and
  Osceola filters, so the filter is not a payload-county match.
- **Falsifier:** if a whole-state paged sweep returns the same 1,965 assets the
  county union did, the whole-state `totalCount` is inflated and F-B14 is a
  reporting artefact, not a coverage hole.
- **If confirmed:** the fix is a partitioning key that covers the scope, not a
  wider county list — the county list is already complete.

Runners-up, in order, and why they wait: **F-B15** (28.3% dropped on a compound
type string) is blocked on an underwriting decision, not a code decision — is
"Office, Multifamily" a deal? **F-B10** (units in prose, 60.0% → 75.3% strict) is
the highest-value pure code fix, but its effect is measured one lane downstream,
so it wants the value-route baseline running alongside.

Reproducing the frozen pass (fully offline, ~0s):

```bash
cd ~/code/adaptive-ai-lab/projects/wholesaling/crexi-baseline
./rig/db.sh up
source rig/env.sh A

# The DB is an INPUT to the request shape (the cursor decides full vs incremental),
# so the cassette alone does NOT make the pass reproducible. Restore first, always.
./rig/db.sh restore pre_ingest_baseline

CREXI_CASSETTE=$CREXI_BASELINE_ROOT/runs/cassettes/ingest_fl.jsonl \
CREXI_CASSETTE_MODE=replay CREXI_PINNED_NOW=2026-08-27T23:00:00+00:00 \
CREXI_BASE_URL=http://127.0.0.1:1 \
  ./rig/run.sh $CREXI_BASELINE_ROOT/rig/ingest_trace.py --states FL --apply --max-fetch 150 \
    --out runs/ingest_trace_FL_replay2.jsonl
# expect: hits=586 misses=0, wall=0s, funnel fingerprint 3c15972614b09973
```

**Why this and not something else:** we have 9 defect classes but no *rates* over
a defined population. Without that, "we improved it" is unmeasurable.

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

**Ingest half: DONE.** `runs/ingest_trace_FL_record.jsonl` + `runs/ingest_funnel_FL.txt`,
manifest inline, 10/10 counters reconciled, fingerprint reproduced 3x offline.
Value-route half: still the `trace.py` / `provenance.py` outputs, unchanged.

## Phase 3: the first experiment is already chosen

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
