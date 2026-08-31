# DateTime Formatting with TEXT Function

## Problem
Using RIGHT() or similar string functions on datetime values returns only the text portion without proper time formatting. Cell formatting alone doesn't work when the data is extracted as text.

Example: `=RIGHT(I2,8)` on "2021-09-29 18:08:00" returns "18:08:00" as text string, not formatted time.

## Root Cause
RIGHT() returns a text string, which bypasses Excel's datetime formatting system. Need to convert datetime object to formatted string using TEXT function.

## Solution
Use TEXT function with format code for time display:
```
=TEXT(datetime_value, "hh:mm:ss AM/PM")
```

## Example (Task 32438)
Formatting datetime in column I to time in column J:
```
=TEXT(I2,"hh:mm:ss AM/PM")
```

Results:
- I2 = 2021-09-29 18:08:00 → J2 = "06:08:00 PM"
- I3 = 2021-10-01 00:04:00 → J3 = "12:04:00 AM"
- I4 = 2021-10-01 08:08:00 → J4 = "08:08:00 AM"

## Common Format Codes
- `"hh:mm:ss AM/PM"` - 12-hour with seconds and AM/PM
- `"h:mm:ss AM/PM"` - 12-hour without leading zero on hour
- `"hh:mm"` - 24-hour format without seconds

## Key Advantages
- Proper formatting of time values
- Better than string manipulation
- Simple and reliable across Excel versions
