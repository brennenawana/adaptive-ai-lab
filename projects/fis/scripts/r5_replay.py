"""R5 — offline replay of learned routing policies on DEV (selection) and TEST (once).

    frozen local run  +  frozen frontier run
            ↓
    RoutingFeatureSnapshot at the R4 decision point
            ↓
    risk = router(snapshot);  escalate = R4 ∨ risk ≥ τ*
            ↓
    local → the frozen local scored outcome;  escalate → the frozen frontier outcome

No model is called. Every candidate is replayed once at its TRAIN-chosen τ* (that is
what selection sees); the sweep over the threshold grid is printed as the Pareto table,
descriptively. Baselines on the same rows: local-only, R4 (`verifier`), strong-only,
post-answer oracle. Metrics are the contract's § 11 (classifier, system, silent family).

Selection (DEV): the pre-registered rule in `learning/registry/r5/selection_rule.json`
(contract § 12 + § 12a) is applied per local model to ELIGIBLE candidates only; at most
one policy is frozen under `learning/registry/r5/frozen/`.

TEST: `--split test --unlock-test <policy_id>` — refused unless the frozen artifact
records `dev_selection.result == "PASS"` and no earlier unlock exists for that policy;
the unlock is recorded in `learning/registry/r5/test_unlock.json` before any TEST label
is read. Exactly once. Nothing is tuned afterwards.

Telemetry: every decision (per policy, per case; R4 too) is persisted to
`learning.routing_decisions` — production-observable fields only.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.routing.features import (  # noqa: E402
    FEATURE_ORDER, FEATURE_SCHEMA_VERSION, is_forbidden_feature_name,
)
from fis_platform.routing.learn import (  # noqa: E402
    RouterModel, average_precision, brier, canonical_json, digest, roc_auc,
)
from fis_platform.suite import git_head  # noqa: E402
from scripts.r5_dataset import build_dataset, load_run  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")

DEFAULT_RUNS = {
    "dev": {"qwen": ("V3-qwen-dev", "E4-v3-dev"), "nemotron": ("V3-nemotron-dev", "E4-v3-dev")},
    "test": {"qwen": ("V3-qwen-96", "E4-v3-96"), "nemotron": ("V3-nemotron-96", "E4-v3-96")},
}
TRAIN_RUNS = {"qwen": "R5-qwen-train", "nemotron": "R5-nemotron-train"}     # contract § 3


class Registry:
    """Where R5's experiment state lives (contract § 13–14). Rooted at
    `learning/registry/r5` unless FIS_R5_REGISTRY_ROOT points elsewhere — tests exercise
    the state machine against a temporary root, never the canonical tree.

    State files and their invariants:
      candidates/<policy_id>.json      TRAIN artifacts (r5_train.py); read-only here
      selection_rule.json              § 12a numbers (r5_amend_rule.py)
      frozen/<model>.selection.json    ONE record per local model, written exactly once by
                                       `--select`; names the winner (or null)
      frozen/<policy_id>.json          the winner's artifact only (never a loser's)
      test_unlock.json                 append-only; at most one unlock per local model,
                                       bound to the recorded winner's digest
    """

    def __init__(self, root: Path | None = None):
        env = os.environ.get("FIS_R5_REGISTRY_ROOT")
        self.root = Path(root) if root is not None else (Path(env) if env else ROOT / "learning" / "registry" / "r5")

    @property
    def candidates(self) -> Path: return self.root / "candidates"
    @property
    def frozen(self) -> Path: return self.root / "frozen"
    @property
    def rule_file(self) -> Path: return self.root / "selection_rule.json"
    @property
    def unlock_file(self) -> Path: return self.root / "test_unlock.json"
    def selection_file(self, model: str) -> Path: return self.frozen / f"{model}.selection.json"
    def frozen_artifact(self, policy_id: str) -> Path: return self.frozen / f"{policy_id}.json"
    def dataset_meta(self, model: str) -> Path:
        return ROOT / "learning" / "datasets" / "r5" / f"{TRAIN_RUNS[model]}.meta.json"


# ------------------------------------------------------------------ outcome model

def _p50p95(xs: list[float]) -> tuple[float, float]:
    if not xs:
        return 0.0, 0.0
    s = sorted(xs)
    p50 = median(s)
    k = max(0, math.ceil(0.95 * len(s)) - 1)
    return p50, s[k]


def evaluate_policy(rows: list[dict], strong_rows: dict[str, dict], local_rows: dict[str, dict],
                    escalate: dict[str, bool]) -> dict:
    """System metrics for one decision vector over the split (contract § 11)."""
    n = len(rows)
    final_pass = esc = unnecessary = fn = rescued_needed = accepted_fail = 0
    walls, costs, local_out = [], [], 0
    for r in rows:
        sid = r["scenario_id"]
        e = escalate[sid]
        lp, sp = r["label_safe"], bool(r["strong_pass"])
        w = local_rows[sid]["score"]["wall_ms"]
        c = float(local_rows[sid]["score"].get("reference_cost_usd") or 0.0)   # weak stage always paid ($0 locally)
        local_out += sum(i.get("usage", {}).get("output_tokens", 0)
                         for i in local_rows[sid]["traj"].get("model_invocations", []))
        if e:
            esc += 1
            fp = sp
            w += strong_rows[sid]["score"]["wall_ms"]
            c += strong_rows[sid]["score"]["reference_cost_usd"]
            if lp:
                unnecessary += 1
            elif sp:
                rescued_needed += 1
        else:
            fp = lp
            if not lp:
                accepted_fail += 1
                if sp:
                    fn += 1
        final_pass += int(fp)
        walls.append(w); costs.append(c)
    p50, p95 = _p50p95(walls)
    total_cost = sum(costs)
    return {
        "n": n, "all_pass": final_pass, "all_pass_rate": final_pass / n,
        "escalated": esc, "utilization": esc / n,
        "unnecessary": unnecessary, "routing_fn": fn, "accepted_fail": accepted_fail,
        "rescued_needed": rescued_needed,
        "rescue_rate": (rescued_needed / esc) if esc else None,
        "cost_total": total_cost, "cost_per_attempt": total_cost / n,
        "cost_per_success": (total_cost / final_pass) if final_pass else None,
        "wall_p50_ms": p50, "wall_p95_ms": p95, "local_output_tokens": local_out,
    }


def classifier_metrics(rows: list[dict], risk: dict[str, float], tau: float) -> dict:
    """On the R4-accepted subset — the router's domain."""
    acc = [r for r in rows if not r["r4_escalate"]]
    y = [int(r["label_unsafe"]) for r in acc]
    p = [risk[r["scenario_id"]] for r in acc]
    tp = sum(1 for r in acc if r["label_unsafe"] and risk[r["scenario_id"]] >= tau)
    fp = sum(1 for r in acc if not r["label_unsafe"] and risk[r["scenario_id"]] >= tau)
    fn = sum(1 for r in acc if r["label_unsafe"] and risk[r["scenario_id"]] < tau)
    tn = len(acc) - tp - fp - fn
    return {
        "n_accepted": len(acc), "unsafe_in_accepted": sum(y),
        "unsafe_recall": (tp / (tp + fn)) if (tp + fn) else None,
        "unsafe_precision": (tp / (tp + fp)) if (tp + fp) else None,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "roc_auc": roc_auc(y, p) if y else None, "pr_auc": average_precision(y, p) if y else None,
        "brier": brier(y, p) if y else None,
        "base_rate": (sum(y) / len(y)) if y else None,
    }


