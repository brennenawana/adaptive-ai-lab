# Evolution Log

## [iter 1] ## Iteration 1 (6 tasks graded, 3 scored 1.0, 4 scored 0.0)

Clear split found. All four 0.0 tasks (39931, 10452, 472-15, 55060, 50916) ended with the agent writing **Excel formula strings** into the output workbook via openpyxl. All three 1.0 tasks (408-39, 66-24, 170-13) ended with the agent writing **literal computed values** after doing the transformation in Python.

Root cause: openpyxl writes formulas as text only; it has no calculation engine, so the saved xlsx contains no cached result. Graders that read cell values (or `data_only=True`) get `None`. Task 39931's own trace proves this — the agent printed "Calculated values in range C4:F6: Row 4: ['None','None','None','None']" and still declared success. Task 10452 compounded this by relying on FILTER spill into E5:E12 which stayed empty.

Created 4 patterns: formula-written-but-no-cached-value, ignored-none-verification-signal, dynamic-array-spill-formula-misuse, compute-values-in-python-success. No skills were active this iteration; the highest-leverage skill candidate is "always materialize computed literal values, never rely on formula evaluation."

## [iter 2] ## Iteration 2 (8 tasks: 3 scored 1.0 — 42354, 48080, 408-39; 5 scored 0.0 — 370-43, 36097, 58484, 194-19, 6239)

Major shift: iteration-1's lesson landed. Every 0.0 task this round wrote **literal values, not formulas**, and several ran explicit "no formulas / no None" verification — yet still scored 0. So `formula-written-but-no-cached-value` is necessary but not sufficient.

New root cause #1 (dominant): **the computed rule contradicted ground truth already present in the file/prompt**. 36097 overwrote the given H3=5000 with its own 4000; 58484 emitted counts in rows the sheet's own "Expected Result" column showed blank; 6239 built a base+adjustment model that can never produce the 3% the instruction explicitly cited. All three winners did the opposite — 48080 derived its rule from the demo formulas C2='=A25'/C3='=A41', 42354 reproduced the pre-filled D2:D4, 408-39 asserted the instruction-stated `[None,None,None,2,1]`.

New root cause #2: **destructive edits**. 36097 converted column G's existing `=D3+F3` formulas to literals and replaced `=SUM(H3:H6)`; 58484 nulled all of column G and the expected-result column. Winners made minimal diffs.

New root cause #3: **never enumerated sheets / ignored the supplied before-after demo sheet** (370-43 went straight to `wb["Before Insert Row"]`; 194-19 never reconciled duplicate Track/Race rows against the already-completed first meet).

Environment fact recorded: `soffice` is absent (exit 127) — the LibreOffice recalculation workaround suggested in iteration 1 is unusable here.

Created 3 patterns (contradicting-provided-examples, destructive-overwrite-of-given-content, ignore-reference-and-sheet-structure); updated formula-written-but-no-cached-value and compute-values-in-python-success. Highest-leverage skill candidate now: "harvest every given example as a unit test, assert your rule reproduces all of them, then write only the target cells."

## [iter 3] ## Iteration 3 (8 tasks: 3 scored 1.0 — 48745, 10452, 39931; 5 scored 0.0 — 6239, 247-24, 370-43, 55060, 36097)

Strong confirmation signal: **10452 and 39931 both scored 0.0 in iteration 1 and 1.0 now**, doing exactly what the wiki prescribes — dump the sheet, build a Python dict lookup, write literal values into every target cell, reload with `data_only=True` and assert no formulas / no None. 48745 won the same way and added a new nuance: the prompt's abstract summary said outputs could be `BOTH`, but the row-by-row examples said "would return Group 1, Group 2", and the pre-filled D5:D7 agreed with the examples — the agent followed the examples and scored 1.0. Recorded as "concrete examples beat the abstract summary".

Regression: **55060** (a 0.0 in iteration 1 too) again wrote the formula string `=IF(I12="","",I12)` into J23, again tried `soffice` (exit 127), and "verified" by *simulating* the formula in prose ("J23 will display 'January'") rather than reading a computed value. I12 was known to be `January`; writing the literal was trivial. Root cause of the regression: the instruction is phrased as "how do I create a formula", which pulls the agent into formula-authoring mode. Added this framing explicitly to formula-written-but-no-cached-value and ignored-none-verification-signal.

Two genuinely new root causes:
1. **row-restructure-breaks-references** (new pattern). 370-43 and 247-24 both did structural row edits. 370-43 *did* print `wb.sheetnames` this time (only one sheet existed — the promised before/after demo was absent), so the old "never enumerated sheets" diagnosis is not the cause; the cause is that `insert_rows` shifts cells without translating formulas, without carrying styles, and without populating the new rows, in a sheet driven by `=IF(C6="","X","")`. 247-24 did `delete_rows(2, max_row)` then rewrote every row, copying formula *text* (`=G2*H2`, `=I2-K2`) into different row numbers so every relative reference became wrong, and dropping all formatting.
2. **misread-lookup-table-geometry** (new pattern). 6239 repeated its iteration-2 failure with the same invented `goal + metric2 − base` interpolation. Reverse-engineering the sheet shows J2:M2 are *goal* boundaries and J3:M6 are *variance thresholds per goal bucket*, while P2:T2 are metric2 boundaries and P3:T6 is the actual payout grid indexed by (variance bucket, metric2 bucket). That geometry reproduces both numbers quoted in the prompt exactly (P3 = 3%, T3 = 7%). The correct decoding is now written into the pattern page.

