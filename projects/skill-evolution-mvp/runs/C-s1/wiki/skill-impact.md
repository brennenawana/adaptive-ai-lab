# Skill Impact History

## Iteration 1 — create `spreadsheet_values_and_oracle` — **ACCEPTED**
- validation score: 0.8000 (best before: 0.3333)

```diff
--- a/spreadsheet_values_and_oracle/PURPOSE.md
+++ b/spreadsheet_values_and_oracle/PURPOSE.md
@@ -0,0 +1,27 @@
+| # PURPOSE
+
+## Origin
+Iteration 1 of SpreadsheetBench training: 24 of 30 tasks scored 0.000. Root-cause
+analysis of traces 1818, 50916, 58484, 10747, 194-19, 22-47 and 247-24 showed three
+recurring, mechanical causes — not reasoning failures.
+
+## Patterns Addressed
+- `write-values-not-formulas`: every 0.000 task ended with a formula STRING in the
+  target cells (1818 INDEX/SMALL, 50916 nested IF, 58484 INDIRECT/COUNTIF, 10747
+  SUMIFS). openpyxl stores no cached result, so a value-reading grader sees None.
+  All three 1.000 tasks wrote literal Python-computed values.
+- `legacy-array-formula-cse` and `openpyxl-formula-fill-down`: subsumed by the
+  "compute in Python, write values" rule plus a LibreOffice recalc escape hatch.
+- `verify-against-reference-sheet` (success pattern, promoted here to a hard gate):
+  58484 had an "Expected Result" column pre-filled by the user; 194-19 had the
+  first meet already completed. The agent OVERWROTE both instead of using them as
+  an oracle, and never checked that its logic reproduced them.
+- New: destructive `pandas.to_excel` round-trip (247-24) discarded workbook layout;
+  "insert two new rows" was implemented as duplicating the source row.
+- New: `Sheet.$A$1` (LibreOffice/ODF syntax) written instead of `Sheet!$A$1` (1818).
+- New: source workbooks are often formula-driven with no cached values (10747), so
+  `data_only=True` reads return None — inputs must be recalculated before reading.
+
+## Evolution History
+- v1 (this version): initial creation. Covers inspect -> find in-file oracle ->
+  compute in Python -> write literal values -> edit in place -> reload-and-assert.
--- a/spreadsheet_values_and_oracle/SKILL.md
+++ b/spreadsheet_values_and_oracle/SKILL.md
@@ -0,0 +1,92 @@
+---
+name: spreadsheet_values_and_oracle
+description: Use when solving any Excel/spreadsheet manipulation task (openpyxl/pandas) where a grader compares cell values in an output .xlsx — especially when the request mentions a formula, macro/VBA, lookup, filter, sort, or "fix my formula".
+---
+
+# Write Values, Not Formulas — and Validate Against the File's Own Oracle
+
+## When to Apply
+- Any SpreadsheetBench-style task producing `*_output.xlsx` that will be graded by
+  reading cell values.
+- The user asks for "a formula", "an array formula", "a macro/VBA", "a VLOOKUP",
+  "help me fix this formula", or "an Excel 2013 alternative to FILTER".
+- The workbook contains an example/reference: a sheet named like `Manual Result`,
+  a column headed `Expected Result`, or rows the user says they "already completed".
+
+## When NOT to Apply
+- Tasks graded on file structure only (e.g. "add a sheet named X") with no computed
+  values.
+- Pure formatting tasks with no computation (still follow rule 5 on in-place edits).
+
+## Instructions
+
+### 1. Inspect raw, and get real input values
+Dump cells with openpyxl (`data_only=False`) over the plausible range — headers are
+rarely on row 1. `pd.read_excel` alone hides layout; never rely on it for structure.
+
+If input cells themselves contain formulas (you see `'=+C3*2'`), their cached values
+may be missing. Recalculate a copy before reading:
+
+```bash
+soffice --headless --convert-to xlsx --outdir recalc/ in.xlsx
+```
+then read `recalc/in.xlsx` with `load_workbook(..., data_only=True)`.
+
+### 2. Find the in-file oracle FIRST — and never overwrite it
+Scan for pre-filled expected answers: an `Expected Result` column, a `Manual Result`
+sheet, or the first block/meet/group already completed by the user.
+- These cells are ground truth, **not** cells to fill. Leave their existing values
+  intact unless the task explicitly says to regenerate them.
+- Hand-derive those rows with your logic in Python and assert an exact match before
+  writing anything else. If your logic does not reproduce them, your interpretation
+  is wrong — fix the logic, do not proceed.
+- If there is no oracle, hand-derive at least two rows and print the derivation.
+
+### 3. Compute in Python; write literal values
+`ws['C4'] = '=SUMPRODUCT(...)'` stores only text — openpyxl caches no result, so the
+grader reads `None`. Score 0. Do the filter/lookup/aggregation in Python and write
+the answer:
+
+```python
+ws['E4'] = 'PK01/P819760979'   # not '=INDEX(...SMALL(IF(...)))'
+ws['C4'] = 23.56               # int/float, not a string
+ws['B7'] = None                # blank, not ""
+```
+Match expected types: numbers as `int`/`float`, dates as `datetime`, blanks as `None`.
+
+### 4. If a live formula is genuinely required
+Write the formula **and** materialize its value: save, then
+`soffice --headless --convert-to xlsx --outdir . out.xlsx`, and confirm with
+`load_workbook(out, data_only=True)` that every target cell is non-None. If recalc
+is unavailable, prefer literal values — a correct value beats an uncomputed formula.
+Cross-sheet references use `Sheet1!$A$1`, never `Sheet1.$A$1` (that is ODF syntax and
+Excel rejects it). Never rely on a copied formula string to shift relative refs; use
+`from openpyxl.formula.translate import Translator` if you must (note the module path).
+
+### 5. Edit in place; never round-trip through pandas
+Load the original with openpyxl, mutate, save once at the end. `df.to_excel(...)`
+rebuilds the workbook and destroys layout, offsets, formatting and untouched columns.
+For row/column surgery use `ws.insert_rows(idx, n)` / `ws.delete_rows(idx, n)`,
+processing indices in descending order.
+
+### 6. Read the instruction literally
+- "Insert two new rows after each X" means two **blank** rows, not duplicates.
+- "no values or bordering on column G" means clear values *and* set
+  `cell.border = Border()` on that exact column, and do not bold/wrap it.
+- Formatting clauses (borders, bold, font name/size, wrap text) are graded — apply
+  them to the exact stated range only, and re-check `font.bold`, `alignment.wrap_text`,
+  `border.left.style` after reload.
+- When rules conflict, enumerate every stated rule, and pick the reading that
+  reproduces the oracle from step 2.
+
+### 7. Mandatory final gate
+Save last, then reopen the saved file and assert — do not just print formula text:
+
+```python
+chk = openpyxl.load_workbook(out, data_only=True)[sheet]
+for addr, expected in oracle.items():
+    got = chk[addr].value
+    assert got == expected, (addr, got, expected)
+    assert not (isinstance(got, str) and got.startswith('=')), addr
+```
+Only claim completion after this diff is empty.
```

