# Iteration 056 — Engineering Report

## Change Implemented

Removed `is_unbalance=True` from LightGBM parameters in `optimization.py` (two locations: Optuna objective and final retraining). Sample weights (PnL-magnitude, scaled [1, 10]) remain active. Updated log message in `lgbm.py`.

## Backtest Results (seed=42)

| Metric | IS | OOS | OOS/IS Ratio |
|--------|-----|-----|-------------|
| Sharpe | 1.0927 | 0.4499 | 0.4117 |
| Sortino | 1.5315 | 0.5779 | 0.3773 |
| Win Rate | 41.9% | 39.4% | 0.9401 |
| Profit Factor | 1.2415 | 1.0986 | 0.8849 |
| Max Drawdown | 72.76% | 59.84% | 0.8224 |
| Total Trades | 511 | 127 | — |
| Total Net PnL | +274.84% | +28.86% | 0.1050 |
| Calmar Ratio | 3.7774 | 0.4823 | 0.1277 |

## Comparison vs Baseline 047 (seed=42)

| Metric | Iter 056 | Baseline 047 | Delta |
|--------|----------|-------------|-------|
| IS Sharpe | +1.09 | +1.60 | -0.51 |
| OOS Sharpe | +0.45 | +1.16 | -0.71 |
| IS WR | 41.9% | 43.4% | -1.5pp |
| OOS WR | 39.4% | 44.9% | -5.5pp |
| IS PF | 1.24 | 1.31 | -0.07 |
| OOS PF | 1.10 | 1.27 | -0.17 |
| IS Trades | 511 | 574 | -63 |
| OOS Trades | 127 | 136 | -9 |
| OOS/IS Sharpe | 0.41 | 0.72 | -0.31 |

Every metric degraded. OOS/IS Sharpe ratio 0.41 < 0.50 threshold (fails overfitting gate).

## Seed Validation

**Skipped.** First seed already fails primary metric (OOS Sharpe 0.45 < baseline 1.16) AND hard constraint (OOS/IS Sharpe ratio 0.41 < 0.50). No reasonable number of seeds will bring the mean above baseline.

## Trade Execution Verification

Sampled 17 trades (10 IS + 5 OOS + 2 end_of_data). All clean:
- SL prices match entry * (1 ± 0.04) exactly
- TP prices match entry * (1 ± 0.08) exactly
- SL net PnL = -4.1%, TP net PnL = +7.9% (correct with 0.1% fee)
- Timeout trades within bounds
- All weight_factor = 1.0

## Key Observations

1. **is_unbalance=True helps the model.** Removing it reduced IS Sharpe from 1.60 to 1.09 (-32%) and OOS Sharpe from 1.16 to 0.45 (-61%). The class imbalance correction is load-bearing.

2. **More IS degradation than expected.** If the change only affected OOS generalization, IS should be similar. The large IS drop (-0.51 Sharpe, -1.5pp WR) means `is_unbalance` genuinely helps the model learn better, not just overfit.

3. **Trade count decreased.** 511 IS trades vs 574 baseline (-11%), and 127 OOS vs 136 (-7%). Without is_unbalance, the model is slightly less confident overall.

4. **The 57/43% class imbalance matters.** Training labels are 57% long / 43% short. Without is_unbalance, the model over-predicts the majority class (long) at the expense of the minority class (short). Since shorts are actually more profitable in this strategy, this hurts performance disproportionately.

## Runtime

1227 seconds (~20 minutes) for full walk-forward backtest.
