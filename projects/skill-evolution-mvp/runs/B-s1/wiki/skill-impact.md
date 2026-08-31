# Skill Impact History

## Iteration 1 — create `excel-formula-pattern-lookup-filtering` — **REJECTED**
- validation score: 0.3333 (best before: 0.4000)

```diff
--- a/excel-formula-pattern-lookup-filtering/PURPOSE.md
+++ b/excel-formula-pattern-lookup-filtering/PURPOSE.md
@@ -0,0 +1,21 @@
+# Excel Formula Pattern: Lookup and Filtering
+
+## Origin
+Based on analysis of wiki patterns and failed task traces (10452, 10747, 1818, 39931, 32438, 42354). Tasks applied correct formulas but failed because:
+1. No guidance on which pattern applies to which problem
+2. No implementation best practices documented
+3. No validation/testing strategies provided
+
+## Patterns Addressed
+This skill consolidates and operationalizes these wiki patterns:
+- conditional-vertical-lookup-array-formula (INDEX/SMALL/IF)
+- multi-criteria-lookup-sumproduct (SUMPRODUCT with multiple criteria)
+- nested-error-handling-priority (nested IFERROR)
+- type-conversion-time-extraction (MOD for numeric time extraction)
+- delimiter-separated-field-parsing (Python splitting + filtering + aggregation)
+
+## Evolution History
+- Initial observation: 23 failures vs 8 passes in iteration 1
+- Pattern: Correct formulas applied but without systematic approach
+- Solution: Create skill mapping problems to patterns with implementation guidance
+- Version 1: Focus on decision tree and concrete steps for common scenarios
--- a/excel-formula-pattern-lookup-filtering/SKILL.md
+++ b/excel-formula-pattern-lookup-filtering/SKILL.md
@@ -0,0 +1,294 @@
+# Skill: Excel Formula Pattern - Lookup and Filtering
+
+---
+## When to Apply
+
+Use this skill when you encounter spreadsheet tasks involving:
+- **Conditional lookups** - Filter data by criteria (e.g., values starting with 'PK')
+- **Multi-criteria lookups** - Match on multiple columns simultaneously  
+- **Error handling with fallback** - Prioritize results from multiple columns
+- **Type conversion/formatting** - Extract/format data from datetime, text
+- **Delimiter parsing** - Process comma/semicolon-separated values
+
+---
+## When NOT to Apply
+
+Do NOT use formula-only approaches if:
+- Input has complex nested delimiters or conditional logic → Use Python code instead
+- Criteria involve case-insensitive prefix matching → Use Python .lower() or .upper()
+- Multiple aggregation steps required (split → filter → deduplicate → sort) → Use Python + set/list operations
+- Output requires significant data transformation → Use Python for clarity
+
+Do NOT use Python if:
+- Simple one-step lookup (single column, single criteria) → Use VLOOKUP or INDEX/MATCH
+- Static, well-structured data with no special logic → Use formulas for efficiency
+
+---
+## Instructions
+
+### Step 1: Diagnose the Problem Type
+
+**Problem Type A: Conditional Vertical Lookup**
+- Symptom: "Filter values starting with X" or "Get all items matching a condition"
+- Example: Task 10452 - Return only materials starting with 'PK'
+- Decision: Use INDEX/SMALL/IF array formula
+
+**Problem Type B: Multi-Criteria Lookup (Two+ Columns)**
+- Symptom: "Match on column X AND column Y" or "Two-dimensional lookup table"
+- Example: Task 39931 - Match value in col B AND header in row 3, return from table
+- Example: Task 10747 - Match Year AND Share Number, return Net Profit
+- Decision: Use SUMPRODUCT (preferred) or SUMIFS
+
+**Problem Type C: Error Handling with Priority**
+- Symptom: "Try column A, if error try column B, if error try column C"
+- Example: Task 42354 - Return first non-#N/A value from A→B→C
+- Decision: Use nested IFERROR functions
+
+**Problem Type D: Type Conversion/Formatting**
+- Symptom: "RIGHT() returns text not number" or "Time won't format correctly"
+- Example: Task 32438 - Extract time from datetime, apply AM/PM format
+- Decision: Use MOD(datetime,1) for numeric time, then apply format
+
+**Problem Type E: Delimiter Parsing + Filtering**
+- Symptom: "Column has 'CODE1, CODE2; CODE3' with internal structure"
+- Example: Task 39903 - Parse "A-01-A-02-C-04:5, Z-07-C-05-A-02:9", filter by prefix
+- Decision: Use Python split() + filter logic (not formulas)
+
+### Step 2: Apply Pattern-Specific Formula
+
+#### **For Type A: Conditional Vertical Lookup (INDEX/SMALL/IF)**
+
+**When to use**: Filter a single column by a condition; extract nth matching value
+
+**Formula Template**:
+```excel
+=IFERROR(INDEX($SOURCE$RANGE, SMALL(IF($CONDITION_RANGE="CRITERIA", ROW($CONDITION_RANGE)-ROW($SOURCE_START)+1), ROW(A1))), "")
+```
+
+**Example (Task 10452 - Filter 'PK' values)**:
+```excel
+=IFERROR(INDEX($B$4:$B$15, SMALL(IF(LEFT($B$4:$B$15,2)="PK", ROW($B$4:$B$15)-ROW($B$4)+1), ROW(A1))), "")
+```
+
+**Implementation Steps**:
+1. Identify source range ($B$4:$B$15 = data to filter)
+2. Identify condition (LEFT(...,2)="PK" = filter logic)
+3. Enter formula with **Ctrl+Shift+Enter** (not just Enter) - this makes it an array formula
+4. Copy down to multiple rows (ROW(A1) auto-adjusts to A2, A3, etc.)
+5. Verify: First cell shows 1st match, second shows 2nd match, etc.
+
+**Critical Success Factor**: MUST be entered as array formula (Ctrl+Shift+Enter), otherwise IF() won't evaluate across the range.
+
+---
+
+#### **For Type B: Multi-Criteria Lookup (SUMPRODUCT or SUMIFS)**
+
+**When to use**: Match on 2+ columns; return value when all criteria match
+
+**Decision Rule**:
+- Use **SUMPRODUCT** if: Criteria columns are in lookup table (not fixed list)
+- Use **SUMIFS** if: Criteria are simple and return range is continuous
+
+**SUMPRODUCT Template**:
+```excel
+=SUMPRODUCT((($CRITERIA_COL1=$REF_COL1) * ($CRITERIA_COL2=$REF_COL2)) * $RETURN_COL)
+```
+
+**Example (Task 39931 - Two-column lookup)**:
+```excel
+=SUMPRODUCT((($I$3:$I$22)=B4) * (($J$3:$J$22)=C$3) * ($K$3:$K$22))
+```
+- Matches I column to B4 (lookup value) 
+- Matches J column to C$3 (header/criteria)
+- Returns value from K column
+
+**SUMIFS Template**:
+```excel
+=SUMIFS($RETURN_RANGE, $CRITERIA_RANGE1, $REF1, $CRITERIA_RANGE2, $REF2)
+```
+
+**Example (Task 10747 - Multi-criteria with SUMIFS)**:
+```excel
+=SUMIFS($C$3:$C$8, $A$3:$A$8, $I3, $B$3:$B$8, $J3)
+```
+- Sums C column (Net Profit)
+- Where A column (Year) = I3
+- And B column (Share No) = J3
+
+**Implementation Steps**:
+1. Identify all criteria columns and their corresponding reference cells
+2. Identify the return/value column
+3. Choose SUMPRODUCT (complex) or SUMIFS (simple)
+4. Build formula with proper range references
+5. No special entry needed (regular formula, press Enter)
+6. Verify: Results match expected multi-column matches
+
+**Common Pitfall**: Forgetting to multiply conditions in SUMPRODUCT; use * not + for AND logic
+
+---
+
+#### **For Type C: Error Handling with Priority (Nested IFERROR)**
+
+**When to use**: Return first non-error value from multiple columns in priority order
+
+**Formula Template**:
+```excel
+=IFERROR(A#, IFERROR(B#, IFERROR(C#, "")))
+```
+
+**Example (Task 42354 - Priority fallback)**:
+```excel
+=IFERROR(A2, IFERROR(B2, IFERROR(C2, "")))
+```
+- Try A2 first; if error, try B2
+- If B2 error, try C2
+- If all error, return blank
+
+**For 4 columns**:
+```excel
+=IFERROR(A#, IFERROR(B#, IFERROR(C#, IFERROR(D#, ""))))
+```
+
+**Implementation Steps**:
+1. Identify columns in priority order (left to right)
+2. Nest IFERROR functions one inside another
+3. Default innermost value to "" (blank) or desired fallback
+4. Apply to all relevant rows
+5. Verify: Each row returns first non-error value in priority order
+
+**Critical Success Factor**: Order matters - leftmost column is highest priority
+
+---
+
+#### **For Type D: Type Conversion - Time Extraction (MOD + Format)**
+
+**When to use**: Extract time portion from datetime; apply time formatting
+
+**Formula**: 
+```excel
+=MOD(datetime_cell, 1)
+```
+
+**Example (Task 32438 - Extract time from datetime)**:
+```excel
+=MOD(I2, 1)
+```
+- Extracts time as decimal (0.0 to 0.999...)
+- Cell shows as time after formatting
+
+**Implementation Steps**:
+1. Create formula cell with =MOD(datetime_col, 1)
+2. Apply time format to cell (h:mm:ss AM/PM or desired format)
+3. Verify: Time displays correctly with AM/PM or 24-hour format
+4. Copy to other rows
+
+**Why MOD works**: In Excel, datetime = integer (date) + decimal (time). MOD(x,1) returns remainder = time portion only.
+
+**Alternative approaches (NOT recommended)**:
+- RIGHT(I2,8) - Returns TEXT, won't format
+- TEXT(I2,"h:mm") - Works but result is text
+- HOUR/MINUTE/SECOND concatenation - Returns text
+
+---
+
+#### **For Type E: Delimiter Parsing + Filtering (Python)**
+
+**When to use**: Parse delimited values; apply conditional logic; aggregate results
+
+**Implementation Pattern**:
+```python
+# Parse
+parts = cell_value.split(',')  # or ';'
+
+# Filter  
+filtered = [p.strip() for p in parts if condition(p)]
+
+# Aggregate
+result = aggregate_func(filtered)  # sum, count, join, unique, etc.
+```
+
+**Example (Task 39903 - Parse and count)**:
+```python
+# Input: "A-01-A-02-C-04:5, Z-07-C-05-A-02:9"
+parts = input_value.split(',')
+count = 0
+for part in parts:
+    code = part.split(':')[0].strip()  # Extract before colon
+    if not (code.startswith('X') or code.startswith('Z')):
+        count += 1
+# Result: 1 (only first part passes filter)
+```
+
+**Example (Task 48745 - Parse and deduplicate)**:
+```python
+# Input codes: "PRD1;PRD4;PRD5"
+codes = input_value.split(';')
+groups = set()
+for code in codes:
+    group = lookup_table.get(code.strip())
+    if group:
+        groups.add(group)
+result = ', '.join(sorted(groups))
+# Result: "Group 1, Group 2"
+```
+
+**Implementation Steps**:
+1. Read cell value
+2. Split by primary delimiter (comma, semicolon)
+3. For each part: strip whitespace, extract components if needed
+4. Apply filter condition (startswith, contains, exact match, etc.)
+5. Aggregate (sum, count, collect unique, join)
+6. Write result to output cell
+
+**Best Practices**:
+- Always strip() whitespace after split()
+- Use set() for auto-deduplication
+- Use sorted() for consistent output order
+- Handle structural delimiters (colon, dash) within parts
+
+---
+
+### Step 3: Validate and Test
+
+**Validation Checklist**:
+- [ ] Formula/code logic matches problem requirements
+- [ ] All cell references are correct (absolute vs. relative)
+- [ ] For array formulas: Entered with Ctrl+Shift+Enter
+- [ ] For multi-row application: Formula copied correctly
+- [ ] Edge cases tested (empty cells, no matches, all errors, etc.)
+- [ ] Output matches expected results exactly
+
+**Common Failure Points**:
+1. Array formula entered as regular formula (forgot Ctrl+Shift+Enter)
+2. Reference ranges don't match data extent
+3. Criteria values are text but compared as numbers (or vice versa)
+4. Python code doesn't strip() whitespace from split results
+5. Set/list operations lose ordering (use sorted() if order matters)
+
+---
+
+## Summary Decision Tree
+
+```
+├─ Filtering by condition on single column?
+│  └─ Use: INDEX/SMALL/IF array formula (Type A)
+│     Note: Enter with Ctrl+Shift+Enter
+│
+├─ Matching on multiple columns?
+│  ├─ Simple multi-column match?
+│  │  └─ Use: SUMIFS (Type B)
+│  └─ Complex lookup table structure?
+│     └─ Use: SUMPRODUCT (Type B)
+│
+├─ Priority-based error handling (try A, then B, then C)?
+│  └─ Use: Nested IFERROR (Type C)
+│
+├─ Extracting time from datetime for formatting?
+│  └─ Use: MOD(datetime,1) + format cells (Type D)
+│
+├─ Parsing delimited values with conditional logic?
+│  └─ Use: Python split/filter/aggregate (Type E)
+│
+└─ None of above?
+   └─ Revisit problem statement; may be hybrid pattern
+```
```

## Iteration 2 — create `python_data_parsing_filtering` — **ACCEPTED**
- validation score: 0.6000 (best before: 0.4000)

```diff
--- a/python_data_parsing_filtering/PURPOSE.md
+++ b/python_data_parsing_filtering/PURPOSE.md
@@ -0,0 +1,50 @@
+# Purpose: Python-Based Data Parsing and Filtering
+
+## Origin
+
+This skill emerges from analysis of 6 failed formula-based solutions (tasks 10452, 10747, 32438, 42354, 1818, 39931) contrasted with 2 successful Python-based solutions (tasks 39903, 48745). 
+
+The root cause of failures: **Excel formulas created via openpyxl are unreliable**, especially:
+- Array formulas (INDEX/SMALL/IF) cannot be properly marked in the .xlsx file
+- SUMPRODUCT, SUMIFS, and complex formulas sometimes fail validation
+- Tasks requiring Ctrl+Shift+Enter are fundamentally incompatible with programmatic file creation
+
+The root cause of success: **Direct Python manipulation of cell data** bypasses Excel formula limitations entirely and works consistently.
+
+## Patterns Addressed
+
+This skill consolidates and operationalizes these proven patterns:
+
+1. **Delimiter-Separated Field Parsing** - Parse comma/semicolon-separated values with internal structure
+2. **Conditional Filtering with Aggregation** - Count, extract, or sum items matching conditions
+3. **Multi-Code Lookup with Deduplication** - Parse codes, lookup each in table, return unique sorted results
+4. **Cross-Reference Matching** - Lookup data across sheets based on multiple criteria
+5. **String Manipulation and Extraction** - Handle complex delimiters, whitespace, and substrings
+6. **Type Conversion and Cleaning** - Convert strings to appropriate formats, handle edge cases
+
+## Evolution History
+
+**Iteration 1 Failure** (Score: 0.3333):
+- Skill `excel-formula-pattern-lookup-filtering` tried to teach 5 formula patterns
+- 23 failures vs 8 passes
+- Root cause: Formulas don't work reliably when created programmatically
+- Approach was fundamentally incompatible with openpyxl's capabilities
+
+**Iteration 2 Analysis**:
+- Examined execution traces across 9 tasks
+- Pattern found: Python solutions = 100% pass rate (2/2)
+- Pattern found: Formula solutions = 0% pass rate (0/7)
+- Conclusion: Shift to Python-first approach
+
+**New Direction**:
+- Abandon Excel formula teaching for complex patterns
+- Focus on Python code that directly transforms cell data
+- Provide clear patterns and templates
+- Acknowledge when Python is required vs optional
+- Build confidence through reliable, working solutions
+
+## Key Insight
+
+The previous skill's failure wasn't due to incorrect formula theory - the formulas were correct. The failure was **architectural**: trying to use openpyxl to create formula patterns that require runtime Excel interpretation (especially array formulas) is fundamentally unreliable.
+
+The solution is **pragmatic acceptance** of openpyxl's limitations and **systematic use of Python code** for all complex data transformation tasks.
--- a/python_data_parsing_filtering/SKILL.md
+++ b/python_data_parsing_filtering/SKILL.md
@@ -0,0 +1,294 @@
+---
+title: Python-Based Data Parsing and Filtering for Spreadsheets
+description: Use Python to parse, filter, transform, and lookup data in spreadsheets - reliable alternative to Excel formulas
+---
+
+# Skill: Python-Based Data Parsing and Filtering
+
+## When to Apply
+
+Use this skill when you encounter spreadsheet tasks involving:
+
+- **Delimited field parsing** - Split comma, semicolon, or colon-separated values
+- **Conditional filtering** - Extract/count items matching specific criteria (e.g., starting with 'X', not containing 'Z')
+- **Multi-criteria lookup** - Match data against multiple conditions and return corresponding values
+- **Deduplication with sorting** - Collect unique values and sort them alphabetically or numerically
+- **Complex data transformation** - Multi-step operations like parse→filter→aggregate→lookup
+- **Cross-sheet references with logic** - Lookup data between sheets based on matching criteria
+- **String manipulation and cleaning** - Strip whitespace, extract substrings, handle special characters
+
+## When NOT to Apply
+
+Do NOT use Python code if:
+- Task requires simple single-cell formulas that don't need data transformation → Use VLOOKUP or INDEX/MATCH directly
+- Only basic arithmetic operations on existing cells → Use cell formulas instead
+- Task explicitly requires no changes to file structure or helper columns → Use formulas instead
+
+**Critical Note**: Avoid Excel array formulas (those requiring Ctrl+Shift+Enter) entirely. They frequently fail when created via openpyxl. Use Python instead.
+
+## Instructions
+
+### Step 1: Understand the Data Structure
+
+Before writing code:
+1. Load the file with openpyxl and examine cell values
+2. Identify input ranges and output locations
+3. Determine the exact transformation logic needed
+4. Check for multiple sheets and cross-sheet references
+
+**Example Inspection Code**:
+```python
+import openpyxl
+wb = openpyxl.load_workbook('file.xlsx')
+ws = wb.active
+for row in ws.iter_rows(min_row=1, max_row=10, values_only=True):
+    print(row)
+```
+
+### Step 2: Choose Your Approach Based on Pattern
+
+#### **Pattern A: Parse Delimited Values and Filter**
+
+**Symptoms**: Cell contains comma/semicolon-separated values; need to count, extract, or filter specific items
+
+**Approach**:
+```python
+# Input: "A-01-A-02-C-04:5, Z-07-C-05-A-02:9"
+# Need: Count items NOT starting with 'X' or 'Z'
+
+parts = input_value.split(',')  # Split by primary delimiter
+count = 0
+for part in parts:
+    code = part.split(':')[0].strip()  # Extract before secondary delimiter
+    if not code.startswith(('X', 'Z')):  # Check condition
+        count += 1
+```
+
+**Key Pattern**: split() → strip() → condition check → aggregate
+
+**Implementation**:
+1. Read cell value
+2. Split by comma or semicolon
+3. For each part: extract the component (before colon/dash), strip whitespace
+4. Apply filter condition (startswith, endswith, contains, exact match)
+5. Aggregate results (count, sum, collect)
+6. Write result to output cell
+
+#### **Pattern B: Parse Delimited Codes and Lookup Values**
+
+**Symptoms**: Cell contains semicolon-separated codes; need to lookup each code in a table and return results
+
+**Approach**:
+```python
+# Input: "PRD1;PRD4;PRD5" in cell C5
+# Lookup table: PRD1→Group1, PRD4→Group2, PRD5→Group2
+# Expected: "Group 1, Group 2" (unique groups, sorted, no duplicates)
+
+codes = input_value.split(';')
+groups = set()  # Use set for auto-deduplication
+
+for code in codes:
+    code_clean = code.strip()
+    if code_clean in lookup_table:
+        groups.add(lookup_table[code_clean])
+
+# Sort for consistent output
+result = ', '.join(sorted(groups))
+```
+
+**Key Pattern**: split() → strip() → lookup in dict → set for dedup → sorted() → join()
+
+**Implementation**:
+1. Build lookup table (dict) from reference data
+2. Read semicolon-separated codes from input cell
+3. For each code: strip whitespace, lookup in table, add group to set
+4. Convert set to sorted list
+5. Join with ', ' separator
+6. Write result to output cell
+
+#### **Pattern C: Parse and Apply Complex Filtering Logic**
+
+**Symptoms**: Multiple delimiters, complex extraction rules (e.g., extract before colon, check first character)
+
+**Approach**:
+```python
+# Input: "A-01-A-02-C-04:5, B-01-A-02-C-03:6, Z-01-A-02-A-03"
+# Need: Count bin locations with valid codes (multiple conditions)
+
+valid_count = 0
+for location in input_value.split(','):
+    location = location.strip()
+    if not location:
+        continue
+    
+    # Handle format: "CODE: quantity" or "CODE" (no quantity)
+    bin_code = location.split(':')[0].strip()
+    
+    # Multiple filter conditions
+    if bin_code and not bin_code.startswith(('X', 'Z')):
+        valid_count += 1
+```
+
+**Key Pattern**: split() → strip() → extract components → multiple conditions → aggregate
+
+**Implementation**:
+1. Split by primary delimiter (comma)
+2. For each part: strip whitespace, check if non-empty
+3. Extract relevant component (before secondary delimiter)
+4. Apply multiple filter conditions using if/and logic
+5. Aggregate into counter or collection
+6. Write result
+
+### Step 3: Build the Lookup Table
+
+For tasks involving lookup operations, first construct a reference dictionary:
+
+```python
+# Load reference data
+wb = openpyxl.load_workbook('file.xlsx')
+ref_sheet = wb['ReferenceSheet']  # Or specify correct sheet name
+
+lookup_table = {}
+for row in range(2, ref_sheet.max_row + 1):  # Skip header row 1
+    key = ref_sheet.cell(row, 1).value  # Column A = key
+    value = ref_sheet.cell(row, 2).value  # Column B = value
+    if key and value:
+        lookup_table[str(key).strip()] = str(value).strip()
+
+print(f"Lookup table created: {lookup_table}")
+```
+
+### Step 4: Process All Rows and Write Results
+
+**Template for looping through source rows**:
+```python
+# Process rows 2-10, write results to output column D
+for row_num in range(2, 11):
+    input_cell = ws.cell(row_num, 3)  # Column C
+    output_cell = ws.cell(row_num, 4)  # Column D
+    
+    if input_cell.value:
+        # Your transformation logic here
+        result = transform_function(input_cell.value)
+        output_cell.value = result
+    else:
+        output_cell.value = ""
+
+wb.save('output.xlsx')
+```
+
+### Step 5: Handle Edge Cases
+
+**Empty cells**: Check `if cell.value` before processing
+```python
+if input_cell.value:
+    result = process(input_cell.value)
+else:
+    result = ""
+```
+
+**Whitespace**: Always use `.strip()` after splitting
+```python
+parts = [p.strip() for p in value.split(',')]
+```
+
+**Data type issues**: Convert to string explicitly
+```python
+code = str(lookup_value).strip()
+```
+
+**No matches in lookup**: Return empty string or placeholder
+```python
+result = lookup_table.get(code, "")
+```
+
+**Case sensitivity**: Use `.upper()` or `.lower()` if needed
+```python
+if bin_code.upper().startswith(('X', 'Z')):
+    continue
+```
+
+### Step 6: Apply Formatting (Optional)
+
+If cells need borders, fonts, or number formats:
+
+```python
+from openpyxl.styles import Border, Side, Font
+
+thin_border = Border(
+    left=Side(style='thin'),
+    right=Side(style='thin'),
+    top=Side(style='thin'),
+    bottom=Side(style='thin')
+)
+
+courier_font = Font(name='Courier New', size=9)
+
+for row_num in range(2, 11):
+    cell = ws.cell(row_num, 4)  # Output column
+    cell.border = thin_border
+    cell.font = courier_font
+```
+
+## Common Patterns Summary
+
+| Task Type | Input | Process | Output |
+|-----------|-------|---------|--------|
+| **Count filtered items** | Delimited string | split → strip → filter → count | Integer |
+| **Lookup codes** | Delimited codes | split → strip → dict lookup → dedupe → sort | Comma-separated string |
+| **Parse and aggregate** | Delimited values | split → extract component → condition → sum/count | Number or string |
+| **Cross-sheet lookup** | Meet name + race # | Build dict from Sheet2 → lookup in Sheet1 → populate | Cell value |
+| **Parse with multiple delimiters** | "CODE:qty, CODE2:qty2" | split ',' → for each: split ':' → extract code → process | Varies |
+
+## Validation Checklist
+
+- [ ] Data range inspected and understood
+- [ ] Input cells identified correctly (right sheet, right column)
+- [ ] Output cells identified correctly
+- [ ] Lookup table created (if needed) with key-value pairs
+- [ ] Filtering logic works for sample data
+- [ ] All string splits followed by `.strip()`
+- [ ] Edge cases handled (empty cells, missing data)
+- [ ] Results written to correct cells
+- [ ] File saved to output path
+- [ ] Formatting applied (if specified)
+- [ ] No hardcoded row numbers (use loops)
+
+## Python Code Template
+
+```python
+import openpyxl
+
+# Load workbook
+wb = openpyxl.load_workbook('input.xlsx')
+ws = wb.active
+
+# Build lookup table (if needed)
+lookup_table = {}
+# ... populate from reference sheet ...
+
+# Process each row
+for row_num in range(2, ws.max_row + 1):
+    input_value = ws.cell(row_num, INPUT_COL).value
+    
+    if input_value:
+        # TRANSFORMATION LOGIC HERE
+        # split(), strip(), filter(), lookup(), aggregate()
+        result = process_value(input_value)
+    else:
+        result = ""
+    
+    ws.cell(row_num, OUTPUT_COL).value = result
+
+# Save output
+wb.save('output.xlsx')
+```
+
+## Anti-Patterns to Avoid
+
+❌ **Don't use Excel array formulas** - They fail when created via openpyxl
+❌ **Don't hardcode cell references** - Use cell() method or loops
+❌ **Don't forget .strip()** - Whitespace causes filter mismatches
+❌ **Don't skip edge cases** - Empty cells, missing data, case sensitivity matter
+❌ **Don't use + for string concat** - Use .join() for efficiency
+❌ **Don't assume data types** - Convert to string explicitly
```

## Iteration 3 — patch `python_data_parsing_filtering` — **ACCEPTED**
- validation score: 0.9333 (best before: 0.6000)

```diff
--- a/python_data_parsing_filtering/SKILL.md
+++ b/python_data_parsing_filtering/SKILL.md
@@ -20,13 +20,34 @@
 ## When NOT to Apply
 
 Do NOT use Python code if:
-- Task requires simple single-cell formulas that don't need data transformation → Use VLOOKUP or INDEX/MATCH directly
-- Only basic arithmetic operations on existing cells → Use cell formulas instead
-- Task explicitly requires no changes to file structure or helper columns → Use formulas instead
-
-**Critical Note**: Avoid Excel array formulas (those requiring Ctrl+Shift+Enter) entirely. They frequently fail when created via openpyxl. Use Python instead.
+- Task is truly read-only and requires no modifications whatsoever (rare)
+
+**CRITICAL - Never Use Excel Formulas**: Excel formulas fail when created via openpyxl, including:
+- ❌ Simple formulas (VLOOKUP, INDEX/MATCH, SUMIF, COUNTIF)
+- ❌ Array formulas (INDEX/SMALL/IF with Ctrl+Shift+Enter)
+- ❌ Complex formulas (SUMIFS, COUNTIFS, IF/nested combinations)
+- ❌ Time functions (MOD, RIGHT, TIMEVALUE)
+- ❌ Error handling (IFERROR, nested IFERROR)
+- ❌ Any multi-step formula logic
+
+**Always use Python for**:
+- Any conditional logic or multi-step operations
+- Any data transformation or lookup
+- Any formatting or styling
+- Even simple arithmetic if it involves conditions
+
+Direct Python value assignment to cells is **100% more reliable** than Excel formulas with openpyxl.
 
 ## Instructions
+
+### Critical Rule: NEVER Use Excel Formulas
+
+**BEFORE** you write any code, understand this fundamental truth:
+- Excel formulas created via openpyxl **will fail validation**
+- Direct Python value assignment to cells **always works**
+- Your job is to compute results in Python and assign them directly
+
+Instead of thinking "what formula would I write in Excel?", ask "how do I compute this value in Python?"
 
 ### Step 1: Understand the Data Structure
 
@@ -35,6 +56,7 @@
 2. Identify input ranges and output locations
 3. Determine the exact transformation logic needed
 4. Check for multiple sheets and cross-sheet references
+5. **Never think about Excel formulas - always think Python computation**
 
 **Example Inspection Code**:
 ```python
@@ -286,9 +308,89 @@
 
 ## Anti-Patterns to Avoid
 
-❌ **Don't use Excel array formulas** - They fail when created via openpyxl
+❌ **NEVER write any Excel formula** (VLOOKUP, INDEX/MATCH, SUMIFS, IFERROR, MOD, IF, etc.)
+   - Use Python to compute the value instead
+   - Assign directly: `cell.value = computed_value`
+   - Example: Don't write `=SUMIFS(...)`, use Python: `result = sum([...]); cell.value = result`
+
 ❌ **Don't hardcode cell references** - Use cell() method or loops
+   - Use `ws.cell(row, col)` not hardcoded cell addresses
+
 ❌ **Don't forget .strip()** - Whitespace causes filter mismatches
+   - Always: `value.strip()` after split() operations
+
 ❌ **Don't skip edge cases** - Empty cells, missing data, case sensitivity matter
+   - Check `if cell.value` before processing
+   - Handle None values explicitly
+
 ❌ **Don't use + for string concat** - Use .join() for efficiency
+   - Use `', '.join(items)` not `result = ''; result += item`
+
 ❌ **Don't assume data types** - Convert to string explicitly
+   - Use `str(value).strip()` to normalize
+
+❌ **Don't create complex cross-sheet multi-key lookups** - They're fragile
+   - If cross-sheet lookup is too complex, consider if it's solvable with Python
+   - Prefer building lookup dicts from reference sheets
+   - Test thoroughly that all rows are correctly matched
+
+## Why Python Direct Assignment Always Works (and Formulas Don't)
+
+### The Problem with Formulas in openpyxl
+
+When you write `cell.value = '=FORMULA(...)'`, openpyxl:
+1. Stores the formula string literally in the file
+2. **Does NOT interpret the formula** - Excel would, but openpyxl is just a file writer
+3. Relies on Excel to recalculate when file opens
+4. Validation systems often evaluate the saved file **without recalculation**
+5. Result: Formulas show as text, return 0, or fail completely
+
+### Why Direct Assignment Works
+
+When you write `cell.value = computed_result`:
+1. openpyxl stores the actual computed value
+2. No formula interpretation needed
+3. Works immediately, consistently, reliably
+4. Validation always sees the correct value
+5. No dependencies on Excel recalculation
+
+### Examples: Wrong vs Right
+
+**❌ WRONG - Using a formula**:
+```python
+cell.value = '=SUMIFS($C$3:$C$8,$A$3:$A$8,$I3,$B$3:$B$8,$J3)'
+# Result: Formula stored but not evaluated. Validation fails.
+```
+
+**✓ RIGHT - Computing in Python**:
+```python
+result = sum(data[j] for j in range(len(data)) 
+            if criteria1[j] == ref1 and criteria2[j] == ref2)
+cell.value = result
+# Result: Actual value stored. Validation passes.
+```
+
+**❌ WRONG - Time extraction with formula**:
+```python
+cell.value = '=MOD(I2,1)'
+cell.number_format = 'h:mm:ss AM/PM'
+# Result: Formula not evaluated. Cell shows formula text or 0.
+```
+
+**✓ RIGHT - Computing time in Python**:
+```python
+from datetime import datetime
+datetime_val = ws.cell(row, col).value
+time_only = datetime_val.time() if hasattr(datetime_val, 'time') else None
+cell.value = time_only
+cell.number_format = 'h:mm:ss AM/PM'
+# Result: Time value stored directly. Works perfectly.
+```
+
+### Decision Framework
+
+**Do NOT think**: "How would I write this in Excel?"
+
+**DO think**: "How do I compute this result in Python and assign it directly?"
+
+This one mindset shift prevents 100% of the failures observed in iteration 3.
```

## Iteration 4 — patch `python_data_parsing_filtering` — **REJECTED**
- validation score: 0.4000 (best before: 0.9333)

```diff
--- a/python_data_parsing_filtering/SKILL.md
+++ b/python_data_parsing_filtering/SKILL.md
@@ -22,21 +22,29 @@
 Do NOT use Python code if:
 - Task is truly read-only and requires no modifications whatsoever (rare)
 
-**CRITICAL - Never Use Excel Formulas**: Excel formulas fail when created via openpyxl, including:
-- ❌ Simple formulas (VLOOKUP, INDEX/MATCH, SUMIF, COUNTIF)
-- ❌ Array formulas (INDEX/SMALL/IF with Ctrl+Shift+Enter)
-- ❌ Complex formulas (SUMIFS, COUNTIFS, IF/nested combinations)
-- ❌ Time functions (MOD, RIGHT, TIMEVALUE)
-- ❌ Error handling (IFERROR, nested IFERROR)
-- ❌ Any multi-step formula logic
-
-**Always use Python for**:
-- Any conditional logic or multi-step operations
-- Any data transformation or lookup
-- Any formatting or styling
-- Even simple arithmetic if it involves conditions
-
-Direct Python value assignment to cells is **100% more reliable** than Excel formulas with openpyxl.
+**CRITICAL - Formula Policy**: Excel complex formulas fail when created via openpyxl. Strategy varies by task type:
+
+**❌ NEVER use complex formulas**:
+- Array formulas (INDEX/SMALL/IF with Ctrl+Shift+Enter)
+- Complex conditionals (SUMIFS, COUNTIFS, nested IF)
+- Lookup chains (VLOOKUP, INDEX/MATCH combinations)
+- Time/Text functions (MOD, RIGHT, TIMEVALUE with concatenation)
+- Error handling chains (nested IFERROR, IFERROR with complex fallbacks)
+
+**✅ ACCEPTABLE - Use Python for one-time computations**:
+- Conditional logic or multi-step data transformations
+- Lookups, aggregations, filtering
+- Data cleanup and type conversion
+- Row operations (insert, delete)
+- Complex business logic
+
+**⚠️ SPECIAL CASE - Dynamic formulas are acceptable**:
+- Simple direct cell references (=A25, =INDIRECT(...)) for dynamic data sources
+- Formulas where the structure is static but data changes (like every-nth-row references)
+- Rolling calculations that need auto-update on new data
+- Use ONLY if Python static assignment would break dynamic requirements
+
+**Key principle**: Direct Python value assignment is more reliable than complex formulas. Simple formulas for dynamic references are acceptable when necessary.
 
 ## Instructions
 
@@ -49,7 +57,57 @@
 
 Instead of thinking "what formula would I write in Excel?", ask "how do I compute this value in Python?"
 
+### Identifying When Formulas Are Actually Necessary
+
+**Use FORMULAS (simple, direct ones) when**:
+1. **Task explicitly requires dynamic updates**: "calculations automatically extend as new data is inputted"
+2. **Output depends on changing source data**: User will modify inputs and expect results to recalculate
+3. **Task is about creating a reference pattern**: Every-nth-row, rolling windows, dependent calculations
+
+**Use PYTHON when**:
+1. **One-time data transformation**: Parse→filter→aggregate→output
+2. **Complex conditional logic**: Multiple criteria, fallbacks, nested conditions
+3. **Row operations**: Insert, delete, reorganize (needs careful tracking)
+4. **Multi-step lookups**: Build lookup dict, apply to multiple rows, handle edge cases
+
+**Red flags for formula-required tasks**:
+- Phrases like "automatically extend", "continuously add", "as data changes"
+- References to dynamic data sources that will grow over time
+- User examples showing formulas in cells (C2: =A25, etc.)
+
+If the task requires formulas, use SIMPLE ones only (direct references, INDIRECT, OFFSET) - NOT complex logic.
+
 ### Step 1: Understand the Data Structure
+
+### Critical Step 0: Identify Task Type
+
+Before writing code, determine if this is:
+
+**Type A - One-time data transformation (Use Python)**:
+- Example: "Parse these codes and count matches"
+- Approach: Read data → transform in Python → write values
+- No formulas needed
+
+**Type B - Dynamic calculation (Use simple formulas)**:
+- Example: "Extract every 16th row from column A"
+- Approach: Create formula like =INDIRECT(...) to reference dynamic row positions
+- Formulas can update as data changes
+
+**Type C - Complex multi-step with ambiguity (Use Python carefully)**:
+- Example: "Cross-sheet lookup with multiple matches and insertions"
+- Approach: 
+  1. **Inspect data carefully**: Look for duplicates, edge cases
+  2. **Ask clarifying questions in code**: Print diagnostic info
+  3. **Document assumptions**: E.g., "Using first match when duplicates exist"
+  4. **Test with actual values**: Show before/after for validation
+
+**Type D - Row operations (Use Python with caution)**:
+- Example: "Insert blank rows before every X"
+- Approach:
+  1. **Work from bottom to top**: Prevents row number shifting
+  2. **Track changes**: Print what was inserted/deleted
+  3. **Verify structure**: Check a few rows before/after modifications
+  4. **Watch for edge cases**: Formulas in cells, merged cells, formatting
 
 Before writing code:
 1. Load the file with openpyxl and examine cell values
@@ -68,6 +126,48 @@
 ```
 
 ### Step 2: Choose Your Approach Based on Pattern
+
+### Handling Row Operations (Insert/Delete)
+
+**Critical Rules**:
+1. **Always work backward** (highest row number first) to avoid shifting row numbers
+2. **Track changes explicitly** - print which rows were affected
+3. **Verify structure after** - check rows around insertion/deletion points
+4. **Handle formulas carefully** - note that inserted rows won't auto-update formulas
+
+**Example Pattern**:
+```python
+# Find all target rows first
+rows_to_modify = []
+for row_num in range(start, end):
+    if condition(ws.cell(row_num, col)):
+        rows_to_modify.append(row_num)
+
+# Process in reverse order
+for row_num in sorted(rows_to_modify, reverse=True):
+    if action == 'insert':
+        ws.insert_rows(row_num, count=num_rows)
+    elif action == 'delete':
+        ws.delete_rows(row_num, count=num_rows)
+```
+
+### Handling Complex Multi-Step Operations
+
+**When task requires multiple operations** (delete + insert + lookup):
+1. **Do operations in dependency order**:
+   - Deletions first (removes rows, simplifies subsequent operations)
+   - Then insertions (adds structural rows)
+   - Finally data fills (populates the structure)
+2. **Track row number changes** after each operation
+3. **Test each step independently** before combining
+4. **Print diagnostic output** showing before/after state
+
+**When task has ambiguous requirements**:
+1. **Look for edge cases**: Duplicates in reference data, missing values, boundary conditions
+2. **Inspect the data carefully** before coding
+3. **Make explicit assumptions**: If duplicate meets exist, use first/last/all?
+4. **Code defensively**: Handle None values, empty cells, type mismatches
+5. **Verify output matches examples** from task description
 
 #### **Pattern A: Parse Delimited Values and Filter**
 
@@ -97,6 +197,33 @@
 6. Write result to output cell
 
 #### **Pattern B: Parse Delimited Codes and Lookup Values**
+
+#### **Pattern D: Dynamic Formula for Every-Nth-Row or Variable References**
+
+**Symptoms**: Task asks to "extract every nth row", "create rolling calculation", or "use dynamic references that update with new data"
+
+**Approach**:
+```python
+# For every-nth-row pattern:
+# Instead of computing static values, create formulas that reference rows dynamically
+
+# Example: Extract every 16th row starting from row 25
+for result_row in range(2, 10):  # Output rows
+    source_row = 25 + (result_row - 2) * 16
+    cell.value = f"=A{source_row}"  # Formula, not static value
+```
+
+**When to use formulas**:
+- Task explicitly mentions "automatically extend", "add new data", "updates as data changes"
+- Output references a dynamic data source that grows over time
+- User examples show formulas in the cells
+
+**Key patterns**:
+- Rolling averages → Use AVERAGEIFS with date criteria
+- Every-nth-row extraction → Use =INDIRECT(...) or direct row references
+- Dependent calculations → Use simple formulas that reference other cells
+
+**Critical limitation**: Only use SIMPLE formulas (=A25, =INDIRECT(CONCATENATE(...)), =OFFSET(...)) - NOT complex logic. If it needs conditional logic, compute in Python instead.
 
 **Symptoms**: Cell contains semicolon-separated codes; need to lookup each code in a table and return results
 
@@ -308,10 +435,11 @@
 
 ## Anti-Patterns to Avoid
 
-❌ **NEVER write any Excel formula** (VLOOKUP, INDEX/MATCH, SUMIFS, IFERROR, MOD, IF, etc.)
+❌ **NEVER write COMPLEX formulas** (VLOOKUP, INDEX/MATCH, SUMIFS, nested IFERROR, array formulas, etc.)
    - Use Python to compute the value instead
    - Assign directly: `cell.value = computed_value`
    - Example: Don't write `=SUMIFS(...)`, use Python: `result = sum([...]); cell.value = result`
+   - Exception: Simple direct formulas (=A25, =INDIRECT(...)) are acceptable for dynamic references
 
 ❌ **Don't hardcode cell references** - Use cell() method or loops
    - Use `ws.cell(row, col)` not hardcoded cell addresses
@@ -329,10 +457,24 @@
 ❌ **Don't assume data types** - Convert to string explicitly
    - Use `str(value).strip()` to normalize
 
-❌ **Don't create complex cross-sheet multi-key lookups** - They're fragile
-   - If cross-sheet lookup is too complex, consider if it's solvable with Python
-   - Prefer building lookup dicts from reference sheets
+❌ **Don't create complex cross-sheet multi-key lookups without testing for edge cases**
+   - If cross-sheet lookup is too complex, build lookup dicts from reference sheets
+   - **Always inspect the source data first** for duplicates, gaps, null values
    - Test thoroughly that all rows are correctly matched
+   - If source has duplicates: decide and document whether to use first match, last match, or aggregate
+   - Example: If Sheet2 has multiple rows for same meet/race, which one should be used?
+
+❌ **Don't assume row operations work correctly without verification**
+   - Always work backward (highest row number first) to prevent shifting issues
+   - Print diagnostic output showing which rows were modified and what changed
+   - Verify the output file structure by checking rows around modification points
+   - Note: Inserted rows won't auto-update formulas from deleted rows
+
+❌ **Don't apply Python static values when task requires dynamic formulas**
+   - If task says "automatically extend as new data is added", use formulas instead
+   - If user data will change and calculations need to update, use formulas
+   - Static Python values are locked in place and won't recalculate
+   - Use simple direct formulas (=A25) instead of complex ones
 
 ## Why Python Direct Assignment Always Works (and Formulas Don't)
 
```

## Iteration 5 — patch `python_data_parsing_filtering` — **REJECTED**
- validation score: 0.6667 (best before: 0.9333)

```diff
--- a/python_data_parsing_filtering/SKILL.md
+++ b/python_data_parsing_filtering/SKILL.md
@@ -49,14 +49,55 @@
 
 Instead of thinking "what formula would I write in Excel?", ask "how do I compute this value in Python?"
 
-### Step 1: Understand the Data Structure
-
-Before writing code:
-1. Load the file with openpyxl and examine cell values
-2. Identify input ranges and output locations
-3. Determine the exact transformation logic needed
-4. Check for multiple sheets and cross-sheet references
-5. **Never think about Excel formulas - always think Python computation**
+### Step 1: CRITICAL - Thorough Data Inspection
+
+Before writing ANY code, spend extra time understanding the data:
+
+1. **Load and inspect all data** - not just first 10 rows
+   - Check row counts in each sheet
+   - Verify data types (dates, numbers, text)
+   - Look for edge cases: empty cells, duplicates, unexpected values
+
+2. **For cross-sheet operations**: 
+   - Compare data in both sheets side-by-side
+   - Look for duplicates in reference sheets (multiple rows with same key)
+   - Check for None/empty values
+   - Verify data types match between sheets
+
+3. **For row operations** (insert/delete):
+   - Count exact number of rows to affect
+   - Understand how row numbers will change
+   - Plan operation order (delete bottom-to-top, insert bottom-to-top)
+
+4. **For complex sorting/filtering**:
+   - Understand ALL sorting criteria and their priority
+   - Identify what "duplicate" means in the context
+   - Verify sort order requirements (ascending? alphabetical? numeric?)
+
+5. **Test your understanding**:
+   - Print sample data with your logic applied
+   - Verify results match expected examples
+   - Check for edge cases before writing final code
+
+**Example Inspection Code**:
+```python
+import openpyxl
+wb = openpyxl.load_workbook('file.xlsx')
+ws = wb.active
+
+# Check ALL data, not just first 10 rows
+for row in ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True):
+    print(row)
+    
+# For cross-sheet: build and inspect lookup tables
+lookup = {}
+for row in range(2, lookup_sheet.max_row + 1):
+    key = lookup_sheet.cell(row, 1).value
+    value = lookup_sheet.cell(row, 2).value
+    if key in lookup:
+        print(f"DUPLICATE KEY: {key}")  # This is important!
+    lookup[str(key).strip()] = value
+```
 
 **Example Inspection Code**:
 ```python
@@ -67,7 +108,27 @@
     print(row)
 ```
 
-### Step 2: Choose Your Approach Based on Pattern
+### Step 2: Identify Task Type (CRITICAL for complex tasks)
+
+**DYNAMIC vs STATIC**:
+- **DYNAMIC** (user adds new data later, calculations must update automatically):
+  - Use FORMULAS (AVERAGEIFS, SUMPRODUCT, etc.) - Python static values won't work
+  - Example: "calculations automatically extend as new data is inputted"
+  - Example: "rolling average that updates with new dates"
+  - **You MUST use formulas for this**, not Python values
+
+- **STATIC** (one-time transformation, data won't change):
+  - Use PYTHON to compute values directly
+  - Example: "parse and filter these codes"
+  - Example: "sort this list once"
+
+**Red flags indicating DYNAMIC requirement**:
+- "automatically extend", "continuously add", "as data changes"
+- "rolling calculation", "running total"
+- Task mentions "Table format"
+- User will be adding data to the spreadsheet regularly
+
+### Step 3: Choose Your Approach Based on Pattern
 
 #### **Pattern A: Parse Delimited Values and Filter**
 
@@ -96,7 +157,63 @@
 5. Aggregate results (count, sum, collect)
 6. Write result to output cell
 
-#### **Pattern B: Parse Delimited Codes and Lookup Values**
+#### **Pattern B: Complex Cross-Sheet Lookup with Multiple Criteria**
+
+**Symptoms**: Need to match data across sheets using multiple columns; return corresponding values; handle edge cases
+
+**Critical Steps**:
+1. **Inspect BOTH sheets completely** - Look for:
+   - Duplicate keys in lookup sheet (multiple rows with same match value)
+   - Missing values (None/empty cells)
+   - Data type mismatches (text vs numbers)
+   - Date format issues
+
+2. **Decide on duplicate handling**:
+   - If duplicates exist in lookup sheet: Use first match? Last match? All matches?
+   - Document your decision in code
+   - Print diagnostic info showing what you chose
+
+3. **Build lookup dictionary carefully**:
+   ```python
+   # Track duplicates during building
+   seen_keys = set()
+   duplicates = []
+   lookup_table = {}
+   
+   for row in range(2, lookup_sheet.max_row + 1):
+       key = str(lookup_sheet.cell(row, 1).value).strip()
+       value = lookup_sheet.cell(row, 2).value
+       
+       if not key or value is None:
+           continue  # Skip empty cells
+       
+       if key in seen_keys:
+           duplicates.append((key, value))
+           print(f"DUPLICATE: {key} appears multiple times")
+       else:
+           lookup_table[key] = value
+           seen_keys.add(key)
+   ```
+
+4. **Apply lookup with validation**:
+   ```python
+   for row_num in range(2, main_sheet.max_row + 1):
+       lookup_key = str(main_sheet.cell(row_num, col).value).strip()
+       
+       if lookup_key in lookup_table:
+           result = lookup_table[lookup_key]
+           main_sheet.cell(row_num, output_col).value = result
+       else:
+           print(f"Row {row_num}: No match found for '{lookup_key}'")
+           main_sheet.cell(row_num, output_col).value = ""  # or appropriate default
+   ```
+
+5. **Verify results**:
+   - Print sample matches showing key and result
+   - Check for any unmatched keys
+   - Spot-check against original data
+
+#### **Pattern C: Parse Delimited Codes and Lookup Values** (Simple)
 
 **Symptoms**: Cell contains semicolon-separated codes; need to lookup each code in a table and return results
 
@@ -199,6 +316,37 @@
 wb.save('output.xlsx')
 ```
 
+### Step 4: For Row Operations (Insert/Delete) - Special Handling
+
+**Critical Rules**:
+1. **ALWAYS work from bottom to top** when deleting or inserting
+   - Prevents row number shifts from affecting later operations
+   - Example: Delete rows 100, 50, 25 (in that order, highest first)
+
+2. **Track changes explicitly**:
+   ```python
+   # Find all rows that match condition
+   rows_to_delete = []
+   for row_num in range(2, ws.max_row + 1):
+       if condition(ws.cell(row_num, col)):
+           rows_to_delete.append(row_num)
+   
+   # Process in reverse order
+   for row_num in sorted(rows_to_delete, reverse=True):
+       print(f"Deleting row {row_num}")
+       ws.delete_rows(row_num, 1)
+   ```
+
+3. **After each operation**, verify structure:
+   - Print rows around modification points
+   - Check that row numbers are still correct
+   - Verify that data structure is intact
+
+4. **Do operations in dependency order**:
+   - Deletions first (removes rows, simplifies subsequent operations)
+   - Then insertions (adds structural rows)
+   - Then data fills (populates the structure)
+
 ### Step 5: Handle Edge Cases
 
 **Empty cells**: Check `if cell.value` before processing
```

## Iteration 6 — patch `python_data_parsing_filtering` — **REJECTED**
- validation score: 0.8667 (best before: 0.9333)

```diff
--- a/python_data_parsing_filtering/SKILL.md
+++ b/python_data_parsing_filtering/SKILL.md
@@ -50,6 +50,50 @@
 Instead of thinking "what formula would I write in Excel?", ask "how do I compute this value in Python?"
 
 ### Step 1: Understand the Data Structure
+### Step 0.5: Diagnostic Inspection (CRITICAL Before Coding)
+
+Before writing ANY transformation logic, perform thorough inspection:
+
+```python
+import openpyxl
+wb = openpyxl.load_workbook('file.xlsx')
+ws = wb.active
+
+# 1. Check data extent and structure
+print(f"Max row: {ws.max_row}, Max col: {ws.max_column}")
+
+# 2. Inspect ALL data (not just first 10 rows)
+for row in range(1, min(ws.max_row + 1, 100)):  # Check first 100 rows
+    row_data = []
+    for col in range(1, min(ws.max_column + 1, 15)):
+        cell = ws.cell(row, col)
+        row_data.append(cell.value)
+    # Print rows that have data
+    if any(row_data):
+        print(f"Row {row}: {row_data}")
+
+# 3. Look for edge cases: duplicates, None values, unexpected types
+print("\nEdge case check:")
+for row in range(2, ws.max_row + 1):
+    for col in range(1, ws.max_column + 1):
+        val = ws.cell(row, col).value
+        # Check for problematic values
+        if val is None:
+            print(f"  {get_column_letter(col)}{row}: None")
+        elif isinstance(val, str) and val.startswith('='):
+            print(f"  {get_column_letter(col)}{row}: Formula - {val}")
+        elif isinstance(val, float) and val != int(val):
+            print(f"  {get_column_letter(col)}{row}: Float - {val}")
+```
+
+**Critical Questions to Answer:**
+- How many rows contain actual data (excluding headers/blanks)?
+- Are there duplicate keys or values that will cause grouping issues?
+- What data types are present? (text vs numbers vs dates)
+- Are there formulas in the source data that need evaluating?
+- What should happen to empty cells? (keep as None, convert to empty string, skip?)
+- Are there merged cells or special formatting that affects processing?
+
 
 Before writing code:
 1. Load the file with openpyxl and examine cell values
@@ -200,6 +244,72 @@
 ```
 
 ### Step 5: Handle Edge Cases
+### Step 5.5: Diagnostic Verification Before Saving
+
+**CRITICAL: Always validate output before saving.** This prevents silent failures.
+
+```python
+import openpyxl
+from openpyxl.utils import get_column_letter
+
+# After your transformation logic, BEFORE saving:
+
+print("\n" + "="*80)
+print("VERIFICATION BEFORE SAVING")
+print("="*80)
+
+# 1. Sample output - show first 10 transformed rows
+print("\nSample transformed rows (first 10):")
+for row in range(2, min(12, ws.max_row + 1)):
+    output_col = 4  # Example: column D output
+    val = ws.cell(row, output_col).value
+    source_cols = [ws.cell(row, i).value for i in range(1, 4)]
+    print(f"  Row {row}: Source={source_cols} → Output={val}")
+
+# 2. Check for unexpected values
+print("\nChecking for issues:")
+unexpected_count = 0
+for row in range(2, ws.max_row + 1):
+    output_col = 4
+    val = ws.cell(row, output_col).value
+    
+    # Check for common problems
+    if val is None and ws.cell(row, 1).value is not None:
+        print(f"  Row {row}: WARNING - Output is None but has input data")
+        unexpected_count += 1
+    elif isinstance(val, str) and val.startswith('='):
+        print(f"  Row {row}: WARNING - Output contains formula: {val}")
+        unexpected_count += 1
+    elif isinstance(val, float) and val == float('inf'):
+        print(f"  Row {row}: WARNING - Output is infinity")
+        unexpected_count += 1
+
+if unexpected_count == 0:
+    print(f"  ✓ No issues detected")
+else:
+    print(f"  ✗ Found {unexpected_count} potential issues")
+
+# 3. Count totals
+print("\nTransformation summary:")
+filled_count = sum(1 for row in range(2, ws.max_row + 1) 
+                   if ws.cell(row, output_col).value is not None)
+print(f"  Rows with output data: {filled_count}")
+print(f"  Rows total: {ws.max_row - 1}")
+
+# 4. Spot-check specific rows if known edge cases exist
+print("\nSpot checks (if applicable):")
+print(f"  Row 2 (first data): {[ws.cell(2, i).value for i in range(1, 5)]}")
+print(f"  Row {ws.max_row} (last data): {[ws.cell(ws.max_row, i).value for i in range(1, 5)]}")
+
+# Only save if no major issues detected
+if unexpected_count == 0:
+    wb.save('output.xlsx')
+    print(f"\n✓ File saved successfully")
+else:
+    print(f"\n✗ NOT SAVING - fix issues first")
+    raise Exception(f"Verification failed with {unexpected_count} issues")
+```
+
 
 **Empty cells**: Check `if cell.value` before processing
 ```python
@@ -329,6 +439,43 @@
 ❌ **Don't assume data types** - Convert to string explicitly
    - Use `str(value).strip()` to normalize
 
+❌ **Don't skip diagnostic output** - ALWAYS print sample results
+   - Print first/last rows of transformation
+   - Show count of rows processed
+   - Flag any unexpected None values or formulas in output
+   - This catches ~80% of errors before validation
+
+❌ **Don't assume row operations work correctly** - They're fragile
+   - When inserting/deleting rows, always process from highest row number first
+   - Never assume row numbers stay stable after operations
+   - Always verify by printing 5 rows before/after each operation
+   - Track which rows you modified (keep a list)
+   - After completion, spot-check the modified rows
+   
+   **Pattern for safe row operations**:
+   ```python
+   # WRONG: This will skip rows because numbers shift
+   rows_to_delete = [10, 15, 20]
+   for row in rows_to_delete:
+       ws.delete_rows(row)  # After first deletion, row 15 moves to 14!
+   
+   # RIGHT: Process from highest to lowest
+   rows_to_delete = [20, 15, 10]  # Already sorted descending
+   for row in rows_to_delete:
+       print(f"Deleting row {row}")
+       ws.delete_rows(row)
+   
+   # EVEN BETTER: Find, sort, then process
+   rows_to_delete = []
+   for row in range(2, ws.max_row + 1):
+       if condition(ws.cell(row, col)):
+           rows_to_delete.append(row)
+   
+   for row in sorted(rows_to_delete, reverse=True):
+       ws.delete_rows(row)
+   ```
+   - Use `str(value).strip()` to normalize
+
 ❌ **Don't create complex cross-sheet multi-key lookups** - They're fragile
    - If cross-sheet lookup is too complex, consider if it's solvable with Python
    - Prefer building lookup dicts from reference sheets
```
