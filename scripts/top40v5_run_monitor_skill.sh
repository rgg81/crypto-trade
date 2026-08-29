#!/usr/bin/env bash
# Cron entry point: runs the /top40v5-monitor skill headlessly and pushes the four-desk report to
# the user EVERY run, not only on failure. The watchdog restarts a dead engine; this is the piece
# that delivers the report -- without it, a report only happens when a session is open to ask.
set -euo pipefail

# cron runs with a minimal environment: no .bashrc, no user PATH. Without this line every
# scheduled run fails with "claude: command not found", in the stderr of a log nobody re-reads.
export PATH="$HOME/.local/bin:$PATH"

cd "$(dirname "${BASH_SOURCE[0]}")/.."

LOG_DIR="logs/top40v5-monitor-cron"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date -u +%Y%m%dT%H%M%SZ).log"

claude -p \
  "Run the top40v5-monitor skill: report the four-desk healthcheck and performance digest, each desk's backtest parity next to its stats (a standing requirement of the skill), and the capital rule's standing. Send this report via PushNotification every run, not only when something is wrong. If a genuine integrity or parity problem is found, diagnose per the skill and say so plainly in the same notification; do not restart the engine or modify any file yourself -- that stays a human decision unless the skill's recovery section explicitly covers it." \
  --allowedTools "Bash" "Read" "Skill" "PushNotification" \
  > "$LOG_FILE" 2>&1

echo "top40v5 monitor run complete, log: $LOG_FILE"
