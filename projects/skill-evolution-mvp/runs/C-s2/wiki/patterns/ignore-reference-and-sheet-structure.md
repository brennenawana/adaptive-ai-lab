# Ignored reference sheets / never enumerated sheets

## Pattern
The user says "I have also provided a sheet that shows what I am aiming for before and after", and the agent edits one sheet in place without ever reading the demo sheet or even listing the workbook's sheets.

## Root cause
The agent jumps to `wb['<guessed name>']` or `wb.active` after a single dump. The demo/after sheet is the highest-fidelity specification available (it disambiguates *where* rows go, whether the marker row is kept, whether the answer belongs on another sheet), and it is silently discarded.

## Evidence (iteration 2)
- **370-43** (soft=0): first command was `ws = wb["Before Insert Row"]`; `wb.sheetnames` was never printed. The prompt explicitly advertised a before/after example. The agent inserted blank rows above each X in the *Before* sheet and declared success from its own reasoning, with no comparison to the intended *After* layout.
- **194-19** (soft=0): two sheets with different column semantics (Sheet2 Track/Race, Sheet1 Meet/Race) and duplicate Track/Race pairs (rows 2 and 83 for the same race). The agent explored well but never resolved which duplicate to use against the already-completed first meet, which was the on-file reference solution.

## Fix
```python
print(wb.sheetnames)
for name in wb.sheetnames:            # dump ALL sheets before editing
    ...
```
If a before/after (or "sample"/"desired") sheet exists: diff it against the source region cell-by-cell to derive the exact transformation, then apply that transformation and re-diff your output against the demo. If part of the answer is already completed on the sheet (e.g. "I've completed results for the first meet"), reproduce that region with your algorithm first and require an exact match before extending it.

## Iteration 3 correction: 370-43 listed the sheets and there was no demo sheet
The agent *did* run `for sheet_name in wb.sheetnames` this time, and the output was a single sheet:
```
Available sheets:
  - Before Insert Row
```
So the promised "sheet that shows before and after" simply is not in the file. Enumerating sheets is therefore necessary but was **not** the cause of this failure — the cause was structural (see row-restructure-breaks-references.md).

Generalized guidance: enumerate sheets first (cheap, still mandatory). If the advertised reference sheet is absent, do **not** invent your own spec — fall back to the prompt's literal wording ("insert a row **above** every line where there is an X in A7:A1000") and to any partially-completed region on the sheet, and state which spec you used.

## Iteration 4: dumping the reference sheet is not using it (22-47, soft=0)
The agent *did* enumerate sheets and *did* print the second one:
```
Sheets in workbook: ['sheet1', 'ورقة1']
ورقة1: HAMAN, HAMMED, HAMUDDA, HANA, HASSAN, HASSAN, HASSAN, HASSNA, HASSONA, HUSSNI, MOHSION
```
That is the expected output list — alphabetical, with `HASSAN` appearing **three times**, which directly refutes the agent's dedup-to-10-unique-entries model. It also refutes the final global sort-by-REF ordering. The sheet was printed once in turn 1 and never referenced again.

Similarly `F1:H1` already held the headers `ITEM/NAME/REF` and `F2:F11` held `1..10`, pinning the output block to exactly 10 rows starting at F2.

Strengthened rule: enumerating sheets is step 0; the actual requirement is to **turn every non-target sheet and every pre-filled cell in the target block into an assertion**. Before saving:
```python
assert [r[1] for r in my_output] == ref_list, f"output disagrees with reference sheet: {my_output} vs {ref_list}"
```
If you cannot explain what the extra sheet is for, you have not finished analysing the file.

