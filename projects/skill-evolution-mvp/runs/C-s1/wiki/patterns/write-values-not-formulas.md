# Write Computed Values, Not Formula Strings

**Type:** Failure pattern (highest impact observed)

## Problem
Every iteration-1 task that scored 0.000 ended with openpyxl writing a *formula string* into the target cells. Every task that scored 1.000 wrote *literal computed values*.

## Root cause
`ws['C4'] = '=SUMPRODUCT(...)'` stores only the formula text in the xlsx. Excel/LibreOffice compute the value lazily on open; openpyxl never does. A grader that loads with `data_only=True` (or reads values) gets `None` for every such cell -> score 0. The agent's own verification loop re-printed the formula text and mistook that for success.

## Evidence (traces)
- 39931: `=SUMPRODUCT(($I$4:$I$22=$B4)*($J$4:$J$22=C$3)*$K$4:$K$22)` into C4:F6 -> 0.000 (the agent even printed the correct expected numbers 23.56/25.56/... but never wrote them).
- 10452: `=IFERROR(INDEX(...SMALL(IF(LEFT(...)...))))` into E4:E12 -> 0.000 (it printed the correct PK list from column B but wrote formulas).
- 56786: `=AVERAGEIFS($B$4:$B$1000,...)` into C4:C200 -> 0.000.
- 32438: `=MOD(I2,1)` + `number_format='h:mm:ss AM/PM'` -> 0.000.
- 82-30 / 39903 / 48745: pure Python computation, literal values written -> 1.000.

## Fix
1. Do the lookup/filter/aggregation in Python (pandas/openpyxl) and write the **result**:
   `ws['C4'] = 23.56` / `ws['E4'] = 'PK01/P819760979'`.
2. Match the expected type: numbers as `int`/`float` (not strings), datetimes as `datetime`, blanks as `None` (not `""`).
3. If the task explicitly asks for a *live formula*, write the formula AND materialize values: run `soffice --headless --convert-to xlsx --outdir . out.xlsx` to force recalculation, or write values in the cells and put the formula text in a note/adjacent cell.
4. Verify with `openpyxl.load_workbook(out, data_only=True)` and assert the target cells are non-None.

## Iteration 2 evidence (pattern reproduced exactly, 4 more zeros)
- 10747: wrote `=SUMIFS(C$3:C$8,A$3:A$8,I3,B$3:B$8,J3)` into K6 -> 0.000. It had ALREADY computed the answer (-10600) and printed it.
- 58484: nested `=IF(AND(D5="5551234",...),SUMPRODUCT(...),"")` down H5:H26 -> 0.000.
- 36097: `=IF(F3<0,E3-F3,IF(F3<C3,F3,C3-E3))` in H3:H6 -> 0.000 (it printed 4000/2250/800/350).
- 48080: `=INDEX($A:$A,ROW()*16-7)` in C2:C6 -> 0.000 (it printed 14/17/87/45/6).
- 39903 / 472-15 / 192-22 wrote literals (counts, `6`, `"Billing PO"`) -> 1.000.

## "Explain the formula" tasks still need VALUES
10747 ("where have I gone wrong with the formula?") and 48080 ("I've tried OFFSET but haven't succeeded") read like explanation requests. The grader still reads cell values. DO BOTH: write the literal computed result into the requested cell(s) and explain/quote the corrected formula in your prose answer (or an adjacent non-graded cell).

## Note
The usual escape hatch — write the formula then recalc with LibreOffice — is unavailable here; see no-libreoffice-recalc-available.

