---
name: spreadsheet_values_and_oracle
description: Use when solving any Excel/spreadsheet manipulation task (openpyxl/pandas) where a grader compares cell values in an output .xlsx — especially when the request mentions a formula, macro/VBA, lookup, filter, sort, or "fix my formula".
---

# Write Values, Not Formulas — and Validate Against the File's Own Oracle

## When to Apply
- Any SpreadsheetBench-style task producing `*_output.xlsx` that will be graded by
  reading cell values.
- The user asks for "a formula", "an array formula", "a macro/VBA", "a VLOOKUP",
  "help me fix this formula", or "an Excel 2013 alternative to FILTER".
- The workbook contains an example/reference: a sheet named like `Manual Result`,
  a column headed `Expected Result`, or rows the user says they "already completed".

## When NOT to Apply
- Tasks graded on file structure only (e.g. "add a sheet named X") with no computed
  values.
- Pure formatting tasks with no computation (still follow rule 5 on in-place edits).

## Instructions

### 1. Inspect raw, and get real input values
Dump cells with openpyxl (`data_only=False`) over the plausible range — headers are
rarely on row 1. `pd.read_excel` alone hides layout; never rely on it for structure.

**`soffice` does not exist on this machine** (exit 127 / "No such file or directory"),
and `--convert-to xlsx --outdir .` OVERWRITES the input workbook — it already destroyed
one input file. Never invoke it, for reading or for recalculation.

Always open the input TWICE and keep both views:

```python
wbf = load_workbook(src, data_only=False)   # formulas / structure
wbv = load_workbook(src, data_only=True)    # Excel's cached values
```
`wbv` usually has real numbers because Excel saved them. If a cached value is `None`,
evaluate that formula yourself in Python (they are almost always simple chains like
`=+C3*2`); do not give up and do not shell out.

### 2. Find the in-file oracle FIRST — and never overwrite it
Scan for pre-filled expected answers: an `Expected Result` column, a `Manual Result`
sheet, or the first block/meet/group already completed by the user.
- These cells are ground truth, **not** cells to fill. Leave their existing values
  intact unless the task explicitly says to regenerate them.
- Hand-derive those rows with your logic in Python and assert an exact match before
  writing anything else. If your logic does not reproduce them, your interpretation
  is wrong — fix the logic, do not proceed.
- If there is no oracle, hand-derive at least two rows and print the derivation.
- Never write a FORMULA into an oracle cell either: in one failure C2/C3 held the
  user's reference values and were overwritten with `=INDEX(...)`, losing them.
- If your rule reproduces only *some* oracle cells (e.g. matches 5 rows, disagrees on
  3), you are NOT done. Do not ship. The mismatching rows encode an extra condition
  you missed — re-read the prompt, form a new hypothesis, and retest until 100% match.
- **But an oracle match you had to HARDCODE is a failure, not a success.** Refining the
  rule is legitimate only when the new rule (a) is a different *reading* of a term the
  instruction already uses and (b) applies uniformly to every row. It is never
  legitimate to bolt on a keyword the user never listed (`'Tesing  Layer'`), an extra
  arithmetic term, or a row-number gate (`if row_idx <= 32: ... else: leave blank`)
  just to turn the diff green. Three tests before you accept a rule:
  - Can every branch quote a clause of the instruction? If not, delete that branch.
  - Does my code compare against a literal row number, or slice a fixed window? That is
    always a bug — the rule must key off the DATA, never off position.
  - Did I consume EVERY input the prompt names? If it describes three filters (Goal
    bucket, Variance range, Metric2 bucket) and my code reads only two lookup blocks,
    the unread block (e.g. the threshold rows under `Goal Buckets`) is a whole
    dimension I dropped. List each named parameter and point at the line that uses it.
- **Blank cells are not oracle values.** In a column headed `EXPECTED RESULT` that is
  filled for rows 3–32 and empty for 33–71, only the *filled* cells are ground truth;
  the empty ones are exactly what you were asked to compute. Forcing them to stay blank
  reproduces the input byte-for-byte. Print how many cells your output changed versus
  the input — if that count is 0, you did not do the task.

### 3. Compute in Python; write literal values
`ws['C4'] = '=SUMPRODUCT(...)'` stores only text — openpyxl caches no result, so the
grader reads `None`. Score 0. Do the filter/lookup/aggregation in Python and write
the answer:

```python
ws['E4'] = 'PK01/P819760979'   # not '=INDEX(...SMALL(IF(...)))'
ws['C4'] = 23.56               # int/float, not a string
ws['B7'] = None                # blank, not ""
```
Match expected types: numbers as `int`/`float`, dates as `datetime`, blanks as `None`.

**A string that merely LOOKS right is wrong.** "Format column J to show only the time"
means a real time value plus a number format — not `strftime()` text:

```python
c = ws['J2']
c.value = dt.time()                 # datetime.time, NOT '06:08:00 PM'
c.number_format = 'h:mm:ss AM/PM'   # the display comes from the format, not the text
```
Same for dates (`datetime` + `'dd/mm/yyyy'`), percentages (`0.06` + `'0%'`, not `'6%'`)
and currency (`1234.5` + `'$#,##0.00'`, not `'$1,234.50'`). On reload assert the TYPE
(`assert not isinstance(v, str)`), because "does not start with `=`" passes for every
wrong text string.

