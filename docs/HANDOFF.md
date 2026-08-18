# Handoff — 2026-08-18 (Suite v3 released and baselined; next: R5 learned/classifier routing (not started))

Written deliberately at a context boundary. Everything needed to resume is here or
in the other docs. Read `architecture.md` and `task-ontology.md` before coding,
`SUITE_V3_RELEASE_CONTRACT.md` for what Suite v3 is, `SUITE_V3_RELEASE_REPORT.md`
for its numbers, and `OVERNIGHT_STATUS.md` § Milestone 5 for the live log.

**If you read one thing, read this.** Six times now, a number that looked like model
weakness was a harness or scenario defect instead — unreachable webhook evidence, a
clustering signal generated a month apart, an ordering hazard no tool returned, a
scorer that counted refutations as assertions, background settlements that were never
posted, a declined amount larger than the balance. Each was invisible in the aggregate
and obvious once the *ceiling* was measured or an arm disagreement was reviewed.
Before believing any low score, run `make reachability` and check whether the case
was winnable at all. The strongest tell is an **inversion**: if the weaker arm
outscores the frontier arm on a class, the scenario is rewarding guessing, not
measuring skill.

---

## State: Suite v3 released (tag `suite-v3`, HEAD `7764601`), DEV + TEST baselines done for Qwen, Nemotron, frontier

**~70 commits, 368 tests green** (`make test`; one live test skips unless
`FIS_LIVE_TESTS=1` — it must never touch :8082 during a paired run; the DB-gated
`test_corpus_live.py` skips unless the corpus in Postgres is this code's suite).

| Piece | State |
|---|---|
| Schemas (6 foundational + 2 FIS) | done, invariant-tested |
| Model gateway (local + claude-CLI) | done, three arms verified end-to-end |
| Tool broker, 8 read-only tools | done; ground truth blocked in Python **and** by DB role |
| Deterministic verifier | done; **unit-tested since suite v3** (`VERIFIER_VERSION 3`: harvests `idempotency_key`) |
| Orchestrator (`investigate`) | done, two evidence modes |
| Scenario generator, 12 classes | done, deterministic, 288 scenarios; **suite v3**: background settlements published and posted, per-event mapper version, S08/S05 amounts vs balances fixed, no direct ledger writes |
| Eval runner + scorers | done, checkpointed/resumable; **suite identity on every row**; scorer polarity rule v3 (`SCORER_VERSION 3`) |
| Event layer | done — generator publishes, consumers materialise; projection == live rows asserted for all 288 |
| Prompt registry (`prompts.py`) | done, 8 named variants; `DEFAULT_PROMPT` is the control; **unchanged in suite v3** |
| Suite identity | `fis_platform/suite.py` `SUITE_VERSION = "3"`; migration 006; `compare.py` labels every row; analysis scripts refuse cross-suite pairs without `--allow-cross-suite`; `scenarios/manifests/corpus_v3.json` is the corpus identity |
| Experiments | Suite v2: E2/E4/E6/E6b/R0–R4/R3/R3b (historical, labelled v2). **Suite v3: DEV + TEST baselines for all three arms, pairwise matrices, unchanged R4 replay** — `SUITE_V3_RELEASE_REPORT.md` |
| Routing gateway / cascade | unchanged: Switchyard 0.2.0 on :4000 (R0.1 key-order fix), `cascade.py` policy `verifier` |

Infra (all healthy): Postgres+pgvector `:5433`, NATS JetStream `:4222`,
Qwen3-8B on llama.cpp `:8082`, Nemotron 3.5 Lightning on `:8083`. Start with
`make up-core`, `make serve-local`, `make serve-nemotron`.

**Suite version is now `3`** (`fis_platform/suite.py`), frozen at tag `suite-v3`
(`7764601`), corpus digest `1e7c5278ba1f4cc1cc96fa8a1f04946ab622270eaba4c5671274c21e9d39e528`
(`scenarios/manifests/corpus_v3.json`). Nothing from v2 is comparable to anything from
v3, and the tooling now says so: `make report` labels rows `[v2]`/`[v3]`, and
`compare_routes` / `model_migration_matrix` / `routing_cascade_report` /
`routing_oracle` / `token_budget_delta` / `r3b_selection_rule` refuse a cross-suite
pair unless `--allow-cross-suite` is given (which prints the caveat).

### What Suite v3 changed (contract § 2; report § 2)

Four benchmark defects found by arm disagreement in R2/R4 and deferred until a
versioned release, plus the bookkeeping to keep suites apart:

1. **Background settlements** — six classes carried S10's unposted-settlement
   signature as ambient noise (`_distractors` settlements were never published). Now
   `_background()` publishes them and the consumers post them; S11's hand-written
   postings go through the same path and `World.add_entry` is gone; background
   precedes the case; the mapper version is recorded per event so S06's bad release
   touches only the injected settlement; S07's deliveries arrive after their events;
   every settlement/reversal event carries a safe key except S02's (whose defect is
   the missing key).
