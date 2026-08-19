# Overnight status — routing-foundation milestone (R0–R2)

Live log for the autonomous run started 2026-08-16. Newest entries at the bottom of
each section; the **Morning summary** at the end is rewritten last.

Milestone definition: `docs/FIS_MSI_Pivot_Guide_Switchyard_Nemotron.html` — close
E6b, freeze the local baseline (R0), Switchyard passthrough equivalence (R1), paired
weak/strong oracle map on dev (R2). R3+ (Nemotron, cascade, learned routing, QLoRA)
are explicitly out of scope.

---

## 0. Reconciliation of repository state (turn 1)

Read: pivot guide, `HANDOFF.md`, `architecture.md`, `experiment-log.md`, Makefile,
git log, persisted runs (`learning.case_scores`), `evals/reports/`.

| Claim in prose | Repository / artifact state | Verdict |
|---|---|---|
| Guide: "E6b is the only experiment in flight" (written at `da35ab3`) | Commits `8eedc8b`, `aca5731` after it: E6b dev sweep is **complete** — 4 cells (E, F, G, H) all persisted, n=48 each, run ids `E6b-E-citelast-dev`, `E6b-F-elim-dev`, `E6b-G-both-dev`, `E6b-H-subject-dev` | prose stale; **E6b already closed as a negative result** |
| Guide: "select the E6b winner on dev and run the single test confirmation" | Pre-registered rule (adopt H only if evidence ≥ C+5 **and** rc ≥ C−3) was applied; H returned −5.9 / −6.3. Winner is the **control, variant C**, whose one test confirmation already exists (`E6-cause_action_directed-96`, n=96) | no new test run is warranted — running one would be a second look at test for the same variant |
| Guide: "the one unconfirmed figure is the post-E6b full-suite test count" | `HANDOFF.md` says 160; needed confirming | confirmed this turn, see §1 |
| HANDOFF: "26 commits" | `git log` at start: 27 commits, HEAD `8599326` | trivially stale |
| Guide R2: "join weak and strong results on dev" | Local dev runs exist (E6-C-directed-dev etc.). **No frontier run on dev exists** — E4 was only run on test (`E4-v2-96`) | must run E4 on dev once (measurement of the strong arm, not selection on test) — started this turn |

Infra at start: `fis-postgres` healthy (5433), `fis-nats` healthy (4222), llama.cpp on
8082 `{"status":"ok"}`, GPU RTX 5080 Laptop 16 GB with 7.8 GB in use (the 8B model).
`gateway_smoke.py`: local and claude-frontier both answered schema-valid.

## 1. Confirmations at cutover (turn 1)

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest tests/ -q` | **160 passed** in 0.38 s (0 skipped; `--co` collects 160) |
| `scripts/evidence_reachability.py --split test` | 96 cases, 12/12 classes ceiling 1.000, **0 capped classes** |
| `scripts/evidence_reachability.py --split dev` | 48 cases, 12/12 classes ceiling 1.000, **0 capped classes** |
| `scripts/gateway_smoke.py` | local: schema-valid, 130/646 tok, 7.3 s; frontier: schema-valid, 8.1 s |

The previously-unconfirmed passing-test count is therefore **160/160 at commit
`8599326`** (pre-routing). It is re-recorded after each commit below.

## 2. E6b closure — decision record (criterion 1)

Closed on the recorded dev results, no re-run:

| Variant | rc | evidence | ≥0.8 | all-pass |
|---|---|---|---|---|
| C control (`E6-C-directed-dev`) | 62.5% | 70.8% | 22 | 35.4% |
| E cite_last | 56.3% | 60.1% | 15 | 27.1% |
| F eliminative | 54.2% | 67.5% | 20 | 31.3% |
| G both | 62.5% | 67.4% | 22 | 35.4% |
| H subject | 56.3% | 64.9% | 21 | 39.6% |

Winner on dev = **C** (control). C's single test confirmation is
`E6-cause_action_directed-96` (already run 2026-08-16 00:55–01:21 UTC). **No further
test run.** `DEFAULT_PROMPT` stays `baseline`.

## 3. R0 — frozen local baseline `weak-baseline-v1` (criterion 2)

| Field | Value |
|---|---|
| Git commit of the code that produced the run | **`f48039a`** (run 2026-08-16 00:55–01:21 UTC sits between `f48039a` 00:56 UTC and `1c3e2d3` 01:22 UTC, which only added docs/report). Verified: `evals/scorers/score.py`, `services/ai_orchestrator/investigate.py`, `fis_platform/`, `schemas/` are byte-identical from `f48039a` to `8599326`; `prompts.py` only gained variants E–H, and `PROMPTS["cause_action_directed"]` is byte-identical (2 553 chars, sha256 `40111d53f60e0a37…`) |
| Run id | `E6-cause_action_directed-96` |
| Suite | `fis-eval` **v2**, corpus 288 (96 test / 48 dev / 144 train), event-sourced, uuid5 envelopes |
| Split | test (96 = 8 × 12 classes) |
| Model | `local-specialist` → Qwen3-8B, Q4_K_M, llama.cpp CUDA, greedy (`temperature 0`, `seed 42`), `--parallel 1`, ctx 16 384, `max_tokens 4096`, GBNF-constrained (`response_format json_schema`, minLength/maxLength stripped) |
| Prompt variant | `cause_action_directed` (variant C), `PROMPT_VERSION=1`, `config_digest=local-specialist\|fixed_evidence\|cause_action_directed` |
| Evidence mode | `FIXED_EVIDENCE` (two-phase deterministic plan) |
| Scorer | `evals/scorers/score.py` at `1c3e2d3`+ (polarity-aware forbidden-claim matcher; threshold 0.8) |
| **Root-cause accuracy** | **65.6%** (63/96) |
| **act \| rc** | **100%** (63/63); aggregate action 80.2% |
| **Evidence recall (mean)** | **61.1%**; cases ≥ 0.8: 34/96 |
| **Verifier pass** | **78.1%** (75/96) |
| **Strict all-pass** | **29.2%** (28/96) |
| Unsupported claims | 9 cases; forbidden claims 0 |
| **Parse failures** | **12/96 produced no scoreable output** = 4 raw-unparseable JSON (all S07: `model produced no parseable structured output`) + 8 pydantic-schema-invalid (5×S01, 2×S04, 1×S08 — "facts must draw on at least two distinct services"). E2-v2-96 had 4 + 5 = 9. |
| Latency (wall, per case incl. tool calls) | p50 13 782 ms, p95 50 355 ms, mean 17 795 ms; model-only p50 13 776 / p95 50 348 ms |
| Tokens | input 234 548 total (mean 2 443/case), output 114 578 (mean 1 194/case) |
| Reference cost | $0.00 (local-marginal-zero) |

Same configuration on **dev** (`E6-C-directed-dev`, n=48): rc 62.5%, act|rc 100%,
evidence 70.8%, verifier 83.3%, all-pass 35.4%, no-output 4/48 (0 raw + 4 schema),
in 2 446 / out 1 255 tokens per case, p50 15 385 / p95 35 824 ms. This dev run is the
**weak arm** for R2 and the **direct-path control** for R1.

Strong arm reference on test: `E4-v2-96` all-pass 99.0%, rc 100%, evidence 100%,
verifier 100%, 1 forbidden (known false positive), p50 38 158 / p95 59 464 ms,
$9.24 total reference cost. (CLI input-token accounting is known to be unreliable —
226 input tokens total — see architecture.md; output tokens 298 456.)

## 4. Runs started / in flight

| Run id | Arm | Model | Split | Prompt | Purpose | Status |
|---|---|---|---|---|---|---|
| `E4-v2-dev` | E4 | claude-frontier | dev | baseline | strong arm on dev for R2 pairing | **done** 09:07–09:41 UTC, 48/48 |
| `R1-direct-dev` | R1 | local-specialist | dev | cause_action_directed | direct-path control under the new adapter code (cross-session floor vs `E6-C-directed-dev`) | **done** 09:26–09:47 UTC, 48/48 |
| `R1-direct2-dev` | R1 | local-specialist | dev | cause_action_directed | second same-session direct run: within-session determinism floor with digests | **done** 09:47–10:01 UTC, 48/48 |
| `R1-switchyard-dev` | R1 | local-specialist-switchyard | dev | cause_action_directed | routed arm | **done** 10:01–10:15 UTC, 48/48 |

## 4b. R1 finding — Switchyard 0.2.0 is NOT semantically invisible for grammar-constrained llama.cpp (turn 1)

Set-up: `nemo-switchyard==0.2.0` (`switchyard serve`, Python FastAPI front + Rust
core), route bundle `infra/switchyard/routes.yaml` — one `type: model` route
`fis-local-specialist` → `http://127.0.0.1:8082/v1`, `api_key ""`, `format openai`.
Registry entry `local-specialist-switchyard` (provider `switchyard`, model fields
identical to `local-specialist`, `base_url` 4000). `SwitchyardAdapter` subclasses the
local adapter; `build_body` is inherited, so the request the orchestrator produces is
**byte-identical** on both paths (`test_request_body_is_byte_identical_on_both_paths`).

Smoke on one fixed request (greedy, seed 42, `max_tokens 1200`, InvestigationResult schema):

| path | repeat 1 | repeat 2 | repeat 3 |
|---|---|---|---|
| direct :8082 | sha `ec965b29…`, 1031 out tok | `ec965b29…` | `ec965b29…` |
| via Switchyard :4000 | sha `b536f509…`, 1049 out tok | `b536f509…` | — |

Each path is deterministic; the two paths **disagree**. Root cause, proven two ways:

1. **Byte tap** (throw-away proxy on 8083 between Switchyard and llama.cpp): the body
   Switchyard forwards is the same length (2 991 B), semantically equal as JSON, but
   **every object's keys are sorted alphabetically** (serde_json without
   `preserve_order`). Top-level order `model,messages,max_tokens,temperature,seed,
   response_format` → `max_tokens,messages,model,response_format,seed,temperature`;
   schema `properties` order `case_id, classification, root_cause, facts, hypotheses,
   recommended_next_action, escalation_required, uncertainties, summary` →
   alphabetical. Headers upstream: only `content-type`, `x-switchyard-version: 0.2.0`.
2. **Reproduction on the direct path**: sending the direct request with *only* the
   `response_format.json_schema` keys sorted reproduces Switchyard's output exactly
   (`b536f509…`, 1049 tok). llama.cpp's JSON-schema→GBNF compiler preserves property
   order and the grammar forces the model to emit keys in that order — through
   Switchyard the model must write `facts` before `root_cause`, and its greedy
   generation diverges.

Attempted thin adapter (guide: "add the thinnest possible protocol adapter"): send a
client-side GBNF string (`grammar`, order-proof) built with llama.cpp's own
`examples/json_schema_to_grammar.py`. Direct and Switchyard then agree **exactly**
(`473c9ebe…`, 287 tok) — but that output differs from the frozen path, because
llama.cpp treats `response_format` specially for reasoning models (the grammar is
applied lazily after the `<think>` block: 3 456 reasoning chars) whereas a raw
`grammar` constrains from the first token (0 reasoning chars). So the adapter
restores transport equivalence at the cost of changing the baseline's thinking
behaviour — **not adopted**; the frozen weak baseline is left untouched as the guide
requires.

Consequence for R1: exact equivalence through Switchyard 0.2.0 is not achievable for
FIS's grammar-constrained local arm without either (a) an upstream Switchyard fix
(preserve JSON key order — filed as the recommended issue), or (b) a deliberate FIS
suite bump that canonicalises schema property order for **all** arms and re-baselines.
R1 therefore proceeds as designed and **measures the delta**: `R1-direct-dev` (control
re-run under the new adapter code — also the nondeterminism floor) and
`R1-switchyard-dev`. Pinned as an executable note:
`test_schema_property_order_is_not_alphabetical__the_known_r1_difference`.

Everything else about the hop checked out: verbatim body otherwise, no retries,
no timeout, no message condensing, no `x-switchyard-*` headers on a passthrough
success (recorded honestly as `selected_backend=None`), llama.cpp response body
returned verbatim (`usage`, `timings`, `finish_reason`), gateway routing log JSONL
line per request with token counts, `/v1/stats` per-model counters. `make test`
with both servers up: **187 passed** (incl. `test_live_passthrough_reaches_llamacpp`
and `test_route_bundle_loads_in_switchyard_itself`).

## 4c. Surprise: the direct path does not reproduce its own recorded dev run case-by-case (turn 1, partial)

`compare_routes.py --a E6-C-directed-dev --b R1-direct-dev` on the first 10 paired
cases: input tokens identical in 10/10 (same prompt bytes), **output tokens differ in
10/10, scored outcome differs in 6/10** (3 all-pass vs 0). Everything upstream of the
model is identical (same DB rows, same plan, same prompt); the model server was
**restarted at 04:14 EDT on 2026-08-16** (`ps lstart`, flags identical to the script)
between the E6-C run (00:25 UTC) and now. Earlier smoke: the same request produced
1200 tok/`length` cold and 1031 tok/`stop` with the prompt prefix cached (`cache_n=83`)
— llama.cpp's KV prompt-cache reuse changes the numerics enough to move greedy
argmax. So "greedy + seed ⇒ reproducible" holds within a server session for a fixed
cache state, and evidently **not** across server restarts / cache histories.

