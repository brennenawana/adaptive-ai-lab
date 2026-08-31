# insert_rows/delete_rows Do Not Fix Formulas or Indices

**Type:** Failure pattern

## Problem
Multi-step "delete these rows, insert blanks after those rows, then VLOOKUP" jobs done with `ws.delete_rows` / `ws.insert_rows` produce a corrupt sheet.

## Evidence (task 247-24, score 0.000)
Sheet had formulas in I:L (`=G2*H2`, `=J2*H2`, ...). After:
```python
for r in sorted(rows_to_delete, reverse=True): main_sheet.delete_rows(r, 1)
...
for r in sorted(ahmed_sons_adjusted, reverse=True): main_sheet.insert_rows(r + 1, 2)
```
every surviving formula still referenced its ORIGINAL row numbers, so shifted rows compute from the wrong data. The agent also hand-adjusted `national_tv_rows` and `ahmed_sons_adjusted` by counting deletions — fragile bookkeeping that is easy to get off by one — and the instruction's "no output remaining in the deleted rows" was never explicitly enforced.

## Root cause
openpyxl's row shifting moves cell objects only; it has no formula translator and does not move merged ranges, conditional formats, or row styles.

## Fix
1. Read the whole sheet into a list of dicts/lists **first** (resolving formulas to computed values in Python).
2. Apply all deletes/inserts/updates/lookups on that list — no index arithmetic against the live sheet.
3. Clear the target range (`for row in ws.iter_rows(min_row=2): for c in row: c.value = None`) and rewrite every row from the list as literal values.
4. Reload and print the first ~20 rows plus row count to confirm the shape (expected rows = original - deleted + 2*inserted).

## Iteration 3: same task, same approach, still 0.000
247-24 improved one thing — it materialized cached formula values *before* shifting rows:
```python
for row in main_f.iter_rows(min_row=2, ...):
    if isinstance(cell.value, str) and cell.value.startswith('='):
        cell.value = main_v[cell.coordinate].value   # good: kills the stale-ref problem
```
but still called `delete_rows`/`insert_rows` on the live sheet and still failed, because:
- requirement #1 (delete `'Motorcycle'`) matched zero rows and was skipped (see zero-match-filter-check);
- the 20 inserted blank rows keep the row styles/borders of what they displaced, and "no output remaining in the deleted rows" was never enforced by clearing column M / the whole row;
- it re-scanned for `'Ahmed Sons'` *after* deleting, which is correct, but nothing checked the final shape.

Add to the fix list: after rewriting from the Python list, assert the arithmetic explicitly —
`assert ws.max_row == orig_rows - len(deleted) + 2*len(insert_after)` — and print the inserted-row indices to confirm they are fully empty.

## Iteration 4: 247-24 finally scored 1.000 — the live-sheet recipe that works
The agent stayed with `delete_rows`/`insert_rows` but fixed the three things that had broken it twice:
1. **Print the domain before filtering** (`Unique companies and counts: …`) so the zero-match Motorcycle requirement was a verified no-op, not a silent skip.
2. **Materialize every formula column to a literal BEFORE any structural change** — I=G*H, J=G-30, K=J*H, L=I-K were recomputed in Python (falling back to the `data_only=True` cached value) so no formula could survive with a stale row reference.
3. **Re-scan for target rows after every mutation instead of reusing pre-mutation indices**:
```python
for r in sorted(rows_to_delete, reverse=True): wsf.delete_rows(r, 1)   # bottom-up
# then RE-DERIVE, do not adjust by hand:
for r in range(2, wsf.max_row + 1):
    if wsf.cell(r,1).value == 'National TV' and wsf.cell(r,2).value == 'India':
        wsf.cell(r,7).value = 180
```
4. **Order matters:** delete → update → VLOOKUP-populate → materialize formulas → insert blank rows LAST. Inserting last guarantees the blank rows stay blank and nothing is written into them afterwards ("no output remaining in the deleted rows").

