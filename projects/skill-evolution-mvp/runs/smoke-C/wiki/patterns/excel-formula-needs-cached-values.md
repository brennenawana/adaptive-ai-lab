# Formulas written by openpyxl have no cached values

## Problem
Task 57445 (score 0.000): agent wrote a *semantically correct* SUMIFS lookup into E2:E5 with openpyxl and saved. The grader reads cell *values*, but openpyxl stores only the formula string — there is no cached result — so every target cell evaluates to None/empty and the task scores 0 even though the formula text is reasonable.

## Root cause
openpyxl is not a calculation engine. `wb.save()` writes `<f>` without `<v>`. Any downstream reader using `data_only=True` (or pandas) gets `None`. The agent even self-diagnosed this and shipped anyway: "the formulas will evaluate correctly when opened in Excel/LibreOffice".

## Fix (do one of these before finishing)
1. Recalculate headlessly after saving:
   ```bash
   soffice --headless --convert-to xlsx --outdir . out.xlsx   # LibreOffice recalcs on load/convert
   ```
   then verify: `openpyxl.load_workbook('out.xlsx', data_only=True)` shows real numbers.
2. Or compute the expected values in Python and write them, using formulas only if the task explicitly asks for a formula.
3. Always end with a `data_only=True` verification print. If it prints `None` for the target cells, the task is NOT done.

## Anti-signal
A final message containing "will evaluate correctly when opened in Excel" is a strong predictor of a 0 score.

## Confirmed evidence (re-analysis of iter 1 trace)
The failing formula was NOT an array formula — it was:
```excel
=SUMIFS('Package & Weight Data'!$D:$D,'Package & Weight Data'!$A:$A,C2,'Package & Weight Data'!$B:$B,"<="&D2,'Package & Weight Data'!$C:$C,">="&D2)
```
which would compute 2 / 2.5 / 0 / 6 correctly in any engine. It still scored 0.000. This isolates the cause: **formula correctness is irrelevant if no cached value is stored.** Getting the formula right is necessary but never sufficient.

## Minimal safe recipe
```python
wb = openpyxl.load_workbook(src); ws = wb['Pricing']
for r in range(2, 6):
    ws[f'E{r}'] = FORMULA(r)
wb.save(out)
```
```bash
soffice --headless --convert-to xlsx --outdir . 1_57445_output.xlsx
```
```python
wb = openpyxl.load_workbook(out, data_only=True)
assert all(wb['Pricing'][f'E{r}'].value is not None for r in range(2,6))
```
If LibreOffice is unavailable, compute the values in Python and write them into the cells directly (optionally keeping the formula in a note/answer text). See also fake-verification-hardcoded-expectations.md — the iter-1 agent's "verification" hid this failure.
