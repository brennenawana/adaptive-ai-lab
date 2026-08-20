"""M0 telemetry floor (autopsy §13, scoped by docs/current/NEXT_STEP_M0.md § 6-D).

Three pieces, deliberately small:

  clocks     dual-clock stamps — every span carries realtime AND monotonic, because
             the WSL2 realtime clock was measured 7-12% slow against monotonic and
             the skew was invisible until the two were cross-checked.
  lifecycle  signal-safe run/case event log — the interrupted Bonsai probe left no
             end line and cost a forensic reconstruction; run_end is now written
             from atexit/SIGINT/SIGTERM handlers, exactly once.
  sampler    lightweight GPU/RAM sampler for long runs — only spot samples existed.

Deliberately NOT here (deferred to M-STAT, pre-registered in NEXT_STEP_M0.md § 6-D):
TOOLS spans, HARNESS events, periodic CLOCK-offset sampling, the DB inserted_at fix.
"""

from .clocks import dual_clock, monotonic_s, realtime_iso
from .lifecycle import RunEventLog
from .sampler import ResourceSampler

__all__ = [
    "ResourceSampler",
    "RunEventLog",
    "dual_clock",
    "monotonic_s",
    "realtime_iso",
]
