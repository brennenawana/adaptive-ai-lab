#!/usr/bin/env python3
"""TEST-look ledger CLI — the only writer of `learning/registry/test_looks.jsonl`.

Every write goes to `TestLookLedger(default_path())`. There is deliberately no `--path`
and no environment variable: a ledger you can point somewhere else is a reset button,
and the whole point of this file is that "we already spent look #N" is not a thing
anyone can un-say (playbook §1, authority model, owner decision 2026-08-21). Tests
construct `TestLookLedger(tmp_path / "test_looks.jsonl")` and call the ledger's methods
directly.

    seed      create the ledger with the seven historical Suite-v3 looks (once)
    plan      append a planned look at contract-freeze time
    verify    chain verification + mirror validation against TEST_LOOK_LEDGER.md
    show      print every entry
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fis_platform.test_looks import (
    LedgerIntegrityError,
    LookRefused,
    MirrorDivergence,
    TestLookLedger,
    default_markdown_path,
    default_path,
)


def cmd_seed(args: argparse.Namespace, ledger: TestLookLedger) -> int:
    written = ledger.seed()
    print(f"seeded {len(written)} historical looks at {ledger.path}")
    return 0


def cmd_plan(args: argparse.Namespace, ledger: TestLookLedger) -> int:
    look_no = args.look_no if args.look_no is not None else ledger.next_look_no(args.suite_version)
    entry = ledger.plan_look(
        look_no=look_no, suite_version=args.suite_version, experiment=args.experiment,
        arm=args.arm, run_id=args.run_id, authorized_by=args.authorized_by,
        trigger_review_ref=args.trigger_review_ref,
    )
    print(f"planned look #{entry['look_no']} suite={entry['suite_version']} "
          f"run_id={entry['run_id']} authorized_by={entry['authorized_by']}")
    return 0


def cmd_verify(args: argparse.Namespace, ledger: TestLookLedger) -> int:
    from fis_platform.test_looks import validate_mirror
    entries = ledger.read()
    print(f"{ledger.path}: {len(entries)} entries, chain OK")
    validate_mirror(ledger.path, default_markdown_path())
    print(f"{default_markdown_path()}: mirror OK")
    return 0


def cmd_show(args: argparse.Namespace, ledger: TestLookLedger) -> int:
    entries = ledger.read()
    if not entries:
        print(f"no entries at {ledger.path}")
        return 0
    for e in entries:
        if e["kind"] == "historical":
            label = f"{e['experiment']} / {e['arm_run']} ({e['look_kind']})"
        elif e["kind"] == "planned":
            label = (f"{e['experiment']} / {e['arm']} run_id={e['run_id']} "
                     f"by={e['authorized_by']} review={e['trigger_review_ref']}")
        else:
            label = f"run_id={e['run_id']} first_scenario={e['first_scenario_id']}"
        print(f"{e['seq']:>3} look#{e['look_no']:<3} suite={e['suite_version']:<3} "
              f"{e['kind']:<10} {label}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("seed", help="create the ledger from the seven historical looks")
    p.set_defaults(func=cmd_seed)

    p = sub.add_parser("plan", help="append a planned TEST look at contract-freeze time")
    p.add_argument("--look-no", type=int, help="defaults to next_look_no(suite-version)")
    p.add_argument("--suite-version", required=True)
    p.add_argument("--experiment", required=True)
    p.add_argument("--arm", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--authorized-by", required=True)
    p.add_argument("--trigger-review-ref", help="required for suite 3 look #8+")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("verify", help="chain verification + mirror validation")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("show", help="print every entry in the ledger")
    p.set_defaults(func=cmd_show)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ledger = TestLookLedger(default_path())
    try:
        return int(args.func(args, ledger))
    except (LookRefused, LedgerIntegrityError, MirrorDivergence) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
