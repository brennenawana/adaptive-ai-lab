import os, re, sys
sys.path.insert(0, os.environ["WHOLESALING_REPO"] + "/backend")
from sqlalchemy import create_engine, text
from app.config.settings import Settings
from app.services.listing_income import _numbers_in

KM = re.compile(r"\$\s?([0-9][\d.,]*)\s?([kKmM])\b")
INCOME = re.compile(r"(rent|income|noi|gross|produces?|generat|cap rate)", re.I)
TAG = re.compile(r"<[^>]+>")

eng = create_engine(Settings().database_url, future=True)
rows = [(a, TAG.sub(" ", d)) for a, d in eng.connect().execute(text(
    "select asset_id, marketing_description from crexi_listings "
    "where marketing_description is not null and marketing_description <> ''"))]

km, km_income, examples = 0, 0, []
for a, t in rows:
    hits = KM.findall(t)
    if hits:
        km += 1
        if INCOME.search(t):
            km_income += 1
            if len(examples) < 8:
                nums = _numbers_in(t)
                for val, suf in hits[:2]:
                    try:
                        full = int(float(val.replace(",", "")) * (1000 if suf in "kK" else 1_000_000))
                    except ValueError:
                        continue
                    examples.append((a, f"${val}{suf}", full, full in nums))
print(f"descriptions                         : {len(rows)}")
print(f"  use $NNNk / $NNNM money notation   : {km}  ({100*km/len(rows):.0f}%)")
print(f"  ...AND mention income/rent         : {km_income}  ({100*km_income/len(rows):.0f}%)")
print(f"\nfor each: does the FULL value reach _numbers_in()? (False = correct extraction gets rejected)")
for a, raw, full, seen in examples:
    print(f"   asset {a}  text={raw:>10s} -> value {full:>10,d}   in _numbers_in? {seen}")
