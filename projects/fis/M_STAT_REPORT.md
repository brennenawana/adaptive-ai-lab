# M-STAT Report — Methodology Enforcement in Code + Registry

> STATUS: COMPLETED MILESTONE REPORT — a completion record for the scientific
> owner (Brennen), not an autonomous gate. Executed 2026-08-21 against
> `M_STAT_IMPLEMENTATION_MAP.md` (owner-corrected 2026-08-21) under the `/goal`
> authorization recorded in `OWNER_DECISIONS.md`. Per that authorization: after
> this report, M-STAT **stops**. Nothing below performs the Suite-v4 trigger
> review, freezes or drafts R7, releases Suite v4, or runs any inference.

## 1. What M-STAT was and what ran

M-STAT's question (master plan §10): **do the corrected rules bind the runner,
not just the docs?** The answer is yes — every playbook guard named in the
implementation map is now fail-closed code with positive and negative tests.

Zero model inference. Zero TRAIN/DEV/TEST acquisition. **TEST looks consumed: 0**
(the machine ledger holds exactly the 7 seeded historical looks; next = #8, gated).
Database work was read-only except the additive migration 009 (below).

## 2. Requirement → implementation → tests matrix

| # | Requirement | Implementation | Tests (all green) |
|---|---|---|---|
| 1 | Consequence-bearing tolerances (curtailed exact counting, halt at k+1, ABORT / RECALIBRATE / PROCEED_WITH_DECLARED_CEILING) | `fis_platform/tolerances.py` (`ToleranceSpec` fail-closed at construction — RECALIBRATE requires its pre-registered procedure, PROCEED requires ceiling + cost; `ToleranceTracker` with exact k+1 crossing, ABORT structurally blocks continuation, `from_persisted` resume reconstruction); wired into `evals/runner/run_eval.py` (`--tolerance-spec`, consequence events + ledger, resume reconstruction from canonical storage; exception-metric resume refused fail-closed) | `test_mstat_tolerances.py` (26), runner integration in `test_mstat_runner.py` |
| 2 | SMOKE as a literal registry state | `fis_platform/provenance.py`: `SMOKE` state precedes the promotable path; new candidates open at SMOKE; `TRANSITIONS[SMOKE] = (REGISTERED, WITHDRAWN)` — no promotable edge; SMOKE→REGISTERED requires a 36-case (12×3, round-robin, digest-pinned) zero-violation smoke run in the ledger; `smoke` run kind exists **in addition** (ledger-line-only, TRAIN-only, SMOKE-state-only, planned_cases must be 36); smoke/diagnostic evidence refused in adoption (`train_run_ids`) and elimination (`evidence_run_ids`) payloads; `smoke_case_selection()` builds the canonical 36-case list | `test_mstat_smoke_state.py` (32), `test_r6_state_machine.py` (88) |
| 3 | Round-robin ordering | `fis_platform/ordering.py` (canonical interleave, `is_round_robin`, fail-closed id validation); runner applies it to every run; SQL `LIMIT` removed — `--limit` is now a class-balanced prefix; the class-blocked decision-prefix path **no longer exists** | `test_mstat_ordering.py` (23), runner tests |
| 4 | Cluster-robust statistics + MDE + verdicts | `fis_platform/stats.py` (stdlib-only: ICC(1), Kish DEFF, effective N, cluster-robust paired t primary, exact McNemar secondary labeled anti-conservative, closed-form MDE, CONFIRMED/REFUTED/INCONCLUSIVE/RANKED, `describe_null` refuses unregistered equivalence claims); `scripts/mstat_stats.py standing-facts` regenerates the playbook §7 facts from committed R6 TEST data → `artifacts/mstat_standing_facts.json` | `test_mstat_stats.py` (24, known-answer) |
| 5 | Machine-checkable contract validation | `fis_platform/contract_spec.py` (typed by experiment kind — INFERENTIAL / SCREENING / DIAGNOSTIC / MEASUREMENT; conditional requirements; all problems reported at once) + `scripts/contract_check.py`; `CONTRACT_FROZEN` transitions now **require** a validated spec (path + digest + candidate listed) — missing fields prevent freeze | `test_mstat_contract_spec.py` (32), freeze-hook tests in `test_r6_state_machine.py` |
| 6 | Prediction ledger | `fis_platform/predictions.py` (hash-chained append-only; frozen entries immutable — any edit breaks chain verification; predicted-vs-actual appended as separate evaluation entries, one per prediction) + `scripts/prediction_ledger.py`. No historical predictions invented | `test_mstat_predictions.py` (21) |
| 7 | TEST-look ledger, one source of truth | `fis_platform/test_looks.py` + `learning/registry/test_looks.jsonl` (hash-chained; seeded with the 7 historical looks verbatim) + `scripts/test_look_ledger.py`; runner gate for **every** arm (provider-independent — closes the frontier bypass), mirror validation against `TEST_LOOK_LEDGER.md` (divergence fails), plan-look guard (look #8 on Suite v3 refuses without an existing committed trigger-review reference), spend recorded at the first executed case; `--split` is now **required** — no silent-TEST default | `test_mstat_test_looks.py` (31), gate tests in `test_mstat_runner.py` (34) |
| 8 | Suite-refresh mechanics only | Pinned-corpus fail-closed check in the runner (live digest vs `scenarios/manifests/corpus_v3.json`); look-#8 gate above. No v4 release, no trigger verdict | runner tests; live `--check` (§5) |
| 9 | Canary mechanism, future suites only | `scenarios/generator/canary.py` (per-suite GUID; token only for suite ≥ 4 AND split=test; `activate_canary` refuses suite ≤ 3 **even with force**); one additive injection point in `run.py` (`raw_payload["canary"]`, model-observable via `get_webhook_history`), provably a no-op at SUITE_VERSION "3" | `test_mstat_canary.py` (45); live v3 digest check (§5) |
| 10 | Certainty curtailment + 3 guards | `CurtailmentPolicy` (exact integer arithmetic) in `tolerances.py`; runner `--curtail-bar` → irreversible arm stop, interval-only report `[k, k+remaining]/N` + unrun classes (no point-estimate field exists), curtailed-runs machine record; guard A holds by construction (spend at case 1); guard C: `refuse_curtailed` wired into every paired entry point (`r6_metrics` pairwise/oracle/tiers/gates-with-reference/quant-select, `compare_routes`, `model_migration_matrix`, and — post-review — `r6_analysis`, `routing_cascade_report`, `r3b_selection_rule`) | `test_mstat_firewall.py` (11, incl. the known-answer 0.0596→0.0139 flip made structurally unreachable), `test_mstat_tolerances.py`, runner tests |
| 11 | Elimination rule | Structured `WITHDRAWN` (reason_category required; `pilot_selection_loss` requires margin/n/MDE fields and refuses margin < pilot MDE quoting playbook §4; non-comparative categories — runtime_incompatibility, infrastructure_failure, owner_decision — need no MDE comparison). Historical UD withdrawal untouched (write-time-only guard; read-compat proven) | `test_r6_state_machine.py` withdrawal suite |
| 12 | `TrainedArtifact` provenance | `TrainedArtifact` record (base artifact id, dataset digest + provenance, method, hyperparameters, seeds, adapter/merged SHA — at least one required, pipeline digests, quantization, result identity, runtime lineage); `put/get_trained_artifact` with lineage validation (unregistered base/runtime refused); CLI `register-trained-artifact`. Fixtures only — nothing trained, no live record | `test_mstat_trained_artifact.py` (22) |
| 13 | pass^k protocol | `fis_platform/passk.py` (`PassKSpec`: declared frozen subset + k, `measurement_only: Literal[True]` — selection use unrepresentable; every sample must link to the one declared look run id; exact-k-per-case validation; estimator). **Not executed** — R9 runs the first measurement | `test_mstat_passk.py` |
| 14 | M0-deferred telemetry | TOOLS: dual-clock stamps on `ToolCall` (additive optional fields) + `on_event` tool_call_start/end hook in the broker, plumbed from the runner. HARNESS: config digest computed **before** run_start; event context gains config_digest / experiment_id / candidate_id / execution_system_digest / ordering. CLOCK: `clock_offset_s` per sampler line. DB: migration `009_inserted_at.sql` | `test_mstat_telemetry.py` (12; DB-gated historical-rows test runs live post-migration) |

## 3. Migrations / schema changes

One migration: `infra/migrations/009_inserted_at.sql` — for each of
`learning.{trajectories, case_scores, model_outputs, routing_decisions}`:
`ADD COLUMN IF NOT EXISTS inserted_at timestamptz` (nullable, **no default in the
ADD**) then a separate `SET DEFAULT clock_timestamp()`. Applied to the live DB;
verified post-apply: **every historical row has `inserted_at IS NULL`**
(trajectories 3231/3231, case_scores 3046/3046, model_outputs 609/609,
routing_decisions 1824/1824) — no backfill, migration time never stamped onto
history. Schema-model additions (`ToolCall.ts_realtime/ts_monotonic`) are
optional-with-None defaults, so all persisted trajectories still validate.

## 4. Backward compatibility / registry history

- The live R6 registry (`learning/registry/r6/`) is byte-untouched by M-STAT and
  still verifies (hash chains, HEAD.json). All new payload validation is
  **write-time only**: `tests/test_r6_provenance.py` (15) and
  `tests/test_m0_diagnostic_runs.py` (15) pass **unmodified**; dedicated
  read-compat tests prove that pre-SMOKE chains (first entry REGISTERED),
  reason-only WITHDRAWN entries, and spec-less CONTRACT_FROZEN entries all still
  read and transition legally.
- The literal SMOKE state raised **no historical-provenance contradiction** (the
  STOP clause was never triggered): chain verification is content-based, and all
  historical candidates sit at terminal/late states. SMOKE applies to new
  candidates prospectively.
- One M0-era call-site fix: `scripts/m0_paired_probe.py` updated to
  `load_manifests`' new signature (tooling compatibility; M0's frozen rubric,
  artifacts and results untouched).

## 5. Suite-v3 identity verification

`scripts/corpus_digest.py --check scenarios/manifests/corpus_v3.json` against the
live corpus, run with the canary mechanism present in the generator:
**DETERMINISTIC — identical to the recorded identity**
(`1e7c5278ba1f4cc1cc96fa8a1f04946ab622270eaba4c5671274c21e9d39e528`; per-split
digests all match). Canary injection is provably a no-op for suite ≤ 3 on every
split (45 unit tests incl. forced-activation refusal). Suite-v3 semantic content
and corpus identity unchanged.

## 6. Statistics acceptance target

`scripts/mstat_stats.py standing-facts` regenerates every playbook-§7 standing
fact from the committed R6 TEST record (`R6-qwen38-q3km-test` vs
`R6-bonsai-test`): ICC 0.475032 (quoted 0.475), DEFF 4.325221 (4.33), N_eff
22.195 (≈22), cluster-robust t 0.9751 df=11 (0.98 — not significant; the +13.5pp
headline confirmed non-significant cluster-robustly), pd 0.427083 (0.427),
McNemar 0.059584 (0.0596) → curtailed 0.013853 (0.0139). **Documented precision
boundary**: the quoted MDE figures were simulation-derived in the research
record; the committed closed form reproduces them within ~1–2pp and is the
mechanical definition going forward (stated in the artifact's `precision_note`
and the module docstring).

## 7. Test results

`make test`: **1023 passed, 2 skipped** (baseline before M-STAT: 672 + 2; +351
new tests, zero regressions; the two skips are the pre-existing live-inference
and corpus-live gates). Every guard has negative/misuse tests per the mission's
test plan — the full checklist is covered across `tests/test_mstat_*.py` (11 new
files) plus the updated `test_r6_state_machine.py`.

## 8. Adversarial review

An independent load-bearing reviewer (Opus, xhigh) attacked the seven mission
questions with executed bypass attempts (tmp registries/ledgers, driven refusal
paths). Baseline re-verified independently: full suite green, machine ledger
chain + mirror OK, live R6 registry byte-clean (0 problems), v3 digest match,
migration leaves 0 historical rows stamped, canary refuses suite ≤ 3 with force,
runner TEST gate provider-agnostic with spend-before-first-model-call confirmed.

Findings and dispositions:

1. **BYPASS (fixed):** the paired-comparison firewall was missing from the
   offline analysis path — `r6_analysis.py` calls `pairwise()`/oracle directly,
   and `routing_cascade_report.py` / `r3b_selection_rule.py` make paired
   discordant-cell claims. `refuse_curtailed` is now wired into all three at
   run-id resolution, with refusal-before-DB tests.
2. **Doc-stronger-than-code (fixed both ways):** the TEST-look gate lived only at
   the runner entry; scripts importing `persist()` could in principle write
   TEST rows unledgered, and offline replays are not runner-gated. Fixed: a
   fail-closed choke point inside `persist()` refuses any TEST-seed-range row
   whose run has no planned/spent look in the machine ledger (`.weak` cascade
   rows count under their base look); playbook §1 wording now states the exact
   mechanical surface (runner gate + persist choke point) and that replay looks
   bind procedurally via freeze-time planning — r5's own unlock gate is spent
   and closed.
3. **Scope gap (fixed):** contract `experiment_type` was not bound to the
   promotable path — a DIAGNOSTIC/MEASUREMENT/SCREENING spec could freeze and
   walk DEV→TEST, dodging the inferential bar. `CONTRACT_FROZEN` now requires an
   INFERENTIAL spec on this state machine's path; screening/diagnostic/
   measurement work runs under its own protocols and never freezes onto it.
4. **Scope gap (strengthened):** `owner_decision` withdrawals accepted a bare
   reason string — a below-MDE selection loss could hide under the category.
   Now requires a non-empty `authorized_by` field. Residual, accepted boundary:
   the machine does not text-scan reasons for selection language under
   non-comparative categories — the playbook explicitly licenses those
   categories, and the structured record makes misuse auditable.
5. **Minor (documented at M-STAT close; CLOSED by the 2026-08-21 closeout
   addendum, §12):** SMOKE→REGISTERED validated the ledgered 36-case round-robin
   smoke run but `smoke_violations` was operator-reported and no runner `--smoke`
   lane executed the 36 cases. Non-promotability — the load-bearing property —
   was fully enforced throughout and was never bypassable (laundering attempts
   refused on `run_kind`, not run-id strings). See §12 for the operational lane
   and the machine-derived violation count.

Verdicts after fixes: Q2/Q3/Q6 NO BYPASS; Q1/Q4 bypasses closed; Q5 strengthened
with a documented residual boundary; Q7 doc claims now match code.

## 9. Intentionally deferred / not done

1. **No Suite-v4 trigger review, verdict, or release** — owner-level, after this
   report (master plan §3; `M_STAT_IMPLEMENTATION_MAP.md` §16 preserves the
   procedure). The look-#8 gate enforces its precedence mechanically.
2. **No R7 contract drafted or frozen; no R9; no FT-rig; nothing trained**; the
   pass^k protocol and `TrainedArtifact` exist as code + fixtures only.
3. **Canary activation** deferred to the next versioned suite release.
4. **Full autopsy-§13 HARNESS row** (subagent/tests/report spans) deferred to the
   D-series; M-STAT shipped the context floor only.
5. **GPU-hours ledger automation** — remains a hand-maintained doc (adequate).
6. **Offline replay tooling** (r5-style) predates the machine-ledger gate; future
   replay-based TEST looks must plan a look before reading TEST labels — enforced
   procedurally by playbook §1 and the freeze checklist; mechanical enforcement
   covers all case execution and all canonical-storage writes (runner gate +
   persist choke point, §8 finding 2). r5's own unlock gate is spent and closed.
7. **SMOKE runner lane** — was deferred here at M-STAT close; **closed by the
   2026-08-21 closeout addendum (§12)**.
8. **No housekeeping**: dead seed placeholders (`scenarios/*_seeds.txt`), the
   stale `Makefile` `eval-smoke` target (dead against the registry since R6), and
   `r6_analysis.py`'s side-by-side descriptive tables are recorded as cleanup /
   follow-up candidates, untouched.

## 10. Blockers remaining before an R7 contract may freeze

1. **Suite-v4 trigger review** (owner): conduct and record the review; link its
   committed reference when planning look #8 (`scripts/test_look_ledger.py plan
   … --trigger-review-ref <committed file>`). The gate refuses look #8 without it.
2. **R7 contract** authored on template v2 with a machine spec
   (`fis_platform/contract_spec.py`, INFERENTIAL): tolerances with consequences,
   MDE/effective-N (compute via `fis_platform.stats`), prediction frozen in the
   prediction ledger, planned TEST look, curtailment bar, node placement,
   authoritative clocks. `CONTRACT_FROZEN` refuses without all of it.
3. **SMOKE pass** for any new candidate (new registrations open at SMOKE; R7's
   candidates from the existing registry are historical and already beyond it —
   UD-Q3_K_XL re-entry per the elimination-rule correction will need owner
   direction on registry mechanics, since UD is WITHDRAWN (terminal) and R7's
   contract must state how it re-enters selection).

## 11. Accounting

| item | value |
|---|---|
| model inference | **0 calls** (local, frontier, all) |
| TEST looks consumed | **0** (machine ledger: 7 historical, unchanged) |
| DEV/TRAIN cases executed | 0 |
| DB writes | migration 009 only (additive, nullable, no backfill) |
| registry (r5/r6) | byte-untouched; verifies |
| new files | 13 modules/scripts, 11 test files, 1 migration, machine ledger, standing-facts artifact |
| tests | 672+2 → **1023 passed + 2 skipped** |

## 12. Closeout addendum (2026-08-21, post-commit `67a2647`): SMOKE operational lane

The one operational residual from §8 finding 5 is closed. This addendum is a
separate, dated closeout — the original M-STAT commit did not contain it.

**Sanctioned runner lane.** `run_eval --smoke` (requires `--candidate`; the
candidate must be at state SMOKE; `--split train` only — DEV/TEST refused;
`--limit`, `--scenario-ids-file`, `--escalate-to`, `--tolerance-spec`,
`--curtail-bar` all refused so the canonical population cannot be substituted,
subset, cascaded, or wrapped). The runner selects the canonical 36 TRAIN cases
via `smoke_case_selection` (first 3 per class, round-robin order), pins them
with `smoke_case_digest`, runs under the existing `smoke` run kind
(ledger-line-only, planned_cases must be 36), and leaves the candidate at SMOKE
— the transition is a separate, explicit registry act.

**Machine-derived violations** (`smoke-violation-rule-v1`, frozen in
`fis_platform/provenance.py` before any live validation; digested): per scored
case, a violation iff (a) any tool call has status ≠ success (under
FIXED_EVIDENCE the tool sequence is harness-chosen, so non-success is
harness/protocol breakage), or (b) the trajectory has zero model invocations
(gateway breakage). Task failures, cap-hits, and wrong answers are deliberately
NOT violations — SMOKE is breakage detection, not a quality benchmark. A case
that raises never persists a score, so an excepted run fails the completeness
gate rather than being counted.

**Evidence + gate.** At 36/36 scored, the runner writes a per-run smoke result
record (`candidates/<cid>/smoke/<run_id>.json` — candidate/run/split/suite/
corpus digest, ordered case ids + selection digest, rule identity/digest,
per-case `tool_call_statuses`/`n_model_invocations`/trace ids/derived flags,
total, eligibility) and binds its digest into the smoke run's end ledger line.
SMOKE→REGISTERED now loads that record, verifies the ledger digest binding,
**recomputes every per-case flag from the raw statuses**, and requires
payload `smoke_violations` == recomputed == 0 — a caller-claimed zero cannot
override the persisted evidence (`test_gate_refuses_payload_zero_when_the_
persisted_result_derives_one`). `scripts/r6_registry.py smoke-eligibility`
derives the transition payload from the record; it never invents one.

**Verification.** Focused suite 197 passed; full suite **1064 passed + 2
skipped** (from 1023+2 at M-STAT close; +41 lane tests). Live TRAIN inference
was **skipped deliberately**: every registered candidate is beyond SMOKE, and a
disposable candidate would permanently contaminate the append-only live
registry — fixtures exercise the lane end-to-end through the real APIs instead.
TEST looks remain **7**; Suite-v3 digest re-verified unchanged; live registry
verifies read-only; historical chains unaffected (write-time-only gate on an
edge no historical chain takes). A bounded adversarial re-check of the six
fabrication/laundering/override/consumption questions ran before commit:
NO BYPASS on override/adoption/elimination/DEV-TEST/history; one hardening it
surfaced was applied (every smoke end ledger line carrying a
`smoke_result_digest` must agree — a re-appended, sum-neutral end line can no
longer re-bind the result file); the two remaining items are the documented
boundaries below.

**Residual, stated:** fabricating a full smoke pass would require hand-writing
the result record AND its ledger binding — the same trust boundary as
hand-writing `dev_result.json` plus ledger lines in the pre-existing
architecture, backstopped by the committed-tree and append-only-vs-git rules;
no new weaker path was introduced. The structural gate pins population shape
(36 ids, 12×3, canonical round-robin, digest-bound); pinning to the exact
corpus-canonical id set at transition time would need DB access inside the
file-based registry and is deliberately left to the runner (the only sanctioned
writer), documented here.
