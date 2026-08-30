"""Rig commands. Everything except `smoke` and `run` is offline (no model calls).

  uv run python -m rig.cli check         # dataset, checker, CLI presence
  uv run python -m rig.cli draw-suite    # seeded, filtered 30/15/100 + smoke draw
  uv run python -m rig.cli selftest-checker
  uv run python -m rig.cli selftest-budget
  uv run python -m rig.cli smoke         # paid: tiny end-to-end loop, phase P0
  uv run python -m rig.cli spend         # totals from runs/spend.json
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

from . import config, gateway, scorer, tasksio
from .budget import BudgetExceeded, Meter


def cmd_check(_):
    ok = True
    for label, path in [("dataset", config.DATASET_DIR / "dataset.json"),
                        ("checker", config.UPSTREAM_DIR / "evaluation.py"),
                        ("commit pin", config.UPSTREAM_DIR / "COMMIT")]:
        print(f"{label}: {'OK' if path.exists() else 'MISSING'} ({path})")
        ok &= path.exists()
    try:
        print(f"claude CLI: {gateway.cli_binary()}")
    except gateway.GatewayError as e:
        print(f"claude CLI: MISSING ({e})")
        ok = False
    print(f"tarball sha256 pinned: {config.DATASET_TARBALL_SHA256[:16]}…")
    sys.exit(0 if ok else 1)


def cmd_draw_suite(_):
    m = tasksio.draw_suite()
    print(json.dumps({k: (len(v) if isinstance(v, list) else v)
                      for k, v in m["splits"].items()}, indent=2))
    print(f"smoke tasks: {m['smoke']}")
    print(f"excluded: {len(m['excluded'])} of {m['candidates_scanned']} scanned")
    for e in m["excluded"]:
        print(f"  - {e['id']}: {e['reason']}")
    print(f"manifest sha256: {m['manifest_sha256']}")


def cmd_selftest_checker(_):
    dataset = tasksio.load_dataset()
    sample = dataset[:3]
    failures = 0
    for task in sample:
        for tc in tasksio.test_cases(task):
            inp, ans = tasksio.task_files(task, tc)
            a, _ = scorer.compare(ans, ans, task)
            b, msg = scorer.compare(ans, inp, task)
            status = "OK" if (a and not b) else "UNEXPECTED"
            if status != "OK":
                failures += 1
            print(f"task {task['id']} tc{tc}: answer==answer {a}, "
                  f"input==answer {b} -> {status} {msg[:60]}")
    print("PASS" if failures == 0 else f"{failures} unexpected results "
          "(acceptable if the suite draw filter excludes such tasks)")


def cmd_selftest_budget(_):
    with tempfile.TemporaryDirectory() as td:
        meter = Meter(phase="P0", run_id="selftest", arm="A", run_dir=Path(td))
        meter.spend_file = Path(td) / "spend.json"  # isolated from real totals
        fake_usage = {"input_tokens": 400_000, "output_tokens": 100_000}
        calls = 0
        try:
            while True:
                meter.precheck()
                meter.record(model="claude-opus-5", usage=fake_usage,
                             role="selftest", meta={})
                calls += 1
                if calls > 100:
                    print("FAIL: meter never halted")
                    sys.exit(1)
        except BudgetExceeded as e:
            ledger_rows = (Path(td) / "ledger.jsonl").read_text().strip().count("\n") + 1
            print(f"halted after {calls} recorded calls: {e}")
            print(f"ledger rows intact: {ledger_rows}")
            print("PASS" if calls > 0 else "FAIL")
            sys.exit(0 if calls > 0 else 1)


def cmd_smoke(args):
    from . import orchestrator
    manifest = tasksio.load_manifest()
    smoke_tasks = tasksio.tasks_by_id(manifest["smoke"])
    train, val = smoke_tasks[:2], smoke_tasks[2:3]
    print(f"smoke: train={[t['id'] for t in train]} val={[t['id'] for t in val]}")
    state = orchestrator.run_evolution(
        arm=args.arm, seed=0, phase="P0", train=train, val=val,
        k_iterations=1, workers=1, run_id=f"smoke-{args.arm}",
        audit=True, force_full_loop=True)
    print(json.dumps(state, indent=2))


def cmd_run(args):
    from . import orchestrator
    manifest = tasksio.load_manifest()
    state = orchestrator.run_evolution(
        arm=args.arm, seed=args.seed, phase=args.phase,
        train=tasksio.tasks_by_id(manifest["splits"]["train"]),
        val=tasksio.tasks_by_id(manifest["splits"]["val"]))
    print(json.dumps(state, indent=2))


def cmd_eval(args):
    """One held-out evaluation. TEST looks are guarded by the look ledger:
    the look must be planned and not yet spent; the spent row is written
    BEFORE the evaluation starts (contract §5, §12)."""
    import time as _time

    from . import orchestrator
    manifest = tasksio.load_manifest()
    tasks = tasksio.tasks_by_id(manifest["splits"][args.split])
    run_id = f"eval-{args.arm}-s{args.seed}-{args.split}"

    if args.split == "test":
        key = f"{args.arm}-s{args.seed}"
        ledger = config.RUNS_DIR / "test_looks.jsonl"
        rows = [json.loads(l) for l in ledger.read_text().splitlines()] \
            if ledger.exists() else []
        planned = {r["planned"] for r in rows if "planned" in r}
        spent = {r["spent"] for r in rows if "spent" in r}
        if key not in planned:
            sys.exit(f"REFUSED: TEST look {key} is not in the planned ledger (S11)")
        if key in spent:
            sys.exit(f"REFUSED: TEST look {key} was already spent (S11)")
        with ledger.open("a") as f:
            f.write(json.dumps({"spent": key, "ts": _time.time(),
                                "skills_from": args.skills_from}) + "\n")

    out = orchestrator.evaluate_split(
        arm=args.arm, run_id=run_id, phase=args.phase, tasks=tasks,
        split_name=args.split, skills_from=args.skills_from)
    print(json.dumps({k: v for k, v in out.items() if k != "per_task"}, indent=2))


def cmd_spend(_):
    f = config.RUNS_DIR / "spend.json"
    print(f.read_text() if f.exists() else "no spend recorded")


def main():
    p = argparse.ArgumentParser(prog="rig")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    sub.add_parser("draw-suite").set_defaults(fn=cmd_draw_suite)
    sub.add_parser("selftest-checker").set_defaults(fn=cmd_selftest_checker)
    sub.add_parser("selftest-budget").set_defaults(fn=cmd_selftest_budget)
    ps = sub.add_parser("smoke")
    ps.add_argument("--arm", default="C", choices=["B", "C"])
    ps.set_defaults(fn=cmd_smoke)
    pr = sub.add_parser("run")
    pr.add_argument("--arm", required=True, choices=["A", "B", "C"])
    pr.add_argument("--seed", type=int, required=True)
    pr.add_argument("--phase", required=True, choices=list(config.PHASE_CAPS_USD))
    pr.set_defaults(fn=cmd_run)
    pe = sub.add_parser("eval")
    pe.add_argument("--arm", required=True, choices=["A", "B", "C"])
    pe.add_argument("--seed", type=int, required=True)
    pe.add_argument("--phase", required=True, choices=list(config.PHASE_CAPS_USD))
    pe.add_argument("--split", required=True, choices=["val", "test"])
    pe.add_argument("--skills-from", default=None,
                    help="run id whose accepted skills/ to inject (omit for no skills)")
    pe.set_defaults(fn=cmd_eval)
    sub.add_parser("spend").set_defaults(fn=cmd_spend)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
