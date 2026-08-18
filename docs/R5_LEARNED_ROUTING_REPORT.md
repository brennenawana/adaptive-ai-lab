# R5 — Learned Silent-Failure Routing: Report

Milestone R5 of the Fintech Integration Sandbox. Governing plan
`docs/FIS_R5_Learned_Silent_Failure_Routing_Plan.html`; pre-registered contract
`docs/R5_EXPERIMENT_CONTRACT.md` (skeleton `e3b8066`, amendments `76a7ec1`, `4b10da0`,
`6766e86` — all before the corresponding DEV replay); live log `OVERNIGHT_STATUS.md`
§ Milestone 6. Suite v3, the models, prompts, budgets, evidence plan, scorer, verifier and
the R4 gate are unchanged; R5 added a routing policy, its offline replay, and the
telemetry to learn from.

**One-paragraph result.** Production-observable trajectory + answer features can raise
the cascade well above the deterministic R4 gate on this benchmark — Qwen 50.0 % → 78.1 %
strict all-pass on TEST (routing FN 47 → 20) at 57 % frontier utilization; Nemotron
71.9 % → 77.1 % (FN 26 → 21) at 33 % utilization, which did *not* meet the pre-registered TEST reading — but the signal they carry is *template difficulty*: labels are
class-clustered (P(unsafe | class) 0.09–1.0; the minority label has n ≤ 1 in 8 of 11 classes),
four production-observable case constants identify the scenario class for 45/48 DEV cases,
the best learned router sits within 0.01 AUC of the class-identity ceiling on TRAIN, and
nothing transfers to a held-out template (per-fold LOGO AUC 0.00–0.88, mean 0.39). No
within-template signal was detected beyond the S02 said-label — and TRAIN's label structure
gives R5 little power to find a small one. Under the plan's primary (leave-one-class-out)
protocol no candidate passed the TRAIN gate; **under the skeleton alone R5 is a null
result**. Two amendments made after TRAIN CV and before DEV — the secondary,
deployment-matched protocol and, for it, the removal of the a-priori utilization caps —
were each necessary for any selection; they were TRAIN- and audit-motivated, and they moved
in the direction of permitting a pass. Under them, the contract's tie-break ("fewer frontier
calls" — one of two readings of the plan's "fewer unnecessary escalations/frontier calls";
the other would have frozen `lr_full`) picked the *least-escalating* survivor for Qwen, a
depth-3 tree below the class ceiling on DEV; it was replayed on TEST exactly once and met
the pre-registered TEST reading — a reading a random escalator of the same size also meets
with p ≈ 0.6, so it certifies non-degeneracy, not information.

---

## 1. R5 identity

| field | value |
|---|---|
| Suite v3 | tag `suite-v3` = `7764601`; corpus `1e7c5278…9d39e528`; scorer 3 / verifier 3 / ontology 1 / prompt 1; `git diff suite-v3 -- . ':!docs'` empty at R5 start (`47723b2`) |
| R5 commits | `fc1c18e` plan + acquisition tooling · `e3b8066` contract skeleton · `ab1d7ab` reconciliation · `54c6fa9` feature/learner/replay/oracle tooling · `eda2e56` release-report erratum · `76a7ec1` Qwen TRAIN + § 12a-Q · `4b10da0` audit-driven amendment + state machine · `57f1a9d` artifacts · `503b042` Qwen DEV selection · `b1e92e9` pre-TEST follow-ups · `dbf5414` Qwen TEST · `6766e86`/`b078d4c` § 12a-Q reconciliation · `3e04dc7` Nemotron TRAIN + § 12a-N · `af199a5` Nemotron DEV selection · `5d277f6` Nemotron TEST · final docs commit(s) listed in `OVERNIGHT_STATUS.md` § M6.9 |
| source runs | TRAIN `R5-qwen-train`, `R5-nemotron-train` (acquired for R5); DEV `V3-qwen-dev`, `V3-nemotron-dev`, `E4-v3-dev`; TEST `V3-qwen-96`, `V3-nemotron-96`, `E4-v3-96` (all frozen Suite v3) |
| new model inference | **288 local calls, 0 frontier calls, 0 TEST calls**: Qwen 144 + Nemotron 144 TRAIN cases under the frozen operating configuration (`make eval-r5-train`); DEV/TEST answered entirely by offline replay |
| feature schema | `RoutingFeatureSnapshot` v1, 58 names (`fis_platform/routing/features.py`) |
| frozen policies | Qwen `r5-qwen-tree-stratified-v1` (digest `aa13e045bb95d412…`, τ 0.70) · Nemotron `r5-nemotron-lr_core-stratified-v1` (digest in `learning/registry/r5/frozen/nemotron.selection.json`, τ 0.50) |

## 2. Dataset and splits

| split | n | Qwen safe / R4-accepted / silent | Nemotron safe / R4-accepted / silent | dataset digest |
|---|---|---|---|---|
| TRAIN | 144 (12 × 12) | 41 / 105 / 64 | 66 / 104 / 38 | Qwen `d4d3c09d…`, Nemotron `fdb015a8…` |
| DEV | 48 (12 × 4) | 17 / 33 / 16 | 23 / 36 / 13 | Qwen `a4c777d4…`, Nemotron `93373f00…` |
| TEST | 96 (12 × 8) | 27 / 74 / 47 | 48 / 75 / 26 | opened once per frozen policy (§ 9) |

- **Grouping.** Seeds are `lo + i·1000 + class_idx` — independent draws per class, so the
  only template relation is the class. Group key = class; primary CV = leave-one-class-out
  (12 folds); secondary CV = seed-stratified 4-fold. The group key is an offline column,
  never a feature.
