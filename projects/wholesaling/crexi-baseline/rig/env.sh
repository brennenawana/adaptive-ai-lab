#!/usr/bin/env bash
# Hermetic environment for the Crexi baseline. SOURCE this, never execute it.
#   source rig/env.sh A     # deterministic arm
#   source rig/env.sh B     # AI-on arm
#
# Everything the wholesaling scripts could read is set EXPLICITLY here, because
# an unset var is what makes them fall back to backend/.env.local (real prod).

_arm="${1:-}"
if [[ "$_arm" != "A" && "$_arm" != "B" ]]; then
  echo "usage: source env.sh <A|B>" >&2
  return 1 2>/dev/null || exit 1
fi

# --- local database (BOTH vars, so --db prod and --db dev are equally harmless) ---
export CREXI_PG_IMAGE="postgres@sha256:67f41722b7a8cbdb868a44a4995c846eddfdc2973bccb291ce937dce88ad5675"
export CREXI_PG_CONTAINER="crexi-baseline-pg"
export CREXI_PG_PORT="55432"
export DATABASE_URL="postgresql+psycopg://wholesaling:wholesaling@localhost:${CREXI_PG_PORT}/wholesaling"
export DEV_DATABASE_URL="$DATABASE_URL"

# --- neutralize the production R2 photo mirror (exported EMPTY, not unset) ---
export R2_ACCOUNT_ID="" R2_ACCESS_KEY_ID="" R2_SECRET_ACCESS_KEY=""
export R2_BUCKET="" R2_PUBLIC_BASE_URL="" R2_API_TOKEN=""

# --- declare the arm; Arm A silences the unflagged LLM income-extraction tier ---
export CREXI_BASELINE_ARM="$_arm"
if [[ "$_arm" == "A" ]]; then
  export AI_LOCAL_TRANSPORTS_DISABLED="true"
else
  unset AI_LOCAL_TRANSPORTS_DISABLED
fi

# --- keep the experiment lane's z.ai routing OUT of the product's AI calls ---
unset ANTHROPIC_BASE_URL ANTHROPIC_AUTH_TOKEN

# --- run identity ---
export CREXI_BASELINE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONUTF8=1

echo "crexi-baseline env: arm=$_arm db=localhost:${CREXI_PG_PORT} r2=inert"
