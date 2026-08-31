# Time/Date "Formatting" Tasks Need a Typed Value + number_format, Not strftime Text

**Type:** Failure pattern

## Problem
The user asks to *display* a time ("format column J to only show the standard time 00:00:00 AM/PM from I2"). The agent produces a Python string with `strftime` and writes it. The cell now holds TEXT; a grader comparing against a real time value, or checking `number_format`, fails. It is also semantically wrong — the user's complaint was precisely that `=RIGHT(I2,8)` gave them text.

## Evidence (task 32438, 0.000)
```python
formatted_time = datetime_val.strftime('%I:%M:%S %p')   # '06:08:00 PM'  -> str
ws_formulas[f'J{row}'].value = formatted_time
```
Verification printed `J2: '06:08:00 PM'` — quoted, i.e. a string — and the agent accepted it.
Note the file itself showed the intent: `I1` already carried `number_format = [$-F400]h:mm:ss\ AM/PM`.

## Fix
```python
from datetime import datetime, time
dt = ws_src[f'I{r}'].value            # datetime.datetime
cell = ws[f'J{r}']
cell.value = time(dt.hour, dt.minute, dt.second)   # or dt itself, or the fraction dt-hour/24 float
cell.number_format = 'h:mm:ss AM/PM'
```
- Copy the number_format the workbook already uses for that concept (here `I1`'s `[$-F400]h:mm:ss AM/PM`).
- Verify by type, not just by print: `assert not isinstance(v, str)` and echo `cell.number_format`.
- Only write text when the prompt explicitly asks for `TEXT(...)`/a string result.
- Same rule for dates, percentages and currency: store the number, express the appearance in `number_format`.

## Iteration 5: identical failure repeated (32438, 0.000 for the second time)
Same file, same prompt, same `strftime`:
```python
formatted_time = time_obj.strftime("%I:%M:%S %p")   # '06:08:00 PM' -> str
ws[f'J{row}'].value = formatted_time
```
What is new and important is the **verification**, which looked rigorous and proved nothing:
```
J2: 06:08:00 PM (formula: False)
✓ All cells contain literal values, not formulas
```
A text string passes `not str(v).startswith('=')` trivially. The "no formula strings" assertion is necessary but blind to type errors.

Also visible in the trace and ignored: the pre-existing J column held `'55555556'` **strings** (mangled fractional-day remnants) — evidence that the user's `=RIGHT(I2,8)` text approach is exactly what they are complaining about, i.e. more text is the wrong answer.

**Closing check for any "format/display as X" task:**
```python
v = chk[f'J{r}'].value
assert not isinstance(v, str), (r, repr(v))          # type, not just '='
assert isinstance(v, (datetime, time, float, int))
print(chk[f'J{r}'].number_format)                    # must be the h:mm:ss AM/PM style
```

