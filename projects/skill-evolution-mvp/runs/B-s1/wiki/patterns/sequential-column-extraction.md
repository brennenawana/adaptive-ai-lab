# Sequential Column Extraction with Filtering

## Problem
Extract filtered numeric data from multiple columns (e.g., integers from column A, skip decimals in column B, integers from column C). Need to arrange in output 6 values per row. Manual filtering is tedious.

## Root Cause
Standard filtering approaches interleave columns (A1, B1, C1, A2, B2, C2...). Sequential extraction (all of A, then all of B, then all of C) is simpler and matches common data patterns.

## Solution
Process each source column completely before moving to next:

```python
results = []

# Extract all from column A
for row in range(1, max_row + 1):
    value = ws[f'A{row}'].value
    if is_whole_number(value):
        results.append(int(value))

# Extract all from column C (skip B which has decimals)
for row in range(1, max_row + 1):
    value = ws[f'C{row}'].value
    if is_whole_number(value):
        results.append(int(value))

# Extract all from column E (skip D which has decimals)
for row in range(1, max_row + 1):
    value = ws[f'E{row}'].value
    if is_whole_number(value):
        results.append(int(value))

# Arrange 6 per row in output
row_num = 1
for i, value in enumerate(results):
    col_num = (i % 6) + 1
    if col_num == 1 and i > 0:
        row_num += 1
    ws.cell(row_num, col_num).value = value
```

## Example
Task 82-30: Extract whole numbers from columns A, C, E
- Column A (rows 1-18): [12, 41, 22, 8, 7, 50, 38, 20, 6, 39, 43, 45, 26, 25, 32, 13, 31, 34] (18 values)
- Column C (rows 1-17): [19, 52, 30, 42, 10, 23, 37, 36, 2, 11, 1, 5, 29, 3, 9, 15, 28] (17 values, row 18 empty)
- Column E (rows 1-17): [18, 48, 49, 40, 17, 21, 46, 4, 35, 44, 47, 33, 51, 27, 14, 16, 24] (17 values)
- Total: 52 values → arrange as 9 rows of 6 values each
- Output rows: [12,41,22,8,7,50], [38,20,6,39,43,45], [26,25,32,13,31,34], [19,52,30,42,10,23], etc.

## Key Points
- Process each source column independently
- Apply filter condition within each column loop
- Collect all results in single list
- Arrange output using modulo arithmetic (i % 6) to determine position
- Simple and maintainable compared to interleaved approaches

## Task 82-30 Validation Evidence
Task 82-30 perfectly demonstrates the pattern:
- Raw Data sheet has 18 rows × 6 columns (A-F)
- Columns A, C, E contain whole numbers (integers)
- Columns B, D, F contain decimals
- Extracted 18 numbers from column A: [12, 41, 22, 8, 7, 50, 38, 20, 6, 39, 43, 45, 26, 25, 32, 13, 31, 34]
- Extracted 17 numbers from column C: [19, 52, 30, 42, 10, 23, 37, 36, 2, 11, 1, 5, 29, 3, 9, 15, 28]
- Extracted 17 numbers from column E: [18, 48, 49, 40, 17, 21, 46, 4, 35, 44, 47, 33, 51, 27, 14, 16, 24]
- Total: 52 values → arranged as 9 rows (6 per row) in output
- Output matches Manual Result sheet exactly ✓
- Pattern confirmed: sequential processing (all A, then all C, then all E) produces correct results