## Iteration 3: RESOLVED (skill active) — but not sufficient
With the write-literal-values skill active, **no task left a formula string in a target cell**. Two chronic failures flipped to 1.000:
- 39931 (was 0.000 with `=SUMPRODUCT(...)`): built a `(key1,key2) -> value` dict and wrote 23.56/25.56/42.1/... into C4:F6.
- 48080 (was 0.000 with `=INDEX($A:$A,ROW()*16-7)`): wrote 87/45/6 into C4:C6 AND noticed openpyxl had dropped the cached values of the pre-existing `=A25`/`=A41`, re-reading them with `data_only=True` from the init file and rewriting C2=14, C3=17 as literals. **Rule: when you round-trip a file through openpyxl, any pre-existing formula cell loses its cached value — re-materialize those cells from a `data_only=True` load of the ORIGINAL.**
- 10452 (was 0.000 with the CSE array formula): correctly wrote the literal PK list this time, and still scored 0.000 — for a different reason (truncated scan window, see hardcoded-range-truncation).

The five iteration-3 zeros all wrote literals. Literal values are necessary but not sufficient; the remaining causes are coverage (hardcoded-range-truncation), value TYPE (time-value-vs-text-string), predicate correctness (zero-match-filter-check), and ignoring the oracle (contradicting-oracle-cells).

## Iteration 4: REGRESSED once — trigger word "dynamic" (263-1, 0.000)
With no skill guidance about framing, 263-1 recomputed the right totals, printed them, and then wrote `=SUMPRODUCT((($A$2:$A$276)=G2)*($B$2:$B$276)*($C$2:$C$276))` into H2:H5 because the prompt said "please make this sheet dynamic" and mentioned Power Query + VBA. It also overwrote the two pre-filled oracle values (H3=1660, H4=2753) with formulas "for consistency".

The verification is the tell — it asserted the WRONG property:
```
Verifying that formulas are in place (not just values):
✓ H2 contains formula: =SUMPRODUCT(...)
```
A correct check asserts the opposite. Standard closing check for every task:
```python
chk = load_workbook(out, data_only=True)
v = chk[f'H{r}'].value
assert v is not None and not (isinstance(v, str) and v.startswith('=')), (r, v)
```
The other seven iteration-4 tasks all wrote literals; the three winners (48080, 58484, 247-24) all ran a value-based reload check. See macro-vba-dynamic-requests for the framing trap.

## Iteration 5: failed again on a "help me copy this formula across" task (50916, 0.000)
Prompt: *"I managed a formula that works in one cell but am struggling to copy it across other cells as shown by the problems in C12, E12:H12, and D13:D14."* The agent diagnosed the reference bug perfectly (`B$12` should be `$B12` so it survives a copy right AND down) and then wrote 18 formula STRINGS:
```python
formula = f'=IF($B{row}=$B$2,{col}$2,IF($B{row}=$B$3,{col}$3, ... ))'
wsf[f'{col}{row}'].value = formula
```
and narrated the failure itself: *"(Note: File won't recalculate without Excel, but formulas are correct)"*. That sentence is the tell — if you have to say the file won't recalculate, the grader sees `None`.

Worse, it *destroyed* three correct answers: D12/F12/H12 already held cached `French`/`Science`/`Social Studies` from the user's working formula; overwriting them with new strings made them `None` (see formula-cell-cached-value-loss).

The data was tiny and fully visible: rows 2-8 are the 7-day cycle (day → H1,P1..P5), rows 12-14 have cycle days 1,2,3 in column B. The whole answer is a dict lookup:
```python
cycle = {wsv.cell(r,2).value: [wsv.cell(r,c).value for c in range(3,9)] for r in range(2,9)}
for r in (12,13,14):
    for i, c in enumerate(range(3,9)):
        ws.cell(r,c).value = cycle[ws.cell(r,2).value][i]
```
**Rule:** "my formula won't copy across" = write the correct values into every named cell, and give the corrected `$`-anchored formula in prose. Both, always.

