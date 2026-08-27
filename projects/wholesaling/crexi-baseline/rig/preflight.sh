#!/usr/bin/env bash
# FAIL-CLOSED safety preflight. Nothing in this epic runs without it passing.
#
# The hazard being guarded (verified in the wholesaling repo):
#   * crexi_ingest.py:55-72 / crexi_value_route.py:126-132 resolve their OWN db url:
#       --db prod -> DATABASE_URL,  --db dev -> DEV_DATABASE_URL
#     read from os.environ FIRST, then falling back to parsing backend/.env.local,
#     which on this machine holds REAL prod + dev Supabase URLs.
#   * backend/.env holds R2_* creds and pydantic-settings loads .env relative to CWD,
#     so an --apply ingest would upload to the PRODUCTION R2 bucket.
#
# Therefore: BOTH url vars must be local, and every R2_* must be empty, in the
# environment we hand to the scripts. Anything unexpected aborts.
set -uo pipefail

fail=0
ok()   { printf '  \033[32mPASS\033[0m  %s\n' "$1"; }
bad()  { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; fail=1; }

echo "=== Crexi baseline preflight ==="

# 1. Both DB urls must be set AND local. An unset var is a FAILURE, not a pass,
#    because unset is exactly what triggers the .env.local fallback to prod.
for var in DATABASE_URL DEV_DATABASE_URL; do
  val="${!var-}"
  if [[ -z "$val" ]]; then
    bad "$var is UNSET (would fall back to backend/.env.local -> prod/dev Supabase)"
  elif [[ "$val" == *"supabase"* || "$val" == *"pooler."* ]]; then
    bad "$var points at Supabase: ${val%%@*}@..."
  elif [[ "$val" != *"localhost"* && "$val" != *"127.0.0.1"* ]]; then
    bad "$var is not local: ${val%%@*}@..."
  else
    ok "$var is local"
  fi
done

# 2. Every R2_* must be present-and-empty (present so nothing falls through to .env).
r2_bad=0
for var in R2_ACCOUNT_ID R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_BUCKET R2_PUBLIC_BASE_URL R2_API_TOKEN; do
  if [[ -z "${!var-}" && -n "${!var+set}" ]]; then continue; fi
  if [[ -n "${!var-}" ]]; then bad "$var is NON-EMPTY (photo mirror would upload to prod R2)"; r2_bad=1
  else bad "$var is unset (must be exported empty so .env cannot supply it)"; r2_bad=1; fi
done
[[ $r2_bad -eq 0 ]] && ok "all R2_* exported and empty (photo mirror inert)"

# 3. The local Postgres must actually be reachable, or a 'local' url is a lie.
if command -v psql >/dev/null 2>&1; then
  if psql "${DATABASE_URL/postgresql+psycopg/postgresql}" -c 'select 1' >/dev/null 2>&1; then
    ok "local Postgres reachable"
  else
    bad "local Postgres NOT reachable at DATABASE_URL"
  fi
else
  bad "psql not found; cannot verify the local database"
fi

# 4. Declare the AI arm explicitly. Silence here means the LLM income-extraction
#    tier fires unannounced (ai/routes.py:29-34 -- no flag, no budget by design).
case "${CREXI_BASELINE_ARM-}" in
  A) [[ "${AI_LOCAL_TRANSPORTS_DISABLED-}" == "true" ]] \
       && ok "Arm A (deterministic): local AI transports disabled" \
       || bad "Arm A declared but AI_LOCAL_TRANSPORTS_DISABLED != true" ;;
  B) [[ "${AI_LOCAL_TRANSPORTS_DISABLED-}" == "true" ]] \
       && bad "Arm B declared but local AI transports are disabled" \
       || ok "Arm B (AI-on): LLM income extraction live" ;;
  *) bad "CREXI_BASELINE_ARM must be A or B (got '${CREXI_BASELINE_ARM-unset}')" ;;
esac

# 5. Never let the experiment lane's z.ai routing leak into the product's own AI calls.
if [[ -n "${ANTHROPIC_BASE_URL-}" ]]; then
  bad "ANTHROPIC_BASE_URL is set ($ANTHROPIC_BASE_URL) -- the z.ai lane must not reach the pipeline's AI calls"
else
  ok "ANTHROPIC_BASE_URL unset (product AI path unaltered)"
fi

echo
if [[ $fail -ne 0 ]]; then
  echo "PREFLIGHT FAILED -- refusing to run." >&2
  exit 1
fi
echo "PREFLIGHT PASSED"
