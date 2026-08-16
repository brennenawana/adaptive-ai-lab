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
