#!/usr/bin/env bash
# Serve NeMo Switchyard on 127.0.0.1:4000 with the FIS route bundle.
#
# Usage: infra/switchyard/serve.sh [routes.yaml] [port]
#
# Runs in the background with logs in the scratch dir the Makefile passes via
# FIS_SWITCHYARD_LOG (default: /tmp/fis-switchyard.log). The routing log
# (`--routing-log-file`) is one JSONL line per request — served model, upstream
# model, token counts — and is the gateway-side record R1 reconciles against the
# FIS trajectories.
#
# Deliberately NOT exporting the whole .env: Switchyard reads $OPENAI_API_KEY as a
# fallback when a target has no api_key, and the FIS route bundle sets api_key ""
# precisely so nothing from the shell can leak into the llama.cpp request.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
ROUTES="${1:-$HERE/routes.yaml}"
PORT="${2:-4000}"
LOG="${FIS_SWITCHYARD_LOG:-/tmp/fis-switchyard.log}"
RLOG="${FIS_SWITCHYARD_ROUTING_LOG:-/tmp/fis-switchyard-routing.jsonl}"
BIN="$ROOT/.venv/bin/switchyard"

[ -x "$BIN" ] || { echo "!! $BIN not found — uv pip install --python .venv/bin/python 'nemo-switchyard[cli,server]==0.2.0'"; exit 1; }
[ -f "$ROUTES" ] || { echo "!! route bundle not found: $ROUTES"; exit 1; }

# 4000 must be ours. 8080/8081 (Bonsai, Qwen-27B) and 5432/6379 are other projects.
if curl -s --max-time 2 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
  if pgrep -f "switchyard serve .*--port $PORT" >/dev/null; then
    echo "already running on $PORT (restarting)"
    pkill -f "switchyard serve .*--port $PORT" && sleep 1
  else
    echo "!! something else answers on $PORT — refusing to start"; exit 1
  fi
fi

nohup "$BIN" serve --routing-profiles "$ROUTES" --host 127.0.0.1 --port "$PORT" \
  --routing-log-file "$RLOG" >"$LOG" 2>&1 &

for _ in $(seq 1 30); do
  if curl -s --max-time 2 "http://127.0.0.1:$PORT/health" 2>/dev/null | grep -q '"ok"'; then
    ROUTES_UP=$(curl -s --max-time 2 "http://127.0.0.1:$PORT/v1/models" | python3 -c 'import sys,json; print(",".join(m["id"] for m in json.load(sys.stdin)["data"]))' 2>/dev/null)
    echo "UP switchyard=$("$BIN" --version 2>/dev/null | awk '{print $2}') port=$PORT routes=$ROUTES_UP log=$LOG routing_log=$RLOG"
    exit 0
  fi
  sleep 1
done
echo "!! switchyard did not come up; tail of $LOG:"; tail -20 "$LOG"; exit 1
