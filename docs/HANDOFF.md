# Handoff — 2026-08-17 (R0–R2, R0.1, R4 done; R3 Nemotron benchmarked — negative under the frozen budget)

Written deliberately at a context boundary. Everything needed to resume is here or
in the other docs. Read `architecture.md` and `task-ontology.md` before coding, and
`routing-experiments.md` + `OVERNIGHT_STATUS.md` for what the overnight run found.

**If you read one thing, read this.** Five times now, a number that looked like model
weakness was a harness or scenario defect instead — unreachable webhook evidence, a
clustering signal generated a month apart, an ordering hazard no tool returned, a
scorer that counted refutations as assertions. Each was invisible in the aggregate
and obvious once the *ceiling* was measured. Before believing any low score, run
`make reachability` and check whether the case was winnable at all. The strongest
tell is an **inversion**: if the weaker arm outscores the frontier arm on a class,
the scenario is rewarding guessing, not measuring skill. That is how the S07 bug was
found.

---

## State: migration done, E6 done, E6b closed, routing baseline done (R0–R2, R0.1, R4)

**~46 commits, 197 tests green** (`make test`; one live test skips unless
`FIS_LIVE_TESTS=1` — it must never touch :8082 during a paired run). `git log
--oneline` for the trail.

| Piece | State |
|---|---|
| Schemas (6 foundational + 2 FIS) | done, invariant-tested |
| Model gateway (local + claude-CLI) | done, both tiers verified end-to-end |
| Tool broker, 8 read-only tools | done; ground truth blocked in Python **and** by DB role |
| Deterministic verifier | done |
| Orchestrator (`investigate`) | done, two evidence modes |
| Scenario generator, 12 classes | done, deterministic, 288 scenarios |
| Eval runner + scorers | done, checkpointed/resumable; `--prompt` selects a variant and lands in `config_digest` |
| **Event layer** | **DONE — all 7 steps. Generator publishes; consumers materialise.** |
| Prompt registry (`prompts.py`) | done, 8 named variants; `DEFAULT_PROMPT` is the control |
| Experiments | E2, E4 baselined on suite v2. **E6 done** (variant C is local best). **E6b closed — negative.** E3/E5/E7/E8 open |
| **Routing track (R-series)** | **R0 frozen** (`weak-baseline-v1` = variant C on `f48039a`), **R1 measured**, **R0.1 fixed** (Switchyard passthrough now 48/48 identical to direct), **R2 done** (oracle map on dev), **R4 done** (deterministic cascade, policy `verifier`, dev + one test confirmation), **R3 done** (Nemotron 3.5 Lightning compatible and benchmarked on dev; does not qualify under the frozen 4 096-token budget; test untouched). R5 not started. `routing-experiments.md` |
| Candidate weak arm | `nemotron-lightning` registry entry, `infra/serve-nemotron.sh` (8083, `--fit on --no-mmap`, same llama.cpp build), `scripts/model_migration_matrix.py`, `scripts/model_throughput_probe.py`, make `serve-nemotron` / `eval-r3-dev` / `r3-compare` |
| Routing gateway | NeMo Switchyard 0.2.0 on :4000 (`make serve-switchyard`), registry entry `local-specialist-switchyard` with the key-order-invariant schema rewrite, `RoutingRecord` on every routed invocation, gold-leak guards tested |
| Deterministic cascade | `services/ai_orchestrator/cascade.py`, `run_eval --escalate-to`, `scripts/routing_cascade_report.py` (replay + live), make `r4-replay` / `eval-r4-dev` / `r4-report` / `eval-r4-confirm` |

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

## THE NEXT TASK — R3b: the token-budget factor, both weak arms, dev only. Then suite v3.

R3 answered its question with a twist. Nemotron 3.5 Lightning (IQ4_XS, same llama.cpp,
hybrid GPU/RAM, ~91 tok/s with `--no-mmap`) removes ~80% of Qwen's silent
valid-but-wrong answers (23 → 4 on dev) and, on the cases it finishes, passes 63%
vs Qwen's 29% — but under the frozen `max_tokens 4096` it is still inside `<think>`
on 29/48 cases and produces nothing. As a weak-only arm it is therefore *worse*
(25.0% vs 29.2%); as the weak stage of the unchanged R4 cascade it reaches 89.6%
(frontier 91.7%) by sending 67% of cases to the frontier, at $0.087 per success vs
Qwen+R4's $0.055. It failed 4 of the 6 pre-registered criteria; test was not run.

The one confound is the decoding budget. R3b: the *same* paired design (Qwen A →
Nemotron → Qwen B, one server session per model, priming, same order, dev only) with
`max_tokens 8192` for **both** arms — one factor, nothing else changed — then the
migration matrix and the R4 replay again, with a pre-registered rule written before
the run. `--reasoning-budget` and Nemotron-specific prompts remain off the table (they
change the task / add a factor). Keep `--no-mmap` (quality-neutral, digests identical).

