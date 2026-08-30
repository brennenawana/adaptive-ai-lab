# Skill-Evolution MVP — Game Plan

Date: 2026-08-30 · Owner: Brennen Awana · Drafted by: Claude (Fable 5)
Grounding: `research/2026-08-30_WikiSkill_LLM_Wiki_Autoresearch.html` §8 (all evidence
citations live there; this plan cites it by anchor as `report#…`).

---

## 1. The question

**H1:** With a cheap executor in the rollout loop (Claude Haiku 4.5) and a frontier
maintainer/proposer (Claude Opus 5), evolved skills lift the executor's held-out accuracy
significantly over its no-skill baseline — and match or beat fully-self-evolved skills at
comparable evolution cost. This is the cell the WikiSkill paper left empty
(`report#economics`): its cross-model results transplant *finished* skills; nobody has run
the mixed configuration natively, where executor-in-the-loop rollouts guard against the
workaround-encoding failure that produced negative transfer (`report#claim-negative-transfer`).

Three arms, one task suite, identical harness:

| Arm | Executor (rollouts + test) | Wiki Maintainer + Skill Proposer | Answers |
|---|---|---|---|
| A | Haiku 4.5, no skills | — (no evolution) | the baseline |
| B | Haiku 4.5 | Haiku 4.5 | does the loop work at the cheap tier at all? |
| C | Haiku 4.5 | Opus 5 | **H1** — is discovery intelligence what you pay for? |

Each arm reports accuracy **and** cost-per-completed-task; the economic claim is a ratio.

### The client work pattern this MVP practices

The playbook's primary use is client engagements: a client shows us their current
process and their AI implementation of it; we prove, at small scale and fixed cost, how
we would improve it. This MVP is a small practice run of that work pattern, with one
step replaced:

| Client engagement | This MVP (Phases 0–2) |
|---|---|
| The client's recurring task family | 145 real spreadsheet tasks from real users (SpreadsheetBench is built from Excel-forum problems — messy, multi-table, genuinely client-shaped) |
| Their current / naive AI implementation | Arm A: the bare cheap-model baseline |
| "Prove it small before we commit" | Frozen small task suite, capped spend, pre-registered verdict |
| The deliverable they can inspect | The evolved skill pack + PURPOSE.md audit trail — plain text: client-readable, model-portable, diffable, rollbackable |
| The number they buy on | Accuracy delta + cost-per-completed-task |
| Building the trusted eval from an undocumented process | **Replaced: the benchmark supplies answer keys.** In a real engagement this is the first and usually largest work item (P1) |

Phases 0–2 validate the improvement machine on borrowed answer keys. Phase 3 (millwork
— a real prospective client) practices the full work pattern including the replaced
step: build answer keys from the client's own documents, then run the same machine. If
both hold, the lab has a repeatable client offer: "give us ~100 graded examples of the
task; we baseline your setup, evolve a skill pack against your own examples, and hand
you an auditable before/after with its economics." The S6 baseline band is the
mechanical form of the client-qualification screen: is this task family procedural,
verifiable, and does it have headroom (room to improve)?

### Reference hierarchy

Authority differs by layer; each source is normative only where stated:

| Layer | Primary | Secondary | Tertiary |
|---|---|---|---|
| This rig (mechanism) | WikiSkill paper — normative: where it specifies a mechanism we copy it exactly; deviations are declared in the contract | LLM Wiki gist — design language and scale-up options; informative only | autoresearch — validation shape (small, cheap, gated); no mechanism content |
| The playbook (doctrine) | Our own executed contracts (project evidence) | External research incl. WikiSkill (corroboration) | Gists, community practice (background) |
| A client engagement | The client's tasks and data (ground truth) | The playbook (method) | The research (the method's citations) |

The inversion between rows is by design (the promotion path): research is primary for a
replication, secondary for doctrine, and background inside an engagement, where the
client's own data governs.

Non-goals: skill retrieval/triggering (full prompt injection, matching the paper's
control, `report#ws-what-is-a-skill`); production integration; any playbook change (that
requires the follow-up report + adjudication, `report#pb-position`).

