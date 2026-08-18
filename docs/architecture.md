# FIS Architecture

Concrete shape of the Fintech Integration Sandbox, and the decisions behind it.
For *why the platform exists*, see the Canonical Architecture doc in `docs/`.

---

## Runtime topology

```
                        ┌──────────────── MODEL GATEWAY ────────────────┐
                        │  one contract; provider is a registry entry   │
  eval runner ─────────▶│                                               │
  (checkpointed)        │  local-specialist   claude-frontier  (codex)  │
                        │  llama.cpp :8082    claude -p CLI            │
                        │  local-specialist-switchyard                  │
                        │  Switchyard :4000 ──▶ llama.cpp :8082 (R1)    │
                        └───────────────────────┬───────────────────────┘
                                                │
                     ┌──────────────────────────▼──────────────────────────┐
                     │            AI ORCHESTRATOR (investigate)            │
                     │  gather → generate → verify → score → persist       │
                     └───────────┬─────────────────────────┬───────────────┘
                                 │                         │
                    ┌────────────▼──────────┐   ┌──────────▼─────────────┐
                    │   TOOL BROKER         │   │  DETERMINISTIC VERIFIER│
                    │   8 read-only tools   │   │  schema / citations /  │
                    │   role: fis_tools     │   │  observed ids / calib. │
                    └────────────┬──────────┘   └────────────────────────┘
                                 │ SELECT only, no ground_truth grant
   ┌─────────────────────────────▼─────────────────────────────────────┐
   │  PostgreSQL 16 + pgvector  :5433                                  │
   │  customer identity ledger processor risk webhook integration      │
   │  cases knowledge          │ ground_truth (ANSWER KEY, isolated)   │
   │                           │ learning (trajectories, case_scores)  │
   └───────────────────────────┴───────────────────────────────────────┘
                                 ▲
                                 │ materialised by consumers
   ┌─────────────────────────────┴─────────────────────────────────────┐
   │  NATS JetStream :4222   — see "Event-driven requirement" below    │
   └───────────────────────────────────────────────────────────────────┘
```

### Ports

| Port | Service | Note |
|---|---|---|
| 5433 | FIS PostgreSQL + pgvector | offset deliberately |
| 4222 | NATS JetStream | 8222 monitoring |
| 8082 | local model (llama.cpp) | |
| 4000 | NeMo Switchyard (routing gateway) | `make serve-switchyard`; passthrough to 8082 in R1 |
| 8083 | candidate weak arm — Nemotron 3.5 Lightning (llama.cpp, same build) | `make serve-nemotron`; hybrid GPU/RAM placement, `--no-mmap` (R3) |
| 9000/9001 | MinIO | `artifacts` profile, not yet used |
| **5432** | **pre-existing `thewall` Postgres** | **not ours — do not touch** |
| **6379** | **pre-existing Redis** | **not ours** |
| **8080/8081** | **Bonsai / Qwen3.8-27B** | **not ours** |

---

## Event-driven requirement (NORMATIVE)

**Status: LANDED 2026-08-15.** All seven migration steps are done. The requirement
below stays normative: a new scenario class in an event-shaped category must publish
rather than insert, and `test_event_driven_scenarios_do_not_hand_author_their_consequences`
enforces it for the ported classes.

The guide names event-driven workflows and eventual consistency as core things the
sandbox must teach. Before the migration the scenario generator wrote rows directly
into every service schema, which meant the interesting failures were **depicted
rather than produced**:

- S01/S02 (duplicate delivery, idempotency) were hand-authored row pairs. Nothing
  actually attempted deduplication, so nothing could actually fail to.
- S07 (reversal race) was hand-authored out-of-order timestamps. No real ordering
  hazard existed.
- S09 (stale mapping) was a hand-written mismatch between `raw_payload` and
  `normalized_state`, rather than the output of a mapper that is genuinely stale.

That was a meaningful gap. A scripted race teaches the *shape* of the bug; an
emergent one teaches the mechanism, and only the emergent one can surprise us.

