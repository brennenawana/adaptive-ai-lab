# Reverse-Order Row Operations (Delete/Insert)

## Problem
When deleting or inserting multiple rows in an Excel worksheet using code, row numbers shift as operations execute. If processing rows in ascending order (1, 2, 3...), a delete at row 10 shifts all subsequent rows up, causing row 11 to become row 10, and subsequent operations reference wrong rows. Formulas may point to incorrect cells.

## Root Cause
Row shifting occurs when deleting/inserting rows. When row N is deleted, all rows N+1, N+2, ... shift down by 1. Processing forward causes reference instability.

## Solution
Process rows from highest to lowest (reverse order). When row 100 is deleted, rows 1-99 are unaffected. Iterate in descending order:

```python
# Identify rows to delete/insert first
rows_to_process = [10, 23, 45, 67]  # Found by scanning

# Process in reverse order (highest first)
for row_num in sorted(rows_to_process, reverse=True):
    ws.delete_rows(row_num, 1)  # or insert_rows(row_num, 1)
```

## Example
Task 370-43: Insert blank rows above every "X" marker
- Found rows with "X": [18, 32, 43]
- Processed in reverse: 43 → 32 → 18
- Result: Each insertion unaffected by previous insertions because higher rows don't shift lower rows

Task 247-24: Delete multiple rows
- Identified: Motorcycle rows, Ahmed Sons + Canada rows
- Deleted in reverse order to maintain row stability
- Then performed subsequent insert operations

## Key Points
- Always sort row numbers in descending order before processing
- Use `sorted(list, reverse=True)` in Python
- Works for both delete_rows() and insert_rows()
- Prevents cascading reference errors
- Critical when combining multiple row operations (delete then insert)

## Limitations
- Only solves row number shifting during operations
- Does not prevent formula reference breakage from operations themselves (e.g., VLOOKUP after structural changes)
- For complex multi-operation sequences, may need formula re-validation afterward

## Related Patterns
- When combining delete + insert + VLOOKUP in sequence, validate formulas after all row operations complete (Task 247-24 risk pattern)

## Validation Evidence (Iteration 6)
- Task 247-24: Deleted rows 9, 8, 7 (reverse order) successfully, then inserted 2 new rows after Ahmed Sons rows without cascading errors
- Task 370-43: Found X markers at rows 18, 32, 43; inserted blank rows above each (reverse: 43→32→18) - all 3 insertions executed correctly without row shifting issues
- Pattern confirmed: reverse iteration prevents row number instability during bulk operations