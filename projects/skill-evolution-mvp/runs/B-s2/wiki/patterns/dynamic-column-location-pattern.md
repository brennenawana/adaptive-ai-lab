# Dynamic Column Location Pattern

## Problem
Column position changes daily due to new data; hardcoding column letters (cut column I, paste column B) breaks when column position shifts.

## Root Cause
VBA code cuts/pastes specific columns (e.g., `Columns("I").Cut`), which fails if '0-15' moves from column I to column J tomorrow.

## Successful Pattern (Task 408-39)
1. **Search header row for identifier**: Loop through row 5 to find header matching '0-15'
2. **Extract column index**: Save column number (9 for column I)
3. **Copy column data**: Use column index to read/write data dynamically
4. **Copy formatting**: Preserve fonts, fills, borders from source column

## Exact Syntax
```python
# Find column by header
column_0_15 = None
for col in range(1, ws.max_column + 1):
    if ws.cell(5, col).value == '0-15':
        column_0_15 = col
        break

# Copy to column B using index
for row in range(6, ws.max_row + 1):
    source_cell = ws.cell(row, column_0_15)
    target_cell = ws.cell(row, 2)  # Column B
    target_cell.value = source_cell.value
    # Copy formatting with copy() module
```

## Why This Works
- Searches header row each run → finds any column position
- No hardcoded column letters → scales to daily data changes
- Preserves formatting → meets visual requirements
