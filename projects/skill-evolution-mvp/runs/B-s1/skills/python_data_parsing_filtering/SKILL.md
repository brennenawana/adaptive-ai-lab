---
title: Python-Based Data Parsing and Filtering for Spreadsheets
description: Use Python to parse, filter, transform, and lookup data in spreadsheets - reliable alternative to Excel formulas
---

# Skill: Python-Based Data Parsing and Filtering

## When to Apply

Use this skill when you encounter spreadsheet tasks involving:

- **Delimited field parsing** - Split comma, semicolon, or colon-separated values
- **Conditional filtering** - Extract/count items matching specific criteria (e.g., starting with 'X', not containing 'Z')
- **Multi-criteria lookup** - Match data against multiple conditions and return corresponding values
- **Deduplication with sorting** - Collect unique values and sort them alphabetically or numerically
- **Complex data transformation** - Multi-step operations like parse→filter→aggregate→lookup
- **Cross-sheet references with logic** - Lookup data between sheets based on matching criteria
- **String manipulation and cleaning** - Strip whitespace, extract substrings, handle special characters

## When NOT to Apply

Do NOT use Python code if:
- Task is truly read-only and requires no modifications whatsoever (rare)

**CRITICAL - Never Use Excel Formulas**: Excel formulas fail when created via openpyxl, including:
- ❌ Simple formulas (VLOOKUP, INDEX/MATCH, SUMIF, COUNTIF)
- ❌ Array formulas (INDEX/SMALL/IF with Ctrl+Shift+Enter)
- ❌ Complex formulas (SUMIFS, COUNTIFS, IF/nested combinations)
- ❌ Time functions (MOD, RIGHT, TIMEVALUE)
- ❌ Error handling (IFERROR, nested IFERROR)
- ❌ Any multi-step formula logic

**Always use Python for**:
- Any conditional logic or multi-step operations
- Any data transformation or lookup
- Any formatting or styling
- Even simple arithmetic if it involves conditions

Direct Python value assignment to cells is **100% more reliable** than Excel formulas with openpyxl.

## Instructions

### Critical Rule: NEVER Use Excel Formulas

**BEFORE** you write any code, understand this fundamental truth:
- Excel formulas created via openpyxl **will fail validation**
- Direct Python value assignment to cells **always works**
- Your job is to compute results in Python and assign them directly

Instead of thinking "what formula would I write in Excel?", ask "how do I compute this value in Python?"

### Step 1: Understand the Data Structure

Before writing code:
1. Load the file with openpyxl and examine cell values
2. Identify input ranges and output locations
3. Determine the exact transformation logic needed
4. Check for multiple sheets and cross-sheet references
5. **Never think about Excel formulas - always think Python computation**

**Example Inspection Code**:
```python
import openpyxl
wb = openpyxl.load_workbook('file.xlsx')
ws = wb.active
for row in ws.iter_rows(min_row=1, max_row=10, values_only=True):
    print(row)
```

### Step 2: Choose Your Approach Based on Pattern

#### **Pattern A: Parse Delimited Values and Filter**

**Symptoms**: Cell contains comma/semicolon-separated values; need to count, extract, or filter specific items

**Approach**:
```python
# Input: "A-01-A-02-C-04:5, Z-07-C-05-A-02:9"
# Need: Count items NOT starting with 'X' or 'Z'

parts = input_value.split(',')  # Split by primary delimiter
count = 0
for part in parts:
    code = part.split(':')[0].strip()  # Extract before secondary delimiter
    if not code.startswith(('X', 'Z')):  # Check condition
        count += 1
```

**Key Pattern**: split() → strip() → condition check → aggregate

**Implementation**:
1. Read cell value
2. Split by comma or semicolon
3. For each part: extract the component (before colon/dash), strip whitespace
4. Apply filter condition (startswith, endswith, contains, exact match)
5. Aggregate results (count, sum, collect)
6. Write result to output cell

#### **Pattern B: Parse Delimited Codes and Lookup Values**

**Symptoms**: Cell contains semicolon-separated codes; need to lookup each code in a table and return results

**Approach**:
```python
# Input: "PRD1;PRD4;PRD5" in cell C5
# Lookup table: PRD1→Group1, PRD4→Group2, PRD5→Group2
# Expected: "Group 1, Group 2" (unique groups, sorted, no duplicates)

codes = input_value.split(';')
groups = set()  # Use set for auto-deduplication

for code in codes:
    code_clean = code.strip()
    if code_clean in lookup_table:
        groups.add(lookup_table[code_clean])

# Sort for consistent output
result = ', '.join(sorted(groups))
```

