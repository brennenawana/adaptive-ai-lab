# Lookup-Table Population for Multiple Output Columns

## Problem
Need to populate multiple output columns for each row based on a lookup key. Example: School calendar where entering cycle day number automatically populates all classes for that day across multiple columns (H1, P1, P2, P3, P4, P5). Manual copy/paste is tedious and breaks with irregular patterns (off-days, cycle changes).

## Root Cause
Excel formulas handle single-value lookups well (VLOOKUP, INDEX/MATCH, SUMIF), but populating multiple output columns from a reference table requires building an in-memory lookup structure rather than using formulas.

## Solution
Build a lookup table from source data, then programmatically query it to populate multiple output columns:

```python
# Step 1: Build lookup table from source data
lookup_table = {}
for row in range(2, 9):  # Source rows
    key = ws.cell(row, 2).value  # Column B - lookup key (e.g., cycle day)
    values = []
    for col in range(3, 9):  # Columns C-H - output values
        values.append(ws.cell(row, col).value)
    lookup_table[key] = values

# Step 2: For each target row, query lookup and populate
for target_row in range(12, 15):
    key = ws.cell(target_row, 2).value  # Column B - lookup key
    
    if key in lookup_table:
        output_values = lookup_table[key]
        
        # Populate output columns C-H
        for col_offset, value in enumerate(output_values):
            ws.cell(target_row, 3 + col_offset).value = value
```

## Example
Task 50916: School calendar with 7-day cycle
- **Source data** (rows 2-8): For each cycle day (1-7), stores class names for H1, P1, P2, P3, P4, P5
- **Target data** (rows 12-14): Three dates with cycle day numbers in column B (1, 2, 3)
- **Lookup table**: `{1: [Homeroom, French, Math, Science, Eng. Lang. Arts, Social Studies], 2: [Homeroom, RE, Art, PE, Social Studies, Math], ...}`
- **Result**: Each target row populated with all classes for its cycle day:
  - Row 12 (Cycle 1): [Homeroom, French, Math, Science, Eng. Lang. Arts, Social Studies]
  - Row 13 (Cycle 2): [Homeroom, RE, Art, PE, Social Studies, Math]
  - Row 14 (Cycle 3): [Homeroom, French, Science, Math, RE, Eng. Lang. Arts]

## Key Points
- Lookup key can be any unique identifier (number, text, date, composite)
- Output array can contain any number of columns
- More flexible than formulas for multi-column populations
- Solves irregular cycle problems (off-days, cycle changes) - just change key value
- Reference data should be relatively static; lookup queries can be frequent
- Works well when multiple rows need the same reference mapping

## Variations
- **Composite keys**: Use tuples instead of single value
  ```python
  key = (ws.cell(row, 4).value, ws.cell(row, 8).value)  # (meet_name, race_number)
  lookup_table[key] = values
  ```
- **Selective columns**: Populate only specific output columns based on conditions
- **Occurrence counter**: For repeated keys, rotate through different result columns

## Related Patterns
- [multi-criteria-lookup-sumproduct](wiki/patterns/multi-criteria-lookup-sumproduct.md) - for single-value lookups with multiple criteria
- [conditional-aggregation-sumproduct](wiki/patterns/conditional-aggregation-sumproduct.md) - for calculating aggregates based on criteria
- [sequential-column-extraction](wiki/patterns/sequential-column-extraction.md) - for extracting and arranging multiple values
