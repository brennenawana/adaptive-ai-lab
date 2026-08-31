# Prove your filter/match predicate actually hits the rows you think it does

## Pattern (FAILURE) — task 247-24, 0.000 in both iter 3 and iter 4 for opposite reasons
Requirement 1: "Delete rows where the Company name in Column A is 'Motorcycle'".

| Iter | Predicate used | Rows matched | Outcome |
|---|---|---|---|
| 3 | `'Cycle' in company` | too many (also caught 'Mehommod Cycle') | wrong rows deleted |
| 4 | `company == 'Motorcycle'` | **0** — the deletion log prints only the three 'Ahmed Sons'+Canada rows | requirement silently skipped |

In neither run did the agent ever print the distinct values of column A. A requirement that
matches nothing produces no error, no exception and no visible symptom — the run "succeeds" and
scores 0.

## Root cause
The predicate is written from the *prompt's* wording rather than from the *file's* data. Whitespace,
case, 'Motor Cycle' vs 'Motorcycle', trailing spaces, ints-vs-strings in an ID column (247-24's
lookup keys are a mix of `1111` and `'C-21111'`) all break equality silently.

## Fix — enumerate, then assert a count
```python
from collections import Counter
print(Counter(ws.cell(r, 1).value for r in range(2, ws.max_row + 1)))   # every distinct value

hits = [r for r in range(2, ws.max_row+1) if ws.cell(r,1).value == 'Motorcycle']
assert hits, "predicate 'Motorcycle' matched 0 rows — check spelling/case/whitespace"
print(len(hits), 'rows will be deleted')
```
Do this for **every** clause of a multi-part instruction (delete A, delete A+B, set G=180 where
C+D, VLOOKUP on C) and print a per-clause hit count before mutating anything. If a clause's count
is 0, resolve it against the real values (`.strip()`, `.lower()`, substring) instead of moving on.

## Related
- Lookup joins: assert `set(main_keys) - set(lookup_keys) == set()` or log the misses; 247-24's key
  column mixes `int` and `str` IDs, so `lookup_dict[emp_id]` fails silently for the wrong type.
- validate-rule-against-worked-examples.md covers the value-computation side of the same discipline.
