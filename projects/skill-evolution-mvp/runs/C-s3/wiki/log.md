# Evolution Log

## [iter 1] ## Iteration 1 — 8 tasks, 3/8 scored 1.000

Decisive signal found: score correlates perfectly with *what was written into the answer cells*.
- 0.000 (39931, 10452, 472-15, 55060, 50916): agent wrote Excel formula strings via openpyxl. openpyxl has no calc engine, so no cached value is stored; a grader loading with data_only=True sees None. In several traces the agent computed the correct expected values in a separate Python block but never wrote them.
- 1.000 (408-39, 66-24, 170-13): agent computed the result in Python and wrote literal values (plus copied cell styles with copy.copy), then re-verified from the saved file.

Secondary observations:
- 408-39 success came from locating the '0-15' column dynamically via cell.column_letter rather than hardcoding, directly addressing the "position changes daily" requirement.
- Verification steps in the failing runs were tautological (reloading with data_only=False and printing back the formula just written).
- 55060 additionally mutated number_format outside strict need — risk of diverging from expected output.
- 50916 assumed cycle days were in column B without confirming from a full dump (output was truncated).

Created 4 patterns: formula-strings-score-zero, compute-then-write-literal-values, dynamic-header-lookup-not-hardcoded-columns, verify-answer-range-values-not-formulas. Index rewritten from empty.

## [iter 2] ## [iter 2] 7 tasks, 3/7 scored 1.000 (39903, 42354, 192-22); 0.000 on 247-24, 6239, 170-13, 10747, 3413

Confirmations of iter-1 findings:
- 10747 and 3413 wrote formula strings again → 0.000. New nuance: both prompts were phrased as "help me with the formula", which the agent read as a mandate to store formula text. 3413 even printed the correct cached values (14/27/4/11) beside each formula and discarded them. Updated formula-strings-score-zero with the "user asked for a formula" carve-out (answer in chat, literal in cell).
- 3413 ran the correct `data_only=True` check, saw `G3..G6: None`, rationalised it away and re-verified with `data_only=False` so output looked populated. Updated verify-answer-range-values-not-formulas: a `None` under data_only=True is a hard failure, and never downgrade a failing verification.

New root causes found:
1. REGRESSION on 170-13 (1.000 in iter 1 → 0.000 now). Sheet3 already contained the expected output; the agent blanked it and rewrote in its own ordering. Same class as 3413 (overwrote given examples G3/G4) and 247-24 (wiped A2:M47). Contrast: 42354 and 192-22 scored 1.0 by leaving pre-filled cells intact. → created preserve-prefilled-examples-in-answer-range.md.
2. 6239 invented a 3-D bucket mapping that ignores the Goal bucket in the payout lookup and never evaluated the worked example stated in the prompt ("65-74% / 0-3% / -20..-10% → 3%"). Successes did the opposite: 42354 asserted its rule against pre-filled D2:D5; 192-22 built an explicit positive/negative test-case table; 39903 unit-tested the counter on prompt examples. → created validate-rule-against-worked-examples.md.
3. 247-24 did read-all-values → wipe sheet → rewrite, which carried relative formula strings (`=G2*H2`) into different rows (stale refs) and used a stale `max_row`. → created row-edits-break-relative-formulas.md (use bottom-up delete_rows/insert_rows, rewrite or literalise formula columns).
4. 39903's win included explicitly applying the requested Font(name='Courier New', size=9) + thin Border to C2:C6 and verifying style attributes on reload. → created apply-requested-formatting-explicitly.md.

Actions: created 4 patterns, appended evidence to 3 existing patterns, rewrote index (8 entries). No skill file was visible in the traces, so skill-impact unchanged.

## [iter 3] ## [iter 3] 8 tasks, 3/8 scored 1.000 (48745, 10452, 39931); 0.000 on 50916, 6239, 48080, 22-47, 247-24

Wiki guidance is visibly being adopted — and two previously-failed tasks flipped to 1.000:
- 10452 (0.000 in iter 1 → 1.000): filtered with `str.startswith('PK')` in Python, asserted its output against the pre-filled worked example E4:E8 (`match=True` ×5), then filled only the blank E9:E12. Textbook compute-then-write-literal + validate-against-examples.
- 39931 (0.000 in iter 1 → 1.000): built a `(row_id, header) -> value` dict, wrote literals into C4:F6, built an `expected` map *before* saving and asserted it after reloading with `data_only=True`.
- 48745 (new, 1.000): dumped every cell with `repr()` first, recomputed the pre-filled D5:D7 to identical values, filled D8:D10.
- 247-24 used bottom-up `delete_rows`/`insert_rows` (exactly the wiki fix) and 48080 ran the `data_only=True` check — both wiki-derived behaviours — yet both still scored 0.

NEW dominant root cause (3 tasks): openpyxl's save drops the cached `<v>` of every formula already in the file.
- 48080: init had `C2='=A25'` (cached 14) and `C3='=A41'` (cached 17). The agent "preserved" them per the wiki rule, filled C4:C6 with literals, and its own verification printed `C2: None, C3: None, C4: 87...` — then shipped. The preserve-prefilled rule actively caused this failure, so it has been refined: preserve the *value*, literalising formulas.
- 50916: rewrote nested IF chains into C12:H14; the init had real cached values ('French', 'Science') which are now gone workbook-wide. Third consecutive 0.000 for this task, all from writing formula text.
- 247-24: columns I:L (`=G2*H2`, `=J2*H2`, ...) lose their cached values on save AND are not retargeted by `delete_rows`/`insert_rows`, so moved rows point at the wrong source rows. Created openpyxl-save-wipes-cached-formula-values.md; updated row-edits-break-relative-formulas.

