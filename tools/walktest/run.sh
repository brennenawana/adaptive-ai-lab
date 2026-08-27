#!/usr/bin/env bash
# Execute a walk test inside an isolated sandbox as a genuinely fresh session.
#
#   ./run.sh <sandbox-root> [--model sonnet]
#
# Uses headless `claude -p` with the sandbox as cwd, so the session gets:
#   * no project CLAUDE.md (stripped at build)
#   * no memory (memory is keyed by cwd slug; this slug is new)
#   * the sandbox's logging-only hooks
# A SUBAGENT CANNOT SUBSTITUTE FOR THIS: subagents inherit the parent session's
# ambient context, which is exactly the defect this rig exists to remove.
set -euo pipefail

ROOT="${1:?usage: run.sh <sandbox-root> [--model <name>]}"
shift || true
MODEL="sonnet"; PROMPT_NAME="PROMPT.md"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)  MODEL="${2:?}"; shift 2 ;;
    --prompt) PROMPT_NAME="${2:?}"; shift 2 ;;
    *) echo "unknown flag: $1"; exit 2 ;;
  esac
done

[[ -d "$ROOT/workspace" ]] || { echo "no workspace/ in $ROOT"; exit 1; }
grep -q "RESULT: ISOLATED" "$ROOT/MANIFEST.txt" || { echo "sandbox not isolated; rebuild"; exit 1; }

PROMPT_FILE="$(cd "$(dirname "$0")" && pwd)/$PROMPT_NAME"
OUT="$ROOT/logs/report.md"

echo "running walk test in $ROOT (model: $MODEL)"
cd "$ROOT"
claude -p "$(cat "$PROMPT_FILE")" \
  --model "$MODEL" \
  --permission-mode acceptEdits \
  --output-format text \
  > "$OUT" 2> "$ROOT/logs/stderr.txt" || true

echo "report: $OUT"
echo "events: $ROOT/logs/events.jsonl ($(wc -l < "$ROOT/logs/events.jsonl" 2>/dev/null || echo 0) lines)"
