# Hardcoded Row Windows Produce Partially-Filled Output

**Type:** Failure pattern (highest impact in iteration 3)

## Problem
The agent picks an arbitrary inspection window (`range(1, 15)`, `range(2, 5)`), never prints `ws.max_row`, and then reuses that same window for computing AND for verifying. The output covers only the first few rows, and the verification loop — reading the same window — reports success.

## Evidence (iteration 3)
- **32438 (0.000):** inspected rows 1-4 only, then `for row in range(2, 5): ws[f'J{row}'] = ...`. Only J2:J4 written; the sheet is an "Email Campaign" log with unknown (larger) row count.
- **10452 (0.000):** dump loop `for row in range(1, 15)`, then PK scan `for row in range(4, 15)` on column B. Any material below B14 was never seen; the final "FINAL RESULT" print only re-listed E4:E12.
- **Contrast, 48080 (1.000):** printed `Dimensions: A1:C89` first, then probed A25/A41/A57/A73/A89 to the true last row.
- **Contrast, 39931 (1.000):** looped `range(3, 23)` after seeing `Dimensions: B1:K22` — window derived from the file, not guessed.

## Root cause
The window is chosen before the file's extent is known, and the same constant is copy-pasted into the write and the verify step, so truncation is invisible.

## Fix
1. First command on every task:
```python
print(ws.title, ws.dimensions, ws.max_row, ws.max_column)
for r in ws.iter_rows(values_only=True):  # full dump if small
    ...
```
2. Derive the last data row from the data: `last = max(r for r in range(1, ws.max_row+1) if ws.cell(r, col).value is not None)`.
3. Loop to `last`, never to a literal you typed by hand.
4. Verify with an INDEPENDENT count: `sum(1 for r in ... if ws[f'J{r}'].value is not None)` must equal the number of source rows that qualify.
5. If the target column already has a header plus N pre-filled example rows, the output almost always must extend to the last populated row of the SOURCE column.

## Iteration 4 evidence — the window can also be a COLUMN window
- **194-19 (0.000):** `for row in range(2, min(30, sheet1_v.max_row + 1))` to collect distinct meets on a 372-row sheet → printed `Unique meets: ['PORT MACQUARIE']`. The whole task is "repeat for each meet"; the agent believed there was only one, so its rule was never tested against a second group.
- **370-43 (0.000):** `Max row: 2483, Max column: 20` was printed, then every subsequent command touched column A only. Rows were inserted into a 20-column sheet whose other 19 columns were never inspected before or after; the final verification printed `A15..A50` of a 2486-row sheet.
- **263-1 (0.000):** hardcoded `$A$2:$A$276` while advertising the result as "dynamic".

**Add to the fix list:** the extent check has two axes.
```python
print(ws.title, ws.dimensions, ws.max_row, ws.max_column)
# and for any structural edit, dump the FULL row, not just the key column:
print([c.value for c in ws[row_idx]])
```
When the task says "for each X … until the end of the sheet", first print `len(set(all values of X over the FULL range))` and assert it is > 1 before trusting a rule derived from one group.

## Iteration 5: truncating the OUTPUT to an assumed range (22-47, 0.000)
```python
output_rows = final_sorted[:9]   # "Only 9 rows for F2:H10"
```
There were 10 qualifying rows. The agent invented the target range `F2:H10` (the prompt never states it), then silently discarded a data row to make the data fit the guess. Related in the same run: `header_rows = {1, 8, 14, 21}` — header rows enumerated by eye from a partial dump instead of detected (`B == 'NAME' and C == 'REF'`) across `max_row`, which breaks the moment the user "handles new ranges that contain headers" as the prompt explicitly requires.

**Rules:** the number of output rows is an OUTPUT of the computation, never an input. If your result does not fit the range you assumed, the assumption is wrong — extend the range and print `len(result)` next to the number of rows written. Detect structural markers (headers, blank separators, group starts) with a predicate over the full range; never hardcode their row numbers.

## Iteration 6: the truncated window hid the ORACLE the user told us existed (56786, 0.000)
The prompt says: *"I filled in a couple of examples of how I would calculate the average"* and quotes `AVERAGE(B24:B69)`. The agent's search for those examples was:
```python
for i in range(1, min(30, wsf.max_row + 1)):   # sheet is 515 rows, data runs 4..200
    if wsf[f'C{i}'].value is not None: ...
```
Nothing printed, and the agent never mentioned the missing examples again — it invented its own window semantics (`threshold < date <= current`), wrote 197 literals to C4:C200, and "verified" row 20 by re-running its own rule. The one artifact that could have decided the window semantics (does the average include the current row? is it 365 days back from the row's date or a fixed block?) was 40+ rows below the scan limit.
**Rule:** when the prompt claims examples/reference values exist, search the ENTIRE used range for non-empty cells in the target column before writing anything —
```python
prefilled = {r: ws.cell(r, col).value for r in range(1, ws.max_row+1) if ws.cell(r, col).value is not None}
print('pre-filled target cells:', prefilled)     # must be non-empty if the user says so
```
If it comes back empty, the user's claim and the file disagree — say so and look on other sheets (see replicate-completed-example-block).

22-47 repeated `final_sorted[:9]` in this iteration too — the same silent drop of the 10th row, two iterations running.

## Iteration 7: 56786 searched for the oracle again — and stopped 45 rows short
The prompt quotes the user's own example as `AVERAGE(B24:B69)`. The agent's search for pre-filled examples:
```python
print("Checking for existing examples in column C:")
for row in range(4, 25):        # stops at 24; the quoted range ends at 69
    if wsf[f'C{row}'].value is not None: print(...)
# (prints nothing, no comment)
```
It had *already* computed `last_row = 200` and `max_row = 515` in the same command — the bound was available and simply not used. It then wrote 197 literals under invented window semantics.

**Mechanical rule:** any search for "does the user's example exist?" must run over `range(1, ws.max_row+1)` — there is no cost argument for a 515-row sheet. And when the prompt quotes specific cell coordinates (`B24:B69`), those coordinates set the minimum extent of your search.
