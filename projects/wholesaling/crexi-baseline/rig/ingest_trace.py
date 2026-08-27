"""Per-ASSET trace of the Crexi INGEST funnel: sweep -> stored ``crexi_listings`` row.

The value-route lane already has ``trace.py`` (24 seams, income -> gate). That covers
only what happens AFTER a listing is a row. This module covers the half before it:
for every asset ``/assets/search`` returns, WHERE IT WENT AND WHY.

``IngestStats`` already counts the funnel in aggregate (swept / type_matched /
unpriced_excluded / unchanged / fetched / fetch_errors / strict_matches / upserted).
What it cannot answer is WHICH asset died WHERE -- and two of the eleven steps
(cross-partition dedupe, normalization) have no counter at all.

Same discipline as trace.py: wrap the product's own seams at RUNTIME (no product-code
edits), ``install()`` ASSERTS every target exists and records its source digest, one
JSONL record per asset.

Two deliberate differences from trace.py:

* **No ``_boundary()``.** trace.py needs one because the value route interleaves seams
  per listing with no stable order. ``ingest_state`` is PHASE-BATCHED -- it sweeps
  everything, then gates everything, then fetches one at a time -- so records are keyed
  by ``asset_id`` in a dict and the misattribution class boundary-detection exists to
  prevent cannot arise here.
* **Capture + derive, then RECONCILE.** Most funnel steps are inline comprehensions
  (``matched = [s for s in stubs.values() if ...]``), not callables, so they cannot be
  wrapped. Those are DERIVED by re-running the product's own predicate per asset -- and
  every derived population is then checked against the corresponding ``IngestStats``
  counter. A per-asset attribution that does not sum to the aggregate is wrong, and the
  reconciliation says so out loud instead of leaving it to be believed.

  ./rig/run.sh $CREXI_BASELINE_ROOT/rig/ingest_trace.py --states FL --apply --max-fetch 150
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime

sys.path.insert(0, os.path.join(os.environ["WHOLESALING_REPO"], "backend"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cassette import from_env as cassette_from_env  # noqa: E402
from defects import DEFECTS  # noqa: E402

# ---------------------------------------------------------------------------
# capture state
# ---------------------------------------------------------------------------
PATCHES: list[dict] = []
SWEEPS: list[dict] = []      # one per AssetsSearchSweeper.sweep() call, IN CALL ORDER
PROBES: list[dict] = []      # total_count() partition probes
HTTP: list[dict] = []        # every outbound Crexi request
CURSOR: dict = {}            # step 1 (read) + step 11 (write)
STORED: dict = {}            # step 6: asset_id -> stored source_updated_on (real datetimes)
FETCH: dict[str, dict] = {}  # step 7
NORM: dict[str, dict] = {}   # step 8
STRICT: dict[str, dict] = {} # step 9
CLAMP: dict[str, dict] = {}  # step 10 (clamp_to_column_limits)
UPSERT: dict[str, dict] = {} # step 10 (batched upsert)
BUMPED: list[str] = []       # step 11
TYPE_GATE_CALLS: list[dict] = []  # step 4, observed (reconciles the derived population)

#: asset_id currently inside the detail-fetch try block, so a CrexiError raised by any of
#: the three calls is attributed to the right asset. Set by the fetch loop's only
#: observable entry point -- the GET /assets/{id} request itself.
_IN_FLIGHT: dict = {"asset_id": None}


def _digest(obj) -> str:
    try:
        return hashlib.sha256(inspect.getsource(obj).encode()).hexdigest()[:12]
    except (OSError, TypeError):
        return "const:" + hashlib.sha256(repr(obj).encode()).hexdigest()[:10]


def _iso(dt) -> str | None:
    return dt.isoformat() if isinstance(dt, datetime) else None


def scope_label(scope) -> str:
    """A stable, human-readable name for one sweep partition.

    Must be stable across replays: it is the partition identity the cross-partition
    dedupe finding is stated in terms of, so a label that moved between runs would make
    "the winner is stable" unfalsifiable.
    """
    state = "/".join(scope.states) or "?"
    part = scope.counties[0] if scope.counties else "WHOLE-STATE"
    band = ""
    if scope.asking_price_min is not None or scope.asking_price_max is not None:
        band = f"[{scope.asking_price_min},{scope.asking_price_max}]"
    return f"{state}:{part}{band}"


# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------
def install() -> None:
    """Wrap every ingest seam. Fails loudly if a target has moved.

    The assert list is the point: these are private names in product modules, and a
    rename must break the trace visibly rather than silently drop a funnel step -- which
    would read as "nothing died there", the single most dangerous wrong answer this
    module can give.
    """
    import app.providers.crexi.assets_search as AS
    import app.providers.crexi.listing_filters as LF
    import app.providers.crexi.listing_normalize as LN
    import app.providers.normalization as NORMZ
    import app.persistence.crexi_listing_store as LS
    import app.services.crexi_ingest as CI
    from app.providers.crexi.client import CrexiClient

    targets = [
        # step 1: watermark / fingerprint gate
        (CI, "get_scrape_cursor"), (CI, "scope_fingerprint"), (CI, "scope_for_state"),
        (CI, "DEFAULT_OVERLAP_MINUTES"),
        # step 2: partitioned sweep
        (CI, "backfill_partitions"), (CI, "SAFE_WINDOW"),
        (AS, "AssetsSearchSweeper"), (AS, "AssetStub"), (AS, "SweepScope"), (AS, "to_search_stub"),
        # steps 4/9: the client-side gates
        (LF, "ListingFilters"), (LN, "is_strict_mf_2_4"),
        # step 6: detail-fetch economy
        (CI, "_stored_updated_map"), (CI, "_aware"),
        # step 7: fetch + error breaker
        (CI, "_FETCH_ERROR_BREAKER"),
        # step 8: normalization
        (CI, "normalize_listing"),
        # step 10: row mapping + clamp + batched upsert
        (CI, "listing_row"), (CI, "upsert_listing_rows"), (CI, "update_photo_mirror"),
        (LS, "clamp_to_column_limits"), (LS, "_STR_LIMITS"), (LS, "_INT_COLS"),
        (LS, "_INT4_MAX"), (LS, "SCALAR_FIELDS"), (LS, "_ENRICHMENT_FIELDS"),
        # step 11: last-seen bump + cursor stamp
        (CI, "bump_last_seen"), (CI, "upsert_scrape_cursor"), (CI, "_new_watermark"),
        # the plausibility envelopes the ledger reports a COUNTERFACTUAL against
        # (see fields_of(): this path never calls them -- that is the finding)
        (NORMZ, "plausible_price"), (NORMZ, "plausible_sqft"), (NORMZ, "plausible_year_built"),
        (NORMZ, "plausible_units"), (NORMZ, "plausible_latlng"), (NORMZ, "PRICE_MIN"),
    ]
    for mod, name in targets:
        obj = getattr(mod, name, None)
        if obj is None:
            raise SystemExit(
                f"ingest_trace: seam {mod.__name__}.{name} does not exist -- product code moved"
            )
        PATCHES.append({"target": f"{mod.__name__}.{name}", "source_sha12": _digest(obj)})

    # ---- every outbound Crexi request (replayability + fetch-error attribution) ----
    _req = CrexiClient._request

    def t_req(self, method, path, *a, **k):
        t0 = time.time()
        err = None
        try:
            return _req(self, method, path, *a, **k)
        except Exception as exc:
            err = f"{type(exc).__name__}: {str(exc)[:160]}"
            raise
        finally:
            HTTP.append({"method": method, "path": path, "error": err,
                         "ms": round((time.time() - t0) * 1000),
                         "asset_id": _IN_FLIGHT["asset_id"]})

    CrexiClient._request = t_req

    # ---- step 1: the watermark / fingerprint gate ----------------------------
    _cur, _fp = CI.get_scrape_cursor, CI.scope_fingerprint

    def t_cursor(session, key):
        row = _cur(session, key)
        CURSOR["read"] = {
            "key": key,
            "existed": row is not None,
            "stored_fingerprint": getattr(row, "fingerprint", None),
            "last_seen_updated_on": _iso(getattr(row, "last_seen_updated_on", None)),
            "backfilled_at": _iso(getattr(row, "backfilled_at", None)),
        }
        return row

    def t_fp(scope):
        out = _fp(scope)
        CURSOR.setdefault("run_fingerprint", out)
        return out

    CI.get_scrape_cursor, CI.scope_fingerprint = t_cursor, t_fp

    # ---- step 2: partition probes + the sweep itself -------------------------
    _sweep, _total = AS.AssetsSearchSweeper.sweep, AS.AssetsSearchSweeper.total_count

    def t_sweep(self, scope, *, watermark=None, max_pages=None):
        t0 = time.time()
        res = _sweep(self, scope, watermark=watermark, max_pages=max_pages)
        SWEEPS.append({
            "partition": scope_label(scope),
            "order": len(SWEEPS),
            "counties": list(scope.counties),
            "include_unpriced": scope.include_unpriced,
            "watermark": _iso(watermark),
            "total_count": res.total_count,
            "pages": res.pages,
            "truncated": res.truncated,
            "n_stubs": len(res.stubs),
            # The ORDERED stub ids are the whole cross-partition-dedupe finding: the
            # winner of a duplicate is whichever partition ran first, and that is only
            # checkable if the order is recorded rather than inferred.
            "stub_ids": [s.asset_id for s in res.stubs],
            "ms": round((time.time() - t0) * 1000),
        })
        for s in res.stubs:
            STUBS.setdefault(s.asset_id, s)
        return res

    def t_total(self, scope):
        n = _total(self, scope)
        PROBES.append({"partition": scope_label(scope), "total_count": n})
        return n

    AS.AssetsSearchSweeper.sweep = t_sweep
    AS.AssetsSearchSweeper.total_count = t_total

    # ---- step 4: the stub type gate ------------------------------------------
    # Called as `filters.stub_type_ok(s.type_str)` inside a comprehension -- it never
    # sees the asset id, so this records only the observed (input, verdict) pairs. The
    # per-asset verdict is DERIVED in derive() by re-running the same predicate; these
    # calls exist to prove the derivation saw the same population the product did.
    _sto = LF.ListingFilters.stub_type_ok
    UNWRAPPED["stub_type_ok"] = _sto

    def t_stub_type(self, type_str):
        ok = _sto(self, type_str)
        TYPE_GATE_CALLS.append({"type_str": type_str, "ok": ok})
        return ok

    LF.ListingFilters.stub_type_ok = t_stub_type

    # ---- step 6: the detail-fetch economy's input ----------------------------
    _sum = CI._stored_updated_map

    def t_stored(session, asset_ids):
        out = _sum(session, asset_ids)
        # Datetimes, not their ISO strings: the economy test is `stub.updated_on <=
        # _aware(held)`, and reproducing it on strings would be a lexical comparison
        # that happens to agree -- until a tz offset or microsecond width differs.
        STORED.update(out)
        return out

    CI._stored_updated_map = t_stored

    # ---- step 8: normalization ------------------------------------------------
    _norm = CI.normalize_listing

    def t_norm(stub, detail, brokers, *, gallery=None, market=None, as_of=None, **k):
        aid = _IN_FLIGHT["asset_id"]
        listing = _norm(stub, detail, brokers, gallery=gallery, market=market, as_of=as_of, **k)
        NORM[aid] = {
            "returned_none": listing is None,
            "detail_keys": sorted(detail.keys()) if isinstance(detail, dict) else None,
            "n_brokers": len(brokers or []),
            "n_gallery": len(gallery or []),
        }
        if listing is not None:
            NORM[aid]["fields"] = fields_of(listing, detail)
        return listing

    CI.normalize_listing = t_norm

    # ---- step 9: the strict type + unit-band filter ---------------------------
    _matches = LF.ListingFilters.matches

    def t_matches(self, listing):
        ok = _matches(self, listing)
        STRICT[str(listing.asset_id)] = {"match": ok, "reason": None if ok else strict_reason(self, listing)}
        return ok

    LF.ListingFilters.matches = t_matches

    # ---- step 10a: clamp_to_column_limits ------------------------------------
    # Patched on the STORE module, not the ingest one: `listing_row` resolves the name
    # from its own module globals at call time, so this observes the real call and the
    # row dict carries its own asset_id -- no in-flight context needed.
    _clamp = LS.clamp_to_column_limits
    watched = set(LS._STR_LIMITS) | set(LS._INT_COLS)

    def t_clamp(row):
        before = {c: row.get(c) for c in watched if row.get(c) is not None}
        out = _clamp(row)
        aid = str(out.get("asset_id"))
        truncated = {c: {"from_len": len(before[c]), "to_len": LS._STR_LIMITS[c]}
                     for c in before
                     if isinstance(before[c], str) and before[c] != out.get(c)}
        nulled = {c: before[c] for c in before
                  if isinstance(before[c], int) and not isinstance(before[c], bool)
                  and out.get(c) is None}
        CLAMP[aid] = {"truncated": truncated, "nulled_int4": nulled}
        return out

    LS.clamp_to_column_limits = t_clamp

    # ---- step 10b: the batched upsert ----------------------------------------
    # insert-vs-update is only knowable BEFORE the statement runs, so the pre-existing
    # ids are read inside the wrapper rather than reconstructed after the fact.
    _upsert = CI.upsert_listing_rows

    def t_upsert(session, rows, *, dialect):
        from sqlalchemy import select as _select
        from app.db.models import CrexiListingORM as ORM

        ids = [r["asset_id"] for r in rows]
        prior = {
            r[0]: {"is_sold": r[1], "property_record_id": r[2], "owner_name": r[3]}
            for r in session.execute(
                _select(ORM.asset_id, ORM.is_sold, ORM.property_record_id, ORM.owner_name)
                .where(ORM.asset_id.in_(ids))
            ).all()
        }
        feed_owned = set(rows[0].keys()) - {"asset_id", "first_seen_at"} if rows else set()
        out = _upsert(session, rows, dialect=dialect)
        for r in rows:
            aid = r["asset_id"]
            was = prior.get(aid)
            UPSERT[aid] = {
                "mode": "update" if was else "insert",
                "batch_size": len(rows),
                # The columns the ON CONFLICT clause deliberately does NOT refresh --
                # structural, identical for every row, so the list itself lives in the
                # manifest and only its size is carried per asset. See write_gate_note()
                # for why this is not the confidence gate the audit went looking for.
                "n_not_refreshed": len(set(LS._ENRICHMENT_FIELDS) - feed_owned),
                "is_sold_sticky_suppressed": bool(
                    was and was["is_sold"] is True and r.get("is_sold") is not True
                ),
                "had_enrichment": bool(was and (was["property_record_id"] or was["owner_name"])),
            }
        return out

    CI.upsert_listing_rows = t_upsert

    # ---- step 11: last-seen bump + cursor stamp -------------------------------
    _bump, _stamp = CI.bump_last_seen, CI.upsert_scrape_cursor

    def t_bump(session, asset_ids, *, seen_at=None):
        BUMPED.extend(asset_ids)
        return _bump(session, asset_ids, seen_at=seen_at)

    def t_stamp(session, key, **k):
        CURSOR["write"] = {"key": key, "fingerprint": k.get("fingerprint"),
                           "last_seen_updated_on": _iso(k.get("last_seen_updated_on")),
                           "backfilled_at": _iso(k.get("backfilled_at"))}
        return _stamp(session, key, **k)

    CI.bump_last_seen, CI.upsert_scrape_cursor = t_bump, t_stamp


STUBS: dict = {}      # asset_id -> AssetStub, populated by the sweep seam
#: Pre-patch originals. derive() re-runs the product's predicates to reproduce the inline
#: comprehensions -- through the ORIGINALS, so the derivation cannot pollute the observed
#: call counts it is then reconciled against.
UNWRAPPED: dict = {}


# ---------------------------------------------------------------------------
# per-field arrival state (step 8 output) + the plausibility counterfactual
# ---------------------------------------------------------------------------
#: Fields whose value has a plausibility envelope in providers/normalization.py.
#: The envelope is applied by ``registry._sanitize_record`` at the MLS/registry merge
#: boundary, which the Crexi ingest never reaches -- so what this records is a
#: COUNTERFACTUAL ("would be nulled there"), never an observed nulling.
_ENVELOPES = {
    "asking_price": "plausible_price",
    "building_sqft": "plausible_sqft",
    "year_built": "plausible_year_built",
    "units": "plausible_units",
}

_UNIT_PROSE = re.compile(
    r"\b(\d{1,3})\s*[-\s]?\s*unit\b|\bunits?\s*[:=]\s*(\d{1,3})\b|\b(duplex|triplex|fourplex|quadplex|quadruplex)\b",
    re.I,
)


def fields_of(listing, detail: dict) -> dict:
    """Per-field arrival state after normalization, plus the bounds counterfactual.

    ``state`` is one of ``populated`` / ``null``. ``would_null_at_merge_boundary`` marks a
    populated value that ``registry._sanitize_record`` WOULD null -- reported separately
    from ``state`` precisely because it does not happen on this path.
    """
    import app.persistence.crexi_listing_store as LS
    import app.providers.normalization as NORMZ

    out: dict = {}
    for f in LS.SCALAR_FIELDS:
        v = getattr(listing, f, None)
        rec = {"state": "null" if v is None else "populated"}
        env = _ENVELOPES.get(f)
        if env and v is not None:
            if getattr(NORMZ, env)(v) is None:
                rec["would_null_at_merge_boundary"] = env
        out[f] = rec
    lat, lon = NORMZ.plausible_latlng(listing.latitude, listing.longitude)
    if listing.latitude is not None and lat is None:
        out["latitude"]["would_null_at_merge_boundary"] = "plausible_latlng"
        out["longitude"]["would_null_at_merge_boundary"] = "plausible_latlng"
    for f in ("photo_urls", "brokers", "summary_details"):
        seq = getattr(listing, f, None) or ()
        out[f] = {"state": "populated" if len(seq) else "null", "n": len(seq)}
    out["_units_evidence"] = units_evidence(listing, detail)
    return out


def units_evidence(listing, detail: dict) -> dict:
    """Does the RAW payload carry unit information normalization did not map?

    The lead this exists to settle: 29/100 stored listings have ``units`` NULL. Either
    Crexi genuinely does not state the count, or ``normalize_listing`` fails to map it.
    Those are different defects with different fixes, and only the raw payload can tell
    them apart -- so the verdict is derived from the payload, never assumed.
    """
    from app.providers.crexi.listing_normalize import _as_int, _summary_map

    summary = _summary_map(detail.get("summaryDetails")) if isinstance(detail, dict) else {}
    raw_units = summary.get("Units")
    other_keys = sorted(k for k in summary if "unit" in k.lower() and k != "Units")
    prose = " ".join(str(x or "") for x in (listing.property_name, listing.marketing_description))
    m = _UNIT_PROSE.search(prose)

    if listing.units is not None:
        verdict = "mapped"
    elif raw_units is not None and _as_int(raw_units) is None:
        verdict = "parse_failure"          # the key IS there; _as_int could not read it
    elif raw_units is not None:
        verdict = "unreachable"            # would mean _as_int succeeded but units is None
    elif other_keys:
        verdict = "unmapped_summary_key"   # a different summaryDetails key carries it
    elif m:
        verdict = "prose_only"             # stated in the description, never structured
    else:
        verdict = "absent_from_source"     # Crexi genuinely does not state it

    return {"verdict": verdict, "summary_units_raw": raw_units,
            "other_unit_keys": other_keys,
            "prose_match": m.group(0) if m else None,
            "n_summary_keys": len(summary)}


def strict_reason(filters, listing) -> dict:
    """Decompose a ``ListingFilters.matches`` rejection into WHICH gate failed.

    Mirrors the order in ``listing_filters.matches`` and reads the product's OWN bounds,
    so a config change moves this with it. ``unit_unknown`` and ``unit_out_of_band`` are
    kept apart deliberately: the GOAL's first lead is exactly that distinction, and a
    single "unit band" bucket cannot answer it.
    """
    ptypes = filters.property_types
    if (listing.property_type or "").strip().lower() not in ptypes:
        return {"gate": "property_type", "detail": f"{listing.property_type!r} not in {list(ptypes)}"}
    if not (filters.unit_min is None and filters.unit_max is None):
        if listing.units is None:
            return {"gate": "unit_unknown",
                    "detail": f"units is None and a bound is set ({filters.unit_min}-{filters.unit_max})"}
        if filters.unit_min is not None and listing.units < filters.unit_min:
            return {"gate": "unit_out_of_band", "detail": f"units={listing.units} < {filters.unit_min}"}
        if filters.unit_max is not None and listing.units > filters.unit_max:
            return {"gate": "unit_out_of_band", "detail": f"units={listing.units} > {filters.unit_max}"}
    if filters.property_sub_types:
        return {"gate": "property_sub_type", "detail": str(listing.property_sub_type)}
    if filters.tenancy_types:
        return {"gate": "tenancy_type", "detail": str(listing.tenancy_type)}
    for fld, lo, hi in (
        ("asking_price", filters.price_min, filters.price_max),
        ("price_per_unit", filters.price_per_unit_min, filters.price_per_unit_max),
        ("year_built", filters.year_built_min, filters.year_built_max),
        ("building_sqft", filters.building_sqft_min, filters.building_sqft_max),
        ("lot_acres", filters.lot_acres_min, filters.lot_acres_max),
        ("stories", filters.stories_min, filters.stories_max),
        ("buildings_count", filters.buildings_count_min, filters.buildings_count_max),
        ("occupancy_rate_percent", filters.occupancy_min, filters.occupancy_max),
        ("days_on_market", None, filters.max_days_on_market),
    ):
        v = getattr(listing, fld, None)
        if v is None or (lo is None and hi is None):
            continue
        if (lo is not None and v < lo) or (hi is not None and v > hi):
            return {"gate": fld, "detail": f"{v} outside [{lo},{hi}]"}
    if filters.opportunity_zone is not None:
        return {"gate": "opportunity_zone", "detail": str(listing.opportunity_zone)}
    if filters.has_offering_memorandum is not None:
        return {"gate": "has_offering_memorandum", "detail": str(listing.has_offering_memorandum)}
    return {"gate": "unknown", "detail": "matches() rejected but no mirrored gate did"}


def write_gate_note() -> str:
    """Why the GOAL's 'confidence gate' column is empty on this path.

    ``upsert_listing_rows`` has no confidence comparison of any kind. Its ON CONFLICT
    clause refreshes exactly the keys ``listing_row`` emits; everything else -- the
    subject-record ENRICHMENT block and ``sold_evidence`` -- is simply absent from the
    SET list, so it is never written by the feed regardless of confidence. The one
    conditional write is ``is_sold``, which is sticky toward True. Reporting those as
    "a lower-confidence source lost" would name a mechanism that does not exist.
    """
    return ("upsert_listing_rows applies NO confidence gate; column-level skips are "
            "structural (enrichment columns absent from the ON CONFLICT SET list) plus "
            "the is_sold sticky-True case")


# ---------------------------------------------------------------------------
# derive: one record per asset, then reconcile against IngestStats
# ---------------------------------------------------------------------------
def derive(stats, filters, scope, max_fetch: int | None) -> list[dict]:
    """Turn the captured evidence into one attributed record per swept asset.

    Steps 3/4/5/6 are inline comprehensions in ``ingest_state`` with no wrappable seam,
    so they are reproduced here from the SAME inputs the product used (the ordered
    partition stub lists, the stored-updated map, the scope) by calling the product's
    own predicates. ``reconcile()`` then checks every derived population against the
    aggregate counter, which is what makes the reproduction checkable rather than
    asserted.
    """
    import app.services.crexi_ingest as CI

    # --- step 3: cross-partition dedupe, exactly as `stubs.setdefault` does it ---
    first_seen: dict[str, str] = {}
    seen_in: dict[str, list[str]] = {}
    for sw in SWEEPS:
        for aid in sw["stub_ids"]:
            if not aid:
                continue
            seen_in.setdefault(aid, []).append(sw["partition"])
            first_seen.setdefault(aid, sw["partition"])

    order = list(first_seen)  # insertion order == dict `stubs` order == the gate's order
    recs: dict[str, dict] = {}
    for aid in order:
        stub = STUBS.get(aid)
        recs[aid] = {
            "asset_id": aid,
            "partitions": seen_in[aid],
            "n_partitions": len(seen_in[aid]),
            "duplicate": len(seen_in[aid]) > 1,
            "winner_partition": first_seen[aid],
            "stub": {
                "type_str": getattr(stub, "type_str", None),
                "status": getattr(stub, "status", None),
                "updated_on": _iso(getattr(stub, "updated_on", None)),
                "asking_price": getattr(stub, "asking_price", None),
                "has_price": getattr(stub, "has_price", None),
            },
            "steps": {}, "outcome": None, "drop_stage": None, "drop_reason": None,
        }

    # --- step 4: type gate ---
    stub_type_ok = UNWRAPPED.get("stub_type_ok", type(filters).stub_type_ok)
    matched = [a for a in order if stub_type_ok(filters, recs[a]["stub"]["type_str"])]
    matched_set = set(matched)
    for a in order:
        ok = a in matched_set
        recs[a]["steps"]["type_gate"] = "pass" if ok else "drop"
        if not ok:
            recs[a].update(outcome="dropped", drop_stage="type_gate",
                           drop_reason=f"stub type {recs[a]['stub']['type_str']!r} not in "
                                       f"{list(filters.property_types)}")

    # --- step 5: unpriced skip (only runs when the scope excludes unpriced) ---
    if not scope.include_unpriced:
        survivors = []
        for a in matched:
            if recs[a]["stub"]["has_price"]:
                recs[a]["steps"]["unpriced"] = "pass"
                survivors.append(a)
            else:
                recs[a]["steps"]["unpriced"] = "drop"
                recs[a].update(outcome="dropped", drop_stage="unpriced",
                               drop_reason="stub carries no askingPrice and include_unpriced=False")
        matched = survivors
    else:
        for a in matched:
            recs[a]["steps"]["unpriced"] = "n/a (include_unpriced=True)"

    # --- step 6: detail-fetch economy ---
    to_fetch, unchanged = [], []
    for a in matched:
        held = STORED.get(a)
        up = getattr(STUBS.get(a), "updated_on", None)
        if held is not None and up is not None and up <= CI._aware(held):
            unchanged.append(a)
            recs[a]["steps"]["economy"] = "unchanged"
            recs[a].update(outcome="unchanged",
                           drop_reason=f"stub updated_on {_iso(up)} <= stored "
                                       f"source_updated_on {_iso(CI._aware(held))}")
        else:
            to_fetch.append(a)
            recs[a]["steps"]["economy"] = "fetch" if held is not None else "fetch (new)"

    # --- step 6b: the --max-fetch cap. A capped asset is NOT a drop: it was never
    #     offered to any gate, and the run flags itself truncated so the tail is
    #     rediscovered. Calling it "dropped" would inflate every downstream rate. ---
    if max_fetch is not None and len(to_fetch) > max_fetch:
        for a in to_fetch[max_fetch:]:
            recs[a]["steps"]["economy"] = "capped"
            recs[a].update(outcome="capped",
                           drop_reason=f"--max-fetch {max_fetch} reached; tail left stale (run truncated)")
        to_fetch = to_fetch[:max_fetch]

    # --- steps 7-10, per fetched asset ---
    for a in to_fetch:
        f = FETCH.get(a, {})
        if f.get("error"):
            recs[a]["steps"]["fetch"] = "error"
            recs[a].update(outcome="fetch_error", drop_stage="fetch_error", drop_reason=f["error"])
            continue
        if not f.get("ok"):
            # Reached only if the run aborted (breaker / CrexiBlocked) before this stub.
            recs[a]["steps"]["fetch"] = "not_attempted"
            recs[a].update(outcome="not_reached", drop_reason="run ended before this stub was fetched")
            continue
        recs[a]["steps"]["fetch"] = "ok"
        n = NORM.get(a)
        if n is None or n.get("returned_none"):
            recs[a]["steps"]["normalize"] = "returned None"
            recs[a].update(outcome="dropped", drop_stage="normalization",
                           drop_reason="normalize_listing returned None (no resolvable asset id)")
            continue
        recs[a]["steps"]["normalize"] = "ok"
        recs[a]["fields"] = n["fields"]
        st = STRICT.get(a, {})
        recs[a]["steps"]["strict_filter"] = "match" if st.get("match") else "nonmatch"
        recs[a]["strict"] = st
        recs[a]["clamp"] = CLAMP.get(a, {"truncated": {}, "nulled_int4": {}})
        u = UPSERT.get(a)
        if u is None:
            recs[a]["steps"]["upsert"] = "not written (dry-run or batch not flushed)"
            recs[a]["outcome"] = "normalized_not_written"
        else:
            recs[a]["steps"]["upsert"] = u["mode"]
            recs[a]["upsert"] = u
            recs[a]["outcome"] = "upserted"

    for a in unchanged:
        recs[a]["steps"]["last_seen_bump"] = "bumped" if a in set(BUMPED) else "not bumped"

    return [recs[a] for a in order]


def reconcile(records: list[dict], stats) -> list[dict]:
    """Check every derived population against the matching ``IngestStats`` counter.

    The whole value of a per-asset attribution is that it explains the aggregate. If it
    does not sum to the aggregate it is wrong, and this is where that shows up -- rather
    than in a table that looks authoritative and is not.
    """
    n = lambda pred: sum(1 for r in records if pred(r))  # noqa: E731
    checks = [
        ("swept", len(records), stats.swept),
        ("type_matched", n(lambda r: r["steps"].get("type_gate") == "pass"), stats.type_matched),
        ("unpriced_excluded", n(lambda r: r["drop_stage"] == "unpriced"), stats.unpriced_excluded),
        ("unchanged", n(lambda r: r["outcome"] == "unchanged"), stats.unchanged),
        # `stats.fetched` is incremented AFTER the normalize-None check, so it counts
        # SUCCESSFUL NORMALIZATIONS, not detail fetches. Reconciled against that meaning.
        ("fetched (== normalized ok)", n(lambda r: r["steps"].get("normalize") == "ok"), stats.fetched),
        ("fetch_errors", n(lambda r: r["outcome"] == "fetch_error"), stats.fetch_errors),
        ("strict_matches", n(lambda r: r["steps"].get("strict_filter") == "match"), stats.strict_matches),
        ("upserted", n(lambda r: r["outcome"] == "upserted"), stats.upserted),
        ("type_gate calls observed", len(TYPE_GATE_CALLS), stats.swept),
        ("partitions", len(SWEEPS), stats.partitions),
    ]
    return [{"counter": k, "derived": d, "IngestStats": s, "ok": d == s} for k, d, s in checks]


def fingerprint(records: list[dict]) -> str:
    """A digest of the funnel VERDICTS only -- the thing a replay must reproduce.

    Deliberately excludes wall time, HTTP latency and row counts-in-flight: a second
    replay differing in those is not a reproducibility failure, and folding them in
    would make the check fire on noise and stop meaning anything.
    """
    body = [
        {"asset_id": r["asset_id"], "winner": r["winner_partition"], "parts": sorted(r["partitions"]),
         "outcome": r["outcome"], "drop_stage": r["drop_stage"],
         "strict": (r.get("strict") or {}).get("match"),
         "strict_gate": ((r.get("strict") or {}).get("reason") or {}).get("gate"),
         "units": ((r.get("fields") or {}).get("_units_evidence") or {}).get("verdict"),
         "upsert": (r.get("upsert") or {}).get("mode")}
        for r in sorted(records, key=lambda x: x["asset_id"])
    ]
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", default="FL")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--backfill", action="store_true")
    ap.add_argument("--max-fetch", type=int, default=None)
    ap.add_argument("--max-pages", type=int, default=None)
    ap.add_argument("--page-size", type=int, default=100)
    ap.add_argument("--overlap-minutes", type=int, default=60)
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-seams", action="store_true",
                    help="cassette only, no instrumentation -- the Phase-1 record/replay proof, "
                         "so a cassette bug cannot hide behind a seam bug")
    args = ap.parse_args()

    # The cassette installs BEFORE the trace, so the trace observes what it served.
    cas = cassette_from_env()
    if cas is not None:
        cas.install()
        print(f"cassette: mode={cas.mode} entries={len(cas.entries)} path={cas.path}")
    if not args.no_seams:
        install()

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.config.settings import Settings
    from app.providers.crexi.client import CrexiClient
    from app.providers.crexi.listing_filters import ListingFilters
    from app.services.crexi_image_client import build_crexi_mirror
    from app.services.crexi_ingest import ingest_state, scope_for_state
    from app.services.scrape_profile_service import get_effective_scrape_config

    s = Settings()
    # ingest_state() defaults `started` to datetime.now(UTC), which lands in harvested_at,
    # last_seen_at and days_on_market -- so an unpinned clock makes the run unreproducible
    # by construction. Same reason trace.py calls value_route_pass directly instead of the
    # CLI: the CLI cannot pass `now`.
    pinned = datetime.fromisoformat(os.environ["CREXI_PINNED_NOW"]) \
        if os.environ.get("CREXI_PINNED_NOW") else datetime.now(UTC)

    eng = create_engine(s.database_url, future=True)
    with Session(eng) as sess:
        cfg = get_effective_scrape_config(sess)
    filters = ListingFilters.from_scrape_config(cfg)
    mirror = build_crexi_mirror(s)
    if mirror.enabled:  # preflight asserts this too; a second, in-process guard is cheap
        raise SystemExit("ingest_trace: photo mirror is ENABLED -- refusing to run")

    client = CrexiClient(token=s.crexi_token, base_url=s.crexi_base_url,
                         requests_per_second=s.crexi_requests_per_second,
                         max_retries=s.crexi_max_retries)

    # The detail-fetch loop's three calls share one try block, so a CrexiError cannot be
    # attributed by call alone. GET /assets/<id> is always the first of the three, so it
    # is the loop's only observable per-asset entry point -- hook it to set the in-flight
    # id and to record which of the three succeeded.
    _gpa, _gab, _gag = client.get_property_asset, client.get_asset_brokers, client.get_asset_gallery

    def gpa(asset_id):
        _IN_FLIGHT["asset_id"] = str(asset_id)
        FETCH[str(asset_id)] = {"ok": False, "error": None, "got": []}
        try:
            out = _gpa(asset_id)
        except Exception as exc:
            FETCH[str(asset_id)]["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            raise
        FETCH[str(asset_id)]["got"].append("detail")
        return out

    def gab(asset_id):
        try:
            out = _gab(asset_id)
        except Exception as exc:
            FETCH[str(asset_id)]["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            raise
        FETCH[str(asset_id)]["got"].append("brokers")
        return out

    def gag(asset_id):
        try:
            out = _gag(asset_id)
        except Exception as exc:
            FETCH[str(asset_id)]["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            raise
        FETCH[str(asset_id)]["got"].append("gallery")
        FETCH[str(asset_id)]["ok"] = True   # all three landed
        return out

    if not args.no_seams:
        client.get_property_asset, client.get_asset_brokers, client.get_asset_gallery = gpa, gab, gag

    state = args.states.split(",")[0].strip().upper()
    scope = scope_for_state(cfg, state)
    t0 = time.time()
    lines: list[str] = []
    with Session(eng) as sess:
        stats = ingest_state(
            sess, client, cfg, state,
            apply=args.apply, backfill=args.backfill,
            overlap_minutes=args.overlap_minutes, page_size=args.page_size,
            max_pages=args.max_pages, max_fetch=args.max_fetch, keep_raw=True,
            include_unpriced=True, photo_mirror=mirror, now=pinned, log=lines.append,
        )
    wall = round(time.time() - t0)
    client.close()

    print(f"\ningest: {'FULL' if stats.full_sweep else 'delta'} partitions={stats.partitions} "
          f"swept={stats.swept} type_matched={stats.type_matched} "
          f"unpriced_excl={stats.unpriced_excluded} unchanged={stats.unchanged} "
          f"fetched={stats.fetched} fetch_errors={stats.fetch_errors} "
          f"strict={stats.strict_matches} upserted={stats.upserted} wall={wall}s")
    for w in stats.warnings[:5]:
        print(f"  WARNING: {w}")
    if len(stats.warnings) > 5:
        print(f"  ... and {len(stats.warnings) - 5} more warnings")

    if args.no_seams:
        # The Phase-1 proof needs a comparable answer with NO instrumentation in the way.
        print("\nno-seams fingerprint: " + hashlib.sha256(
            json.dumps(stats.as_json(), sort_keys=True, default=str).encode()).hexdigest()[:16])
        if cas is not None:
            sm = cas.summary()
            print(f"cassette: hits={sm['hits']} misses={sm['misses']} recorded={sm['recorded']} "
                  f"entries={sm['entries']}")
        print("outbound crexi calls: not counted (--no-seams installs no request tap)")
        return 0

    records = derive(stats, filters, scope, args.max_fetch)
    checks = reconcile(records, stats)
    fp = fingerprint(records)

    git = subprocess.run(["git", "-C", os.environ["WHOLESALING_REPO"], "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    lab = subprocess.run(["git", "-C", os.environ["CREXI_BASELINE_ROOT"], "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    with Session(eng) as sess:
        from sqlalchemy import text as _text
        alembic = sess.execute(_text("select version_num from alembic_version")).scalar()

    cas_digest = None
    if cas is not None and cas.path.exists():
        h = hashlib.sha256()
        with cas.path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        cas_digest = h.hexdigest()[:16]

    manifest = {
        "arm": os.environ.get("CREXI_BASELINE_ARM"),
        "wholesaling_git": git, "lab_git": lab, "alembic_head": alembic,
        "pinned_now": pinned.isoformat(), "state": state,
        "apply": args.apply, "backfill": args.backfill, "max_fetch": args.max_fetch,
        "scope_fingerprint": CURSOR.get("run_fingerprint"),
        "cassette": (cas.mode if cas else None), "cassette_sha16": cas_digest,
        "cassette_entries": (len(cas.entries) if cas else None),
        "crexi_base_url": s.crexi_base_url,
        "ingest_stats": stats.as_json(),
        "funnel_fingerprint": fp,
        "reconciliation": checks,
        "cursor": CURSOR, "seams": PATCHES,
        "sweeps": [{k: v for k, v in sw.items() if k != "stub_ids"} for sw in SWEEPS],
        "probes": PROBES,
        "write_gate": write_gate_note(),
        "defect_classes": sorted(DEFECTS),
        "wall_s": wall,
    }

    arm = os.environ.get("CREXI_BASELINE_ARM", "?")
    out = args.out or os.path.join(os.environ["CREXI_BASELINE_ROOT"], "runs",
                                   f"ingest_trace_{state}_arm{arm}.jsonl")
    with open(out, "w") as fh:
        fh.write(json.dumps({"_manifest": manifest}, default=str) + "\n")
        for r in records:
            fh.write(json.dumps(r, default=str) + "\n")

    http_out = os.path.join(os.environ["CREXI_BASELINE_ROOT"], "runs", f"ingest_http_{state}.jsonl")
    with open(http_out, "w") as hf:
        for e in HTTP:
            hf.write(json.dumps(e) + "\n")

    if cas is not None:
        sm = cas.summary()
        print(f"\ncassette: hits={sm['hits']} misses={sm['misses']} recorded={sm['recorded']} "
              f"entries={sm['entries']}")
    print(f"outbound crexi calls: {len(HTTP)} -> {http_out}")

    print("\n=== RECONCILIATION (derived per-asset vs IngestStats) ===")
    bad = 0
    for c in checks:
        mark = "ok  " if c["ok"] else "MISMATCH"
        bad += 0 if c["ok"] else 1
        print(f"  {mark}  {c['counter']:32s} derived={c['derived']:6d}  stats={c['IngestStats']}")
    print(f"\nfunnel fingerprint: {fp}")
    print(f"records: {len(records)} -> {out}")
    if bad:
        print(f"\n!! {bad} counter(s) disagree -- the per-asset attribution does not explain "
              f"the aggregate and must not be reported as a baseline")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
