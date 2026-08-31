# Long, Conflicting Instructions: Resolve Before Coding

**Type:** Failure pattern (task comprehension)

## Problem
Task 22-47 stated many rules at once: helper-column J priority order, preserve source order within groups, skip headers/blanks/duplicates (duplicate = same B AND C), fall back to A-Z if J empty, output to "F:H" but also "final answer in columns G and H", and "sort only column H lowest to highest". These conflict.

## Root cause
The agent implemented interpretation #1 (priority-first, then ref ascending), printed the result, then second-guessed itself ("which might mean the primary sort should be by column H") and rewrote the sort key to ref-first — discarding the helper-column semantics that the instruction spent most of its words on. No hand-derived expected output was ever produced, so neither version could be validated. Score 0.000.

## Fix
1. Enumerate every rule as a numbered checklist before writing code.
2. Resolve conflicts by precedence: explicit examples in the file > detailed prose rules > terse trailing clauses. "Sort only column H" most plausibly means "within a group, order by H" — i.e., a tiebreaker, not the primary key.
3. Hand-derive the expected first 3 output rows and assert the code reproduces them.
4. Honor the literal output range stated last (here G and H), and check whether an existing header/pre-filled column (F held 1..10) implies rows to fill.
5. Do not silently switch interpretations mid-run; pick one that satisfies the most rules and state the assumption.

## Iteration 4: 6239 (0.000) — a multi-axis lookup grid with no oracle
The prompt describes a 3-axis rule (Goal bucket × Variance band × Metric2 band → incentive %) and the sheet holds TWO side-by-side tables: J2:M2 goal-bucket boundaries with J3:M6 values, and P2:T2 metric2 boundaries with P3:T6 values. Column G ("Incentive") is entirely empty — no worked example anywhere.
What went wrong:
1. **Boundary columns guessed, then corrected.** The agent first read the Metric2 bounds from O–S (`[-0.2,-0.1,0,0.1]`, four values for five buckets), noticed the count was wrong, and only then dumped O–U to find the real range P–T (`[-0.2,-0.1,0,0.1,0.2]`). Always locate a lookup table by scanning for its non-empty extent, never by counting columns from a neighbour.
2. **Two tables, one output, no stated combination rule.** The prompt's single worked example ("Goal 65-74%, Variance 0-3%, Metric2 -20..-10% → 3%") maps onto the P3 cell (0.03) alone, which implies the J:M table is the *variance-band* definition per goal bucket (the bands are not fixed 0/3/5/7% — they differ per goal column: J=0/.03/.05/.07, M=0/.01/.02/.04), not a second additive payout. The agent instead treated J:M as "base incentive" values.
3. **Invented defaults** for uncovered cases (`if variance < 0: return 0`) — see fabricated-rule-overfitting.
**Fix for grid tasks:** write down the ONE example the prompt gives as a coordinate triple, find the single cell in the workbook that holds that number, and let that cell's position define which table is the payout and which is the bucket definition. Then hand-check a second employee row before filling the column.

## Iteration 5: 22-47 failed a second time — the trailing clause ate the whole spec
This run fixed iteration 1's mechanical bugs (it wrote literal values, saved last) and still scored 0.000, because it resolved the ambiguity the opposite way from what the prompt's word-count implies:
```
Combined (J order + original order):   # <-- correct, the spec's whole point
  HASSAN 133444422, HASSAN 123444441, HAMAN 133444424, HAMMED 123344577, HASSONA ...
Final sorted (by REF lowest to highest):   # <-- then thrown away
  HASSONA 123344555, HAMMED 123344577, HASSAN 123444441, ...
```
The prompt spends ~80% of its text defining a helper-column priority order and "keep their original order from the source and do not sort within the group", then ends with "sort only column H sorted lowest to highest". Sorting everything by H makes every preceding sentence dead text. **Heuristic: an interpretation that renders the majority of the instruction inoperative is wrong** — the trailing clause is a tiebreaker inside a group, not the primary key.

