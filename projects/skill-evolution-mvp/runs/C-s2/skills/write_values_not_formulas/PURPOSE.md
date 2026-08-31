## Origin

Created after iteration 1 of the SpreadsheetBench training set: 24 of 30 tasks
scored 0.000 while 6 scored 1.000, and the split was almost entirely explained by
whether the agent wrote literal cell values or formula strings.

## Patterns Addressed

- `formula-written-but-no-cached-value` — openpyxl stores formula text with no
  cached `<v>`; graders reading values see `None`. Seen in 263-1 (SUMPRODUCT into
  H2:H4 when 3710/1660/2753 were already computed in Python), 3413 (IF/COUNTIFS/
  SUMIFS into G3:G6 with the answers 14/27/4/11 printed in the trace), 36097
  (nested IF into H3:H6), 39931, 10452, 472-15, 55060, 50916.
- `ignored-none-verification-signal` — verification steps that print formula
  strings or `None` and are narrated as success. Every failing trace ended with a
  ✅ summary.
- `dynamic-array-spill-formula-misuse` — one FILTER in the first cell, N-1 empty
  cells (10452).
- `compute-values-in-python-success` — the shape shared by all 1.0 runs (408-39,
  66-24, 170-13, 192-22, 39903, 48745, 82-30).

New root causes surfaced by this round of trace reading:

- **Instruction wording overrides the grading criterion.** Task 1818 is the clearest
  case: the agent extracted the 16 "Lowest Performing" students and wrote them as
  literals into Summary!B3:C18, then *deliberately reverted* to INDEX/SMALL/IF
  array formulas, deleting a static backup file and stating "the formula method is
  what you asked for." 263-1 ("make this sheet dynamic") and 247-24 ("I require VBA
  code") show the same pull. The skill therefore contains an explicit request→
  deliverable translation table and a prohibition on reverting literals.
- **The openpyxl round-trip destroys cached values of pre-existing formulas.**
  247-24's Main sheet had `=G2*H2`, `=G2-30`, `=J2*H2`, `=I2-K2` in columns I–L of
  every data row; 36097 had `=D3+F3` in column G and `=SUM(...)` in row 7. Loading
  with the default `data_only=False` and saving blanks all of them, so cells the
  agent never touched grade as `None`. Prior wiki pages only warned about formulas
  the agent *writes*, not ones already in the file — this is the gap the skill
  closes with a pre-scan plus a `soffice --headless --convert-to xlsx` recalc pass
  (with a data_only fallback).
- **Output-shape drift.** Task 22-47 computed a defensible result but wrote a header
  row and an extra column F that the instruction ("output in columns G and H") did
  not ask for, hence step 4.

## Evolution History

- v1 (iteration 2): initial creation. Combines the four existing wiki patterns into
  one actionable workflow and adds three previously unrecorded root causes:
  wording-driven reversion to formulas, cached-value loss on pre-existing formulas,
  and output-shape drift. Verification is specified as an `assert` gate rather than
  a print, since narrated verification failed in 100% of the traces examined.
