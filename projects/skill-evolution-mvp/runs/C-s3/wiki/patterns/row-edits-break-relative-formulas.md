# Row insert/delete via read-all-then-rewrite corrupts formulas and styles

## Pattern (FAILURE) — task 247-24, 0.000
The task required deleting rows, inserting 2 rows after each 'Ahmed Sons' row, and a VLOOKUP fill.
The agent did:
```python
data = [[ws.cell(r,c).value for c in range(1,14)] for r in range(2, ws.max_row+1)]
...filter/insert in the Python list...
for r in range(2, ws.max_row+1):
    for c in range(1,14): ws.cell(r,c).value = None   # wipe
for i,row in enumerate(data, start=2):                 # rewrite
    for j,v in enumerate(row, start=1): ws.cell(i,j).value = v
```

## Why it fails
1. Columns I..L held relative formulas `=G2*H2`, `=G2-30`, `=J2*H2`, `=I2-K2`. Moving row 2's data to
   row 5 carries the *string* `=G2*H2` with it → every moved row now points at the wrong source row.
   openpyxl does not translate references on assignment.
2. Wiping and rewriting drops nothing visually but leaves per-cell styles bound to the old row
   contents (blank inserted rows inherit the previous occupant's formatting).
3. `ws.max_row` is captured *after* rows grew, so the wipe/rewrite ranges are inconsistent.

## Correct approaches
- Use openpyxl's structural ops, iterating **bottom-up** so indices stay valid:
```python
for r in range(ws.max_row, 1, -1):
    if ws.cell(r,1).value == 'Motorcycle': ws.delete_rows(r)
for r in range(ws.max_row, 1, -1):
    if ws.cell(r,1).value == 'Ahmed Sons': ws.insert_rows(r+1, 2)
```
  (`delete_rows`/`insert_rows` still do not retarget formulas — see next bullet.)
- For any column containing relative formulas, either rewrite the formula for the new row
  (`f"=G{r}*H{r}"`) or, preferably, write the computed literal product.
- Re-read the instruction for cleanup clauses ("no output remaining in the deleted rows after the
  VLOOKUP") and explicitly blank the inserted/deleted rows' lookup column.

## Iteration 3: 247-24 retried with the recommended API — still 0.000
The agent followed this page's advice: it built `rows_to_delete`, sorted `reverse=True`, called
`ws.delete_rows(r, 1)`, then `ws.insert_rows(r+1, 2)` bottom-up. The structural result was right
(47 - 8 + 20 = 59 rows, blank inserted rows, M populated before deleting, G=180 applied). It still
scored 0 because of the formulas in I:L:
1. `delete_rows`/`insert_rows` **do not retarget formula text**. A row whose `I` said `=G20*H20`
   now sits at row 14 and still says `=G20*H20`, pointing at someone else's data.
2. openpyxl's save wiped the cached results of all 46 rows of I:L, so even the untouched rows read
   `None` (openpyxl-save-wipes-cached-formula-values.md).

**Therefore the mandatory first step for any row insert/delete task is to literalise formula
columns before moving anything:**
```python
vals = load_workbook(init, data_only=True)['Main']
for r in range(2, ws.max_row+1):
    for col in ('I','J','K','L'):
        ws[f'{col}{r}'] = vals[f'{col}{r}'].value   # number, moves safely with the row
```
Only then delete/insert rows bottom-up. Also re-check literal matching rules: the agent deleted on
`'Cycle' in company` (to catch 'Mehommod Cycle') rather than the stated `'Motorcycle'` — confirm
such a substring rule against the actual distinct values in the column before relying on it.

## Iteration 4: 247-24 regressed to read-all-then-rewrite (4th 0.000)
Despite this page's iter-3 guidance, the agent abandoned bottom-up `delete_rows`/`insert_rows` and
went back to the worst version:
```python
all_rows = [row for row in ws_main.iter_rows(...)]     # Cell objects
...build processed_rows, insert plain [None]*13 lists...
ws_main.delete_rows(2, ws_main.max_row)                 # nuke everything
for row_idx, row in enumerate(processed_rows[1:], start=2):
    ws_main.cell(row_idx, col_idx).value = cell.value   # copies '=G2*H2' text
```
Consequences: (a) `=G2*H2` strings landed on rows 5, 8, 11...; (b) all styles lost; (c) the VLOOKUP
pass ran over a list whose indices had already been shifted by the insertions, so the log shows
employee 1111 written twice (rows 2 and 29); (d) requirement 1 matched nothing
(confirm-filter-predicates-match-real-values.md).

## 370-43: `insert_rows` alone is not enough either
Inserting blank rows above each 'X' worked structurally, but the sheet's other formulas lost their
cached values on save, and the inserted rows inherit no styling/row height. For an insert-only task:
1. literalise all formulas from a `data_only=True` handle,
2. `insert_rows` bottom-up,
3. copy the style of the neighbouring row onto the inserted row if the expected output shows it,
4. diff `data_only=True` init vs output to prove nothing went blank.

