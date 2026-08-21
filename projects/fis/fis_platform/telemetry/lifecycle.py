"""Signal-safe run lifecycle events.

The R6 autopsy could not tell when the interrupted Bonsai probe ended because the
runner wrote its end line only on the happy path. This log writes every event as one
appended JSONL line (crash-safe: a dead process loses at most the line being written),
and guarantees a `run_end` line via atexit + SIGINT/SIGTERM handlers — written exactly
once, with `status` saying HOW the run ended.

Not a registry: nothing reads these events to make a decision. They are the timeline
the next autopsy queries instead of reconstructing (autopsy §13 EXPERIMENT rows).
"""

from __future__ import annotations

import atexit
import json
import signal
import sys
from pathlib import Path
from typing import Any

from .clocks import dual_clock

__all__ = ["RunEventLog"]


class RunEventLog:
    """Append-only JSONL event log for one run, with a guaranteed run_end line.

    Usage:
        log = RunEventLog(path, run_id="M0-...", experiment="M0")
        log.run_start(planned_cases=15)
        log.event("case_start", scenario_id="S02-1001001")
        ...
        log.run_end(status="completed", cases_done=15)   # or SIGINT writes it for you
    """

    def __init__(self, path: Path | str, run_id: str, **context: Any) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.context = dict(context)
        self._ended = False
        self._installed = False
        self._prev_handlers: dict[int, Any] = {}

    # ------------------------------------------------------------------ writing
    def event(self, event: str, **fields: Any) -> dict[str, Any]:
        line: dict[str, Any] = {"event": event, "run_id": self.run_id, **self.context,
                                **dual_clock(), **fields}
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, sort_keys=True, default=str) + "\n")
        return line

    def run_start(self, **fields: Any) -> dict[str, Any]:
        self._install_guards()
        return self.event("run_start", **fields)

    def run_end(self, status: str = "completed", **fields: Any) -> dict[str, Any] | None:
        """Written at most once — the guard handlers and the happy path can both call
        this without producing a second line."""
        if self._ended:
            return None
        self._ended = True
        return self.event("run_end", status=status, **fields)

    # ------------------------------------------------------------------ guards
    def _install_guards(self) -> None:
        """atexit + SIGINT/SIGTERM: a run that dies leaves a run_end line saying so.

        The signal handlers restore the previous handler and re-raise the signal, so
        exit codes and KeyboardInterrupt semantics are unchanged — the log observes
        the interruption, it does not swallow it.
        """
        if self._installed:
            return
        self._installed = True
        atexit.register(self._atexit_end)
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                self._prev_handlers[sig] = signal.signal(sig, self._signal_end)
            except (ValueError, OSError):      # non-main thread / unsupported platform
                pass

    def _atexit_end(self) -> None:
        self.run_end(status="interrupted-atexit")

    def _signal_end(self, signum: int, frame: Any) -> None:
        self.run_end(status=f"interrupted-signal-{signal.Signals(signum).name}")
        prev = self._prev_handlers.get(signum, signal.SIG_DFL)
        signal.signal(signum, prev if callable(prev) or prev in (signal.SIG_DFL, signal.SIG_IGN)
                      else signal.SIG_DFL)
        signal.raise_signal(signum)
        sys.exit(128 + signum)      # unreachable for SIG_DFL, explicit for SIG_IGN
