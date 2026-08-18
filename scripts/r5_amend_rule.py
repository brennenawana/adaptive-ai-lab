"""R5 — derive the § 12a numbers of the selection rule from TRAIN evidence, mechanically.

Contract § 12 fixes the FORMULAS before TRAIN is seen; this script applies them to the
TRAIN reports written by `scripts/r5_train.py` and writes
`learning/registry/r5/selection_rule.json`, which `scripts/r5_replay.py --select` reads.
It exists so the amendment is a computation over committed TRAIN artifacts rather than
a number typed by hand after looking at anything.

    K        = max(3, ceil(0.25 · routing_FN(R4 on the split)))     [applied at replay]
    Δ_util   = min(0.20, 1.5 · max over ELIGIBLE candidates of the OOF escalation-rate
               increase at τ* — (catches + unnecessary) / N_train)
    E_max    = ceil(1.5 · max over ELIGIBLE candidates of the OOF unnecessary rate at τ*
               (unnecessary / N_train) · 48)

If a local model has no eligible candidate, its Δ_util and E_max are recorded as null:
the rule cannot pass anything for it, and DEV selection reports that outcome. The
absolute caps of § 12 (utilization ≤ 50 %) are unchanged.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.suite import git_head  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "learning" / "registry" / "r5"
DEV_N = 48
SLACK = 1.5
DELTA_UTIL_CAP = 0.20


def derive(report: dict, protocol: str = "grouped") -> dict:
    """§ 12a. PRIMARY (grouped): Δ_util = min(0.20, 1.5 × max OOF escalation-rate increase),
    utilization also ≤ 0.50 absolute — the skeleton's a-priori caps. SECONDARY (stratified,
    § 12a-2): the same 1.5× TRAIN-derived slack WITHOUT the a-priori caps — TRAIN showed
    the caps forbid any FN-catching router for a local model whose R4-accepted subset is
    mostly unsafe, whatever its ranking quality; non-degeneracy is carried by E_max."""
    elig = [c for c in report["candidates"] if c["eligible"]]
    rows = []
    for c in report["candidates"]:
        t = c["cv"]["at_threshold"]
        rows.append({"policy_id": c["policy_id"], "eligible": c["eligible"], "threshold": c["threshold"],
                     "oof_escalation_rate_all": t["escalation_rate_all"],
                     "oof_unnecessary_rate_all": t["unnecessary_rate_all"],
                     "oof_catches": t["catches"], "oof_unnecessary": t["unnecessary"]})
    capped = protocol == "grouped"
    if not elig:
        return {"eligible_candidates": [], "delta_util": None, "e_max": None,
                "absolute_cap": 0.50 if capped else None, "inputs": rows}
    esc = max(c["cv"]["at_threshold"]["escalation_rate_all"] for c in elig)
    unn = max(c["cv"]["at_threshold"]["unnecessary_rate_all"] for c in elig)
    return {
        "eligible_candidates": [c["policy_id"] for c in elig],
        "delta_util": round(min(DELTA_UTIL_CAP, SLACK * esc) if capped else SLACK * esc, 6),
        "e_max": math.ceil(SLACK * unn * DEV_N),
        "absolute_cap": 0.50 if capped else None,
        "derivation": {"max_oof_escalation_rate_all": esc, "max_oof_unnecessary_rate_all": unn,
                       "slack": SLACK, "delta_util_cap": DELTA_UTIL_CAP if capped else None,
                       "dev_n": DEV_N},
        "inputs": rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--qwen", default=str(REG / "train_report_qwen.json"))
    ap.add_argument("--nemotron", default=str(REG / "train_report_nemotron.json"))
    ap.add_argument("--out", default=str(REG / "selection_rule.json"))
    args = ap.parse_args()
    out_path = Path(args.out)
    out = json.loads(out_path.read_text()) if out_path.exists() else {"per_model": {}}
    out.update({"contract": "docs/R5_EXPERIMENT_CONTRACT.md § 12 + § 12a",
                "K_formula": "max(3, ceil(0.25 * routing_FN(R4 on the split)))",
                "utilization_cap": 0.50, "code_commit": git_head()})
    for m, base in (("qwen", args.qwen), ("nemotron", args.nemotron)):
        for protocol in ("grouped", "stratified"):
            path = Path(base) if protocol == "grouped" else Path(base).with_name(
                Path(base).name.replace(".json", "_stratified.json"))
            if not path.exists():
                print(f"({m}/{protocol}: no TRAIN report at {path}; entry left as is)")
                continue
            if protocol in out["per_model"].get(m, {}):
                # An entry is written once, from the TRAIN report, before that model's DEV
                # replay. Re-deriving would only matter if the TRAIN report changed, which
                # would mean re-training after DEV — not allowed.
                print(f"({m}/{protocol}: entry already present; not overwritten)")
                continue
            rep = json.loads(path.read_text())
            out["per_model"].setdefault(m, {})[protocol] = {
                "train_report": str(path.relative_to(ROOT)), "train_run_id": rep["train_run_id"],
                "dataset_digest": rep["dataset_digest"], **derive(rep, protocol)}
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    print(f"\nwritten: {args.out}")


if __name__ == "__main__":
    main()
