# Filling a Formula Down Does Not Adjust Relative References

**Type:** Failure pattern (mechanical)

## Problem
Assigning the same formula string to a whole column leaves every relative reference pointing at the first row.

## Evidence (task 56786)
```python
formula = '=AVERAGEIFS($B$4:$B$1000,$A$4:$A$1000,">="&A4-365,$A$4:$A$1000,"<="&A4)'
for row in range(4, 201):
    ws[f'C{row}'] = formula   # every row still says A4
```
The agent then tried:
```python
from openpyxl.formula import Translator   # ImportError: cannot import name 'Translator'
```
and finally fell back to `formula.replace('A4', f'A{row}')`, which is fragile (would also rewrite `A40`, `A400`, or `$A$4`).

## Fix
- Correct import: `from openpyxl.formula.translate import Translator`;
  `Translator(base_formula, origin='C4').translate_formula(f'C{row}')`.
- Never use naive `str.replace` on cell refs; use a regex with boundaries or the Translator.
- Best: skip formulas entirely and write per-row computed values (see write-values-not-formulas).