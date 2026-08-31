# Delimiter-Separated Field Parsing and Filtering

## Problem
Column contains multiple values separated by delimiter (comma, semicolon, etc.), often with additional structure (e.g., "CODE:quantity"). Need to parse, apply condition filter, and aggregate results without manual steps.

## Root Cause
Excel formulas have no built-in delimiter parsing with conditional logic. SUMIF/VLOOKUP work on entire cells, not substrings. Manual filtering is tedious.

## Solution
Parse in code (Python/VBA) by splitting on delimiter, applying condition, aggregating:

```python
for cell_value in column_c:
    parts = cell_value.split(',')  # or ';'
    for part in parts:
        part = part.strip()
        if ':' in part:
            code = part.split(':')[0].strip()
        else:
            code = part
        if condition(code):  # e.g., not startswith('X')
            result += 1
```

### Condition Examples:
- Prefix check: `not code.startswith('X')` or `not code.upper().startswith('Z')`
- Contains check: `'PK' in code`
- Exact match: `code == 'specific'`

## Examples

### Task 39903: Count bin locations not starting with X or Z
- Input: "A-01-A-02-C-04:5, Z-07-C-05-A-02:9"
- Split by comma → ["A-01-A-02-C-04:5", "Z-07-C-05-A-02:9"]
- Extract before colon → ["A-01-A-02-C-04", "Z-07-C-05-A-02"]
- Filter: exclude if starts with X or Z → ["A-01-A-02-C-04"]
- Result: count = 1

### Task 48745: Lookup multiple codes, collect unique groups
- Input: "PRD1;PRD4;PRD5"
- Split by semicolon → ["PRD1", "PRD4", "PRD5"]
- Lookup each → ["Group 1", "Group 2", "Group 2"]
- Unique groups → set(["Group 1", "Group 2"])
- Sort → ["Group 1", "Group 2"]
- Join → "Group 1, Group 2"

## Key Points
- Always strip() whitespace after split
- Handle structural delimiters (colon, dash) within parts
- Use set() for deduplication before aggregating
- Sort results for consistent output
