#!/usr/bin/env python3
"""Prediction ledger CLI — playbook § 7's pre-registered point estimate + interval,
frozen once per prediction and scored once against the actual result.

Every write goes through `fis_platform.predictions.PredictionLedger`, which is the only
writer of the file: append-only, hash-chained, and refuses on the guards documented
there (duplicate prediction_id, a point outside its own interval, an empty rationale,
evaluating before a freeze, evaluating twice, a caller's inside_interval/abs_error claim
that disagrees with what the ledger itself computes). `--path` defaults to the live
location (`learning/registry/predictions.jsonl`); tests pass a `tmp_path` file instead —
there is deliberately no environment variable that relocates the default (see the module
docstring in `fis_platform.predictions`).

    freeze     append one prediction entry
    evaluate   append one evaluation entry, scoring an existing prediction
    show       print one prediction (+ its evaluation, if scored) or the whole ledger
    verify     re-derive every digest and chain link; exit 1 on the first mismatch
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.predictions import (
    DEFAULT_LEDGER_PATH,
    LedgerIntegrityError,
    PredictionLedger,
    PredictionRefused,
)


def _emit(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def _bool_arg(value: str) -> bool:
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    raise argparse.ArgumentTypeError(f"expected true/false, got {value!r}")


# ------------------------------------------------------------------ commands

def cmd_freeze(args: argparse.Namespace, ledger: PredictionLedger) -> int:
    entry = ledger.freeze_prediction(
        prediction_id=args.prediction_id, experiment_id=args.experiment_id,
        candidate_id=args.candidate_id, metric=args.metric, point=args.point,
        interval=(args.lo, args.hi), rationale=args.rationale,
    )
    _emit(entry)
    return 0


def cmd_evaluate(args: argparse.Namespace, ledger: PredictionLedger) -> int:
    entry = ledger.evaluate(
        args.prediction_id, args.actual,
        inside_interval=args.inside_interval, abs_error=args.abs_error,
    )
    _emit(entry)
    return 0


def cmd_show(args: argparse.Namespace, ledger: PredictionLedger) -> int:
    if args.prediction_id:
        _emit(ledger.get(args.prediction_id))
        return 0
    entries = ledger.read()
    if not entries:
        print(f"no entries at {ledger.path}")
        return 0
    for e in entries:
        if e["kind"] == "prediction":
            print(f"{e['seq']:>3} prediction  {e['prediction_id']:<28} {e['metric']:<20} "
                  f"point={e['point']} interval={e['interval']}  {e['frozen_at']}")
        else:
            print(f"{e['seq']:>3} evaluation  {e['prediction_id']:<28} actual={e['actual']} "
                  f"inside_interval={e['inside_interval']} abs_error={e['abs_error']}  "
                  f"{e['evaluated_at']}")
    return 0


def cmd_verify(args: argparse.Namespace, ledger: PredictionLedger) -> int:
    try:
        entries = ledger.read()
    except LedgerIntegrityError as exc:
        print(f"INTEGRITY: {exc}", file=sys.stderr)
        return 1
    predicted = sum(1 for e in entries if e["kind"] == "prediction")
    evaluated = sum(1 for e in entries if e["kind"] == "evaluation")
    print(f"{ledger.path}: {len(entries)} entries OK "
          f"({predicted} predictions, {evaluated} evaluations)")
    return 0


# ------------------------------------------------------------------ argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--path", default=str(DEFAULT_LEDGER_PATH),
                        help="ledger file (default: the live location)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("freeze", help="append one prediction entry")
    p.add_argument("--prediction-id", required=True)
    p.add_argument("--experiment-id", required=True)
    p.add_argument("--candidate-id")
    p.add_argument("--metric", required=True)
    p.add_argument("--point", required=True, type=float)
    p.add_argument("--lo", required=True, type=float)
    p.add_argument("--hi", required=True, type=float)
    p.add_argument("--rationale", required=True)
    p.set_defaults(func=cmd_freeze)

    p = sub.add_parser("evaluate", help="append one evaluation entry")
    p.add_argument("--prediction-id", required=True)
    p.add_argument("--actual", required=True, type=float)
    p.add_argument("--inside-interval", type=_bool_arg, default=None,
                   help="optional independent claim; refused if it disagrees with the "
                        "ledger's own computation")
    p.add_argument("--abs-error", type=float, default=None,
                   help="optional independent claim; refused if it disagrees with the "
                        "ledger's own computation")
    p.set_defaults(func=cmd_evaluate)

    p = sub.add_parser("show", help="print one prediction or the whole ledger")
    p.add_argument("--prediction-id")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("verify", help="re-derive every digest and chain link")
    p.set_defaults(func=cmd_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ledger = PredictionLedger(args.path)
    try:
        return int(args.func(args, ledger))
    except (PredictionRefused, LedgerIntegrityError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
