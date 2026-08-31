# Date-Window Aggregation for Rolling Calculations

## Problem
Need to calculate rolling average or sum over a dynamic time window (e.g., previous 365 days) for data that doesn't have entries for every day. Manual date arithmetic for each row is tedious; need automated window-based aggregation.

## Root Cause
Excel formulas struggle with dynamic date windows for sparse data. SUMIF/AVERAGEIF work with fixed criteria but not with "all values within N days of current row's date" logic. Data gaps make row-based windows unreliable.

## Solution
Use code to iterate through data, calculating window boundaries based on dates:

```python
from datetime import datetime, timedelta

for current_row in data:
    current_date = current_row['date']
    window_start = current_date - timedelta(days=365)
    
    # Find all data points within window
    values_in_window = []
    for data_point in all_data:
        if window_start < data_point['date'] <= current_date:
            values_in_window.append(data_point['value'])
    
    # Calculate aggregate
    if values_in_window:
        rolling_avg = sum(values_in_window) / len(values_in_window)
        write_result(rolling_avg)
```

### How it works:
- For each row, calculate window boundaries: (current_date - N days) to current_date
- Scan all data to find entries within window (don't rely on row order)
- Aggregate values (sum, average, count) for matching entries
- Window automatically expands as more historical data accumulates
- Window shrinks when no data exists in earlier portion (sparse data)

## Example
Task 56786: 365-day rolling bean count average
- Data spans 2009-01-30 to 2011-06-26 (877 days) with sparse entries
- Row 4 (2009-01-30): Only 2 values in window → avg = 6.17
- Row 8 (2009-02-14): 5 values in window → avg = 383.91
- Row 100 (2010-07-10): 87 values in window → avg = 345.31
- Row 200 (2011-06-26): 128 values in window → avg = 460.63

## Key Points
- Window boundary is: window_start < date <= current_date (left-exclusive, right-inclusive)
- Use datetime/timedelta for reliable date arithmetic
- Sort by date first to potentially optimize scanning
- Handle edge cases: if no data in window, return empty or 0
- Works for any window size (days, weeks, months via timedelta)
- Fully dynamic: add new data and re-run to update all rolling calculations

## Scalability
For large datasets, optimize by:
- Pre-sorting data by date
- Using date indexing to narrow search range
- Calculating only for most recent N rows if full recalculation is expensive

## Distinction from date-threshold-filtering
- **date-threshold-filtering**: Find max date, calculate fixed threshold (max - N days), extract older rows
- **date-window-aggregation**: For each row, create dynamic window based on that row's date, aggregate matching values

## Related Patterns
- [date-threshold-filtering](wiki/patterns/date-threshold-filtering.md) - for extracting historical data
- [conditional-aggregation-sumproduct](wiki/patterns/conditional-aggregation-sumproduct.md) - for multi-criteria sums without date windows