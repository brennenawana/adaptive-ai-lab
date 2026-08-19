# R6 — Modern Local Specialist Refresh: Report

**Milestone:** R6 (`docs/FIS_R6_Modern_Local_Specialist_Refresh_Plan.html`) · **Contract:** `docs/R6_EXPERIMENT_CONTRACT.md` (frozen blob `0604d661…` at `b4e9095`; amendments appended only, § 17) · **Registry:** `learning/registry/r6/` (records, hash-chained state logs, run ledger, analyses) · **Suite:** v3, unchanged · **Window:** 2026-08-18 20:59 UTC (`/goal`) → 2026-08-19 {{END_HHMM}} UTC.

## 0. One screen

| | Qwen3-8B (hist.) | Nemotron (hist.) | **Qwen3.5-9B** | **Qwen3.8-27B Q3_K_M** | **Ternary Bonsai 27B** | frontier |
|---|---|---|---|---|---|---|
| artifact SHA-256 / size | `d98cdcbd…` 5.03 GB | `c7be5d2c…` 18.92 GB | `03b74727…` 5.68 GB | `7f3b845b…` 13.82 GB | `868c1171…` 7.17 GB | Claude Opus 5 (CLI) |
| runtime | upstream `b1-9b05354` | upstream `b1-9b05354` | upstream `b1-9b05354` | upstream `b1-9b05354` | **Prism** `b1-9fcaed7` | — |
| cap (frozen) | 4096 | 8192 | 8192 | 8192 | 8192 | — |
| **DEV all-pass (48)** | 17 | 23 | **23** | **25** | **21** | 48 |
| DEV gate (§ 11) | control | control | REJECTED (latency, no-output; quality clause met) | QUALIFIED (≥ Nemotron) | QUALIFIED (floor + efficiency) | — |
| **TEST all-pass (96)** | 27 | 48 | — (not opened) | **47** | **{{B_TEST}}** | 95 |
| DEV / TEST silent failures | 16 / 47 | 13 / 27 | 12 / — | **1 / 2** | 21 / {{B_TEST_SILENT}} | 0 / 1 |
| DEV / TEST no-output (cap) | 9 (1) / 13 (1) | 12 (10) / 19 (15) | 10 (10) / — | 22 (22) / 47 (47) | 5 (4) / {{B_TEST_NOOUT}} | 0 / 0 |
| unchanged R4 cascade DEV / TEST | 32, FN 16 / 48, FN 47 | 35, FN 13 / 69, FN 26 | 36, FN 12 / — | **47, FN 1 / 93, FN 2** (util 46 / 49 %) | 27, FN 21 / {{B_R4_TEST}} | — |
| p50 wall DEV / TEST | 12.9 / 13.2 s | 53.8 / 55.8 s | 58.1 s / — | 263 / 265 s | 79.5 / {{B_P50_TEST}} s | 37.2 / 37.8 s |
| resident GPU, served alone | ~6.4 GiB † | ~15 GiB †‡ | 7.1 GiB | 15.1 GiB | 9.1 GiB | — |
| unique TEST successes among locals | 3 | 12 | — | 15 | {{B_UNIQUE}} | (26 vs all locals) |
| dominated? | by frontier only | by frontier only | by frontier only (DEV) | by frontier only | by frontier only | — |

† not re-measured in R6; ‡ partially CPU-offloaded, beside the resident Qwen3-8B server. **No local arm dominates any other local arm** on DEV or TEST (pairwise tables § 6–7).