It surprised us immediately. Porting S04 to a real clustering query exposed that its
four "simultaneous" vendor timeouts were generated a *month apart* — `add_customer`
ticked the shared clock back 30 days, so every extra customer dragged the timeline
with it. The scenario had never contained the cluster it claimed to model.

### Required topology

```
provider event
     │
     ▼
webhook-gateway ── publishes ──▶  fis.webhook.received.<provider>
                                        │
                          integration-service consumer
                            (idempotency + mapping)
                                        │
                                        ▼
                                 fis.domain.normalized.<type>
                                        │
                      ┌─────────────────┼──────────────────┐
                      ▼                 ▼                  ▼
              ledger-service     risk-service        case-service
              posts entries      raises alerts       opens cases
```

Streams (JetStream, file-backed):

| Stream | Subjects | Retention |
|---|---|---|
| `FIS_WEBHOOK` | `fis.webhook.received.*` | limits, work-queue per consumer |
| `FIS_DOMAIN` | `fis.domain.normalized.*` | limits |

### Non-negotiable constraint: determinism survives

Making the pipeline asynchronous must **not** make the corpus non-deterministic.
The eval depends on the same seed producing the same world; if consumer timing can
reorder effects, every before/after comparison silently loses its meaning.

Resolution — **deterministic event sourcing**:

1. The generator publishes events in a seed-determined order and **awaits consumer
   acknowledgement** before publishing the next. The mechanism is genuinely
   event-driven; the schedule is not left to timing luck.
2. Races are produced by **deliberately publishing out of order** (S07 publishes
   the reversal before the late settlement), not by hoping the scheduler does it.
3. Idempotency is enforced by the consumer keyed on `provider_event_id` +
   `idempotency_key`. S02 makes it fail by omitting the key — so the double
   posting is a real consequence of a real defect.
4. A generation run is complete only when the consumer lag is zero. The generator
   blocks on that, so a partially-materialised world can never be scored.

### Migration plan — all steps complete

| Step | Change | Status |
|---|---|---|
| 1 | `fis_platform/events/` — JetStream connection, publisher, typed envelopes | done |
| 2 | Stream provisioning in `make up-core` (idempotent) | done |
| 3 | `integration-service` consumer: idempotency + versioned mapper | done |
| 4 | `ledger-service` consumer: posts entries from normalized events | done |
| 5 | Generator publishes instead of inserting for webhook/settlement paths | done |
| 6 | Regenerate the corpus; re-baseline every arm | done — suite v2 |
| 7 | Delete the direct-insert path so it cannot silently come back | done |

Genuinely event-driven: **S01, S02, S06, S07, S09, S10** — and, since suite v3,
every class with card activity publishes its **background** settlements too
(`catalog._background`: S01, S02, S05, S06, S07, S08; S11's three "already
reconciled" postings). State-based, correctly: **S03, S04, S09's state, S12** — not
every operational problem is an event-ordering problem. Under suite v2 the background
settlements of six classes were state rows with no posting, i.e. S10's fault
signature as ambient noise (`SUITE_V3_RELEASE_CONTRACT.md` § 2A).

The mapper version is recorded **per published event** (`World.mapping_versions`,
applied identically by `projection.project` and `run.materialise`): S06's
transposing release (v3) is live for the injected settlement only and rolled back
(v4) before its background arrives, so `integration.events.mapping_version` says
which event the bad release touched.

#### What step 7 actually deleted, and what survives

`World.add_event` is gone outright and `integration.events` is not in the writer's
table list, so a normalized event cannot be hand-authored at all — it is the mapper's
output, and the mapper is the thing under test. Since suite v3 `World.add_entry` is
gone too and `ledger.entries` left `_TABLES`: every posting in the corpus is the
ledger consumer's (S11's hand-written `le_<seed>_NN` entries beside pipeline
`le_<12hex>` ids were a class fingerprint).

One narrow direct-write path survives **on purpose**:

