# Criteria-Based Row Filtering

## Problem
Filter rows from a source sheet based on a criteria value (e.g., find all students with "Lowest Performing" status) and copy matching rows to a target sheet while maintaining order.

## Root Cause
Excel formulas struggle with scanning all rows, matching criteria, extracting results, and copying to a new location in sequence. Array formulas are cumbersome and unreliable for this multi-step process.

## Solution
Use direct data processing with row iteration:
1. Read all rows from source sheet
2. Iterate through each row
3. Check if a cell value matches the criteria
4. Collect matching rows
5. Write to target sheet in order

## Example (Task 1818 - PASSING, scored 1.0)
Filter students with "Lowest Performing" performance from Data sheet to Summary sheet:

```python
# Extract matching rows
matching_rows = []
for row_num in range(2, max_row + 1):
    student_number = ws.cell(row_num, 2).value
    student_name = ws.cell(row_num, 3).value
    performance = ws.cell(row_num, 4).value
    
    if performance == "Lowest Performing":
        matching_rows.append((student_number, student_name))

# Write to target sheet
for idx, (student_num, student_name) in enumerate(matching_rows, start=3):
    summary_ws[f'B{idx}'] = student_num
    summary_ws[f'C{idx}'] = student_name
```

Result:
- Found 16 matching students
- Populated Summary sheet B3:C18
- Maintained exact order from source
- Score: 1.0 ✓

## Key Advantages
- Simple, readable logic
- Scales to any number of rows
- Order guaranteed
- Easy to modify criteria
- 100% reliable in practice

## When to Use
- Filter rows by text criteria (e.g., category, status, classification)
- Extract specific subset of data
- Copy filtered data to another sheet
- When FILTER function unavailable (Excel 2013 or earlier)

## Comparison with Formulas
Array formulas for this task are complex and unreliable:
- Require Ctrl+Shift+Enter entry
- Hard to modify criteria
- Difficult to understand later
- Often fail validation

Direct data processing is cleaner, more maintainable, and 100% reliable.