Only after R3b is the model comparison a model comparison; then **suite v3** as a
deliberate release re-baselining Qwen, Nemotron and the frontier together (backlog:
background settlements never posted in 7 classes; S08 declined amount > balance;
`idempotency_key` not an observed id; post-positioned refutation cue).

Rules that carry: select on dev, one test look, one factor per arm, gold labels score a
route but never choose it, same server session + same order for any case-level local
comparison (design A: keep both endpoints alive), `FIS_LIVE_TESTS` off during paired
runs, never probe an endpoint mid-run.

## Numbers — the current baseline

**Suite v2.** `E2-v2-96` (control), `E6-cause_action_directed-96` (current best
local), `E4-v2-96` (frontier ceiling). All 96 test scenarios, `FIXED_EVIDENCE`.

| Metric | E2 local | **E6 local (C)** | E4 frontier |
|---|---|---|---|
| Strict all-pass | 3.1% | **29.2%** | 99.0% |
| Root-cause accuracy | 16.7% | **65.6%** | 100% |
| act \| rc | 18.8% | **100%** | 100% |
| Required-evidence recall | 74.6% | **61.1%** ⚠ | 100% |
| Verifier pass | 77.1% | 78.1% | 100% |
| Forbidden claims | 0 | 0 | 1 (a false positive) |

Run with `--prompt cause_action_directed`. `DEFAULT_PROMPT` stays `baseline` on
purpose, so a run without `--prompt` is still the control.

**Routing numbers (dev, R2, `E6-C-directed-dev` × `E4-v2-dev`, n=48):**
weak-pass/strong-pass 16 · weak-fail/strong-pass 28 · weak-pass/strong-fail 1 ·
both-fail 3 → safe-local 35.4%, rescueable 58.3%, oracle hybrid 93.8% (strong-only
91.7%), oracle strong-call minimum 64.6%, cascade cost −35%. All four disagreements
reviewed: two harness defects, two scenario-realism issues (see next task).

**R4 deterministic cascade (policy `verifier`, frozen on dev):** dev 50.0% all-pass at
22.9% strong calls; **test 49.0%** (`R4-cascade-verifier-96`) at 21.9%, rescue 19/21,
0 unnecessary escalations, 47/96 verifier-clean weak failures accepted, cost per
success $0.046 vs $0.097 strong-only, wall p50 14.5 s vs 38.2 s. Details in
`routing-experiments.md` § R4.

**R3 Nemotron 3.5 Lightning (dev, `R3-nemotron-dev` vs `R3-qwen-dev`, n=48):** all-pass
25.0% vs 29.2%; 29 length-capped no-outputs; silent failures 4 vs 23; migration
A/B/C/D 4/10/8/26; Nemotron+R4 89.6% at 66.7% strong calls ($0.0868/success) vs
Qwen+R4 45.8% at 22.9% ($0.0545). Not adopted; test untouched. `routing-experiments.md`
§ R3.

**Four findings that matter:**

1. **Enumerating the hypothesis space is what fixed diagnosis, not the remedy
   table.** Variant D (the twelve cause labels, no actions) recovered essentially all
   the diagnostic gain — 60.4% against a control's 18.8% — and none of the action
   gain. The label set was already enforced by the response grammar, so an invalid
   cause could never be *emitted*; a grammar does nothing for what is *considered*.
   Without variant D this would have been recorded as "the cause→action table triples
   diagnosis", which is false.
2. **The cause→action mapping fixed the action gap completely.** `act | rc` went
   18.8% → 100%: every case E6 diagnoses correctly now gets a sanctioned remedy.
   Note this metric now measures lookup compliance rather than judgement — by
   design — so it is not comparable to E2's.
3. **Evidence recall is now the binding constraint.** It *fell* 74.6% → 61.1%, and
   35 of the 63 cases E6 diagnoses correctly fail on evidence alone. Diagnosis was
   the bottleneck this morning; citation is the bottleneck now. See the next task.
4. **Zero forbidden claims from the local model at any accuracy**, across every run.
   Frequently wrong, never dangerous.

> The old "~2× better at diagnosis than remedy" (29.2% vs 13.5%) framing came from
> `E2-local-96`, which is **suite v1 and not comparable** — five classes could not be
> passed by any model. `compare.py` marks it with a †. Do not subtract across it.

## Deliberately NOT done (do not silently undo these)