| Survivor | Used by | Why it is not a regression |
|---|---|---|
| `World.add_failed_delivery` | S04, S12 | A delivery that FAILED is the one thing a consumer cannot record about itself — the bus naks and redelivers on handler exception, so recording its own failure would mean pretending to have survived it. Modelling retry storms properly needs poison-message handling, which this migration deliberately does not add. Restricted to `retrying`/`failed`; a handled delivery raises `ValueError`. |

**S12 is the open one.** Its retry storm is genuinely webhook-shaped and would be
better as a real one; it stays hand-authored only because the bus has no poison-message
path. Closing that gap is a change to `add_failed_delivery`'s callers, not a new
escape hatch — which is the point of the status restriction.

### Evidence reachability (NORMATIVE)

**Every id a manifest requires must be returnable by some tool call the evidence plan
actually makes.** Not "exists in the database" — *reachable*.

This is stated in `task-ontology.md` §5 and was violated by the entire corpus until
the migration. The event trail is addressed by `provider_event_id`, which the
fixed-evidence plan discovers by walking `provider_ref` out of phase-one results —
and no delivery's `provider_event_id` had ever matched one. Zero of 312 deliveries
were reachable. Four classes were capped below the 0.8 recall threshold before a
model saw them, which reads in a report as model weakness.

Two enforcement points, both required for a new scenario class:

- `test_required_evidence_is_reachable_by_the_tool_set` — static, per class.
- `make reachability` — replays the real plan through the real broker against the
  generated corpus and prints the recall **ceiling** per class. Anything below
  threshold is a harness bug. Run it after every `make corpus`.

Cross-entity queries carry an extra obligation. `get_verifications` v2 can select by
vendor and time rather than by customer, so it is the first tool whose results are
not confined to one scenario by construction. Scenarios therefore occupy disjoint
48-hour slots on the timeline (`scenario_epoch`), and
`test_scenario_verification_windows_do_not_overlap` guards it. Any future
time-scoped or cohort-scoped tool inherits this constraint.

---

## Components

### Model gateway (`fis_platform/model_gateway/`)
One `GenerationRequest`/`GenerationResponse` contract; the provider is a registry
entry. **This is what makes E2/E4/E5 a controlled comparison** — the arms differ by
one string (`model_ref`), not by call path.

Adapters: `local.py` (OpenAI-compatible HTTP, GBNF-constrained, greedy + seeded —
the reproducible baseline), `claude_cli.py` (subscription CLI as a backend). A second
local entry, `nemotron-lightning` (8083), uses the same adapter and decoding — R3
compared the two weak arms by `model_ref` alone; see `routing-experiments.md` § R3.

The generation budget is an explicit factor, not a constant: `run_eval --max-tokens`
(default `DEFAULT_MAX_TOKENS = 4096`, the value every run before R3b was made with)
reaches `GenerationRequest.max_tokens` and is recorded on every
`ModelInvocation.max_tokens` (and in `config_digest` when non-default). The local
adapter also records `reasoning_chars` / `content_chars` from llama.cpp's
`reasoning_content` — observation only — so a `length` stop can be told apart from a
wrong answer, and thinking length is measurable per case (R3b).

Two transport quirks handled here rather than leaking upward:
- llama.cpp's schema→GBNF compiler rejects `minLength`/`maxLength`; `schema_compat.py`
  strips them for the grammar while the verifier still enforces them.
- Claude Code invokes an internal side model on every call; `_extract_usage` filters
  `modelUsage` to the canonical model so per-arm cost is not inflated.

### Routing gateway — NeMo Switchyard (`fis_platform/model_gateway/switchyard.py`, `infra/switchyard/`)
**Beneath** the model-gateway contract, never beside it. A routed model is one more
registry entry (`local-specialist-switchyard`): same `GenerationRequest`, same
`GenerationResponse`, same trajectory; its `base_url` is the Switchyard listener on
**:4000** and its `model_id` a Switchyard route id. `SwitchyardAdapter` subclasses the
local adapter and inherits `build_body`, so the request is byte-identical on both
paths by construction. Whatever the gateway reports lands in
`ModelInvocation.routing` (`schemas/routing.py`) — only what it *actually* reported;
a passthrough records `selected_backend=None`.

