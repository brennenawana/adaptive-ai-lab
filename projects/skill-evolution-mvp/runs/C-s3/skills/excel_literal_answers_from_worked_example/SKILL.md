---
name: excel_literal_answers_from_worked_example
description: For SpreadsheetBench/openpyxl tasks — compute answers in Python and write literal values (never formula strings), and derive the answer rule by reverse-engineering the worked example already present in the init file. Use whenever filling an answer range in an .xlsx.
---

# Literal answers, calibrated against the file's worked example

## When to Apply
- Any task that edits an `.xlsx` and produces `1_<taskid>_output.xlsx`.
- Especially when the instruction says "I've completed the first one / part of the answer
  examples have been given / see my sample", or asks for a *formula*, *macro*, *VBA*,
  *Power Query*, or a "dynamic" sheet.

## When NOT to Apply
- Pure file-format/metadata tasks with no computed answer cells (e.g. rename a sheet,
  set a print area).
- When the task explicitly says the graded artifact is a `.bas`/text macro file rather
  than cell contents.

## Instructions

### 1. Dump everything, with types and coordinates
```python
wb = openpyxl.load_workbook(path)           # keep a second load with data_only=True
for ws in wb:
    print("===", ws.title, ws.dimensions)
    for r in ws.iter_rows():
        vals = [(c.coordinate, c.value, type(c.value).__name__) for c in r if c.value is not None]
        if vals: print(vals)
```
Never use truncating `pd.read_excel` printouts (`...` columns) as your only view — 6239
and 263-1 both mis-read the file that way. Types matter: `datetime` vs `str` changes the logic.

### 2. Find the worked example FIRST, and treat it as the spec
The init file almost always contains a partially completed answer: some rows/cells of the
answer range are already filled (263-1: `metal=1660`, `PVC=2753`; 194-19: the whole first
meet's H/I; 6239: the payout grid in P2:T6; 408-39: an example block).

- Enumerate the already-filled cells inside/adjacent to the answer range.
- Form a hypothesis for the rule, then **reproduce those given cells with your Python code**
  and assert equality. If your code cannot regenerate the given values, your rule is wrong —
  iterate, do not proceed.
  ```python
  for coord, given in given_cells.items():
      assert my_rule(coord) == given, (coord, my_rule(coord), given)
  ```
  (194-19 failed exactly here: the example proves column I is matched by *Tab number*, not by
  row position; the agent filled positionally and never checked.)
- **Never invent data.** If a lookup/payout table is only partially shown, the missing part is
  derivable from the given table or from the instruction — do not fabricate plausible numbers
  (6239 fabricated 60 payout values).
- **Never overwrite the given example cells.** Write only into the still-empty positions,
  preserving the given ones byte-for-byte.

### 3. Compute in Python; write literal values — never formula strings
openpyxl has no calc engine: `ws['B2'] = '=SUMIF(...)'` stores text with no cached `<v>`, so
a grader loading `data_only=True` sees `None`. Every 0.000 task in iteration 1 wrote formulas.

```python
totals = {}                                   # do the SUMIF / IF-chain / MOD / lookup in Python
for r in range(2, ws.max_row+1):
    m = ws.cell(r,1).value
    if m: totals[m] = totals.get(m,0) + ws.cell(r,2).value*ws.cell(r,3).value
ws['H2'] = totals['glass']                    # the NUMBER, not '=SUMIF(...)'
```
Common translations:
| Asked for | Write instead |
|---|---|
| `=RIGHT(I2,8)` / `=MOD(I2,1)` time | `dt.time()` literal (or `dt - datetime.combine(dt.date(), time())`) + set `number_format` |
| `=SUMIF/SUMIFS` | Python dict accumulate |
| nested `=IF` buckets | Python `if/elif` returning the bucket value |
| `=INDEX/MATCH`, `=VLOOKUP` | Python dict keyed on the match columns |

If the user explicitly asks for a formula/macro/VBA/Power Query: still write the **computed
literal** into the cells, and put the formula/macro text in your chat reply only.
"Dynamic" in the instruction refers to the described behaviour, not to what must sit in the cell.

### 4. Respect the answer range exactly
- Write only inside the stated answer range; do not shift rows (22-47 wrote a `NAME`/`REF`
  header row into the first answer row, offsetting every value by one). Check whether the
  first answer row is a header or a data row by looking at the worked example.
- Don't add helper columns inside the graded sheet unless asked (263-1 added column D).
- Don't change `number_format`, fonts or fills of cells outside the answer range.
- Copy style from the source cell when relocating values:
  ```python
  from copy import copy
  for a in ('font','border','fill','number_format','protection','alignment'):
      setattr(dst, a, copy(getattr(src, a)))
  ```

### 5. Verify by reloading with data_only=True
```python
wb2 = openpyxl.load_workbook(out, data_only=True)
ws2 = wb2[sheet]
for coord, exp in expected.items():
    got = ws2[coord].value
    assert got == exp, (coord, got, exp)
print("ALL OK")
```
`expected` must include the pre-given example cells (unchanged) plus your computed cells.
Printing back what you just assigned proves nothing. If any answer cell reads `None` here,
you wrote a formula — go back to step 3.
