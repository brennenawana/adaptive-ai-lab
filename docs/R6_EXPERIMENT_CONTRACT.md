# R6 Experiment Contract — Modern Local Specialist Refresh

Pre-registration for R6 (`docs/FIS_R6_Modern_Local_Specialist_Refresh_Plan.html`). This
file is the binding record. Sections marked **[frozen at R6.3]** are completed by the
contract-freeze commit before any new-candidate DEV inference; every other section is
committed **before the first TRAIN pilot** so that no rule below can be shaped by a
candidate's numbers. Amendments are appended to § 17 with the commit that made them;
nothing above § 17 is rewritten after DEV starts.

Reading order: R6.0 reconciliation → this contract → `learning/registry/r6/` (the
cryptographic records this contract names) → `docs/R6_MODERN_LOCAL_SPECIALIST_REFRESH_REPORT.md`.

---

## 1. Question and scope

Primary causal question: **before changing weights, how much residual FIS failure
disappears when the local specialist is refreshed to modern operating points?**

In scope: cryptographic model/runtime provenance; one modern small-Qwen arm; TRAIN-only
selection between the two Qwen3.8-27B quants; DEV and conditional TEST for each eligible
candidate; Ternary Bonsai only if its Prism runtime preserves FIS semantics; offline R4,
post-answer oracle, pass-set overlap, unique-rescue, dominance and tier-coverage analysis;
runtime/footprint characterisation.

Out of scope (hard): any weight change (QLoRA/SFT/RL/distillation); a new learned router;
model-specific prompt tuning; any change to Suite v3 scenarios/gold/prompt/tools/evidence/
scorer/verifier; new frontier inference (absent a documented integrity exception); an
open-ended quant/model search; H0–H3 harness work.

## 2. Frozen scientific baseline (asserted at start and end of R6)

| Component | Identity | Check |
|---|---|---|
| Suite v3 corpus | `1e7c5278ba1f4cc1cc96fa8a1f04946ab622270eaba4c5671274c21e9d39e528` (train `d9d1570e6b70…1f2e` 144 · dev `5d5c94b049a9…ac34` 48 · test `8deea4a26c4b…c8ac` 96) | `scripts/corpus_digest.py --check scenarios/manifests/corpus_v3.json` |
| Release | tag `suite-v3` → `7764601f709de243e238fe4045552a06802eabbf` | `git rev-parse suite-v3^{commit}` |
| Scorer / verifier / ontology / prompt version | `3` / `3` / `1` / `1` | constants + `runtime_context` on every trajectory |
| Investigation prompt (weak arms) | `cause_action_directed`, sha256 `40111d53f60e0a373f1c1dd05542e708691334904efd90559b78261123ece51c` (2 553 chars) | `sha256(PROMPTS["cause_action_directed"])` |
| Frontier prompt | `baseline`, sha256 `456c19802be917dfd52553c8094786c1385d1cd66363f3a726a94388480b01f3` | — |
| Evidence plan | `FIXED_EVIDENCE`, `_phase_one`/`_phase_two(limit=6)` | tree hash of `services/` unchanged since `suite-v3` |
| Structured output | llama.cpp `response_format.json_schema` = `to_gbnf_safe(InvestigationResult.model_json_schema())`, strict | digest recorded in every R6 generation-config record |
| Decoding (local) | temperature 0.0, seed 42, `--parallel 1` | `fis_platform/model_gateway/local.py` unchanged |
| Frontier trajectories | `E4-v3-dev` (48/48) and `E4-v3-96` (95/96) in Postgres — reused offline only | no new frontier calls |
| Historical controls | `V3-qwen-dev` 17/48, `V3-qwen-96` 27/96 (Qwen3-8B, cap 4096) · `V3-nemotron-dev` 23/48, `V3-nemotron-96` 48/96 (Nemotron, cap 8192) · R4 replays 32/48, 48/96 · 35/48, 69/96 | replay only, never rerun |

Historical control identity is by **artifact SHA-256 backfilled into the registry** plus
`corpus_digest`; their trajectories predate the registry and are attributed by the served
`model_path` recorded in `runtime_context` (1,283 rows) — recorded as *attribution*, not as
cryptographic binding. R5's dirty-tree records are grandfathered: they are frozen inputs,
not R6 outputs. R6's TEST rows for the historical local arms are **already seen** by the R5
learned-routing looks; R6 uses them only as paired controls for new candidates.

## 3. Artifacts (SHA-256 is the identity anchor; the registry record is normative)

