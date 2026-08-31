# SE-1 Experiment Report: Skill Evolution with a Frontier Optimizer and a Cheap Executor

**Date:** 2026-08-31 · **Status:** informative, never normative · **Extraction status:** not yet adjudicated
**Contract:** `projects/skill-evolution-mvp/SE1_EXPERIMENT_CONTRACT.md`, frozen at commit
`2da2ff9` (blob `62093fd`), two owner amendments (§18). Results commit: `b7642d0`.
**Verdict (pre-registered): CONFIRMED.**

This report is frozen on landing. Cite it by line number. The machine-readable record
is `projects/skill-evolution-mvp/runs/VERDICT.json`; the running narrative is
`projects/skill-evolution-mvp/IMPLEMENTATION.md`. Written to the lab language
standard: plain English for technical ESL readers.

## 1. Summary

We built a small replication of the WikiSkill skill-evolution loop (arXiv:2608.27454)
and ran the one configuration the paper never tested: a frontier model (Claude Opus 5)
as the skill discoverer, with a cheap model (Claude Haiku 4.5) executing every rollout.
On a 145-task spreadsheet-manipulation suite drawn from inside the published
SpreadsheetBench splits, evolved skills raised the cheap executor's held-out score
from 36.0% to 75.7% (+39.7 points, p < 0.001), and the frontier-guided arm beat cheap
self-evolution by +13.0 points. Skills also cut inference cost per solved task by
about 3×. Total program cost: $166.77 list-price-equivalent (about $0 real cost on a
subscription). One experiment on one task family — findings below are candidates, not
rules.

## 2. Question and design

**H1:** with a cheap executor inside the rollout loop and a frontier
maintainer/proposer, evolved skills beat the executor's no-skill baseline on held-out
TEST, and match or beat skills evolved entirely by the cheap model.

Three arms, identical harness, one variable (the optimizer model):

| Arm | Executor | Wiki Maintainer + Skill Proposer | Seeds |
|---|---|---|---|
| A | Haiku 4.5, no skills | none | 1 (fixed configuration) |
| B | Haiku 4.5 | Haiku 4.5 | 3 |
| C | Haiku 4.5 | Opus 5 | 3 |

The loop is WikiSkill's (three layers: immutable traces, persistent wiki, gated
skills; four roles; accept a skill only if validation strictly improves; the wiki is
never rolled back). Prompts are word-for-word from the paper's Appendix E. All model
calls go through the Claude Code CLI on subscription login with the FIS-validated
isolation flags; every call is a fresh process with no session state, no memories,
and a fully replaced system prompt. Full design: `projects/skill-evolution-mvp/PLAN.md`.

## 3. Task suite

- Source: SpreadsheetBench "Verified-400" (real Excel-forum tasks, one input/answer
  pair per task for 395 of 400), tarball SHA-256 `10ef893d…c03fc949`.
- Splits: 30 train / 15 validation / 100 test, each drawn from inside the matching
  split of microsoft/SkillOpt's published 80/40/280 id split — the split WikiSkill
  reports matching — so results stay distribution-comparable at lower cost.
- Filter: a task qualifies only if its answer file passes the checker against itself
  and its input file fails (the task is well-formed and requires work). 4 tasks were
  excluded by this filter.
- Scorer: the benchmark's own checker, imported at pinned commit `49b73a94…`
  (upstream has no license file; its code and data are cached locally, never
  committed to this repository).
- Manifest: `projects/skill-evolution-mvp/tasks/manifest.json`, SHA-256 `2f3a4d71…`,
  draw seed 20260830.

## 4. Execution record

Executed 2026-08-30 → 2026-08-31 on one 16 GB macOS host. Discipline held throughout:
7 planned TEST looks, 7 spent, none extra; every proposal, gate decision, and dollar
on append-only ledgers; spend totals reconciled from the ledgers at close
(P0 $1.02 · P1 $71.80 · P2 $93.94 · total $166.77 against a $1,000 ceiling).

Incidents, all handled through the contract's own paths:

1. **Budget stop, real (S3-class).** The first TEST evaluation paced at $0.057/task,
   1.9× the projection its $5 cap was sized from. The run was stopped at 43/100
   tasks ($2.74) before the cap could kill it mid-flight; the owner raised the caps
   through §18 Amendment 1. The evaluation step gained per-task checkpointing (its
   absence would have lost all paid work on a halt). The interrupted look continued
   as the same look — no result was ever produced or seen, so the one-look rule held.
