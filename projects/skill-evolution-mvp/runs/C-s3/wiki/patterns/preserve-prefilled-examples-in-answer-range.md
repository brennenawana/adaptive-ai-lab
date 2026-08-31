# Do not clear or reorder a pre-filled answer range

## Pattern (FAILURE + SUCCESS)
Init files frequently already contain part (or all) of the expected answer as worked examples.

| Task | Pre-filled | Agent action | Score |
|---|---|---|---|
| 170-13 | Sheet3 already held the full expected output (41 rows, specific order) | looped `ws3.cell(r,1).value = None` then rewrote in its own order | 0.000 (was 1.000 in iter 1) |
| 3413 | G3=14, G4=27 given as examples | overwrote G3:G6 with formula strings | 0.000 |
| 247-24 | Main sheet A2:M47 with formulas in I:L | blanked all rows and rewrote | 0.000 |
| 42354 | D2:D5 given as examples | left them alone, filled only D6:D8 | 1.000 |
| 192-22 | F3:F8, F20... already 'Billing PO' | recomputed all of F but produced identical values for the pre-filled rows | 1.000 |

## Root cause
The agent treats the init file as raw input to be regenerated, instead of a partially-completed answer.
Regenerating loses (a) the exact row ordering the grader expects, (b) values it could not have derived,
(c) cell styles/formulas in untouched columns. 170-13 is the proof: the correct answer was literally
already in the file and the agent deleted it.

## Rule
0. **"Preserve" means preserve the VALUE a human sees, not the cell's contents.** If a pre-filled
   cell holds a formula, leaving it untouched *destroys* it on save. Literalise first, then fill:
   ```python
   vals = load_workbook(init, data_only=True)[sheet]   # Excel's cached results
   wb   = load_workbook(init); ws = wb[sheet]
   for row in ws.iter_rows():
       for c in row:
           if isinstance(c.value, str) and c.value.startswith('='):
               c.value = vals[c.coordinate].value       # e.g. '=A25' -> 14
   # ...only now write your new literals into the blank cells
   ```
1. Before writing, list which cells of the answer range are already populated.
2. Write ONLY into cells that are empty, unless the task explicitly says to change a value.
2b. **Preserve the pre-filled cell's VALUE, not its formula text.** If a pre-filled answer cell
   contains a formula, read its cached result with a `data_only=True` handle and write that number
   back as a literal — otherwise `wb.save()` blanks it (openpyxl-save-wipes-cached-formula-values.md).
   48080 scored 0.000 by faithfully "preserving" `C2='=A25'` and `C3='=A41'`, which then read `None`.
3. If your recomputation disagrees with a pre-filled cell, your rule is wrong — fix the rule, do not
   overwrite the example (see validate-rule-against-worked-examples.md).
4. Never do `for r in range(...): cell.value = None` on a sheet you are also the answer for.
5. Preserve row order of existing data; append rather than re-sort.

## Iteration 3 evidence
| Task | Pre-filled | Agent action | Score |
|---|---|---|---|
| 48080 | `C2='=A25'` (14), `C3='=A41'` (17) as the worked example | kept the formulas, filled C4:C6 literals | 0.000 — C2/C3 read `None` |
| 22-47 | column F pre-filled with the row counter 1,2,3,4,5... | overwrote F with source ITEM numbers, though the prompt said "output in columns G and H" | 0.000 |
| 10452 | `E4:E8` = first five PK values | asserted its filter reproduced all five, then wrote only E9:E12 | 1.000 |
| 48745 | `D5:D7` = 'Group 1','Group 1','Group 2' | recomputed all of D5:D10, values for D5:D7 came out identical | 1.000 |

Add rule 6: **do not write outside the columns/ranges the prompt names as output**, even when the
neighbouring column looks like part of the same result block (22-47's column F).

## Iteration 4 — the rule was cited and still misapplied (48080, 3rd 0.000)
The trace says, verbatim: *"Following the skill pattern (preserve given example, compute and write
literal values for the empty cells), I'll fill C4:C6"*. It had **already read** `C2=14, C3=17` with
a `data_only=True` handle two blocks earlier, then chose to leave `=A25` / `=A41` in place. Output:
`C2: None, C3: None, C4: 87, C5: 45, C6: 6`.

If you find yourself writing "preserved from example" in a summary next to a cell whose value is a
formula, you have failed. Say instead: "C2 literalised to 14 (was `=A25`)".

Counter-example, 263-1 (1.000): the pre-filled H3/H4 were *numbers*, the agent recomputed them,
printed `Given=1660, Calculated=1660, Match=True`, left them, and wrote only H2. That is the shape
to imitate — recompute the example, compare, then fill the blanks.

