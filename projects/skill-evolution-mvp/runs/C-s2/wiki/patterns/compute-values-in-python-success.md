# Success pattern: do the transformation in Python, write literals

## Pattern
Every iteration-1 task that scored 1.0 shared the same shape: read -> compute in Python -> write concrete cell values / structural edits -> verify by re-reading values.

## Evidence (iteration 1, soft=1.0)
- **408-39** (move a column whose position varies): located the header dynamically instead of hardcoding.
  ```python
  for row in ws.iter_rows(min_row=1, max_row=5):
      for cell in row:
          if cell.value == '0-15':
              source_col = cell.column
  ```
  Copied values **and** style (`from copy import copy`; font/border/fill/number_format/protection/alignment) into column B, then `ws.delete_cols(source_col)`. Verified B9==2, B10==1.
- **66-24** (filter rows older than 30 days vs max date): computed `max(dates)`, `threshold = max_date - timedelta(days=30)`, copied header + matching rows into the target sheet, preserved `cell.number_format` for the date column, then `ws_target.delete_cols(26)` for column Z.
- **170-13** (expand entries by matching form headers): parsed form name with `re.search(r'(U4_\w*Form)', entry)`, joined each Sheet2 value, cleared Sheet3, wrote all 77 rows.

## Reusable recipe
1. Dump the sheet(s) fully first (`iter_rows(values_only=True)`) before assuming layout; headers are often not in row 1 (39931 starts row 3, 408-39 row 5).
2. Compute the answer in Python.
3. Write literal values; for moved/copied cells also `copy()` the style objects and `number_format`.
4. Use `ws.delete_cols(n)` / `insert_cols` for structural edits rather than VBA-style thinking.
5. Re-open the saved file and print the target cells' **values** as the final check.

## Iteration 2 evidence (soft=1.0): the extra ingredient is an anchor check
The three winners all had an *external ground truth* they explicitly reconciled with:
- **408-39**: instruction said "Column B should have the values 2 & 1". Agent ended with
  `assert vals == [None, None, None, 2, 1]` — a real assert, not narration.
- **48080**: sheet supplied `C2='=A25'`, `C3='=A41'` as the desired-results demo. Agent read those two formulas, inferred the every-16-rows pattern, and extended it to C4:C6 (87/45/6). It let the given examples define the rule.
- **42354**: the file already contained correct D2:D4 (`Completed`, date, `ENR`). Agent's first-non-#N/A rule reproduced them exactly and then filled D5:D8, including a deliberate blank at D8.

All three also made a **minimal diff** — only the requested cells changed.

## Updated recipe
1. `print(wb.sheetnames)` and dump every sheet.
2. Harvest all ground truth: pre-filled answer cells, demo formulas, numbers quoted in the instruction.
3. Implement the rule in Python; `assert` it reproduces every piece of ground truth. Revise the rule until it does.
4. Write literal values into the target range **only**; touch nothing else.
5. Reload with `data_only=True`, print targets, and re-diff against the input file.

## Iteration 3 evidence (soft=1.0): two former failures flipped to success
- **39931** (was 0.0 in iter 1 with `=SUMPRODUCT(...)`): built `lookup_dict[(key, header)] = value` from the I/J/K data block, wrote the 12 literals into C4:F6, reloaded with `data_only=True` and asserted no cell starts with `=`. 1.0.
- **10452** (was 0.0 in iter 1 with `=FILTER(...)`): `pk_values = [v for v in b_values if isinstance(v,str) and v.startswith('PK')]`, then one `ws[f'E{idx+4}'] = v` per result. 1.0.
- **48745**: built the G:H dict, split column C on `';'`, `sorted(set(groups))`, wrote `'Group 1, Group 2'`. Reproduced the three pre-filled cells D5:D7 exactly and extended to D8:D10. 1.0.

The shared shape across all three: **dict lookup built from the sheet -> one literal per target cell -> assert (no formulas, no None) on the reloaded file**. No structural edits, no formulas, minimal diff.

## Environment gotchas seen in traces
- `from openpyxl.styles import copy` -> `ImportError`. The correct import is `from copy import copy` (36097 burned three turns retrying the same broken line — after two identical errors, change the approach rather than the surrounding code).
- `soffice` is absent (exit 127); never plan a recalculation step.
- `print(f"{value:20}")` on a `None` cell raises `TypeError` and kills the whole verification script mid-run (247-24). Coerce with `str(v) if v is not None else 'BLANK'` in verification loops.

## Iteration 4 evidence (soft=1.0 x3): the recipe is now reproducible
- **39931** (1.0 in iter 3 and iter 4): identical solution both times — `lookup_table[(colI, colJ)] = colK` built from rows 4–22, then 12 literals into C4:F6, reload with `data_only=True`, print the values.
- **48745** (1.0 in iter 3 and iter 4): identical again — `lookup[G] = H`, `split(';')`, `sorted(set(groups))`, `", ".join(...)`, then a real assert pair:
  ```python
  assert all(v is not None for v in values)
  assert not any(isinstance(v, str) and v.startswith('=') for v in values)
  ```
- **58484** (0.0 in iter 2 -> 1.0 in iter 4): computed the consecutive-transfer counts in Python, wrote literals into H, **and** executed every formatting imperative in the prompt. See multi-requirement-instruction-checklist.md.

These three are stable repeats: for pure "read a lookup table, derive a per-row value, fill a target column" tasks the recipe works every time. The remaining failures are all in other categories — structural row edits (370-43), multi-axis rules (6239, 194-19), conflicting instruction clauses (22-47), and formula-authoring framing (50916).

## Pre-write checklist distilled from iterations 1–4
1. `print(wb.sheetnames)`; dump **every** sheet, including ones with non-Latin names.
2. List every input column/field the prompt names; your rule must read all of them.
3. Harvest ground truth: pre-filled answer cells, completed regions, reference sheets, numbers quoted in the prompt.
4. Split the prompt into one checklist item per imperative (including formatting).
5. Implement in Python; `assert` the rule reproduces every non-blank ground-truth cell.
6. Write literals into the target cells only; never a formula string; never touch a pre-filled cell.
7. Reload with `data_only=True`, print `cell.coordinate` + value, and end on an `assert`, not a ✓.

