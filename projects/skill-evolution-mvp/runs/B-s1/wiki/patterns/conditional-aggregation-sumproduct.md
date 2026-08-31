# Conditional Aggregation with SUMPRODUCT

## Problem
Need to calculate totals (sum of products) based on multiple criteria, where values come from multiple columns. Example: sum of (width × height) for each material type. Manual aggregation or pivot tables are tedious; need dynamic formula-based solution.

## Root Cause
VLOOKUP/SUMIF work on single criteria and return single values. SUMPRODUCT can multiply multiple condition arrays with data columns to aggregate sums conditionally.

## Solution
Use SUMPRODUCT to multiply conditions with data ranges:
```excel
=SUMPRODUCT(($A$2:$A$276=G2)*($B$2:$B$276)*($C$2:$C$276))
```

### How it works:
- `($A$2:$A$276=G2)` creates TRUE/FALSE array where material matches (converted to 1/0)
- `($B$2:$B$276)` is the Width column (numeric values)
- `($C$2:$C$276)` is the Height column (numeric values)
- Multiply the arrays: (1/0) × width × height for each row
- SUMPRODUCT sums all products → total area for matching material

## Example
Task 263-1: Calculate total area for each material type
- Material = 'glass' in G2 → sum of all width × height where material = 'glass' → 3710 sqf
- Material = 'metal' in G3 → sum of all width × height where material = 'metal' → 1660 sqf
- Material = 'PVC' in G4 → sum of all width × height where material = 'PVC' → 2753 sqf

Data rows 2-276 contain (Mtrl, Width, Height) for each item. Formula dynamically calculates totals.

## Key Points
- All range arrays must be same size
- Condition arrays are converted to 1/0 automatically via multiplication
- Works with any numeric columns (not limited to 2)
- Fully dynamic: if data changes, totals update automatically
- More flexible than SUMIF for multi-column products

## Scalability
For 3+ condition columns:
```excel
=SUMPRODUCT(($A$2:$A$100=G2)*($B$2:$B$100=H2)*($C$2:$C$100)*($D$2:$D$100))
```
Each additional criteria column gets its own equality check with AND logic via multiplication.