| Role | Artifact | Source (repo @ revision) | SHA-256 | Bytes |
|---|---|---|---|---|
| historical small control | `Qwen3-8B-Q4_K_M.gguf` | `Qwen/Qwen3-8B-GGUF` @ `6a569868d07d3bd59e8b97fb001bf8c0b254bb20` (base `Qwen/Qwen3-8B`, apache-2.0) | `d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785` | 5,027,783,488 |
| strong local control | `NVIDIA-Nemotron-3.5-Lightning-30B-A3B-IQ4_XS.gguf` | `bartowski/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF` @ `be042bfc3b0fbe10b78c9b91b7f1a9fe392f1062` (base `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16`, openmdw-1.1) | `c7be5d2ca9700a0e02de1a6707bbcdda3b38b7721caef7ac05bf9dda158aa270` | 18,918,361,056 |
| modern small | `Qwen3.5-9B-Q4_K_M.gguf` | `unsloth/Qwen3.5-9B-GGUF` @ `99a1b2185534379e6e8b5ec869da25d3e7b3f73c` (base `Qwen/Qwen3.5-9B`) | `03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8` | 5,680,522,464 |
| modern strong (quant A) | `Qwen3.8-27B-Q3_K_M.gguf` | `unsloth/Qwen3.8-27B-GGUF` @ `fa83dc3165d11f3cc617c41ba5fbfb22b2791ca8` (base `Qwen/Qwen3.8-27B`, apache-2.0) | `7f3b845b563888ec3abc269474cf744bf703a7ce8766dbb7f696c63975facfd7` | 13,818,690,528 |
| modern strong (quant B) | `Qwen3.8-27B-UD-Q3_K_XL.gguf` | `unsloth/Qwen3.8-27B-GGUF` @ `1cff334a4a228324d4ee1f76d55d372588f0d556` (base `Qwen/Qwen3.8-27B`, apache-2.0) | `00cf92e666c6af6566996c38c89a44ccdb6449ea25ef0f112a452c853b2a71e2` | 13,441,059,904 |
| efficiency | `Ternary-Bonsai-27B-Q2_0.gguf` | `prism-ml/Ternary-Bonsai-27B-gguf` @ `abbae723028d71be674e71e1a71201a6f43fab22` (base `Qwen/Qwen3.6-27B` per plan; not verifiable from the file) | `868c11714cf8fe47f5ec9eeb2be0ab1a337112886f92ee0ede6b855c4fa31757` | 7,165,121,600 |

All six digests were recomputed from local bytes on 2026-08-18 and every (repo, revision,
file) triple resolves upstream to the same LFS digest. The Nemotron file was re-uploaded
upstream (an earlier 18,166,697,920-byte version at `d549c0b5` was replaced) — the pin is
the file-upload commit, not `main`. The two `Qwen3.8-27B-*` files are **Unsloth Qwen3.8**
artifacts; they are not Bonsai. `Ternary-Bonsai-27B-Q2_0.gguf` is the Prism artifact.
GGUF metadata digests (`gguf_metadata_digest_v1`, `fis_platform/provenance.py`) are in
`learning/registry/r6/models/*.json`.

Registry identities (R6.1, `learning/registry/r6/`): artifacts `qwen3-8b-q4_k_m@d98cdcbd03e1`
(gguf md `a0f5e4c4…`), `nemotron-3.5-lightning-30b-a3b-iq4_xs@c7be5d2ca970` (`41423697…`),
`qwen3.5-9b-q4_k_m@03b74727a860` (`80e78173…`), `qwen3.8-27b-q3_k_m@7f3b845b5638` (`5697d81f…`),
`qwen3.8-27b-ud-q3_k_xl@00cf92e666c6` (`9eafa178…`), `ternary-bonsai-27b-q2_0@868c11714cf8`
(`50ee7e09…`); candidates `qwen35-9b@9f010021daba`, `qwen38-27b-q3km@8528f049af75`,
`qwen38-27b-udq3kxl@d9d3f9771d67`, `bonsai-27b@ddd13c20e0e8`; generation configs
(`cause_action_directed`, temp 0.0, seed 42, strict json_schema `07f92914…`) `gc@265b30b4efb4`
(4096), `gc@9dc828f0e36e` (6144), `gc@5d1e73fdadd7` (8192). Historical control execution
systems: `learning/registry/r6/historical_controls.json` (server args captured from `/proc`
of the still-resident 8082/8083 sessions before they were stopped).

## 4. Runtimes (execution-system identity)

