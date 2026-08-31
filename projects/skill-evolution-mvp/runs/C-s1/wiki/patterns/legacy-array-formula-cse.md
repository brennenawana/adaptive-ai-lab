# Legacy CSE Array Formulas Cannot Be Written by openpyxl

**Type:** Failure pattern

## Problem
The classic "filter a list" idiom
`=IFERROR(INDEX($B$3:$B$15,SMALL(IF(LEFT($B$3:$B$15,2)="PK",ROW($B$3:$B$15)-ROW($B$3)+1),ROW()-3)),"")`
is a Ctrl+Shift+Enter (CSE) array formula in pre-dynamic-array Excel. Written as a plain string by openpyxl it is stored without the array flag (`<f t="array" ref=...>`), so it evaluates the IF over only the first element -> `#VALUE!` or blank.

## Root cause
openpyxl has no API to set the CSE array attribute on a normal cell assignment; the agent assumed "Excel will recognize it as an array formula" (it stated this in its final answer for task 10452, which scored 0.000).

## Evidence
- Task 10452: identical formula written to E4:E12; the agent had already printed the correct ordered PK values from column B but never wrote them.

## Fix
- Compute the filtered list in Python and write the literal strings down the target range; pad remaining cells with `None`.
- If a formula is genuinely required, prefer a non-array modern equivalent (`=TEXTJOIN`, `=FILTER`) and still materialize values via a LibreOffice recalculation pass.