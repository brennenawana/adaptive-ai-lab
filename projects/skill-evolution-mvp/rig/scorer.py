"""Adapter over the upstream SpreadsheetBench checker.

The upstream code (no license file -> never vendored into this repo) is fetched
at the pinned commit into ~/.cache/skill-evolution-mvp/upstream and imported
from there. Ground-truth isolation: only this module ever touches answer
files; executor workdirs receive input files only.
"""

import importlib.util
import sys

from . import config

_eval_mod = None


def _upstream():
    global _eval_mod
    if _eval_mod is None:
        path = config.UPSTREAM_DIR / "evaluation.py"
        if not path.exists():
            raise SystemExit(f"Upstream checker missing at {path}; fetch it first.")
        recorded = (config.UPSTREAM_DIR / "COMMIT").read_text().strip()
        if recorded != config.UPSTREAM_COMMIT:
            raise SystemExit("Upstream checker commit mismatch; refusing to score.")
        spec = importlib.util.spec_from_file_location("sb_evaluation", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["sb_evaluation"] = mod
        spec.loader.exec_module(mod)
        _eval_mod = mod
    return _eval_mod


def compare(gt_file, proc_file, task: dict) -> tuple[bool, str]:
    """True iff proc_file matches gt_file at the task's answer_position,
    per upstream compare_workbooks semantics."""
    import contextlib
    import io
    try:
        with contextlib.redirect_stdout(io.StringIO()):  # upstream prints on match
            ok, msg = _upstream().compare_workbooks(
                str(gt_file), str(proc_file),
                task["instruction_type"], task["answer_position"])
        return bool(ok), msg
    except Exception as e:
        return False, f"checker exception: {e}"


def score_task(task: dict, output_paths: dict) -> dict:
    """Soft score = fraction of available test cases passed (upstream
    soft_restriction; Verified-400 has one test case for 395/400 tasks).
    output_paths: {test_case: produced output path}."""
    from . import tasksio
    tcs = tasksio.test_cases(task)
    results = []
    for tc in tcs:
        _, ans = tasksio.task_files(task, tc)
        out = output_paths.get(tc)
        if out is None:
            results.append(0)
            continue
        ok, _ = compare(ans, out, task)
        results.append(int(ok))
    n = max(len(results), 1)
    return {"test_case_results": results,
            "soft": results.count(1) / n,
            "hard": 0 if (not results or 0 in results) else 1}
