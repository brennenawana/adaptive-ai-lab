# Purpose: Python-Based Data Parsing and Filtering

## Origin

This skill emerges from analysis of 6 failed formula-based solutions (tasks 10452, 10747, 32438, 42354, 1818, 39931) contrasted with 2 successful Python-based solutions (tasks 39903, 48745). 

The root cause of failures: **Excel formulas created via openpyxl are unreliable**, especially:
- Array formulas (INDEX/SMALL/IF) cannot be properly marked in the .xlsx file
- SUMPRODUCT, SUMIFS, and complex formulas sometimes fail validation
- Tasks requiring Ctrl+Shift+Enter are fundamentally incompatible with programmatic file creation

The root cause of success: **Direct Python manipulation of cell data** bypasses Excel formula limitations entirely and works consistently.

## Patterns Addressed

This skill consolidates and operationalizes these proven patterns:

1. **Delimiter-Separated Field Parsing** - Parse comma/semicolon-separated values with internal structure
2. **Conditional Filtering with Aggregation** - Count, extract, or sum items matching conditions
3. **Multi-Code Lookup with Deduplication** - Parse codes, lookup each in table, return unique sorted results
4. **Cross-Reference Matching** - Lookup data across sheets based on multiple criteria
5. **String Manipulation and Extraction** - Handle complex delimiters, whitespace, and substrings
6. **Type Conversion and Cleaning** - Convert strings to appropriate formats, handle edge cases

## Evolution History

**Iteration 1 Failure** (Score: 0.3333):
- Skill `excel-formula-pattern-lookup-filtering` tried to teach 5 formula patterns
- 23 failures vs 8 passes
- Root cause: Formulas don't work reliably when created programmatically
- Approach was fundamentally incompatible with openpyxl's capabilities

**Iteration 2 Analysis**:
- Examined execution traces across 9 tasks
- Pattern found: Python solutions = 100% pass rate (2/2)
- Pattern found: Formula solutions = 0% pass rate (0/7)
- Conclusion: Shift to Python-first approach

**New Direction**:
- Abandon Excel formula teaching for complex patterns
- Focus on Python code that directly transforms cell data
- Provide clear patterns and templates
- Acknowledge when Python is required vs optional
- Build confidence through reliable, working solutions

## Key Insight

The previous skill's failure wasn't due to incorrect formula theory - the formulas were correct. The failure was **architectural**: trying to use openpyxl to create formula patterns that require runtime Excel interpretation (especially array formulas) is fundamentally unreliable.

The solution is **pragmatic acceptance** of openpyxl's limitations and **systematic use of Python code** for all complex data transformation tasks.
