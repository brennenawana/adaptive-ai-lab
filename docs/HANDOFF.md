# Handoff — 2026-08-19 (R6 modern local refresh done; Suite v3 unchanged; next: R7 reasoning-budget calibration of the frozen Qwen3.8-27B execution system (not started))

Written deliberately at a context boundary. Everything needed to resume is here or
in the other docs. Read `architecture.md` and `task-ontology.md` before coding,
`SUITE_V3_RELEASE_CONTRACT.md` / `SUITE_V3_RELEASE_REPORT.md` for what Suite v3 is,
`R5_EXPERIMENT_CONTRACT.md` / `R5_LEARNED_ROUTING_REPORT.md` for R5,
`R6_EXPERIMENT_CONTRACT.md` / `R6_MODERN_LOCAL_SPECIALIST_REFRESH_REPORT.md` for R6 (and
`learning/registry/r6/` for the cryptographic record), and `OVERNIGHT_STATUS.md`
§ Milestone 6–7 for the live log.

**If you read one thing, read this.** Six times now, a number that looked like model
weakness was a harness or scenario defect instead — unreachable webhook evidence, a
clustering signal generated a month apart, an ordering hazard no tool returned, a
scorer that counted refutations as assertions, background settlements that were never
posted, a declined amount larger than the balance. Each was invisible in the aggregate
and obvious once the *ceiling* was measured or an arm disagreement was reviewed.
Before believing any low score, run `make reachability` and check whether the case
was winnable at all. The strongest tell is an **inversion**: if the weaker arm
outscores the frontier arm on a class, the scenario is rewarding guessing, not
measuring skill. **R5 added a seventh:** a number that looks like a *router learning to
detect failure* can be a router learning *which template it is* — under FIXED_EVIDENCE
four production-observable case constants identify the scenario class for 45/48 cases,
and the labels are class-clustered. Always report a learned gain net of the
class-identity ceiling (`prior_class_ceiling`) and check the leave-one-class-out
per-fold AUC before believing it.

## R5 in one screen (2026-08-18; commits `fc1c18e` … see OVERNIGHT_STATUS M6.9)

- **Built:** `fis_platform/routing/` (`RoutingFeatureSnapshot` v1 — explicit 58-name
  allowlist, forbidden names are schema errors, deterministic digest; stdlib logistic /
  CART learner), migrations 007 (`learning.model_outputs`: the answer body, kept from now
  on) and 008 (`learning.routing_decisions`), `scripts/r5_*.py` (dataset, TRAIN-only
  development, offline DEV/TEST replay with a fail-closed selection/unlock state machine,
  oracles + R4 reproduction, diagnostics), 81 new tests (534 total).
- **Data:** TRAIN trajectories acquired for both local arms under the frozen Suite v3
  configuration (`R5-qwen-train` 41/144, `R5-nemotron-train` 66/144; 288 local calls,
  0 frontier). DEV/TEST answered by replay only. **Both models' TEST is now spent for
  learned routing on Suite v3** (`learning/registry/r5/test_unlock.json`).
- **Result:** primary (leave-one-class-out) protocol — nothing passes the TRAIN gate for
  either model (labels are class-clustered; per-fold LOGO AUC mean 0.39 Qwen / 0.61
  Nemotron). Secondary, deployment-matched protocol (registered before DEV, a-priori
  utilization caps removed for it — both amendments were necessary for any selection):
  routers reach 93–100 % all-pass on DEV at 50–71 % utilization but sit at/near the
  class-identity ceiling; the contract's tie-break ("fewer frontier calls") froze the
  least-escalating survivor for both models. TEST once each: Qwen tree 78.1 % (R4 50.0 %)
  at 57 % utilization — meets the pre-registered reading, which a random escalator of that
  size also meets (p ≈ 0.59); Nemotron `lr_core` 77.1 % (R4 71.9 %) at 33 % — not confirmed.
- **Meaning:** production-observable features carry template difficulty (plus a thin
  said-label layer: S02 `duplicate_webhook_handled`, S12 `kyc_hold`); within-template
  silent failure was not detected and TRAIN gives little power to find a small signal.
  Nemotron is the better routing base (routers above the class ceiling on DEV, within-class
  `content_chars` signal) but its cascade p50 exceeds the frontier's.
