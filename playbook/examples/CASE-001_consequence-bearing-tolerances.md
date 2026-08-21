# CASE-001: Consequence-Bearing Tolerances

> Real empirical case from the FIS project (Fintech Integration Sandbox), a
> realistic synthetic fintech-operations laboratory used to develop this
> playbook's methodology.

**Source ID:** INT-CASE-001 · **Date:** 2026-08-18 – 2026-08-20 · **Cited by:**
[00. Principles and Scope](../00_PRINCIPLES_AND_SCOPE.md) ·
[04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md) ·
[07. Optimization and Intervention Ladder](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md)

## Situation

Milestone R6 refreshed the project's local-specialist model lineup, adding a
dense 27B candidate (`Qwen3.8-27B Q3_K_M`) alongside historical and efficiency
arms. Before any DEV/TEST inference, R6's frozen experiment contract
pre-registered a TRAIN-only generation-cap calibration procedure (`R6_EXPERIMENT_CONTRACT.md`
§6): run a 36-case stratified pilot once at the manifest ceiling (8,192
output tokens, greedy, seed 42 — since a shorter cap's completion is a
prefix of the ceiling run, one run at the ceiling decides every smaller cap);
for each candidate cap `c` in `{4096, 6144, 8192}`, count `capped(c)` = pilot
cases with `output_tokens ≥ c` or `stop_reason == "length"`; require
`capped(c) ≤ 3` of 36 (≤ 8.3%); freeze the smallest cap meeting that
tolerance. The contract also wrote down what to do if no cap met it: *"if
none does, freeze 8192 and record the truncation rate."* That clause is the
escape hatch this case is about.

## Decision faced

Whether a pre-registered calibration tolerance, once breached, could be
allowed to resolve itself by falling through to a pre-written default
("freeze the ceiling cap and note the number") — or whether a breach that
size needed to force an explicit, priced decision (abort the candidate,
recalibrate the pilot, or proceed only with the cost stated in advance)
before the milestone's most expensive phases (DEV, TEST) ran on the
resulting configuration.

## Evidence

The TRAIN pilot cap table for the selected quant (`R6_EXPERIMENT_CONTRACT.md`
§10; corroborated in `R6_MODERN_LOCAL_SPECIALIST_REFRESH_REPORT.md` §4):

| cap | pilot cases capped (of 36) | rate |
|---|---|---|
| 4096 | 32† | 88.9% |
| 6144 | 26 | 72.2% |
| 8192 | 15 | 41.7% |

† §10 originally transcribed 33/91.7%; the contract's own §17 amendment log
corrects this to 32/36 against the registry payload and cap-calibration
record (outcome unchanged — 8192 was the cap frozen either way, and the 5×
breach below is computed from the unaffected 8192 row).

None met the ≤3/36 (8.3%) tolerance at any allowed cap. The rule fired
exactly as written — no bug, no contract violation — and froze cap 8192 with
the 41.7% truncation rate recorded, as designed. Independent statistical
re-derivation against the project's own trajectory store, done after the
milestone closed, states the size of the breach plainly (research 2026-08-20
§2.2, Finding 1): *"The 36-case pilot measured a 5× tolerance breach (15/36
cap-hits vs ≤3/36 pre-registered) and the contract's own escape hatch said
proceed. Detection was never the gap; the tolerance had no consequence
attached."* Fifteen actual cap-hits against a ceiling of three is a 5×
breach on the pilot's own units (41.7% against an 8.3% bar).

## What happened

Because the escape hatch carried no named consequence, the milestone
proceeded automatically at cap 8192 through DEV and TEST on the frozen
configuration. The breach was not a one-off pilot artifact — it was the
candidate's steady-state failure shape:

| split | Qwen3.8-27B no-output (cap-hit) | of total failures |
|---|---|---|
| TRAIN pilot | 15/36 (41.7%) | — |
| DEV | 22/48 (45.8%) | 22 of 23 DEV failures |
| TEST | 47/96 (49.0%) | 47 of 49 TEST failures |

