# Pattern Index

[criteria-based-row-filtering](wiki/patterns/criteria-based-row-filtering.md): Filter rows from source sheet by criteria value using direct data processing iteration; extract matching rows and copy to target sheet maintaining order; 100% reliable compared to array formulas.

[keyword-pattern-matching-and-population](wiki/patterns/keyword-pattern-matching-and-population.md): Search for multiple keywords (case-insensitive, partial match) in cells and populate target column; iterate rows checking if any keyword is substring of cell text; successfully handles complex multi-keyword scenarios.

[multi-criteria-lookup-sumproduct](wiki/patterns/multi-criteria-lookup-sumproduct.md): Multi-criteria lookups without array formula entry using SUMPRODUCT; handles multiple match conditions reliably across Excel versions with formula `=IFERROR(SUMPRODUCT((range1=crit1)*(range2=crit2)*return_range),"")`.

[cascading-error-priority-lookup](wiki/patterns/cascading-error-priority-lookup.md): Prioritize between multiple columns/values by checking left-to-right, using nested IFERROR `=IFERROR(A2, IFERROR(B2, IFERROR(C2, "")))` to return first non-error value.

[datetime-formatting-with-text](wiki/patterns/datetime-formatting-with-text.md): Use TEXT function `=TEXT(datetime_value,"hh:mm:ss AM/PM")` instead of RIGHT() or string manipulation to properly format datetime values for display.

[delimited-data-parsing-aggregation](wiki/patterns/delimited-data-parsing-aggregation.md): Parse semicolon-separated values, lookup each individually, collect unique results, sort alphabetically, and join with comma-space; handles cases like "PRD1;PRD4;PRD5" → "Group 1, Group 2".

[prefix-based-filtering-pattern](wiki/patterns/prefix-based-filtering-pattern.md): Filter items based on starting prefix using LEFT(value,2)="PK" or character[0] checks; commonly used to include/exclude by code prefix (e.g., exclude X* and Z* prefixes).

[conditional-sequential-lookup](wiki/patterns/conditional-sequential-lookup.md): Return nth matching value from range based on condition using INDEX/SMALL/IF array formula `=INDEX(range,SMALL(IF(condition,ROW(range)-ROW(range)+1),n))`; requires Ctrl+Shift+Enter entry.

[type-filtering-and-reorganization](wiki/patterns/type-filtering-and-reorganization.md): Filter data by type (e.g., whole numbers only by checking value==int(value)), then reorganize into fixed-width rows (max items per row); more reliable when implemented via data processing than formulas.

[dynamic-column-finding-and-movement](wiki/patterns/dynamic-column-finding-and-movement.md): Find a column by header value (not hard-coded column letter), copy its data and formatting to a target location, then delete the original; enables handling of dynamic data structures where column positions change daily.

[multi-criteria-date-range-lookup](wiki/patterns/multi-criteria-date-range-lookup.md): Lookup values across multiple exact-match criteria (e.g., salesperson, type) combined with a date range check (start_date ≤ target_date ≤ end_date); return matching value or empty if no match found.

[formula-copy-reference-issues](wiki/patterns/formula-copy-reference-issues.md): When copying lookup formulas across rows/columns, distinguish between absolute and relative references; keep lookup criteria columns absolute ($B12 not $B$12) but row relative, and return values partially absolute (C2 not $C$2) so they update when formula copies down.
