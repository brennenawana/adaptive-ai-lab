# Don't Drop the Formatting Clause Buried in the Prompt

**Type:** Success pattern / checklist item

## Pattern
Spreadsheet prompts frequently append a styling requirement to a computation request. Both must be satisfied for full credit.

## Evidence (task 39903, score 1.000)
Instruction ended with: "Please include all borders for cells C:2-6, with Courier new font 9pt."
```python
thin = Border(left=Side(style='thin'), right=Side(style='thin'),
              top=Side(style='thin'), bottom=Side(style='thin'))
font = Font(name='Courier New', size=9)
for r in range(2, 7):
    ws[f'C{r}'].value = count
    ws[f'C{r}'].font = font
    ws[f'C{r}'].border = thin
```
Verified after reload: `cell.font.name == 'Courier New'`, `cell.font.size == 9.0`, `cell.border.left.style == 'thin'`.

## Checklist
- Apply styling to the EXACT stated range (C2:C6, not the header C1).
- Font name must match the string in the prompt case-correctly ('Courier New').
- Number formats (e.g. `h:mm:ss AM/PM`) are formatting only — they do NOT create a value; pair them with an actual value (see write-values-not-formulas).
- Re-open the saved file and assert each style attribute; styles set on a cell object before a save-then-mutate sequence are easy to lose.

## A number_format only renders a properly TYPED value (iteration 3, task 32438)
The workbook already declared the intended look: `I1.number_format == '[$-F400]h:mm:ss\\ AM/PM'`. The agent wrote `'06:08:00 PM'` as a string and set nothing — text ignores number formats entirely, and a value-comparing grader sees a string instead of a time. Correct pattern: write `datetime.time(...)` (or the datetime) and copy the concept's existing `number_format` onto the target cells. See time-value-vs-text-string.

## "Preserve the formatting of column X" (36097)
This clause means *do not disturb* those cells — do not write to them, do not reassign `.font`/`.border`/`.number_format`. Read the existing style objects, and if you must copy them use `copy(cell._style)` or `copy(cell.font)` (openpyxl style objects are shared and immutable-ish; assigning one cell's Font object to many cells is fine, mutating it is not).

## Iteration 4 success: 58484 (1.000) satisfied four formatting clauses at once
"headings properly bordered and bolded", "'Wrap Text' on for row 4", "no values or bordering on column G":
```python
for col in ['D','E','F','H']:
    c = ws[f'{col}4']
    c.font = Font(bold=True)
    c.border = thin_border
    c.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
for row in range(1, 27):                 # clear column G completely
    ws[f'G{row}'].value = None
    ws[f'G{row}'].border = Border()      # empty Border() = remove borders
```
Notes: `Border()` with no sides is how you *remove* bordering (there is no `None` assignment); apply styles to the exact stated cells only (the header row, not the data); and a "no values in column X" clause means explicitly setting `.value = None`, not just skipping the column.

