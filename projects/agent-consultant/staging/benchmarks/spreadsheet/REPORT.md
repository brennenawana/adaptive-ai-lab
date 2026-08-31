# Skill Evolution on Spreadsheet Tasks — Experiment Report

**Date:** 2026-08-31 · **Verdict (pre-registered): CONFIRMED**

This report is the frozen record of an experiment we ran on 2026-08-30/31, before
this repository existed. It was edited once for publication: private project names
and file paths were replaced so the report stands on its own. Every number, rule,
and result is unchanged. The machine-readable results are in
`results/VERDICT.json`. The rules were fixed **before** the data — see
`CONTRACT.md` in this folder.

## 1. Summary

We built a small replication of the WikiSkill skill-evolution loop
(arXiv:2608.27454) and ran the one configuration the paper never tested: a
frontier model (Claude Opus 5) discovers and maintains the skills, while a cheap
model (Claude Haiku 4.5) executes every task attempt. On a 145-task
spreadsheet-manipulation suite drawn from inside the published SpreadsheetBench
splits, evolved skills raised the cheap executor's held-out test score from
36.0% to 75.7% (+39.7 points, p < 0.001), and the frontier-guided arm beat cheap
self-evolution by +13.0 points. Skills also cut inference cost per solved task by
about 3×. Total program cost: $166.77 in list-price-equivalent dollars (about $0
in real money on a subscription plan). This is one experiment on one task family —
treat the findings as candidates, not laws.

("Held-out" means the 100 test tasks stayed locked away during all skill
discovery. Nothing was tuned on them, and each was scored exactly once.)

## 2. Question and design

**Hypothesis:** with a cheap executor inside the rollout loop and a frontier
model proposing and maintaining skills, the evolved skills beat the executor's
no-skill baseline on the held-out test set — and match or beat skills the cheap
model evolves for itself.

Three arms, identical harness, one variable (the optimizer model):

| Arm | Executor | Wiki Maintainer + Skill Proposer | Seeds |
|---|---|---|---|
| A | Haiku 4.5, no skills | none | 1 (fixed configuration) |
| B | Haiku 4.5 | Haiku 4.5 | 3 |
| C | Haiku 4.5 | Opus 5 | 3 |

(A "seed" is one independent repeat of the whole evolution run, starting from an
empty wiki. Three seeds show how much the outcome depends on luck.)

The loop is WikiSkill's: three layers (immutable raw traces; a persistent wiki
that is never rolled back; gated skills), four roles, and one acceptance rule —
a skill proposal is accepted only if the validation score strictly improves.
Prompts are word-for-word from the paper's Appendix E. All model calls went
through the Claude Code CLI on a subscription login; every call is a fresh
process with no session state, no saved memories, and a fully replaced system
prompt (the exact flags are in `CONTRACT.md` §4).

## 3. Task suite

- Source: SpreadsheetBench "Verified-400" (real Excel-forum tasks, one
  input/answer pair per task for 395 of 400), tarball SHA-256
  `10ef893d…c03fc949`.
- Splits: 30 train / 15 validation / 100 test, each drawn from inside the
  matching split of microsoft/SkillOpt's published 80/40/280 id split — the
  split the WikiSkill paper reports matching — so results stay
  distribution-comparable at lower cost. Draw seed 20260830; task-id manifest
  SHA-256 `2f3a4d71…99a5e1d2`.
- Filter: a task qualifies only if its answer file passes the checker against
  itself and its input file fails (the task is well-formed and requires work).
  4 tasks were excluded by this filter.
- Scorer: the benchmark's own checker, at pinned upstream commit `49b73a94…`.
  The upstream project has no license file, so its code and data are downloaded
  from the original sources at run time and never copied into this repository.

## 4. Execution record

Executed 2026-08-30 → 2026-08-31 on one 16 GB macOS host. Discipline held
throughout: 7 planned test-set looks, 7 spent, none extra; every proposal, gate
decision, and dollar on append-only ledgers; spend totals reconciled from the
ledgers at close ($1.02 setup + $71.80 pilot + $93.94 extension = $166.77,
against a $1,000 ceiling).

Incidents, all handled through the contract's own paths:

