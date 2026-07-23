---
name: team09-monitor
description: Monitor the frozen Team 09 exact-replay paper-trading desk, diagnose parity or data-integrity failures, and report forward performance without intervening in the strategy. Use when asked to check Team 09 health, paper PnL, live/backtest parity, pure-crypto membership, stale boundaries, append-invariance, or safe engine recovery.
---

# Team 09 Monitor

Monitor the paper test in `/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top40-v4-r1`.
Treat the frozen strategy plus organizer evaluator as one indivisible model.

## Preserve the experiment

- Observe and report; never flatten, hedge, resize, or edit a signal because of performance.
- Treat PnL, drawdown, Sharpe, turnover, and exposure as test results, not operational alerts.
- Alert only on test-integrity failures: engine down, stale boundary, frozen-authority drift,
  parity-record drift, revised sealed data, cache-manifest drift, missing current opens/marks,
  unclassified or non-pure-crypto membership, malformed append logs, or a traceback.
- Never edit `paper-team09/` artifacts to make a check pass. They are append-invariant evidence.
- Never introduce stablecoins, metals, commodities, equities, indexes, forex, premarket, TradFi,
  leveraged tokens, or unknown classifications. The pure-crypto policy fails closed.
- Keep the desk paper-only. `run_team09_paper.py` has no signed client or order path.

## Run the standard check

Run these commands serially:

```bash
cd /home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top40-v4-r1
uv run python scripts/team09_paper_healthcheck.py
uv run python scripts/team09_paper_digest.py
```

Interpret `STATUS OK` as operationally healthy. The healthcheck binds every paper artifact and
load-bearing market-cache file by path, size, row count, and SHA-256. It also verifies that every
Team 09 adapter and monitoring file matches the Git-anchored deployment manifest recorded in the
paper tick. Report the digest as observational information. Before 90 official forward bars,
label the result `INSUFFICIENT`; do not infer success or failure. The unscored continuity bridge
begins 2026-07-01. Official forward observations begin 2026-08-01T00:00:00Z.

## Diagnose an alert

Inspect, in order:

```bash
tail -40 logs/team09_paper.log
cat paper-team09/integrity.json
tail -10 paper-team09/runs.log
GEN=$(cat paper-team09/market-cache/CURRENT)
case "$GEN" in generations/*) ;; *) echo "unsafe cache pointer: $GEN"; exit 1 ;; esac
cat "paper-team09/market-cache/$GEN/cache-manifest.json"
cat "paper-team09/market-cache/$GEN/diagnostics.json"
```

Classify the failure:

- `AUTHORITY DRIFT` or `PARITY RECORD DRIFT`: stop. Do not regenerate evidence or launch the
  engine. Report the exact mismatched hash/file or deployment commit.
- `APPEND-INVARIANCE ABORT`: stop. Identify the revised key/column and preserve both source and
  cached evidence. Never overwrite the old row.
- `CACHE ... DRIFT`, missing mark, missing transaction open, unclassified bridge contract, or
  pure-crypto violation: keep the last sealed paper state and report the affected file/symbol.
- REST-invalid historical contracts use Binance's official daily transaction archives only after
  their published SHA-256 checksums pass. Treat archive-provenance drift as an integrity alert.
- Funding follows actual published Binance events. A boundary with no funding event is valid;
  alert only on malformed, revised, duplicated, or future funding rows.
- `ENGINE DOWN` or stale boundary with clean authority/data: a restart is experiment-preserving,
  but only restart when the user asks for recovery or the active monitoring mandate explicitly
  authorizes it. Confirm no other Team 09 process first.
- Traceback: diagnose from the log; never bypass a fail-closed check merely to advance the desk.

Use this restart command when authorized:

```bash
cd /home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top40-v4-r1
mkdir -p logs
PYTHONUNBUFFERED=1 nohup uv run python run_team09_paper.py \
  > logs/team09_paper.log 2>&1 &
```

The replay starts from 2020-02-03 on every tick. A restart therefore reconstructs all state rather
than trusting a mutable live strategy state. It catches up missed 8-hour boundaries in order.
The installed five-minute `scripts/team09_paper_watchdog.sh` cron is the reboot/restart mechanism;
it uses the same engine lock and never launches a second desk. A running process pins its startup
deployment identity and exits if a new committed Team 09 deployment appears, allowing this
watchdog to restart it on one internally consistent release.

## Run deep parity only on demand

Do not run the multi-year parity replay in every monitoring tick. It is compute-heavy.
When the user asks for deep verification, run it by itself:

```bash
uv run pytest -m parity tests/team09/test_team09_pipeline.py -q
```

The proof must show exact logical equality for targets, held positions, and all evaluator bar
returns against the one-shot golden replay. The paper runner then uses the same
`crypto_trade.team09.backtest.run_replay` function, discarding only the still-forming terminal
return.

## Report concisely

Lead with one verdict:

- `OK`: boundary current, authority/parity/append/cache/pure-crypto checks pass.
- `INSUFFICIENT`: integrity passes but fewer than 90 official forward bars exist.
- `INTEGRITY ALERT`: name the exact invariant and affected file/symbol/boundary.

Then give latest boundary, official forward bar/day counts and cumulative return, daily-annualized
Sharpe/max drawdown when meaningful, current gross/net and long/short count, actual funding-event
count, and any integrity action taken. Never recommend a strategy intervention based on losses.
