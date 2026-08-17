# Suite v3 — Release Contract (pre-registered)

Written and committed **before** any Suite v3 implementation and before any Suite v3
model run, per `docs/FIS_Suite_v3_Benchmark_Release_Goal_Prompt.txt` § "SCOPE FREEZE".
Reconciliation record: `OVERNIGHT_STATUS.md` § M5.0. Anything not listed here is not
in Suite v3; anything listed here that turns out to be wrong is corrected by a further
commit that says so, never silently.

Every change below answers two questions, and only those:
*What simulator, evidence, scorer or verifier invariant was wrong under Suite v2?* and
*How does the change make the benchmark more faithful to its own declared task
semantics?* No change is justified by, or was chosen after looking at, any model's
score.

---

## 1. Purpose

Suite v3 is a **benchmark revision**, not a model, prompt, routing, QLoRA or
learned-routing experiment. It removes four classes of harness defect that were found
independently by arm disagreement during R2/R4 (`routing-experiments.md` § R2 harness
review) and deliberately deferred instead of being patched mid-baseline, then
re-establishes DEV and TEST baselines for the three arms under one recorded contract.
Suite v2 results stay as history and are never subtracted from Suite v3 results.

## 2. Exact changelist

### A. Background settlement realism (generator, event pipeline)

**v2 defect.** `catalog._distractors()` creates 3 approved authorizations with
settlements in S01, S02, S05, S06, S07, S08 but never publishes them, so those
settlements have no webhook delivery, no normalized event and no ledger entry. That is
S10's fault signature (`reconciliation_gap`) present as ambient noise in six classes:
every S06 world has 4 settlements and 1 entry, S05/S08 have 3 settlements and 0
entries. S11 posts its 3 background settlements by direct `World.add_entry`, giving
them counter-shaped ids (`le_<seed>_NN`) unlike every pipeline entry (`le_<12hex>`) —
a model-visible class fingerprint. Distractors are generated *after* `add_case`, so
background purchases post-date the case they are background to (and in S08 they are
approvals on a card the world says is frozen). S07's two published events are
"received" (`published_at`) at T+2/T+4 minutes although they occurred at T+75/T+65 — a
delivery received before its event happened.

**v3 change.**
1. `_distractors` becomes `_background(w, cus, acc, card)`: each background settlement
   is **published** as a `settlement.created` `ProviderEvent` (its own
   `provider_ref`, idempotency key `idem-<provider_ref>`, attempt 1) and materialised by
   the integration and ledger consumers exactly like an injected one. No direct write.
2. Ordering per class, chosen for world coherence and for the fixed-evidence plan's
   `_phase_two` limit (webhook history is fetched for the first 6 `provider_ref`s in
   time order, so an injected settlement must not fall behind background ones):
   S01/S02/S06/S07 — injected activity, then background, then the case;
   S05/S08 — background, then the injected decline, then the case;
   S11 — its 3 auth/settlement pairs are the background and are published (no
   `add_entry`); no other class gains background activity.
3. Every builder opens the case **after** all activity: no state row or event
   post-dates `cases.opened_at`.
4. S06: the transposing mapper (v3) is live for the injected settlement only; the
   world records the mapper version **per published event** (`World.mapping_versions`,
   consumed by both `projection.project` and `run.materialise`), and S06 sets it back
   to 4 before background activity ("bad release, rolled back"). Background
   settlements therefore post faithfully; `integration.events.mapping_version` shows 3
   on the corrupted event and 4 on the others — the honest discriminator, not a new
   difficulty.
5. S07: the clock is advanced past the reversal before publishing, so both deliveries
   are received after their events occurred; the race itself (publish order, entries'
   `posted_at` inversion) is unchanged.
6. `World.add_entry` and `World.entries` are deleted; `ledger.entries` leaves the
   generator's `_TABLES`. Every ledger entry in the corpus is now pipeline-caused
   (completes migration step 7 for the ledger). `add_failed_delivery` (S04, S12)
   survives unchanged — out of scope, still documented in `architecture.md`.

