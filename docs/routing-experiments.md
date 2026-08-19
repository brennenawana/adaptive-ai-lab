# Routing experiments — the R-series

Protocol and results for the routing track defined in
`FIS_MSI_Pivot_Guide_Switchyard_Nemotron.html`. A separate series so routing
experiments cannot be confused with the prompt/context E-series. Same rules:
**selection on dev, one test confirmation, one factor per arm, gold labels may
score a route but never choose it.**

| Track | Question | Status |
|---|---|---|
| R0 | What is the causally selected local configuration before routing? | **done** — `weak-baseline-v1` below |
| R1 | Can Switchyard sit in the model path without changing outcomes? | **measured** — no for the grammar-constrained local arm as shipped (14/48 dev outcomes change; +4 ms overhead; tokens reconcile exactly); root cause identified; see below |
| **R0.1** | Can the hop be made transparent without touching the suite or the model's reasoning? | **yes — fixed and proven**: key-order-invariant schema rewrite in the adapter; same-session dev re-run **48/48 identical output digests**, 48/48 identical outcomes, tokens identical, +10 ms p50 |
| R2 | How much routing opportunity exists between weak and strong on dev? | **done** — see below |
| R3 | Nemotron 3.5 Lightning as candidate weak arm | **done — negative under the pre-registered rule; test untouched.** Compatible (IQ4_XS, same llama.cpp, hybrid GPU/RAM, ~91 tok/s with `--no-mmap`); dev all-pass 25.0% vs Qwen 29.2% because 29/48 cases hit the 4 096-token cap while reasoning; silent failures 23 → 4; Nemotron+R4 89.6% at 66.7% strong calls; see below |
| **R3b** | Was the 4 096-token budget the reason Nemotron failed R3? | **done — negative under the pre-registered rule; test untouched.** One factor (`max_tokens` 8 192, both weak arms, dev, same paired design): Nemotron completes 39/48 (was 19), all-pass 18/48 vs Qwen 15/48, rc 31 vs 30, evidence 0.649 vs 0.648 — but silent failures 4 → 16 (Qwen 21), 9 cases still capped at 8 192, cell B = 6; Nemotron+R4 64.6% at 29.2% strong calls, $0.0534/success vs Qwen+R4 52.1% at 25.0%, $0.0553; fails A/C/D of the pre-registered rule; see below |
| R4 | Deterministic weak→strong cascade | **done** — policy `verifier` (dev replay, pre-registered rule); dev live 50.0% all-pass at 22.9% strong calls, **test 49.0% at 21.9%**, 0 unnecessary escalations, rescue 90%; see below |
| R5 | Predictive / stage routing (learned silent-failure routing over production-observable features) | **done — see § R5 below and `R5_LEARNED_ROUTING_REPORT.md`**: primary (leave-one-class-out) protocol null for both models; secondary protocol selected `r5-qwen-tree-stratified-v1` (TEST 78.1 % vs R4 50.0 % at 57 % util; reading met, non-informative) and `r5-nemotron-lr_core-stratified-v1` (TEST 77.1 % vs 71.9 % at 33 %; not confirmed); the signal is template difficulty |

Runs live in `learning.case_scores` / `learning.trajectories`; `make report` lists
them all. Reports under `evals/reports/` are gitignored, so the numbers that matter
are copied here.

---

## R0 — frozen local baseline: `weak-baseline-v1`

| Field | Value |
|---|---|
| Producing code | commit `f48039a` (verified byte-identical scorer, orchestrator, gateway, schemas and variant-C prompt text through `8599326`) |
| Run | `E6-cause_action_directed-96`, test split, n=96, `config_digest=local-specialist\|fixed_evidence\|cause_action_directed` |
| Suite | `fis-eval` v2 (event-sourced corpus, uuid5 envelopes, `get_verifications` v2) |
| Model | Qwen3-8B Q4_K_M, llama.cpp CUDA build `b1-9b05354` (upstream `9b05354`, 2026-08-14), `--parallel 1`, `--jinja`, ctx 16 384, greedy (`temperature 0`, `seed 42`), `max_tokens 4096`, `response_format json_schema` → GBNF |
| Prompt | `cause_action_directed` (E6 variant C, sha256 `40111d53f60e0a37…`), `PROMPT_VERSION 1` |
| Evidence | `FIXED_EVIDENCE`, two-phase plan; reachability 12/12 classes at 1.000 on test and dev |
| Scorer | `evals/scorers/score.py` — polarity-aware forbidden claims, evidence threshold 0.8 |
| Root cause | **65.6%** (63/96) |
| act \| rc | **100%** (63/63) — aggregate action 80.2% |
| Evidence recall | **61.1%** mean; 34/96 ≥ 0.8 |
| Verifier pass | **78.1%** (75/96) |
| Strict all-pass | **29.2%** (28/96) |
| Unsupported / forbidden | 9 cases / 0 |
| No scoreable output | **12/96**: 4 raw-unparseable (all S07, `finish_reason` length — thinking exhausted the cap) + 8 schema-invalid (5×S01, 2×S04, 1×S08: single-service corroboration) |
| Latency | wall p50 13 782 / p95 50 355 / mean 17 795 ms per case |
| Tokens | in 2 443 / out 1 194 per case (234 548 / 114 578 total) |
| Reference cost | $0.00 |

Same configuration on **dev** (`E6-C-directed-dev`, n=48, the weak arm for R1/R2):
rc 62.5%, act|rc 100%, evidence 70.8%, verifier 83.3%, all-pass 35.4%, no-output 4/48,
in 2 446 / out 1 255 tokens per case, p50 15 385 / p95 35 824 ms.

Confirmations at cutover (2026-08-16): `make test` **160 passed** at `8599326`;
`make reachability` test 96/96 and dev 48/48 with 0 capped classes.

E6b closure: four citation-recovery variants (E, F, G, H) run on dev against C; none
beat it under the pre-registered rule; C stands and its one test confirmation is the
run above. No further test run was made.

---

## R1 — Switchyard passthrough equivalence

**Design.** Same prompt, evidence, model, decoding, grammar and scorer; only the
path differs. Three dev runs, n=48 each, `--prompt cause_action_directed`:

| Run | Path | Purpose |
|---|---|---|
| `E6-C-directed-dev` | direct, pre-refactor adapter (2026-08-16 00:25 UTC) | recorded control |
| `R1-direct-dev` | direct, current adapter | control re-run: nondeterminism floor **and** proof the adapter refactor changed nothing |
| `R1-switchyard-dev` | orchestrator → Switchyard :4000 → llama.cpp :8082 | the routed arm |

Judged per scenario with `scripts/compare_routes.py` (output digest, scored outcome,
tokens, stop reason, latency, routing-metadata coverage), not by aggregate rates.

**Set-up.** `nemo-switchyard==0.2.0`, `infra/switchyard/routes.yaml` (one `type:
model` route `fis-local-specialist` → 8082, `api_key ""`, `format openai`), registry
entry `local-specialist-switchyard` whose model fields equal `local-specialist`;
`SwitchyardAdapter` inherits `build_body`, so the request is byte-identical on both
paths (`tests/test_switchyard_passthrough.py`).

### Finding: the hop is verbatim except for JSON key order — and key order is semantic here

Smoke on one fixed request, three repeats per path: each path deterministic, the two
paths disagree (direct `ec965b29…` 1031 tok; via Switchyard `b536f509…` 1049 tok).

1. A byte tap between Switchyard and llama.cpp showed the forwarded body is the same
   length and semantically equal, but **every object's keys are sorted** (serde_json
   without `preserve_order`). The response schema's `properties` therefore arrive
   alphabetical instead of `case_id, classification, root_cause, facts, hypotheses,
   recommended_next_action, escalation_required, uncertainties, summary`.
2. llama.cpp compiles the JSON schema to a GBNF grammar that enforces property order.
   Re-sending the direct request with only the schema keys sorted reproduces
   Switchyard's output byte-for-byte. The model is forced to write `facts` before
   `root_cause`; under greedy decoding the text diverges.
3. Thin-adapter attempt: a client-side GBNF string (llama.cpp's own
   `json_schema_to_grammar.py`, sent as `grammar`) makes direct and Switchyard agree
   exactly (`473c9ebe…`) — but at 287 tokens with **no reasoning**: llama.cpp applies
   a `response_format` grammar lazily after the `<think>` block and a raw `grammar`
   from token one. That changes the frozen baseline's behaviour, so it was not
   adopted.

Everything else checked out: no retries/fallback/timeout/condensing on a `type:
model` route; response body verbatim (`usage`, `timings`, `finish_reason`); no
`x-switchyard-*` headers on a passthrough success (recorded as `selected_backend
None`); routing log JSONL and `/v1/stats` per model.

**Consequence.** Exact equivalence through Switchyard 0.2.0 is not achievable for a
grammar-constrained llama.cpp arm whose schema order is not alphabetical, without
either an upstream fix (preserve key order) or a FIS suite bump that canonicalises
schema property order for *every* arm and re-baselines. R1 therefore measures the
delta rather than assuming zero.

### Results (2026-08-16, all three runs in one llama.cpp server session, back-to-back, same case order)

Runs: `R1-direct-dev` 09:26–09:47 UTC (overlapped with the E4 dev run on CPU),
`R1-direct2-dev` 09:47–10:01, `R1-switchyard-dev` 10:01–10:15 (both alone).