Plan (no extra requests to 8082 while a run is in flight — a stray request evicts
the prefix cache and perturbs the next case): after `R1-direct-dev`, run
`R1-direct2-dev` back-to-back (same session ⇒ within-session determinism floor
with output digests), then `R1-switchyard-dev`. Judge Switchyard against the
same-session direct pair, and record the cross-session gap as an R0 caveat: the
frozen baseline is reproducible in aggregate, not per case, unless the server
build, flags **and** cache history are held fixed. Add llama.cpp
`system_fingerprint` (`b1-9b05354`) and the exact server flags to the R0 record.

## 4d. R2 — paired weak/strong oracle on DEV (criterion 6) — DONE (turn 1)

`E4-v2-dev` finished 09:41 UTC (48/48; all-pass 91.7%, rc 97.9%, evidence 100%,
verifier 97.9%, forbidden 2, $5.16). `make routing-oracle` (weak `E6-C-directed-dev`,
strong `E4-v2-dev`), full output in `docs/routing-experiments.md` § R2:

| cell | n | rate |
|---|---|---|
| weak-pass/strong-pass | 16 | 33.3% |
| weak-fail/strong-pass | 28 | 58.3% |
| weak-pass/strong-fail | 1 | 2.1% (S06-2003005) |
| both-fail | 3 | 6.2% (S01-2001000, S08-2001007, S08-2003007) |

Theoretical safe-local **35.4%**, rescueable escalation **58.3%**, oracle hybrid
quality **93.8%** (vs strong-only 91.7%), oracle strong-call minimum 64.6%, hard-case
6.2%; oracle cascade cost $3.36 vs strong-only $5.16 (−35%), $0.0747 vs $0.1172 per
strict pass. **All four disagreements were reviewed against the harness before being
read as model behaviour** (details in routing-experiments.md): one scorer false
positive (post-positioned refutation cue), one verifier gap (`idempotency_key` not
harvested as an observed id), two scenario-realism issues (background settlements
never posted in 7 classes → S06 legitimately looks compound; S08 declined amount >
available balance). Corrected matrix: 16 / 30 / 2 ambiguous / 0. **No scorer,
verifier or generator change made** — recorded for a versioned suite bump.

## 4e. R1 results (criterion 5) — DONE

`make r1-compare` equivalents (`scripts/compare_routes.py`), full tables in
`docs/routing-experiments.md` § R1:

| pair | digest equal | outcome equal | all-pass | rc | evidence | verifier | no-output |
|---|---|---|---|---|---|---|---|
| direct vs direct2 (same session) | **47/48** (first case only differs) | **48/48** | 14 = 14 | 31 = 31 | 0.606 = 0.606 | 37 = 37 | 5 = 5 |
| E6-C (earlier server) vs direct | n/a (no digests then) | 25/48 | 17 → 14 | 30 → 31 | 0.708 → 0.606 | 40 → 37 | 4 → 5 |
| **direct2 vs Switchyard** | **0/48** | **34/48** | 14 → 11 | 31 → 28 | 0.606 → 0.655 | 37 → 39 | 5 → 4 |

Latency: model p50 12 619 → 12 691 ms (+72), p95 +260; transport overhead
(wall − llama.cpp compute) mean 138.9 → 142.7 ms (**+3.8 ms**), p50 unchanged 132 ms;
Switchyard's own reported routing overhead p50 0.89 ms. Tokens: input identical
(2 446.4/case), output 1 311.3 vs 1 304.7; **gateway routing-log totals for the 48
requests = FIS trajectory totals exactly** (117 426 prompt / 62 627 completion).
RoutingRecord on 48/48 routed invocations (`switchyard 0.2.0`, `passthrough`,
`upstream_model fis-local-specialist`, `selected_backend None`).

Verdict: **behaviour not equivalent** (every output differs; 14/48 outcomes change,
both directions) — fully explained by the key-order → grammar mechanism in §4b;
**parse rate equivalent** (4 vs 5); **latency equivalent** (+4 ms on 12.7 s);
**token accounting identical**. Decision-gate: keep the boundary/telemetry, keep the
weak stage on the direct path until key order is preserved upstream or the schema is
canonicalised in a versioned suite bump.

## 5. Work log

- turn 1: reconciliation; `make test` 160/160; reachability test+dev clean; E4-v2-dev
  started; `nemo-switchyard==0.2.0` installed into `.venv` (`uv pip install
  "nemo-switchyard[cli,server]==0.2.0"`) — pure-python server with a Rust extension,
  CLI `switchyard serve --routing-profiles <yaml>`; passthrough profile exists
  (`switchyard/lib/profiles/passthrough.py`).
- turn 1 (cont.): commits `8a93eda` routing schema + gold-leak guards · `b509b10` local
  adapter split + telemetry (`api_ms` from llama.cpp timings, `stop_reason`,
  `output_digest`) · `c72f5e7` Switchyard passthrough (adapter, registry entry,
  `infra/switchyard/{routes.yaml,serve.sh,README.md}`, make targets, tests) ·
  `3490b25` `scripts/compare_routes.py`, `scripts/routing_oracle.py`, make targets ·
  `fd4643c` docs (R2 results, protocol). Runs: E4-v2-dev, R1-direct-dev,
  R1-direct2-dev, R1-switchyard-dev, all 48/48. Docs updated: `routing-experiments.md`
  (new), `experiment-log.md` (appended), `architecture.md`, `HANDOFF.md`,
  `infra/switchyard/README.md`.

## 6. Blockers

None so far.

## 7. Next action

Milestone criteria all addressed (see morning summary). Next milestone: R4
deterministic cascade on dev (weak stage on the direct path; escalate on
parse/schema failure, verifier failure, unsupported claims), after the human decides
between the two ways to make the routed weak stage equivalent (upstream key-order
fix vs suite-v3 schema canonicalisation).

---

## Morning summary

### What was accomplished (all 7 criteria)

1. **E6b closed correctly** — on the recorded dev sweep (E/F/G/H all n=48); winner is
   the control C, whose single test confirmation already existed. No new test run.
2. **Post-E6b baseline frozen** as `weak-baseline-v1` (§3 above and
   `routing-experiments.md` § R0): commit `f48039a`, suite v2, Qwen3-8B Q4_K_M on
   llama.cpp `b1-9b05354`, prompt `cause_action_directed`, test split, rc 65.6%,
   act|rc 100%, evidence 61.1%, verifier 78.1%, all-pass 29.2%, no-output 12/96
   (4 raw + 8 schema), p50 13.8 s / p95 50.4 s, 2 443 in / 1 194 out tokens per case.
3. **Full test suite run and recorded**: 160/160 at `8599326` before any change;
   **187/187** at the end (`.venv/bin/python -m pytest tests -q`, incl. two live tests
   that skip when the servers are down). Reachability 96/96 test, 48/48 dev, 0 caps.
4. **Switchyard integrated as middleware only** — a registry entry + adapter beneath
   the FIS gateway contract; ground truth, scoring, evidence plan, trajectory record
   and lineage untouched; `RoutingRecord` is additive; gold-leak guards are tests.
5. **Passthrough evaluated vs direct on dev, n=48, one server session** — behaviour
   NOT equivalent (0/48 identical outputs, 34/48 identical outcomes, all-pass 14→11,
   rc 31→28, evidence +5 pts, verifier +2), root cause proven (sorted JSON keys →
   alphabetical GBNF property order); parse rate, latency (+4 ms) and token
   accounting (exact reconciliation) equivalent.
6. **Paired weak/strong oracle on dev**: 16 / 28 / 1 / 3; safe-local 35.4%,
   rescueable 58.3%, oracle quality 93.8%, strong-call minimum 64.6%; all four
   disagreements harness-reviewed (1 scorer FP, 1 verifier gap, 2 scenario-realism
   issues) — recorded, not patched.
7. Nothing from R3+ started; no scorer/rubric/corpus/model change.

### Measured results — headline table (dev, n=48 unless noted)

| arm | all-pass | rc | evidence | verifier | notes |
|---|---|---|---|---|---|
| E6-C-directed-dev (recorded control, earlier server) | 35.4% | 62.5% | 70.8% | 83.3% | weak arm for R2 |
| R1-direct-dev / R1-direct2-dev (same session) | 29.2% / 29.2% | 64.6% | 60.6% | 77.1% | 47/48 identical digests |
| R1-switchyard-dev | 22.9% | 58.3% | 65.5% | 81.2% | 0/48 identical digests; +4 ms |
| E4-v2-dev (strong) | 91.7% | 97.9% | 100% | 97.9% | $5.16, 2 forbidden = FPs |
| Oracle hybrid (R2) | 93.8% | — | — | — | −35% strong cost |

### Surprises

- **Switchyard is not a transparent hop for grammar-constrained llama.cpp**: its Rust
  core sorts JSON keys and llama.cpp's grammar compiler is order-sensitive. The thin
  fix (client-side GBNF) trades away the model's thinking phase, so it was not taken.
- **The local arm is reproducible only within a server session**: back-to-back runs
  agree 47/48; across the overnight server restart the same config moved 23/48
  outcomes and 10 pts of evidence recall. Every past case-level local comparison
  should be read with that in mind (E6b's +5 pt rule was of that order).
- **Background settlements are never posted in 7 of 12 classes**, so S10's fault
  signature is ambient noise; the frontier's two S06 `compound_failure` answers are
  defensible. Found only because R2 flagged a weak>strong inversion.

### Unresolved

- Choice between upstream Switchyard fix and a suite-v3 schema canonicalisation
  (both re-baseline the routed weak arm; the latter re-baselines everything).
- Four harness candidates for the next suite version (unposted background
  settlements; S08 amount vs balance; `idempotency_key` not an observed id;
  post-positioned refutation cue) — all versioned, none applied.
- Latency of `R1-direct-dev` overlapped the E4 CLI run; `R1-direct2-dev` and
  `R1-switchyard-dev` ran alone and are the pair used for overhead.

### Recommended next experiment

**R4 deterministic cascade on dev**: weak stage on the direct path (until the R1
caveat is resolved), escalate to `claude-frontier` on no-output / schema-invalid,
verifier failure, or any unsupported claim; report weak coverage, strong-call rate,
route regret, unnecessary escalation, rescue rate, cost and latency per strict pass
against the R2 oracle; pre-register the quality floor in case counts; one test
confirmation of one frozen policy. Do not use evidence recall as an online signal.

### Working tree

Clean after the final commit; generated artefacts (`evals/reports/*.json`) are
gitignored by design and reproducible from `learning.*` via `make report`,
`make r1-compare`, `make routing-oracle`.

---
---

# Milestone 2 — R0.1 (Switchyard transparency) → R4 (deterministic cascade)

Started 2026-08-16 ~12:45 UTC from HEAD `5d67804` (clean, 187 tests, servers up:
llama.cpp pid 4848 = the same session as the R1 runs, Switchyard 4000).

## M2.0 Reconciliation

`git status` clean at `5d67804`; `pytest` 187 passed; `fis-postgres`/`fis-nats`
healthy; llama.cpp `/health` ok (`b1-9b05354`, pid 4848, same session as R1);
Switchyard `/health` ok. Prose in `HANDOFF.md`/`OVERNIGHT_STATUS.md` matched the
artefacts (runs `R1-*`, `E4-v2-dev` present with the recorded counts). No stale
claims found beyond what M1 already corrected.

## M2.1 R0.1 — fix: key-order-invariant schema on the routed path (commit `11ff23f`)

Mechanism recap: Switchyard 0.2.0's Rust core sorts JSON keys; llama.cpp's
schema→GBNF converter enforces `properties` order. Fix at the adapter boundary, no
eval-suite change, no loss of reasoning behaviour: `SwitchyardAdapter.build_body`
rewrites every object schema into `allOf` components — one property per component,
optional properties wrapped in `anyOf` — which llama.cpp's converter (C++
`common/json-schema-to-grammar.cpp` `allOf` branch, mirrored by the reference
Python) compiles to the **byte-identical grammar text** as the plain schema, and
which survives key sorting because arrays are ordered. `additionalProperties` is
dropped from rewritten objects (the converter's `allOf` branch forbids extras
anyway; leaving it would route the object to the `properties` branch with an empty
list). Direct path untouched.

