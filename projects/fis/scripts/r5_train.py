"""R5 — TRAIN-only development of the learned routers (contract § 9–10).

Input: a TRAIN dataset written by `scripts/r5_dataset.py` (one local model). Refuses
any row whose split is not `train`. Everything here is decided on TRAIN alone:

  * the training subset is the R4-ACCEPTED rows (policy form `R4 ∨ risk ≥ τ`: the
    router only ever sees the cases the deterministic gate would return locally);
  * hyperparameters (λ for logistic, depth for the tree) by leave-one-class-out
    out-of-fold log-loss (ties → the simpler model);
  * the operating threshold τ* per candidate by out-of-fold utility
    U(τ) = catches − unnecessary over the pre-registered grid (ties → larger τ);
  * the TRAIN eligibility gate: OOF ROC-AUC ≥ 0.60 and OOF PR-AUC ≥ base rate + 0.10.

Outputs, per candidate: an artifact JSON under `learning/registry/r5/candidates/`
(model, standardizer, feature order, feature_schema_version, τ*, CV numbers, dataset
digest, code commit, eligibility) with a stable `artifact_digest`, plus a TRAIN report.
Exploratory comparators (`lr_answer`, `prior_category`, `answer_structure`,
`lr_unified`) are trained and reported the same way but marked `eligible: false`
regardless of their numbers — they exist to explain, not to be selected.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.routing.features import (  # noqa: E402
    FEATURE_FAMILIES, FEATURE_ORDER, FEATURE_SCHEMA_VERSION,
)
from fis_platform.routing.learn import (  # noqa: E402
    DecisionTree, LogisticRegression, RouterModel, Standardizer, average_precision, brier,
    canonical_json, digest, grouped_folds, log_loss, roc_auc, stratified_folds,
)
from fis_platform.suite import git_head  # noqa: E402
from scripts.r5_dataset import read_dataset  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_DIR = ROOT / "learning" / "registry" / "r5" / "candidates"

THRESHOLD_GRID = [round(0.30 + 0.05 * i, 2) for i in range(11)]      # 0.30 … 0.80
LR_LAMBDAS = [0.1, 1.0, 10.0, 100.0]
TREE_DEPTHS = [2, 3]
TREE_MIN_LEAF = 8
GATE_AUC = 0.60
GATE_AP_MARGIN = 0.10

ALL = list(FEATURE_ORDER)
CORE = list(FEATURE_FAMILIES["A"]) + list(FEATURE_FAMILIES["B"]) + list(FEATURE_FAMILIES["C"])
ANSWER = list(FEATURE_FAMILIES["D"])

# Eligible candidates: contract § 9. Exploratory ones are appended by flags.
CANDIDATES = {
    "lr_full": ("logistic", ALL),
    "lr_core": ("logistic", CORE),
    "tree": ("tree", ALL),
}
# Behaviour-only ablation: family A minus the bundle-size channel (input_tokens and its
# ratio) plus the answer echo, no family C — how much of the signal survives without the
# case-shape constants that identify the template (audit finding, § 12a).
BEHAVIOR = [f for f in FEATURE_FAMILIES["A"] if f not in ("input_tokens", "output_per_input")] + ANSWER
EXPLORATORY = {
    "lr_answer": ("logistic", ANSWER),
    "lr_behavior": ("logistic", BEHAVIOR),
}


# ------------------------------------------------------------------ helpers

def _matrix(rows: list[dict], names: list[str], source: str = "features") -> list[list[float]]:
    return [[float(r[source][n]) for n in names] for r in rows]


def _fit(family: str, hp: float | int, X: list[list[float]], y: list[int],
         names: list[str]) -> RouterModel:
    if family == "logistic":
        st = Standardizer().fit(X)
        m = LogisticRegression(l2=float(hp)).fit(st.transform(X), y)
        return RouterModel(family="logistic", feature_names=names, standardizer=st, model=m)
    if family == "tree":
        m = DecisionTree(max_depth=int(hp), min_samples_leaf=TREE_MIN_LEAF).fit(X, y)
        return RouterModel(family="tree", feature_names=names, standardizer=None, model=m)
    raise ValueError(family)


def _oof(family: str, hp, rows: list[dict], names: list[str], folds, source="features"):
    """Out-of-fold probabilities under the given folds; index-aligned with rows."""
    p = [None] * len(rows)
    for tr, te in folds:
        Xtr = _matrix([rows[i] for i in tr], names, source)
        ytr = [int(rows[i]["label_unsafe"]) for i in tr]
        if len(set(ytr)) < 2:
            # a fold whose training side has one class: predict the base rate
            base = sum(ytr) / len(ytr) if ytr else 0.5
            for i in te:
                p[i] = base
            continue
        m = _fit(family, hp, Xtr, ytr, names)
        Xte = [{n: float(rows[i][source][n]) for n in names} for i in te]
        for i, q in zip(te, m.predict_proba(Xte)):
            p[i] = q
    return p


def _metrics(y: list[int], p: list[float]) -> dict:
    return {
        "roc_auc": roc_auc(y, p),
        "pr_auc": average_precision(y, p),
        "brier": brier(y, p),
        "log_loss": log_loss(y, p),
        "base_rate": sum(y) / len(y) if y else None,
        "n": len(y),
    }


def _utility_curve(y: list[int], p: list[float], n_all: int) -> list[dict]:
    """Per grid threshold on the R4-accepted subset: catches (unsafe escalated),
    unnecessary (safe escalated), utility, and rates the contract's amendment uses."""
    out = []
    n_safe = sum(1 for v in y if v == 0)
    for t in THRESHOLD_GRID:
        esc = [i for i, q in enumerate(p) if q >= t]
        catches = sum(1 for i in esc if y[i] == 1)
        unnecessary = len(esc) - catches
        out.append({
            "threshold": t, "escalated": len(esc), "catches": catches,
            "unnecessary": unnecessary, "utility": catches - unnecessary,
            "escalation_rate_all": len(esc) / n_all,           # over ALL train cases
            "unnecessary_rate_all": unnecessary / n_all,
            "unnecessary_rate_safe": (unnecessary / n_safe) if n_safe else None,
            "catch_rate": (catches / sum(y)) if sum(y) else None,
            "precision": (catches / len(esc)) if esc else None,
        })
    return out