**Reproducibility floor first (direct vs direct, same session):**

| `R1-direct-dev` vs `R1-direct2-dev` | |
|---|---|
| exact output digest equal | **47/48** — the one difference is the first case in run order (S01-2000000, 657 vs 662 tokens), whose prompt-cache predecessor differed |
| identical scored outcome | **48/48** |
| identical token counts | 47/48 |
| aggregates | identical: all-pass 14, rc 31, verifier 37, evidence 0.606, no-output 5 |

So within one server session, with the same request order, the local arm is
reproducible; the only nondeterminism is the KV prompt-cache state left by the
previous request. **Across a server restart it is not**: the recorded control
`E6-C-directed-dev` (00:25 UTC, earlier server process) vs `R1-direct-dev` — same
prompt bytes (input tokens identical 48/48), output tokens different 48/48, scored
outcome different **23/48**, all-pass 17 vs 14, evidence recall 70.8% vs 60.6%,
verifier 40 vs 37. Nothing above the model changed (`test_request_body_is_byte…`,
identical prompt tokens). Consequence, recorded as an R0 caveat: two local runs are
comparable case-by-case only if produced in one server session in the same order.

**Switchyard vs same-session direct (`R1-direct2-dev` → `R1-switchyard-dev`):**

| quantity | direct2 (control) | via Switchyard | Δ |
|---|---|---|---|
| exact output digest equal | — | **0/48** | as predicted by the key-order finding |
| identical scored outcome | — | **34/48 (70.8%)** | 14 cases differ |
| identical token counts | — | 1/48 | |
| strict all-pass | 14 (29.2%) | 11 (22.9%) | −3 |
| root cause correct | 31 (64.6%) | 28 (58.3%) | −3 |
| act \| rc | 100% | 100% | 0 |
| verifier pass | 37 (77.1%) | 39 (81.2%) | +2 |
| evidence recall mean | 0.606 | 0.655 | +0.049 |
| no scoreable output (parse/schema) | 5 | 4 | −1 |
| unsupported claims (cases) | 6 | 5 | −1 |
| forbidden claims | 0 | 0 | 0 |
| input tokens / case | 2 446.4 | 2 446.4 | 0 (same prompt) |
| output tokens / case | 1 311.3 | 1 304.7 | −6.6 |
| model latency p50 / p95 | 12 619 / 39 558 ms | 12 691 / 39 818 ms | +72 / +260 |
| transport overhead = wall − llama.cpp compute (p50 / mean / max) | 132 / 138.9 / 244 ms | 132 / 142.7 / 248 ms | **+0 / +3.8 / +4 ms** |
| gateway-reported routing overhead (`/v1/stats`) | — | p50 0.89 ms, max 1.34 ms | |
| RoutingRecord present | 0/48 | **48/48** (`switchyard 0.2.0`, `passthrough`, `upstream_model=fis-local-specialist`, `selected_backend=None`) | |
| stop reasons | stop ×48 | stop ×48 | |

**Token accounting reconciles exactly**: Switchyard's routing log for the run's 48
requests sums to prompt 117 426 / completion 62 627 — identical to the FIS
trajectories for `R1-switchyard-dev` (and prompt 117 426 for the direct runs).
`/v1/stats` per-model counters agree once the smoke requests are subtracted.

**Reading.** Behaviour: *not equivalent* — every output differs and 14/48 scored
outcomes change, in both directions (rc −3, evidence +5 pts, verifier +2). This is
the alphabetical-grammar effect measured on dev; note it is a *prompt-format*
factor and must not be adopted or rejected on these numbers (n=48, unpre-registered,
and it would be a change to the frozen baseline). Parse rate: 4 vs 5 no-output —
equivalent within noise. Latency: +4 ms mean transport overhead, ~0.03% of a
12.7 s call — negligible; gateway's own routing overhead < 1.5 ms. Token accounting:
identical to the token. Metadata: every routed invocation carries a RoutingRecord
that names the gateway, version, route, mode and the upstream model llama.cpp
served, and honestly leaves `selected_backend` empty because a passthrough chain
reports none.

**Decision-gate outcome (guide: "Keep Switchyard if R1 equivalence holds").**
Equivalence does **not** hold as shipped for the grammar-constrained local arm; the
model-client boundary, RoutingRecord and route bundle are kept (they are the
replaceable interface the guide asks for), and the routing implementation is
retained *for the strong hop and telemetry only* until one of: (a) upstream
Switchyard preserves JSON key order; (b) FIS suite v3 canonicalises the schema
property order for every arm and re-baselines. The weak stage of R4 should run on
the direct path in the meantime — that is what the current registry supports.

---

## R0.1 — Switchyard transparency restored at the adapter boundary

**Fix (commit `11ff23f`).** `SwitchyardAdapter.build_body` rewrites every object
schema in the request (`response_format.json_schema.schema`, and tool parameter
schemas) into an `allOf` list — one property per component, optional properties
wrapped in `anyOf`, `additionalProperties` dropped. llama.cpp's converter builds an
object rule from `allOf` by appending each component's properties in array order and
treats "no additionalProperties" exactly like `false`, so this compiles to the
**byte-identical grammar text** as the plain schema — and arrays survive Switchyard's
key sorting. Not a suite change, not a contract change: the direct path still sends
the plain schema it was baselined with, and the model's `<think>` phase is untouched
(unlike the rejected client-side `grammar` string).

**Static evidence.** With llama.cpp's own `examples/json_schema_to_grammar.py`:
`grammar(sorted(rewritten)) == grammar(plain)`; `grammar(sorted(plain)) != grammar(plain)`
(`test_grammar_through_switchyard_equals_grammar_on_the_direct_path`). Property order
and required-ness preserved for root/Fact/RootCause; idempotent.

**Paired verification (2026-08-16, one llama.cpp session pid 4848 / `b1-9b05354`, same
case order, `prime-local` before each arm, nothing else on 8082):**

| pair | digest equal | outcome equal | tokens equal | all-pass | rc | verifier | evidence | no-output | model p50 |
|---|---|---|---|---|---|---|---|---|---|
| `R01-direct2-dev` → `R01-switchyard-dev` (unperturbed) | **48/48** | **48/48** | **48/48** | 14 = 14 | 31 = 31 | 37 = 37 | 0.606 = 0.606 | 5 = 5 | 12 734 → 12 745 ms (**+11**) |
| `R01-direct-dev` → `R01-switchyard-dev` | 47/48 | 47/48 | 47/48 | 14 = 14 | 31 = 31 | 36 → 37 | 0.599 → 0.606 | 6 → 5 | +421 |
| `R1-direct2-dev` (10:01 UTC) → `R01-direct-dev` (13:00 UTC), same session | 46/48 | 47/48 | 46/48 | | | | | | |

The single R01-direct-dev difference (S04-2003003, dev case 16) is attributable: a
`pytest` run at 13:12 UTC sent one 1-token request to 8082 during that arm (the
live tests were opt-in from `021890a` onward), changing that case's prompt-cache
predecessor; the primed re-run `R01-direct2-dev` removed it. Transport overhead
(wall − llama.cpp compute) p50: direct 120–139 ms across the two direct runs,
Switchyard 136 ms — inside direct-vs-direct variation. Token accounting: FIS
trajectories 117 426 in / 62 938 out on both arms; Switchyard's routing log for the
48 requests 117 426 / 62 938 — exact. `runtime_context` on every trajectory records
`pid=4848 start_ticks=37314 boot=b6ea9365`, build `b1-9b05354`, model path;
`runtime_fingerprint=b1-9b05354` on every invocation.

**Verdict.** Behaviour, parse rate, FIS metrics, tokens and latency are equivalent
through the gateway; the routed local arm is now usable interchangeably with the
direct one for routing experiments. Decision-gate: keep Switchyard. Residual caveats
are the general ones — same server session and same request order for case-level
comparisons; and the rewrite is only needed while the schema is non-alphabetical
(pinned by `test_schema_property_order_is_not_alphabetical__why_r0_1_exists`).

---

## R2 — paired weak/strong opportunity map (dev)

Weak = `E6-C-directed-dev` (the frozen configuration on dev). Strong = `E4-v2-dev`
(claude-frontier, `baseline` prompt as in `E4-v2-96`, run once on dev for this
pairing — 48 frontier calls). Script: `scripts/routing_oracle.py` (`make
routing-oracle`), which refuses the test split without `--allow-test`.

`E4-v2-dev` (n=48, run 2026-08-16 09:07–09:41 UTC): all-pass **91.7%** (44/48), rc
97.9%, evidence 100%, verifier 47/48, forbidden 2 (see review), P95 57 s, $5.16
reference cost ($0.1172 per strict pass).

### Paired outcome matrix (as measured)

| cell | n | rate | meaning |
|---|---|---|---|
| weak-pass / strong-pass | 16 | 33.3% | weak sufficient — ideal cheap coverage |
| weak-fail / strong-pass | 28 | 58.3% | strong can rescue — a router must escalate these |
| weak-pass / strong-fail | 1 | 2.1% | inversion — harness review below |
| both-fail | 3 | 6.2% | neither — harness review below |

