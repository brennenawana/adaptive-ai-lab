# Direct Data Manipulation vs. Excel Formulas

## Problem
Complex Excel formulas fail in test environments (formula errors, version incompatibility, range scoping issues), while simpler solutions using Python/openpyxl succeed consistently.

## Pattern Evidence
**Failures (score 0.0) - Iter 1:**
- Task 39931: INDEX/SUMPRODUCT multi-criteria lookup
- Task 47766: SUMIFS date-range rolling calculation
- Task 10452: FILTER vertical lookup
- Task 56786: AVERAGEIFS rolling average

**Successes (score 1.0) - Iter 1:**
- Task 82-30: Python extraction + arrangement of whole numbers
- Task 192-22: Python keyword scanning + populate column
- Task 408-39: Python dynamic column find + copy

**Failures (score 0.0) - Iter 2:**
- Task 42354: IFERROR nested formula (incomplete else clause)
- Task 55060: IF formula (missing else clause + wrong number format)
- Task 58484: Complex IF/SUMPRODUCT sequence detection
- Task 263-1: SUMPRODUCT aggregation formulas

**Successes (score 1.0) - Iter 2:**
- Task 192-22: Python keyword scanning (case-insensitive substring matching)
- Task 43589: Python regex parsing (extract numbers from text ranges)
- Task 57558: Python multi-criteria lookup with date range validation

**Successes (score 1.0) - Iter 3:**
- Task 48745: Python delimited value multi-lookup (split semicolons, lookup each, collect unique groups, sort)
- Task 58484: Python sequence detection (lookahead logic to count only on last transfer in sequence)
- Task 66-24: Python date threshold filtering (identify rows older than max_date - 30 days, copy with formatting)

## Root Cause
1. **Formula Fragility**: Complex formulas (SUMPRODUCT, SMALL/IF arrays, nested IF/IFERROR) are error-prone and prone to incomplete implementation
2. **Version Incompatibility**: Modern functions (FILTER) not available in test harness
3. **Range Complexity**: Hard to scope ranges correctly; test data often extends differently
4. **Text Processing Limitation**: Excel formulas lack regex support, flexible substring matching, and keyword scanning
5. **Multi-Criteria Complexity**: Date range validation + multiple criteria = nested INDEX/MATCH/IF nightmare
6. **Relative Row Logic**: Formulas can't easily look ahead/behind to detect sequences
7. **Testing Difficulty**: Can't easily verify formula logic without opening in Excel

## Solution
**Use Python for:**
- Multi-criteria lookups (iterate + match)
- Sparse data with dynamic ranges (loop + filter)
- Conditional arrangement (extract, filter, arrange)
- Keyword/text matching (string operations, case-insensitive substring matching)
- Regex-based text parsing (extract numbers, patterns from text)
- Multi-criteria lookup with date range filtering (salesperson + type + date range)
- Sequence/streak detection (lookahead/lookback logic)
- Complex conditional logic (if statements easier than nested formulas)

**Use Formulas only for:**
- Simple VLOOKUP (single criterion)
- Straightforward aggregation (SUM, COUNT)
- Static ranges with guaranteed data extent
- Simple error handling (IFERROR when formula is complete and correct)
- Basic date range sums (AVERAGEIFS with proper row bounds)

## Implementation Pattern
```python
import openpyxl

# Basic iteration pattern for multi-criteria
for row in range(2, ws.max_row + 1):
    # Read criteria
    crit1 = ws.cell(row, col_a).value
    crit2 = ws.cell(row, col_b).value
    lookup_val = ws.cell(row, col_c).value
    
    # Find match in lookup table
    for lookup_row in range(2, lookup_ws.max_row + 1):
        if (lookup_ws.cell(lookup_row, col_x).value == crit1 and
            lookup_ws.cell(lookup_row, col_y).value == crit2 and
            lookup_ws.cell(lookup_row, col_z).value <= lookup_val <= lookup_ws.cell(lookup_row, col_w).value):
            ws.cell(row, result_col).value = lookup_ws.cell(lookup_row, result_lookup_col).value
            break

# Text matching pattern
for row in range(2, ws.max_row + 1):
    text = str(ws.cell(row, col).value).lower()
    if any(keyword.lower() in text for keyword in keywords_list):
        ws.cell(row, result_col).value = "Match Found"

# Regex pattern
import re
for row in range(2, ws.max_row + 1):
    text = ws.cell(row, col).value
    match = re.search(r'pattern', text)
    if match:
        extracted = match.group(1)
        ws.cell(row, result_col).value = extracted
```