def silent_family(rows: list[dict], escalate: dict[str, bool]) -> dict:
    """R4's verifier-clean routing FNs: caught by the policy or remaining, by kind."""
    def kind(r):
        d = r["diag"]
        if d["wrong_root_cause"]:
            return "root_cause"
        if d["evidence_miss"] and not d["action_fail"]:
            return "evidence"
        return "other"
    r4_fn = [r for r in rows if not r["r4_escalate"] and r["label_unsafe"] and r["strong_pass"]]
    caught = [r for r in r4_fn if escalate[r["scenario_id"]]]
    remaining = [r for r in r4_fn if not escalate[r["scenario_id"]]]
    new_unnecessary = [r for r in rows if not r["r4_escalate"] and r["label_safe"] and escalate[r["scenario_id"]]]
    return {
        "r4_fn": len(r4_fn),
        "caught": len(caught), "caught_by_kind": dict(Counter(kind(r) for r in caught)),
        "caught_ids": [r["scenario_id"] for r in caught],
        "remaining": len(remaining), "remaining_by_kind": dict(Counter(kind(r) for r in remaining)),
        "remaining_ids": [r["scenario_id"] for r in remaining],
        "new_unnecessary": len(new_unnecessary),
        "new_unnecessary_ids": [r["scenario_id"] for r in new_unnecessary],
    }


# ------------------------------------------------------------------ policies

# Fields the freeze/selection step adds on top of the TRAIN artifact. Excluded from the
# digest so a frozen copy verifies against the digest its candidate was trained with.
_MUTABLE_FIELDS = ("artifact_digest", "dev_selection", "local_model_short")
ELIGIBLE_CANDIDATES = ("lr_full", "lr_core", "tree")          # contract § 9


def verify_artifact(a: dict) -> None:
    """Fail closed (contract § 13): schema version, allowlist, digest, and the eligibility
    flag itself — an artifact may claim `eligible` only if it is one of the § 9 candidates
    over the production feature source, whatever its TRAIN numbers say."""
    pid = a.get("policy_id", "?")
    if a["feature_schema_version"] != FEATURE_SCHEMA_VERSION:
        raise SystemExit(f"{pid}: artifact schema {a['feature_schema_version']} != extractor "
                         f"{FEATURE_SCHEMA_VERSION} — refusing (fail closed)")
    forbidden = sorted(n for n in a["feature_names"] if is_forbidden_feature_name(n))
    if a["feature_source"] == "features":
        if not set(a["feature_names"]) <= set(FEATURE_ORDER):
            raise SystemExit(f"{pid}: features outside the allowlist — refusing")
    if a.get("eligible") and (a["feature_source"] != "features" or a["candidate"] not in ELIGIBLE_CANDIDATES
                              or forbidden):
        raise SystemExit(f"{pid}: claims eligibility but is not a § 9 candidate over production "
                         f"features (source={a['feature_source']}, forbidden={forbidden}) — refusing")
    recomputed = digest({k: v for k, v in a.items() if k not in _MUTABLE_FIELDS})
    if recomputed != a["artifact_digest"]:
        raise SystemExit(f"{pid}: artifact digest mismatch — refusing")


