# Iteration 094 — Engineering Report

**EARLY STOP**: Year 2022 PnL=-102.0%, WR=31.6%, 114 trades.

## Configuration

Same as iter 093 except:
- **Features: 50** (MDA-pruned from 185, correlation-deduped)
- New `feature_columns` parameter in `LightGbmStrategy` overrides auto-discovery

## Implementation

1. Added `feature_columns: list[str] | None` parameter to `LightGbmStrategy.__init__`
2. When provided, `compute_features()` uses the list directly instead of calling `_discover_feature_columns()`
3. MDA analysis script (`analysis/mda_importance_094.py`) trained reference LightGBM on IS data with 5-fold CV (gap=44), computed permutation importance by shuffling each feature 5 times

## MDA Analysis Results

- 185 features analyzed
- 371 highly correlated pairs (|Spearman r| > 0.9)
- After correlation dedup: 108 survivors (77 dropped)
- After MDA > 0 filter: 70 features with positive MDA
- Top 50 selected for iteration

Top 5 by MDA:
1. `vol_ad` (MDA=+0.0315) — Accumulation/Distribution
2. `trend_ema_5` (MDA=+0.0257) — raw EMA(5)
3. `vol_garman_klass_50` (MDA=+0.0206) — historical vol estimator
4. `trend_aroon_osc_25` (MDA=+0.0203) — trend oscillator
5. `vol_hist_30` (MDA=+0.0135) — historical volatility

3 harmful features identified (MDA < -0.01): `trend_aroon_osc_50`, `trend_sma_cross_20_100`, `vol_bb_bandwidth_30`

## Backtest Results (EARLY STOP)

| Metric | Iter 094 | Baseline (093) |
|--------|----------|----------------|
| IS Sharpe | **-1.46** | +0.73 |
| IS WR | 31.3% | 42.8% |
| IS PF | 0.71 | 1.19 |
| IS MaxDD | 150.5% | 92.9% |
| IS Trades | 115 (partial) | 346 |
| IS PnL | -104.5% | +150.2% |

Per-symbol: BTC 30.9% WR, ETH 31.7% WR — both below 33.3% break-even.

Exit breakdown: TP 20.0%, SL 63.5%, Timeout 16.5% (baseline: TP 32.1%, SL 52.9%).

## Label Leakage Audit

- CV gap: 44 rows (verified in all folds: 176-184h gap > 168h timeout)
- Walk-forward: standard monthly retraining, labels scan within training window only
- **No leakage detected**

## Trade Execution Verification

Sampled 5 trades from trades.csv — all verified:
- Entry prices match, SL/TP computed correctly from ATR
- Exit reasons consistent with PnL magnitudes

## Bug Found: Optuna Numerical Overflow

In the last month's training (2023-01, seed 1001), trial 11 achieved Sharpe=889460926405673.1 — a numerical overflow. One CV fold had exactly 1 trade with std=0, producing Sharpe=4.4e15. Optuna then selected this degenerate trial (training_days=30 → only 180 samples). This didn't cause the overall failure but highlights a robustness issue in the optimizer.

**Recommended fix**: Add a sanity cap in `compute_sharpe_with_threshold()` — return -10.0 if Sharpe > 100 (physically impossible).

## Root Cause Analysis

The 185→50 pruning was too aggressive. The MDA was computed on a **single reference model** with fixed hyperparameters, which does not represent the walk-forward monthly models well. Features important to the reference model may differ from features important to individual monthly models.

Key issues:
1. **MDA computed on full IS at once** — does not capture feature importance variation across time periods
2. **Reference model hyperparams** differ from Optuna-optimized monthly hyperparams
3. **Many "safe" features dropped** — RSI variants, return periods, BB %B were correlated with retained features but may have provided complementary signal in tree splits
4. **Vol_ad and trend_ema_5 ranked highest** — these are non-stationary, price-scale features that may have dominated the reference model but provide spurious signal in walk-forward
