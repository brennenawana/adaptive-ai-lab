# Shared interpreter resolver. Sourced by the hook scripts.
#
# Must work on BOTH Windows Git Bash and WSL/Linux, because the project directory
# may be either. Two traps this exists to avoid:
#
#   1. Linux has `python3` but often no `python`.
#   2. Windows has a Microsoft Store STUB at WindowsApps/python3 which `command -v`
#      finds successfully but which prints "Python was not found" and exits non-zero
#      when run. Testing for existence is therefore not enough — the interpreter
#      has to be executed to know it works.
#
# Sets FIS_PY, or emits an empty JSON object and exits 0 if nothing usable exists
# (a hook that fails must not break the session).

FIS_PY=""
for _cand in python3 python py; do
    if command -v "$_cand" >/dev/null 2>&1 && "$_cand" -c "pass" >/dev/null 2>&1; then
        FIS_PY="$_cand"
        break
    fi
done

if [ -z "$FIS_PY" ]; then
    echo '{}'
    exit 0
fi
