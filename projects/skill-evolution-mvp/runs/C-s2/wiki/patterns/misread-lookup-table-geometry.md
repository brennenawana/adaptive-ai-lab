# Misread helper-table geometry (thresholds vs payout grid)

## Pattern
The sheet contains a small helper block next to the data. The agent guesses that each sub-table is an independent set of results and combines them arithmetically (interpolation, `a + b - base`, averaging) instead of reading the block as *boundaries + grid*.

## Root cause
In hand-built Excel models the first row (or column) of a helper block holds **bucket boundaries for another dimension**, and the body holds either thresholds or payouts. Two adjacent blocks are usually "thresholds table" + "result grid", not "two result grids". The agent never tests its reading against the number the prompt quotes.

## Evidence: task 6239 (soft=0 in both iteration 2 and iteration 3)
Layout actually present in the file:
```
J2:M2 = 0.65 0.75 0.85 0.95        <- Goal bucket boundaries
J3:M6 = 0    0    0    0           <- Variance thresholds, PER GOAL BUCKET
        .03  .02  .015 .01
        .05  .04  .03  .02
        .07  .06  .045 .04
P2:T2 = -0.2 -0.1 0 0.1 0.2        <- Metric2 bucket boundaries
P3:T6 = .03 .04 .05 .06 .07        <- PAYOUT GRID, rows = variance band
        .04 .05 .06 .07 .08
        .05 .06 .07 .08 .12
        .06 .07 .08 .12 .18
```
Correct rule: pick the goal-bucket **column** of J3:M6, walk down it to find which variance band the employee's Variance falls in, then read `P..T` of that band's **row** at the employee's Metric2 bucket.

This reproduces both numbers quoted in the instruction: Goal 65-74% + Variance 0-3% + Metric2 -20..-10% -> `P3 = 0.03 = 3%`; same with Metric2 > 20% -> `T3 = 0.07 = 7%`.

What the agent did instead (twice): `incentive = goal_payout[goal_bucket] + metric2_payout[metric2_bucket] - base_payout`, producing 0.18 / 0.045 / 0.0 — and, critically, **3% is unreachable** under that model. It also hardcoded variance bands 3%/5%/7% for every goal bucket, ignoring that J3:M6 makes the bands goal-dependent.

## Fix
1. Before coding, label every helper cell: is this row/column a *boundary list* (monotonic, matches a dimension named in the prompt) or a *result*?
2. A block whose header row equals another dimension's boundaries is a **lookup keyed by that dimension** — index into it, do not sum across it.
3. Implement the rule, then `assert` it reproduces every worked example quoted in the prompt before writing any cell. If an outcome the prompt names (e.g. exactly 3%) cannot be produced by your model at all, the model is wrong. See contradicting-provided-examples.md.

## Iteration 4: 6239 fails a third time — right table, wrong axis
The summation model is gone (progress), replaced by a clean 2-D grid lookup — indexed on the **wrong dimension**:
```python
# agent's iteration-4 code
payout_grid[goal_bucket][metric2_bucket]      # rows indexed by GOAL
```
But `P3:T6`'s rows are **variance bands**, not goal buckets; `J2:M2` (goal boundaries) selects which *column* of `J3:M6` supplies the variance thresholds, and the resulting variance band selects the payout row. Goal never indexes `P3:T6` directly.

The trap: this wrong axis assignment still reproduces both numbers quoted in the prompt, because `payout_grid[0]` is simultaneously "goal bucket 0" and "variance band 0" and both examples lie there. Column E (`Varince to Goal`) and the whole `J3:M6` block were never read.

Diagnostic to add before coding: for each grid, name its row axis and its column axis out loud, and check the count matches — `P3:T6` has **4 rows** and `J3:M6` has **4 rows** of thresholds (one band per row) but `J2:M2` has 4 *goal* columns; the 4 grid rows correspond to the 4 threshold rows, not to the 4 goal columns. When two dimensions share a cardinality, cardinality alone cannot disambiguate — use the semantic order (thresholds table feeds the grid's row index). See dropped-dimension-in-rule.md.

