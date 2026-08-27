#!/usr/bin/env bash
# Hermetic environment for the Crexi baseline. SOURCE this, never execute it,
# and never pipe it (a pipe runs it in a subshell and the exports vanish).
#   source rig/env.sh A     # deterministic arm (LLM income extraction OFF)
#   source rig/env.sh B     # AI-on arm
#
# Every value the wholesaling scripts could read is set EXPLICITLY, because for
# those scripts an UNSET var is not a safe default -- _env_value() falls through
# to backend/.env.local, which holds real Supabase URLs.

_arm="${1:-}"
if [[ "$_arm" != "A" && "$_arm" != "B" ]]; then
  echo "usage: source env.sh <A|B>" >&2
  return 1 2>/dev/null || exit 1
fi

# --- resolve the rig root FIRST; everything else derives from it -------------
_src="${BASH_SOURCE[0]:-$0}"
export CREXI_BASELINE_ROOT="$(cd "$(dirname "$_src")/.." >/dev/null 2>&1 && pwd)"
if [[ ! -d "$CREXI_BASELINE_ROOT/rig" ]]; then
  echo "env.sh: could not resolve rig root (got '$CREXI_BASELINE_ROOT')" >&2
  return 1 2>/dev/null || exit 1
fi
export WHOLESALING_REPO="${WHOLESALING_REPO:-$HOME/code/wholesaling}"
export PYTHONPATH="$WHOLESALING_REPO/backend"

# --- work dir: a CWD with NO .env adjacent ----------------------------------
# This is the ONLY thing that actually neutralizes the production R2 photo
# mirror. Exporting R2_* as empty strings does NOT work: Settings sets
# env_ignore_empty=True (settings.py:124), so an empty var reads as UNSET and
# backend/.env supplies R2_BUCKET=media. MEASURED: with empty exports and
# CWD=backend, build_crexi_mirror().enabled was still True.
export CREXI_RIG_WORK="$CREXI_BASELINE_ROOT/runs/work"
mkdir -p "$CREXI_RIG_WORK"
unset R2_ACCOUNT_ID R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_BUCKET R2_PUBLIC_BASE_URL R2_API_TOKEN

# --- local database: BOTH flags land here, so --db prod is equally harmless --
export CREXI_PG_IMAGE="postgres@sha256:67f41722b7a8cbdb868a44a4995c846eddfdc2973bccb291ce937dce88ad5675"
export CREXI_PG_CONTAINER="crexi-baseline-pg"
export CREXI_PG_PORT="55432"
export DATABASE_URL="postgresql+psycopg://wholesaling:wholesaling@127.0.0.1:${CREXI_PG_PORT}/wholesaling"
export DEV_DATABASE_URL="$DATABASE_URL"
# Host+port are NOT proof of locality on this machine: an ssh tunnel listens on
# 127.0.0.1:25432 and forwards to a remote postgres. preflight.py additionally
# requires this in-DB sentinel row.
export CREXI_RIG_SENTINEL="crexi-baseline-rig"

# --- non-empty dummies: block every backend/.env.local fallback -------------
# _env_value() uses `if os.environ.get(name):` -- a FALSY value falls through to
# the dotenv. These must be non-empty to be effective.
export INTEGRATION_SECRET_KEY="rig-not-a-key"
export GH_DISPATCH_TOKEN="rig-disabled"
export OPENROUTER_API_KEY="rig-disabled"
export VERCEL_TOKEN="rig-disabled"
: "${CREXI_TOKEN:=rig-replay-no-token}" ; export CREXI_TOKEN

# --- send paths inert --------------------------------------------------------
export KILL_SWITCH=true
export FORCE_DRY_RUN_SENDS=true

# --- AI arm ------------------------------------------------------------------
export CREXI_BASELINE_ARM="$_arm"
if [[ "$_arm" == "A" ]]; then
  export AI_LOCAL_TRANSPORTS_DISABLED=true AI_CLAUDE_SDK_DISABLED=true AI_CODEX_DISABLED=true
else
  unset AI_LOCAL_TRANSPORTS_DISABLED AI_CLAUDE_SDK_DISABLED AI_CODEX_DISABLED
fi

# --- keep the experiment lane's z.ai routing OUT of the product's AI calls ---
unset ANTHROPIC_BASE_URL ANTHROPIC_AUTH_TOKEN

# --- determinism -------------------------------------------------------------
export TZ=UTC PYTHONUTF8=1 PYTHONHASHSEED=0

echo "crexi-baseline: arm=$_arm  db=127.0.0.1:${CREXI_PG_PORT}  root=$CREXI_BASELINE_ROOT"
