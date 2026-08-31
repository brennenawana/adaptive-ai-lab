# Type Filtering and Row Reorganization

## Problem
Extract only values matching a type criteria (e.g., whole numbers only, skipping decimals), then reorganize into fixed-width rows (max items per row) while maintaining original order.

Example: Extract whole numbers from mixed integer/decimal columns, organize into rows of max 6 items each.

## Root Cause
Type filtering is challenging in pure Excel formulas. More reliable via data processing logic that can check data types directly and iterate reorganization.

## Solution
1. Iterate through source columns
2. Check if value matches type criteria (e.g., `value == int(value)`)
3. Collect matching values in order
4. Split into groups of fixed size
5. Write to output range row-by-row

## Example (Task 82-30 - PASSING, scored 1.0)
Extract whole numbers from columns A, C, E of Raw Data sheet (rows 1-18), organize into Numbers sheet with max 6 per row:

```python
# Step 1: Extract whole numbers
whole_numbers = []
for col in [0, 2, 4]:  # Columns A, C, E
    for value in raw_data[col]:
        if value == int(value):  # Check if whole number
            whole_numbers.append(int(value))

# Step 2: Organize into max-6-per-row groups
rows = []
for i in range(0, len(whole_numbers), 6):
    row = whole_numbers[i:i+6]
    # Pad with None if needed
    while len(row) < 6:
        row.append(None)
    rows.append(row)

# Step 3: Write to output
for row_idx, row_data in enumerate(rows, start=1):
    for col_idx, value in enumerate(row_data, start=1):
        if value is not None:
            ws.cell(row=row_idx, column=col_idx, value=value)
```

Result: 52 whole numbers extracted from 18 rows × 3 columns, organized into 9 rows × 6 columns in output sheet.

## Key Advantages
- Type criteria checked directly (no formula workarounds)
- Precise control over grouping
- Handles edge cases (last row with fewer items)
- Maintains original order
- Highly reliable (scored 1.0 on test)

## When to Use
- Extract by data type (numbers, text, dates)
- Reorganize data into fixed-width rows
- When formula complexity would be prohibitive
- Data processing via VBA or Python preferred

## Success Factor
This pattern succeeds because it bypasses Excel formula limitations and uses direct data processing logic, making it more robust than complex nested formulas.
