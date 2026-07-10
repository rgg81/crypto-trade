#!/bin/bash
# MN track §4.3 — 1h kline backfill driver (QE, 2026-07-10).
# Fetches 1h klines via bulk monthly ZIPs (data.binance.vision) for one scope
# group from diary-portfolio-mn/klines_1h_scope.json ("core" = 35 priority
# symbols: DIAG-B census30 U core20 U BTC/ETH; "remainder" = 328 others of the
# PIT top-40 union). Usage:
#
#   bash diary-portfolio-mn/klines_1h_backfill.sh core
#   nohup bash diary-portfolio-mn/klines_1h_backfill.sh remainder \
#     > logs/klines_1h_remainder.log 2>&1 &
#
# Rate-limit courtesy: N_WORKERS=5 (the OI backfill runs 16 workers in
# parallel; bulk hits S3/data.binance.vision only, no fapi weight).
# Idempotent: bulk skips already-downloaded months (compute_missing_months),
# so re-running resumes safely — but do NOT run two instances of the SAME
# group at once (same-symbol CSV writes would race). Per-symbol process
# isolation + 2 retries: one bad symbol never kills the batch.
# NOTE: the bulk CLI exits 0 even when a symbol yields no data (per-symbol
# tolerance is inside bulk_fetch_all), so the ledger's OK means "process
# completed", not "data exists" — the coverage report is the real gate:
#
#   uv run python analysis/portfolio checks are read-only; coverage verifier
#   lives with the 1H-FETCH-REPORT (see diary-portfolio-mn/1H-FETCH-REPORT.md §7).
set -u
cd "$(dirname "$0")/.." || exit 1
export PATH="$HOME/.local/bin:$PATH"
GROUP="${1:?usage: klines_1h_backfill.sh <core|remainder>}"
N_WORKERS=5
LOGDIR="logs/klines_1h_${GROUP}"
mkdir -p "$LOGDIR"

# Single-instance lock per group.
LOCKDIR="$LOGDIR/.lock"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "Another klines_1h_backfill($GROUP) instance appears to be running ($LOCKDIR exists)." >&2
  echo "If you are sure it is dead: rmdir $LOCKDIR and re-run." >&2
  exit 2
fi
trap 'rmdir "$LOCKDIR"' EXIT

SYMS=$(python3 -c "
import json
print('\n'.join(json.load(open('diary-portfolio-mn/klines_1h_scope.json'))['$GROUP']))
")

worker() {
  local wid=$1
  local i=0
  while IFS= read -r s; do
    if [ $((i % N_WORKERS)) -eq "$wid" ]; then
      # Fast resume: skip only symbols the ledger already marks OK (bulk is
      # month-incremental anyway, so a re-fetch of a done symbol is cheap but
      # the skip avoids ~360 pointless S3 listings on resume).
      if grep -q "^$s OK$" "$LOGDIR/_status.txt" 2>/dev/null; then
        echo "$s SKIP_DONE" >> "$LOGDIR/_status.txt"
      else
        local ok=0
        for attempt in 1 2 3; do
          PYTHONUNBUFFERED=1 uv run crypto-trade bulk --symbols "$s" --intervals 1h \
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
echo "1H BACKFILL ($GROUP) DONE in $((($(date +%s) - start_ts) / 60)) min" | tee -a "$LOGDIR/_status.txt"
