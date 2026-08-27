# Crexi Baseline — State of Work

> Durable handoff. Written 2026-08-27. Everything needed to resume without
> conversation history. Append-only in spirit: correct facts in place, add new
> sections at the end.

## Where things stand

**Epic:** build a reproducible, fully-observed baseline of the Crexi
ingest→analysis lane, then optimize. Plan approved; Phases 0–1 complete, Phase 2
(trace instrumentation) partially built, Phase 3+ not started.

**Current activity:** walking listings one at a time to harvest defect classes
(error analysis) — deliberately NOT building a corpus yet. Operator's call, and
correct: the playbook's ch. 03 §5.1 requires harvesting real failures before
deriving any ontology.

**Next task (operator-directed):** full auditability of *what produced each value*
— deterministic script vs LLM vs external API — at every step, before walking more
listings. **DONE 2026-08-27** — see "Provenance ledger" at the end of this file.

## The rig

Repo: `~/code/adaptive-ai-lab`, branch `project/wholesaling-intake`.
All rig files under `projects/wholesaling/crexi-baseline/`.

| File | Role |
|---|---|
| `rig/env.sh` | Hermetic env. **source, never execute, never pipe.** `source rig/env.sh A\|B` |
| `rig/preflight.py` | Fail-closed gate. Asserts **effective outcomes**, not env inputs |
| `rig/preflight.sh` | Wrapper that runs the above from the guarded CWD |
| `rig/run.sh` | **The only sanctioned way to invoke anything.** cds to the work dir, runs preflight *there*, then execs |
| `rig/db.sh` | `up / schema / down / nuke / snapshot / restore / psql` |
| `rig/defects.py` | Stable defect-class registry (F-B1…F-B8), keyed to stages |
| `rig/trace.py` | Per-listing seam CAPTURE via runtime wrapping (no product edits) |
| `rig/provenance.py` | Per-value provenance ledger: model, derivation, producer-mix aggregate |
| `rig/cassette.py` | Record/replay for BOTH non-deterministic boundaries: Crexi HTTP + the LLM |
| `runs/*.jsonl` | Trace + sweep outputs (`trace_arm*`, `http_arm*`, `ai_arm*`) |
| `FINDINGS.md` | The defect write-ups with evidence chains |

Arms: **A** = deterministic (`AI_LOCAL_TRANSPORTS_DISABLED=true`, LLM income
extraction structurally off). **B** = AI-on (claude_sdk serves).

## Local database

- Docker `postgres:17`, digest-pinned, container `crexi-baseline-pg`, **port 55432**
- URL: `postgresql+psycopg://wholesaling:wholesaling@127.0.0.1:55432/wholesaling`
- Schema at alembic head **`0107_comm_fact_homes`**
- Sentinel row `rig_marker = 'crexi-baseline-rig'` proves identity (host+port alone
  do not: an ssh tunnel on `127.0.0.1:25432` reaches a **remote** Postgres)

**Row counts as of 2026-08-27:**

| table | rows |
|---|---|
| crexi_listings | 100 |
| crexi_comps | 846 |
| property / valuation / deal / listing | 27 each (25 + the 2 fresh listings walked 2026-08-27) |
| crexi_comps | 847 |
| audit_log | 102+ (62 at first count; the provenance passes appended `crexi_link` rows) |

Data provenance: a live FL ingest (`--states FL --db prod --apply --max-fetch 500`)
stopped early at 100 listings; comps accumulated from value-route passes.

## Safety — three fail-open defects found and fixed

The dominant risk is touching production. `crexi_ingest.py:55-72` /
`crexi_value_route.py:126-132` resolve their own DB URL and **fall back to
`backend/.env.local` (real Supabase) when a var is unset or empty**.

1. **R2 false pass.** Exporting `R2_*` as empty strings did NOT neutralize the
   photo mirror — `Settings` sets `env_ignore_empty=True`, so empty reads as
   unset and `backend/.env` supplied `R2_BUCKET=media`. **Measured
   `mirror.enabled=True` while the gate printed PASS.** Only a CWD with no
   `.env` works.
