# openpyxl save destroys the cached values of formulas that were already in the file

## Pattern (FAILURE) — 48080, 50916, 247-24 (all 0.000)
`load_workbook(path)` reads formula *text* only. `wb.save(out)` then writes a workbook whose
formula cells have **no `<v>` cached result — including every cell you never touched**. A grader
loading with `data_only=True` sees `None` for all of them.

| Task | Formula cells in the init file | Cached value in init | Value in output |
|---|---|---|---|
| 48080 | `C2='=A25'`, `C3='=A41'` | 14, 17 | `None`, `None` |
| 50916 | `D12..H14` IF-chains | 'French', 'Science', ... | `None` |
| 247-24 | `I:L` = `=G2*H2`, `=G2-30`, `=J2*H2`, `=I2-K2` (46 rows) | numbers | `None` |

48080 is the clearest case: the agent deliberately "preserved" C2:C3 per the preserve-pre-filled
rule, filled C4:C6 with literals, and its own verification printed
`C2: None / C3: None / C4: 87 / C5: 45 / C6: 6` — then shipped.

## Root cause
"Preserve the pre-filled cells" was applied to the formula *text* rather than to the *value the
user can see*. Excel wrote the cache; openpyxl cannot regenerate it, so a round-trip is lossy for
every formula in the workbook.

## Fix — literalise every formula in the graded sheet
```python
vals = load_workbook(init, data_only=True)   # cached results written by real Excel
wb   = load_workbook(init)                   # structure + styles you will save
ws, wsv = wb[name], vals[name]
for row in ws.iter_rows():
    for c in row:
        if isinstance(c.value, str) and c.value.startswith('='):
            c.value = wsv[c.coordinate].value    # keep the number, drop the formula
```
Run this over at least the answer range and any column the answer depends on, *before* you make
structural edits (see row-edits-break-relative-formulas.md — moving rows also invalidates the text).

## Checks
- Always diff `data_only=True` values between init and output: any cell that was a number in the
  init and is `None` in the output is a regression you caused.
- If a live formula is genuinely required, recalc the saved file:
  `soffice --headless --convert-to xlsx 1_<id>_output.xlsx` and re-verify with `data_only=True`.
- Loading with `data_only=True` and saving *that* workbook is the opposite trap: it discards the
  formulas permanently. Use two handles as above.

## Iteration 4 — the blast radius includes totals rows you never looked at
| Task | Formulas in the init that lost their cache | Was it verified? |
|---|---|---|
| 48080 | `C2='=A25'` (14), `C3='=A41'` (17) | yes — printed `C2: None, C3: None`, ignored (3rd repeat) |
| 36097 | `G3:G6 = '=D3+F3'`, `C7:H7 = '=SUM(x3:x6)'` | **no** — verification only covered H3:H6 |
| 370-43 | `A6 = '=IF(C6="","X","")'` and the rest of the 2483-row sheet | no |
| 247-24 | `I:L` per-row formulas ×46 | no |

36097 is the new lesson: the agent wrote correct literals into H5/H6, but the file it shipped also
contained a `SUM` total row and a whole `Proceeds` column that now read `None`. **Your verification
range must be the whole sheet, not the cells you wrote.**

```python
before = load_workbook(init, data_only=True)[sheet]
after  = load_workbook(out,  data_only=True)[sheet]
for row in before.iter_rows():
    for c in row:
        if c.value is not None:
            assert after[c.coordinate].value is not None, f'{c.coordinate} went blank'
```
Run that diff on every task. Anything it flags must be literalised from the `data_only=True` handle
before you save.

