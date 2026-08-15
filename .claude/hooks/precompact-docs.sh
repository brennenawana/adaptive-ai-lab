#!/usr/bin/env bash
# PreCompact: fires before auto or manual compaction.
#
# Compaction is the moment accumulated design decisions get lost. This injects an
# instruction to flush them to the durable docs FIRST, so the post-compaction
# context can recover them by reading files rather than by remembering.
cat > /dev/null 2>&1 || true

# shellcheck source=_resolve-python.sh
. "$(dirname "${BASH_SOURCE[0]}")/_resolve-python.sh"

CONTEXT=$(cat <<'EOF'
CONTEXT IS ABOUT TO BE COMPACTED.

Before continuing, bring the durable design docs fully up to date. Anything that
exists only in conversation history is about to be lost; anything written to
these files survives.

In the FIS repo:
  docs/architecture.md         component map, ports, event topology
  docs/task-ontology.md        case categories, root causes, cause->action table
  docs/clean-room-boundary.md  what may and may not enter this sandbox
  docs/experiment-log.md       results so far, AND decisions deliberately NOT taken

Capture, in full:
  1. Any architectural decision made this session, and the reason for it
  2. Any bug found, its root cause, and the fix - especially HARNESS bugs, which
     would otherwise be mistaken for model weakness on a later read
  3. Current experiment state: which arms ran, on which split, with what n, and
     whether those results are still comparable to anything
  4. Anything deliberately rejected and why (rubric changes, scope cuts, runs not
     performed because a pending change would invalidate them)

Write the files completely. Do not summarise in chat and skip the write.
EOF
)

printf '%s' "$CONTEXT" | "$FIS_PY" -c '
import json, sys
print(json.dumps({
    "systemMessage": "Compaction imminent - flush design decisions to docs/ first.",
    "hookSpecificOutput": {
        "hookEventName": "PreCompact",
        "additionalContext": sys.stdin.read(),
    },
}))
'
