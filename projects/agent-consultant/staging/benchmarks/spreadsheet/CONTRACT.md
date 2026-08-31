# Experiment Contract — Spreadsheet Skill Evolution (v1, FROZEN)

> **What this is.** The actual pre-registration used for the experiment in
> `REPORT.md`, frozen in a private repository (commit `2da2ff9`) on 2026-08-30 —
> before any training run started. It is published here so readers can see what
> "the rules were written before the data" looks like when filled in for real.
> Edits for publication: private project names and file paths were replaced or
> described generically, and a code legend was added at the end. Every value,
> rule, threshold, and amendment is unchanged.
>
> Format: 18 sections. After the freeze commit, nothing above §18 changes;
> corrections are appended to §18 only. File paths below (`rig/…`, `runs/…`)
> refer to the private rig the experiment ran in; the public port of that code
> is this repository's engine.

## 1. Question and scope

- Question: with a cheap executor (Claude Haiku 4.5) inside the rollout loop
  and a frontier maintainer/proposer (Claude Opus 5), do evolved skills raise
  the executor's held-out test score significantly above its no-skill baseline —
  and do they match or beat skills evolved entirely by the cheap model, at
  comparable cost?
- Decision this answer drives: whether to build further machinery on this loop.
- Prediction register (written before data; drafted from the paper's
  small-model results; the owner could replace these values through §18 at any
  time before training started):
  - Arm C − Arm A on test: point estimate +8 points; 90% interval 0 to +16.
  - Arm C − Arm B on test: point estimate +3 points; 90% interval −3 to +9.
- Non-goals: skill retrieval/triggering; more than two model tiers; changing
  the harness prompts mid-run.

## 2. Frozen scientific baseline

- Task-suite manifest SHA-256:
  `2f3a4d7149125e67c272734732a8685d8e9f564f7f1627fc5a607f7e99a5e1d2`
  (draw seed 20260830): 30 train / 15 validation / 100 test + 3 smoke tasks.
  Each split is drawn from inside the matching split of microsoft/SkillOpt's
  published `spreadsheetbench_id_split` (80/40/280 over the same Verified-400
  file — the split the WikiSkill paper reports matching). Filter: the answer
  file must match itself, and the input file must not match the answer, on
  every available test case. 4 tasks were excluded; the manifest lists them.
