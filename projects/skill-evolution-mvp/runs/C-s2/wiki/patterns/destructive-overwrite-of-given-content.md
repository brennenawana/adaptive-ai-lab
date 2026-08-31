# Destructive overwrite of pre-existing content

## Pattern
While filling the target range, the agent also mutates cells it was never asked to touch: pre-filled sample answers, existing formulas, or whole columns.

## Root cause
The agent optimizes for "my final file is internally consistent / has no formulas" rather than "minimal diff from input plus the requested change". Graders usually compare the whole sheet, so every gratuitous change is a lost point — and destroyed formulas also destroy cached values the grader may read.

## Evidence (iteration 2)
- **36097**: instruction said only "formula in column H" + "preserve the formatting of column I". Agent rewrote **column G** (`=D3+F3` → literals 34600/8100/800/100), wrote H7 as a literal replacing `=SUM(H3:H6)`, and overwrote the given H3=5000 / H4=2250. soft=0.
- **58484**: agent looped `for row in 1..27: ws.cell(row,7).value = None; cell.border = Border()` clearing all of column G, and blanked H rows that already contained the user's expected results. soft=0.
- **370-43**: `ws.insert_rows()` on a sheet containing `A6 = '=IF(C6="","X","")'` shifts rows under existing formulas without checking the demo sheet for the intended end state. soft=0.

## Contrast (soft=1.0)
- **408-39** touched only B5:B10; **48080** touched only C2:C6; **42354** touched only D2:D8. Minimal diff.

## Fix
1. Write **only** the cells named in the instruction's answer region.
2. Never convert an existing formula to a literal; leave it alone (its cached value is already in the file).
3. Only clear a column/border if the instruction explicitly demands it, and clear exactly what it names.
4. Final check: reload input and output, print every coordinate whose value differs, and justify each one:
```python
diff = [(c.coordinate, a.value, b.value) for ra, rb in zip(wa.rows, wb_.rows)
        for a, b in zip(ra, rb) if a.value != b.value]
```

## Iteration 3 evidence
- **247-24** (soft=0): the most destructive variant yet — `main_ws.delete_rows(2, main_ws.max_row)` wiped every data row, then the agent re-wrote header + rows from a Python list. All cell styles, number formats and column widths were lost, and the formulas in I–L were re-pasted at wrong row numbers. The requested changes (2 deletions, a bill-rate update, blank-row insertion, a VLOOKUP fill) touched at most 4 columns; the diff touched the entire sheet.
- **36097** (soft=0): repeat offender — overwrote the given `H3 = 5000` with its own 4000.

Added rule: never clear-and-rebuild a sheet. Mutate in place, cell by cell, so untouched cells keep their styles and cached values.

## Iteration 4 evidence
- **194-19** (soft=0, second time): rows 2–9 of Sheet1 were the user's own completed answer for the first meet (`I=None,2,4,3,None,None,1,...`). The agent wrote `sheet1.cell(row, 9, result_val)` for **every** row it matched, including those 8 — replacing the answer key with a single constant per race. It also overwrote column H (`'(P)'`) on rows that already had it. The instruction literally said "I've completed results for the first meet"; that region should have been read-only. See partially-completed-region-is-the-spec.md.
- **58484** (soft=1.0 this time): the contrast case. Clearing column G (`value = None; border = None`) was explicitly requested and was done exactly; the pre-filled H values were left in place. Minimal, instruction-justified diff -> 1.0.

Rule refinement: a cell may only be written if (a) the instruction names it as the answer region **and** (b) it is currently empty, or the instruction explicitly says to replace it. Pre-filled cells inside the answer region are ground truth, not scratch space.

