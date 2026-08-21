"""Dual-clock stamps.

The R6 autopsy measured the WSL2 realtime clock 7-12% slow against CLOCK_MONOTONIC
across long runs (suspected host suspend interaction), which silently deflated every
published latency. Neither clock alone is trustworthy here:

  realtime   names WHEN something happened (comparable across machines and logs),
             but has been observed to lose time under WSL2;
  monotonic  measures HOW LONG something took (immune to the skew and to NTP steps),
             but is meaningless across a reboot.

So every span carries both, and the consumer declares which clock is authoritative
per metric (playbook § 8: wall-clock claims use realtime, durations use monotonic).
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

__all__ = ["dual_clock", "monotonic_s", "realtime_iso"]


def realtime_iso() -> str:
    """UTC realtime, millisecond resolution."""
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def monotonic_s() -> float:
    """CLOCK_MONOTONIC seconds, millisecond resolution (raw float is unbounded noise)."""
    return round(time.monotonic(), 3)


def dual_clock(prefix: str = "ts") -> dict[str, Any]:
    """Both stamps, keyed `<prefix>_realtime` / `<prefix>_monotonic`."""
    return {f"{prefix}_realtime": realtime_iso(), f"{prefix}_monotonic": monotonic_s()}