- **Interim production gate if one is wanted:** R4 ∨ an `lr_full`-style router
  (families A + D) — it is a template-difficulty prior with a said-label layer; call it that.

---

## R6 in one screen (2026-08-18/19; commits `b2f85d5` … see OVERNIGHT_STATUS M7)

- **Built:** `fis_platform/provenance.py` — pure-Python GGUF header reader + metadata digest,
  self-digested `ModelArtifact` / `RuntimeIdentity` / `GenerationConfig` / `ExecutionSystem`
  records, `R6Registry` (hash-chained append-only per-candidate state logs, `HEAD.json`, run
  ledger, explicit transition table, no env/flag root, reset guards); `scripts/r6_registry.py`;
  `run_eval --candidate` (fail-closed: registry state, committed code tree, one resident
  server, running exe/libs/args/model-SHA bound to the record; local llama.cpp arms now
  require it); `infra/serve-r6.sh`; `scripts/r6_{pilot,metrics,analysis,dev_record,
  accounting,report_tables,runtime_compat}.py`; `fis_platform/r6_gates.py`; ~100 new tests.
- **Provenance closed:** six artifacts pinned by SHA-256 + upstream revision (Qwen3-8B
  official; Nemotron bartowski `be042bfc` — the file was re-uploaded upstream; Qwen3.5-9B
  acquired from `unsloth/Qwen3.5-9B-GGUF@99a1b218`; both `Qwen3.8-27B-*` are **Unsloth
  Qwen3.8, not Bonsai**; Bonsai is the Prism file), two runtimes (upstream `b1-9b05354`,
  Prism `b1-9fcaed7` — Q2_0 block geometry differs, so Bonsai runs only on Prism).
- **TRAIN-only:** 36-case stratified pilot; Q3_K_M beat UD-Q3_K_XL 20 vs 16 (quality-first
  rule) → UD withdrawn; every cap calibration landed at 8192 (truncation recorded);
  Bonsai eligible; probes 12/12 bit-identical (Qwen3.8 across sessions).
- **DEV (48):** Qwen3.5-9B 23 (REJECTED on latency 58 s and 10 cap-hit no-outputs;
  quality clause met), Qwen3.8-27B Q3_K_M 25 (QUALIFIED), Bonsai 21 (QUALIFIED: floor +
  0.61× memory, 0.30× latency of Qwen3.8). Controls: Qwen3-8B 17, Nemotron 23.
- **TEST (96), once each:** Qwen3.8 **47** (Nemotron 48, Qwen3-8B 27) — competitive, not
  better; but silent failures **2** vs 27 (Nemotron) / 47 (Qwen3-8B) — its 47 failures are
  cap truncations at 8192, so the *unchanged* R4 verifier cascade reaches **93/96** (FN 2,
  util 49 %) vs 69/96 on Nemotron. Bonsai 34/96 (41 silent).
  No local arm dominates another; Nemotron keeps 12 unique TEST successes (S10/S06/S11).
- **New inference:** 516 local cases, 0 frontier calls; ~24 h wall. TEST spent
  for `qwen38-27b-q3km` and `bonsai-27b` on Suite v3.
- **Meaning:** the modern strong local's residual failure is a reasoning *budget* (8192
  cap) not a behaviour gap — when it finishes it is right (47/49 on TEST); QLoRA on Qwen3.8 is not the
  next step; neither is a router (Nemotron specialization stays the fallback).

---

## THE NEXT TASK — R7: reasoning-budget calibration of the frozen Qwen3.8-27B execution system (recommended, NOT started)

Exactly one recommendation (R6 report § 11): a pre-registered TRAIN-only study of caps above
8192 (e.g. 12288 at `-c 16384`, or a larger context) and, if the chat template supports it,
a declared thinking-budget toggle, on `qwen3.8-27b-q3_k_m@7f3b845b5638` /
`llama.cpp-upstream-9b05354@0e90f9139596`; select on TRAIN, freeze, one DEV, one TEST,
same Suite v3, same registry/state machine, R4 replay + latency/VRAM reported. Question:
how much of the 49 % truncation converts to passes, at what wall time, and whether the
UD-Q3_K_XL quant (39 % faster, frozen out by the quality-first rule at 8192) becomes the
better operating point once the budget is not binding. No training, no router.