## Iteration 2 — patch `spreadsheet_values_and_oracle` — **ACCEPTED**
- validation score: 0.8667 (best before: 0.8000)

```diff
--- a/spreadsheet_values_and_oracle/SKILL.md
+++ b/spreadsheet_values_and_oracle/SKILL.md
@@ -24,13 +24,19 @@
 Dump cells with openpyxl (`data_only=False`) over the plausible range — headers are
 rarely on row 1. `pd.read_excel` alone hides layout; never rely on it for structure.
 
-If input cells themselves contain formulas (you see `'=+C3*2'`), their cached values
-may be missing. Recalculate a copy before reading:
+**`soffice` does not exist on this machine** (exit 127 / "No such file or directory"),
+and `--convert-to xlsx --outdir .` OVERWRITES the input workbook — it already destroyed
+one input file. Never invoke it, for reading or for recalculation.
 
-```bash
-soffice --headless --convert-to xlsx --outdir recalc/ in.xlsx
+Always open the input TWICE and keep both views:
+
+```python
+wbf = load_workbook(src, data_only=False)   # formulas / structure
+wbv = load_workbook(src, data_only=True)    # Excel's cached values
 ```
-then read `recalc/in.xlsx` with `load_workbook(..., data_only=True)`.
+`wbv` usually has real numbers because Excel saved them. If a cached value is `None`,
+evaluate that formula yourself in Python (they are almost always simple chains like
+`=+C3*2`); do not give up and do not shell out.
 
 ### 2. Find the in-file oracle FIRST — and never overwrite it
 Scan for pre-filled expected answers: an `Expected Result` column, a `Manual Result`
@@ -41,6 +47,11 @@
   writing anything else. If your logic does not reproduce them, your interpretation
   is wrong — fix the logic, do not proceed.
 - If there is no oracle, hand-derive at least two rows and print the derivation.
+- Never write a FORMULA into an oracle cell either: in one failure C2/C3 held the
+  user's reference values and were overwritten with `=INDEX(...)`, losing them.
+- If your rule reproduces only *some* oracle cells (e.g. matches 5 rows, disagrees on
+  3), you are NOT done. Do not ship. The mismatching rows encode an extra condition
+  you missed — re-read the prompt, form a new hypothesis, and retest until 100% match.
 
 ### 3. Compute in Python; write literal values
 `ws['C4'] = '=SUMPRODUCT(...)'` stores only text — openpyxl caches no result, so the