| Runtime | Identity | Used for |
|---|---|---|
| `llama.cpp-upstream` — `llama.cpp-upstream-9b05354@0e90f9139596` | ggml-org/llama.cpp `9b05354ec6fb58b4e665e9a39ebc40285c015638`, local untagged CUDA build (`build_info b1-9b05354`, sm_120a, cudart 12.8.90 / nvcc 12.8.93), binary-set digest `0e90f913…`, runtime digest `2612296d…` | all historical arms; Qwen3.5-9B; Qwen3.8-27B |
| `llama.cpp-prism` — `llama.cpp-prism-9fcaed7@4f0400389699` | PrismML-Eng/llama.cpp `9fcaed763ccda38ea81068ad9d7f991aaddca451` (`prism-b9596-9fcaed7`, tree dirty only in `tools/ui/package-lock.json`), CUDA build, same CUDA 12.8.93 toolchain, binary-set digest `4f040038…`, runtime digest `6fbf2251…` | Ternary Bonsai only |

Why two runtimes: upstream and Prism both define `GGML_TYPE_Q2_0 = 42`, but with
`QK2_0 = 64` (upstream) vs `128` (Prism) — the same type id with a different on-disk block
geometry. The Bonsai file is Prism-geometry; it must never be served by the upstream binary
and no Bonsai trajectory produced by the upstream binary may enter canonical storage. The
runtime digest is the only discriminator (file metadata cannot tell the two apart), which
is why `runtime_id`/`runtime_digest` are mandatory on every R6 trajectory.

Material runtime settings (part of `server_args_digest`/runtime record): binary and
`lib*.so*` hashes, `LD_LIBRARY_PATH` content (resolved CUDA libs are hashed), `-c`,
offload (`-ngl N` explicit — `--fit` is used only as a probe to find N and never in a
frozen system), `--flash-attn on`, `--cache-type-k/v q8_0`, `--jinja`, `--parallel 1`,
CUDA arch/toolkit/driver, GPU. Informational: host, port, alias, paths.

## 5. Split protocol

| Split | Allowed use in R6 |
|---|---|
| TRAIN (144) | compatibility, cap calibration, Qwen3.8 quant selection, Bonsai viability, stability probe, resource capture. No weight training. |
| DEV (48) | exactly one evaluation per frozen candidate execution system, only after the R6.3 freeze commit; used only to apply § 11. |
| TEST (96) | exactly once per DEV-qualified candidate; no tuning, no rerun, no quant switch afterwards. |

**Pre-registered TRAIN pilot** (`r6-train-pilot-v1`, `scripts/r6_pilot.py --k 3`): the first
3 scenario ids of every class in ascending scenario-id (= seed) order — 36 cases,
`pilot_digest = fde034b054809a026e2632710df21a2b1149692501faa4bae635e4787b275b71`,
id list committed at `learning/registry/r6/pilot/train_pilot_k3.json`. Every TRAIN pilot
below runs exactly this list under `run_eval --scenario-ids-file`.

New inference is counted per (artifact, split, run id) in `learning/registry/r6/ledger.jsonl`;
wall time per phase in `learning/registry/r6/phases.jsonl`.

## 6. Generation cap calibration (TRAIN only, deterministic)

Allowed cap set: `{4096, 6144, 8192}` (8192 = the manifest ceiling; every candidate is
served with context ≥ 12 288 so 8192 + the ~3.6k-token prompt always fits).

Rule: run the pilot **once at cap 8192** (greedy, seed 42 — the completion at a smaller cap
is a prefix of this one, so the run at the ceiling decides every smaller cap). For each cap
`c`, `capped(c)` = number of pilot cases with `output_tokens ≥ c` or `stop_reason ==
"length"`. Tolerance: `capped(c) ≤ 3` of 36 (≤ 8.3 %). Freeze the **smallest** allowed cap
meeting the tolerance; if none does, freeze 8192 and record the truncation rate. The cap is
part of the generation-config digest and cannot change after DEV begins.

## 7. Qwen3.8-27B quant selection (TRAIN only; exactly one quant reaches DEV)

Both quants are served on the same runtime with **identical** server args (same `-c`, same
explicit `-ngl N` — N is found once with a `--fit on` probe on the larger file, Q3_K_M, and
then applied to both), run on the pilot at cap 8192, and compared **before** cap selection:

1. strict all-pass count on the 36 pilot cases — higher wins;
2. tie → fewer no-output cases (`stop_reason == "length"` with no parsable answer, plus
   schema/parse failures);
3. tie → fewer cases with `output_tokens ≥ 8192` (cap hits);
4. tie → lower p50 wall latency;
5. tie → smaller artifact (UD-Q3_K_XL).