**Invariants (tests).** For every corpus seed: each settlement in
S01/S02/S05/S06/S07/S08/S11 has exactly one pipeline ledger entry, except S02's injected
settlement (two — the defect) and S10's gap settlement (zero — the defect); S03/S04/S09/
S12 have no settlements; no state row/event post-dates its case; every delivery
`received_at ≥` its event's `occurred_at`; projection ids == live ids (existing) **and**
projection rows == live rows on amount/`posted_at`/status (new, DB-gated); no
`ledger.entries` row exists that no published event caused; S06's corrupted entry is
the only one whose amount differs from its settlement; the S07 inversion is exactly
one pair.

**Model-facing effect.** Ledger entries and webhook history now exist for background
settlements; the tool contracts, prompts, schema and evidence plan are unchanged.
Required evidence, actions and forbidden claims are unchanged in every class.

### B. S08 (and S05) amount-vs-balance semantics (generator)

**v2 defect.** `risk_hold` pins neither the declined amount nor the balance, so in 3 of
24 corpus S08 worlds the declined amount exceeds `available_balance` (dev `S08-2003007`
70 530 > 17 530; test `S08-3003007`; train `S08-1004007`), which makes the forbidden
`insufficient_funds` hypothesis data-consistent. S05 sets `available_balance = 150` and
leaves `ledger_balance` at its original draw with no holds to explain the gap.

**v3 semantics (declared).** `available_balance`/`ledger_balance` are the account's
balances at the moment the case is opened; ledger entries are the postings in the
scenario window; the world does not carry an opening balance and nothing derives
balances from entries (unchanged, now stated). Under that reading a background
purchase larger than the current balance is consistent (it was paid before the
snapshot); the injected event must be consistent with the snapshot.

**v3 change.** S08's declined amount is drawn strictly below `available_balance`
(`minor_units(rng, 500, available_balance)`) — one draw, as before, so nothing else in
the world moves for that reason. S05 sets `ledger_balance = available_balance = 150`.

**Invariants (tests).** Failing-first reproduction on seed 2003007, then for every
corpus seed: S08 declined amount < `available_balance`; S05 declined amount >
`available_balance == ledger_balance`; every account has `available_balance ==
ledger_balance` except where a builder states otherwise (none after this change).

**Model-facing effect.** S08/S05 amounts and balances; rubric untouched
(`required_evidence`, actions, forbidden claims identical).

### C. Forbidden-claim polarity (scorer)

