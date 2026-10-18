#!/usr/bin/env bash
# NVIDIA A100 setup + optional overnight study launch.
# Usage:
#   bash run_a100.sh            # install deps, start Ollama, pull models
#   bash run_a100.sh --trial    # then 1-round Star smoke test
#   bash run_a100.sh --full     # then nohup all 5 experiments × 3 topologies

set -euo pipefail
cd "$(dirname "$0")"

export PYTHONUNBUFFERED=1
export OLLAMA_FLASH_ATTENTION="${OLLAMA_FLASH_ATTENTION:-1}"
export OLLAMA_MAX_LOADED_MODELS="${OLLAMA_MAX_LOADED_MODELS:-2}"
export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-30m}"
export OLLAMA_NUM_CTX="${OLLAMA_NUM_CTX:-32768}"
export OLLAMA_TIMEOUT_S="${OLLAMA_TIMEOUT_S:-240}"

echo "=== NVIDIA A100 check ==="
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader
else
  echo "nvidia-smi not found — is this the A100 session?"
fi

echo "=== Python deps ==="
python3 -m pip install -r requirements.txt

echo "=== Ollama ==="
if ! curl -sf "${OLLAMA_HOST:-http://localhost:11434}/api/tags" >/dev/null 2>&1; then
  echo "Starting ollama serve in the background..."
  ollama serve >ollama_serve.log 2>&1 &
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if curl -sf "${OLLAMA_HOST:-http://localhost:11434}/api/tags" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

ollama pull qwen3.5:4b
ollama pull qwen3.5:9b
ollama list

mode="${1:-}"
if [[ "$mode" == "--trial" ]]; then
  echo "=== Trial: exp1, Star, 1 round ==="
  python3 main.py --trial
elif [[ "$mode" == "--full" ]]; then
  echo "=== Full study in background → full_study.log ==="
  nohup python3 main.py > full_study.log 2>&1 &
  echo "PID $!  —  tail -f full_study.log"
else
  echo
  echo "Ready. On this A100 box:"
  echo "  python3 main.py --trial"
  echo "  nohup python3 main.py > full_study.log 2>&1 &"
fi