def _pick_threshold(curve: list[dict]) -> float:
    best = max(c["utility"] for c in curve)
    return max(c["threshold"] for c in curve if c["utility"] == best)   # ties → larger τ


def _sign_stability(family: str, hp, rows, names, folds) -> dict | None:
    """Logistic: fraction of folds where each coefficient keeps the full-fit sign.
    Tree: which feature the root split uses per fold."""
    if family == "logistic":
        full = _fit(family, hp, _matrix(rows, names), [int(r["label_unsafe"]) for r in rows], names)
        ref = full.coefficients()
        agree = Counter()
        n_folds = 0
        for tr, _ in folds:
            ytr = [int(rows[i]["label_unsafe"]) for i in tr]
            if len(set(ytr)) < 2:
                continue
            m = _fit(family, hp, _matrix([rows[i] for i in tr], names), ytr, names)
            n_folds += 1
            for k, v in m.coefficients().items():
                if k == "__intercept__" or abs(ref.get(k, 0.0)) < 1e-9:
                    continue
                if math.copysign(1, v) == math.copysign(1, ref[k]) and abs(v) > 1e-9:
                    agree[k] += 1
        coefs = {k: v for k, v in ref.items() if k != "__intercept__" and abs(v) > 1e-9}
        top = sorted(coefs.items(), key=lambda kv: -abs(kv[1]))[:12]
        return {"n_folds": n_folds,
                "top_coefficients": [{"feature": k, "coef": round(v, 4),
                                      "sign_agreement": (agree[k] / n_folds) if n_folds else None}
                                     for k, v in top]}
    if family == "tree":
        roots = Counter()
        for tr, _ in folds:
            ytr = [int(rows[i]["label_unsafe"]) for i in tr]
            if len(set(ytr)) < 2:
                continue
            m = _fit(family, hp, _matrix([rows[i] for i in tr], names), ytr, names)
            d = m.model.to_dict()
            node = d.get("tree", d)
            roots[names[node["feature"]] if "feature" in node else "(leaf)"] += 1
        return {"root_split_by_fold": dict(roots)}
    return None


