# Consecutive Occurrence Counting with Smart Display

## Problem
Need to count how many consecutive rows have a specific value in a column, but display the count only once per group (on the final row). Example: Operator 5551234 makes 3 consecutive transfers → show "3" only on row 3 of that group, not on rows 1 and 2.

## Root Cause
Simple COUNTIF counts total occurrences in range. To count consecutive groups and display intelligently requires checking group boundaries and writing results selectively.

## Solution
For each row, check if it matches the criterion AND the next row doesn't match (group boundary). If boundary detected, count backward to find start of group, then write count only on current (final) row:

```python
for row_num in range(5, max_row + 1):
    current_value = ws.cell(row_num, 4).value  # Column D
    next_value = ws.cell(row_num + 1, 4).value if row_num < max_row else None
    
    # Check if current matches criterion and next doesn't (group boundary)
    if current_value == '5551234' and next_value != '5551234':
        # This is the last row of a group
        # Count backward to find group start
        count = 1
        check_row = row_num - 1
        while check_row >= 5:
            check_val = ws.cell(check_row, 4).value
            if check_val == '5551234':
                count += 1
                check_row -= 1
            else:
                break
        
        # Write count only on this final row
        ws.cell(row_num, 8).value = count  # Column H
    else:
        # Not a group boundary, leave blank
        ws.cell(row_num, 8).value = None
```

## Example
Task 58484: Count consecutive transfers from operator 5551234
- Row 6 (5551234): Next row different (18151234567) → boundary → count=1, display 1
- Rows 8-9 (5551234, 5551234): Row 9 next row different → boundary → count=2, display only on row 9
- Rows 23-25 (5551234, 5551234, 5551234): Row 25 next row different → boundary → count=3, display only on row 25
- Single occurrences show 1
- Non-matching rows show nothing

## Key Points
- Check CURRENT row matches AND NEXT row doesn't (not vice versa)
- Count backward from current position to find group size
- Write result ONLY on final row of group (the boundary row)
- Non-group rows left blank (prevents "all lines filled" issue)
- Works with any criterion value, not just 5551234

## Variations
- Count groups of numbers: `if current == 5 and next != 5: count_and_write()`
- Count groups of text: `if current == 'X' and next != 'X': count_and_write()`
- Count groups by condition: `if condition(current) and not condition(next): count_and_write()`

## Related Patterns
- Works with reverse-order-row-operations if groups need to be deleted/moved as units