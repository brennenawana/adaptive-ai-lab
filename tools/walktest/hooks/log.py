#!/usr/bin/env python3
"""Walk-test observability hook: append every harness event to a JSONL log.

Reads the hook payload from stdin, stamps it, and appends to $WALKTEST_LOG.
Writes NOTHING to stdout that could become model context (a bare exit 0), so
the logger cannot contaminate the run it observes.
"""
import json
import os
import sys
import datetime

LOG = os.environ.get("WALKTEST_LOG", "/tmp/walktest.jsonl")


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {"_unparsed": raw[:4000]}

    event = {
        "ts": datetime.datetime.now().isoformat(timespec="microseconds"),
        "event": os.environ.get("CLAUDE_HOOK_EVENT", payload.get("hook_event_name", "?")),
        "session_id": payload.get("session_id"),
        "cwd": payload.get("cwd"),
        "tool": payload.get("tool_name"),
        "tool_input": payload.get("tool_input"),
        "prompt": payload.get("prompt"),
        "source": payload.get("source"),
    }
    # Tool results can be huge; keep a bounded, typed summary.
    resp = payload.get("tool_response")
    if resp is not None:
        text = resp if isinstance(resp, str) else json.dumps(resp, default=str)
        event["result_bytes"] = len(text)
        event["result_head"] = text[:600]

    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, default=str) + "\n")
    except OSError as exc:                      # never break the run being observed
        print(f"walktest-log-error: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
