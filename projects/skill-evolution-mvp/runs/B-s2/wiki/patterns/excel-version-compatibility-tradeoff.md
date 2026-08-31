# Excel Version Compatibility Tradeoff

## Problem
Modern Excel functions (FILTER, LAMBDA) fail when test harness uses older Excel versions or test environments that don't support them.

## Evidence
**Task 10452 - FILTER failure:**
- Formula: `=FILTER(B$3:B$100,LEFT(B$3:B$100,2)="PK")`
- FILTER is Excel 365+ only (2021 or later)
- Score: 0.0 → Test harness likely uses Excel 2019 or earlier
- Feature: Would work perfectly in modern Excel (spill array)

## Root Cause
1. **Excel version diversity**: Test environments may use older Excel
2. **Backward compatibility**: Not all test systems have Excel 365
3. **Function availability**: FILTER, LAMBDA, SEQUENCE not in pre-2021 Excel
4. **Silent failures**: Formula returns #NAME? error instead of result

## Solution Strategy
**When using modern functions:**
1. Provide primary solution (FILTER)
2. Include fallback for older Excel (array formula with INDEX/SMALL/IF)
3. Document which version works where
4. **Better: Use Python** to avoid version dependency entirely

## Alternative Formula (Backward-Compatible)
```excel
=IFERROR(INDEX($B$3:$B$100,SMALL(IF(LEFT($B$3:$B$100,2)="PK",ROW($B$3:$B$100)-ROW($B$3)+1),ROW()-3)),"")
```
- Requires Ctrl+Shift+Enter (array formula)
- Works in all Excel versions
- More complex than FILTER but compatible

## Best Practice
Use **Python/openpyxl** when:
- Modern Excel functions are required
- Test harness version is unknown
- Backward compatibility is uncertain
