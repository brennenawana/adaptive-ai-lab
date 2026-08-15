# Handoff — 2026-08-15

Written deliberately at a context boundary. Everything needed to resume is here or
in the other four docs. Read `architecture.md` and `task-ontology.md` before coding.

---

## State: the event migration is DONE

**6 commits, 132 tests green.** `git log --oneline` for the trail.

| Piece | State |
|---|---|
| Schemas (6 foundational + 2 FIS) | done, invariant-tested |
| Model gateway (local + claude-CLI) | done, both tiers verified end-to-end |
| Tool broker, 8 read-only tools | done; ground truth blocked in Python **and** by DB role |
| Deterministic verifier | done |
| Orchestrator (`investigate`) | done, two evidence modes |
| Scenario generator, 12 classes | done, deterministic, 288 scenarios |
| Eval runner + scorers | done, checkpointed/resumable |
| **Event layer** | **DONE — all 7 steps. Generator publishes; consumers materialise.** |

Infra (all healthy): Postgres+pgvector `:5433`, NATS JetStream `:4222`,
Qwen3-8B on llama.cpp `:8082`. Start with `make up-core` and `make serve-local`.

**Suite version is now `2`.** The corpus is event-sourced and the tool set gained
`get_verifications` v2. Nothing from v1 is comparable to anything from v2.

### What landed

S01, S02, S06, S07, S09 and S10 publish `ProviderEvent`s and let the consumers decide
what happens. `World.add_event` is deleted; `add_delivery` is now
`add_failed_delivery`, restricted to `retrying`/`failed` because a delivery that
failed is the one thing a consumer cannot record about itself. See
`architecture.md` § "What step 7 actually deleted, and what survives" — two narrow
direct-write paths survive on purpose, and **S12's retry storm is the one genuinely
open item** (it needs poison-message handling in the bus).

Determinism held by making envelope ids `uuid5` over the scenario id. Every
materialised row is named after the envelope that caused it, so `uuid4` would have
given the same seed a different world on every regeneration — and the
`ON CONFLICT DO NOTHING` on manifests would have hidden it as stale evidence ids.
`fis_platform/events/projection.py` replays the real consumer logic without a broker
so a builder can name rows before publishing them; generation asserts the projection
and the live pipeline agree, per scenario.

---

## THE NEXT TASK — E6, the cause→action intervention

The action gap is confirmed and is the largest addressable failure. The intervention
is already written: the cause→action table in `task-ontology.md` §3. Put it in the
investigator system prompt and re-run E2 against suite v2.

E6 sits **above** LoRA on the specialization ladder — run it before considering any
training. It is also the first genuinely fan-out-shaped work in this project (several
prompt variants scored blind against the same frozen suite is a judge panel), so it
is the first place `ultracode` is warranted. See the per-stage table below.

While writing that table: **`replay_webhook` is sanctioned for no current root
cause** — a genuinely-lost-event scenario belongs in the ontology and is not
generated yet. It is therefore a pure distractor, which is very likely why a
name-anchoring model reached for it across three unrelated scenarios. Note that S10
is now *literally* a lost event (never published), but its correct remedy is still
reconciliation, not replay.

---

## Numbers — the current baseline

**Suite v2, both arms on the final event-sourced corpus.** `E2-v2-96`, `E4-v2-96`.

| Metric | E2 local 8B | E4 frontier |
|---|---|---|
| Strict all-pass | 3.1% | 91.7% (**99.0% corrected**) |
| Root-cause accuracy | 16.7% | 99.0% |
| Next-action accuracy | 17.7% | 100% |
| Evidence recall | 74.6% | 100% |
| Verifier pass | 77.1% | 100% |
| Unsupported claims | 13 | 0 |
| Forbidden claims | 0 | 7 — all **false positives** |

**Three findings that matter:**

1. **The local model's action choice is independent of its own diagnosis.** Action
   accuracy is 18.8% when its root cause was right and 17.5% when it was wrong —
   identical. It is not reasoning cause → remedy badly; it is not doing it at all.
   **Evaluate E6 on this conditional, not on aggregate action accuracy**, which
   rises if a model simply guesses common actions.
2. **Evidence is no longer the bottleneck.** E2 sees 74.6% of required evidence and
   still diagnoses 16.7%. E4 reaches 100% on the same bundles, so the ceiling is
   real and the remainder is reasoning.
3. **E4's 7 forbidden claims are a scorer bug, not model behaviour** — the detector
   substring-matches, so "the decline was **not** caused by insufficient funds"
   scores as the claim `insufficient_funds`. Verified by reproduction. Left unfixed
   deliberately; see `experiment-log.md` harness bug #8. **Decide before E6.**

