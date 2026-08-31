# Rule silently drops an input dimension the prompt names

## Pattern
The agent builds a lookup/rule that uses fewer input columns than the problem actually has. The code runs, produces plausible values, writes clean literals, passes its own asserts — and scores 0, because an entire axis of the problem was never read.

## Root cause
Two compounding effects:
1. A 3-D problem (A x B -> C) is easy to mistake for a 2-D one when the helper block on the sheet is stored as two 2-D tables (see misread-lookup-table-geometry.md).
2. **The examples quoted in the prompt often cannot discriminate.** If every worked example shares the same value of the dropped dimension, a rule that ignores that dimension reproduces all of them. Passing the examples is then *not* evidence the rule is right.

## Evidence: 6239 (soft=0, third consecutive failure, new failure mode)
Prompt names three inputs: `Goal`, `Variance to Goal` (col E), `Metric2` (col F). The agent's final code:
```python
goal_bucket   = get_goal_bucket(ws.cell(r,4).value)     # col D
metric2_bucket= get_metric2_bucket(ws.cell(r,6).value)  # col F
incentive = payout_grid[goal_bucket][metric2_bucket]    # col E NEVER READ
```
Column E and the entire J3:M6 variance-threshold table were never touched. Yet both examples in the prompt (Goal 65–74% + Variance 0–3% + Metric2 −20..−10% -> 3%; same with Metric2 >20% -> 7%) *do* come out right, because both live in goal bucket 0 / variance band 0 and `payout_grid[0]` happens to equal the correct variance-band-0 row. The examples validated nothing.

Correct geometry: grid **rows = variance band** (chosen from the goal-dependent thresholds in J3:M6), grid **columns = Metric2 bucket**. Goal only selects which threshold column of J3:M6 to walk.

## Evidence: 194-19 (soft=0, twice)
Sheet2's J,K,L,M are four *positions*; the agent collapsed them to `first non-empty value` — one scalar per (track, race) — dropping the position axis and the Sheet1 `Tab` column entirely, then wrote that one constant into all 7–12 Sheet1 rows of the race.

## Fix
```python
inputs_named_in_prompt = ['Goal', 'Variance to Goal', 'Metric2']
# after writing rule(), grep your own code:
assert all(name_is_read(n) for n in inputs_named_in_prompt), "a named input is unused"
```
1. Before coding, write the literal list of every column/field the prompt names and every helper block on the sheet. If your rule doesn't consume one of them, your rule is wrong — the task author put it there for a reason.
2. Check your examples **discriminate**: for each dimension, do the given examples take at least two different values along it? If not, that dimension is untested — reason about it explicitly instead of trusting the passing assert.
3. Sanity-check the output distribution: 6239's output used only 4 of the 20 grid cells and every employee landed in goal buckets 1–2. A rule whose outputs never span the table is suspicious.