2. **S08/S05 amounts vs balances** — S08's declined amount now fits its balance (v2:
   3 of 24 worlds had it larger, making `insufficient_funds` data-consistent); S05's
   two balances agree.
3. **Forbidden-claim polarity** — one same-sentence rule in both directions
   (`SCORER_VERSION 3`); the recorded false positives replay as refuted, the recorded
   hedges still count.
4. **`idempotency_key`** is an observed id (`VERIFIER_VERSION 3`).

Rubric (root causes, required evidence, actions, forbidden claims), prompts, tools,
evidence plan, schema/grammar, decoding, budgets' default, R4 policy: unchanged.

---

## THE NEXT TASK — R5: learned / classifier routing (recommended, NOT started)

Suite v3's TEST baselines say the dominant remaining bottleneck is **silent-failure
detection**: the unchanged R4 `verifier` gate accepts 47/96 Qwen and 26/96 Nemotron
answers that are verifier-clean and wrong, never escalates unnecessarily, and rescues
almost everything it does escalate (21/22, 21/21). Weak capability is real (both
weak arms ~70% root cause; S01/S11/S12 at 0/8 for both) and Nemotron's +21 TEST
passes cost 3.7× tokens and 4.3× latency, but the gap between delivered (50–72%)
and pair-achievable (99%) is the gate.

R5 = a router over **production-available features only** (parse/verifier signals,
output length/structure, cited-id counts vs bundle size, case category, model
confidence — never evidence recall or any gold field; `router_signals` rejects
`GOLD_FEATURE_NAMES` and `test_routing_no_gold_leak.py` enforces the import ban),
selected on DEV under a pre-registered rule in case counts (strong-call ceiling,
unnecessary-escalation budget), compared with the deterministic `verifier` policy
and a transparent baseline (pivot guide § R5), one TEST look. Weak stage on the
direct path or through Switchyard (interchangeable since R0.1). Suite v3 stays
frozen; any harness defect found on the way is a v4 item, not a patch.

## Numbers — the Suite v3 baselines (report § 4–7)

**DEV (n=48).** Reproducibility gate Qwen A vs B: 47/47 digests, 48/48 outcomes.

| arm | run | all-pass | rc | evidence | verifier | no-output | cap | wall p50/p95 | out tokens |
|---|---|---|---|---|---|---|---|---|---|
| Qwen 4096 | `V3-qwen-dev` | **35.4%** (17) | 62.5% | 0.611 | 68.8% | 9 | 1 | 12.8 / 41.7 s | 65 588 |
| Nemotron 8192 | `V3-nemotron-dev` | **47.9%** (23) | 64.6% | 0.675 | 75.0% | 12 | 10 | 53.2 / 96.0 s | 238 293 |
| frontier | `E4-v3-dev` | **100%** (48) | 100% | 1.000 | 100% | 0 | 0 | 36.9 / 60.1 s | 180 033 |
| Qwen + R4 (replay) | — | **66.7%** at 31.2% strong calls | | | | | | 16.7 s | $0.0608/success |
| Nemotron + R4 (replay) | — | **72.9%** at 25.0% strong calls | | | | | | 54.7 s | $0.0453/success |

Pairwise A/B/C/D: Qwen×Nemotron 13/4/10/21 (B = four Nemotron `length` no-outputs);
Qwen×frontier 17/0/31/0; Nemotron×frontier 23/0/25/0. **No inversion anywhere.**
Silent failures 16 (Qwen) / 13 (Nemotron); every routing false negative is
verifier-clean and wrong on evidence recall or root cause.

**TEST (n=96, once, after the freeze).**

| arm | run | all-pass | rc | evidence | verifier | no-output | cap | wall p50/p95 | out tokens |
|---|---|---|---|---|---|---|---|---|---|
| Qwen 4096 | `V3-qwen-96` | **28.1%** (27) | 70.8% | 0.628 | 77.1% | 13 | 1 | 12.9 / 33.8 s | 129 910 |
| Nemotron 8192 | `V3-nemotron-96` | **50.0%** (48) | 67.7% | 0.713 | 78.1% | 19 | 15 | 55.8 / 94.1 s | 480 810 |
| frontier | `E4-v3-96` | **99.0%** (95; S12-3002011 chose `replay_webhook`) | 100% | 1.000 | 100% | 0 | 0 | 37.6 / 61.0 s | 354 059 |
| Qwen + R4 (replay) | — | **50.0%** at 22.9% strong calls, FN 47 | | | | | | 15.4 s | $0.0513/success |
| Nemotron + R4 (replay) | — | **71.9%** at 21.9% strong calls, FN 26 | | | | | | 56.1 s | $0.0380/success |