| quantity | value |
|---|---|
| weak-only all-pass | 35.4% (17/48) |
| strong-only all-pass | 91.7% (44/48) |
| **oracle hybrid all-pass** (quality ceiling for any router over these two arms) | **93.8%** (45/48) = 1 − both-fail |
| **theoretical safe-local rate** (a perfect router keeps these local) | **35.4%** |
| **rescueable escalation rate** (weak fails strong fixes) | **58.3%** |
| oracle strong-call minimum | 64.6% (of which 9.7% would still fail) |
| hard-case rate | 6.2% |
| reference cost, whole split | weak-only $0.00 · strong-only $5.16 · oracle cascade $3.36 (−35%) |
| cost per strict pass | strong-only $0.1172 · oracle $0.0747 |
| latency p50 per case | weak 15.5 s · strong 33.2 s · oracle cascade 43.5 s (weak always runs first) |

Per class (w+s+ / w−s+ / w+s− / both-fail): S01 0/3/0/1 · S02 0/4/0/0 · S03 0/4/0/0 ·
S04 2/2/0/0 · S05 4/0/0/0 · S06 2/1/**1**/0 · S07 3/1/0/0 · S08 1/1/0/**2** · S09 4/0/0/0 ·
S10 0/4/0/0 · S11 0/4/0/0 · S12 0/4/0/0. Weak-fail/strong-pass failure reasons on
the weak arm (what a router has to detect): evidence 23, root cause 15, action 10,
verifier 7, unsupported 4 — evidence recall is the dominant escalation signal, but it
is an eval-only quantity; the production-available proxies are verifier failure,
no-output and unsupported claims (R4).

**Decision-gate reading:** weak-pass/strong-pass overlap (33%) and rescueable cases
(58%) are both large; routing is economically meaningful (oracle saves 35% of strong
cost at +2 pp quality over strong-only). Proceed to R4 in the next milestone.

### Harness review of the disagreements (required before any of it counts as model behaviour)

| case | cell | what the arm did | review outcome |
|---|---|---|---|
| **S06-2003005** | weak-pass / strong-fail | strong said `compound_failure` / `escalate_to_engineering`; weak correct | **scenario ambiguity, not model superiority.** Every S06 world (dev and test, incl. the one S06 miss in `E4-v2-96`, S06-3007005) has 4 settlements and **1** ledger entry: the three background settlements are never posted, which is exactly S10's fault signature layered on top of S06's transposition. Background settlements are unposted in S01, S02, S05, S06, S07, S08 and S10 (posted only in S11) — the reconciliation-gap signal is present as background noise across the corpus. A careful investigator calling this "compound" is defensible. Generator fix (post background settlements) = corpus regeneration = suite v3; **deferred, recorded** |
| **S08-2001007** | both-fail | strong `forbidden_claims: insufficient_funds`; scorer excerpt: "…insufficient funds, kyc/onboarding state and processor outage **are all ruled out** as causes…" | **scorer false positive** — refutation whose cue follows the phrase; the polarity window looks back only. Same family as harness bug #9's residual. Corrected: strong pass → weak-fail/strong-pass. Scorer left as is (do not change scoring mid-baseline; version it) |
| **S08-2003007** | both-fail | strong `forbidden_claims: insufficient_funds`; excerpt: "…70530 gbp also exceeded the available balance of 17530 gbp, so insufficient funds **could be a contributing factor**, but the decline code points to card state…" | **scenario-realism defect + hedged assertion.** The world's declined amount (70 530) exceeds the account's available balance (17 530), so the forbidden hypothesis is data-consistent; the model hedged it and still concluded risk hold. Generator should keep S08's declined amount below available balance. Deferred |
| **S01-2001000** | both-fail | strong: 1 unsupported claim — "cites an id no tool returned: `idem-st-2001000-03`"; weak: schema-invalid | **verifier gap.** The id is in the bundle (`get_webhook_history … idempotency_key: idem-st-2001000-03`) but `collect_observed_ids` harvests only `*_id` and `provider_ref` keys, so citing an idempotency key — the very thing S01 is about — reads as fabrication. Corrected: strong pass. Verifier fix affects unsupported-claim scoring for every arm → versioned change, deferred |

Annotated (review-corrected) matrix: weak-pass/strong-pass 16, weak-fail/strong-pass
30, harness-ambiguous 2 (S06-2003005, S08-2003007), both-fail 0 → oracle ceiling
≥ 95.8%; strong-only corrected 95.8% (46/48). Reported alongside, not instead of,
the as-measured figures. Nothing in the scorer, verifier or generator was changed.

Three harness candidates recorded for the next suite version (all found by arm
disagreement, none by aggregate rates): unposted background settlements; S08 declined
amount vs balance; observed-id collection missing `idempotency_key`.

---

## R4 — deterministic weak→strong cascade

**Implementation (commit `021890a`).** `services/ai_orchestrator/cascade.py`: weak
model first (`local-specialist`, direct path, prompt `cause_action_directed`);
escalate to `claude-frontier` (prompt `baseline`, as `E4-v2-*` was baselined) on
production-available signals only — no schema-valid output, an unsupported claim
(the scorer's own verifier-violation markers, reused), any other deterministic
verifier failure. Policies are nested prefixes: `none` ⊂ `parse` ⊂ `verifier`. The
gate reads nothing the scorer knows (`RouterDecision.features` = produced_output,
verifier_passed, unsupported_claims; `test_routing_no_gold_leak.py` covers the
module). Escalated cases re-run the deterministic FIXED_EVIDENCE plan for the strong
model; the merged trajectory carries both stages' invocations (cost, tokens, wall) and
the decision on `Trajectory.router`; the weak stage is scored under `<run>.weak`.

**Selection on dev (replay, pre-registered rule).** Weak = `R01-direct2-dev`
(same-session weak-only run), strong reference = `E4-v2-dev`. Rule, registered before
any live run: adopt `verifier` unless it costs > 2 unnecessary escalations beyond
`parse`.

| policy | escalated | rescued | unnecessary | all-pass | rescueable caught (of 30) |
|---|---|---|---|---|---|
| parse | 5 (10.4%) | 3 | 0 | 35.4% | 3 |
| **verifier** | **11 (22.9%)** | 8 | **0** | **45.8%** | 8 |

`verifier` adopted and frozen. Note the pairing cells against this same-session weak
run are 14 / 30 / 0 / 4 (M1's 16 / 28 / 1 / 3 used the earlier-session
`E6-C-directed-dev`; the S06 inversion is not present in this session's weak run).

**Live dev run `R4-cascade-verifier-dev`** (2026-08-16 13:57–14:16 UTC, primed, same
session; the weak stage reproduced `R01-direct2-dev` **48/48** digests):

| metric | weak-only | **cascade** | strong-only | oracle |
|---|---|---|---|---|
| strict all-pass | 29.2% (14) | **50.0% (24)** | 91.7% (44) | 91.7% (44) |
| root cause | 64.6% | **79.2%** | 97.9% | 97.9% |
| act \| rc | 100% | 100% | 100% | 100% |
| evidence recall (mean) | 0.606 | **0.783** | 1.000 | 1.000 |
| verifier pass | 77.1% | **100%** | 97.9% | 97.9% |
| no-output | 10.4% | **0%** | 0% | 0% |
| wall p50 | 12.6 s | 16.9 s | 33.2 s | 42.9 s (cascade reading) |
| tokens in / out (total) | 117 426 / 62 938 | 117 452 / 99 101 | 130† / 164 038 | 117 520 / 179 511 |
| reference cost (total) | $0.00 | **$1.13** | $5.16† | $3.67 |
| cost / attempted case | $0 | **$0.0235** | $0.1074 | $0.0764 |
| cost / successful case | $0 | **$0.0471** | $0.1172 | $0.0833 |

† frontier input tokens under-reported by the CLI (~2/case) — strong cost is a floor.

Routing metrics: weak-local acceptance **77.1%** (37/48); escalation **22.9%** (11/48:
6 unsupported claims, 5 no-output); rescue rate **90.9%** (10/11 escalations turned a
weak fail into a pass); unnecessary escalation **0/48**; false negatives **22/48**
(weak accepted, weak failed, strong-ref would pass); strong-call reduction vs
strong-only **77.1%**; quality delta vs strong-only −20 cases, vs oracle −20.
Against the oracle: rescueable caught 8/30 (the two extra live rescues, S01-2001000
and S06-2003005, are cases the recorded strong arm had failed); safe-local escalated
0/14; the one escalated case that still fails is S08-2003007 — the strong output
mentions `insufficient_funds` hedged ("would also have failed for insufficient funds
… is unknown"), the recorded suite-v3 candidate (declined amount 70 530 > available
balance 17 530).

**What the 22 false negatives are.** All are weak results the verifier accepts:
schema-valid, well-cited, calibrated — and wrong on the eval-only dimensions:
evidence recall alone (13: S03 ×4, S06 ×3, S09, S10 ×4, S11), or root cause and/or
action with a clean citation record (9: S02, S04, S08 ×2, S11, S12 ×4). Deterministic
gates see *broken* outputs, not *confidently terse or wrong* ones. That is the residual
a learned or content-aware router (R5) would have to detect — and it is exactly the
evidence-discipline gap E6b already found prompting cannot close.

### Test confirmation — `R4-cascade-verifier-96` (one run, policy frozen on dev)

2026-08-16 14:16–14:57 UTC, session pid 4848, primed. Weak-only column = the run's own
weak stage (`R4-cascade-verifier-96.weak`, same session); strong-only = `E4-v2-96`.

| metric | weak-only (this session) | **cascade** | strong-only | oracle |
|---|---|---|---|---|
| strict all-pass | 29.2% (28) | **49.0% (47)** | 99.0% (95) | 100% (96) |
| root cause | 60.4% | **75.0%** | 100% | 100% |
| act \| rc | 100% | 100% | 100% | 100% |
| evidence recall (mean) | 0.661 | **0.811** | 1.000 | 1.000 |
| verifier pass | 78.1% | **97.9%** | 100% | 100% |
| no-output | 9.4% | **0%** | 0% | 0% |
| wall p50 | 12.4 s | 14.5 s | 38.2 s | 48.2 s |
| tokens in / out (total) | 234 548 / 117 167 | 234 602 / 186 130 | 226† / 298 456 | 234 710 / 329 719 |
| reference cost (total) | $0.00 | **$2.18** | $9.24† | $6.59 |
| cost / attempted case | $0 | **$0.0227** | $0.0963 | $0.0687 |
| cost / successful case | $0 | **$0.0464** | $0.0973 | $0.0687 |

Routing metrics: weak-local acceptance **78.1%** (75/96); escalation **21.9%** (21/96:
12 unsupported claims, 9 no-output); rescue rate **90.5%** (19/21); unnecessary
escalation **0/96**; false negatives **47/96**; strong-call reduction **78.1%**;
quality delta vs strong-only −48 cases, vs oracle −49. Cells vs `E4-v2-96`: w+s+ 27,
w−s+ 68, w+s− 1 (S08-3005007, the known scorer false positive on the strong arm —
kept local, correctly), w−s− 0. Rescueable caught 21/68; safe-local escalated 0/28.
Dev estimate 50.0% → test 49.0%: the policy did not overfit dev (there was nothing to
overfit — one nested gate, one pre-registered rule).

The weak stage on test scored all-pass 28/96 = the frozen baseline's 29.2% exactly,
while differing from it on 42/96 individual outcomes (rc 58 vs 63, evidence 0.662 vs
0.611): the cross-session effect once more, and a reminder that `weak-baseline-v1` is
a historical aggregate, not a per-case answer key.

### Interpretation

Simple deterministic escalation recovers **about a quarter of the gap** between the
weak and strong arms (test: 29.2% → 49.0% of a possible 99.0%; dev: 29.2% → 50.0% of
91.7%) at **~22% strong-model calls** — 78% fewer than strong-only — with **zero
unnecessary escalations** and a **90% rescue rate** on what it does escalate. Cost per
successful investigation halves versus strong-only ($0.046 vs $0.097 on test, strong
cost being a floor) and median latency is 2.6× lower (14.5 s vs 38.2 s). What it
cannot recover is the other three quarters: 47/96 test cases (22/48 dev) where the
weak model returns a schema-valid, well-cited, calibrated answer that is wrong on
root cause or too terse on evidence — the failure family E6b already showed prompting
does not move, and one that no production-available deterministic signal exposes.
Closing that gap needs either a better weak model (R3) or a router that reads
content, not just structure (R5); the oracle says the ceiling for either is ~92–100%
at ~65–70% strong calls avoided.

---

## R3 — Nemotron 3.5 Lightning as a candidate weak arm (compatibility spike + dev benchmark)

**Question.** Can a stronger specialist reduce the *silent* failures of the Qwen weak
tier — verifier-clean answers that are wrong — enough to improve the quality and
economics of the weak→strong cascade? Not "is it smarter overall".

### Compatibility (commits `3e02b3e`, `9b211dc`)

| | |
|---|---|
| Checkpoint | `bartowski/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF`, **IQ4_XS** (18.92 GB, imatrix; experts IQ4_NL ≈ 4.25 bpw). Model released 2026-08-11 (OpenMDW-1.1) |
| Architecture | `nemotron_h_moe`: hybrid Mamba-2 + attention + MoE, 52 blocks (+1 MTP head, ignored), 16 MoE blocks × 128 experts (6 used + 1 shared); 30.65 B expert params, 1.56 B dense, 0.70 B embeddings — ~3 B active/token; declared context 1 M |
| Why this quant | every GGUF of this model is ≥ 17.9 GB (dense ≈ 1.7 GB, experts ≥ 16 GB; K-quants fall back to Q5_0/Q8_0 for the 1856-wide expert matrices, so Q4_K_M is 25.5 GB); IQ4_XS is the closest 4-bit class to Qwen's Q4_K_M and the smallest high-quality option |
| Fit on the RTX 5080 (16 GB) | **cannot be held whole at any quantization**; placement is hybrid: dense + KV/SSM + a share of expert layers on the GPU (`--fit on`), the rest in system RAM. Alone: 15.3 GB VRAM used; beside Qwen (fit-target 1024 MiB): ~8.0 GB, total 15.7 GB. RSS 18.9 GB. WSL exposes 47 GB RAM |
| Runtime | the **same** llama.cpp build as Qwen (`b1-9b05354`, `nemotron_h_moe` already compiled in — no rebuild), `infra/serve-nemotron.sh` on 8083, `--jinja --parallel 1`, q8_0 KV, flash-attn, ctx 16 384, `--no-mmap` (see throughput). Loads in 9 s (mmap) / 80 s (no-mmap) |
| Structured output | llama.cpp json_schema→GBNF, model-agnostic — schema-valid `InvestigationResult` on every completed case; reasoning on by default (`enable_thinking`), extracted to `reasoning_content` like Qwen3; grammar applied after `</think>` as for Qwen |
| Throughput (back-to-back probe, real 3 150-token FIS prompt, 256-token gen) | Qwen 97 tok/s gen, prompt 5 000 tok/s (TTFT 0.5 s). Nemotron **91 tok/s beside Qwen / 95 tok/s alone with `--no-mmap`**, prompt ≈ 1 400 tok/s (TTFT 2.2 s); with mmap after the page cache turned over: 20 tok/s (the dev run ran in that state — quality unaffected, digests identical across placements) |
| Stability | 48/48 + 3 smoke cases completed, no crash/OOM/restart; deterministic (3/3 identical smoke repeats, S01-2000000 identical across three server placements) |
| Contract | unchanged: suite v2, prompt `cause_action_directed`, FIXED_EVIDENCE, same schema/grammar path, scorer, verifier, greedy/seed 42/`max_tokens 4096` — arms differ by `model_ref` only |

### Design and reproducibility control

Design **A — simultaneous endpoints**: Qwen (session pid 4848, the same process as
every R0.1/R4 run) on 8082, Nemotron on 8083, same case order, each endpoint primed
before its run. `R3-qwen-dev` (A) → `R3-nemotron-dev` → `R3-qwen2-dev` (B),
2026-08-17 01:58–05:10 UTC. **Qwen A vs B: 48/48 identical output digests, 48/48
identical outcomes** — and identical to `R01-direct2-dev` from the previous milestone.
Within-session drift is zero; every Qwen/Nemotron difference below is model (plus
quantization) difference, not process variance.

### Dev benchmark (n=48)

| metric | Qwen A (= B) | **Nemotron** | Δ |
|---|---|---|---|
| strict all-pass | 14 (29.2%) | **12 (25.0%)** | −2 |
| root cause correct | 31 (64.6%) | 16 (33.3%) | −15 |
| act \| rc | 100% | 100% | — |
| evidence recall (mean) | 0.606 | 0.316 | −0.29 |
| verifier pass | 37 | 16 | −21 |
| **no-output** | 5 (all schema-invalid) | **31** = 29 `length` (4 096-token cap reached inside `<think>`) + 2 schema-invalid | +26 |
| unsupported claims (total) | 6 | 1 | −5 |
| forbidden claims | 0 | 0 | — |
| **silent failures** (verifier-clean, wrong) | **23** | **4** | −19 |
| output tokens (total) | 62 938 | 172 436 | ×2.7 |
| wall p50 / p95 (as run, mmap-slow placement) | 14.0 s / 41.3 s | 206.6 s / 211.0 s | see throughput — projected p50 ≈ 47 s at 90 tok/s, still dominated by the cap |
| **among the 19 cases Nemotron completed** | — | **12 pass (63%), rc 16/19 (84%), evidence 0.798, verifier 16/19** | |

Per class (Nemotron pass / length-capped of 4): S01 0/0 · S02 1/3 · S03 2/1 ·
S04 0/4 · S05 1/3 · S06 1/3 · S07 0/4 · S08 **4**/0 · S09 2/2 · S10 1/3 · S11 0/3 ·
S12 0/3.

