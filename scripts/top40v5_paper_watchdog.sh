#!/usr/bin/env bash
# Refresh the forward snapshot if it can be, then tick the desks.
#
# Safe to call on a schedule. The refresh is a no-op when the snapshot already reaches the last
# complete month -- which is the furthest the canonical archive-based builder can go -- and the
# engine declines when another holds paper-top40v5/engine.lock, so an overlapping start costs
# nothing. Nothing runs at all before launch.json.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ ! -f paper-top40v5/launch.json ]; then
  echo "not launched; nothing to do"
  exit 0
fi

mkdir -p logs

# Data first: a tick against stale data publishes stale rows, and the engine's DATA-STALE clamp
# means it would do so quietly rather than failing.
PYTHONUNBUFFERED=1 uv run python scripts/top40v5_refresh_forward.py >> logs/v5_refresh.log 2>&1 \
  || echo "refresh failed; ticking against whatever data is already on disk" >> logs/v5_refresh.log

PYTHONUNBUFFERED=1 uv run python scripts/top40v5_paper_engine.py --once >> logs/v5_paper_tick.log 2>&1
echo "tick complete"