---

## State: Suite v3 released (tag `suite-v3` = `7764601`, unchanged through R5), DEV + TEST baselines done for Qwen, Nemotron, frontier; R5 learned routing done (see above)

**~125 commits, 627 passed + 1 skipped tests green** (`make test`; one live test skips unless
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
| Experiments | Suite v2: E2/E4/E6/E6b/R0–R4/R3/R3b (historical, labelled v2). **Suite v3: DEV + TEST baselines for all three arms, pairwise matrices, unchanged R4 replay** — `SUITE_V3_RELEASE_REPORT.md`; **R5 learned routing** — `R5_LEARNED_ROUTING_REPORT.md`; **R6 modern local refresh** (Qwen3.5-9B, Qwen3.8-27B Q3_K_M, Ternary Bonsai; provenance registry) — `R6_MODERN_LOCAL_SPECIALIST_REFRESH_REPORT.md` |
| Provenance registry (R6) | `learning/registry/r6/` — artifacts (SHA-256 + upstream revision + GGUF metadata digest), runtimes (binary-set digest, CUDA/driver/GPU), generation configs, candidates with hash-chained state logs, run ledger, analyses; `fis_platform/provenance.py`, `scripts/r6_registry.py` |
| Routing gateway / cascade | unchanged: Switchyard 0.2.0 on :4000 (R0.1 key-order fix), `cascade.py` policy `verifier`; **R5** `fis_platform/routing/` (snapshot v1, learner), `scripts/r5_replay.py` (offline replay, selection/unlock state machine), frozen policies under `learning/registry/r5/frozen/` |

Infra: Postgres+pgvector `:5433`, NATS JetStream `:4222`. **No model server is left
running after R6**: the historical 8082/8083 sessions were stopped at the start of R6.2
(their execution systems are recorded in `learning/registry/r6/historical_controls.json`;
the historical arms are replay-only and `run_eval` now refuses to run a local arm without
`--candidate`). R6 candidates are served one at a time with `make r6-serve …`
(ports 8084/8085/8086). Start with `make up-core`.

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

## What Suite v3's baselines said the next task was — R5 (now done)

Suite v3's TEST baselines said the dominant remaining bottleneck was silent-failure
detection (R4 accepts 47/96 Qwen and 26/96 Nemotron verifier-clean wrong answers). R5
tested whether production-observable features could detect them; the answer, and the
one recommendation that follows, are above.

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
make test              # 534 passed + 1 skipped (535 with FIS_LIVE_TESTS=1); test_corpus_live needs the v3 corpus in Postgres
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
| Runs | **suite v3:** `E4-v3-dev`, `V3-qwen-dev`, `V3-nemotron-dev`, `V3-qwen2-dev`, `V3-qwen-96`, `V3-nemotron-96`, `E4-v3-96`, **R5 TRAIN** `R5-qwen-train`, `R5-nemotron-train` (answer bodies in `learning.model_outputs`; decisions in `learning.routing_decisions`). **suite v2 (labelled, do not compare):** `E2-v2-96`, `E4-v2-96`, `E6-cause_action_directed-96`, eight E6/E6b dev runs, `E4-v2-dev`, `R1-*`, `R01-*`, `R4-cascade-verifier-{dev,96}` (+`.weak`), `R3-*`, `R3b-*`, `SMOKE-nemotron*`. **suite v1:** `E2-local-96` |
| Preserved | `learning.*` is never truncated by `make corpus`; prior run scores survive a regeneration and carry their `suite_version` |

Regenerating is `make corpus`, which passes `--reset` on the first split only. It
truncates the scenario tables and purges the JetStream streams — required, because
re-running over an existing corpus collides primary keys and a surviving dedupe
ledger would make S01's *first* delivery look like a duplicate.

## Loose end for the human

A stray `.env` containing a live OAuth token remains at
`c:\Users\4kind-work\code\company-intelligence-platform\.env`. The canonical copy
is in this repo at mode 600 and gitignored. Delete the stray one.
