# SE-1 Experiment Contract — v1 (FROZEN at first commit)

> STATUS: FROZEN when this file lands in the repository's first commit for this
> project. Derives from the generic `playbook/templates/EXPERIMENT_CONTRACT.md`
> apparatus (18 sections). After the freeze commit, nothing above §18 changes;
> corrections are appended to §18 only. The freeze commit hash and this file's git
> blob hash are recorded in `runs/CONTRACT_BINDING.json` immediately after the
> commit. Language follows the lab standard: plain English, no idioms.

## 1. Question and scope
- Question: with a cheap executor (Claude Haiku 4.5) inside the rollout loop and a
  frontier maintainer/proposer (Claude Opus 5), do evolved skills raise the executor's
  held-out TEST score significantly above its no-skill baseline — and do they match or
  beat skills evolved entirely by the cheap model, at comparable cost?
- Decision this answer drives: whether the lab builds skill-evolution machinery beyond
  this MVP (Phase 3 gate; later playbook adjudication).
- Prediction register (written before data; drafted by Claude from the paper's
  small-model results; the owner may replace these values through §18 at any time
  before training starts):
  - Arm C − Arm A on TEST: point estimate +8 points; 90% interval 0 to +16.
  - Arm C − Arm B on TEST: point estimate +3 points; 90% interval −3 to +9.
- Non-goals: skill retrieval/triggering; more than two model tiers; changing the
  harness prompts mid-run.

## 2. Frozen scientific baseline
- Task-suite manifest SHA-256:
  `2f3a4d7149125e67c272734732a8685d8e9f564f7f1627fc5a607f7e99a5e1d2`
  (`tasks/manifest.json`, seed 20260830): 30 train / 15 val / 100 test + 3 smoke
  tasks. Each split is drawn from inside the matching split of microsoft/SkillOpt's
  published `spreadsheetbench_id_split` (80/40/280 over the same Verified-400 file —
  the split the WikiSkill paper reports matching). Filter: the answer file must match
  itself, and the input file must not match the answer, on every available test case.
  4 tasks were excluded; the manifest lists them.
- Dataset: `spreadsheetbench_verified_400.tar.gz`, SHA-256 `10ef893d…c03fc949` (full
  value pinned in `rig/config.py`). 395 of 400 tasks have exactly one init/golden
  test-case pair. Score per task = fraction of its available test cases passed
  (the upstream "soft" metric; 0 or 1 for single-case tasks).
- Scorer: upstream `evaluation.py::compare_workbooks` at commit
  `49b73a94775fb489063f60ca1865e3a650079a79`, imported from the local cache at run
  time (upstream has no license file, so its code and data are never copied into this
  repository). Adapter: `rig/scorer.py`, bound by the freeze commit.
- Task-family system prompt: word-for-word from WikiSkill Appendix E.1
  (`rig/prompts.py`), bound by the freeze commit.

## 3. Artifacts
- Models: `claude-haiku-4-5` (executor, all arms; also optimizer for arm B),
  `claude-opus-5` (optimizer, arm C). Provider model snapshots cannot be pinned;
  the canonical model id from each call's usage report is stored per ledger row.
  No local weights.

## 4. Runtimes (execution-system identity)
- Model gateway: Claude Code CLI on subscription login, version 2.1.251 (pinned).
  Flags (validated in FIS): `--safe-mode --disable-slash-commands --strict-mcp-config
  --no-session-persistence --system-prompt <role prompt> --tools <role tools>
  --model <id>`. Executor adds `--tools Bash --max-turns 15 --permission-mode
  bypassPermissions` with `BASH_MAX_TIMEOUT_MS=90000`. Proposer adds `--tools Read
  --max-turns 25`. Maintainer and proposer use `--json-schema`. `--bare` is forbidden
  (it turns off subscription login).
