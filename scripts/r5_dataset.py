"""R5 — build the learned-routing dataset for one frozen run: snapshot + labels.

This is the analysis layer's side of the production-observable boundary. It reads a
persisted run (`learning.case_scores` + `learning.trajectories`), computes the
`RoutingFeatureSnapshot` for every case exactly as the runtime would at the R4 decision
point, and writes ONE row per case:

    features   the snapshot (allowlist only, `fis_platform/routing/features.py`)
    labels     safe_local = strict_all_pass, diagnostic failure flags, r4_escalate,
               strong_pass when a strong reference run is given (DEV/TEST)
    group      the CV grouping key (scenario class) — offline only, never a feature
    meta       analysis-only columns (case category for the exploratory class-prior
               comparator) — never a feature

Labels supervise; they never enter the snapshot. The extractor has no score/manifest
parameter, so the separation is structural, not a matter of discipline.

Two things worth knowing about the frozen Suite v3 arms:

* The answer body was not persisted (only its sha256), so the answer's own
  `root_cause.label` / `recommended_next_action` are reconstructed from the scorer's
  verbatim echo (`dimensions[root_cause].detail == "said <label>, truth <…>"`,
  `dimensions[next_action].detail == "said <action>"`). Only the `said` value is
  taken. From R5's TRAIN acquisition onward the parsed answer is in
  `learning.model_outputs`; when both exist the two are asserted equal, which
  validates the echo reconstruction on every TRAIN case.
* TEST is sealed for learned-policy work: this builder refuses `split == "test"`
  unless `--allow-test` is given AND `learning/registry/r5/test_unlock.json` names the
  run (written by `scripts/r5_replay.py --unlock-test`, contract § 14).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.routing.features import (  # noqa: E402
    FEATURE_ORDER, FEATURE_SCHEMA_VERSION, AnswerFields, snapshot_from,
)
from fis_platform.suite import git_head, require_comparable  # noqa: E402
from schemas.investigator import InvestigationResult  # noqa: E402
from schemas.trajectory import Trajectory  # noqa: E402
from services.ai_orchestrator.cascade import (  # noqa: E402
    EscalationPolicy, EscalationSignals, _UNSUPPORTED_MARKERS, should_escalate,
)

ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ.get("FIS_PG_DSN", "postgresql://fis:fis_local_dev@127.0.0.1:5433/fis")
DATASET_DIR = ROOT / "learning" / "datasets" / "r5"
UNLOCK_FILE = ROOT / "learning" / "registry" / "r5" / "test_unlock.json"

_SAID_LABEL = re.compile(r"^said (?P<said>[a-z_]+), truth ")
_SAID_ACTION = re.compile(r"^said (?P<said>[a-z_]+)$")


# ----------------------------------------------------------------------------- loading

def load_run(conn, run_id: str) -> dict[str, dict]:
    """Score + trajectory (+ split/class/category from the manifest, analysis-only)."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT cs.scenario_id, cs.all_pass, cs.trace_id, cs.payload AS score,
                      t.payload AS traj, m.split, m.category,
                      o.output AS answer
               FROM learning.case_scores cs
               JOIN learning.trajectories t ON t.trace_id = cs.trace_id
               JOIN ground_truth.scenario_manifests m ON m.scenario_id = cs.scenario_id
               LEFT JOIN learning.model_outputs o ON o.trace_id = cs.trace_id
               WHERE cs.run_id = %s
               ORDER BY cs.scenario_id""",
            (run_id,),
        )
        rows = cur.fetchall()
    if not rows:
        raise SystemExit(f"run {run_id!r} has no persisted scores")
    return {r["scenario_id"]: dict(r) for r in rows}


def load_strong_pass(conn, run_id: str) -> dict[str, bool]:
    with conn.cursor() as cur:
        cur.execute("SELECT scenario_id, all_pass FROM learning.case_scores WHERE run_id = %s",
                    (run_id,))
        return {sid: bool(ap) for sid, ap in cur.fetchall()}


# ------------------------------------------------------------- answer reconstruction

def answer_from_echo(score: dict[str, Any]) -> AnswerFields | None:
    """The model's own label/action, from the scorer's verbatim echo. None when the
    case produced no schema-valid object (a `produced_output` dimension exists)."""
    dims = {d["name"]: d for d in score.get("dimensions", [])}
    if "produced_output" in dims:
        return None
    label = action = None
    if (d := dims.get("root_cause")) and d.get("detail"):
        if m := _SAID_LABEL.match(d["detail"]):
            label = m.group("said")
    if (d := dims.get("next_action")) and d.get("detail"):
        if m := _SAID_ACTION.match(d["detail"]):
            action = m.group("said")
    if label is None and action is None:
        return None
    return AnswerFields(root_cause_label=label, recommended_next_action=action)


def answer_from_output(output: dict[str, Any] | None) -> AnswerFields | None:
    if not output:
        return None
    return AnswerFields.from_result(InvestigationResult.model_validate(output))


def answer_structure(output: dict[str, Any] | None) -> dict[str, float] | None:
    """EXPLORATORY answer-structure features from a persisted answer body (TRAIN
    acquisitions only). Not part of the versioned snapshot: the frozen DEV/TEST arms
    cannot compute them, so no eligible candidate may use them (contract § 9)."""
    if not output:
        return None
    r = InvestigationResult.model_validate(output)
    ids = [e for f in r.facts for e in f.entity_ids]
    services = {f.source.split("/")[2] for f in r.facts if f.source.count("/") >= 2}
    return {
        "n_facts": float(len(r.facts)),
        "n_entity_ids": float(len(ids)),
        "n_unique_entity_ids": float(len(set(ids))),
        "n_unique_sources": float(len({f.source for f in r.facts})),
        "n_services_cited": float(len(services)),
        "n_hypotheses": float(len(r.hypotheses)),
        "n_uncertainties": float(len(r.uncertainties)),
        "confidence": float(r.root_cause.confidence),
        "escalation_required": float(r.escalation_required),
        "summary_chars": float(len(r.summary)),
        "classification_chars": float(len(r.classification)),
        "facts_chars": float(sum(len(f.claim) for f in r.facts)),
    }


# ------------------------------------------------------------------------- labels

def r4_signals(score: dict[str, Any], traj: dict[str, Any]) -> EscalationSignals:
    """Exactly `routing_cascade_report._signals`, so replay and dataset agree."""
    v = traj.get("verification") or {}
    violations = tuple(v.get("violations") or [])
    produced = not any(d["name"] == "produced_output" for d in score.get("dimensions", []))
    return EscalationSignals(
        produced_output=produced,
        verifier_passed=bool(v.get("passed")) and produced,
        unsupported_claims=sum(1 for m in violations if any(k in m for k in _UNSUPPORTED_MARKERS)),
        violations=violations,
    )


def diagnostics(score: dict[str, Any], r4_escalate: bool) -> dict[str, bool]:
    s = score
    no_output = any(d["name"] == "produced_output" for d in s.get("dimensions", []))
    verifier_fail = (not s["verifier_passed"]) and not no_output
    unsafe = not s["all_pass"]
    return {
        "unsafe": unsafe,
        "no_output": no_output,
        "verifier_fail": verifier_fail,
        "unsupported": s.get("unsupported_claims", 0) > 0,
        "wrong_root_cause": (not no_output) and not s["root_cause_correct"],
        "evidence_miss": (not no_output) and s["required_evidence_recall"] < s.get("evidence_recall_threshold", 0.8),
        "action_fail": (not no_output) and not s["next_action_acceptable"],
        "forbidden_claim": bool(s.get("forbidden_claim_made")),
        # verifier-clean and wrong: the family the deterministic gate cannot see
        "silent": unsafe and not r4_escalate,
    }


# ------------------------------------------------------------------------- build

def build_rows(rows: dict[str, dict], run_id: str, strong: dict[str, bool] | None,
               *, check_echo: bool = True) -> tuple[list[dict], dict]:
    out: list[dict] = []
    echo_checked = echo_mismatch = 0
    for sid in sorted(rows):
        r = rows[sid]
        traj = Trajectory.model_validate(r["traj"])
        echo = answer_from_echo(r["score"])
        body = answer_from_output(r["answer"])
        if body is not None and check_echo:
            echo_checked += 1
            if echo != body:
                echo_mismatch += 1
                raise SystemExit(f"{sid}: scorer echo {echo} != persisted answer {body}")
        answer = body or echo
        snap = snapshot_from(traj, answer)
        sig = r4_signals(r["score"], r["traj"])
        r4_esc, r4_reason = should_escalate(sig, EscalationPolicy.VERIFIER)
        out.append({
            "scenario_id": sid,
            "run_id": run_id,
            "trace_id": str(r["trace_id"]),
            "split": r["split"],
            "group": sid[:3],                       # CV grouping key; offline only
            "local_model": snap.local_model,
            "feature_schema_version": snap.feature_schema_version,
            "snapshot_digest": snap.digest,
            "features": {k: snap.features[k] for k in FEATURE_ORDER},
            "label_safe": bool(r["all_pass"]),
            "label_unsafe": not bool(r["all_pass"]),
            "r4_escalate": bool(r4_esc),
            "r4_reason": r4_reason,
            "strong_pass": (None if strong is None else strong.get(sid)),
            "diag": diagnostics(r["score"], bool(r4_esc)),
            "meta": {"category": r["category"]},   # analysis-only; never a feature
            "answer_structure": answer_structure(r["answer"]),
        })
    return out, {"echo_checked": echo_checked, "echo_mismatch": echo_mismatch}


def dataset_digest(rows: list[dict]) -> str:
    """Digest of what a learner can see: features + labels + group, in order."""
    h = hashlib.sha256()
    for r in rows:
        h.update(json.dumps(
            [r["scenario_id"], r["group"], r["label_safe"], r["r4_escalate"], r["strong_pass"],
             [[k, r["features"][k]] for k in FEATURE_ORDER]],
            separators=(",", ":")).encode())
    return h.hexdigest()


def guard_split(split: str, run_id: str, allow_test: bool) -> None:
    if split != "test":
        return
    if not allow_test:
        raise SystemExit(f"{run_id!r} is a TEST run: sealed for learned-policy work "
                         "(contract § 14). Pass --allow-test only through r5_replay.py --unlock-test.")
    if not UNLOCK_FILE.exists():
        raise SystemExit(f"{run_id!r} is TEST and no unlock record exists at {UNLOCK_FILE}")
    unlock = json.loads(UNLOCK_FILE.read_text())
    if run_id not in {u.get("local_run") for u in unlock.get("unlocks", [])}:
        raise SystemExit(f"{run_id!r} is TEST and is not named by any unlock in {UNLOCK_FILE}")


def build_dataset(conn, run_id: str, strong_run: str | None, *, allow_test: bool = False,
                  allow_cross_suite: bool = False) -> tuple[list[dict], dict]:
    require_comparable(conn, [run_id, *([strong_run] if strong_run else [])],
                       allow_cross_suite=allow_cross_suite, against_corpus=True)
    rows = load_run(conn, run_id)
    splits = {r["split"] for r in rows.values()}
    if len(splits) != 1:
        raise SystemExit(f"run {run_id!r} spans splits {sorted(splits)}")
    split = splits.pop()
    guard_split(split, run_id, allow_test)
    strong = load_strong_pass(conn, strong_run) if strong_run else None
    if strong is not None:
        missing = sorted(set(rows) - set(strong))
        if missing:
            raise SystemExit(f"strong run {strong_run!r} lacks {len(missing)} scenarios: {missing[:5]}…")
    built, checks = build_rows(rows, run_id, strong)
    meta = {
        "run_id": run_id, "strong_run": strong_run, "split": split, "n": len(built),
        "feature_schema_version": FEATURE_SCHEMA_VERSION, "n_features": len(FEATURE_ORDER),
        "dataset_digest": dataset_digest(built), "code_commit": git_head(),
        "local_models": sorted({r["local_model"] for r in built if r["local_model"]}),
        "n_safe": sum(r["label_safe"] for r in built),
        "n_r4_escalate": sum(r["r4_escalate"] for r in built),
        "n_r4_accepted": sum(not r["r4_escalate"] for r in built),
        "n_silent": sum(r["diag"]["silent"] for r in built),
        "n_with_answer_body": sum(r["answer_structure"] is not None for r in built),
        **checks,
    }
    return built, meta


def write_dataset(rows: list[dict], meta: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r, separators=(",", ":"), sort_keys=True) + "\n" for r in rows))
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")


def read_dataset(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="R5 dataset: snapshot + labels for one frozen run")
    ap.add_argument("--run", required=True, help="local run id (e.g. R5-qwen-train, V3-qwen-dev)")
    ap.add_argument("--strong", help="strong reference run id (DEV/TEST): E4-v3-dev / E4-v3-96")
    ap.add_argument("--out", help=f"output JSONL (default {DATASET_DIR}/<run>.jsonl)")
    ap.add_argument("--allow-test", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--allow-cross-suite", action="store_true")
    args = ap.parse_args()
    with psycopg.connect(DSN) as conn:
        rows, meta = build_dataset(conn, args.run, args.strong, allow_test=args.allow_test,
                                   allow_cross_suite=args.allow_cross_suite)
    out = Path(args.out) if args.out else DATASET_DIR / f"{args.run}.jsonl"
    write_dataset(rows, meta, out)
    print(json.dumps(meta, indent=2, sort_keys=True))
    print(f"written: {out}")


if __name__ == "__main__":
    main()
