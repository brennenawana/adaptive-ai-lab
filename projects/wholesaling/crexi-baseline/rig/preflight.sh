#!/usr/bin/env bash
# Thin wrapper: always run the real (outcome-asserting) preflight from a CWD
# with no .env adjacent. The previous pure-shell version FALSELY PASSED on R2
# (see preflight.py's docstring) and is retired as preflight.sh.RETIRED.
set -euo pipefail
: "${CREXI_RIG_WORK:?source rig/env.sh first}"
: "${CREXI_BASELINE_ROOT:?source rig/env.sh first}"
cd "$CREXI_RIG_WORK"
exec "${WHOLESALING_REPO:-$HOME/code/wholesaling}/backend/.venv/bin/python" \
     "$CREXI_BASELINE_ROOT/rig/preflight.py"
