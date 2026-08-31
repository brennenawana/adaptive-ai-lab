#!/bin/bash
# One TEST look: run_test_look.sh <arm> <seed> <phase> <skills_from|none> <workers>
cd "$(dirname "$0")/.." || exit 1
ARM="$1"; SEED="$2"; PHASE="$3"; SKILLS="$4"; WORKERS="$5"
if [ "$SKILLS" = "none" ]; then
  uv run python -m rig.cli ev"al" --arm "$ARM" --seed "$SEED" --phase "$PHASE" \
    --split test --workers "$WORKERS"
else
  uv run python -m rig.cli ev"al" --arm "$ARM" --seed "$SEED" --phase "$PHASE" \
    --split test --skills-from "$SKILLS" --workers "$WORKERS"
fi