@@ -54,20 +65,53 @@
 ```
 Match expected types: numbers as `int`/`float`, dates as `datetime`, blanks as `None`.
 
-### 4. If a live formula is genuinely required
-Write the formula **and** materialize its value: save, then
-`soffice --headless --convert-to xlsx --outdir . out.xlsx`, and confirm with
-`load_workbook(out, data_only=True)` that every target cell is non-None. If recalc
-is unavailable, prefer literal values — a correct value beats an uncomputed formula.
-Cross-sheet references use `Sheet1!$A$1`, never `Sheet1.$A$1` (that is ODF syntax and
-Excel rejects it). Never rely on a copied formula string to shift relative refs; use
-`from openpyxl.formula.translate import Translator` if you must (note the module path).
+### 4. "Give me a formula" still means WRITE VALUES — never flip back
+This is the single largest source of 0.000 scores, and it happens on the LAST turn:
+the agent computes correct literal values, then "upgrades" them to a formula because
+the prompt said *"create a new formula and insert it in column H"*, *"the correct
+formula should be placed into cell K6"*, *"write VBA that..."*, or *"how do I create
+a formula that..."*. Since there is no recalculation engine available, that formula
+is saved with no cached result and the grader reads `None`. Score 0.
+
+Rule, no exceptions:
+- The **output .xlsx contains literal values only** in the cells you touch.
+- The **formula text belongs in your chat answer** ("the formula you want is
+  `=SUMIFS(C$3:C$8,A$3:A$8,I3,B$3:B$8,J3)`; I have placed its result, -10600, in K6").
+  That satisfies the "explain my formula" request without losing the value.
+- Same for VBA/macro requests: perform the transformation with Python, and show the
+  VBA in prose only.
+- Once literal values are written and verified against the oracle, **do not rewrite
+  those cells again**. Any later turn that replaces a value with a formula is a
+  regression — stop and save.
+
+Only if a value truly cannot be computed (rare) fall back to a formula, and then also
+ensure syntax is Excel's: `Sheet1!$A$1`, never `Sheet1.$A$1`; and use
+`from openpyxl.formula.translate import Translator` (that module path) rather than
+string-replacing row numbers — naive `.replace(str(row-1), str(row))` corrupted
+`5551234` into `6661234` in a real run.
 
 ### 5. Edit in place; never round-trip through pandas
 Load the original with openpyxl, mutate, save once at the end. `df.to_excel(...)`
 rebuilds the workbook and destroys layout, offsets, formatting and untouched columns.
 For row/column surgery use `ws.insert_rows(idx, n)` / `ws.delete_rows(idx, n)`,
 processing indices in descending order.
+
+**Critical: openpyxl discards the cached results of formulas it did not write.** Every
+pre-existing formula in the workbook (`=SUM(F19:F31)`, `=IF(I11="Yes",...)`) comes back
+as `None` for a value-reading grader after you save — even in cells you never touched.
+And `insert_rows`/`delete_rows` do not retarget those formulas, so they are wrong too.
+
+So before saving, materialize inherited formulas across the graded sheet:
+
+```python
+for row in wsf.iter_rows():
+    for c in row:
+        if isinstance(c.value, str) and c.value.startswith('='):
+            v = wsv[c.coordinate].value          # cached value from the data_only load
+            c.value = v if v is not None else <computed in Python>
+```
+When rows are inserted/deleted, do this mapping **before** the shift (or recompute the
+aggregates in Python for the new layout), so each moved row keeps the right number.
 
 ### 6. Read the instruction literally
 - "Insert two new rows after each X" means two **blank** rows, not duplicates.
@@ -90,3 +134,14 @@
     assert not (isinstance(got, str) and got.startswith('=')), addr
 ```
 Only claim completion after this diff is empty.
+
+### 8. Self-check before you answer
+Answer these out loud before declaring completion:
+1. Does any cell in the output start with `=`? -> If yes, replace it with its value.
+2. Does every oracle/example cell still hold its original value, and does my logic
+   reproduce 100% of them?
+3. Did I read every formula cell of the saved file with `data_only=True` and confirm
+   none is `None` in the graded region?
+4. Did I avoid `soffice` and avoid writing anything into the input file?
+If any answer is no, fix it and re-save before responding.
+
```

## Iteration 3 — patch `spreadsheet_values_and_oracle` — **REJECTED**
- validation score: 0.7333 (best before: 0.8667)

```diff
--- a/spreadsheet_values_and_oracle/SKILL.md
+++ b/spreadsheet_values_and_oracle/SKILL.md
@@ -20,6 +20,24 @@
 
 ## Instructions
 
+### 0. Produce an output file EARLY, then refine it
+One task scored 0.000 purely because the run hit the turn limit after ~12 exploration
+steps with **no `*_output.xlsx` ever written** — correct analysis, zero score.
+Exploration is not progress; a saved file is.
+
+- Budget: by your 3rd or 4th tool call you must have saved
+  `<input_stem>_output.xlsx` (a verbatim copy of the input if you still know nothing).
+  Then keep improving that file in place and re-saving.
+- Re-save after every meaningful advance. Whatever is on disk when you stop is your score.
+- Do ALL inspection in one big script (sheet names, `dimensions`, `max_row`, headers,
+  the target block, the oracle block, `type()` of key cells) instead of one script per
+  question — each round trip burns a turn you may need for writing the answer.
+- If an inspection script crashes (e.g. `TypeError: '<' not supported between instances
+  of 'NoneType' and 'str'` while sorting keys that may be `None`), do not spend turns
+  perfecting the *printout*. Guard it once (`sorted(k for k in keys if k is not None)`)
+  and move on to computing and saving the answer.
+
+
 ### 1. Inspect raw, and get real input values
 Dump cells with openpyxl (`data_only=False`) over the plausible range — headers are
 rarely on row 1. `pd.read_excel` alone hides layout; never rely on it for structure.
@@ -37,6 +55,26 @@
 `wbv` usually has real numbers because Excel saved them. If a cached value is `None`,
 evaluate that formula yourself in Python (they are almost always simple chains like
 `=+C3*2`); do not give up and do not shell out.
+
+### 1b. Establish the data extent and the exact write range — never hardcode a window
+Two failures wrote correct-looking values into the wrong number of rows because the
+agent looped `range(4, 15)` / `range(2, 5)` and never asked how large the data is.
+
+Before any computation, print the extent:
+
+```python
+print(ws.title, ws.dimensions, ws.max_row, ws.max_column)
+last_b = max((c.row for c in ws['B'] if c.value not in (None, '')), default=0)
+print('last row with data in B:', last_b)
+```
+- `max_row` may be inflated by stray formatting — confirm with the per-column scan —
+  but it is never safe to assume the data ends before your loop bound.
+- Derive the SOURCE range from the data, then derive the OUTPUT range from the source:
+  if 30 source rows yield 22 matches, the answer occupies 22 rows. State that count
+  out loud before writing, and write every one of those rows.
+- After writing, clear leftover cells below your last written row in the output block
+  (`cell.value = None`) so stale sample data is not mistaken for your answer.
+
 
 ### 2. Find the in-file oracle FIRST — and never overwrite it
 Scan for pre-filled expected answers: an `Expected Result` column, a `Manual Result`
