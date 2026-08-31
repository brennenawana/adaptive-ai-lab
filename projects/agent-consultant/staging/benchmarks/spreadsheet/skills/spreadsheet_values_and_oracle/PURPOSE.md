| # PURPOSE

## Origin
Iteration 1 of SpreadsheetBench training: 24 of 30 tasks scored 0.000. Root-cause
analysis of traces 1818, 50916, 58484, 10747, 194-19, 22-47 and 247-24 showed three
recurring, mechanical causes — not reasoning failures.

## Patterns Addressed
- `write-values-not-formulas`: every 0.000 task ended with a formula STRING in the
  target cells (1818 INDEX/SMALL, 50916 nested IF, 58484 INDIRECT/COUNTIF, 10747
  SUMIFS). openpyxl stores no cached result, so a value-reading grader sees None.
  All three 1.000 tasks wrote literal Python-computed values.
- `legacy-array-formula-cse` and `openpyxl-formula-fill-down`: subsumed by the
  "compute in Python, write values" rule plus a LibreOffice recalc escape hatch.
- `verify-against-reference-sheet` (success pattern, promoted here to a hard gate):
  58484 had an "Expected Result" column pre-filled by the user; 194-19 had the
  first meet already completed. The agent OVERWROTE both instead of using them as
  an oracle, and never checked that its logic reproduced them.
- New: destructive `pandas.to_excel` round-trip (247-24) discarded workbook layout;
  "insert two new rows" was implemented as duplicating the source row.
- New: `Sheet.$A$1` (LibreOffice/ODF syntax) written instead of `Sheet!$A$1` (1818).
- New: source workbooks are often formula-driven with no cached values (10747), so
  `data_only=True` reads return None — inputs must be recalculated before reading.

## Evolution History
- v1 (this version): initial creation. Covers inspect -> find in-file oracle ->
  compute in Python -> write literal values -> edit in place -> reload-and-assert.
