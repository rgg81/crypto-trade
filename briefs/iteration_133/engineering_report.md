# Iteration 133 — Engineering Report

**Date**: 2026-04-03
**Type**: EXPLORATION (Model D/E screening: DOT standalone)
**Runner**: `run_iteration_133.py`
**Runtime**: 4859s (~1.4h)

## Implementation

Single model, iter 126 config template:
- Symbol: DOTUSDT
- Labeling: ATR-based TP=3.5x, SL=1.75x, timeout=7d
- Features: 185 auto-discovered
- Ensemble: 5 seeds [42, 123, 456, 789, 1001]
- CV gap: 22 rows (22 × 1 symbol)

## Label Leakage Audit

- CV gap = 22 (22 × 1 symbol). Verified from logs.

## Results

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | **-0.02** | 1.10 | -64.92 |
| Max Drawdown | 148.2% | 42.0% | 0.28 |
| Win Rate | 42.5% | 44.7% | 1.05 |
| Profit Factor | 0.99 | 1.41 | 1.42 |
| Total Trades | 113 | 47 | 0.42 |
| Net PnL | -2.5% | +59.0% | -23.60 |

## Assessment

DOT fails Model D screening:
- IS Sharpe -0.02 (gate requires > 0) — break-even over 3 years IS
- IS PF 0.99 — model has no edge
- Same pattern as XRP (iter 131): flat IS, positive OOS is noise with 47 trades
