# GOAL — an INGEST baseline: audit every listing's journey from sweep to stored row

> Session goal file. Self-contained: this file plus `STATE.md` in the same
> directory is everything you need. Do not explore beyond what they name.
> **Supersedes `GOAL_BASELINE.md`**, which was scoped to the value-route lane —
> the wrong half. Read this one.

## Why this scope

Existing instrumentation (`rig/trace.py`, 24 seams) covers only what happens
**after** a listing is already a row: income, ARV, linkage, routing, gate. The
ingest half — sweep, filter, normalize, identity, upsert — has **zero**
coverage. That is the half the project is actually about.

## The objective, in one sentence

For every asset the sweep returns, record **where it went and why**, from the
Crexi search result to the stored `crexi_listings` row — then freeze that as a
measured baseline.

## Hard constraints

- **`~/code/wholesaling` is READ-ONLY.** Never edit it; `git -C ~/code/wholesaling status`
  must be clean at the end. All instrumentation is runtime seam-wrapping in the
  lab repo, exactly as `rig/trace.py` already does.
- Invoke everything through `./rig/run.sh` — never bypass it. Running from
  `~/code/wholesaling/backend` silently re-enables the **production** R2 mirror.
- Branch `project/wholesaling-intake` in `~/code/adaptive-ai-lab`. Commit and
  push at each phase boundary. Update `NEXT.md` first, then `STATE.md`.
- Do not touch the value-route instrumentation. It works; leave it alone.

## The ingest funnel you are auditing

`app/services/crexi_ingest.py::ingest_state`, in order:

| # | step | where | today's visibility |
|---|---|---|---|
| 1 | watermark / fingerprint gate (full vs incremental) | `:275-282` | one aggregate flag |
| 2 | county-partitioned sweep (FL = 56 partitions) | `:286-305` | `swept` count only |
| 3 | cross-partition dedupe (`stubs.setdefault`) | `:302-304` | **none — and order-dependent** |
| 4 | type gate | `:309-311` | `type_matched` count |
| 5 | unpriced skip | `:313-320` | `unpriced_excluded` count |
| 6 | detail-fetch economy vs stored `source_updated_on` | `:322-341` | `unchanged` / `fetched` |
| 7 | per-asset detail fetch + error breaker | `:349-379` | `fetch_errors` |
| 8 | normalization → `CrexiListing` | `providers/crexi/listing_normalize.py` | **none** |
| 9 | strict type+unit-band filter (2-4u; **unknown units DROPPED**) | `providers/crexi/listing_filters.py:9,45,112` | `strict_matches` count |
| 10 | batched upsert + `clamp_to_column_limits` | `persistence/crexi_listing_store.py:29-60,105` | `upserted` count |
| 11 | `bump_last_seen` + cursor stamp | `:412-424` | — |

Aggregate counters exist (`IngestStats.as_json()`, `:145-164`). **Per-asset
attribution does not.** That is the gap.

## Phase 1 — record one ingest pass, then replay offline

The cassette (`rig/cassette.py`) already wraps `CrexiClient._request`, the
chokepoint for both `POST /assets/search` and `GET /assets/{id}`. So:

1. Run `scripts.crexi_ingest --states FL --db prod --apply` under
   `CREXI_CASSETTE_MODE=record` with a bounded `--max-fetch`.
2. Verify a second run in `replay` mode is `hits=N misses=0` and produces an
   identical result — **prove it by pointing `CREXI_BASE_URL` at an unreachable
   port**, as was done for value-route.

Now the whole ingest funnel is deterministic and free to re-run.

## Phase 2 — per-asset ingest trace

Build `rig/ingest_trace.py` on the same pattern as `rig/trace.py`
(seam-wrapping, `install()` asserting each seam exists and recording its source
digest, one JSONL record per **asset**). For every asset the sweep returns:

- `asset_id`, the partition(s) it appeared in, and whether it was a
  cross-partition duplicate
- **terminal outcome**: `upserted` | `dropped` | `unchanged` | `fetch_error`
- **drop stage + reason**, one of: type gate · unpriced · unit-band
  (distinguish **unit unknown** from **out of range**) · normalization ·
  fetch error
- per-field **arrival state** after normalization: populated / null / **nulled
  by plausibility bounds** (`providers/normalization.py:225` — `PRICE_MIN=1000`,
  sqft 100..1e6, year 1700..2100) / **clamped** by `clamp_to_column_limits`
- upsert outcome: insert vs update, and for updates which fields were
  **skipped because a lower-confidence source lost** (the confidence gate)

Reuse `rig/defects.py` — add ingest-stage classes as you find them (the registry
already has a `stage` field and `"ingest"` is already in `STAGES`).

## Phase 3 — the baseline table, and STOP

Produce the funnel with per-asset attribution, not just counters:

```
swept N
  -> dropped: type gate        n  (%)
  -> dropped: unpriced         n
  -> dropped: unit unknown     n   <- expect this to be large; 29% of a prior
  -> dropped: unit out-of-band n      sample had units NULL
  -> fetch error               n
  -> unchanged (economy)       n
  -> upserted                  n
       of which insert / update
       fields nulled by bounds: {field: n}
       fields clamped:          {field: n}
       upsert writes skipped:   {field: n}
```

Plus a **manifest** (git SHAs, alembic head, cassette digest, corpus digest,
pinned clock) and a **reproducibility check**: a second replay must produce an
identical fingerprint.

**Then STOP and hand back.** Do not start fixing anything you find. Report the
table, the defect classes discovered, and a recommended first experiment — as a
recommendation, not an action.

## Two known leads to confirm or refute (do not assume)

1. **Unit-band strictness.** `listing_filters.py:9-11` says unknown units are
   dropped when a bound is set. A prior sample had **29/100 with `units` NULL**.
   Quantify: how many assets die there, and does the raw payload carry unit
   information that normalization did not map?
2. **Cross-partition dedupe order-dependence.** `crexi_ingest.py:302-304` uses
   `stubs.setdefault`, so which duplicate wins depends on partition arrival
   order. With FL's 56 partitions, determine whether any asset appears in more
   than one partition and whether the winner is stable across replays.

## Do not revisit (settled — see FINDINGS.md F-B9)

- Seeding a rehab estimate (inert, 0.05% of the book).
- "Making the gate reachable" (a tautology; the router declines to price).