### Migration matrix (Qwen A vs Nemotron, strong-ref `E4-v2-dev`)

| cell | n | % | breakdown |
|---|---|---|---|
| **A** both pass | 4 | 8.3% | S02 1, S05 1, S09 2 |
| **B** Qwen pass / Nemotron FAIL | **10** | 20.8% | **all 10 are `length` no-output** (S02 ×2, S05 ×3, S07 ×3, S09, S11); root causes missing_idempotency 2, processor_decline 3, reversal_race 3, stale_integration_mapping 1, false_positive_alert 1 — the strong arm passes all 10 |
| **C** Qwen FAIL / Nemotron pass | **8** | 16.7% | S08 ×4 (risk_hold — Qwen said processor_decline / no-output; Nemotron evidence 1.00), S03 ×2 (kyc_hold — Qwen silent:evidence 0.67 → 1.00), S06-2003005, S10-2001009; 6 of the 8 were Qwen **silent** failures |
| **D** both fail | 26 | 54.2% | Nemotron pattern: no-output 21, silent:evidence 3, verifier-fail 1, silent:rc 1; classes S01 ×4, S04 ×4, S12 ×4, S06 ×3, S10 ×3, S11 ×3, S03 ×2, S02, S07, S09 |

Regressions reviewed: every one of the 10 is the same mechanism — the model was
still reasoning when the 4 096-token cap hit (`finish_reason: length`, empty content),
not a wrong answer. Not a harness issue, not a scenario issue: a **thinking-budget /
contract-fit** issue. Rescues reviewed: S06-2003005 and S08-2001007/S08-2003007 are
the R2 harness-review cases (background settlements; declined amount > balance /
scorer FP) where the *strong* arm was scored as failing — Nemotron's passes there are
genuine answers, and the S08 forbidden-claim FP did **not** recur for Nemotron.