2. **Locality.** `127.0.0.1` proves nothing here (ssh tunnel to a remote PG,
   verified live — it answered and rejected our password). Gate now requires
   host+port+database+sentinel.
3. **Preflight/run CWD mismatch.** The gate passed from `runs/work` while the
   script ran from `backend/` and printed `photo mirror: ON (R2)`. `run.sh` now
   runs both in one CWD.

**Standing rule learned:** assert the *effective outcome*
(`build_crexi_mirror().enabled`), never the environment meant to produce it.

## Credentials

`CREXI_TOKEN` read by reference from `~/.config/crexi/token` (mode 0600, outside
both repos). Valid to **2026-10-11**, carries the `Comps` capability. It was
pasted in chat, so it lives in a transcript — **rotate after the baseline.**

## Defect classes found (details + evidence in FINDINGS.md)

| id | stage | rate (n=25) | summary |
|---|---|---|---|
| **F-B8** | arv | **100%** | `sale_event_name` never reaches `Comp.exclusion_reason` → universal ×0.55 haircut; moves 58% of ARVs below the 0.35 floor AND disables the package-deal exclusion |
| F-B6 | income | 76% | priced off tier-4 market median |
| F-B3 | arv | 60% | ARV confidence below the 0.35 floor (mostly an effect of F-B8) |
| F-B4 | income | 25% of extractions | `_numbers_in` can't parse `$400k` → correct extractions discarded |
| F-B2 | arv | all | `comp_set` computed (61/41 comps in memory) then **dropped at persist time** |
| F-B1 | income | 4% | per-unit band rejects a correct high-rent extraction |
| F-B5 | arv | 4% | no ARV despite comps fetched |
| F-B7 | income | — | no income signal at all |

Only **1 of 25** listings is defect-free.

## Corrections I made to my own claims

Recorded because they matter for trusting the rest:
- "Validator rejected 73%" — **wrong**; 11 of 13 rejections were `gross=None`,
  the LLM correctly reporting no stated income.
- "ARV may be anchored to the ask" — **wrong**; ARV is genuinely comp-derived.
- A crude regex screen suggested 22% band exposure — **discarded**, it was
  matching asking prices, not income.
- Two bugs in my own trace harness (chunk_limit semantics; ARV attributed to the
  predecessor listing because ARV computes before income).

## Known operational facts

- Value-route throughput: ~30s–2min/listing, dominated by comp fetches at
  `crexi_requests_per_second=2.0`. A full FL pass (1,511 type-matched) ≈ 12–40h.
- Income resolution alone: median **7.6s**/listing in Arm B (the LLM call).
- FL scope: 56 county partitions, 2,087 swept, 1,511 type-matched multifamily,
  `total_count=3,480`.
- Prod cron fires 01:41/07:41/13:41/19:41 UTC — stay clear during record passes.

## Offline replay — the corpus is self-contained

**Question:** can we re-run against local data without re-scraping?
**Answer: yes, fully — verified by cutting the network.**

What is stored locally: **100/100** listings with `raw_listing`, `raw_brokers`,
`summary_details`, `photo_urls`; **846/846** comps with `raw_payload`.
(`transaction_history` / `property_record_id` exist on the 24 listings that have
been through value-route — subject-record enrichment only runs there.)

Stored data alone was NOT enough. Measured on a re-run, two calls per listing
still fired:

| call | purpose | when |
|---|---|---|
| `POST /universal-search/v2/search` | comp bbox search | **unconditionally, every listing** |
| `GET /universal-search/rental-markets/stats?lat=&lon=` | tier-4 market-median rent | when income falls to tier 4 |

Detail fetches were already avoided by the freshness gate (`comps_new=0`,
40s → 4s). Both survivors take deterministic inputs, so `rig/cassette.py` caches
them at the transport layer.

```
record  : 5 recorded, wall 3s
replay  : 5 hits / 0 misses, wall 0s
replay with CREXI_BASE_URL=http://127.0.0.1:1 (unreachable)
        : 5 hits / 0 misses, wall 0s   <- proof, not inference
```

