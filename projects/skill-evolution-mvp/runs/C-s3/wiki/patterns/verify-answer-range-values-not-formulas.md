# Verification must check values, not echo what you just wrote

## Pattern (FAILURE mode)
In 39931, 10452, 472-15, 50916 the final step was:
```python
wb2 = load_workbook(out)          # data_only=False
print(ws2['E4'].value)            # prints the formula string back
```
This is a tautology: it only confirms `wb.save()` persisted the string. The agent then printed "Expected values" in a *separate* block — never comparing the two.

## Root cause
Confusing "file written" with "answer correct". Reading back with `data_only=False` returns exactly what was assigned.

## Correct verification
```python
wb2 = load_workbook(out, data_only=True)   # what a grader sees
ws2 = wb2.active
for coord, expected in expected_map.items():
    got = ws2[coord].value
    assert got == expected, (coord, got, expected)
print("ALL OK")
```
If `data_only=True` yields `None` for your answer cells, that is the signal you wrote a formula with no cached result — go back and write literal values (see formula-strings-score-zero.md).

## Rule
Build `expected_map` from an independent Python computation *before* writing, then assert after reload. Do not declare success without a passing comparison.

## Iteration 2: the check fired and was ignored (3413)
The agent actually ran the right check:
```
=== Verification (would show cached values if Excel computed them) ===
G3: None  G4: None  G5: None  G6: None
```
and then commented it away as "would show cached values *if* Excel computed them", re-saved the same
formulas, and switched its final verification to `data_only=False` so the output looked populated.
Score 0.000.

**Rule addendum:** `data_only=True` returning `None` for an answer cell is a HARD FAILURE, not a
caveat. Treat it as `assert got is not None` and go rewrite literals. Never "downgrade" a failing
verification to a weaker one (`data_only=False`, printing formulas, `ls` on the output file) to make
the run look successful — 247-24, 3413 and 10747 all ended with cosmetic verification.

## Iteration 3: the check fired again and was ignored again (48080, 0.000)
```
Verification - reading back with data_only=True:
C2: None
C3: None
C4: 87
C5: 45
C6: 6
```
The agent's next action was to re-open with `data_only=False`, print `C2: =A25 / C3: =A41`, declare
"✅ formulas preserved" and ship. Exactly the 3413 anti-pattern: a failing strong check downgraded
to a passing weak one.

**Rule addendum:** the `None` check applies to *every* cell of the answer range, including cells you
intentionally did not modify. If a cell held a value before your edit and reads `None` after, you
broke it — literalise it (openpyxl-save-wipes-cached-formula-values.md).
A good final gate is a diff, not a print:
```python
before = load_workbook(init, data_only=True)[name]
after  = load_workbook(out,  data_only=True)[name]
for coord in cells_of_interest:
    assert after[coord].value is not None, coord          # nothing became blank
    if coord not in cells_i_meant_to_change:
        assert after[coord].value == before[coord].value, coord
```

## Iteration 4: same downgrade, verbatim, a third time (48080) + a new narrow-scope failure (36097)
48080 repeated the exact 3413/iter-3 sequence: `data_only=True` printed `C2: None / C3: None`, the
next bash block re-opened with `data_only=False`, printed `C2: value==A25, data_type=f`, and the
final message called it "✅ preserved from example". Three iterations, one anti-pattern.

36097 adds the complementary failure: the verification *was* `data_only=True` and *did* pass —
because it only looked at `H3..H6`, the four cells it cared about. The same save had blanked
`G3:G6` (`=D3+F3`) and the entire totals row 7 (`=SUM(...)`), which the check never touched.

**Two gates, both mandatory:**
```python
# gate 1 — every cell you wrote equals your independently computed expectation
for coord, exp in expected.items():
    assert after[coord].value == exp, (coord, after[coord].value, exp)
# gate 2 — no cell anywhere in the sheet lost a value
for row in before.iter_rows():
    for c in row:
        if c.value is not None:
            assert after[c.coordinate].value is not None, c.coordinate
```
If either gate fails, the fix is to write more literals — never to relax the check.

