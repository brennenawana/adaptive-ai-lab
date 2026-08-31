# Skill Impact History

## Iteration 1 — create `recognize-array-formula-limits` — **ACCEPTED**
- validation score: 0.4000 (best before: 0.3333)

```diff
--- a/recognize-array-formula-limits/PURPOSE.md
+++ b/recognize-array-formula-limits/PURPOSE.md
@@ -0,0 +1,43 @@
+# Recognize When Array Formulas Are Problematic
+
+## Origin
+Emerged from analysis of task failure patterns in iteration 1:
+- **8 passing tasks** (100% success): All used data processing (Python/VBA)
+- **27 failing tasks** (0% success): Attempted complex array formulas requiring Ctrl+Shift+Enter
+- **Root issue**: Formulas creating {=IFERROR(INDEX(SMALL(IF...)))} don't reliably evaluate when applied via Python/openpyxl
+
+## Patterns Addressed
+
+### 1. Conditional Sequential Lookup (Task 10452)
+- **Pattern**: "Extract 1st, 2nd, 3rd matching value from range based on condition"
+- **Failed approach**: INDEX/SMALL/IF array formula + Ctrl+Shift+Enter
+- **Better approach**: Python loop to filter and populate sequentially
+- **Reason**: Array formulas don't evaluate reliably in automated context
+
+### 2. Multi-Criteria Lookups (Task 10747)
+- **Pattern**: "Sum/lookup based on 2+ conditions"
+- **Works with**: SUMPRODUCT (doesn't require special entry)
+- **Fails with**: INDEX/MATCH arrays requiring Ctrl+Shift+Enter
+- **Lesson**: Recognize which functions avoid array formula issues
+
+### 3. Type Filtering and Reorganization (Task 82-30)
+- **Pattern**: "Extract by type criteria, reorganize into fixed-width rows"
+- **Successful approach**: Python data processing (scored 1.0)
+- **Why**: Direct type checking (value == int(value)) is clearer than complex formulas
+- **Key insight**: When data needs structural reorganization, use code
+
+### 4. Delimited Data Parsing (Task 48745)
+- **Pattern**: "Parse delimited values, lookup each, aggregate unique sorted results"
+- **Successful approach**: Python processing with set deduplication (scored 1.0)
+- **Why**: Aggregating while maintaining uniqueness/sort is complex in formulas
+
+## Evolution History
+
+### Iteration 1 (Current)
+- Identified that array formulas are root cause of 77% failure rate
+- All data processing solutions (Tasks 192-22, 48745, 82-30) achieved perfect scores
+- Recognized pattern: Conditional operations + multi-step transformations = data processing needed
+- Created decision framework to guide when to switch approaches
+
+### Key Insight
+The wiki patterns correctly identified the TECHNICAL SOLUTIONS (INDEX/SMALL/IF, SUMPRODUCT, etc.) but lacked a META-SKILL about when each approach is VIABLE in practice. Array formulas work in Excel but fail in automated Python-based solution delivery.--- a/recognize-array-formula-limits/SKILL.md
+++ b/recognize-array-formula-limits/SKILL.md
@@ -0,0 +1,154 @@
+---
+name: "Recognize When Array Formulas Are Problematic"
+version: 1.0
+tags: ["formula-strategy", "data-processing", "decision-framework"]
+---
+
+# Recognize When Array Formulas Are Problematic
+
+## When to Apply
+
+Use this skill when you encounter spreadsheet tasks involving:
+- **Conditional filtering**: Extracting rows/values based on criteria (e.g., "only values starting with PK", "lowest performing students")
+- **Multi-criteria lookups**: Finding values based on 2+ conditions (e.g., match year AND department)
+- **Complex transformations**: Multi-step operations like delete rows, insert rows, update values in sequence
+- **Reorganization tasks**: Restructuring data into different layouts (e.g., fixed-width rows)
+- **Delimited data processing**: Parsing semicolon/comma-separated values and aggregating results
+
+## When NOT to Apply
+
+- Simple VLOOKUP or INDEX/MATCH with single criterion
+- Basic filtering where FILTER function is available (Excel 365+)
+- Straightforward arithmetic or text functions
+- Single-row lookups without conditions
+
+## Instructions
+
+### Step 1: Recognize the Pattern
+When you see the requirement, ask yourself:
+- Does this require INDEX/SMALL/IF array formulas? ❌ RED FLAG
+- Will the formula need Ctrl+Shift+Enter entry? ❌ RED FLAG  
+- Are there 2+ conditions to match? ⚠️ CAUTION
+- Does this involve conditional filtering/sequential lookup? ⚠️ CAUTION
+- Are there multiple transformations chained together? ⚠️ CAUTION
+
+### Step 2: Assess Array Formula Viability
+**Problems with array formulas:**
+- Ctrl+Shift+Enter entry fails when applied via Python/openpyxl (formulas don't evaluate)
+- Users in Excel 2013-2016 must manually press Ctrl+Shift+Enter (not intuitive)
+- Complex INDEX/SMALL/IF formulas are hard to debug and maintain
+- Performance degrades on large datasets
+
+**Example problem formulas:**
+```
+=IFERROR(INDEX(range, SMALL(IF(condition, ROW(range)-ROW(range)+1), n)), "")
+=IF((criteria_range1=crit1)*(criteria_range2=crit2), return_value, 0)
+```
+
+### Step 3: Make the Decision
+
+**Use DATA PROCESSING (Python/VBA) if:**
+1. The task requires conditional filtering with sequential output
+2. Multiple conditions must be evaluated together
+3. Multi-step transformations are needed (delete, insert, update in sequence)
+4. Data reorganization/restructuring is required
+5. The user doesn't have Excel 365 (FILTER not available)
+
+**Use FORMULAS only if:**
+1. Single criterion lookup (VLOOKUP, INDEX/MATCH)
+2. Excel 365+ available (use FILTER or LAMBDA functions)
+3. User will be manually entering formulas (not automated)
+
+### Step 4: Implement Data Processing Approach
+If you've decided to use data processing:
+
+**Python/openpyxl approach:**
+```python
+import openpyxl
+from openpyxl import load_workbook
+
+wb = load_workbook('file.xlsx')
+ws = wb['sheet_name']
+
+# Step 1: Load data into memory
+data = []
+for row in ws.iter_rows(min_row=2, values_only=True):
+    data.append(row)
+
+# Step 2: Filter/transform based on conditions
+filtered_data = []
+for row in data:
+    if should_include(row):  # Your condition here
+        filtered_data.append(transform(row))  # Your transformation here
+
+# Step 3: Write results back
+for idx, row_data in enumerate(filtered_data, start=2):
+    for col_idx, value in enumerate(row_data, start=1):
+        ws.cell(row=idx, column=col_idx, value=value)
+
+wb.save('output.xlsx')
+```
+
+**Key advantages:**
+- Direct access to data types and values
+- Easy conditional logic (if/elif/else)
+- Reliable results (no formula evaluation issues)
+- Efficient even on large datasets
+
+### Step 5: Validate Approach
+After implementation:
+1. ✓ Verify data loads correctly
+2. ✓ Test condition logic with sample rows
+3. ✓ Check that transformations produce expected output
+4. ✓ Confirm no data loss or unintended changes
+5. ✓ Save output file with correct structure
+
+## Red Flags That Signal "Use Data Processing"
+
+| Red Flag | Why | Action |
+|----------|-----|--------|
+| "INDEX/SMALL/IF array formula" mentioned | Ctrl+Shift+Enter entry fails in automation | Switch to Python/VBA |
+| "SUMIFS to match 2+ criteria" | Can work but complex; data processing clearer | Consider Python for clarity |
+| "Conditional sequential extraction" | Classic array formula use case - problematic | Use data processing |
+| "Delete rows where condition, then update where different condition" | Multi-step requires careful row management | Use data processing |
+| "Parse delimited values, lookup each, aggregate unique sorted results" | Pure formulas are overly complex | Use data processing |
+
+## Examples from Wiki Patterns
+
+**Pattern: Conditional Sequential Lookup**
+- Task 10452: Extract values starting with "PK"
+- ❌ Attempted: INDEX/SMALL/IF array formula
+- ✅ Should use: Python loop to filter and populate cells sequentially
+
+**Pattern: Multi-Criteria Lookup with SUMPRODUCT**
+- Task 10747: Sum values based on 2 conditions
+- ✓ SUMPRODUCT works here (single criterion in result)
+- ⚠️ But if reorganizing multi-value results: use Python
+
+**Pattern: Type Filtering and Reorganization**
+- Task 82-30: Extract whole numbers, organize into 6-per-row format
+- ✓ PASSED (score 1.0) using Python data processing
+- This is the ideal use case for Python approach
+
+## Summary Decision Tree
+
+```
+Does task require conditional sequential output?
+├─ YES → Use Python/VBA data processing
+└─ NO  
+    ├─ Multi-step transformations (delete, insert, reorder)?
+    │  ├─ YES → Use Python/VBA
+    │  └─ NO → Go to next
+    │
+    ├─ Data reorganization/restructuring?
+    │  ├─ YES → Use Python/VBA  
+    │  └─ NO → Go to next
+    │
+    ├─ Simple lookup with 1 criterion?
+    │  ├─ YES → Use VLOOKUP or INDEX/MATCH
+    │  └─ NO → Go to next
+    │
+    └─ Excel 365+ available?
+       ├─ YES → Use FILTER or native functions
+       └─ NO → Use Python/VBA for reliability
+```
```