### Silent-failure analysis (the question R3 was asked)

Silent = schema-valid, verifier-clean, and still failing — the family the R4 gate
cannot see. Qwen A: **23/48** (22 of them routing false negatives: the strong-ref
passes). Nemotron: **4/48** (4 routing false negatives). Of Qwen's 23: Nemotron
**passes 6**, fails **15 loudly** (visible to the gate: 14 no-output, 1 verifier),
stays silent on 2; and introduces **2 new** silent failures (S01-2000000 evidence
0.50; S11-2001010 evidence 0.50). Silent patterns: Qwen evidence-only 13, rc+evidence
(+action) 10; Nemotron evidence-only 3, rc 1.

So: **yes — Nemotron reduces the silent valid-but-wrong failures by ~80% (23 → 4,
false negatives 22 → 4)**, but overwhelmingly by converting them into *loud*
failures (unfinished reasoning), and only 6 of them into passes. When it finishes, it
is thorough (evidence 0.80 vs 0.61) and right (rc 84% vs 65%); it finishes 40% of the
time under the frozen 4 096-token budget.

### R4 cascade replay — same `verifier` policy, both weak arms, strong-ref `E4-v2-dev`

| configuration | all-pass | rc | evidence | verifier | weak accepted | strong calls | rescue | unnecessary | false neg | cost / attempt | cost / success | wall p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen only | 29.2% | 64.6% | 0.606 | 77.1% | 100% | 0% | — | — | 22 silent | $0 | $0 | 14.0 s |
| **Qwen + R4** | 45.8% | 77.1% | 0.783 | 97.9% | 77.1% | **22.9%** | 8/11 | 0 | **22** | $0.0250 | **$0.0545** | 17.4 s |
| Nemotron only | 25.0% | 33.3% | 0.316 | 33.3% | 100% | 0% | — | — | 4 silent | $0 | $0 | 206 s (mmap) → ~47 s (no-mmap) |
| **Nemotron + R4** | **89.6%** | 97.9% | 0.972 | 97.9% | 33.3% | **66.7%** | 31/32 | 0 | **4** | $0.0777 | **$0.0868** | 236 s (mmap) → ~70 s |
| Frontier only | 91.7% | 97.9% | 1.000 | 97.9% | 0% | 100% | — | — | — | $0.1074† | $0.1172† | 33.2 s |
| Oracle (Qwen) / (Nemotron) | 91.7% / 97.9% | | | | | 70.8% / 81.3% | | | | | $0.0833 / $0.0887 | |

† frontier input tokens under-reported by the CLI — strong cost is a floor.
Escalation reasons — Qwen: 6 unsupported claims, 5 no-output; Nemotron: 31 no-output,
1 unsupported. Nemotron+R4 keeps the three "w+s−" cases local (S06-2003005,
S08-2001007, S08-2003007 — the harness-flagged ones) and misses only 4 rescueable
cases (its 4 silent failures).

**Intelligence-density reading.** Nemotron + R4 nearly matches the frontier (−1
case) at 33% fewer strong calls, but its cost per success is 1.6× Qwen + R4's
($0.087 vs $0.055) because two thirds of cases still go to the frontier — the local
tier absorbs 33% of the work instead of 77%. Quality per dollar: Qwen+R4 22 passes for
$1.20; Nemotron+R4 43 passes for $3.73; frontier 44 for $5.16.

### Pre-registered selection rule — outcome: **Nemotron does NOT qualify. TEST untouched.**

| # | criterion | result |
|---|---|---|
| 1 | all-pass ≥ Qwen A + max(5, 2×A/B drift) = +5; rc ≥ Qwen | **FAIL** — 12 vs 14 (−2); rc 16 vs 31 |
| 2 | silent false negatives −5 under R4 replay | **PASS** — 22 → 4 (−18) |
| 3 | cell B ≤ 3, reviewed, no forbidden claims | **FAIL** — B = 10 (all length-cap no-output; reviewed); forbidden 0 ✓ |
| 4 | 48/48 no crash/OOM; wall p50 ≤ 30 s | **FAIL** on latency — 206 s as run, ≈ 47 s projected with `--no-mmap` (the length-capped cases alone are ~45 s); stability ✓ |
| 5 | Nemotron+R4 cost/success ≤ Qwen+R4, or +5 all-pass at ≤ 1.5× strong-call rate | **FAIL** — $0.0868 > $0.0545; +21 all-pass but strong calls 66.7% vs 22.9% (2.9×) |
| 6 | above A/B noise | moot (drift = 0) |

Qwen stays the incumbent weak arm. No Nemotron prompt tuning, no trigger change, no
scorer change, no test run.

### Interpretation

Nemotron 3.5 Lightning is compatible with the FIS contract on this hardware and, on
the cases it completes, is a clearly stronger investigator than Qwen3-8B (63% vs 29%
strict pass, evidence 0.80 vs 0.61) — and it does the one thing R3 asked about: it
almost eliminates the silent-wrong family (23 → 4). But under the frozen decoding
budget it fails to finish 60% of the cases (its `<think>` runs past 4 096 tokens), so
as a *weak-only* arm it is worse, and as a *cascade* weak arm it buys near-frontier
quality by sending two thirds of the traffic to the frontier. Under this contract it
does not improve the specialist tier's economics. The result **does** support the
architecture — with Nemotron the deterministic gate captures 31 of 35 rescueable
cases because the model's failures are structural rather than confident — and it
isolates exactly one confound to resolve before the model comparison is meaningful:
the token budget.


---

## R3b — the token-budget factor: `max_tokens` 4 096 → 8 192, both weak arms, dev only

**Question.** R3 left one confound: 29/48 Nemotron dev cases were still inside `<think>`
when the frozen 4 096-token budget ran out. Was that cap the reason Nemotron failed
the R3 rule — and, once given room to finish, does its completed-case profile (63%
strict pass, ~80% fewer silent failures) hold across the split and change the cascade
economics? One factor was varied, for **both** weak arms, and nothing else.

### Contract (frozen before the run; rule pre-registered in `OVERNIGHT_STATUS.md` § M4.2 at `99fe730`)

| | R3 (historical) | R3b |
|---|---|---|
| suite / split / order / prompt / evidence / schema / grammar path / scorer / verifier / decoding | v2 / dev 48 / `ORDER BY scenario_id` / `cause_action_directed` / `FIXED_EVIDENCE` / `InvestigationResult` / llama.cpp json_schema→GBNF, direct path / unchanged / greedy, seed 42, thinking on | **identical** |
| `max_tokens` | 4 096 | **8 192** (the only factor; `run_eval --max-tokens`, recorded on every invocation and in `config_digest` as `\|max_tokens:8192`) |
| models / quants / build / flags | Qwen3-8B Q4_K_M `-ngl 99` (8082); Nemotron 3.5 Lightning 30B-A3B IQ4_XS `--fit on --fit-target 1024 --no-mmap` (8083); llama.cpp `b1-9b05354`, ctx 16 384, `--parallel 1`, q8_0 KV, flash-attn, `--jinja` | **identical** |
| design | A: Qwen A → Nemotron → Qwen B, one session per model, `prime-*` before each arm, nothing else on 8082/8083 | **identical**; runs `R3b-qwen-dev` 08:09–08:21 UTC, `R3b-nemotron-dev` 08:21–09:12, `R3b-qwen2-dev` 09:12–09:24 (2026-08-17); code at `b947972`/`f9e1223` |
| sessions (fingerprints on every trajectory) | — | Qwen `pid=586847 start_ticks=7008514 boot=b6ea9365` for all Qwen arms; Nemotron `pid=670208 start_ticks=8016445 boot=b6ea9365`, started 08:21:5x UTC immediately before its arm (see runtime note); `system_fingerprint b1-9b05354` on 144/144 invocations |
| strong reference / cascade | `E4-v2-dev`, R4 `verifier` policy by replay | **identical, no new trigger** |
| test | untouched | **untouched** (rule failed) |

