# Plan the Whole Pipeline Before the First Mutation — and Always Save an Output

**Type:** Failure pattern (process / budget)

## Problem
The agent starts mutating the live worksheet while still figuring out the task, discovers halfway that the order of operations was wrong, abandons the run, and restarts. The turn/context budget is consumed by the restarts and the task ends with **no output file written at all** → 0.000 regardless of how good the understanding was.

## Evidence — 247-24, iteration 6 (0.000)
The same task scored 1.000 in iteration 4. This run:
1. Turn 3 materialized formulas by printing **one line per formula cell** (~160 lines of `Formula at I2: =G2*H2 -> 17600`), consuming context for no information gain.
2. It filled column M, then deleted rows, then reloaded the ORIGINAL file to find `National TV` rows and realised the indices no longer lined up:
```python
# Map to actual row in current worksheet (accounting for deletions)
# Actually, we need to track this differently since we've already deleted rows
pass
print("\nLet me restart with a better approach...")
```
3. Turn 4 started over from the source file — and the run ended there. No `wb.save(output)` ever executed.

## Root cause
Exploration and mutation were interleaved on the live sheet, so every new realisation invalidated work already applied to the workbook object. Each restart costs a full re-read plus a full re-print.

## Fix
1. **Read once into plain Python** (`rows = [[c.value for c in r] for r in ws.iter_rows()]`, resolving formulas from the `data_only` snapshot). All exploration then happens on the list, where a wrong idea costs nothing.
2. **Write the ordered step list in prose before any mutation** — for row surgery the proven order is: snapshot → materialize formulas → delete (bottom-up) → re-scan → update/lookup → insert blank rows LAST (see openpyxl-row-insert-delete).
3. **One mutation script.** Load, apply every change, save, reload, verify. Never save a half-applied state and continue from it.
4. **Save an output file as early as you can** with the best-known answer, then refine and re-save. A partially-correct saved file beats an unsaved perfect plan.
5. **Print summaries, not per-cell logs**: `print(len(formula_cells), 'formulas materialized;', sum(v is None for v in vals), 'missing')` instead of one line per cell.

## Iteration 7: 6239 (0.000) — five turns of inspection, no output file
The run dumped the employee block, then the lookup tables, then the lookup tables again cell-by-cell (`I1..T6`, one `print` per cell), then the employee list sorted by variance, then a single test case. The trace ends there: no `ws['G{r}'] = …`, no `wb.save`. Even the partially-wrong rule it had in hand (goal bucket + metric2 grid) would have produced a scoreable file.

**Restated priority:** an output file containing your current best answer is the first deliverable, not the last. Concretely, by the end of your *second* command you should have:
1. all source data in Python lists/dicts, and
2. a saved output file with a first-draft answer written into the target range.
Every later turn refines and re-saves. Cell-by-cell dumps of a lookup table (`print(f"  {col}{row}: {cell.value}")` × 60) buy nothing that `[[c.value for c in r] for r in ws['I1:T6']]` does not.
