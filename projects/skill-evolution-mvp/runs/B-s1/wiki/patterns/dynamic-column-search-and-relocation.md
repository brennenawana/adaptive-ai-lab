# Dynamic Column Search and Relocation

## Problem
Column position changes daily due to updated data structure. Need to find a column by header name (not fixed position) and move it to a target column with formatting preserved.

## Root Cause
Hardcoded column references ("always use column I") fail when data structure changes daily. Manual searching and moving is error-prone and not automatable.

## Solution
Search header row for matching column name, extract column index, copy values and formatting to target column:

```python
# Find the column by header name
column_index = None
for col_idx in range(1, max_column + 1):
    if sheet.cell(header_row, col_idx).value == "Column Name":
        column_index = col_idx
        break

# Copy values and formatting from found column to target
for row_idx in range(start_row, end_row + 1):
    source_cell = sheet.cell(row_idx, column_index)
    target_cell = sheet.cell(row_idx, target_column)
    target_cell.value = source_cell.value
    # Copy formatting: font, border, fill, number_format, alignment
    copy_cell_format(source_cell, target_cell)
```

## Example
Task 408-39: Relocate '0-15' age group column
- Data structure changes daily: '0-15' column could be at I, J, K, etc.
- Search row 5 headers for '0-15' → Found at column I
- Copy column I (rows 5-11) to column B with all formatting
- Result: Column B now contains '0-15' data (2, 1 values) regardless of source position
- Grand Total column L now sums correctly

## Key Points
- Search headers in consistent row (usually row 1 or 5)
- Use exact match or case-insensitive comparison
- Preserve all formatting: font, borders, fill, number format, alignment
- Works with any number of columns
- Automatable - no manual intervention needed for daily data changes

## Implementation Notes
- Use openpyxl: `copy(source_cell.font)` to copy each style element
- Use `cell.has_style` to check if formatting exists before copying
- Verify column was found before attempting copy (avoid silent failures)