Evidence before the paired run:
- `test_grammar_through_switchyard_equals_grammar_on_the_direct_path`: with
  llama.cpp's own `examples/json_schema_to_grammar.py`, `grammar(sorted(rewritten))
  == grammar(plain)` and `grammar(sorted(plain)) != grammar(plain)`.
- `test_key_order_invariant_preserves_property_order_and_requiredness_under_sorting`
  (root, Fact, RootCause; idempotent).
- Live smoke, one request, six calls in sequence: direct plain `ec965b29…` (1031 tok,
  3456 reasoning chars) ×3, Switchyard+rewritten `ec965b29…`, direct+rewritten
  `ec965b29…`, Switchyard+plain `b536f509…` (the bug). Thinking preserved.
- Session telemetry added: `ModelInvocation.runtime_fingerprint` (llama.cpp
  `system_fingerprint`), `Trajectory.runtime_context` (local server pid/start-ticks/
  boot-id, build, model path, gateway version, cascade stage) written by the runner.

Paired verification (in flight): `make eval-r01-dev` — `prime-local` (one fixed
request so both arms' first case has the same prompt-cache predecessor) →
`R01-direct-dev` → `prime-local` → `R01-switchyard-dev`; nothing else on 8082.
**Caveat recorded:** a `pytest` run at ~13:12 UTC (before live tests were made opt-in
in `021890a`) sent one 1-token request to 8082 during `R01-direct-dev` case ~15; a
primed `R01-direct2-dev` will follow so the Switchyard arm can be judged against an
unperturbed same-session direct run.

## M2.2 R4 — implementation (commit `021890a`)

`services/ai_orchestrator/cascade.py`, `run_eval --escalate-to`, weak stage persisted
under `<run>.weak`, `scripts/routing_cascade_report.py` (replay + live). Signals:
no-output / unsupported claim / verifier failure — nested, so policies are `none` ⊂
`parse` ⊂ `verifier`.

**Pre-registered selection rule (dev, replay on the same-session weak run, before
any live cascade run):** adopt `verifier` unless it costs more than 2 unnecessary
escalations (weak would have passed) beyond `parse` on dev; otherwise `parse`. No
other trigger will be added in this milestone whatever the oracle gap turns out to
be. Then: one live dev run to validate the implementation, freeze, one test run.

## M2.3 R0.1 — result: SOLVED (runs `R01-direct-dev`, `R01-switchyard-dev`, `R01-direct2-dev`, all n=48, session pid 4848)

| pair | digest equal | outcome equal | all-pass | model p50 Δ |
|---|---|---|---|---|
| direct2 (unperturbed, primed) → Switchyard | **48/48** | **48/48** | 14 = 14 | +11 ms |
| direct (one case perturbed by the 13:12 pytest request) → Switchyard | 47/48 (S04-2003003) | 47/48 | 14 = 14 | +421 ms (load-confounded) |

Tokens 117 426 / 62 938 identical on both arms and in Switchyard's routing log;
transport overhead p50 136 ms vs 120–139 ms direct. Full table in
`routing-experiments.md` § R0.1. Same-session stability over 3 h confirmed
(`R1-direct2-dev` 10:01 UTC vs `R01-direct-dev` 13:00 UTC: 46/48 digests, the two
differences being the first case's predecessor and the perturbed case).

## M2.4 R4 — selection on dev by replay (weak = `R01-direct2-dev`, strong-ref = `E4-v2-dev`)

| policy | escalated | rescued (weak fail→pass) | unnecessary | all-pass | rescueable caught |
|---|---|---|---|---|---|
| parse | 5/48 (10.4%) | 3 | 0 | 35.4% | 3/30 |
| verifier | 11/48 (22.9%) | 8 | 0 | 45.8% | 8/30 |
| weak-only / strong-only / oracle | — | — | — | 29.2% / 91.7% / 91.7% | cells 14 / 30 / 0 / 4 |

Rule applied: `verifier` costs 0 unnecessary escalations beyond `parse` → **frozen
policy = `verifier`**. 22 rescueable cases stay invisible to the gate (weak result
verifier-clean but wrong on root cause and/or evidence recall — eval-only
dimensions). Live dev run `R4-cascade-verifier-dev` started 13:57 UTC.

## M2.5 R4 — live dev run and the one test confirmation

| run | split | all-pass | rc | evidence | verifier | escalated | rescue | unnecessary | false neg | cost/success | wall p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `R4-cascade-verifier-dev` (13:57–14:16 UTC) | dev 48 | **50.0%** (weak 29.2 · strong 91.7 · oracle 91.7) | 79.2% | 0.783 | 100% | 11 (22.9%) | 10/11 | 0 | 22 | $0.0471 (strong $0.1172) | 16.9 s (strong 33.2) |
| `R4-cascade-verifier-96` (14:16–14:57 UTC) | test 96 | **49.0%** (weak 29.2 · strong 99.0 · oracle 100) | 75.0% | 0.811 | 97.9% | 21 (21.9%) | 19/21 | 0 | 47 | $0.0464 (strong $0.0973) | 14.5 s (strong 38.2) |

Both in session pid 4848, primed; the dev cascade's weak stage reproduced
`R01-direct2-dev` 48/48. Weak stage on test = 29.2% all-pass, equal to the frozen
baseline's aggregate while differing on 42/96 individual outcomes (cross-session).
Full tables and interpretation: `routing-experiments.md` § R4; append-only record in
`experiment-log.md`.

## M2.6 Milestone-2 summary

**Completed:** reconciliation · R0.1 fixed at the adapter (`11ff23f`) and proven
48/48 same-session (`R01-*`) · R4 implemented (`021890a`), policy selected on dev by
replay under a pre-registered rule, live dev run, one test confirmation · docs
(`routing-experiments.md`, `experiment-log.md`, `HANDOFF.md`, `architecture.md`,
this file) · tests 197 (one live, opt-in) · suite v2, scorer, verifier, generator,
`weak-baseline-v1` untouched · Nemotron/learned routing/QLoRA not started.

**Surprises:** (1) the fix that restored Switchyard transparency is a schema
*representation* change that llama.cpp compiles to the identical grammar — no
middleware patch, no suite change; (2) the live strong stage rescued 10/11 on dev
where the recorded strong arm would have rescued 8/11 (frontier nondeterminism —
S06-2003005, the M1 inversion, passed this time); (3) 47/96 test cases are
verifier-clean weak failures — the deterministic gate's blind spot is exactly the
evidence-discipline gap from E6b; (4) S08-2003007 tripped the strong arm's forbidden
claim again (suite-v3 candidate confirmed twice).

**Unresolved (backlog, not blockers):** suite-v3 candidates (4); frontier input-token
under-reporting makes strong cost a floor; the routed weak arm still runs direct in
R4 (interchangeable after R0.1, kept direct for one-factor discipline).

**Recommended next experiment (one):** R3 — Nemotron 3.5 Lightning benchmark on
suite v2 (see HANDOFF). Suite v3 afterwards as a deliberate release.

---
---

# Milestone 3 — R3: Nemotron 3.5 Lightning compatibility spike and benchmark

Started 2026-08-17 ~01:35 UTC (2026-08-16 21:35 EDT) from HEAD `8078da8` (clean, 196 passed + 1 opt-in live
test, servers: llama.cpp Qwen pid 4848 `b1-9b05354` on 8082 — the same session as every
R0.1/R4 run — and Switchyard 4000).

## M3.0 Reconciliation

`git status` clean at `8078da8`; pytest 196 passed / 1 skipped (live, opt-in);
reachability unchanged (test 96/96, dev 48/48 — no corpus regeneration in R3);
hardware as seen from WSL: RTX 5080 Laptop 16 303 MiB (7 760 MiB used by the Qwen
server), driver 610.62, **47 GB RAM visible to WSL** (35 GB free; the machine's 64 GB
is not all exposed to the VM), 845 GB disk free. Recorded artefacts match the prose
(`R01-*`, `R4-cascade-verifier-{dev,96}` present with the documented counts).

## M3.1 Compatibility spike — findings from the model's own metadata

Sources: `bartowski/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF` and
`ggml-org/…-GGUF` (HF), model card `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16`
(released 2026-08-11), GGUF headers parsed locally.

| Property | Value |
|---|---|
| Architecture | `nemotron_h_moe` — hybrid Mamba-2 + attention + MoE, 53 blocks (attention in a few, per `head_count_kv` array), 16 MoE blocks |
| Parameters | 30.65 B in experts (128 experts × 16 layers, `expert_used_count 6` + 1 shared), 1.56 B dense (Mamba-2/attention), 0.70 B embeddings/output; ~3 B active/token |
| Context | 1 048 576 declared; FIS uses 16 384 |
| Reasoning | on by default via chat template (`enable_thinking`), `<think>` block — same default as Qwen3 |
| Vendor sampling | T 1.0 / top-p 0.95 (both modes). FIS holds decoding at greedy/seed 42 for both arms — a deliberate, shared deviation |
| Structured output / tools | function calling supported (qwen3_coder-style parser); JSON-schema grammar is llama.cpp-side and model-agnostic |
| llama.cpp support | `nemotron_h_moe` present in the local build `b1-9b05354` (2026-08-14; `libllama.so` carries the arch strings) — **no rebuild needed** if it loads |
| GGUF sizes | every quant ≥ 17.9 GB: dense/embeddings only ~1.7 GB, experts 16.3 GB (IQ4_XS: IQ4_NL) / 17.4 GB (Q4_0) / 23.6 GB (Q4_K_M — experts fall back to Q5_0/Q8_0 because 1856-wide expert matrices are not 256-block aligned) |
| Fit on 16 GB VRAM | **cannot be held whole at any available quantization**; placement is necessarily hybrid — dense weights + KV/SSM state + some expert layers on GPU, remaining experts in system RAM (`--fit on` / `--n-cpu-moe`) |
| Chosen file | `bartowski/…-IQ4_XS.gguf` (17.94 GB, imatrix, experts IQ4_NL ~4.25 bpw — the closest 4-bit class to Qwen's Q4_K_M) |
| Runtime | same llama.cpp binary/build as Qwen; `infra/serve-nemotron.sh` on **8083**, `--fit on --fit-target 1024` so Qwen (8082) keeps its headroom; otherwise identical flags (`--jinja`, `--parallel 1`, q8_0 KV, flash-attn, ctx 16 384) |
| Design | **A — simultaneous endpoints**: Qwen session pid 4848 untouched, Nemotron on 8083, same ordered dev cases through both, fingerprints on every trajectory |

## M3.2 Experiment contract (frozen before any benchmark run)

| Field | Value |
|---|---|
| suite / split | v2 / dev (48 = 4 × 12 classes), corpus unchanged, reachability 48/48 |
| prompt | `cause_action_directed` (variant C, sha256 `40111d53f60e0a37…`), `PROMPT_VERSION 1` — no Nemotron-specific prompt |
| evidence / tools | `FIXED_EVIDENCE`, same two-phase plan, same 8 tools |
| response schema | `InvestigationResult` — plain schema on the direct path (both arms direct); grammar = llama.cpp json_schema→GBNF |
| scorer / verifier | unchanged (`evals/scorers/score.py`, `fis_platform/verification/verifier.py`) |
| scenario order | `ORDER BY scenario_id` (S01-2000000 … S12-2003011), `prime-local`-style priming of each endpoint before its run |
| decoding | `temperature 0`, `seed 42`, `max_tokens 4096`, chat template default (thinking on) — identical for both arms |
| runtime | llama.cpp `b1-9b05354` for both; Qwen `-ngl 99`; Nemotron `--fit on` (hybrid GPU/RAM) — recorded in `runtime_context` |
| arms | `R3-qwen-dev` (contemporaneous control, session pid 4848), `R3-nemotron-dev`, plus a second Qwen control after Nemotron (`R3-qwen2-dev`) to bound within-session drift |
| comparison | `compare_routes.py` per scenario; migration matrix A/B/C/D; `routing_cascade_report.py` replay with the unchanged R4 `verifier` policy for both weak arms against `E4-v2-dev` |
| test policy | test untouched unless the pre-registered rule (M3.5) is met; then exactly one run |

## M3.3 Compatibility spike — result: COMPATIBLE (commit `3e02b3e`)

Loaded on the existing llama.cpp build in 9 s (mmap): Nemotron process ~8.0 GB VRAM
(GPU total 15.7 GB with Qwen's 7.7 GB), RSS 18.9 GB (the mmap'd file), n_threads 16
(Ryzen 9 9955HX, 16C/32T). Note: WSL exposes 47 GB of the machine's RAM. Smoke on the
fixed request ×3: **72 tok/s** generation with experts partly in system RAM, prompt
~100 tok/s cold, identical output all three times (deterministic), reasoning on by
default (4 163 chars of `<think>` — longer than Qwen's 3 456 on the same request; at
`max_tokens 1200` it was still thinking, so the FIS cap of 4 096 is the operative
constraint and stays as is). Two real dev cases (`SMOKE-nemotron`, S01-2000000/1):
schema-valid output, both root causes correct, 3 034 / 1 885 output tokens, 45.6 s /
29.1 s wall; one verifier violation ("cites a service that was never successfully
called: `tool://case_summary/…`") — a citation-format habit to watch. Task contract
unchanged: same prompt, evidence, schema, grammar path, scorer, verifier.

## M3.4 Benchmark runs (in flight, `make eval-r3-dev`)

`prime-local` → `R3-qwen-dev` (control A, session pid 4848) → `prime-nemotron` →
`R3-nemotron-dev` (session pid 489534) → `prime-local` → `R3-qwen2-dev` (control B).
Ran 2026-08-17 01:58–05:10 UTC (Qwen A 01:58–02:17, Nemotron 02:18–04:57, Qwen B
04:57–05:10).

## M3.5 Pre-registered selection rule (written before any R3 result was read)

Nemotron becomes the preferred weak-tier candidate — and earns the single test
confirmation — only if ALL of the following hold on DEV (n=48):

1. **Quality:** strict all-pass(Nemotron) − all-pass(Qwen A) ≥ max(5 cases, 2 ×
   |all-pass(Qwen A) − all-pass(Qwen B)|). Root-cause accuracy not below Qwen A.
2. **Silent failures:** under the unchanged R4 `verifier` replay against `E4-v2-dev`,
   false negatives (weak accepted, weak fail, strong-ref pass) fall by ≥ 5 cases vs
   the Qwen A replay.
3. **Regressions:** cell B (Qwen A pass / Nemotron fail) ≤ 3 cases, each reviewed
   (harness vs model), and Nemotron introduces no forbidden claims.
4. **Operational:** all 48 cases complete with no crash/OOM/restart; wall p50 ≤ 30 s
   (Qwen ≈ 12.6 s) in the design-A placement; VRAM stays within the card.
5. **Economics with the same cascade:** Nemotron + R4 has cost per successful
   investigation ≤ Qwen + R4's, OR its all-pass exceeds Qwen + R4's by ≥ 5 cases at
   ≤ 1.5× the strong-call rate.
6. **Above noise:** (1) already requires the gain to exceed twice the Qwen A/B drift.