> The earlier "~2× better at diagnosis than remedy" (29.2% vs 13.5%) framing came
> from `E2-local-96`, which is **suite v1 and not comparable** — five classes could
> not be passed by any model. `compare.py` marks it with a †. Do not subtract across
> that line.

---

## Deliberately NOT done (do not silently undo these)

1. **The action rubric was not widened** despite two arguably-defensible E4 answers
   (S09 `contact_identity_vendor`, S10 `inspect_mapping_version`). It was written
   on the merits *before* results existed; changing it after seeing model answers
   is tuning against the test set. Logged as `BAD_RUBRIC` candidates in
   `task-ontology.md` §3 — decide before the next frozen suite version, not after
   seeing more scores. **Still open, and now more tempting**, because the v2
   corpus makes both answers marginally more defensible. Decide it on the merits or
   not at all.
2. **S12's retry storm was not made event-driven.** It needs poison-message handling
   in the bus, which is a new capability rather than a port. `add_failed_delivery`
   rejects non-failure statuses so the gap stays visible instead of quietly widening.
3. **The root-cause and action sets were not touched** by the migration. Suite v2 is
   a corpus + tool change, not an ontology change.
4. **MinIO provisioned but unused** — trajectories still fit in JSONB.

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
5. **Every webhook delivery in the corpus was unaddressable — 0 of 312.** Bug (2)
   added the second hop but nothing ever checked a real address existed on the other
   end. Deliveries were keyed by a `provider_event_id` no state row carried as
   `provider_ref`, so the hop always returned nothing. S01 was capped at 0.25
   evidence recall, S02/S09/S12 at 0.50. Now `make reachability` measures the
   ceiling per class against the built corpus instead of trusting the generator.
6. **S04 was undiagnosable in principle.** `provider_outage` is defined by clustering
   across customers; every tool was keyed by `customer_id`. Root-cause accuracy was
   0.000 for all 8 cases. Fixed by `get_verifications` v2 (vendor + window).
7. **S04's cluster was not a cluster.** `add_customer` used `tick(days=-30)`, which
   rewound the *shared* cursor, so its four "simultaneous" vendor timeouts were
   generated a month apart — and the vendor was drawn per verification, so they were
   often three different vendors. Backdated fields now use `Clock.before()`, which
   does not move the cursor, and the outage vendor is pinned.

8. **`get_ledger_entries` hid `posting_seq`**, which made S07 undiagnosable after the
   migration. The consumer stamps `posted_at` from `occurred_at`, so the reversal
   race lives entirely in posting order — and the tool sorted by `posted_at` and
   never returned the sequence. The model saw a chronological, net-zero ledger and
   correctly concluded nothing was wrong. E4: **0.125 → 1.000** once exposed.
9. **The forbidden-claim detector counts refutations as assertions** (substring
   match). E4's "the decline was *not* caused by insufficient funds" scores as the
   forbidden claim. **Still open — deliberately.** It is a metric about harm; see
   `experiment-log.md`.

> The pattern in (2), (5), (6), (7) and (8) is one bug wearing five costumes:
> **evidence that exists but cannot be reached, or a signal the scenario never
> actually contained.** It reads as a weak model every time. When a class scores near
> zero, check the ceiling before believing the score.
>
> **(8) was found by disagreement between the arms** — E4 scored 12.5% on S07 while
> the *weaker* local model scored higher. An inversion where the stronger arm does
> worse is the signature of a scenario that rewards guessing. Watch for it.

---

## Model, effort, and ultracode — per stage

Guidance, not law. The principle: **match the setting to the shape of the work, not
to how important the project feels.** Most of what remains is execution against a
written spec, which is cheaper than it looks.

| Stage | Model | Effort | Ultracode | Why |
|---|---|---|---|---|
| **Steps 5-7: generator port, regenerate, re-baseline** | Opus 5 | `high` | **off** | Execution against a spec already written here and in `bus.py`. Inherently sequential — fanning out agents risks parallel edits to the same files with no upside. Raise to `xhigh` if the determinism logic stalls; that is the one expensive failure mode. |
| **E6: cause->action prompt variants** | Opus 5 | `high` | **on** | Genuinely fan-out shaped: several prompt variants scored blind against the same frozen suite is a judge panel. This is what workflows are for. |
| **E3 retrieval, E5 router** | Opus 5 | `high` | off | Sequential build-and-measure, same as the migration. |
| **E7: QLoRA** | Opus 5 | `xhigh` | off | Training config is unforgiving and failures are slow to surface. Worth the extra depth. |
| **E8: failure diagnosis** | Opus 5 | `high` | **on** | Classifying ~90 failed cases into the Discovery Controller taxonomy is embarrassingly parallel. |
| **Phase 6: Discovery Controller design** | **Fable 5** | `xhigh` | off | The one genuinely novel design problem left. Not execution — this is where the premium buys something. |