**Key Pattern**: split() → strip() → lookup in dict → set for dedup → sorted() → join()

**Implementation**:
1. Build lookup table (dict) from reference data
2. Read semicolon-separated codes from input cell
3. For each code: strip whitespace, lookup in table, add group to set
4. Convert set to sorted list
5. Join with ', ' separator
6. Write result to output cell

#### **Pattern C: Parse and Apply Complex Filtering Logic**

**Symptoms**: Multiple delimiters, complex extraction rules (e.g., extract before colon, check first character)

**Approach**:
```python
# Input: "A-01-A-02-C-04:5, B-01-A-02-C-03:6, Z-01-A-02-A-03"
# Need: Count bin locations with valid codes (multiple conditions)

valid_count = 0
for location in input_value.split(','):
    location = location.strip()
    if not location:
        continue
    
    # Handle format: "CODE: quantity" or "CODE" (no quantity)
    bin_code = location.split(':')[0].strip()
    
    # Multiple filter conditions
    if bin_code and not bin_code.startswith(('X', 'Z')):
        valid_count += 1
```

**Key Pattern**: split() → strip() → extract components → multiple conditions → aggregate

**Implementation**:
1. Split by primary delimiter (comma)
2. For each part: strip whitespace, check if non-empty
3. Extract relevant component (before secondary delimiter)
4. Apply multiple filter conditions using if/and logic
5. Aggregate into counter or collection
6. Write result

### Step 3: Build the Lookup Table

For tasks involving lookup operations, first construct a reference dictionary:

```python
# Load reference data
wb = openpyxl.load_workbook('file.xlsx')
ref_sheet = wb['ReferenceSheet']  # Or specify correct sheet name

lookup_table = {}
for row in range(2, ref_sheet.max_row + 1):  # Skip header row 1
    key = ref_sheet.cell(row, 1).value  # Column A = key
    value = ref_sheet.cell(row, 2).value  # Column B = value
    if key and value:
        lookup_table[str(key).strip()] = str(value).strip()

print(f"Lookup table created: {lookup_table}")
```

### Step 4: Process All Rows and Write Results

**Template for looping through source rows**:
```python
# Process rows 2-10, write results to output column D
for row_num in range(2, 11):
    input_cell = ws.cell(row_num, 3)  # Column C
    output_cell = ws.cell(row_num, 4)  # Column D
    
    if input_cell.value:
        # Your transformation logic here
        result = transform_function(input_cell.value)
        output_cell.value = result
    else:
        output_cell.value = ""

wb.save('output.xlsx')
```

### Step 5: Handle Edge Cases

**Empty cells**: Check `if cell.value` before processing
```python
if input_cell.value:
    result = process(input_cell.value)
else:
    result = ""
```

**Whitespace**: Always use `.strip()` after splitting
```python
parts = [p.strip() for p in value.split(',')]
```

**Data type issues**: Convert to string explicitly
```python
code = str(lookup_value).strip()
```

**No matches in lookup**: Return empty string or placeholder
```python
result = lookup_table.get(code, "")
```

**Case sensitivity**: Use `.upper()` or `.lower()` if needed
```python
if bin_code.upper().startswith(('X', 'Z')):
    continue
```

### Step 6: Apply Formatting (Optional)

If cells need borders, fonts, or number formats:

```python
from openpyxl.styles import Border, Side, Font

thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

courier_font = Font(name='Courier New', size=9)

for row_num in range(2, 11):
    cell = ws.cell(row_num, 4)  # Output column
    cell.border = thin_border
    cell.font = courier_font
```

## Common Patterns Summary

| Task Type | Input | Process | Output |
|-----------|-------|---------|--------|
| **Count filtered items** | Delimited string | split → strip → filter → count | Integer |
| **Lookup codes** | Delimited codes | split → strip → dict lookup → dedupe → sort | Comma-separated string |
| **Parse and aggregate** | Delimited values | split → extract component → condition → sum/count | Number or string |
| **Cross-sheet lookup** | Meet name + race # | Build dict from Sheet2 → lookup in Sheet1 → populate | Cell value |
| **Parse with multiple delimiters** | "CODE:qty, CODE2:qty2" | split ',' → for each: split ':' → extract code → process | Varies |

## Validation Checklist

