# Iteration 131 — Engineering Report

**Date**: 2026-04-03
**Type**: EXPLORATION (Model D screening: XRP standalone)
**Runner**: `run_iteration_131.py`
**Runtime**: 5549s (~1.5h)

## Implementation

Single model, iter 126 config template:
- Symbol: XRPUSDT
- Labeling: ATR-based TP=3.5x, SL=1.75x, timeout=7d
- Features: 185 auto-discovered
- Ensemble: 5 seeds [42, 123, 456, 789, 1001]
- CV gap: 22 rows (22 × 1 symbol)

## Label Leakage Audit

- CV gap = 22 (22 × 1 symbol). Verified from logs.

## Results

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | **-0.03** | 2.03 | -74.18 |
| Sortino | -0.02 | 2.34 | -100.17 |
| Max Drawdown | 116.0% | 12.3% | 0.11 |
| Win Rate | 46.7% | 59.1% | 1.26 |
| Profit Factor | 0.99 | 2.52 | 2.54 |
| Total Trades | 169 | **22** | 0.13 |
| Net PnL | **-4.8%** | +69.4% | -14.47 |

## Assessment

XRP fails Model D screening:
- IS Sharpe -0.03 (gate requires > 0) — model is essentially break-even over 3 years IS
- IS Net PnL -4.8% (slightly negative)
- Only 22 OOS trades (gate requires ≥ 20, hard constraint requires ≥ 50)
- OOS Sharpe +2.03 is statistically meaningless with 22 trades (binomial p ≈ 0.28 for 13/22 vs 50%)

XRP's ATR-based barriers produce very few trades — the model is too selective but without IS profitability backing it up.