- **Answer bodies.** The frozen Suite v3 arms kept only the answer's sha256, so the
  answer's `root_cause.label` / `recommended_next_action` are rebuilt from the scorer's
  verbatim `said …` echo; migration 007 persists the parsed body from R5's TRAIN
  acquisition on, and the echo equals the body on 117/117 Qwen and 114/114 Nemotron
  TRAIN cases. Everything else about the answer (facts, cited ids, hypotheses,
  confidence) is unrecoverable for DEV/TEST and appears only in the TRAIN-only
  exploratory `answer_structure` comparator.
- **TEST access.** Sealed for every R5 script until `r5_replay.py --unlock-test`; the
  unlock is append-only, one per local model, bound to the recorded DEV winner and its
  lineage (`learning/registry/r5/test_unlock.json`, `tests/test_r5_state_machine.py`).

## 3. Feature contract and leak evidence

`FEATURE_ORDER` (58): **A** model/runtime 11 (`produced_output`, `stop_length`,
`input_tokens`, `output_tokens`, `reasoning_chars`, `content_chars`, `reasoning_share`,
`output_per_input`, `budget_used`, `wall_ms`, `api_ms`) · **B** verifier 16 (`verifier_passed`,
`schema_valid`, `checks_evaluated`, 7 `check_*` booleans, `n_violations`,
`n_unsupported_claims`, `n_fabricated_ids`, `n_uncalled_services`, `schema_error_count`,
`no_output_error`) · **C** tool trajectory 8 (`n_tool_calls`, `n_tool_success`,
`n_tool_errors`, `n_unique_tools`, `n_webhook_history_calls`, `n_verification_calls`,
`n_repeated_calls`, `tool_latency_ms_total`) · **D** answer echo 23 (`answer_present`, 13
`said_label_*`, 9 `said_action_*`). Forbidden: `GOLD_FEATURE_NAMES` ∪ {`strict_all_pass`,
`all_pass`, `score`, `scorer`, `frontier`, `strong`, `split`, `category`, `class`, `seed`,
`scenario_id`, `expected_*`, `gold`, `manifest`, `evidence_recall`, `truth`}; the case
`category` is excluded (a class identifier for four of eight categories).

Leak evidence: 43 tests in `tests/test_routing_features_no_gold_leak.py` (forbidden and
unlisted names are schema errors; extraction with no gold fields; gold-removal invariance
incl. `router`, `failure_class`, `human_feedback`, `business_outcome`, `was_useful`;
no name mentions scenario/class/seed/split; signature `(trajectory, answer)` only;
determinism; schema version; production `InvestigationResult` == scorer echo; import ban
extended to `fis_platform/routing/`), 64 pipeline tests (`answer_from_echo` never captures
the truth; `build_rows` invariance to perturbed truth/all_pass/category/split), snapshot
identical for the two identical-outcome Qwen DEV runs (48/48 non-latency features), and a
five-lens adversarial audit before DEV. **What the audit refuted:** the plan's promise that
the class cannot enter *indirectly*. Under FIXED_EVIDENCE `n_tool_calls`,
`n_webhook_history_calls`, `n_verification_calls` and `input_tokens` are case constants that
identify the scenario class for 45/48 DEV cases (leave-one-out 1-NN); every behaviour
feature also clusters by template. This is production-observable and cannot be removed
from a 12-template benchmark without removing legitimate bundle-size signal, so R5 is
read as an **in-template** experiment; DEV gains are reported net of the class-identity
ceiling (§ 7), the TEST gain is compared to a post-hoc class-prior counterfactual (§ 9). Effective inputs on the R4-accepted subset: family B is
constant by construction; ≈ 9 behaviour numbers, 4 template constants and the D one-hots
carry everything.

Timing features are session-conditioned (Nemotron restarted for TRAIN, probe 78 tok/s vs
88 in Suite v3); the selected policies do not split on them (§ 7). Diagnostics promised in
contract § 12a are in `learning/registry/r5/reports/diagnostics_<model>.json`
(`scripts/r5_diagnostics.py`).

## 4. Oracle ceilings (`scripts/r5_oracles.py`)

**Post-answer oracle (DEV, n = 48).**

| arm | local-safe | rescueable | unresolved | oracle all-pass | min-useful utilization | R4 utilization | oracle $/attempt | wall p50 |
|---|---|---|---|---|---|---|---|---|
| Qwen | 17 (35.4 %) | 31 (64.6 %) | 0 | 48/48 | 64.6 % | 31.2 % | $0.0788 | 42.6 s |
| Nemotron | 23 (47.9 %) | 25 (52.1 %) | 0 | 48/48 | 52.1 % | 25.0 % | $0.0635 | 72.3 s |