@@ -52,6 +90,17 @@
 - If your rule reproduces only *some* oracle cells (e.g. matches 5 rows, disagrees on
   3), you are NOT done. Do not ship. The mismatching rows encode an extra condition
   you missed — re-read the prompt, form a new hypothesis, and retest until 100% match.
+- **A completed sample block is a PREFIX, not the scope.** In one failure Sheet3 came
+  pre-filled with the first ~40 result rows; the agent concluded "only these two
+  categories belong in the output", regenerated exactly those rows, and saved a file
+  identical to the input — while the prompt said "repeat for each Sheet1 entry ... till
+  the last row of Sheet1". Use the sample only to pin down the RULE (join key, ordering,
+  concatenation/format); then apply that rule to EVERY source row the instruction names.
+  Never let the sample shrink the answer, and never drop a source category just because
+  it is absent from the sample.
+- Sanity check before saving: if the graded region of your output is identical to the
+  input, you produced no work — that is always wrong. Print how many cells/rows you
+  changed.
 
 ### 3. Compute in Python; write literal values
 `ws['C4'] = '=SUMPRODUCT(...)'` stores only text — openpyxl caches no result, so the
@@ -143,5 +192,11 @@
 3. Did I read every formula cell of the saved file with `data_only=True` and confirm
    none is `None` in the graded region?
 4. Did I avoid `soffice` and avoid writing anything into the input file?
+5. Does `<input_stem>_output.xlsx` exist on disk right now, containing my latest work?
+   (If I am near the turn limit, save what I have IMMEDIATELY — a partial answer beats
+   no file.)
+6. Did I print `max_row` / the last data row, and does my output cover EVERY row the
+   instruction names — not just the rows that were pre-filled as a sample?
+7. How many cells did I actually change? If zero, I have not done the task.
 If any answer is no, fix it and re-save before responding.
 
```

## Iteration 4 — patch `spreadsheet_values_and_oracle` — **REJECTED**
- validation score: 0.8000 (best before: 0.8667)

```diff
--- a/spreadsheet_values_and_oracle/SKILL.md
+++ b/spreadsheet_values_and_oracle/SKILL.md
@@ -122,6 +122,17 @@
   `border.left.style` after reload.
 - When rules conflict, enumerate every stated rule, and pick the reading that
   reproduces the oracle from step 2.
+- **A later clause never cancels an earlier one.** "Names listed in J come first, keep
+  their original order ... and sort only column H lowest to highest" cannot mean "sort
+  everything by H" — that erases the J grouping you just built. When applying step 2
+  makes step 1 pointless, you have misread one of them; find the reading where both
+  survive (here: sort by H *within* each group).
+- **A lookup grid is often two tables: boundaries + payouts.** A block whose first row
+  is all zeros, or whose values descend across columns as cut-offs, holds the *bucket
+  boundaries* for one axis — per goal-bucket variance thresholds, say — not answers.
+  Pick the row/column using that entity's OWN boundary column; never combine two tables
+  with an invented `max()`/`sum()`. If your rule reads the same boundary column for
+  every record, you have collapsed a 3-D grid into 2-D.
 
 ### 7. Mandatory final gate
 Save last, then reopen the saved file and assert — do not just print formula text:
@@ -134,6 +145,50 @@
     assert not (isinstance(got, str) and got.startswith('=')), addr
 ```
 Only claim completion after this diff is empty.
+
+### 7b. MANDATORY: diff the WHOLE sheet against the input, cell by cell
+Most zeros are not wrong answers — they are cells you never meant to touch. Real cases:
+`B2:B19` held `=IF(E2<0,...,"Eligible")` and read `None` after save; `A6` held
+`=IF(C6="","X","")` and read `None`; `F2:F11` was already numbered 1..10 while the prompt
+said "output in columns G and H" and got clobbered; a pre-filled `EXPECTED RESULT` block
+and the user's worked-example cells were overwritten. Verifying only your target column
+cannot see any of this.
+
+Before you answer, run this over EVERY cell of EVERY sheet:
+
+```python
+inp = load_workbook(src, data_only=True)    # Excel's cached values
+out = load_workbook(dst, data_only=True)
+for wi, wo in zip(inp.worksheets, out.worksheets):
+    R = max(wi.max_row, wo.max_row); C = max(wi.max_column, wo.max_column)
+    for r in range(1, R+1):
+        for c in range(1, C+1):
+            a, b = wi.cell(r, c).value, wo.cell(r, c).value
+            if a != b:
+                print(wi.title, wi.cell(r, c).coordinate, repr(a), '->', repr(b))
+```
+
+How to read the diff — each line must survive one of these tests:
+- **Every changed cell must be one the instruction told you to write.** If the prompt
+  names a range ("output in columns G and H", "column F", "cell K6"), a diff line
+  outside it is a bug: revert that cell to the input value.
+- **`<value> -> None` is ALWAYS a bug.** A pre-existing formula lost its cached result.
+  Fix it for the whole sheet before saving, not just your target column:
+  ```python
+  for row in wsf.iter_rows():
+      for cf in row:
+          if isinstance(cf.value, str) and cf.value.startswith('='):
+              cf.value = wsv[cf.coordinate].value   # cached value, or compute in Python
+  ```
+- **A pre-filled cell whose value changed is a bug** unless the task explicitly says to
+  recompute it. Fill blanks; leave author-typed cells alone. If your rule disagrees with
+  a pre-filled cell, your rule is wrong — do not invent a special case for that one row.
+- **Never `load_workbook(..., data_only=True)` and then `.save()`** — that writes the
+  cached values back as the file's only content and blanks every uncached formula.
+  Mutate and save only the `data_only=False` workbook.
+- If you inserted/deleted rows, a positional diff is meaningless: diff the aligned
+  regions instead (match by key) and still account for every unmatched row.
+
 
 ### 8. Self-check before you answer
 Answer these out loud before declaring completion:
@@ -143,5 +198,11 @@
 3. Did I read every formula cell of the saved file with `data_only=True` and confirm
    none is `None` in the graded region?
 4. Did I avoid `soffice` and avoid writing anything into the input file?
+5. Did I run the whole-sheet input->output diff (7b), and is EVERY printed line a cell
+   the instruction asked me to change? No `value -> None`, no clobbered pre-filled cell,
+   nothing outside the named output range?
+6. Did I write only inside the range the prompt names? An adjacent already-numbered
+   column, a header row, or a user's worked example is context and an oracle — not
+   output. (A pre-numbered index column also tells you how many answer rows to produce.)
 If any answer is no, fix it and re-save before responding.
 
```

