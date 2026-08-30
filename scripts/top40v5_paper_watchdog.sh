#!/usr/bin/env bash
# Bring the data up to the latest closed boundary, then tick the desks.
#
# Two data steps, in order, because they cover different ranges:
#
#   1. live append  -- REST klines from the local proxy + funding direct from Binance, filling from
#      the snapshot's last bar to the latest closed 8h boundary. This is what keeps the desks
#      current; the archive path structurally cannot, because Binance publishes a month's ZIPs only
#      after that month closes.
#   2. archive refresh -- rebuilds from checksum-verified monthly archives when a new month has
#      published, upgrading the provenance of rows the live path already filled in.
#
# Both are no-ops when there is nothing to do. The engine declines when another holds
# paper-top40v5/engine.lock, so an overlapping start costs nothing, and nothing runs at all before
# launch.json.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ ! -f paper-top40v5/launch.json ]; then
  echo "not launched; nothing to do"
  exit 0
fi

mkdir -p logs

# Data first: a tick against stale data publishes stale rows, and the DATA-STALE clamp means it
# would do so quietly rather than failing.
PYTHONUNBUFFERED=1 uv run python scripts/top40v5_live_append.py --workers 4 \
  >> logs/v5_live_append.log 2>&1 \
  || echo "live append failed; ticking against whatever is on disk" >> logs/v5_live_append.log

PYTHONUNBUFFERED=1 uv run python scripts/top40v5_paper_engine.py --once >> logs/v5_paper_tick.log 2>&1
echo "tick complete"
