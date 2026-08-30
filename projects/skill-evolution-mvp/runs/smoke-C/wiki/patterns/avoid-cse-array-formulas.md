# Avoid CSE / array formulas in generated spreadsheets

## Status note (corrected after re-reading the iter-1 trace)
The actual 57445 trace used SUMIFS, not the array formula below, and *still* scored 0.000 — so this pattern is a real Excel-portability hazard but was **not** the cause of that failure (see excel-formula-needs-cached-values.md). Keep the guidance; do not attribute scores to it without evidence.

## Problem
For a two-key + range lookup, an agent may write:
```excel
=IFERROR(INDEX('Package & Weight Data'!$D:$D,MATCH(1,('Package & Weight Data'!$A:$A=C2)*('Package & Weight Data'!$B:$B<=D2)*('Package & Weight Data'!$C:$C>=D2),0)),"")
```
This is a legacy array formula requiring Ctrl+Shift+Enter. Written as a plain `<f>` by openpyxl it is not marked as an array formula, so LibreOffice/older Excel evaluate `MATCH(1, scalar, 0)` and return #N/A — which the surrounding `IFERROR` silently converts to `""`. The failure is invisible.

## Root cause
`IFERROR(...,"")` masks the breakage, and full-column references (`$D:$D`) make array evaluation extra expensive/unreliable.

## Fix — use non-array equivalents
```excel
=SUMIFS('Package & Weight Data'!$D$2:$D$8,'Package & Weight Data'!$A$2:$A$8,C2,'Package & Weight Data'!$B$2:$B$8,"<="&D2,'Package & Weight Data'!$C$2:$C$8,">="&D2)
```
or `SUMPRODUCT(...)`, or `LOOKUP(2,1/((...)*(...)),range)`. Guidelines:
- Prefer SUMIFS/SUMPRODUCT over INDEX/MATCH-with-multiplication.
- Use bounded ranges (`$A$2:$A$8`), not whole columns.
- Drop `IFERROR` while testing so errors are visible; add it back only at the end.
- Verify by recalculating (see excel-formula-needs-cached-values.md).

## Additional guidance from the 57445 trace
Even the correct SUMIFS used full-column references (`'Package & Weight Data'!$D:$D`). Prefer bounded ranges matching `ws.max_row` (here `$D$2:$D$19`): full-column refs slow recalculation, can pick up stray cells in the 12 empty trailing columns of that sheet, and some engines refuse them inside SUMIFS criteria.
