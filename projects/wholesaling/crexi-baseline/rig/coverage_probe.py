#!/usr/bin/env python3
"""F-B14 probe: is the whole-state ``totalCount`` a real denominator, or a number?

The claim under test was authored by a DIFFERENT session and is being audited, not
continued: *county partitions reach 1,965 of 3,496 in-scope FL multifamily listings
(56%)*. A coverage loss and a reporting artefact are indistinguishable from inside
the partitioned run, so this probe attacks the denominator from outside it.

WHY THE OBVIOUS PROBE DOES NOT WORK
-----------------------------------
"Just run a whole-state paged sweep and count" cannot settle it. ``assets_search``
enforces ``offset + count < PAGE_WINDOW (1500)`` (``assets_search.py:180-182``:
``size = min(page_size, PAGE_WINDOW - 1 - offset)``, returning ``truncated`` when
``size <= 0``). A whole-state sweep therefore stops at **1,499 ids no matter what
the population is** -- so "the sweep returned fewer than 3,496" is guaranteed in
advance and carries zero information. Any probe that ignores this measures the
client's cap and reports it as Crexi's coverage.

THREE ARMS, EACH ABLE TO FALSIFY ON ITS OWN
-------------------------------------------
1. ``window`` -- page whole-state (NO county scoping) twice, once
   ``sortDirection=Descending`` and once ``Ascending``. Each arm is capped at 1,499
   by the window, but they enter the population from opposite ends, so their
   OVERLAP is the measurement:

     * population truly >= 2,998  ->  the two windows are DISJOINT, union ~2,998.
       2,998 > 1,965 proves reachable stock the county union never saw, with no
       reliance on ``totalCount`` being honest.
     * population truly ~1,965    ->  both windows enumerate most of the same set,
       union saturates near 1,965 and overlap is ~1,033. ``totalCount`` is then
       inflated and F-B14 is a reporting artefact -- the pre-registered falsifier.

   The discriminator is overlap, which no pagination cap can manufacture.

2. ``ceiling`` -- two single requests, ``offset+count = 1499`` and ``= 1500``, to
   establish whether the 1,499 ceiling is OURS (client refuses) or CREXI'S (API
   400s). ``SAFE_WINDOW = 1400`` (``crexi_ingest.py:61``) is a separate, lower
   partitioning threshold and is only ever compared against ``totalCount``; it
   never truncates a sweep in progress. Stating which cap is whose is required
   before any gap can be attributed to a county index.

3. ``price`` -- re-partition the SAME whole-state scope by asking price instead of
   county, using the product's own ``_price_bisect``. This is the load-bearing arm:
   it is an independent partitioning of the identical server-side scope. If county
   partitioning loses stock, price partitioning should recover it; if both land on
   the same ~1,965, two independent partition keys agree and ``totalCount`` is the
   outlier. Caveat, documented by the product itself at ``crexi_ingest.py:175-178``:
   unpriced listings "don't attach to price bands reliably", so this arm's misses
   are informative only in one direction.

Everything is recorded to its own cassette so the verdict is re-derivable offline.
Read-only: no DB writes, no ingest, no product file touched.

  ./rig/run.sh $CREXI_BASELINE_ROOT/rig/coverage_probe.py --arm all \
      --out runs/coverage_probe_FL.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
from datetime import UTC, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from cassette import from_env as cassette_from_env  # noqa: E402

#: Hard ceiling on outbound calls for the whole probe. A bounded live probe that
#: cannot state its own bound is not bounded.
MAX_REQUESTS = 400

_CALLS: list[dict] = []


def _install_call_log(client) -> None:
    """Count and log every outbound call, and ABORT at MAX_REQUESTS.

    Wraps the client instance (not the class) so the bound is a property of this
    probe rather than a global side effect.
    """
    orig = client._request

    def counted(method, path, *a, **k):
        if len(_CALLS) >= MAX_REQUESTS:
            raise SystemExit(
                f"coverage_probe: request budget exhausted at {MAX_REQUESTS} -- refusing "
                "to keep sweeping. Raise --max-requests deliberately or narrow the arm."
            )
        body = k.get("json_body")
        t0 = time.time()
        rec = {"method": method, "path": path,
               "body": {x: y for x, y in (body or {}).items() if x != "count"} if body else None,
               "offset": (body or {}).get("offset"), "count": (body or {}).get("count")}
        try:
            out = orig(method, path, *a, **k)
        except Exception as exc:  # noqa: BLE001 - the ceiling arm NEEDS the failure shape
            rec.update(error=f"{type(exc).__name__}: {str(exc)[:300]}",
                       ms=round((time.time() - t0) * 1000))
            _CALLS.append(rec)
            raise
        rec.update(error=None, ms=round((time.time() - t0) * 1000),
                   returned=len((out or {}).get("data") or []),
                   total_count=(out or {}).get("totalCount"))
        _CALLS.append(rec)
        return out

    client._request = counted


def _page_all(client, scope, *, direction: str, page_size: int = 100,
              max_pages: int = 25) -> dict:
    """Page one scope to exhaustion, honoring the product's own window arithmetic.

    Deliberately NOT ``AssetsSearchSweeper.sweep``: that method hardcodes
    ``sortDirection: Descending`` in ``SweepScope.body`` (``assets_search.py:90-91``),
    and the ascending arm is the entire discriminator. The offset/size arithmetic
    below is copied from ``sweep`` verbatim (``assets_search.py:177-197``) so the
    two arms differ in ONE key and nothing else -- if this reimplemented the paging
    loop differently, a difference in results would be unattributable.
    """
    from app.providers.crexi.assets_search import PAGE_WINDOW

    seen: dict[str, dict] = {}
    offset = 0
    pages = 0
    total: int | None = None
    truncated = False
    stop = None
    while True:
        if pages >= max_pages:
            stop, truncated = "max_pages", True
            break
        size = min(page_size, PAGE_WINDOW - 1 - offset)
        if size <= 0:
            stop, truncated = "page_window_exhausted", True
            break
        body = scope.body(offset=offset, count=size)
        body["sortDirection"] = direction
        payload = client.search_assets(body)
        items = payload.get("data") or []
        if total is None:
            total = payload.get("totalCount")
        pages += 1
        for it in items:
            aid = str(it.get("id") or "")
            if aid:
                seen.setdefault(aid, it)
        offset += len(items)
        if len(items) < size:
            stop = "short_page"
            break
        if total is not None and offset >= total:
            stop = "reached_total"
            break
    return {"direction": direction, "ids": seen, "pages": pages, "offset_reached": offset,
            "total_count": total, "truncated": truncated, "stop_reason": stop}


def arm_window(client, scope, page_size: int, max_pages: int) -> dict:
    out = {}
    for direction in ("Descending", "Ascending"):
        print(f"  window/{direction}: paging whole-state (no counties)...", file=sys.stderr)
        r = _page_all(client, scope, direction=direction, page_size=page_size,
                      max_pages=max_pages)
        print(f"    -> {len(r['ids'])} ids, {r['pages']} pages, offset={r['offset_reached']}, "
              f"total_count={r['total_count']}, stop={r['stop_reason']}", file=sys.stderr)
        out[direction] = r
    return out


#: Offsets probed to LOCATE the server's real pagination ceiling. The first two
#: straddle the ``PAGE_WINDOW = 1500`` boundary the code believes in; the rest walk
#: out past ``totalCount`` to find where the feed actually ends. Each probe returns
#: the asset id it saw, because a server that CLAMPS a too-deep offset answers 200
#: with the last page's content -- which would read as "coverage" to a naive
#: counter and is the single most dangerous way this probe could lie.
_CEILING_OFFSETS = (1498, 1499, 1500, 1600, 1900, 1960, 1964, 1965, 1966,
                    2000, 2500, 3000, 3400, 3494, 3495, 3496, 3600, 5000)


def arm_ceiling(client, scope) -> list[dict]:
    """Locate the server's real pagination ceiling, and test for offset CLAMPING."""
    probes = []
    for offset, count, expect in ((o, 1, f"offset+count={o + 1}") for o in _CEILING_OFFSETS):
        body = scope.body(offset=offset, count=count)
        rec = {"offset": offset, "count": count, "sum": offset + count, "expect": expect}
        try:
            payload = client.search_assets(body)
            data = payload.get("data") or []
            rec.update(ok=True, returned=len(data),
                       total_count=payload.get("totalCount"),
                       asset_id=str(data[0].get("id")) if data else None,
                       updated_on=(data[0].get("updatedOn") if data else None))
        except Exception as exc:  # noqa: BLE001 - the failure IS the result here
            rec.update(ok=False, error=f"{type(exc).__name__}: {str(exc)[:300]}")
        print(f"  ceiling: offset={offset:5d} -> "
              f"{('id=' + str(rec.get('asset_id')) + ' updated=' + str(rec.get('updated_on'))) if rec.get('ok') else rec.get('error')}",
              file=sys.stderr)
        probes.append(rec)
    return probes


