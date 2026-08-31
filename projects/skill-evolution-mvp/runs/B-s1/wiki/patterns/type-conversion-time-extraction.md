# Type Conversion: Time Extraction from DateTime

## Problem
Cell I contains datetime (e.g., 2021-09-29 18:08:00). Using =RIGHT(I2,8) extracts the time portion as text string "18:08:00". Applying time format h:mm:ss AM/PM doesn't work because Excel won't format text values.

## Root Cause
RIGHT() function returns text, not a numeric time value. Excel number formats only work on numeric values, not text. Text "18:08:00" and number 0.754166... (representing 6:08 PM) are different data types.

## Solution
Use MOD(datetime, 1) to extract time as numeric value, then apply time format:
```excel
=MOD(I2,1)
```
Apply cell format: `h:mm:ss AM/PM`

### How it works:
- In Excel, dates are integers (days since 1900) and times are decimals (0.0 to 0.999...)
- DateTime 2021-09-29 18:08:00 = integer part (date) + fractional part (time)
- MOD(value, 1) returns remainder after dividing by 1 = fractional part = time only
- Result is numeric, so number formats work correctly

## Example
Task 32438: Extract time from datetime in different AM/PM format
- Input: 2021-09-29 18:08:00
- Formula: =MOD(I2,1)
- Format: h:mm:ss AM/PM
- Output: 6:08:00 PM

## Alternative Approaches
- =HOUR(I2)&":"&MINUTE(I2)&":"&SECOND(I2) - returns text (won't format)
- TEXT(I2,"h:mm:ss AM/PM") - works but result is text, less flexible
- =MOD(I2,1) - best: returns time value, fully compatible with all time formats

## Key Points
- MOD returns numeric time value 0.0-0.999...
- Apply time format AFTER formula, not before
- Works with any time format: h:mm AM/PM, hh:mm:ss, etc.

## Task 32438 Evidence
Task 32438 successfully validated this pattern:
- Input: datetime 2021-09-29 18:08:00 in column I
- Formula applied: =MOD(I2,1)
- Format applied: h:mm:ss AM/PM
- Result: 6:08:00 PM (correctly extracted and formatted)
- Verified on rows 2-4 with dates: 2021-09-29 18:08:00, 2021-10-01 00:04:00, 2021-10-01 08:08:00
- All rows correctly displayed times with AM/PM formatting
