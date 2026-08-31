# Delimited-Value Multi-Lookup Pattern

## Problem
Looking up multiple values in a single cell where values are separated by a delimiter (semicolon, comma, pipe, etc.), and needing to collect, deduplicate, and sort results from a lookup table.

## Pattern Evidence
**Success (score 1.0):**
- Task 48745: Product code lookup with semicolon delimiter
  - C5: "PRD1;" → D5: "Group 1" (single value, trailing semicolon handled)
  - C6: "PRD2;PRD1" → D6: "Group 1" (multiple values, same group)
  - C9: "PRD1;PRD4;PRD5" → D9: "Group 1, Group 2" (multiple values, different groups, sorted alphabetically)
  - C10: "PRD1;PRD6" → D10: "Group 1, Group 2"
  - All lookups correct, deduplication works, results sorted ascending

## Root Cause
Excel formulas struggle with:
- Splitting delimited text within a cell
- Iterating through each split value without helper columns
- Looking up each value independently
- Aggregating all results (not just first/last match)
- Deduplicating automatically
- Sorting results for consistent presentation
- Combining all logic in a single formula becomes unwieldy

## Solution
**Use Python for:**
1. Load lookup table into dictionary (fast O(1) lookups)
2. For each row, split the delimited string
3. Strip whitespace from each split value (handle edge cases like trailing delimiters)
4. Look up each value in dictionary, collecting matches
5. Use set() to automatically deduplicate results
6. Sort results (alphabetically for strings)
7. Join with comma-space for display

## Implementation Pattern (Task 48745)
```python
import openpyxl

# Load lookup table into dictionary
lookup_table = {}
for row in range(5, 11):
    code = ws.cell(row, 7).value  # Column G
    group = ws.cell(row, 8).value  # Column H
    if code and group:
        lookup_table[code] = group

# Process rows with delimited values
for row in range(5, 11):
    delimited_str = ws.cell(row, 3).value  # Column C
    
    if not delimited_str:
        ws.cell(row, 4).value = ""
        continue
    
    # Split by delimiter and clean up
    values = [v.strip() for v in delimited_str.split(';') if v.strip()]
    
    # Look up each value and collect results
    results = set()
    for value in values:
        if value in lookup_table:
            results.add(lookup_table[value])
    
    # Sort and output
    if results:
        output = ", ".join(sorted(results))
    else:
        output = ""
    
    ws.cell(row, 4).value = output
```

## Why This Works
- Dictionary lookup is O(1) efficient for multiple lookups per row
- Set() automatically handles deduplication (no duplicate groups in output)
- Sorting ensures consistent output (Group 1 before Group 2)
- Clean, readable logic that handles edge cases (trailing delimiters, whitespace)
- Easy to debug: print intermediate values to verify splits and lookups
- Scales to large lookup tables

## When to Use
- Multiple values in single cell need individual lookups
- Need to collect/aggregate ALL results (not just first match)
- Results need deduplication and consistent sorting
- Delimiter-separated data (semicolon, comma, pipe, etc.)
- Lookup results can vary (different groups, categories, etc.)

## Comparison to Excel
Excel would require:
- TEXTSPLIT (if Excel 365 available) or complex SUBSTITUTE workarounds for splitting
- Array formulas with IFERROR, SMALL, IF nesting for iteration
- Helper columns or multiple formulas to aggregate results
- Difficult to deduplicate and sort without VBA
- Result: fragile, version-dependent, nearly unmaintainable formula

## Lesson
When Excel cells contain delimited data that needs multi-value lookup and result aggregation, **Python is the right tool**. Dictionary-based lookup + set deduplication is a pattern that appears in many data processing scenarios.