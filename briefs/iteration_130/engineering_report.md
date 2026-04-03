# Iteration 130 — Engineering Report

**Date**: 2026-04-03
**Type**: EXPLORATION (Model D screening: ADA standalone)
**Runner**: `run_iteration_130.py`
**Runtime**: 5908s (~1.6h)

## Implementation

Single model, iter 126 config template:
- Symbol: ADAUSDT
- Labeling: ATR-based TP=3.5x, SL=1.75x, timeout=7d
- Features: 185 auto-discovered
- Ensemble: 5 seeds [42, 123, 456, 789, 1001]
- CV gap: 22 rows (22 × 1 symbol)

## Label Leakage Audit

- CV gap = 22 (22 × 1 symbol). Verified from logs.

## Results

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | **-0.73** | 0.31 | -0.43 |
| Sortino | -0.71 | 0.48 | -0.67 |
| Max Drawdown | 166.8% | 41.3% | 0.25 |
| Win Rate | 36.0% | 48.9% | 1.36 |
| Profit Factor | 0.79 | 1.10 | 1.39 |
| Total Trades | 186 | 47 | 0.25 |
| Net PnL | **-149.1%** | +15.3% | -0.10 |

## Assessment

ADA fails Model D screening decisively:
- IS Sharpe -0.73 (gate requires > 0)
- IS Net PnL -149% (catastrophic losses over 3 years of IS)
- OOS marginally positive (+15.3%, 47 trades) but likely noise given terrible IS
- IS WR 36.0% is below break-even for ATR-scaled barriers

ADA does not have exploitable signal with this config.
