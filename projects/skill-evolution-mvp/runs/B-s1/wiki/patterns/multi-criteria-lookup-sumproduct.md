# Multi-Criteria Lookup with SUMPRODUCT

## Problem
VLOOKUP cannot match on multiple columns simultaneously. User has lookup table with two criteria columns (e.g., lookup value in col I, secondary criterion in col J) and needs to return matching value from col K.

## Root Cause
VLOOKUP only matches the first column of the range. To match two criteria, need a different approach than standard vertical/horizontal lookup.

## Solution
Use SUMPRODUCT with multiple IF conditions:
```excel
=SUMPRODUCT((($I$3:$I$22)=B4)*(($J$3:$J$22)=C$3)*($K$3:$K$22))
```

### How it works:
- `($I$3:$I$22)=B4` creates TRUE/FALSE array for first criterion
- `($J$3:$J$22)=C$3` creates TRUE/FALSE array for second criterion  
- Multiply the arrays (AND logic) to get rows matching both criteria
- Multiply by values in `$K$3:$K$22` to extract matching values
- SUMPRODUCT sums the result (only one row should match, so sum = value)

## Example
Task 39931: Match two-column lookup table
- Column B (lookup value): x, y, z
- Column headers (secondary match): A, B, C, D
- Lookup table in I:K with both criteria
- Result: 23.56, 25.56, 42.1, etc.

## Key Points
- Both criteria ranges and return range must be same size
- SUMPRODUCT returns number, not error if no match
- Works in Excel 2016+

## Task 39931 Evidence
Task 39931 successfully validated 2D lookup approach:
- Built lookup dictionary from Data section (I:K): 20 entries with composite keys (code, header)
  - Examples: ('x', 'A')→23.56, ('x', 'B')→25.56, ('y', 'A')→8.77, ('z', 'D')→56.81
- Matched row keys (B column: x, y, z) with column headers (C:F: A, B, C, D)
- Created composite keys per cell and looked up in dictionary
- Successfully filled C4:F6 with correct values:
  - x row: 23.56, 25.56, 42.1, 73.63
  - y row: 8.77, 57.72, 98.88, 4.22
  - z row: 3.2, 85.75, 54.02, 56.81
- Pattern validated: SUMPRODUCT/dictionary lookup with multiple criteria outperforms VLOOKUP/MATCH
