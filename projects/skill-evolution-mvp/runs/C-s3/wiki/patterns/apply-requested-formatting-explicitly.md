# Formatting stated in the instruction is part of the answer

## Pattern (SUCCESS) — task 39903, 1.000
Instruction: "...Please include all borders for cells C:2-6, with Courier new font 9pt."
The agent computed the counts, then applied the styling to exactly the named range:
```python
from openpyxl.styles import Font, Border, Side
thin = Side(style='thin')
border = Border(left=thin, right=thin, top=thin, bottom=thin)
font = Font(name='Courier New', size=9)
for r in range(2, 7):
    c = ws[f'C{r}']; c.value = count; c.font = font; c.border = border
```
and verified after reload by printing `cell.font.name`, `cell.font.size`, and each
`cell.border.<side>.style`.

## Notes
- Apply style to the **named range only**; do not restyle neighbours (55060 in iter 1 lost points
  for changing `number_format` outside the answer range).
- Verify style attributes explicitly on reload — a saved file can silently lose a style if it was
  assigned to a shared style object rather than per cell.
- Note the counting rule 39903 used: split the cell on ',', take the token before ':',
  and exclude names whose first char is in 'XZ' — worked examples in the prompt were unit-tested first.

## Iteration 4 note (36097, 0.000 — formatting clause left unhandled)
The instruction ended with "**Preserve the formatting of the cells in column I.**" The agent printed
column I once (all `None`, `number_format=General`), never mentioned it again, and instead copied
H4's number format onto H5/H6 (which already had it). When a clause names a range you think is
empty or irrelevant, still handle it explicitly and say so:
```python
for r in range(1, ws.max_row+1):
    src, dst = init_ws[f'I{r}'], ws[f'I{r}']
    for attr in ('font','border','fill','number_format','protection','alignment'):
        setattr(dst, attr, copy(getattr(src, attr)))
```
and assert the attributes survive the reload. A named formatting clause is a graded requirement even
when the cells look blank.

