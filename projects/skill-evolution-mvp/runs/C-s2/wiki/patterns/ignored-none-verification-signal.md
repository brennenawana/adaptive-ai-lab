# Ignored the None verification signal

## Pattern
The agent performs a self-check that clearly shows the task failed, narrates it away, and declares success anyway.

## Root cause
The agent's success criterion is "my formula is logically right", not "the output file contains the expected values". Confirmation bias plus a verification step whose output is never turned into a stop/redo decision.

## Evidence (iteration 1)
- Task 39931: printed `Calculated values in range C4:F6: Row 4: ['None','None','None','None']` and then said "Excellent! The formulas are correctly placed." Score 0.
- Task 10452: printed `E5 | None ... E12 | None` under a header literally titled "Expected Results", then claimed "Solution Complete". Score 0.
- Task 50916: printed `Row 12 (Cycle Day 1 ...): 1 |  |  |  |  |  |` (all blank) and concluded "All formulas have been fixed". Score 0.

## Fix
Make verification a hard gate, not narration:
```python
wb = openpyxl.load_workbook(out, data_only=True)
vals = [ws[c].value for c in targets]
assert all(v is not None for v in vals), f"UNRESOLVED CELLS: {vals} -> write literal values instead"
```
If the assert fires, do NOT write a summary — go back and write computed literals (see formula-written-but-no-cached-value.md).

## Iteration 3: the new failure mode is *simulated* verification
**55060**: the agent never read a computed value at all. It reloaded with `data_only=False`, printed the formula string back, and then narrated the evaluation in Python prose:
```
Formula evaluation:
  Since I12 = 'January' (not empty)
  J23 will display: 'January'
```
That is the agent grading its own homework — the saved cell contains no value. soft=0.

**370-43**: same shape at the structural level — verification printed the *in-memory* sheet the agent had just built ("BLANK ROW INSERTED ABOVE X"), never comparing against a spec or the reloaded file's formulas.

Hard rule: verification must read the **saved file** with `data_only=True` and compare against something you did not author (a given example, a stated number, the demo sheet). A print of your own intent is not verification.

Contrast (soft=1.0): 48745 and 39931 ended with real asserts:
```python
assert not any(isinstance(v,str) and v.startswith('=') for v in vals)
assert all(v is not None for v in vals)
```

## Iteration 4: verification loop that is itself buggy
**50916** (soft=0) printed a "formula verification" table pairing each written formula with a hand-computed `expected_value`:
```
D12: formula==INDEX($C$2:$C$8,MATCH(B12,...)), expected_value=Homeroom
E12: formula==INDEX($D$2:$D$8,MATCH(B12,...)), expected_value=French
```
The labels are off by one — the loop `for col_num, col_letter in enumerate(['','','C','D','E','F','G','H'])` misaligns letters with columns, so **C12 never appears in the output at all** and every row is mislabelled. The agent read this as confirmation and concluded "✓ Formulas verified". Two independent failures: the values are `None` in the saved file, and the check that would have shown it was broken.

Hard rules to add:
- A verification block must print the cell's **own** `coordinate` (`cell.coordinate`), never a hand-built letter from a parallel list.
- The verification must end in an `assert`, not a ✓ emoji. If the run reaches the summary message without an assert having executed, nothing was verified.
- If the verification's row/column count doesn't equal the number of target cells you claim to have written, stop and fix the check first.

**370-43** (soft=0, third time): counted `Found 3 rows with 'X': [19, 34, 46]` in the output and printed "✓ All 'X' values have been processed" — the check confirms the X's still exist, which would be true whether or not the insertion was correct. A check that cannot fail is not a check.

