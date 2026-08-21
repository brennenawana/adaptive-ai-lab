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

In the Adaptive AI Lab repo:
  projects/fis/architecture.md         FIS component map, ports, event topology
  projects/fis/task-ontology.md        case categories, root causes, cause->action table
  projects/fis/clean-room-boundary.md  what may and may not enter the sandbox
  projects/fis/experiment-log.md       results so far, AND decisions deliberately NOT taken
  projects/fis/HANDOFF.md              operational state, gotchas, environment facts
  playbook/ + docs/playbook-development/EVIDENCE_MAP.md
                                       if the session changed generic methodology
  docs/LAB_DECISIONS.md                if the session moved repository/lab state

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
    "systemMessage": "Compaction imminent - flush design decisions to the durable docs first.",
    "hookSpecificOutput": {
        "hookEventName": "PreCompact",
        "additionalContext": sys.stdin.read(),
    },
}))
'