## Iteration 6: 56786 flipped from formulas to literals — and still scored 0.000
In iteration 1 this task failed by writing `=AVERAGEIFS(...)` down C4:C200. In iteration 6 it wrote 197 literal floats, asserted `✓ No formulas found - all cells contain literal values`, and still scored 0.000 because the *rule* was unverified: the user's pre-filled example rows (the ones that define whether the 365-day window is inclusive, and whether it is anchored on the row's date or on a fixed block like the quoted `AVERAGE(B24:B69)`) were never located — the search window stopped at row 30.
This is the cleanest reminder available that the "no formula strings" assertion is a *floor*, not a finish line. After it passes, you still owe: full-range coverage, correct value TYPE, a predicate that matches something, and a diff against an author-typed cell.

## Iteration 7: a SOLVED task regressed — 10747, 1.000 (iter 5) → 0.000
Same file, same prompt ("could you help me understand where I've gone wrong with the formula?"). Iteration 5 wrote the literal `-10600` into K6 and scored 1.000. Iteration 7:
```python
ws['K6'] = '=SUMIFS($C$3:$C$8,$A$3:$A$8,I6,$B$3:$B$8,J6)'
wb.save('1_10747_output.xlsx')
# "verification": load_workbook(..., data_only=False) -> prints the formula back
```
Three things make this the clearest possible restatement of the pattern:
1. The agent's OWN first dump already contained the answer — `K3: -10600` (the cached value of `=+C4`) — and it still wrote a formula.
2. Its verification reloaded with `data_only=**False**` and printed the formula string. That check can only ever confirm the bug (see verify-against-reference-sheet).
3. The formula it wrote is broken even in Excel: the prompt says the criteria are `I3` and `J3`, the agent rewrote them as `I6`/`J6` (empty cells) because K6 is on row 6 → result 0. See prompt-example-as-oracle.

**Rule:** a diagnosis is not a deliverable. The moment you can print the right number, write it into the cell the prompt names; the corrected formula goes in the prose answer.

## Iteration 7: 50916 fails a third time, and the formula it wrote is itself un-copyable
The generated strings anchored the lookup key absolutely on row 12 for every output row:
```python
formula = f"=IF($B${row_num}=$B$2,{col}$2, ... )"   # row_num interpolated, but written as $B$13/$B$14 — still fully absolute
```
The first attempt was also malformed (a duplicated `IF($B$12=$B$8,...)` branch and nine closing parens). Both attempts left 18 formula strings and overwrote the three cells whose cached values were already CORRECT (`D12='French'`, `F12='Science'`, `H12='Social Studies'`). The whole task is a 7-row dict lookup; the agent even printed the expected answers ("Row 13: Homeroom, RE, Art, PE, Social Studies, Math") in prose and wrote none of them.

## Iteration 8: 50916 fails a FOURTH time — it printed the entire answer table, then wrote formulas
This is the purest form of the pattern in the corpus. In one command the agent produced the complete correct output:
```
Row 12 (B12=1, day 1):  C12 should be: Homeroom   D12: French   E12: Math   F12: Science   G12: Eng. Lang. Arts   H12: Social Studies
Row 13 (B13=2, day 2):  Homeroom  RE  Art  PE  Social Studies  Math
Row 14 (B14=3, day 3):  Homeroom  French  Science  Math  RE  Eng. Lang. Arts
```
and in the very next lines wrote 18 formula strings over those exact cells:
```python
ws['C12'] = '=INDEX($C$2:$C$8,MATCH($B12,$B$2:$B$8,0))'   # ... ×18
```
The formulas are *correct Excel* — INDEX/MATCH is a better answer than the user's nested IF — and they score 0.000, because openpyxl stores no cached value. It also destroyed the three cells (D12/F12/H12) that already held correct cached results, and "verified" by reloading with `data_only=False` and printing the formulas back.

**The gap to close is one line long.** The moment your program prints `X should be: Y`, the next statement must be `ws[X] = Y`. If your final message contains a formula and your target cells contain strings starting with `=`, you have written a tutorial, not a spreadsheet. The corrected INDEX/MATCH goes in the prose answer.

