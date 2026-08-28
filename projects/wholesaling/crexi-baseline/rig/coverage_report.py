#!/usr/bin/env python3
"""Derive the F-B14 verdict + the Phase-2 targeting decision packet from frozen runs.

Pure derivation: reads the frozen partitioned trace and the coverage-probe outputs,
issues NO network calls, and writes both reports. Kept separate from
``coverage_probe.py`` for the same reason ``ingest_funnel.py`` is separate from
``ingest_trace.py`` -- a taxonomy fix should re-derive from the frozen evidence
rather than force a re-sweep.

  python rig/coverage_report.py              # both reports to runs/
"""
from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FROZEN_RUN_AT = "2026-08-27T23:00"


def _load_trace() -> tuple[dict, dict]:
    recs, manifest = {}, {}
    with (ROOT / "runs/ingest_trace_FL_replay1.jsonl").open() as fh:
        for line in fh:
            r = json.loads(line)
            if "_manifest" in r:
                manifest = r
                continue
            recs[str(r["asset_id"])] = r
    return recs, manifest


def _load_probe(name: str) -> tuple[dict, dict]:
    payloads, manifest = {}, {}
    with (ROOT / f"runs/{name}").open() as fh:
        manifest = json.loads(fh.readline())
        for line in fh:
            r = json.loads(line)
            payloads[str(r["asset_id"])] = r["payload"]
    return payloads, manifest


def _county_totals() -> dict[str, int]:
    """Per-county ``totalCount`` probes, read back out of the frozen ingest cassette."""
    out = {}
    with (ROOT / "runs/cassettes/ingest_fl.jsonl").open() as fh:
        for line in fh:
            e = json.loads(line)
            if e["path"] != "/assets/search" or e["body"].get("count") != 1:
                continue
            c = e["body"].get("counties")
            if c:
                out[c[0]] = e["response"].get("totalCount")
    return out


def _loc(payload: dict) -> dict:
    return next((x for x in (payload.get("locations") or []) if isinstance(x, dict)), {})


def _norm_county(raw: str | None) -> str | None:
    """Normalize a payload county string toward the gazetteer's ``"X County"`` form.

    Deliberately generous -- uppercase, missing/extra suffix, ``St``/``St.`` and
    ``Saint``, stray whitespace. The point is to prove the miss is NOT a mere
    string-format mismatch we could fix with a normalizer: whatever survives this
    is a genuine index miss, not a spelling one.
    """
    if not raw or not str(raw).strip():
        return None
    s = re.sub(r"\s+", " ", str(raw).strip())
    s = re.sub(r"\s+(County|Parish|Borough)$", "", s, flags=re.I)
    s = re.sub(r"^St\.?\s+", "Saint ", s, flags=re.I)
    return " ".join(w.capitalize() if w.isupper() or w.islower() else w
                    for w in s.split()).replace("Miami-dade", "Miami-Dade")


def _gaz_norm(name: str) -> str:
    return _norm_county(name) or name


