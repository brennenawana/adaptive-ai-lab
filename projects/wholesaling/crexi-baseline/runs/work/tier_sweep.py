"""Measure the income-tier distribution and F-B1's real rate, per listing.

This is the telemetry the lane does not persist: which tier fired, whether the
LLM was attempted, what it returned, and whether the validator accepted it.
"""
import os, sys, json, time
sys.path.insert(0, os.environ["WHOLESALING_REPO"] + "/backend")
from collections import Counter
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.config.settings import Settings
from app.db.models import CrexiListingORM
from app.persistence.crexi_listing_store import listing_from_row
from app.providers.crexi.client import CrexiClient
import app.services.listing_income as LI

LIMIT = int(os.environ.get("SWEEP_LIMIT", "40"))
OUT = os.path.join(os.environ["CREXI_BASELINE_ROOT"], "runs", f"tier_sweep_arm{os.environ['CREXI_BASELINE_ARM']}.jsonl")

cur = {}
_llm, _val = LI._try_llm_extract, LI._validate_facts
def t_llm(*a, **k):
    try:
        o = _llm(*a, **k)
        cur["llm_returned"] = None if o is None else {
            "gross": getattr(o, "gross_monthly_rent", None),
            "conf": getattr(o, "confidence", None),
            "per_unit": list(getattr(o, "per_unit_rents", []) or [])}
        return o
    except Exception as e:
        cur["llm_error"] = f"{type(e).__name__}"; raise
def t_val(f, l):
    o = _val(f, l)
    cur["validated"] = o is not None
    cur["val_input_gross"] = getattr(f, "gross_monthly_rent", None)
    if o is None and getattr(f, "gross_monthly_rent", None):
        u = l.units or 4
        cur["band_ceiling"] = u * LI._MAX_UNIT_RENT
        cur["over_band"] = f.gross_monthly_rent > cur["band_ceiling"]
    return o
LI._try_llm_extract, LI._validate_facts = t_llm, t_val

s = Settings()
eng = create_engine(s.database_url, future=True)
with Session(eng) as sess:
    rows = sess.execute(
        select(CrexiListingORM)
        .where(CrexiListingORM.marketing_description.isnot(None))
        .order_by(CrexiListingORM.asset_id).limit(LIMIT)).scalars().all()
    listings = [(r.asset_id, listing_from_row(r)) for r in rows]

client = CrexiClient(token=s.crexi_token, base_url=s.crexi_base_url,
                     requests_per_second=s.crexi_requests_per_second, max_retries=s.crexi_max_retries)
tiers, band_kills, n = Counter(), [], 0
with open(OUT, "w") as fh:
    for asset_id, lst in listings:
        cur.clear(); t0 = time.time()
        try:
            sig = LI.resolve_income(lst, s, crexi_client=client)
            rec = {"asset_id": asset_id, "units": lst.units, "ask": lst.asking_price,
                   "method": sig.method, "source": sig.source,
                   "gross": sig.gross_monthly_rent, "confidence": sig.confidence,
                   "ms": round((time.time()-t0)*1000), **cur}
        except Exception as e:
            rec = {"asset_id": asset_id, "error": f"{type(e).__name__}: {e}", **cur}
        fh.write(json.dumps(rec) + "\n"); fh.flush()
        n += 1
        tiers[rec.get("method", "ERROR")] += 1
        if rec.get("over_band"):
            band_kills.append((asset_id, lst.units, rec.get("val_input_gross"), rec.get("band_ceiling")))

print(f"\nARM {os.environ['CREXI_BASELINE_ARM']}  n={n}   -> {OUT}")
print("tier distribution:")
for k, v in tiers.most_common():
    print(f"   {str(k):16s} {v:3d}  ({100*v/max(n,1):.0f}%)")
print(f"\nF-B1 (correct-looking LLM extraction killed by the band): {len(band_kills)}")
for a, u, g, c in band_kills:
    print(f"   asset {a}  {u}u  llm_gross=${g:,.0f}/mo  ceiling=${c:,.0f}/mo  over by ${g-c:,.0f}")
