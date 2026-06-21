# Portfolio Monitor — live watch on the deployed L/S portfolio bot

## Operating principle (read first)
**This skill is the canonical home for ALL monitoring + assistant intelligence on the trade bot.**
Every improvement we make — a new health signal, a smarter alert, a reconciliation check, a report,
an auto-recovery playbook — lands HERE (in this file + its helper scripts under `scripts/`), gets
committed, and is logged in the Changelog below. Intelligence compounds in one place instead of
scattering across sessions. When the user asks to "improve the monitoring/assistant," extend this
skill. Keep helper logic in committed scripts (testable, reusable) and keep this file the index +
playbook over them. The roadmap below is the living backlog; promote items into the workflow as we
build them and tick them off in the Changelog.

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

## Intelligence roadmap (the living backlog — build these into the skill over time)
Prioritized; each becomes a committed helper script + a section here when built.
1. **Parity / drift check (HIGH).** Each tick, compare the LIVE exchange book to the v3 strategy's
   intended target weights (`strategy.next_target_weights` on current data). Alert if any name
   diverges beyond the band+dust tolerance — the real correctness check: *is the bot actually
   holding what the strategy says?* This is the safety net the threshold checks don't give.
2. **PnL attribution + daily digest (HIGH).** Realized vs unrealized, funding accrued, taker cost
   paid, per-name contribution; once-a-day summary via PushNotification. Persist equity snapshots.
3. **Drawdown / equity-curve tracking.** Log equity each tick to a CSV; track live maxDD vs the
   backtest −23%; alert if live DD breaches an IS-calibrated band.
4. **Fill-quality / slippage tracking.** Compare actual fills (from order history) vs the
   close-proxy reference price the leg was sized at — measures real slippage vs the 5bps assumption.
5. **Trend-aware alerts.** Not just thresholds: margin steadily declining, gross drifting, uPnL
   trend, "what changed since last tick" deltas. Reduce both misses and false alarms.
6. **Turnover / cost ledger.** Track tickets/candle + notional turnover live; confirm the −63%
   ticket win (and the eligibility-exit ticket reduction) actually holds in production.
7. **Live-money pre-flight + kill-switch.** A checklist before the production cutover (keys, balance,
   leverage caps, max-gross guard) and a one-command flatten/halt.

## Changelog (tick off as we build)
- **2026-06-21 v0** — initial skill: live-API health check (`scripts/portfolio_healthcheck.py`),
  STATUS OK|ALERT, threshold alerts, benign list, engine-down relaunch, self-paced ScheduleWakeup
  loop. Deployed against baseline-v3 on testnet ($10k/3x). Task #189.
