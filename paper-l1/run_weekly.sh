#!/usr/bin/env bash
# PROTOCOL-L1-FORWARD weekly paper-trade run (Wed ~00:10 UTC; idempotent any day).
# Runs the frozen L1 recompute runner, then commits paper-l1/ logs (tamper-evident
# audit trail) via a temporary git index so the pre-existing unmerged path in this
# worktree (src/crypto_trade/features_v1/__init__.py) never blocks the commit.
set -uo pipefail

WORKTREE="/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind"
LOG="$WORKTREE/paper-l1/cron_runs.log"
export PATH="$HOME/.local/bin:$PATH"
export PYTHONUNBUFFERED=1

cd "$WORKTREE"
{
  echo "==== run_weekly $(date -u +%Y-%m-%dT%H:%M:%SZ) ===="
  uv run python analysis/portfolio/blind_paper_l1.py
  RC=$?
  echo "runner exit code: $RC"
  if [ "$RC" -eq 0 ]; then
    if ! git diff --quiet HEAD -- paper-l1/; then
      TMPIDX=$(mktemp)
      GIT_INDEX_FILE=$TMPIDX git read-tree HEAD \
        && GIT_INDEX_FILE=$TMPIDX git update-index --add \
             $(git ls-files -o -m --exclude-standard paper-l1/ | grep -v run_weekly.sh; git ls-files paper-l1/) \
        && TREE=$(GIT_INDEX_FILE=$TMPIDX git write-tree) \
        && COMMIT=$(git commit-tree "$TREE" -p HEAD -m "chore(paper-l1): weekly paper-trade run $(date -u +%Y-%m-%d)

Automated PROTOCOL-L1-FORWARD weekly recompute + log append.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>") \
        && git update-ref refs/heads/quant-portfolio-blind "$COMMIT" \
        && echo "logs committed: $COMMIT"
      rm -f "$TMPIDX"
    else
      echo "no log changes to commit"
    fi
  else
    echo "RUNNER FAILED (rc=$RC) — logs NOT committed; inspect above output"
  fi
  echo "==== end $(date -u +%Y-%m-%dT%H:%M:%SZ) ===="
} >> "$LOG" 2>&1