Defect output identical across all three. **A replay miss RAISES** rather than
falling through to the network, so "it stayed offline" is proven each run rather
than assumed.

Usage:
```bash
CREXI_CASSETTE=$CREXI_BASELINE_ROOT/runs/cassettes/fl.jsonl CREXI_CASSETTE_MODE=replay ./rig/run.sh $CREXI_BASELINE_ROOT/rig/trace.py --limit N
```

**Caveat:** the cassette covers only what the listings exercised so far. Walking
new listings requires a `record` pass first — and a miss failing loudly is the
correct behavior, not a bug.

**Why this matters:** the iteration loop drops from ~40s to ~0s per pass and
becomes deterministic, so "change the code, re-run, diff" measures the change
rather than Crexi's churn.

## Not yet examined

- **Routing and gate stages.** Every listing so far terminates at
  `MF_REVIEW_HOLD_REASON`, so the gate has never done real work in a trace.
- The `F-B5` no-ARV case is undiagnosed.
- Ingest-stage defects (only the value-route half is instrumented).

---

## 2026-08-27 — Provenance ledger (ingest→value-route)

**Task:** `briefs/PROVENANCE_LEDGER.md`. Built entirely by runtime seam-wrapping in
this repo; `git -C ~/code/wholesaling status` clean (0 changed files).

### What was built

`rig/provenance.py` (new) — the ledger. Three parts:

1. **`PValue`** — one record per value that would appear on a sellable lead:
   `field · value · producer · producer_detail · inputs · validated_by ·
   fallback_from · confidence · is_fallback · notes`. `producer` is a fixed
   vocabulary (`deterministic · llm · external_api · default_constant ·
   human_attested · absent`); an unknown one raises, and a record flagged
   `is_fallback` with no `fallback_from` raises — a fallback with no record of
   what it fell back *from* is the un-auditable state the ledger exists to remove.
2. **`build_ledger(rec, consts)`** — derives those records from one captured trace
   record. Derivation is deliberately NOT inside the seams: a fallback is only
   knowable once you know which tier won, and keeping it here means a taxonomy fix
   re-derives from a frozen trace instead of forcing a re-run.
3. **`aggregate` / `render` + CLI** — the producer-mix table, one per arm.
   `./rig/run.sh $CREXI_BASELINE_ROOT/rig/provenance.py runs/trace_armA.jsonl runs/trace_armB.jsonl [--fallbacks] [--json]`

`rig/trace.py` — stays a pure CAPTURE layer, extended from 6 seams to 22. New:
the whole income ladder tier by tier (`request_listing_extract`, `_from_regex`,
`_parse_unit_mix`, `_from_unit_mix_fmr`, `_from_market`), the LLM transport
chokepoint (`message_generator.ai_complete` → served provider/model + prompt
digest), `crexi_linkage.link_listing`, `workers.routing.route`,
`valuation.engine.estimate_rehab` (both bindings), `workers.guardrail.apply_gate`,
`repositories.append_audit_log` (filtered to `event_type=guardrail`), and
`crexi_value_route._hold_for_mf_review`. `install()` still asserts every target
exists and records its source digest.

**Seam ordering.** `_boundary()` is now documented as callable only by the three
OPENING seams — `resolve_income`, `compute_mf_arv`, `link_listing` — the ones that
receive the listing itself and can be the first event for a new asset. Every other
seam is strictly nested inside one of those and calls the new `_inner()`, which
never flushes and instead records a `seam_id_mismatch`. Flushing from a nested
seam would have re-introduced the exact misattribution `_boundary()` exists to
prevent (a deduped property carries a canonical id that is not this listing's
asset id). Both arms ran with **0 `seam_id_mismatch` records**.

Also: `classify()` now emits **F-B8**, which the registry documented but the
classifier never implemented; and the HTTP path roll-up's `len(seg) > 12` test was
eating real segments (`/<id>/v2/search` for `/universal-search/v2/search`).