### Reasoning worth keeping

**Opus 5 over Fable 5 by default.** Fable costs roughly double the rate-limit
consumption ($10/$50 vs $5/$25 per MTok equivalent) and takes longer turns. Its
advantage is novel long-horizon reasoning, which almost nothing remaining requires
— the hard thinking is already written down. Reach for Fable when a result is
confusing and needs real diagnosis, or when designing something not yet specified.

**`high`, not `xhigh`, as the default.** `xhigh` is the documented default for
coding on Opus 5 and is a fine one-setting-for-everything choice. But this codebase
is well-specified and Opus 5 is unusually strong at lower effort; `high` is the
balance point. Avoid `max` — it overthinks mechanical refactors.

**Ultracode off unless the work fans out.** It standing-orders multi-agent
workflows. That is right for parallel exploration, adversarial verification and
broad audits; it is wrong for build-verify-fix loops, which are serial. Ultracode
was on for the entire session that built this platform and no workflow was ever
warranted — the two rows marked **on** above are the first places one would be.

Set per session (`cc --model opus --effort high`) or persist in
`.claude/settings.json` so it travels with the repo.

---

## Final paths after the restructure (2026-08-15) — VERIFIED

```
~/projects/fintech-integration-sandbox     <- THE REPO (moved from ~/)
~/infra/llama.cpp-upstream                 llama.cpp build (build-cuda/bin/)
~/infra/models                             GGUF weights
~/infra/cudaenv/lib                        CUDA runtime libs
~/infra/ollama                             alt runtime, unused by FIS
~/archive/                                 the-wall, bonsai-eval, rearch*, hmh
```

Claude Code project key is now
`~/.claude/projects/-home-wall-projects-fintech-integration-sandbox/`
(memories live there).

Verified after the move: model UP on 8082, both containers healthy, **102 tests
passing**, git clean, `.env.bak` removed.

Three things the move broke, all fixed — each failed in a way that did not point
at relocation:

1. **CUDA libs** lived in `~/bonsai-eval/` (an archived project). Now `~/infra/cudaenv`.
2. **`.env` had no trailing newline**, so `cat >>` concatenated `FIS_LLAMA_DIR=...`
   onto the end of the OAuth token, corrupting it to 157 chars. Would have
   surfaced only as an E4 auth failure hours later. **Never `cat >>` into `.env`.**
3. **llama.cpp bakes an absolute RPATH**, so it could not find its own sibling
   `.so` files. Fixed by adding `dirname(BIN)` to `LD_LIBRARY_PATH`.

Also: `.venv` was rebuilt (uv bakes absolute paths, so a move invalidates it), and
editing any file through a Windows UNC path drops the Unix exec bit — modes are
now tracked in git as `100755` and the Makefile invokes `bash` explicitly.

---

## Home-directory restructure — rationale

`/home/wall` had accumulated three unrelated things in one flat directory: shared
AI infrastructure, an earlier unrelated project ("the wall" / bonsai / rearch), and
this project. The user reorganised into `~/infra`, `~/projects`, `~/archive`.

**Why this is recorded:** FIS had a *hidden cross-project dependency*. The local
model server sourced its CUDA runtime libraries from `~/bonsai-eval/cudaenv/lib` —
inside the earlier project. Archiving that directory would have broken the model
server with a bare `libcudart.so.12 not found`, which points nowhere near the
actual cause. If the local model will not start, suspect this first.

`infra/serve-local-model.sh` is now parameterised, defaults unchanged:

| Variable | Default | What it is |
|---|---|---|
| `FIS_LLAMA_DIR` | `~/llama.cpp-upstream` | llama.cpp build (needs `build-cuda/bin/llama-server`) |
| `FIS_MODELS_DIR` | `~/models` | GGUF weights |
| `FIS_CUDA_LIB` | `~/bonsai-eval/cudaenv/lib` | CUDA runtime libs |

After relocation, set these in `.env` (gitignored) or export them. The script now
warns if `FIS_CUDA_LIB` does not exist rather than failing obscurely later.

**Two consequences of moving the repo itself** (if `~/fintech-integration-sandbox`
moved under `~/projects/`):

1. **`.venv` breaks.** uv venvs bake absolute paths into their scripts. Recreate:
   `uv venv --python 3.12 && uv pip install -e ".[dev]"` — or reinstall the
   packages listed in `pyproject.toml`.
2. **The Claude Code project key changes**, so the memory directory moves with it:
   `~/.claude/projects/-home-wall-fintech-integration-sandbox/` becomes
   `-home-wall-projects-fintech-integration-sandbox`. Memories do not follow
   automatically.

Also relocated: `~/ollama` sets `OLLAMA_MODELS=$HOME/ollama/models` in its own
`env.sh`, which needs updating if that directory moved. Not used by FIS.

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
