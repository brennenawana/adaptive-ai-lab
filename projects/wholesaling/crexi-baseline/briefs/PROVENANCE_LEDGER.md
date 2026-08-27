# Task Brief — Provenance ledger for the Crexi ingest→value-route path

Status: READY TO EXECUTE
Session model: Opus · effort high · fresh context
Repo to edit: `~/code/adaptive-ai-lab` (branch `project/wholesaling-intake`)
Repo that is READ-ONLY: `~/code/wholesaling` — **make no edits there**

## Standing rules (this brief is your complete task context)

- Read this file and the rig files it names. Do **not** go exploring the wider
  wholesaling repo beyond the specific files cited here — scope creep is the
  main risk on this task.
- **No product-code edits.** All instrumentation is runtime seam-wrapping in the
  lab repo. If you believe a product change is unavoidable, STOP and report why
  rather than making it.
- Stay inside the **ingest → value-route** path. Do not instrument outreach,
  voice, CIS, dives, or the Redfin/nightly lane.
- Commit and push to `project/wholesaling-intake` at meaningful checkpoints.
- Append a dated entry to `projects/wholesaling/crexi-baseline/STATE.md` when done.

## Background you need (no other reading required)

There is a working rig at `~/code/adaptive-ai-lab/projects/wholesaling/crexi-baseline/`
that runs the real Crexi value-route pass against a local Postgres, fully offline.

```bash
cd ~/code/adaptive-ai-lab/projects/wholesaling/crexi-baseline
source rig/env.sh A          # A = deterministic (LLM off) | B = AI-on. SOURCE, never pipe.
./rig/db.sh up               # docker postgres:17 on port 55432, already has data
CREXI_CASSETTE=$CREXI_BASELINE_ROOT/runs/cassettes/fl.jsonl \
CREXI_CASSETTE_MODE=replay \
  ./rig/run.sh $CREXI_BASELINE_ROOT/rig/trace.py --limit 3
```

`rig/run.sh` is the ONLY sanctioned way to invoke anything: it cds to a guarded
work dir, runs a fail-closed preflight *there*, then execs. Never bypass it —
running from `~/code/wholesaling/backend` silently re-enables the **production**
R2 photo mirror.

Local DB already contains: 100 `crexi_listings`, 846 `crexi_comps`, 25 each of
property/valuation/deal/listing. Alembic head `0107_comm_fact_homes`.

`rig/trace.py` already wraps these seams at runtime and emits one JSONL record
per listing, tagged with defect ids from `rig/defects.py`:

| seam | currently captured |
|---|---|
| `listing_income._try_llm_extract` | llm gross, confidence, per-unit rents |
| `listing_income._validate_facts` | accepted/rejected, band ceiling, K/M rescue check |
| `listing_income.resolve_income` | final method/source/gross/confidence, ms |
| `crexi_value_route.compute_mf_arv` | arv value/confidence/source, comps in, comp_set len |
| `guardrails.apply.evaluate` | gate decision, reasons, **holds**, **overridden** |
| `CrexiClient._request` | every outbound call (method, path, ms, asset) |

## The problem to solve

The trace records **values** but not **producers**. It can say the rent was
`$5,382` via `market_median` — but not, in a structured way, that this value is
a *fallback* that exists only because an LLM extraction of `$46,000` was
**rejected by a deterministic validator**. That distinction is the whole point:
we are trying to establish what the LLM contributes versus what the script does,
and today the two are indistinguishable in the output.

Two real defects already found depend on exactly this distinction:
- **F-B4**: `_numbers_in` cannot parse `$400k`, so correct LLM extractions are
  discarded and the value silently falls back to a market median.
- **F-B8**: `sale_event_name` never reaches the field the ARV engine checks, so
  a ×0.55 confidence haircut applies to 100% of Crexi ARVs.

## What to build

A **provenance ledger**: for every value the lane produces that would appear on
a sellable lead, emit a structured record of what produced it.

### 1. The per-value record

Add to `rig/` a provenance model with at least these fields per value:

| field | meaning |
|---|---|
| `field` | e.g. `rent_estimate`, `arv`, `rehab_estimate`, `offer_price`, `condition_tier` |
| `value` | the value that reached the DB / the deal |
| `producer` | one of: `deterministic` · `llm` · `external_api` · `default_constant` · `human_attested` · `absent` |
| `producer_detail` | deterministic → `module.function`; llm → model id + prompt/tier id; external → endpoint path; default → the constant's name and value |
| `inputs` | the specific inputs consumed (ids, not whole payloads) |
| `validated_by` | which check accepted or rejected it, and the outcome |
| `fallback_from` | **required when this value is a fallback** — what was attempted first and why it lost |
| `confidence` | if the producer emits one |

`fallback_from` is the field that makes F-B1/F-B4 visible without prose. A
`market_median` rent whose `fallback_from` says
`{producer: llm, value: 46000, rejected_by: _validate_facts/band}` is
self-explaining.

### 2. Cover at minimum these values

- `rent_estimate` (+ which of the 4 income-ladder tiers produced it)
- `arv` (+ whether the ×0.55 no-provenance haircut applied)
- `arv_confidence`
- `rehab_estimate` (note: derived from condition tier × a constant — a
  `default_constant` producer when the tier is itself a heuristic default)
- the gate decision and each hold reason
- the terminal lifecycle stage

### 3. The aggregate the ledger must answer

Produce a summary (a script or a function in the rig) that answers, over N
listings:

> For each sellable field, what fraction of values were produced by
> deterministic code, an LLM, an external API, or a default constant — and how
> many were fallbacks from a rejected higher-tier producer?

This table is the deliverable. It is what tells us whether the LLM is
contributing, and what a buyer would actually be relying on.

## Constraints and gotchas (learned the hard way)

- **Seam ordering is not stable.** `_process_listing` computes the ARV *before*
  resolving income. `trace.py` already handles this with `_boundary()` — any new
  seam must call it too, or values get attributed to the previous listing. This
  bug already happened once and produced confidently wrong records.
- **`install()` asserts every seam exists** and records its source digest. Keep
  that discipline for new seams: a rename must fail loudly, not silently drop a
  column.
- Prefer wrapping **module-global** names. `_process_listing` is a closure inside
  `value_route_pass` and cannot be patched.
- Use the cassette in `replay` mode while developing — it is instant and
  deterministic. A miss raises by design.
- Arm A vs Arm B differ only in whether the LLM can serve. Run both: the ledger
  should make the difference between them legible, which today it is not.

## Acceptance criteria

1. `./rig/run.sh $CREXI_BASELINE_ROOT/rig/trace.py --limit 5` in **both arms**
   emits per-value provenance records for the fields listed above.
2. For the known case `asset_id=2660435` in **Arm B**, the `rent_estimate`
   record shows `producer=deterministic` (market median) with `fallback_from`
   naming the rejected LLM value `46000.0` and the rejecting check.
3. For any listing with an ARV, the `arv_confidence` record indicates whether
   the no-provenance haircut applied.
4. The aggregate table runs over an existing trace file and prints the
   producer-mix per field.
5. Replay stays offline: `cassette: hits=N misses=0`.
6. Nothing under `~/code/wholesaling` is modified (`git -C ~/code/wholesaling status` clean).

## Report when done

Append to `STATE.md`: what was built, the producer-mix table for a sample run,
and anything the ledger revealed that the value-only trace had hidden.