# ---------------------------------------------------------------- F-B14 verdict
def build_coverage(out: pathlib.Path) -> dict:
    trace, tman = _load_trace()
    county_ids = set(trace)
    swept_counties = {p.split(":", 1)[1] for r in trace.values() for p in r["partitions"]}
    ctot = _county_totals()

    win, wman = _load_probe("coverage_window_FL.jsonl")
    price, pman = _load_probe("coverage_price_FL.jsonl")
    ceil_man = json.loads((ROOT / "runs/coverage_ceiling_FL.jsonl").read_text().split("\n")[0])

    wres = wman["result"]["window"]
    desc = set(wman["result"]["window_ids"]["Descending"])
    asc = set(wman["result"]["window_ids"]["Ascending"])
    ws = set(price)                      # the price-partitioned whole-state enumeration
    total_count = pman["_manifest"]["whole_state_total_count"]

    only = ws - county_ids               # reachable whole-state, never seen by a county sweep
    both = ws & county_ids
    cty_only = county_ids - ws

    # Attribution of the miss set
    rows = []
    for aid in sorted(only):
        p = price[aid]
        loc = _loc(p)
        raw = loc.get("county")
        norm = _norm_county(raw)
        gaz = {_gaz_norm(c) for c in ctot}
        rows.append({
            "asset_id": aid,
            "county_raw": raw,
            "county_norm": norm,
            "county_in_gazetteer": bool(norm and norm in gaz),
            "county_swept": bool(norm and f"{norm} County" in swept_counties),
            "activated_on": p.get("activatedOn"),
            "updated_on": p.get("updatedOn"),
            "types": p.get("types") or [],
            "status": p.get("status"),
        })

    no_county = [r for r in rows if not r["county_raw"]]
    named_swept = [r for r in rows if r["county_raw"] and r["county_swept"]]
    named_unswept = [r for r in rows if r["county_raw"] and not r["county_swept"]]
    new_stock = [r for r in rows if (r["activated_on"] or "") >= FROZEN_RUN_AT]

    # Per-county reconciliation: what the county probe CLAIMED vs what the payloads say
    payload_county = collections.Counter()
    for aid, p in price.items():
        payload_county[_norm_county(_loc(p).get("county")) or "(none)"] += 1

    recon = []
    for cname, tc in sorted(ctot.items(), key=lambda x: -(x[1] or 0)):
        n = _gaz_norm(cname)
        swept_here = sum(1 for r in trace.values() if f"FL:{cname}" in r["partitions"])
        recon.append({"county": cname, "county_total_count": tc,
                      "swept_in_partition": swept_here,
                      "payload_claims_this_county": payload_county.get(n, 0)})

    verdict = {
        "question": "does the county-partition union miss ~44% of the FL multifamily book, "
                    "or is the whole-state total_count an inflated denominator?",
        "sets": {
            "whole_state_price_partitioned": len(ws),
            "whole_state_total_count": total_count,
            "total_count_matches_enumeration": len(ws) == total_count,
            "county_union": len(county_ids),
            "county_total_count_sum": sum(v or 0 for v in ctot.values()),
            "intersection": len(both),
            "whole_state_only": len(only),
            "county_union_only": len(cty_only),
        },
        "window_arm": {
            "descending_ids": len(desc), "ascending_ids": len(asc),
            "overlap": len(desc & asc), "union": len(desc | asc),
            "stop_reason": {d: r["stop_reason"] for d, r in wres.items()},
            "reading": ("DISJOINT windows -- the two 1,499-id ends of the feed share no asset, "
                        "so the reachable population is at least 2,998 without trusting "
                        "total_count at all")
            if not (desc & asc) else
            ("OVERLAPPING windows -- the feed saturates below 2,998, so total_count is inflated"),
        },
        "pagination_ceiling": {
            "product_constant_PAGE_WINDOW": 1500,
            "product_constant_SAFE_WINDOW": 1400,
            "probes": ceil_man["result"]["ceiling"],
        },
        "miss_attribution": {
            "whole_state_only": len(only),
            "payload_carries_no_county": len(no_county),
            "payload_names_a_county_that_WAS_swept": len(named_swept),
            "payload_names_a_county_NOT_swept": len(named_unswept),
            "activated_after_the_frozen_run (new stock, not a miss)": len(new_stock),
        },
        "county_reconciliation": recon,
        "miss_rows": rows,
    }
    out.write_text(json.dumps(verdict, indent=1, default=str))
    return verdict


