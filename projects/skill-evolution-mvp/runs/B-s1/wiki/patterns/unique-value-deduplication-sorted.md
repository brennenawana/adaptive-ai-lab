# Unique Value Collection, Deduplication, and Sorting

## Problem
Multiple input values map to multiple output categories. Need to return unique categories, sorted alphabetically/numerically, without duplicates. Example: three product codes map to Group 1, Group 2, Group 2 → should return "Group 1, Group 2" not "Group 1, Group 2, Group 2".

## Root Cause
Direct concatenation includes duplicates. Manual deduplication required.

## Solution
Use set data structure to collect unique values, then sort and join:

```python
groups_found = set()  # auto-deduplicates
for code in codes:
    group = lookup[code]
    groups_found.add(group)

sorted_groups = sorted(list(groups_found))  # sort alphabetically
result = ", ".join(sorted_groups)  # join with separator
```

## Process
1. Create empty set
2. For each input value:
   - Lookup or evaluate to get output category
   - Add to set (duplicates ignored automatically)
3. Convert set to sorted list
4. Join with separator (comma, semicolon, etc.)

## Example
Task 48745: Consolidate product codes to groups
- Input codes: "PRD1;PRD4;PRD5"
- Lookups: PRD1→Group 1, PRD4→Group 2, PRD5→Group 2
- Set collection: {"Group 1", "Group 2"} (PRD5 duplicate ignored)
- Sorted: ["Group 1", "Group 2"] (alphabetically)
- Result: "Group 1, Group 2"

## Key Points
- Sets automatically eliminate duplicates
- sorted() returns alphabetical order by default
- sorted(list, reverse=True) for descending order
- For numeric sorting: sorted([2, 10, 1]) = [1, 2, 10]
- Join separator can be ', ' (comma-space), ';', etc.

## Task 48745 Evidence
Task 48745 successfully validated this pattern:
- Input codes: "PRD1;PRD4;PRD5" (semicolon-separated)
- Split: ['PRD1', 'PRD4', 'PRD5']
- Lookup results: {PRD1→Group 1, PRD4→Group 2, PRD5→Group 2}
- Set collection: {'Group 1', 'Group 2'} (automatic deduplication)
- Sorted: ['Group 1', 'Group 2'] (alphabetically)
- Result: "Group 1, Group 2" (comma-separated)
- Additional validation: PRD1;PRD6 → {Group 1, Group 2}, PRD2;PRD1 → {Group 1} (correct dedup)
- Pattern confirmed: set-based deduplication eliminates duplicate 'Group 2' from multiple codes mapping to same group
