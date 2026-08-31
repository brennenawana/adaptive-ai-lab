# Multi-Criteria Lookup with Date Range Filtering

## Problem
Looking up a value based on multiple criteria (e.g., salesperson, type of sale, date) where the date must fall within a start/end date range on a lookup table. Excel formulas become extremely complex with nested INDEX/MATCH/IF combinations.

## Pattern Evidence
**Success (score 1.0):**
- Task 57558: Commission rate lookup by salesperson + type + date range
  - Criteria: Find rate matching (Type == 'Orange Sale') AND (Salesperson == 'John') AND (PODate >= StartDate AND PODate <= EndDate)
  - Row 2: Orange Sale + John + 2017-09-21 → matched rate 0.03 (date range: 2017-01-03 to 2018-09-25)
  - Row 3: Peach Sale + Chris + 2019-10-01 → matched rate 0.17 (date range: 2017-01-15 to 2019-10-07)
  - Both matches correct (2/2)

## Root Cause
Excel formulas struggle with:
- Multiple AND conditions simultaneously
- Date range checks (requires two comparisons: >= start AND <= end)
- Combining all criteria with dynamic lookup (would need array formula complexity)
- Combining SUMPRODUCT or multiple nested INDEX/MATCH
- Complex syntax makes formula error-prone and hard to debug

## Solution
**Use Python for:**
1. Load lookup table data into memory
2. Loop through each row needing lookup
3. For each row, iterate through lookup table
4. Check ALL criteria (type, salesperson, and date range)
5. Return first matching rate

## Implementation Pattern (Task 57558)
```python
import openpyxl

# Load lookup data
rate_data = []
for row in range(2, ws_rates.max_row + 1):
    rate_data.append({
        'start_date': ws_rates.cell(row, 1).value,
        'end_date': ws_rates.cell(row, 2).value,
        'type': ws_rates.cell(row, 3).value,
        'salesperson': ws_rates.cell(row, 4).value,
        'rate': ws_rates.cell(row, 5).value
    })

# Lookup for each deposits row
for dep_row in range(2, 4):
    sale_type = ws_deposits.cell(dep_row, 2).value
    salesperson = ws_deposits.cell(dep_row, 3).value
    po_date = ws_deposits.cell(dep_row, 4).value
    
    # Find matching rate
    for rate_record in rate_data:
        if (rate_record['type'] == sale_type and 
            rate_record['salesperson'] == salesperson and
            rate_record['start_date'] <= po_date <= rate_record['end_date']):
            ws_deposits.cell(dep_row, 1).value = rate_record['rate']
            break
```

## Why This Works
- Clear, readable logic with explicit AND conditions
- Date range check is trivial: `start_date <= date <= end_date`
- First match pattern prevents multiple results
- Easy to extend with more criteria (just add more `and` clauses)
- Debugging is straightforward: print intermediate values

## Comparison to Excel Formula
Excel would require something like:
```
=INDEX(RateHurdles!$E:$E, SUMPRODUCT((RateHurdles!$C:$C=B2)*(RateHurdles!$D:$D=C2)*(RateHurdles!$A:$A<=D2)*(RateHurdles!$B:$B>=D2)))
```
This is fragile, hard to understand, and breaks with version differences.

## Verification (Task 57558)
All lookups returned correct rates. Date range validation worked correctly for both test cases.