# ------------------------------------------------------- Phase 2 decision packet
def _detail_facts() -> dict[str, dict]:
    """asset_id -> the fields normalization would derive, for every detail we hold.

    Uses the PRODUCT's own ``_summary_map`` / ``_type_str`` rather than re-guessing
    the payload shape: a census of ``property_sub_type`` has to mean the same string
    the gate would see, or it is a census of something else. (The first draft of this
    read ``propertyAttributes.subType`` and reported 150/150 empty -- the value lives
    under ``summaryDetails`` -> ``SubType``.)

    Sub-type is a DETAIL field: the ``/assets/search`` feed does not carry it. So this
    census is over the assets that have been detail-fetched, NOT over the 3,496.
    Stated as a denominator rather than quietly projected onto the population.
    """
    from app.providers.crexi.listing_normalize import _summary_map, _type_str

    out: dict[str, dict] = {}
    with (ROOT / "runs/cassettes/ingest_fl.jsonl").open() as fh:
        for line in fh:
            e = json.loads(line)
            m = re.fullmatch(r"/assets/(\d+)", e["path"])
            if not m:
                continue
            d = e["response"] or {}
            summary = _summary_map(d.get("summaryDetails"))
            out[m.group(1)] = {
                "sub_type": (_type_str(summary.get("SubType")) or "").strip(),
                "property_type": (_type_str(summary.get("PropertyType")) or "").strip(),
                "units": summary.get("Units"),
                "asking_price": d.get("askingPrice"),
                "source": "ingest cassette (passed the exact-match gate)",
            }

    # The example fetches: the ONLY details we hold for COMPOUND-type listings, since
    # the exact-match gate means no compound listing has ever been detail-fetched by a
    # real pass. Without these the packet cannot state units for the very listings the
    # operator is being asked to rule on.
    ex_path = ROOT / "runs/coverage_examples_FL.jsonl"
    if ex_path.exists():
        ex = json.loads(ex_path.read_text().split("\n")[0])
        for aid, rec in (ex["result"].get("examples") or {}).items():
            d = rec.get("detail") or {}
            if not d:
                continue
            summary = _summary_map(d.get("summaryDetails"))
            out[str(aid)] = {
                "sub_type": (_type_str(summary.get("SubType")) or "").strip(),
                "property_type": (_type_str(summary.get("PropertyType")) or "").strip(),
                "units": summary.get("Units"),
                "asking_price": d.get("askingPrice"),
                "source": "packet example fetch",
            }
    return out


def _db_sub_types() -> dict[str, dict]:
    """A second, independent sub-type sample: the rows an earlier live ingest stored."""
    import os

    from sqlalchemy import create_engine, text

    url = os.environ.get("DATABASE_URL")
    if not url:
        return {}
    eng = create_engine(url, future=True)
    out = {}
    try:
        with eng.connect() as c:
            for aid, sub, units, ask in c.execute(text(
                "select asset_id, coalesce(property_sub_type,''), units, asking_price "
                "from crexi_listings")):
                out[str(aid)] = {"sub_type": (sub or "").strip(), "units": units,
                                 "asking_price": float(ask) if ask is not None else None}
    finally:
        eng.dispose()
    return out


#: Sub-type tokens that are out of scope for a 2-4 unit multifamily buy-box. Flagged,
#: never filtered -- the whole point of the packet is that this is the operator's call.
_OUT_OF_SCOPE_SUBTYPE = ("single family rental portfolio", "rv park", "apartment/condo",
                         "student housing", "vacation rental", "mobile home")

#: Types that, combined with Multifamily, most plausibly mean "not an operating 2-4u
#: building": raw dirt and pads. Used only to SIZE candidate policies, not to pick one.
_DILUTIVE = ("Land", "Mobile Home Park")


def _policies(combos: collections.Counter) -> list[dict]:
    """Size every candidate targeting rule over the true in-scope population.

    Cost is stated in DETAIL FETCHES, because that is the unit that actually costs:
    each admitted stub spends 3 requests (``get_property_asset`` + ``get_asset_brokers``
    + ``get_asset_gallery``, ``listing_harvester.fetch_listing``). Sub-type rules are
    absent from this table on purpose -- see ``sub_type_cost_note``.
    """
    total = sum(combos.values())

    def size(pred, name, desc):
        adm = sum(n for k, n in combos.items() if pred(k))
        return {"policy": name, "rule": desc, "admitted": adm, "excluded": total - adm,
                "admitted_pct": round(100 * adm / total, 1),
                "detail_fetches": adm * 3,
                "delta_fetches_vs_today": None}

    def has(k, t):
        return t in [x.strip() for x in k.split(",")]

    rows = [
        size(lambda k: k == "Multifamily", "P0 today (exact match)",
             'joined type string == "Multifamily" (listing_filters.py:106-108)'),
        size(lambda k: True, "P1 substring (the comps rule)",
             'type string CONTAINS "multifamily" (harvester.py:141-149)'),
        size(lambda k: not any(has(k, d) for d in _DILUTIVE),
             "P2 substring minus Land/MHP",
             'contains Multifamily AND contains neither "Land" nor "Mobile Home Park"'),
        size(lambda k: len([x for x in k.split(",")]) <= 2 and not any(has(k, d) for d in _DILUTIVE),
             "P3 P2 + at most one co-type",
             "as P2, and the listing carries at most 2 types total"),
        size(lambda k: k == "Multifamily" or all(
                 x.strip() in ("Multifamily", "Office", "Retail", "Mixed Use")
                 for x in k.split(",")),
             "P4 exact + building-only co-types",
             "exact Multifamily, OR every co-type is one of Office / Retail / Mixed Use "
             "(i.e. there IS a building)"),
    ]
    today = rows[0]["detail_fetches"]
    for r in rows:
        r["delta_fetches_vs_today"] = r["detail_fetches"] - today
    return rows


