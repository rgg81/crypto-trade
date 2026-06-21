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
Each tick runs BOTH the fast health check and the deeper parity/drift check:
```
cd /home/roberto/crypto-trade/.worktrees/quant-research \
  && export PATH="$HOME/.local/bin:$PATH" \
  && set -a; source ~/.binance_testnet_env; set +a \
  && export BINANCE_AUTH_BASE_URL="https://testnet.binancefuture.com" \
  && uv run python scripts/portfolio_healthcheck.py \
  && uv run python scripts/portfolio_candle_check.py \
  && uv run python scripts/portfolio_parity_check.py \
  && uv run python scripts/portfolio_digest.py
```
- `portfolio_healthcheck.py` → `STATUS: OK|ALERT` + positions summary + `FLAG:` lines (fast, API-only).
- `portfolio_candle_check.py` → `CANDLE: OK|BAD` (fast, CSV-only). BAD = a forming (incomplete) candle
  leaked into the signal data, or the data is stale (missed refresh). Guards the "close must be a
  COMPLETE candle, never the forming one" invariant.
- `portfolio_parity_check.py` → `PARITY: OK|DRIFT` (loads the universe + recomputes the strategy
  target; ~20s). DRIFT = the live book no longer matches what the strategy says it should hold.
- `portfolio_digest.py` → appends an equity snapshot to `data/portfolio_equity.csv` (the equity
  curve) and prints a 24h PnL digest (realized / funding / commission / unrealized, per-name) +
  `DIGEST_DUE: yes|no`. Not an alert source — it's the periodic report (see Daily digest below).
Filter stderr noise with `| grep -vE "UserWarning|warn"`. Treat **any** of `STATUS=ALERT`,
`CANDLE=BAD`, or `PARITY=DRIFT` (not flagged near-boundary-transient) as an alert.

## Daily digest (PnL attribution)
`portfolio_digest.py` runs every tick to log the equity snapshot (cheap). When its output shows
`DIGEST_DUE: yes` (first tick of a new UTC day), **PushNotification the digest block** to the user
(equity + 24h Δ, realized/funding/commission/net, top winners/losers), then run
`uv run python scripts/portfolio_digest.py --mark-pushed` so it only fires once per day. On
`DIGEST_DUE: no`, do nothing with it (the snapshot was already logged). The equity CSV builds the
curve; after 24h of snapshots the "24h Δ" populates. NOTE early realized/commission numbers are
inflated by deploy/debug churn (flatten + re-enter); steady-state commission is near-zero (the band +
eligibility-exit keep turnover low).

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
- **PARITY=DRIFT** — the live book diverges from the strategy target: a `MISSING` name (failed
  entry), `EXTRA` (failed close), `WRONGSIDE`, or `MISSIZED` leg. The real correctness alarm —
  means the bot is NOT holding what v3 says. (If the line says "NEAR 8h boundary, likely transient,"
  the engine is mid-rebalance — re-check next tick before alerting.)
- **CANDLE=BAD** — `FORMING-CANDLE LEAK` (an incomplete candle is in the signal data — a look-ahead
  bug; the fetcher should have dropped it) or `STALE data` (freshest complete candle >9h old → the
  engine missed a refresh). Either breaks backtest parity at the data layer — investigate the
  fetcher / refresh immediately.

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
1. **Parity / drift check (HIGH).** ✅ DONE 2026-06-21 — `scripts/portfolio_parity_check.py`.
1b. **Candle-integrity check (HIGH).** ✅ DONE 2026-06-21 — `scripts/portfolio_candle_check.py`
   (signal close must be a COMPLETE candle, never the forming one; + staleness).
2. **PnL attribution + daily digest (HIGH).** ✅ DONE 2026-06-21 — `scripts/portfolio_digest.py`
   (realized/funding/commission/unrealized, per-name, equity snapshots, once-a-day digest).
3. **Drawdown / equity-curve tracking.** Equity snapshots now logged (#2) to
   `data/portfolio_equity.csv`; NEXT: track live maxDD vs the backtest −23% + alert on breach.
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
- **2026-06-21 v1** — roadmap #1: **parity/drift check** (`scripts/portfolio_parity_check.py`).
  Recomputes the v3 strategy target (same code + close-proxy forming) and compares per-name to the
  LIVE book; flags MISSING / EXTRA / WRONGSIDE / MISSIZED, tolerates price-drift + dust, notes 8h
  boundary transients. Monitor now runs health + parity each tick; either ALERT or DRIFT pings.
- **2026-06-21 v3** — roadmap #2: **PnL attribution + daily digest** (`scripts/portfolio_digest.py`
  + read-only `auth_client.get_income`). Logs an equity snapshot each tick to
  `data/portfolio_equity.csv`; reports 24h realized/funding/commission/unrealized PnL attributed
  per-name from `/fapi/v1/income`; pushes a digest once per UTC day (DIGEST_DUE flag + --mark-pushed).
- **2026-06-21 v2** — roadmap #1b: **candle-integrity check** (`scripts/portfolio_candle_check.py`),
  per the user: the signal close must always be a COMPLETE candle, never the forming one. Verifies no
  forming candle leaked into any coin CSV (close_time > now) + data isn't stale (missed refresh).
  Confirmed clean live (667 coins, 0 leaks). Monitor now runs health + candle + parity each tick.
  GUIDING MANDATE (user): make the bot run as close as possible to the backtest, solve any unexpected
  issue, be the user's eyes when away — contribute proactively, every improvement lands in this skill.
