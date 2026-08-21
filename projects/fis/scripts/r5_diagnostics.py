"""R5 — TRAIN diagnostics promised in contract § 12a (reported, never used for selection).

  * per-fold leave-one-class-out AUC of each eligible candidate, over the folds whose
    held-out class carries both labels (the pooled LOGO AUC is dominated by base-rate
    shift when labels are class-clustered, so it is not evidence about transfer);
  * mean predicted risk on held-out one-label classes (does "generic hardness" transfer?);
  * within-class label structure of the R4-accepted subset;
  * within-class pooled AUC per feature (pairs drawn inside a class only).

Reads a TRAIN dataset only; writes nothing to the registry.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.routing.features import FEATURE_FAMILIES, FEATURE_ORDER  # noqa: E402
from fis_platform.routing.learn import grouped_folds, roc_auc  # noqa: E402
from scripts.r5_dataset import read_dataset  # noqa: E402
from scripts.r5_train import _oof  # noqa: E402

ALL = list(FEATURE_ORDER)
CORE = list(FEATURE_FAMILIES["A"]) + list(FEATURE_FAMILIES["B"]) + list(FEATURE_FAMILIES["C"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--json-out")
    args = ap.parse_args()
    rows = read_dataset(Path(args.dataset))
    if any(r["split"] != "train" for r in rows):
        raise SystemExit("diagnostics are TRAIN-only")
    acc = [r for r in rows if not r["r4_escalate"]]
    y = [int(r["label_unsafe"]) for r in acc]
    groups = [r["group"] for r in acc]
    folds = grouped_folds(groups)
    out: dict = {"n_accepted": len(acc), "n_unsafe": sum(y)}

    print(f"R5 diagnostics — {Path(args.dataset).name}: accepted {len(acc)}, unsafe {sum(y)}")
    by = defaultdict(list)
    for r in acc:
        by[r["group"]].append(r)
    print("\nwithin-class label structure (R4-accepted): class  n  unsafe  safe  said labels (unsafe | safe)")
    out["by_class"] = {}
    for g in sorted(by):
        rs = by[g]
        u = [r for r in rs if r["label_unsafe"]]; s_ = [r for r in rs if not r["label_unsafe"]]
        def labs(rr):
            c = Counter()
            for r in rr:
                c.update(k.replace("said_label_", "") for k, v in r["features"].items() if k.startswith("said_label_") and v)
            return dict(c)
        out["by_class"][g] = {"n": len(rs), "unsafe": len(u), "safe": len(s_), "said_unsafe": labs(u), "said_safe": labs(s_)}
        print(f"  {g}  {len(rs):>3} {len(u):>6} {len(s_):>5}   {labs(u)} | {labs(s_)}")

    print("\nper-fold LOGO AUC (held-out class with both labels) and mean risk on one-label classes")
    out["per_fold"] = {}
    for cid, fam, hp, names in (("lr_full", "logistic", 10.0, ALL), ("lr_core", "logistic", 1.0, CORE),
                                ("tree", "tree", 3, ALL), ("lr_full_l100", "logistic", 100.0, ALL)):
        p = _oof(fam, hp, acc, names, folds)
        rec = {"pooled_auc": roc_auc(y, p), "folds": {}}
        for tr, te in folds:
            g = groups[te[0]]
            yy = [y[i] for i in te]; pp = [p[i] for i in te]
            if len(set(yy)) == 2:
                rec["folds"][g] = {"n": len(te), "unsafe": sum(yy), "auc": roc_auc(yy, pp)}
            else:
                rec["folds"][g] = {"n": len(te), "all": "unsafe" if yy[0] else "safe", "mean_risk": sum(pp) / len(pp)}
        mixed = [v["auc"] for v in rec["folds"].values() if "auc" in v]
        rec["mean_auc_mixed_folds"] = (sum(mixed) / len(mixed)) if mixed else None
        out["per_fold"][cid] = rec
        print(f"  {cid} (hp {hp}): pooled {rec['pooled_auc']:.3f}; mixed-fold mean AUC "
              f"{rec['mean_auc_mixed_folds'] if rec['mean_auc_mixed_folds'] is None else round(rec['mean_auc_mixed_folds'], 3)}")
        for g, v in rec["folds"].items():
            if "auc" in v:
                print(f"     {g} n={v['n']} unsafe={v['unsafe']} AUC {v['auc']:.2f}")
            else:
                print(f"     {g} n={v['n']} all {v['all']} mean risk {v['mean_risk']:.2f}")

    print("\nwithin-class pooled AUC per feature (pairs inside a class only), |AUC-0.5| top 12")
    res = []
    for f in ALL:
        conc = disc = ties = 0
        for g, rs in by.items():
            u = [r["features"][f] for r in rs if r["label_unsafe"]]
            s_ = [r["features"][f] for r in rs if not r["label_unsafe"]]
            for a in u:
                for b in s_:
                    if a > b: conc += 1
                    elif a < b: disc += 1
                    else: ties += 1
        tot = conc + disc + ties
        if tot:
            res.append((f, (conc + 0.5 * ties) / tot, tot))
    out["within_class_feature_auc"] = {f: {"auc": a, "pairs": n} for f, a, n in res}
    for f, a, n in sorted(res, key=lambda x: -abs(x[1] - 0.5))[:12]:
        print(f"  {f:<40} {a:.3f}  ({n} pairs)")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(out, indent=1) + "\n")
        print(f"\nwritten: {args.json_out}")


if __name__ == "__main__":
    main()
