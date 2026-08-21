"""M0 — frozen metric computation + mechanical decision-table application.

Reads artifacts/m0_paired_probe.csv (the WP-B record) and recomputes every § 6
metric from raw fields, so any headline number in M0_REPORT.md is regenerable with:

    python scripts/m0_metrics.py

The decision logic is the rev-4 frozen rule, applied in order:

    1. PRECEDENCE GATE: n_control_reconfirmed < 10  →  RE-SCOPE / INCONCLUSIVE,
       regardless of f_rescue. Poor reconfirmation can never support DROP.
    2. Bands on f_rescue = n_rescue / n_control_reconfirmed (UNDEFINED at
       denominator 0 — reported as UNDEFINED, never coerced to 0%):
         >= 0.30                    → STRONG R7 GO
         0.10 <= f < 0.30           → R7 RE-SCOPE
         <  0.10                    → R7 DROP (requires the gate passed)
    3. Completion (f_complete) is diagnostic context and can never produce a GO.

The output is a RECOMMENDATION to the scientific owner, not an autonomous gate;
boundary readings fall to the owner (NEXT_STEP_M0.md § 7).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "artifacts" / "m0_paired_probe.csv"
OUT_PATH = ROOT / "artifacts" / "m0_metrics.json"

GO_BAND = 0.30
DROP_BAND = 0.10
PRECEDENCE_MIN_RECONFIRMED = 10


def _bool(v: str) -> bool:
    return str(v).strip().lower() in ("true", "1", "yes")


def compute(rows: list[dict[str, str]]) -> dict:
    n_hist_cap = len(rows)
    reconfirmed = [r for r in rows if _bool(r["reconfirmed"])]
    non_reconfirmed = [r for r in rows if not _bool(r["reconfirmed"])]
    n_reconf = len(reconfirmed)

    def n_class(c: str) -> int:
        return sum(1 for r in reconfirmed if r["treatment_class"] == c)

    n_rescue = n_class("a")
    n_wrong_complete = n_class("b")
    n_still_trunc = n_class("c") + n_class("d")
    n_conv, n_degen = n_class("c"), n_class("d")
    n_edge_e = n_class("e")
    n_complete = n_rescue + n_wrong_complete

    def frac(num: int, den: int) -> float | None:
        return round(num / den, 4) if den else None

    f_rescue = frac(n_rescue, n_reconf)
    metrics = {
        "n_hist_cap": n_hist_cap,
        "n_control_reconfirmed": n_reconf,
        "f_reconfirm": frac(n_reconf, n_hist_cap),
        "n_rescue": n_rescue,
        "f_rescue": "UNDEFINED" if f_rescue is None else f_rescue,
        "n_wrong_complete": n_wrong_complete,
        "f_wrong_complete": "UNDEFINED" if n_reconf == 0 else frac(n_wrong_complete, n_reconf),
        "n_still_truncated": n_still_trunc,
        "n_still_truncated_convergent": n_conv,
        "n_still_truncated_degenerate": n_degen,
        "n_completed_unparseable_edge": n_edge_e,
        "f_complete": "UNDEFINED" if n_reconf == 0 else frac(n_complete, n_reconf),
        "pass_given_completion": frac(n_rescue, n_complete),
        "non_reconfirmed_cases": [
            {"scenario_id": r["scenario_id"],
             "control_stop_reason": r["control_stop_reason"],
             "control_pass": r["control_pass"],
             "control_output_tokens": r["control_output_tokens"],
             "treatment_class_descriptive_only": r["treatment_class"]}
            for r in non_reconfirmed],
        "order_balance": {
            "AB": sum(1 for r in rows if r["order"] == "AB"),
            "BA": sum(1 for r in rows if r["order"] == "BA"),
            "rescues_AB": sum(1 for r in reconfirmed
                              if r["order"] == "AB" and r["treatment_class"] == "a"),
            "rescues_BA": sum(1 for r in reconfirmed
                              if r["order"] == "BA" and r["treatment_class"] == "a"),
        },
        "input_tokens_all_equal": all(_bool(r["input_tokens_equal"]) for r in rows),
    }

    # ------------------------------------------------------------ frozen decision
    if n_reconf < PRECEDENCE_MIN_RECONFIRMED:
        verdict = {
            "row": "R7 RE-SCOPE / INCONCLUSIVE (precedence gate)",
            "reason": (f"n_control_reconfirmed={n_reconf} < {PRECEDENCE_MIN_RECONFIRMED}: "
                       "the historical premise / causal denominator is unstable — this is "
                       "NOT evidence that extra budget fails to rescue, and it can never "
                       "support DROP"),
        }
    elif f_rescue is None:
        verdict = {"row": "R7 RE-SCOPE / INCONCLUSIVE", "reason": "f_rescue UNDEFINED"}
    elif f_rescue >= GO_BAND:
        verdict = {"row": "STRONG R7 GO",
                   "reason": f"f_rescue={f_rescue:.0%} >= {GO_BAND:.0%} — material "
                             "deterministic rescue, not just completion"}
    elif f_rescue >= DROP_BAND:
        verdict = {"row": "R7 RE-SCOPE",
                   "reason": f"f_rescue={f_rescue:.0%} in [{DROP_BAND:.0%}, {GO_BAND:.0%})"}
    else:
        verdict = {"row": "R7 DROP / R9 MOVES UP",
                   "reason": f"f_rescue={f_rescue:.0%} < {DROP_BAND:.0%} with the gate "
                             "passed (diagnostic pattern to be read alongside: "
                             f"wrong_complete={n_wrong_complete}, degenerate={n_degen})"}
    verdict["note"] = ("Recommendation to the scientific owner, not an autonomous gate; "
                      "completion alone can never produce GO (f_complete is context).")
    return {"metrics": metrics, "decision": verdict,
            "frozen_bands": {"go": GO_BAND, "drop": DROP_BAND,
                             "precedence_min_reconfirmed": PRECEDENCE_MIN_RECONFIRMED}}


def main() -> None:
    if not CSV_PATH.exists():
        sys.exit(f"!! {CSV_PATH} missing — run the paired probe first")
    rows = list(csv.DictReader(CSV_PATH.open()))
    if len(rows) != 15:
        sys.exit(f"!! expected 15 pairs in {CSV_PATH}, found {len(rows)} — a partial "
                 "session never enters the analysis")
    out = compute(rows)
    OUT_PATH.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