- Rig: bound by the freeze commit (see `runs/CONTRACT_BINDING.json`). Python 3.12.8;
  `pandas==2.2.0`, `openpyxl==3.1.3` (both matching upstream's pins). Single machine,
  operator present for the pilot; unattended runs require the upstream Docker sandbox
  (decision D2).
- Executor isolation: each test case runs in its own working directory containing only
  a copy of the input file; 90 seconds per bash command; 15 turns per conversation.
  Answer files never enter any working directory or prompt (§14).

## 5. Split protocol
- 30 train / 15 val / 100 test, ids fixed by the manifest.
- TEST-look ledger: exactly one TEST evaluation per arm-seed. Planned looks, seeded
  into `runs/test_looks.jsonl` at freeze: A-s1 (1), B-s1, B-s2, B-s3, C-s1, C-s2,
  C-s3 (7 total). Any additional look triggers S11: the affected comparison is
  downgraded to INCONCLUSIVE. The ledger is append-only.

## 6. Calibration rules — every tolerance names its consequence

| Parameter | Value | Tolerance | Consequence on breach |
|---|---|---|---|
| Executor turn cap / command timeout | 15 turns / 90 s | rollout failure rate ≤ 20% per iteration | S9: halt and diagnose (a rig defect is not evidence) |
| Iteration spend projection | arm B $2.30, arm C $3.00 (from smoke measurements) | ≤ 1.5× projection per iteration | S2: STOPPED-BUDGET(iteration), checkpoint, human note to resume |
| Arm-run spend | A $5 / B $25 / C $45 | hard | S3: STOPPED-BUDGET(run) |
| Phase spend | P1 $100 / P2 $200 | hard | S4: phase halt; owner note to resume |
| Program ceiling | $600 | hard | S5: full stop; raising it is an owner amendment in §18 |

All amounts are list-price-equivalent USD (subscription billing; see §15).

## 7. Candidate selection rules (TRAIN only)
- Accept a skill proposal only if the VAL score strictly exceeds the best VAL score so
  far (WikiSkill Eq. 4). The wiki is never rolled back. One atomic proposal per
  iteration.
- Early stop inside a run: VAL = 100%, or 3 consecutive iterations without an accepted
  proposal (S8, EARLY-PLATEAU — a declared deviation from the paper's fixed K = 8).

## 8. Eligibility / feasibility probes
- SMOKE precondition: met on 2026-08-30 — full loop, all four roles, zero harness
  errors on the final attempt, $1.02 equivalent.
- S6 headroom check: arm-A VAL score must fall inside [15%, 60%] before any evolution
  spend. Outside the band → STOP-RESCOPE (redraw or re-scope the task suite under a
  new contract).

## 9. Statistical plan (pre-registered)
- Primary: arm C vs arm A on TEST. Paired bootstrap over tasks: 1,000 resamples,
  one-sided, α = 0.05. Per-task score for an evolved arm = mean over its 3 seeds
  (arm A is a single fixed configuration, evaluated once).
- Effect floor: +5 points. Below this, the machinery is not worth its complexity.
- Secondary (RANKED, not confirmatory): C vs B vs A on accuracy and on
  cost-per-completed-task (arm spend ÷ TEST tasks solved).
- Verdict readings, written before data:
  - CONFIRMED: p < .05 AND the point estimate ≥ +5 → build Phase 3; the follow-up
    report becomes a candidate EVIDENCE_MAP row.
  - REFUTED: point estimate ≤ 0, or the 95% interval's upper bound < +5 → skill
    evolution is not worth it on this suite at this tier; record; no Phase 3.
  - INCONCLUSIVE: everything else, including every STOPPED-BUDGET outcome. A budget
    stop is a finding about cost, reported as such; the budget is never quietly raised.

## 10. Generation configuration per arm
- All generation settings are the CLI's defaults for the given model, fixed by the CLI
  version pin. Identical across arms except the optimizer model.
- Declared deviation D4: the proposer's `read_file` and `finish` tools are served by
  the CLI Read tool plus a schema-forced final JSON answer; a `traces/` link keeps the
  paper's `traces/<task_id>` paths valid. All system prompts otherwise word-for-word
  (`rig/prompts.py`); the proposer's has a short tool-mapping note appended.

## 11. Qualification gates (before TEST)
- A run reaches TEST only if: it completed or stopped at EARLY-PLATEAU within caps;
  its ledger is complete; and no S9/S10 event is open.

## 12. TEST protocol
- One look per arm-seed, appended to the look ledger before the evaluation starts.
  No one — human or agent — inspects per-task TEST results before the verdict
  computation runs.

## 13. State machine
- BUILT → SMOKED → FROZEN → BASELINED → PILOT → EXTENDED → VERDICT. Budget or
  integrity halts move to STOPPED-*; leaving a STOPPED state requires a §18 note.

## 14. Integrity controls
- The meter checks caps BEFORE each call and can never undercount (§15).
- The rig runs from a committed tree; the freeze commit binds all code and prompts.
- Ground-truth isolation: only `rig/scorer.py` reads answer files.
- The ledger and the wiki's `skill-impact.md` are written by the harness only.

## 15. Telemetry
- Per CLI call, one ledger row: role, model, attributed tokens (usage entries matching
  the model under test), turn count, error flag, and two cost figures — ours and the
  CLI's own.
- Authoritative spend per call = the highest of: the sum of every usage entry's
  list-basis cost, the CLI's reported total, and our own computation from pinned list
  prices (Haiku $1/$5, Opus $5/$25 per Mtok in/out; cache writes 1.25×, cache reads
  0.10× input price). This "take the highest" rule exists because a single-entry
  reading undercounted by ~30× during smoke.

## 16. Analysis plan (offline, after TEST)
- Tables: per-arm accuracy (VAL trajectory and TEST), acceptance history, spend by
  role and by arm.
- Economics: cost-per-completed-task per arm; amortization of evolution cost against
  a frontier-executor alternative at the pinned list prices.
- Qualitative skill review: a human reads every accepted skill and classifies it as a
  general procedure or a Haiku-specific workaround (the negative-transfer screen).
- Iteration spend projections for S2 (from smoke): arm B $2.30, arm C $3.00.

## 17. Roles
- Scientific owner: Brennen Awana. Interprets results; authorizes resumes, ceiling
  changes, and prediction-register replacement (all via §18).
- Executor of the contract: Claude sessions running the rig. They follow the written
  rules and do not change them during a run.

## 18. Amendment log (append-only after freeze)
- (empty)

---
### Freeze checklist
- [x] Task-suite manifest hashed; scorer verified on samples; SMOKE recorded (§2, §8)
- [x] Forced-overrun budget test passed — the meter halts before spending (§6, §14)
- [x] Every tolerance names a consequence (§6)
- [x] Prediction register filled; verdict readings written before data (§1, §9)
- [x] TEST-look ledger seeded with the 7 planned looks (§5)
- [x] Rates recorded; metering rule set to "take the highest" (§15)
- [ ] Freeze commit made and blob hash recorded in `runs/CONTRACT_BINDING.json`
      (this box is checked by the commit that lands this file)
