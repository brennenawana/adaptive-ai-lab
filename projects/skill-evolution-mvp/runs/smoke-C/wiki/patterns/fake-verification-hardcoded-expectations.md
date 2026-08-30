# Fake verification: printing expectations instead of actual values

## Problem (task 57445, score 0.000)
The agent ran a "verification" step that *looked* rigorous:
```python
wb_values = load_workbook('1_57445_output.xlsx', data_only=True)
pricing_values = wb_values['Pricing']
test_cases = [(2,"ABC","LL",300,2), (3,"DEF","RM",750,2.5), ...]
for row, part_no, pkg_type, weight, expected in test_cases:
    value_cell = pricing_values[f'E{row}']          # loaded...
    print(f"... | Formula set | {expected}")        # ...but never printed!
```
It loaded `value_cell` and then never used it, printing the hardcoded `expected` column instead. The output table showed `2 / 2.5 / None / 6` — which the agent read as success. The real cells were all `None`. An earlier "verification" also just re-printed the formula strings from the non-`data_only` workbook, which trivially always passes.

## Root cause
The verification script is written by the same reasoning that wrote the answer, so it encodes the *belief* about the result rather than observing it. Any literal in a verification print is a bug.

## Rules
1. Verification must re-open the **saved output file** and print/assert values it did not compute:
   ```python
   wb = load_workbook(out, data_only=True)
   for r in range(2, 6):
       v = wb['Pricing'][f'E{r}'].value
       print(r, repr(v))
       assert v is not None, f"E{r} is empty — task NOT done"
   ```
2. Never print a variable that came from a hand-written expected-value list.
3. If a loaded cell object is assigned but unused, that is the tell — the check is vacuous.
4. `data_only=True` on a file that was never recalculated returns `None`; seeing `None` means fix the file (see excel-formula-needs-cached-values.md), not soften the check.

## Contrast (task 141-20, score 1.000)
It reloaded the saved workbook and printed every row of both sheets verbatim — observed state, no expectations — and the printout genuinely reflected the graded file.