## 2. Readiness assessment (2026-08-30)

**Verified ready:**
- Evidence base and design skeleton: the reviewed research report (285 paper-table cells
  verified byte-identical; design at `report#mvp`).
- Task source exists and is usable: `RUCKBReasoning/SpreadsheetBench` (NeurIPS 2024,
  spotlight) — 912 real-forum tasks, fully released (`data/all_data_912.tar.gz`),
  OJ-style checkers with ~3 input/answer test-case files per instruction, JSONL schema
  identical to the fields the WikiSkill inference prompt uses (instruction,
  spreadsheet_path, instruction_type, answer_position). A 400-instance expert-verified
  subset ("SpreadsheetBench Verified", 2025-12) exists on HuggingFace; notably the
  paper's splits (80/40/280) sum to exactly 400.
- Lab machinery to reuse: `projects/fis/EXPERIMENT_CONTRACT_TEMPLATE.md` (18-section
  apparatus; the generic `playbook/templates/EXPERIMENT_CONTRACT.md` is our base),
  `projects/fis/fis_platform/stats.py` (`mde_pp`, `verdict()`, four-valued vocabulary),
  the test-look-ledger pattern.
- Model access + prices: Haiku 4.5 $1/$5, Opus 5 $5/$25 per Mtok (first-party rates;
  re-verify at contract freeze).

**Not ready (gaps this plan closes, in order):**
1. No rig exists (Phase 0 builds it).
2. Task suite not drawn/frozen (Phase 0; includes checker verification and a license check —
   the SpreadsheetBench repo carries **no LICENSE file**; treat as research-use, never
   redistribute: data is fetched at run time and stays out of our git).
3. Contract not frozen; thresholds, caps, and stop rules below are **pre-registered
   defaults** that bind only at the freeze commit.
4. Budget enforcement does not exist anywhere in the lab yet (Phase 0 builds the meter;
   §7 proposes it as standing doctrine).

## 3. Structure decision: in-repo, not a separate repo

**Decision: `projects/skill-evolution-mvp/` in `adaptive-ai-lab`.** Rationale:
- The promotion path requires project evidence to live with the project; a future
  EVIDENCE_MAP row cites `projects/<name>/…` artifacts.
- Direct reuse of the contract apparatus, stats conventions, and ledger patterns —
  copying them into a fresh repo would fork the method the experiment exists to validate.
- The playbook's 1.0 gate wants instantiations carried through frozen contracts using
  only the playbook; this becomes a third, deliberately tiny instantiation.
- Karpathy's autoresearch is a separate repo because it is a public demo. Ours is lab
  evidence. **Revisit trigger:** if we later open-source the rig, extract `rig/` to its
  own repo at that point; nothing in this layout blocks that.

**Artifact policy (keeps the repo light — the wholesaling-cassette lesson):**
- Committed: `runs/<run-id>/ledger.jsonl` (every proposal: diff, val score, accept/reject,
  spend), final `wiki/` snapshot, accepted `skills/`, `summary.json`, the contract.
- Gitignored: raw traces (`runs/**/raw/`), fetched benchmark data, tempdirs. Traces are
  tarred per run and kept locally; retention noted in each run's summary.

## 4. Architecture

```
projects/skill-evolution-mvp/
  PLAN.md  CONTRACT_DRAFT.md  README.md
  rig/
    run.py         orchestrator: evolution loop, gating, resume-safe state
    executor.py    inference agent: plain Anthropic API tool loop (bash tool),
                   skills injected verbatim into the system prompt
    maintainer.py  wiki maintainer: one call/iteration, JSON patch-ops output
    proposer.py    skill proposer: ReAct loop with read_file/finish tools,
                   must read ≥4 traces, one atomic proposal (paper App. E)
    scorer.py      SpreadsheetBench OJ checker adapter (all test cases per task)
    budget.py      fail-closed spend meter (see §6, S1–S5)
    stats.py       paired bootstrap + verdict vocabulary (vendored, stdlib-only)
    tasks/fetch.py task-suite download + seeded sampling + manifest freeze (SHA-256)
  runs/            per-run workspaces: raw/ wiki/ skills/ ledger.jsonl summary.json
```

