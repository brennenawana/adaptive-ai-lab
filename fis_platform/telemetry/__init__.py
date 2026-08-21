"""M0 telemetry floor (autopsy §13, scoped by docs/current/NEXT_STEP_M0.md § 6-D).

Three pieces, deliberately small:

  clocks     dual-clock stamps — every span carries realtime AND monotonic, because
             the WSL2 realtime clock was measured 7-12% slow against monotonic and
             the skew was invisible until the two were cross-checked.
  lifecycle  signal-safe run/case event log — the interrupted Bonsai probe left no
             end line and cost a forensic reconstruction; run_end is now written
             from atexit/SIGINT/SIGTERM handlers, exactly once.
  sampler    lightweight GPU/RAM sampler for long runs — only spot samples existed.

M-STAT (M_STAT_IMPLEMENTATION_MAP.md § 14) lands three of the four items pre-registered
here as deferred: TOOLS spans (dual-clock stamps + an optional `on_event` hook on
`ToolBroker.invoke`, in fis_platform/tool_broker/broker.py and schemas/tool.py — every
call gets `tool_call_start`/`tool_call_end`, denied path included), periodic CLOCK-offset
sampling (`clock_offset_s` on every `ResourceSampler` line, in sampler.py), and the DB
`inserted_at` fix (infra/migrations/009_inserted_at.sql — nullable, no backfill; a
statement-time column beside the transaction-frozen `created_at`).

Still deferred, to the D-series: the full autopsy-§13 HARNESS row (subagent start/end,
tests spans, report-generation spans, commit-sha events) — M0's manual phase-span call
and run/case-level events are the floor; M-STAT does not extend HARNESS beyond that.
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