1. **The action rubric was not widened, and the review is CLOSED.** Two E4 answers
   on suite v1 looked defensible but scored wrong (S09 `contact_identity_vendor`,
   S10 `inspect_mapping_version`). On v2 neither recurred — E4 chose a sanctioned
   action in 96/96 — so both were artefacts of the v1 corpus, where those classes had
   unreachable evidence. Closed as no change in `task-ontology.md` §3. Note what did
   not happen: it was not widened because a model disagreed, and it was not narrowed
   because one later agreed.
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
- **`make serve-local` did not read `.env`** until 2026-08-15. The script honours
  `FIS_LLAMA_DIR`/`FIS_MODELS_DIR`/`FIS_CUDA_LIB` but never loaded the file this
  doc tells you to put them in, so it worked only in a shell that already had them
  exported and failed after any restart with `model not found: /home/wall/models/...`
  — naming the PRE-restructure path, which points nowhere near the cause. Fixed; it
  now reads `FIS_` keys only, and only when unset.
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
9. **The forbidden-claim detector counted refutations as assertions** (substring
   match). E4's "the decline was *not* caused by insufficient funds" scored as the
   forbidden claim `insufficient_funds`, costing 8 points of all-pass for being
   right. Now polarity-aware, with the lookback stopping at a sentence boundary so a
   refutation cannot launder a later assertion. E4 re-ran at **99.0%**, exactly the
   corrected figure predicted. **One residual false positive remains** (1 of 96); the
   scorer now logs an excerpt of the matched text so the next one is auditable
   without re-running a non-deterministic case.

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
| ~~Steps 5-7: generator port~~ | — | — | — | **Done 2026-08-15.** The prediction held: sequential, no fan-out warranted. What cost the time was not the port but four latent harness bugs it exposed. |
| ~~E6: cause->action prompt variants~~ | Opus 5 | `high` | off in practice | **Done.** Predicted as the first place a workflow would pay. It was not: four variants run **sequentially** against one local model, ~10 min each, and each variant's design depended on the previous result — D exists because B/C were confounded, H exists because E/F/G failed. A fan-out would have run the wrong variants in parallel. Fan-out suits independent work; this was a chain. |
| ~~E5 router~~ → **R4 deterministic cascade** (next) | Opus 5 | `high` | off | Sequential build-and-measure. R2 has already sized the opportunity; R4 uses only production-available signals (parse, verifier, unsupported claims) — evidence recall is eval-only and may score a route, never choose it. |
| **E3 retrieval** | Opus 5 | `high` | off | Demoted. It was queued to help diagnosis; diagnosis is no longer the loss. |
| **E7: QLoRA** | Opus 5 | `xhigh` | off | Training config is unforgiving and failures are slow to surface. **Do not start it yet** — two prompt changes moved the local arm 18.8% → 65.6% on root cause, and the remaining headroom is much smaller than it was. |
| **E8: failure diagnosis** | Opus 5 | `high` | **on** | The one place fan-out still looks right: classifying failed cases into the Discovery Controller taxonomy is genuinely independent per case. |
| **Phase 6: Discovery Controller design** | **Fable 5** | `xhigh` | off | The one genuinely novel design problem left. Not execution — this is where the premium buys something. |

**Revised view on ultracode, from having done E6.** The old note said prompt variants
were "a judge panel — what workflows are for". Running it showed otherwise: the value
was in *reading each result and choosing the next variant*, which is serial by
construction. Fan-out is for work that is independent in advance. An experiment where
each cell is designed from the last one is not, however parallel the runs look.

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
passing** (that was the count on 2026-08-15 before the event migration; 160 after it,
187 after the routing foundation on 2026-08-16), git clean, `.env.bak` removed.

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
cd ~/projects/fintech-integration-sandbox
make ps                # fis-postgres + fis-nats healthy
make serve-local       # reads FIS_* from .env; prints "UP model=... port=8082"
make model-health      # {"status":"ok"}
make serve-switchyard  # Switchyard on 4000, passthrough to 8082 (optional)
make serve-nemotron    # Nemotron 3.5 Lightning on 8083 beside Qwen (R3 candidate; --no-mmap)
make switchyard-health # {"status":"ok"} + routes: ['fis-local-specialist']
make test              # 196 passed + 1 skipped (197 with FIS_LIVE_TESTS=1)
make reachability      # 96 cases, 0 classes with an unreachable-evidence cap
make report            # persisted cross-arm comparison
```

`make reachability` is the one that is easy to skip and expensive to skip. It replays
the real evidence plan through the real broker and prints the recall **ceiling** per
class. Anything below the 0.8 threshold is a harness bug wearing a model's clothes —
that failure mode has now cost this project four separate times.

### What is in the database

| | |
|---|---|
| Corpus | 288 scenarios — 96 test / 48 dev / 144 train, suite v2 |
| Runs | `E2-local-96` (**suite v1, do not compare**), `E2-v2-96`, `E4-v2-96`, `E6-cause_action_directed-96`, eight E6/E6b dev runs, `E4-v2-dev` (strong arm on dev, R2), `R1-*` (R1), `R01-*` (R0.1), `R4-cascade-verifier-{dev,96}` (+`.weak`), `R3-qwen-dev`, `R3-nemotron-dev`, `R3-qwen2-dev` (R3), plus `SMOKE-*` |
| Preserved | `learning.*` is never truncated by `make corpus`; prior run scores survive a regeneration |

Regenerating is `make corpus`, which passes `--reset` on the first split only. It
truncates the scenario tables and purges the JetStream streams — required, because
re-running over an existing corpus collides primary keys and a surviving dedupe
ledger would make S01's *first* delivery look like a duplicate.

## Loose end for the human

A stray `.env` containing a live OAuth token remains at
`c:\Users\4kind-work\code\company-intelligence-platform\.env`. The canonical copy
is in this repo at mode 600 and gitignored. Delete the stray one.
