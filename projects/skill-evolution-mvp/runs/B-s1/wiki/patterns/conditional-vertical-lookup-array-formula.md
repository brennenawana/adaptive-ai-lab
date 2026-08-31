# Conditional Vertical Lookup with Array Formula

## Problem
Need vertical lookup that only returns values meeting a condition (e.g., starting with 'PK'), skipping non-matching entries. Manual filtering/deleting is tedious.

## Root Cause
Standard VLOOKUP/HLOOKUP cannot filter by condition during lookup. User manually copies, filters, deletes rows as workaround.

## Solution
Use INDEX/SMALL/IF array formula:
```excel
=IFERROR(INDEX($B$4:$B$15,SMALL(IF(LEFT($B$4:$B$15,2)="PK",ROW($B$4:$B$15)-ROW($B$4)+1),ROW(A1))),"")
```

### How it works:
- `LEFT($B$4:$B$15,2)="PK"` creates TRUE/FALSE array for condition
- `ROW($B$4:$B$15)-ROW($B$4)+1` converts matching rows to relative positions (1,2,3...)
- `SMALL(IF(...),ROW(A1))` gets nth smallest matching position
  - E4: ROW(A1)=1 → 1st match
  - E5: ROW(A1)=2 → 2nd match
  - E6: ROW(A1)=3 → 3rd match
- `INDEX(...)` retrieves value at that position
- `IFERROR(...,"")` returns blank when no more matches

## Usage
1. Enter formula in E4
2. Press **Ctrl+Shift+Enter** (not just Enter) to make array formula
3. Copy down to E5, E6, etc.
4. Excel will automatically adjust ROW(A1) to ROW(A2), ROW(A3), etc.

## Example
Task 10452: Filter materials starting with 'PK'
- Source: B4:B15 containing mixed materials
- Condition: LEFT(value,2)="PK"
- Output: E4:E12 shows only PK materials in sequence

## Key Points
- Must enter with Ctrl+Shift+Enter, not just Enter
- Leave as-is when copying down (ROW() auto-adjusts)
- Works in Excel 2016+