def load_candidates(model_short: str, paths: list[Path] | None, reg: Registry | None = None) -> list[dict]:
    reg = reg or Registry()
    paths = paths or sorted(reg.candidates.glob(f"r5-{model_short}-*.json"))
    arts = [json.loads(p.read_text()) for p in paths]
    for a in arts:
        verify_artifact(a)
    return arts


def risk_scores(art: dict, rows: list[dict]) -> dict[str, float]:
    router = RouterModel.from_dict(art["router"])
    src = art["feature_source"]
    if src == "prior":
        feats = [{f"category_{r['meta']['category']}": 1.0} for r in rows]
        feats = [{n: f.get(n, 0.0) for n in art["feature_names"]} for f in feats]
    elif src == "prior_class":
        # analysis-only ceiling: the offline group key, never a production feature
        feats = [{f"class_{r['group']}": 1.0} for r in rows]
        feats = [{n: f.get(n, 0.0) for n in art["feature_names"]} for f in feats]
    elif src == "features":
        feats = [r["features"] for r in rows]
    else:
        raise SystemExit(f"{art['policy_id']}: feature source {src!r} cannot be replayed on frozen arms")
    return dict(zip([r["scenario_id"] for r in rows], router.predict_proba(feats)))


def decisions(rows: list[dict], risk: dict[str, float] | None, tau: float | None,
              mode: str) -> dict[str, bool]:
    if mode == "local":
        return {r["scenario_id"]: False for r in rows}
    if mode == "strong":
        return {r["scenario_id"]: True for r in rows}
    if mode == "r4":
        return {r["scenario_id"]: bool(r["r4_escalate"]) for r in rows}
    if mode == "oracle":
        return {r["scenario_id"]: (not r["label_safe"]) and bool(r["strong_pass"]) for r in rows}
    if mode == "learned":
        return {r["scenario_id"]: bool(r["r4_escalate"]) or risk[r["scenario_id"]] >= tau for r in rows}
    raise ValueError(mode)


# ------------------------------------------------------------------ selection

def apply_rule(model_short: str, rule: dict, r4: dict, cands: list[dict],
               protocol: str) -> tuple[dict | None, list[dict]]:
    """Contract § 12 lexicographic rule with the § 12a numbers for one protocol.
    Returns (winner, verdicts)."""
    p = (rule["per_model"].get(model_short) or {}).get(protocol)
    if p is None:
        raise SystemExit(f"selection_rule.json has no {protocol} entry for {model_short} — commit the "
                         "§ 12a amendment for this model/protocol (scripts/r5_amend_rule.py) before DEV selection")
    K = max(3, math.ceil(0.25 * r4["routing_fn"]))
    verdicts = []
    for c in cands:
        m = c["system"]
        r1 = m["routing_fn"] <= r4["routing_fn"] - K
        # delta_util / e_max are null when TRAIN produced no eligible candidate: nothing
        # can pass R2 then, by construction.
        # A MISSING key is the primary reading (0.50, contract § 12); only an explicit
        # null — written by r5_amend_rule.py for the secondary protocol — means uncapped.
        cap = p["absolute_cap"] if "absolute_cap" in p else 0.50
        r2 = (p["delta_util"] is not None and p["e_max"] is not None
              and m["utilization"] <= r4["utilization"] + p["delta_util"]
              and (cap is None or m["utilization"] <= cap) and m["unnecessary"] <= p["e_max"])
        # Also recorded: the verdict under the skeleton's a-priori caps (§ 12), so a
        # secondary PASS is always shown beside what the capped rule would have said.
        r2_capped = (p["delta_util"] is not None and p["e_max"] is not None
                     and m["utilization"] <= r4["utilization"] + min(0.20, p["delta_util"])
                     and m["utilization"] <= 0.50 and m["unnecessary"] <= p["e_max"])
        r3 = m["all_pass"] > r4["all_pass"]
        verdicts.append({
            "policy_id": c["policy_id"], "eligible": c["eligible"], "protocol": protocol,
            "K": K, "delta_util": p["delta_util"], "e_max": p["e_max"],
            "R1_fn_reduction": r1, "R2_no_collapse": r2, "R2_under_skeleton_caps": r2_capped, "R3_quality": r3,
            "pass": bool(c["eligible"] and r1 and r2 and r3),
        })
    survivors = [c for c, v in zip(cands, verdicts) if v["pass"]]
    if not survivors:
        return None, verdicts
    def _cps(c):
        v = c["system"]["cost_per_success"]
        return float("inf") if v is None else v
    survivors.sort(key=lambda c: (c["system"]["escalated"], _cps(c), c["system"]["wall_p50_ms"]))
    return survivors[0], verdicts