If any criterion fails: no test run, negative result recorded, Qwen stays incumbent.
No Nemotron-specific prompt, no trigger changes, no scorer changes regardless.

## M3.6 Results (all on dev, n=48; full tables in `routing-experiments.md` § R3)

**Reproducibility control:** Qwen A vs Qwen B — 48/48 identical output digests and
outcomes (and identical to `R01-direct2-dev`); design A gave zero within-session drift.

| | Qwen A/B | Nemotron |
|---|---|---|
| all-pass · rc · evidence · verifier | 29.2% · 64.6% · 0.606 · 77.1% | 25.0% · 33.3% · 0.316 · 33.3% |
| no-output | 5 (schema) | 31 (29 `length` — still in `<think>` at 4 096 tokens; 2 schema) |
| silent failures (verifier-clean, wrong) | 23 | **4** |
| completed cases | — | 19: 12 pass, rc 16, evidence 0.80 |
| migration A/B/C/D | — | 4 / 10 / 8 / 26 (B = all length-cap; C = 6 Qwen-silent cases rescued) |
| R4 replay (verifier policy) | 45.8% at 22.9% strong calls, $0.0545/success | **89.6%** at 66.7% strong calls, $0.0868/success |
| throughput (probe, `--no-mmap`) | 97 tok/s, TTFT 0.5 s | 91–95 tok/s, TTFT 2.2 s |

