# Pattern Index

- [formula-range-scoping-errors](wiki/patterns/formula-range-scoping-errors.md): Formulas fail when ranges aren't properly bounded (entire columns, wrong row limits). Fix: Explicitly scope ranges to data extent (e.g., $B$6:$B$200 not $B:$B) and validate upper/lower bounds.

- [direct-manipulation-vs-formulas](wiki/patterns/direct-manipulation-vs-formulas.md): Complex Excel formulas often fail in test environments (formula errors, version incompatibility, range issues). Python/openpyxl direct data manipulation is more reliable and easier to verify.

- [dynamic-column-location-pattern](wiki/patterns/dynamic-column-location-pattern.md): When column position changes daily, search header row for identifier, extract column index, then act on that column. Prevents hardcoding column letters; enables daily data updates.

- [sparse-data-rolling-calculations](wiki/patterns/sparse-data-rolling-calculations.md): Rolling averages on sparse data fail when formula ranges include headers. Use AVERAGEIFS with explicit row bounds (e.g., A6:A200) and filter by date criteria, not cell count.

- [excel-version-compatibility-tradeoff](wiki/patterns/excel-version-compatibility-tradeoff.md): Modern Excel functions (FILTER, LAMBDA) fail in older versions or test harnesses. Provide backward-compatible alternatives (INDEX/SMALL/IF arrays or Python) when modern functions are primary solution.

- [python-string-processing-for-text-matching](wiki/patterns/python-string-processing-for-text-matching.md): Keyword scanning and text pattern matching fail or become fragile in Excel formulas. Python string operations (substring matching, regex) provide case-insensitive, flexible text processing that scales to prefix/suffix variations.

- [multi-criteria-lookup-with-date-ranges](wiki/patterns/multi-criteria-lookup-with-date-ranges.md): Multi-criteria lookups requiring date range validation (e.g., commission rates by salesperson + type + date within range) become extremely complex in Excel (nested INDEX/MATCH/IF). Python loop-based matching with simple date comparisons is clear, maintainable, and reliable.

- [sequence-detection-formula-complexity](wiki/patterns/sequence-detection-formula-complexity.md): Detecting sequences or streaks (e.g., count only on last row of consecutive group) requires complex Excel logic (SUMPRODUCT/IF nesting with row comparisons). Python loop-based approach with simple conditions is more maintainable and less error-prone.

- [delimited-value-multi-lookup](wiki/patterns/delimited-value-multi-lookup.md): Semicolon-delimited multi-value lookups with result aggregation fail or become fragile in Excel formulas. Use Python to split by delimiter, lookup each value, collect/deduplicate with set(), and sort results.

- [test-harness-validation-gap](wiki/patterns/test-harness-validation-gap.md): Solutions that appear functionally correct (working logic, proper values, correct formulas) still fail test validation (score 0.0), suggesting unspecified file structure or output format requirements. When implementation looks correct but fails, verify file structure, cell placement, and output format match test expectations exactly.
