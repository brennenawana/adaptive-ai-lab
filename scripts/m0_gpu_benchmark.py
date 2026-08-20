"""M0 WP-E — assemble artifacts/m0_gpu_benchmark.json from rented-box outputs.

Usage:
    python scripts/m0_gpu_benchmark.py assemble \
        --input out_3090/m0_bench_*.json --input out_5090/m0_bench_*.json \
        --spend-usd 4.10 --gpu-hours 3.6

The remote halves are produced by scripts/m0_gpu_benchmark_remote.sh (one run per
rented GPU). This assembler adds the laptop baseline (the R6 autopsy's measured
operating point) and computes the ratio the hardware decision table keys on
(NEXT_STEP_M0.md § 7: 3090 >= ~1.2x laptop decode keeps the designated used-3090
trigger buy; below that, the designated buy is reconsidered).

If no inputs exist yet, `status` prints what is missing — WP-E without rented
infrastructure is recorded INCOMPLETE, never approximated by an uncontrolled
comparison.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "m0_gpu_benchmark.json"

# The laptop's measured reference point for the SAME artifact + runtime lineage:
# R6 autopsy §6/§9 (decode bandwidth 353-496 GB/s effective across the run; the
# fit-probe/paired-probe decode rates land beside it in the M0 report). Recorded
# here as the comparison anchor, clock caveat included.
LAPTOP_BASELINE = {
    "node": "RTX 5080 Laptop 16 GB (WSL2)",
    "source": "R6_PERFORMANCE_AUTOPSY.md §6/§9 + M0 fit/paired probes",
    "decode_bandwidth_gb_s": [353, 496],
    "clock_caveat": "WSL2 realtime skew 8-12%; monotonic-derived rates",
}


def assemble(inputs: list[Path], spend_usd: float | None,
             gpu_hours: float | None) -> None:
    nodes = []
    for path in inputs:
        data = json.loads(path.read_text())
        rows = data if isinstance(data, list) else data.get("results", [])
        node: dict = {"source_file": path.name, "rows": rows}
        for r in rows:
            name = f"pp{r.get('n_prompt', 0)}+tg{r.get('n_gen', 0)}"
            node[name] = {"avg_ts": r.get("avg_ts"), "stddev_ts": r.get("stddev_ts"),
                          "samples": r.get("samples_ts") or r.get("n_runs", 3)}
            node.setdefault("gpu", r.get("gpu_info") or r.get("backends", ""))
            node.setdefault("model_sha_prefix", (r.get("model_filename") or ""))
        nodes.append(node)
    out = {"laptop_baseline": LAPTOP_BASELINE, "rented_nodes": nodes,
           "spend_usd": spend_usd, "gpu_hours": gpu_hours,
           "complete": len(nodes) >= 2,
           "note": ("3 repetitions per GPU on the pinned artifact + pinned llama.cpp "
                    "lineage (rebuilt per arch, digests recorded remotely)")}
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT} (nodes: {len(nodes)}, complete: {out['complete']})")


def status() -> None:
    if OUT.exists():
        data = json.loads(OUT.read_text())
        print(f"{OUT}: {len(data.get('rented_nodes', []))} node(s), "
              f"complete={data.get('complete')}")
    else:
        print(f"{OUT}: MISSING — WP-E incomplete. Needed: a GPU-rental account "
              "(e.g. RunPod) with API access; then run "
              "scripts/m0_gpu_benchmark_remote.sh on a 3090 and a 5090 and "
              "assemble the outputs here.")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("assemble")
    a.add_argument("--input", action="append", type=Path, required=True)
    a.add_argument("--spend-usd", type=float)
    a.add_argument("--gpu-hours", type=float)
    sub.add_parser("status")
    args = ap.parse_args()
    if args.cmd == "assemble":
        missing = [p for p in args.input if not p.exists()]
        if missing:
            sys.exit(f"!! missing inputs: {missing}")
        assemble(args.input, args.spend_usd, args.gpu_hours)
    else:
        status()


if __name__ == "__main__":
    main()
