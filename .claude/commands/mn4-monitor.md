# MN4 Monitor — live watch on the unified 01+03 paper-trading book

## Operating principle (read first)
**This skill is the canonical home for ALL monitoring intelligence on the unified 01+03
paper-trading book.** Every improvement — a new health signal, a smarter alert, a parity
check, an attribution read — lands HERE, gets committed, and is logged in the Changelog.
Intelligence compounds in one place. When the user asks to "improve the monitoring," extend
this file (+ helper scripts under `analysis/portfolio/` if logic gets non-trivial). This file
is the index + playbook.

Companion to `/portfolio-monitor` (the exchange-deployed v3 bot). That skill watches a live
Binance bot; THIS skill watches a **paper recompute book** — different surface, same discipline.

## HANDS-OFF MANDATE — NEVER interfere with the strategy (user directive, inherited)
We are TESTING the book. It must run UNTOUCHED through wins AND losses. The monitor OBSERVES
and INFORMS; it NEVER intervenes.
- **NEVER** flatten, reduce, hedge, or alter the position in response to performance.
- **NEVER** run or recommend a kill-switch because of drawdown or a losing streak. The
  forward gates (Sharpe/maxDD/slow-bleed) are TEST RESULTS, surfaced as information, not a
  call to act. Overriding on a loss corrupts the test.
- **The ONLY things that warrant an alert are TEST-INTEGRITY failures** — the paper trade
  isn't running correctly or has drifted from the backtest:
  - **PARITY DRIFT** — the live forward log no longer matches a direct backtest over the same
    window (the bit-identity guarantee broke). This is the single most important alert.
  - **APPEND-INVARIANCE ABORT** — `mn4_live_unified.py` refused to append (the panel revised
    history under it; a silent revision would corrupt the log). Surface + diagnose.
  - **CRON DEAD / DATA STALE** — the session CronCreate job stopped firing, or the last
    forward candle is > ~1 day old (the panel isn't being extended). For a paper trade this
    is the equivalent of "engine down."
  - **FUNDING FEED WRONG** — funding_rets went all-zero/flat (stale feed) or the sign flipped
    (a silent parity killer for a market-neutral book).
- Re-running the live tick after a crash/abort is PRO-test (it resumes + reconciles to the
  book's own frozen target), so it's allowed — it is not interference.

## What this book is (context)
- **Construction:** the frozen UNIFIED-01+03 single-signal book (TS-mom + regime-adaptive
  momentum, α=0.5887 blend, union universe, min risk-scalar, BTC+ETH hedge, daily rebal=3,
  5+2.5bps, real 8h funding). See `diary-portfolio-mn4/UNIFIED-01-03.md`.
- **Live architecture:** `analysis/portfolio/mn4_live_unified.py` runs the SAME `run_unified()`
  backtest on the GROWING panel each tick and reads off the forward window. The engine IS the
  paper broker (open-to-open fills, cost, funding — all applied). Parity is by construction;
  proven bit-identical in `tests/test_mn4_live_unified.py`.
- **Source of truth:** `paper-unified-0103/forward_returns.csv` (the forward P&L log,
  append-invariant, tamper-evident). Plus `gates.csv`, `integrity.json`, `runs.log`.
- **Schedule:** a session CronCreate job (NOT systemd, per user direction "for now") fires the
  tick at 8h cadence. Session-only + 7-day auto-expiry — a known limitation.

## How to run a check (the tick)
Run this sequence and synthesize a one-screen health report:
```
cd /home/roberto/crypto-trade/.worktrees/quant-portfolio-blind
# 1. Forward P&L + gates (the test results)
cat paper-unified-0103/gates.csv
tail -1 paper-unified-0103/forward_returns.csv   # latest candle
wc -l paper-unified-0103/forward_returns.csv     # n forward candles
# 2. Integrity (parity + append-invariance last status)
cat paper-unified-0103/integrity.json
tail -5 paper-unified-0103/runs.log
# 3. Cron health (is the tick still firing?)
#    (the orchestrator checks CronList — is the mn4 paper-trade job present + when did it last fire?)
# 4. Data freshness — last forward candle date vs now (stale => cron dead / fetch failed)
# 5. Optional: re-run a tick if stale/aborted (pro-test, idempotent):
#    PATH="$HOME/.local/bin:$PATH" PYTHONUNBUFFERED=1 uv run python analysis/portfolio/mn4_live_unified.py
```

## The report (one screen)
- **Verdict line:** `INSUFFICIENT (n=X<90)` | `RUNNING (Sharpe=Fwd ±Z, maxDD=Y%, cum=Z%)` | `GATE-FAIL` | `INTEGRITY-ALERT`.
- **Forward P&L:** cumulative return, 8h Sharpe (1× + 2×-GT), maxDD, n candles, since 2026-07-01.
- **Funding attribution:** cumulative funding paid/received, funding share of gross P&L, long-leg vs short-leg vs hedge-leg. (Flag if funding-drag > 30% of gross edge — FG-4 concern.)
- **Latest position:** n_held, gross leverage, β_BTC/β_ETH, top longs/shorts, regime state.
- **Integrity:** last parity check (PASS=bit-identical), last append-invariance (PASS/ABORT), cron status (firing/stale), data freshness (last candle age).
- **Alerts (integrity-only):** PARITY-DRIFT / APPEND-ABORT / CRON-DEAD / FUNDING-FEED — each with the diagnosis + the pro-test fix (re-run the tick).

## Forward gates (pre-registered — TEST RESULTS, not action triggers)
- Primary: forward Sharpe ≥ +0.50 (SUCCESS) / < 0 (FAIL) — evaluated at n ≥ 90 candles (~1 month).
- maxDD < −30% (FAIL).
- Slow-bleed: any rolling-6mo forward Sharpe < −0.5 (CONCERN).
- Funding discipline: cumulative funding drag > 30% of gross edge (FG-4 CONCERN).
A FAIL is INFORMATION for the user (the test gave its answer), never a trigger for the monitor to act.

## Changelog (living — append every improvement)
- 2026-07-12: skill created. Monitors the unified 01+03 paper book. Hands-off, integrity-only
  alerts. Surface = forward_returns.csv + gates + integrity + cron. Session-CronCreate schedule
  (systemd = documented upgrade for unattended operation).

*— MN4 monitor skill. One living brain for the unified 01+03 paper book. Observe, inform, never intervene.*
