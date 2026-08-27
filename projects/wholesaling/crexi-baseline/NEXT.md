# NEXT — the single source of truth for "what do I do now"

> If you read one file, read this one. Updated at every checkpoint.
> Last updated: 2026-08-27 (after F-B9).

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

## THE NEXT ACTION (one thing)

**Run the full instrumented pass over all 100 local listings, both arms, offline,
and produce the baseline table.**

```bash
cd ~/code/adaptive-ai-lab/projects/wholesaling/crexi-baseline
./rig/db.sh up

# Arm A (deterministic) -- record first (new listings need cassette entries), then replay
source rig/env.sh A
CREXI_CASSETTE=$CREXI_BASELINE_ROOT/runs/cassettes/fl.jsonl CREXI_CASSETTE_MODE=record \
  ./rig/run.sh $CREXI_BASELINE_ROOT/rig/trace.py --limit 100 --out runs/baseline_armA.jsonl

# Arm B (AI on) -- needs the AI cassette too
source rig/env.sh B
CREXI_CASSETTE=... CREXI_AI_CASSETTE=... CREXI_CASSETTE_MODE=record \
  ./rig/run.sh $CREXI_BASELINE_ROOT/rig/trace.py --limit 100 --out runs/baseline_armB.jsonl

# the deliverable
./rig/run.sh $CREXI_BASELINE_ROOT/rig/provenance.py runs/baseline_armA.jsonl runs/baseline_armB.jsonl
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
