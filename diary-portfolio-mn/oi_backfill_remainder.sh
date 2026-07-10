#!/bin/bash
# MN track §4.2 — REMAINDER OI backfill (579 symbols: full PIT top-60 union minus
# the already-fetched top-20 core). Run detached, e.g.:
#
#   nohup bash diary-portfolio-mn/oi_backfill_remainder.sh > logs/oi_remainder.log 2>&1 &
#
# Estimated wall-clock: ~8-12h at 16 workers (measured priority-run throughput:
# ~94 scanned days/min/worker under 20-way contention; 579 symbols x 2,138
# scanned days each, most of them fast 404s outside each listing window).
# Idempotent: fetch-oi dedups on open_time, so re-running resumes safely —
# but do NOT run two instances at once (same-symbol CSV writes would race).
# Per-symbol process isolation + 2 retries: one bad symbol never kills the batch.
# After completion, regenerate the coverage report:
#
#   uv run python analysis/portfolio/mn_oi_report.py \
#     --scope-json diary-portfolio-mn/oi_scope.json
#
set -u
cd "$(dirname "$0")/.." || exit 1
export PATH="$HOME/.local/bin:$PATH"
N_WORKERS=16
LOGDIR=logs/oi_backfill_remainder
mkdir -p "$LOGDIR"

# Single-instance lock — two concurrent runs would race on same-symbol CSV writes.
LOCKDIR="$LOGDIR/.lock"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "Another oi_backfill_remainder instance appears to be running ($LOCKDIR exists)." >&2
  echo "If you are sure it is dead: rmdir $LOCKDIR and re-run." >&2
  exit 2
fi
trap 'rmdir "$LOCKDIR"' EXIT

# Extract the remainder list from the scope JSON (kept next to this script).
SYMS=$(python3 -c "
import json
print('\n'.join(json.load(open('diary-portfolio-mn/oi_scope.json'))['remainder']))
")

worker() {
  local wid=$1
  local i=0
  while IFS= read -r s; do
    if [ $((i % N_WORKERS)) -eq "$wid" ]; then
      # Fast resume: skip only symbols the ledger already marks OK (a merely
      # non-empty cache could be a half-fetched symbol from a crashed run).
      if grep -q "^$s OK$" "$LOGDIR/_status.txt" 2>/dev/null; then
        echo "$s SKIP_DONE" >> "$LOGDIR/_status.txt"
      else
        local ok=0
        for attempt in 1 2 3; do
          PYTHONUNBUFFERED=1 uv run crypto-trade fetch-oi --symbols "$s" \
            >> "$LOGDIR/$s.log" 2>&1 && { ok=1; break; }
          echo "[driver] attempt $attempt for $s failed — retry in 10s" >> "$LOGDIR/$s.log"
          sleep 10
        done
        if [ $ok -eq 1 ]; then
          echo "$s OK" >> "$LOGDIR/_status.txt"
        else
          echo "$s FAILED_3X" >> "$LOGDIR/_status.txt"
        fi
      fi
    fi
    i=$((i + 1))
  done <<< "$SYMS"
}

start_ts=$(date +%s)
for w in $(seq 0 $((N_WORKERS - 1))); do
  worker "$w" &
done
wait
echo "REMAINDER BACKFILL DONE in $((($(date +%s) - start_ts) / 60)) min" | tee -a "$LOGDIR/_status.txt"