def _assert_rule_matches_artifacts(rule: dict, model_short: str, arts: list[dict]) -> None:
    """The § 12a numbers are a computation over the committed candidate artifacts
    (`scripts/r5_amend_rule.py`); recompute them here so the file cannot drift."""
    from scripts.r5_amend_rule import derive
    for protocol in ("grouped", "stratified"):
        entry = (rule["per_model"].get(model_short) or {}).get(protocol)
        sub = [a for a in arts if a.get("protocol", "grouped") == protocol]
        if entry is None or not sub:
            continue
        got = derive({"candidates": sub}, protocol)
        if (got["delta_util"], got["e_max"]) != (entry["delta_util"], entry["e_max"]):
            raise SystemExit(f"selection_rule.json {model_short}/{protocol} (Δ_util {entry['delta_util']}, "
                             f"E_max {entry['e_max']}) does not match the candidate artifacts "
                             f"({got['delta_util']}, {got['e_max']}) — refusing")


# ------------------------------------------------------------------ state machine

def freeze_selection(reg: Registry, model: str, arts: list[dict], results: list[dict], verdicts: list[dict],
                     winner: dict | None, selected_protocol: str | None, dev_local_run: str,
                     dev_strong_run: str) -> dict:
    """Write the ONE selection record for `model` and, if there is a winner, its frozen
    artifact. Exactly once: a second call for the same model refuses (fail closed) —
    re-selection is not a normal experiment command. Losers are recorded in the
    selection record's verdicts, never frozen as artifacts, so at most one frozen policy
    per model can exist."""
    sel_path = reg.selection_file(model)
    if sel_path.exists():
        raise SystemExit(f"{sel_path} exists: DEV selection for {model} has already happened and is "
                         "not repeatable (contract § 12/§ 13)")
    existing = sorted(p.name for p in reg.frozen.glob(f"r5-{model}-*.json")) if reg.frozen.exists() else []
    if existing:
        raise SystemExit(f"frozen artifacts already exist for {model}: {existing} — refusing")
    winner_id = winner["policy_id"] if winner else None
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record = {
        "model": model, "winner": winner_id, "selected_protocol": selected_protocol,
        "winner_artifact_digest": winner["artifact_digest"] if winner else None,
        "dev_local_run": dev_local_run, "dev_strong_run": dev_strong_run,
        "candidates": [{"policy_id": a["policy_id"], "artifact_digest": a["artifact_digest"],
                        "protocol": a.get("protocol", "grouped"), "eligible": a["eligible"]} for a in arts],
        "verdicts": verdicts, "frozen_at": now, "code_commit": git_head(),
    }
    reg.frozen.mkdir(parents=True, exist_ok=True)
    if winner is not None:
        a = next(a for a in arts if a["policy_id"] == winner_id)
        verify_artifact(a)
        frozen = dict(a)
        frozen["local_model_short"] = model
        frozen["dev_selection"] = {
            "result": "PASS",
            "verdict": next(v for v in verdicts if v["policy_id"] == winner_id),
            "dev_local_run": dev_local_run, "dev_strong_run": dev_strong_run,
            "dev_system": next(r["system"] for r in results if r["policy_id"] == winner_id),
            "frozen_at": now, "code_commit": git_head(),
        }
        verify_artifact(frozen)      # digest excludes the mutable fields; must still verify
        reg.frozen_artifact(winner_id).write_text(canonical_json(frozen) + "\n")
    sel_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return record