def train_candidate(cid: str, family: str, names: list[str], rows: list[dict],
                    *, source: str = "features", eligible_kind: bool,
                    dataset_meta: dict, hp_grid=None, protocol: str = "grouped") -> dict:
    """`protocol` names the CV that drives hp, τ* and the gate: "grouped" (contract § 8/
    § 10, leave-one-class-out — the PRIMARY protocol) or "stratified" (seed-stratified
    4-fold, deployment-matched — the SECONDARY protocol registered in § 12a after TRAIN
    showed the labels are class-clustered). The other CV is always reported beside it."""
    accepted = [r for r in rows if not r["r4_escalate"]]
    y = [int(r["label_unsafe"]) for r in accepted]
    groups = [r["group"] for r in accepted]
    grouped = grouped_folds(groups)
    strat = stratified_folds(y, 4)
    folds, other = (grouped, strat) if protocol == "grouped" else (strat, grouped)
    n_all = len(rows)
    if hp_grid is None:
        hp_grid = LR_LAMBDAS if family == "logistic" else TREE_DEPTHS

    # 1. hyperparameter by OOF log-loss under the protocol's CV (ties → simpler)
    trials = []
    for hp in hp_grid:
        p = _oof(family, hp, accepted, names, folds, source)
        m = _metrics(y, p)
        trials.append({"hp": hp, **m})
    def _simplicity(t):
        return (-t["hp"]) if family == "logistic" else t["hp"]
    best = min(trials, key=lambda t: (round(t["log_loss"], 6), _simplicity(t)))
    hp = best["hp"]

    # 2. OOF at the chosen hp: metrics, utility curve, τ*
    p = _oof(family, hp, accepted, names, folds, source)
    m_primary = _metrics(y, p)
    curve = _utility_curve(y, p, n_all)
    tau = _pick_threshold(curve)
    at_tau = next(c for c in curve if c["threshold"] == tau)
    p_other = _oof(family, hp, accepted, names, other, source)
    m_other = _metrics(y, p_other)
    m_grouped, m_strat = (m_primary, m_other) if protocol == "grouped" else (m_other, m_primary)

    # 3. eligibility gate (contract § 10) under the protocol's CV
    gate = (m_primary["roc_auc"] is not None and m_primary["roc_auc"] >= GATE_AUC
            and m_primary["pr_auc"] is not None
            and m_primary["pr_auc"] >= m_primary["base_rate"] + GATE_AP_MARGIN)

    # 4. final fit on all accepted TRAIN rows
    final = _fit(family, hp, _matrix(accepted, names, source), y, names)
    stability = _sign_stability(family, hp, accepted, names, folds) if source == "features" else None

    suffix = "" if protocol == "grouped" else f"-{protocol}"
    art = {
        "policy_id": f"r5-{dataset_meta['local_model_short']}-{cid}{suffix}-v1",
        "candidate": cid,
        "protocol": protocol,
        "family": family,
        "eligible_kind": eligible_kind,             # contract § 9 eligible list
        "eligible": bool(eligible_kind and gate),   # kind AND TRAIN gate
        "train_gate": {"auc_min": GATE_AUC, "ap_margin": GATE_AP_MARGIN, "passed": bool(gate)},
        "local_model": dataset_meta["local_model"],
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_source": source,
        "feature_names": names,
        "hyperparameter": hp,
        "hyperparameter_grid": hp_grid,
        "threshold": tau,
        "threshold_grid": THRESHOLD_GRID,
        "router": final.to_dict(),
        "train_run_id": dataset_meta["run_id"],
        "train_dataset_digest": dataset_meta["dataset_digest"],
        "train_n_all": n_all,
        "train_n_accepted": len(accepted),
        "train_n_accepted_unsafe": sum(y),
        "code_commit": git_head(),
        "cv": {
            "method": ("leave-one-class-out (grouped by scenario class)" if protocol == "grouped"
                       else "seed-stratified 4-fold (deployment-matched; SECONDARY protocol)"),
            "hp_trials": trials,
            "grouped_oof": m_grouped,
            "stratified4_oof": m_strat,
            "primary_oof": m_primary,
            "utility_curve": curve,
            "at_threshold": at_tau,
            "stability": stability,
        },
        "dev_selection": None,
    }
    art["artifact_digest"] = digest({k: v for k, v in art.items()
                                     if k not in ("artifact_digest", "dev_selection")})
    return art


