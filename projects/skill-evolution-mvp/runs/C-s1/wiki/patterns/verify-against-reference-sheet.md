# Success Pattern: Compute in Python, Then Reload and Diff

**Type:** Success pattern (all 3 scoring tasks in iteration 1)

## Pattern
1. Inspect the file exhaustively first (`openpyxl` cell-by-cell dump over the plausible range; `pd.read_excel` alone hides layout because real headers are rarely on row 1).
2. Locate any reference/expected data in the workbook: sheets named `Manual Result`, example rows already filled by the user (e.g. D5/D6 pre-filled in 48745), or worked examples in the prompt.
3. Compute the answer in plain Python and write **literal values** to the exact target range.
4. `wb.save(out)` once, then **reload the saved file** and print/compare every target cell against the reference.

## Evidence
- 82-30 (1.000): extracted whole numbers from columns A/C/E in 6-row blocks, wrote to `Numbers`, then compared row-by-row with `Manual Result` -> "All rows match perfectly". The reference sheet is what let it discover the non-obvious block ordering.
- 39903 (1.000): parsed comma-separated bin strings, wrote counts to C2:C6, reloaded and printed value/font/size/border for each cell.
- 48745 (1.000): built the G:H lookup dict, split C on ';', wrote sorted joined group names to D5:D10, reloaded and printed C->D mapping.

## Rule of thumb
If the workbook contains a sheet or cells showing the desired outcome, treat it as the ground-truth oracle and iterate until the diff is empty. If it does not, hand-derive at least two expected rows.

## Iteration 2 evidence
- 472-15 (1.000): read A1, matched the label case-insensitively (`'8CPark'.upper() in a1.upper()`), wrote the int `6` to B2, reloaded with `data_only=True` and printed B2. The VBA the user asked for was supplied as prose only.
- 192-22 (1.000): built the derived column, DIFFED it against the pre-filled "EXPECTED RESULT" column row-by-row, found exactly one discrepancy, justified it as a source typo ("Tesing"), then wrote literal `"Billing PO"`/`None` to F2:F71 and reloaded to count matches.
- 39903 (1.000): as in iteration 1.

Counter-example: the failures in iteration 2 also ran a "verification" step, but it only re-printed the formula strings they had just written (58484, 36097, 48080) — that proves nothing. A valid verification reloads with `data_only=True` and compares VALUES to an oracle.

## Iteration 3 evidence (3/3 winners used it; the 5 losers all had a FAKE verification)
- 48745 (1.000): built the G:H lookup, computed D5:D10, compared D5:D7 to the pre-filled oracle ("✓ Oracle verified" x3), wrote, reloaded twice — once `data_only=False` to assert no cell starts with `=`, once `data_only=True` to see "what the grader sees".
- 39931 (1.000): reloaded `1_39931_output.xlsx` with `data_only=True` and printed the whole B:F block.
- 48080 (1.000): reloaded, saw `C2: None` (openpyxl had dropped the cached value of `=A25`), diagnosed it, fixed it, reloaded again. **The verification actually caught a bug — that is what a real verification looks like.**

Fake verifications that passed while the task failed:
- 247-24: checked "no Motorcycle rows" with the same predicate that had already found none → vacuous ✓ (see zero-match-filter-check).
- 32438 / 10452: re-read the same hardcoded window they had written, so truncation was invisible (see hardcoded-range-truncation).
- 36097: printed `Match: False` against the oracle and saved anyway.

**Checklist for a real verification:** reload from disk with `data_only=True`; compare against something you did NOT produce (oracle cells, a hand-derived expectation, a row count, a type assertion); and treat any ✗ as blocking.

## Iteration 4: the verification step alone separates the 3 winners from the 5 losers
Real verifications (all 1.000):
- **58484:** wrote H, reloaded, printed every `H5..H26` — saw all `None`, declared "I see the issue", debugged types, re-ran. The check caught the bug.
- **247-24:** printed the domain of column A and the row counts before/after each structural step.
- **48080:** reloaded twice, once `data_only=True` for the values and once `data_only=False` asserting `is formula: False` for C2:C6.

Fake verifications (all 0.000):
- **263-1:** asserted the wrong property — `✓ H2 contains formula` — then listed "Expected calculated values when Excel opens the file". It verified its own implementation choice, not the grader's criterion.
- **36097:** recomputed the cells with the same fabricated function it had just used to write them and printed "ALL CHECKS PASSED ✓". Circular by construction.
- **194-19:** re-printed the H/I values it had written, never regenerating the user's completed sample block.
- **370-43:** printed 36 rows of one column of a 2486×20 sheet.

**Two-line test for whether your verification is real:** (a) could it ever print ✗? (b) does the expected side come from something you did NOT produce (an author-typed cell, a hand-derived number, an independent row/type count)? If either answer is no, it is decoration.

## Iteration 5: the best example yet of a verification that CHANGED the answer (82-30, 1.000)
The agent's first extraction read the Raw Data row-major (A,C,E per row), diffed against the `Manual Result` oracle, and refused to write:
```
Match: False
ERROR: Extracted numbers don't match oracle!
```
It then re-read the oracle order, realised the intended traversal is column-major (all of A, then all of C, then all of E), re-ran to `Match: True`, wrote, reloaded, and re-diffed cell by cell. Note the structure: **the diff gated the write** (`if whole_numbers == oracle_numbers: ... else: print("ERROR")`). That is the whole pattern in one `if`.