def begin_test_unlock(reg: Registry, policy_id: str, model: str, local_run: str, strong_run: str,
                      *, dataset_meta: dict | None = None) -> dict:
    """Consume `model`'s single TEST look for `policy_id`. Every check fails closed:

      * a selection record for `model` exists and names `policy_id` as its winner;
      * the frozen artifact exists, verifies (schema, allowlist, digest), is eligible,
        carries dev_selection PASS on the contract's DEV runs, and its digest equals
        the one the selection record froze;
      * lineage: trained on the contract's TRAIN run for the model, on the committed
        TRAIN dataset digest (`dataset_meta`, default the registry's meta file);
      * the TEST runs are the contract's for the model;
      * no unlock exists for this policy AND none for this model.

    The unlock record is append-only and written before any TEST label is read. There
    is no function that removes an entry: the state is monotonic by construction.
    """
    sel_path = reg.selection_file(model)
    if not sel_path.exists():
        raise SystemExit(f"TEST is sealed: no DEV selection record for {model} at {sel_path}")
    sel = json.loads(sel_path.read_text())
    if sel.get("winner") != policy_id:
        raise SystemExit(f"TEST is sealed: the DEV selection record for {model} names "
                         f"{sel.get('winner')!r} as its winner, not {policy_id!r}")
    fpath = reg.frozen_artifact(policy_id)
    if not fpath.exists():
        raise SystemExit(f"no frozen artifact for {policy_id!r} at {fpath}")
    art = json.loads(fpath.read_text())
    verify_artifact(art)
    if art.get("policy_id") != policy_id:
        raise SystemExit(f"{fpath} holds {art.get('policy_id')!r}, not {policy_id!r}")
    if art["artifact_digest"] != sel.get("winner_artifact_digest"):
        raise SystemExit(f"{policy_id!r}: frozen artifact digest {art['artifact_digest'][:12]}… != the digest the "
                         f"selection record froze {str(sel.get('winner_artifact_digest'))[:12]}… — refusing")
    if not art.get("eligible"):
        raise SystemExit(f"{policy_id!r} is not an eligible policy — TEST stays sealed")
    ds = art.get("dev_selection") or {}
    if ds.get("result") != "PASS":
        raise SystemExit(f"{policy_id!r} did not PASS DEV selection — TEST stays sealed")
    if art.get("local_model_short") != model:
        raise SystemExit(f"{policy_id!r} is a {art.get('local_model_short')!r} policy, not {model!r}")
    if (ds.get("dev_local_run"), ds.get("dev_strong_run")) != DEFAULT_RUNS["dev"][model]:
        raise SystemExit(f"{policy_id!r} was selected on {ds.get('dev_local_run')}/{ds.get('dev_strong_run')}, "
                         f"not the contract's DEV runs {DEFAULT_RUNS['dev'][model]} — refusing")
    if art.get("train_run_id") != TRAIN_RUNS[model]:
        raise SystemExit(f"{policy_id!r} lineage: trained on {art.get('train_run_id')!r}, "
                         f"not the contract's {TRAIN_RUNS[model]!r} — refusing")
    if dataset_meta is None:
        mp = reg.dataset_meta(model)
        if not mp.exists():
            raise SystemExit(f"{policy_id!r} lineage: no committed TRAIN dataset meta at {mp}")
        dataset_meta = json.loads(mp.read_text())
    if art.get("train_dataset_digest") != dataset_meta.get("dataset_digest"):
        raise SystemExit(f"{policy_id!r} lineage: artifact trained on dataset {str(art.get('train_dataset_digest'))[:12]}…, "
                         f"committed TRAIN dataset is {str(dataset_meta.get('dataset_digest'))[:12]}… — refusing")
    if (local_run, strong_run) != DEFAULT_RUNS["test"][model]:
        raise SystemExit(f"TEST runs {(local_run, strong_run)} are not the contract's {DEFAULT_RUNS['test'][model]}")
    unlock = json.loads(reg.unlock_file.read_text()) if reg.unlock_file.exists() else {"unlocks": []}
    for u in unlock["unlocks"]:
        if u["policy_id"] == policy_id:
            raise SystemExit(f"{policy_id!r} has already had its one TEST replay — refusing")
        if u.get("model") == model:
            raise SystemExit(f"{model} has already had its one TEST replay ({u['policy_id']}) — refusing")
    unlock["unlocks"].append({
        "policy_id": policy_id, "model": model, "artifact_digest": art["artifact_digest"],
        "selection_record_digest": digest(sel),
        "local_run": local_run, "strong_run": strong_run,
        "unlocked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "code_commit": git_head(),
    })
    reg.unlock_file.parent.mkdir(parents=True, exist_ok=True)
    reg.unlock_file.write_text(json.dumps(unlock, indent=2) + "\n")
    return art


def preflight_test_runs(conn, local_run: str, strong_run: str, n_expected: int = 96) -> None:
    """Before the unlock is consumed: the TEST runs exist, are suite-comparable and
    complete. Reads counts only — no label."""
    from fis_platform.suite import require_comparable
    require_comparable(conn, [local_run, strong_run], against_corpus=True)
    with conn.cursor() as cur:
        for rid in (local_run, strong_run):
            cur.execute("SELECT count(*) FROM learning.case_scores WHERE run_id = %s", (rid,))
            n = cur.fetchone()[0]
            if n != n_expected:
                raise SystemExit(f"{rid} has {n} scored cases, expected {n_expected} — not unlocking")


# ------------------------------------------------------------------ telemetry

def persist_decisions(conn, policy_id: str, local_model: str, art: dict | None, rows: list[dict],
                      risk: dict[str, float] | None, tau: float | None, esc: dict[str, bool],
                      run_id: str, snapshot_digests: dict[str, str]) -> int:
    n = 0
    with conn.cursor() as cur:
        for r in rows:
            sid = r["scenario_id"]
            cur.execute(
                """INSERT INTO learning.routing_decisions
                     (routing_policy, local_model, router_artifact_digest, feature_schema_version,
                      feature_snapshot_digest, risk_score, threshold, decision, r4_decision,
                      production_observable_only, run_id, scenario_id, trace_id, replay)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,true,%s,%s,%s,true)
                   ON CONFLICT (routing_policy, run_id, scenario_id) DO NOTHING""",
                (policy_id, local_model, art["artifact_digest"] if art else None,
                 FEATURE_SCHEMA_VERSION if art else None, snapshot_digests[sid],
                 risk[sid] if risk else None, tau,
                 "escalate" if esc[sid] else "local",
                 "escalate" if r["r4_escalate"] else "local",
                 run_id, sid, r["trace_id"]),
            )
            n += cur.rowcount
    conn.commit()
    return n


# ------------------------------------------------------------------ main

