# A grid next to a lookup table is often band *edges*, not values to add

## Pattern (FAILURE) — task 6239, 0.000 (second attempt at this task)
The sheet holds two blocks:
```
J2:M2 = 0.65 0.75 0.85 0.95        <- 'Goal Buckets' header
J3:M6 = 0     0    0     0
        0.03  0.02 0.015 0.01
        0.05  0.04 0.03  0.02
        0.07  0.06 0.045 0.04
P2:T2 = -0.2 -0.1 0 0.1 0.2        <- 'Metric2' header
P3:T6 = the 4x5 'Pay out Grid' (0.03..0.18)
```
**Correct reading:** Goal selects a *column* of J:M; that column's four numbers are the variance
band edges *for that goal bucket*; the band gives the row 3..6; Metric2 gives the column P..T;
the payout is that one cell of P3:T6.

**Agent's reading:** J:M = "base incentive", P:T = "metric2 incentive", answer = base + metric2.

## Why the worked examples did not catch it
The prompt's two examples both sit in the Goal 65-74% / Variance 0-3% band, whose J:M entry is
`0`. Adding zero is indistinguishable from not adding at all, so both hypotheses printed
`Expected: 0.03, Got: 0.03 ✓`. Every actual employee had Goal ≈0.83-0.85 (the **K** column, edges
0/.02/.04/.06), but the agent hard-coded the J column edges (0/.03/.05/.07) into
`get_variance_row()` — so nearly every row was banded wrong *and* double-counted.

## Tells that a block is thresholds, not values
- Its numbers restate ranges quoted in the prompt ("0% to more than 7%", "65% to 99%", "-20% to +20%").
- The first row/column of the block is all zeros — a lower bound, not a payout of 0%.
- Each column is monotonically increasing (a ladder), and columns differ from each other.
- Bucket counts line up with exactly ONE grid: prompt said 5 Metric2 buckets × 4 variance rows,
  and P3:T6 is exactly 4×5. The other block must therefore be the banding key, not a second payout.

## Procedure
1. Write one sentence per table: "this block is <what> indexed by <row dim> × <col dim>".
2. Confirm every number in every block is consumed by your rule, and consumed once.
3. If your rule sums two blocks, ask whether one of them is a lookup index instead.
4. Build a discriminating test: pick inputs where the candidate rules disagree (here, any Goal in
   75-84% with variance 2.5%) and check that the sheet's own structure supports your answer.
