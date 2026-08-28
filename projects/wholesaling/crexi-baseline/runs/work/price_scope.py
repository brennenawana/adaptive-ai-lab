"""How big is the FL multifamily population under various price caps?

If a buy-box cap puts the population under Crexi's ~1,499 pagination ceiling,
partitioning becomes UNNECESSARY -- one scoped sweep covers the whole scope with
no county mess and no coverage loss. One count=1 probe per cap.
"""
import os, sys
sys.path.insert(0, os.environ["WHOLESALING_REPO"] + "/backend")
from dataclasses import replace
from app.config.settings import Settings
from app.providers.crexi.client import CrexiClient
from app.providers.crexi.assets_search import SweepScope, AssetsSearchSweeper

s = Settings()
c = CrexiClient(token=s.crexi_token, base_url=s.crexi_base_url,
                requests_per_second=s.crexi_requests_per_second, max_retries=s.crexi_max_retries)
sw = AssetsSearchSweeper(c, page_size=1)
base = SweepScope(states=("FL",), types=("multifamily",))

CEILING = 1499
print(f"{'price cap':>14s}  {'in scope':>9s}  {'vs 1499 ceiling':>16s}")
print("-" * 46)
prev = None
for cap in (None, 2_000_000, 1_500_000, 1_000_000, 800_000, 600_000, 400_000, 250_000):
    scope = base if cap is None else replace(base, asking_price_max=cap)
    try:
        n = sw.total_count(scope)
    except Exception as exc:
        print(f"{str(cap):>14s}  ERROR {type(exc).__name__}: {str(exc)[:60]}")
        continue
    label = "no cap" if cap is None else f"<= ${cap:,}"
    verdict = "ONE SWEEP OK" if (n or 0) <= CEILING else f"needs partitioning ({n - CEILING} over)"
    print(f"{label:>14s}  {n:>9,}  {verdict:>16s}")
