# Engineering Report: Iteration 007

## Implementation

No code changes. Runner script sets `take_profit_pct=5.0` and `label_tp_pct=5.0`.

## QE Code Review

After reviewing iter 007 OOS trades:
- Exit reasons: 66.3% SL, 23.0% TP, 10.6% timeout, 0.1% end_of_data
- Trades open/close correctly — SL at entry*(1±2%), TP at entry*(1±5%)
- Timeout at 4320min (3 days) working correctly
- The backtest engine is functioning as expected

## Identified Code Issues for Future Iterations

1. `_discover_feature_columns()` intersection drops features available in 49/50 symbols — should use union with NaN
2. `_sync_label_params` default detection is fragile
3. No warm-starting between walk-forward months

## Results

- 56,731 total trades, 8,898 OOS
- WR: 28.0% (dropped from 32.9%)
- OOS Sharpe: -3.21 (worse than baseline -1.91)
- Runtime: ~6,500s
