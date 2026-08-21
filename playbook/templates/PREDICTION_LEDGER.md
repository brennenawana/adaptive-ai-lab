# Prediction Ledger

A running record of pre-run effect estimates — point and interval, per primary
metric — scored against actuals once a confirmation split reports. This is the
operational form of the
[prediction ledger](../GLOSSARY.md#prediction-ledger): it turns "is this
experiment worth running?" from taste into an empirical property of the
estimator's own calibration. An
[experiment contract](../GLOSSARY.md#experiment-contract) fills its prediction
register at freeze (its §1); this document is where that entry is scored and
accumulated across every experiment.

> Index: [../README.md](../README.md) · Governing chapter: [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)

## When to use / when not to use

- **MUST** log one entry per primary metric at [freeze](../GLOSSARY.md#freeze)
  — before any qualification or confirmation look — mirroring the experiment
  contract's prediction register.
- **SHOULD** use at Tier 1 too, for the calibration practice — it costs one
  line and a moment of honesty before the answer is already known.
- **Do not** backfill a prediction after seeing the result. A "prediction"
  entered after a look has started is not a prediction; if this happens, mark
  the row `VOID (post-hoc)` and state why rather than quietly discarding it — a
  pattern of voided rows is itself a finding.
- **Do not** treat this ledger as a substitute for the statistical plan's
  [MDE](../GLOSSARY.md#mde) and verdict — a well-calibrated wrong-direction
  prediction and a badly-calibrated right-direction one both still need the
  primary/secondary statistics to call
  [CONFIRMED / REFUTED / INCONCLUSIVE](../GLOSSARY.md#verdict-vocabulary).

## Rigor-tier applicability

| Tier | Requirement |
|---|---|
| Tier 1 — Exploratory | Optional; recommended for the calibration habit. |
| Tier 2 — Consequential (default) | **MUST** be maintained — part of the experiment contract's frozen prediction register (its §1, Freeze Checklist). |
| Tier 3 — High-stakes/regulated | **MUST** be maintained, and scored entries are subject to the periodic methodology audit (chapter 12). |

Rigor attaches to the *decision's* consequence, same as elsewhere: any
experiment whose contract is required to freeze a prediction register (Tier 2+)
is required to score it here. See chapter 00 §6 (rigor dial) and
[PROJECT_PROFILE.md](PROJECT_PROFILE.md).

---

## The Ledger

*Fill every section below. Placeholders in `[brackets]` carry inline guidance in
italics — replace the placeholder, keep or delete the guidance. No section may
be silently omitted; see ["Delete no section"](#delete-no-section) at the end of
this document.*

### 1. Ledger Table

| Date | Experiment | Primary metric | Predicted (point + interval) | Actual | Inside interval? | Surprise notes |
|---|---|---|---|---|---|---|
| [YYYY-MM-DD, ≤ freeze date] | [contract ID] | [the one metric named primary in the contract] | [point estimate; interval reflecting genuine uncertainty] | [scored result, filled after confirm] | yes \| no \| pending | [what you'd revise about your model of the system if this diverged] |

*`Date` must be at or before the contract's freeze date — a prediction dated
after the look started is not a prediction (see "When to use"). The interval
should be wide enough to reflect real uncertainty; an interval you are never
surprised to miss is not doing calibration work.*

### 2. Scoring

**Coverage rate.** `count(inside interval? = yes) / count(scored)`, updated as
rows resolve. Compare against the intervals' *nominal* coverage — an interval
intended as an 80% interval should contain the actual roughly 80% of the time
over enough entries; a coverage rate persistently far from nominal, in either
direction, is a finding about the intervals, not noise to explain away.

**Systematic bias.** Track direction, not just hit rate: are predictions
consistently over- or under-stating effect size? Consistently too narrow
(overconfident) or too wide (underconfident)? Note any pattern here in prose as
it becomes visible across rows — this is where the ledger earns its keep.

**[PARAMETER]** The handful-of-entries rule: coverage rate is data-thin
evidence — read it as anecdote before roughly 5–10 scored entries have
accumulated, and as a genuine (if still small-sample) signal after. Calibrate
this threshold against how often consequential experiments actually run; the
caution echoes vendor precedent for treating small-n statistics as insufficient
evidence rather than a verdict [NV-EVALSDK-001].

---

## Delete No Section

Every numbered section above **MUST** appear in a filled ledger. If no
experiments have been scored yet, write the section header with the body
`N/A — no entries scored as of [date]` under §2 rather than omitting it.
Absence is a decision, and a reviewer needs to see that it was considered, not
skipped.

---

## Miniature Filled Example

*Illustrative example — synthetic. Invented project: the invoice-triage
assistant from [EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md)'s worked
example, Tier 2.*

**§1 Ledger table:**

| Date | Experiment | Primary metric | Predicted (point + interval) | Actual | Inside interval? | Surprise notes |
|---|---|---|---|---|---|---|
| 2026-03-02 | invoice-triage-C1 | misrouting rate, paired delta | −4pp [−7pp, −1pp] | −5.5pp | yes | slightly beyond the point estimate, still inside |
| 2026-05-01 | invoice-triage-C2 | misrouting rate, paired delta | −6pp [−9pp, −3pp] | −1.2pp | no | INCONCLUSIVE result — overestimated effect size; candidate-B's gain concentrated in one stratum |
| 2026-06-10 | invoice-triage-C3 | p95 latency, ms | −80 [−120, −40] | −95 | yes | |
| 2026-07-22 | invoice-triage-C4 | misrouting rate, paired delta | −3pp [−6pp, 0pp] | −0.5pp | yes | inside interval but near the floor — direction right, magnitude optimistic |

**§2 Scoring, as of 2026-07-22:** coverage = 3/4 (75%, nominal target ~80% —
read as anecdote at 4 entries). Systematic bias: three of four predictions
overshoot the actual effect size on misrouting-rate metrics; treat the next few
point estimates for that metric family as candidates for a downward adjustment,
and revisit once entries reach the double digits.

---

**Governing chapters:** [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)

**Related templates:** [EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md) ·
[TEST_LOOK_LEDGER.md](TEST_LOOK_LEDGER.md) ·
[METHOD_DECISION_RECORD.md](METHOD_DECISION_RECORD.md)

[Index](../README.md) · [Glossary](../GLOSSARY.md)