def main() -> None:
    ap = argparse.ArgumentParser(description="R5 offline replay: DEV selection / TEST once")
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--model", choices=["qwen", "nemotron"], required=True)
    ap.add_argument("--local", help="local run id (default per split/model)")
    ap.add_argument("--strong", help="strong run id (default per split)")
    ap.add_argument("--candidates", nargs="*", help="artifact paths (default: registry candidates for the model)")
    ap.add_argument("--select", action="store_true", help="DEV: apply the pre-registered rule and freeze the winner")
    ap.add_argument("--unlock-test", metavar="POLICY_ID", help="TEST: the frozen policy to replay, once")
    ap.add_argument("--no-telemetry", action="store_true")
    ap.add_argument("--json-out")
    args = ap.parse_args()

    local_run, strong_run = DEFAULT_RUNS[args.split][args.model]
    local_run = args.local or local_run
    strong_run = args.strong or strong_run

    reg = Registry()
    if args.split == "test" and args.candidates:
        raise SystemExit("--candidates cannot be combined with a TEST replay: TEST replays the frozen winner only")
    if args.select and args.candidates:
        raise SystemExit("--candidates cannot be combined with --select: selection reads the registry candidates only")

    # ---- TEST gate: the unlock is consumed BEFORE any TEST label is read ---------
    frozen_only: dict | None = None
    if args.split == "test":
        if not args.unlock_test:
            raise SystemExit("TEST is sealed: pass --unlock-test <policy_id> for the DEV-selected frozen policy")
        with psycopg.connect(DSN) as conn:
            preflight_test_runs(conn, local_run, strong_run)
        frozen_only = begin_test_unlock(reg, args.unlock_test, args.model, local_run, strong_run)
        print(f"TEST UNLOCKED for {args.unlock_test} (recorded in {reg.unlock_file}); this is {args.model}'s only replay.\n")

    with psycopg.connect(DSN) as conn:
        rows, meta = build_dataset(conn, local_run, strong_run, allow_test=(args.split == "test"))
        local_rows = load_run(conn, local_run)
        strong_rows = load_run(conn, strong_run)
        snap_digests = {r["scenario_id"]: r["snapshot_digest"] for r in rows}
        n = len(rows)
        local_model = meta["local_models"][0] if meta["local_models"] else args.model

        print(f"R5 replay — split={args.split} model={args.model} local={local_run} strong={strong_run} "
              f"n={n} schema v{FEATURE_SCHEMA_VERSION} dataset digest {meta['dataset_digest'][:16]}… "
              f"echo-checked {meta['echo_checked']}")

        # ---- baselines --------------------------------------------------------
        deferred_telemetry: list = []      # written after the report so a DB hiccup cannot eat the one TEST look
        base = {}
        for mode in ("local", "r4", "strong", "oracle"):
            esc = decisions(rows, None, None, mode)
            base[mode] = evaluate_policy(rows, strong_rows, local_rows, esc)
            base[mode]["silent"] = silent_family(rows, esc)
            if not args.no_telemetry and mode == "r4":
                deferred_telemetry.append(("r4-verifier", None, None, None, esc))
        r4 = base["r4"]

        # ---- candidates -------------------------------------------------------
        if frozen_only is not None:
            arts = [frozen_only]
        else:
            arts = load_candidates(args.model, [Path(p) for p in args.candidates] if args.candidates else None, reg)
            # TRAIN-only comparators (answer bodies exist for TRAIN acquisitions only) cannot
            # be replayed on the frozen DEV/TEST arms; they are reported from TRAIN alone.
            skipped = [a["policy_id"] for a in arts if a["feature_source"] not in ("features", "prior", "prior_class")]
            arts = [a for a in arts if a["feature_source"] in ("features", "prior", "prior_class")]
            if skipped:
                print(f"(not replayable on frozen arms — TRAIN-only comparators skipped: {skipped})")
        results = []
        for a in arts:
            risk = risk_scores(a, rows)
            tau = a["threshold"]
            esc = decisions(rows, risk, tau, "learned")
            sysm = evaluate_policy(rows, strong_rows, local_rows, esc)
            clf = classifier_metrics(rows, risk, tau)
            sil = silent_family(rows, esc)
            sweep = []
            # No threshold sweep on TEST: a Pareto over the grid would be a selection
            # signal from the sealed split. TEST is τ* only.
            for t in (a["threshold_grid"] if args.split != "test" else []):
                e_t = decisions(rows, risk, t, "learned")
                m_t = evaluate_policy(rows, strong_rows, local_rows, e_t)
                sweep.append({"threshold": t, "utilization": m_t["utilization"], "escalated": m_t["escalated"],
                              "all_pass": m_t["all_pass"], "routing_fn": m_t["routing_fn"],
                              "unnecessary": m_t["unnecessary"]})
            if not args.no_telemetry:
                deferred_telemetry.append((f"{a['policy_id']}@{a['artifact_digest'][:12]}", a, risk, tau, esc))
            results.append({"policy_id": a["policy_id"], "candidate": a["candidate"], "family": a["family"],
                            "protocol": a.get("protocol", "grouped"),
                            "eligible": a["eligible"], "eligible_kind": a["eligible_kind"],
                            "threshold": tau, "artifact_digest": a["artifact_digest"],
                            "system": sysm, "classifier": clf, "silent": sil, "sweep": sweep,
                            "risk": risk})

    # ---- print ---------------------------------------------------------------
    def line(name, m, extra=""):
        cps = "n/a" if m["cost_per_success"] is None else f"${m['cost_per_success']:.4f}"
        rr = "n/a" if m["rescue_rate"] is None else f"{m['rescue_rate']:.2f}"
        print(f"  {name:<34} all-pass {m['all_pass']:>3}/{n} ({100*m['all_pass_rate']:5.1f}%)  "
              f"esc {m['escalated']:>3} ({100*m['utilization']:5.1f}%)  FN {m['routing_fn']:>3}  "
              f"unnec {m['unnecessary']:>2}  rescue {rr:>4}  $/att {m['cost_per_attempt']:.4f}  "
              f"$/succ {cps:>8}  p50 {m['wall_p50_ms']/1000:5.1f}s p95 {m['wall_p95_ms']/1000:5.1f}s{extra}")

    print("\nSYSTEM (frozen replay)")
    line("local-only", base["local"])
    line("R4 verifier (incumbent)", base["r4"])
    for r in results:
        tag = "ELIGIBLE" if r["eligible"] else ("inelig(gate)" if r["eligible_kind"] else "exploratory")
        line(f"{r['candidate']} τ={r['threshold']} [{tag}]", r["system"])
    line("always-escalate (strong, cascade)", base["strong"])
    line("post-answer oracle (min-useful)", base["oracle"])
    print(f"  gap to oracle: R4 {base['r4']['all_pass'] - base['oracle']['all_pass']:+d}"
          + "".join(f"; {r['candidate']} {r['system']['all_pass'] - base['oracle']['all_pass']:+d}" for r in results))

    print("\nCLASSIFIER (R4-accepted subset)")
    for r in results:
        c = r["classifier"]
        auc = "n/a" if c["roc_auc"] is None else f"{c['roc_auc']:.3f}"
        ap_ = "n/a" if c["pr_auc"] is None else f"{c['pr_auc']:.3f}"
        rec = "n/a" if c["unsafe_recall"] is None else f"{c['unsafe_recall']:.2f}"
        pre = "n/a" if c["unsafe_precision"] is None else f"{c['unsafe_precision']:.2f}"
        print(f"  {r['candidate']:<12} n={c['n_accepted']} unsafe={c['unsafe_in_accepted']} base={c['base_rate']:.2f}  "
              f"AUC {auc}  PR-AUC {ap_}  Brier {c['brier']:.3f}  recall {rec} precision {pre}  "
              f"tp {c['tp']} fp {c['fp']} fn {c['fn']} tn {c['tn']}")

    print("\nSILENT FAMILY (R4 verifier-clean routing FNs)")
    s0 = base["r4"]["silent"]
    print(f"  R4 FN {s0['r4_fn']}: by kind {s0['remaining_by_kind']}")
    for r in results:
        s = r["silent"]
        print(f"  {r['candidate']:<12} caught {s['caught']} {s['caught_by_kind']}  remaining {s['remaining']} "
              f"{s['remaining_by_kind']}  new unnecessary {s['new_unnecessary']} {s['new_unnecessary_ids']}")
        print(f"               caught ids {s['caught_ids']}")

    print("\nPARETO (threshold sweep; utilization / all-pass / routing FN / unnecessary)")
    print(f"  local-only  {100*base['local']['utilization']:5.1f}%  {base['local']['all_pass']:>3}  {base['local']['routing_fn']:>3}  {base['local']['unnecessary']:>2}")
    print(f"  R4          {100*base['r4']['utilization']:5.1f}%  {base['r4']['all_pass']:>3}  {base['r4']['routing_fn']:>3}  {base['r4']['unnecessary']:>2}")
    for r in results:
        print(f"  {r['candidate']}:")
        for s in r["sweep"]:
            mark = "  <- τ*" if s["threshold"] == r["threshold"] else ""
            print(f"     τ={s['threshold']:.2f}  {100*s['utilization']:5.1f}%  {s['all_pass']:>3}  {s['routing_fn']:>3}  {s['unnecessary']:>2}{mark}")
    print(f"  always-esc  {100*base['strong']['utilization']:5.1f}%  {base['strong']['all_pass']:>3}  {base['strong']['routing_fn']:>3}  {base['strong']['unnecessary']:>2}   (strong for every case, cascade reading: weak wall/tokens included)")
    print(f"  oracle      {100*base['oracle']['utilization']:5.1f}%  {base['oracle']['all_pass']:>3}  {base['oracle']['routing_fn']:>3}  {base['oracle']['unnecessary']:>2}   (min-useful: escalate only what the frontier rescues)")

    # ---- DEV selection -------------------------------------------------------
    selection = None
    if args.split == "dev" and args.select:
        if not reg.rule_file.exists():
            raise SystemExit(f"no pre-registered rule at {reg.rule_file} — commit the § 12a amendment first")
        if reg.selection_file(args.model).exists():
            raise SystemExit(f"DEV selection for {args.model} already recorded at {reg.selection_file(args.model)} — "
                             "not repeatable")
        rule = json.loads(reg.rule_file.read_text())
        _assert_rule_matches_artifacts(rule, args.model, arts)
        # PRIMARY protocol (grouped CV) first; the SECONDARY (stratified, § 12a) is
        # consulted only if the primary selects nothing.
        prim = [r for r in results if r["protocol"] == "grouped"]
        sec = [r for r in results if r["protocol"] == "stratified"]
        winner, verdicts = apply_rule(args.model, rule, r4, prim, "grouped")
        selected_protocol = "grouped" if winner else None
        if winner is None and sec:
            w2, v2 = apply_rule(args.model, rule, r4, sec, "stratified")
            verdicts += v2
            if w2 is not None:
                winner, selected_protocol = w2, "stratified"
        print("\nSELECTION (pre-registered rule, contract § 12/12a; primary protocol first)")
        for v in verdicts:
            print(f"  {v['policy_id']:<40} [{v['protocol']}] eligible={v['eligible']}  K={v['K']} Δutil={v['delta_util']} Emax={v['e_max']}  "
                  f"R1 {v['R1_fn_reduction']}  R2 {v['R2_no_collapse']} (capped {v['R2_under_skeleton_caps']})  R3 {v['R3_quality']}  → {'PASS' if v['pass'] else 'FAIL'}")
        winner_art = next((a for a in arts if winner and a["policy_id"] == winner["policy_id"]), None)
        record = freeze_selection(reg, args.model, arts, results, verdicts, winner_art, selected_protocol,
                                  local_run, strong_run)
        selection = {"rule": rule["per_model"][args.model], "verdicts": verdicts,
                     "winner": record["winner"], "selected_protocol": selected_protocol}
        print(f"  winner: {selection['winner'] or 'NONE — R4 stays incumbent; TEST not opened for any learned policy'}"
              + (f"  (protocol {selected_protocol})" if selected_protocol else ""))
        print(f"  selection record {reg.selection_file(args.model)}"
              + (f"; frozen artifact {reg.frozen_artifact(record['winner'])}" if record["winner"] else ""))

    # ---- TEST reading (contract § 14, pre-registered; a reading, not a selection) ----
    test_reading = None
    if args.split == "test" and results:
        rule = json.loads(reg.rule_file.read_text())
        proto = arts[0].get("protocol", "grouped")
        p_ = rule["per_model"][args.model][proto]
        m = results[0]["system"]
        k_test = max(3, math.ceil(0.25 * r4["routing_fn"]))
        cap = p_["absolute_cap"] if "absolute_cap" in p_ else 0.50
        util_ok = (m["utilization"] <= r4["utilization"] + p_["delta_util"]) and (cap is None or m["utilization"] <= cap)
        test_reading = {
            "policy_id": results[0]["policy_id"], "protocol": proto, "K_test": k_test,
            "fn_r4": r4["routing_fn"], "fn_policy": m["routing_fn"],
            "R1_fn": m["routing_fn"] <= r4["routing_fn"] - k_test,
            "unnecessary": m["unnecessary"], "e_max_x2": 2 * p_["e_max"],
            "R2_unnecessary": m["unnecessary"] <= 2 * p_["e_max"],
            "utilization": m["utilization"], "util_bound": r4["utilization"] + p_["delta_util"], "absolute_cap": cap,
            "R2_utilization": util_ok,
        }
        test_reading["confirmed"] = bool(test_reading["R1_fn"] and test_reading["R2_unnecessary"] and util_ok)
        print("\nTEST READING (contract § 14, pre-registered)")
        print(f"  K_test={k_test}  FN {m['routing_fn']} vs R4 {r4['routing_fn']} → R1 {test_reading['R1_fn']};  "
              f"unnecessary {m['unnecessary']} ≤ {2 * p_['e_max']} → {test_reading['R2_unnecessary']};  "
              f"utilization {m['utilization']:.3f} ≤ {r4['utilization'] + p_['delta_util']:.3f}"
              + (f" and ≤ {cap}" if cap is not None else "") + f" → {util_ok}")
        print(f"  => {'CONFIRMED on TEST' if test_reading['confirmed'] else 'NOT CONFIRMED on TEST'}")

    out = Path(args.json_out) if args.json_out else ROOT / "evals" / "reports" / f"r5-replay-{args.split}-{args.model}.json"
    out.write_text(json.dumps({
        "split": args.split, "model": args.model, "local_run": local_run, "strong_run": strong_run, "n": n,
        "dataset_digest": meta["dataset_digest"], "baselines": base,
        "candidates": [{k: v for k, v in r.items() if k != "risk"} | {"risk": r["risk"]} for r in results],
        "selection": selection, "test_reading": test_reading, "code_commit": git_head(),
    }, indent=1, default=str) + "\n")
    print(f"\nwritten: {out}")

    if deferred_telemetry:
        try:
            with psycopg.connect(DSN) as conn:
                for policy, a, risk, tau, esc in deferred_telemetry:
                    persist_decisions(conn, policy, local_model, a, rows, risk, tau, esc, local_run, snap_digests)
            print(f"telemetry: {len(deferred_telemetry)} policies × {n} decisions → learning.routing_decisions")
        except Exception as exc:  # noqa: BLE001 — telemetry must never cost the replay its numbers
            print(f"telemetry NOT persisted ({exc.__class__.__name__}: {exc}); the report above stands")


if __name__ == "__main__":
    main()
