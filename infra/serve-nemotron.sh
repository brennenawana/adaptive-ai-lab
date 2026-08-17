#!/usr/bin/env bash
# Serve the R3 candidate weak arm — NVIDIA Nemotron 3.5 Lightning 30B-A3B — on
# port 8083, OpenAI-compatible, from the SAME llama.cpp build that serves Qwen on 8082.
#
# Usage: ./serve-nemotron.sh [model.gguf] [ctx] [port]
#
# Why a second script rather than a parameter on serve-local-model.sh: the two
# servers are meant to run SIDE BY SIDE (R3 design A — simultaneous endpoints, so
# the Qwen session is never restarted while Nemotron is measured), and their
# placement differs in one deliberate way:
#
#   Qwen3-8B Q4_K_M    -ngl 99            all 5 GB on the GPU
#   Nemotron 30B-A3B   --fit on           dense (Mamba-2 + attention, ~1.7 GB) and as
#                                          many expert layers as fit on the GPU; the
#                                          rest of the 128-expert MoE weights (16 GB
#                                          at IQ4_XS) in system RAM. Every available
#                                          GGUF of this model is >= 18 GB, so a 16 GB
#                                          card cannot hold it whole at any quant.
#
# Everything else that shapes generation is identical to the Qwen server: --jinja,
# --parallel 1, q8_0 KV, flash-attn, ctx 16384. Sampling is set per request by the
# FIS adapter (greedy, seed 42) — same as Qwen — not here.
set -u

ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.env"
if [ -f "$ENV_FILE" ]; then
  while IFS='=' read -r _key _value; do
    _value="${_value%\"}"; _value="${_value#\"}"
    _value="${_value%\'}"; _value="${_value#\'}"
    [ -z "${!_key:-}" ] && export "$_key=$_value"
  done < <(grep -E '^FIS_[A-Z0-9_]+=' "$ENV_FILE" || true)
fi

FIS_LLAMA_DIR="${FIS_LLAMA_DIR:-$HOME/llama.cpp-upstream}"
FIS_MODELS_DIR="${FIS_MODELS_DIR:-$HOME/models}"
FIS_CUDA_LIB="${FIS_CUDA_LIB:-$HOME/bonsai-eval/cudaenv/lib}"

BIN="$FIS_LLAMA_DIR/build-cuda/bin/llama-server"
MODEL="${1:-$FIS_MODELS_DIR/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-IQ4_XS.gguf}"
CTX="${2:-16384}"
PORT="${3:-8083}"
# Leave this much VRAM alone so the Qwen server on 8082 keeps its headroom
# (override with FIS_NEMOTRON_FIT_TARGET_MIB when Nemotron runs alone).
FIT_TARGET="${FIS_NEMOTRON_FIT_TARGET_MIB:-1024}"
LOG=/tmp/fis-nemotron.log

export LD_LIBRARY_PATH="$FIS_CUDA_LIB:$(dirname "$BIN"):${LD_LIBRARY_PATH:-}"
[ -f "$MODEL" ] || { echo "!! model not found: $MODEL"; exit 1; }
[ -x "$BIN" ]   || { echo "!! llama-server not found: $BIN"; exit 1; }

pkill -f "llama-serve[r] .*--port $PORT" 2>/dev/null && sleep 2

setsid nohup "$BIN" \
  -m "$MODEL" \
  --host 127.0.0.1 --port "$PORT" \
  -c "$CTX" \
  --fit on --fit-target "$FIT_TARGET" \
  --flash-attn on \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --jinja \
  --parallel 1 \
  --alias fis-nemotron-lightning \
  > "$LOG" 2>&1 </dev/null &

for _ in $(seq 1 200); do
  if curl -s --max-time 2 "http://127.0.0.1:$PORT/health" 2>/dev/null | grep -q '"ok"'; then
    echo "UP  model=$(basename "$MODEL")  ctx=$CTX  port=$PORT  fit-target=${FIT_TARGET}MiB  log=$LOG"
    grep -E "n_cpu_moe|n_gpu_layers|CUDA0 model buffer|CPU model buffer|CUDA_Host|KV self size|fit:" "$LOG" | tail -12
    exit 0
  fi
  sleep 3
done
echo "!! failed to come up within 10min — tail of $LOG:"; tail -30 "$LOG"; exit 1
