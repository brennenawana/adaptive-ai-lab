# Handoff — 2026-08-15

Written deliberately at a context boundary. Everything needed to resume is here or
in the other four docs. Read `architecture.md` and `task-ontology.md` before coding.

---

## State: working, coherent, mid-migration

**5 commits, 102 tests green.** `git log --oneline` for the trail.

| Piece | State |
|---|---|
| Schemas (6 foundational + 2 FIS) | done, invariant-tested |
| Model gateway (local + claude-CLI) | done, both tiers verified end-to-end |
| Tool broker, 8 read-only tools | done; ground truth blocked in Python **and** by DB role |
| Deterministic verifier | done |
| Orchestrator (`investigate`) | done, two evidence modes |
| Scenario generator, 12 classes | done, deterministic, 288 scenarios |
| Eval runner + scorers | done, checkpointed/resumable |
| **Event layer** | **envelopes + bus + integration consumer + ledger consumer done; generator NOT yet ported** |

Infra (all healthy): Postgres+pgvector `:5433`, NATS JetStream `:4222`,
Qwen3-8B on llama.cpp `:8082`. Start with `make up-core` and `make serve-local`.

---

## THE NEXT TASK — finish the event migration

`architecture.md` declares this **normative**: no new scenario class or experiment
arm ships until it lands. Steps 1–4 are done. Remaining:

**5. Port the generator to publish instead of insert.**
`scenarios/generator/world.py` currently appends rows to lists which
`run.py::write()` INSERTs directly. For the webhook/settlement/verification paths,
publish a `ProviderEvent` through `EventBus.publish_provider_event()` and let
`IntegrationConsumer` → `LedgerConsumer` materialise the rows.

Keep determinism: publish, then drain to consumer acknowledgement before the next
publish (`EventBus.drain()`). Do **not** fire-and-forget — see the reasoning in
`bus.py`'s docstring. Races (S07) come from publishing in a deliberately inverted
order, never from timing.

Scenarios that become genuinely event-driven: **S01, S02, S06, S07, S09, S10.**
S03/S04/S05/S08/S11 stay state-based, which is correct.

**6. Delete the direct-insert path** so it cannot silently return.

**7. Regenerate the corpus and re-baseline E2 and E4 together.**

---

## Numbers so far, and their status

**E2 at n=96 (`run_id=E2-local-96`) — PRE-MIGRATION REFERENCE ONLY.**
Do not compare anything post-migration to it; the corpus changes.

| Metric | value |
|---|---|
| Strict all-pass | 5.2% |
| Root-cause accuracy | 29.2% |
| Next-action accuracy | 13.5% |
| Verifier pass | 64.6% |
| Forbidden claims | 0 |

**The finding that matters:** the model is ~2× better at diagnosis (29.2%) than at
remedy (13.5%). Confirmed at n=96 after an n=12 run suggested it. It is frequently
wrong but never *dangerous* — zero forbidden claims in 96 cases.

An earlier n=12 run showed 41.7% root-cause. That was small-sample optimism; one
case was worth 8.3 points.

---

## Deliberately NOT done (do not silently undo these)

1. **E4 was not re-run at n=96.** The migration invalidates it. Baseline both arms
   once, together, on the final corpus.
2. **The action rubric was not widened** despite two arguably-defensible E4 answers
   (S09 `contact_identity_vendor`, S10 `inspect_mapping_version`). It was written
   on the merits *before* results existed; changing it after seeing model answers
   is tuning against the test set. Logged as `BAD_RUBRIC` candidates in
   `task-ontology.md` §3 — decide before the next frozen suite version, not after
   seeing more scores.
3. **MinIO provisioned but unused** — trajectories still fit in JSONB.

---

## After the migration: E6

Targets the confirmed action gap, and sits **above** LoRA on the specialization
ladder — run it before considering any training.

The intervention is already written: the cause→action table in
`task-ontology.md` §3. Put it in the investigator system prompt and re-run E2.

While writing that table I noticed **`replay_webhook` is sanctioned for no current
root cause** — a genuinely-lost-event scenario belongs in the ontology and is not
generated yet. It is therefore a pure distractor, which is very likely why a
name-anchoring model reached for it across three unrelated scenarios.

---

## Environment gotchas that cost real time

- **Windows `sudo` ≠ WSL `sudo`.** Different programs. Linux commands must run
  inside WSL. `wsl -d Ubuntu-24.04 -u root -- <cmd>` gives passwordless root.
- **Running from Windows:** write WSL commands to a script file first — inline
  `$VARIABLES` are eaten by the interop layer. Running Claude Code *from WSL*
  removes this entirely and is recommended.
- **`command -v python3` succeeds on Windows but the binary is a Store stub** that
  refuses to run. Existence ≠ executability; `.claude/hooks/_resolve-python.sh`
  executes each candidate to check.
- **llama.cpp's GBNF compiler rejects `minLength`/`maxLength`** → 400. Stripped in
  `model_gateway/schema_compat.py`; the verifier still enforces them.
- **`npm -g` from WSL installs to the *Windows* prefix** if WSL has no native node.
- Ports **5432 / 6379 / 8080 / 8081** belong to other projects. Do not touch.

## Harness bugs already found and fixed — do not reintroduce

Each was initially mistakable for model weakness:

1. Verifier rejected citations naming the *tool* rather than the service — failed
   11 of 12 correct citations.
2. Fixed-evidence plan never called `get_webhook_history`, making required evidence
   unreachable for four scenario classes. Fixing (1)+(2) moved root-cause accuracy
   16.7% → 41.7%.
3. `scenario_id` was `seed % 100_000`, colliding train seed 1,000,000 with test seed
   3,000,000 — the same primary key for a train and a test scenario.
4. Reversal-race detector ordered by `entry_id` (a random uuid hex), so it silently
   reported no anomalies. Fixed with `ledger.entries.posting_seq`.

---

## Verify everything is alive

```bash
cd ~/fintech-integration-sandbox
make ps                # fis-postgres + fis-nats healthy
make model-health      # {"status":"ok"}
make test              # 102 passed
make report            # persisted cross-arm comparison
```

## Loose end for the human

A stray `.env` containing a live OAuth token remains at
`c:\Users\4kind-work\code\company-intelligence-platform\.env`. The canonical copy
is in this repo at mode 600 and gitignored. Delete the stray one.
