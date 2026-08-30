# Prediction Ledger

Before you run anything, you already expect something — otherwise you would not have
chosen to run it. This ledger is where that expectation gets written down, one line
per metric, while the answer is still unknown. When the result lands, you score the
line against it.

One scored line teaches you nothing. A handful teaches you something no single
experiment can: whether your expectations are any good. That is what turns "is this
experiment worth running?" from a matter of taste into an empirical question about
your own calibration, and it is the working form of the
[prediction ledger](../GLOSSARY.md#prediction-ledger). It also shows you whether your
surprises are genuine surprises or just optimism — a question only answerable against a
record written before you knew. Writing it down first is the uncomfortable part,
and the discomfort is the mechanism: a prediction that can be wrong in public is the
only kind that can teach you anything.

Where this sits relative to the rest: an
[experiment contract](../GLOSSARY.md#experiment-contract) fills its prediction register
at [freeze](../GLOSSARY.md#freeze) (its §1). This document is where that entry gets
scored, and where entries accumulate across every experiment you run.

> Index: [../README.md](../README.md) · Governing chapter: [04. Experiment Design and Statistics](../04_EXPERIMENT_DESIGN_AND_STATISTICS.md)

## When to use / when not to use

- **MUST** log one entry per primary metric at [freeze](../GLOSSARY.md#freeze) —
  before any qualification or confirmation look — mirroring the experiment contract's
  prediction register. Same numbers, now in the place where they get scored.
- **SHOULD** be kept at Tier 1 too, purely for the calibration practice. It costs one
  line and a moment of honesty, spent before the answer is available to lean on.
- **Do not** backfill a prediction after seeing the result. A row entered once a look
  has started is not a prediction. If it happens anyway, do not quietly drop it: mark
  the row `VOID (post-hoc)` and state why — a pattern of voided rows is itself a
  finding.
- **Do not** treat this ledger as a substitute for the statistical plan's
  [MDE](../GLOSSARY.md#mde) and verdict. A well-calibrated wrong-direction prediction
  and a badly-calibrated right-direction one both still need the primary/secondary
  statistics to call
  [CONFIRMED / REFUTED / INCONCLUSIVE](../GLOSSARY.md#verdict-vocabulary).

## Rigor-tier applicability

| Tier | Requirement |
|---|---|
| Tier 1 — Exploratory | Optional; recommended for the calibration habit. |
| Tier 2 — Consequential (default) | **MUST** be maintained — the prediction register is part of the frozen experiment contract (its §1), and the Freeze Checklist checks that it is filled. |
| Tier 3 — High-stakes/regulated | **MUST** be maintained, and scored entries are subject to the periodic methodology audit (chapter 12). |

Rigor attaches to the *decision's* consequence, same as elsewhere: any experiment whose
contract is required to freeze a prediction register (Tier 2+) is required to score it
here. See chapter 00 §6 (rigor dial) and [PROJECT_PROFILE.md](PROJECT_PROFILE.md).

---

## The Ledger

*Fill every section below. Placeholders in `[brackets]` carry inline guidance in
italics — replace the placeholder, keep or delete the guidance. No section may
be silently omitted; see ["Delete no section"](#delete-no-section) at the end of
this document.*

### 1. Ledger Table

One row per primary metric per experiment. Rows are appended, and the prediction columns
are written once — the later columns are the ones that get filled in.

| Date | Experiment | Primary metric | Predicted (point + interval) | Actual | Inside interval? | Surprise notes |
|---|---|---|---|---|---|---|
| [YYYY-MM-DD, ≤ freeze date] | [contract ID] | [the one metric named primary in the contract] | [point estimate; interval reflecting genuine uncertainty] | [scored result, filled after confirm] | yes \| no \| pending | [what you'd revise about your model of the system if this diverged] |

*Filling a row:*

- **Date** — when the prediction was written, which must be at or before the contract's
  freeze date. A row dated after the look started is not a prediction (see "When to
  use"), and the date column is what makes that checkable by someone else.
- **Primary metric** — the one metric the contract names primary, stated the way the
  contract states it: `misrouting rate, paired delta`, not `accuracy`. A vague metric
  makes the row unscoreable later, which is the same as not having written it.
- **Predicted** — a point estimate *and* an interval, because the two fail differently:
  the point tells you whether you are biased, the interval tells you whether you know
  how much you don't know. Make the interval wide enough to reflect real uncertainty;
  an interval you would not be surprised to miss is not doing calibration work.
- **Actual / Inside interval?** — left `pending` until the confirmation split reports,
  then filled from the scored result. The yes/no column is what §2 counts.
- **Surprise notes** — the column that pays for the rest. When the actual lands outside
  the interval, write what you would now revise about your model of the system, not why
  the run was unusual.

### 2. Scoring

**Coverage rate.** `count(inside interval? = yes) / count(scored)`, updated as rows
resolve.

Read that number against what your intervals *claimed*. An interval intended as an 80%
interval should contain the actual roughly 80% of the time over enough entries. A
coverage rate persistently far from nominal, in either direction, is a finding about
the intervals, not noise to explain away — too low means they are too narrow, too high
means they are so wide they commit to nothing.

**Systematic bias.** Track direction, not just hit rate: are predictions consistently
over- or under-stating effect size? Consistently too narrow (overconfident) or too wide
(underconfident)? Note any pattern here in prose as it becomes visible across rows —
this is where the ledger earns its keep.

**[PARAMETER]** The handful-of-entries rule: coverage rate is data-thin evidence — read
it as anecdote before roughly 5–10 scored entries have accumulated, and as a genuine
(if still small-sample) signal after. Calibrate this threshold against how often
consequential experiments actually run; the caution echoes vendor precedent for
treating small-n statistics as insufficient evidence rather than a verdict
[NV-EVALSDK-001]. The coverage arithmetic, the calibration curve, and how far a gap
from nominal has to be before it means anything are worked in
[references/STATISTICS_FORMULAS.md §12](../references/STATISTICS_FORMULAS.md#12-prediction-ledger-scoring).

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