Design rules, all inherited (`report#tbl-mvp-map`):
- **Model gateway = the Claude Code CLI on subscription auth (the FIS pattern).**
  The owner runs on a Max subscription, not API keys, so every model call goes through
  `claude -p` with the FIS-validated flag set (`--safe-mode`, `--system-prompt`,
  `--tools` restricted per role). FIS measured this: `--system-prompt` fully replaces
  the Claude Code harness prompt (~33.6K tokens of ambient context down to ~0.7K), so
  the executor still sees exactly: task-family system prompt + `{skill_section}` + task.
  The gateway is identical across arms; only the optimizer model differs.
- **Blind executor.** The inference agent never sees `wiki/` (the paper's ablation shows
  access *hurts*, `report#claim-blind-executor`).
- **Harness-written audit trail.** `ledger.jsonl` is written by `run.py`, never by an
  LLM — the objective record the proposer reads to avoid repeating rejections.
- **Wiki persists; skills roll back.** Gate: accept iff validation score strictly
  improves best-so-far (paper Eq. 4).
- **Sandbox (decision D2, default):** executor bash runs as a subprocess in a per-task
  tempdir copy, 90 s per command, cumulative 15 tool turns per rollout, env scrubbed of
  all secrets. Model-written code executes locally: acceptable for attended runs;
  **upgrade to the benchmark's own `code_exec_docker/` container before any unattended
  overnight run** (it exists upstream precisely for this).
- **Resume-safe.** Every iteration checkpoints; a budget halt or crash never loses paid
  work.
- Models: executor `claude-haiku-4-5`; optimizer `claude-opus-5`. Under the
  subscription gateway there is no Batch API discount; long evaluations run as normal
  CLI calls, paced so they respect the subscription's usage windows.

## 5. Phases, each with entry/exit gates

**Phase 0 — Build & smoke.** *API spend cap: $5.*
Build the rig; fetch benchmark; verify the official checker by hand on 3 sample tasks;
draw the task suite from the Verified-400 subset with a seeded, documented sample —
30 train / 15 val / 100 test, manifest hashed; timebox 30 min to check whether
SkillOpt/WikiSkill's exact 80/40/280 split is published (if so, document overlap);
smoke-run 3 tasks end-to-end through all four roles.
*Exit gate:* smoke passes with zero harness/schema violations (the SMOKE precondition,
contract §13); checker output reproduces the benchmark's own sample results; budget
meter demonstrably halts a run in a forced-overrun test. **Build budget: ≤3 working
sessions; if the smoke test does not pass by then, stop and reassess scope.**

**Phase 1 — Freeze + baseline + pilot.** *API spend cap: $100.*
Freeze `CONTRACT_v1.md` (all TBDs resolved) — commit before any TRAIN inference.
Order of spend, cheapest-informative-first:
1. Arm A baseline on VAL (15 tasks, ≈$1). **Gate S6:** baseline within [15%, 60%] band,
   else STOP-RESCOPE the task suite before any evolution money moves.
2. Arm A on TEST (100 tasks, one look, recorded in the look ledger).
3. Pilot: arms B and C, one seed each, K = 8 iterations.
*Exit gate:* **S7 futility rule** — if C − A on final VAL < +2 pts, do not extend;
record FUTILITY and stop for owner review.

**Phase 2 — Confirm.** *API spend cap: additional $200.*
Extend B and C to 3 seeds (sequential runs, paced); single pre-registered TEST look per arm-seed;
compute verdict; write the dated follow-up report in `research/` (that report — not this
plan — is what becomes eligible for EVIDENCE_MAP adjudication); qualitative skill
review: a human reads every accepted skill and answers — is this a general procedure,
or a workaround that only helps Haiku (`report#claim-negative-transfer`)?