1. **Budget stop, real.** The first test evaluation paced at $0.057/task, 1.9×
   the projection its cap was sized from. The run was stopped at 43/100 tasks
   ($2.74) before the cap could kill it mid-flight; the owner raised the caps
   through the contract's amendment path (`CONTRACT.md` §18, Amendment 1). The
   evaluation step gained per-task checkpointing — without it, a halt would have
   thrown away all paid work. The interrupted look continued as the same look:
   no result was ever produced or seen, so the one-look rule held.
2. **Machine overload, operator error.** During the owner-authorized parallel
   phase (Amendment 2), ~31 concurrent CLI processes pushed the 16 GB host into
   heavy swap (9 GB, 15-minute load 17), slowing everything else on the machine.
   The owner had authorized 20; the flows totaled 31. Standing guidance now:
   count TOTAL concurrent processes before launching; ~12–15 on a shared 16 GB
   machine.
3. **Zero provider pushback.** No rate-limit events at any point; the
   transport-retry code went unused. Zero harness crashes across 6 evolution
   runs and 7 test looks.

One near-miss worth recording: the deepest run (C, seed 1) spent $46.15 — more
than its original $45 cap. Amendment 1 is the only reason its best skill exists.

## 5. Results

### 5.1 Primary and secondary outcomes (test set, n=100, pre-registered)

| Arm | Test mean | Per-seed test | Validation peak per seed | Discovery cost |
|---|---|---|---|---|
| A — no skill | 36.0% | — | 33.3% | $0.72 |
| B — self-evolved | 62.7% | 81.0 / 59.0 / 48.0 | 93.3 / 73.3 / 40.0 | $40.11 |
| C — frontier-guided | **75.7%** | 80.0 / 77.0 / 70.0 | 93.3 / 93.3 / 86.7 | $86.51 |

Statistics: paired bootstrap over tasks — resample the 100 test tasks with
replacement 1,000 times, recompute the between-arm difference each time, and
read the confidence interval from the spread (one-sided, seed 20260830). An
evolved arm's score per task is the mean over its 3 seeds.

- **Primary, C vs A: +39.7 points, 95% CI [+30.0, +49.3], p < 0.001.**
  The pre-registered minimum worthwhile effect was +5 points → **CONFIRMED**.
- Secondary (ranked, not confirmatory): C vs B **+13.0** [+6.0, +20.0],
  p < 0.001; B vs A **+26.7** [+19.3, +33.7], p < 0.001. Order: C > B > A.
- Prediction register: the estimate written before the data (C−A = +8, interval
  [0, +16]) was far too low. Recorded for calibration.

### 5.2 What the runs did

All six evolution runs accepted at least one skill. Five stopped early at the
plateau rule (3 straight rejections); C seed 1 ran all 8 iterations and refined
one skill three times through the gate (created at validation 0.80 → patched to
0.867 → patched to 0.933) — the iterative-refinement pattern the persistent wiki
exists to enable. The gate also proved its worth in reverse: one B seed-1 patch
dropped validation from 0.93 to 0.40 and was rejected.

Every run's test score landed 8–14 points below its validation peak. The 15-task
validation split flatters the skills chosen on it; only test numbers are
quotable. Two identical no-skill baselines scored 33.3% and 40.0% on validation —
the same noise, visible directly.

### 5.3 Discovery reliability — the main difference between arms