def _print_candidate(a: dict) -> None:
    g = a["cv"]["grouped_oof"]; s = a["cv"]["stratified4_oof"]; t = a["cv"]["at_threshold"]
    flag = "ELIGIBLE" if a["eligible"] else ("ineligible(gate)" if a["eligible_kind"] else "exploratory")
    print(f"\n== {a['policy_id']}  [{a['family']}, hp={a['hyperparameter']}, {len(a['feature_names'])} features, "
          f"protocol={a['protocol']}]  {flag}")
    print(f"   accepted subset n={a['train_n_accepted']} unsafe={a['train_n_accepted_unsafe']} "
          f"(base rate {g['base_rate']:.3f})")
    pg = " <- drives hp/τ/gate" if a["protocol"] == "grouped" else ""
    ps = " <- drives hp/τ/gate" if a["protocol"] == "stratified" else ""
    print(f"   grouped OOF   AUC {g['roc_auc']:.3f}  PR-AUC {g['pr_auc']:.3f}  Brier {g['brier']:.3f}  logloss {g['log_loss']:.3f}{pg}")
    print(f"   strat-4 OOF   AUC {s['roc_auc']:.3f}  PR-AUC {s['pr_auc']:.3f}  Brier {s['brier']:.3f}  logloss {s['log_loss']:.3f}{ps}")
    print("   hp trials: " + ", ".join(f"{x['hp']}:{x['log_loss']:.3f}/{x['roc_auc']:.3f}" for x in a['cv']['hp_trials']))
    print(f"   τ*={a['threshold']}  OOF at τ*: escalated {t['escalated']} catches {t['catches']} unnecessary {t['unnecessary']} "
          f"U={t['utility']}  esc-rate(all) {t['escalation_rate_all']:.3f}  unnecessary-rate(all) {t['unnecessary_rate_all']:.3f}  "
          f"catch-rate {t['catch_rate']}  precision {t['precision']}")
    st = a["cv"]["stability"]
    if st and "top_coefficients" in st:
        print("   coefficients (standardized) / sign agreement across folds:")
        for c in st["top_coefficients"]:
            print(f"      {c['feature']:<40} {c['coef']:+.3f}   {c['sign_agreement']}")
    elif st:
        print(f"   root split by fold: {st['root_split_by_fold']}")
    print(f"   artifact digest {a['artifact_digest'][:16]}…")