Also observed: 36097 wasted three turns on the same `from openpyxl.styles import copy` ImportError (correct import is `from copy import copy`) and its trace truncated mid-task; noted as a tooling gotcha in compute-values-in-python-success. 36097 also still emitted H3=4000 against the given H3=5000 — contradicting-provided-examples remains the single most repeated failure.

Created 2 patterns (row-restructure-breaks-references, misread-lookup-table-geometry); updated 6 existing pages. Highest-leverage skill candidate is unchanged and now doubly evidenced: "never write a formula string — compute and write the literal — and assert your rule reproduces every example the user gave you", plus a new second clause: "for structural edits, rebuild formulas for their new row numbers."

## [iter 4] ## Iteration 4 (8 tasks: 3 scored 1.0 — 58484, 39931, 48745; 5 scored 0.0 — 6239, 22-47, 50916, 370-43, 194-19)

**Stability signal:** the "dict lookup -> literal values -> assert on reloaded `data_only=True` file" recipe is now reliably reproducible. 39931 and 48745 both won again with byte-for-byte the same shape as iteration 3. Pure lookup-and-fill tasks are effectively solved.

**58484 flipped 0.0 -> 1.0, and it forces a correction to the wiki.** Iteration 2 diagnosed its failure as "contradicted the blank cells in the Expected Result column". That was wrong: the winning run *also* emitted values at rows 17/19/21/25 where the given column was blank, and still scored 1.0. The real differentiators were (a) it reproduced all five *non-blank* given values (H6=1, H9=2, H11=1, H13=1, H15=1) exactly, and (b) it executed every formatting imperative in the prompt — bold+bordered headers, wrap text on row 4, column G cleared of values *and* borders — instead of blanking H. Recorded as a correction on contradicting-provided-examples and as a new pattern multi-requirement-instruction-checklist.

**6239 (0.0 for the third straight iteration) changed approach and failed differently — the most instructive failure this round.** It abandoned the `goal + metric2 − base` summation (wiki lesson landed) and did a proper 2-D grid lookup... but indexed the payout grid rows by **Goal bucket** instead of **Variance bucket**, never reading column E ("Varince to Goal") at all, and never touching the J3:M6 variance-threshold table. Critically, its model *does* reproduce both examples quoted in the prompt (3% and 7%), because both examples sit in Goal bucket 0 / variance band 0 — the examples cannot discriminate the two readings. This is a genuinely new root cause: **an under-specified rule can pass every stated example while dropping an entire dimension**. New pattern: dropped-dimension-in-rule ("assert every input the prompt names is actually read by your code").

**194-19 (0.0 twice now)** has the same shape. The instruction says "I've completed results for the first meet", and rows 2–9 of Sheet1 held the answer key (Tab 7 -> blank, 14 -> 2, 12 -> 4, ... ). Decoding it: Sheet2's J,K,L,M hold *Tab numbers* and their column *position* is the rank; you write the rank into Sheet1 column I on the row whose Tab (Sheet1 col J) matches. The agent instead built `(track,race) -> first non-empty of J..M`, a single scalar per race, wrote that same constant into every row of the race, and overwrote the completed first meet. New pattern: partially-completed-region-is-the-spec.

**22-47 (new task, 0.0):** the workbook's second sheet `ورقة1` contains the expected output list, and F2:F11 was pre-filled with item numbers 1–10 defining the exact output height. The agent dumped both, then ignored both. It also oscillated across three turns between "order by helper column J" and "sort by REF lowest to highest" and finished by applying the latter globally, destroying the J-priority ordering the same sentence demanded. Evidence added to ignore-reference-and-sheet-structure and contradicting-provided-examples.

**50916 regression (0.0 in iter 1 and iter 4):** wrote `=INDEX($C$2:$C$8,MATCH(B12,$B$2:$B$8,0))` into all 18 cells of C12:H14, ran the dead `soffice` conversion (exit 127), and "verified" by printing the formula text next to a hand-computed `expected_value`. Its verification loop was itself mis-indexed (printed D12..H12 labels against C..G formulas, silently omitting C12) and it never noticed. Same trigger as 55060: the prompt is phrased as "I managed a formula that works in one cell but am struggling to copy it across".

**370-43 (0.0 three iterations running):** `insert_rows` again. New concrete evidence of openpyxl data loss — cell C18 held an empty string before the insert; after the shift and save, the reloaded C19 is `None`. The inserted rows are value-less and style-less.

Created 3 patterns (dropped-dimension-in-rule, partially-completed-region-is-the-spec, multi-requirement-instruction-checklist); updated 8 existing pages including a factual correction to contradicting-provided-examples. Highest-leverage skill candidate, updated: "compute literals, never write formula strings; reproduce every non-blank given value AND every completed region; assert that every input column the prompt names is actually read by your rule; treat each imperative sentence as a checklist item."
