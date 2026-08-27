# GOAL — close Phase 1, freeze the Phase 2 baseline, run ONE Phase 3 experiment, then STOP

> Session goal file. Self-contained: read this plus `NEXT.md` and `STATE.md` in
> this directory and you have everything. Do not go exploring beyond the files
> they name.

## The objective, in one sentence

Take the Crexi ingest→value-route lane from "we have defect anecdotes" to "we
have a frozen, measured baseline and one experimentally-measured improvement" —
then **stop for operator review**.

## Hard constraints

- **`~/code/wholesaling` is READ-ONLY.** Never edit it. `git -C ~/code/wholesaling status`
  must be clean when you finish. The Phase 3 change is a **rig-side patch**, not
  a product edit (see Phase 3 below).
- Invoke everything through `./rig/run.sh` — never bypass it. Running from
  `~/code/wholesaling/backend` silently re-enables the **production** R2 mirror.
- Stay inside the ingest→value-route path. Do not instrument outreach, voice,
  CIS, dives, or the Redfin nightly lane.
- Work on branch `project/wholesaling-intake` in `~/code/adaptive-ai-lab`.
  Commit and push at each phase boundary.
- **Update `NEXT.md` first, then `STATE.md`, at every checkpoint.** A stale
  `NEXT.md` is a defect.

## Phase 1 — close it (~30 min)

One item remains: **map every defect class in `rig/defects.py` (F-B1…F-B9) onto
the playbook's canonical failure taxonomy RC-1…RC-12.** The taxonomy is in
`../ARCHETYPE_C_BRIEF.md` §2 (RC-1 instrument defect … RC-12 architecture
mismatch).

This is not bookkeeping: the RC class determines which intervention rung Phase 3
is *allowed* to use, and RC-1 (instrument defect) must be cleared before any
other diagnosis is trusted. Record the mapping in `rig/defects.py` as an `rc`
field per class, with a one-line justification.

Flag explicitly if any defect is RC-1 — that would mean our own measurement is
suspect and Phase 2 must fix it first.

## Phase 2 — freeze the baseline

Produce ONE measured baseline over a defined corpus. Deliverables:

1. **Corpus definition + digest.** All 100 local `crexi_listings` (or a stated
   stratified subset). Record row counts and a content digest so "the same
   corpus" is checkable later.
2. **Full instrumented run, BOTH arms, offline.** New listings need a `record`
   pass first (a cassette miss raises by design); then verify a `replay` pass is
   `hits=N misses=0`.
3. **The baseline table**, via `rig/provenance.py`: per-field producer mix
   (deterministic / llm / external_api / default_constant / absent), per-defect
   rate, and fallback counts.
4. **A manifest**: git SHA of both repos, alembic head, arm, cassette digests,
   corpus digest, pinned clock. Without this the baseline is not re-checkable.

**Phase 2 is done when** a second identical replay reproduces the same ledger
fingerprint. If it does not, the baseline is not frozen — find the variance
before proceeding. (Arm B needed an AI cassette for exactly this reason.)

## Phase 3 — ONE experiment, then STOP

**The experiment is already chosen and pre-registered. Do not substitute a
different one.**

**Change:** fix `_numbers_in` so it parses `$400k` / `$1.2M` notation
(`app/services/listing_income.py:752-760` — currently
`\$?\s?([0-9][0-9,]{2,})(?:\.[0-9]{2})?`, no K/M handling).

**How:** as a **rig-side monkeypatch** in the trace harness — the same
seam-wrapping used everywhere else. This is a diagnostic gate: it measures the
effect cheaply and reversibly *before* anyone commits to a product change. Do
NOT edit the wholesaling repo.

**Measure:** re-run the frozen corpus, both arms, and report the delta:
- listings whose rent producer changes from `market_median` → `llm_extract`
- listings whose rent confidence crosses the **0.35** `min_rent_confidence` floor
- any change in `deal_type` / terminal stage
- defect-rate delta for F-B4 specifically

**Pre-registered prediction (stated before looking — do not revise it):**
F-B4 affects ~6% of descriptions and ~25% of successful extractions; expect
single-digit percentage-point movement on this 100-listing corpus.

**Pre-registered consequences:**
- **Moves the needle** → write it up as a work order for the wholesaling repo
  (spec + measurement + acceptance), and STOP.
- **Does not move the needle** → F-B4 is real but not the binding constraint.
  Record that, name the next candidate (tier-1 generator is OFF in prod — zero
  `crexi:marketing_desc:llm` rows have ever been written), and STOP.
- **Result is below what the corpus can resolve** → say INCONCLUSIVE. n=100 with
  a ~6% base rate is a handful of listings; do not report a rate you cannot
  support.

## STOP CONDITION — read this twice

When the F-B4 delta is measured and written up, **STOP and hand back to the
operator.** Do NOT continue into the standing queue (F-B8 sale_event_name
mapping, F-B2 comp_set persistence, condition coverage). F-B8 in particular is
an **underwriting change** requiring operator sign-off — starting it
unprompted would be a scope violation.

Report at the stop: what the baseline says, what the experiment measured against
its prediction, and what you recommend next — as a recommendation, not an action.

## Do not revisit (settled, see FINDINGS.md F-B9)

- Seeding a rehab estimate — inert on this book (0.05% of listings).
- "Making the gate reachable" — a tautology; the gate runs, the router declines
  to price.