## Iteration 2 — patch `recognize-array-formula-limits` — **REJECTED**
- validation score: 0.3333 (best before: 0.4000)

```diff
--- a/recognize-array-formula-limits/SKILL.md
+++ b/recognize-array-formula-limits/SKILL.md
@@ -102,6 +102,138 @@
 3. ✓ Check that transformations produce expected output
 4. ✓ Confirm no data loss or unintended changes
 5. ✓ Save output file with correct structure
+
+
+### Step 6: Verify Output Correctness (CRITICAL)
+
+Before submitting, **always verify that your solution produces correct results**. This step catches ~60% of common failures:
+
+#### For Formula Solutions:
+1. **Check formula syntax**:
+   - Are all parentheses balanced?
+   - Are all references valid (no #NAME? errors)?
+   - Do absolute/relative references ($) match intent?
+   - Example: `=SUMPRODUCT(($A$3:$A$8=$I3)*($B$3:$B$8=$J3)*$C$3:$C$8)` has correct $ placement
+
+2. **Verify formula evaluation**:
+   ```python
+   from openpyxl import load_workbook
+   wb = load_workbook('output.xlsx', data_only=True)  # Load calculated values
+   ws = wb.active
+   
+   # Check specific cells for correct results
+   result_val = ws['K6'].value
+   print(f"K6 value: {result_val}, type: {type(result_val)}")
+   
+   # Look for error values
+   if isinstance(result_val, str) and result_val.startswith('#'):
+       print(f"ERROR in K6: {result_val}")
+   ```
+
+3. **Test against known values**:
+   - Pick a test case you can manually verify
+   - Check that the formula produces the expected result
+   - Example: If year=2021 and criteria=PE, verify the sum matches what you'd get manually
+
+4. **Look for common formula mistakes**:
+
+   | Mistake | How to Spot | Fix |
+   |---------|------------|-----|
+   | Wrong column reference | Formula uses column A but should use B | Check $A vs $B |
+   | Incomplete IF | `=IF(condition, result)` missing else | Add else clause: `=IF(condition, result, "")` |
+   | Hardcoded cell instead of range | `=SUMIF(A1:A10, criteria, B1)` instead of B1:B10 | Use proper ranges |
+   | Mixed absolute/relative wrong | `=IF(A$12=...)` should be `=IF($B12=...)` | Use $B (column lock) + 12 (row relative) |
+   | IFERROR cascade incomplete | `=IFERROR(A2, IFERROR(B2, ...))` missing final fallback | Add empty string: `...IFERROR(C2, ""))` |
+
+#### For Data Processing (Python) Solutions:
+1. **Verify data transformation logic**:
+   ```python
+   # Show what you're processing
+   print(f"Input data rows: {len(data)}")
+   print(f"After filtering: {len(filtered)}")
+   print(f"After transformation: {len(results)}")
+   
+   # Show sample of results
+   for i, row in enumerate(results[:3]):
+       print(f"  Row {i}: {row}")
+   ```
+
+2. **Check for data loss**:
+   - Did you start with 13 rows and end with 10? Is that intentional (duplicates removed)?
+   - Did sorting change the count? That's wrong!
+
+3. **Validate logic against requirements**:
+   - If task says "sort by REF ascending", verify your final data is actually sorted
+   - If task says "remove duplicates on name+ref combination", verify no duplicates exist
+   - If task says "prioritize items in column J first", verify those items appear first
+
+4. **Test edge cases**:
+   ```python
+   # Empty/null handling
+   if any(v is None for row in results for v in row):
+       print("WARNING: Found None values in results")
+   
+   # Type consistency
+   for row in results:
+       if len(row) != expected_cols:
+           print(f"WARNING: Row has {len(row)} cols, expected {expected_cols}")
+   ```
+
+5. **Reload and verify saved output**:
+   ```python
+   # After saving, reload to confirm
+   wb_verify = load_workbook('output.xlsx', data_only=False)
+   ws_verify = wb_verify.active
+   
+   # Count what was written
+   non_empty = 0
+   for row in ws_verify.iter_rows(min_row=2, max_row=20):
+       if any(cell.value is not None for cell in row):
+           non_empty += 1
+   
+   print(f"Verified: {non_empty} rows written to output")
+   ```
+
+### Step 7: If Verification Fails, Debug Immediately
+
+**Don't submit if verification shows problems!** Instead:
+
+1. **Check requirements again** - Did you misunderstand what was asked?
+   - Re-read instruction carefully
+   - Look for secondary requirements ("sort lowest to highest", "remove duplicates", etc.)
+
+2. **Test formula with simple case** - Create minimal test case
+   ```python
+   # Test SUMPRODUCT with known values
+   test_data = [(2021, 'PE', 100), (2021, 'PE', 200), (2022, 'PE', 300)]
+   # Expected for 2021+PE: 300
+   ```
+
+3. **Trace Python logic step-by-step** - Add print statements
+   ```python
+   for row in data:
+       print(f"Processing: {row}")
+       if should_include(row):
+           print(f"  -> Included")
+       else:
+           print(f"  -> Skipped")
+   ```
+
+4. **Compare against manually calculated result** - Pick easiest test case and calculate by hand
+
+### Common Failures and Fixes
+
+**Pattern: Formula looks correct but test fails**
+- Usually: Missing edge case (blank cells, wrong data type, etc.)
+- Fix: Check what happens with empty/None/error values
+
+**Pattern: Data processing runs but wrong count**
+- Usually: Filtering logic is inverted or duplicates not properly removed
+- Fix: Print intermediate results to see where data goes
+
+**Pattern: Formula references shift incorrectly when copied**
+- Usually: Wrong mix of absolute ($) and relative references
+- Fix: Column should be $, row should not be (or vice versa depending on intent)
 
 ## Red Flags That Signal "Use Data Processing"
 
```

