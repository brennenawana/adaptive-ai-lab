# pandas/openpyxl version mismatch inside the project .venv

## Symptom
```
ImportError: Pandas requires version '3.1.5' or newer of 'openpyxl' (version '3.1.3' currently installed).
```
raised from `pd.read_excel(...)`, while `pip install --upgrade openpyxl` reports "Requirement already satisfied ... 3.1.5".

## Root cause
`python`/`pip` on PATH resolve to the user install (`~/.local/lib/python3.12/site-packages`), but the executing interpreter loads the project `.venv/lib/python3.12/site-packages`, which still holds `openpyxl-3.1.3.dist-info`. Task 141-20 burned 4 tool calls on `--upgrade`, `--force-reinstall`, and `uninstall && install==3.1.5` — none of which touched the .venv.

## Fix
- Fastest: stop using pandas for Excel I/O. `import openpyxl; wb = openpyxl.load_workbook(path)` works with 3.1.3 and is what finally succeeded.
- If pandas is required, target the right interpreter explicitly:
  `python -c "import sys; print(sys.executable)"` then `"$(python -c 'import sys;print(sys.executable)')" -m pip install -U openpyxl`.
- Diagnose before reinstalling: `ls .venv/lib/python*/site-packages | grep openpyxl`.
