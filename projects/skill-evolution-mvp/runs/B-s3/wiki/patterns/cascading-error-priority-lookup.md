# Cascading Error Priority Lookup

## Problem
Need to return first available (non-error) value from multiple columns, checking left-to-right in priority order. If column A contains #N/A, check B; if B has #N/A, check C; only blank if all are #N/A.

## Root Cause
Simple priority-based selection across multiple columns requires checking for errors sequentially. IFERROR function treats any error (including #N/A) as a condition.

## Solution
Nest IFERROR functions in priority order:
```
=IFERROR(first_choice, IFERROR(second_choice, IFERROR(third_choice, "")))
```

## Example (Task 42354)
For columns A, B, C with priority A→B→C:
```
=IFERROR(A2, IFERROR(B2, IFERROR(C2, "")))
```

For each row:
- Row 2: A="Completed" → returns "Completed"
- Row 3: A=#N/A, B="2022-03-15" → returns "2022-03-15" 
- Row 4: A=#N/A, B=#N/A, C="ENR" → returns "ENR"
- Row 8: All #N/A → returns blank

## Key Advantages
- Simple and intuitive logic
- Works with any error type
- Easy to extend to more columns
- Excel 2016+ compatible

## Limitation
Not suitable if you need to distinguish between different error types. All errors are treated the same.
