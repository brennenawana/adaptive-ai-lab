# Conditional Sequential Lookup

## Problem
Return the nth matching value from a range, where "matching" is based on a condition. For example, get the 1st product starting with "PK", then 2nd, then 3rd, etc., skipping non-matching values.

## Root Cause
Simple INDEX/MATCH can't skip non-matching values in sequence. Need to: (1) identify matching positions, (2) get the nth matching position, (3) return value at that position.

## Solution
Use INDEX/SMALL/IF array formula:
```
=IFERROR(INDEX(range, SMALL(IF(condition, ROW(range)-ROW(range)+1), n)), "")
```

Where `n` increases as formula copies down (e.g., ROW()-ROW($E$4)+1).

## Example (Task 10452 - PASSING)
Extract values starting with "PK" from B4:B15 into E4:E12:
```
=IFERROR(INDEX($B$4:$B$15, SMALL(IF(LEFT($B$4:$B$15,2)="PK", ROW($B$4:$B$15)-ROW($B$4)+1), ROW()-ROW($E$4)+1)), "")
```

How it works:
1. LEFT($B$4:$B$15,2)="PK" creates TRUE/FALSE array
2. ROW($B$4:$B$15)-ROW($B$4)+1 converts to position numbers [1,2,3...12]
3. IF filters positions: [1,3,5,7...] (only PK positions)
4. SMALL(..., ROW()-ROW($E$4)+1) gets 1st, 2nd, 3rd... matching position as formula copies down
5. INDEX retrieves value at that position
6. IFERROR returns empty when no more matches

Result:
- E4: 1st PK value ("PK01/P819760979")
- E5: 2nd PK value ("PK01/P819761058")
- ... continues in order, skipping non-PK entries

## Critical Note
**IMPORTANT:** This is an ARRAY FORMULA. When entering in Excel:
- Type formula normally
- Press **Ctrl+Shift+Enter** (NOT just Enter)
- Excel will add curly braces: {=IFERROR(...)}

## Limitations
- Requires array formula entry (more complex for end users)
- Can be slow on large ranges
- Less intuitive than simple VLOOKUP

## When to Use
- Skip non-matching values in order
- Matrix filtering
- Complex conditional extraction
