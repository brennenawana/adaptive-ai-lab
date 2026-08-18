"""R6 DEV qualification gates — the numbers of docs/R6_EXPERIMENT_CONTRACT.md § 11, as code.

They are constants here so that (1) the contract-freeze commit can record
`gates_digest = digest(GATES)` in every candidate's CONTRACT_FROZEN entry and (2) the
DEV_QUALIFIED / DEV_REJECTED transition can be produced by one function applied to the
DEV metrics, with the evaluation trace stored in the registry. Nothing in this module
reads a result file or the database; it is pure.

Historical DEV inputs (n = 48): Qwen3-8B all-pass 17, no-output 1, p50 12,864 ms;
Nemotron all-pass 23, no-output 12, p50 53,840.5 ms (p50 = statistics.median of wall_ms).
"""

from __future__ import annotations

from typing import Any

from fis_platform.routing.learn import digest

GATES: dict[str, Any] = {
    "contract": "docs/R6_EXPERIMENT_CONTRACT.md § 11",
    "n_dev": 48,
    "historical": {
        "qwen3-8b": {"all_pass": 17, "no_output": 1, "p50_wall_ms": 12864},
        "nemotron": {"all_pass": 23, "no_output": 12, "p50_wall_ms": 53840.5},
    },
    "modern_small": {
        "all_pass_min": 22,           # >= Qwen3-8B + 5
        "no_output_max": 8,
        "p50_wall_ms_max": 38592,     # 3 x Qwen3-8B p50 (12,864)
    },
    "modern_strong": {
        "all_pass_min": 23,           # >= Nemotron
        "or": {
            "all_pass_min": 21,       # within 2 cases of Nemotron, plus an operational advantage:
            "p50_wall_ms_max": 40380,     # <= 0.75 x Nemotron p50 (53,840.5)   (either this ...)
            "no_output_max": 6,           # <= half Nemotron's no-output (... or this)
        },
    },
    "efficiency": {
        "all_pass_min": 20,           # quality floor: >= Qwen3-8B + 3
        "gpu_mem_ratio_max": 0.65,    # resident GPU memory vs the Qwen3.8 selected quant
        "p50_wall_ratio_max": 1.25,   # p50 wall vs the Qwen3.8 selected quant
        "fallback_reference": "nemotron",   # if no Qwen3.8 DEV numbers exist
    },
}

GATES_DIGEST = digest(GATES)


def _m(metrics: dict, key: str) -> Any:
    if key not in metrics or metrics[key] is None:
        raise KeyError(f"gate input {key!r} missing from DEV metrics")
    return metrics[key]


def evaluate_gates(role: str, metrics: dict, reference: dict | None = None) -> dict:
    """Apply § 11 to a candidate's DEV metrics.

    `metrics` needs: all_pass, no_output, p50_wall_ms (and, for the efficiency role,
    gpu_mem_used_mib). `reference` (efficiency role only) is the comparison system's
    DEV metrics: p50_wall_ms and gpu_mem_used_mib. Returns a dict with `qualified`, the
    per-clause values and verdicts, and the gates digest that was applied.
    """
    out: dict[str, Any] = {"role": role, "gates_digest": GATES_DIGEST, "clauses": {}}
    c = out["clauses"]
    ap, no_out, p50 = _m(metrics, "all_pass"), _m(metrics, "no_output"), _m(metrics, "p50_wall_ms")

    if role == "modern_small":
        g = GATES["modern_small"]
        c["all_pass"] = {"value": ap, "min": g["all_pass_min"], "ok": ap >= g["all_pass_min"]}
        c["no_output"] = {"value": no_out, "max": g["no_output_max"], "ok": no_out <= g["no_output_max"]}
        c["p50_wall_ms"] = {"value": p50, "max": g["p50_wall_ms_max"], "ok": p50 <= g["p50_wall_ms_max"]}
        out["qualified"] = all(x["ok"] for x in c.values())

    elif role == "modern_strong":
        g = GATES["modern_strong"]
        c["all_pass_ge_nemotron"] = {"value": ap, "min": g["all_pass_min"], "ok": ap >= g["all_pass_min"]}
        alt = g["or"]
        c["alt_all_pass"] = {"value": ap, "min": alt["all_pass_min"], "ok": ap >= alt["all_pass_min"]}
        c["alt_p50_wall_ms"] = {"value": p50, "max": alt["p50_wall_ms_max"], "ok": p50 <= alt["p50_wall_ms_max"]}
        c["alt_no_output"] = {"value": no_out, "max": alt["no_output_max"], "ok": no_out <= alt["no_output_max"]}
        alt_ok = c["alt_all_pass"]["ok"] and (c["alt_p50_wall_ms"]["ok"] or c["alt_no_output"]["ok"])
        c["alternative_branch"] = {"ok": alt_ok}
        out["qualified"] = c["all_pass_ge_nemotron"]["ok"] or alt_ok

    elif role == "efficiency":
        g = GATES["efficiency"]
        if reference is None:
            raise KeyError("efficiency gate needs the reference system's DEV metrics")
        ref_p50, ref_mem = _m(reference, "p50_wall_ms"), _m(reference, "gpu_mem_used_mib")
        mem = _m(metrics, "gpu_mem_used_mib")
        c["all_pass"] = {"value": ap, "min": g["all_pass_min"], "ok": ap >= g["all_pass_min"]}
        ratio_mem = mem / ref_mem if ref_mem else float("inf")
        ratio_p50 = p50 / ref_p50 if ref_p50 else float("inf")
        c["gpu_mem_ratio"] = {"value": round(ratio_mem, 4), "max": g["gpu_mem_ratio_max"],
                              "candidate_mib": mem, "reference_mib": ref_mem,
                              "ok": ratio_mem <= g["gpu_mem_ratio_max"]}
        c["p50_wall_ratio"] = {"value": round(ratio_p50, 4), "max": g["p50_wall_ratio_max"],
                               "candidate_ms": p50, "reference_ms": ref_p50,
                               "ok": ratio_p50 <= g["p50_wall_ratio_max"]}
        out["reference"] = reference.get("label", "?")
        out["qualified"] = all(x["ok"] for x in c.values())
    else:
        raise ValueError(f"unknown candidate role {role!r}")
    return out