**v2 defect.** `_asserts` looks back 80 characters only, so a refutation whose cue
follows the phrase ("insufficient funds … are all ruled out", `E4-v2-dev`
S08-2001007) counts as an assertion. Two mechanical bugs found during reconciliation
belong to the same rule: (i) `str.rfind` returns −1 for an absent boundary, so the
window is always trimmed by ≥ 2 characters and the `if cut > 0` guard is dead
(effective lookback 78); (ii) cues written with a leading space (`" not "`, `" no "`,
`" nor "`) are lost when the cue opens a sentence or a JSON field (persisted real
false positive: `E6b-G-both-dev` S05-2000004, "…no risk alerts … or system outages were
detected").

**v3 rule (documented, deterministic).** An occurrence of a forbidden phrase is
*refuted* iff a cue from `_EXCLUSION_CUES` occurs within the same sentence/field
(bounded by `_SENTENCE_BOUNDARIES`) either in the ≤ 80 characters before the phrase or
in the ≤ 80 characters after it; the sentence/field is padded with one space on both
ends so leading/trailing cues match; the boundary trim only applies when a boundary is
present. Unchanged: any single un-refuted occurrence is an assertion; hedges ("could be
a contributing factor", "is unclear") are assertions; the whole serialised
`InvestigationResult` is scanned; the cue list is not widened. `SCORER_VERSION`
becomes a recorded constant.

**Fixtures.** Assertion, negation, refutation-before, refutation-after (same
sentence), contrast, cue in the next sentence (must still assert), cue distance at the
window edge, sentence-start cue, JSON-field-start cue, underscored spelling, and a
replay of the 7 persisted forbidden hits with the expected v3 verdict recorded per
case (S08-2001007 → refuted; S08-2003007 hedge → still asserted; S05-2000004 → refuted;
genuine assertions → asserted).

### D. Idempotency-key observability (verifier)

**v2 defect.** `collect_observed_ids` harvests values under keys ending `_id` and
`provider_ref` only. `get_webhook_history` already returns `idempotency_key` to the
model, so citing the key S01 is *about* (`idem-st-2001000-03`, `E4-v2-dev`
S01-2001000) is judged a fabrication.

**v3 change.** `collect_observed_ids` also harvests non-null `idempotency_key` values.
Nothing else in the verifier changes; no new tool surface (the key was already
observable). `VERIFIER_VERSION` becomes a recorded constant.

**Tests.** First unit tests for `fis_platform/verification/verifier.py`: known-good
and known-bad fixtures for every check; the key harvested from a `get_webhook_history`
result and accepted in `entity_ids`; a key never returned still fails; DB-gated: the
fixed-evidence bundle for a built S01 world contains the key. Gold-leak: observed ids
are built from tool results only (a manifest passed as a tool result is a test-time
impossibility asserted by construction: `router_signals`/`GOLD_FEATURE_NAMES` guards
stand; a new test asserts no manifest-only field name (`root_cause`,
`required_evidence`, …) can be harvested as an observed id, and that `scenario_manifests`
stays unreadable to `fis_tools`).

### E. Suite identity, versioning and comparability (infrastructure — no benchmark semantics)

Needed for V3.2 steps 4–5 of the goal prompt, which are not satisfiable with the v2
mechanisms (`suite_version` is a literal in `run_eval.py`, persisted only in gitignored
report JSON; scenario ids are seed-deterministic so v2 score rows would silently join
v3 manifests in every analysis script).

1. `fis_platform/suite.py`: `SUITE_VERSION = "3"`, `ONTOLOGY_VERSION = "1"` (root
   causes/actions/mapping unchanged since suite v1), imported by the generator, runner,
   scorer/verifier and scripts. `SCORER_VERSION = "3"` in `evals/scorers/score.py`,
   `VERIFIER_VERSION = "3"` in the verifier. `PROMPT_VERSION` stays `"1"`.
2. Migration `006_suite_version.sql`: `ground_truth.scenario_manifests.suite_version`
   (written by the generator) and `learning.case_scores.suite_version`; backfill
   existing rows: `E2-local-96`, `E2-local-specialist-test`, `E4-claude-frontier-test`,
   `SMOKE-local-specialist-dev` → `1`, all other existing rows → `2`. `learning.*` rows
   are never deleted or rewritten otherwise.
3. Runner: refuses to run if the manifests' `suite_version` ≠ `SUITE_VERSION`
   (code/corpus mismatch); persists `suite_version` on every `case_scores` row (and on
   `<run>.weak`); refuses `--resume` into, or persisting into, a run_id whose stored
   rows carry a different suite version; records `suite_version`, scorer/verifier
   versions and `git_head` in `runtime_context`; `EvalRun.suite_version` from the
   constant.
4. `compare.py` groups by `(run_id, suite_version)`, labels every row with its suite
   and prints the non-comparability footnote whenever more than one suite is present.
   The analysis scripts (`compare_routes`, `routing_oracle`, `routing_cascade_report`,
   `model_migration_matrix`, `token_budget_delta`, `r3b_selection_rule`) refuse to
   pair runs from different suites and refuse to join a run against manifests of a
   different suite unless `--allow-cross-suite` is given (which prints the caveat).
5. Corpus identity: `scripts/corpus_digest.py` computes a canonical SHA-256 per split
   and overall over manifests + state rows + pipeline rows (excluding DB serials and
   `generated_at`; entry order by `posting_seq`); `scenarios/manifests/corpus_v3.json`
   (tracked) records suite version, digests, counts, generator plan and HEAD.
6. `make reachability` runs test **and** dev; `make corpus-digest` writes the digest;
   `make corpus-determinism` regenerates twice and compares digests.

## 3. What is NOT changing

Task ontology (root-cause set, action set, cause→action table, `CAUSE_TO_ACTION`,
`replay_webhook` distractor); every prompt variant and `DEFAULT_PROMPT = baseline`;
per-arm prompts as recorded (weak arms `cause_action_directed`, frontier `baseline`,
R4 strong stage `baseline`); the `InvestigationResult` schema and grammar path (no
property-order canonicalisation — R0.1 closed that); the tool set, its column lists
and orderings; the fixed-evidence plan (`_phase_one`/`_phase_two`, limit 6) and
evidence mode; the 0.8 recall threshold; decoding (greedy, seed 42), llama.cpp build
`b1-9b05354`, serve flags, quantizations, registry entries; `DEFAULT_MAX_TOKENS = 4096`
and the digest rule; the R4 cascade policy `verifier` and its signals; the deleted
direct-insert paths stay deleted, `add_failed_delivery` stays; `fis_tools` grants;
`learning.*` contents; every Suite v2 run row and run_id; the R3b verdict; the split
seed ranges and per-class counts (96 test / 48 dev / 144 train); TEST is not touched
before the freeze. Scenario ids are unchanged by construction (seed-derived); the
worlds behind them change, which is why suite identity is now recorded per row.

## 4. Expected invariants (release gates, deterministic)

| Gate | Check | Tooling |
|---|---|---|
| Automated tests | all pass | `make test` |
| Reachability | DEV and TEST: every class ceiling ≥ 0.8, 0 capped | `make reachability` (both splits) |
| Determinism | two full regenerations under `make corpus` give identical per-split corpus digests | `make corpus-determinism` |
| Scenario invariants | § 2A/2B invariants over every corpus seed, in memory | `tests/test_scenario_invariants.py` |
| Projection/live | ids equal (generation aborts otherwise) and row contents equal on the built corpus | `run.materialise` + DB-gated test |
| Scorer/verifier fixtures | § 2C/2D fixtures incl. persisted-hit replay | tests |
| Frontier DEV sanity | every disagreement reviewed and recorded; suite unchanged unless a defect is proven, in which case gates re-run | § 6 |

## 5. Versioning behaviour

`suite_version = 3` on every manifest and every score row written from now on; v1/v2
rows are labelled and immutable. Cross-suite comparisons are refused by default by
every tool that pairs runs. `SCORER_VERSION = 3`, `VERIFIER_VERSION = 3`,
`ONTOLOGY_VERSION = 1`, `PROMPT_VERSION = 1`, `WORKFLOW_VERSION = 1.0.0` are recorded
per run in `runtime_context`. Prior scorer states are identifiable only by suite (the
v2 polarity change happened inside suite v2 and is recorded in prose; that is why the
constant now exists).

## 6. Baseline procedure (pre-registered)

**Order.** (1) implement A–D with tests, one commit each; (2) versioning
infrastructure; (3) bump, migrate, regenerate, gates; (4) frontier DEV sanity run
`E4-v3-dev` (prompt `baseline`, CLI defaults, effort unset — the recorded frontier
configuration); (5) freeze commit + tag `suite-v3`; (6) DEV baselines; (7) analyses;
(8) TEST once per arm; (9) report.

**Frontier sanity run doubles as the frontier DEV baseline** if and only if no suite
change follows it before the freeze (the freeze commit adds only the release record).
Rationale, fixed now: the arm is non-deterministic and un-seedable, so a second run of
an identical configuration is a second sample, not a cleaner baseline; if anything in
the suite changes after the sanity run, the gates and the frontier run are repeated.

**DEV baselines (design A, as R3/R3b).** Same session per model, same order
(`ORDER BY scenario_id`), nothing else on 8082/8083, `FIS_LIVE_TESTS` unset:
`prime-local` → `V3-qwen-dev` (Qwen A) → restart Nemotron with unchanged flags, probe
with a *train* case, `prime-nemotron` → `V3-nemotron-dev` → `prime-local` →
`V3-qwen2-dev` (Qwen B). Reproducibility gate before any per-case reading: Qwen A vs B
≥ 46/48 identical output digests and ≥ 46/48 identical outcomes; otherwise stop for
diagnosis. Cascade baselines are derived by **replay** of the unchanged R4 `verifier`
policy (`routing_cascade_report.py --weak <weak> --strong E4-v3-dev`) — no new
escalation signal, no live cascade run.

**Per-arm operating configuration (system candidates, not parameter equality).**

| arm | model | quant | endpoint | max_tokens | prompt | decoding | runtime |
|---|---|---|---|---|---|---|---|
| Qwen | Qwen3-8B | Q4_K_M | 8082 direct | **4096** | `cause_action_directed` | greedy, seed 42, thinking on | llama.cpp `b1-9b05354`, `-ngl 99`, ctx 16 384 |
| Nemotron | Nemotron 3.5 Lightning 30B-A3B | IQ4_XS | 8083 direct | **8192** | `cause_action_directed` | greedy, seed 42, thinking on | same build, `--fit on --fit-target 1024 --no-mmap`, ctx 16 384, restarted + probed before its arm |
| frontier | Claude Opus 5 via CLI (`claude-frontier`) | — | CLI | CLI default (no budget passed) | `baseline` | CLI default, no seed | `--safe-mode --tools ""`, effort unset |

Reasons: Qwen completed the suite at 4096 (R3b: one budget-sensitive case) — its
lower-latency incumbent envelope; Nemotron at 4096 truncated 29/48 (R3), 8192 is the
minimum investigated envelope that removes most of it (R3b: 9 still capped); frontier
keeps its recorded configuration. These are fixed now and are not revisited after any
score is seen.

**Recorded per arm:** run id, HEAD, suite version, corpus digest, model/checkpoint,
quantization, `max_tokens`, decoding, runtime build and server session (pid/start
ticks/boot), prompt, evidence mode, schema config, scorer/verifier versions — all in
`runtime_context`/`ModelInvocation`, plus `corpus_v3.json`.

**Metrics.** Quality: strict all-pass, root-cause accuracy, act|rc, evidence recall,
verifier pass, no-output/schema failures, unsupported claims, forbidden claims.
Performance: wall p50/p95, TTFT where available, throughput, output tokens, cap hits
(`stop_reason == length`), VRAM (nvidia-smi), RSS where practical.

**Analyses (descriptive only).** Pairwise A/B/C/D matrices Qwen×Nemotron,
Qwen×frontier, Nemotron×frontier by class and failure dimension; every weak>strong
inversion harness-reviewed and recorded; R4 replay for both weak arms.

**TEST (once, after freeze and after all DEV reports).** `V3-qwen-96`,
`V3-nemotron-96` (same restart/probe/prime discipline), `E4-v3-96`; cascade arms by
replay against `E4-v3-96`. No tuning after seeing TEST.

## 7. DEV/TEST policy

DEV only during suite development and for the sanity run; TEST untouched until the
freeze tag exists; then exactly one run per frozen arm; no second look.

## 8. Method rules carried

Model-neutral construction; no prompt tuning; no model-specific scorer/rubric change;
no learned routing; no QLoRA; R4 policy unchanged; reachability after every
regeneration; deterministic generation preserved; Suite v2 artefacts preserved;
cross-suite metrics are not causal comparisons; investigate arm disagreement before
crediting or blaming a model; never widen the rubric in response to model answers;
model-facing ids separate from gold; small conceptual commits; documentation updated as
work proceeds.

## 9. Known limitations left intentionally unfixed (recorded now)

- Balances are static snapshots; nothing derives them from entries (declared, § 2B).
- `add_failed_delivery` (S04, S12) remains the one hand-authored delivery path; the
  bus has no poison-message handling.
- The scorer scans the whole serialised result, so a forbidden phrase listed bare in
  `hypotheses`/`uncertainties` without a cue counts as an assertion; hedged assertions
  count as assertions. Scoring `facts[].claim` alone is a semantics change deferred on
  purpose.
- The verifier checks `Fact.entity_ids` against observed ids, not the `<ref>` segment
  of `tool://` sources.
- The frontier CLI takes no token budget or seed and reports no runtime fingerprint;
  its input-token accounting under-reports (strong cost is a floor).
- `_phase_two`'s limit of 6 provider refs bounds which webhook histories the model
  sees in fixed-evidence mode (unchanged from v2).
