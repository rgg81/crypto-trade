#!/usr/bin/env bash
# Restart the four-desk CUP-50 v2 paper engine only when its singleton lock is free.
#
# ROOT is resolved from this script's own location rather than hard-coded. CUP-50's watchdog
# carried an absolute path to a different worktree, which is the kind of line that keeps working
# right up until someone copies the file.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER_ROOT="$ROOT/paper-cup50v2"
LOG_DIR="$ROOT/logs"
ENGINE_LOG="$LOG_DIR/cup50v2_paper.log"
WATCHDOG_LOG="$LOG_DIR/cup50v2_watchdog.log"
PYTHON="$ROOT/.venv/bin/python"
LAUNCH_FILE="$PAPER_ROOT/launch.json"

mkdir -p "$PAPER_ROOT" "$LOG_DIR"
test -x "$PYTHON"

log() {
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [cup50v2-watchdog] $*" >>"$WATCHDOG_LOG"
}

if [ ! -f "$LAUNCH_FILE" ]; then
    log "no launch.json; desks are not live yet, did nothing"
    exit 0
fi
LAUNCH="$("$PYTHON" -c "import json,sys;print(json.load(open(sys.argv[1]))['launch'])" "$LAUNCH_FILE")"

exec 9>"$PAPER_ROOT/watchdog.lock"
if ! flock -n 9; then
    log "another watchdog holds the watchdog lock; did nothing"
    exit 0
fi

# The engine lock is held at the shared root for all four desks, so this one test covers the
# whole field: a half-started engine holding some desks and not others cannot exist.
if ! flock -n "$PAPER_ROOT/engine.lock" -c true; then
    log "engine already running; did nothing"
    exit 0
fi

cd "$ROOT"
PYTHONUNBUFFERED=1 nohup "$PYTHON" run_cup50v2_paper.py --launch "$LAUNCH" \
    </dev/null >>"$ENGINE_LOG" 2>&1 9>&- &
log "engine was not running; started pid $! (paper only, no orders, four desks)"