TEST (opened at the unlock): Qwen local-safe 27, rescueable 68, unresolved 1 (S12-3002011,
the frontier's one miss), oracle 95/96 at 70.8 %; Nemotron local-safe 48, rescueable 47, unresolved 1 (the same S12-3002011), oracle 95/96 at 49.0 % (R4 21.9 %).

**Three-tier cheapest-sufficient oracle (descriptive, for R6).** DEV: Qwen sufficient 17
(35.4 %), Nemotron sufficient 10 (20.8 %: S10 ×3, S03/S06/S08 ×2, S02), frontier required 21
(43.8 %), unresolved 0; sufficient-tier cost $0.0542/attempt. TEST: Qwen sufficient 27 (28.1 %), Nemotron sufficient 27 (28.1 %: S03 ×5, S10 ×5, S08 ×4, S02/S04/S06 ×3, S11 ×2, S05/S09), frontier required 41 (42.7 %), unresolved 1 (S12-3002011); sufficient-tier cost $0.0503/attempt, cascade reading $0.0514.
TRAIN (no frontier run): Qwen sufficient 41 (28.5 %), Nemotron sufficient 33 (22.9 %: S03 ×7, S02/S10 ×6, S04 ×4, S08 ×3, S05/S06/S09 ×2, S11), neither local 70 (48.6 %); the Nemotron-sufficient band is not template-clean on any split (S03/S06/S10 mix all three tiers).

## 5. R4 reproduction

`r5_oracles.py --split dev` reproduces `SUITE_V3_RELEASE_REPORT.md` § 4/§ 6 on all 23
gated fields (Qwen 32/48, 15 calls, 15/15, 0, FN 16, $0.0405/$0.0608, 16.7 s; Nemotron
35/48, 12, 12/12, 0, FN 13, $0.0330/$0.0453, 54.7 s; strong-only 48/48, $0.1160) —
AGREES; `r5_replay.py` reproduces the same R4 rows on DEV and TEST (TEST: 48/96, 22
calls, FN 47, $0.0513; Nemotron 69/96, 21 calls, FN 26, $0.0380; strong-only 95/96, $0.1139/success — one transcription error in the script's expected table (strong-only TEST cost/attempt, which the release report does not state) corrected in place). One erratum recorded (release report § 11): the
Qwen DEV FN prose split is 7 root_cause / 9 evidence_only under the exclusive bucketing.

## 6. TRAIN development (TRAIN only; `learning/registry/r5/train_report_*.json`)

**Qwen** (`R5-qwen-train`, R4-accepted 105, unsafe 64 = 0.61):

| candidate | protocol | hp | grouped OOF AUC / AP | stratified OOF AUC / AP / Brier | τ* | OOF at τ*: esc / catches / unnecessary (of 105) | gate |
|---|---|---|---|---|---|---|---|
| `lr_full` | primary | λ 100 | **0.238** / 0.460 | 0.898 / 0.913 | 0.40 | 105 / 64 / 41 | FAIL |
| `lr_core` | primary | λ 100 | **0.253** / 0.464 | 0.749 / 0.805 | 0.45 | 101 / 62 / 39 | FAIL |
| `tree` | primary | d 3 | **0.515** / 0.604 | 0.822 / 0.851 | 0.35 | 90 / 57 / 33 | FAIL |
| `lr_full` | secondary | λ 10 | 0.293 / 0.490 | **0.901** / 0.906 / 0.106 | 0.60 | 62 / 57 / 5 | PASS |
| `lr_core` | secondary | λ 1 | 0.362 / 0.512 | **0.821** / 0.872 / 0.170 | 0.60 | 62 / 51 / 11 | PASS |
| `tree` | secondary | d 3 | 0.515 / 0.604 | **0.822** / 0.851 / 0.160 | 0.70 | 57 / 49 / 8 | PASS |
| `prior_class_ceiling` (expl.) | secondary | λ 1 | 0.083 | 0.892 / 0.907 / 0.111 | 0.60 | 61 / 55 / 6 | — |
| `prior_category` (expl.) | secondary | λ 1 | 0.609 | 0.884 / 0.897 | 0.60 | 58 / 52 / 6 | — |
| `lr_answer` (expl.) | secondary | λ 1 | 0.419 | 0.904 / 0.902 | 0.70 | 60 / 56 / 4 | — |
| `lr_behavior` (expl.) | secondary | λ 1 | 0.416 | 0.909 / 0.920 | 0.55 | 62 / 57 / 5 | — |
| `answer_structure` (TRAIN bodies) | secondary | λ 10 | 0.223 | 0.873 / 0.858 | 0.50 | 66 / 59 / 7 | — |
| `answer_structure_only` | secondary | λ 10 | 0.265 | 0.685 / 0.767 | 0.60 | 58 / 44 / 14 | — |

Reading (unsafe/accepted per class): S03 11/12, S05 1/11, S08 1/10, S09 1/11, S10 11/12,
S12 12/12, S04 3/3, S11 6/6 — nine of eleven classes are ≥ 80 % one label; only S02 (6
unsafe / 6 safe, perfectly separated by the said label `duplicate_webhook_handled` vs
`missing_idempotency`), S06 (8/2) and S07 (4/2) mix. Pooled LOGO AUC is therefore dominated
by fold base-rate shift and is *not* evidence about transfer; the pre-registered
diagnostic is the per-fold LOGO AUC on mixed held-out classes: `lr_full` (λ 10) S02 0.00,
S03 0.09, S05 0.60, S06 0.50, S07 0.88, S08 0.56, S09 0.50, S10 0.00 (mean 0.39), and mean
predicted risk on the all-unsafe held-out S11 = 0.31 — nothing transfers to an unseen
template, not even generic hardness. Stratified AUC ≈ class-identity ceiling (0.892).
Within-class pooled AUC per feature (pairs inside a class only, 111 pairs): the S02
said-label pair 0.66/0.34, `input_tokens` 0.64, `content_chars` 0.39, all others within
0.06 of 0.5. The primary-protocol candidates' τ* sits at the grid floor (escalating
everything accepted has positive utility at 61 % unsafe), exactly the degeneration the
contract's E_max rejects. Full answer bodies (TRAIN only) add nothing over the snapshot
(0.873 vs 0.901; the class prior dominates both, so "nothing in the answer counts" is
untested rather than refuted). Coefficient signs are stable across folds (≥ 0.9 agreement
for the top 12); the tree's root split is `output_per_input` in 9/12 grouped folds.

**Nemotron** (`R5-nemotron-train`, R4-accepted 104, unsafe 38 = 0.365):

| candidate | protocol | hp | grouped OOF AUC / AP | stratified OOF AUC / AP / Brier | τ* | OOF at τ*: esc / catches / unnecessary (of 104) | gate |
|---|---|---|---|---|---|---|---|
| `lr_full` | primary | λ 100 | **0.201** / 0.248 | 0.863 / 0.767 | 0.80 | 0 / 0 / 0 | FAIL |
| `lr_core` | primary | λ 100 | **0.244** / 0.257 | 0.657 / 0.569 | 0.80 | 0 / 0 / 0 | FAIL |
| `tree` | primary | d 2 | **0.224** / 0.265 | 0.735 / 0.630 | 0.80 | 33 / 5 / 28 | FAIL |
| `lr_full` | secondary | λ 1 | 0.321 / 0.278 | **0.919** / 0.876 / 0.102 | 0.55 | 37 / 31 / 6 | PASS |
| `lr_core` | secondary | λ 10 | 0.331 / 0.281 | **0.656** / 0.591 / 0.212 | 0.50 | 18 / 15 / 3 | PASS (AUC 0.656 ≥ 0.60; AP 0.591 ≥ 0.465) |
| `tree` | secondary | d 3 | 0.279 / 0.276 | **0.849** / 0.731 / 0.137 | 0.50 | 45 / 32 / 13 | PASS |
| `prior_class_ceiling` (expl.) | secondary | λ 1 | 0.056 | **0.936** / 0.891 / 0.096 | 0.55 | 41 / 33 / 8 | — |
| `prior_category` (expl.) | secondary | λ 1 | 0.440 | 0.859 / 0.739 | 0.60 | 31 / 23 / 8 | — |
| `lr_answer` (expl.) | secondary | λ 1 | 0.300 | 0.860 / 0.729 | 0.60 | 42 / 31 / 11 | — |
| `lr_behavior` (expl.) | secondary | λ 1 | 0.342 | 0.896 / 0.815 | 0.45 | 43 / 33 / 10 | — |
| `answer_structure` (TRAIN bodies) | secondary | λ 10 | 0.322 | 0.904 / 0.830 | 0.45 | 39 / 31 / 8 | — |

Reading (unsafe/accepted per class): S01 5/5, S02 0/12, S03 3/10, S04 6/10, S05 0/12, S06
7/10, S08 0/11, S09 0/10, S10 2/8, S11 4/5, S12 11/11 — six of eleven classes are one label,
but S03, S04, S06, S10, S11 mix. Per-fold LOGO AUC (`lr_full`, λ 10): S03 0.29, S04 0.92,
S06 0.24, S10 0.83, S11 0.75 (mean 0.61); mean risk on held-out all-unsafe S01 = 0.15,
S12 = 0.51, all-safe S08 = 0.88 — transfer to unseen templates is inconsistent. Unlike Qwen,
Nemotron shows a genuine within-template behaviour signal: within-class per-feature AUC
`content_chars` 0.26 (a shorter answer is the unsafe one), `input_tokens` 0.29,
`reasoning_share` 0.68 (82 within-class pairs); the class-identity ceiling (0.936) is
nevertheless *above* every eligible candidate, and the primary-protocol τ* sits at the
grid ceiling (escalate nothing) — the utility rule's other degenerate corner when the
router is weak and the base rate is below 0.5.

**§ 12a numbers** (`learning/registry/r5/selection_rule.json`): Qwen primary null/null;
secondary Δ_util 0.646, E_max 6; Nemotron primary null/null; secondary Δ_util 0.469, E_max 7. K on DEV = 4 (Qwen), 4 (Nemotron).

## 7. DEV replay, Pareto frontier and selection

**Qwen DEV (n = 48; R4 32/48 @ 31.2 %, FN 16).** One replay per candidate at τ*
(`evals/reports/r5-replay-dev-qwen.json`, telemetry in `learning.routing_decisions`):

| policy | all-pass | util. | FN | unnec. | rescue | $/success | p50 / p95 | AUC (accepted) | caught of 16 (rc / ev) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| local-only | 17 (35.4 %) | 0 % | 31 | 0 | — | — | 12.9 / 41.7 s | — | — | — |
| **R4 verifier** | 32 (66.7 %) | 31.2 % | 16 | 0 | 1.00 | $0.0608 | 16.7 / 77.5 s | — | — | incumbent |
| `lr_full` sec. τ 0.60 | **47 (97.9 %)** | 70.8 % | 1 | 4 | 0.88 | $0.0854 | 45.8 / 86.3 s | 0.875 | 15 (6 / 9) | PASS |
| `lr_core` sec. τ 0.60 | 44 (91.7 %) | 68.8 % | 4 | 6 | 0.82 | $0.0865 | 43.3 / 77.7 s | 0.772 | 12 (3 / 9) | PASS |
| `tree` sec. τ 0.70 | 39 (81.2 %) | 56.2 % | 9 | 5 | 0.81 | $0.0790 | 40.1 / 77.5 s | 0.688 | 7 (2 / 5) | **PASS → selected (tie-break)** |
| `prior_class_ceiling` τ 0.60 (expl.) | 45 (93.8 %) | 68.8 % | 3 | 5 | 0.85 | $0.0875 | 43.3 s | 0.847 | 13 (4 / 9) | — |
| `prior_category` τ 0.60 (expl.) | 44 (91.7 %) | 64.6 % | 4 | 4 | 0.87 | $0.0841 | 42.6 s | 0.838 | 12 (4 / 8) | — |
| `lr_answer` τ 0.70 (expl.) | 46 (95.8 %) | 68.8 % | 2 | 4 | 0.88 | $0.0842 | 43.3 s | 0.888 | 14 (6 / 8) | — |
| `lr_behavior` τ 0.55 (expl.) | 47 (97.9 %) | 70.8 % | 1 | 4 | 0.88 | $0.0854 | 45.8 s | 0.882 | 15 (6 / 9) | — |
| primary-protocol candidates (τ* 0.35–0.45) | 47–48 | 81–100 % | 0–1 | 9–17 | 0.65–0.77 | $0.097–0.116 | 48–52 s | — | 15–16 | FAIL (gate; R2) |
| always-escalate | 48 | 100 % | 0 | 17 | 0.65 | $0.1160 | 51.5 / 86.3 s | — | 16 | — |
| oracle (min-useful) | 48 | 64.6 % | 0 | 0 | 1.00 | $0.0788 | 42.6 / 86.3 s | — | 16 | — |

Pareto (utilization → all-pass / FN / unnecessary), `lr_full` (secondary) sweep: 62.5 % →
45/3/2 · 68.8 % → 46/2/4 · 70.8 % → 47/1/4 · 75.0 % → 47/1/6 (grid floor); `tree`: 56.2 % →
39/9/5 · 72.9 % → 45/3/7 · 81.2 % → 47/1/9; cap-respecting FN-catching points existed
(`lr_core` τ 0.75: 40/48, FN 8, unnec 1, 50.0 %; `lr_full` primary τ 0.80: FN 12, unnec 0,
39.6 %) — the τ* rule, not the routers, put every selected point above the caps. Both routers reach oracle-level quality only
above the oracle's own 64.6 % utilization; the tree's τ* point is 8 pp *below* the oracle's
utilization at a cost of 9 FN. Selection under the pre-registered rule: primary protocol —
nothing eligible; secondary — all three PASS R1 (FN ≤ 12), R2 (util ≤ 31.2 + 64.6 %,
unnec ≤ 6), R3; none passes the skeleton's 50 % cap. Tie-break "fewer frontier calls" →
`tree` (27 calls vs 33/34); under the other reading of the plan's clause ("fewer
unnecessary escalations": 4 / 6 / 5) `lr_full` would have been frozen. Net of the class
ceiling at τ*: `lr_full` +2 catches, −1 unnecessary; `tree` −6 catches. Chance
(hypergeometric): `tree` 7/12 p = 0.31; `lr_full` 15/19 p = 4.7 × 10⁻⁵; ceiling 13/18
p = 0.004; a random 12-escalation passes R1 ∧ E_max with p ≈ 0.59. No abstain criterion
existed in the contract, and none is added for Nemotron (the two arms use identical
machinery); the chance-level numbers were first recorded (`6766e86`) after the Qwen TEST
look. The amended R2 utilization bound (95.8 % on DEV) did not bind; only E_max did.

**Nemotron DEV (n = 48; R4 35/48 @ 25.0 %, FN 13; `evals/reports/r5-replay-dev-nemotron.json`):**

| policy | all-pass | util. | FN | unnec. | rescue | $/success | p50 / p95 | AUC (accepted) | caught of 13 (rc / ev) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| local-only | 23 (47.9 %) | 0 % | 25 | 0 | — | — | 53.8 / 96.0 s | — | — | — |
| **R4 verifier** | 35 (72.9 %) | 25.0 % | 13 | 0 | 1.00 | $0.0453 | 54.7 / 150.0 s | — | — | incumbent |
| `lr_full` sec. τ 0.55 | **45 (93.8 %)** | 50.0 % | 3 | 2 | 0.92 | $0.0691 | 69.3 / 150.0 s | **0.953** | 10 (5 / 5) | PASS |
| `lr_core` sec. τ 0.50 | 40 (83.3 %) | 39.6 % | 8 | 2 | 0.89 | $0.0590 | 55.0 / 150.0 s | 0.676 | 5 (3 / 2) | **PASS → selected (tie-break)** |
| `tree` sec. τ 0.50 | 44 (91.7 %) | 56.2 % | 4 | 6 | 0.78 | $0.0784 | 67.3 / 150.0 s | 0.823 | 9 (4 / 5) | PASS |
| `prior_class_ceiling` τ 0.55 (expl.) | 45 (93.8 %) | 52.1 % | 3 | 3 | 0.88 | $0.0707 | 69.3 s | 0.876 | 10 (4 / 6) | — |
| `prior_category` τ 0.60 (expl.) | 44 (91.7 %) | 47.9 % | 4 | 2 | 0.91 | $0.0633 | 67.0 s | 0.823 | 9 (4 / 5) | — |
| `lr_answer` τ 0.60 (expl.) | 45 (93.8 %) | 54.2 % | 3 | 4 | 0.85 | $0.0697 | 71.3 s | 0.940 | 10 (5 / 5) | — |
| `lr_behavior` τ 0.45 (expl.) | **48 (100 %)** | 60.4 % | 0 | 4 | 0.86 | $0.0727 | 72.6 s | 0.926 | 13 (5 / 8) | — |
| primary-protocol candidates (τ* 0.80) | 35–39 | 25–33 % | 9–13 | 0 | 1.00 | $0.045–0.056 | 55–59 s | — | 0–4 | FAIL (gate) |
| always-escalate | 48 | 100 % | 0 | 23 | 0.52 | $0.1160 | 91.1 / 150.0 s | — | 13 | — |
| oracle (min-useful) | 48 | 52.1 % | 0 | 0 | 1.00 | $0.0635 | 72.3 / 150.0 s | — | 13 | — |

Pareto, `lr_full`: 41.7 % → 42/6/1 · 47.9 % → 45/3/1 · 50.0 % → 45/3/2 · 54.2 % → 47/1/2 ·
60.4 % → 48/0/4; `lr_core`: 25.0 % → 35/13/0 · 33.3 % → 38/10/1 · 39.6 % → 40/8/2 · 47.9 % →
41/7/5 · 64.6 % → 44/4/10; `tree`: 33.3 % → 39/9/0 · 45.8 % → 42/6/3 · 56.2 % → 44/4/6.
Selection: primary — nothing eligible; secondary — all three PASS R1 (FN ≤ 9), R2 (util ≤
25.0 + 46.9 %, unnec ≤ 7), R3; `lr_core` is the only one that also passes the skeleton's
caps (39.6 % ≤ 45 %). Tie-break "fewer frontier calls" → `lr_core` (19 calls vs 24 / 27);
under "fewer unnecessary escalations" `lr_full` and `lr_core` tie at 2 and the next key
(cost/success) would again pick `lr_core`. Net of the class ceiling at τ*: `lr_full` +0
catches / −1 unnecessary at 2 pp less utilization (and AUC 0.953 vs 0.876 — the router
ranks better than the class prior on DEV); `lr_core` −5 catches. Chance: `lr_core` 5/7
p = 0.044; `lr_full` 10/12 p = 6 × 10⁻⁵; `tree` 9/15 p = 0.015; a random 7-escalation passes
R1 ∧ E_max with p ≈ 0.20. The amended R2 bound (71.9 %) did not bind.

## 8. Silent-failure result

*How many verifier-clean R4 failures did the learned router catch?*

| | R4 FN | selected policy caught | root-cause misses | evidence misses | other | remaining | new unnecessary |
|---|---|---|---|---|---|---|---|
| Qwen DEV | 16 (7 rc / 9 ev) | `tree` 7 | 2 | 5 | 0 | 9 | 5 |
| Qwen DEV, best survivor `lr_full` | 16 | 15 | 6 | 9 | 0 | 1 (S08-2003007 → said `processor_decline`) | 4 |
| Qwen TEST | 47 (14 rc / 33 ev) | `tree` 27 | 5 | 22 | 0 | 20 (9 rc / 11 ev) | 6 |
| Nemotron DEV | 13 (5 rc / 8 ev) | `lr_core` 5 | 3 | 2 | 0 | 8 | 2 |
| Nemotron DEV, best survivor `lr_full` | 13 | 10 | 5 | 5 | 0 | 3 (S03/S04/S10 evidence) | 2 |
| Nemotron DEV, exploratory `lr_behavior` | 13 | 13 | 5 | 8 | 0 | 0 | 4 |
| Nemotron TEST | 26 (10 rc / 16 ev) | `lr_core` 5 | 4 | 1 | 0 | 21 (6 rc / 15 ev) | 6 |

The catches are the classes whose template the router recognises as hard for the local
model (Qwen TEST caught: S03 ×6, S04 ×3, S06 ×4, S08, S10 ×6, S11 ×2, S12 ×5); the
S12 → `kyc_hold` root-cause misses are caught via the answer echo + bundle shape, the S02
`duplicate_webhook_handled` misses via the said label. Evidence-short answers are caught by
template, not by anything in the answer that says "this is short".

## 9. TEST (exactly once per frozen policy)

| policy | all-pass | util. | FN | unnec. | rescue | $/attempt | $/success | p50 / p95 | AUC (accepted) | reading |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen R4 | 48/96 (50.0 %) | 22.9 % | 47 | 0 | 0.95 | $0.0256 | $0.0513 | 15.4 / 62.0 s | — | incumbent |
| **Qwen `r5-qwen-tree-stratified-v1`** | **75/96 (78.1 %)** | 57.3 % | **20** | 6 | 0.87 | $0.0624 | $0.0799 | 37.6 / 77.2 s | 0.762 | **CONFIRMED** (K_test 12; unnec ≤ 12; util ≤ 87.5 %) |
| Qwen oracle (min-useful) / always-escalate | 95 / 95 | 70.8 % / 100 % | 0 / 0 | 0 / 27 | | $0.0811 / $0.1127 | $0.0819 / $0.1139 | 43.4 / 52.7 s | | |
| Nemotron R4 | 69/96 (71.9 %) | 21.9 % | 26 | 0 | 1.00 | $0.0273 | $0.0380 | 56.1 s | — | incumbent |
| **Nemotron `r5-nemotron-lr_core-stratified-v1`** (τ 0.50) | 74/96 (77.1 %) | 33.3 % | **21** | 6 | 0.81 | $0.0392 | $0.0509 | 57.1 / 145.9 s | 0.557 | **NOT CONFIRMED** (FN 26 → 21 < K_test 7; unnecessary 6 ≤ 14 ✓; util ≤ 68.8 % ✓) |
| Nemotron oracle (min-useful) / always-escalate | 95 / 95 | 49.0 % / 100 % | 0 / 0 | 0 / 48 | | $0.0586 / $0.1127 | $0.0592 / $0.1139 | 64.9 / 94.1 s | | |

No threshold sweep was computed on TEST; nothing was changed after either look. The Qwen
TEST catch count (27 of 33 escalations vs base rate 0.64) has hypergeometric p = 0.003
against a *random* null — but a random escalator of the same size also meets the
pre-registered reading with p ≈ 0.59 (K_test 12 is met by any 33-draw; unnecessary ≤ 12 is
the binding clause), and the reading says nothing against the template-prior null. Post-hoc
descriptive counterfactual from the same opened look: a TRAIN class prior at τ 0.60
(escalate S03/S04/S06/S07/S10/S11/S12) would have caught 39 with the same 6 unnecessary at
69.8 % utilization — the TEST gain is *not* net of the class ceiling; the frozen tree missed
10 cases in classes with zero safe accepted TEST cases (S06/S10/S11/S12) and all four S02
said-label misses. Price of the tree over R4 on TEST: cost/success +56 % ($0.0513 →
$0.0799), wall p50 2.4× (15.4 → 37.6 s), rescue rate 0.95 → 0.87; frontier utilization
57.3 % vs the oracle's 70.8 % and always-escalate's 100 % — not a collapse toward
strong-only by precision (0.82 vs base 0.64), though the amended R2 bound (87.5 %) would
have tolerated one. Nemotron: the frozen `lr_core` caught 5 of 26 in 11 escalations (p = 0.35 against a
random null; a random 11-escalation would be *confirmed* with p ≈ 0.04, so the Nemotron
reading had teeth and was not met) — cost/success +34 % ($0.0380 → $0.0509) for +5 passes.
Second-order cost: both models' TEST is no longer blind for learned routing on Suite v3 —
any later router (R5b, R6) inherits these looks.

## 10. Timing and efficiency

| phase | wall (UTC, 2026-08-18) | notes |
|---|---|---|
| reconciliation | 04:55–05:12 (17 min) | docs, DB, code, servers |
| acquisition tooling + contract skeleton | 05:12–05:20 | migration 007, make targets, § 1–16 |
| TRAIN acquisition (Qwen) | 05:16–05:53 (37 min) | 144 local calls, same session as the Suite v3 arms |
| TRAIN acquisition (Nemotron) | 05:55–08:59 (3 h 04 min; S07 cases at 8 192 tokens dominate) | restart + probe + 144 local calls |
| feature/learner/replay/oracle tooling + tests (3 Opus agents in parallel) | 05:20–05:35 | 453 tests green |
| adversarial audit (5 Fable lenses + synthesis) | 05:33–06:24 (parallel) | lens findings landed pre-DEV (`4b10da0`); synthesis and follow-ups (`b1e92e9`) landed after the Qwen DEV selection and before/around the Qwen TEST look |
| Qwen TRAIN CV, amendment, state machine, DEV selection | 05:56–06:22 | |
| Qwen TEST replay | 06:24 (< 1 min) | offline |
| Nemotron TRAIN CV, amendment, DEV selection, TEST | 09:00–09:15 (TRAIN CV both protocols 3 min, § 12a-N, DEV selection, TEST replay, oracles — all offline) | |
| documentation | 06:30–09:45 interleaved (report drafting during the Nemotron acquisition; independent reviewer 06:40–06:57) | |
| **total** | ≈ 4 h 50 min wall (04:55–09:45 UTC), of which 3 h 41 min was local model inference for TRAIN acquisition; everything after the acquisition finished took 45 min | vs ≈ 6 h for the Suite v3 release |

Work answered by offline replay: every DEV and TEST number, every oracle, the R4
reproduction, all Pareto sweeps (thousands of policy evaluations) — no frontier call.

## 11. Interpretation

**Can production-observable trajectory features predict silent local failure well enough
to improve on R4?** In this benchmark, yes for the *system* number and — as far as R5
could test — no for the *mechanism the plan asked about*. Every eligible candidate under the deployment-matched
protocol lifts strict all-pass far above R4 (Qwen DEV 66.7 % → 81–98 %; TEST 50.0 % →
78.1 % for the frozen tree) while keeping unnecessary escalations at 4–6 of 48, and the
frozen policy's TEST catches are far beyond chance. But the routers are within 0.01 AUC of
a router that reads only the scenario class (TRAIN), the eligible feature set identifies
that class for 45/48 cases from bundle size and tool-call shape, and within a class the
label barely varies. What R5 learned is *which templates the local model fails on* — a
task-difficulty prior expressed through production-observable proxies — plus a thin layer
of genuine answer-content signal (the S02 `duplicate_webhook_handled` label, within-class
AUC 0.66; `lr_full` catches 2 more than the class ceiling on DEV with one fewer unnecessary
escalation). The plan's own primary protocol, which asks the router to generalise to unseen
templates, found nothing (per-fold LOGO AUC mean 0.39). The honest bound: TRAIN's label
structure (minority n ≤ 1 in 8 of 11 classes) leaves R5 almost no power to detect a small
within-template signal, so "not detected" is not "absent".

**Which local model produces the better learned-routing system frontier?**
Nemotron — on every axis but one. Its verifier-clean base rate is lower (TRAIN 0.365 vs 0.61,
DEV 13/36 vs 16/33), so a router has room to be selective; its DEV frontier is strictly
better (`lr_full` 45/48 at 50 % with 2 unnecessary vs Qwen's 47/48 at 71 % with 4; the
behaviour-only `lr_behavior` reaches 48/48 at 60 % — the oracle's quality 8 pp above the
oracle's utilization); it is the only model whose routers rank *above* the class-identity
ceiling on DEV (0.953 vs 0.876) and whose within-class features carry signal
(`content_chars` 0.26); and Nemotron + R4 alone already dominates Qwen + frozen tree on cost
on TEST ($0.0380 vs $0.0799 per success at 71.9 % vs 78.1 %). The one axis it loses is
latency: Nemotron's cascade p50 (55–72 s) exceeds the frontier's own 37 s, so a Nemotron
cascade trades cost for wall time. The frozen Nemotron policy (`lr_core`, no answer echo)
was the weakest survivor and did not carry to TEST (AUC 0.557); the DEV evidence for the
better Nemotron routers is what stands.

**How far does the learned policy remain from the oracle?** Qwen: the frozen tree is 20
cases (TEST) / 9 cases (DEV) short of the min-useful oracle at 13 pp / 8 pp less
utilization; `lr_full`, the best DEV survivor, was 1 case short at 6 pp more utilization
than the oracle. Nemotron: the frozen `lr_core` is 21 cases (TEST) / 8 (DEV) short of the oracle at 16 pp / 13 pp *less* utilization; the best DEV survivor `lr_full` was 3 short at 2 pp less utilization than the oracle, and the exploratory behaviour-only `lr_behavior` reached the oracle's 48/48 on DEV at 60.4 % (8 pp above it). Reaching the oracle for Qwen requires ~65–70 %
frontier utilization because ~64 % of Qwen's verifier-clean answers are wrong — the
a-priori "no collapse" caps in the skeleton (20 pp / 50 %) would have forbidden every
FN-catching Qwen router regardless of its precision, which is why § 12a-2 replaced them,
before DEV, with the TRAIN-derived bound plus E_max.

**What went wrong with the pre-registration, stated plainly.** (1) The contract
operationalised the plan's tie-break "fewer unnecessary escalations/frontier calls" as
"fewer frontier calls"; that reading selects the least-escalating survivor, not the
highest-quality one — for Qwen it froze a router below the class ceiling on DEV while
`lr_full` (47/48, p = 4.7 × 10⁻⁵) was on the table and would have won under the other
reading; the rule was applied as written and the tree was the policy tested. (2) The utility
rule U = catches − unnecessary degenerates when more than half the accepted cases are
unsafe; § 12a-2 relaxed the utilization bound to fit the τ* that rule produced, when
choosing τ* subject to the cap was the TRAIN-driven alternative. (3) Pooled LOGO AUC is
null-biased under class-clustered labels, so the primary gate could not be informative;
the secondary protocol and the uncapped R2 were registered before DEV but after TRAIN CV,
each was necessary for any selection, and each moved toward permitting a pass — a
skeptical reader should weight the Qwen result accordingly (the ordering rests on the
commit record and telemetry timestamps plus the operator's statement; `--no-telemetry`
exists). (4) With n = 48 the rule and the TEST reading have little power against a random
escalator for Qwen (p ≈ 0.59). All four are recorded in the contract, not repaired after the
fact.

## 12. Residual failure analysis

Qwen TEST remaining after the tree (20): root cause 9 — S02 `duplicate_webhook_handled` ×4
(the said-label pattern the tree does not split on), S06 `reconciliation_gap`, S07
`reconciliation_gap` ×2, S08 `processor_decline`, S12 `kyc_hold` — and evidence 11 — S06 ×3,
S07, S08, S09, S10 ×2, S11 ×3 (recall 0.50–0.75, all scored below τ 0.70). Nemotron TEST remaining after `lr_core` (21): root cause 6 (S12 `kyc_hold` ×3, S02
`duplicate_webhook_handled`, S05 `settlement_amount_mapping_error`, S11 `risk_hold`),
evidence 15 (S01 ×4, S06 ×4, S11 ×2, S03, S04, S05, S09, S10); caught: S12 ×4 and S10
×1; the classifier's TEST AUC on the accepted subset (0.557) is near chance — the
family A + B + C router (no answer echo) did not carry Nemotron's DEV signal to TEST,
whereas its DEV AUC was 0.676.
Nothing in the snapshot distinguishes an evidence-short answer from a complete one on the
same template; the answer-structure comparator on TRAIN bodies (fact count, cited-id
count, confidence…) did not raise the class-dominated AUC either (0.873 vs 0.901) — which
is untested rather than refuted, because TRAIN holds almost no within-template contrast.

## 13. Next recommendation (exactly one)

**Model specialization of the local tier (QLoRA on Nemotron 3.5 Lightning first, Qwen
second) targeted at evidence-citation discipline on the systematically failing templates,
trained on the TRAIN split only and measured with the R5 replay/oracle machinery as the
instrument — with a class-difficulty router (`lr_full`-style, family A + D) kept as the
interim production gate above R4.**

Why this and not the others. (i) The plan's own mapping applies: "model specialization if
residual failures are not predictable" — R5's central finding is that within-template silent
failure is not predictable from anything the trajectory or the answer body exposes; routing
has been taken to the point where its only remaining lever is the template prior. (ii) The
residual is a *capability* deficit, not an evidence or gate deficit: the dominant bucket is
evidence-short answers on specific templates (Qwen TEST 33/47 R4 FNs, Nemotron 16/26;
S01/S03/S06/S10/S11 throughout, plus S12/S02 root-cause misses), evidence reachability is
1.000, and the frontier passes 99 % of the same bundles. (iii) Prompting is exhausted on
exactly this dimension — E6/E6b ran eight variants and none moved evidence recall — so a
"narrow evidence/prompt intervention" would be a ninth variant without a new mechanism;
richer deterministic verifier signals cannot see a short-but-consistent answer either.
(iv) R6 multi-tier is not yet supported: the three-tier oracle's Nemotron-sufficient band
(DEV 10/48, TEST 27/96, TRAIN 33/144) is *not* template-clean — S03/S06/S10 mix Qwen-,
Nemotron- and frontier-sufficient cases on every split — so a class-difficulty gate cannot
select it, within-template routing is not learnable, the upside is bounded (frontier-
required 41–43 % regardless), and Nemotron's cascade p50 exceeds the frontier's own.
(v) The data now exists: TRAIN trajectories with persisted answer bodies for both local
models (`learning.model_outputs`), the frozen DEV/TEST arms for a blind-on-DEV
comparison, and the replay instrument that turns any new local run into cascade numbers
without a frontier call. Nemotron first because its routers rank above the class ceiling
and its within-class features carry signal, i.e. it is the model whose failures are
closest to correctable. R5 also leaves two methodological fixes for whoever pre-registers
next: a quality-first tie-break among survivors, and a threshold rule that charges
escalation (or optimises subject to the utilization bound) so the τ* rule and the R2 rule
optimise the same objective.

Not started here: QLoRA, R6, dynamic harness work, any Suite v3 change.
