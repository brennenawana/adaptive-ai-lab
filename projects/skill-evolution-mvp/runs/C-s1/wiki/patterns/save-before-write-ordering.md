# Saving the Workbook Before Writing the Output Cells

**Type:** Failure pattern

## Problem
Output file is saved (or the sheet handle re-fetched) before the target cells are populated, so the artifact on disk is empty or stale.

## Evidence (task 22-47, score 0.000)
```python
wb.save('1_22-47_output.xlsx')   # <-- saved first
ws = wb['sheet1']                # "refresh reference"
for row in range(2, 11):         # clearing + writing happens AFTER the save
    ...
```
The final write loop was never followed by a second `wb.save(...)` in the trace, so the graded file could not contain the sorted result.

## Fix
1. Order strictly: load -> compute -> write all cells -> `wb.save(out)` **once, last**.
2. Never re-derive `ws` after a save expecting a fresh object; openpyxl keeps the same in-memory workbook.
3. Always finish with a reload check:
```python
chk = openpyxl.load_workbook(out, data_only=True)
print([chk['sheet1'][f'G{r}'].value for r in range(2, 11)])
```
If any expected cell is `None`, the task is not done.