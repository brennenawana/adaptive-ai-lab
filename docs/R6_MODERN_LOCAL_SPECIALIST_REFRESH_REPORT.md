# R6 — Modern Local Specialist Refresh: Report

**Milestone:** R6 (`docs/FIS_R6_Modern_Local_Specialist_Refresh_Plan.html`) · **Contract:** `docs/R6_EXPERIMENT_CONTRACT.md` (frozen blob `0604d661…` at `b4e9095`; amendments appended only, § 17) · **Registry:** `learning/registry/r6/` (records, hash-chained state logs, run ledger, analyses) · **Suite:** v3, unchanged · **Window:** 2026-08-18 20:59 UTC (`/goal`) → 2026-08-19 ~22:30 UTC.

## 0. One screen

| | Qwen3-8B (hist.) | Nemotron (hist.) | **Qwen3.5-9B** | **Qwen3.8-27B Q3_K_M** | **Ternary Bonsai 27B** | frontier |
|---|---|---|---|---|---|---|
| artifact SHA-256 / size | `d98cdcbd…` 5.03 GB | `c7be5d2c…` 18.92 GB | `03b74727…` 5.68 GB | `7f3b845b…` 13.82 GB | `868c1171…` 7.17 GB | Claude Opus 5 (CLI) |
| runtime | upstream `b1-9b05354` | upstream `b1-9b05354` | upstream `b1-9b05354` | upstream `b1-9b05354` | **Prism** `b1-9fcaed7` | — |
| cap (frozen) | 4096 | 8192 | 8192 | 8192 | 8192 | — |
| **DEV all-pass (48)** | 17 | 23 | **23** | **25** | **21** | 48 |
| DEV gate (§ 11) | control | control | REJECTED (latency, no-output; quality clause met) | QUALIFIED (≥ Nemotron) | QUALIFIED (floor + efficiency) | — |
| **TEST all-pass (96)** | 27 | 48 | — (not opened) | **47** | **34** | 95 |
| DEV / TEST silent failures | 16 / 47 | 13 / 27 | 12 / — | **1 / 2** | 21 / 41 | 0 / 1 |
| DEV / TEST no-output (cap) | 9 (1) / 13 (1) | 12 (10) / 19 (15) | 10 (10) / — | 22 (22) / 47 (47) | 5 (4) / 8 (8) | 0 / 0 |
| unchanged R4 cascade DEV / TEST | 32, FN 16 / 48, FN 47 | 35, FN 13 / 69, FN 26 | 36, FN 12 / — | **47, FN 1 / 93, FN 2** (util 46 / 49 %) | 27, FN 21 / 55, FN 40 | — |
| p50 wall DEV / TEST | 12.9 / 13.2 s | 53.8 / 55.8 s | 58.1 s / — | 263 / 265 s | 79.5 / 76.8 s | 37.2 / 37.8 s |
| resident GPU, served alone | ~6.4 GiB † | ~15 GiB †‡ | 7.1 GiB | 15.1 GiB | 9.1 GiB | — |
| unique TEST successes among the four locals | 3 | 6 (12 vs Qwen3-8B + Qwen3.8 only) | — | 13 (15 vs Qwen3-8B + Nemotron only) | 3 | 23 vs all locals |
| dominated? | by frontier only | by frontier only | by frontier only (DEV) | by frontier only | by frontier only | — |

† not re-measured in R6; ‡ partially CPU-offloaded, beside the resident Qwen3-8B server. **No local arm dominates any other local arm** on DEV or TEST (pairwise tables § 6–7).

