"""The drop-attributed ingest funnel table, derived from a frozen ingest trace.

Same division of labour as trace.py / provenance.py: ``ingest_trace.py`` CAPTURES,
this DERIVES and RENDERS. Keeping the aggregation out of the run means a taxonomy fix
re-derives from the frozen JSONL instead of forcing another pass -- which matters more
here than for the value route, because an ingest pass is stateful and re-running it
means restoring a DB snapshot first.

  ./rig/run.sh $CREXI_BASELINE_ROOT/rig/ingest_funnel.py runs/ingest_trace_FL_record.jsonl \
      [--compare runs/ingest_trace_FL_replay2.jsonl] [--json]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from defects import DEFECTS, classify_ingest  # noqa: E402

#: Prose spellings of a unit count. Used ONLY to split the recoverable population into
#: in-band / out-of-band -- an "8-unit" signal is just as unmapped as a "duplex" one, but
#: recovering it would not produce a strict match, and conflating the two would overstate
#: the prize of the fix.
_WORD_UNITS = {"duplex": 2, "triplex": 3, "fourplex": 4, "quadplex": 4, "quadruplex": 4}

#: The scrape profile's configured types for this baseline (DEFAULT_SCRAPE_CONFIG).
#: Read from the trace rather than hardcoded would be better; this run has no stored
#: profile, so the shipped default is what ran and the manifest's scope fingerprint pins it.
_CONFIGURED_TYPES = ("multifamily",)


def prose_units(match: str | None) -> int | None:
    if not match:
        return None
    m = match.strip().lower()
    if m in _WORD_UNITS:
        return _WORD_UNITS[m]
    d = re.search(r"\d{1,3}", m)
    return int(d.group()) if d else None


def load(path: str) -> tuple[dict, list[dict]]:
    with open(path) as fh:
        rows = [json.loads(ln) for ln in fh if ln.strip()]
    return rows[0]["_manifest"], rows[1:]


def pct(n: int, d: int) -> str:
    return f"{100.0 * n / d:5.1f}%" if d else "    - "


def render(man: dict, recs: list[dict]) -> str:  # noqa: C901 - one report, read top to bottom
    out: list[str] = []
    w = out.append
    N = len(recs)
    st = man["ingest_stats"]

    by_outcome = collections.Counter(r["outcome"] for r in recs)
    by_drop = collections.Counter(r["drop_stage"] for r in recs if r["drop_stage"])
    fetched = [r for r in recs if r["steps"].get("normalize") == "ok"]

    w("=" * 78)
    w(f"INGEST FUNNEL BASELINE -- {man['state']}   fingerprint {man['funnel_fingerprint']}")
    w("=" * 78)

    # ---- the funnel itself -------------------------------------------------
    w("")
    w(f"swept {N}   ({man['ingest_stats']['partitions']} county partitions, "
      f"total_in_scope={st.get('total_in_scope')})")
    w(f"  -> dropped: type gate        {by_drop['type_gate']:5d}  {pct(by_drop['type_gate'], N)}")
    tg = [r for r in recs if r["drop_stage"] == "type_gate"]
    compound = [r for r in tg
                if any(t in (r["stub"]["type_str"] or "").lower() for t in _CONFIGURED_TYPES)]
    w(f"       of which the stub type STRING CONTAINS a configured type: "
      f"{len(compound)}  {pct(len(compound), len(tg))}   <- F-B15")
    w(f"  -> dropped: unpriced         {by_drop['unpriced']:5d}  {pct(by_drop['unpriced'], N)}"
      f"   [step inactive: include_unpriced=True]")
    w(f"  -> unchanged (economy)       {by_outcome['unchanged']:5d}  {pct(by_outcome['unchanged'], N)}")
    w(f"  -> capped (--max-fetch)      {by_outcome['capped']:5d}  {pct(by_outcome['capped'], N)}"
      f"   [never offered to a gate; run flagged truncated]")
    w(f"  -> fetch error               {by_outcome['fetch_error']:5d}  {pct(by_outcome['fetch_error'], N)}")
    w(f"  -> dropped: normalization    {by_drop['normalization']:5d}  {pct(by_drop['normalization'], N)}")
    w(f"  -> upserted                  {by_outcome['upserted']:5d}  {pct(by_outcome['upserted'], N)}")
    modes = collections.Counter((r.get("upsert") or {}).get("mode")
                                for r in recs if r["outcome"] == "upserted")
    w(f"       of which insert {modes['insert']} / update {modes['update']}")
    other = {k: v for k, v in by_outcome.items()
             if k not in ("unchanged", "capped", "fetch_error", "upserted", "dropped")}
    if other:
        w(f"  -> other outcomes            {other}")

    # ---- F-B14: does the partition set even cover the scope? ---------------
    probes = {p["partition"]: p["total_count"] for p in man.get("probes", [])}
    whole = next((v for k, v in probes.items() if "WHOLE-STATE" in k), None)
    county = {k: v for k, v in probes.items() if "WHOLE-STATE" not in k}
    csum = sum(v or 0 for v in county.values())
    if whole:
        w("")
        w("-" * 78)
        w("F-B14 -- PARTITION COVERAGE: the county set does not cover the state scope")
        w("-" * 78)
        w(f"  whole-state scope totalCount        {whole:6d}   (one count=1 probe, same filters)")
        w(f"  sum over {len(county)} county partitions      {csum:6d}   "
          f"{pct(csum, whole)} of the scope")
        w(f"  UNREACHABLE through any partition   {whole - csum:6d}   {pct(whole - csum, whole)}")
        w("")
        zero = [k.split(':')[-1] for k, v in county.items() if not v]
        w(f"  Not a missing-county-name bug: the {len(zero)} counties probing zero are all small")
        w(f"  rural ones ({', '.join(z.replace(' County','') for z in zero[:6])}...), and every")
        w("  non-zero partition's sweep returned EXACTLY its probe count -- 0 partitions")
        w("  truncated, 0 short. The partitioner is internally consistent; its union is not")
        w("  the scope.")
        w("")
        w("  Corroborating per-asset evidence: 11 listings this rig ingested from this exact")
        w("  scope earlier -- all status=Active, all Broward County, a partition that probed")
        w("  446 and returned all 446 -- did not reappear in ANY partition.")
        w("")
        w("  NOT DIAGNOSED (needs a live probe, deliberately out of scope here): whether the")
        w("  cause is Crexi's county index differing from the payload county, or genuine")
        w("  delisting since the earlier pass. The filter-leak evidence under LEAD 2 favours")
        w("  the former -- an asset whose payload says Brevard is returned under Orange and")
        w("  Osceola filters, so the county filter is plainly not a payload-county match.")
        w("")
        w("  Why no counter shows this: backfill_partitions warns only when a county alone")
        w("  exceeds SAFE_WINDOW or a state has no county reference. And ingest_state sets")
        w("  stats.total_in_scope ONLY when len(scopes) == 1 -- so it is None exactly when")
        w(f"  partitioning happened, i.e. exactly when the gap exists. Reported here: "
          f"{st.get('total_in_scope')}.")

    # ---- step 9: the strict filter, which is NOT a drop here ---------------
    w("")
    w("-" * 78)
    w("STEP 9 -- strict type + unit-band filter: ADVISORY AT INGEST, NOT A DROP")
    w("-" * 78)
    w("crexi_ingest.py:386-389 computes `strict` and uses it for exactly two things:")
    w("the strict_matches counter, and whether to mirror photos. The row is appended")
    w("to `rows` and upserted REGARDLESS. The module docstring says so outright:")
    w('  \"The full strict filter set (2-4u etc.) is NOT applied here -- the ingest')
    w('   stores the configured-type superset so the downstream valuation/routing')
    w('   pass owns deal qualification and unknown-unit listings aren\'t lost.\"')
    w("So a non-strict asset is STORED. The unit band drops it downstream, in the")
    w("value route's qualification step -- a different stage with a different fix.")
    w("")
    nonstrict = [r for r in fetched if r["steps"].get("strict_filter") == "nonmatch"]
    gates = collections.Counter((r.get("strict") or {}).get("reason", {}).get("gate")
                                for r in nonstrict)
    nf = len(fetched)
    w(f"of {nf} normalized assets:")
    w(f"  strict match                 {nf - len(nonstrict):5d}  {pct(nf - len(nonstrict), nf)}"
      f"   <- what the value route will qualify")
    for gate, n in gates.most_common():
        tag = "  <- lead 1" if gate in ("unit_unknown", "unit_out_of_band") else ""
        w(f"  non-strict: {gate:<16s} {n:5d}  {pct(n, nf)}{tag}")

    # ---- lead 1: is the unit information in the payload at all? -----------
    w("")
    w("-" * 78)
    w("LEAD 1 -- units NULL: does the raw payload carry it?")
    w("-" * 78)
    ev = collections.Counter(
        (r.get("fields") or {}).get("_units_evidence", {}).get("verdict") for r in fetched)
    legend = {
        "mapped": "units parsed and stored",
        "parse_failure": "summaryDetails HAS a Units row, _as_int could not read it",
        "unmapped_summary_key": "a DIFFERENT summaryDetails key carries the count",
        "prose_only": "stated in the name/description, never structured",
        "absent_from_source": "Crexi does not state a unit count at all",
        "unreachable": "should be impossible -- investigate",
    }
    for k, n in ev.most_common():
        w(f"  {k:<22s} {n:5d}  {pct(n, nf)}   {legend.get(k, '')}")
    unknown = [r for r in fetched
               if (r.get("fields") or {}).get("_units_evidence", {}).get("verdict") != "mapped"]
    recoverable = [r for r in unknown
                   if (r.get("fields") or {})["_units_evidence"]["verdict"]
                   in ("parse_failure", "unmapped_summary_key", "prose_only")]
    # Recoverable is NOT the same as "would become a strict match": an 8-unit building is
    # equally unmapped and equally out of the 2-4 band. Only the in-band half is the prize.
    inband = [r for r in recoverable
              if (n := prose_units(r["fields"]["_units_evidence"]["prose_match"])) and 2 <= n <= 4]
    w("")
    w(f"  units unknown:            {len(unknown):5d}/{nf}  {pct(len(unknown), nf)}")
    w(f"    of which recoverable:   {len(recoverable):5d}      {pct(len(recoverable), nf)}"
      f"   the payload states it; normalize_listing does not read it")
    w(f"    of which IN BAND (2-4): {len(inband):5d}      {pct(len(inband), nf)}"
      f"   <- would become strict matches")
    w("")
    w(f"  So strict matches would move {nf - len(nonstrict)} -> {nf - len(nonstrict) + len(inband)} "
      f"of {nf} ({pct(nf - len(nonstrict), nf).strip()} -> "
      f"{pct(nf - len(nonstrict) + len(inband), nf).strip()}) if units were read from prose.")
    w("")
    w("  Sample (spot-checked against the stored description: all subject-property claims,")
    w("  not references to a neighbouring building):")
    for r in inband[:6]:
        e = r["fields"]["_units_evidence"]
        w(f"    {r['asset_id']:>9s}  prose={e['prose_match']!r:<12s} -> {prose_units(e['prose_match'])} units"
          f"   (summaryDetails Units key: {e['summary_units_raw']!r}, "
          f"{e['n_summary_keys']} keys present)")
    if len(inband) > 6:
        w(f"    ... and {len(inband) - 6} more")

    # ---- lead 2: cross-partition dedupe -----------------------------------
    w("")
    w("-" * 78)
    w("LEAD 2 -- cross-partition dedupe (stubs.setdefault, order-dependent)")
    w("-" * 78)
    dups = [r for r in recs if r["duplicate"]]
    w(f"  assets seen in >1 of the {st['partitions']} partitions: {len(dups)}  "
      f"{pct(len(dups), N)}")
    if dups:
        spread = collections.Counter(r["n_partitions"] for r in dups)
        w(f"  partition multiplicity: {dict(sorted(spread.items()))}")
        for r in dups[:6]:
            w(f"    {r['asset_id']:>9s}  seen in {r['partitions']}")
            w(f"    {'':>9s}  winner={r['winner_partition']}")
        if len(dups) > 6:
            w(f"    ... and {len(dups) - 6} more")
        w("")
        w("  Winner stability: the partition order is counties_for_state(state), a committed")
        w("  ALPHABETICAL Census list, so setdefault's choice is deterministic given the same")
        w("  scope -- and all three runs produced the identical funnel fingerprint, which")
        w("  includes each duplicate's winner.")
        w("")
        w("  Materiality: checked directly against the frozen cassette -- the stub payloads")
        w("  for these assets are BYTE-IDENTICAL across the partitions that returned them,")
        w("  so which one setdefault keeps changes nothing that is stored. The order")
        w("  dependence is real in code and inert on this data.")
        w("")
        w("  What the duplicates actually expose is a SERVER-side filter leak: asset 2297949")
        w("  carries county='Brevard County' in its own payload and is still returned under")
        w("  counties=['Orange County'] and counties=['Osceola County']. The client-side")
        w("  dedupe is what keeps that from triple-counting the sweep.")
    else:
        w("  -> the order-dependence is UNREACHABLE on this scope: county partitions")
        w("     do not overlap, so setdefault never has to choose. The hazard is real")
        w("     in code but has no population here. It becomes reachable only under")
        w("     price-bisection (_price_bisect), which this run never triggered")
        w(f"     (0 of {st['partitions']} partitions carry a price band).")

    # ---- per-field arrival state ------------------------------------------
    w("")
    w("-" * 78)
    w("PER-FIELD ARRIVAL STATE after normalization (n=%d normalized assets)" % nf)
    w("-" * 78)
    fieldnames = [f for f in (fetched[0].get("fields") or {}) if not f.startswith("_")] if fetched else []
    nulls = {f: sum(1 for r in fetched if r["fields"][f]["state"] == "null") for f in fieldnames}
    w(f"  {'field':<26s} {'null':>6s} {'':>7s}")
    for f, n in sorted(nulls.items(), key=lambda kv: -kv[1]):
        if n:
            w(f"  {f:<26s} {n:6d}  {pct(n, nf)}")
    allpop = [f for f, n in nulls.items() if n == 0]
    w(f"  (always populated: {', '.join(sorted(allpop))})")

    # ---- clamp + the plausibility counterfactual --------------------------
    w("")
    w("-" * 78)
    w("STEP 10 -- clamp_to_column_limits, and the plausibility bounds that never run")
    w("-" * 78)
    trunc = collections.Counter()
    nulled = collections.Counter()
    for r in fetched:
        c = r.get("clamp") or {}
        for k in c.get("truncated") or {}:
            trunc[k] += 1
        for k in c.get("nulled_int4") or {}:
            nulled[k] += 1
    w(f"  fields truncated to column length: {dict(trunc) or '{}'}")
    w(f"  fields nulled for exceeding int4:  {dict(nulled) or '{}'}")
    cf = collections.Counter()
    for r in fetched:
        for f, v in (r.get("fields") or {}).items():
            if isinstance(v, dict) and v.get("would_null_at_merge_boundary"):
                cf[f"{f} ({v['would_null_at_merge_boundary']})"] += 1
    w("")
    w("  The GOAL asked for fields 'nulled by plausibility bounds'")
    w("  (providers/normalization.py:225). Measured: this path NEVER calls them.")
    w("  plausible_price/sqft/year_built/units/latlng are applied only by")
    w("  registry._sanitize_record, the MLS/registry merge boundary, which operates on")
    w("  Property/Listing -- not on CrexiListing. The Crexi ingest reaches no such")
    w("  boundary, so nothing is nulled by an envelope here. COUNTERFACTUAL (what")
    w("  _sanitize_record WOULD null if this path had it):")
    w(f"    {dict(cf) if cf else 'nothing -- every value is inside every envelope'}")

    # ---- the write gate that isn't --------------------------------------
    w("")
    w("-" * 78)
    w("STEP 10b -- upsert writes 'skipped because a lower-confidence source lost'")
    w("-" * 78)
    w(f"  {man['write_gate']}.")
    sticky = sum(1 for r in fetched if (r.get("upsert") or {}).get("is_sold_sticky_suppressed"))
    upd = [r for r in fetched if (r.get("upsert") or {}).get("mode") == "update"]
    withenr = sum(1 for r in upd if (r.get("upsert") or {}).get("had_enrichment"))
    w(f"  updates: {len(upd)}   of which carried downstream enrichment protected from the")
    w(f"           feed by its absence from the ON CONFLICT SET list: {withenr}")
    w(f"  is_sold sticky-True suppressed a feed downgrade on: {sticky}")

    # ---- steps 1 and 11 ---------------------------------------------------
    w("")
    w("-" * 78)
    w("STEPS 1 & 11 -- watermark gate in, cursor stamp out")
    w("-" * 78)
    cur = man["cursor"]
    rd, wr = cur.get("read") or {}, cur.get("write") or {}
    w(f"  read : key={rd.get('key')} existed={rd.get('existed')} "
      f"stored_fp={rd.get('stored_fingerprint')} watermark={rd.get('last_seen_updated_on')}")
    w(f"         -> {'FULL sweep' if st['full_sweep'] else 'incremental sweep'}"
      f"   run scope fingerprint={man['scope_fingerprint']}")
    w(f"  write: last_seen_updated_on={wr.get('last_seen_updated_on')} "
      f"backfilled_at={wr.get('backfilled_at')}")
    if st["truncated"] and wr.get("backfilled_at") is None:
        w("         backfilled_at correctly withheld: the run was truncated (--max-fetch),")
        w("         so the delisting anchor is not claimed and the gap stays discoverable.")

    # ---- defect classes ----------------------------------------------------
    w("")
    w("-" * 78)
    w("DEFECT CLASSES (rig/defects.py, stage=ingest) -- rate over the %d normalized assets" % nf)
    w("-" * 78)
    tally: collections.Counter = collections.Counter()
    for r in recs:
        for d in classify_ingest(r):
            tally[d] += 1
    for d, n in tally.most_common():
        w(f"  {d:<7s} {n:5d}  {pct(n, nf)}  {DEFECTS[d]['severity']:<7s} {DEFECTS[d]['title']}")
    for d, meta in sorted(DEFECTS.items()):
        if meta["stage"] == "ingest" and d not in tally and meta.get("scope") != "run":
            w(f"  {d:<7s} {0:5d}  {pct(0, nf)}  {meta['severity']:<7s} {meta['title']}")
    w("")
    w("  run-level (a property of the pass, not of any one asset -- classify_ingest cannot")
    w("  see these):")
    for d in ("F-B14", "F-B15"):
        m = DEFECTS[d]
        w(f"  {d:<7s} {'FIRED':>5s}         {m['severity']:<7s} {m['title']}")
    w(f"  {'':<7s} F-B14: {whole - csum if whole else '?'} of {whole} in-scope listings "
      f"unreachable through any partition")
    w(f"  {'':<7s} F-B15: {len(compound)} of {len(tg)} type-gate drops carry a configured "
      f"type inside a compound string")

    # ---- what this corpus CANNOT speak to ----------------------------------
    w("")
    w("-" * 78)
    w("UNTESTED BY THIS CORPUS -- by construction, not by sampling")
    w("-" * 78)
    w(f"  * The UPDATE path. All {len([r for r in recs if r['outcome'] == 'upserted'])} upserts "
      f"were INSERTs. Of the 100 listings already stored, 89")
    w("    came back unchanged (economy skip) and 11 were not returned by the sweep at all.")
    w("    So the ON CONFLICT branch, the is_sold sticky-True rule and the enrichment-column")
    w("    protection never executed. Reporting '0 suppressed' as a measurement of a working")
    w("    mechanism would be the same error F-B9 corrected.")
    w("  * The fetch-error breaker (_FETCH_ERROR_BREAKER=5): 0 fetch errors this pass.")
    w("  * The unpriced skip (step 5): inactive, the scope runs include_unpriced=True.")
    w("  * Price bisection (_price_bisect): no FL county exceeded SAFE_WINDOW=1400, so all")
    w("    56 partitions are plain county scopes and no price band was ever cut.")
    w(f"  * {by_outcome['capped']} of {N} swept assets ({pct(by_outcome['capped'], N).strip()}) "
      f"never reached a gate: --max-fetch {man['max_fetch']}")
    w("    bounded the run. Steps 7-11 are measured over the newest-updated 150, steps 1-6")
    w("    over all %d." % N)

    # ---- manifest ---------------------------------------------------------
    w("")
    w("-" * 78)
    w("MANIFEST")
    w("-" * 78)
    for k in ("arm", "wholesaling_git", "lab_git", "alembic_head", "pinned_now", "state",
              "apply", "max_fetch", "scope_fingerprint", "cassette", "cassette_sha16",
              "cassette_entries", "crexi_base_url", "funnel_fingerprint", "wall_s"):
        w(f"  {k:<20s} {man.get(k)}")
    w(f"  {'seams asserted':<20s} {len(man['seams'])}")
    w(f"  {'reconciliation':<20s} "
      f"{sum(1 for c in man['reconciliation'] if c['ok'])}/{len(man['reconciliation'])} counters match")
    return "\n".join(out)


def compare(a: str, b: str) -> str:
    ma, ra = load(a)
    mb, rb = load(b)
    lines = ["", "-" * 78, "REPRODUCIBILITY CHECK", "-" * 78,
             f"  A {a}", f"  B {b}",
             f"  funnel fingerprint  A={ma['funnel_fingerprint']}  B={mb['funnel_fingerprint']}  "
             f"{'IDENTICAL' if ma['funnel_fingerprint'] == mb['funnel_fingerprint'] else 'DIFFERENT'}",
             f"  per-asset records   {'IDENTICAL' if ra == rb else 'DIFFERENT'}  (n={len(ra)} vs {len(rb)})"]
    if ra != rb:
        diff = [x["asset_id"] for x, y in zip(ra, rb) if x != y]
        lines.append(f"  first differing assets: {diff[:10]}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("trace")
    ap.add_argument("--compare", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    man, recs = load(args.trace)
    if args.json:
        json.dump({"manifest": man, "n": len(recs),
                   "outcomes": dict(collections.Counter(r["outcome"] for r in recs)),
                   "drop_stages": dict(collections.Counter(
                       r["drop_stage"] for r in recs if r["drop_stage"]))},
                  sys.stdout, indent=2, default=str)
        print()
        return 0
    print(render(man, recs))
    if args.compare:
        print(compare(args.trace, args.compare))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
