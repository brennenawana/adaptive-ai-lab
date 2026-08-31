# Formula Range Scoping Errors

## Problem
Excel formulas fail silently or produce incorrect results when ranges are too broad or improperly bounded.

## Root Cause
Formulas like `=AVERAGEIFS($B:$B,$A:$A,">="&(A4-365),$A:$A,"<="&A4)` reference entire columns, including:
- Header rows (text) interfering with date/numeric comparisons
- Empty cells below data causing NaN or division errors
- Unbounded ranges that break when test harness extends data

## Examples from Traces
- **Task 56786**: AVERAGEIFS used $B:$B (entire column) → header row caused calculation errors
- **Task 39931**: INDEX range $K$3:$K$21 may have been too small if data extended beyond row 21

## Solution
1. **Explicitly bound ranges**: Use specific row limits like $B$6:$B$200 instead of $B:$B
2. **Validate data extent**: Check max_row before setting formula range
3. **Test with empty rows**: Verify formula handles sparse data without errors
4. **Start formula row consistently**: Begin data ranges one row below header (e.g., row 6 if header is row 5)

## Verified Workaround
Use Python/openpyxl to directly extract data, avoiding formula complexity entirely.