def _example_units_band() -> dict:
    """Units band across the bounded example fetch -- the only units we hold for compounds.

    n is deliberately tiny (45, 3 per type set) and NOT a random sample, so this is
    reported as an observation about the examples the operator is about to read, never
    projected onto the 1,086. It exists because "is Office, Multifamily a deal?" is
    unanswerable without knowing whether those listings are 2-4 unit buildings at all.
    """
    facts = _detail_facts()
    ex_path = ROOT / "runs/coverage_examples_FL.jsonl"
    if not ex_path.exists():
        return {}
    ids = list((json.loads(ex_path.read_text().split("\n")[0])["result"].get("examples") or {}))
    band = collections.Counter()
    for aid in ids:
        u = (facts.get(str(aid)) or {}).get("units")
        try:
            u = int(u)
        except (TypeError, ValueError):
            u = None
        band["units NULL" if u is None else "2-4 units" if 2 <= u <= 4
             else "1 unit" if u == 1 else "5+ units"] += 1
    return {"n": len(ids), "counts": band.most_common(),
            "note": "3 examples per type set, not a random sample -- read as anecdote, "
                    "not as a rate. 'units NULL' here is the same defect as F-B10."}


def build_packet() -> dict:
    price, pman = _load_probe("coverage_price_FL.jsonl")
    facts = _detail_facts()
    db = _db_sub_types()

    # --- 1. compound-type census over the TRUE in-scope population (3,496) ------
    combos = collections.Counter()
    by_set: dict[str, list[dict]] = collections.defaultdict(list)
    for aid, p in sorted(price.items()):
        key = ", ".join(p.get("types") or []) or "(none)"
        combos[key] += 1
        # Examples are keyed by the ORDER-NORMALIZED set: the operator is judging
        # "is Office+Multifamily a deal", not "is the string 'Office, Multifamily'".
        skey = ", ".join(sorted(x.strip() for x in key.split(",")))
        f = facts.get(aid) or db.get(aid) or {}
        if len(by_set[skey]) < 3 and (f or skey == "Multifamily"):
            loc = _loc(p)
            by_set[skey].append({
                "asset_id": aid,
                "address": loc.get("fullAddress") or loc.get("address"),
                "ask": p.get("askingPrice") or f.get("asking_price"),
                "units": f.get("units"),
                "sub_type": f.get("sub_type") or None,
                "description_first_line": (p.get("description") or "").split("\n")[0][:150],
                "detail_source": f.get("source"),
            })

    # Order fragmentation: the gate compares a JOINED string, so "Land, Multifamily"
    # and "Multifamily, Land" are two different keys for one underlying type SET.
    sets = collections.Counter()
    for k, n in combos.items():
        sets[", ".join(sorted(x.strip() for x in k.split(",")))] += n

    # --- 2. sub-type census -- TWO populations, deliberately NOT merged ---------
    # Merging them would be a methodological error: the first sample is everything
    # that PASSED the exact-match gate, the second is a compound-type sample chosen
    # precisely because nothing in it ever passed. One number over both would answer
    # neither "what are we admitting today" nor "what would admitting compounds bring".
    def census(items):
        c = collections.Counter((v.get("sub_type") or "").strip() or "(empty)"
                                for v in items)
        flg = {k: n for k, n in c.items()
               if any(t in k.lower() for t in _OUT_OF_SCOPE_SUBTYPE) or k == "(empty)"}
        return {"denominator": sum(c.values()), "counts": c.most_common(),
                "flagged_out_of_scope_for_2_4u": sorted(flg.items(), key=lambda x: -x[1]),
                "flagged_total": sum(flg.values())}

    def is_exact(aid):
        return ", ".join((price.get(aid) or {}).get("types") or []) == "Multifamily"

    admitted = dict(db)
    admitted.update({k: v for k, v in facts.items()
                     if v.get("source") != "packet example fetch"})
    compound = {k: v for k, v in facts.items()
                if v.get("source") == "packet example fetch" and not is_exact(k)}
    sub_admitted, sub_compound = census(admitted.values()), census(compound.values())

    return {
        "population": {
            "in_scope_total": len(price),
            "source": "price-partitioned whole-state enumeration (Phase-1 probe), "
                      "verified equal to the server's own totalCount",
        },
        "compound_type_census": {
            "distinct_joined_strings": len(combos),
            "distinct_type_SETS": len(sets),
            "order_fragmentation": len(combos) - len(sets),
            "exact_Multifamily": combos.get("Multifamily", 0),
            "compound_containing_Multifamily": sum(n for k, n in combos.items()
                                                   if k != "Multifamily"),
            "no_Multifamily_at_all": sum(n for k, n in combos.items()
                                         if "Multifamily" not in k),
            "combinations": combos.most_common(),
            "as_type_sets": sets.most_common(),
            "examples_by_type_set": dict(by_set),
        },
        "sub_type_census": {
            "note": (
                "property_sub_type lives in the DETAIL document (summaryDetails -> "
                "SubType); the /assets/search feed does not carry it, so neither census "
                "below can be projected onto the 3,496. They are also two DIFFERENT "
                "populations and are reported apart on purpose."),
            "admitted_today": dict(sub_admitted, description=(
                "assets that PASSED the exact-match type gate and were detail-fetched "
                "(ingest cassette + stored crexi_listings rows). Answers: what are we "
                "storing today?")),
            "compound_sample": dict(sub_compound, description=(
                "the bounded example fetch of COMPOUND-type listings -- the only "
                "sub-type data that has ever existed for them, since the gate drops "
                "them before any fetch. Tiny and not random (3 per type set): read as "
                "anecdote. Answers: what would admitting compounds bring in?")),
        },
        "example_units_band": _example_units_band(),
        "policy_costs": {
            "rows": _policies(combos),
            "fetch_unit": "3 requests per admitted listing (get_property_asset + "
                          "get_asset_brokers + get_asset_gallery, listing_harvester.py:124-129)",
            "sub_type_cost_note": (
                "NO sub-type policy can appear in this table. property_sub_type is only "
                "known AFTER the 3-request detail fetch, so a sub-type filter saves ZERO "
                "requests -- it can only prevent storage and downstream value-route work. "
                "Type policy is the only lever that moves the fetch bill."),
        },
        "the_inconsistency": {
            "listings_path": {
                "site": "listing_filters.py:106-108 (via listing_harvester.py:116-122)",
                "rule": '(stub_type or "").strip().lower() in self.property_types',
                "behaviour": "EXACT set membership on the JOINED string -> compound types DROPPED",
                "deliberate": True,
                "evidence": 'listing_harvester.py:116-122 "Strict per operator choice -- '
                            "compound types like 'Land, Multifamily' are excluded\"; locked by "
                            "test_crexi_listings.py:160 and test_crexi_ingest_service.py:127",
            },
            "comps_path": {
                "site": "harvester.py:141-149",
                "rule": '"multifamily" not in stub.type.lower() -> reject',
                "behaviour": "SUBSTRING match -> compound types KEPT",
                "extra": "the comps path additionally requires a non-null in-band unit count "
                         "at the STUB stage; the listings path does not.",
            },
            "statement": (
                "Two Crexi code paths disagree about what multifamily is. The listings "
                "harvester admits 2,410 of 3,496; the comps harvester's rule would admit "
                "3,496 of 3,496. A comp can therefore be a property the listings lane would "
                "never have ingested. This is surfaced as a decision, NOT fixed here."),
        },
    }


