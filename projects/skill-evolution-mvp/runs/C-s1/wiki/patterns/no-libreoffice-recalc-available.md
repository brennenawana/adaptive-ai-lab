# LibreOffice Recalculation Is Not Available (and Is Destructive)

**Type:** Failure pattern (environment)

## Problem
The common workaround "write the formula, then recalc with LibreOffice so a cached value exists" does not work in this environment.

## Evidence (iteration 2)
```
$ soffice --headless --convert-to xlsx --outdir . 1_58484_output.xlsx
/opt/homebrew/bin/soffice: line 2: /Applications/LibreOffice.app/Contents/MacOS/soffice: No such file or directory
```
```
subprocess.CalledProcessError: ... returned non-zero exit status 127   # task 247-24
```
Tasks 58484, 36097, 48080, 247-24 all hit this and then shipped formula-only files -> 0.000.

## Second, worse failure: it overwrites the input
Task 10747 ran the conversion with `--outdir <the workdir>` on `1_10747_init.xlsx`. The converted file has the SAME name, so the original was overwritten, then `os.rename(...)` moved it to `recalc.xlsx`, and the next `load_workbook('...init.xlsx')` raised `FileNotFoundError`. The agent spent several turns trying `git checkout` (not tracked) to recover.

## Fix
1. Do not plan around soffice. Compute every needed value in Python and write literals.
2. If you ever do convert, use a scratch dir: `--outdir /tmp/recalc_$$` and never the directory holding the source workbook.
3. Never call `os.rename` on the init file. Copy first (`shutil.copy(init, scratch)`) and operate on the copy.
4. Check availability before relying on it: `subprocess.run(['soffice','--version'])` — if returncode != 0, go straight to the Python-values path.
