"""Phase 1 driver: runs the contract's pre-registered spend order.

  1. Arm A baseline on VAL (15 tasks).
  2. S6 headroom gate: baseline must be inside [15%, 60%], else stop everything.
  3. Arm A TEST look (100 tasks; guarded by the look ledger).
  4. Pilot arm B, seed 1 (Haiku optimizer).
  5. Pilot arm C, seed 1 (Opus optimizer).

Every step prints a MILESTONE line for the monitor. Any budget/crash halt stops
the driver; runs are resumable after a human note (contract §13).
"""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rig import cli, config, orchestrator, tasksio  # noqa: E402

S6_BAND = (0.15, 0.60)


def milestone(msg: str) -> None:
    print(f"MILESTONE {msg}", flush=True)


def main() -> int:
    manifest = tasksio.load_manifest()
    train = tasksio.tasks_by_id(manifest["splits"]["train"])
    val = tasksio.tasks_by_id(manifest["splits"]["val"])
    milestone("phase1 start (contract SE-1, freeze 2da2ff9)")

    # Step 1-2: baseline + S6 gate.
    state_a = orchestrator.run_evolution(arm="A", seed=1, phase="P1",
                                         train=train, val=val, run_id="A-s1")
    base = state_a["r_best"]
    milestone(f"armA baseline VAL soft={base:.3f} spend=${state_a['spend_usd_equiv']:.2f}")
    if not (S6_BAND[0] <= base <= S6_BAND[1]):
        milestone(f"S6-STOP-RESCOPE: baseline {base:.3f} outside {S6_BAND}")
        return 2

    # Step 3: the one planned no-skill TEST look.
    milestone("armA TEST look starting (100 tasks)")
    cli.cmd_eval(SimpleNamespace(arm="A", seed=1, phase="P1", split="test",
                                 skills_from=None))
    test_a = json.loads((config.RUNS_DIR / "eval-A-s1-test" / "eval_test.json")
                        .read_text())
    milestone(f"armA TEST soft={test_a['mean_soft']:.3f}")

    # Steps 4-5: pilot evolution runs.
    for arm in ("B", "C"):
        milestone(f"arm{arm} pilot starting (seed 1, K={config.K_ITERATIONS})")
        state = orchestrator.run_evolution(arm=arm, seed=1, phase="P1",
                                           train=train, val=val,
                                           run_id=f"{arm}-s1")
        milestone(f"arm{arm} pilot done: stop={state['stop_reason']} "
                  f"best_val={state['r_best']:.3f} accepted={len(state['accepted'])} "
                  f"spend=${state['spend_usd_equiv']:.2f}")
        if str(state["stop_reason"]).startswith(("STOPPED", "S9")):
            milestone(f"HALT: arm{arm} stopped by rule; human note required to resume")
            return 3

    milestone("phase1 pilot complete — futility gate S7 is computed from B/C VAL "
              "scores vs baseline; see summaries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
