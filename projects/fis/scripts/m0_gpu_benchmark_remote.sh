#!/usr/bin/env bash
# M0 WP-E — rented-GPU decode benchmark (NEXT_STEP_M0.md § 6-E). SELF-CONTAINED:
# run this ON the rented box (RunPod Secure/Community CUDA image or equivalent),
# once on a 3090 and once on a 5090. ~$2 per GPU at 2026-08 spot prices.
#
#   bash m0_gpu_benchmark_remote.sh /workspace/out
#
# What it does, all pinned:
#   1. clones llama.cpp at the FROZEN runtime commit (b1-9b05354) and builds for the
#      local CUDA arch (a rebuild is required per arch; binary digests are recorded —
#      the runtime LINEAGE is pinned, the binaries are per-arch by necessity);
#   2. downloads the pinned artifact unsloth/Qwen3.8-27B-GGUF Q3_K_M and REFUSES to
#      continue unless its sha256 is exactly the registered
#      7f3b845b563888ec3abc269474cf744bf703a7ce8766dbb7f696c63975facfd7;
#   3. runs llama-bench at the R6-representative operating point — single sequence,
#      ~3.6k-token prompt, long generation, flash-attn on, q8_0 KV, full offload —
#      3 repetitions (the M0 requirement), JSON out;
#   4. writes <out>/m0_bench_<gpu>.json + environment/digest records.
#
# SPLIT FIREWALL: nothing in this script touches FIS data. The benchmark prompt is
# llama-bench's synthetic token stream — no TEST (or any) corpus content ever
# reaches the rented host.
set -euo pipefail

OUT="${1:?usage: m0_gpu_benchmark_remote.sh <out-dir>}"
mkdir -p "$OUT"

LLAMA_COMMIT="9b05354ec6fb58b4e665e9a39ebc40285c015638"   # b1-9b05354, the frozen lineage
MODEL_REPO="unsloth/Qwen3.8-27B-GGUF"
MODEL_FILE="Qwen3.8-27B-Q3_K_M.gguf"
MODEL_SHA="7f3b845b563888ec3abc269474cf744bf703a7ce8766dbb7f696c63975facfd7"

GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1 | tr ' ' '_' )"
echo "== GPU: $GPU_NAME"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv > "$OUT/gpu.csv"

echo "== build llama.cpp @ $LLAMA_COMMIT"
if [ ! -d llama.cpp ]; then git clone https://github.com/ggml-org/llama.cpp; fi
cd llama.cpp && git fetch --all --quiet && git checkout -q "$LLAMA_COMMIT"
cmake -B build-cuda -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build build-cuda -j "$(nproc)" --target llama-bench llama-server >/dev/null
cd ..
sha256sum llama.cpp/build-cuda/bin/llama-bench llama.cpp/build-cuda/bin/llama-server \
  llama.cpp/build-cuda/bin/lib*.so* > "$OUT/binary_digests.txt" 2>/dev/null || \
  sha256sum llama.cpp/build-cuda/bin/llama-bench llama.cpp/build-cuda/bin/llama-server > "$OUT/binary_digests.txt"

echo "== fetch + verify artifact"
if [ ! -f "$MODEL_FILE" ]; then
  pip -q install "huggingface_hub[cli]" >/dev/null
  hf download "$MODEL_REPO" "$MODEL_FILE" --local-dir . 2>/dev/null \
    || huggingface-cli download "$MODEL_REPO" "$MODEL_FILE" --local-dir .
fi
GOT="$(sha256sum "$MODEL_FILE" | cut -d' ' -f1)"
if [ "$GOT" != "$MODEL_SHA" ]; then
  echo "!! artifact sha256 $GOT != registered $MODEL_SHA — refusing to benchmark a different file"
  exit 1
fi
echo "artifact sha256 verified: $GOT"

echo "== llama-bench (R6-representative: 3584-token prompt, long generation, 3 reps)"
./llama.cpp/build-cuda/bin/llama-bench \
  -m "$MODEL_FILE" \
  -fa 1 -ctk q8_0 -ctv q8_0 -ngl 99 \
  -p 3584 -n 1024 -pg 3584,8192 \
  -r 3 -o json | tee "$OUT/m0_bench_${GPU_NAME}.json"

{ echo "commit=$LLAMA_COMMIT"; echo "model_sha256=$GOT"; date -u +"%Y-%m-%dT%H:%M:%SZ"; \
  nvcc --version | tail -1 || true; } > "$OUT/env.txt"
echo "== done. Collect $OUT/ and feed it to scripts/m0_gpu_benchmark.py assemble"