Three further self-inflicted wounds in the same run:
- `header_rows = {1, 8, 14, 21}` hardcoded from an eyeball of rows 1-22 instead of detected by `B=="NAME" and C=="REF"` over `max_row`;
- `output_rows = final_sorted[:9]  # Only 9 rows for F2:H10` — it had **10** unique rows and silently dropped one to fit a range it invented;
- it wrote F, G and H although the instruction says "the final answer should be output in columns G and H", and column F already contained the author's 1..9 ITEM numbering.

## Iteration 6: 22-47 fails a THIRD time with the identical inversion
Two independent runs (iters 5 and 6) computed the correct grouped order and then destroyed it with the same final line:
```
Sorted rows (before sorting by REF):
  1. HASSAN 133444422  2. HASSAN 123444441  3. HAMAN 133444424  4. HAMMED 123344577  ...   # correct
unique_rows_sorted_by_ref = sorted(unique_rows_sorted, key=lambda x: float(x['ref']))      # thrown away
```
plus the same two side-effects the wiki already records: `unique_rows_sorted_by_ref[:9]  # Only 9 rows (F2:H10)` silently dropping the 10th of 10 unique rows, and writing column F although the prompt says "the final answer should be output in columns G and H". Its verification only asserted "Is sorted ascending? True" — i.e. it verified the interpretation it had chosen, which can never fail.
**Restated rule:** when a late clause and the body of the prompt conflict, apply the late clause as a *tiebreaker inside the groups the body defines*, and verify by hand-deriving the first three rows from the prose — not by asserting that your own sort key sorted.

## Iteration 6: 6239 fails again by dropping a whole axis
The prompt names THREE filters (Goal bucket, Variance to Goal, Metric2). The implemented function took two:
```python
def find_variance_row(value): ...      # fixed bands 0/0.03/0.05/0.07
def find_metric2_col(value): ...
incentive = payout_grid[(var_row, m2_col)]   # `goal` never used
```
The `J2:M6` table is exactly the missing axis: its header row `J2..M2 = 0.65/0.75/0.85/0.95` are the Goal buckets and each column holds that bucket's variance-band boundaries (`J: 0/.03/.05/.07`, `K: 0/.02/.04/.06`, `L: 0/.015/.03/.045`, `M: 0/.01/.02/.04`). Every employee in the file has Goal ≈ 0.83-0.87 → the K/L columns, so hardcoding the J column's bands mis-buckets essentially every row.
**Mechanical guard:** list the inputs the prompt names, then assert each one appears in your function signature and is actually referenced in the body. If a lookup table in the sheet is never read, you have dropped an axis.

## Iteration 7: 6239 fails a THIRD time — right axis, wrong boundaries, no output
Progress: this run did read the Goal-bucket table and used it (`find_goal_bucket`), combining the two tables additively (`incentive = lookup_goal[(var_row, goal_col)] + lookup_metric2[(var_row, m2_col)]`). Two problems remain:
1. **The variance bands are still hardcoded to the J column.**
```python
def find_variance_row(variance):
    if variance < 0.03: return 3
    elif variance < 0.05: return 4
    elif variance < 0.07: return 5
    else: return 6
```
The J:M table exists precisely because the bands differ per Goal bucket (`J: 0/.03/.05/.07`, `K: 0/.02/.04/.06`, `L: 0/.015/.03/.045`, `M: 0/.01/.02/.04`). Every employee has Goal ≈0.83-0.87 → the L column (bands .015/.03/.045), so nearly every row is mis-bucketed. **The band boundaries must be looked up from the goal column, not typed as constants.** A per-column table in the sheet whose numbers never appear in your code is a dropped axis, even if the column *label* appears.
2. **The validating example does not discriminate.** `J3 = 0`, so `J3 + P3` and `P3` alone both give the prompt's 0.03 (see aggregate-match-is-not-verification).
3. The run then ended: five turns of table dumps and a test print, **no write, no `wb.save`** (see plan-pipeline-before-mutating). Budget spent on inspection is budget not spent on an answer — write a first-draft output file as soon as any defensible rule exists.
