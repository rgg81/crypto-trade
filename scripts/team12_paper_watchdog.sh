#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top12-v2
PAPER_DIR="$ROOT/paper-team12"
LOG_DIR="$ROOT/logs"
UV=/home/roberto/.local/bin/uv

mkdir -p "$PAPER_DIR" "$LOG_DIR"
test -x "$UV"
exec 9>"$PAPER_DIR/watchdog.lock"
flock -n 9 || exit 0

# A held engine lock is the authoritative singleton/liveness signal.
if ! flock -n "$PAPER_DIR/engine.lock" -c true; then
    exit 0
fi

cd "$ROOT"
PYTHONUNBUFFERED=1 nohup "$UV" run python run_team12_paper.py \
    </dev/null \
    >>"$LOG_DIR/team12_paper.log" 2>&1 9>&- &
