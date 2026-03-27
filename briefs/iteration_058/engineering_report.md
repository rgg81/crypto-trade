# Engineering Report: Iteration 058

## Implementation Summary

Same slow feature additions as iter 057 (56 new periods across 6 feature modules). Key difference: NO changes to lgbm.py — feature discovery uses the original global intersection across ALL symbols. Regenerated all ~760 symbol parquets so slow features appear in the intersection.

## Feature Count

- Global intersection: **137 features** (106 baseline + 31 new slow features)
- 25 slow features did not survive the intersection because a few very short-lived symbols (< 100 candles) can't compute them (e.g., Stochastic-42, MACD(21,63,9), ADX-42, EMA/SMA-150, BB %B 42/60)
- This is a controlled increase from the baseline's 106 — much better than iter 057's 242

## Backtest Results

**EARLY STOP** — Year 2024 PnL = -13.8% (WR 38.2%, 144 trades). Fail-fast triggered.

| Metric | IS (iter 058) | IS (baseline 047) | IS (iter 057) |
|--------|--------------|-------------------|---------------|
| Sharpe | +0.38 | +1.60 | +0.35 |
| WR | 40.6% | 43.4% | 41.8% |
| PF | 1.07 | 1.31 | 1.07 |
| MaxDD | 110.0% | 64.3% | 79.3% |
| Trades | 480 | 574 | 479 |
| Features | 137 | 106 | 242 |

No OOS data (early stopped before OOS period).

## Per-Symbol Breakdown (IS)
- ETH: 280 trades, 39.6% WR, +51.3% PnL (65.7% of total)
- BTC: 200 trades, 42.0% WR, +26.8% PnL (34.3% of total)

Both symbols profitable but weak. MaxDD 110% is the worst across all recent iterations.

## Trade Execution Verification

Sampled trades confirmed correct: SL = -4.1%, TP = +7.9%, entry prices match candle close.

## Key Finding

With the confounding variable removed (global intersection, 137 features vs 242), the results are nearly identical to iter 057. IS Sharpe +0.38 vs +0.35. This proves the **slow features themselves** are the problem, not the extra 80 features from iter 057's discovery change.

The slow features add noise without adding signal. The model degraded from 1.60 to 0.38 IS Sharpe despite only a controlled 29% increase in feature count (106 → 137).