Switchyard owns transport, backend selection inside a profile, fallback and
per-request stats. FIS keeps scenario truth, the evidence plan, prompts and grammar,
the scorer, the split and the trajectory. `router_signals` rejects every manifest gold
field, and routing code may not import the scorer or the manifest schema
(`test_routing_no_gold_leak.py`).

**Measured non-equivalence (R1) and its fix (R0.1), both 2026-08-16:** Switchyard 0.2.0
re-serialises JSON with sorted keys; llama.cpp's schema→GBNF compiler enforces
property *order*; so a plain passthrough changed the grammar and the greedy output
(0/48 identical). `SwitchyardAdapter.build_body` now rewrites every object schema into
an `allOf` form (`schema_compat.key_order_invariant`) that compiles to the identical
grammar text and survives sorting; same-session dev re-run: 48/48 identical output
digests, +11 ms. The direct path is unchanged. See `routing-experiments.md` § R1/R0.1
and `infra/switchyard/README.md`. The routed local arm is interchangeable with the
direct one for routing experiments; case-level comparisons still require one server
session and one request order.

### Deterministic cascade (`services/ai_orchestrator/cascade.py`)
R4. Weak model first; escalate to the strong model on production-available signals
only (no schema-valid output, unsupported claim, any verifier failure — nested policies
`none` ⊂ `parse` ⊂ `verifier`). The decision and its features live on
`Trajectory.router`; the weak stage is scored under `<run>.weak`. Business policy stays
in FIS; the gateway is transport.

### Learned routing (`fis_platform/routing/`, R5)
The production-observable boundary for a learned gate. `features.py` builds a
`RoutingFeatureSnapshot` (schema v1, 58-name explicit allowlist; forbidden names such as
`root_cause`, `split`, `category`, `strict_all_pass` are schema errors; deterministic
digest) from *only* the local stage's invocation, verifier verdict, tool calls, error and
the answer's own label/action — at exactly the R4 decision point in `cascade.py`, before
any strong call. It inherits the routing import ban. `learn.py` is a stdlib logistic /
CART learner with JSON artifacts and stable digests. The scientific pipeline lives in
`scripts/r5_*.py`: dataset (labels join in the analysis layer only; the answer body is
reconstructed from the scorer's `said …` echo for the frozen Suite v3 arms and read from
`learning.model_outputs`, migration 007, from R5 on), TRAIN-only development, offline
DEV/TEST replay with a fail-closed selection/unlock state machine (one selection record
per model, winner-only freeze, TEST unlock bound to the recorded winner + lineage,
append-only), telemetry to `learning.routing_decisions` (migration 008; no gold), oracles
and R4 reproduction. **Known property of this benchmark:** under FIXED_EVIDENCE the
tool-call shape and `input_tokens` are case constants that identify the scenario class
for 45/48 DEV cases, so any learned gain must be read net of the class-identity ceiling.

### Tool broker (`fis_platform/tool_broker/`)
Eight narrow, typed, read-only tools. Parameterised SQL only.

**Ground truth is protected at two layers**: `ToolDefinition.forbidden_schemas` in
Python, and the `fis_tools` Postgres role which holds no grant on `ground_truth` or
`learning`. A leak requires defeating both. Tests assert the database refuses.

**A tool's ordering and column list are part of its contract, not an implementation
detail.** Two classes were unsolvable because of this, and neither looked like a tool
problem:

- `get_ledger_entries` sorted by `posted_at` and did not return `posting_seq`. S07's
  reversal race lives *entirely* in the disagreement between the two — the consumer
  stamps `posted_at` from `occurred_at` on purpose — so the model saw a perfectly
  chronological, net-zero ledger and correctly concluded nothing was wrong. Entries
  are now returned in posting order with `posting_seq` included.