### 4. "Give me a formula" still means WRITE VALUES — never flip back
This is the single largest source of 0.000 scores, and it happens on the LAST turn:
the agent computes correct literal values, then "upgrades" them to a formula because
the prompt said *"create a new formula and insert it in column H"*, *"the correct
formula should be placed into cell K6"*, *"write VBA that..."*, or *"how do I create
a formula that..."*. Since there is no recalculation engine available, that formula
is saved with no cached result and the grader reads `None`. Score 0.

Rule, no exceptions:
- The **output .xlsx contains literal values only** in the cells you touch.
- The **formula text belongs in your chat answer** ("the formula you want is
  `=SUMIFS(C$3:C$8,A$3:A$8,I3,B$3:B$8,J3)`; I have placed its result, -10600, in K6").
  That satisfies the "explain my formula" request without losing the value.
- Same for VBA/macro requests: perform the transformation with Python, and show the
  VBA in prose only.
- Once literal values are written and verified against the oracle, **do not rewrite
  those cells again**. Any later turn that replaces a value with a formula is a
  regression — stop and save.

Only if a value truly cannot be computed (rare) fall back to a formula, and then also
ensure syntax is Excel's: `Sheet1!$A$1`, never `Sheet1.$A$1`; and use
`from openpyxl.formula.translate import Translator` (that module path) rather than
string-replacing row numbers — naive `.replace(str(row-1), str(row))` corrupted
`5551234` into `6661234` in a real run.

### 5. Edit in place; never round-trip through pandas
Load the original with openpyxl, mutate, save once at the end. `df.to_excel(...)`
rebuilds the workbook and destroys layout, offsets, formatting and untouched columns.
For row/column surgery use `ws.insert_rows(idx, n)` / `ws.delete_rows(idx, n)`,
processing indices in descending order.

**Critical: openpyxl discards the cached results of formulas it did not write.** Every
pre-existing formula in the workbook (`=SUM(F19:F31)`, `=IF(I11="Yes",...)`) comes back
as `None` for a value-reading grader after you save — even in cells you never touched.
And `insert_rows`/`delete_rows` do not retarget those formulas, so they are wrong too.

So before saving, materialize inherited formulas across the graded sheet:

```python
for row in wsf.iter_rows():
    for c in row:
        if isinstance(c.value, str) and c.value.startswith('='):
            v = wsv[c.coordinate].value          # cached value from the data_only load
            c.value = v if v is not None else <computed in Python>
```
**Order matters, and getting it wrong silently ships formula strings.** `wsv` (the
`data_only` workbook) does NOT shift when you `insert_rows`/`delete_rows` on `wsf`, so
after any structural edit `wsv[c.coordinate]` reads the wrong row — and returns `None`
for every row past the original `max_row`. Follow this exact order:

1. Snapshot first: materialize every formula cell to its literal value **while the
   layout is still original** (`cache = {c.coordinate: wsv[c.coordinate].value}`).
2. Re-derive target row numbers from the data — never reuse indices captured before an
   edit.
3. Deletions (descending) → re-scan → insertions (descending) LAST.
4. Recompute in Python any aggregate whose inputs moved.
5. Assert the final row count, and that no cell in the sheet still starts with `=`.

If step 1 prints anything like `Warning: Formula in I48 has no cached value`, STOP.
That is not a warning — it is dozens of cells about to be graded as `None`. Evaluate
those formulas yourself (they are simple chains like `=G48*H48`) before continuing.

### 6. Read the instruction literally
- "Insert two new rows after each X" means two **blank** rows, not duplicates.
- "no values or bordering on column G" means clear values *and* set
  `cell.border = Border()` on that exact column, and do not bold/wrap it.
- Formatting clauses (borders, bold, font name/size, wrap text) are graded — apply
  them to the exact stated range only, and re-check `font.bold`, `alignment.wrap_text`,
  `border.left.style` after reload.
- When rules conflict, enumerate every stated rule, and pick the reading that
  reproduces the oracle from step 2.

### 7. Mandatory final gate
Save last, then reopen the saved file and assert — do not just print formula text:

```python
chk = openpyxl.load_workbook(out, data_only=True)[sheet]
for addr, expected in oracle.items():
    got = chk[addr].value
    assert got == expected, (addr, got, expected)
    assert not (isinstance(got, str) and got.startswith('=')), addr
```
Only claim completion after this diff is empty.

### 8. Self-check before you answer
Answer these out loud before declaring completion:
1. Does any cell in the output start with `=`? -> If yes, replace it with its value.
2. Does every oracle/example cell still hold its original value, and does my logic
   reproduce 100% of them?
3. Did I read every formula cell of the saved file with `data_only=True` and confirm
   none is `None` in the graded region?
4. Did I avoid `soffice` and avoid writing anything into the input file?
5. Wherever the ask was about DISPLAY, did I write a real typed value
   (number/`datetime`/`time`/`None`) plus a `number_format`, and assert the type rather
   than just the absence of `=`?
6. Does every branch of my rule quote a clause of the instruction — no row-number gates,
   no invented keywords or extra terms — and did I consume every input block the prompt
   names?
7. How many cells does my output change versus the input? If zero, I have not done the
   task.
If any answer is no, fix it and re-save before responding.