Milestone-wide, the R6 performance autopsy measured 24h 03m (≈24.1 h) of
total wall clock, of which **9h 55m (≈41%) was cap-hit generation that
scored zero — 145 cases, 0 passes** (`R6_PERFORMANCE_AUTOPSY.md` §1;
`experiment-log.md`, R6 entry; corroborated by `AI_SYSTEMS_LAB_MASTER_PLAN.md` §2). The dense 27B family, decoding at
~28 tok/s, accounted for 65% of the milestone's wall clock on its own. None
of this made Qwen3.8-27B a failed candidate — it went on to `DEV_QUALIFIED`
and `TEST_EVALUATED`, and under the project's unchanged deterministic
verifier gate it became the strongest local substrate measured to date (93/96
on the cascade, 2 silent failures against Nemotron's 27 on TEST). The defect was not
that the milestone proceeded; it is that **proceeding happened without
anyone deciding to pay for it.** The 9h55m was real compute, spent on a
configuration everyone could see was truncating at 5× the pre-registered
limit, and no one had to write down that cost before it was spent.

The fix adopted afterward (`AI_SYSTEMS_LAB_MASTER_PLAN.md` §3, REVISED) was
not "add a stopping rule" — it was to close the specific gap the escape
hatch left open: every pre-registered tolerance must now name its breach
consequence — **ABORT**, **RECALIBRATE**, or **PROCEED-WITH-DECLARED-CEILING**
(with the projected cost stated before proceeding) — enforced fail-closed by
the runner itself, in the same style as the project's existing `--candidate`
execution-system-match refusal. A tolerance is no longer allowed to resolve
into a default; it must resolve into a decision.

## The generic lesson

**Portable rule: a pre-registered tolerance without a named breach
consequence is an unpriced escape hatch.** It will fire exactly as
designed and will still let an arbitrarily large breach through, because
"record the rate and continue" is itself a consequence — just one nobody
chose. A [consequence-bearing tolerance](../GLOSSARY.md#consequence-bearing-tolerance)
closes this by requiring, for every calibration/qualification parameter,
one of three named outcomes decided *before* the breach is observed:
ABORT, RECALIBRATE, or PROCEED-WITH-DECLARED-CEILING with its cost stated
in writing. This is not a heavier process for its own sake — R6's own
tolerance already existed and already ran; the fix adds one sentence per
tolerance, enforced [fail-closed](../GLOSSARY.md#fail-closed) so the runner
itself, not a reviewer's memory, is what stops an unpriced proceed.

This case is why chapter 00's [never-skippable floor](../GLOSSARY.md#never-skippable-floor)
includes "predeclare consequences for decision-driving thresholds/tolerances"
at every stakes tier, and why the [experiment contract](../GLOSSARY.md#experiment-contract)
template (chapter 04) requires a consequence column on every calibration
rule with the note that "a tolerance without a consequence fails contract
review." It also grounds the [intervention ladder](../GLOSSARY.md#intervention-ladder)'s
rung 5 (generation/reasoning-budget calibration, chapter 07): a capacity
parameter like a generation cap is exactly the kind of tolerance this
discipline targets, because a truncation breach there is silent and
cumulative rather than a single visible crash.

## What would NOT have worked

Adding a generic *stopping rule* to catch this earlier would not have
solved it, and treating one as the fix is itself the anti-pattern this
case exists to name. The natural instinct — "certainty curtailment would
have cut the arm short and saved most of the 9h55m" — is contradicted by
the project's own replay of the real R6 data (research 2026-08-20 §2.2,
Finding 3): certainty curtailment only fires on *hopeless* arms, and
Qwen3.8-27B was sitting near its qualification bar, not hopeless — its
measured saving on the real TEST arms was **0.51h of 24h (≈2%)**, not the
naively expected ~10h. The 9h55m was a decision-quality problem (an
unpriced tolerance breach), not a futility-detection problem, and a
stopping rule adopted to solve it for speed would have been solving the
wrong problem while looking like progress. A sequential test (SPRT) fares
worse still: replayed on the four real R6 pilot sequences it wrongly
accepted the null at case 9 on a real 10/36 violator and never fired at all
on a real 4/36 violator, because cap-hits are class-clustered (measured
ICC 0.398) against a class-blocked pilot order, inflating its nominal 5%
error rate to roughly 11% — [sequential-rule admissibility](../GLOSSARY.md#sequential-rule-admissibility)
fails here, and [curtailed exact counting](../GLOSSARY.md#curtailed-exact-counting)
(halt at the 4th violation, an exact count with no distributional claim)
dominates it on this project's own clustered data.

Nor would "just raise the cap" have been a free recalibration: at the
frozen context length, Qwen3.8-27B already occupies 15.1–15.2 GiB of the
16.3 GiB card at cap 8192 with q8_0 KV cache, so a larger cap may not fit
at all without other tradeoffs. That is exactly why RECALIBRATE has to be a
named, costed option rather than an assumed one — the "obvious" remedy has
its own price that also needs to be written down before it is chosen.

## References

- [EXT-STOPPING-001] Wald SPRT / always-valid sequential testing — the
  rejected alternative; dominated by curtailed exact counting on this
  project's clustered pilot data.
- [EXT-STOPPING-002] Lan & DeMets; clinical-trial adaptive-design
  pre-specification — the general principle consequence-bearing tolerances
  instantiate: pre-register the adaptation *rule*, never the outcome.
- Governing chapters: [00](../00_PRINCIPLES_AND_SCOPE.md),
  [04](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md),
  [07](../07_OPTIMIZATION_AND_INTERVENTION_LADDER.md).
- Glossary: [consequence-bearing tolerance](../GLOSSARY.md#consequence-bearing-tolerance),
  [curtailed exact counting](../GLOSSARY.md#curtailed-exact-counting),
  [certainty curtailment](../GLOSSARY.md#certainty-curtailment),
  [sequential-rule admissibility](../GLOSSARY.md#sequential-rule-admissibility),
  [fail-closed](../GLOSSARY.md#fail-closed),
  [intervention ladder](../GLOSSARY.md#intervention-ladder),
  [never-skippable floor](../GLOSSARY.md#never-skippable-floor).