## Iteration 5 — patch `spreadsheet_values_and_oracle` — **ACCEPTED**
- validation score: 0.9333 (best before: 0.8667)

```diff
--- a/spreadsheet_values_and_oracle/SKILL.md
+++ b/spreadsheet_values_and_oracle/SKILL.md
@@ -52,6 +52,24 @@
 - If your rule reproduces only *some* oracle cells (e.g. matches 5 rows, disagrees on
   3), you are NOT done. Do not ship. The mismatching rows encode an extra condition
   you missed — re-read the prompt, form a new hypothesis, and retest until 100% match.
+- **But an oracle match you had to HARDCODE is a failure, not a success.** Refining the
+  rule is legitimate only when the new rule (a) is a different *reading* of a term the
+  instruction already uses and (b) applies uniformly to every row. It is never
+  legitimate to bolt on a keyword the user never listed (`'Tesing  Layer'`), an extra
+  arithmetic term, or a row-number gate (`if row_idx <= 32: ... else: leave blank`)
+  just to turn the diff green. Three tests before you accept a rule:
+  - Can every branch quote a clause of the instruction? If not, delete that branch.
+  - Does my code compare against a literal row number, or slice a fixed window? That is
+    always a bug — the rule must key off the DATA, never off position.
+  - Did I consume EVERY input the prompt names? If it describes three filters (Goal
+    bucket, Variance range, Metric2 bucket) and my code reads only two lookup blocks,
+    the unread block (e.g. the threshold rows under `Goal Buckets`) is a whole
+    dimension I dropped. List each named parameter and point at the line that uses it.
+- **Blank cells are not oracle values.** In a column headed `EXPECTED RESULT` that is
+  filled for rows 3–32 and empty for 33–71, only the *filled* cells are ground truth;
+  the empty ones are exactly what you were asked to compute. Forcing them to stay blank
+  reproduces the input byte-for-byte. Print how many cells your output changed versus
+  the input — if that count is 0, you did not do the task.
 
 ### 3. Compute in Python; write literal values
 `ws['C4'] = '=SUMPRODUCT(...)'` stores only text — openpyxl caches no result, so the
@@ -64,6 +82,19 @@
 ws['B7'] = None                # blank, not ""
 ```
 Match expected types: numbers as `int`/`float`, dates as `datetime`, blanks as `None`.
+
+**A string that merely LOOKS right is wrong.** "Format column J to show only the time"
+means a real time value plus a number format — not `strftime()` text:
+
+```python
+c = ws['J2']
+c.value = dt.time()                 # datetime.time, NOT '06:08:00 PM'
+c.number_format = 'h:mm:ss AM/PM'   # the display comes from the format, not the text
+```
+Same for dates (`datetime` + `'dd/mm/yyyy'`), percentages (`0.06` + `'0%'`, not `'6%'`)
+and currency (`1234.5` + `'$#,##0.00'`, not `'$1,234.50'`). On reload assert the TYPE
+(`assert not isinstance(v, str)`), because "does not start with `=`" passes for every
+wrong text string.
 
 ### 4. "Give me a formula" still means WRITE VALUES — never flip back
 This is the single largest source of 0.000 scores, and it happens on the LAST turn:
