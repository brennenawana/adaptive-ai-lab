# Compare Cell Values With Matching Types

**Type:** Failure pattern (mechanical)

## Problem
openpyxl returns numbers as `int`/`float`, not strings. Comparing against a quoted literal silently yields all-False and an empty result set.

## Evidence (task 58484)
```python
if ws[f'D{row}'].value == "5551234":   # never true
```
```
D6 value: '5551234' (type: int)
D6 == '5551234': False
```
Every row evaluated blank; the emitted Excel formula had the same bug (`D5="5551234"` compares a number to text and is FALSE in Excel too).

## Fix
- During inspection, always print types: `print(repr(v), type(v).__name__)` for a few sample cells.
- Normalize both sides before comparing: `str(v).strip() == '5551234'` or `int(v) == 5551234`.
- For text matching add `.strip().lower()` (double spaces and case are common in these files).
- Excel side: compare a numeric cell to a bare number (`D5=5551234`), not a quoted string.

## Also applies to strings: trailing spaces and case (iteration 3)
`'PORT MACQUARIE '` (trailing space) and `'CRANBOURNE'` (none) coexist in the same column of 194-19; 247-24's `== 'Motorcycle'` matched nothing. Exact `==` on raw cell text is unreliable in these user-supplied workbooks.
```python
def norm(v):
    return str(v).strip().lower() if v is not None else None
```
Use `norm()` on BOTH sides for every join key and every filter, and print `sorted({repr(v) for v in column})` once before relying on equality. See zero-match-filter-check for the verification consequence.

## Iteration 4: same file, same bug, correct recovery → 1.000 (58484)
The agent repeated the iter-2 mistake (`d_val == '5551234'` against int cells), but this time the empty output triggered a debug pass:
```python
print(f"D{row}: value={repr(cell_val)}, type={type(cell_val).__name__}, equals '5551234'? {cell_val == '5551234'}")
print(f"D{row}: data_type={cell.data_type}")   # 'n' = numeric
```
`cell.data_type` ('n' numeric, 's' string, 'f' formula, 'd' date) is the cheapest one-shot type probe. Run the repr/type dump on ~5 sample cells of every column you will compare against, as part of the initial inspection — not as post-mortem debugging.

## Case and embedded junk: the winning normalization (472-15, 1.000 twice)
The rule was "if A1 contains '8CPark' set B2 to 6"; the cell actually holds `'8CPARK  /03-27-2021/22:21:06'` — different case, extra tokens, double spaces. Exact `==` scores 0; the winner used a case-folded substring test:
```python
if key.upper() in str(a1).upper(): ...
```
Rule of thumb for "contains"-style prompts (including Excel wildcards like `"*PE*"`): the predicate is `needle.upper() in str(cell).upper()`, never equality, and never a raw-case comparison.
