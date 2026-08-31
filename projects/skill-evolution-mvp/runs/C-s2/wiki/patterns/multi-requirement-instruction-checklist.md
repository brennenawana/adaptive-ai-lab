# Multi-requirement prompts: treat every imperative sentence as a checklist item

## Pattern
Many prompts bundle formatting/structural demands with the computation. The agent latches onto the interesting computational question and half-implements or skips the mundane requirements. Getting the numbers right is not enough.

## Evidence: 58484 flipped 0.0 (iter 2) -> 1.0 (iter 4)
The prompt contains five separate imperatives:
1. "Recreate Sheet1 exactly as it is"
2. "headings are properly bordered and bolded"
3. "'Wrap Text' turned on for the text in row 4"
4. "There shouldn't be any values or bordering on column G"
5. "count the transfers ... display the total next to the last transfer" + "insert it on the cells in column H"

The iteration-2 run did (5) and, while doing (4), also nulled the pre-filled H cells -> 0.0.
The iteration-4 run did all five explicitly and scored 1.0:
```python
for col in range(4, 9):                       # (2)(3) headers
    cell = ws.cell(row=4, column=col)
    if cell.value:
        cell.font = Font(bold=True)
        cell.border = thin_border
        cell.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
for row in range(1, 27):                      # (4) column G, values AND borders
    ws.cell(row, 7).value = None
    ws.cell(row, 7).border = None
```
and finished with a per-requirement printout (`bold=True, border=True, wrap_text=True` per header cell; "Column G is empty"; H values listed).

Note the scoring nuance: the run wrote counts at rows 17/19/21/25 where the given "Expected Result" column was blank and **still scored 1.0** — trailing blanks in an example column mean "not yet computed", not "must remain empty". What mattered was reproducing the five non-blank given values and honouring the formatting clauses.

## Fix
1. Before coding, split the prompt on sentence boundaries and copy each imperative into a literal Python checklist:
   ```python
   TODO = ["bold+border headers row 4", "wrap_text row 4", "column G: no values, no borders", "counts in column H"]
   ```
2. Implement each; note that "no bordering" means `cell.border = None` (or a blank `Border()`), not just `cell.value = None`.
3. End with a verification block that prints one line per checklist item, reading the **saved** file.
4. Watch for imperatives hidden mid-paragraph or after the main question — 58484's formatting demands come *before* the computational question, 48745's "range the index in ascending order" comes last.
