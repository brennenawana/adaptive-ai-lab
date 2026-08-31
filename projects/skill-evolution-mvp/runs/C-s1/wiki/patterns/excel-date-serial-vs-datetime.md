# Date Columns May Arrive as Excel Serial Numbers

**Type:** Mechanical pattern (success recipe from 47766, 1.000)

## Problem
openpyxl returns a `datetime` only when the cell carries a date number_format. In these user workbooks the same column often yields raw serials (`44392`), so any `date >= datetime(2021,1,1)` comparison raises `TypeError`, and any year-bucketing done on the int silently produces one giant bucket.

## Evidence — 47766 (1.000): "adapt my SUMIF to a date range from column F"
Column F came back as ints. The agent converted and then printed the boundary serials so the buckets were auditable:
```python
def excel_date_to_datetime(v):
    if isinstance(v, datetime): return v
    if isinstance(v, (int, float)): return datetime(1899, 12, 30) + timedelta(days=v)
    return None
# 44392 -> 2021-07-15 ; 44565 -> 2022-01-04
for year in (2021, 2022, 2023, 2024, 2025, 2026):
    print(year, (datetime(year,1,1) - datetime(1899,12,30)).days)   # 44197, 44562, ...
```
It then rebuilt the whole `J39:O53` grid (3 agents × 3 categories × 5 years) as literals, cross-checking its 2021 Rentals-PE number against the cached value of the user's existing `=SUMIF($H$8:$H$37,"*PE*",$C$8:$C$37)` → 14755.

## Fix / checklist
- Probe every date column during inspection: `print(repr(v), type(v).__name__)`. Never assume.
- Normalize to `datetime` on BOTH sides before comparing; epoch is **1899-12-30** (this absorbs Excel's 1900 leap-year bug for all dates after 1900-03-01).
- Year/quarter bucketing: convert first, then `dt.year`; do not do arithmetic on serials.
- When writing a date back, write a `datetime`/`date` object and set `number_format` (see time-value-vs-text-string).
- A wildcard criterion like `"*PE*"` is a **substring** test, not equality: `'PE' in str(h)` — combine with `.strip().upper()`.
