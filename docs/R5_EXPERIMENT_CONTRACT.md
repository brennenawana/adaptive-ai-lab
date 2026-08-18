# R5 — Learned Silent-Failure Routing: Experiment Contract (pre-registered)

Governing document: `docs/FIS_R5_Learned_Silent_Failure_Routing_Plan.html` (committed
`fc1c18e`). Reconciliation record: `OVERNIGHT_STATUS.md` § M6.0. This contract is
written in two commits, both **before any learned candidate is scored on DEV**:

1. **Skeleton (this commit):** boundary, allowlist, labels, grouping, CV, candidate
   families, hyperparameter bounds, threshold grid, replay semantics, TEST unlock,
   reporting metrics, and the *shape* of the DEV selection rule.
2. **Numeric amendment (§ 12, after TRAIN CV, before DEV):** the exact numbers in the
   selection rule, derived from TRAIN evidence by the formulas fixed here.

Anything not listed is not in R5. Anything listed that turns out wrong is corrected by a
further commit that says so, never silently. Nothing here was chosen after looking at a
DEV or TEST candidate result.

---

## 1. Purpose and scientific question

Can production-observable trajectory + answer features identify verifier-clean local
failures that the deterministic R4 gate misses — with fewer unsafe local returns and
without degenerating toward strong-only routing?

The target is not classifier accuracy. It is a routing policy that, on DEV, catches a
material share of R4's routing false negatives while staying far from strong-only
utilization. A null result is a valid result and is reported as one.

## 2. Frozen identity (unchanged by R5)

| field | value |
|---|---|
| suite | 3, tag `suite-v3` (`7764601`), corpus digest `1e7c5278ba1f4cc1cc96fa8a1f04946ab622270eaba4c5671274c21e9d39e528` |
| scorer / verifier / ontology / prompt | 3 / 3 / 1 / 1 |
| local arms | `local-specialist` (Qwen3-8B Q4_K_M, 8082, `max_tokens 4096`, prompt `cause_action_directed`); `nemotron-lightning` (Nemotron 3.5 Lightning 30B-A3B IQ4_XS, 8083, `--fit on --fit-target 1024 --no-mmap`, `max_tokens 8192`, same prompt) |
| strong arm | `claude-frontier` (Claude Opus 5 via `claude` CLI, prompt `baseline`) |
| evidence | `FIXED_EVIDENCE`, two-phase plan, 8 tools |
| incumbent gate | R4 `verifier` policy (`services/ai_orchestrator/cascade.py`), unchanged |

Not changed by R5: suite, corpus, prompts, models, budgets, evidence plan, scorer,
verifier, cascade gate. R5 adds a routing policy and its offline replay/analysis only.

## 3. Source runs

| split | Qwen | Nemotron | frontier |
|---|---|---|---|
| TRAIN (144) | `R5-qwen-train` (acquired for R5 under the frozen configuration, `make eval-r5-train-qwen`) | `R5-nemotron-train` (`make eval-r5-train-nemotron`: restart + train-case probe + prime, as Suite v3) | **not run** — labels come from the local scorer; the three-tier oracle on TRAIN therefore reports "neither local" without a frontier split |
| DEV (48) | `V3-qwen-dev` | `V3-nemotron-dev` | `E4-v3-dev` |
| TEST (96) | `V3-qwen-96` | `V3-nemotron-96` | `E4-v3-96` |

`V3-qwen2-dev` (the Suite v3 reproducibility arm) is used only to check that the
snapshot is identical for identical outputs. No DEV or TEST model output is regenerated.

## 4. Split policy

- **TRAIN**: fit preprocessing and classifiers; all hyperparameter, feature-set and
  threshold choices; grouped TRAIN-only CV.
- **DEV**: one replay per pre-registered candidate at its TRAIN-chosen threshold; the
  Pareto sweep over the threshold grid is reported *descriptively*; the selection rule
  (§ 12) picks at most one policy per local model.
- **TEST**: opened once, only for a policy that qualified on DEV and was frozen (§ 14).
  TEST labels are not read by any R5 script until the unlock (§ 14); no threshold,
  feature or classifier is chosen on TEST.

## 5. Decision point and snapshot

The R5 snapshot is taken at exactly the R4 decision point: after `investigate()` returns
`(weak_result, weak_traj)` — i.e. after parse and `verify()` — and before any strong
call (`cascade.py::investigate_cascade`, `signals_from` → `should_escalate`).