Pairwise A/B/C/D: Qwen×Nemotron 21/6/27/42; Qwen×frontier 27/0/68/1;
Nemotron×frontier 48/0/47/1. No inversion. Silent failures 47 / 27.

Rules that carry: select on dev, one test look, one factor per arm, gold labels score a
route but never choose it, same server session + same order for any case-level local
comparison (restart the `--no-mmap` Nemotron endpoint right before its arm and probe
it with a *train* case), `FIS_LIVE_TESTS` off during paired runs, never probe an
endpoint mid-run, per-arm `--max-tokens` chosen and recorded (Qwen 4096, Nemotron 8192).

**Four findings that still matter (Suite v2, unchanged in kind by v3):**

1. Enumerating the hypothesis space is what fixed diagnosis, not the remedy table
   (E6 variant D).
2. The cause→action mapping fixed the action gap completely (`act | rc` 100% on every
   arm since).
3. Evidence recall / citation discipline is the binding constraint for the weak arms
   and the R4 gate cannot see it.
4. Zero forbidden claims from either local model at any accuracy, across every run.

## Deliberately NOT done (do not silently undo these)

1. **The rubric was not widened**, in v2 or v3. Every v3 change is to the world, the
   scorer's polarity mechanics or the verifier's observed-id set; required evidence,
   actions and forbidden claims are byte-identical per class.
2. **S12's retry storm was not made event-driven** (`add_failed_delivery` stays; the
   bus has no poison-message path).
3. **Balances are static snapshots**; nothing derives them from entries.
4. **The scorer still scans the whole serialised result**; scoring `facts[].claim`
   alone is a semantics change deferred on purpose. Hedged assertions count.
5. **No prompt, budget, routing, QLoRA or ontology change** happened in this
   milestone; the R3b verdict stands and was not revisited.
6. **MinIO provisioned but unused.**

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

10. **Background settlements were never posted in six classes** (suite v3 A) — S10's
    fault signature as ambient noise; the frontier's "compound failure" reading of S06
    was defensible. Found by the R2 weak>strong inversion.
11. **S08's declined amount could exceed the balance** (suite v3 B) — the forbidden
    `insufficient_funds` hypothesis was data-consistent in 3 of 24 worlds.
12. **The polarity matcher looked back only, trimmed two chars off every window and
    lost sentence-initial cues** (suite v3 C) — three recorded frontier false positives.
13. **`idempotency_key` was shown by a tool but not harvested as observed** (suite v3
    D) — citing the fact S01 is about read as fabrication.

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
make serve-nemotron    # Nemotron 3.5 Lightning on 8083 beside Qwen (--no-mmap; restart before its arm)
make switchyard-health # {"status":"ok"} + routes: ['fis-local-specialist']
make test              # 368 passed + 1 skipped (369 with FIS_LIVE_TESTS=1); test_corpus_live needs the v3 corpus in Postgres
make reachability      # test 96 + dev 48 cases, 0 classes with an unreachable-evidence cap
make corpus-digest     # canonical corpus digest -> scenarios/manifests/corpus_v3.json
make corpus-determinism# regenerate again and check the digest is identical
make report            # persisted cross-arm comparison, rows labelled [vN]
```

`make reachability` is the one that is easy to skip and expensive to skip. It replays
the real evidence plan through the real broker and prints the recall **ceiling** per
class. Anything below the 0.8 threshold is a harness bug wearing a model's clothes —
that failure mode has now cost this project four separate times.

### What is in the database

| | |
|---|---|
| Corpus | 288 scenarios — 96 test / 48 dev / 144 train, **suite v3** (`ground_truth.scenario_manifests.suite_version = '3'`) |
| Runs | **suite v3:** `E4-v3-dev`, `V3-qwen-dev`, `V3-nemotron-dev`, `V3-qwen2-dev`, `V3-qwen-96`, `V3-nemotron-96`, `E4-v3-96`. **suite v2 (labelled, do not compare):** `E2-v2-96`, `E4-v2-96`, `E6-cause_action_directed-96`, eight E6/E6b dev runs, `E4-v2-dev`, `R1-*`, `R01-*`, `R4-cascade-verifier-{dev,96}` (+`.weak`), `R3-*`, `R3b-*`, `SMOKE-nemotron*`. **suite v1:** `E2-local-96` |
| Preserved | `learning.*` is never truncated by `make corpus`; prior run scores survive a regeneration and carry their `suite_version` |

Regenerating is `make corpus`, which passes `--reset` on the first split only. It
truncates the scenario tables and purges the JetStream streams — required, because
re-running over an existing corpus collides primary keys and a surviving dedupe
ledger would make S01's *first* delivery look like a duplicate.

## Loose end for the human

A stray `.env` containing a live OAuth token remains at
`c:\Users\4kind-work\code\company-intelligence-platform\.env`. The canonical copy
is in this repo at mode 600 and gitignored. Delete the stray one.
