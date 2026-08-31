# Structural row edits break formulas, styles and cached values

## Pattern
The task asks to insert/delete/move rows (often phrased "write VBA that..."). The agent uses `ws.insert_rows()` / `ws.delete_rows()` or rebuilds the sheet by rewriting cell values, prints a tidy before/after listing, and scores 0.

## Root cause
openpyxl is not Excel. When you shift rows it does **not**:
- translate relative formula references (a formula 10 rows below an insertion still points at the old rows);
- carry merged ranges, conditional formatting, data validation, row heights or styles into the new rows;
- populate the inserted row with the neighbouring row's formula/format.

And when you rebuild a sheet by copying `cell.value`, you copy the formula **text**: `'=G2*H2'` written into row 25 still multiplies row 2. Additionally every pre-existing formula loses its cached `<v>` on an openpyxl round-trip, so a grader loading with `data_only=True` sees `None` across the file.

## Evidence (iteration 3, both soft=0)
- **370-43**: sheet `Before Insert Row`, 2483 rows x 20 cols, column A driven by `A6 = '=IF(C6="","X","")'`. Agent found X at rows 18/32/43 and ran `ws.insert_rows(x_row)` bottom-up. The three new rows are value-less and style-less, and every formula below them keeps its old references. Verification was only the agent's own printout of the in-memory sheet.
- **247-24**: `main_ws.delete_rows(2, main_ws.max_row)` followed by a full rewrite of 63 rows. Columns I–L held `'=G2*H2'`, `'=G2-30'`, `'=J2*H2'`, `'=I2-K2'` etc.; these strings were written verbatim into their **new** row numbers, so after deleting 3 rows and inserting 20 blanks essentially every reference is wrong. All formatting was also destroyed by the delete+rewrite.

## Fix
1. Snapshot formula cells first: `pre = {c.coordinate: c.value for row in ws.iter_rows() for c in row if isinstance(c.value,str) and c.value.startswith('=')}`.
2. After any shift, **regenerate** each moved formula for its new row: `ws.cell(r, 9, f'=G{r}*H{r}')` — never copy the old string. If the grader reads values, write the computed literal instead (see formula-written-but-no-cached-value.md).
3. For inserted rows, copy `_style` / `number_format` from the row above unless the reference sheet shows otherwise.
4. Verify by reloading the saved file and printing 3 rows either side of every insertion/deletion point, plus an explicit check such as `assert ws['I25'].value == '=G25*H25'`.
5. Prefer the smallest structural operation that satisfies the instruction; a full delete-and-rewrite loses styles and is almost never what the grader expects.

## Iteration 4: 370-43 fails a third consecutive time — plus proof of silent data loss
Same `for row_idx in sorted(x_rows, reverse=True): ws.insert_rows(row_idx)` on rows [18, 32, 43]. New evidence from the agent's own two printouts:

- In-memory after insert: `Row 19: A=X, C=` (C holds the empty string `''`, as in the input).
- Reloaded from the saved file: `Row 19: A=X, C=None`.

So the save round-trip **dropped the empty-string cell value** on the shifted rows. Anything a grader compares cell-by-cell will differ. The inserted rows themselves are value-less and style-less, and `A6 = '=IF(C6="","X","")'` (the formula that generates the X markers) is not filled down into them.

Cumulative verdict after three failures: on this sheet, `insert_rows` alone is never sufficient. Build the target explicitly instead:
```python
rows = [[c.value for c in r] for r in ws.iter_rows()]        # snapshot values
styles = [[c._style for c in r] for r in ws.iter_rows()]     # snapshot styles
# construct the new row list with blanks inserted, then write every cell back
```
and finish by diffing the reloaded output against the input row-by-row, asserting that each source row's full tuple reappears at its expected new index — including `''` vs `None`.

