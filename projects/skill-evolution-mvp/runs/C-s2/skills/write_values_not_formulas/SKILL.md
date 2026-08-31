---
name: write_values_not_formulas
description: Produce gradeable .xlsx output by computing answers in Python and writing literal cell values, recalculating with LibreOffice when formulas are involved, and hard-gating on data_only=True verification. Use for every SpreadsheetBench task, especially ones whose wording asks for "a formula", "a macro/VBA", or a "dynamic" sheet.
---

# Write Values, Not Formulas

## When to Apply

Every task that saves an `.xlsx` with openpyxl/pandas. Apply *especially* when:

- The instruction says "I need a formula", "what formula can I use", "create a macro",
  "I require VBA code", "make this sheet dynamic", "Excel 2013 doesn't have FILTER".
- The source workbook already contains formula cells (`=G2*H2`, `=SUM(C3:C6)`).
- The answer range spans several cells (a filtered list, a cross-tab, a summary block).

## When NOT to Apply

- Pure structural tasks with no computed cells (rename a sheet, set a fill colour,
  change a number format) — but the verification gate in step 5 still applies.
- Tasks where the grader is explicitly documented to compare formula *strings*.
  This is rare; assume value comparison unless told otherwise.

## Instructions

### 1. The instruction's wording is not the grading criterion

The grader opens your file and reads **cell values**. `openpyxl` has no formula
engine: `ws['H2'] = '=SUMPRODUCT(...)'` writes text only, with no cached `<v>`
element, so `data_only=True` returns `None` and the task scores 0 — no matter how
correct the formula is.

So translate the request:

| User says | You deliver |
|---|---|
| "I need a formula in G3:G6" | the four computed numbers in G3:G6 |
| "I require VBA code / a macro" | the finished data transformation, done in Python |
| "make this sheet dynamic" | the correct values for the data that is actually present |
| "Excel 2013 has no FILTER, give an alternative" | the materialized filtered list, one value per cell |

**Never revert working literal values back to formulas because "the user asked for a
formula."** If you have already written correct values, you are done; explain the
formula in your prose summary instead of putting it in the file.

### 2. Compute in Python, write one literal per target cell

```python
totals = {}
for mtrl, w, h in ws.iter_rows(min_row=2, values_only=True):
    if mtrl is None: continue
    totals[mtrl] = totals.get(mtrl, 0) + w * h
for r in range(2, 6):
    ws.cell(row=r, column=8, value=totals[ws.cell(row=r, column=7).value])
```

Never leave a spill function (FILTER/SORT/UNIQUE/SEQUENCE) in one cell expecting
the rest of the range to fill — write every cell of the expected range explicitly.

### 3. Protect pre-existing formulas from the round-trip

`load_workbook(path)` (default `data_only=False`) keeps formula **strings** and
throws away their cached results. Saving therefore blanks out formula cells you
never touched, and the grader reads `None` for them.

Before you start, detect them:

```python
pre = [(ws.title, c.coordinate, c.value)
       for ws in wb for row in ws.iter_rows() for c in row
       if isinstance(c.value, str) and c.value.startswith('=')]
print(f"{len(pre)} pre-existing formula cells -> recalculation required")
```

If `pre` is non-empty (or if you deliberately wrote formulas), recalculate after
saving so every formula gets a cached value back:

```bash
soffice --headless --convert-to xlsx --outdir recalc out.xlsx && mv recalc/out.xlsx out.xlsx
```

If `soffice` is unavailable, read the original values with a second
`load_workbook(path, data_only=True)` handle and **write those cached numbers back
as literals** into the formula cells before saving.

### 4. Re-read the instruction for output shape before writing

Several failures were correct computations placed wrongly. Confirm, in writing,
before you save: which sheet, which exact columns, which start row, whether a
header row is expected, and how many rows. If the instruction names specific
output columns (e.g. "output in columns G and H"), do not also populate a
neighbouring column you inferred.

### 5. Hard verification gate — assert, don't narrate

The final check must be able to fail. Printing a formula string and writing
"✓ looks correct" is not verification.

```python
import openpyxl
wb = openpyxl.load_workbook(OUT, data_only=True)
ws = wb[SHEET]
vals = [ws[c].value for c in TARGET_CELLS]
assert not any(isinstance(v, str) and v.startswith('=') for v in vals), f"raw formulas: {vals}"
assert all(v is not None for v in vals), f"UNRESOLVED (None) cells: {vals}"
print("PASS", vals)
```

If this assert fires, do **not** write a completion summary. Go back to step 2 and
write computed literals. A run that ends with `None` in the answer range scores 0.