2. **Machine overload, operator error.** During the owner-authorized parallel phase
   (§18 Amendment 2), ~31 concurrent CLI processes pushed the 16 GB host into heavy
   swap (9 GB, 15-minute load 17), slowing the owner's other work. The owner had
   said 20; the flows totaled 31. Standing guidance now in the rig config: count
   TOTAL concurrent processes; ~12–15 on this machine when shared.
3. **Zero provider pushback.** No rate-limit events at any point; the transport-retry
   code went unused. Zero harness crashes across 6 evolution runs and 7 looks.

One near-miss worth recording: the deepest run (C-s1) spent $46.15 — more than its
original $45 cap. Amendment 1 is the only reason its best skill exists.

## 5. Results

### 5.1 Primary and secondary outcomes (TEST, n=100, pre-registered)

| Arm | TEST mean | Per-seed TEST | VAL peak per seed | Discovery cost |
|---|---|---|---|---|
| A — no skill | 36.0% | — | 33.3% | $0.72 |
| B — self-evolved | 62.7% | 81.0 / 59.0 / 48.0 | 93.3 / 73.3 / 40.0 | $40.11 |
| C — Opus-guided | **75.7%** | 80.0 / 77.0 / 70.0 | 93.3 / 93.3 / 86.7 | $86.51 |

Paired bootstrap over tasks (1,000 resamples, one-sided, seed 20260830), evolved-arm
score per task = mean over 3 seeds:

- **Primary, C vs A: +39.7 points, 95% CI [+30.0, +49.3], p < 0.001.**
  Pre-registered floor was +5 → **CONFIRMED**.
- Secondary (RANKED): C vs B **+13.0** [+6.0, +20.0], p < 0.001;
  B vs A **+26.7** [+19.3, +33.7], p < 0.001. Order: C > B > A.
- Prediction register: the drafted estimate (C−A = +8, interval [0, +16]) was far too
  low. Recorded for calibration.

### 5.2 What the runs did

All six evolution runs accepted at least one skill. Five stopped early at the plateau
rule (3 straight rejections); C-s1 ran all 8 iterations and refined one skill three
times through the gate (create at VAL 0.80 → patch 0.867 → patch 0.933) — the
iterative-refinement pattern the persistent wiki exists to enable. The gate also
proved its rollback: one B-s1 patch dropped VAL from 0.93 to 0.40 and was rejected.

Every run's TEST score landed 8–14 points below its VAL peak. The 15-task validation
split flatters the skills chosen on it; only TEST numbers are quotable. Two identical
no-skill baselines scored 33.3% and 40.0% on VAL — the same noise, visible directly.

### 5.3 Discovery reliability — the main qualitative difference between arms

The task family has one dominant failure cause: formulas written by openpyxl carry no
computed values, so the value-based checker reads empty cells. Every strong seed
converged on the same counter-rule ("compute in Python, write literal values"):

- Arm B (Haiku discovery): seed 1 found it fully (TEST 81), seed 2 partially
  (TEST 59), seed 3 missed it and shipped only a narrow array-formula rule (TEST 48).
- Arm C (Opus discovery): all three seeds found it (TEST 70–80); C-s2 found it on
  its first proposal. Two C seeds also found a second idea no B seed found: many
  workbooks contain their own answer key (a "Manual Result" sheet, completed example
  rows), and the skill teaches the executor to check its output against that built-in
  example before saving.

Frontier discovery bought **reliability** (tight seed spread) more than peak score.
Qualitative classification of accepted skills: general procedures for this task
family, not model-specific workarounds; one line references the benchmark by name
and would name a client's file conventions in a client version.

### 5.4 Economics

Inference cost per solved task (TEST, per 100-task evaluation): A $0.225 · B $0.071 ·
C $0.075. Skills made the executor better **and** ~3× cheaper per solved task — a
skilled run wastes fewer turns, so the no-skill arm's evaluation cost more ($8.09)
than the skilled arms' ($4.46–5.65) while solving half as many tasks. Discovery is a
one-time bill ($40–87 for three seeds; one seed suffices in deployment). All figures
are list-price equivalents; on the owner's subscription the marginal cash cost was ~$0.

