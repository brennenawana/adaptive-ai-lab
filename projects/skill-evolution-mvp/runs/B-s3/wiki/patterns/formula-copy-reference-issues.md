# Formula Copy Reference Issues

## Problem
When copying a lookup formula from one cell to another (especially across rows and columns), the formula fails or returns wrong values. The issue: wrong mix of absolute ($) and relative references causes the formula to look at wrong source rows or columns when copied.

## Root Cause
Excel formulas use `$` to lock references:
- `$B$2` = fully absolute (never changes when copied)
- `B$2` = column relative, row absolute (column changes when copied right, row stays)
- `$B2` = column absolute, row relative (column stays, row changes when copied down)
- `B2` = fully relative (both change)

Common mistake: Using `$C$2` (fully absolute) for return values means formula always returns from row 2, even when copied to rows 3, 4, etc.

## Solution

### Lookup Criteria Column (always check current row's criteria)
```
$B12   ← Column B is absolute (always check B), row 12 is relative (updates when copied down: 12, 13, 14...)
```

### Return Value Column (must update row with formula)
```
C2     ← Column C is relative (updates C→D→E when copied right)
       ← Row 2 is relative (updates 2→3→4 when copied down)
```

## Example (Task 50916 - Formula Issue)
School calendar: Match cycle day and return corresponding class

**WRONG Formula (doesn't copy correctly):**
```excel
=IF(A$12=A$2,C$2,IF(A$12=A$3,C$3,...))
       ↑ Row 12    ↑ Row 2
Both absolute row - When copied to row 13, still checks row 12!
```

**CORRECT Formula (copies properly):**
```excel
=IF($B12=$B$2,C2,IF($B12=$B$3,C3,...))
   ↑ Col absolute  ↑ Fully absolute  ↑ Row relative
   Row relative    (lookup table)    Row relative
```

How it works when copied:
- **Copy RIGHT (D12, E12, H12):** Column C becomes D, E, H (good!), row stays 12 (good!)
- **Copy DOWN (C13, C14):** Row becomes 13, 14 (good!), column stays C (good!), and return values update to C3, C4 (correct!)

## Reference Pattern for Lookups

| Part | Pattern | Reason |
|------|---------|--------|
| Lookup criteria column | `$B12` | Always check column B, but row updates with formula |
| Lookup criteria range | `$B$2:$B$8` | Fully absolute - criteria table never moves |
| Return value column | `C2` | Column updates when copied right; row updates when copied down |

## Key Advantages
- Formula copies correctly across cells
- Returns update to match the lookup row
- Logic remains consistent throughout the range
- Easier to maintain and extend

## When to Use
- Lookup formulas that need to copy to multiple cells
- Cycle lookups, rate tables, priority lists
- Any INDEX/MATCH variant that copies across multiple rows/columns

## Common Mistakes to Avoid
1. Using `$C$2` for return values (row never updates)
2. Using `B12` for lookup criteria (column shifts when copied right)
3. Not using `$` on lookup table range (table position shifts)
4. Mixing absolute/relative inconsistently (confusing when debugging)

## Testing
Always test by:
1. Enter formula in one cell
2. Copy right and down
3. Verify: Criteria column is correct, return values match their row
4. Check a few cells manually to confirm logic is sound