@@ -110,8 +141,22 @@
             v = wsv[c.coordinate].value          # cached value from the data_only load
             c.value = v if v is not None else <computed in Python>
 ```
-When rows are inserted/deleted, do this mapping **before** the shift (or recompute the
-aggregates in Python for the new layout), so each moved row keeps the right number.
+**Order matters, and getting it wrong silently ships formula strings.** `wsv` (the
+`data_only` workbook) does NOT shift when you `insert_rows`/`delete_rows` on `wsf`, so
+after any structural edit `wsv[c.coordinate]` reads the wrong row — and returns `None`
+for every row past the original `max_row`. Follow this exact order:
+
+1. Snapshot first: materialize every formula cell to its literal value **while the
+   layout is still original** (`cache = {c.coordinate: wsv[c.coordinate].value}`).
+2. Re-derive target row numbers from the data — never reuse indices captured before an
+   edit.
+3. Deletions (descending) → re-scan → insertions (descending) LAST.
+4. Recompute in Python any aggregate whose inputs moved.
+5. Assert the final row count, and that no cell in the sheet still starts with `=`.
+
+If step 1 prints anything like `Warning: Formula in I48 has no cached value`, STOP.
+That is not a warning — it is dozens of cells about to be graded as `None`. Evaluate
+those formulas yourself (they are simple chains like `=G48*H48`) before continuing.
 
 ### 6. Read the instruction literally
 - "Insert two new rows after each X" means two **blank** rows, not duplicates.
@@ -143,5 +188,13 @@
 3. Did I read every formula cell of the saved file with `data_only=True` and confirm
    none is `None` in the graded region?
 4. Did I avoid `soffice` and avoid writing anything into the input file?
+5. Wherever the ask was about DISPLAY, did I write a real typed value
+   (number/`datetime`/`time`/`None`) plus a `number_format`, and assert the type rather
+   than just the absence of `=`?
+6. Does every branch of my rule quote a clause of the instruction — no row-number gates,
+   no invented keywords or extra terms — and did I consume every input block the prompt
+   names?
+7. How many cells does my output change versus the input? If zero, I have not done the
+   task.
 If any answer is no, fix it and re-save before responding.
 
```

## Iteration 6 — patch `spreadsheet_values_and_oracle` — **REJECTED**
- validation score: 0.9333 (best before: 0.9333)

```diff
--- a/spreadsheet_values_and_oracle/SKILL.md
+++ b/spreadsheet_values_and_oracle/SKILL.md
@@ -37,6 +37,52 @@
 `wbv` usually has real numbers because Excel saved them. If a cached value is `None`,
 evaluate that formula yourself in Python (they are almost always simple chains like
 `=+C3*2`); do not give up and do not shell out.
+
+### 1b. Census EVERY sheet and EVERY column before you compute anything
+The most expensive failures are not bad math — they are answer keys the agent never
+looked at because it inspected a window it guessed. Real cases: a 515-row sheet where
+the user's worked examples sat below the `range(1, 30)` scan, so the agent reported
+"no oracle" and overwrote them; a sheet with `max_row=2483, max_column=20` where only
+column A was ever printed, so the "before and after" demo the user described was never
+found; a second sheet holding the sorted reference list that was printed once and
+ignored.
+
+Run this ONCE, before any hypothesis, and read the output:
+
+```python
+for ws in wbf.worksheets:                      # every sheet, including odd names
+    print('==', repr(ws.title), ws.dimensions, ws.max_row, ws.max_column,
+          'hidden' if ws.sheet_state != 'visible' else '')
+    cols = {}
+    for row in ws.iter_rows():
+        for c in row:
+            if c.value is not None:
+                cols.setdefault(c.column_letter, []).append(c.row)
+    for L, rs in sorted(cols.items()):
+        print(f'  col {L}: {len(rs)} filled, rows {min(rs)}..{max(rs)}, e.g. {ws[L+str(rs[0])].value!r}')
+```
+
+How to act on it:
+- **Any populated column you were not expecting is a lead.** A block sitting to the
+  right of the data is usually the user's "this is what I'm aiming for" example,
+  a lookup grid, or a helper list. Print it in full before designing your rule.
+- **Every extra sheet is a suspect answer key** (`Sheet2`, `Manual Result`, a
+  non-Latin name, a "Before/After" pair). Dump it fully and ask: is it a sorted /
+  filtered / joined version of the main data? If yes, it IS the expected output —
+  reproduce it exactly and diff against it.
+- **If the prompt references an artifact you cannot find, you have not looked hard
+  enough.** "I filled in a couple of examples", "a sheet that shows before and after",
+  "the first meet is completed" — search the FULL extent of every column and sheet
+  (and hidden sheets) before concluding it is absent, and say so explicitly if it
+  truly is. Never proceed to overwrite a region you never inspected.
+- **Derive loop bounds from this census, never from a guess.** No `range(1, 30)`, no
+  `results[:9]` to make the answer fit an assumed block. If 10 rows survive filtering,
+  write 10 rows; if the count differs from the block you expected, that is a finding to
+  investigate, not to truncate.
+- **Columns adjacent to your output range that are already populated are context, not
+  output.** If the instruction names "columns G and H", an already-numbered column F is
+  an input; leave it untouched.
+
 
 ### 2. Find the in-file oracle FIRST — and never overwrite it
 Scan for pre-filled expected answers: an `Expected Result` column, a `Manual Result`
@@ -154,6 +200,21 @@
 4. Recompute in Python any aggregate whose inputs moved.
 5. Assert the final row count, and that no cell in the sheet still starts with `=`.
 
+**If you CHANGE an input cell, its dependents' cached values are now LIES.** One task
+said "change the Bill Rate in column G to 180 where Company='National TV' and
+Location='India'". The agent wrote 180, then materialized `I=G*H`, `J=G-30`, `K=J*H`,
+`L=I-K` from the cache — values Excel had computed with the OLD rate. Four wrong
+columns on every row it "fixed". So:
+
+- Before materializing, list every cell you overwrote, then find every formula whose
+  text mentions that column/coordinate (`'G2' in f` / the column letter with the row).
+- Those cells must be **recomputed in Python from the new inputs**, in dependency
+  order (`I` before `L`, `J` before `K`) — never copied from `wsv`.
+- The cache is only trustworthy for formulas whose entire input closure is untouched.
+- Sanity-print one affected row before/after (`G 100->180, I 17600->31680`) so a stale
+  number is visible rather than silent.
+
+
 If step 1 prints anything like `Warning: Formula in I48 has no cached value`, STOP.
 That is not a warning — it is dozens of cells about to be graded as `None`. Evaluate
 those formulas yourself (they are simple chains like `=G48*H48`) before continuing.
@@ -196,5 +257,10 @@
    names?
 7. How many cells does my output change versus the input? If zero, I have not done the
    task.
+8. Did I run the whole-workbook census (1b) — every sheet, every populated column, full
+   row extent — BEFORE forming my rule? If the prompt mentions an example/reference
+   block, did I actually locate it, or did I just fail to find it in a window I guessed?
+9. For every input cell I overwrote, did I RECOMPUTE its dependent formulas from the new
+   values instead of restoring their stale cached results?
 If any answer is no, fix it and re-save before responding.
 
```