**Answers in one line each.** *Qwen3-8B* is now a historical control only (§ 2). *Qwen3.5-9B* materially improves DEV quality (+6 all-pass, equal to Nemotron) but fails the pre-registered reliability and latency clauses (10 cap hits, 4.5× Qwen3-8B's wall) — a real quality gain, not a drop-in small-tier replacement at this reasoning budget (§ 5.1). *Q3_K_M* won the TRAIN-only quant selection on quality (§ 4). *Qwen3.8-27B* is the strongest local on DEV (25/48) and within one case of Nemotron on TEST (47 vs 48/96); it is **not** better than Nemotron on all-pass but is categorically better on silent-failure burden (2 vs 27 on TEST) and therefore on the unchanged R4 cascade (93/96 vs 69/96); it is slower (265 s vs 56 s p50) and uses the whole card; the two are complementary, not dominated (§ 5.2, § 7). *Nemotron* retains 12 unique TEST successes, concentrated in S10/S06/S11 where Qwen3.8 never finishes (§ 7). *Bonsai* is a real efficiency point by the contract's definition ({{B_ONE_LINE}}) but carries the largest silent-failure burden of any arm (§ 5.3). The cheapest sufficient oracle structure changes: with Qwen3.8 under the *unchanged* R4 verifier gate nearly every residual failure is visible, so the 93/96 system needs no learned router (§ 8). Remaining silent failures are evidence-citation failures in the 9B/Bonsai tier and two in Qwen3.8 (§ 9). The evidence favours **a reasoning-budget (cap/context) milestone on the frozen Qwen3.8-27B execution system** as the single next step — not QLoRA specialization and not a new router (§ 11). New inference: {{CALLS}} local cases, **0 frontier calls**; wall {{WALL_TOTAL}} h across phases (§ 10).

## 1. Frozen baseline — asserted at start and end

Suite v3 corpus `1e7c5278ba1f4cc1cc96fa8a1f04946ab622270eaba4c5671274c21e9d39e528` (train 144 `d9d1570e…`, dev 48 `5d5c94b0…`, test 96 `8deea4a2…`), tag `suite-v3` → `7764601`; scorer 3 / verifier 3 / ontology 1 / prompt 1; weak-arm prompt `cause_action_directed` (sha256 `40111d53…`), FIXED_EVIDENCE plan `_phase_two(limit=6)`; greedy, seed 42, `--parallel 1`; frontier `E4-v3-dev` (48/48) and `E4-v3-96` (95/96) reused offline; historical Qwen3-8B/Nemotron DEV/TEST/TRAIN rows replayed, never rerun. Asserted at R6.0 (bootstrap) and again at the end: {{BASELINE_END}}. Tree hashes of `scenarios/`, `evals/scorers/`, `fis_platform/verification/`, `fis_platform/tool_broker/`, `services/`, `schemas/` are unchanged since the tag; `fis_platform/model_gateway/gateway.py` gained three R6 manifests (additive). No new frontier calls were made.

## 2. Provenance (R6.1) — what is now cryptographically versioned

`learning/registry/r6/` (tracked): 6 artifact records, 2 runtime records, 3 generation-config records, 4 candidate directories with hash-chained append-only state logs anchored by `HEAD.json`, the run ledger, phase markers, the pre-registered TRAIN pilot, the historical-control execution systems (`/proc` server args of the still-resident 8082/8083 sessions, captured before they were stopped), and the offline analyses.

| Artifact | Source (repo @ revision) | SHA-256 | bytes | GGUF md digest v1 | license |
|---|---|---|---|---|---|
| `Qwen3-8B-Q4_K_M.gguf` | `Qwen/Qwen3-8B-GGUF` @ `6a569868d07d3bd59e8b97fb001bf8c0b254bb20` | `d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785` | 5,027,783,488 | `a0f5e4c4…` | apache-2.0 |
| `NVIDIA-Nemotron-3.5-Lightning-30B-A3B-IQ4_XS.gguf` | `bartowski/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF` @ `be042bfc3b0fbe10b78c9b91b7f1a9fe392f1062` | `c7be5d2ca9700a0e02de1a6707bbcdda3b38b7721caef7ac05bf9dda158aa270` | 18,918,361,056 | `41423697…` | openmdw-1.1 |
| `Qwen3.5-9B-Q4_K_M.gguf` | `unsloth/Qwen3.5-9B-GGUF` @ `99a1b2185534379e6e8b5ec869da25d3e7b3f73c` | `03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8` | 5,680,522,464 | `80e78173…` | apache-2.0 |
| `Qwen3.8-27B-Q3_K_M.gguf` | `unsloth/Qwen3.8-27B-GGUF` @ `fa83dc3165d11f3cc617c41ba5fbfb22b2791ca8` | `7f3b845b563888ec3abc269474cf744bf703a7ce8766dbb7f696c63975facfd7` | 13,818,690,528 | `5697d81f…` | apache-2.0 |
| `Qwen3.8-27B-UD-Q3_K_XL.gguf` | `unsloth/Qwen3.8-27B-GGUF` @ `1cff334a4a228324d4ee1f76d55d372588f0d556` | `00cf92e666c6af6566996c38c89a44ccdb6449ea25ef0f112a452c853b2a71e2` | 13,441,059,904 | `9eafa178…` | apache-2.0 |
| `Ternary-Bonsai-27B-Q2_0.gguf` | `prism-ml/Ternary-Bonsai-27B-gguf` @ `abbae723028d71be674e71e1a71201a6f43fab22` | `868c11714cf8fe47f5ec9eeb2be0ab1a337112886f92ee0ede6b855c4fa31757` | 7,165,121,600 | `50ee7e09…` | not in GGUF (plan: Qwen3.6-27B lineage) |

All six SHA-256s were recomputed from local bytes; every (repo, revision, file) resolves upstream to the same LFS digest (operator check, 2026-08-18). **Qwen3-8B provenance is closed** — the official `Qwen/Qwen3-8B-GGUF` artifact at the pinned revision; its descriptive GGUF KV ("Qwen3 8B Awq Compatible Instruct") misdescribes a plain Q4_K/Q6_K file and is recorded as an anomaly; SHA + byte length identify it. **Nemotron** is pinned to the bartowski file-upload commit `be042bfc` (the file was re-uploaded upstream; an earlier 18,166,697,920-byte version was replaced on 2026-08-11) — reproducible artifact + runtime (upstream record + captured server args + historical serve script flags). **Both `Qwen3.8-27B-*` files are Unsloth Qwen3.8 artifacts; they were never Bonsai** (two doc mislabels corrected). **Qwen3.5-9B** was acquired at 21:05 UTC by a pinned-revision download and digest-verified before placement. Historical-control binding is by *attribution* (served `model_path` + `llamacpp_build` on their trajectories), stated as such in the contract.

Runtimes: `llama.cpp-upstream-9b05354@0e90f9139596` (ggml-org/llama.cpp `9b05354…`, local CUDA build `b1-9b05354`, sm_120a, cudart 12.8.90 / nvcc 12.8.93; digest over `llama-server` + 10 `lib*.so*`; driver 610.43.02, KMD 610.62, CUDA UMD 13.3; RTX 5080 Laptop 16 GB) and `llama.cpp-prism-9fcaed7@4f0400389699` (PrismML fork `prism-b9596-9fcaed7`, `b1-9fcaed7`). Bonsai needs Prism because upstream and Prism both define `GGML_TYPE_Q2_0 = 42` with a different block geometry (64 vs 128); the runtime digest is the only discriminator.

Every R6 trajectory carries `candidate_id, artifact_id, artifact_sha256, gguf_metadata_digest, runtime_id, runtime_digest, server_args_digest, generation_config_digest, execution_system_digest, local_server_session, git_head`, tree state and GPU-memory samples. `run_eval --candidate` refuses a model call unless the registry state allows the split, the code tree is committed (only `learning/registry/r6/` may be ahead), exactly one `llama-server` is resident, and the **running** server's `/props` build, model-file SHA (re-hashed at start), `/proc` args, executable and mapped shared objects match the registered execution system; local llama.cpp arms cannot run without `--candidate` (historical local arms are replay-only). Two independent Fable reviews (provenance/state audit; contract/gates) ran before DEV; every finding was fixed in code or recorded in contract § 17.

## 3. State machine and final states

`REGISTERED → TRAIN_COMPATIBLE → CONTRACT_FROZEN → DEV_EVALUATED → {DEV_QUALIFIED | DEV_REJECTED} → TEST_UNLOCKED → TEST_EVALUATED`; `WITHDRAWN` only before the freeze. Enforced and tested on temporary registries (`tests/test_r6_state_machine.py`): one quant per family at/after the freeze; one DEV run per candidate (ledger + canonical-storage check); TEST only at `TEST_UNLOCKED` on the unlock's run id, bound to the re-hashed artifact SHA, runtime/gen-config/execution-system digests, DEV result digest and contract blob; results written once; the DEV verdict is the gate function's (re-derived from the stored result); no env/flag registry root; registry resets refused.

Final: `qwen35-9b@9f010021daba` **DEV_REJECTED** · `qwen38-27b-q3km@8528f049af75` **TEST_EVALUATED** · `qwen38-27b-udq3kxl@d9d3f9771d67` **WITHDRAWN** (quant-selection loser) · `bonsai-27b@ddd13c20e0e8` **TEST_EVALUATED**.

## 4. TRAIN (R6.2) — calibration and selection, TRAIN only

Pilot `r6-train-pilot-v1`: the first 3 TRAIN cases of each class (36 ids, digest `fde034b0…`). Every candidate was served with the historical Qwen server args (`-c 16384 -ngl 99 --flash-attn on --cache-type-k/v q8_0 --jinja --parallel 1`; server-args digest `7c6f27cb…`), cap 8192, one server resident, fresh session + 8-token prime. The Q3_K_M `--fit` probe showed 66/66 layers fit (12.4 GiB model buffer), so no CPU offload was needed anywhere.

| TRAIN pilot (36 ids) | all-pass | no-output (cap) | silent | p50 wall | tok/s | resident GiB |
|---|---|---|---|---|---|---|
| Qwen3-8B (`R5-qwen-train`, same ids) | 8 | 7 (0) | 18 | 11.4 s | — | — |
| Nemotron (`R5-nemotron-train`, same ids) | 15 | 5 (5) | 11 | 64.0 s | — | — |
| Qwen3.5-9B | 13 | 11 (10) | 10 | 68.5 s | 81 | 7.9 |
| Qwen3.8-27B Q3_K_M | **20** | 15 (15) | 1 | 288.6 s | 28 | 15.7 |
| Qwen3.8-27B UD-Q3_K_XL | 16 | 18 (18) | 2 | 201.0 s | 39 | 14.8 |
| Ternary Bonsai 27B | 15 | 5 (4) | 12 | 72.2 s | 58 | 9.2 |

**Quant selection (contract § 7):** rule 1 decided — Q3_K_M 20 vs UD-Q3_K_XL 16 (pairwise 13/7/3/13; UD is 39 % faster per token but truncates more). UD withdrawn; only Q3_K_M reached DEV. **Cap calibration (§ 6):** no candidate met the ≤ 3/36 truncation tolerance at any allowed cap, so all were frozen at 8192 with the truncation recorded (Qwen3.5 27.8 %, Qwen3.8 41.7 %, Bonsai 11.1 %). **Bonsai eligibility (§ 8):** the Prism server answers strict `json_schema`, returns `timings`/`system_fingerprint`/`reasoning_content`, 31/36 parsable, resource capture works → eligible. **Stability probes (§ 9):** 12/12 identical output digests (or identical no-output) for Qwen3.5-9B (same session), Qwen3.8 Q3_K_M (**across** sessions), Bonsai (same session; interrupted after 8 cases by a tool timeout and resumed in the same session — the only resumed run in R6).

## 5. DEV (R6.4) — gates applied exactly as frozen

{{DEV_TABLES}}

### 5.1 Modern small — Qwen3.5-9B → DEV_REJECTED (reported per clause)
all-pass **23/48 ≥ 22: met** (+6 over Qwen3-8B, equal to Nemotron's DEV); no-output **10 > 8: failed** (all ten are cap hits; median 5.4k output tokens, 5× Qwen3-8B); p50 wall **58.1 s > 38.6 s: failed** (94 tok/s but five times the tokens). Root-cause correctness 35/48 (best of all locals incl. Qwen3.8), evidence 25, silent 12. It is complementary with Nemotron (13 both / 10 / 10 / 15) and with Qwen3.8 (13 / 10 / 12 / 13). TEST was not opened; by the contract it is a material quality gain that is not a drop-in small-tier replacement at this reasoning budget.

### 5.2 Modern strong — Qwen3.8-27B Q3_K_M → DEV_QUALIFIED (clause 1)
all-pass **25/48 ≥ 23**. Failure shape unlike any earlier arm: 22 no-outputs, all cap hits (reasoning > 8192 tokens; S07/S10/S11/S12 almost never finish), and **one** verifier-clean wrong answer (`S08-2000007`); 25 of the 26 completed answers passed. p50 263 s (30 tok/s, dense 27B at Q3), 15.1 GiB resident. The alternative branch (p50 ≤ 40.4 s or no-output ≤ 6) was not met — it qualifies on quality alone.

### 5.3 Efficiency — Ternary Bonsai 27B → DEV_QUALIFIED
all-pass **21/48 ≥ 20**; resident memory 9,126 MiB = **0.61×** Qwen3.8's 15,064 (≤ 0.65); p50 79.5 s = **0.30×** Qwen3.8's (≤ 1.25). But 21 of its 27 failures are verifier-clean wrong answers (14 evidence-only, 7 root-cause) — the largest silent burden of any arm; the unchanged R4 gate rescues only 6 of them (R4 27/48, FN 21).

## 6. TEST (R6.5) — exactly once per qualified candidate

{{TEST_TABLES}}

**Pre-registered readings (contract § 11 materiality).** Qwen3.8-27B vs Nemotron: 47 vs 48/96 → **competitive** (within ±4), not "better"; pairwise 29 both / 19 Nemotron-only / 18 Qwen3.8-only / 30 neither → complementary. Qwen3.8 vs Qwen3-8B: 30 Qwen3.8-only vs 10 Qwen3-8B-only (paired difference +20, well above the +8 materiality bar). {{B_TEST_READING}} The frontier dominates every local arm (each local's pass set ⊂ frontier's, one `S12-3002011` case fails everywhere).

## 7. Unchanged R4, post-answer oracle, overlap, unique rescue, tier coverage, dominance

**R4 (verifier cascade, unchanged, replayed against the frozen frontier rows).** The gate escalates on no-output / verifier failure — exactly Qwen3.8's failure mode — so on TEST Qwen3.8 + R4 reaches **93/96** (FN 2, utilization 49.0 %, 0 unnecessary, $0.0628/success) against Nemotron + R4 69/96 (FN 26, util 21.9 %, $0.0380) and Qwen3-8B + R4 48/96 (FN 47). The price is frontier utilization (47 calls vs 21) and wall time (p50 268 s incl. escalations). The **post-answer oracle** (escalate exactly the local failures) is 95/96 for every arm; Qwen3.8's oracle gap is 2 cases — R4 is already the oracle for it, because its failures are visible. {{B_R4_TEXT}}

**Unique successes on TEST (among locals):** Qwen3.8 15 (S01 ×7, S04 ×4, S03, S06 ×2, S09 — the classes every earlier local scored 0–1 on), Nemotron 12 (S10 ×5, S06 ×3, S11 ×2, S02, S03), Qwen3-8B 3, {{B_UNIQUE_TEXT}}. **Dominance:** no local arm's pass set contains another's on either split; every pair is complementary; only the frontier dominates. Qwen3.8 does not *operationally* dominate Nemotron either (slower, more VRAM) — it wins on silent-failure burden and loses on latency.

**Tier coverage (cheapest-sufficient, descriptive, no router):** {{TIERS_TEXT}}

**Is Nemotron still useful?** Yes, as a complement: it finishes the long-reasoning classes (S10, S11, S06) inside its budget where Qwen3.8 truncates, at a fifth of the latency; but it carries 27 silent failures that no deterministic gate sees. **Does Qwen3.8 simplify the stack?** Under the unchanged R4 gate it makes a learned silent-failure router unnecessary (FN 2); it does not remove the frontier (49 % utilization) and it raises latency.

## 8. Cheapest / lowest-burden oracle structure with the new candidates

With Qwen3.8-27B as the local tier, the oracle is the deterministic verifier gate itself: local answers that finish are almost always right (TEST: 47 pass of 49 finished); answers that do not finish are visibly no-output and escalate. 93/96 at 49 % frontier utilization, 0 unnecessary escalations, 2 false negatives (`S03-3000002`, `S11-3001010`, both evidence-only). A two-local tier (Qwen3.8 → Nemotron → frontier) would cover 47 + 19 = 66 locally in the descriptive ordering, but Nemotron's 27 TEST silent failures mean a real cascade could not route to it safely without a learned detector — which R5 showed does not generalise. The lowest-burden *sufficient* structure is therefore the single-local Qwen3.8 + R4 cascade; its burden is latency (265 s local p50) and VRAM (15.1 GiB), not routing complexity.

## 9. What silent failures remain

TEST silent (verifier-clean, wrong): Qwen3-8B 47 (33 evidence-only, 14 root cause), Nemotron 27 (16 / 11), **Qwen3.8 2 (2 evidence-only)**, {{B_SILENT_TEXT}}. DEV: Qwen3-8B 16, Nemotron 13, Qwen3.5-9B 12 (9 evidence-only, 3 root cause), Qwen3.8 1, Bonsai 21 (14 / 7). The modern strong model reduces verifier-clean silent failures by more than an order of magnitude relative to both controls — by converting failure into visible truncation. The 9B and Bonsai tiers keep the historical evidence-citation failure shape (root cause right, citations thin).

## 10. Accounting — new inference and wall time

{{ACCOUNTING}}

## 11. Residual failure mechanisms of the strongest modern local, and the one next milestone

Qwen3.8-27B Q3_K_M's residual failures are almost entirely **reasoning-budget truncations** — 47 of 49 TEST failures and 22 of 23 DEV failures are `stop_reason=length` at 8192 tokens with no content emitted (28–34k reasoning characters), concentrated in S07, S10, S11, S12 (0/8 each on TEST) and S06/S02; the model's median completed answer is already ~8k tokens. When it finishes it is right (TEST 47/49, DEV 25/26). This is not an evidence-discipline gap, not a root-cause gap and not a schema gap — the behaviours QLoRA specialization was proposed to train — and it is not a routing gap (the failures are visible). It is a budget/latency gap: the cap set pre-registered for R6 stopped at the manifest ceiling (8192) and the contract forbids changing it after DEV.

**Does post-training remain justified?** Not for the strongest substrate on this evidence: Qwen3.8's behaviour when it completes is already at the frontier's level on the classes it finishes, and its dominant failure mode is a budget the harness imposes. Specialization might still be argued for the cheap tier (Qwen3.5-9B / Bonsai evidence citation), but those are quality-dominated by Qwen3.8 and the contract's gates rejected or merely floor-qualified them. **Favoured substrate if specialization is ever revisited:** Qwen3.8-27B Q3_K_M (`qwen3.8-27b-q3_k_m@7f3b845b5638` on `llama.cpp-upstream-9b05354@0e90f9139596`).

**Recommended next milestone (exactly one, not started):** **R7 — reasoning-budget calibration for the frozen Qwen3.8-27B execution system**: a pre-registered TRAIN-only study of caps beyond 8192 (e.g. 12288 at `-c 16384`, or a larger context) and, if the model's chat template supports it, a declared thinking-budget toggle — selected on TRAIN, frozen, then one DEV and one TEST under the same Suite v3, provenance registry and state machine, with the R4 replay and the latency/VRAM cost reported alongside. Its question is the one R6 leaves open: how much of the 49 % truncation converts to passes, at what wall time, and whether the UD-Q3_K_XL quant (39 % faster, frozen out by the quality-first rule at 8192) becomes the better operating point when the budget is no longer the binding constraint. No training, no router.

## A. Definition-of-done checklist

{{DOD}}
