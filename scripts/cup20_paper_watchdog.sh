#!/usr/bin/env bash
# Restart the CUP-20 paper desk if, and only if, it is not already running.
#
# The engine's own fcntl lock is the singleton signal, not a pidfile: `flock` lives on an open file
# description and the kernel releases it the instant the holder dies, so "can I take engine.lock?"
# answers "is an engine alive?" without trusting a number written in a file by a process that may
# have crashed. If the lock is held, this script starts nothing. A second watchdog racing the first
# is excluded by its own lock.
#
# Every decision is logged, because a watchdog that silently does nothing and a watchdog that is
# broken look identical from outside.
set -euo pipefail

ROOT=/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top20-low-dd
DESK_DIR="$ROOT/paper-cup20"
LOG_DIR="$ROOT/logs"
WATCHDOG_LOG="$LOG_DIR/cup20_paper_watchdog.log"
ENGINE_LOG="$LOG_DIR/cup20_paper.log"
UV=/home/roberto/.local/bin/uv

mkdir -p "$DESK_DIR" "$LOG_DIR"
test -x "$UV"

log() {
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [cup20-watchdog] $*" >>"$WATCHDOG_LOG"
}

exec 9>"$DESK_DIR/watchdog.lock"
if ! flock -n 9; then
    log "another watchdog holds the watchdog lock; did nothing"
    exit 0
fi

# A held engine lock is an alive engine. Nothing to do, and starting a second one would be the
# failure this script exists to prevent.
if ! flock -n "$DESK_DIR/engine.lock" -c true; then
    log "engine already running (engine.lock is held); did nothing"
    exit 0
fi

cd "$ROOT"
PYTHONUNBUFFERED=1 nohup "$UV" run python run_cup20_paper.py \
    </dev/null \
    >>"$ENGINE_LOG" 2>&1 9>&- &
log "engine was not running; started pid $! (paper only, no orders), logging to $ENGINE_LOG"