Snapshot inputs are only:

- the local stage's `Trajectory` (model invocation, verifier verdict, tool calls, error);
- the answer's own `root_cause.label` and `recommended_next_action` (fields of the
  model's `InvestigationResult`).

For the frozen Suite v3 arms the answer body was not persisted (only its sha256), so
those two answer fields are reconstructed in the **dataset layer** from the scorer's
verbatim echo (`dimensions[root_cause].detail = "said <label>, truth …"`,
`dimensions[next_action].detail = "said <action>"`). Only the `said` value is taken;
the truth is never read. `test_routing_features_no_gold_leak.py` asserts that the
snapshot from a real `InvestigationResult` equals the snapshot from the echo.

## 6. Feature contract — `RoutingFeatureSnapshot`, `feature_schema_version = "1"`

Module: `fis_platform/routing/features.py`. Explicit allowlist (`FEATURE_ORDER`); a
name outside it is a schema error; a name in `FORBIDDEN_FEATURE_NAMES`
(= `GOLD_FEATURE_NAMES` ∪ {`strict_all_pass`, `all_pass`, `score`, `scorer`, `frontier`,
`strong`, `split`, `category`, `class`, `seed`, `scenario_id`, `expected_*`, `gold`,
`manifest`, `evidence_recall`, `truth`}) is a schema error even if it were listed.
Serialization is canonical JSON in `FEATURE_ORDER`; `digest` = sha256 of it. All
features are numeric. Values derived from ratios are rounded to 6 decimals.

**Family A — model/runtime** (from `model_invocations[0]`, the local stage):
`produced_output`, `stop_length`, `input_tokens`, `output_tokens`, `reasoning_chars`,
`content_chars`, `reasoning_share`, `output_per_input`, `budget_used`
(`output_tokens/max_tokens`), `wall_ms`, `api_ms`.

**Family B — verifier** (from `verification`): `verifier_passed`, `schema_valid`,
`checks_evaluated`, `check_schema_validation`, `check_citation_required`,
`check_citation_resolves_to_call`, `check_cited_ids_observed`, `check_known_action_code`,
`check_confidence_supported`, `check_facts_present` (absent check → 0),
`n_violations`, `n_unsupported_claims` (the scorer's/R4's marker rule),
`n_fabricated_ids`, `n_uncalled_services`, `schema_error_count`, `no_output_error`.

**Family C — tool trajectory** (from `tool_calls`): `n_tool_calls`, `n_tool_success`,
`n_tool_errors`, `n_unique_tools`, `n_webhook_history_calls`, `n_verification_calls`,
`n_repeated_calls` (same tool + `args_hash` more than once), `tool_latency_ms_total`.

**Family D — answer echo**: `answer_present`; one-hot `said_label_<RootCauseLabel>`
(13 values) and `said_action_<NextAction>` (9 values).

