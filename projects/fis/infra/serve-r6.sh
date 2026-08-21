#!/usr/bin/env bash
# Serve one R6 candidate GGUF on its own port, OpenAI-compatible — the R6 execution
# system is (artifact, runtime, server args, generation config), so every material
# server flag is EXPLICIT here and nothing is inherited from a hidden default.
#
# Usage:
#   infra/serve-r6.sh --model FILE --port PORT --alias ALIAS [--ctx N]
#                     [--runtime upstream|prism] [--offload "-ngl 99"|"--fit on"]
#                     [--extra "..."]
#
# The two runtimes:
#   upstream  $FIS_LLAMA_DIR/build-cuda/bin/llama-server        (b1-9b05354; every
#             historical FIS arm; Qwen3.5-9B and Qwen3.8-27B run here)
#   prism     $FIS_PRISM_LLAMA_DIR/build-cuda/bin/llama-server  (PrismML fork,
#             prism-b9596-9fcaed7; the ONLY runtime that reads Ternary Bonsai's
#             Q2_0 blocks — upstream defines the same type id with a different block
#             geometry, see docs/R6_EXPERIMENT_CONTRACT.md § runtime)
#
# Flags shared with the historical arms on purpose (execution-system identity should
# differ only in the intended dimensions): --flash-attn on, q8_0 KV, --jinja,
# --parallel 1 (eval determinism), loopback host. The registry captures the actual
# /proc cmdline afterwards; this script is a launcher, not the record.
set -u

ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.env"
if [ -f "$ENV_FILE" ]; then
  while IFS='=' read -r _key _value; do
    _value="${_value%\"}"; _value="${_value#\"}"
    _value="${_value%\'}"; _value="${_value#\'}"
    [ -z "${!_key:-}" ] && export "$_key=$_value"
  done < <(grep -E '^FIS_[A-Z0-9_]+=' "$ENV_FILE" || true)
fi

FIS_LLAMA_DIR="${FIS_LLAMA_DIR:-$HOME/infra/llama.cpp-upstream}"
FIS_MODELS_DIR="${FIS_MODELS_DIR:-$HOME/infra/models}"
FIS_CUDA_LIB="${FIS_CUDA_LIB:-$HOME/infra/cudaenv/lib}"
FIS_PRISM_LLAMA_DIR="${FIS_PRISM_LLAMA_DIR:-$HOME/archive/bonsai-eval/llama.cpp}"
FIS_PRISM_CUDA_LIB="${FIS_PRISM_CUDA_LIB:-$HOME/archive/bonsai-eval/cudaenv/lib}"

MODEL=""; PORT=""; ALIAS=""; CTX=16384; RUNTIME=upstream; OFFLOAD="-ngl 99"; EXTRA=""
while [ $# -gt 0 ]; do
  case "$1" in
    --model) MODEL="$2"; shift 2;;
    --port) PORT="$2"; shift 2;;
    --alias) ALIAS="$2"; shift 2;;
    --ctx) CTX="$2"; shift 2;;
    --runtime) RUNTIME="$2"; shift 2;;
    --offload) OFFLOAD="$2"; shift 2;;
    --extra) EXTRA="$2"; shift 2;;
    *) echo "!! unknown argument: $1"; exit 2;;
  esac
done
[ -n "$MODEL" ] && [ -n "$PORT" ] && [ -n "$ALIAS" ] || { echo "!! --model, --port and --alias are required"; exit 2; }
case "$MODEL" in /*) ;; *) MODEL="$FIS_MODELS_DIR/$MODEL";; esac

case "$RUNTIME" in
  upstream) BIN="$FIS_LLAMA_DIR/build-cuda/bin/llama-server"; CUDA_LIB="$FIS_CUDA_LIB";;
  prism)    BIN="$FIS_PRISM_LLAMA_DIR/build-cuda/bin/llama-server"; CUDA_LIB="$FIS_PRISM_CUDA_LIB";;
  *) echo "!! --runtime must be upstream or prism"; exit 2;;
esac
# One log file PER SESSION, never truncated by a relaunch (the R6 autopsy lost 8 of
# 11 session logs to the old fixed-name `> $LOG`). The fixed name stays valid as a
# symlink to the current session so callers that copy "the server log" keep working.
LOG="/tmp/fis-r6-${ALIAS}-$(date -u +%Y%m%dT%H%M%SZ)-$$.log"
ln -sfn "$LOG" "/tmp/fis-r6-${ALIAS}.log"

# The build bakes a dead absolute RUNPATH (pre-restructure path + a trailing-colon cwd
# entry), so the binary's OWN directory must come first, then the CUDA runtime that
# matches the build. Putting the fork's bin/ first also stops upstream's libggml from
# shadowing the fork's when both trees are on the machine.
export LD_LIBRARY_PATH="$(dirname "$BIN"):$CUDA_LIB:${LD_LIBRARY_PATH:-}"

[ -f "$MODEL" ] || { echo "!! model not found: $MODEL"; exit 1; }
[ -x "$BIN" ]   || { echo "!! llama-server not found: $BIN"; exit 1; }
[ -d "$CUDA_LIB" ] || echo "!! warning: CUDA lib dir not found: $CUDA_LIB" >&2

if ss -ltn 2>/dev/null | grep -q ":$PORT "; then
  echo "!! port $PORT is already in use — stop that server first (make r6-stop PORT=$PORT)"; exit 1
fi

# shellcheck disable=SC2086
setsid nohup "$BIN" \
  -m "$MODEL" \
  --host 127.0.0.1 --port "$PORT" \
  -c "$CTX" $OFFLOAD \
  --flash-attn on \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --jinja \
  --parallel 1 \
  --alias "$ALIAS" \
  $EXTRA \
  > "$LOG" 2>&1 </dev/null &
PID=$!

for _ in $(seq 1 200); do
  if curl -s --max-time 2 "http://127.0.0.1:$PORT/health" 2>/dev/null | grep -q '"ok"'; then
    echo "UP  runtime=$RUNTIME  model=$(basename "$MODEL")  ctx=$CTX  port=$PORT  alias=$ALIAS  pid=$PID  log=$LOG"
    grep -E "n_gpu_layers|n_cpu_moe|CUDA0 model buffer|CPU model buffer|CUDA_Host model buffer|KV self size|fit:|load_tensors: offloaded" "$LOG" | tail -12
    exit 0
  fi
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "!! server exited during startup — tail of $LOG:"; tail -30 "$LOG"; exit 1
  fi
  sleep 3
done
echo "!! failed to come up within 10min — tail of $LOG:"; tail -30 "$LOG"; exit 1