**Phase 3 (conditional) — Lab-domain task suite.** *Separate contract; cap $250.*
Only on a CONFIRMED Phase 2 (or owner-authorized INCONCLUSIVE-positive): same rig,
millwork microtasks (room-by-room coverage checks, finish-schedule reconciliation,
cross-sheet reference following) against a surrogate document pack with hand-built
answer keys — converting `projects/millwork-estimating/WORKFLOW_HYPOTHESIS.md:179`
("generic prompt vs reusable estimator skill") into an executed contract.
This phase is the full practice run of the client work pattern: unlike Phases 0–2, the
answer keys do not exist and must be built from the client's documents first — the work
item real engagements start with (§1, "The client work pattern this MVP practices").

## 6. Stop criteria (the most important part of this plan)

Denomination note (2026-08-30): the lab runs on a Max subscription, so marginal dollars
are ~$0 and the caps below are **list-price-equivalent USD** computed from provider
token counts at first-party rates. They remain enforced fail-closed: the real scarce
resources are the subscription's usage windows and the owner's stated token-consumption
concern, and equivalents keep every run comparable if work ever moves to API billing.

Three layers. Mechanical rules are **enforced by `budget.py`/`run.py`, fail closed** —
a breach halts cleanly, checkpoints, writes the reason to the ledger, and requires a
human note to resume. Scientific rules are pre-registered in the contract; per lab
doctrine every tolerance names its consequence.

### 6.1 Mechanical (rig-enforced)

| ID | Trigger | Consequence |
|---|---|---|
| S1 | Rollout exceeds 15 tool turns or any bash command exceeds 90 s | Rollout scored 0, tagged `budget_fail`, run continues |
| S2 | Iteration spend > 1.5× its contract projection | Halt run, checkpoint, ledger `STOPPED-BUDGET(iteration)` |
| S3 | Arm-run spend > cap (A $5 · B $25 · C $45) | Halt run, `STOPPED-BUDGET(run)` |
| S4 | Phase spend > cap (P0 $5 · P1 $100 · P2 $200 · P3 $250) | Halt phase; resume only with owner note in the amendment log |
| S5 | Program total > **$600 hard ceiling** | Full stop; raising the ceiling is an owner decision recorded in the contract amendment log, never an in-run judgment call |

The meter counts actual `usage` fields from every API response (both models, both
tiers), maintains a per-call ledger row, and refuses to issue the next
API call once a cap is crossed — the check is *before* spend, not after.

### 6.2 Scientific (pre-registered; defaults below bind at freeze)

| ID | Trigger | Consequence |
|---|---|---|
| S6 | Arm-A VAL baseline outside [15%, 60%] | STOP-RESCOPE: task suite has no headroom (scores already too high) or no floor (scores too low); redraw before any evolution spend |
| S7 | Pilot futility: C − A on final VAL < +2 pts | No 3-seed extension; FUTILITY recorded (continuing would not be useful); owner decides re-scope vs abandon |
| S8 | Within-run: VAL hits 100% (paper's rule), OR 3 consecutive iterations with zero accepted proposals and a `no_action`/repeat-shaped proposal | End run early, `EARLY-PLATEAU` (declared deviation from the paper's fixed-K protocol — saves iterations the paper always paid for) |
| S9 | >20% of an iteration's rollouts crash/timeout | Halt; this is a rig defect (rung-0 instrument integrity), not evidence; fix before further spend |
| S10 | Ground-truth leakage into executor context, scorer defect, or gate contamination discovered at any point | STOP-INTEGRITY: run invalidated regardless of results; amendment log entry; restart |
| S11 | Any TEST evaluation beyond the single pre-registered look per arm-seed | Protocol breach: affected comparison downgraded to INCONCLUSIVE; look ledger is append-only |

### 6.3 Decision criteria (written before data, per contract §9)