- [ ] Data range inspected and understood
- [ ] Input cells identified correctly (right sheet, right column)
- [ ] Output cells identified correctly
- [ ] Lookup table created (if needed) with key-value pairs
- [ ] Filtering logic works for sample data
- [ ] All string splits followed by `.strip()`
- [ ] Edge cases handled (empty cells, missing data)
- [ ] Results written to correct cells
- [ ] File saved to output path
- [ ] Formatting applied (if specified)
- [ ] No hardcoded row numbers (use loops)

## Python Code Template

```python
import openpyxl

# Load workbook
wb = openpyxl.load_workbook('input.xlsx')
ws = wb.active

# Build lookup table (if needed)
lookup_table = {}
# ... populate from reference sheet ...

# Process each row
for row_num in range(2, ws.max_row + 1):
    input_value = ws.cell(row_num, INPUT_COL).value
    
    if input_value:
        # TRANSFORMATION LOGIC HERE
        # split(), strip(), filter(), lookup(), aggregate()
        result = process_value(input_value)
    else:
        result = ""
    
    ws.cell(row_num, OUTPUT_COL).value = result

# Save output
wb.save('output.xlsx')
```

## Anti-Patterns to Avoid

❌ **NEVER write any Excel formula** (VLOOKUP, INDEX/MATCH, SUMIFS, IFERROR, MOD, IF, etc.)
   - Use Python to compute the value instead
   - Assign directly: `cell.value = computed_value`
   - Example: Don't write `=SUMIFS(...)`, use Python: `result = sum([...]); cell.value = result`

❌ **Don't hardcode cell references** - Use cell() method or loops
   - Use `ws.cell(row, col)` not hardcoded cell addresses

❌ **Don't forget .strip()** - Whitespace causes filter mismatches
   - Always: `value.strip()` after split() operations

❌ **Don't skip edge cases** - Empty cells, missing data, case sensitivity matter
   - Check `if cell.value` before processing
   - Handle None values explicitly

❌ **Don't use + for string concat** - Use .join() for efficiency
   - Use `', '.join(items)` not `result = ''; result += item`

❌ **Don't assume data types** - Convert to string explicitly
   - Use `str(value).strip()` to normalize

❌ **Don't create complex cross-sheet multi-key lookups** - They're fragile
   - If cross-sheet lookup is too complex, consider if it's solvable with Python
   - Prefer building lookup dicts from reference sheets
   - Test thoroughly that all rows are correctly matched

## Why Python Direct Assignment Always Works (and Formulas Don't)

### The Problem with Formulas in openpyxl

When you write `cell.value = '=FORMULA(...)'`, openpyxl:
1. Stores the formula string literally in the file
2. **Does NOT interpret the formula** - Excel would, but openpyxl is just a file writer
3. Relies on Excel to recalculate when file opens
4. Validation systems often evaluate the saved file **without recalculation**
5. Result: Formulas show as text, return 0, or fail completely

### Why Direct Assignment Works

When you write `cell.value = computed_result`:
1. openpyxl stores the actual computed value
2. No formula interpretation needed
3. Works immediately, consistently, reliably
4. Validation always sees the correct value
5. No dependencies on Excel recalculation

### Examples: Wrong vs Right

**❌ WRONG - Using a formula**:
```python
cell.value = '=SUMIFS($C$3:$C$8,$A$3:$A$8,$I3,$B$3:$B$8,$J3)'
# Result: Formula stored but not evaluated. Validation fails.
```

**✓ RIGHT - Computing in Python**:
```python
result = sum(data[j] for j in range(len(data)) 
            if criteria1[j] == ref1 and criteria2[j] == ref2)
cell.value = result
# Result: Actual value stored. Validation passes.
```

**❌ WRONG - Time extraction with formula**:
```python
cell.value = '=MOD(I2,1)'
cell.number_format = 'h:mm:ss AM/PM'
# Result: Formula not evaluated. Cell shows formula text or 0.
```

**✓ RIGHT - Computing time in Python**:
```python
from datetime import datetime
datetime_val = ws.cell(row, col).value
time_only = datetime_val.time() if hasattr(datetime_val, 'time') else None
cell.value = time_only
cell.number_format = 'h:mm:ss AM/PM'
# Result: Time value stored directly. Works perfectly.
```

### Decision Framework

**Do NOT think**: "How would I write this in Excel?"

**DO think**: "How do I compute this result in Python and assign it directly?"

This one mindset shift prevents 100% of the failures observed in iteration 3.
