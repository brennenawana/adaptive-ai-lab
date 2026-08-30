"""Frozen-by-contract constants. Values marked TBD-at-freeze are pre-registered
defaults from PLAN.md; CONTRACT_v1 resolves them before any TRAIN inference."""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
RUNS_DIR = PROJECT_DIR / "runs"
TASKS_DIR = PROJECT_DIR / "tasks"
CACHE_DIR = Path.home() / ".cache" / "skill-evolution-mvp"
DATASET_DIR = CACHE_DIR / "spreadsheetbench_verified_400"
UPSTREAM_DIR = CACHE_DIR / "upstream"

DATASET_TARBALL_SHA256 = "10ef893dd29cb13ab97143ea787e68cdc9574a13873ab9a54e50b31dc03fc949"
UPSTREAM_COMMIT = "49b73a94775fb489063f60ca1865e3a650079a79"

EXECUTOR_MODEL = "claude-haiku-4-5"
OPTIMIZER_MODEL = {"B": "claude-haiku-4-5", "C": "claude-opus-5"}  # arm -> model

# First-party list prices, USD per Mtok (input, output), recorded 2026-08-30.
# Contract §15 re-verifies at freeze. Cache writes bill 1.25x input, reads 0.1x.
PRICES = {
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-opus-5": (5.00, 25.00),
}

# --- Stop criteria S1-S5 (PLAN §6.1) ---
TURN_CAP = 15            # S1: max assistant turns per test-case conversation
CMD_TIMEOUT = 90         # S1: seconds per bash command
PROPOSER_TURN_CAP = 25   # ReAct turns before forced no_action
GLOBAL_CAP_USD = 600.0   # S5
PHASE_CAPS_USD = {"P0": 5.0, "P1": 100.0, "P2": 200.0, "P3": 250.0}  # S4
RUN_CAPS_USD = {"A": 5.0, "B": 25.0, "C": 45.0}                      # S3
ITER_OVERRUN_MULT = 1.5  # S2, applied when an iteration projection is set

K_ITERATIONS = 8         # WikiSkill iterations 0-7 (Tab. 5 grouping)
PLATEAU_STOP = 3         # S8: consecutive iterations without an accepted proposal
CRASH_RATE_HALT = 0.20   # S9: harness-crash fraction per iteration

# Wiki maintainer trace sampling (paper App. C)
SAMPLE_MAX_FAIL = 5
SAMPLE_MAX_PASS = 3
TRACE_CHAR_CAP = 15_000

SUITE_SEED = 20260830
SPLIT_SIZES = {"train": 30, "val": 15, "test": 100}
SMOKE_TASKS = 3

ROLLOUT_WORKERS = 3

# S2 iteration spend projections (list-equivalent USD), measured in smoke;
# frozen in SE1 contract §16.
ITERATION_PROJECTION_USD = {"B": 2.30, "C": 3.00}
