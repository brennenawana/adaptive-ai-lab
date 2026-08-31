# Formula written but no cached value (score 0)

## Pattern
Agent solves an Excel task by writing a formula *string* into a cell with openpyxl, saves, and reports success. Score = 0.

## Root cause
`openpyxl` has **no formula evaluation engine**. `ws['B2'] = '=IF(...)'` stores the text only; the xlsx has no `<v>` cached result. Any grader that compares cell *values* (or loads with `data_only=True`) reads `None`. The formula may be perfectly correct in Excel and still score 0.

## Evidence (iteration 1)
All 0.0 tasks did exactly this:
- 39931: `=SUMPRODUCT(($I$3:$I$22=$B4)*($J$3:$J$22=C$3)*$K$3:$K$22)` into C4:F6 -> verification printed `Row 4: ['None','None','None','None']`. soft=0.
- 10452: `=FILTER($B$4:$B$15,LEFT($B$4:$B$15,2)="PK")` into E4 only. soft=0.
- 472-15: nested `IF(ISNUMBER(SEARCH(...)))` into B2; A1 was already known to be `8CPARK...` so the answer `6` was computable in Python. soft=0.
- 55060: `=IF(I12="","",I12)` into J23; I12 was known to be `January`. soft=0.
- 50916: nested IF chain into C12:H14; verification showed all blanks. soft=0.

Contrast: 408-39, 66-24, 170-13 wrote literal values -> soft=1.0.

## Fix
1. Compute the intended result **in Python** from the data you already read.
2. Write the literal value: `ws['B2'] = 6`, `ws['J23'] = 'January'`, fill C4:F6 with the 12 looked-up numbers.
3. If a live formula is genuinely desired, write the formula **and then recalculate** so a cached value exists:
   `soffice --headless --convert-to xlsx --outdir . out.xlsx` (or `libreoffice ... --convert-to xlsx:"Calc MS Excel 2007 XML"`), then verify with `load_workbook(..., data_only=True)`.
4. Never finish while `data_only=True` returns `None` for a target cell.

## Iteration 2 update: LibreOffice is NOT available
Two agents tried the recalculation workaround and both got:
```
$ soffice --headless --convert-to xlsx --outdir . out.xlsx
Exit code 127
/opt/homebrew/bin/soffice: line 2: /Applications/LibreOffice.app/.../soffice: No such file or directory
```
(tasks 36097, 58484). **Do not plan around `soffice`.** Computing the value in Python is the only reliable route in this environment. Corollary: also do not rely on it to "refresh" pre-existing formulas — leave those cells untouched, their cached values are already in the file (see destructive-overwrite-of-given-content.md).

## Iteration 2 caveat: literals are necessary but NOT sufficient
36097, 58484, 6239 all wrote clean literals and still scored 0 because the underlying rule was wrong. Pair this pattern with contradicting-provided-examples.md.

## Iteration 3: regression — "how do I create a formula" phrasing is the trigger
**55060 scored 0 again** (it also scored 0 in iteration 1) with the identical mistake:
```python
ws['J23'] = '=IF(I12="","",I12)'   # I12 was already known to be the literal string 'January'
```
followed once more by the dead `soffice --headless --convert-to xlsx` attempt (exit 127) and a "verification" that only re-read the formula string.

Root cause of the regression: the instruction is worded as *"How do I create a formula ... my current formula is IF(I12="","")"*, which pulls the agent into formula-authoring mode. **The deliverable is still the evaluated cell value.** Correct action here was one line:
```python
ws['J23'] = ws['I12'].value or ''   # -> 'January'
```
Rule of thumb: if the prompt asks for a formula, explain the formula in prose *in your answer* but write the **computed literal** into the workbook.

Contrast (iteration 3, soft=1.0): 39931 and 10452 — both 0.0 in iteration 1 — flipped to 1.0 purely by building a Python dict / list comprehension and writing literals into C4:F6 and E4:E12 respectively.

## Iteration 4: regression on 50916 (0.0 in iteration 1 and iteration 4)
Identical mistake, new function family. The agent wrote 18 formula strings into C12:H14:
```python
formula = f"=INDEX(${col_letter}$2:${col_letter}$8,MATCH(B{row},$B$2:$B$8,0))"
ws.cell(row=row, column=col_num, value=formula)
```
then ran the dead `soffice --headless --convert-to xlsx` (exit 127 again) and "verified" by printing the formula text alongside a hand-computed `expected_value`. Every target cell is `None` under `data_only=True`.

The agent had already computed the full answer — its own dump printed `schedule[day][col]` for all 7 cycle days — and B12/B13/B14 were the literal values 1/2/3. The whole task was:
```python
for r, day in [(12,1),(13,2),(14,3)]:
    for c in range(3, 9):
        ws.cell(r, c, schedule[day][c])   # 'Homeroom', 'French', 'Math', ...
```

**Trigger phrasing, now seen three times** (55060 twice, 50916): *"I managed a formula that works in one cell but am struggling to copy it across"* / *"how do I create a formula"* / *"fix the problems in cells C12, E12:H12"*. Any prompt that talks about formulas pulls the agent into formula-authoring mode. **Explain the formula in your prose answer; write the computed literal into the workbook.**

