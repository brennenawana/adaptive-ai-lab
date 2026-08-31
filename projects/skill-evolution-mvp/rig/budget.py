"""Fail-closed spend meter (PLAN §6.1, S2-S5).

Every API call must pass precheck() BEFORE it is issued and record() after it
returns. Totals persist across processes in runs/spend.json; every call appends
a row to the run ledger. A cap breach raises BudgetExceeded — the orchestrator
checkpoints and halts cleanly; it never tops up on its own.
"""

import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path

from . import config


@contextmanager
def _locked(path: Path):
    """Cross-process lock so parallel runs cannot lose spend updates."""
    lock_path = path.with_suffix(".lock")
    with lock_path.open("w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


class BudgetExceeded(Exception):
    def __init__(self, scope: str, cap: float, spent: float):
        self.scope, self.cap, self.spent = scope, cap, spent
        super().__init__(f"STOPPED-BUDGET({scope}): spent ${spent:.4f} of ${cap:.2f} cap")


def _atomic_write(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, path)


class Meter:
    def __init__(self, phase: str, run_id: str, arm: str, run_dir: Path,
                 iteration_projection_usd: float | None = None):
        self.phase, self.run_id, self.arm = phase, run_id, arm
        self.run_dir = run_dir
        self.iteration_projection = iteration_projection_usd
        self.iteration = 0
        self.iteration_spend = 0.0
        self.spend_file = config.RUNS_DIR / "spend.json"
        config.RUNS_DIR.mkdir(parents=True, exist_ok=True)
        run_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = run_dir / "ledger.jsonl"

    # -- totals ------------------------------------------------------------
    def _totals(self) -> dict:
        if self.spend_file.exists():
            return json.loads(self.spend_file.read_text())
        return {"global": 0.0, "phases": {}, "runs": {}}

    def new_iteration(self, iteration: int) -> None:
        self.iteration = iteration
        self.iteration_spend = 0.0

    # -- the two mandatory hooks --------------------------------------------
    def precheck(self) -> None:
        t = self._totals()
        if t["global"] >= config.GLOBAL_CAP_USD:
            raise BudgetExceeded("global", config.GLOBAL_CAP_USD, t["global"])
        pcap = config.PHASE_CAPS_USD.get(self.phase)
        pspent = t["phases"].get(self.phase, 0.0)
        if pcap is not None and pspent >= pcap:
            raise BudgetExceeded(f"phase:{self.phase}", pcap, pspent)
        rcap = config.RUN_CAPS_USD.get(self.arm)
        rspent = t["runs"].get(self.run_id, 0.0)
        if rcap is not None and rspent >= rcap:
            raise BudgetExceeded(f"run:{self.run_id}", rcap, rspent)
        if self.iteration_projection is not None:
            icap = self.iteration_projection * config.ITER_OVERRUN_MULT
            if self.iteration_spend >= icap:
                raise BudgetExceeded(f"iteration:{self.iteration}", icap, self.iteration_spend)

    def record(self, *, model: str, usage, role: str, meta: dict,
               usd_total: float | None = None) -> float:
        p_in, p_out = config.PRICES[model]
        get = usage.get if isinstance(usage, dict) else lambda k, d=0: getattr(usage, k, d)
        in_tok = get("input_tokens", 0) or 0
        out_tok = get("output_tokens", 0) or 0
        cache_w = get("cache_creation_input_tokens", 0) or 0
        cache_r = get("cache_read_input_tokens", 0) or 0
        computed = (in_tok * p_in + cache_w * p_in * 1.25 + cache_r * p_in * 0.10
                    + out_tok * p_out) / 1e6
        # Bill the larger of our attributed computation and the provider's own
        # all-models total — the meter must never undercount.
        usd = max(computed, usd_total or 0.0)

        with _locked(self.spend_file):
            t = self._totals()
            t["global"] += usd
            t["phases"][self.phase] = t["phases"].get(self.phase, 0.0) + usd
            t["runs"][self.run_id] = t["runs"].get(self.run_id, 0.0) + usd
            _atomic_write(self.spend_file, t)
        self.iteration_spend += usd

        row = {"ts": time.time(), "kind": "api_call", "run": self.run_id,
               "arm": self.arm, "phase": self.phase, "iteration": self.iteration,
               "role": role, "model": model, "input_tokens": in_tok,
               "output_tokens": out_tok, "cache_write": cache_w,
               "cache_read": cache_r, "usd": round(usd, 6), **meta}
        with self.ledger.open("a") as f:
            f.write(json.dumps(row) + "\n")
        return usd

    def log_event(self, kind: str, **fields) -> None:
        row = {"ts": time.time(), "kind": kind, "run": self.run_id,
               "iteration": self.iteration, **fields}
        with self.ledger.open("a") as f:
            f.write(json.dumps(row) + "\n")

    def run_spend(self) -> float:
        return self._totals()["runs"].get(self.run_id, 0.0)