- **CONFIRMED:** C > A on TEST, paired bootstrap (1,000 resamples, tasks as units,
  paired within task) p < 0.05 **and** effect ≥ +5 pts (the pre-registered minimum
  worth the machinery's complexity). Secondary, RANKED: C vs B vs A ordering on
  accuracy and on cost-per-completed-task.
- **REFUTED:** C ≤ A, or the CI excludes +5 on the downside.
- **INCONCLUSIVE:** everything else — including every `STOPPED-BUDGET` outcome. A
  budget stop is a real result about the method's cost envelope, and is reported as
  such, never quietly topped up.
- **Phase-3 gate:** CONFIRMED, or INCONCLUSIVE with positive point estimate plus an
  explicit owner authorization.

## 7. Systemic proposal: spend tolerances as standing doctrine

What §6.1 builds is not MVP-specific. Proposed as a captured feedback item (the
wholesaling-ledger F-item pattern), to be promoted only through the normal path:

> **Candidate rule — consequence-bearing spend tolerances.** Every experiment contract
> declares a per-stage spend schedule and a hard program ceiling, each with a named
> consequence on breach; a fail-closed meter (counting provider-reported usage, checked
> before each call) enforces them; spend is ledgered append-only, like TEST looks.
> Chapter 04 already demands consequence-bearing tolerances for calibration parameters;
> this extends the same discipline to money and tokens. This MVP is its first exercise.

## 8. Cost model (pre-registered projections; contract freezes them)

Per-rollout (Haiku, multi-round bash, history growth): ~$0.03. Optimizer per iteration:
1 maintainer call (wiki + ≤8 traces ≤15K chars each) + 10–20 ReAct turns — Opus ≈
$1.30–2.50, Haiku ≈ $0.30–0.50.

| Item | Formula | Est. |
|---|---|---|
| Arm A (baseline + TEST) | 115 rollouts | ≈ $3 |
| Arm B, per seed | 375 rollouts + 100 TEST + Haiku optimizer | ≈ $16 |
| Arm C, per seed | same rollouts + Opus optimizer | ≈ $28 |
| Pilot (P1) | A + B×1 + C×1, with margin | ≈ $50–70 |
| Extension (P2) | (B+C)×2 more seeds each | ≈ $90–160 |
| **Program, Phase A total** | | **≈ $150–250 against a $600 ceiling** |

Elapsed: Phase 0 ≈ 1–2 build sessions; pilot ≈ one overnight; full ≈ 2–3 days.
Harness-side (Claude Code session) budget: ≤3 sessions for Phase 0, checkpoint with
owner after each.

## 9. Proof standard and deliverables

"Proven" means, in order: (1) frozen contract committed before TRAIN; (2) run artifacts
+ ledgers + wiki/skill snapshots committed; (3) verdict computed by the pre-registered
plan, spend report included; (4) a dated `research/` follow-up report; (5) a candidate
EVIDENCE_MAP §2 row pairing that report (project evidence) with WikiSkill (external
corroboration). Only after (5) does any playbook edit — a MINOR at most — become
possible. Success also has a qualitative bar: at least one accepted skill that a human
reads and recognizes as a general procedure, with its PURPOSE.md tracing to wiki
patterns — the audit-trail property is half the point.

## 10. Risks

| Risk | Mitigation |
|---|---|
| Benchmark contamination in Haiku's training data | Paired design (skill vs no-skill on the same model) measures the delta, not absolute skill; noted in report |
| Benchmark license unstated | Data fetched at runtime, never committed or redistributed; research use only; re-check upstream before any publication |
| Gating noise on 15-task VAL (the autoresearch seed-change lesson, `report#ar-gating-noise`) | 3 seeds; strict-improvement gate; verdict from TEST only; effect floor +5 pts |
| Haiku tool-use variance inflates crash rate | S9 gate separates rig defects from evidence; smoke phase tunes prompts before freeze |
| Model-written code execution | Tempdir + timeout + scrubbed env attended; upstream Docker image for unattended runs (D2) |
| Scope creep ("let's also test retrieval / more models / more arms") | Non-goals in §1; any addition = new contract, new budget |

## 11. Immediate next actions (on owner go)

1. Phase 0 build (rig + task-suite fetch/sample + checker verification + forced-overrun
   budget test). No contract, no TRAIN inference, ≤$5 API.
2. Owner reviews `CONTRACT_DRAFT.md` TBDs (caps, band, floor, futility threshold — all
   have proposed defaults; changing them costs nothing until freeze).
3. Freeze, then Phase 1 in the stated spend order.
