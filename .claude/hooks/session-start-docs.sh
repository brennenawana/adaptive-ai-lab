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
Adaptive AI Lab. The product is the Adaptive AI Systems Playbook (playbook/);
research/ holds its generic evidence; docs/ is lab governance; projects/fis/ is
the first project implementation (the Fintech Integration Sandbox) and the source
of the playbook's real case studies. FIS is a project in this lab, not the repo's
identity.

Repo location depends on where this session was started:
  from WSL:     ~/projects/adaptive-ai-lab        (preferred - native tooling)
  from Windows: \\wsl.localhost\Ubuntu-24.04\home\wall\projects\adaptive-ai-lab

READ FIRST, in this order:
  README.md                    the lab front page and navigation
  docs/README.md               governance index: authority model, repository model
  projects/fis/README.md       the FIS index: reading order, what is CURRENT vs
                               FROZEN vs HISTORICAL, and the path map for
                               pre-restructuring citations. Start here for any
                               FIS work.
  projects/fis/PROJECT_PLAN.md project strategy + sequencing authority
  projects/fis/PLAYBOOK_ADAPTATION.md
                               the FIS methodology (normative for FIS; "playbook
                               §N" citations in FIS code bind here)
  projects/fis/HANDOFF.md      operational state, environment gotchas, harness-bug
                               history, verification commands
  projects/fis/architecture.md component map, ports, event topology, and the
                               NORMATIVE event-driven requirement
  projects/fis/task-ontology.md  case categories, root causes, cause->action table
  projects/fis/clean-room-boundary.md  what must never enter the sandbox
  projects/fis/experiment-log.md results, and their comparability status

On conflict (FIS): PROJECT_PLAN > PLAYBOOK_ADAPTATION/contract-template > HANDOFF >
historical plans. Historical FINAL REPORTS stay authoritative for the facts of
their own experiments but never override the current plan. Generic playbook/ and
project adaptation each govern their own domain. Milestone transitions require
owner acceptance in projects/fis/OWNER_DECISIONS.md; repository-level decisions in
docs/LAB_DECISIONS.md. M0 and M-STAT are executed and accepted; the next
owner-level task is the Suite-v4 trigger review
(projects/fis/SUITE_V4_TRIGGER_REVIEW_PROCEDURE.md).

Reference designs (projects/fis/reference/ - consult, don't execute); executed
launch plans (projects/fis/history/superseded/ - never instructions). Historical
documents cite pre-restructuring paths (docs/..., docs/current/...) - do NOT "fix"
those citations; the path map in projects/fis/README.md resolves them.

Standing environment facts:
  - FIS operations run FROM projects/fis/ (its Makefile, .venv, .env live there).
  - Ports: 5433 FIS Postgres, 4222 NATS, 8082 local model.
    5432 and 6379 belong to a separate pre-existing project - do not touch.
    8080/8081 belong to Bonsai and a Qwen3.8-27B server - also not ours.
  - The ground_truth schema is the eval answer key. The fis_tools DB role holds
    no grant on it. Never route a model-facing tool there.
  - FIS clean-tree/provenance checks are scoped to projects/fis/ (owner decision
    D3): edits elsewhere in the lab do not dirty FIS runs; anything modified or
    untracked inside that tree still refuses fail-closed.
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
