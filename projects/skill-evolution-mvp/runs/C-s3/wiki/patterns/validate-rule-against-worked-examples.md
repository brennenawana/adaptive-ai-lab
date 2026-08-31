# Derive the rule, then prove it on the given examples

## Pattern
Most of these tasks state an example in the prompt AND ship a few solved rows in the file.
Those are the only ground truth available — use them as unit tests.

### Successes
- 42354: agent first ran its `get_result(a,b,c)` against pre-filled D2:D5 and printed
  `computed=... expected=... match=True` for all four, *then* filled D6:D8 → 1.000.
- 192-22: agent built explicit `test_cases = [(row, should_match, text), ...]` including the
  tricky negatives ('Tesing' typo → no match, 'Interoperability Testing' → no match) and asserted → 1.000.

### Failures
- 6239: the instruction stated "Goal 65-74%, Variance 0-3%, Metric2 -20 to -10 → 3% incentive";
  the agent never evaluated that case. Its `payout_grid[variance_range][metric2_range]` ignores the
  Goal bucket entirely (goal bucket only picks variance thresholds), and its metric2 binning uses
  `< -0.1 → column P` even though P is labelled -20%. No example was ever reproduced → 0.000.
- 170-13: the agent's first output disagreed with Sheet3 on every row; instead of concluding its
  matching/ordering rule was wrong it began reverse-engineering which entries "should be included",
  and shipped a guess → 0.000.
- 3413: computed correct values (14, 27, 4, 11) matching the given G3/G4, then discarded them and
  wrote formulas → 0.000.

## Procedure
```python
expected = {r: ws[f'D{r}'].value for r in example_rows}   # pre-filled cells + prompt examples
for r, exp in expected.items():
    got = rule(*inputs(r))
    assert got == exp, (r, got, exp)      # rule is wrong -> iterate on rule, not on the data
```
Only after every example reproduces should you write into the blank cells.
If a stated example cannot be reproduced by any reading of the lookup table, re-read the table
orientation (rows vs columns, boundary inclusive vs exclusive) before proceeding.

## Iteration 3: the example must DISCRIMINATE (6239 again, 0.000)
This time the agent did run the check the wiki asks for:
```
Variance 0-3%, Goal 65-74%, Metric2 -20..-10%  Expected: 0.03, Got: 0.03 ✓
Variance 0-3%, Goal 65-74%, Metric2 > 20%      Expected: 0.07, Got: 0.07 ✓
```
and was still wrong, because its `base + metric2` rule and the correct `payout_grid[band][metric2]`
rule give the same answer whenever the base is 0 — and the base for that exact bucket is 0.
All real employees sat in a *different* goal bucket, where the two rules diverge.

**Addendum to the procedure:**
- After a rule passes the examples, ask "what other rule also passes these examples?" If you can name
  one, the test is degenerate; construct an input where they disagree and resolve it from the
  sheet's structure (see threshold-tables-vs-payout-tables.md).
- Prefer examples that exercise a *non-neutral* value (non-zero, non-identity, non-first-row).
- Check the examples cover the buckets your actual data falls into. Here every example was Goal
  65-74% while every employee was 83-85%.

### Iteration 3 successes
- 10452: printed `expected=... actual=... match=True` for all five pre-filled E4:E8 rows before
  filling E9:E12 → 1.000.
- 39931: asserted all 12 written cells against a pre-built `expected` map after reload → 1.000.

## Iteration 4: a non-reproducing example was noticed and shipped past (36097, 0.000)
Instruction: "if the asset sold at a loss, recoup ITV adjusted by the loss; if profit is less than
original cost, recoup the full profit; otherwise recoup the cost basis reduced by ITV."
Two worked rows were given, H3=5000 and H4=2250. The agent's own output:
```
Row 3: Profit 34600 >= Cost 4000 -> rule 3: Cost - ITV = 4000 - 0 = 4000
       Actual: 5000
       Difference: Could there be a different interpretation?
Row 4: Cost - ITV = 3000 - 750 = 2250   Actual: 2250 ✓ MATCH!
```
It then filled H5/H6 with the unmodified rule and shipped. **One example passing does not license
ignoring another that fails.** 50% agreement means the rule is wrong (or the row uses a branch you
haven't identified — e.g. a different Cost/Book-value basis for fully-depreciated 2017 assets).

It also invented an unevidenced clamp: `max(0, itv + profit)` turned H6's −50 into 0, with the
comment "(Likely needs MAX(0, ...))". Never add a floor/cap/rounding the prompt does not state and
no example demonstrates — if the natural reading gives a negative number, write the negative number.

**Hard gate before writing:**
```python
for r, exp in given_examples.items():
    got = rule(r)
    if got != exp:
        raise SystemExit(f'STOP: row {r} rule={got} given={exp} — re-derive, do not write')
```