**Surprises:** (1) 29/48 Nemotron cases never leave `<think>` under the frozen
4 096-token budget — a contract-fit failure, not a wrong answer; (2) mmap +
CPU-offloaded experts collapsed to 20 tok/s after the page cache turned over
(the dev run's 206 s p50); `--no-mmap` restores 91 tok/s with identical outputs;
(3) Nemotron converts Qwen's silent failures into *loud* ones (15 of 23), which is
why Nemotron+R4 lands one case short of the frontier; (4) the S08 forbidden-claim FP
did not recur for Nemotron.

## M3.7 Decision under the pre-registered rule: **Nemotron does NOT qualify — TEST untouched**

1 FAIL (12 vs 14; rc 16 vs 31) · 2 PASS (22 → 4) · 3 FAIL (B = 10, all length-cap) ·
4 FAIL (p50 206 s as run / ≈ 47 s projected > 30 s) · 5 FAIL ($0.0868 > $0.0545;
strong calls 2.9×) · 6 moot. Qwen remains the incumbent. Recorded as a negative
result with the confound named (token budget).

## M3.8 Milestone-3 summary

Completed: reconciliation · compatibility spike (compatible; hybrid placement; same
runtime) · frozen contract · pre-registered rule · design-A benchmark with two Qwen
controls · migration matrix · silent-failure analysis · R4 replay for both arms ·
intelligence-density table · decision (negative) · docs. Not touched: test, suite v2,
scorer, verifier, prompt, R4 policy, QLoRA, learned routing, suite v3.

Environment left: Qwen on 8082 (new session — pid 4848 ended 05:15 UTC after all
same-session work), Nemotron on 8083 (`--no-mmap`, fit-target 1024), Switchyard 4000.

**Recommended next milestone (one): R3b — token-budget factor.** Re-run the *same*
paired design (Qwen A → Nemotron → Qwen B, one session each, dev only) at
`max_tokens 8192` for **both** arms — one decoding-config factor, everything else
frozen — to learn whether Nemotron's completed-case quality (63% pass, 4 silent)
holds across the whole split and what it does to Qwen; then the R4 replay again. Only
after that is the Nemotron-vs-Qwen comparison a model comparison; and only then does
suite v3 (re-baselining Qwen, Nemotron and the frontier together) buy the most.

---
---

# Milestone 4 — R3b: the token-budget factor (`max_tokens` 4096 → 8192, both weak arms, dev only)

Started 2026-08-17 ~07:50 UTC from HEAD `332b9d0` (clean; 196 passed + 1 opt-in
live test skipped). R3 left exactly one confound: Nemotron's 29/48 `length` no-outputs
under the frozen 4 096-token budget. R3b varies that one factor for **both** weak arms
and nothing else. Suite v3, prompts, scorer, verifier, ontology, evidence, R4 policy,
learned routing and QLoRA are all out of scope.

## M4.0 Reconciliation

| Claim in prose | Repository / artefact state | Verdict |
|---|---|---|
| HANDOFF/OVERNIGHT: R3 done, negative under the frozen budget, test untouched, HEAD `332b9d0` | `git log` HEAD `332b9d0`, tree clean; persisted runs `R3-qwen-dev` (14/48), `R3-nemotron-dev` (12/48), `R3-qwen2-dev` (14/48), all n=48; no run touched the test split after `R4-cascade-verifier-96` | matches |
| R3: Nemotron 29 `length` + 2 schema no-outputs; Qwen 5 schema no-outputs | `stop_reason` counts from `learning.trajectories`: Nemotron `length` 29 / `stop` 19; Qwen `stop` 48/48, **max output 3 508 tokens — Qwen never reached 4 096** | matches; for Qwen the cap was never binding at 4 096 |
| Both servers up in new sessions after R3 (`--no-mmap`, fit-target 1024) | 8082 Qwen pid 586847, 8083 Nemotron pid 586986 (`--fit on --fit-target 1024 --no-mmap`), both `b1-9b05354`, ctx 16 384, 1 slot; Switchyard 4000 pid 44417 unused by R3b; `fis-postgres`/`fis-nats` healthy; GPU 15.6/16.3 GB used (both models resident); WSL RAM 47 GB, 40 GB available | matches — one session per model for the whole of R3b, no restart needed |
| ctx 16 384 leaves room for 8 192 output tokens | largest dev prompt: 3 390 tokens (Qwen tokenizer) / 3 482 (Nemotron); 3 482 + 8 192 = 11 674 < 16 384 | no runtime blocker; placement unchanged |
| Tests | 196 passed, 1 skipped (live) at `332b9d0` | matches |

Runtime memory note (recorded, not acted on): the `--no-mmap` Nemotron process shows
VmRSS 4.6 GB (RssShmem 4.0 GB) and `free` reports only ~6 GB used across the VM,
although ~11 GB of expert weights must be off-GPU. Under WSL2 the CUDA host
allocations appear to be accounted outside the guest's RSS. Reported as observed;
VRAM (nvidia-smi) is the reliable footprint measure here.

## M4.1 Experiment contract (frozen before any 8 192-token run)

| Field | R3 (historical) | **R3b** |
|---|---|---|
| suite / split / order | v2 / dev (48) / `ORDER BY scenario_id` | **same** |
| prompt | `cause_action_directed`, `PROMPT_VERSION 1` | **same** |
| evidence / tools / schema / grammar path | `FIXED_EVIDENCE`, 8 tools, `InvestigationResult`, llama.cpp json_schema→GBNF, direct path | **same** |
| scorer / verifier | `evals/scorers/score.py`, `fis_platform/verification/verifier.py` | **same (untouched)** |
| decoding | greedy, `seed 42`, chat-template default (thinking on) | **same** |
| **`max_tokens`** | **4 096** | **8 192 — the only factor, both weak arms** |
| models | Qwen3-8B Q4_K_M (8082, `-ngl 99`); Nemotron 3.5 Lightning 30B-A3B IQ4_XS (8083, `--fit on --fit-target 1024 --no-mmap`) | **same checkpoints, quants, flags, build `b1-9b05354`** |
| design | A: Qwen A → Nemotron → Qwen B, one session per model, `prime-*` before each arm, nothing else on 8082/8083, `FIS_LIVE_TESTS` unset | **same**; run ids `R3b-qwen-dev`, `R3b-nemotron-dev`, `R3b-qwen2-dev` |
| strong reference | `E4-v2-dev` (recorded), R4 `verifier` policy by replay | **same, unchanged policy, no new trigger** |
| implementation | — | `run_eval --max-tokens` (default 4 096 so every historical target is unchanged) threaded to `GenerationRequest.max_tokens`; recorded in `runtime_context` and, when non-default, in `config_digest`; additive telemetry `reasoning_chars`/`content_chars` on `ModelInvocation` (observation only — the model sees nothing new) |
| test policy | untouched | **untouched unless M4.2 passes in full; then exactly one run** |

## M4.2 Pre-registered R3b selection rule (written and committed BEFORE any 8 192-token result was observed)

Definitions, fixed now: **complete** = the generation finished inside the budget and
reached its final JSON (`stop_reason == "stop"`) — the notion behind R3's "19
completed" (19 `stop` = 17 schema-valid + 2 schema-invalid; 29 `length`); a `length`
stop is by construction not complete. The schema-valid ("scoreable") count is reported
beside it. *Correction ~08:11 UTC (commit `6742930`), before the Nemotron arm started at 08:21 (Qwen A in flight):
the first wording defined complete as "schema-valid, scoreable" and claimed that
equalled 48 − 31 = 19; it equals 17. The rule's threshold (43 = 19 + 24) was written
against the `stop`-count, so the definition is aligned to it here rather than the
threshold moved.* **Silent failure** = schema-valid, verifier-clean, `all_pass` false
(`model_migration_matrix.py` `_silent`). **Routing false negative** = silent AND the
strong reference (`E4-v2-dev`) passes. **Migration cells** A/B/C/D are built with Qwen A
as incumbent; if Qwen A and B disagree on any outcome, every criterion below is
evaluated against both and must hold against both. **Cascade economics** come from
`routing_cascade_report.py --weak <run> --strong E4-v2-dev --policy verifier` (replay,
local reference cost $0, strong cost = recorded `E4-v2-dev` reference cost, a floor).

Nemotron qualifies as a viable weak-tier challenger on DEV only if **ALL** of A–F hold:

| # | criterion | threshold (mechanical) |
|---|---|---|
| **A** completion | Nemotron completes ≥ **43/48** (≥ +24 vs R3's 19/48) |
| **B** quality | Nemotron strict all-pass ≥ **14/48**; AND Nemotron root-cause-correct count ≥ Qwen A's − max(2, 2 × \|rc(Qwen A) − rc(Qwen B)\|). "Materially worse" is fixed here as **more than 2 cases below Qwen A** (adjusted upward only if the Qwen A/B drift in rc exceeds 1 case); the exact difference is recorded either way |
| **C** silent failure | Nemotron silent failures ≤ **6/48** (the superset of routing false negatives; both counts recorded) |
| **D** regressions | cell B (Qwen A pass / Nemotron fail) ≤ **5**; every remaining B case reviewed and its cause classified (length cap / wrong rc / evidence / verifier / parse-schema / other) |
| **E** cascade economics | under the unchanged R4 `verifier` replay: Nemotron strong-call rate < **50%** (i.e. ≤ 23/48 escalations) AND Nemotron + R4 cost per successful investigation ≤ **$0.070** |
| **F** latency | Nemotron-only wall p50 (as run, current `--no-mmap` placement beside Qwen) ≤ **75 s**; p95 recorded |

Interpretation, fixed now: all six PASS ⇒ Nemotron qualifies and receives **exactly
one** TEST confirmation under the identical R3b contract (`R3b-nemotron-96`:
Nemotron-only at 8 192, primed, one session; Nemotron + R4 by the same replay against
the recorded `E4-v2-96`), with no tuning before or after and no second look. Any FAIL ⇒
Qwen remains incumbent, TEST untouched, negative result recorded, stop after the DEV
analysis. Thresholds will not be reinterpreted after results are seen.

Reproducibility gate, fixed now: Qwen A vs Qwen B must agree on ≥ 46/48 output digests
and ≥ 46/48 scored outcomes (R3: 48/48). If they diverge more than that, R3b stops for
diagnosis before any Qwen-vs-Nemotron interpretation.

Historical length-cap classification, fixed now (each of R3's 29 `length` cases lands in
exactly one): **RECOVERED_PASS** (R3b complete and all-pass) · **RECOVERED_FAIL** (R3b
complete, not all-pass) · **STILL_LENGTH_CAPPED** (R3b `stop_reason == length`) ·
**OTHER_FAILURE** (R3b not complete for another reason — schema-invalid or error).

## M4.3 Implementation (commits `b947972`, `f9e1223`, `6742930`, `7625a5a`)

`run_eval --max-tokens` (default `DEFAULT_MAX_TOKENS = 4096`, so every recorded make
target reproduces its configuration byte-for-byte) threaded to `GenerationRequest`;
recorded on every `ModelInvocation.max_tokens`, in `runtime_context`, and — only when
non-default — as `|max_tokens:N` in `config_digest`. Additive telemetry
`reasoning_chars` / `content_chars` from llama.cpp's `reasoning_content` (observation
only; verified live: a `length` stop returns empty `content` beside a long
`reasoning_content` — the R3 failure mode). Local manifests declare the 8 192 ceiling
(16k ctx − ~3.5k prompt); the runner refuses a budget above it. `make eval-r3b-dev` /
`r3b-compare`; `scripts/token_budget_delta.py` (4 096 → 8 192 per model, the
RECOVERED_PASS / RECOVERED_FAIL / STILL_LENGTH_CAPPED / OTHER_FAILURE classification);
`scripts/r3b_selection_rule.py` (the M4.2 rule as a function of the persisted rows,
validated against R3: reproduces silent 4, cell B 10, 32/48 escalations, $0.0868, p50
206 s). Tests 196 → 202 (+1 opt-in live).

Two pre-run runtime findings, both handled before any arm ran: (1) the idle
`--no-mmap` Nemotron process measured 47–50 tok/s vs 91 recorded — restarted with the
identical command line: 92.8–93.1 tok/s; the make target now restarts and probes the
endpoint (train case) right before its arm; (2) the 8082 throughput check I ran at
08:02 used case 1's own prompt — that is the source of the single Qwen A/B digest
difference below (first case, predecessor), and why the Nemotron probe uses a train
case.

## M4.4 Runs (design A, one Qwen session, `make eval-r3b-dev` at `f9e1223`)

| run | model | max_tokens | session | window (UTC) | all-pass | rc | evidence | verifier | no-output |
|---|---|---|---|---|---|---|---|---|---|
| `R3b-qwen-dev` (A) | Qwen3-8B Q4_K_M | 8 192 | pid 586847 start_ticks 7008514 boot b6ea9365 | 08:09–08:21 | 15/48 | 30 | 0.648 | 36 | 6 (schema) |
| `R3b-nemotron-dev` | Nemotron 3.5 Lightning IQ4_XS, `--fit on --fit-target 1024 --no-mmap`, fresh session probed at 89.7–90.4 tok/s | 8 192 | pid 670208 start_ticks 8016445 boot b6ea9365 | 08:21–09:12 | **18/48** | 31 | 0.649 | 34 | 11 (9 `length` + 2 schema) |
| `R3b-qwen2-dev` (B) | Qwen3-8B Q4_K_M | 8 192 | pid 586847 (same) | 09:12–09:24 | 15/48 | 30 | 0.648 | 36 | 6 |
| `R3b-qwen4096-dev` (diagnostic, after B) | Qwen3-8B Q4_K_M | **4 096** | pid 586847 (same) | 09:25–09:37 | 15/48 | 30 | 0.627 | 35 | 7 (6 schema + 1 `length`: S07-2003006) |

Build `b1-9b05354` on 192/192 invocations; `max_tokens` recorded on every trajectory.
Operator observations (sampler every 10 s, outside the JSON artefacts): GPU peak 15 666
MiB (both models resident); Nemotron VmRSS 4.6 → 13.65 GB over its arm; WSL available
memory never below 24.4 GB.

## M4.5 Reproducibility gate — PASS

Qwen A vs B: **47/48 digests, 48/48 outcomes** (the first case in run order differs by
8 tokens, same outcome — predecessor effect from the pre-run probe). Same-session
diagnostic A (8 192) vs 4 096: 46/48 digests, 47/48 outcomes; the budget changed exactly
one case (S07-2003006, 4 105 tokens: silent wrong at 8 192, `length` no-output at 4 096).
Nemotron: the 19 cases R3 completed reproduce byte-identically at 8 192 in a new
session (19/19 digests and token counts). Comparison valid.

## M4.6 Results (full tables in `routing-experiments.md` § R3b)

| | Qwen A 8 192 | Nemotron 8 192 | Nemotron 4 096 (R3) |
|---|---|---|---|
| complete (`stop`) / scoreable / `length` | 48 / 42 / 0 | **39 / 37 / 9** | 19 / 17 / 29 |
| all-pass · rc · evidence · verifier | 15 · 30 · 0.648 · 36 | **18 · 31 · 0.649 · 34** | 12 · 16 · 0.316 · 16 |
| silent failures (routing FN) | 21 (21) | **16 (16)** | 4 (4) |
| output tokens (total / mean) | 62 673 / 1 306 | 239 961 / 4 999 | 172 436 / 3 592 |
| wall p50 / p95 | 11.5 / 35.1 s | **52.0 / 94.1 s** | 206.6 / 211.0 s (mmap-slow) |
| R3's 29 length-cap cases | — | **RECOVERED_PASS 6 · RECOVERED_FAIL 14 (12 silent) · STILL_LENGTH_CAPPED 9 · OTHER 0** | — |
| migration A/B/C/D (vs Qwen A) | — | **9 / 6 / 9 / 24** (B: 3 length cap, 2 verifier, 1 wrong rc; C: 6 Qwen-silent, 2 Qwen no-output, 1 Qwen verifier) | 4 / 10 / 8 / 26 (R3) |
| R4 replay (`verifier`) | 52.1% at 25.0% strong calls, FN 21, $0.0553/success, p50 15.1 s | **64.6% at 29.2%, FN 16, $0.0534/success, p50 55.4 s** | 89.6% at 66.7%, FN 4, $0.0868, ~70 s |

**Surprises:** (1) the budget was inert for Qwen except in one case, and the whole
R3 → R3b Qwen shift is cross-session drift (0/48 digests at the same budget across
sessions) — the same-session diagnostic proves it; (2) Nemotron is byte-stable across
sessions (19/19), Qwen is not; (3) the ~80% silent-failure reduction was mostly the
cap — 12 of the 14 recovered-but-wrong cases are silent, so silent 4 → 16 (Qwen 21);
(4) S07 `reversal_race` never finishes for Nemotron even at 8 192 (4/4 capped, 24–34 k
reasoning chars); (5) at 8 192 Nemotron + R4 sends *more* to the frontier than Qwen + R4
(29.2% vs 25.0%) at essentially equal cost per success — the extra budget buys local
passes, not fewer strong calls.

## M4.7 Decision under the pre-registered rule (`scripts/r3b_selection_rule.py`): **Nemotron does NOT qualify — TEST untouched**

gate PASS (47/48, 48/48) · **A FAIL** (39/48 complete < 43) · B1 PASS (18 ≥ 14) · B2 PASS
(rc 31 vs 30, +1, tolerance 2) · **C FAIL** (silent 16 > 6) · **D FAIL** (cell B 6 > 5, vs A
and vs B) · E1 PASS (29.2% < 50%) · E2 PASS ($0.0534 ≤ $0.070) · F PASS (p50 52.0 s ≤ 75 s;
p95 94.1 s). Qwen remains the incumbent. TEST NOT RUN.

## M4.8 Milestone-4 summary

Completed: reconciliation · pre-registered rule (before any result; one definition
corrected before the Nemotron arm, recorded) · `--max-tokens` as the only factor, with
per-invocation telemetry · Qwen A → Nemotron → Qwen B at 8 192, one session per model,
plus a same-session Qwen 4 096 diagnostic · reproducibility gate · token-budget delta
per model with every historical length-cap case classified · migration matrix · silent-
failure analysis · unchanged R4 replay for both arms · rule applied mechanically ·
docs. Not touched: test, suite v2, scorer, verifier, prompt, R4 policy, QLoRA, learned
routing, suite v3.

Environment left: Qwen on 8082 (pid 586847, the R3b session), Nemotron on 8083 (pid
670208, `--no-mmap`, fit-target 1024), Switchyard 4000.

**Recommended next milestone (one): suite v3** — a deliberate benchmark release
(background settlements posted; S08 amount vs balance and the scorer FP;
`idempotency_key` as an observed id; the refutation-cue lookback), then re-baseline
Qwen, Nemotron and the frontier together with the generation budget fixed and recorded
for every arm. R3b closes the token-budget question: what remains between the two weak
models is model, not budget, and it is not enough on suite v2 to change the incumbent.

---
---

# Milestone 5 — Suite v3: a deliberate benchmark release, then re-baseline all three arms

Started 2026-08-17 ~22:00 UTC from HEAD `ce0d11d` (clean apart from the untracked goal
prompt `docs/FIS_Suite_v3_Benchmark_Release_Goal_Prompt.txt`, committed in the first
commit of this milestone). Governing document: that prompt; contract:
`docs/SUITE_V3_RELEASE_CONTRACT.md` (committed before any implementation or model run).

## M5.0 Reconciliation

Direct checks: `pytest` 202 passed + 1 skipped (opt-in live test); `fis-postgres` /
`fis-nats` healthy; Qwen pid 586847 on 8082, Nemotron pid 670208 on 8083 (`--no-mmap`),
Switchyard pid 44417 on 4000 — the M4.8 "environment left" state; GPU 14.6/16.3 GB with
both models resident. `learning.case_scores` holds all 32 recorded run_ids (incl. `R3-*`,
`R3b-*`, `R3b-qwen4096-dev`); `learning.trajectories` 1 916 rows. No git tags exist.

| Claim in prose | Repository / artefact state | Verdict |
|---|---|---|
| Goal prompt: HEAD `d99e21d`, clean | HEAD `ce0d11d` = `d99e21d` + one docs-only commit (dev-agent telemetry plan) | trivially stale |
| "Background settlements unposted in **7** of 12 classes (S01,S02,S05,S06,S07,S08,S10)" | `catalog._distractors()` (3 approved auths + settlements, never published, no `add_entry`) is called by exactly **6** classes: S01, S02, S05, S06, S07, S08. S10's unposted settlement is the injected gap; S03/S04/S09/S12 have no settlements; S11's 3 entries are direct `World.add_entry` (counter-shaped `le_<seed>_NN` ids, unlike every pipeline entry `le_<12hex>`). S05 and S08 have **zero** ledger entries. Distractors are generated AFTER `add_case`, so background approvals post-date the case (and, in S08, a frozen card). | prose over-counts by S10; two further background-realism facts (timing, S11 id shape) |
| "S08 declined amount > available balance" | `risk_hold` pins neither amount nor balance — independent draws (P≈7.3%): 3 of 24 corpus S08 worlds (dev `S08-2003007` 70 530>17 530, test `S08-3003007`, train `S08-1004007`); 5 of 24 counting distractor approvals. Balances are static everywhere; S05 sets `available_balance=150` and leaves `ledger_balance` at its draw. | confirmed, larger than one case |
| Scorer "polarity-aware, lookback stops at a sentence boundary; residual = post-positioned cue" | lookback-only 80 chars (probe: `insufficient funds is ruled out` → assertion). Two more mechanical defects: `rfind` returns −1 so the window is always cut ≥2 chars (`if cut > 0` dead, effective 78); leading-space cues (`" not "`, `" no "`, `" nor "`) are lost at sentence/JSON-field start — a persisted real FP exists (`E6b-G-both-dev` S05-2000004 `system_outage`). 6 tests, none post-positioned; 7 persisted forbidden hits to replay. | item C = three sub-defects |
| Verifier "harvests only `*_id` + `provider_ref`" | exact; `idempotency_key` is **already** returned by `get_webhook_history`, so the fix is harvesting; only S01 sets a non-null key; **no unit tests exist for the verifier module** | matches |
| "bump `EvalRun.suite_version`" | literal `"2"` at `run_eval.py:238`; not persisted in any DB column; `compare.py` marks v1 by a hard-coded run-id set; every analysis script joins `ground_truth.scenario_manifests` on `scenario_id`, and scenario_ids are seed-deterministic, so v2 rows would silently join v3 manifests; `<run>.weak` rows have no metadata; no corpus digest; determinism test in-memory only | V3.2 steps 4–5 need new mechanisms |
| Frontier "existing frozen configuration/budget" | `claude_cli.py` passes no `max_tokens`/`--effort`; frontier runs used prompt `baseline`, weak arms `cause_action_directed` | record as-is; carry the asymmetry unchanged |
| R1: "suite v3 canonicalises schema property order" | superseded by R0.1 (adapter rewrite, 48/48 identical) | not in v3 scope |
| `task-ontology.md` §4 forbidden-claim table (8) | code catalog forbids 13 (doc lacks `kyc_hold_active`, `merchant_overcharged_customer`, `duplicate_charge_confirmed`, `insufficient_funds`, `ledger_mismatch_detected`) | doc drift; fixed in the docs pass, no behaviour change |
| `projection.py` cites `test_projection_matches_the_live_pipeline` | no such test; the only projection/live check is `run.materialise()`'s id-set equality | gate needs a real check |
| `make reachability` | TEST split only | v3 gate needs both splits |

Environment side effect, recorded: an inspection agent ran `uv run pytest --collect-only`,
which created an untracked `uv.lock` (deleted) and re-synced `.venv` (sqlalchemy 2.0.52,
greenlet 3.5.5, pgvector 0.5.0, python-dotenv 1.2.3 reinstalled; `nemo-switchyard 0.2.0`
untouched; tests unchanged 202+1). None of these libraries sits on the model, scorer or
verifier path.

## M5.1 Release contract (commit `7d606cf`) — before any implementation

`docs/SUITE_V3_RELEASE_CONTRACT.md`: the four fixes A–D with the v2 defect, the
model-neutral rationale, the v3 change and its invariants; the suite-identity
infrastructure (E) needed for "v2 artefacts remain identifiable, cross-suite
subtraction rejected"; what is not changing; the deterministic gates; per-arm
budgets (Qwen 4096, Nemotron 8192, frontier CLI default) and the DEV/TEST procedure
— including, fixed in advance, that the frontier DEV sanity run doubles as the
frontier DEV baseline if no suite change follows it.

## M5.2 Implementation (one conceptual commit per item)

| commit | item | what changed | tests |
|---|---|---|---|
| `d7d25d5` | **A** background settlements | `_distractors` → `_background`: every background purchase is published (`settlement.created`, key `idem-<provider_ref>`) and posted by the consumers, in S01/S02/S05/S06/S07/S08 and S11 (whose `add_entry` postings were the last hand-written ledger rows — `World.add_entry` deleted, `ledger.entries` out of `_TABLES`); background precedes the case (after the injected activity in S01/S02/S06/S07 so the injected settlement stays within `_phase_two`'s first six refs; before the decline in S05/S08); mapper version recorded per event (`World.mapping_versions`, used by `project()` and `materialise()`), S06 rolls back to v4 after the injected settlement; S07 deliveries received after their events | 202 → 300 (+`test_scenario_invariants.py`, 69 corpus-wide invariants; pinned pipeline tests revised to select the injected events) |
| `1101930` | **B** amounts vs balances | S08 declined amount drawn strictly below `available_balance` (one draw, as before); S05 `ledger_balance = available_balance = 150`; snapshot semantics declared | failing-first on seed 2003007 (41 655 > 17 530 in the new world), then corpus-wide: S08 amount < balance, S05 amount > balance, available == ledger everywhere |
| `d7c93c1` | **C** polarity | same-sentence lookahead for predicate negations (`_LOOKAHEAD_CUES`), boundary trim only when a boundary exists (the `rfind(-1)+len` bug cut 2 chars off every window), sentence/field-initial cues (padding only at boundaries/edges), string-value opener as a boundary; `SCORER_VERSION = "3"` | 6 → 38 fixtures incl. the 4 persisted excerpts (S08-2001007 → refuted; the two S08-2003007 hedges → asserted; E6b-G S05-2000004 → refuted); the two hits without excerpts are unrecoverable and recorded as such |
| `b7ff7f3` | **D** idempotency_key | `collect_observed_ids` harvests `idempotency_key` (`_OBSERVED_ID_KEYS`); `VERIFIER_VERSION = "3"` | first verifier unit tests (17): every check known-good/known-bad, the S01 key case, fabrication, gold fields never harvested |
| `082fa8a` | **E** suite identity | `fis_platform/suite.py` (`SUITE_VERSION = "3"`, `ONTOLOGY_VERSION = "1"`, `require_comparable`), migration 006 (`suite_version` on manifests and score rows; backfill 96 rows → 1, 1 635 → 2, 288 manifests → 2), runner guards (corpus/code mismatch; run-id reuse across suites; suite on every score row incl. `.weak`; `suite_version`/scorer/verifier/ontology/prompt/workflow versions, `git_head`, `corpus_digest` in `runtime_context`), suite-aware `compare.py`, `--allow-cross-suite` refusal in all six analysis scripts, `scripts/corpus_digest.py` + `scenarios/manifests/corpus_v3.json`, `make reachability` on test **and** dev, `make corpus-digest` / `corpus-determinism`, V3 baseline targets | `test_corpus_live.py` (DB-gated: projection == live rows for all 288, no entry without a cause, S01 bundle contains and harvests the key, cross-suite refusal, runner guard) |
| `acdabac` | V3.3 | gold-answer reference checks | 2 |

## M5.3 Deterministic release gates — all PASS (at `082fa8a`/`acdabac`)

| gate | result |
|---|---|
| tests | **354 passed, 1 skipped** (opt-in live) |
| corpus regenerated | `make corpus` 3.8 s: 96/48/144; 720 events published, 672 ledger entries; projection == live ids asserted per scenario |
| corpus digest | `f9eba238f004d35afe86b3ef681e8e20d0025d65dc1107db3daa6176b3ae3fc8` (train `15e45cde…`, dev `c15ac2ca…`, test `970e98c3…`) → `scenarios/manifests/corpus_v3.json` |
| determinism | second full regeneration: **DETERMINISTIC — identical** |
| reachability | test 96 cases 12/12 ceiling 1.000, 0 capped; dev 48 cases 12/12 ceiling 1.000, 0 capped |
| projection/live rows | 288/288 identical on status, mapping_version, amount, reference, posted_at, posting order |
| scenario invariants | 88 (69 A/B + reference sanity) over every corpus seed |
| scorer/verifier fixtures | 38 polarity + 17 verifier |

Suite v2 artefacts: `learning.*` untouched (32 run_ids, 1 916 trajectories); every pre-006
score row now labelled `suite_version` 1 or 2; `evals/reports/*.json` untouched.

## M5.4 One correction before the sanity run counted (commit below)

Reviewing the fixed-evidence bundle for S06-2000005 and S08-2003007 through the real
broker (not a model result): the injected S06/S07/S10 provider events were still
published without an idempotency key (as in v2) while the new background settlements
carry one — "the settlement without a key" would have been a spurious discriminator
for the injected event. Every provider settlement/reversal event now carries a safe
key except S02's, whose defect *is* the missing key
(`test_the_idempotency_key_never_distinguishes_the_injected_event`). The frontier
sanity run had 4/48 cases on the pre-fix corpus; it was stopped, its 4 rows and JSON
removed (my own aborted run of minutes earlier, not a historical artefact), the corpus
regenerated (digest `1e7c5278ba1f4cc1cc96fa8a1f04946ab622270eaba4c5671274c21e9d39e528`,
deterministic on the second regeneration, reachability 96/96 + 48/48 clean, 368
tests) and the sanity run restarted from scratch.

## M5.5 Frontier DEV sanity run — clean; Suite v3 FROZEN

`E4-v3-dev` (arm V3, `claude-frontier`, prompt `baseline`, CLI 2.1.234 default budget,
effort unset; 22:40–23:35 UTC): **48/48 strict all-pass**, root cause 48/48, evidence
recall 1.000, verifier 48/48, unsupported 0, forbidden 0; wall p50 36.9 s / p95 60.1 s;
180 033 output tokens; reference cost $5.57. Every class 4/4. Under suite v2 the same
arm on the same dev seeds had four failures, all of them the harness cases R2 flagged
(S06-2003005 compound reading, S08-2001007 scorer FP, S08-2003007 amount > balance,
S01-2001000 verifier gap) — none recurs, and no new disagreement, impossible scenario
or surprising class behaviour appeared. **No harness defect found; the suite is
unchanged after the sanity run.**

Two operational notes, neither a suite change: (1) three cases (S09-2003008,
S10-2000009, S11-2002010) hit an upstream API 500 through the CLI, and the adapter
died in a pydantic error on the numeric status instead of surfacing it — fixed in
`3517466` (error string + `investigate()` raises so the runner skips the case
unpersisted and `--resume` retries), then the three cases were resumed and passed;
cases 1–45 ran at `00ee124`, 46–48 at `3517466` (transport-only difference,
recorded in `runtime_context.git_head`). (2) `evals/reports/E4-v3-dev.json` holds
only the resumed remainder (a runner limitation recorded in M5.0); `learning.*` is
the record.

Per the contract (§ 6, fixed before any run) this run **is** the frontier DEV
baseline. Freeze marker: tag `suite-v3` on the release commit; identity —
suite 3, corpus `1e7c5278ba1f4cc1cc96fa8a1f04946ab622270eaba4c5671274c21e9d39e528` (train `d9d1570e6b70…`), scorer 3, verifier 3, ontology 1,
prompt 1, evidence FIXED_EVIDENCE, llama.cpp `b1-9b05354`, claude CLI 2.1.234.

## M5.6 DEV baselines (design A; `make eval-v3-dev`, 23:39–00:56 UTC 2026-08-18; HEAD `7764601` = tag `suite-v3`)

Qwen session pid 586847 (the R3b session, still up), Nemotron restarted with unchanged
flags right before its arm (pid 1000667; probe on train case S05-1000004: 87.6–88.8
tok/s, TTFT 2.2 s), each endpoint primed, nothing else on 8082/8083, `FIS_LIVE_TESTS`
unset. Frontier = the sanity run (M5.5). Every trajectory carries suite 3, scorer 3,
verifier 3, corpus `1e7c5278…`, `git_head`, server session and fingerprint `b1-9b05354`.

| arm | run | max_tokens | all-pass | rc | evidence | verifier | unsup | forb | no-output | cap hits | wall p50 / p95 | out tokens | resource |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen A | `V3-qwen-dev` | 4096 | **17/48 (35.4%)** | 30 | 0.611 | 33 | 9 | 0 | 9 (all schema) | 1 (S07-2003006) | 12.8 / 41.7 s | 65 588 | 7.7 GB VRAM, RSS 8.7 GB |
| Nemotron | `V3-nemotron-dev` | 8192 | **23/48 (47.9%)** | 31 | 0.675 | 36 | 0 | 0 | 12 (10 `length` + 2 schema) | 10 | 53.2 / 96.0 s | 238 293 | ~8 GB VRAM beside Qwen (card 15.6/16.3 GB), RSS 13.0 GB |
| Qwen B | `V3-qwen2-dev` | 4096 | 17/48 | 30 | 0.611 | 33 | 9 | 0 | 9 | 1 | 12.1 / 40.9 s | 65 588 | same session |
| frontier | `E4-v3-dev` | CLI default | **48/48 (100%)** | 48 | 1.000 | 48 | 0 | 0 | 0 | 0 | 36.9 / 60.1 s (TTFT p50 9.4 s) | 180 033 | $5.57 reference (floor) |

**Reproducibility gate — PASS:** Qwen A vs B 47/47 identical output digests (the 48th
pair has a no-output side without a digest), 48/48 identical outcomes, identical
token counts and stop reasons. All-pass 17 = 17. Comparison valid.

## M5.7 Pairwise analysis (DEV, descriptive; `make v3-dev-analysis`)

| pair | A both pass | B first pass / second fail | C first fail / second pass | D both fail |
|---|---|---|---|---|
| Qwen × Nemotron | 13 | **4** (S02-2001001, S04-2003003, S06-2000005, S07-2000006 — all Nemotron `length` no-outputs) | 10 (S02, S03 ×2, S06 ×2, S08 ×2, S10 ×3 — 7 were Qwen silent failures) | 21 |
| Qwen × frontier | 17 | 0 | 31 | 0 |
| Nemotron × frontier | 23 | 0 | 25 | 0 |

No weak>strong inversion exists (the frontier passes every dev case), so no
harness review was triggered by an inversion; the four B cases were reviewed and are
budget/contract failures of the candidate (still inside `<think>` at 8 192 tokens),
not harness. Silent failures (verifier-clean, wrong): Qwen 16, Nemotron 13 (7 Qwen-silent
cases pass under Nemotron, 7 stay silent, 2 become loud, 6 new). Per class (Qwen /
Nemotron / frontier of 4): S01 0/0/4 · S02 2/2/4 · S03 0/2/4 · S04 1/0/4 · S05 4/4/4 ·
S06 2/3/4 · S07 1/0/4 · S08 2/4/4 · S09 4/4/4 · S10 1/4/4 · S11 0/0/4 · S12 0/0/4.
Failure dimensions of the two weak arms: Qwen — 9 no-output (schema), 9 unsupported
claims (fabricated ids such as `ver_000000`, `proc_2000010_01`), 9 evidence-only,
5 root-cause; Nemotron — 12 no-output (10 cap), 8 evidence-only, 5 root-cause, 0
unsupported.

## M5.8 Unchanged R4 cascade, by replay (`verifier` policy vs `E4-v3-dev`)

| weak arm | cascade all-pass | weak acceptance | strong calls | rescue | unnecessary | routing FN | cost / attempt | cost / success | wall p50 | local out tokens |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen + R4 | **32/48 (66.7%)** | 68.8% | 15 (31.2%: 9 no-output, 6 unsupported) | 15/15 | 0 | 16 | $0.0405 | **$0.0608** | 16.7 s | 65 588 |
| Nemotron + R4 | **35/48 (72.9%)** | 75.0% | 12 (25.0%: all no-output) | 12/12 | 0 | 13 | $0.0330 | **$0.0453** | 54.7 s | 238 293 |
| strong-only | 48/48 | — | 48 | — | — | — | $0.1160 | $0.1160 | 37.2 s | — |

The gate's blind spot is unchanged in kind: every routing false negative is a
verifier-clean answer wrong on evidence recall or root cause.

## M5.9 TEST — once per frozen arm (`make eval-v3-test`, 00:57–04:15 UTC 2026-08-18; refuses to run without tag `suite-v3`)

Qwen in its DEV session (pid 586847); Nemotron restarted + probed (87.7–88.3 tok/s, pid
1045208); frontier last. Nemotron/frontier trajectories carry `git_head 2bbc0a1-dirty`
— uncommitted documentation drafts only; `git diff suite-v3 -- . ':!docs'` is empty.

| arm | run | all-pass | rc | evidence | verifier | unsup | forb | no-output | cap | wall p50/p95 | out tokens | cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen 4096 | `V3-qwen-96` | **27/96 (28.1%)** | 68 | 0.628 | 74 | 12 | 0 | 13 | 1 | 12.9 / 33.8 s | 129 910 | $0 |
| Nemotron 8192 | `V3-nemotron-96` | **48/96 (50.0%)** | 65 | 0.713 | 75 | 2 | 0 | 19 (15 `length`) | 15 | 55.8 / 94.1 s | 480 810 | $0 |
| frontier | `E4-v3-96` | **95/96 (99.0%)** | 96 | 1.000 | 96 | 0 | 0 | 0 | 0 | 37.6 / 61.0 s | 354 059 | $10.82 |
| Qwen + R4 (replay) | — | **48/96 (50.0%)** at 22 strong calls (22.9%), rescue 21/22, unnecessary 0, FN 47 | | | | | | | | 15.4 s | | $0.0513/success |
| Nemotron + R4 (replay) | — | **69/96 (71.9%)** at 21 strong calls (21.9%), rescue 21/21, unnecessary 0, FN 26 | | | | | | | | 56.1 s | | $0.0380/success |

Pairwise A/B/C/D: Qwen×Nemotron 21/6/27/42; Qwen×frontier 27/0/68/1;
Nemotron×frontier 48/0/47/1; no inversion. The one frontier miss (S12-3002011:
correct label, 4/4 evidence, action `replay_webhook`) is recorded, not acted on. No
tuning, no re-run, no second look.

## M5.10 Milestone-5 summary and completion checklist

Completed: reconciliation · pre-registered contract before implementation · A/B/C/D
one commit each with tests · suite identity + migration 006 · corpus regenerated,
digest recorded, deterministic on second regeneration · reachability test+dev clean ·
projection == live rows for all 288 · 88 scenario invariants incl. gold reference ·
scorer/verifier fixtures · frontier DEV sanity 48/48 (no defect) · freeze tag
`suite-v3` · DEV baselines (Qwen A/Nemotron/Qwen B; gate 47/47, 48/48) · pairwise
matrices · unchanged R4 replay · TEST once per arm · release report
(`SUITE_V3_RELEASE_REPORT.md`) · experiment log, HANDOFF, architecture, ontology,
routing-experiments updated. Not done, by design: prompt tuning, learned routing,
QLoRA, ontology expansion, any change after a score was seen; the R3b verdict stands.

| goal-prompt criterion | status |
|---|---|
| repo state reconciled | ✔ M5.0 |
| release contract committed before implementation/model runs | ✔ `7d606cf` |
| changelist limited to genuine benchmark defects | ✔ A–D (+ E bookkeeping) |
| A background settlements fixed + tested | ✔ `d7d25d5`, `00ee124` |
| B S08 amount/balance fixed + tested | ✔ `1101930` |
| C refutation polarity fixed + tested | ✔ `d7c93c1` |
| D idempotency_key observability fixed + gold-leak tested | ✔ `b7ff7f3` |
| suite version 3 | ✔ `082fa8a` |
| corpus regenerated under normal reset rules | ✔ (`make corpus`, `learning.*` untouched) |
| reachability clean DEV and TEST | ✔ 48/48, 96/96, 0 capped |
| deterministic regeneration verified | ✔ digest identical |
| scenario invariants pass | ✔ 88 |
| projection/live agreement | ✔ ids at generation + rows for 288 |
| scorer/verifier reference fixtures pass | ✔ |
| frontier DEV sanity, no unresolved harness defect | ✔ 48/48 |
| Suite v3 frozen (commit/tag) | ✔ `suite-v3` = `7764601` |
| Qwen / Nemotron / frontier DEV baselines | ✔ 17/48 · 23/48 · 48/48 |
| pairwise migration analysis | ✔ |
| existing R4 cascade replayed unchanged | ✔ |
| exactly-once frozen TEST baselines | ✔ 27/96 · 48/96 · 95/96 |
| no prompt tuning / learned routing / QLoRA / ontology expansion | ✔ none |
| Suite v2 artefacts intact | ✔ `learning.*` rows untouched, labelled |
| full automated tests pass | ✔ 368 + 1 skipped |
| experiment log / handoff / release report updated | ✔ |
| working tree clean | ✔ at the final commit |

---

# Milestone 6 — R5: learned silent-failure routing (2026-08-18)

Governing document: `docs/FIS_R5_Learned_Silent_Failure_Routing_Plan.html` (committed
`fc1c18e`). Contract: `docs/R5_EXPERIMENT_CONTRACT.md`. Report:
`docs/R5_LEARNED_ROUTING_REPORT.md`. Timing is logged per phase at the end (M6.x).

## M6.0 Reconciliation (04:55–05:12 UTC)

Direct checks: HEAD `47723b2` on `main`, clean but for the untracked R5 plan HTML;
`git diff suite-v3 -- . ':!docs'` empty (code + corpus identical to the freeze);
`fis-postgres`/`fis-nats` healthy; Qwen pid 586847 on 8082 (the very session that made
`V3-qwen-dev` and `V3-qwen-96`), Nemotron pid 1045208 on 8083 (the `V3-nemotron-96`
session, idle >24 h); GPU 15.6/16.3 GB with both resident.

| item | repository / artefact state |
|---|---|
| Suite v3 identity | `SUITE_VERSION "3"`, tag `suite-v3` → `7764601`, corpus `1e7c5278…9d39e528` (train `d9d1570e…`, dev `5d5c94b0…`, test `8deea4a2…`), scorer 3 / verifier 3 / ontology 1 / prompt 1 |
| suite-3 runs in `learning.case_scores` | DEV: `V3-qwen-dev` 17/48, `V3-qwen2-dev` 17/48, `V3-nemotron-dev` 23/48, `E4-v3-dev` 48/48; TEST: `V3-qwen-96` 27/96, `V3-nemotron-96` 48/96, `E4-v3-96` 95/96 — all goal-prompt figures match the DB |
| TRAIN split | 144 scenarios (12 × 12, seeds 1,000,000–1,999,999), in the v3 corpus, reachable |
| TRAIN trajectories | **none, for any arm, any suite** → acquire Qwen + Nemotron on TRAIN under the frozen configuration (`make eval-r5-train`); frontier not required for labels, not acquired |
| decision point | `cascade.py::investigate_cascade`: after `investigate()` (parse + `verify()`), `signals_from` → `should_escalate` → `RouterDecision`, before any strong call |
| R4 inputs | `EscalationSignals(produced_output, verifier_passed, unsupported_claims, violations)` from `traj.verification` only |
| where gold enters | `score_case(manifest=…)`; analysis scripts join `ground_truth.scenario_manifests`; guards `GOLD_FEATURE_NAMES`, `test_routing_no_gold_leak.py`, `fis_tools` role |
| **mismatch (a): the answer body was never persisted** | `investigate()` keeps only `output_digest`; server logs hold timings only. For the frozen DEV/TEST arms the answer-structure family reduces to length (`content_chars`, `output_tokens`), the verifier's per-check booleans, and the model's own `root_cause.label` / `recommended_next_action` (echoed verbatim by the scorer as `said …`). Fact/citation/hypothesis counts and confidence are unrecoverable for DEV/TEST. R5's primary feature set is thin on the verifier-clean subset; a null result is a live outcome. Migration 007 (`learning.model_outputs`) keeps the parsed answer from the TRAIN acquisition onward (best-effort, beside the trajectory) — exploratory TRAIN-only analysis, and so the next suite does not lose it again |
| mismatch (b): case `category` | model-visible, but a class identifier for 4 of 8 categories → excluded from the eligible allowlist; exploratory class-prior comparator only |
| mismatch (c): FIXED_EVIDENCE tool trajectory | deterministic per case: 0 errors, 0 retries; family C is bundle shape (`n_tool_calls` ∈ {9,10,11,12}, webhook/vendor query counts, `input_tokens`) |
| mismatch (d): no numpy/scikit-learn | routers are stdlib logistic regression (L2, Newton) + CART depth ≤ 3, JSON artifacts, stable digests |
| grouping | seeds are independent draws per class (`lo + i·1000 + class_idx`) → group = class, leave-one-class-out CV (conservative vs deployment; seed-stratified CV exploratory) |
| Nemotron latency drift | idle `--no-mmap` degrades to ~50 tok/s; restart + train-case probe before its arm as in Suite v3; latency features are session-fragile, tokens are the invariant |

No scientific blocker. `fc1c18e`: plan committed, migration 007, `eval-r5-train*`
targets. `e3b8066`: contract skeleton (numbers amended after TRAIN CV, before DEV).

## M6.1 TRAIN acquisition (`make eval-r5-train`, started 05:16 UTC)

Qwen `R5-qwen-train` (4096, `cause_action_directed`, primed, session pid 586847) then
Nemotron `R5-nemotron-train` (8192, restarted with unchanged flags, probed on
S05-1000004, primed). Dataset acquisition only; the answer body persists to
`learning.model_outputs` for producing cases (verified on the first S02 rows).

Qwen arm done 05:16–05:53 UTC (144 cases, 41/144 = 28.5 % all-pass; 117 answer bodies
persisted). Nemotron restarted 05:54 (probe 77.6–78.2 tok/s vs 87–88 in Suite v3 —
recorded), primed, arm 05:55 → ~08:2x UTC.

## M6.2 Tooling and pre-registration (05:20–06:25 UTC; commits `54c6fa9` … `b078d4c`)

`fis_platform/routing/features.py` (schema v1, 58-name allowlist, forbidden names,
deterministic digest; 43 leak-guard tests, import ban extended), `learn.py` (stdlib L2
logistic Newton, CART ≤ 3, AUC/AP/Brier/log-loss, LOGO + stratified folds; 26 tests),
migration 008 `learning.routing_decisions`, `r5_dataset.py` (echo reconstruction of the
answer's label/action, checked equal to the persisted TRAIN bodies on 117/117 Qwen
cases), `r5_train.py`, `r5_replay.py`, `r5_oracles.py` (R4 reproduction gate: DEV AGREES
with the release report on all 23 fields; release-report erratum § 11 recorded for the
Qwen FN prose split), `r5_amend_rule.py`. Adversarial audit (5 lenses + synthesis) before
DEV: feature boundary and learner arithmetic HOLD; the plan's "classes cannot appear
indirectly" does NOT hold — four case constants (`n_tool_calls`, webhook/vendor query
counts, `input_tokens`) identify the class for 45/48 DEV cases — recorded in contract
§ 6, with `prior_class_ceiling` / `lr_behavior` comparators added; pooled LOGO AUC is
null-biased under class-clustered labels → SECONDARY (seed-stratified) protocol
registered in § 12a before DEV; the τ rule's degeneration at unsafe-rate ≥ 0.5 noted;
TEST reading pre-registered (§ 14). Selection state machine hardened after the user's
invariant list (one selection record per model, winner-only freeze, unlock bound to the
recorded winner + lineage + one look per model, append-only, no rollback; 17 temp-registry
tests). Full suite 534 passed + 1 skipped.

## M6.3 Qwen TRAIN development (`R5-qwen-train`, TRAIN only)

R4-accepted subset 105/144, 64 unsafe (0.61); P(unsafe | class) 0.09–1.0, eight of eleven
classes ≥ 80 % one label. Grouped (primary) OOF AUC: `lr_full` 0.238, `lr_core` 0.253,
`tree` 0.515 — none passes the gate. Stratified (secondary): `lr_full` 0.901 (τ* 0.60),
`lr_core` 0.821 (0.60), `tree` 0.822 (0.70) — all pass; `prior_class_ceiling` 0.892,
`lr_answer` 0.904, `lr_behavior` 0.909, answer-structure (TRAIN bodies) 0.873 / 0.685 —
the router is within 0.01 AUC of the class-identity ceiling. § 12a-Q: Δ_util 0.646
(uncapped secondary; 0.20 capped), E_max 6, K = 4.

## M6.4 Qwen DEV replay + selection (one look, `503b042`)

R4 32/48 @ 31.2 %, FN 16. Secondary candidates at τ*: `lr_full` 47/48 @ 70.8 % (FN 1,
unnec 4, caught 15/16), `lr_core` 44/48 @ 68.8 % (FN 4, unnec 6), `tree` 39/48 @ 56.2 %
(FN 9, unnec 5, caught 7/16); all three PASS R1–R3 (none under the skeleton's 50 % cap).
Pre-registered tie-break "fewer frontier calls" freezes **`r5-qwen-tree-stratified-v1`**
(τ 0.70, digest `aa13e045…`) — the least-escalating survivor, not the best; on DEV its 7
catches in 12 escalations are not distinguishable from chance (hypergeometric p 0.31;
`lr_full` 15/19: p 3e-5; class ceiling 13/18: p 0.004). Recorded, not re-selected.

## M6.5 Qwen TEST — exactly once (`dbf5414`)

`r5-qwen-tree-stratified-v1` on `V3-qwen-96` vs `E4-v3-96`: all-pass **75/96 (78.1 %)** vs
R4 48/96 (50.0 %); routing FN 47 → **20** (27 caught: 22 evidence, 5 root cause);
unnecessary 6; utilization 57.3 % (R4 22.9 %, oracle 70.8 %, always-escalate 100 %);
$0.0799/success (R4 $0.0513, strong $0.1139); wall p50 37.6 s; classifier AUC 0.762 on
the accepted subset; catches 27/33 vs base 0.64: p 0.003. Pre-registered TEST reading:
**CONFIRMED** (K_test 12). No sweep computed on TEST.

## M6.6 Independent challenge of the interpretation (06:40–06:57 UTC, Fable reviewer)

Verdicts on the Qwen half: the "template difficulty" reading holds but was over-evidenced
(pooled LOGO is null-biased, so the per-fold LOGO diagnostic — `scripts/r5_diagnostics.py`,
now in the report — is the evidence; "no detectable within-template signal beyond the S02
said-label; TRAIN has little power to find a small one" is the defensible sentence);
applying the tie-break as written was the discipline-consistent action but the contract's
"fewer frontier calls" is one of two readings of the plan's clause and the other would have
frozen `lr_full`; the secondary protocol and the uncapped R2 were each necessary for any
selection and moved toward permitting a pass — stated as such in the report; "CONFIRMED on
TEST" certifies non-degeneracy, not information (a random escalator of the same size meets
the reading with p ≈ 0.59); the R6 premise (template-clean Nemotron band) is contradicted by
the three-tier oracle. All required wording changes applied; the recommendation was
rewritten after Nemotron's numbers.

## M6.7 Nemotron TRAIN development, DEV selection, TEST (08:59–09:15 UTC; `3e04dc7`, `af199a5`, `5d277f6`)

TRAIN (`R5-nemotron-train`, 05:55–08:59): 66/144 = 45.8 % all-pass, R4-accepted 104,
unsafe 38 (0.365), 114 answer bodies (echo == body 114/114). Primary protocol: nothing
passes the gate (LOGO AUC 0.20/0.24/0.22). Secondary: `lr_full` 0.919 (τ* 0.55), `lr_core`
0.656 (0.50), `tree` 0.849 (0.50) eligible; class ceiling 0.936 *above* all; within-class
`content_chars` AUC 0.26 (a genuine within-template signal). § 12a-N: Δ_util 0.469, E_max
7, K 4. DEV (one look): R4 35/48 @ 25.0 %, FN 13; `lr_full` 45/48 @ 50.0 % (FN 3, unnec 2,
AUC 0.953 — above the class ceiling 0.876), `lr_core` 40/48 @ 39.6 % (FN 8, unnec 2), `tree`
44/48 @ 56.2 % (FN 4, unnec 6); exploratory `lr_behavior` 48/48 @ 60.4 %; tie-break freezes
**`r5-nemotron-lr_core-stratified-v1`** (τ 0.50). TEST (once): 74/96 (77.1 %) vs R4 69/96
(71.9 %), FN 26 → 21 (5 caught: 4 rc, 1 ev), unnecessary 6, utilization 33.3 % (oracle
49.0 %), $0.0509/success, AUC 0.557 on the accepted subset — **NOT CONFIRMED** (K_test 7).
Three-tier oracle at the unlock (TEST): Qwen-sufficient 27, Nemotron-sufficient 27,
frontier-required 41, unresolved 1; R4 reproduction on TEST AGREES on every field (one
transcription error in the script's expected table — strong-only cost/attempt, which the
report never stated — corrected in place, `2f40c42`).

## M6.8 Timing

reconciliation 04:55–05:12 · tooling + contract 05:12–05:35 · Qwen TRAIN acquisition
05:16–05:53 · audit 05:33–06:24 · Qwen TRAIN CV / amendment / state machine / DEV / TEST
05:56–06:25 · Nemotron acquisition 05:55–08:59 · Nemotron CV / DEV / TEST / oracles
09:00–09:15 · documentation interleaved, final commits by 09:10. **Total ≈ 4 h 15 min** (04:55–09:10 UTC), of which
3 h 41 min was local inference (288 calls); 0 frontier calls; 0 TEST model calls; every
DEV/TEST number, oracle, reproduction and Pareto sweep by offline replay.

## M6.9 Milestone-6 summary and completion checklist

| goal-prompt criterion | status |
|---|---|
| repository and Suite v3 identity reconciled | ✔ M6.0 |
| TRAIN/DEV/TEST trajectory availability documented | ✔ M6.0 (TRAIN acquired M6.1/M6.7) |
| R5 experiment contract committed before DEV candidate scoring | ✔ `e3b8066`, `76a7ec1`, `4b10da0`, `3e04dc7` (each before the corresponding DEV replay) |
| production routing decision point identified | ✔ `cascade.py::investigate_cascade` after `investigate()` |
| RoutingFeatureSnapshot implemented and versioned | ✔ schema v1, 58 names |
| explicit feature allowlist | ✔ `FEATURE_ORDER` + `FORBIDDEN_FEATURE_NAMES` |
| gold/scenario leakage tests pass | ✔ 43 + 64 + 17 (state machine) |
| grouped memorization guard | ✔ leave-one-class-out primary CV; class key offline only |
| Qwen / Nemotron post-answer oracles | ✔ DEV and TEST (report § 4) |
| three-tier cheapest-sufficient oracle (descriptive) | ✔ TRAIN/DEV/TEST |
| existing R4 reproduced from frozen trajectories | ✔ DEV and TEST, every field |
| TRAIN dataset without TEST leakage | ✔ digests `d4d3c09d…`, `fdb015a8…` |
| logistic + tree baselines per local model | ✔ both protocols |
| candidate development TRAIN only | ✔ |
| DEV replay: classifier + system + silent metrics, Pareto | ✔ report § 7–8 |
| pre-registered DEV selection rule applied exactly | ✔ (tie-break outcome recorded, not re-selected) |
| ≤ 1 learned policy per local model frozen | ✔ `r5-qwen-tree-stratified-v1`, `r5-nemotron-lr_core-stratified-v1` |
| artifacts with stable digests + schema version | ✔ registry, fail-closed verification |
| TEST sealed for policies failing DEV; exactly one replay for qualified ones | ✔ unlock records, append-only |
| no new TEST inference | ✔ 0 |
| Suite v3 / models / prompts / evidence / verifier unchanged | ✔ (`git diff suite-v3 -- fis_platform/verification scenarios evals/scorers services/ai_orchestrator/prompts.py` empty) |
| no three-tier learned routing, no QLoRA | ✔ none |
| routing telemetry persisted | ✔ `learning.routing_decisions` (17 policies × 48 DEV, 2 × 96 TEST per model) |
| timing documented | ✔ M6.8 |
| full automated tests pass | ✔ 534 + 1 skipped |
| documentation updated | ✔ report, contract, experiment-log, HANDOFF, routing-experiments, architecture |
| working tree clean except intentional artifacts | ✔ at the final commit |

---

# Milestone 7 — R6 modern local specialist refresh (2026-08-18 20:59 UTC → 2026-08-19 ~22:30 UTC)

Plan `FIS_R6_Modern_Local_Specialist_Refresh_Plan.html`; contract `R6_EXPERIMENT_CONTRACT.md`;
report `R6_MODERN_LOCAL_SPECIALIST_REFRESH_REPORT.md`; record `learning/registry/r6/`.
Orchestrated by Fable; Opus subagents for inspection and the provenance module; three Fable
independent reviews (provenance/state audit, contract/gates, final challenge).

## M7.0 Read-only reconciliation (bootstrap, before `/goal`)
Six inspectors + a critic over docs, Suite v3 freeze, registry surfaces, code surface, the R5
state machine and runtime identity; SHA-256 of all five local GGUFs recomputed and matched to
the packet and to the upstream LFS digests (Nemotron's pin recovered: bartowski file-upload
commit `be042bfc`; the upstream file had been re-uploaded); `Ternary-Bonsai-27B-Q2_0.gguf`
moved from `~/archive/bonsai-eval/models` to `~/infra/models`; Q2_0 block-geometry divergence
between upstream and Prism found (same type id 42, QK 64 vs 128); two "Bonsai" mislabels found;
Qwen3.5-9B confirmed absent. Report returned, stop, `/goal` received 20:59 UTC.

## M7.1 Provenance hardening (21:00–21:36 UTC; `b2f85d5`, `ac81825`)
`fis_platform/provenance.py` (GGUF reader, digests, records, `R6Registry`, transition table),
`scripts/r6_registry.py`, `scripts/r6_pilot.py`, `scripts/r6_metrics.py`, `fis_platform/r6_gates.py`,
`run_eval --candidate` + `--scenario-ids-file`, gateway manifests, `infra/serve-r6.sh`, Makefile
targets; Qwen3.5-9B downloaded from the pinned revision and digest-verified (21:05 UTC); six
artifacts, two runtimes, three generation configs, four candidates registered; historical
8082/8083 server args captured from `/proc`; contract pre-registered (pilot, cap rule, quant
rule, Bonsai eligibility, numeric DEV gates from historical DEV metrics only) and committed
before any pilot. Registry-aware clean-tree rule (only `learning/registry/r6/**` may be ahead
of HEAD) made normative.

## M7.2 TRAIN (21:36 UTC → 05:46 UTC; 8.2 h)
Historical servers stopped (GPU idle baseline 1,734 MiB). Qwen3.5-9B pilot 13/36 (10 cap hits,
p50 68.5 s), probe 12/12 identical, TRAIN_COMPATIBLE. Qwen3.8 Q3_K_M: `--fit` probe → 66/66
layers fit, frozen `-ngl 99`; pilot 20/36 (15 cap hits, p50 288.6 s, 28 tok/s). UD-Q3_K_XL pilot
16/36 (18 cap hits, 38.8 tok/s) → WITHDRAWN by § 7 rule 1. Q3_K_M cross-session probe 12/12
identical. Bonsai on Prism: compat probe OK (json_schema, timings, fingerprint, reasoning);
pilot 15/36 (4 cap hits, p50 72 s, 9.2 GiB); probe 12/12 identical (interrupted after 8 by a
tool timeout, resumed same session). Every cap calibration → 8192 (no allowed cap within
tolerance). Independent audit A (provenance/state) ran during the Q3_K_M pilot — no blockers,
4 must-fixes landed before DEV (`364428b`): mandatory `--candidate`, family guard at freeze
and in `require_state`, running-server binding (exe + mapped libs + env), registry reset
guards + ledger-vs-git prefix check + DB one-look check, untracked-aware cleanliness,
finished-full-run requirement, session-consistent resume, exact pid matching.

## M7.3 Freeze (05:46–06:05 UTC; `b4e9095`, `f4ae5f5`)
Contract § 10 frozen (three execution systems, run ids, gates digest `6b9699fe…`);
CONTRACT_FROZEN ×3 bound to blob `0604d661…`. Independent review B (contract/gates) — no
blockers; follow-ups landed: no-output erratum (Qwen3-8B DEV no-output is 9 by § 11's
definition; thresholds unchanged), resumed-run counting, gate-verdict binding + re-derivation,
fresh-session guard, wording/disclosure/fallback rows (§ 17).

## M7.4 DEV (06:05–11:24 UTC; 5.5 h)
Qwen3.5-9B 23/48 → DEV_REJECTED (p50 58.1 s > 38.6 s; no-output 10 > 8; all-pass clause met).
Qwen3.8 Q3_K_M 25/48 → DEV_QUALIFIED (clause 1; 22 cap-hit no-outputs, 1 silent).
Bonsai 21/48 → DEV_QUALIFIED (floor; memory 0.61×, p50 0.30× of Qwen3.8). Verdicts produced
by `scripts/r6_dev_record.py` (the gate function, re-derived by the registry).

## M7.5 TEST (11:24 UTC → 20:35 UTC)
Unlocks re-hashed the artifacts and bound DEV result digests + contract blob. Qwen3.8 Q3_K_M
TEST 47/96 (47 cap hits, 2 silent; 6.2 h). Bonsai TEST 34/96 (41 silent;
2.3 h). Both TEST_EVALUATED (terminal). Qwen3.5-9B's TEST never opened.

## M7.6 Offline analysis
`scripts/r6_analysis.py` (DEV and TEST JSON under `learning/registry/r6/analysis/`): per-arm
quality/failure shape/runtime, unchanged R4 replay, post-answer oracle, pairwise A/B/C/D and
dominance, unique successes, tier coverage, by-class. Headline: Qwen3.8 + unchanged R4 = 93/96
TEST (FN 2, util 49 %); no local arm dominates another; Nemotron complementary (12 unique).

## M7.7 Report, docs, review C, tests, clean tree
Report `R6_MODERN_LOCAL_SPECIALIST_REFRESH_REPORT.md` (one screen, provenance, TRAIN/DEV/TEST tables from `learning/registry/r6/analysis/*.json` via `scripts/r6_report_tables.py`, R4/oracle/overlap/dominance/tiers, silent-failure and residual-failure analysis, accounting, one next milestone); HANDOFF, experiment-log, routing-experiments, architecture (provenance registry section, port table) updated; independent review C (final challenge of the dominance/substrate conclusions) — dominance/complementarity SUPPORTED, substrate/next-milestone SUPPORTED WITH CHANGES (truncation description corrected — 16/47 TEST cap hits were cut inside the JSON answer; selection-effect caveat on "right when it finishes"; Bonsai silent-burden sentence corrected to DEV-largest / TEST-second; two-local cascade quantified 77/96 FN 18 at 12.5 % util; Nemotron specialization named as the fallback; VRAM/latency feasibility constraint added; wall-time projections replaced by actuals) — all applied; full tests 627 passed + 1 skipped; tree clean at the final commit.

## M7.8 Timing and inference
New inference 516 local cases (TRAIN 180 / DEV 144 / TEST 192), 0 frontier; model time 20.5 h (Qwen3.8 arms 14.3 h); wall by phase: R6.0 ~1.1 h (before `/goal`), R6.1 0.6 h, R6.2 8.2 h, R6.3 0.3 h, R6.4 5.5 h, R6.5 9.3 h, R6.6–7 0.5 h — ≈ 24.1 h from `/goal` (20:59 UTC 08-18) to the final commit (~21:05 UTC 08-19).

## M7.9 Completion checklist
| goal criterion | status |
|---|---|
| Suite v3 frozen, asserted start + end | ✔ |
| Qwen3-8B official provenance backfilled | ✔ `Qwen/Qwen3-8B-GGUF@6a569868`, SHA `d98cdcbd…` |
| both Qwen3.8 artifacts registered as Unsloth Qwen3.8 (not Bonsai) | ✔ |
| Nemotron artifact/runtime reproducible | ✔ bartowski `be042bfc`, runtime record, server args |
| Bonsai provenance/runtime requirement recorded | ✔ Prism `b1-9fcaed7` |
| Qwen3.5-9B acquired from pinned source, digest-verified | ✔ |
| every new trajectory carries artifact + runtime/config identity | ✔ 516/516 |
| both Qwen3.8 quants compared on TRAIN only, one advanced | ✔ Q3_K_M |
| generation/runtime calibration TRAIN-only, frozen before DEV | ✔ |
| contract + numeric gates committed before new DEV | ✔ `b2f85d5` / `b4e9095` |
| independent Fable pre-DEV review passes | ✔ A + B |
| one DEV per eligible candidate; gates applied as registered | ✔ |
| TEST once, only DEV-qualified; no post-TEST changes | ✔ |
| no new frontier calls | ✔ 0 |
| R4 + post-answer oracle for new candidates | ✔ |
| overlap / unique rescue / dominance | ✔ |
| report answers the plan's questions | ✔ report § 0, § 5–11 |
| calls by split/artifact, wall by phase | ✔ report § 10 |
| full tests pass; tree clean | ✔ 627 + 1 skipped |
| exactly one next milestone, not started | ✔ R7 reasoning-budget calibration |
