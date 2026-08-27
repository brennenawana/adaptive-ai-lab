#!/usr/bin/env bash
# The ONLY sanctioned way to invoke a wholesaling script in this rig.
#
# Why a wrapper: the preflight and the run must share one CWD, or the gate
# validates an environment the run never uses. That exact mismatch happened --
# preflight passed from runs/work (no .env -> R2 off) while the script ran from
# backend/ (.env present -> "photo mirror: ON (R2)"). Only dry-run saved it.
# Here the preflight executes in the same directory the command will, so a PASS
# is a statement about the run that is actually about to happen.
#
#   ./rig/run.sh -m scripts.crexi_ingest --states FL --db prod --apply
set -euo pipefail

: "${CREXI_RIG_WORK:?source rig/env.sh <A|B> first}"
: "${CREXI_BASELINE_ROOT:?source rig/env.sh <A|B> first}"
: "${WHOLESALING_REPO:?source rig/env.sh <A|B> first}"
PY="$WHOLESALING_REPO/backend/.venv/bin/python"

cd "$CREXI_RIG_WORK"          # <-- the guarded CWD; everything below inherits it

echo "--- preflight (same cwd as the run) ---"
"$PY" "$CREXI_BASELINE_ROOT/rig/preflight.py" || {
  echo "run.sh: preflight failed -- refusing to execute" >&2; exit 1; }

echo "--- exec: python $* ---"
echo "    cwd=$(pwd)  arm=${CREXI_BASELINE_ARM}  $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
exec "$PY" "$@"
