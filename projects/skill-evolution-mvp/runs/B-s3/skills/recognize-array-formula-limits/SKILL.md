---
name: "Recognize When Array Formulas Are Problematic"
version: 1.0
tags: ["formula-strategy", "data-processing", "decision-framework"]
---

# Recognize When Array Formulas Are Problematic

## When to Apply

Use this skill when you encounter spreadsheet tasks involving:
- **Conditional filtering**: Extracting rows/values based on criteria (e.g., "only values starting with PK", "lowest performing students")
- **Multi-criteria lookups**: Finding values based on 2+ conditions (e.g., match year AND department)
- **Complex transformations**: Multi-step operations like delete rows, insert rows, update values in sequence
- **Reorganization tasks**: Restructuring data into different layouts (e.g., fixed-width rows)
- **Delimited data processing**: Parsing semicolon/comma-separated values and aggregating results

## When NOT to Apply

- Simple VLOOKUP or INDEX/MATCH with single criterion
- Basic filtering where FILTER function is available (Excel 365+)
- Straightforward arithmetic or text functions
- Single-row lookups without conditions

## Instructions

### Step 1: Recognize the Pattern
When you see the requirement, ask yourself:
- Does this require INDEX/SMALL/IF array formulas? ❌ RED FLAG
- Will the formula need Ctrl+Shift+Enter entry? ❌ RED FLAG  
- Are there 2+ conditions to match? ⚠️ CAUTION
- Does this involve conditional filtering/sequential lookup? ⚠️ CAUTION
- Are there multiple transformations chained together? ⚠️ CAUTION

### Step 2: Assess Array Formula Viability
**Problems with array formulas:**
- Ctrl+Shift+Enter entry fails when applied via Python/openpyxl (formulas don't evaluate)
- Users in Excel 2013-2016 must manually press Ctrl+Shift+Enter (not intuitive)
- Complex INDEX/SMALL/IF formulas are hard to debug and maintain
- Performance degrades on large datasets

**Example problem formulas:**
```
=IFERROR(INDEX(range, SMALL(IF(condition, ROW(range)-ROW(range)+1), n)), "")
=IF((criteria_range1=crit1)*(criteria_range2=crit2), return_value, 0)
```

### Step 3: Make the Decision

**Use DATA PROCESSING (Python/VBA) if:**
1. The task requires conditional filtering with sequential output
2. Multiple conditions must be evaluated together
3. Multi-step transformations are needed (delete, insert, update in sequence)
4. Data reorganization/restructuring is required
5. The user doesn't have Excel 365 (FILTER not available)

**Use FORMULAS only if:**
1. Single criterion lookup (VLOOKUP, INDEX/MATCH)
2. Excel 365+ available (use FILTER or LAMBDA functions)
3. User will be manually entering formulas (not automated)

### Step 4: Implement Data Processing Approach
If you've decided to use data processing:

**Python/openpyxl approach:**
```python
import openpyxl
from openpyxl import load_workbook

wb = load_workbook('file.xlsx')
ws = wb['sheet_name']

# Step 1: Load data into memory
data = []
for row in ws.iter_rows(min_row=2, values_only=True):
    data.append(row)

# Step 2: Filter/transform based on conditions
filtered_data = []
for row in data:
    if should_include(row):  # Your condition here
        filtered_data.append(transform(row))  # Your transformation here

# Step 3: Write results back
for idx, row_data in enumerate(filtered_data, start=2):
    for col_idx, value in enumerate(row_data, start=1):
        ws.cell(row=idx, column=col_idx, value=value)

wb.save('output.xlsx')
```

**Key advantages:**
- Direct access to data types and values
- Easy conditional logic (if/elif/else)
- Reliable results (no formula evaluation issues)
- Efficient even on large datasets

### Step 5: Validate Approach
After implementation:
1. ✓ Verify data loads correctly
2. ✓ Test condition logic with sample rows
3. ✓ Check that transformations produce expected output
4. ✓ Confirm no data loss or unintended changes
5. ✓ Save output file with correct structure

## Red Flags That Signal "Use Data Processing"

| Red Flag | Why | Action |
|----------|-----|--------|
| "INDEX/SMALL/IF array formula" mentioned | Ctrl+Shift+Enter entry fails in automation | Switch to Python/VBA |
| "SUMIFS to match 2+ criteria" | Can work but complex; data processing clearer | Consider Python for clarity |
| "Conditional sequential extraction" | Classic array formula use case - problematic | Use data processing |
| "Delete rows where condition, then update where different condition" | Multi-step requires careful row management | Use data processing |
| "Parse delimited values, lookup each, aggregate unique sorted results" | Pure formulas are overly complex | Use data processing |

## Examples from Wiki Patterns

**Pattern: Conditional Sequential Lookup**
- Task 10452: Extract values starting with "PK"
- ❌ Attempted: INDEX/SMALL/IF array formula
- ✅ Should use: Python loop to filter and populate cells sequentially

**Pattern: Multi-Criteria Lookup with SUMPRODUCT**
- Task 10747: Sum values based on 2 conditions
- ✓ SUMPRODUCT works here (single criterion in result)
- ⚠️ But if reorganizing multi-value results: use Python

**Pattern: Type Filtering and Reorganization**
- Task 82-30: Extract whole numbers, organize into 6-per-row format
- ✓ PASSED (score 1.0) using Python data processing
- This is the ideal use case for Python approach

## Summary Decision Tree

```
Does task require conditional sequential output?
├─ YES → Use Python/VBA data processing
└─ NO  
    ├─ Multi-step transformations (delete, insert, reorder)?
    │  ├─ YES → Use Python/VBA
    │  └─ NO → Go to next
    │
    ├─ Data reorganization/restructuring?
    │  ├─ YES → Use Python/VBA  
    │  └─ NO → Go to next
    │
    ├─ Simple lookup with 1 criterion?
    │  ├─ YES → Use VLOOKUP or INDEX/MATCH
    │  └─ NO → Go to next
    │
    └─ Excel 365+ available?
       ├─ YES → Use FILTER or native functions
       └─ NO → Use Python/VBA for reliability
```