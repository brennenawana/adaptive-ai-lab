#!/usr/bin/env bash
# SessionStart: fires on new session, resume, and after compaction.
#
# The other half of the PreCompact hook. PreCompact writes the decisions down;
# this points the fresh context at them. Without it the docs exist but nothing
# prompts a re-read, and the recovered session confidently repeats old mistakes.
cat > /dev/null 2>&1 || true

# shellcheck source=_resolve-python.sh
. "$(dirname "${BASH_SOURCE[0]}")/_resolve-python.sh"

CONTEXT=$(cat <<'EOF'
Fintech Integration Sandbox (FIS).

Repo location depends on where this session was started:
  from WSL:     ~/adaptive-ai-lab        (preferred - native tooling)
  from Windows: \\wsl.localhost\Ubuntu-24.04\home\wall\adaptive-ai-lab

READ FIRST, in this order (docs/README.md is the full index):
  docs/README.md               the documentation index: what is CURRENT, what is
                               HISTORICAL EVIDENCE, what is SUPERSEDED. Start here.
  docs/current/AI_SYSTEMS_LAB_MASTER_PLAN.md
                               program strategy + sequencing authority
  docs/current/NEXT_STEP_M0.md the single authorized next task
  docs/current/EXPERIMENTAL_AI_SYSTEMS_PLAYBOOK.md
                               the experimental methodology (normative)
  docs/HANDOFF.md              operational state, environment gotchas, harness-bug
                               history, verification commands
  docs/architecture.md         component map, ports, event topology, and the
                               NORMATIVE event-driven requirement
  docs/task-ontology.md        case categories, root causes, cause->action table
  docs/clean-room-boundary.md  what must never enter this sandbox
  docs/experiment-log.md       results, and their comparability status

On conflict: master plan > next-step plan > playbook/contract-template > HANDOFF >
historical plans. Historical FINAL REPORTS stay authoritative for the facts of
their own experiments but never override the current plan.

REFERENCE DESIGNS (docs/reference/ - consult, don't execute): the Canonical
Architecture HTML (two planes, five memory types, specialization ladder), the MSI
FIS spec HTML (12 scenario classes, tool contracts; its E0-E8 matrix is closed),
the MacBook guide (a DIFFERENT machine - ignore), and the deferred H0-H3/D0
roadmaps. docs/superseded/ holds executed launch plans - never instructions.

Standing environment facts:
  - Ports: 5433 FIS Postgres, 4222 NATS, 8082 local model.
    5432 and 6379 belong to a separate pre-existing project - do not touch.
    8080/8081 belong to Bonsai and a Qwen3.8-27B server - also not ours.
  - The ground_truth schema is the eval answer key. The fis_tools DB role holds
    no grant on it. Never route a model-facing tool there.
  - Sudo is passwordless in WSL. Windows sudo.exe is a different program and
    has no effect on WSL.
  - If running from Windows, WSL commands must be written to a script file first:
    inline $VARIABLES are mangled by the interop layer.
EOF
)

printf '%s' "$CONTEXT" | "$FIS_PY" -c '
import json, sys
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": sys.stdin.read(),
    },
}))
'
