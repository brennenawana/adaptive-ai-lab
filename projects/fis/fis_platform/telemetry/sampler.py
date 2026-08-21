"""Lightweight GPU/RAM sampler for long runs.

The R6 autopsy had only spot samples of VRAM and host RAM, so the 9h55m of cap-burn
could not be correlated with memory pressure after the fact. This thread samples
every few seconds into JSONL; ~17k lines across a 24 h run, negligible overhead.

Every sample also carries `clock_offset_s` (realtime minus monotonic, sampled at
that instant): its DRIFT over a run IS the WSL2 realtime-clock skew the R6 autopsy
§13 CLOCK row asked to make a first-class measurement instead of a forensic
discovery (projects/fis/R6_PERFORMANCE_AUTOPSY.md:249-250).

Best-effort by design: a missing nvidia-smi is a missing field, never a dead run.
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Self

from .clocks import dual_clock

__all__ = ["ResourceSampler"]

_SMI_QUERY = ("utilization.gpu,memory.used,memory.total,temperature.gpu,"
              "power.draw,clocks.sm")


def _gpu_sample() -> dict[str, Any]:
    try:
        out = subprocess.run(
            ["nvidia-smi", f"--query-gpu={_SMI_QUERY}", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10, check=True).stdout
        vals = [v.strip() for v in out.strip().splitlines()[0].split(",")]
        keys = ["gpu_util_pct", "vram_used_mib", "vram_total_mib", "gpu_temp_c",
                "gpu_power_w", "gpu_sm_mhz"]
        return dict(zip(keys, vals))
    except Exception:  # noqa: BLE001 — telemetry only
        return {}


def _host_sample() -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        meminfo = Path("/proc/meminfo").read_text()
        for key, name in (("MemAvailable", "host_mem_available_kib"),
                          ("MemTotal", "host_mem_total_kib")):
            for ln in meminfo.splitlines():
                if ln.startswith(key + ":"):
                    out[name] = int(ln.split()[1])
                    break
        out["host_load1"] = float(Path("/proc/loadavg").read_text().split()[0])
    except Exception:  # noqa: BLE001, S110 — telemetry only
        pass
    return out


class ResourceSampler:
    """Background sampling thread. `with ResourceSampler(path, interval_s=5): ...`"""

    def __init__(self, path: Path | str, interval_s: float = 5.0,
                 context: dict[str, Any] | None = None) -> None:
        self.path = Path(path)
        self.interval_s = float(interval_s)
        self.context = dict(context or {})
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.samples_written = 0

    def _loop(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            while not self._stop.is_set():
                # Sampled directly from time.time()/time.monotonic(), right next to the
                # dual_clock() call, so the pairing is tight rather than reusing a stamp
                # that was already rounded/formatted for a different purpose.
                realtime_epoch_seconds = time.time()
                monotonic_seconds = time.monotonic()
                line = {**self.context, **dual_clock(),
                        "clock_offset_s": round(realtime_epoch_seconds - monotonic_seconds, 3),
                        **_gpu_sample(), **_host_sample()}
                fh.write(json.dumps(line, sort_keys=True, default=str) + "\n")
                fh.flush()
                self.samples_written += 1
                self._stop.wait(self.interval_s)

    def start(self) -> ResourceSampler:
        if self._thread is None:
            self._thread = threading.Thread(target=self._loop, name="fis-resource-sampler",
                                            daemon=True)
            self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.interval_s + 12)
            self._thread = None

    def __enter__(self) -> Self:
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.stop()
