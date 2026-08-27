import os, sys
sys.path.insert(0, os.environ["WHOLESALING_REPO"] + "/backend")
from datetime import UTC, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.config.settings import Settings
from app.config.parameters import DEFAULT_PARAMETERS
from app.services.crexi_value_route import value_route_pass
from app.services.scrape_profile_service import get_effective_scrape_config
from app.providers.crexi.client import CrexiClient

s = Settings()
eng = create_engine(s.database_url, future=True)
client = CrexiClient(token=s.crexi_token, base_url=s.crexi_base_url,
                     requests_per_second=s.crexi_requests_per_second, max_retries=s.crexi_max_retries)
lines = []
with Session(eng) as sess:
    cfg = get_effective_scrape_config(sess)
    print("cfg.states =", getattr(cfg, "states", None), " types =", getattr(cfg, "property_types", None),
          " units =", getattr(cfg, "unit_min", None), "-", getattr(cfg, "unit_max", None))
    st = value_route_pass(sess, client, cfg, DEFAULT_PARAMETERS, s,
                          apply=True, all_rows=True, overlap_minutes=120, max_deals=1,
                          states=("FL",), keep_raw=True, now=datetime.now(UTC),
                          chunk_limit=1, after_key=None, stamp_cursor=False,
                          listing_timeout_s=None, skip_asset_ids=frozenset(),
                          parcel_registry=None, reverse_geocoder=None, log=lines.append)
print("stats:", {k: getattr(st, k) for k in ("candidates","qualified","processed","routed","held_for_review","skipped_no_address") if hasattr(st, k)})
for l in lines[:8]: print("  log:", l)