## Iteration 4 counter-example: 370-43 (0.000)
"Insert a row above every line where there is an X in A7:A1000." The insertion arithmetic itself was right (`insert_rows(r,1)` bottom-up for X at 18/32/43), yet it scored 0. What it never did:
- looked at only column A of a `max_row=2483, max_column=20` sheet — the other 19 columns shift too and were never inspected or verified;
- ignored that `A6` holds `=IF(C6="","X","")`, i.e. the X markers are formula-driven; rows 55/56 held `''` (a cached formula result). Formula-produced 'X' values below the scanned area, or rows whose cached value is `None`, are invisible to a `data_only=True` scan;
- never re-checked the formulas in the shifted region (`=IF(C6=...)` style refs are not retargeted);
- reported success on a 36-row printout of a 2486-row sheet.
When a marker column contains formulas, resolve the marker in Python from its *source* (here: `C{r} is None → 'X'`) over the full stated range, and verify the whole row content around every insertion point.

## Iteration 5: 247-24 REGRESSED 1.000 → 0.000 — same API, wrong ORDER
The only material difference from the iteration-4 winner is that the blank rows were inserted **before** the formulas were materialized:
```
Deleting row 9 / 8 / 7
Ahmed Sons rows after deletion: [2..11]
Inserting 2 rows after row 11 ... row 2        # 20 rows inserted, formulas now live at r+20
Updating Bill Rate at row 60..63 to 180
Materializing existing formulas...
  Warning: Formula in I48 has no cached value   # x ~40
```
Root cause: the materialization loop read `main_v[f'I{row_num}']` — but `main_v` is the *separate* `data_only=True` workbook, which never receives the inserts. Post-insert coordinates address the wrong (empty) rows, every lookup returned `None`, and the agent's code left the original `=G2*H2` strings in place. The output therefore ships formula strings with wrong row refs → grader reads `None`.

**Confirmed ordering contract (do not deviate):**
1. snapshot cached values into a Python dict keyed by ORIGINAL coordinate;
2. materialize / recompute every formula column to literals;
3. delete rows bottom-up, then RE-SCAN for targets;
4. apply value updates and lookups;
5. `insert_rows` LAST, bottom-up;
6. assert `ws.max_row == orig - deleted + 2*inserted` and print the inserted indices to prove they are empty.
See formula-cell-cached-value-loss for the snapshot step.

## Iteration 6: 247-24 fails a fourth time — this time it never finished
No new API bug; a process failure. The agent applied the VLOOKUP into column M *before* the deletions (trying to honor "no output remaining in the deleted rows" by skipping rows it planned to delete), then deleted rows, then needed to locate `National TV`/`India` rows and found its pre-deletion indices unusable:
```python
# Map to actual row in current worksheet (accounting for deletions)
# Actually, we need to track this differently since we've already deleted rows
pass
print("\nLet me restart with a better approach...")
```
The restart consumed the remaining budget and **no output file was ever saved**. Note the requirement "no output remaining in the deleted rows after the VLOOKUP" does not mean "skip those rows when populating" — it means delete first (or clear afterwards) so that the deleted/blank rows carry no column-M value. Populate M *after* the deletes and *before* the inserts, then assert the inserted rows are entirely empty.
See plan-pipeline-before-mutating: do the whole transformation on an in-memory list and touch the worksheet exactly once.

## Iteration 8: 247-24 fails a fifth time — the API was used correctly, the row SELECTION was fabricated
This run finally followed the ordering contract almost exactly: materialize formulas → delete bottom-up → re-scan for `National TV`/`India` → set G=180 → re-scan for `Ahmed Sons` → `insert_rows(r+1, 2)` in reverse → populate column M last, skipping rows whose column A is empty so the inserted blanks stay blank. Mechanically clean.

It still scored 0.000 because of *which* rows it deleted: `if company == 'Mehommod Cycle':  # Assuming this is 'Motorcycle'` removed five rows the user never named (see zero-match-filter-check). Structural surgery amplifies a selection error into an unrecoverable one — you cannot diff your way back to the rows you deleted.

**Add to the contract, as step 0:** print the domain of every column you will filter on, resolve each named value to either an exact normalized match or an explicit no-op, and echo the final `rows_to_delete` list with the full row contents *before* calling `delete_rows`. Deleting is the one operation with no undo.