**Answers in one line each.** *Qwen3-8B* is now a historical control only (§ 2). *Qwen3.5-9B* materially improves DEV quality (+6 all-pass, equal to Nemotron) but fails the pre-registered reliability and latency clauses (10 cap hits, 4.5× Qwen3-8B's wall) — a real quality gain, not a drop-in small-tier replacement at this reasoning budget (§ 5.1). *Q3_K_M* won the TRAIN-only quant selection on quality (§ 4). *Qwen3.8-27B* is the strongest local on DEV (25/48) and within one case of Nemotron on TEST (47 vs 48/96); it is **not** better than Nemotron on all-pass but is categorically better on silent-failure burden (2 vs 27 on TEST) and therefore on the unchanged R4 cascade (93/96 vs 69/96); it is slower (265 s vs 56 s p50) and uses the whole card; the two are complementary, not dominated (§ 5.2, § 7). *Nemotron* retains unique TEST successes (12 against Qwen3-8B + Qwen3.8, 6 once Bonsai is in the set), concentrated in S10/S06/S11 where Qwen3.8 never finishes (§ 7). *Bonsai* is a real efficiency point by the contract's definition (TEST 34/96 at 0.61× memory and 0.29× latency of Qwen3.8, 10.2 GiB resident) but carries the largest silent-failure burden of any arm (§ 5.3). The cheapest sufficient oracle structure changes: with Qwen3.8 under the *unchanged* R4 verifier gate nearly every residual failure is visible, so the 93/96 system needs no learned router (§ 8). Remaining silent failures are evidence-citation failures in the 9B/Bonsai tier and two in Qwen3.8 (§ 9). The evidence favours **a reasoning-budget (cap/context) milestone on the frozen Qwen3.8-27B execution system** as the single next step — not QLoRA specialization and not a new router (§ 11). New inference: 516 local cases, **0 frontier calls**; wall ≈ 25 h across phases (§ 10).

## 1. Frozen baseline — asserted at start and end

Suite v3 corpus `1e7c5278ba1f4cc1cc96fa8a1f04946ab622270eaba4c5671274c21e9d39e528` (train 144 `d9d1570e…`, dev 48 `5d5c94b0…`, test 96 `8deea4a2…`), tag `suite-v3` → `7764601`; scorer 3 / verifier 3 / ontology 1 / prompt 1; weak-arm prompt `cause_action_directed` (sha256 `40111d53…`), FIXED_EVIDENCE plan `_phase_two(limit=6)`; greedy, seed 42, `--parallel 1`; frontier `E4-v3-dev` (48/48) and `E4-v3-96` (95/96) reused offline; historical Qwen3-8B/Nemotron DEV/TEST/TRAIN rows replayed, never rerun. Asserted at R6.0 (bootstrap) and again at the end: `scripts/corpus_digest.py --check` → DETERMINISTIC (same four digests); scorer 3 / verifier 3; prompt sha `40111d53…`; `git diff suite-v3 -- fis_platform/verification scenarios evals/scorers services/ai_orchestrator/prompts.py services/ai_orchestrator/investigate.py fis_platform/tool_broker schemas` empty. Tree hashes of `scenarios/`, `evals/scorers/`, `fis_platform/verification/`, `fis_platform/tool_broker/`, `services/`, `schemas/` are unchanged since the tag; `fis_platform/model_gateway/gateway.py` gained three R6 manifests (additive). No new frontier calls were made.

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

### DEV — arms {'qwen3-8b': 'V3-qwen-dev', 'nemotron': 'V3-nemotron-dev', 'qwen35-9b': 'R6-qwen35-dev', 'qwen38-27b': 'R6-qwen38-q3km-dev', 'bonsai-27b': 'R6-bonsai-dev'} vs frontier `E4-v3-dev`

**Quality / failure shape / runtime**

| metric | qwen3-8b | nemotron | qwen35-9b | qwen38-27b | bonsai-27b | frontier |
|---|---|---|---|---|---|---|
| strict all-pass | 17/48 (35.4%) | 23/48 (47.9%) | 23/48 (47.9%) | 25/48 (52.1%) | 21/48 (43.8%) | 48/48 (100.0%) |
| root cause correct | 30 | 31 | 35 | 26 | 35 | 48 |
| action acceptable | 35 | 35 | 37 | 26 | 39 | 48 |
| evidence recall ≥ 0.8 | 20 | 28 | 25 | 26 | 23 | 48 |
| verifier passed | 33 | 36 | 35 | 26 | 42 | 48 |
| no-output (cap / schema) | 9 (1 / 8) | 12 (10 / 2) | 10 (10 / 0) | 22 (22 / 0) | 5 (4 / 1) | 0 (0 / 0) |
| silent (verifier-clean, wrong) | 16 | 13 | 12 | 1 | 21 | 0 |
| root-cause failures | 18 | 17 | 13 | 22 | 13 | 0 |
| evidence failures | 13 | 8 | 12 | 0 | 14 | 0 |
| p50 / p95 wall (s) | 12.9 / 41.7 | 53.8 / 96.0 | 58.1 / 88.9 | 263.3 / 280.4 | 79.5 / 145.6 | 37.2 / 60.1 |
| output tokens p50 / sum | 1096 / 65588 | 4547 / 238293 | 5413 / 271798 | 8002 / 325937 | 4556 / 227139 | 3360 / 180033 |
| tok/s median | 89.4 | 85.5 | 94.1 | 30.0 | 56.2 | 91.9 |
| resident GPU MiB (max sample) | — | — | 7147 | 15064 | 9126 | — |

**Failure patterns**

| failure pattern | qwen3-8b | nemotron | qwen35-9b | qwen38-27b | bonsai-27b | frontier |
|---|---|---|---|---|---|---|
| no-output | 9 | 12 | 10 | 22 | 5 | 0 |
| pass | 17 | 23 | 23 | 25 | 21 | 48 |
| silent:evidence_only | 9 | 8 | 9 | 0 | 14 | 0 |
| silent:other | 0 | 0 | 0 | 1 | 0 | 0 |
| silent:root_cause | 7 | 5 | 3 | 0 | 7 | 0 |
| verifier-fail(unsupported) | 6 | 0 | 3 | 0 | 1 | 0 |

**Unchanged R4 verifier cascade (offline replay)**

| arm | R4 cascade all-pass | escalated (util.) | unnecessary | routing FN | rescued | $/success | wall p50 (s) |
|---|---|---|---|---|---|---|---|
| qwen3-8b | 32/48 | 15 (31.2%) | 0 | 16 | 15 | 0.0608 | 16.7 |
| nemotron | 35/48 | 12 (25.0%) | 0 | 13 | 12 | 0.0453 | 54.7 |
| qwen35-9b | 36/48 | 13 (27.1%) | 0 | 12 | 13 | 0.0463 | 60.7 |
| qwen38-27b | 47/48 | 22 (45.8%) | 0 | 1 | 22 | 0.0594 | 263.3 |
| bonsai-27b | 27/48 | 6 (12.5%) | 0 | 21 | 6 | 0.0271 | 79.5 |

**Post-answer ideal oracle vs frontier**

| arm | local-safe | rescueable | unresolved | oracle all-pass | oracle utilization |
|---|---|---|---|---|---|
| qwen3-8b | 17 | 31 | 0 | 48/48 | 64.6% |
| nemotron | 23 | 25 | 0 | 48/48 | 52.1% |
| qwen35-9b | 23 | 25 | 0 | 48/48 | 52.1% |
| qwen38-27b | 25 | 23 | 0 | 48/48 | 47.9% |
| bonsai-27b | 21 | 27 | 0 | 48/48 | 56.2% |

**Pairwise pass sets**

| pair (A vs B) | both | A-only | B-only | neither | relation |
|---|---|---|---|---|---|
| qwen3-8b vs nemotron | 13 | 4 | 10 | 21 | complementary |
| qwen3-8b vs qwen35-9b | 12 | 5 | 11 | 20 | complementary |
| qwen3-8b vs qwen38-27b | 11 | 6 | 14 | 17 | complementary |
| qwen3-8b vs bonsai-27b | 8 | 9 | 13 | 18 | complementary |
| qwen3-8b vs frontier | 17 | 0 | 31 | 0 | B dominates A |
| nemotron vs qwen35-9b | 13 | 10 | 10 | 15 | complementary |
| nemotron vs qwen38-27b | 14 | 9 | 11 | 14 | complementary |
| nemotron vs bonsai-27b | 13 | 10 | 8 | 17 | complementary |
| nemotron vs frontier | 23 | 0 | 25 | 0 | B dominates A |
| qwen35-9b vs qwen38-27b | 13 | 10 | 12 | 13 | complementary |
| qwen35-9b vs bonsai-27b | 15 | 8 | 6 | 19 | complementary |
| qwen35-9b vs frontier | 23 | 0 | 25 | 0 | B dominates A |
| qwen38-27b vs bonsai-27b | 14 | 11 | 7 | 16 | complementary |
| qwen38-27b vs frontier | 25 | 0 | 23 | 0 | B dominates A |
| bonsai-27b vs frontier | 21 | 0 | 27 | 0 | B dominates A |

**Unique successes**

| arm | unique successes among locals | unique incl. frontier |
|---|---|---|
| qwen3-8b | 1 | 0 |
| nemotron | 1 | 0 |
| qwen35-9b | 3 | 0 |
| qwen38-27b | 5 | 0 |
| bonsai-27b | 2 | 0 |
| frontier | — | 6 |

**Tier coverage (cheapest-sufficient)**

| ordering (cheapest first → frontier) | first-pass by tier | covered / n |
|---|---|---|
| qwen3-8b,qwen35-9b,qwen38-27b → frontier | qwen38-27b: 9, frontier: 11, qwen3-8b: 17, qwen35-9b: 11 | 48/48 |
| qwen35-9b,qwen38-27b → frontier | qwen38-27b: 12, frontier: 13, qwen35-9b: 23 | 48/48 |
| qwen35-9b,bonsai-27b,qwen38-27b → frontier | qwen38-27b: 10, bonsai-27b: 6, qwen35-9b: 23, frontier: 9 | 48/48 |
| qwen35-9b,nemotron,qwen38-27b → frontier | qwen38-27b: 6, frontier: 9, nemotron: 10, qwen35-9b: 23 | 48/48 |
| qwen35-9b,qwen38-27b,nemotron → frontier | qwen38-27b: 12, frontier: 9, qwen35-9b: 23, nemotron: 4 | 48/48 |
| qwen3-8b,nemotron → frontier | frontier: 21, qwen3-8b: 17, nemotron: 10 | 48/48 |
| bonsai-27b,qwen38-27b → frontier | qwen38-27b: 11, bonsai-27b: 21, frontier: 16 | 48/48 |

**All-pass by class**

| class | qwen3-8b | nemotron | qwen35-9b | qwen38-27b | bonsai-27b | frontier |
|---|---|---|---|---|---|---|
| S01 | 0 | 0 | 0 | 3 | 1 | 4 |
| S02 | 2 | 2 | 3 | 2 | 4 | 4 |
| S03 | 0 | 2 | 0 | 4 | 1 | 4 |
| S04 | 1 | 0 | 4 | 4 | 3 | 4 |
| S05 | 4 | 4 | 4 | 4 | 4 | 4 |
| S06 | 2 | 3 | 1 | 1 | 1 | 4 |
| S07 | 1 | 0 | 3 | 0 | 0 | 4 |
| S08 | 2 | 4 | 4 | 3 | 3 | 4 |
| S09 | 4 | 4 | 2 | 3 | 1 | 4 |
| S10 | 1 | 4 | 2 | 0 | 2 | 4 |
| S11 | 0 | 0 | 0 | 0 | 1 | 4 |
| S12 | 0 | 0 | 0 | 1 | 0 | 4 |

### 5.1 Modern small — Qwen3.5-9B → DEV_REJECTED (reported per clause)
all-pass **23/48 ≥ 22: met** (+6 over Qwen3-8B, equal to Nemotron's DEV); no-output **10 > 8: failed** (all ten are cap hits; median 5.4k output tokens, 5× Qwen3-8B); p50 wall **58.1 s > 38.6 s: failed** (94 tok/s but five times the tokens). Root-cause correctness 35/48 (best of all locals incl. Qwen3.8), evidence 25, silent 12. It is complementary with Nemotron (13 both / 10 / 10 / 15) and with Qwen3.8 (13 / 10 / 12 / 13). TEST was not opened; by the contract it is a material quality gain that is not a drop-in small-tier replacement at this reasoning budget.

### 5.2 Modern strong — Qwen3.8-27B Q3_K_M → DEV_QUALIFIED (clause 1)
all-pass **25/48 ≥ 23**. Failure shape unlike any earlier arm: 22 no-outputs, all cap hits (reasoning > 8192 tokens; S07/S10/S11/S12 almost never finish), and **one** verifier-clean wrong answer (`S08-2000007`); 25 of the 26 completed answers passed. p50 263 s (30 tok/s, dense 27B at Q3), 15.1 GiB resident. The alternative branch (p50 ≤ 40.4 s or no-output ≤ 6) was not met — it qualifies on quality alone.

### 5.3 Efficiency — Ternary Bonsai 27B → DEV_QUALIFIED
all-pass **21/48 ≥ 20**; resident memory 9,126 MiB = **0.61×** Qwen3.8's 15,064 (≤ 0.65); p50 79.5 s = **0.30×** Qwen3.8's (≤ 1.25). But 21 of its 27 failures are verifier-clean wrong answers (14 evidence-only, 7 root-cause) — the largest silent burden of any arm; the unchanged R4 gate rescues only 6 of them (R4 27/48, FN 21).

## 6. TEST (R6.5) — exactly once per qualified candidate

### TEST — arms {'qwen3-8b': 'V3-qwen-96', 'nemotron': 'V3-nemotron-96', 'qwen38-27b': 'R6-qwen38-q3km-test', 'bonsai-27b': 'R6-bonsai-test'} vs frontier `E4-v3-96`

**Quality / failure shape / runtime**

| metric | qwen3-8b | nemotron | qwen38-27b | bonsai-27b | frontier |
|---|---|---|---|---|---|
| strict all-pass | 27/96 (28.1%) | 48/96 (50.0%) | 47/96 (49.0%) | 34/96 (35.4%) | 95/96 (99.0%) |
| root cause correct | 68 | 65 | 49 | 74 | 96 |
| action acceptable | 78 | 74 | 49 | 80 | 95 |
| evidence recall ≥ 0.8 | 34 | 58 | 47 | 43 | 96 |
| verifier passed | 74 | 75 | 49 | 75 | 96 |
| no-output (cap / schema) | 13 (1 / 12) | 19 (15 / 4) | 47 (47 / 0) | 8 (8 / 0) | 0 (0 / 0) |
| silent (verifier-clean, wrong) | 47 | 27 | 2 | 41 | 1 |
| root-cause failures | 28 | 31 | 47 | 22 | 0 |
| evidence failures | 40 | 16 | 2 | 36 | 0 |
| p50 / p95 wall (s) | 13.2 / 29.1 | 55.8 / 93.9 | 265.4 / 279.3 | 76.8 / 150.6 | 37.8 / 59.5 |
| output tokens p50 / sum | 1153 / 129910 | 4850 / 480810 | 7936 / 665540 | 4088 / 432449 | 3526 / 354059 |
| tok/s median | 90.9 | 87.3 | 29.8 | 52.5 | 93.1 |
| resident GPU MiB (max sample) | — | — | 15186 | 10183 | — |

**Failure patterns**

| failure pattern | qwen3-8b | nemotron | qwen38-27b | bonsai-27b | frontier |
|---|---|---|---|---|---|
| no-output | 13 | 19 | 47 | 8 | 0 |
| pass | 27 | 48 | 47 | 34 | 95 |
| silent:action_only | 0 | 0 | 0 | 0 | 1 |
| silent:evidence_only | 33 | 16 | 2 | 29 | 0 |
| silent:root_cause | 14 | 11 | 0 | 12 | 0 |
| verifier-fail(unsupported) | 9 | 2 | 0 | 13 | 0 |

**Unchanged R4 verifier cascade (offline replay)**

| arm | R4 cascade all-pass | escalated (util.) | unnecessary | routing FN | rescued | $/success | wall p50 (s) |
|---|---|---|---|---|---|---|---|
| qwen3-8b | 48/96 | 22 (22.9%) | 0 | 47 | 21 | 0.0513 | 15.4 |
| nemotron | 69/96 | 21 (21.9%) | 0 | 26 | 21 | 0.0380 | 56.1 |
| qwen38-27b | 93/96 | 47 (49.0%) | 0 | 2 | 46 | 0.0628 | 268.1 |
| bonsai-27b | 55/96 | 21 (21.9%) | 0 | 40 | 21 | 0.0444 | 83.6 |

**Post-answer ideal oracle vs frontier**

| arm | local-safe | rescueable | unresolved | oracle all-pass | oracle utilization |
|---|---|---|---|---|---|
| qwen3-8b | 27 | 68 | 1 | 95/96 | 70.8% |
| nemotron | 48 | 47 | 1 | 95/96 | 49.0% |
| qwen38-27b | 47 | 48 | 1 | 95/96 | 50.0% |
| bonsai-27b | 34 | 61 | 1 | 95/96 | 63.5% |

**Pairwise pass sets**

| pair (A vs B) | both | A-only | B-only | neither | relation |
|---|---|---|---|---|---|
| qwen3-8b vs nemotron | 21 | 6 | 27 | 42 | complementary |
| qwen3-8b vs qwen38-27b | 17 | 10 | 30 | 39 | complementary |
| qwen3-8b vs bonsai-27b | 14 | 13 | 20 | 49 | complementary |
| qwen3-8b vs frontier | 27 | 0 | 68 | 1 | B dominates A |
| nemotron vs qwen38-27b | 29 | 19 | 18 | 30 | complementary |
| nemotron vs bonsai-27b | 28 | 20 | 6 | 42 | complementary |
| nemotron vs frontier | 48 | 0 | 47 | 1 | B dominates A |
| qwen38-27b vs bonsai-27b | 20 | 27 | 14 | 35 | complementary |
| qwen38-27b vs frontier | 47 | 0 | 48 | 1 | B dominates A |
| bonsai-27b vs frontier | 34 | 0 | 61 | 1 | B dominates A |

**Unique successes**

| arm | unique successes among locals | unique incl. frontier |
|---|---|---|
| qwen3-8b | 3 | 0 |
| nemotron | 6 | 0 |
| qwen38-27b | 13 | 0 |
| bonsai-27b | 3 | 0 |
| frontier | — | 23 |

**Tier coverage (cheapest-sufficient)**

| ordering (cheapest first → frontier) | first-pass by tier | covered / n |
|---|---|---|
| qwen3-8b,nemotron → frontier | frontier: 41, qwen3-8b: 27, nemotron: 27, unresolved: 1 | 95/96 |
| qwen3-8b,qwen38-27b → frontier | qwen38-27b: 30, frontier: 38, qwen3-8b: 27, unresolved: 1 | 95/96 |
| nemotron,qwen38-27b → frontier | qwen38-27b: 18, frontier: 29, nemotron: 48, unresolved: 1 | 95/96 |
| qwen38-27b,nemotron → frontier | qwen38-27b: 47, frontier: 29, nemotron: 19, unresolved: 1 | 95/96 |
| bonsai-27b,qwen38-27b → frontier | qwen38-27b: 27, frontier: 34, bonsai-27b: 34, unresolved: 1 | 95/96 |
| bonsai-27b,nemotron,qwen38-27b → frontier | qwen38-27b: 15, frontier: 26, bonsai-27b: 34, nemotron: 20, unresolved: 1 | 95/96 |
| qwen3-8b,bonsai-27b,qwen38-27b → frontier | qwen38-27b: 19, frontier: 29, bonsai-27b: 20, qwen3-8b: 27, unresolved: 1 | 95/96 |

**All-pass by class**

| class | qwen3-8b | nemotron | qwen38-27b | bonsai-27b | frontier |
|---|---|---|---|---|---|
| S01 | 0 | 0 | 7 | 1 | 8 |
| S02 | 4 | 7 | 3 | 7 | 8 |
| S03 | 2 | 6 | 7 | 0 | 8 |
| S04 | 1 | 4 | 8 | 3 | 8 |
| S05 | 7 | 6 | 6 | 6 | 8 |
| S06 | 0 | 3 | 2 | 1 | 8 |
| S07 | 3 | 0 | 0 | 0 | 8 |
| S08 | 4 | 8 | 7 | 7 | 8 |
| S09 | 6 | 7 | 7 | 2 | 8 |
| S10 | 0 | 5 | 0 | 4 | 8 |
| S11 | 0 | 2 | 0 | 3 | 8 |
| S12 | 0 | 0 | 0 | 0 | 7 |

**Pre-registered readings (contract § 11 materiality).** Qwen3.8-27B vs Nemotron: 47 vs 48/96 → **competitive** (within ±4), not "better"; pairwise 29 both / 19 Nemotron-only / 18 Qwen3.8-only / 30 neither → complementary. Qwen3.8 vs Qwen3-8B: 30 Qwen3.8-only vs 10 Qwen3-8B-only (paired difference +20, well above the +8 materiality bar). Bonsai on TEST: 34/96 — below Nemotron by 14 and Qwen3.8 by 13, above Qwen3-8B by 7 (pairwise vs Qwen3-8B 14 both / 13 / 20 / 49); no pre-registered materiality reading applied to the efficiency role beyond its DEV gate; it is complementary with every local arm (vs Qwen3.8: 20 both / 27 / 14 / 35; vs Nemotron 28 / 20 / 6 / 42). The frontier dominates every local arm (each local's pass set ⊂ frontier's, one `S12-3002011` case fails everywhere).

## 7. Unchanged R4, post-answer oracle, overlap, unique rescue, tier coverage, dominance

**R4 (verifier cascade, unchanged, replayed against the frozen frontier rows).** The gate escalates on no-output / verifier failure — exactly Qwen3.8's failure mode — so on TEST Qwen3.8 + R4 reaches **93/96** (FN 2, utilization 49.0 %, 0 unnecessary, $0.0628/success) against Nemotron + R4 69/96 (FN 26, util 21.9 %, $0.0380) and Qwen3-8B + R4 48/96 (FN 47). The price is frontier utilization (47 calls vs 21) and wall time (p50 268 s incl. escalations). The **post-answer oracle** (escalate exactly the local failures) is 95/96 for every arm; Qwen3.8's oracle gap is 2 cases — R4 is already the oracle for it, because its failures are visible. Bonsai + R4 reaches only 55/96 (FN 40, util 21.9 %): 41 of its 62 failures are verifier-clean wrong answers the gate cannot see — the efficiency tier inherits the historical silent-failure shape (29 evidence-only, 12 root cause) and adds 13 unsupported-claim verifier failures.

**Unique successes on TEST (among locals):** Qwen3.8 15 (S01 ×7, S04 ×4, S03, S06 ×2, S09 — the classes every earlier local scored 0–1 on), Nemotron 12 (S10 ×5, S06 ×3, S11 ×2, S02, S03), Qwen3-8B 3, Bonsai 3 (in the four-local set: Qwen3.8 13, Nemotron 6, Qwen3-8B 3, Bonsai 3 — Nemotron's unique set shrinks from 12 to 6 once Bonsai is in the set, Bonsai taking S10/S11 cases). **Dominance:** no local arm's pass set contains another's on either split; every pair is complementary; only the frontier dominates. Qwen3.8 does not *operationally* dominate Nemotron either (slower, more VRAM) — it wins on silent-failure burden and loses on latency.

**Tier coverage (cheapest-sufficient, descriptive, no router):** `qwen3-8b → nemotron → frontier` (the R5 structure) covers 27 + 27 locally and sends 41 to the frontier; `qwen38-27b → nemotron → frontier` covers 47 + 19 and sends 29; `nemotron → qwen38-27b → frontier` 48 + 18 → 29; `bonsai → qwen38-27b → frontier` 34 + 27 → 34; `bonsai → nemotron → qwen38-27b → frontier` 34 + 20 + 15 → 26 (the most local coverage, 69/96, at three resident models the card cannot hold together); one case (`S12-3002011`) is unresolved everywhere. These are descriptive first-pass orderings, not cascades — only the R4 gate's decisions are replayable, and it can see Qwen3.8's failures but not Nemotron's or Bonsai's.

**Is Nemotron still useful?** Yes, as a complement: it finishes the long-reasoning classes (S10, S11, S06) inside its budget where Qwen3.8 truncates, at a fifth of the latency; but it carries 27 silent failures that no deterministic gate sees. **Does Qwen3.8 simplify the stack?** Under the unchanged R4 gate it makes a learned silent-failure router unnecessary (FN 2); it does not remove the frontier (49 % utilization) and it raises latency.

## 8. Cheapest / lowest-burden oracle structure with the new candidates

With Qwen3.8-27B as the local tier, the oracle is the deterministic verifier gate itself: local answers that finish are almost always right (TEST: 47 pass of 49 finished); answers that do not finish are visibly no-output and escalate. 93/96 at 49 % frontier utilization, 0 unnecessary escalations, 2 false negatives (`S03-3000002`, `S11-3001010`, both evidence-only). A two-local tier (Qwen3.8 → Nemotron → frontier) would cover 47 + 19 = 66 locally in the descriptive ordering, but Nemotron's 27 TEST silent failures mean a real cascade could not route to it safely without a learned detector — which R5 showed does not generalise. The lowest-burden *sufficient* structure is therefore the single-local Qwen3.8 + R4 cascade; its burden is latency (265 s local p50) and VRAM (15.1 GiB), not routing complexity.

## 9. What silent failures remain

TEST silent (verifier-clean, wrong): Qwen3-8B 47 (33 evidence-only, 14 root cause), Nemotron 27 (16 / 11), **Qwen3.8 2 (2 evidence-only)**, Bonsai 41 (29 / 12). DEV: Qwen3-8B 16, Nemotron 13, Qwen3.5-9B 12 (9 evidence-only, 3 root cause), Qwen3.8 1, Bonsai 21 (14 / 7). The modern strong model reduces verifier-clean silent failures by more than an order of magnitude relative to both controls — by converting failure into visible truncation. The 9B and Bonsai tiers keep the historical evidence-citation failure shape (root cause right, citations thin).

## 10. Accounting — new inference and wall time

New local inference, counted from canonical storage (trajectories carrying an R6 `candidate_id`): **516 cases; 0 frontier calls** (no R6 trajectory used the frontier). By artifact and split — Qwen3.5-9B: TRAIN 48 (36 pilot + 12 probe), DEV 48; Qwen3.8 Q3_K_M: TRAIN 48, DEV 48, TEST 96; Qwen3.8 UD-Q3_K_XL: TRAIN 36; Bonsai: TRAIN 48, DEV 48, TEST 96 — plus one synthetic (non-corpus) Bonsai compatibility request. TRAIN 180 / DEV 144 / TEST 192. One run was interrupted and resumed in the same session (`R6-bonsai-train-stab`, 8 + 4; the ledger's end lines record 4, the DB holds 12).

Run wall (ledger end lines, h): Qwen3.5 pilot 0.72, probe 0.24, DEV 0.81; Qwen3.8 Q3_K_M pilot 2.58, probe 0.71, DEV 3.03, TEST 6.20; UD pilot 1.81; Bonsai pilot 0.81, probe 0.10 (+ the unrecorded 8-case first part), DEV 1.13, TEST 2.33 — **20.5 h of model time**. Wall by phase (`phases.jsonl`): R6.0 bootstrap ~1.1 h (before `/goal`); R6.1 provenance 21:00–21:36 UTC (0.6 h); R6.2 TRAIN 8.2 h; R6.3 freeze + reviews 0.3 h; R6.4 DEV 5.5 h; R6.5 TEST 9.3 h; R6.6–7 analysis, report, docs, final review ≈ 1.5 h — **≈ 25.4 h** from `/goal` to the final commit. Model time dominates; the Qwen3.8 arms (27B at 30 tok/s, ~8k tokens per case) account for 14.3 h of the 20.5.

## 11. Residual failure mechanisms of the strongest modern local, and the one next milestone

Qwen3.8-27B Q3_K_M's residual failures are almost entirely **reasoning-budget truncations** — 47 of 49 TEST failures and 22 of 23 DEV failures are `stop_reason=length` at 8192 tokens with no content emitted (28–34k reasoning characters), concentrated in S07, S10, S11, S12 (0/8 each on TEST) and S06/S02; the model's median completed answer is already ~8k tokens. When it finishes it is right (TEST 47/49, DEV 25/26). This is not an evidence-discipline gap, not a root-cause gap and not a schema gap — the behaviours QLoRA specialization was proposed to train — and it is not a routing gap (the failures are visible). It is a budget/latency gap: the cap set pre-registered for R6 stopped at the manifest ceiling (8192) and the contract forbids changing it after DEV.

**Does post-training remain justified?** Not for the strongest substrate on this evidence: Qwen3.8's behaviour when it completes is already at the frontier's level on the classes it finishes, and its dominant failure mode is a budget the harness imposes. Specialization might still be argued for the cheap tier (Qwen3.5-9B / Bonsai evidence citation), but those are quality-dominated by Qwen3.8 and the contract's gates rejected or merely floor-qualified them. **Favoured substrate if specialization is ever revisited:** Qwen3.8-27B Q3_K_M (`qwen3.8-27b-q3_k_m@7f3b845b5638` on `llama.cpp-upstream-9b05354@0e90f9139596`).

**Recommended next milestone (exactly one, not started):** **R7 — reasoning-budget calibration for the frozen Qwen3.8-27B execution system**: a pre-registered TRAIN-only study of caps beyond 8192 (e.g. 12288 at `-c 16384`, or a larger context) and, if the model's chat template supports it, a declared thinking-budget toggle — selected on TRAIN, frozen, then one DEV and one TEST under the same Suite v3, provenance registry and state machine, with the R4 replay and the latency/VRAM cost reported alongside. Its question is the one R6 leaves open: how much of the 49 % truncation converts to passes, at what wall time, and whether the UD-Q3_K_XL quant (39 % faster, frozen out by the quality-first rule at 8192) becomes the better operating point when the budget is no longer the binding constraint. No training, no router.

## A. Definition-of-done checklist

| # | criterion | status |
|---|---|---|
| 1 | Suite v3 scientific components frozen | ✔ asserted at start and end (§ 1) |
| 2 | Qwen3-8B official provenance backfilled exactly | ✔ `Qwen/Qwen3-8B-GGUF@6a569868`, SHA + bytes (§ 2) |
| 3 | both Qwen3.8 artifacts registered as Unsloth Qwen3.8 | ✔ (§ 2; "Bonsai" mislabels corrected) |
| 4 | Nemotron artifact/runtime reproducible | ✔ bartowski `be042bfc`, upstream runtime record, captured server args |
| 5 | Bonsai provenance/runtime requirement recorded | ✔ Prism `b1-9fcaed7`, Q2_0 geometry note |
| 6 | Qwen3.5-9B acquired from the pinned source, digest-verified | ✔ 21:05 UTC |
| 7 | every new trajectory carries artifact + runtime/config identity | ✔ 516/516 (runner refuses otherwise) |
| 8 | both Qwen3.8 quants compared on TRAIN only, exactly one advanced | ✔ 20 vs 16; UD withdrawn |
| 9 | generation/runtime calibration TRAIN-only and frozen before DEV | ✔ cap 8192 ×3, execution systems frozen at TRAIN_COMPATIBLE |
| 10 | contract + numeric gates committed before new DEV | ✔ `b2f85d5` (gates) / `b4e9095` (freeze) |
| 11 | independent Fable pre-DEV review passes | ✔ reviews A and B, follow-ups landed |
| 12 | each eligible candidate evaluated exactly once on DEV | ✔ three DEV runs, ledger + DB guarded |
| 13 | DEV qualification applied exactly as registered | ✔ verdicts by `evaluate_gates`, re-derived by the registry |
| 14 | TEST opened once, only for DEV-qualified | ✔ Qwen3.8, Bonsai; Qwen3.5 never opened |
| 15 | no post-TEST tuning/quant switch/prompt/cap change/rerun | ✔ (state machine terminal) |
| 16 | no new frontier calls | ✔ 0 |
| 17 | R4 and post-answer oracle computed for new candidates | ✔ § 7 |
| 18 | pairwise overlap, unique rescue, dominance complete | ✔ § 6–7 |
| 19 | answers whether Qwen3.5 improves the small tier | ✔ § 5.1 (quality yes; gate no) |
| 20 | answers whether Qwen3.8 dominates/complements/loses to Nemotron | ✔ complements (§ 7) |
| 21 | answers whether Bonsai is a useful efficiency point | ✔ § 5.3, § 6 (qualifies; largest silent burden) |
| 22 | residual failure mechanisms of the strongest modern local | ✔ § 11 |
| 23 | post-training justified? favoured substrate | ✔ § 11 (not now; Qwen3.8 Q3_K_M if ever) |
| 24 | new calls counted by split/artifact | ✔ § 10 |
| 25 | wall time by phase | ✔ § 10 |
| 26 | full tests pass | ✔ 627 passed + 1 skipped (see HANDOFF) |
| 27 | working tree clean | ✔ at the final commit |
| 28 | exactly one next milestone recommended, not started | ✔ § 11 |