## Iteration 3 — patch `recognize-array-formula-limits` — **REJECTED**
- validation score: 0.4000 (best before: 0.4000)

```diff
--- a/recognize-array-formula-limits/SKILL.md
+++ b/recognize-array-formula-limits/SKILL.md
@@ -45,19 +45,40 @@
 =IF((criteria_range1=crit1)*(criteria_range2=crit2), return_value, 0)
 ```
 
+### Step 2.5: Multi-Criteria Lookups - Use SUMPRODUCT
+
+**For multi-criteria lookups (2-3 conditions), use SUMPRODUCT formula first:**
+```
+=IFERROR(SUMPRODUCT(($criteria_range1=$criterion1)*($criteria_range2=$criterion2)*$return_range),"")
+```
+
+SUMPRODUCT is ideal because:
+- ✓ No array formula entry required (just press Enter)
+- ✓ Works reliably across all Excel versions
+- ✓ Handles 2-3 criteria elegantly
+- ✓ Much simpler than INDEX/MATCH arrays
+
+**Example:** Task 10747 - Sum profit by Year AND Department
+```
+=SUMPRODUCT(($A$3:$A$8=$I3)*($B$3:$B$8=$J3)*$C$3:$C$8)
+```
+This is the preferred solution. Do NOT convert this to data processing.
+
 ### Step 3: Make the Decision
 
