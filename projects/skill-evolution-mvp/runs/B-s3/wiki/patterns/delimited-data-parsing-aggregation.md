# Delimited Data Parsing and Aggregation

## Problem
Single cells contain multiple delimited values (e.g., "PRD1;PRD4;PRD6") that each need individual lookup. Result should show unique values from lookup, sorted, and aggregated into single cell (e.g., "Group 1, Group 2").

## Root Cause
Excel formulas can't easily parse delimited data, perform individual lookups, and aggregate unique sorted results. Better handled via data processing.

## Solution
1. Parse by delimiter (split string)
2. Clean/trim each value
3. Lookup each value individually in reference table
4. Collect results into set (automatically unique)
5. Sort results alphabetically
6. Join with comma-space separator

## Example (Task 48745 - PASSING)
Looking up product codes in semicolon-delimited cell against lookup table (columns G:H):

Input: C9 = "PRD1;PRD4;PRD5"
Lookup table:
- PRD1 → Group 1
- PRD4 → Group 2
- PRD5 → Group 2

Process:
1. Split "PRD1;PRD4;PRD5" → ["PRD1", "PRD4", "PRD5"]
2. Lookup each:
   - PRD1 → Group 1
   - PRD4 → Group 2
   - PRD5 → Group 2
3. Unique groups: {Group 1, Group 2}
4. Sort: ["Group 1", "Group 2"]
5. Join: "Group 1, Group 2"

Output: D9 = "Group 1, Group 2"

## Special Cases
- Single product with trailing delimiter: "PRD1;" → parse to "PRD1"
- Multiple from same group: "PRD2;PRD1" → "Group 1" (unique aggregation)
- Multiple from different groups: "PRD1;PRD6" → "Group 1, Group 2" (sorted)

## Key Advantages
- Handles multi-value cells elegantly
- Results naturally sorted and deduplicated
- Scalable to any delimiter and lookup table

## Implementation Note
This pattern is reliably implemented via data processing (Python/VBA) rather than pure formulas, as shown by Task 48745 passing score of 1.0.

## Iteration 3 Update (Task 48745 - CONFIRMED PASSING)
Task 48745 executed this exact pattern with score 1.0:
- Input: C5:C10 with semicolon-separated product codes ("PRD1;", "PRD2;PRD1", etc.)
- Lookup table: Columns G:H (PRD1→Group 1, PRD2→Group 1, PRD4→Group 2, etc.)
- Process: Split by semicolon, lookup each code individually, collect unique groups, sort, join with ", "
- Output (Column D):
  - Row 5: "PRD1;" → "Group 1" ✓
  - Row 6: "PRD2;PRD1" → "Group 1" ✓
  - Row 7: "PRD4;" → "Group 2" ✓
  - Row 8: "PRD5;PRD6" → "Group 2" ✓
  - Row 9: "PRD1;PRD4;PRD5" → "Group 1, Group 2" ✓
  - Row 10: "PRD1;PRD6" → "Group 1, Group 2" ✓

Confirmed reliable when implemented via Python data processing with explicit group deduplication.
