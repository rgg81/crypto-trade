# Engineering Report: Iteration 073

## Implementation

1. Added `feature_whitelist: list[str] | None` parameter to `LightGbmStrategy.__init__`
2. In `compute_features()`, after `_discover_feature_columns()`, filter to whitelist if provided
3. **Bug fix**: Changed `_discover_feature_columns()` call to pass `symbols` extracted from master DataFrame. Without this, discovery scanned all 760 parquet files, and the intersection reduced features from 60 to 38 (other symbols have different feature sets).
4. Runner script provides the 60-feature whitelist from IS importance analysis

## Backtest Results

### Run 1 (with discovery bug — 38 features):
- Early stop at Year 2023: PnL=-46.7% (WR=33.0%, 112 trades)
- IS Sharpe: +0.41 (vs baseline +1.22)
- IS MaxDD: 104.5% (vs baseline 45.9%)
- 199 IS trades, 0 OOS trades

### Run 2 (with fix — 60 features):
- Early stop at Year 2022: PnL=-21.1% (WR=35.1%, 74 trades)
- IS Sharpe: **-0.41** (negative)
- IS MaxDD: 69.0%
- IS WR: 34.7% (below break-even of ~34%)
- IS PF: 0.89 (losing money)
- 75 IS trades, 0 OOS trades

Both runs catastrophically worse than baseline.

## Key Observations

1. **Optuna found much weaker signal**: Best Sharpe per month was 0.05-0.14 with 60 features vs 0.4-0.5 with full features. The model simply can't find profitable patterns with the reduced feature set.

2. **Very short training_days preferred**: With 60 features, Optuna chose training_days=60 (very recent data only), suggesting the model struggles with longer history. With full features, training_days=450-500 is typical.

3. **Low confidence thresholds**: Best thresholds were 0.52-0.53 (barely above coin flip), vs 0.72-0.85 with full features. The model can't achieve high-confidence predictions.

4. **Fewer features = worse, not better**: Despite improving the samples/feature ratio from 24 to 73, the model lost critical signal.

## Trade Execution Verification

Limited to 75 trades (early stop). Spot-checked 5 trades:
- Entry prices match close of signal candle: YES
- SL/TP computed from ATR (NATR_21 × multipliers): YES
- PnL calculations correct

## Deviation from Brief

No deviations. The brief specified top 60 features by importance, which was implemented exactly. The approach simply didn't work.

## Runtime

- Run 1 (38 features): ~1038s (17 min)
- Run 2 (60 features): ~675s (11 min) — faster due to earlier early stop
