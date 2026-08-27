"""Free screen: how many stored listings could trip the _MAX_UNIT_RENT band?

No API, no LLM. Regex over descriptions already in the DB. This is an UPPER
BOUND on F-B1's rate, not a measurement: a number appearing in prose is not
proof the LLM would extract it as gross income.
"""
import os, re, sys
sys.path.insert(0, os.environ["WHOLESALING_REPO"] + "/backend")
from sqlalchemy import create_engine, text
from app.config.settings import Settings
from app.services.listing_income import _MAX_UNIT_RENT

MONEY = re.compile(r"\$\s?([\d,]+(?:\.\d+)?)")
s = Settings()
eng = create_engine(s.database_url, future=True)

rows = []
with eng.connect() as c:
    for r in c.execute(text("""
        select asset_id, units, asking_price, marketing_description
        from crexi_listings
        where marketing_description is not null and marketing_description <> ''
    """)):
        rows.append(r)

with_desc = len(rows)
have_units = [r for r in rows if r.units]
trip, near = [], []
for r in have_units:
    ceiling = r.units * _MAX_UNIT_RENT
    nums = []
    for m in MONEY.finditer(r.marketing_description):
        try:
            v = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        if v > 0:
            nums.append(v)
    # A stated ANNUAL income implies monthly = v/12. A stated MONTHLY gross is v.
    implied = [v / 12 for v in nums if v >= 12 * 200] + [v for v in nums if 200 <= v <= 10_000_000]
    over = [v for v in implied if v > ceiling]
    if over:
        trip.append((r.asset_id, r.units, r.asking_price, ceiling, max(over)))
    elif implied and max(implied) > 0.75 * ceiling:
        near.append((r.asset_id, r.units, ceiling, max(implied)))

print(f"listings with a description : {with_desc}")
print(f"  ... and a unit count      : {len(have_units)}")
print(f"  ceiling = units x ${_MAX_UNIT_RENT:,.0f}/mo\n")
print(f"COULD trip the band (some plausible income reading exceeds the ceiling): "
      f"{len(trip)}/{len(have_units)} ({100*len(trip)/max(len(have_units),1):.0f}%)")
for a, u, ask, ceil, mx in sorted(trip, key=lambda t: -t[4])[:12]:
    ask_s = f"${ask:,.0f}" if ask else "unpriced"
    print(f"   asset {a}  {u}u  ask {ask_s:>12s}  ceiling ${ceil:>9,.0f}/mo  max implied ${mx:>11,.0f}/mo")
print(f"\nwithin 25% of the ceiling (fragile): {len(near)}")
