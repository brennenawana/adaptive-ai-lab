# Sparse Data Rolling Calculations

## Problem
Rolling averages fail when data is sparse (not every day has entry) and formula ranges include headers.

## Root Cause
Formula like `=AVERAGEIFS($B:$B,$A:$A,">="&(A4-365),$A:$A,"<="&A4)` references entire columns ($B:$B, $A:$A), including:
- Row 1-3: Headers (text) instead of dates → date comparisons fail
- Row 1 header "Beans Counted" cannot be compared to dates
- Results in NaN or zero instead of correct average

## Example Failure (Task 56786)
- Data: 199 rows, dates in column A, values in column B
- Formula included header in date range → calculation error
- Expected: Average of all values within 365 days of each row
- Got: Errors due to non-date header row

## Solution
1. **Use explicit row bounds**: `$B$6:$B$200` instead of `$B:$B`
2. **Validate data starts after header**: Check that row 6 is first data row
3. **Test with sparse data**: Verify formula handles gaps (multiple days with no entry)
4. **Formula structure**:
```excel
=AVERAGEIFS($B$6:$B$200, $A$6:$A$200, ">="&(A4-365), $A$6:$A$200, "<="&A4)
```
5. **Alternative**: Use Python to iterate and calculate manually → more reliable

## Verification
For each test row, manually verify:
- Date range captured (365 days lookback)
- Only rows within range included
- No header interference