### Producer mix — n=5 listings, both arms, cassette replay, `CREXI_PINNED_NOW=2026-08-27T20:00:00Z`

```
                    ARM A (LLM off)                         ARM B (LLM on)
field            vals determ  llm  const absent fb ext  | determ  llm  const absent fb ext
rent_estimate       5  5 100%    .     .     .   5   4  |  4 80%  1 20%    .     .   4   3
arv                 5   4 80%    .     .  1 20%  0   0  |  4 80%     .     .  1 20%  0   0
arv_confidence      5   4 80%    .     .  1 20%  4   0  |  4 80%     .     .  1 20%  4   0
rehab_estimate      5      .     .     .  5 100% 0   0  |     .      .     .  5 100% 0   0
condition_tier      5      .     .  5 100%   .   0   0  |     .      .  5 100%   .   0   0
offer_price         5      .     .     .  5 100% 0   0  |     .      .     .  5 100% 0   0
gate_decision       5      .     .     .  5 100% 0   0  |     .      .     .  5 100% 0   0
lifecycle_stage     5  5 100%    .     .     .   0   0  |  5 100%    .     .     .   0   0
```
`fb` = fallbacks from a rejected higher-tier producer. `ext` = values whose
dominant input came from an external API.

Cassette: arm A `hits=9 misses=0`, arm B `hits=8 misses=0` (arm B skips one
market-stats call because the LLM served that listing). Arm A: 5/5 LLM
completions `FAILED AiUnavailableError`. Arm B: 5/5 `served claude_sdk/claude-opus-4-8`.

### What the ledger revealed that the value-only trace had hidden

1. **A quarter of the sellable fields have no producer at all.** `rehab_estimate`,
   `offer_price` and `gate_decision` are `absent` on 10/10 listing-arms. Not
   "low confidence" — structurally never computed:
   - `crexi_linkage.link_listing` seeds a valuation with `arv` + `rent` only, and
     `recompute.route_new_property` (unlike `recompute_property`) never calls
     `_refresh_rehab`. So `router.route` sees `estimated_rehab=None`, which by
     §1.5 step 8 makes the cash terms UNPRICEABLE → `deal_type=none` → no offer.
   - Because the deal is `none`, `routing_result.produced_ids` is empty, nothing is
     threaded into `deal_ids`, and **`guardrails.gate.evaluate` never runs**.
     Corroborated in the DB: all 25 `event_type=guardrail` audit rows were written
     by `crexi_value_route` (the MF-review hold), zero by the guardrail worker.
   The value-only trace showed this as three blank columns, indistinguishable from
   "not instrumented yet".

2. **`condition_tier` is a hardcoded constant on 100% of listings.** Every listing
   routes on `ConditionSignal(tier=UNKNOWN, confidence=0.2)` minted inline in
   `RoutingWorker._route` because `property.condition_signal` is None. That
   constant is the multiplicand the rehab model would use — so the one input the
   rehab estimate is most sensitive to is not a measurement at all. New
   `default_constant` finding; not previously recorded.

3. **In arm A, every rent is a fallback.** `fb=5/5`. The ladder shows tier 1
   `attempted=true, served=false,
   transport_unavailable(MessageGeneratorError: no provider is configured to serve
   task kind 'extract')`. The value-only trace showed `llm_gross: null` — identical
   to "the LLM ran and found nothing", which is a completely different fact. This
   is the arm-A/arm-B discriminator the brief asked for.

4. **Arm B is not reproducible.** Two identical cassette replays of the same 5
   listings produced different rent producers: `2659977` was `llm_extract` on the
   first run and `regex_extract` on the second (LLM returned 3300.0, rejected
   `not_in_source`), and `2660435`'s self-reported confidence moved 0.9 → 0.6.
   The cassette froze Crexi; the LLM tier is the remaining source of variance, and
   the ledger is what makes it visible. **An arm-B LLM cassette is the next
   prerequisite for treating arm B as a measurable arm.**