The task family has one dominant failure cause: formulas written by openpyxl
carry no computed values, so a value-reading checker sees empty cells. Every
strong seed converged on the same counter-rule ("compute in Python, write
literal values"):

- Arm B (cheap-model discovery): seed 1 found it fully (test 81), seed 2
  partially (test 59), seed 3 missed it and shipped only a narrow array-formula
  rule (test 48).
- Arm C (frontier discovery): all three seeds found it (test 70–80); one seed
  found it on its first proposal. Two C seeds also found a second idea no B seed
  found: many workbooks contain their own answer key (a "Manual Result" sheet,
  completed example rows), and the skill teaches the executor to check its
  output against that built-in example before saving.

Frontier discovery bought **reliability** (tight seed spread) more than peak
score. A human read every accepted skill and classified each as a general
procedure for this task family, not a model-specific workaround; one line
references the benchmark by name and would name a team's own file conventions in
a real deployment. The winning skill is in `skills/` in this folder.

### 5.4 Economics

Inference cost per solved task (test set): A $0.225 · B $0.071 · C $0.075.
Skills made the executor better **and** ~3× cheaper per solved task — a skilled
run wastes fewer turns, so the no-skill arm's 100-task evaluation cost more
($8.09) than the skilled arms' ($4.46 and $5.65 on average) while solving half
as many tasks. Discovery is a one-time bill ($40–87 for three seeds; one seed
suffices in deployment). All figures are list-price equivalents; on a
subscription plan the marginal cash cost was ~$0.

## 6. What we learned

Six findings. Each is one experiment's evidence, not a law.

1. On procedural, tool-mediated task families with checkable outputs, evolved
   skills can substitute for model scale at inference time (+39.7 points here;
   WikiSkill's Table 1 shows a 9B model with skills beating a bare 27B).
2. A frontier optimizer with the cheap executor inside the loop improves
   discovery **reliability** over cheap self-evolution (seed spread 70–80 vs
   48–81; +13.0 points mean). This configuration was previously untested; it
   needs a second task family before anyone should treat it as a rule.
3. Gate on the small validation split, but claim only test numbers: validation
   peaks overstated test by 8–14 points in all six runs.
4. Hard budget caps with fail-closed metering work — but cost projections must
   be measured, not estimated. Our one real budget stop traced to an estimated
   unit cost that reality beat by 1.9×. Re-project from the first measured runs.
5. Skills reduce inference cost per solved task (~3× here). The case for them is
   economic, not only accuracy. (WikiSkill's Appendix D analyzes optimizer cost
   only; the per-task inference saving is our observation.)
6. Meter provider usage by summing **every** model entry in a usage report and
   taking the maximum of independent accountings. A single-entry reading
   undercounted by ~30× before our smoke test caught it.

## 7. Limits and threats to validity

1. One task family, one benchmark subset, one executor model. Nothing here
   generalizes on its own.
2. The gain is concentrated: one dominant failure cause explains most of it.
   Task families without such a concentration should expect smaller effects
   (WikiSkill's cross-domain range was roughly +11 to +41).
3. Possible training-data contamination of the public benchmark is mitigated,
   not removed, by the paired design (skill vs no-skill on the same model and
   tasks).
4. The single-test-case Verified-400 subset is easier than the full 912-task
   set; absolute scores are not comparable to published full-set numbers.
5. Validation noise is large at n=15; acceptance decisions inherit it
   (mitigated by 3 seeds and test-only claims).
6. Runs shared one host and one subscription account; provider-side prompt
   caching reuses identical prefixes across calls (a cost effect, not an
   information leak).

## 8. Reproducing this

The engine in this repository is the public port of the private rig that ran
this experiment. This folder's `adapter/` wires the engine to the benchmark's
task format and checker, and `fetch_data.py` downloads the dataset and the
checker from their original sources at the pinned versions above — we point at
the upstream work instead of copying it, because it has no license file.
(Adapter and fetch script land together with the engine port; the report,
contract, skill, and results in this folder are final.)

POSIX only as written; use WSL2 on Windows. A run on a different machine is a
different execution system: run a small equivalence probe (the 15 no-skill
validation tasks on both machines) before comparing numbers across machines.

## 9. Credits and sources

- **WikiSkill** (Tang et al., Google Research), arXiv:2608.27454 — the loop,
  the role prompts (Appendix E, CC BY 4.0), and the external corroboration
  cited above.
- **SpreadsheetBench** (Ma et al., NeurIPS 2024) and the "Verified-400" subset
  (Hugging Face: KAKA22) — the tasks and the checker. No license file is
  published, so their data and code are fetched from the source and never
  redistributed here.
- **microsoft/SkillOpt** — the published task-id splits ours nest inside.
- Lineage for the wider method: Andrej Karpathy's "LLM Wiki" gist and
  karpathy/autoresearch.
- Models: Claude Haiku 4.5 (executor; arm-B optimizer) and Claude Opus 5
  (arm-C optimizer), via the Claude Code CLI.