## 6. Findings as candidate rules (for adjudication, not adoption)

Each pairs project evidence (this report) with external corroboration, per the
promotion path. Single-project evidence caps proposals at class B.

- **F-SE1-1.** On procedural, tool-mediated task families with verifiable outputs,
  evolved skills can substitute for model scale at inference time. Here: cheap
  executor +39.7 points. External: WikiSkill Table 1 (9B+skills > 27B bare).
- **F-SE1-2.** A frontier optimizer with the cheap executor inside the rollout loop
  improves discovery reliability over cheap self-evolution (seed spread 70–80 vs
  48–81; +13.0 points mean). External: adjacent only — WikiSkill's cross-model
  transfer; this configuration itself was previously untested. Strongest novel claim;
  needs a second task family before promotion past B.
- **F-SE1-3.** Gate on the small validation split, claim only on held-out TEST:
  VAL peaks overstated TEST by 8–14 points in all six runs. External: WikiSkill's
  small-split caveat; the autoresearch seed-change lesson.
- **F-SE1-4.** Consequence-bearing spend tolerances with fail-closed metering work,
  but projections must be measured, not estimated: the one real budget stop traced
  to an estimated unit cost that reality beat by 1.9×. Re-project from the first
  measured runs. External: chapter 04's calibration doctrine, extended to money.
- **F-SE1-5.** Skills reduce inference cost per solved task (~3× here) — the
  economics case is not only accuracy. External: WikiSkill App. D (optimizer-cost
  analysis only; the per-task inference saving is this lab's observation).
- **F-SE1-6.** Meter provider usage by summing every model entry in the response and
  taking the maximum of independent accountings; a single-entry reading undercounted
  30× before the smoke test caught it. External: none (implementation lesson).

## 7. Limits and threats to validity

1. One task family, one benchmark subset, one executor model. Nothing here
   generalizes on its own.
2. The gain is concentrated: one dominant failure cause explains most of it. Task
   families without such a concentration should expect smaller effects (WikiSkill's
   cross-domain range was roughly +11 to +41).
3. Possible training-data contamination of the public benchmark is mitigated, not
   removed, by the paired design (skill vs no-skill on the same model and tasks).
4. The single-test-case Verified-400 subset is easier than the full 912-task set;
   absolute scores are not comparable to published full-set numbers.
5. Validation noise is large at n=15; acceptance decisions inherit it (mitigated by
   3 seeds and TEST-only claims).
6. Runs shared one host and one subscription account; provider-side prompt caching
   reuses identical prefixes across calls (a cost effect, not an information leak).

## 8. Reproduction

Rig, contract, manifest, ledgers, wiki snapshots, accepted skills, and verdict are in
`projects/skill-evolution-mvp/` at commit `b7642d0`. Setup on a new machine: install
uv and the Claude Code CLI (2.1.251), log in, fetch the dataset tarball and pinned
checker into `~/.cache/skill-evolution-mvp/`, then `uv sync`. Verify with
`rig.cli check`, `selftest-budget`, `selftest-checker`, `draw-suite` (deterministic),
smoke ≤$5. POSIX only as written (`fcntl`, symlinks, bash scripts) — use WSL2 on
Windows. A run on a different host is a different execution system: probe equivalence
(15 no-skill validation tasks, both hosts) before comparing across machines.

## 9. Sources

External sources are recorded per `playbook/references/sources.yaml` conventions when
adjudicated; primary here:

- WikiSkill (Tang et al., Google Research), arXiv:2608.27454v1 — the loop, prompts,
  and external corroboration. See the sibling deep-dive:
  `2026-08-30_WikiSkill_LLM_Wiki_Autoresearch.html` (cite by anchor).
- SpreadsheetBench (Ma et al., NeurIPS 2024) + Verified-400 (HF: KAKA22), no license
  file — research use, never redistributed.
- microsoft/SkillOpt `data/spreadsheetbench_id_split` — the published splits ours
  nest inside.
- Lab machinery: FIS CLI gateway pattern (`fis_platform/model_gateway/`), experiment
  contract apparatus, verdict vocabulary (`fis_platform/stats.py`).
