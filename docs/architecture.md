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
| 9000/9001 | MinIO | `artifacts` profile, not yet used |
| **5432** | **pre-existing `thewall` Postgres** | **not ours — do not touch** |
| **6379** | **pre-existing Redis** | **not ours** |
| **8080/8081** | **Bonsai / Qwen3.8-27B** | **not ours** |

---

## Event-driven requirement (NORMATIVE)

**Status: required, not yet implemented. No new scenario class or experiment arm
ships until the event layer lands.**

The guide names event-driven workflows and eventual consistency as core things the
sandbox must teach. Today the scenario generator writes rows directly into every
service schema, which means the interesting failures are **depicted rather than
produced**:

- S01/S02 (duplicate delivery, idempotency) are hand-authored row pairs. Nothing
  actually attempts deduplication, so nothing can actually fail to.
- S07 (reversal race) is hand-authored out-of-order timestamps. No real ordering
  hazard exists.
- S09 (stale mapping) is a hand-written mismatch between `raw_payload` and
  `normalized_state`, rather than the output of a mapper that is genuinely stale.

That is a meaningful gap. A scripted race teaches the *shape* of the bug; an
emergent one teaches the mechanism, and only the emergent one can surprise us.

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

### Migration plan

| Step | Change |
|---|---|
| 1 | `fis_platform/events/` — JetStream connection, publisher, typed envelopes |
| 2 | Stream provisioning in `make up-core` (idempotent) |
| 3 | `integration-service` consumer: idempotency + versioned mapper |
| 4 | `ledger-service` consumer: posts entries from normalized events |
| 5 | Generator publishes instead of inserting for webhook/settlement paths |
| 6 | Regenerate the corpus; re-baseline every arm (results are not comparable across this change) |
| 7 | Delete the direct-insert path so it cannot silently come back |

Scenarios that are genuinely event-driven after this: S01, S02, S06, S07, S09, S10.
S03/S04/S05/S08/S11 stay largely state-based, which is correct — not every
operational problem is an event-ordering problem.

---

## Components

### Model gateway (`fis_platform/model_gateway/`)
One `GenerationRequest`/`GenerationResponse` contract; the provider is a registry
entry. **This is what makes E2/E4/E5 a controlled comparison** — the arms differ by
one string (`model_ref`), not by call path.

Adapters: `local.py` (OpenAI-compatible HTTP, GBNF-constrained, greedy + seeded —
the reproducible baseline), `claude_cli.py` (subscription CLI as a backend).

Two transport quirks handled here rather than leaking upward:
- llama.cpp's schema→GBNF compiler rejects `minLength`/`maxLength`; `schema_compat.py`
  strips them for the grammar while the verifier still enforces them.
- Claude Code invokes an internal side model on every call; `_extract_usage` filters
  `modelUsage` to the canonical model so per-arm cost is not inflated.

### Tool broker (`fis_platform/tool_broker/`)
Eight narrow, typed, read-only tools. Parameterised SQL only.

**Ground truth is protected at two layers**: `ToolDefinition.forbidden_schemas` in
Python, and the `fis_tools` Postgres role which holds no grant on `ground_truth` or
`learning`. A leak requires defeating both. Tests assert the database refuses.

### Verifier (`fis_platform/verification/`)
Deterministic only — schema, citation format, citation resolves to a call actually
made, cited IDs actually observed, action code known, confidence calibrated against
work done. Anything needing judgement belongs in the scorer, which has ground truth;
the verifier must work in production where no answer key exists.

### Orchestrator (`services/ai_orchestrator/`)
Two evidence modes, and the distinction is the backbone of the matrix:
`FIXED_EVIDENCE` (identical bundle to every arm — isolates reasoning) and `AGENTIC`
(model picks its own tools — measures tool strategy plus reasoning).

### Scenario generator (`scenarios/generator/`)
Deterministic: no global `random`, no `datetime.now()`. Splits are disjoint seed
ranges so train/test leakage is structurally impossible. Entity IDs embed the seed
(they share one table space across the whole corpus).

### Eval runner (`evals/runner/`)
Commits per case with `UNIQUE(run_id, scenario_id)`, so `--resume` is exact.
Subscription rate limits *will* interrupt a long run.

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
| NATS for events | **provisioned, unused** | **being fixed — see requirement above** |
