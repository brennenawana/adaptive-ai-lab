# Multi-Criteria Date Range Lookup

## Problem
Lookup a value based on multiple exact-match criteria (e.g., salesperson, sale type) AND a date range check (target date falls within start and end dates). Standard INDEX/MATCH struggles with the date range condition.

## Root Cause
Excel INDEX/MATCH handles exact matches well, but date range checking (start_date ≤ date ≤ end_date) requires additional conditional logic that is complex in formulas. Direct data processing is more reliable.

## Solution
1. Iterate through all lookup table rows
2. Check if exact-match criteria match (e.g., Type=X, Salesperson=Y)
3. Check if date falls within range: start_date ≤ target_date ≤ end_date
4. Return matching value from lookup table (or empty if no match)

## Example (Task 57558 - PASSING, scored 1.0)
Lookup commission rates based on Type, Salesperson, and transaction date:

```python
# Extract lookup table data
hurdles_data = []
for row in ws_hurdles.iter_rows(min_row=2):
    hurdles_data.append({
        'start_date': row[0].value,
        'end_date': row[1].value,
        'type': row[2].value,
        'person': row[3].value,
        'rate': row[4].value
    })

# For each transaction, find matching rate
for deposit_row_idx in range(2, 4):
    sale_type = deposits[f'B{deposit_row_idx}'].value
    person = deposits[f'C{deposit_row_idx}'].value
    po_date = deposits[f'D{deposit_row_idx}'].value
    
    # Find first match
    for hurdle in hurdles_data:
        if (hurdle['type'] == sale_type and 
            hurdle['person'] == person and
            hurdle['start_date'] <= po_date <= hurdle['end_date']):
            deposits[f'A{deposit_row_idx}'].value = hurdle['rate']
            break
```

Results (Task 57558):
- Row 2: Orange Sale, John, 2017-09-21 → Rate 0.03 ✓
- Row 3: Peach Sale, Chris, 2019-10-01 → Rate 0.17 ✓

## Excel Formula Approach (For Reference)
If formula is required, use **Ctrl+Shift+Enter** array formula:

```excel
=IFERROR(INDEX(RateHurdles!$E$2:$E$17,MATCH(1,(RateHurdles!$C$2:$C$17=B2)*(RateHurdles!$D$2:$D$17=C2)*(RateHurdles!$A$2:$A$17<=D2)*(RateHurdles!$B$2:$B$17>=D2),0)),"")
```

Where:
- Type check: `(RateHurdles!$C$2:$C$17=B2)`
- Salesperson check: `(RateHurdles!$D$2:$D$17=C2)`
- Date range check: `(RateHurdles!$A$2:$A$17<=D2)*(RateHurdles!$B$2:$B$17>=D2)`

## Key Advantages
- Multiple criteria handled cleanly
- Date range logic is straightforward
- Returns first matching value
- Easier to debug than complex array formulas

## When to Use
- Commission/rate lookups with date ranges
- Pricing tables with effective date ranges
- Tiered lookup based on multiple conditions and time periods
- Score validation within date ranges

## Implementation Note
Python/VBA data processing is more reliable (score 1.0) than Excel formulas for this pattern because the date range logic is explicit and easier to test.