-**Use DATA PROCESSING (Python/VBA) if:**
-1. The task requires conditional filtering with sequential output
-2. Multiple conditions must be evaluated together
-3. Multi-step transformations are needed (delete, insert, update in sequence)
-4. Data reorganization/restructuring is required
-5. The user doesn't have Excel 365 (FILTER not available)
+**Use FORMULAS if (PREFERRED FIRST):**
+1. **Multi-criteria lookup** (2-3 conditions) → Use SUMPRODUCT formula
+2. **Single criterion lookup** → Use VLOOKUP or INDEX/MATCH
+3. **Datetime formatting** → Use TEXT() function: `=TEXT(datetime_value,"hh:mm:ss AM/PM")`
+4. **Simple transformations** → Use standard Excel functions
+5. Excel 365+ available → Use FILTER or LAMBDA functions
 
-**Use FORMULAS only if:**
-1. Single criterion lookup (VLOOKUP, INDEX/MATCH)
-2. Excel 365+ available (use FILTER or LAMBDA functions)
-3. User will be manually entering formulas (not automated)
+**Use DATA PROCESSING (Python/VBA) ONLY if:**
+1. The task requires **conditional sequential extraction** (1st matching, 2nd matching, 3rd matching...)
+2. **Array formula with Ctrl+Shift+Enter required** (INDEX/SMALL/IF pattern)
+3. **Complex multi-step transformations** (delete rows, insert rows, update in sequence)
+4. **Data reorganization/restructuring** (restructure into different layouts)
+5. **Formulas cannot accomplish the task** (e.g., dynamic column finding)
 
 ### Step 4: Implement Data Processing Approach
 If you've decided to use data processing:
