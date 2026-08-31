# A Matching Total Does Not Validate the Individual Rows

**Type:** Failure pattern (validation discipline)

## Problem
The agent has several candidate readings of an ambiguous rule. None reproduces the author-typed oracle cell, so it selects the one whose **sum** equals a pre-existing `=SUM(...)` cached total, declares the interpretation confirmed, and overwrites the oracle.

## Evidence — 36097, iteration 6 (fifth consecutive 0.000)
The agent did the right thing first: it enumerated three readings and scored each against the oracle.
```
Logic 1: If loss→abs(profit), elif profit<cost→profit, else→cost-itv:
  Caterpillar    → 4000 (actual: 5000) ✗
  Utility truck  → 2250 (actual: 2250) ✓
  Total: 7250 (actual: 7250) ✓
Logic 2 ... Total: 7400 ✗ ;  Logic 3 ... ✗
```
It then wrote: *"Logic 1 gives the exact total match (7250), which confirms the correct interpretation"*, wrote 4000 over the oracle `H3=5000`, and additionally replaced the live `H7 = =SUM(H3:H6)` formula with the literal 7250 so its own total could never disagree.

## Root cause
1. A total is ONE equation over N unknowns — an unbounded number of wrong per-row decompositions produce the same sum (here 4000+2250+800+200 = 5000+2250+x+y for many x,y).
2. `H7`'s 7250 is a **cached** value from the file's last save, i.e. an artifact, not an author-typed answer (see fabricated-rule-overfitting §4). Matching it is matching a ghost.
3. "Best of my three candidates" was treated as "correct", although every candidate had a ✗.

## Fix
1. Rank candidate rules **only** by per-cell agreement with author-typed literal cells. A candidate with any ✗ is rejected, not ranked.
2. If no candidate reproduces every oracle cell, that is a signal to enumerate MORE readings (which column is the base? is the adjustment + or −? does the branch test F or G?), not to pick the least-bad one.
3. An aggregate may be used as a weak tiebreaker between candidates that are already 100% per-cell correct — never as primary evidence.
4. Never replace a live `=SUM()`/`=AVERAGE()` formula cell with a literal to make your own arithmetic self-consistent; leave the aggregate alone and let it disagree if it wants to.
```python
survivors = [f for f in candidates if all(f(row) == oracle[r] for r, row in oracle_rows)]
assert survivors, "no reading reproduces the oracle -> enumerate more readings"
```

## Corollary — a NON-DISCRIMINATING example validates nothing (6239, iteration 7)
The prompt supplies one worked case: Goal 65-74%, Variance 0-3%, Metric2 -20..-10% → 3%. The agent tested its additive reading and accepted it:
```
Goal component: 0        # J3
Metric2 component: 0.03  # P3
Total incentive: 0.03 (expected: 0.03)
```
But `J3 = 0`, so the rival reading "the P:T grid alone is the payout" also yields 0.03, as does "J + P" and "max(J,P)". The test passes for every candidate and therefore selects none.

**Discrimination check before you trust any example:**
```python
results = {name: f(example_inputs) for name, f in candidates.items()}
assert len(set(results.values())) > 1, "example does not discriminate -> find another test"
```
If the example cannot separate the candidates, look for structural evidence instead (which cell in the sheet literally holds the example's answer? which table has per-bucket boundaries that must be read?), or construct a second case from a different corner of the grid and reason about it in prose.
