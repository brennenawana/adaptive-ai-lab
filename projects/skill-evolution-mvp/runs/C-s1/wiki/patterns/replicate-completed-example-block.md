# Reverse-Engineer the User's Completed Sample Block Before Coding

**Type:** Failure pattern (task comprehension) / success recipe

## Problem
Multi-sheet "write me a macro" tasks usually ship with the first group already filled in by hand ("I've completed results for the first meet and uploaded a sample sheet for reference"). That block *is* the specification of the join. Skipping it leads to a plausible-looking but wrong mapping.

## Evidence (task 194-19, 0.000)
Sheet1 (372 rows, one row per runner) vs Sheet2 (one row per race, finishing order in J,K,L,M).
Completed sample, PORT MACQUARIE race 1 — Sheet2 row 2: `Top=(P), J=1, K=14, L=4, M=12`.
Sheet1: row 8 Tab=1 → Rank 1; row 3 Tab=14 → Rank 2; row 5 Tab=4 → Rank 3; row 4 Tab=12 → Rank 4; all rows H=`(P)`.
So the real rule is: **I (Rank) = the 1-based position of that row's Tab number within Sheet2's J:M for the matching (meet, race#); H = Sheet2 column I**, and non-placing rows stay blank.
The agent instead built `sheet2_data[(track, race)] = {J,K,L,M}` and never derived the Tab↔position join, never regenerated the completed block to check itself. It also treated the prompt's "more data to the right of column J" as fact after proving `max_column == 13`.

## Fix
1. Print the completed block side by side with its source rows and state the mapping in one sentence.
2. Implement, then **regenerate the already-completed rows** and assert a 100% match before writing any new rows.
3. Beware many-to-one joins: the sheet-level key ((meet, race#)) is rarely the whole key — look for a second, row-level key (here the Tab number).
4. When the prompt's claim about the data contradicts what you measured (`max_column`, extra columns), trust the file and say so; do not code speculative branches.
5. Blank means blank: leave non-matching rows `None`, do not backfill zeros.

## Iteration 4: 194-19 failed again (0.000) — this time it INVERTED the mapping
Same file, opposite mistake. The agent looked at the completed rows, saw `Row 3: Rank=2, Tab=14` and Sheet2 `K=14`, and concluded: "Column I currently shows Rank numbers but should show the result VALUES from J/K/L/M". It then wrote `sheet1.I = results_dict[rank]` — i.e. it used the sample's own answer as the *input* and overwrote the sample with Tab numbers (I3: 2 → 14). It also set H from Sheet2's Top for every row (that part is right) but destroyed I.

The missing guard is step 2 of this page, unchanged:
```python
# regenerate ONLY the rows the user already completed, from scratch
for r in completed_rows:
    assert computed[r] == original[r], (r, computed[r], original[r])
```
Running that on rows 2-8 fails on the first row and the whole interpretation collapses.

Also from this iteration: the agent scanned only `range(2, min(30, max_row))` for distinct meets and reported "Unique meets: ['PORT MACQUARIE']" for a 372-row sheet (see hardcoded-range-truncation), so it never tested its rule on a second meet.

## Prompt claims about the file must be reconciled, not assumed (370-43)
"I have also provided a sheet that shows what I am aiming for before and after the VBA is implemented" — but `wb.sheetnames` returned `['Before Insert Row']`: there is no "after" sheet. The agent printed that fact and moved on without comment. When the user references an example/reference artifact you cannot find, say so explicitly and search harder (other sheets, hidden sheets, a block further right/down) — the missing reference is usually where the grading criterion lives. Same class as 194-19's "more data to the right of column J" claim with `max_column == 13`.

## Iteration 7: the example can be on a sheet you are about to clear (170-13, 0.000)
"An example is provided where 'Sheet2 Header - U4_ComponentPropertyForm' has various associated data…" — the example was Sheet3's existing content. The agent dumped Sheet3 in the same command as Sheet1/Sheet2 (output truncated), never looked again, and deleted rows 2..max before writing. Consequences visible in its own verification output:
- the join key was guessed (`if form_name in entry`, first match wins over a dict — order-dependent);
- the output format was invented: one column of `f"{entry}+{value}"`, producing `…Sealing Method++u4_description` because Sheet1 entries already end with `+`;
- "cross-check" compared its output against itself (`out_val.startswith(entry)` for values it had just built) and reported `Match: True`.

**Checklist addition:** when the prompt says "an example is provided", locate it explicitly and print it *in its own command* before any transformation:
```python
for name in wb.sheetnames:
    ws = wb[name]; print(name, ws.dimensions, ws.max_row, ws.max_column)
    for r in ws.iter_rows(values_only=True):
        if any(v is not None for v in r): print(r)
```
Then state "the example maps X → Y" in one sentence, and reproduce those exact output rows byte-for-byte (delimiters included) before generating any new ones. A doubled separator, a stray space, or a shifted column in your output is proof you never diffed against the example.

## Iteration 8: 194-19 fails a FOURTH time — fourth different mapping, sample still never regenerated
This run got column H right (`H = Sheet2 column I`, the 'Top' marker) and invented a third wrong reading of column I: assign J, K, L, M by the **row-occurrence index** within each (meet, race#) group.
```python
occurrence_idx = meet_race_count[lookup_key]         # 0,1,2,3 in sheet order
i_value = sheet2_data['values'][occurrence_idx]      # J,K,L,M
```
Its own log is the refutation: `Row 2: Set I2 = 4`, `Row 3: Set I3 = 11`, `Row 4: Set I4 = 9` — while the author's completed sample holds I2 blank, I3=2, I4=4. It overwrote the sample instead of reproducing it.

**The correct rule, confirmed again from this trace's own dump** (Sheet2 row 2: `J=1, K=14, L=4, M=12`; Sheet1 rows: Tab 1→Rank 1, Tab 14→Rank 2, Tab 4→Rank 3, Tab 12→Rank 4):
```python
order = [J, K, L, M]                       # Sheet2 row for this (meet, race#)
I = order.index(tab) + 1 if tab in order else None   # rank = POSITION of this row's Tab
H = sheet2_I                                # the 'Top' marker
```
Every run of this task has failed at the same step — none of the four regenerated rows 2-15 and diffed them. The three-line guard that ends this task:
```python
for r in completed_rows:                    # rows the author already filled
    assert computed_I[r] == original_I[r], (r, computed_I[r], original_I[r])
```
Also note this run *did* check the prompt's claim about "more data to the right of column J" (`max_column == 13`, so the claim is false) and then said nothing about it — reconcile such contradictions out loud, because they usually mean you are looking at the wrong axis of the data.