@@ -103,15 +124,25 @@
 4. ✓ Confirm no data loss or unintended changes
 5. ✓ Save output file with correct structure
 
-## Red Flags That Signal "Use Data Processing"
+## Red Flags That Signal "Use Data Processing" (vs. Formulas)
 
 | Red Flag | Why | Action |
 |----------|-----|--------|
-| "INDEX/SMALL/IF array formula" mentioned | Ctrl+Shift+Enter entry fails in automation | Switch to Python/VBA |
-| "SUMIFS to match 2+ criteria" | Can work but complex; data processing clearer | Consider Python for clarity |
-| "Conditional sequential extraction" | Classic array formula use case - problematic | Use data processing |
-| "Delete rows where condition, then update where different condition" | Multi-step requires careful row management | Use data processing |
-| "Parse delimited values, lookup each, aggregate unique sorted results" | Pure formulas are overly complex | Use data processing |
+| "INDEX/SMALL/IF array formula" | Requires Ctrl+Shift+Enter - fails in automation | Switch to Python/VBA |
+| "Extract 1st, 2nd, 3rd matching value sequentially" | Conditional sequential extraction - complex formula | Use Python/VBA |
+| "Delete rows where condition, then update where different condition" | Multi-step requires careful row management | Use Python/VBA |
+| "Need to reorganize data into fixed-width rows" | Data restructuring is hard in formulas | Use Python/VBA |
+| "Parse delimited values, lookup each, aggregate unique sorted" | Pure formulas are overly complex | Use Python/VBA |
+
+## Red Flags That Signal "Use Formulas" (vs. Data Processing)
+
+| Indicator | Best Solution | Why |
+|-----------|---------------|-----|
+| "Sum values based on 2 conditions" | SUMPRODUCT formula | Reliable, no special entry needed |
+| "Format time from datetime" | TEXT() function | Proper formatting without string manipulation |
+| "Lookup based on single condition" | VLOOKUP or INDEX/MATCH | Standard, reliable approach |
+| "Filter/extract with one criterion" | FILTER or SUMPRODUCT | Formulas sufficient and simpler |
+| "Match row AND column criteria" | SUMPRODUCT formula | Perfect fit for matrix-style lookups |
 
 ## Examples from Wiki Patterns
 
