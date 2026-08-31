# Python String Processing for Text Matching

## Problem
Keyword scanning and text pattern matching fail or become fragile in Excel formulas. Users need to find text containing keywords (case-insensitive, partial matches with prefixes/suffixes) and populate results conditionally.

## Pattern Evidence
**Success (score 1.0):**
- Task 192-22: Python keyword scanning in column D, populating column F
  - Keywords: 'Core Activation', 'Core Design', 'Mobile Terminology', 'Mobile Design', 'Mobile Integration', 'Testing Layer', 'Testing Offshore', 'Carrier', 'Barrier'
  - Found 18/70 matches (e.g., "Core Activation Signaling and Protocols" → "Billing PO")
  - Handled entries with numeric prefixes (e.g., "123-Core Design")

- Task 43589: Python regex parsing to extract date range
  - Pattern: `r'(\d+)\s*to\s*(\d+)'` extracted 2 and 5 from "2 to 5"
  - Calculated inclusive day count: 5 - 2 + 1 = 4

## Root Cause
Excel formulas lack:
- Flexible string searching (FIND requires exact case or multiple nested checks)
- Regex support (only basic SUBSTITUTE/SEARCH available)
- Collection/iteration logic for scanning multiple keywords
- Easy case-insensitive matching without helper columns

## Solution
**Use Python for:**
- Keyword scanning: `if keyword_lower in value_str`
- Case-insensitive matching: `str(value).lower()`
- Regex extraction: `re.search(r'pattern', text)`
- Prefix/suffix handling: substring matching handles automatically

## Implementation Pattern (Task 192-22)
```python
import openpyxl

keywords = ['Core Activation', 'Core Design', 'Mobile Terminology', ...]
keywords_lower = [kw.lower() for kw in keywords]

for row in range(2, max_row):
    value_d = ws.cell(row, 4).value
    if value_d is not None:
        value_str = str(value_d).lower()
        match_found = any(keyword_lower in value_str for keyword_lower in keywords_lower)
        ws.cell(row, 6).value = "Billing PO" if match_found else None
```

## Implementation Pattern (Task 43589 - Regex)
```python
import re
date_range = "2 to 5"
match = re.search(r'(\d+)\s*to\s*(\d+)', date_range)
if match:
    start = int(match.group(1))
    end = int(match.group(2))
    days = end - start + 1  # 4 days for "2 to 5"
```

## Why This Works
- Substring matching is trivial in Python (`in` operator)
- Case conversion is built-in (`.lower()` method)
- Regex is available via `re` module for complex patterns
- Loop-based processing naturally handles dynamic row counts
- No helper columns needed

## Verification (Task 192-22)
Scanned 70 rows, matched 18 rows containing keywords. Expected results matched in all cases.
