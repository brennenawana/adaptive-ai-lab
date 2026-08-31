# Multi-Criteria Lookup with SUMPRODUCT

## Problem
Multi-criteria lookups using INDEX/MATCH require array formula entry (Ctrl+Shift+Enter), which is error-prone and not intuitive for users. Looking up values based on two or more matching conditions across different columns.

## Root Cause
INDEX/MATCH array formulas require special entry mode in Excel 2016+, and behavior is inconsistent. SUMPRODUCT provides a more direct approach that works as regular formula entry.

## Solution
Use SUMPRODUCT with multiple conditions:
```
=IFERROR(SUMPRODUCT(($lookup_range1=$criterion1)*($lookup_range2=$criterion2)*$return_range),"")
```

## Example (Task 39931)
Looking up value from column K by matching column I against column B (row criteria) AND column J against column headers (column criteria):
```
=IFERROR(SUMPRODUCT(($I$3:$I$22=$B4)*($J$3:$J$22=C$3)*$K$3:$K$22),"")
```

This formula:
- Checks if I3:I22 matches value in B4 (row criterion)
- AND checks if J3:J22 matches header in C3 (column criterion)  
- Returns matching value from K3:K22
- Returns empty string if no match

## Key Advantages
- No array formula entry required (just Enter, not Ctrl+Shift+Enter)
- Works reliably across Excel versions
- More readable than nested INDEX/MATCH
- Handles multiple criteria elegantly

## When to Use
- Matrix-style lookups (both row and column criteria)
- Multiple condition matching
- Cross-version compatibility needed