The loser is `WITHDRAWN` in the registry with reason `quant-selection-loser` and never
reaches DEV. Latency/resource burden is a tie-break only (rule 4).

## 8. Ternary Bonsai eligibility (TRAIN only)

Bonsai proceeds to DEV only if, on the Prism runtime: (a) `/props` reports the model and the
server answers `/chat/completions` with `response_format.json_schema`; (b) the pilot at cap
8192 produces a schema-valid `InvestigationResult` on ≥ 30 of 36 cases (≤ 6 no-output —
the tolerance is Nemotron's DEV no-output rate 12/48); (c) `timings`, `system_fingerprint`
and `reasoning_content` are present in responses (so `api_ms`, runtime fingerprint and
`reasoning_chars` are comparable); (d) resource capture (resident GPU memory) works. If any
of (a)–(d) fails, the report states **BONSAI NOT RUN — RUNTIME INCOMPATIBLE FOR R6** and the
candidate is `WITHDRAWN`. No FIS semantics (task, tools, evidence, scorer, verifier) may be
changed to make Bonsai fit; a thin serve/runtime adapter is the only allowed integration.

## 9. Stability probe (TRAIN only, informational)

For each candidate that reaches `TRAIN_COMPATIBLE`, the first pilot case of every class
(12 cases) is rerun once in the same server session under the frozen execution system; the
fraction of identical `output_digest` and identical `all_pass` is reported. No gate.

## 10. Server configuration per candidate **[frozen at R6.3]**

Recorded as `execution_system_digest` in each candidate's `TRAIN_COMPATIBLE` entry
(`learning/registry/r6/candidates/<id>/state.jsonl`): `-c`, `-ngl N`, cap, generation-config
digest, server-args digest, runtime digest, artifact SHA. The freeze commit lists them in
§ 17.

## 11. DEV qualification gates (numeric; fixed here from historical DEV metrics only)

Historical DEV (n = 48): Qwen3-8B all-pass **17**, no-output 1, p50 wall **12,864 ms**;
Nemotron all-pass **23**, no-output 12 (10 `length` + 2 schema), p50 wall **53,840.5 ms**;
frontier 48/48 (p50 37,165 ms). "No-output" = a case with no parsable `InvestigationResult` (cap hit or
schema/parse failure). "p50 wall" = `statistics.median` of `wall_ms` over the 48 DEV cases (mean of the two middle values).

| Candidate | DEV_QUALIFIED iff |
|---|---|
| **Modern small — Qwen3.5-9B** | strict all-pass ≥ **22/48** (≥ +5 over Qwen3-8B; the R5 restart probe moved 23 case outcomes but net 0 all-pass, so +5 net is above session noise) **AND** no-output ≤ **8/48** **AND** p50 wall ≤ **38,592 ms** (3 × Qwen3-8B, i.e. still faster than Nemotron) |
| **Modern strong — Qwen3.8-27B (selected quant)** | strict all-pass ≥ **23/48** (≥ Nemotron) **OR** [ all-pass ≥ **21/48** (within 2 cases of Nemotron) **AND** ( p50 wall ≤ **40,380 ms** (≤ 0.75 × Nemotron) **OR** no-output ≤ **6/48** (≤ ½ Nemotron's) ) ] |
| **Efficiency — Ternary Bonsai** | strict all-pass ≥ **20/48** (quality floor: ≥ Qwen3-8B + 3) **AND** resident GPU memory while served alone (`nvidia-smi memory.used`, same ctx, measured before/after the DEV run) ≤ **0.65 ×** the Qwen3.8 selected quant's **AND** p50 wall ≤ **1.25 ×** the Qwen3.8 selected quant's DEV p50 |

`DEV_REJECTED` otherwise. Gates are applied exactly as written; no post-hoc scalar. If the
Qwen3.8 candidate is `WITHDRAWN`/`DEV_REJECTED`, the Bonsai efficiency comparison uses the
Qwen3.8 candidate's DEV numbers if they exist, else Nemotron's DEV numbers (resident GPU
memory measured for Nemotron under `--fit on --fit-target 1024` = the historical serving
mode; p50 53,840.5 ms).

Materiality thresholds for interpretation (not gates): "material" small-tier improvement
= ≥ +5 all-pass on DEV and, on TEST, candidate-only − control-only ≥ **8** paired cases vs
`V3-qwen-96` (all-pass ≥ 35/96); "better than Nemotron" on TEST = all-pass ≥ Nemotron + 5
(≥ 53/96); "competitive" = within ±4; "worse" = ≤ 43/96. Dominance is never claimed from
average score alone — the pairwise A/B/C/D and unique-success tables decide.

## 12. TEST protocol

TEST opens once per DEV-qualified candidate, bound (in the `TEST_UNLOCKED` entry) to the
artifact SHA re-hashed at unlock time, the runtime digest, the generation-config digest,
the execution-system digest, the DEV result digest and the contract revision (git blob sha
of this file at the freeze commit). TEST run id: `R6-<slug>-test`. After `TEST_EVALUATED`
nothing about that candidate may change; a rerun, prompt/cap change or quant switch is
refused by the state machine and would in any case be reported as a violation.

## 13. State machine (implemented in `fis_platform/provenance.py`)

`REGISTERED → TRAIN_COMPATIBLE → CONTRACT_FROZEN → DEV_EVALUATED → {DEV_QUALIFIED |
DEV_REJECTED} → TEST_UNLOCKED → TEST_EVALUATED`; `WITHDRAWN` only from `REGISTERED` /
`TRAIN_COMPATIBLE`. Guarantees: at most one candidate of family `qwen3.8-27b` at or beyond
`DEV_EVALUATED`; one DEV run per candidate (ledger-enforced in `run_eval`, resume of the
same run id only); TEST requires state `TEST_UNLOCKED` and the unlock's run id; rejected/
withdrawn candidates have no edge to TEST; every entry is hash-chained and `HEAD.json`
anchors the tip; no environment variable or flag relocates the registry root; adversarial
destructive tests use `tmp_path` registries only. `run_eval --candidate` refuses to make a
single model call unless `require_state` passes and the served `/props` build, model file
SHA and `/proc` server args match the frozen execution system.

## 14. Integrity controls

- Suite v3 digests asserted at R6 start (R6.0) and end (report § A).
- Committed code tree for every DEV/TEST run: every modified tracked path must lie under `learning/registry/r6/` — the registry's own append-only records (run ledger, phase markers, state logs, once-written result files) are necessarily ahead of HEAD at the moment a guarded run starts, and are committed right after. Allowed dirty paths outside the registry: **none** (`fis_platform/provenance.tree_state`, refused by `run_eval` and by every state transition). TRAIN pilots follow the same rule; each run's `git_head` and `code_tree_clean_except_registry` are recorded on its trajectories.
- No new frontier calls. Historical Qwen/Nemotron/frontier arms are replayed, never rerun.
- No `evals/reports` glob deletion; DEV/TEST result files are written once into the registry.
- Only one candidate server resident at a time; the historical `:8082`/`:8083` servers are stopped at the start of R6.2 (their sessions are recorded in the R6.0 report; the controls are replay-only).
- Every new trajectory carries `candidate_id, artifact_id, artifact_sha256, runtime_id, runtime_digest, execution_system_digest, generation_config_digest, server_args_digest` in `runtime_context`.

## 15. Analysis plan (offline, after TEST)

For each new candidate with DEV/TEST rows: local-only quality (all-pass, root cause, action,
evidence recall ≥ 0.8, verifier); failure shape (root-cause / evidence / combined / schema /
cap / verifier-clean silent); unchanged R4 verifier cascade replay against `E4-v3-*`
(`scripts/routing_cascade_report.py --weak <run> --strong E4-v3-<split> --policy verifier`);
post-answer ideal oracle and oracle gap; pairwise A/B/C/D and unique successes vs every
other arm (`scripts/model_migration_matrix.py`); descriptive tier orderings (historical
small → modern small → modern strong → frontier; modern small → modern strong → frontier;
modern small → Bonsai → modern strong → frontier; modern small → {Nemotron, Qwen3.8} →
frontier) computed as cheapest-sufficient coverage; latency p50/p95, output tokens, cap hits,
artifact bytes, resident GPU memory. All from Postgres by run id.

## 16. Roles

Main Fable owns contract interpretation, provenance acceptance, quant/candidate eligibility,
DEV gates, TEST unlock, dominance interpretation, the next-step recommendation. Opus
subagents: inspection, implementation, tests, metric recomputation, report consistency.
Fable subagents: pre-DEV provenance/state audit, pre-DEV contract/gate review, final
challenge of the conclusions. No subagent decides TEST unlock.

## 17. Amendment log

| When (commit) | Section | Change |
|---|---|---|
| `b2f85d5` | all | initial pre-registration, before any TRAIN pilot |
| (this commit) | § 14 | cleanliness rule made precise: the registry's own tracked append-only files may be ahead of HEAD (they are written by the guarded run itself); nothing else may |
