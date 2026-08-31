# A Filter That Matches Zero Rows Means Your Predicate Is Wrong

**Type:** Failure pattern (validation discipline)

## Problem
The task names a literal value (`'Motorcycle'`, `'Canada'`, `'National TV'`). The agent writes `if cell.value == 'Motorcycle'`, gets zero hits, silently skips that requirement, and then "verifies" using the identical predicate — which trivially passes.

## Evidence (task 247-24, 0.000)
Selection pass printed no Motorcycle rows at all:
```
=== Identifying rows for operations ===
Insert after (Ahmed Sons): Row 2 ... Delete (Ahmed Sons + Canada): Row 7 ...
Rows to delete: [7, 8, 9]        # requirement #1 produced nothing
```
Verification pass, same predicate:
```
=== Checking deletion of 'Motorcycle' rows ===
✓ No 'Motorcycle' rows found (correctly handled)
```
The user explicitly asked to delete Motorcycle rows, so they exist — under a different spelling, case, trailing space, or as a substring (e.g. `'Motorcycle '`, `'MOTORCYCLE'`, `'Motorcycle Ltd'`). Note the same file has `'PORT MACQUARIE '` with a trailing space in the sibling task 194-19.

## Root cause
Exact `==` on uncleaned strings + a verification step that re-executes the selection logic instead of checking an independent invariant.

## Fix
1. Before filtering, print the domain: `print(sorted({repr(ws.cell(r,1).value) for r in range(2, ws.max_row+1)}))`.
2. Normalize both sides: `str(v).strip().lower() == 'motorcycle'`; fall back to `in` / `startswith` when the domain shows decorated values.
3. **Hard rule:** if a value the user named yields 0 matches, STOP and re-derive the predicate. Never report "none found (correctly handled)".
4. Verify with an independent invariant, not the same predicate: expected `final_rows == original_rows - deleted + 2*inserted`; print the actual before/after row counts and the deleted rows themselves.

## Iteration 4: this pattern's fix produced TWO score flips (0.000 → 1.000)
- **58484 (1.000, was 0.000 in iter 2):** the agent again wrote `if d_val == '5551234'` and its write loop produced nothing — every H cell came back `None`. Instead of shipping, it said *"I see the issue - no counts were found. Let me debug the logic more carefully"* and printed:
```
D5: value=12041234567, type=int, equals '5551234'? False
```
switched to `operator_id = 5551234` (int), re-ran, got the groups, and matched the pre-filled "Expected Result" oracle. Textbook recovery.
- **247-24 (1.000, was 0.000 twice):** instead of testing `== 'Motorcycle'` and reporting "none found (correctly handled)", it printed the DOMAIN first:
```
Unique companies and counts:
  Ahmed Sons: 13   Ali tyre: 14   Mehommod Cycle: 5   National TV: 14
Motorcycle rows (to delete): []
```
With the full domain visible, the empty result is *evidence* rather than a silent skip — there is genuinely no Motorcycle row (nearest is 'Mehommod Cycle'), the requirement is a no-op, and the rest of the transformation is safe to proceed with.

**Rule confirmed:** an empty result set is never a result — it is a signal to print `repr`/`type` of the raw column and the full domain. Do that *before* the write loop, not after.

## Iteration 8: the opposite failure — 247-24 FABRICATED a match (0.000, fifth failure)
Having apparently absorbed "zero matches means your predicate is wrong", this run picked the nearest-looking value in the domain and deleted rows the user never named:
```python
if company == 'Mehommod Cycle':   # Assuming this is 'Motorcycle'
    rows_to_delete.append(row_idx)
```
Five 'Mehommod Cycle' rows were deleted. The iteration-4 run that scored 1.000 printed the same domain (`Ahmed Sons / Ali tyre / Mehommod Cycle / National TV`) and concluded the requirement is a **verified no-op**.

**Decision rule after you print the domain.** An empty match set has exactly two legitimate resolutions:
1. *Representation difference on the SAME token* — case, whitespace, numeric-vs-string, a decorated superstring (`'Motorcycle '`, `'MOTORCYCLE'`, `'Motorcycle Ltd'`). Normalize and re-run.
2. *The value genuinely is not present* — no member of the domain contains the token. Then the requirement is a no-op: say so in prose, change nothing, and move on.

'Mehommod Cycle' and 'Motorcycle' share no token; `'motorcycle' in 'mehommod cycle'.lower()` is False. Never bridge that gap with a comment beginning "Assuming this is…". Deleting rows on a guess is unrecoverable — it is strictly worse than skipping the requirement.
```python
cands = [v for v in domain if 'motorcycle' in str(v).strip().lower()]
print('candidates:', cands)
assert cands or True, ''
if not cands: print("No company matches 'Motorcycle' -> requirement 1 is a no-op, no rows deleted")
```

