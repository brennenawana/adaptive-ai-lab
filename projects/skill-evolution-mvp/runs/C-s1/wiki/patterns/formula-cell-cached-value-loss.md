# Cached Values Are a Positional Snapshot — Capture Them Before You Touch Anything

**Type:** Failure pattern (mechanical, openpyxl)

## Problem
`load_workbook(..., data_only=True)` does not evaluate anything. It returns the values Excel wrote at the file's last save. That snapshot is lost or misaligned in three ways, and every one of them ends with formula strings (→ `None` for the grader) in the output.

## Three manifestations seen in traces
1. **Re-save drops them (48080, iter 3).** Round-trip a file through openpyxl and every pre-existing formula cell loses its cached value. Recovered by re-reading the ORIGINAL with `data_only=True` and rewriting C2=14, C3=17 as literals → 1.000.
2. **The data_only workbook does not shift (247-24, iter 5, 1.000 → 0.000).** The agent inserted 20 blank rows into `main_f`, then tried to materialize formulas by reading `main_v[f'I{row_num}']` — but `main_v` is a separate object still holding the pre-insert layout:
```
Inserting 2 rows after row 2 ... (20 rows inserted)
Materializing existing formulas...
  Warning: Formula in I48 has no cached value
  Warning: Formula in J48 has no cached value    # ...~40 more
```
Every warned cell kept its `=G2*H2` string, pointing at the wrong row. Score 0.
3. **Overwriting a formula cell throws its value away (50916, iter 5).** D12/F12/H12 held cached `French`/`Science`/`Social Studies` from a working formula. The agent replaced all of C12:H14 with new nested-IF strings, so three correct answers became `None` and the other fifteen stayed empty.

## Fix
```python
wbv = load_workbook(src, data_only=True)
wsv = wbv[name]
# 1. SNAPSHOT FIRST, keyed by ORIGINAL coordinate, before any write/insert/delete
cached = {c.coordinate: c.value for row in wsv.iter_rows() for c in row}
# 2. materialize every formula cell you will keep
for row in wsf.iter_rows():
    for c in row:
        if isinstance(c.value, str) and c.value.startswith('='):
            c.value = cached.get(c.coordinate)   # or recompute in Python
# 3. only now do structural edits / writes
```
- If `cached[coord]` is `None`, the file was never opened in Excel after that formula was added: **recompute the value in Python**, do not ship the string.
- Never index a `data_only` sheet with a coordinate produced after an `insert_rows`/`delete_rows` on the other workbook.
- Before overwriting any cell, check whether it already holds a good value (see contradicting-oracle-cells) — a working cached result is worth more than a prettier formula.

## Iteration 7: the snapshot usually already contains the answer
- **10747 (0.000):** the very first dump printed `K3: -10600` and `L3: 4000` — the cached results of the user's working row-3 formulas, which are exactly the numbers the K6 formula was supposed to produce. The agent read them, quoted them in its explanation, and wrote a formula string instead.
- **50916 (0.000, second time on this file):** `D12='French'`, `F12='Science'`, `H12='Social Studies'` were live cached results; both attempts overwrote all of C12:H14 with new formula strings, converting three correct answers into `None`.

**Add to the checklist:** after loading with `data_only=True`, print every non-empty cell in and around the target range and ask "is the answer already here?" before designing anything. Overwriting a cell that already holds a correct value is a strict regression — see contradicting-oracle-cells.

## Iteration 8: 50916 destroys the same three cached values for the THIRD run in a row
`D12='French'`, `F12='Science'`, `H12='Social Studies'` are live cached results of the user's working formula — three of the eighteen answers, already correct in the file. All three attempts (iters 5, 7, 8) rewrote the whole `C12:H14` block with new formula strings, converting them to `None`.

**Cheapest possible guard, applicable to every task:**
```python
before = {c.coordinate: wsv[c.coordinate].value for c in target_cells}
print('already correct:', {k: v for k, v in before.items() if v is not None})
# after computing:
for k, v in before.items():
    if v is not None: assert computed[k] == v, (k, v, computed[k])   # your rule must reproduce them
```
If your rule reproduces them, writing the same literal back is harmless; if it does not, you have found a bug for free. Either way, a cell that already holds the right answer must never end up empty.