- Dataset: `spreadsheetbench_verified_400.tar.gz`, SHA-256
  `10ef893d…c03fc949` (full value pinned in the rig's config). 395 of 400 tasks
  have exactly one init/golden test-case pair. Score per task = fraction of its
  available test cases passed (the upstream "soft" metric; 0 or 1 for
  single-case tasks).
- Scorer: upstream `evaluation.py::compare_workbooks` at commit
  `49b73a94775fb489063f60ca1865e3a650079a79`, imported from a local cache at
  run time (upstream has no license file, so its code and data are never
  copied into any repository of ours).
- Task-family system prompt: word-for-word from WikiSkill Appendix E.1, bound
  by the freeze commit.

## 3. Artifacts

- Models: `claude-haiku-4-5` (executor, all arms; also optimizer for arm B),
  `claude-opus-5` (optimizer, arm C). Provider model snapshots cannot be
  pinned; the canonical model id from each call's usage report is stored per
  ledger row. No local weights.

## 4. Runtimes (execution-system identity)

- Model gateway: Claude Code CLI on subscription login, version 2.1.251
  (pinned). Flags (validated in earlier private work): `--safe-mode
  --disable-slash-commands --strict-mcp-config --no-session-persistence
  --system-prompt <role prompt> --tools <role tools> --model <id>`. The
  executor adds `--tools Bash --max-turns 15 --permission-mode
  bypassPermissions` with `BASH_MAX_TIMEOUT_MS=90000`. The proposer adds
  `--tools Read --max-turns 25`. Maintainer and proposer use `--json-schema`.
  `--bare` is forbidden (it turns off subscription login).
- Rig: bound by the freeze commit. Python 3.12.8; `pandas==2.2.0`,
  `openpyxl==3.1.3` (both matching upstream's pins). Single machine, operator
  present for the pilot.
- Executor isolation: each test case runs in its own working directory
  containing only a copy of the input file; 90 seconds per bash command; 15
  turns per conversation. Answer files never enter any working directory or
  prompt (§14).

## 5. Split protocol

- 30 train / 15 validation / 100 test, ids fixed by the manifest.
- Test-look ledger: exactly one test evaluation per arm-seed. Planned looks,
  seeded into the ledger at freeze: A-s1, B-s1, B-s2, B-s3, C-s1, C-s2, C-s3
  (7 total). Any additional look triggers S11: the affected comparison is
  downgraded to INCONCLUSIVE. The ledger is append-only. (The as-run ledger is
  `results/test_looks.jsonl` in this folder: 7 planned, 7 spent.)

## 6. Calibration rules — every tolerance names its consequence

| Parameter | Value | Tolerance | Consequence on breach |
|---|---|---|---|
| Executor turn cap / command timeout | 15 turns / 90 s | rollout failure rate ≤ 20% per iteration | S9: halt and diagnose (a rig defect is not evidence) |
| Iteration spend projection | arm B $2.30, arm C $3.00 (from smoke measurements) | ≤ 1.5× projection per iteration | S2: STOPPED-BUDGET(iteration), checkpoint, human note to resume |
| Arm-run spend | A $5 / B $25 / C $45 | hard | S3: STOPPED-BUDGET(run) |
| Phase spend | pilot $100 / extension $200 | hard | S4: phase halt; owner note to resume |
| Program ceiling | $600 | hard | S5: full stop; raising it is an owner amendment in §18 |

All amounts are list-price-equivalent USD (subscription billing; see §15).

## 7. Candidate selection rules (train split only)

- Accept a skill proposal only if the validation score strictly exceeds the
  best validation score so far (WikiSkill Eq. 4). The wiki is never rolled
  back. One atomic proposal per iteration.
- Early stop inside a run: validation = 100%, or 3 consecutive iterations
  without an accepted proposal (S8, EARLY-PLATEAU — a declared deviation from
  the paper's fixed K = 8).

## 8. Eligibility / feasibility probes

- Smoke precondition: met on 2026-08-30 — full loop, all four roles, zero
  harness errors on the final attempt, $1.02 equivalent.
- S6 headroom check: arm-A validation score must fall inside [15%, 60%] before
  any evolution spend. Outside the band → STOP-RESCOPE (redraw or re-scope the
  task suite under a new contract).

## 9. Statistical plan (pre-registered)

- Primary: arm C vs arm A on test. Paired bootstrap over tasks: 1,000
  resamples, one-sided, α = 0.05. Per-task score for an evolved arm = mean over
  its 3 seeds (arm A is a single fixed configuration, evaluated once).
- Effect floor: +5 points. Below this, the machinery is not worth its
  complexity.
- Secondary (ranked, not confirmatory): C vs B vs A on accuracy and on
  cost-per-completed-task (arm spend ÷ test tasks solved).
- Verdict readings, written before data:
  - CONFIRMED: p < .05 AND the point estimate ≥ +5 → build on the machinery;
    the follow-up report becomes citable evidence.
  - REFUTED: point estimate ≤ 0, or the 95% interval's upper bound < +5 →
    skill evolution is not worth it on this suite at this tier; record the
    result; do not build further.
  - INCONCLUSIVE: everything else, including every STOPPED-BUDGET outcome. A
    budget stop is a finding about cost, reported as such; the budget is never
    quietly raised.

## 10. Generation configuration per arm

- All generation settings are the CLI's defaults for the given model, fixed by
  the CLI version pin. Identical across arms except the optimizer model.
- Declared deviation D4: the proposer's `read_file` and `finish` tools are
  served by the CLI Read tool plus a schema-forced final JSON answer; a
  `traces/` link keeps the paper's `traces/<task_id>` paths valid. All system
  prompts otherwise word-for-word; the proposer's has a short tool-mapping note
  appended.

## 11. Qualification gates (before test)

- A run reaches the test set only if: it completed or stopped at EARLY-PLATEAU
  within caps; its ledger is complete; and no S9/S10 event is open.

## 12. Test protocol

- One look per arm-seed, appended to the look ledger before the evaluation
  starts. No one — human or agent — inspects per-task test results before the
  verdict computation runs.

## 13. State machine

- BUILT → SMOKED → FROZEN → BASELINED → PILOT → EXTENDED → VERDICT. Budget or
  integrity halts move to STOPPED-*; leaving a STOPPED state requires a §18
  note.

## 14. Integrity controls

- The meter checks caps BEFORE each call and can never undercount (§15).
- The rig runs from a committed tree; the freeze commit binds all code and
  prompts.
- Ground-truth isolation: only the scorer module reads answer files.
- The ledger and the wiki's `skill-impact.md` are written by the harness only.

## 15. Telemetry

- Per CLI call, one ledger row: role, model, attributed tokens (usage entries
  matching the model under test), turn count, error flag, and two cost figures —
  ours and the CLI's own.
- Authoritative spend per call = the highest of: the sum of every usage entry's
  list-basis cost, the CLI's reported total, and our own computation from
  pinned list prices (Haiku $1/$5, Opus $5/$25 per Mtok in/out; cache writes
  1.25×, cache reads 0.10× input price). This "take the highest" rule exists
  because a single-entry reading undercounted by ~30× during smoke.

## 16. Analysis plan (offline, after test)

- Tables: per-arm accuracy (validation trajectory and test), acceptance
  history, spend by role and by arm.
- Economics: cost-per-completed-task per arm; how the one-time evolution cost
  compares against paying for a frontier executor on every task, at the pinned
  list prices.
- Qualitative skill review: a human reads every accepted skill and classifies
  it as a general procedure or a model-specific workaround (the
  negative-transfer screen).
- Iteration spend projections for S2 (from smoke): arm B $2.30, arm C $3.00.

## 17. Roles

- Scientific owner: Brennen Awana. Interprets results; authorizes resumes,
  ceiling changes, and prediction-register replacement (all via §18).
- Executor of the contract: agent sessions running the rig. They follow the
  written rules and do not change them during a run.

## 18. Amendment log (append-only after freeze)

- **Amendment 1 (2026-08-30, owner-authorized).** Measured cost is ~1.9× the
  projections the §6 caps were sized from ($0.057 per test task vs $0.03
  projected). The owner instructed: "raise the cap to whatever you think allows
  everything to run, it's okay to overshoot" (subscription billing; completion
  matters more than the equivalents). New values, all still enforced
  fail-closed:
  - Arm-run caps: A $5 → $15 · B $25 → $50 · C $45 → $90
  - Iteration projections (S2 basis): B $2.30 → $4.50 · C $3.00 → $6.00
  - Phase caps: pilot $100 → $200 · extension $200 → $400
  - Program ceiling (S5): $600 → $1,000
  Also recorded: attempt 1 of test look A-s1 stopped at 43/100 tasks with no
  result file produced and no per-task score seen by anyone; it continues as
  the same look. Evaluation runs are checkpointed per task from this date, and
  nobody reads the checkpoint file's per-task scores before the verdict
  computation (§12).
- **Amendment 2 (2026-08-30, owner-authorized).** The owner authorized parallel
  execution of independent flows ("we can use this opportunity to run parallel
  runs wherever it makes sense … raise the limit to 20"), after confirming run
  isolation (fresh CLI process per call, `--safe-mode`,
  `--no-session-persistence`, per-run workspaces, seeds start from an empty
  wiki and empty skills). Changes:
  - Rollout worker ceiling raised 3 → 20 per flow; concurrent flows split it so
    the machine runs ~20–30 CLI processes at once. Worker counts do not differ
    between arms within a comparison.
  - Seed-extension runs (B-s2, B-s3, C-s2, C-s3) start before the S7 futility
    gate resolves (C-s1 still running). Risk accepted by the owner: if S7 later
    reads futile, the extension spend was wasted. Rationale: subscription
    window economics; B-s1's validation result makes futility unlikely.
  - Gateway retries transport/overload failures only (HTTP 429/5xx, up to 3
    attempts): a rate-limited call is not evidence about the model. Task-level
    results are never retried.
  - The shared spend file now uses a file lock. The still-running C-s1 process
    predates the lock, so cross-process totals may drift slightly until it
    finishes; per-run ledgers are append-only and authoritative, and the spend
    summary is recomputed from them at close. (It was: see
    `results/spend.json`, `"reconciled_from_ledgers": true`.)

---

### Stop-rule codes used above (legend added for public reading)

| Code | Meaning |
|---|---|
| S2 | Iteration spend beyond 1.5× its projection → stop, checkpoint, human note to resume |
| S3 | Arm-run spend cap hit → stop the run |
| S4 | Phase spend cap hit → halt the phase; owner note to resume |
| S5 | Program ceiling hit → full stop; only an owner amendment can raise it |
| S6 | Headroom check: the no-skill baseline must score 15–60% on validation before any evolution spend |
| S7 | Futility gate: pilot results decide whether extension seeds are worth running |
| S8 | Early plateau: 3 consecutive iterations without an accepted skill → stop the run |
| S9 | Rollout failure rate above 20% in an iteration → halt and diagnose (a rig defect is not evidence) |
| S10 | Integrity incident (ledger gap, isolation breach) → halt until resolved |
| S11 | Any test-set look beyond the planned one per arm-seed → the affected comparison is downgraded to INCONCLUSIVE |

### Freeze checklist (as recorded at freeze)

- [x] Task-suite manifest hashed; scorer verified on samples; smoke recorded (§2, §8)
- [x] Forced-overrun budget test passed — the meter halts before spending (§6, §14)
- [x] Every tolerance names a consequence (§6)
- [x] Prediction register filled; verdict readings written before data (§1, §9)
- [x] Test-look ledger seeded with the 7 planned looks (§5)
- [x] Rates recorded; metering rule set to "take the highest" (§15)
- [x] Freeze commit made and the file's blob hash recorded alongside the run ledgers
