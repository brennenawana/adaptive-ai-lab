# Dump the WHOLE used range — the prompt's "attached example" is hiding in it

## Pattern (FAILURE) — task 370-43, 0.000
Prompt: "insert a row above every line where there is an 'X' in Column A (A7:A1000) ... **I have also
provided a sheet that shows what I am aiming for before and after the VBA is implemented.**"

The agent's inspection was:
```python
for row_num in range(1, min(21, ws.max_row + 1)):      # rows 1..20 only
    for col_num in range(1, 21):                        # cols A..T
```
printed `Dimensions: A1:T2483` in the same breath, and never looked again. The single sheet is named
`'Before Insert Row'` — the promised "after" reference block was never located, so the agent guessed
the target shape (3 blank rows inserted above rows 18/32/43) and shipped.

## Root cause
`ws.dimensions` was *printed* but not *used*. A truncated window (first N rows / first N cols) is a
habit carried over from small files; here 99% of the used range was never seen. Compare 48745 and
42354 (both 1.000), which dumped every non-empty cell with `repr()` before deciding anything.

## Fix — enumerate non-empty islands across the entire range, on every sheet
```python
for ws in wb:
    print('===', ws.title, ws.dimensions, ws.max_row, ws.max_column)
    for row in ws.iter_rows():                       # NO max_row/max_col cap
        vals = [(c.coordinate, c.value) for c in row if c.value not in (None, '')]
        if vals:
            print(vals)
```
If the output is huge, summarise instead of truncating: print the set of populated column letters
per row-band, and print every populated cell in columns *beyond* the main table — that is where
"this is what I need" blocks live (263-1's answer key sat in G1:I5, far right of a 276-row table;
408-39's header row was row 5, not row 1).

## Checklist when the prompt mentions an example
- "as shown in my attached example", "part of the answer is given", "before and after" ⇒ a concrete
  expected-output block exists. Find it and quote its coordinates back in your reasoning.
- Check `wb.sheetnames` for a second/hidden sheet (`ws.sheet_state == 'hidden'`) before concluding
  the example is missing.
- Once found, treat it as the spec: reproduce it exactly (preserve-prefilled-examples-in-answer-range.md)
  and unit-test your rule against it (validate-rule-against-worked-examples.md).
