# Sequence Detection Formula Complexity

## Problem
Detecting sequences or streaks (e.g., "count transfers only on the last row of a consecutive group") requires complex Excel logic with row-relative comparisons that become fragile and hard to maintain.

## Pattern Evidence
**Failure (score 0.0):**
- Task 58484: Count operator 5551234 transfers, display total only on last transfer in sequence
  - Expected: Show count (e.g., "1", "2") only on the final transfer in each consecutive group
  - Attempted solution: Complex nested IF/SUMPRODUCT:
    ```
    =IF(D6<>5551234,"",IF(OR(ROW()=26,INDIRECT("D"&ROW()+1)<>5551234),SUMPRODUCT((D$5:D6=5551234),(--(ROW(D$5:D6)>IFERROR(AGGREGATE(14,6,ROW(D$5:D5)/(D$5:D5<>5551234),1),0)))),))
    ```
  - Problem: Over-complicated, uses INDIRECT/AGGREGATE/IFERROR chains, still failed (0.0 score)

## Root Cause
Excel formulas struggle with:
- Comparing current row to next row (requires INDIRECT for row references)
- Detecting "last in sequence" (requires lookahead logic)
- Counting items from "sequence start" to current row (requires dynamic range start)
- Combining all logic in single formula creates nesting hell
- INDIRECT/AGGREGATE workarounds are version-dependent and error-prone

## Solution
**Use Python for:**
1. Loop through all rows forward
2. For each row, check if it's the start of or continuation of a sequence
3. Look ahead one row to detect sequence break
4. Only populate count when sequence ends

## Implementation Pattern
```python
for row in range(5, 27):
    col_d_val = ws.cell(row, 4).value
    
    # Check if this is an operator transfer (5551234)
    if col_d_val == 5551234:
        # Check if next row is different or we're at end
        is_last_in_sequence = False
        if row == 26:  # Last row
            is_last_in_sequence = True
        elif row < 26:
            next_col_d = ws.cell(row + 1, 4).value
            if next_col_d != 5551234:  # Sequence breaks
                is_last_in_sequence = True
        
        if is_last_in_sequence:
            # Count consecutive 5551234s up to this row
            count = 0
            for check_row in range(row, 4, -1):
                if ws.cell(check_row, 4).value == 5551234:
                    count += 1
                else:
                    break
            ws.cell(row, 8).value = count
        else:
            ws.cell(row, 8).value = None
```

## Why This Works
- Lookahead is trivial: just read `next_row = row + 1`
- Counting backwards is simple: loop and decrement
- Logic is explicit and easy to understand
- No nested functions or INDIRECT workarounds
- Easy to debug: can print each decision

## When to Use
- Detecting runs or streaks in data
- Marking first/last occurrence of a group
- Conditional counting within sequences
- Any logic involving "look ahead" or "look back" to neighbors

## Lesson
When formulas need relative row logic or lookahead, **Python is the right tool**. Excel formulas can't naturally express "if next row differs from current row, then count backwards."