- `get_verifications` was keyed only by `customer_id`, which made `provider_outage`
  undiagnosable in principle: the class is *defined* by clustering across customers.
  v2 takes an optional `vendor` + `window_hours`.

Before adding a scenario class, ask not only whether the evidence exists but whether
any tool call returns it, **in a form that shows the property the class is about**.

### Verifier (`fis_platform/verification/`)
Deterministic only — schema, citation format, citation resolves to a call actually
made, cited IDs actually observed, action code known, confidence calibrated against
work done. Anything needing judgement belongs in the scorer, which has ground truth;
the verifier must work in production where no answer key exists. "Observed" means
returned by a tool this run: values under `*_id` keys, `provider_ref` and (suite v3,
`VERIFIER_VERSION 3`) `idempotency_key` — the key `get_webhook_history` shows the
model was, until then, judged a fabrication when cited. Unit-tested since suite v3
(`tests/test_verifier.py`).

### Orchestrator (`services/ai_orchestrator/`)
Two evidence modes, and the distinction is the backbone of the matrix:
`FIXED_EVIDENCE` (identical bundle to every arm — isolates reasoning) and `AGENTIC`
(model picks its own tools — measures tool strategy plus reasoning).

The fixed-evidence plan is two-phase. Phase one is everything reachable from the
case's subject ids; phase two follows `provider_ref` and `vendor` values discovered
in phase one into the webhook/integration trail and the vendor-clustering query.
Phase two exists because that evidence is not *addressable* until phase one has run —
see § Evidence reachability.

### Prompt registry (`services/ai_orchestrator/prompts.py`)
System prompts are **named, versioned entries in a registry**, selected per run with
`--prompt` and recorded in the run's `config_digest`. Two arms that differ only by
prompt therefore stay distinguishable in the persisted results.

`DEFAULT_PROMPT` is `baseline` and should stay that way: it is byte-identical to the
prompt E2 was baselined with, so a run that forgets `--prompt` is the *control*
rather than silently inheriting whichever intervention won last. The current best
local prompt (`cause_action_directed`) is invoked explicitly.

`CAUSE_TO_ACTION` here mirrors `task-ontology.md` §3 and is pinned to the scorer by
`test_prompt_table_matches_the_rubric` — a prompt that teaches a policy the scorer
does not grade would make its experiment unreadable in the most misleading way: the
variant gets penalised for correctly applying what it was told.

### Scenario generator (`scenarios/generator/`)
Deterministic: no global `random`, no `datetime.now()`. Splits are disjoint seed
ranges so train/test leakage is structurally impossible. Entity IDs embed the seed
(they share one table space across the whole corpus). Suite v3 invariants over every
corpus seed live in `tests/test_scenario_invariants.py` (background posted exactly
once, nothing post-dates the case, deliveries after their events, one injected
defect, S05/S08 amounts vs balances, gold answer scores all-pass); `make
corpus-determinism` regenerates twice and compares the canonical digest.

Since the migration, `build()` is still pure — it produces state rows plus a list of
`ProviderEvent`s — and `run.py` does the I/O: insert state, then publish and drain
one event at a time. **Envelope ids are `uuid5` over the scenario id, not `uuid4`.**
Every row the pipeline writes is named after the envelope that caused it, so a random
id would give the same seed a different delivery/event/entry id set on every
regeneration and leave the manifests pointing at the previous run's rows.

`fis_platform/events/projection.py` replays the real consumer decision functions
without a broker, so a builder can name the rows its events will cause before it
publishes them. Generation asserts projection and live pipeline agree per scenario —
if they ever diverge the manifest would cite ids that do not exist, and the class
would be unwinnable for a reason no score could explain.

### Eval runner (`evals/runner/`)
Commits per case with `UNIQUE(run_id, scenario_id)`, so `--resume` is exact.
Subscription rate limits *will* interrupt a long run; an upstream API error through
the CLI raises so the case is skipped unpersisted and retried on `--resume`.

