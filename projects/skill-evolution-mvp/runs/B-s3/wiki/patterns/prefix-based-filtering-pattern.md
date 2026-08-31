# Prefix-Based Filtering Pattern

## Problem
Need to include or exclude items from processing based on what they start with. Common use cases: filter out pallet locations starting with X or Z, include only material codes starting with PK, count items NOT starting with certain prefixes.

## Root Cause
String-based filtering requires checking the beginning characters of values. Using LEFT() or character indexing efficiently solves this.

## Solution
### Option 1: LEFT() Function
```
LEFT(value, number_of_chars) = "PK"
LEFT(location_code, 2) <> "X" AND LEFT(location_code, 2) <> "Z"
```

### Option 2: First Character Check
```
value[0].upper() in ['X', 'Z']  (in Python)
location_code[0] NOT IN ('X', 'Z')  (in VBA logic)
```

## Example 1 (Task 10452 - Exclude entries NOT starting with PK)
Filter column B to show only values starting with "PK":
```
=IFERROR(INDEX($B$4:$B$15,SMALL(IF(LEFT($B$4:$B$15,2)="PK",ROW($B$4:$B$15)-ROW($B$4)+1),ROW()-ROW($E$4)+1)),"")
```
Extracts: "PK01/P819760979", "PK01/P819761058", etc.
Skips: "FABRIC CARE", "BONUS GOLD", "BRITE MAXIMUM POWER"

## Example 2 (Task 39903 - Count items NOT starting with X or Z)
Count valid bin locations:
```python
if location_code and not (location_code[0].upper() in ['X', 'Z']):
    count += 1
```
Input: "A-01-A-02-C-04.D: 5, Z-07-C-05-A-02:9"
Result: 1 (Z-prefixed location excluded)

## Key Advantages
- Simple substring check
- Efficient filtering
- Works in formulas and code
- Case-insensitive when needed

## Common Use Cases
- Exclude pallet locations (X*, Z*)
- Include material codes (PK*)
- Skip header rows by content
- Filter by product line prefix