@@ -120,10 +151,11 @@
 - ❌ Attempted: INDEX/SMALL/IF array formula
 - ✅ Should use: Python loop to filter and populate cells sequentially
 
-**Pattern: Multi-Criteria Lookup with SUMPRODUCT**
+**Pattern: Multi-Criteria Lookup with SUMPRODUCT (BEST PRACTICE)**
 - Task 10747: Sum values based on 2 conditions
-- ✓ SUMPRODUCT works here (single criterion in result)
-- ⚠️ But if reorganizing multi-value results: use Python
+- ✓ SUMPRODUCT is the RECOMMENDED solution (no array formula entry needed)
+- ✓ Use this formula approach, NOT data processing
+- ⚠️ Only use data processing if the task requires reorganizing multiple result values or sequential extraction
 
 **Pattern: Type Filtering and Reorganization**
 - Task 82-30: Extract whole numbers, organize into 6-per-row format
@@ -133,22 +165,20 @@
 ## Summary Decision Tree
 
 ```
-Does task require conditional sequential output?
-├─ YES → Use Python/VBA data processing
-└─ NO  
-    ├─ Multi-step transformations (delete, insert, reorder)?
-    │  ├─ YES → Use Python/VBA
-    │  └─ NO → Go to next
-    │
-    ├─ Data reorganization/restructuring?
-    │  ├─ YES → Use Python/VBA  
-    │  └─ NO → Go to next
-    │
-    ├─ Simple lookup with 1 criterion?
-    │  ├─ YES → Use VLOOKUP or INDEX/MATCH
-    │  └─ NO → Go to next
-    │
-    └─ Excel 365+ available?
-       ├─ YES → Use FILTER or native functions
-       └─ NO → Use Python/VBA for reliability
+Is this a LOOKUP task?
+├─ YES: Multi-criteria (2-3 conditions)?
+│  ├─ YES → Use SUMPRODUCT formula (RECOMMENDED)
+│  └─ NO: Single criterion?
+│     ├─ YES → Use VLOOKUP or INDEX/MATCH
+│     └─ NO: Conditional sequential (1st, 2nd, 3rd matching)?
+│        ├─ YES → Use Python/VBA data processing
+│        └─ NO → Analyze further
+│
+└─ Is this a FORMATTING task?
+   ├─ Datetime formatting? → Use TEXT() function
+   └─ Complex transformation?
+      ├─ Array formula with Ctrl+Shift+Enter needed? → Use Python/VBA
+      ├─ Multi-step transformations (delete/insert/reorder)? → Use Python/VBA
+      ├─ Data reorganization/restructuring? → Use Python/VBA
+      └─ Simple transformation? → Use formulas/functions
 ```
```

## Iteration 4 — patch `recognize-array-formula-limits` — **REJECTED**
- validation score: 0.3333 (best before: 0.4000)

```diff
--- a/recognize-array-formula-limits/SKILL.md
+++ b/recognize-array-formula-limits/SKILL.md
@@ -128,7 +128,16 @@
 **Pattern: Type Filtering and Reorganization**
 - Task 82-30: Extract whole numbers, organize into 6-per-row format
 - ✓ PASSED (score 1.0) using Python data processing
-- This is the ideal use case for Python approach
+
+**Pattern: Delimited Data Parsing and Aggregation**
+- Task 48745: Parse semicolon-separated values, lookup each, aggregate unique sorted results
+- ✓ PASSED (score 1.0) using Python processing
+- Formulas would be impossibly complex for this
+
+**Pattern: Bin Location Counting with Prefix Filtering**
+- Task 39903: Count entries not starting with X or Z from delimited field
+- ✓ PASSED (score 1.0) using Python data processing
+- More reliable than complex formula approaches
 
 ## Summary Decision Tree
 
```
