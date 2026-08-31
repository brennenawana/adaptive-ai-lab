# Implement the ordering literally; write only the stated output columns

## Pattern (FAILURE) — task 22-47, 0.000
Instruction (compressed): names listed in J come first **in J's order**; *include all matching rows
and keep their original order from the source and do not sort within the group*; names not in J
*arranged as they are in the original data (same order)*; **output in columns G and H**.

What the agent coded:
```python
in_j_order.append(((j_order[name], ref), rec))     # ref = secondary key, never requested
not_in_j.append(((float('inf'), ref), rec))
in_j_order.sort(...); not_in_j.sort(...)
```
Result: every group was re-sorted by REF. The non-J rows came out
HASSONA, HUSSNI, HAMUDDA, HANA, HASSNA, MOHSION instead of their source order. The agent's own
final summary claimed "Preserved original order within each name group (no internal sorting)" —
the prose and the code disagreed, and only the code is graded.

It also wrote column **F**, which the init had pre-filled with the row counter 1,2,3,4,5..., replacing
it with source ITEM numbers (1,5,4,2,1,...). F was never named as an output column.

## Fixes
1. "Keep original order" = collect records in source order and use Python's **stable** sort with the
   group key only:
   ```python
   recs.sort(key=lambda r: j_order.get(r.name, len(j_list)))   # no tiebreaker
   ```
   Never add a secondary key the instruction did not ask for.
2. Turn every ordering clause of the prompt into an assertion on the final list before writing
   (e.g. `assert [r.name for r in out if r.name not in j_list] == source_order_names`).
3. Write only the columns named as output. If the prompt says "output in columns G and H", do not
   touch F even if it looks like part of the same table (see
   preserve-prefilled-examples-in-answer-range.md).
4. Contradictory clauses ("do not sort within the group" vs "sort only column H lowest to highest")
   should be resolved by whichever reading reproduces the pre-filled cells — not by silently
   applying both.