5. **The `×0.55` haircut has a named counterfactual now.** Every ARV-bearing
   listing carries `arv_confidence.fallback_from = {producer: deterministic, value:
   <pre-haircut>, rejected_by: no comp carries a sale-type/owner-occupant signal
   (F-B8)}`. Concretely: 0.553→0.304, 0.658→0.362, 0.551→0.303, 0.551→0.303. Three
   of four sit above the 0.35 credibility floor before the haircut and below it
   after — F-B8 alone is what puts them under the floor. The factor is read from
   `type1.no_provenance_confidence_discount` at run time, never hardcoded.

6. **The tier-4 rent's real input is an external endpoint.** `ext=4/5` (arm A).
   Each market-median rent carries
   `inputs.market_median = {producer: external_api, endpoint: GET
   /universal-search/rental-markets/stats, market_name: "Fort Lauderdale, FL",
   rent_median: 1794.0}`. A buyer relying on "rent $5,382/mo" is relying on a
   metro-wide median × unit count, not on anything about the subject.

**Acceptance criterion 2 verified** — `asset_id=2660435`, arm B:
`rent_estimate = 5382.0, producer=deterministic,
producer_detail="listing_income._from_market (market median x units, FMR-clamped)",
fallback_from={producer: llm, tier: 1, value: 46000.0,
rejected_by: "_validate_facts/band",
detail: "gross 46000.0 outside [200.0, units(3) x _MAX_UNIT_RENT(15000.0) = 45000.0]"}`.

### Taxonomy call worth knowing about

`producer` names the code that COMPUTED AND EMITTED the value that reached the DB,
not the ultimate origin of every number feeding it. So a tier-4 rent is
`deterministic` (`_from_market` multiplied a median by the unit count and clamped
it to the FMR ceiling), matching the brief's acceptance criterion 2 — the external
dependency is not lost, it is recorded in `inputs` with its own `producer` and
endpoint, and the aggregate's `ext-in` column counts it. `producer=external_api`
is reserved for a value that reaches the lead essentially unmodified from an
endpoint. Likewise `arv_confidence` stays `deterministic` even when the ×0.55
haircut fires: the number still varies with comp count/spread/recency, so calling
it a constant would misstate the mix — the constant's effect is carried by
`producer_detail` + `fallback_from` + the `fallback` column.

### Not done / known gaps

- **`gate_hold` had never been emitted by a real pass** at the time of writing.
  **Closed the same day — see the follow-on section below.**
- The Crexi cassette now holds 9 entries covering 5 listings (was 5 / 3).
- Arm B needs an LLM cassette before it is reproducible (finding 4).
  **Closed — see below.**

## 2026-08-27 (follow-on) — closing the two gaps the ledger left open

### 1. Arm B is now a reproducible arm (`rig/cassette.py`)

The Crexi cassette froze the HTTP boundary; the model was the whole remaining
variance. `cassette.py` now holds a shared `_Store` with two installers:
`Cassette` (Crexi HTTP, unchanged API) and **`AiCassette`**, which
records/replays at `message_generator.ai_complete`.

Keyed by what the model was **asked** — `kind|label|system|user|schema|max_tokens`
— not by listing id. Two listings with an identical description are genuinely the
same question, and a prompt-template edit correctly invalidates every entry
instead of serving a stale hit. **Successes only**: reconstructing a provider
exception would be guessing, and an unrecorded failure correctly misses later.

The fail-loud raise matters more here than for HTTP: `_try_llm_extract` swallows
`MessageGeneratorError` and drops to tier 2, so a miss surfacing as an `AiError`
would be **invisible — indistinguishable from arm A**. `CassetteMiss` is a plain
`RuntimeError` for exactly that reason (`_dispatch` catches only `AiError`;
`value_route_pass` catches only `ListingTimeoutError` / connection errors).
**Verified, not assumed:** a replay against a missing cassette aborts with `exit=1`.