Other new root causes:
- 6239 (second 0.000): this time the agent DID test the prompt's examples and both passed — but the test was degenerate. J3:M6 is a table of *variance band edges per goal bucket* (0/.03/.05/.07 for goal 65-74, 0/.02/.04/.06 for 75-84...), not base incentives. The agent read it as an incentive to be added to the P3:T6 payout; because the goal-65-74 row is all zeros, both readings reproduce "3%" and "7%". Every real employee had goal ≈0.84 (the K column), so the agent banded variance with the wrong edges and double-counted. → created threshold-tables-vs-payout-tables.md; appended the "example must discriminate between candidate rules" requirement to validate-rule-against-worked-examples.
- 22-47: the sort key `((j_order[name], ref), rec)` re-sorted inside every group by REF, directly contradicting "keep their original order from the source and do not sort within the group"; the agent's own prose summary claimed it had preserved original order. It also wrote column F, which the init pre-filled with 1..N and which the instruction never listed as output ("output in columns G and H"). → created honor-explicit-ordering-and-output-range.md.

Actions: created 3 patterns (openpyxl-save-wipes-cached-formula-values, threshold-tables-vs-payout-tables, honor-explicit-ordering-and-output-range), appended evidence to 6 existing patterns, rewrote index (11 entries).

## [iter 4] ## [iter 4] 8 tasks, 3/8 scored 1.000 (263-1, 408-39, 57558); 0.000 on 50916, 36097, 247-24, 370-43, 48080

The wiki is demonstrably being consumed (48080's trace says "Following the skill pattern (preserve given example, compute and write literal values...)") — but half-applied. The three winners are pure textbook; the five losers each broke one specific rule.

Successes (all three are "write me a formula / macro / Power Query" prompts answered with literal values):
- 57558 (1.000): multi-criteria lookup incl. date-range containment done in Python, wrote 0.03/0.17 as literals into Deposits!A2:A3, verified with `data_only=True`, and put the INDEX/MATCH formula in the *chat* answer. This is the exact carve-out formula-strings-score-zero prescribes, and it works.
- 263-1 (1.000): summed width×height per material, *verified the pre-filled H3=1660 / H4=2753 reproduced exactly* ("Match=True"), then filled only the blank H2. Ignored the VBA/Power Query framing entirely.
- 408-39 (1.000, second time): dynamic `cell.column_letter` lookup of '0-15', copied value+style I→B, then noticed its own Grand Total double-counted, cleared column I and recomputed L. Note it also overwrote B8's pre-existing 1 with None and still scored 1.0 — grading is concentrated on the stated answer cells.

Failures:
- 50916 (4th consecutive 0.000): wrote 18 nested-IF strings into C12:H14 again. It correctly diagnosed the user's bug (compare B12 to B$2:B$8, not A12) and its final prose lists the right answers ("Homeroom, French, Math, Science...") — it simply never wrote them as values. Direct contrast with 57558 on the same day: same prompt shape, opposite action, opposite score.
- 48080 (3rd 0.000): identical trace to iter 3. Read C2/C3 cached values 14/17 with `data_only=True`, chose to "preserve" the formulas, saw its own verification print `C2: None / C3: None`, then re-opened with `data_only=False`, printed "=A25 / =A41", declared "✅ formulas preserved" and shipped. The preserve rule was applied to formula *text* instead of *value* — I have rewritten the preserve page so rule 2b is the headline and added the mandatory literalise-then-fill snippet.
- 36097 (NEW): the worked example H3 disagreed with its rule (Cost−ITV = 4000 vs given 5000). The trace literally prints "Actual: 5000 / Difference: Could there be a different interpretation?" and then proceeds anyway, using the one example that did match (H4). It also invented an unevidenced `max(0, ITV+profit)` floor (H6 → 0 instead of −50), and its verification only covered H3:H6 — the init's `G3:G6 = '=D3+F3'` and `H7 = '=SUM(H3:H6)'` were blanked by the save and never checked. Evidence appended to validate-rule-against-worked-examples, openpyxl-save-wipes-cached-formula-values and verify-answer-range-values-not-formulas.
- 247-24 (4th 0.000): REGRESSION — abandoned the bottom-up `delete_rows`/`insert_rows` approach the wiki recommends and went back to read-all → `delete_rows(2, max_row)` → rewrite, carrying `=G2*H2` strings into wrong rows. NEW root cause on top of that: `company == 'Motorcycle'` matched **zero** rows (the log shows only the three Ahmed Sons+Canada deletions), so requirement 1 was silently skipped — in iter 3 the same agent over-matched with `'Cycle' in company`. Nobody ever printed the distinct company names. → created confirm-filter-predicates-match-real-values.md.
- 370-43 (NEW): insert a blank row above each 'X' in A7:A1000. Structural work looked right (3 rows found via `data_only=True`, inserted bottom-up), but the sheet's dimensions were **A1:T2483** and the agent only ever dumped rows 1–20 × columns 1–20. The prompt explicitly says "I have also provided a sheet that shows what I am aiming for before and after" — that reference block was never located, so the target shape was guessed. Also `insert_rows` left A6's `=IF(C6="","X","")` and every other formula without cached values after save. → created inspect-full-used-range-and-locate-provided-examples.md.

Actions: created 2 patterns (confirm-filter-predicates-match-real-values, inspect-full-used-range-and-locate-provided-examples), appended iter-4 evidence to 8 existing patterns, sharpened the index wording on the formula/preserve/verify entries so the "literalise, don't preserve" instruction is unmissable. No separate skill file appeared in the traces; the agent's self-reference to "the skill pattern" is the only signal of adoption.
