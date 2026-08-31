# Test Harness Validation Gap Pattern

## Problem
Solutions that appear functionally correct (working logic, proper calculated values, well-formed formulas, correct output) still fail test validation with score 0.0, despite implementations looking correct in the workbook.

## Pattern Evidence
**Failures with apparently correct implementations (Iter 4):**
- Task 32438: Time extraction formula `=TIMEVALUE(RIGHT(I2,8))` created, AM/PM formatting applied correctly → Still scored 0.0
- Task 36097: Python recoupment calculation logic correct (values: 4000, 2250, -200, -250 computed correctly) → Still scored 0.0
- Task 48080: INDIRECT formula `=INDIRECT("A"&(25+(ROW()-2)*16))` dynamically extracts every 16th row → Still scored 0.0
- Task 10747: SUMPRODUCT formula `=SUMPRODUCT(($A$3:$A$8=$I3)*($B$3:$B$8=$J3)*$C$3:$C$8)` correct multi-criteria fix → Still scored 0.0
- Task 50916: Nested IF formulas with proper row references (B{ROW}=B$2:B$8 pattern) applied to all 18 cells → Still scored 0.0

## Root Cause
Unspecified test harness validation requirements beyond cell values and formulas:
- File structure or worksheet naming requirements
- Cell placement or range expectations
- Output format requirements (values vs formulas, number formats, cell formatting)
- Hidden validation rules not apparent from task descriptions

## Solution
When implementation appears functionally correct but fails validation:
1. **Verify output file structure**: Check worksheet names, cell ranges, header locations match task exactly
2. **Verify output format**: Test harness may expect values (not formulas) in certain cells
3. **Check cell formatting**: Number formats, alignment, font/fill may need to match source or requirements
4. **Re-read task description carefully**: Look for hidden requirements about cell placement, range, or output format
5. **Compare to working examples**: When tasks repeat (like 408-39, 39931, 48745), examine what made the repeat successful

## Contrast: Repeat Tasks Validation Success
**Tasks 408-39, 39931, 48745 all scored 1.0 when re-run:**
- Task 408-39: Dynamic column + format preservation worked on repeat
- Task 39931: Dictionary-based multi-criteria lookup worked on repeat
- Task 48745: Delimited multi-value split/lookup worked on repeat

These same solutions had been validated before, suggesting test harness is consistent but new task implementations may miss requirements.

## When to Consider This Pattern
- Solution logic looks correct when reviewed in Excel/openpyxl
- Formulas are well-formed, values are calculated correctly
- Score is 0.0 despite "looks correct" implementation
- No obvious formula errors or reference issues
- Time to investigate file structure, output format, cell placement requirements

## Lesson
Test harness validation may have requirements beyond cell content. When logic is correct but validation fails, shift focus from "did I calculate right" to "did I output in the right format/location/structure."
