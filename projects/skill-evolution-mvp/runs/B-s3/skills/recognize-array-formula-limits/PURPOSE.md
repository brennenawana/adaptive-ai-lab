# Recognize When Array Formulas Are Problematic

## Origin
Emerged from analysis of task failure patterns in iteration 1:
- **8 passing tasks** (100% success): All used data processing (Python/VBA)
- **27 failing tasks** (0% success): Attempted complex array formulas requiring Ctrl+Shift+Enter
- **Root issue**: Formulas creating {=IFERROR(INDEX(SMALL(IF...)))} don't reliably evaluate when applied via Python/openpyxl

## Patterns Addressed

### 1. Conditional Sequential Lookup (Task 10452)
- **Pattern**: "Extract 1st, 2nd, 3rd matching value from range based on condition"
- **Failed approach**: INDEX/SMALL/IF array formula + Ctrl+Shift+Enter
- **Better approach**: Python loop to filter and populate sequentially
- **Reason**: Array formulas don't evaluate reliably in automated context

### 2. Multi-Criteria Lookups (Task 10747)
- **Pattern**: "Sum/lookup based on 2+ conditions"
- **Works with**: SUMPRODUCT (doesn't require special entry)
- **Fails with**: INDEX/MATCH arrays requiring Ctrl+Shift+Enter
- **Lesson**: Recognize which functions avoid array formula issues

### 3. Type Filtering and Reorganization (Task 82-30)
- **Pattern**: "Extract by type criteria, reorganize into fixed-width rows"
- **Successful approach**: Python data processing (scored 1.0)
- **Why**: Direct type checking (value == int(value)) is clearer than complex formulas
- **Key insight**: When data needs structural reorganization, use code

### 4. Delimited Data Parsing (Task 48745)
- **Pattern**: "Parse delimited values, lookup each, aggregate unique sorted results"
- **Successful approach**: Python processing with set deduplication (scored 1.0)
- **Why**: Aggregating while maintaining uniqueness/sort is complex in formulas

## Evolution History

### Iteration 1 (Current)
- Identified that array formulas are root cause of 77% failure rate
- All data processing solutions (Tasks 192-22, 48745, 82-30) achieved perfect scores
- Recognized pattern: Conditional operations + multi-step transformations = data processing needed
- Created decision framework to guide when to switch approaches

### Key Insight
The wiki patterns correctly identified the TECHNICAL SOLUTIONS (INDEX/SMALL/IF, SUMPRODUCT, etc.) but lacked a META-SKILL about when each approach is VIABLE in practice. Array formulas work in Excel but fail in automated Python-based solution delivery.