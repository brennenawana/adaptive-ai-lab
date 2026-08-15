#!/usr/bin/env bash
# Serve the FIS local specialist tier on port 8082, OpenAI-compatible.
#
# Port choice is deliberate — this machine already uses:
#   8080 = Bonsai        8081 = Qwen3.8-27B server        5433/4222 = FIS infra
# Nothing here touches those.
#
# Usage: ./serve-local-model.sh [model.gguf] [ctx] [port]
set -u

BIN="$HOME/llama.cpp-upstream/build-cuda/bin/llama-server"
MODEL="${1:-$HOME/models/Qwen3-8B-Q4_K_M.gguf}"
CTX="${2:-16384}"
PORT="${3:-8082}"
LOG=/tmp/fis-local-model.log

# The CUDA runtime libs live in the bonsai-eval env, not on the default path.
export LD_LIBRARY_PATH="$HOME/bonsai-eval/cudaenv/lib:${LD_LIBRARY_PATH:-}"

[ -f "$MODEL" ] || { echo "!! model not found: $MODEL"; exit 1; }
[ -x "$BIN" ]   || { echo "!! llama-server not found: $BIN"; exit 1; }

# Match the actual server process, not this script's own command line.
pkill -f "llama-serve[r] .*--port $PORT" 2>/dev/null && sleep 2

# Flags that matter for FIS, and why:
#   --jinja          tool-calling via the model's own chat template. Without it the
#                    investigator cannot emit tool calls at all.
#   -ngl 99          all layers on GPU; an 8B Q4 fits in ~5GB of the ~10.7GB free.
#   --flash-attn     lower KV-cache cost per token.
#   --cache-type-*   q8_0 KV roughly halves cache VRAM vs f16 — the difference
#                    between a usable context length on a 16GB card and not.
#   --parallel 1     eval determinism. Concurrent slots change batching and make
#                    run-to-run comparison noisier than the effect being measured.
setsid nohup "$BIN" \
  -m "$MODEL" \
  --host 127.0.0.1 --port "$PORT" \
  -c "$CTX" -ngl 99 \
  --flash-attn on \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --jinja \
  --parallel 1 \
  --alias fis-local-specialist \
  > "$LOG" 2>&1 </dev/null &

for _ in $(seq 1 100); do
  if curl -s --max-time 2 "http://127.0.0.1:$PORT/health" 2>/dev/null | grep -q '"ok"'; then
    echo "UP  model=$(basename "$MODEL")  ctx=$CTX  port=$PORT"
    exit 0
  fi
  sleep 3
done

echo "!! failed to come up within 5min — tail of $LOG:"
tail -20 "$LOG"
exit 1