Runtime note (operator observations from `nvidia-smi`, `/proc` and the throughput probe — not in the JSON artefacts). The Nemotron process left running after R3 (`--no-mmap`, same flags,
idle ~2.5 h) generated at 47–50 tok/s on the fixed probe; the same command line
restarted gave 92.8–93.1 tok/s (R3's recorded state: 91 beside Qwen). Placement and
outputs are unaffected (below: the 19 R3-completed cases reproduce byte-identically);
the latency column is not, so the endpoint is (re)started with unchanged flags right
before its arm and probed with a **train** case (`S05-1000004`: 89.7–90.4 tok/s) — this
is now what `make eval-r3b-dev` does. VmRSS of the fresh process is 4.6 GB (mostly
shmem — the CUDA host buffer under WSL2), rising to 13.65 GB by the end of the arm as
the expert pages are touched; `free` never showed the ~11 GB of off-GPU expert weights
as used guest memory. GPU: 15.67 GB of 16.3 GB peak with both models resident (Qwen
~7.7 GB, Nemotron ~7.9 GB).

### Reproducibility (Qwen A vs Qwen B, plus a same-session budget diagnostic)

| pair | digest equal | outcome equal | all-pass | rc | evidence | verifier | no-output | p50 |
|---|---|---|---|---|---|---|---|---|
| **R3b Qwen A vs B** (8 192, same session, primed) | **47/48** | **48/48** | 15 = 15 | 30 = 30 | 0.648 = 0.648 | 36 = 36 | 6 = 6 | 11.49 → 11.57 s |
| R3b Qwen A (8 192) vs `R3b-qwen4096-dev` (4 096, **same session**, primed, run after B as a diagnostic) | 46/48 | 47/48 | 15 = 15 | 30 = 30 | 0.648 → 0.627 | 36 → 35 | 6 → 7 | 11.49 → 11.54 s |
| R3 Qwen A (4 096, session pid 4848) vs R3b Qwen A (8 192, pid 586847) | 1/48 | 37/48 (all-pass) | 14 → 15 | 31 → 30 | 0.606 → 0.648 | 37 → 36 | 5 → 6 | 13.98 → 11.49 s |
| R3 Qwen A (4 096) vs `R3b-qwen4096-dev` (4 096) — cross-session, same budget | 0/48 | 24/48 (strict outcome) | 14 → 15 | 31 → 30 | | | | |

The one A/B digest difference is the first case in run order (S01-2000000, 656 vs 664
tokens, same outcome): before Qwen A the endpoint had been probed with that case's own
prompt (the throughput check at 08:02, before `prime-local`), and B's predecessor was
case 48 — the same first-case predecessor effect R1 recorded. Gate (≥ 46/48 both) **passes**;
every Qwen-vs-Nemotron difference below is model difference. The same-session
diagnostic settles the Qwen budget question exactly: with `max_tokens` the only
difference, 46/48 outputs are byte-identical, the first case differs by predecessor,
and **one** case differs by budget — S07-2003006, which needs 4 105 tokens (a silent
wrong `reconciliation_gap` at 8 192; a `length` no-output at 4 096). Everything else in
the R3 → R3b Qwen shift (0/48 digests, 24/48 strict outcomes across sessions at the
*same* budget) is the cross-session drift R1 found, not the factor.

### Token-budget effect

| | Qwen 4 096 (R3 A) | Qwen 8 192 (R3b A) | Nemotron 4 096 (R3) | **Nemotron 8 192 (R3b)** |
|---|---|---|---|---|
| complete (`stop`) / scoreable | 48 / 43 | 48 / 42 | 19 / 17 | **39 / 37** |
| cap hits (`length`) | 0 | 0 | 29 | **9** (8 still inside `<think>`, 1 with the JSON started and truncated) |
| strict all-pass | 14 | 15 | 12 | **18** |
| root cause | 31 | 30 | 16 | **31** |
| act \| rc | 100% | 100% | 100% | 100% |
| evidence recall | 0.606 | 0.648 | 0.316 | **0.649** |
| verifier pass | 37 | 36 | 16 | 34 |
| unsupported / forbidden | 6 / 0 | 7 / 0 | 1 / 0 | 5 / 0 |
| silent failures (routing FN) | 23 (22) | 21 (21) | **4 (4)** | **16 (16)** |
| output tokens total / mean / p50 / p95 / max | 62 938 / 1 311 / 999 / 3 111 / 3 508 | 62 673 / 1 306 / 1 057 / 3 193 / 4 105 | 172 436 / 3 592 / 4 096 / 4 096 / 4 096 | **239 961 / 4 999 / 4 507 / 8 192 / 8 192** |
| cases > 4 096 tokens | 0 | 1 | 0 (capped) | **29** (13 in 4 097–6 144, 7 in 6 145–8 191, 9 at 8 192) |
| reasoning / answer chars (mean; new telemetry) | — | 4 342 / 1 053 | — (capped cases: all reasoning) | 17 453 / 1 152; the 39 `stop` cases 14 391 / 1 398, the 37 scoreable 14 912 / 1 423 (≈ 90% of characters are thinking) |
| wall p50 / p95 / max | 14.0 / 41.3 / 45.2 s | 11.5 / 35.1 / 46.7 s | 206.6 / 211.0 / 216.1 s (mmap-slow) | **52.0 / 94.1 / 96.7 s** |
| generation tok/s (median, llama.cpp timings) | 82 | 93 | 20 (mmap-slow) | **87** (80–89) |
| digest equal to the 4 096 run | — | 1/48 (different session) | — | **19/19 of R3's completed cases** — the same tokens, the same sha, across sessions and budgets (the still-empty capped cases have no digest to compare) |

Every one of R3's 29 `length` cases, classified at 8 192:

| class | n | cases |
|---|---|---|
| **RECOVERED_PASS** | **6** (20.7%) | S02-2003001 (6 632 tok), S05-2003004 (4 166), S06-2000005 (4 941), S06-2001005 (5 025), S09-2002008 (5 815), S09-2003008 (4 343) |
| **RECOVERED_FAIL** | **14** (48.3%) | 12 **silent**: S02-2001001 (rc `duplicate_webhook_handled`), S03-2003002 (ev 0.67), S04-2000003 / -2001003 / -2002003 (ev 0.33 / 0.33 / 0.67), S10-2000009 / -2002009 (ev 0.50), S10-2003009 (rc + ev), S11-2000010 (ev 0.50), S12-2000011 / -2001011 / -2002011 (rc `kyc_hold` for `compound_failure`); 2 loud: S05-2000004 / -2001004 (verifier: unsupported citation) |
| **STILL_LENGTH_CAPPED** | **9** (31.0%) | S02-2002001, S04-2003003, S06-2002005, **S07 ×4** (`reversal_race` — never finishes), S11-2002010, S11-2003010; reasoning 23.9–36.3 k chars at the cap |
| OTHER_FAILURE | 0 | — |

By class (RECOVERED_PASS / RECOVERED_FAIL / STILL_CAPPED): S02 1/1/1 · S03 0/1/0 · S04
0/3/1 · S05 1/2/0 · S06 2/0/1 · S07 0/0/4 · S09 2/0/0 · S10 0/3/0 · S11 0/1/2 · S12 0/3/0.

**How much of R3's Nemotron weakness was the cap?** All of its *loudness* and a fifth
of its *failures*: 6 of the 29 capped cases (20.7%) — 6 of R3's 36 failures (16.7%) —
were correct answers waiting to finish; 14 were wrong or evidence-short answers that
the cap had hidden (12 of them now silent), and 9 need more than 8 192 tokens. Doubling
the budget moved strict all-pass 12 → 18 (+6), root cause 16 → 31, evidence 0.32 → 0.65,
verifier 16 → 34, silent 4 → 16, output +39% tokens, wall p50 206 s (mmap) / ~47 s
projected → 52 s measured. Among scoreable cases the profile is 18/37 pass (48.6%; R3's
completed 12/17 = 71% by the same denominator), rc 31/37 (83.8% — held), evidence 0.842
(held): the recovered cases are right about the cause and short on citations.

### Model benchmark at 8 192 (dev, n=48; Qwen A, same-session B identical)

| metric | Qwen A (8 192) | **Nemotron (8 192)** | Δ |
|---|---|---|---|
| strict all-pass | 15 (31.2%) | **18 (37.5%)** | +3 |
| root cause | 30 (62.5%) | **31 (64.6%)** | +1 |
| act \| rc | 100% | 100% | — |
| evidence recall | 0.648 | 0.649 | +0.001 |
| verifier pass | 36 | 34 | −2 |
| no-output | 6 (schema) | 11 (9 `length` + 2 schema) | +5 |
| unsupported / forbidden | 7 / 0 | 5 / 0 | −2 / — |
| silent (routing FN) | 21 (21) | 16 (16) | −5 |
| output tokens | 62 673 | 239 961 | ×3.8 |
| wall p50 / p95 | 11.5 / 35.1 s | 52.0 / 94.1 s | ×4.5 / ×2.7 |
| throughput (gen; prompt) | 93 tok/s; ~4 600 tok/s (0.7 s TTFT) | 87 tok/s; ~1 400 tok/s (2 s TTFT) | |
| VRAM / RAM | Qwen ~7.7 GB VRAM, RSS 9.3 GB (mmap'd weights) | Nemotron ~7.9 GB VRAM beside Qwen (15.67 GB total peak), RSS 4.6 → 13.65 GB over the arm | |
| per class pass (Qwen / Nemotron of 4) | S01 0/0 · S02 2/2 · S03 0/2 · S04 1/0 · S05 4/2 · S06 1/3 · S07 1/0 · S08 2/4 · S09 4/4 · S10 0/1 · S11 0/0 · S12 0/0 | | |

### Migration matrix (Qwen A 8 192 vs Nemotron 8 192, strong-ref `E4-v2-dev`)

| cell | n | % | breakdown |
|---|---|---|---|
| **A** both pass | 9 | 18.8% | S05 ×2, S06, S08 ×2, S09 ×4 |
| **B** Qwen pass / Nemotron FAIL | **6** | 12.5% | **length cap 3** (S02-2002001, S04-2003003, S07-2001006) · **verifier / unsupported citation 2** (S05-2000004, S05-2001004 — rc and evidence right) · **wrong root cause 1** (S02-2001001, `duplicate_webhook_handled` for `missing_idempotency`); classes S02 2, S04 1, S05 2, S07 1; strong-ref passes all 6 |
| **C** Qwen FAIL / Nemotron pass | **9** | 18.8% | **Qwen silent → root-cause improvement 3** (S02-2000001, S02-2003001: `duplicate_webhook_handled` → `missing_idempotency`; S06-2001005) · **Qwen silent → evidence completion 3** (S03-2001002, S03-2002002, S10-2001009: 0.67/0.67/0.50 → 1.00) · **Qwen no-output 2** (S08-2002007, S08-2003007) · **Qwen verifier-fail (unsupported) 1** (S06-2000005); classes S02 2, S03 2, S06 2, S08 2, S10 1; 6 of the 9 were Qwen silent failures. S08-2003007 is the R2 harness-flagged case (declined amount > balance; strong-ref scored FAIL) — Nemotron's `risk_hold` pass there is a genuine answer, as in R3 |
| **D** both fail | 24 | 50.0% | Nemotron pattern: silent:evidence 10, no-output 8, silent:rc 4 (all S12 `kyc_hold` vs `compound_failure`), verifier 1, silent:rc+evidence 1; classes S01 4, S11 4, S12 4, S04 3, S07 3, S10 3, S03 2, S06 1 |

Cells by class (A/B/C/D): S01 0/0/0/4 · S02 0/2/2/0 · S03 0/0/2/2 · S04 0/1/0/3 · S05
2/2/0/0 · S06 1/0/2/1 · S07 0/1/0/3 · S08 2/0/2/0 · S09 4/0/0/0 · S10 0/0/1/3 · S11
0/0/0/4 · S12 0/0/0/4. Against Qwen B the matrix is identical (B: 6). No B regression is
a harness artefact: three are the budget again, two are Nemotron's citation habit
(`tool://` service naming the verifier rejects — the same habit the R3 smoke flagged),
one is a wrong diagnosis the strong arm gets right.

### Silent-failure analysis

| run | silent | routing FN | patterns |
|---|---|---|---|
| Qwen 4 096 (R3) | 23 | 22 | evidence 13, rc+evidence(+action) 10 |
| Nemotron 4 096 (R3) | **4** | 4 | evidence 3, rc 1 |
| Qwen 8 192 (R3b) | 21 | 21 | evidence 11, rc+evidence 5, rc+action 2, rc+evidence+action 2, rc 1 |
| **Nemotron 8 192 (R3b)** | **16** | **16** | evidence 10, rc 4, rc+action 1, rc+evidence 1 |

Of Qwen's 21 silent failures at 8 192, Nemotron passes 6, fails 5 loudly, stays silent
on 10, and adds 6 of its own. **No — the ~80% silent-failure reduction did not survive
the budget.** It was mostly the cap: at 4 096 unfinished reasoning was counted as a loud
failure; at 8 192, 12 of the 14 recovered-but-wrong cases are verifier-clean and wrong
(seven evidence-short, five wrong root cause), so silent failures rise 4 → 16 and the
advantage over Qwen shrinks from −19 to **−5 (−24%)**. R3's loud failures became: 6
passes, 12 silent wrong/short completions, 2 loud (verifier) completions, 9 longer
failures still at the cap.

### R4 cascade replay — unchanged `verifier` policy, strong-ref `E4-v2-dev`

| configuration | all-pass | rc | evidence | verifier | weak accepted | strong calls | rescue | unnec. | FN | cost/attempt | cost/success | wall p50 / p95 | weak output tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen 8 192 only | 31.2% | 62.5% | 0.648 | 75.0% | 100% | 0% | — | — | 21 | $0 | $0 | 11.5 / 35.1 s | 62 673 |
| **Qwen 8 192 + R4** | **52.1%** (25) | 79.2% | 0.825 | 97.9% | 75.0% | **25.0%** (12: 6 unsupported, 6 no-output) | 10/12 | 0 | **21** | $0.0288 | **$0.0553** | 15.1 / 57.5 s | 62 673 (+43 356 strong) |
| Nemotron 8 192 only | 37.5% | 64.6% | 0.649 | 70.8% | 100% | 0% | — | — | 16 | $0 | $0 | 52.0 / 94.1 s | 239 961 |
| **Nemotron 8 192 + R4** | **64.6%** (31) | 87.5% | 0.889 | 97.9% | 70.8% | **29.2%** (14: 11 no-output, 3 unsupported) | 13/14 | 0 | **16** | $0.0345 | **$0.0534** | 55.4 / 146.8 s | 239 961 (+52 621 strong) |
| Frontier only | 91.7% | 97.9% | 1.000 | 97.9% | 0% | 100% | — | — | — | $0.1074† | $0.1172† | 33.2 / 57.0 s | — |
| Oracle (Qwen 8 192 / Nemotron 8 192) | 95.8% / 97.9% | | | | | 68.8% / 62.5% | | | | | $0.0787 / $0.0699 | 41.5 / 77.9 s | |
| *historical R3 4 096:* Qwen + R4 / Nemotron + R4 | 45.8% / **89.6%** | | | | | 22.9% / **66.7%** | 8/11 / 31/32 | 0 / 0 | 22 / 4 | $0.0250 / $0.0777 | $0.0545 / **$0.0868** | 17.4 / ~70 s | 62 938 / 172 436 |

† frontier input tokens under-reported by the CLI — strong cost is a floor.

**The business question.** At 8 192, Nemotron + R4 does *not* reduce strong-model
utilisation — it is 29.2% vs Qwen + R4's 25.0% (14 vs 12 escalations), because the
gate now sees only 9 length no-outputs and 2 schema failures instead of 31. What
changes is quality per escalation: 13 of 14 escalations rescue, and three extra local
passes plus three extra rescues bring the cascade to 31/48 vs 25/48 at essentially the same reference cost per
success ($0.0534 vs $0.0553, −3%) and 20% more cost per attempt ($0.0345 vs $0.0288).
The local burden is 3.8× the generated tokens and 3.7× the p50 wall (55 s vs 15 s;
p95 147 s vs 57 s), with a second model resident on the card. Read against R3's
Nemotron + R4 (89.6% at 66.7% strong calls, $0.0868), the extra budget traded 25
points (12 cases) of cascade quality and 37.5 points (18 cases) of frontier utilisation
for a 38% lower cost per success — but the cheaper configuration is now nowhere near frontier quality (64.6%
vs 91.7%) and its 16 silent false negatives are the same family Qwen's gate cannot see.

### Pre-registered selection rule — outcome: **Nemotron does NOT qualify. TEST untouched.**

| # | criterion (as pre-registered) | value | result |
|---|---|---|---|
| gate | Qwen A vs B ≥ 46/48 digests and outcomes | 47/48, 48/48 | PASS |
| **A** | complete (`stop`) ≥ 43/48 | **39/48** (+20 vs R3; 9 still capped; 37 scoreable) | **FAIL** |
| B1 | all-pass ≥ 14/48 | 18/48 | PASS |
| B2 | rc ≥ rc(Qwen A) − max(2, 2×A/B drift) = 30 − 2 | 31 (exact difference **+1**) | PASS |
| **C** | silent failures ≤ 6/48 | **16** (routing FN 16) | **FAIL** |
| **D** | cell B ≤ 5, vs Qwen A and vs Qwen B | **6** and 6 (3 length cap, 2 verifier, 1 wrong rc — each reviewed above) | **FAIL** |
| E1 | strong calls < 50% under the unchanged R4 replay | 29.2% (14/48) | PASS |
| E2 | Nemotron + R4 cost / success ≤ $0.070 | $0.0534 | PASS |
| F | Nemotron-only wall p50 ≤ 75 s as run | 52.0 s (p95 94.1 s, max 96.7 s) | PASS |

Three of six mandatory criteria fail. Qwen remains the incumbent weak arm; no TEST
run; no tuning, no prompt change, no trigger change, no scorer change.

### Interpretation

Was the 4 096-token limit the reason Nemotron failed R3? **It was the reason R3's
result looked the way it did, not the reason the model does not qualify.** The cap
produced every one of the 29 loud failures and hid the model's real profile; removing
it (i) makes Nemotron the better weak-only arm on this contract by three cases (18 vs
15, rc 31 vs 30, evidence equal), (ii) reproduces R3's completed-case root-cause and
evidence quality on the recovered cases, but (iii) reveals that most of what the cap
was hiding were silent, evidence-short or mis-diagnosed answers of exactly the kind the
deterministic gate cannot see — so the "80% fewer silent failures" headline was an
artefact of counting unfinished reasoning as loud. Nine cases (all four S07
`reversal_race` among them) still do not finish in 8 192 tokens, at ~90% of the
generated characters spent thinking.

At 8 192, is Nemotron a better weak-tier component than Qwen once quality, frontier
usage, latency and cost per success are taken together? **Marginally better on
quality, equal on cost per success, worse on everything operational**: +3 local passes
and +6 cascade passes for 3.8× the tokens, 4.5× the p50 latency, a second model on the
card, *higher* frontier utilisation (29% vs 25%), and 16 silent false negatives against
21. Under the current FIS contract that is not enough to displace the incumbent, and
the pre-registered rule says so on completion (A), silent failures (C) and regressions
(D). What R3b does establish is that the two weak models are now measured on the same
footing: any remaining difference is model, quantisation and thinking-length, not
budget.

### Deliberately NOT changed

Suite v2, scorer, verifier, prompt, R4 policy, `weak-baseline-v1`, `DEFAULT_MAX_TOKENS`
(4 096 — every historical make target reproduces its recorded configuration). No
Nemotron prompt adaptation, no `--reasoning-budget`, no test run, no suite v3, no
learned routing, no QLoRA. Backlog for suite v3 unchanged (background settlements
unposted in 7 classes; S08 declined amount > balance and the scorer FP; `idempotency_key`
not an observed id; post-positioned refutation cue) plus one observation from R3b for
the v3 design: the generation budget is now a recorded, per-invocation factor and the
`reasoning_chars`/`content_chars` split makes thinking length measurable — a v3
re-baseline should fix the budget explicitly and record it for every arm, including
the frontier.

---

## Suite v3 — the R4 cascade replayed on the released suite (2026-08-18)

Suite v3 (`SUITE_V3_RELEASE_CONTRACT.md`, `SUITE_V3_RELEASE_REPORT.md`) re-baselined
the three arms; the R4 policy (`verifier`: escalate on no-output, unsupported claim
or verifier failure) was **not** changed and was applied by replay only
(`routing_cascade_report.py --weak <run> --strong E4-v3-dev|E4-v3-96 --policy verifier`).
Nothing below is comparable to the § R4/R3/R3b tables above (suite v2); the scripts
refuse the pairing.

| split | weak arm | weak-only | cascade all-pass | strong calls | rescue | unnecessary | routing FN | cost/success | wall p50 |
|---|---|---|---|---|---|---|---|---|---|
| dev 48 | Qwen 4096 (`V3-qwen-dev`) | 35.4% | **66.7%** | 15 (31.2%) | 15/15 | 0 | 16 | $0.0608 | 16.7 s |
| dev 48 | Nemotron 8192 (`V3-nemotron-dev`) | 47.9% | **72.9%** | 12 (25.0%) | 12/12 | 0 | 13 | $0.0453 | 54.7 s |
| dev 48 | strong-only (`E4-v3-dev`) | — | 100% | 48 | — | — | — | $0.1160 | 37.2 s |
| test 96 | Qwen 4096 (`V3-qwen-96`) | 28.1% | **50.0%** | 22 (22.9%) | 21/22 | 0 | 47 | $0.0513 | 15.4 s |
| test 96 | Nemotron 8192 (`V3-nemotron-96`) | 50.0% | **71.9%** | 21 (21.9%) | 21/21 | 0 | 26 | $0.0380 | 56.1 s |
| test 96 | strong-only (`E4-v3-96`) | — | 99.0% | 96 | — | — | — | $0.1139 | 37.8 s |

The gate's blind spot is unchanged in kind: every routing false negative is a
verifier-clean answer wrong on evidence recall or root cause. Escalations rescue 100%
in both arms; there are no unnecessary escalations. Descriptive only — no trigger was
added and no policy re-selected.


---

## R5 — learned silent-failure routing (2026-08-18; Suite v3, offline-first)

Contract `R5_EXPERIMENT_CONTRACT.md`; report `R5_LEARNED_ROUTING_REPORT.md`; log
`OVERNIGHT_STATUS.md` § M6. Policy form `escalate = R4 ∨ risk ≥ τ*`, router fitted on the
R4-accepted TRAIN subset over `RoutingFeatureSnapshot` v1 (58 production-observable
features: model/runtime, verifier, tool trajectory, answer echo — never gold, class, seed,
split, scorer, frontier). TRAIN acquired for both local arms (288 local calls); DEV/TEST
by replay only; TEST opened exactly once per model.

| | Qwen | Nemotron |
|---|---|---|
| TRAIN (144) | 41 safe / 105 R4-accepted / 64 silent | 66 / 104 / 38 |
| primary protocol (LOGO) | no candidate passes the TRAIN gate (AUC 0.24/0.25/0.52) | none (0.20/0.24/0.22) |
| secondary (stratified) eligible | `lr_full` 0.901, `lr_core` 0.821, `tree` 0.822 (class ceiling 0.892) | `lr_full` 0.919, `lr_core` 0.656, `tree` 0.849 (class ceiling 0.936) |
| DEV R4 | 32/48 @ 31.2 %, FN 16 | 35/48 @ 25.0 %, FN 13 |
| DEV best survivor | `lr_full` 47/48 @ 70.8 %, FN 1, unnec 4 | `lr_full` 45/48 @ 50.0 %, FN 3, unnec 2, AUC 0.953 |
| DEV frozen (tie-break) | `tree` 39/48 @ 56.2 %, FN 9, unnec 5 | `lr_core` 40/48 @ 39.6 %, FN 8, unnec 2 |
| TEST R4 | 48/96 @ 22.9 %, FN 47 | 69/96 @ 21.9 %, FN 26 |
| TEST frozen policy | **75/96 (78.1 %)** @ 57.3 %, FN 20, unnec 6, $0.0799/success — reading met (random escalator meets it with p ≈ 0.59) | **74/96 (77.1 %)** @ 33.3 %, FN 21, unnec 6, $0.0509/success — not confirmed |
| oracle (min-useful) TEST | 95/96 @ 70.8 % | 95/96 @ 49.0 % |
| three-tier oracle TEST | Qwen 27 / Nemotron 27 / frontier 41 / unresolved 1 (not template-clean) | |

Reading: production-observable features carry template difficulty (four case constants
identify the class for 45/48 DEV cases; routers at/near the class-identity ceiling) plus a
thin said-label layer; within-template silent failure was not detected. Pre-registration
lessons: tie-break by frontier calls picks the least-escalating survivor; U = catches −
unnecessary degenerates at unsafe rate ≥ 0.5; pooled LOGO AUC is null-biased under
class-clustered labels. Next (exactly one): QLoRA specialization of the local tier,
Nemotron first — not started.

## R6 — modern local specialist refresh (2026-08-18/19; Suite v3; no router, no training)

Contract `R6_EXPERIMENT_CONTRACT.md`; report `R6_MODERN_LOCAL_SPECIALIST_REFRESH_REPORT.md`;
record `learning/registry/r6/`. Question: how much residual FIS failure disappears when the
local specialist is refreshed to modern operating points — before changing weights. Candidates
(each a cryptographically registered execution system: artifact SHA-256 + runtime digest +
server-args digest + generation-config digest): Qwen3.5-9B Q4_K_M, Qwen3.8-27B Q3_K_M (TRAIN-
selected over UD-Q3_K_XL, 20 vs 16 on the 36-case pilot), Ternary Bonsai 27B Q2_0 on the
Prism llama.cpp fork. All at cap 8192 (no allowed cap met the truncation tolerance), the
historical Qwen server args, one resident server. Unchanged R4 (`verifier` policy) replayed
against the frozen frontier rows.

| | Qwen3-8B | Nemotron | Qwen3.5-9B | Qwen3.8-27B Q3_K_M | Bonsai |
|---|---|---|---|---|---|
| DEV local | 17/48 | 23/48 | 23/48 (REJECTED: p50 58 s, no-output 10) | 25/48 (QUALIFIED) | 21/48 (QUALIFIED) |
| DEV R4 | 32/48 @ 31.2 %, FN 16 | 35/48 @ 25.0 %, FN 13 | 36/48 @ 27.1 %, FN 12 | **47/48 @ 45.8 %, FN 1** | 27/48 @ 12.5 %, FN 21 |
| TEST local | 27/96 | 48/96 | — | 47/96 | {{B_TEST}}/96 |
| TEST R4 | 48/96 @ 22.9 %, FN 47, $0.0513 | 69/96 @ 21.9 %, FN 26, $0.0380 | — | **93/96 @ 49.0 %, FN 2, $0.0628** | {{B_R4_TEST_LONG}} |
| TEST silent (verifier-clean wrong) | 47 | 27 | — | 2 | {{B_TEST_SILENT}} |
| TEST oracle (min-useful) | 95/96 @ 70.8 % | 95/96 @ 49.0 % | — | 95/96 @ 50.0 % | {{B_ORACLE}} |
| p50 wall (TEST) | 13.2 s | 55.8 s | — | 265 s | {{B_P50_TEST}} s |

Reading: with Qwen3.8-27B the silent-failure burden that motivated R5 almost disappears — its
failures are visible cap truncations (47 of 49 on TEST), so the deterministic verifier gate
is already the oracle (93 vs 95). The price is frontier utilization (49 %) and local latency
(265 s p50). Nemotron is complementary (29 both / 19 / 18 / 30 on TEST; unique successes in
S10/S06/S11 where Qwen3.8 never finishes) but its 27 silent failures are what no gate sees.
No local arm dominates another. Next (exactly one): R7 reasoning-budget calibration of the
frozen Qwen3.8 execution system — not a router, not QLoRA; not started.
