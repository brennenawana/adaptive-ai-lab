"""Isolate the income ladder on one real listing, one factor at a time."""
import os, sys
sys.path.insert(0, os.environ["WHOLESALING_REPO"] + "/backend")
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.config.settings import Settings
from app.db.models import CrexiListingORM
from app.persistence.crexi_listing_store import listing_from_row
from app.services.listing_income import resolve_income, _validate_facts, _MAX_UNIT_RENT, _MIN_UNIT_RENT
from app.providers.crexi.client import CrexiClient

ASSET = sys.argv[1] if len(sys.argv) > 1 else "2660435"
s = Settings()
eng = create_engine(s.database_url, future=True)
with Session(eng) as sess:
    row = sess.execute(select(CrexiListingORM).where(CrexiListingORM.asset_id == ASSET)).scalar_one()
    listing = listing_from_row(row)

client = CrexiClient(token=s.crexi_token, base_url=s.crexi_base_url,
                     requests_per_second=s.crexi_requests_per_second, max_retries=s.crexi_max_retries)

print(f"asset={ASSET}  units={listing.units}  ask=${listing.asking_price:,.0f}")
sig = resolve_income(listing, s, crexi_client=client)
print(f"\nARM {os.environ.get('CREXI_BASELINE_ARM')} ladder result:")
print(f"  method     {sig.method}")
print(f"  source     {sig.source}")
print(f"  gross      ${sig.gross_monthly_rent:,.0f}/mo" if sig.gross_monthly_rent else "  gross      None")
print(f"  confidence {sig.confidence}")

# What WOULD the band do to the truth stated in the description?
stated_annual = 552_000.0
gross_true = stated_annual / 12
units = listing.units or 4
hi = units * _MAX_UNIT_RENT
print(f"\nband check against the description's OWN stated income:")
print(f"  stated  ${stated_annual:,.0f}/yr -> ${gross_true:,.0f}/mo across {units} units")
print(f"  allowed band for gross: ${_MIN_UNIT_RENT:,.0f} .. ${hi:,.0f}   (units x _MAX_UNIT_RENT)")
print(f"  VERDICT: {'REJECTED - exceeds band by $%.0f' % (gross_true - hi) if gross_true > hi else 'accepted'}")
