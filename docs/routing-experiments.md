# Routing experiments — the R-series

Protocol and results for the routing track defined in
`FIS_MSI_Pivot_Guide_Switchyard_Nemotron.html`. A separate series so routing
experiments cannot be confused with the prompt/context E-series. Same rules:
**selection on dev, one test confirmation, one factor per arm, gold labels may
score a route but never choose it.**

| Track | Question | Status |
|---|---|---|
| R0 | What is the causally selected local configuration before routing? | **done** — `weak-baseline-v1` below |
| R1 | Can Switchyard sit in the model path without changing outcomes? | **measured** — no, not for the grammar-constrained local arm as shipped; see below |
| R2 | How much routing opportunity exists between weak and strong on dev? | **done** — see below |
| R3 | Nemotron 3.5 Lightning as candidate weak arm | not started (later milestone) |
| R4 | Deterministic weak→strong cascade | not started |
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

### Results

_(filled from `make r1-compare` when the runs complete — see OVERNIGHT_STATUS.md)_

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
