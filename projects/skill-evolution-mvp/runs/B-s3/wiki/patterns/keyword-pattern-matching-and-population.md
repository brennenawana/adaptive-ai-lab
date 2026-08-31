# Keyword Pattern Matching and Population

## Problem
Search for multiple keywords (case-insensitive, partial match allowed) in cells across many rows, and populate a target column based on whether a match is found.

Example: Scan column D for 9 different keywords, populate column F with "Billing PO" if any keyword found.

## Root Cause
Excel formulas handle single keyword search with SEARCH, but combining multiple keywords with OR logic, case-insensitivity, and partial matching leads to complex nested formulas. Data processing approach is much cleaner.

## Solution
1. Define keyword list (case will be normalized to lowercase)
2. Iterate through each row
3. Get cell value and convert to lowercase
4. Check if any keyword appears as substring in the cell text
5. Populate target column based on match

## Example (Task 192-22 - PASSING, scored 1.0)
Search for 9 keywords in column D, populate column F:

```python
keywords = [
    'Core Activation', 'Core Design', 'Mobile Terminology',
    'Mobile Design', 'Mobile Integration', 'Testing Layer',
    'Testing Offshore', 'Carrier', 'Barrier'
]
keywords_lower = [kw.lower() for kw in keywords]

for row_num in range(2, 72):
    d_value = ws.cell(row_num, 4).value
    
    if d_value is None:
        ws.cell(row_num, 6).value = None
        continue
    
    d_str = str(d_value).lower()
    found_match = False
    
    for keyword_lower in keywords_lower:
        if keyword_lower in d_str:
            found_match = True
            break
    
    if found_match:
        ws.cell(row_num, 6).value = "Billing PO"
    else:
        ws.cell(row_num, 6).value = None
```

Results:
- Processed 70 rows (rows 2-71)
- Found 18 matches
- Successfully handled:
  - Case-insensitive matching ("Core activation" matches "Core Activation")
  - Partial matches ("Core DesignWireless" still matches "Core Design")
  - Prefixes/suffixes ("Carrier IVR Testing" matches "Carrier")
  - Multiple keywords efficiently
- Score: 1.0 ✓

## Key Advantages
- Easy to add/remove keywords
- Case-insensitive by default
- Substring (partial) matching built-in
- Handles prefixes/suffixes naturally
- Clear, readable logic
- Minimal performance impact

## When to Use
- Multi-keyword search across columns
- Conditional population based on text content
- Categorization of rows by keyword
- Tagging or flagging based on keywords
- When keywords might have variations or be embedded in longer text

## Comparison with Formulas
Formula approach would require complex nested SEARCH/ISNUMBER calls. Data processing is much cleaner and more maintainable.