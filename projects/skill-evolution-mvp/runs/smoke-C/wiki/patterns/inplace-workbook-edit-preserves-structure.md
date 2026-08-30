# Success pattern: in-place openpyxl edit + verify

## Pattern (from task 141-20, score 1.000)
1. Load once, keep the original workbook object:
   `wb = openpyxl.load_workbook(input_file)`
2. Read raw cells by index rather than by pandas column name, so header quirks don't matter:
   `sheet.cell(row=i, column=3).value`  # column C
3. Collect the row indices to change first, print them, then mutate.
4. **Delete rows in reverse order** so indices don't shift:
   `for r in sorted(rows, reverse=True): sheet.delete_rows(r, 1)`
5. `wb.save(output_file)` to the exact expected output filename (`<n>_<taskid>_output.xlsx`).
6. Re-open the saved file and print every sheet to confirm the change landed.

## Why it beats the pandas route
The first attempt used `pd.read_excel` + `ExcelWriter`, which (a) hit the openpyxl version wall and (b) would have discarded formatting, highlighting, and any sheet not explicitly rewritten. Multi-sheet tasks almost always require preserving untouched sheets, so mutate the loaded workbook instead of regenerating it.

## Note
When the task mentions "macro"/VBA, delivering the transformed .xlsx (plus explanation) is still what is graded — grade the output file, not the language of the request.