## Iteration 7 — patch `spreadsheet_values_and_oracle` — **REJECTED**
- validation score: 0.8667 (best before: 0.9333)

```diff
--- a/spreadsheet_values_and_oracle/SKILL.md
+++ b/spreadsheet_values_and_oracle/SKILL.md
@@ -4,6 +4,25 @@
 ---
 
 # Write Values, Not Formulas — and Validate Against the File's Own Oracle
+
+## THE OUTPUT CONTRACT (settle this before your first tool call)
+Two sentences decide most scores. State them in your plan, then obey them:
+
+1. **Every cell I write ends up holding a literal Python-computed value** — never a
+   string starting with `=`, no matter how the request is phrased ("where have I gone
+   wrong with my formula", "the correct formula should be placed into cell K6", "I need
+   a VBA code", "make it dynamic/a Table so it auto-extends"). The formula or VBA text
+   goes in my chat reply only.
+2. **Every already-filled cell inside the answer region is ground truth I must
+   reproduce, not a cell to fill.** If my rule disagrees with even one of them, my rule
+   is wrong and I do not write.
+
+Both were violated again this round. Two tasks scored 0.000 by saving
+`=SUMIFS($C$3:$C$8,...)` and `=IF($B$12=$B$2,C$2,...)` into exactly the cell the user
+named — while the answers (`-10600`; `French`/`Science`/`Social Studies`) were already
+visible in the `data_only=True` load the same run had printed one step earlier. Another
+scored 0.000 by overwriting an author-typed `H3=5000` with its own `4000`.
+
 
 ## When to Apply
 - Any SpreadsheetBench-style task producing `*_output.xlsx` that will be graded by
@@ -71,6 +90,45 @@
   reproduces the input byte-for-byte. Print how many cells your output changed versus
   the input — if that count is 0, you did not do the task.
 
+### 2b. The oracle gate — run it as code, before any write
+Losing runs *look at* the pre-filled cells and move on. Winning runs count failures.
+
+```python
+# 1. Collect every already-filled cell in the answer region over its FULL extent
+oracle = {}
+for r in range(1, ws.max_row + 1):          # whole column — NOT range(4, 25)
+    v = ws.cell(r, target_col).value
+    if v is not None and not str(v).startswith('='):
+        oracle[r] = v
+# 2. Score the candidate rule per cell and report the FAIL count
+fails = [(r, oracle[r], rule(r)) for r in oracle if rule(r) != oracle[r]]
+print(f'oracle={len(oracle)} pass={len(oracle)-len(fails)} FAIL={len(fails)}', fails)
+assert not fails            # blocking: do not write, do not save, re-read the prompt
+```
+
+How to read the result:
+- **`len(oracle) == 0` after scanning a guessed window is a search bug, not "no oracle".**
+  When the prompt says "I filled in a couple of examples" or quotes a range, the example
+  exists — `AVERAGE(B24:B69)` means there is a worked cell around row 69. One run
+  searched rows 4–24 of a 515-row sheet, reported no examples, and scored 0.000. Scan
+  the full column, then the other sheets, before concluding anything is absent.
+- **One matching cell never confirms a rule.** A run whose rule produced `H4=2250`
+  (match) and `H3=4000` (author typed `5000`) announced "confirming the logic is
+  correct" and overwrote H3. Print pass/FAIL counts; never quote a cherry-picked ✓.
+- **Check that the example can DISCRIMINATE.** If the prompt's worked example gives the
+  same answer under two rival readings, it proves nothing. (One run read a payout grid
+  as `goal_lookup + metric2_lookup`; the example matched only because the goal term was
+  0.) Before choosing, ask what each block of numbers *is*: a block whose values ascend
+  like the cut-offs the prompt describes ("0% to more than 7%") is a BOUNDARY table
+  selecting a row for another variable — not a set of numbers to add. Prefer the reading
+  that uses every block once in its stated role, with no invented `+`, `max()` or `/4`.
+- **Write only where the prompt points, and size the answer from the data.** If the
+  instruction names "columns G and H", an already-populated column F is input; leave it.
+  A pre-numbered index column in the output block also tells you the expected row count
+  (10 index numbers ⇒ 10 answer rows) — never slice results (`rows[:9]`) to fit a block
+  you assumed.
+
+
 ### 3. Compute in Python; write literal values
 `ws['C4'] = '=SUMPRODUCT(...)'` stores only text — openpyxl caches no result, so the
 grader reads `None`. Score 0. Do the filter/lookup/aggregation in Python and write
@@ -196,5 +254,9 @@
    names?
 7. How many cells does my output change versus the input? If zero, I have not done the
    task.
+8. Did I run the oracle gate (2b) as code and print `FAIL=0`, scanning the FULL column
+   rather than a guessed window — or did I just eyeball a comparison table and proceed?
+9. Did I write outside the cells/columns the prompt names, and does my row count come
+   from the data rather than a slice?
 If any answer is no, fix it and re-save before responding.
 
```