def render(cov: dict, pkt: dict) -> str:
    L: list[str] = []
    w = L.append
    s = cov["sets"]
    w("=" * 78)
    w("F-B14 VERDICT -- is the whole-state total_count a real denominator?")
    w("=" * 78)
    w("")
    w(f"  whole-state enumeration (price-partitioned)   {s['whole_state_price_partitioned']:>6}")
    w(f"  whole-state total_count reported by Crexi     {s['whole_state_total_count']:>6}"
      f"   {'MATCH' if s['total_count_matches_enumeration'] else 'MISMATCH'}")
    w(f"  county-partition union (frozen baseline)      {s['county_union']:>6}")
    w(f"  sum of the 67 per-county total_counts         {s['county_total_count_sum']:>6}")
    w("")
    w(f"  intersection                                  {s['intersection']:>6}")
    w(f"  whole-state ONLY (never seen by any county)   {s['whole_state_only']:>6}"
      f"   {100 * s['whole_state_only'] / s['whole_state_price_partitioned']:.1f}% of scope")
    w(f"  county-union ONLY                             {s['county_union_only']:>6}"
      "   <- the county union is a strict SUBSET")
    w("")
    ww = cov["window_arm"]
    w("  Independent check that does not trust total_count at all:")
    w(f"    newest-1499 window  {ww['descending_ids']:>5}    oldest-1499 window  {ww['ascending_ids']:>5}")
    w(f"    overlap {ww['overlap']:>5}   union {ww['union']:>5}   -> {ww['reading'][:60]}...")
    w("")
    w("  Pagination ceiling (the alternative explanation, ruled out):")
    for pr in cov["pagination_ceiling"]["probes"]:
        mark = "OK " if pr.get("ok") else "400"
        w(f"    offset={pr['offset']:<5} count={pr['count']}  -> {mark}"
          + (f"  id={pr.get('asset_id')}" if pr.get("ok") else "  Offset + Count must be less than 1500"))
    w("")
    ma = cov["miss_attribution"]
    w("  Where the 1,534 missing assets went:")
    for k, v in ma.items():
        w(f"    {k:<52} {v:>6}")
    w("")
    w("  County filter is a CASE-INSENSITIVE but otherwise LITERAL string match:")
    for row in cov.get("variants", []):
        w(f"    counties={row['counties']!r:26} -> total_count={row.get('total_count')}")
    w("")
    w("=" * 78)
    w("TARGETING DECISION PACKET  (evidence for an operator call -- not a decision)")
    w("=" * 78)
    c = pkt["compound_type_census"]
    w("")
    w(f"1. COMPOUND-TYPE CENSUS over the true in-scope population "
      f"({pkt['population']['in_scope_total']})")
    w("")
    w(f"   exact 'Multifamily'                {c['exact_Multifamily']:>6}"
      f"  {100 * c['exact_Multifamily'] / pkt['population']['in_scope_total']:>5.1f}%   ADMITTED today")
    w(f"   compound containing Multifamily    {c['compound_containing_Multifamily']:>6}"
      f"  {100 * c['compound_containing_Multifamily'] / pkt['population']['in_scope_total']:>5.1f}%   DROPPED today")
    w(f"   carrying no Multifamily at all     {c['no_Multifamily_at_all']:>6}"
      "         (the ANY-match filter is honest)")
    w("")
    w(f"   distinct joined type strings       {c['distinct_joined_strings']:>6}")
    w(f"   distinct type SETS                 {c['distinct_type_SETS']:>6}")
    w(f"   strings that are a re-ORDERING     {c['order_fragmentation']:>6}"
      "   <- the gate compares a joined string,")
    w("                                                 so order alone forks the key")
    w("")
    w("   top combinations:")
    for k, n in c["combinations"][:18]:
        w(f"     {n:>5}  {k}")
    w("")
    w("   the same data as ORDER-NORMALIZED type sets:")
    for k, n in c["as_type_sets"][:12]:
        w(f"     {n:>5}  {{{k}}}")
    w("")
    st = pkt["sub_type_census"]
    w("2. SUB-TYPE CENSUS -- two populations, reported apart")
    w("   " + st["note"].replace(". ", ".\n   "))
    w("")
    for key in ("admitted_today", "compound_sample"):
        sc = st[key]
        w(f"   [{key}]  n={sc['denominator']}")
        w("   " + sc["description"].replace(". ", ".\n   "))
        for k, n in sc["counts"][:16]:
            flag = "  <-- OUT OF SCOPE for a 2-4u buy-box" if any(
                t in k.lower() for t in _OUT_OF_SCOPE_SUBTYPE) or k == "(empty)" else ""
            w(f"     {n:>5}  {k[:78]}{flag}")
        if len(sc["counts"]) > 16:
            w(f"     ...   {len(sc['counts']) - 16} more distinct values")
        w(f"     flagged out of scope: {sc['flagged_total']} of {sc['denominator']} "
          f"({100 * sc['flagged_total'] / sc['denominator']:.1f}%)")
        w("")
    ub = pkt.get("example_units_band") or {}
    if ub:
        w(f"   units across those {ub['n']} example fetches:")
        for k, n in ub["counts"]:
            w(f"     {n:>5}  {k}")
        w("   " + ub["note"])
        w("")
    w("3. THE COST OF EACH POLICY")
    w("")
    w(f"   {'policy':<32}{'admitted':>9}{'excluded':>9}{'fetches':>9}{'delta':>9}")
    for r in pkt["policy_costs"]["rows"]:
        w(f"   {r['policy']:<32}{r['admitted']:>9}{r['excluded']:>9}"
          f"{r['detail_fetches']:>9}{r['delta_fetches_vs_today']:>+9}")
    w("")
    for r in pkt["policy_costs"]["rows"]:
        w(f"     {r['policy']}: {r['rule']}")
    w("")
    w("   " + pkt["policy_costs"]["fetch_unit"])
    w("   " + pkt["policy_costs"]["sub_type_cost_note"].replace(". ", ".\n   "))
    w("")
    w("   EXAMPLES the operator can judge (3 per type set; units + sub_type came from")
    w("   the bounded example detail-fetch -- no compound listing had ever been fetched):")
    w("")
    order = [k for k, _ in c["as_type_sets"]]
    for skey in order[:13]:
        ex = c["examples_by_type_set"].get(skey) or []
        if not ex:
            continue
        n = dict(c["as_type_sets"])[skey]
        w(f"   {{{skey}}}   n={n}")
        for e in ex:
            ask = f"${e['ask']:,.0f}" if isinstance(e["ask"], (int, float)) else "unpriced"
            w(f"     {e['asset_id']:<9} {ask:>14}  units={str(e['units'] or '-'):<5} "
              f"{(e['address'] or '')[:52]}")
            if e.get("sub_type"):
                w(f"               sub_type: {e['sub_type']}")
            if e.get("description_first_line"):
                w(f"               \"{e['description_first_line'][:88]}\"")
        w("")
    w("4. THE INCONSISTENCY (surfaced, not fixed)")
    inc = pkt["the_inconsistency"]
    for side in ("listings_path", "comps_path"):
        d = inc[side]
        w(f"   {side}: {d['site']}")
        w(f"     rule      {d['rule']}")
        w(f"     behaviour {d['behaviour']}")
        for extra in ("deliberate", "evidence", "extra"):
            if extra in d:
                w(f"     {extra:<9} {d[extra]}")
        w("")
    w("   " + inc["statement"].replace(". ", ".\n   "))
    w("")
    return "\n".join(L)


if __name__ == "__main__":
    cov = build_coverage(ROOT / "runs/coverage_verdict_FL.json")
    var = json.loads((ROOT / "runs/coverage_variants_FL.jsonl").read_text().split("\n")[0])
    cov["variants"] = var["result"]["variants"]
    (ROOT / "runs/coverage_verdict_FL.json").write_text(json.dumps(cov, indent=1, default=str))
    pkt = build_packet()
    (ROOT / "runs/targeting_packet_FL.json").write_text(json.dumps(pkt, indent=1, default=str))
    txt = render(cov, pkt)
    (ROOT / "runs/coverage_report_FL.txt").write_text(txt)
    print(txt)
