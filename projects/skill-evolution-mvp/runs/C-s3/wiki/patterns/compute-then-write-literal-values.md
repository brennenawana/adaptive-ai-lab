# Success recipe: parse → compute in Python → write literals → re-verify

## Pattern (SUCCESS)
The three 1.000-scoring tasks (408-39, 66-24, 170-13) all followed the same shape.

1. **Inspect first, fully.** Dump every sheet/cell with coordinates before deciding:
```python
wb = openpyxl.load_workbook(path)
for ws in wb:
    print(ws.title, ws.dimensions)
    for r in ws.iter_rows(values_only=False):
        print([(c.coordinate, c.value, type(c.value).__name__) for c in r if c.value is not None])
```
Printing the Python *type* mattered in 66-24 (column E was real `datetime`, enabling `max(dates) - timedelta(days=30)`).

2. **Do the logic in Python**, not in a formula: dict lookup (39931 style), `str.startswith` filter (10452 style), date threshold, substring match.

3. **Write literal values** into the answer range, and copy style from the source cell:
```python
from copy import copy
dst.value = src.value
if src.has_style:
    for attr in ('font','border','fill','number_format','protection','alignment'):
        setattr(dst, attr, copy(getattr(src, attr)))
```

4. **Save to the required output name** `1_<taskid>_output.xlsx` in the same working directory as the init file.

5. **Re-open the saved file** and print the answer-range values, comparing against the independently computed expectation.

## Notes
- `pd.ExcelWriter` (170-13) is fine when the task is a whole-sheet rebuild, but it destroys formatting — only use it when no styling is required.
- Cover the *whole* stated answer range including totals/header rows (408-39 also updated header B5 and grand total B11).

## Iteration 2 confirmations (39903, 42354, 192-22 all 1.000)
- 42354: dumped every cell with `repr()` **and** its Python type first — that revealed `#N/A` was the
  *string* `'#N/A'`, not a real error, so the rule became `if a != '#N/A'`. Writing `None` for the
  all-#N/A row correctly produced a blank cell.
- 192-22: built the keyword list from the instruction, matched with `keyword.lower() in text.lower()`
  (partial, case-insensitive as required), and diffed columns A–E against the init file to prove
  "preserve existing data" was honoured.
- 39903: unit-tested the counting function on the prompt's examples before touching the sheet.

Add to the recipe: **step 0 — enumerate which answer cells are already filled** (see
preserve-prefilled-examples-in-answer-range.md) and **step 2.5 — assert your rule reproduces every
pre-filled example** (see validate-rule-against-worked-examples.md).

## Iteration 3 confirmations (48745, 10452, 39931 all 1.000 — two of them former failures)
- **10452** (0.000 in iter 1 → 1.000): read B4:B15, `[v for v in vals if v.startswith('PK')]`,
  then *proved* the filter against the pre-filled worked example before writing:
  `E4: expected=... actual=... match=True` for E4:E8, and only then filled the blank E9:E12.
- **39931** (0.000 in iter 1 → 1.000): built `lookup_data[(key1,key2)] = value` from I:K, read the
  headers from row 3 and row ids from column B *at runtime*, wrote literals into C4:F6, and kept an
  `expected` dict to assert against after reloading with `data_only=True` (12/12 ✓).
- **48745**: dumped every cell as `repr()` first, built the G:H dict, split column C on ';',
  `sorted(set(groups))` joined with ', '. Recomputing the pre-filled D5:D7 gave identical values —
  that agreement is the signal the rule is right.

The three winners share one negative trait too: **none of them left a formula anywhere in the
graded range.** Where an init file already contains formulas, literalise them (see
openpyxl-save-wipes-cached-formula-values.md) — 48080 lost a run by preserving two.

## Iteration 4 confirmations (263-1, 57558, 408-39 all 1.000)
- **57558**: built `find_commission_rate(type, person, date)` in Python with the date-range test
  `start_date <= po_date <= end_date` (the exact thing the user could not express as a formula),
  wrote `0.03` / `0.17` as literals, reloaded with `data_only=True` and printed the full rows.
  Note the tie-break it used: **first matching RateHurdles row wins** — it stated that choice
  explicitly instead of silently picking one.
- **263-1**: `defaultdict(int)` accumulation of `width*height` per material over 276 rows, printed
  `Given=1660, Calculated=1660, Match=True` for both pre-filled cells, wrote only the blank H2.
- **408-39**: after copying I→B it *checked its own arithmetic*, spotted that the Grand Total now
  double-counted the '0-15' data, cleared the source column and recomputed L. Self-consistency
  checks on derived totals are part of the recipe — a moved column changes every row total.

Step 6 to add to the recipe: **diff `data_only=True` init vs output over the whole sheet** and assert
no populated cell became `None` (see openpyxl-save-wipes-cached-formula-values.md). 36097 passed
steps 1-5 and still scored 0 because the untouched `=SUM` row went blank.