**Suite identity** (suite v3): `fis_platform/suite.py` `SUITE_VERSION` rides on every
manifest and every `learning.case_scores` row (migration 006 backfilled v1/v2). The
runner refuses a corpus whose suite is not its own and a run id reused across suites;
`runtime_context` records suite/scorer/verifier/ontology/prompt/workflow versions,
`git_head` and the corpus digest (`scripts/corpus_digest.py`,
`scenarios/manifests/corpus_v3.json`). `compare.py` labels every row `[vN]`; every
analysis script refuses to pair runs across suites without `--allow-cross-suite`.
Scenario ids are seed-derived and identical across suites, which is why the column
exists.

---

## Cost and latency accounting

Two decisions that keep the KPI honest:

- **Reference cost, not billed cost.** Subscription marginal cost is ~zero, so
  billed amounts would make every cloud arm look free. `CostRecord` carries both;
  the KPI uses list-price-equivalent recomputed from token counts.
- **Wall-clock and API time recorded separately.** A CLI call pays ~0.6–2.2 s of
  process startup a local HTTP endpoint does not.

---

## Deviations from the guide, and why

| Guide says | We do | Reason |
|---|---|---|
| `platform/` directory | `fis_platform/` | `platform` is a Python stdlib module; a root package of that name shadows it and breaks `uvicorn` |
| Case has `injected_root_cause` | It does not | `cases.cases` is model-visible; storing the label there lets the investigator read the answer |
| `scenario_id` short form | 7-digit full seed | `seed % 100_000` collided train seed 1,000,000 with test seed 3,000,000 |
| Add MinIO when useful | provisioned, unused | trajectories still fit in JSONB |
| NATS for events | **in use** | migration landed 2026-08-15; corpus is suite v2 |
| `get_verifications(customer_id)` | v2 also takes `vendor` + `window_hours` | `provider_outage` is *defined* by clustering across customers. With only customer-keyed tools the class was not hard but impossible — 0% root-cause accuracy, 0.333 recall ceiling. Applies identically to every arm, so E2/E4 stay a controlled comparison |
| One clock base for all scenarios | one 48h slot per scenario | a time-scoped tool would otherwise sweep all 288 scenarios into one answer |
| `get_ledger_entries` ordered by `posted_at` | ordered by `posting_seq`, which is also returned | the consumer stamps `posted_at` from `occurred_at`, so S07's reversal race lives only in posting order. Sorting by event time showed a chronological, net-zero ledger and made `reversal_race` unreachable by correct reasoning — E4 went 0.125 → 1.000 on the class once exposed |
| One system prompt | a versioned registry (`prompts.py`), selected per run | E6 compares prompt variants; the prompt has to be part of `config_digest` or two arms differing only by prompt are indistinguishable in the persisted results |
| Switchyard as an invisible transport hop | invisible **after** the adapter's key-order-invariant schema rewrite (R0.1: 48/48 identical) | 0.2.0 sorts JSON keys; llama.cpp's grammar compiler is order-sensitive (R1: 0/48 identical as shipped). Fixed on the FIS side without touching the suite or the direct path |
| Routing owned by the gateway (strong/weak splitting) | R4's cascade is FIS business policy in the orchestrator; Switchyard fronts the local model only; R5's learned router is offline-replayed FIS policy over `RoutingFeatureSnapshot` | the frontier is a subscription CLI with no OpenAI endpoint, and the gate must read FIS's verifier and the answer's own fields |
| Forbidden claims matched by substring | polarity-aware match, same-sentence, both directions (suite v3, `SCORER_VERSION 3`) | a bare substring counted a *refutation* as an assertion — "the decline was not caused by insufficient funds" scored as the claim `insufficient_funds`, costing the frontier arm 8 points of all-pass for being right. The suite-v2 fix looked back only ("insufficient funds … are all ruled out" still scored), always trimmed two chars off the window, and lost sentence-initial cues; suite v3 fixed all three under one documented rule (`SUITE_V3_RELEASE_CONTRACT.md` § 2C) |
