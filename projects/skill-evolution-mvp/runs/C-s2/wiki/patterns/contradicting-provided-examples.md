# Solution contradicts the examples the user already gave (score 0)

## Pattern
Agent writes clean literal values (so iteration-1 lessons were applied) and still scores 0, because the *logic* is wrong. The file or the prompt contains worked examples that disprove the agent's interpretation, and the agent never checks against them.

## Root cause
Ambiguous natural-language business rules ("recoup ITV adjusted by the loss", "incentive bucket", "count of transfers") have many plausible readings. The task authors always embed ground truth: a few pre-filled answer cells, an "Expected Result" column, or a numeric example in the instruction. The agent treats these as decoration instead of as test cases.

## Evidence (iteration 2, all soft=0)
- **36097**: H3 and H4 were **already filled** with 5000 and 2250 — the given examples. Agent's rule produced H3=4000 (≠5000) and **overwrote** the 5000. It even printed `Row 3 (Caterpillar): ... → otherwise → Recoupment = 4000` without noticing the cell already said 5000. A rule reproducing both 5000 and 2250 exists (e.g. Cost−ITV+... ) and could have been searched for.
- **58484**: column H was literally headed `Expected Result` with H6=1, H9=2, H11=1, H13=1, H15=1 and **blank** at 17,19,21,23–25. Agent's "consecutive-run" rule emitted 1 at 17,19,21 and 3 at 25 — contradicting 4 given cells — and it overwrote the expected column anyway.
- **6239**: instruction stated "Goal 65–74%, Variance 0–3%, Metric2 −20..−10% → **3%**" and ">20% under same → **7%**". Those are exactly the grid values in P3:T3. Agent invented `base + adjustment` summation, producing 0.18/0.24/0.115 — no employee could ever get 3%. One sanity check against the stated example would have killed the model.

## Fix (do this before writing any output)
```python
# 1. collect every already-known answer (pre-filled target cells, examples in prompt)
examples = {(3,'H'):5000, (4,'H'):2250}
# 2. implement rule(); 3. assert it reproduces ALL of them
for (r,c),exp in examples.items():
    got = rule(r)
    assert got == exp, f"rule wrong at {c}{r}: got {got}, expected {exp}"
```
If the assert fires, **change the rule**, do not change the example. Enumerate candidate readings (`Cost-ITV`, `ITV+(Cost-Proceeds)`, `min(Profit,Cost)`, direct grid lookup vs sum) and keep the one that fits every example. Never overwrite a cell that already holds a given example.

## Iteration 3: same two tasks failed again the same way
- **6239** (0.0 in iter 2 and iter 3): rebuilt the identical `goal_payout + metric2_payout - base_payout` model. Under it, the 3% the prompt explicitly names is unreachable for any employee — a one-line check against the quoted example would have rejected the model. The table geometry that *does* reproduce 3% and 7% is written up in misread-lookup-table-geometry.md.
- **36097** (0.0 in iter 2 and iter 3): again printed `Row 3 (Caterpillar): ... Recoup = Cost - ITV = 4000 - 0 = 4000` while H3 already contained **5000**, treated the single match at H4=2250 as confirmation, and wrote 4000 over the given 5000. One example matching is not validation — **all** given examples must match.

## Positive counter-example: when the prompt contradicts itself, follow the concrete rows
**48745 (soft=1.0)**: the summary paragraph said the outcome could be `'Group 1'`, `'Group 2'` or **`'BOTH'`**, but the row-by-row narrative said *"Row 9 ... would return Group 1, Group 2"*, and the pre-filled D5:D7 (`Group 1`, `Group 1`, `Group 2`) matched that narrative. The agent emitted `'Group 1, Group 2'` — following the concrete examples over the abstract summary — and scored 1.0.

Priority order for resolving ambiguity: **pre-filled answer cells > worked examples in the prompt > the prompt's abstract summary > your own reading of the business logic.**

## Iteration 4 CORRECTION: blanks in an "Expected Result" column are not ground truth
The iteration-2 diagnosis of **58484** above is wrong and should not be relied on. 58484 scored **1.0** in iteration 4 with a run that *also* emitted values at rows 17/19/21/25 where the given column was blank. What the winning run did differently: it reproduced all five **non-blank** given values (H6=1, H9=2, H11=1, H13=1, H15=1) exactly, left them in place, and satisfied the prompt's formatting clauses (see multi-requirement-instruction-checklist.md).

Refined rule: **non-blank example cells are hard constraints; trailing blanks usually mean "not yet computed", not "must stay empty".** Reproduce every filled example; treat blanks as unknown unless the prompt says the result should be blank there (as 48745's D8 case did).

## Iteration 4: examples that cannot discriminate
**6239** (0.0, third time) finally used a grid lookup and *did* reproduce both numbers quoted in the prompt (3% and 7%) — while ignoring the Variance dimension entirely. Both quoted examples sit in the same variance band, so matching them proved nothing. Passing the given examples is necessary, not sufficient: check that your examples vary along every dimension. See dropped-dimension-in-rule.md.

## Iteration 4: 22-47 — conflicting clauses resolved by guessing, not by the file
The prompt says both "output in range F:H" and "output in columns G and H", and both "keep helper-column-J order, do not sort within the group" and "sort only column H lowest to highest". The agent oscillated across three turns and finished by applying a **global** `sort(key=ref)`, which destroys the J-priority ordering the same sentence demands. It never consulted the two available arbiters: the pre-filled `F2:F11 = 1..10` (output is exactly 10 rows) and the second sheet `ورقة1` holding the expected name list.

When two clauses conflict, do **not** pick one and move on. Enumerate both readings, evaluate each against the file's ground truth, and state which one you chose and why. "Sort column H lowest to highest" is almost always a *within-group tiebreaker*, not a replacement for the primary ordering the same instruction just specified.

