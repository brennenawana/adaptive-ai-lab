# Date Threshold Filtering and Row Extraction

## Problem
Need to extract rows where date is more than N days older than the maximum date in the dataset; manual date arithmetic and comparison is tedious and error-prone.

## Root Cause
Requires two steps: (1) find maximum date in column, (2) calculate threshold date (max - N days), (3) filter and copy rows. No single Excel function handles relative date filtering against max date.

## Solution
Use code to find max date, calculate threshold, filter rows, copy to new sheet:

```python
from datetime import datetime, timedelta

# Step 1: Find maximum date in column E
max_date = None
for row_idx in range(2, max_row + 1):
    date_val = sheet.cell(row_idx, 5).value  # Column E
    if isinstance(date_val, datetime):
        if max_date is None or date_val > max_date:
            max_date = date_val

# Step 2: Calculate threshold (N days before max)
threshold_date = max_date - timedelta(days=30)

# Step 3: Filter rows where date < threshold
rows_to_copy = []
for row_idx in range(2, max_row + 1):
    date_val = sheet.cell(row_idx, 5).value
    if isinstance(date_val, datetime) and date_val < threshold_date:
        rows_to_copy.append(row_idx)

# Step 4: Copy header + filtered rows to target sheet
# Copy header from source
# Copy filtered rows from source to target
# Preserve date formatting in target
```

## Example
Task 66-24: Extract orders more than 30 days old
- Max date found: 2023-08-25
- Threshold date (30 days before max): 2023-07-26
- Filter: date < 2023-07-26 → Found 2023-06-30 (56 days old) ✓
- Copy header row + 1 data row to 'Items Older than 30 days' sheet
- Maintain date formatting (datetime preserved)
- Delete column Z from target sheet
- Result: 1 row extracted, correctly identified as >30 days old

## Key Points
- Must find MAX date first, then calculate threshold relative to it
- Use `isinstance(date_val, datetime)` to filter non-date cells
- Threshold date = max_date - timedelta(days=N)
- Comparison: date_value < threshold (older than threshold)
- Copy header row to target sheet first
- Preserve date formatting (don't convert to text)
- Works for any N-day threshold (30, 60, 90, etc.)

## Edge Cases
- Handle rows with missing/None dates (skip them)
- If all dates are within N days of max: result will be empty (only header)
- Date format should be preserved with `number_format` copy