**Family E — task-visible structure**: nothing beyond what A–C already carry
(`input_tokens` is the bundle size; the tool-call shape is the case's subject shape).
The case `category` is model-visible but identifies the scenario class for four of eight
categories and is **excluded** from the primary allowlist (plan § 7: classes may not
appear directly or indirectly). It may appear only in the exploratory class-prior
comparator (§ 9), never in an eligible candidate.

Snapshot header (not features): `feature_schema_version`, `local_model`
(`canonical_model` of the invocation), `digest`.

Not read by the extractor, ever: `Trajectory.scenario_id`, `experiment_arm`,
`runtime_context`, `case_id`, any score payload, any manifest, any strong-arm row.

### Leak guards (tests, extending `test_routing_no_gold_leak.py`)

1. forbidden names cannot enter the snapshot (schema error), nor names outside the allowlist;
2. extraction succeeds on a trajectory with no gold/scorer fields at all;
3. gold-removal invariance: perturbing/removing `scenario_id`, `experiment_arm`,
   `runtime_context`, `case_id` leaves the digest identical;
4. no feature name mentions scenario/class/seed/split; the extractor signature has no
   score/manifest parameter;
5. TEST/DEV split metadata is not a feature and not an input;
6. deterministic serialization (two extractions → one digest; fixed order);
7. `feature_schema_version` recorded on every snapshot and every artifact;
8. a production-shaped trajectory + `InvestigationResult` yields the snapshot, and it
   equals the snapshot from the scorer echo of the same answer;
9. `fis_platform/routing/` inherits the import ban (`evals.scorers`, `schemas.scenario`,
   `scenarios.generator`, `ground_truth*`).

## 7. Labels (dataset/analysis layer only)

- Primary: `safe_local = strict_all_pass` of the local run; the router's positive class
  is `unsafe = not strict_all_pass`.
- Diagnostic (analysis only): `no_output`, `verifier_fail` (incl. `unsupported`),
  `wrong_root_cause`, `evidence_miss`, `action_fail`, `forbidden_claim`; a case may
  carry several. `silent = verifier-clean and unsafe`.
- Strong reference (DEV/TEST only): `strong_pass` of the frontier run; routing FN =
  accepted ∧ ¬safe_local ∧ strong_pass (the R4 definition in
  `routing_cascade_report.py`).

Labels never enter the snapshot; the dataset builder writes them in separate columns.

## 8. Grouping / memorization guard

Scenario seeds are `lo + i·1000 + class_idx`: every seed of a class is an independent
draw of the same template, and the only template relation is the class. **Group key =
scenario class** (`scenario_id[:3]`), available to the offline pipeline only, never a
feature. Primary CV = leave-one-class-out over the 12 classes (grouped K-fold, K = 12).
Conservative relative to deployment (DEV/TEST contain the same 12 templates); a
seed-stratified 4-fold CV is reported as an exploratory secondary number and drives no
choice.

## 9. Policy form, candidates and hyperparameter bounds

**Policy form (all eligible candidates):** `escalate = R4_escalate ∨ (risk ≥ τ)`. The
learned router is fitted on the R4-accepted (verifier-clean, produced-output) subset of
TRAIN, because R4 already escalates the rest deterministically and the question is the
residual. Features constant on that subset carry zero weight by construction.

Eligible candidates (per local model, trained separately):

| id | classifier | features | hyperparameter bounds |
|---|---|---|---|
| `lr_full` | logistic regression, L2, standardized inputs, unpenalized intercept, Newton–Raphson (stdlib) | all of § 6 | λ ∈ {0.1, 1, 10, 100}, chosen by grouped-CV out-of-fold log-loss |
| `lr_core` | same | families A + B + C (no answer one-hots) | same |
| `tree` | CART, Gini, Laplace leaf probabilities (stdlib) | all of § 6 | depth ∈ {2, 3}, min leaf 8, chosen by grouped-CV out-of-fold log-loss |

Exploratory only (reported, never eligible for selection or TEST): `lr_answer` (family D
only), `prior_category` (case category only — how much of any gain is task prior),
`lr_unified` (both models pooled + a model flag), and, on TRAIN only, an
answer-structure model over the persisted TRAIN answer bodies (fact count, cited-id
count, hypotheses/uncertainties counts, confidence, summary length) — features
DEV/TEST cannot compute; it informs the next-milestone recommendation, nothing else.

Not used: neural nets, LLM judges, embeddings, hidden reasoning text, scenario
ids/classes/seeds, gold-derived features, scikit-learn/numpy (not in the stack; the
routers are stdlib with JSON artifacts and stable digests).

## 10. TRAIN-only development

On TRAIN grouped CV: fit standardizer per fold, choose λ / depth per candidate by
out-of-fold log-loss, report out-of-fold ROC-AUC, PR-AUC (average precision), Brier,
coefficient-sign stability across folds, and the operating-point curve over the
threshold grid.

**Threshold grid:** τ ∈ {0.30, 0.35, 0.40, …, 0.80}. **Threshold rule:** for each
candidate, τ* = the grid value maximizing out-of-fold utility
`U(τ) = catches(τ) − unnecessary(τ)` on the R4-accepted TRAIN subset (a catch = an
unsafe case escalated; unnecessary = a safe case escalated; λ = 1, i.e. escalate when
the case is more likely unsafe than not); ties → the larger τ. One τ* per candidate;
DEV replays the candidate at τ* only for selection.

**TRAIN eligibility gate** (fixed now): a candidate is eligible for DEV selection only if
its pooled out-of-fold ROC-AUC on the R4-accepted TRAIN subset is ≥ 0.60 and its
out-of-fold PR-AUC exceeds the subset base rate by ≥ 0.10. Ineligible candidates are
still replayed on DEV once and reported, marked ineligible.

## 11. Offline replay semantics (DEV and TEST)

For each case of the frozen local run: compute the snapshot at the decision point,
`risk = classifier(snapshot)`, `escalate = R4 ∨ risk ≥ τ`. If local: the frozen local
scored outcome; if escalate: the frozen frontier scored outcome for the same case. Cost,
tokens and wall as `routing_cascade_report.py` (weak stage always paid; strong added when
escalated; frontier input tokens are a floor). No new model calls.

Reported per policy: **classifier** — unsafe recall/precision, FP, FN, ROC-AUC, PR-AUC,
Brier; **system** — strict all-pass, routing FN, frontier utilization, unnecessary
escalations, rescue rate, cost/attempt, cost/success, wall p50/p95, local output tokens,
gap to oracle; **silent family** — R4 verifier-clean FN caught / remaining, split into
root-cause misses, evidence misses, other; new unnecessary escalations. Plus the DEV
Pareto table (utilization vs all-pass vs routing FN) over the grid, with local-only, R4,
each candidate, the selected policy, strong-only and the oracle marked.

## 12. DEV selection rule — shape (numbers amended after TRAIN CV, before DEV)

Applied per local model to eligible candidates at τ*, lexicographically:

- **R1 material FN reduction:** `routing_FN(policy) ≤ routing_FN(R4) − K`, with
  `K = max(3, ⌈0.25 · routing_FN(R4)⌉)` — one quarter of the incumbent's blind spot on
  the same split, never fewer than three cases.
- **R2 no collapse toward strong-only:** frontier utilization ≤ `util(R4) + Δ_util` and
  ≤ 50 % absolute; unnecessary escalations ≤ `E_max`. `Δ_util` and `E_max` are set in
  the amendment from TRAIN out-of-fold evidence by the formulas
  `Δ_util = min(20 pp, 1.5 × OOF escalation-rate increase at τ*)` (over the eligible
  candidates, the largest value) and `E_max = ⌈1.5 × OOF unnecessary-rate at τ* × 48⌉`
  (largest over eligible candidates), i.e. what TRAIN predicts with 50 % slack.
- **R3 quality:** strict all-pass(policy) > strict all-pass(R4).
- **R4 tie-break** among survivors: fewer frontier calls, then lower cost/success, then
  lower wall p50.

If no candidate survives: negative result recorded, R4 stays incumbent, TEST is not
opened for any learned policy. No criterion is relaxed after DEV is seen.

**§ 12a — numeric amendment:** _to be added by a further commit after TRAIN CV and before
any DEV candidate replay; it will state K, Δ_util and E_max per local model with the
TRAIN numbers they were derived from._

## 13. Router artifact freeze

For each qualifying policy, `learning/registry/r5/<policy_id>.json` (committed):
policy id, classifier family, serialized model (coefficients / tree), preprocessing
(means, stds, feature order), `feature_schema_version`, τ*, training run ids, training
dataset digest, code commit, TRAIN CV numbers, DEV selection result; `artifact_digest` =
sha256 of the canonical JSON. Replay and any live runtime fail closed if the artifact's
`feature_schema_version` or feature order differs from the extractor's.

## 14. TEST unlock

Only for a policy frozen under § 13. `scripts/r5_replay.py --split test` refuses to run
without `--unlock-test <policy_id>` naming a policy whose frozen artifact records
`dev_selection = PASS`, and records the unlock in
`learning/registry/r5/test_unlock.json`; a second TEST replay of the same policy is
refused. No feature/threshold/classifier change afterwards; a disappointing number is
reported, not re-run. The three-tier cheapest-sufficient oracle's TEST counts are
computed at the same unlock (from frozen local/frontier TEST outcomes; descriptive).

## 15. Routing telemetry

Every replay decision (DEV, and TEST at unlock) is persisted to
`learning.routing_decisions` (migration 008): `routing_policy`, `local_model`,
`router_artifact_digest`, `feature_schema_version`, `feature_snapshot_digest`,
`risk_score`, `threshold`, `decision`, `r4_decision`,
`production_observable_only = true`, `run_id`, `scenario_id`, `trace_id`. Gold and
outcomes are joined afterwards in the analysis layer; the decision record carries none.

## 16. Reporting

`docs/R5_LEARNED_ROUTING_REPORT.md`: identity, dataset/splits, feature contract and leak
evidence, oracles (post-answer per model; three-tier descriptive), R4 reproduction
against the release report, TRAIN CV results and artifact digests, DEV Pareto and
selection, silent-failure recovery, TEST (or "TEST NOT OPENED"), timing by phase, number
of new model calls, next recommendation (exactly one).
