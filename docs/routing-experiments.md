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
| R4 | Deterministic weak→strong cascade | **done** — policy `verifier` (dev replay, pre-registered rule); dev live 50.0% all-pass at 22.9% strong calls, **test 49.0% at 21.9%**, 0 unnecessary escalations, rescue 90%; see below |
| R5 | Predictive / stage routing | not started |

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
