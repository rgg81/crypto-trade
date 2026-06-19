# BASELINE_PORTFOLIO — systematic top-20 L/S crypto perp portfolio

Living baseline for the `portfolio-iteration` track. Updated only by a confirmed accretive change.

## Current baseline: iter-002 TS-TREND (diversified time-series momentum)
- **Config:** point-in-time top-20 by trailing $-volume (ex-stablecoins, ≥2y-history candidate pool,
  206 coins). Per coin: trend = mean sign of trailing returns over {7d,14d,28d,56d} (8h candles),
  sized inverse-vol. Gross-normalized long/short, portfolio vol-targeted (1%/candle, max 3x).
  Realistic: decide close[t] → fill open[t+1] → hold; taker 0.05%/side on turnover. Leak-safe.
- **Performance:** net **IS Sharpe +1.68 / OOS +0.50 / maxDD −28% / +1271% total**, POSITIVE every
  year 2020–2026. Beats buy-and-hold BTC (IS +0.98 / OOS −0.36 / −77% DD) on every axis.
- **Code:** `analysis/portfolio/iter_002_top20.py` (mode `ts_trend`).

## Rejected so far
- Cross-sectional momentum (rank long/short): OOS −1.81 (momentum reversals); combo drags trend down.

## Open improvement axes (one per EXPLORATION; keep only if net Sharpe rises)
1. Trend-strength / regime filter (sit out chop) — lift OOS, cut DD.
2. Walk-forward horizon weighting (no hindsight on the {7,14,28,56d} mix).
3. Funding tilt as a small additive overlay (earn carry on the held legs).
4. Per-coin vol-floor / correlation-aware weights.

## Sacred constants
OOS_CUTOFF=2025-03-24 · 8h candles · signals past-only, fill open[t+1] · never tune on OOS ·
universe PIT top-20 ex-stables · report net (cost+funding) · NO institutional-capacity gate.
