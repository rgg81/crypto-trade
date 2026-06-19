# BASELINE_PORTFOLIO — systematic top-20 L/S crypto perp portfolio

Living baseline for the `portfolio-iteration` track. Updated only by a confirmed accretive change.

## Current baseline: TREND + CARRY-TILT (walk-forward λ)  [iter-005, walk-forward-confirmed]
- **Config:** point-in-time top-20 by trailing $-volume (ex-stablecoins, ≥2y-history pool, 206 coins).
  Per coin, blended directional signal `(1-λ)·trend + λ·carry`, inverse-vol sized:
    - trend = mean sign of trailing returns over {7d,14d,28d,56d} (8h candles)
    - carry = −sign(trailing-9 funding) (short high-funding / long low-funding)
    - **λ selected WALK-FORWARD** each month on the past 24mo (best past Sharpe); converges ~0.25.
  Gross-normalized long/short, portfolio vol-targeted (1%/candle, max 3x). Real funding P&L booked.
  Realistic: decide close[t] → fill open[t+1] → hold; taker 0.05%/side. Leak-safe.
- **Performance (walk-forward λ, honest):** net **IS +1.21 / OOS +1.22 / maxDD −29%**, positive every
  year. (Fixed-λ=0.25 upper bound: IS +1.67 / OOS +1.31.) Trend-only was OOS +0.49 — the carry tilt
  is a walk-forward-VALIDATED lift (not OOS-selection bias: walk-forward independently picks λ≈0.25 in
  14/18 OOS months). Beats buy-and-hold BTC (IS +0.98 / OOS −0.36 / −77% DD) on every axis.
- **Code:** `analysis/portfolio/iter_002_top20.py` (trend) + `iter_004_funding.py` (carry tilt) +
  `iter_005_wf_lambda.py` (walk-forward λ — the deployable, no-hindsight version).

## Progression
- iter-001 BTC trend anchor: OOS +0.64. → iter-002 diversified top-20 trend: OOS +0.50, −28% DD.
- iter-003 trend-agreement gate: REJECTED (no help). → iter-004/005 carry tilt: OOS +0.50→**+1.22**, confirmed.

## Rejected
- Cross-sectional momentum (rank L/S): OOS −1.81. Trend-agreement gate: no effect / over-concentrates.

## Open improvement axes (one per EXPLORATION; keep only if net Sharpe rises, walk-forward-validated)
1. Walk-forward the trend horizon mix {7,14,28,56d} (currently equal-weight).
2. Short-term reversal overlay (1–3d). 3. Regime/vol scaling of gross exposure. 4. Per-coin caps /
   correlation-aware weights to trim the −29% DD.

## Sacred constants
OOS_CUTOFF=2025-03-24 · 8h candles · signals past-only, fill open[t+1] · never tune on OOS ·
walk-forward any param · universe PIT top-20 ex-stables · report net (cost+funding) · NO capacity gate.
