# Skill Impact History

## Iteration 1 — create `excel_write_values_and_verify` — **REJECTED**
- validation score: 1.0000 (best before: 1.0000)

```diff
--- a/excel_write_values_and_verify/PURPOSE.md
+++ b/excel_write_values_and_verify/PURPOSE.md
@@ -0,0 +1,13 @@
+# Purpose
+
+## Origin
+Created after iteration 1 of the smoke-C training run: task 57445 scored 0.000 while task 141-20 scored 1.000. The failing trace wrote a semantically correct SUMIFS into E2:E5 with openpyxl, saved, and shipped. Because openpyxl stores no cached value, every graded cell read as `None`. The agent's "verification" step loaded the real cells but printed a hardcoded expected-value list instead, so the failure was invisible and the agent declared success.
+
+## Patterns Addressed
+- wiki/patterns/excel-formula-needs-cached-values.md — formulas saved without `<v>` grade as empty.
+- wiki/patterns/fake-verification-hardcoded-expectations.md — verification that prints beliefs rather than observed cell values.
+- wiki/patterns/avoid-cse-array-formulas.md — CSE array formulas and full-column refs as portability hazards.
+- wiki/patterns/inplace-workbook-edit-preserves-structure.md — the 141-20 success pattern: mutate the loaded workbook, save to the exact output name, re-open and print actual state.
+
+## Evolution History
+- v1 (iteration 2): initial creation. Combines the "compute values, recalc or write literals" fix with strict observe-don't-assert verification rules and explicit anti-signal phrases.
--- a/excel_write_values_and_verify/SKILL.md
+++ b/excel_write_values_and_verify/SKILL.md
@@ -0,0 +1,58 @@
+---
+name: excel_write_values_and_verify
+description: Make SpreadsheetBench edits land as real cell VALUES (not just formula strings) and verify by re-reading the saved file. Use for any task that writes formulas, computes results, or edits an .xlsx that will be graded on cell values.
+---
+
+# Write real values, then verify by observation
+
+## When to Apply
+- Any task whose instruction says "create a formula", "calculate", "look up", "fill in column X".
+- Any task where you edit an .xlsx with openpyxl and then declare it done.
+- Any time you are about to write a final summary claiming values like "E2 → 2".
+
+## When NOT to Apply
+- Pure formatting / structural tasks with no computed results (row deletion, renaming, styling) — use the in-place edit + full reprint pattern instead.
+
+## Instructions
+
+### 1. Compute the answer in Python first
+openpyxl is NOT a calculation engine. `wb.save()` writes `<f>` (the formula string) with no cached `<v>`, so a grader reading values (or `data_only=True`, or pandas) gets `None` and you score 0 — even if the formula is perfectly correct (confirmed on task 57445 with a valid SUMIFS).
+
+So: replicate the lookup/aggregation in Python, get concrete numbers, and know them before writing.
+
+### 2. Write both formula and value when a formula is requested
+Preferred order:
+1. Write the formula with openpyxl and `wb.save(out)`.
+2. Recalculate headlessly so cached values exist:
+   ```bash
+   soffice --headless --convert-to xlsx --outdir . 1_<task>_output.xlsx
+   ```
+3. Re-open with `data_only=True` and confirm every target cell is non-None.
+4. **If soffice is unavailable or any target is still None, overwrite those cells with the Python-computed literal values and save again.** A literal correct value always beats an uncached formula. Mention the formula text in your final message for the user.
+
+### 3. Formula hygiene (if you do write formulas)
+- Use SUMIFS / SUMPRODUCT / LOOKUP; never `INDEX/MATCH(1,(A=x)*(B<=y),0)` — that needs Ctrl+Shift+Enter and silently fails elsewhere.
+- Use bounded ranges (`$A$2:$A$19` from `ws.max_row`), never `$A:$A`.
+- Drop `IFERROR(...,"")` while testing — it hides #N/A as blank.
+
+### 4. Verification must observe, never assert beliefs
+Rules, in order of importance:
+1. Re-open the **saved output file** in a *fresh* load: `wb = load_workbook(out, data_only=True)`.
+2. Print `repr(cell.value)` straight from that workbook. **Never print a variable from a hand-written expected-values list.** In the 57445 failure the agent loaded `value_cell` and then printed a hardcoded `expected` column — the table looked right while every real cell was `None`.
+3. Assert, don't eyeball:
+   ```python
+   for r in range(2, 6):
+       v = wb['Pricing'][f'E{r}'].value
+       print(r, repr(v))
+       assert v is not None, f"E{r} empty — task NOT done"
+   ```
+4. If a loaded cell object is assigned but never printed, your check is vacuous — fix it.
+5. Seeing `None` means fix the file, not soften the check.
+
+### 5. Anti-signals — if you are about to write any of these, stop and fix the file
+- "the formulas will evaluate correctly when opened in Excel/LibreOffice"
+- "Formula set" as a stand-in for an actual value in a verification table
+- A results table whose numbers you typed yourself rather than read back
+
+### 6. Output file
+Save to the exact expected name `<n>_<taskid>_output.xlsx` in the working directory, and edit the loaded original workbook in place (never regenerate via pandas `ExcelWriter`) so other sheets, highlighting, and formatting survive.
```
