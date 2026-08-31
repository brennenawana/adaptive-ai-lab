# Python over Formulas for Complexity

## Origin

Observed failure pattern across 19 failed spreadsheet manipulation tasks:
- Tasks using complex Excel formulas (FILTER, INDEX/SUMPRODUCT, AVERAGEIFS, SUMIFS with multiple criteria) consistently score 0.0
- Tasks using Python direct data manipulation consistently pass (11/11 test cases passing with Python approach)

Root cause: Excel formulas fail due to:
1. Version incompatibility (FILTER is 365+ only)
2. Range scoping issues (entire column references including headers)
3. Array formula complexity requiring Ctrl+Shift+Enter
4. Formula calculation errors in test environments
5. Difficulty verifying complex formula logic without opening in Excel

## Patterns Addressed

1. **excel-version-compatibility-tradeoff** - Formulas using modern functions fail in test harnesses with older Excel. Python eliminates version dependencies entirely.

2. **direct-manipulation-vs-formulas** - Complex formulas fail; Python succeeds consistently. This skill operationalizes that pattern into actionable decision criteria.

3. **formula-range-scoping-errors** - Formulas with improper range bounds (entire columns, wrong row limits) cause calculation errors. Python uses explicit row iteration, eliminating ambiguity.

4. **sparse-data-rolling-calculations** - AVERAGEIFS and SUMIFS with date ranges fail when ranges include headers. Python iterates explicitly, avoiding header interference.

5. **dynamic-column-location-pattern** - While documented for hardcoding column letters, this extends to: formulas referencing fixed columns fail when positions change. Python finds columns dynamically at runtime.

## Evolution History

### Iteration 1 (Current)

**Problem**: Agent defaults to formula-based solutions even for complex scenarios where Python would be more reliable. This results in 63% failure rate (19/30 tasks).

**Solution**: Create decision framework that:
- Identifies high-risk formula scenarios (multi-criteria, date ranges, dynamic columns, complex conditions)
- Recommends Python direct manipulation for these cases
- Provides concrete Python code patterns for common patterns
- Explains why Python succeeds where formulas fail

**Evidence**:
- Task 408-39 (PASS): Find column by header, copy with formatting - Python approach
- Task 82-30 (PASS): Extract whole numbers via iteration - Python approach
- Task 22-47 (PASS): Complex sorting with conditions - Python approach
- Task 10452 (FAIL): FILTER function - Formula approach fails
- Task 39931 (FAIL): INDEX/SUMPRODUCT - Formula approach fails
- Task 56786 (FAIL): AVERAGEIFS - Formula approach fails
- Task 47766 (FAIL): SUMIFS with dates - Formula approach fails

**Expected Impact**: Shift agent decision-making from 63% formula-based failures to Python-based successes, targeting 80%+ pass rate by addressing the root cause: inappropriate tool selection.