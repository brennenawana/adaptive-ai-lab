# The Prompt's Own Worked Example Is the Oracle

**Type:** Success recipe + failure pattern (task comprehension)

## Pattern
Almost every one of these prompts contains at least one fully worked case: an input and the answer the user expects. Often it is the ONLY ground truth available (the file may have no pre-filled cells at all). Winners transcribe it into a `(input → expected)` assertion and run it before writing; losers paraphrase it, retarget it, or accept it without checking that it can distinguish their candidate rules.

## Iteration-7 evidence — three wins, three losses, one mechanism
**Wins**
- **39903 (1.000, third time):** the prompt says `A-01-A-02-C-04.D: 5 indicates one position` and `Z-07-C-05-A-02:9 … excluded`. The agent built a test table straight from those sentences and ran it *before* touching the sheet:
```python
test_cases = [("RECEIVING: 67",1), ("03-B-11-D-04: 9, X-18-D-03-A-03: 29",1),
              ("X-21-A-07-A-01: 197",0), ("Z-07-C-05-A-02: 9",0), (…,6)]
```
- **43589 (1.000):** "a range … such as '2 to 5' … which should count as 4 days". The intuitive `end-start` gives 3; the agent used the prompt's stated answer (`end-start+1 = 4`). **The user's stated result beats your arithmetic intuition.**
- **10452 (1.000):** the prompt walks through B4/B5/B6 skipping non-'PK' rows; the agent reproduced that walk and matched the pre-filled E4:E8 exactly before extending to E12.

**Losses**
- **10747 (0.000, regression from 1.000):** the prompt names the cells: "sum the net profit … based on the year and share no values in cells **I3 and J3**. It should be placed into cell **K6**." The agent wrote `=SUMIFS($C$3:$C$8,$A$3:$A$8,I6,$B$3:$B$8,J6)` — it *rewrote the refs to match the row it was pasting into*, and I6/J6 are empty, so the formula is 0 even in Excel. The expected answer (-10600) was already visible as the cached `K3`.
- **56786 (0.000, third failure):** the prompt quotes the user's own example formula `AVERAGE(B24:B69)`. That range **is** the window specification — it names the exact row set for one anchor row. The agent never located which row it belongs to and invented its own semantics.
- **6239 (0.000, third failure):** the prompt's only example is "Goal 65-74%, Variance 0-3%, Metric2 -20..-10% → 3%". The agent tested its additive reading `J3 + P3 = 0 + 0.03 = 0.03` and declared it confirmed — but `J3` is 0, so "P alone" gives 0.03 too. **A test that every candidate passes selects nothing.**

## Fix / checklist
1. Before coding, copy every example sentence out of the prompt as `inputs → expected` and turn it into asserts. Run them on your function first; only then touch the workbook.
2. **Use the exact cell references the prompt names.** If it says the criteria are I3/J3 and the target is K6, the criteria stay I3/J3 — do not "fix" them to the target's row.
3. If the prompt quotes a concrete range (`AVERAGE(B24:B69)`, `$A$2:$A$276`), reverse-engineer it: find the row/anchor it belongs to and assert your rule regenerates that exact set of rows. Print the boundary dates/values so the reconstruction is auditable.
4. **Check the example discriminates.** Evaluate ALL candidate readings on it; if two or more agree, it is not evidence — construct a second test (a row where the candidates differ) or use the table structure itself.
5. If the prompt states the numeric answer for a case, reproduce that number exactly, even if your own arithmetic disagrees (43589's inclusive day count).
6. The example is also the *format* spec — delimiters, column shape, blank vs zero. See replicate-completed-example-block when the example lives in the file rather than the prompt.

## Related
- When the example is a *block of cells in the file* rather than prompt text → replicate-completed-example-block.
- When the example exists but you never find it → contradicting-oracle-cells §Step 0 and hardcoded-range-truncation.
- When your candidates all pass/all fail the example → aggregate-match-is-not-verification.
