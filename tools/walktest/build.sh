#!/usr/bin/env bash
# Build an isolated, fully-observed sandbox for a walk test.
#
#   ./build.sh <source-dir> [--keep-git]
#
# Produces:  /private/tmp/walktest/<stamp>/
#              workspace/   the stripped copy the agent may read
#              logs/        JSONL event log (OUTSIDE workspace by design)
#              .claude/     logging-only hooks (at the PARENT, so the
#                           workspace itself stays pristine)
#              MANIFEST.txt what was copied, what was stripped, isolation proof
set -euo pipefail

SRC="${1:?usage: build.sh <source-dir> [--keep-git]}"
KEEP_GIT="${2:-}"
SRC="$(cd "$SRC" && pwd)"

STAMP="$(date +%Y%m%d-%H%M%S)"
ROOT="/private/tmp/walktest/${STAMP}"
WS="$ROOT/workspace"
LOGS="$ROOT/logs"
HOOK="$(cd "$(dirname "$0")" && pwd)/hooks/log.py"

mkdir -p "$WS" "$LOGS" "$ROOT/.claude"

# ---- copy, stripping every known auto-load / context-injection surface ----
EXCLUDES=(
  --exclude 'CLAUDE.md' --exclude 'CLAUDE.local.md'
  --exclude '.claude/'  --exclude '.cursorrules' --exclude '.cursor/'
  --exclude 'AGENTS.md' --exclude '.github/copilot-instructions.md'
  --exclude '.aider*'   --exclude '.windsurfrules'
  --exclude '.DS_Store'
)
[[ "$KEEP_GIT" == "--keep-git" ]] || EXCLUDES+=( --exclude '.git/' --exclude '.gitignore' )

rsync -a "${EXCLUDES[@]}" "$SRC"/ "$WS"/

# ---- logging-only hook config at the PARENT (workspace stays clean) ----
cat > "$ROOT/.claude/settings.json" <<JSON
{
  "env": { "WALKTEST_LOG": "$LOGS/events.jsonl" },
  "hooks": {
    "SessionStart":     [ { "hooks": [ { "type": "command", "command": "$HOOK" } ] } ],
    "UserPromptSubmit": [ { "hooks": [ { "type": "command", "command": "$HOOK" } ] } ],
    "PreToolUse":       [ { "matcher": "*", "hooks": [ { "type": "command", "command": "$HOOK" } ] } ],
    "PostToolUse":      [ { "matcher": "*", "hooks": [ { "type": "command", "command": "$HOOK" } ] } ],
    "Stop":             [ { "hooks": [ { "type": "command", "command": "$HOOK" } ] } ]
  }
}
JSON

# ---- isolation verification (fail loudly rather than silently contaminate) ----
{
  echo "WALK-TEST SANDBOX MANIFEST"
  echo "built:  $(date -Iseconds)"
  echo "source: $SRC"
  echo "root:   $ROOT"
  echo "git:    $([[ "$KEEP_GIT" == "--keep-git" ]] && echo kept || echo stripped)"
  echo
  echo "--- files copied ($(find "$WS" -type f | wc -l | tr -d ' ')) ---"
  (cd "$WS" && find . -type f | sort)
  echo
  echo "--- isolation checks ---"
} > "$ROOT/MANIFEST.txt"

fail=0
check () { # label, condition-result
  if [[ "$2" == "0" ]]; then echo "  PASS  $1" >> "$ROOT/MANIFEST.txt"
  else echo "  FAIL  $1" >> "$ROOT/MANIFEST.txt"; fail=1; fi
}

# no CLAUDE.md inside the workspace
found=$(find "$WS" -name 'CLAUDE*.md' | wc -l | tr -d ' ')
check "no CLAUDE.md in workspace (found $found)" "$([[ $found -eq 0 ]] && echo 0 || echo 1)"

# no CLAUDE.md in any ancestor of the sandbox
anc=0; d="$ROOT"
while [[ "$d" != "/" ]]; do [[ -f "$d/CLAUDE.md" ]] && anc=$((anc+1)); d="$(dirname "$d")"; done
check "no CLAUDE.md in ancestors (found $anc)" "$([[ $anc -eq 0 ]] && echo 0 || echo 1)"

# no user-level CLAUDE.md
check "no ~/.claude/CLAUDE.md" "$([[ -f "$HOME/.claude/CLAUDE.md" ]] && echo 1 || echo 0)"

# no memory dir for this cwd slug (memory is keyed by cwd path)
slug="$(echo "$ROOT" | sed 's#/#-#g')"
check "no memory dir for slug $slug" "$([[ -d "$HOME/.claude/projects/$slug" ]] && echo 1 || echo 0)"

# no .claude inside the workspace itself
found=$(find "$WS" -name '.claude' -maxdepth 3 | wc -l | tr -d ' ')
check "no .claude/ inside workspace (found $found)" "$([[ $found -eq 0 ]] && echo 0 || echo 1)"

# our own hooks must not emit stdout (would become context)
out="$(echo '{}' | WALKTEST_LOG="$LOGS/probe.jsonl" python3 "$HOOK" 2>/dev/null || true)"
check "logging hook emits no stdout" "$([[ -z "$out" ]] && echo 0 || echo 1)"

{
  echo
  echo "--- KNOWN RESIDUAL (cannot be stripped per-project) ---"
  echo "  ~/.claude/settings.json global hooks inject a timestamp systemMessage"
  echo "  on UserPromptSubmit/Stop. Trivial, but it IS non-workspace context."
  echo "  Remove those hooks for a maximally clean run."
  echo
  echo "RESULT: $([[ $fail -eq 0 ]] && echo 'ISOLATED' || echo 'NOT ISOLATED - do not trust results')"
} >> "$ROOT/MANIFEST.txt"

cat "$ROOT/MANIFEST.txt" | tail -20
echo
echo "sandbox: $ROOT"
echo "launch:  cd $ROOT && claude"
[[ $fail -eq 0 ]] || { echo "ISOLATION FAILED"; exit 1; }