```
record : ai-cassette hits=0 misses=0 recorded=5
replay : ai-cassette hits=5 misses=0   ledger fingerprint 7b443e91b33df21c
replay : ai-cassette hits=5 misses=0   ledger fingerprint 7b443e91b33df21c   <- identical
```

**Arm A must never use it.** The prompts are identical across arms, so a cassette
set in arm A *would* hit — fabricating a completion arm A can never produce and
silently turning it into arm B. `trace.py` now refuses to start in that
configuration rather than measure a lie.

```bash
# arm A: no AI cassette, ever
CREXI_CASSETTE=$CREXI_BASELINE_ROOT/runs/cassettes/fl.jsonl CREXI_CASSETTE_MODE=replay \
  ./rig/run.sh $CREXI_BASELINE_ROOT/rig/trace.py --limit 5
# arm B: both
CREXI_CASSETTE=$CREXI_BASELINE_ROOT/runs/cassettes/fl.jsonl CREXI_CASSETTE_MODE=replay \
CREXI_AI_CASSETTE=$CREXI_BASELINE_ROOT/runs/cassettes/ai_fl.jsonl CREXI_AI_CASSETTE_MODE=replay \
  ./rig/run.sh $CREXI_BASELINE_ROOT/rig/trace.py --limit 5
```

### 2. Real `gate_hold` records — and a confidently wrong one caught

**Reaching a fresh listing.** `skip_asset_ids` is the wrong lever: a poison-skip
still increments `stats.processed`, which is what `max_deals` budgets, so a skip
list just burns the budget. The **keyset cursor** is the right one — it filters in
SQL, before any per-listing work. `trace.py` gained `--after-key ISO_TS,ASSET_ID`
and `--after-last-linked` (computes the boundary as the oldest already-linked
listing, i.e. start at the first listing this lane has never routed). This is also
the "walk the next unseen listing" primitive the error-analysis loop wants.

Two never-linked listings were walked (`2518410`, `2514650`), record mode on both
cassettes. Corpus grew 25 → 27 properties/deals/valuations.

**The bug it caught.** The first fresh run reported
`gate_decision = hold, produced by guardrails.gate.evaluate -> apply_gate` — on a
listing where `evaluate` had returned **nothing**. Cause: `_hold_for_mf_review`
writes its *own* `event_type=guardrail` audit row, and the audit tap was letting
it populate `gate_apply`. It also duplicated the hold reason. Fixed by attributing
audit rows by **call scope** (a depth counter set inside the `apply_gate` wrapper)
rather than by matching the row's actor or text — attribution by string match is
what produced the wrong record in the first place. Every guardrail row is still
kept as evidence, now tagged `from_apply_gate`.

Corrected output for `2514650` (first pass, arm B):

```
gate_decision    absent         None
                 guardrails.gate.evaluate never ran (no deal reached the guardrail worker)
gate_hold        deterministic  "multi-family underwriting pending — held for manual review…"
                 crexi_value_route.MF_REVIEW_HOLD_REASON
lifecycle_stage  deterministic  "guardrail (held: MF review)"
                 crexi_value_route._hold_for_mf_review -> repositories.update_deal_status
                 fallback_from: {producer: deterministic, value: "route",
                                 rejected_by: "router minted deal_type=none -> parked as an MF review card"}
```

**This strengthens finding 1 rather than overturning it.** On a listing's very
first pass — deal freshly minted, nothing idempotent about it — the lane *still*
never reaches `guardrails.gate.evaluate`. The captured `guardrail_audit` now
carries that as in-trace evidence (the only guardrail row is written by
`crexi_value_route`, `from_apply_gate: false`), where before it was a DB query run
by hand. And the ledger now shows what the router had actually reached — stage
`route` — before the lane overrode it to a review card.

### Still open

- The gate has now been proven unreachable on both a re-pass *and* a first pass,
  so `guardrails.gate.evaluate` is untested by this corpus by construction, not by
  sampling. Anything that would change that has to start with seeding a rehab
  estimate so `route` can price a deal.
- `human_attested` and `external_api` remain unobserved producers across every run
  so far — no value in this lane is either.
