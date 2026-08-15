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
  from WSL:     ~/fintech-integration-sandbox        (preferred - native tooling)
  from Windows: \\wsl.localhost\Ubuntu-24.04\home\wall\fintech-integration-sandbox

READ FIRST, in this order:
  docs/HANDOFF.md              current state, the exact next task, and what was
                               deliberately NOT done. Start here.
  docs/architecture.md         component map, ports, event topology, and the
                               NORMATIVE event-driven requirement
  docs/task-ontology.md        case categories, root causes, cause->action table
  docs/clean-room-boundary.md  what must never enter this sandbox
  docs/experiment-log.md       results, and their comparability status

SOURCE PLAN (authoritative, supersedes the derived docs above on any conflict).
Large, so consult rather than read end-to-end - but read the relevant section in
full before planning a new phase or experiment arm:
  docs/Company_Intelligence_Platform_Canonical_Architecture_v1.html
      the reference design: two planes, five memory types, specialist definition,
      Discovery Controller failure taxonomy, specialization ladder (training LAST),
      implementation phases 0-9
  docs/Company_Intelligence_Platform_MSI_Experimentation_and_Fintech_Sandbox_Guide.html
      this project: FIS scope, 12 scenario classes, tool contracts, investigator
      output contract, eval suite, experiment matrix E0-E8, six-week build plan,
      decision gates before adding complexity
  docs/Company_Intelligence_Platform_MacBook_Pro_Hybrid_Deployment_Guide.html
      a DIFFERENT machine (24GB M4 Pro Mac). Not this workstation - ignore unless
      the work is explicitly about that deployment.

The .md docs are derived from the HTML plan plus what was learned building it.
Where they disagree, the HTML is the plan and the .md is the record of deviation -
check experiment-log.md and architecture.md's "Deviations" table before assuming
a mismatch is a bug.

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
