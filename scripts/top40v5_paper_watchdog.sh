#!/usr/bin/env bash
# Runs one tick if no engine holds the lock. Safe to call on a schedule: the engine declines to
# start when another holds paper-top40v5/engine.lock, and does nothing at all before launch.json.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ ! -f paper-top40v5/launch.json ]; then
  echo "not launched; nothing to do"
  exit 0
fi

mkdir -p logs
PYTHONUNBUFFERED=1 uv run python scripts/top40v5_paper_engine.py --once >> logs/v5_paper_tick.log 2>&1
echo "tick complete"