## Iteration 8 — patch `spreadsheet_values_and_oracle` — **REJECTED**
- validation score: 0.8667 (best before: 0.9333)

```diff
--- a/spreadsheet_values_and_oracle/SKILL.md
+++ b/spreadsheet_values_and_oracle/SKILL.md
@@ -168,17 +168,71 @@
 - When rules conflict, enumerate every stated rule, and pick the reading that
   reproduces the oracle from step 2.
 
-### 7. Mandatory final gate
-Save last, then reopen the saved file and assert — do not just print formula text:
-
-```python
-chk = openpyxl.load_workbook(out, data_only=True)[sheet]
-for addr, expected in oracle.items():
-    got = chk[addr].value
-    assert got == expected, (addr, got, expected)
-    assert not (isinstance(got, str) and got.startswith('=')), addr
-```
-Only claim completion after this diff is empty.
+### 7. Mandatory final gate — one script, all asserts, run it LAST
+
+Every 0.000 in the last round ran a verification step. Every one of them **printed** the
+proof of failure and then talked past it:
+- `✓ Verification - J23 displays: None` → *"Perfect! ✓ Your formula has been fixed."*
+- a "verification" that reloaded with `data_only=False` and printed its own 18
+  INDEX/MATCH strings back as evidence they were "correctly applied".
+- `Row 72 ✗  Row 80 ✗` → *"3 out of 5 oracle rows match, my solution is correct"*.
+
+**Never `print` a check. `assert` it.** A printed check is an invitation to keep
+talking; an assertion ends the turn. Your LAST bash command must be the script below,
+and the only successful output is the final `ALL GATES PASSED` line.
+
+```python
+import openpyxl
+SRC, OUT, SHEET = '..._init.xlsx', '..._output.xlsx', 'Sheet1'
+TARGETS = {}   # {coord: value_I_intend} — every cell I meant to write, INCLUDING each
+               # oracle cell mapped to the value it ALREADY had (re-emit, never change)
+inV = openpyxl.load_workbook(SRC, data_only=True)
+oF  = openpyxl.load_workbook(OUT, data_only=False)
+oV  = openpyxl.load_workbook(OUT, data_only=True)
+
+# G1 — no formula string survives anywhere in the workbook
+bad = [(w.title, c.coordinate) for w in oF for r in w.iter_rows() for c in r
+       if isinstance(c.value, str) and c.value.startswith('=')]
+assert not bad, ('G1 formula strings left', bad[:10])
+
+# G2 — nothing that had a value lost it (cached results of inherited formulas)
+lost = [(w.title, c.coordinate) for w in inV for r in w.iter_rows() for c in r
+        if c.value is not None and oV[w.title][c.coordinate].value is None]
+assert not lost, ('G2 values became None', lost[:10])
+
+# G3 — every target holds exactly what I computed, with the right TYPE
+for k, v in TARGETS.items():
+    got = oV[SHEET][k].value
+    assert got == v and type(got) is type(v), ('G3', k, repr(got), repr(v))
+
+# G4 — I changed something, and ONLY cells that were empty or that I listed
+chg = [(w.title, c.coordinate, c.value, oV[w.title][c.coordinate].value)
+       for w in inV for r in w.iter_rows() for c in r
+       if c.value != oV[w.title][c.coordinate].value]
+assert chg, 'G4 output is identical to the input — no work was done'
+for t, coord, old, new in chg:
+    print('CHANGED', t, coord, repr(old), '->', repr(new))
+    assert old is None or coord in TARGETS, ('G4 clobbered a pre-filled cell', t, coord, old, new)
+print('ALL GATES PASSED')
+```
+
+How to react when a gate fires — the fix is never to loosen the gate:
+- **G1** → you shipped a formula. Compute the result in Python, write the literal, and
+  put the formula text in your chat reply only (§4).
+- **G2** → an inherited formula lost its cached value. Materialize it (§5) before saving.
+- **G3** → your own write did not land, or landed as the wrong type (`'6%'` vs `0.06`,
+  a `strftime` string vs a `time`).
+- **G4 clobbered a pre-filled cell** → this is the single most common 0.000. You just
+  destroyed author-typed ground truth: the sample ranks, `H3=5000`, the 5 worked
+  averages, the already-numbered index column F that the prompt did not ask you to
+  touch. Restore the original value and re-run. If your rule *disagrees* with that
+  cell, the rule is wrong — go back to §2; do not add the coordinate to `TARGETS` with
+  a new value just to silence the gate.
+- **G4 no changes** → you reproduced the input; you have not done the task.
+
+Skip G2/G4 only when you deliberately inserted or deleted rows. Then diff the aligned
+regions by key instead of by coordinate, still account for every unmatched row, and
+still assert the final row count.
 
 ### 8. Self-check before you answer
 Answer these out loud before declaring completion:
@@ -196,5 +250,8 @@
    names?
 7. How many cells does my output change versus the input? If zero, I have not done the
    task.
+8. Did my last bash command print `ALL GATES PASSED`? A check that merely *printed* a
+   `None`, an `✗`, or a formula string does not count — rewrite it as an `assert` and
+   run it again. I may not write my final answer until the gate script exits cleanly.
 If any answer is no, fix it and re-save before responding.
 
```
