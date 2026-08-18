#!/usr/bin/env bash
# Restart the exact-replay Team-02 paper engine only when its singleton lock is free.
set -euo pipefail

ROOT=/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top50
PAPER_DIR="$ROOT/paper-cup50/team-02"
LOG_DIR="$ROOT/logs"
ENGINE_LOG="$LOG_DIR/cup50_team02_paper.log"
WATCHDOG_LOG="$LOG_DIR/cup50_team02_watchdog.log"
PYTHON="$ROOT/.venv/bin/python"

mkdir -p "$PAPER_DIR" "$LOG_DIR"
test -x "$PYTHON"

log() {
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [cup50-team02-watchdog] $*" >>"$WATCHDOG_LOG"
}

exec 9>"$PAPER_DIR/watchdog.lock"
if ! flock -n 9; then
    log "another watchdog holds the watchdog lock; did nothing"
    exit 0
fi

if ! flock -n "$PAPER_DIR/engine.lock" -c true; then
    log "engine already running; did nothing"
    exit 0
fi

cd "$ROOT"
PYTHONUNBUFFERED=1 nohup "$PYTHON" run_cup50_team02_paper.py \
    </dev/null >>"$ENGINE_LOG" 2>&1 9>&- &
log "engine was not running; started pid $! (paper only, no orders)"