def main() -> None:
    ap = argparse.ArgumentParser(description="R5 TRAIN-only router development")
    ap.add_argument("--dataset", required=True, help="learning/datasets/r5/<train-run>.jsonl")
    ap.add_argument("--out-dir", default=str(CANDIDATE_DIR))
    ap.add_argument("--exploratory", action="store_true",
                    help="also train the exploratory comparators (never eligible)")
    ap.add_argument("--cv", choices=["grouped", "stratified"], default="grouped",
                    help="which CV drives hp/τ/gate: grouped = PRIMARY (contract § 8/10); "
                         "stratified = SECONDARY (§ 12a); the other is always reported beside it")
    args = ap.parse_args()

    ds = Path(args.dataset)
    rows = read_dataset(ds)
    meta = json.loads(ds.with_suffix(".meta.json").read_text())
    if any(r["split"] != "train" for r in rows):
        raise SystemExit("r5_train.py trains on TRAIN only; the dataset has non-train rows")
    models = {r["local_model"] for r in rows}
    if len(models) != 1:
        raise SystemExit(f"one local model per dataset; got {models}")
    (model,) = models
    short = "qwen" if "qwen" in model else ("nemotron" if "nemotron" in model else model)
    dmeta = {"run_id": meta["run_id"], "dataset_digest": meta["dataset_digest"],
             "local_model": model, "local_model_short": short}

    print(f"R5 TRAIN development — {meta['run_id']}  model={model}  n={len(rows)}  "
          f"safe={meta['n_safe']}  r4-accepted={meta['n_r4_accepted']}  silent={meta['n_silent']}  "
          f"dataset digest {meta['dataset_digest'][:16]}…  schema v{FEATURE_SCHEMA_VERSION}")
    print(f"grid τ={THRESHOLD_GRID}  λ={LR_LAMBDAS}  depth={TREE_DEPTHS} min_leaf={TREE_MIN_LEAF}  "
          f"gate AUC≥{GATE_AUC} & AP≥base+{GATE_AP_MARGIN}")

    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    arts = []
    P = args.cv
    print(f"protocol driving hp/τ/gate: {P}" + ("  (PRIMARY, contract § 8/10)" if P == "grouped" else "  (SECONDARY, § 12a)"))
    for cid, (fam, names) in CANDIDATES.items():
        a = train_candidate(cid, fam, names, rows, eligible_kind=True, dataset_meta=dmeta, protocol=P)
        arts.append(a); _print_candidate(a)
    if args.exploratory:
        for cid, (fam, names) in EXPLORATORY.items():
            a = train_candidate(cid, fam, names, rows, eligible_kind=False, dataset_meta=dmeta, protocol=P)
            arts.append(a); _print_candidate(a)
        # class-prior comparator: case category one-hot (analysis-only column; production-
        # visible but a class identifier for half the categories — never eligible)
        cats = sorted({r["meta"]["category"] for r in rows})
        for r in rows:
            r["prior"] = {f"category_{c}": float(r["meta"]["category"] == c) for c in cats}
        a = train_candidate("prior_category", "logistic", [f"category_{c}" for c in cats], rows,
                            source="prior", eligible_kind=False, dataset_meta=dmeta, protocol=P)
        arts.append(a); _print_candidate(a)
        # class-identity ceiling: P(unsafe | scenario class) — the group key itself, which
        # exists offline only. NOT a router (it reads the answer key's class); it is the
        # ceiling of any router that works purely as a task-difficulty prior.
        classes = sorted({r["group"] for r in rows})
        for r in rows:
            r["prior_class"] = {f"class_{c}": float(r["group"] == c) for c in classes}
        a = train_candidate("prior_class_ceiling", "logistic", [f"class_{c}" for c in classes], rows,
                            source="prior_class", eligible_kind=False, dataset_meta=dmeta, protocol=P)
        arts.append(a); _print_candidate(a)
        # answer-structure comparator over the persisted TRAIN answer bodies (+ snapshot)
        if all(r["answer_structure"] for r in rows if not r["r4_escalate"]):
            keys = sorted(next(r["answer_structure"] for r in rows if r["answer_structure"]))
            for r in rows:
                r["structure"] = {**{k: r["features"][k] for k in ALL},
                                  **{f"as_{k}": (r["answer_structure"] or {}).get(k, 0.0) for k in keys}}
            a = train_candidate("answer_structure", "logistic", ALL + [f"as_{k}" for k in keys], rows,
                                source="structure", eligible_kind=False, dataset_meta=dmeta, protocol=P)
            arts.append(a); _print_candidate(a)
            a = train_candidate("answer_structure_only", "logistic", [f"as_{k}" for k in keys], rows,
                                source="structure", eligible_kind=False, dataset_meta=dmeta, protocol=P)
            arts.append(a); _print_candidate(a)

    for a in arts:
        (out_dir / f"{a['policy_id']}.json").write_text(canonical_json(a) + "\n")
    report = {"train_run_id": meta["run_id"], "local_model": model, "dataset_digest": meta["dataset_digest"],
              "protocol": P, "code_commit": git_head(),
              "candidates": [{k: a[k] for k in ("policy_id", "candidate", "protocol", "family", "eligible_kind",
                                                 "eligible", "hyperparameter", "threshold",
                                                 "artifact_digest", "cv")} for a in arts]}
    rep_name = f"train_report_{short}.json" if P == "grouped" else f"train_report_{short}_{P}.json"
    (out_dir.parent / rep_name).write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(f"\nwritten: {len(arts)} artifacts under {out_dir}; report {rep_name}")


if __name__ == "__main__":
    main()
