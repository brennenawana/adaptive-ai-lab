# Test Your Rule on the Rows That Should NOT Match

**Type:** Failure pattern (validation discipline)

## Problem
A classification/matching rule is validated only against oracle rows whose expected answer is "match". Any rule that is too permissive — including `return True` — passes such a test. The agent then widens the rule to absorb one awkward row and silently flips dozens of negative rows.

## Evidence — 192-22, iteration 8 (REGRESSION: 1.000 in iter 2 → 0.000)
Task: write `"Billing PO"` into F when D contains any of nine keyword phrases ('Core Activation', 'Core Design', 'Mobile Terminology', 'Mobile Design', 'Mobile Integration', 'Testing Layer', 'Testing Offshore', 'Carrier', 'Barrier'). Column F ships pre-filled as an "EXPECTED RESULT" oracle.

The honest reading — case-insensitive substring of the **whole phrase** — reproduces every oracle row except row 7, whose D is `'Tesing  Layer 3 protocols/routing'`: a typo of "Testing". Iteration 2 scored 1.000 by naming it a source typo and shipping the plain rule.

Iteration 8 instead invented a looser rule and tested it on 13 hand-picked rows — **all 13 of which are "Billing PO" rows**:
```python
for kw in keywords:
    words = kw.lower().split()
    if any(word in text_lower for word in words):   # ANY single word matches
        return True
...
for row_idx in [3,4,5,6,7,8,20,27,28,29,30,31,32]:  # every one is a positive
```
```
STRATEGY 2: ... ✓ Row 3 ... ✓ Row 8 ... ✓ Row 20 ...   -> "matches all oracle values perfectly!"
```
Under that rule the bare words `core, design, mobile, testing, layer, carrier, barrier` each match on their own, so `'Interconnection Testing'`, `'Conformance Testing'`, `'Protocol Testing'`, `'Functional Testing'`, `'Automation Testing'` (oracle: blank) all become "Billing PO". The chosen test set could not reveal it.

## Root cause
The candidate was scored on a self-selected subset consisting entirely of positives. Recall was measured; precision never was. Relaxing a multi-word keyword into its individual words is a ~10× widening of coverage adopted to explain ONE row.

## Fix
1. Score every candidate over the **entire** oracle range and print a 2×2 count before writing anything:
```python
rows = [r for r in range(2, ws.max_row+1) if ws[f'D{r}'].value is not None]
tp = sum(1 for r in rows if f(r) and oracle[r]);  fp = sum(1 for r in rows if f(r) and not oracle[r])
fn = sum(1 for r in rows if not f(r) and oracle[r]); tn = len(rows)-tp-fp-fn
print(f"tp={tp} fp={fp} fn={fn} tn={tn}"); assert fp == 0 and fn == 0
```
2. **Never choose the test rows yourself.** Use every row that carries any oracle information — a blank oracle cell is a *negative example*, not a missing one.
3. When exactly one row resists an otherwise perfect rule, prefer the data-defect explanation ("Tesing" is a typo of "Testing") and say so in prose. A rule change that alters many rows to fix one row is almost always wrong. See fabricated-rule-overfitting.
4. Sanity-check the degenerate case: would `lambda r: True` pass your test set? If yes, the test set is worthless.
5. Distinguish an empty cell (`None`) from a cell holding the literal string `'None'` — 192-22's rows 51-71 hold the string, and this run overwrote all 20 of them without noticing they were non-empty.

## Related
- Non-discriminating single examples → aggregate-match-is-not-verification.
- Widening/inventing a rule to force a fit → fabricated-rule-overfitting.
- Which cells count as oracle → contradicting-oracle-cells.