def arm_examples(client, asset_ids: list[str]) -> dict:
    """Detail-fetch a small, explicitly-listed set of assets for the decision packet.

    The packet has to show the operator ``address / ask / units / first line of
    description`` per type combination. Address, ask and description all ride along on
    the ``/assets/search`` feed -- but ``units`` and ``property_sub_type`` live ONLY in
    the detail document, and the compound-type listings have never been detail-fetched
    (the exact-match gate drops them before the fetch). So the one question the operator
    most needs answered about compound types -- how many units are these, actually? --
    is unanswerable from anything already on disk.

    Deliberately NOT a sweep: the caller passes an explicit id list, 3 requests each.
    Read-only; nothing is normalized into the DB.
    """
    out: dict[str, dict] = {}
    for i, aid in enumerate(asset_ids, 1):
        rec: dict = {"asset_id": aid}
        try:
            rec["detail"] = client.get_property_asset(aid)
        except Exception as exc:  # noqa: BLE001
            rec["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        out[aid] = rec
        if i % 10 == 0:
            print(f"  examples: {i}/{len(asset_ids)}", file=sys.stderr)
    return out


def arm_variants(client, scope, variants: list[str]) -> list[dict]:
    """Does ``counties`` match the record's county string LITERALLY?

    The miss set splits almost perfectly by the raw form of ``locations[].county``
    in the payload: ``"Duval County"`` is reachable (2% miss), bare ``"Duval"`` is
    not (99% miss), ``"MANATEE"`` is not (93% miss). That pattern has exactly one
    cheap explanation and one cheap test -- ask the filter for the bare form and see
    whether the missing records come back.

    PRE-REGISTERED, stated before the calls were made:
      * ``counties:["Duval"]``   -> ~106 (the payload count for that exact string),
        NOT 25 (what ``"Duval County"`` returns) and NOT 131 (their sum).
      * ``counties:["MANATEE"]`` -> ~23, distinct from ``"Manatee County"`` -> 22.
      * If instead the filter is case/suffix-INSENSITIVE, every variant of one county
        returns the SAME number -- which would refute a literal match and send the
        explanation back to "the index is simply sparse".

    One ``count=1`` request per variant.
    """
    from dataclasses import replace

    out = []
    for name in variants:
        sub = replace(scope, counties=(name,))
        rec = {"counties": name}
        try:
            payload = client.search_assets(sub.body(offset=0, count=1))
            rec["total_count"] = payload.get("totalCount")
        except Exception as exc:  # noqa: BLE001
            rec["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        print(f"  variant counties={name!r:26} -> totalCount={rec.get('total_count', rec.get('error'))}",
              file=sys.stderr)
        out.append(rec)
    return out


def arm_price(client, scope, page_size: int, max_pages: int) -> dict:
    """Re-partition the whole state by ASKING PRICE using the product's own bisector."""
    from app.providers.crexi.assets_search import AssetsSearchSweeper
    from app.services.crexi_ingest import _price_bisect

    sweeper = AssetsSearchSweeper(client, page_size=page_size)
    warnings: list[str] = []
    print("  price: bisecting the whole-state scope by asking price...", file=sys.stderr)
    bands = _price_bisect(sweeper, scope, warnings)
    print(f"    -> {len(bands)} price bands, {len(warnings)} warnings", file=sys.stderr)

    seen: dict[str, dict] = {}
    band_rows = []
    for band in bands:
        r = _page_all(client, band, direction="Descending", page_size=page_size,
                      max_pages=max_pages)
        band_rows.append({
            "asking_price_min": band.asking_price_min, "asking_price_max": band.asking_price_max,
            "ids": len(r["ids"]), "total_count": r["total_count"], "pages": r["pages"],
            "truncated": r["truncated"], "stop_reason": r["stop_reason"],
        })
        print(f"    band [{band.asking_price_min},{band.asking_price_max}]: "
              f"{len(r['ids'])} ids / total_count={r['total_count']} "
              f"{'TRUNCATED' if r['truncated'] else ''}", file=sys.stderr)
        for aid, it in r["ids"].items():
            seen.setdefault(aid, it)
    return {"bands": band_rows, "warnings": warnings, "ids": seen}


def main() -> int:
    global MAX_REQUESTS
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="all", choices=("all", "window", "ceiling", "price", "variants", "examples"))
    ap.add_argument("--state", default="FL")
    ap.add_argument("--page-size", type=int, default=100)
    ap.add_argument("--max-pages", type=int, default=25,
                    help="per-scope page cap (the window itself stops at 15 pages of 100)")
    ap.add_argument("--max-requests", type=int, default=MAX_REQUESTS)
    ap.add_argument("--asset-ids", default=None,
                    help="comma-separated asset ids to detail-fetch (arm=examples)")
    ap.add_argument("--variants", default=None,
                    help="comma-separated county filter values to probe (arm=variants)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    MAX_REQUESTS = args.max_requests

    cas = cassette_from_env()
    if cas is not None:
        cas.install()
        print(f"cassette: mode={cas.mode} entries={len(cas.entries)} path={cas.path}",
              file=sys.stderr)

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.config.settings import Settings
    from app.providers.crexi.client import CrexiClient
    from app.services.crexi_image_client import build_crexi_mirror
    from app.services.crexi_ingest import scope_for_state
    from app.services.scrape_profile_service import get_effective_scrape_config

    s = Settings()
    mirror = build_crexi_mirror(s)
    if mirror.enabled:  # second, in-process guard: this arm makes LIVE calls
        raise SystemExit("coverage_probe: photo mirror is ENABLED -- refusing to run")

    eng = create_engine(s.database_url, future=True)
    with Session(eng) as sess:
        cfg = get_effective_scrape_config(sess)
    eng.dispose()

    state = args.state.strip().upper()
    scope = scope_for_state(cfg, state)
    print(f"scope: {json.dumps(scope.body(offset=0, count=args.page_size))}", file=sys.stderr)

    client = CrexiClient(token=s.crexi_token, base_url=s.crexi_base_url,
                         requests_per_second=s.crexi_requests_per_second,
                         max_retries=s.crexi_max_retries)
    _install_call_log(client)

    t0 = time.time()
    result: dict = {}
    payloads: dict[str, dict] = {}

    # The headline denominator, re-read now rather than trusted from the frozen run.
    total_now = client.search_assets(scope.body(offset=0, count=1)).get("totalCount")
    print(f"whole-state totalCount NOW = {total_now}", file=sys.stderr)

    if args.arm in ("all", "window"):
        w = arm_window(client, scope, args.page_size, args.max_pages)
        result["window"] = {
            d: {k: v for k, v in r.items() if k != "ids"} | {"n_ids": len(r["ids"])}
            for d, r in w.items()
        }
        result["window_ids"] = {d: sorted(r["ids"]) for d, r in w.items()}
        for r in w.values():
            payloads.update(r["ids"])

    if args.arm in ("all", "ceiling"):
        result["ceiling"] = arm_ceiling(client, scope)

    if args.arm == "examples":
        ids = [x.strip() for x in (args.asset_ids or "").split(",") if x.strip()]
        print(f"  examples: detail-fetching {len(ids)} assets "
              f"({len(ids) * 3} requests)", file=sys.stderr)
        result["examples"] = arm_examples(client, ids)

    if args.arm == "variants":
        result["variants"] = arm_variants(
            client, scope, [x.strip() for x in (args.variants or "").split(",") if x.strip()])

    if args.arm in ("all", "price"):
        p = arm_price(client, scope, args.page_size, args.max_pages)
        result["price"] = {"bands": p["bands"], "warnings": p["warnings"],
                           "n_ids": len(p["ids"])}
        result["price_ids"] = sorted(p["ids"])
        payloads.update(p["ids"])

    manifest = {
        "_manifest": {
            "probe": "F-B14 coverage",
            "state": state,
            "arm_env": os.environ.get("CREXI_BASELINE_ARM"),
            "run_at": datetime.now(UTC).isoformat(),
            "scope_body": scope.body(offset=0, count=args.page_size),
            "page_size": args.page_size,
            "max_pages": args.max_pages,
            "max_requests": MAX_REQUESTS,
            "whole_state_total_count": total_now,
            "requests_made": len(_CALLS),
            "wall_s": round(time.time() - t0, 1),
            "cassette": (cas.summary() if cas else None),
            "crexi_base_url": s.crexi_base_url,
        },
        "result": result,
    }

    out = args.out
    if out:
        path = pathlib.Path(out)
        if not path.is_absolute():
            path = pathlib.Path(os.environ["CREXI_BASELINE_ROOT"]) / out
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps(manifest, default=str) + "\n")
            for aid, item in sorted(payloads.items()):
                fh.write(json.dumps({"asset_id": aid, "payload": item}, default=str) + "\n")
        with path.with_suffix(".calls.jsonl").open("w", encoding="utf-8") as fh:
            for c in _CALLS:
                fh.write(json.dumps(c, default=str) + "\n")
        print(f"wrote {path} ({len(payloads)} payloads) and "
              f"{path.with_suffix('.calls.jsonl')} ({len(_CALLS)} calls)", file=sys.stderr)

    print(json.dumps(manifest["_manifest"], indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
