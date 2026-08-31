## Origin

Created after iteration 1 of the SpreadsheetBench training set: 24 of 30 tasks scored 0.000.
Traces read: 32438, 263-1, 22-47, 6239, 194-19 (plus wiki evidence for 39931, 10452, 472-15,
55060, 50916, 408-39, 66-24, 170-13).

## Patterns Addressed

1. **formula-strings-score-zero** — every 0.000 task ended with an Excel formula string in the
   answer cells (`=MOD(I2,1)` in 32438, `=SUMIF(...)` in 263-1, a 2000-char nested `=IF` in
   6239). openpyxl stores no cached result, so a grader reading values sees `None`. Every
   1.000 task wrote literal computed values.
2. **Ignoring / overwriting the worked example** (new). The init file ships a partially
   completed answer that fully determines the rule:
   - 194-19: the first meet's column I was filled and proves the mapping is by *Tab number*;
     the agent filled positionally by row index and also overwrote given column-H values.
   - 6239: a real payout grid sat in P2:T6; the agent fabricated 60 additional payout numbers.
   - 263-1: `metal`/`PVC` totals were pre-given; the agent replaced them with formulas.
   - 22-47: the agent injected an extra header row into the answer range, offsetting all rows.
3. **verify-answer-range-values-not-formulas** — verification steps echoed the just-written
   formula string; the skill mandates a `data_only=True` reload asserted against an
   independently built `expected` map that includes the pre-given cells.
4. **dynamic-header-lookup-not-hardcoded-columns** — reinforced by requiring a full typed dump
   before deciding coordinates, instead of truncated `pd.read_excel` output.

## Evolution History

- v1 (iteration 1): initial creation. First skill in the repository; no prior proposals existed
  in skill-impact.md. Combines the mandatory compute-then-write-literals recipe with the
  calibrate-against-the-worked-example rule, since the two failure modes co-occurred in every
  trace inspected.
