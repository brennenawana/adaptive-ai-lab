# Text-Based Numeric Range Parsing

## Problem
Text cells contain numeric ranges in format "X to Y" (e.g., "2 to 5" meaning June 2 to June 5). Need to extract start/end values and calculate the inclusive count of items/days in that range. Manual parsing is tedious.

## Root Cause
Excel formulas lack built-in parsing for "X to Y" format. Text must be parsed programmatically to extract numeric components and perform arithmetic.

## Solution
Use regex to extract numbers, calculate inclusive range:

```python
import re

input_value = "2 to 5"
match = re.search(r'(\d+)\s+to\s+(\d+)', input_value)
if match:
    start = int(match.group(1))
    end = int(match.group(2))
    inclusive_count = end - start + 1  # 5 - 2 + 1 = 4
```

### How it works:
- Regex pattern `(\d+)\s+to\s+(\d+)` matches: digits, whitespace, "to", whitespace, digits
- Extract group(1) = start value, group(2) = end value
- Calculate: end - start + 1 (inclusive: includes both boundaries)
  - "2 to 5" → days 2, 3, 4, 5 → 4 days
  - "1 to 10" → days 1 through 10 → 10 days

## Example
Task 43589: Parse date range text
- Input: "2 to 5" (representing June 2 to June 5)
- Parsed: start=2, end=5
- Result: 5 - 2 + 1 = 4 days

## Key Points
- Regex pattern is flexible: `(\d+)\s+to\s+(\d+)` handles variable spacing
- Always add 1 to (end - start) for inclusive count
- Handle edge cases: whitespace trimming, validation before parsing
- Works with any numeric ranges (dates, item numbers, row ranges, etc.)
- Output is numeric, suitable for further calculations

## Variations
- "Jan 2 to Jan 5" → extract digits only, ignore month text
- "2-5" (dash instead of "to") → modify regex to `(\d+)\s*-\s*(\d+)`
- "2..5" → modify regex to `(\d+)\s*\.\.\.\s*(\d+)`
