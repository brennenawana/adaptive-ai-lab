"""Same probe, but WRAPPING the private seams so the tier decision is visible."""
import os, sys, json
sys.path.insert(0, os.environ["WHOLESALING_REPO"] + "/backend")
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.config.settings import Settings
from app.db.models import CrexiListingORM
from app.persistence.crexi_listing_store import listing_from_row
from app.providers.crexi.client import CrexiClient
import app.services.listing_income as LI

ASSET = sys.argv[1] if len(sys.argv) > 1 else "2660435"
TRACE = []

_orig_llm = LI._try_llm_extract
_orig_val = LI._validate_facts

def traced_llm(*a, **k):
    try:
        out = _orig_llm(*a, **k)
        TRACE.append({"seam": "_try_llm_extract", "returned": None if out is None else {
            "confidence": getattr(out, "confidence", None),
            "gross_monthly_rent": getattr(out, "gross_monthly_rent", None),
            "per_unit_rents": list(getattr(out, "per_unit_rents", []) or []),
        }})
        return out
    except Exception as exc:
        TRACE.append({"seam": "_try_llm_extract", "raised": f"{type(exc).__name__}: {exc}"})
        raise

def traced_val(facts, listing):
    out = _orig_val(facts, listing)
    TRACE.append({"seam": "_validate_facts",
                  "input_gross": getattr(facts, "gross_monthly_rent", None),
                  "input_conf": getattr(facts, "confidence", None),
                  "accepted": out is not None})
    return out

LI._try_llm_extract = traced_llm
LI._validate_facts = traced_val

s = Settings()
eng = create_engine(s.database_url, future=True)
with Session(eng) as sess:
    row = sess.execute(select(CrexiListingORM).where(CrexiListingORM.asset_id == ASSET)).scalar_one()
    listing = listing_from_row(row)
client = CrexiClient(token=s.crexi_token, base_url=s.crexi_base_url,
                     requests_per_second=s.crexi_requests_per_second, max_retries=s.crexi_max_retries)

sig = LI.resolve_income(listing, s, crexi_client=client)
print(f"ARM {os.environ.get('CREXI_BASELINE_ARM')}  ->  method={sig.method}  gross=${(sig.gross_monthly_rent or 0):,.0f}  conf={sig.confidence}")
print("TIER TRACE:")
if not TRACE:
    print("   (no LLM seam was reached at all -- tier 1 never attempted)")
for t in TRACE:
    print("   " + json.dumps(t))
