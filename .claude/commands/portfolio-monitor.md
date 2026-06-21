# Portfolio Monitor — live watch on the deployed L/S portfolio bot

## Mission
Keep a continuous, self-paced watch on the **live portfolio trading engine** (currently the
baseline-v3 long/short top-20 book on Binance **testnet**) and alert the user on **any unexpected
situation or error**. The bot rebalances every 8h; this skill verifies — from the **real Binance
API** — that it stays healthy between rebalances and that each rebalance fires cleanly.

Source of truth: **the live signed Binance API**, queried fresh every tick — never local cache.
Positions, unrealized PnL, balance, margin, liquidation come from `/fapi/v3/positionRisk`,
`/balance`, `/account`. Only "engine alive" (a `ps` check) and "last rebalance / errors" (parsed
from the engine log) are local — and correctly so, since they describe the *bot*, not the money.

## How to run a check
```
cd /home/roberto/crypto-trade/.worktrees/quant-research \
  && export PATH="$HOME/.local/bin:$PATH" \
  && set -a; source ~/.binance_testnet_env; set +a \
  && export BINANCE_AUTH_BASE_URL="https://testnet.binancefuture.com" \
  && uv run python scripts/portfolio_healthcheck.py
```
It prints one line: `STATUS: OK` or `STATUS: ALERT` plus a positions summary and any `FLAG:` lines.
Filter stderr noise with `| grep -vE "UserWarning|warn"`.

## What the health check verifies (`scripts/portfolio_healthcheck.py`)
- **engine alive** — the `run_portfolio_testnet.py` process is running (`ps`).
- **log scan** — any `Traceback`; the last rebalance `as_of` + `orders placed/errors`.
- **positions (LIVE API)** — count, gross $, net $, max single-name concentration, and whether any
  delisted/zombie name (TOMO/BLZ) reappeared.
- **balance/margin (LIVE API)** — wallet balance + available margin (liquidation headroom).
- **unrealized PnL (LIVE API)** — Binance's own `unRealizedProfit`, summed (matches account total).

## ALERT conditions (investigate → fix if safe → PushNotification the user)
- **engine DOWN** (process not running) — relaunch (see below) and notify.
- **Traceback** in the log.
- **NEW order errors** — `last_errs > 0` on the most recent rebalance (find the failing leg in the
  log; the usual causes are already fixed — stepSize floor (-4023) and post-floor min-notional
  (-4164) — so a new error means a genuinely new condition).
- **Concentration > 30%** of gross in one name.
- **Gross outside $5–12k** (the $10k-equity × ~0.70–0.85 vol-target band).
- **TOMO/BLZ (delisted) reappear** in the book — the eligibility-exit should keep them out.
- **Margin avail < $200** — liquidation risk.
- **MISSED rebalance** — UTC time is well past an 8h boundary (00/08/16 UTC) but `last_rebal`
  hasn't advanced to it. Check the log tail for a stuck refresh / traceback.

## BENIGN — do NOT alert
- `skipped > 0` dust legs (sub-$5 after stepSize floor — correctly skipped).
- Mild net-short (or net-long) tilt — the trend+carry signal isn't dollar-neutral by construction.
- Small uPnL swings (a few $ to low tens on an ~$8k book = normal mark-price noise).
- `last_rebal` not yet advanced when the next 8h boundary hasn't passed **in UTC** (the schedule
  display is local TZ, often +2h; the health check `checked` line is UTC — trust the UTC one).
- The frozen TNSR ~$0.16 dust position (too small to close under the $5 min; harmless).

## Response protocol each tick
1. Run the check.
2. **STATUS=OK** and `last_rebal` consistent with UTC → stay quiet (no ping), reschedule the next
   tick ~2700s out via ScheduleWakeup (pass the monitor prompt verbatim so it repeats).
3. **STATUS=ALERT** → read the log tail (`tail -30 logs/portfolio_testnet_v3.log`), diagnose, fix if
   it's safe and within established patterns, then **PushNotification** the user with what happened +
   what you did. Reschedule.
4. Don't spam: one ping per *state*, not per tick. If an alert persists across ticks and you've
   already notified + can't safely auto-fix, wait for the user.

## Engine-down recovery (relaunch)
```
cd /home/roberto/crypto-trade/.worktrees/quant-research
export PATH="$HOME/.local/bin:$PATH"; set -a; source ~/.binance_testnet_env; set +a
export BINANCE_AUTH_BASE_URL="https://testnet.binancefuture.com"
rm -f data/portfolio_testnet.db    # fresh DB -> re-reconciles vs ACTUAL exchange positions on start
PYTHONUNBUFFERED=1 uv run python run_portfolio_testnet.py > logs/portfolio_testnet_v3.log 2>&1 &
```
On restart the engine reads the **actual** book from the exchange (`get_positions`), recomputes the
v3 target, and trades only the diff — so a relaunch is safe and self-reconciling. First refresh
takes ~5–7 min (540-coin klines+funding) before the first rebalance line appears.

## Self-paced loop (how to keep watching)
This is a self-pacing monitor, not a cron. On each tick, after handling the check, call
**ScheduleWakeup** with `delaySeconds` ~2700 (the 8h rebalances are the key events; ~45-min checks
catch them and liveness in between) and `prompt` = the same monitor instruction verbatim so the
next firing repeats it. To **stop**, the user says so — then omit the ScheduleWakeup and mark
task #189 done. Keep the cadence at 2700s unless the user asks for tighter/looser watch.

## Key files & facts
- Health check: `scripts/portfolio_healthcheck.py`
- Engine runner: `run_portfolio_testnet.py` (equity $10k, leverage 3x, db `data/portfolio_testnet.db`)
- Log: `logs/portfolio_testnet_v3.log` · Creds: `~/.binance_testnet_env` (testnet keys only)
- Data path = **production** klines/funding (`fapi.binance.com`); **orders/positions = testnet**
  (`testnet.binancefuture.com`). Real market data, fake-money execution.
- Strategy = baseline-v3 (trend+carry walk-forward-λ + hysteresis δ=0.010 + eligibility-exit K=2),
  tag `portfolio-baseline-v3`. Parity is bit-exact vs the backtest (reconcile_live + parity test).
- Going to **real money**: swap `--testnet`/keys for production, seed `data/live.db`; same recipe.
  Tighten the watch cadence and re-confirm the ALERT thresholds before that step.
