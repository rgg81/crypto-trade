# Iteration 065 — Engineering Report

## Change

Added `atr_label_mode: bool` to LightGbmStrategy. When `True`, labeling uses ATR-scaled barriers (same multipliers as execution: TP=2.9×ATR_21, SL=1.45×ATR_21) instead of fixed 8%/4%.

Implementation:
- In `_train_for_month`: loads `vol_atr_21` from feature store for training candles
- Builds master-indexed array for `label_trades()` `atr_values` parameter
- Uses ATR multipliers as tp_pct/sl_pct (these become multipliers when atr_values is provided)
- Column name derived from `atr_column`: `vol_natr_21` → `vol_atr_21` (NATR → ATR)

## Result: Seed 42

### Comparison with Baseline

| Metric | Iter 065 IS | Iter 065 OOS | Baseline IS | Baseline OOS |
|--------|------------|-------------|------------|-------------|
| Sharpe | +1.07 | +0.94 | +1.48 | +1.95 |
| Win Rate | 43.6% | 39.5% | 45.3% | 44.0% |
| Profit Factor | 1.25 | 1.23 | 1.34 | 1.66 |
| Max Drawdown | 70.4% | 70.6% | 74.9% | 18.4% |
| Total Trades | 518 | 147 | 541 | 100 |
| Net PnL | +277.3% | +63.2% | +379.6% | +123.4% |

OOS/IS Sharpe ratio: 0.87 (healthy, vs baseline's suspicious 1.32)

### Label Distribution Shift

ATR labeling created directional bias in trending markets:
- First training month (2020-2022): 60% long / 40% short (bull market → easier long TPs)
- Last training month (2022-2026): 51% long / 49% short (more balanced)

Baseline's fixed 8%/4% labels were ~50/50 symmetric regardless of market regime.

### Trade Execution Verification

Spot-checked 10 trades from OOS. Entry prices, dynamic TP/SL levels, and PnL calculations are correct. The ATR barriers produce the expected wider barriers in volatile periods (Feb 2026: TP=13-22%, SL=6-11%) and tighter in calm periods (TP=3-7%, SL=1.5-3.5%).

The model generated 147 OOS trades vs baseline 100 — the lower confidence threshold (0.510 vs baseline's higher thresholds) allowed more trades through.

### Runtime

1220 seconds (~20 min), slightly longer than baseline due to ATR loading for labeling.