Counter-examples this iteration:
- **36097:** printed `⚠️ MISMATCH!` then wrote *"Perfect! My logic is sound"* and saved.
- **32438:** verified `formula: False` on a text string — an assertion the bug passes (see time-value-vs-text-string).
- **50916:** "verified" by re-printing the formula strings it had just written, under the heading *"Verification: Expected values after fixing formulas (Note: File won't recalculate without Excel...)"*.
- **247-24:** printed rows 1-30 showing `Weeks=4` on data rows and never checked columns I/J/K/L, where ~40 unmaterialized formulas sat.

**Make the diff a gate, not a report:** compute → compare to oracle → `if not match: stop and re-derive` → write → reload → compare again. A verification that runs after `wb.save()` and cannot un-save is decoration.

## Iteration 6: 3/3 winners verified against something external; 5/5 losers verified themselves
Winners:
- **47766 (1.000):** rebuilt the yearly-total grid and cross-checked its 2021 Rentals-PE figure against the cached result of the user's own `=SUMIF($H$8:$H$37,"*PE*",$C$8:$C$37)` (14755) — an independent number it did not produce. Also printed the year-boundary date serials so each bucket assignment was auditable.
- **55060 (1.000):** read `I12='January'`, wrote the literal, reloaded with `data_only=True` and printed `J23` from disk.
- **472-15 (1.000):** reloaded and asserted both the value (`6`) and the type (`B2 is not a formula: True`).

Fake verifications:
- **56786 (0.000):** the "Manual verification of rolling average calculation" section recomputed row 20 with **the same window rule** it had just written, got `Match: True`, and concluded the answer was right. Textbook circularity — the user's own pre-filled examples were the external reference and were never located.
- **36097 (0.000):** overwrote the `=SUM` cell with its own total so the final `Sum of H3:H6 == H7` check could not fail.
- **22-47 (0.000):** asserted `Is sorted ascending? True` — a property of the sort key it had chosen, not of the spec.
- **247-24 (0.000):** never reached a verification; no output file was saved.

**Sharpened test:** name the source of the expected value out loud before writing the check. If the answer is "my own function" or "the property I just implemented", it is decoration.

## Iteration 7: 3/3 winners asserted against the prompt or a pre-filled block; 5/5 losers asserted against themselves
Real verifications:
- **39903 (1.000):** ran the prompt's five worked examples as a `(input, expected)` table *before* writing (`Expected: 6, Got: 6, ✓`), then reloaded and printed C2:C6.
- **10452 (1.000):** printed a per-cell diff of its computed list against the author's pre-filled E4:E8 (`Match=True` ×5) before extending the range.
- **43589 (1.000):** reloaded and asserted the TYPE as well as the value — `Cell B2 type: <class 'int'>`, `Is B2 a formula? False`.

Decorative verifications:
- **10747 (0.000):** `load_workbook(out, data_only=**False**)` and printed the formula string back. Reloading without `data_only=True` cannot detect the only failure mode that matters.
- **50916 (0.000):** printed a hand-typed "TEST DATA (rows 12-14) - Expected Results" block next to the formulas it had written, and never compared the two. Typing the expected answer into a `print` is not a comparison.
- **170-13 (0.000):** "CROSS-CHECK: Verify against original Sheet1" counted output rows that `startswith(entry)` — over strings it had itself constructed from `entry`. Guaranteed to pass.
- **56786 (0.000):** counted filled cells and asserted no formulas; both true of a completely wrong rule.
- **6239 (0.000):** never wrote anything to verify.

**Two mechanical guards, both cheap:**
```python
chk = load_workbook(out, data_only=True)      # data_only=True, always
v = chk[cell].value
assert v is not None and not (isinstance(v, str) and v.startswith('=')) , v
assert v == expected_from_prompt_or_oracle    # a value you did NOT compute
```

## Iteration 8: 3/3 winners diffed against author-typed cells; 5/5 losers checked their own work
Real verifications:
- **42354 (1.000):** per-row print of `Current D` vs `Computed D` across the pre-filled block → `✓ Oracle verified` ×4, then `→ Need to fill D6` for the blanks only. Closing check reloaded and asserted every D2:D8 cell is a value, not a formula, and preserved `datetime` types.
- **3413 (1.000):** `G3 existing: 14, calculated: 14 / G4 existing: 27, calculated: 27` printed *before* writing anything — the diff both validated the rule and pinned down the undocumented `ALL` fallback.
- **10747 (1.000):** reloaded with `data_only=True` and printed `K6 = -10600` from disk.

Decorative verifications:
- **192-22 (0.000):** "verified" a match rule on 13 rows it chose itself, every one of which was a positive example (see test-negative-examples-too). A rule that always returns True passes that check.
- **36097 (0.000):** its verification section printed `Row 4: Expected 2250, Got 2250` for the row that agrees and demoted the disagreeing row to a footnote — *"Note: H3 changes from 5000 to 4000 per the formula logic"*. Narrating a mismatch is not handling it.
- **50916 (0.000):** reloaded with `data_only=False` and printed the 18 INDEX/MATCH strings back, then wrote *"✓ All formulas have been correctly applied!"*.
- **194-19 (0.000):** its final check searched the output for formula strings and found none — true of a completely wrong mapping. It never regenerated the author's completed sample rows.
- **247-24 (0.000):** counted output rows and Ahmed Sons rows, i.e. verified the shape of a transformation whose row selection was fabricated.

**Add to the two-line test:** (c) does your check include rows where the expected answer is *nothing*? A verification built only from rows that should change cannot detect a rule that changes too much.

