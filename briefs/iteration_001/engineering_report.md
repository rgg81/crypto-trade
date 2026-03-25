# Engineering Report: Iteration 001

## Implementation Summary

Implemented the research brief for iteration 001 with minimal deviations. All existing infrastructure (walk-forward backtest, labeling, Optuna optimization, feature pipeline) was reused as-is.

## Changes Made

### 1. `src/crypto_trade/config.py` — OOS cutoff constant

Added project-level constants:
```python
OOS_CUTOFF_DATE = "2025-03-24"
OOS_CUTOFF_MS = 1742774400000  # epoch milliseconds
```

### 2. `src/crypto_trade/strategies/ml/lgbm.py` — Updated defaults

Changed defaults for 8h candles:
- `label_tp_pct`: 3.0 → **4.0**
- `label_timeout_minutes`: 120 → **4320** (3 days = 9 candles on 8h)
- `label_sl_pct`: unchanged at 2.0

### 3. `src/crypto_trade/backtest.py` — Synced defaults

Updated `_sync_label_params` default detection to match new LightGBM defaults, so CLI override logic remains correct.

### 4. `src/crypto_trade/strategies/ml/universe.py` — NEW: Symbol universe selection

Implements the 4 selection criteria from the research brief:
1. Ends with USDT
2. No "SETTLED" suffix
3. >= 1095 IS candles (before OOS cutoff)
4. First candle before 2023-07-01

Result: **201 symbols** (vs. research brief estimate of ~184). The difference is because some symbols that were borderline on the candle count threshold passed.

### 5. `src/crypto_trade/iteration_report.py` — NEW: IS/OOS report splitting

Full implementation of the report layer specified in the research brief:

- **Trade splitting**: Splits at `OOS_CUTOFF_MS` based on `open_time`
- **Per-half reports**: trades.csv, daily_pnl.csv, monthly_pnl.csv, per_symbol.csv, per_regime.csv, quantstats.html
- **comparison.csv**: Side-by-side metrics with OOS/IS ratios
- **Regime classification**: Uses BTC NATR(14)/ADX(14) with IS-period medians as fixed boundaries
- **Metrics computed**: Sharpe, Sortino, max drawdown, win rate, profit factor, Calmar ratio

### 6. `.gitignore` — Added iteration artifact directories

Added: `reports/`, `models/`, `analysis/`

### 7. `run_iteration_001.py` — Runner script

Standalone script that:
1. Selects symbol universe
2. Configures backtest with research brief parameters
3. Runs walk-forward LightGBM backtest (verbose=1)
4. Generates split IS/OOS reports

## Deviations from Research Brief

### Symbol count: 201 vs estimated 184

The research brief estimated ~184 symbols. The actual count is 201 because the estimate was approximate. All 201 meet the stated criteria. No deviation from the selection rules — just a count difference.

### Feature importance export: Deferred

The research brief requested `feature_importance.csv` in the IS report directory. The current LightGBM strategy retrains monthly, producing a new model each month. Feature importance would need to be aggregated across all monthly models. This was deferred to avoid complicating the first iteration. The per-month feature importance is visible in verbose output.

## Backtest Configuration

| Parameter | Value |
|-----------|-------|
| Symbols | 201 USDT pairs |
| Interval | 8h |
| TP | 4.0% |
| SL | 2.0% |
| Timeout | 4320 min (3 days) |
| Fee | 0.1% |
| Training window | 12 months |
| Optuna trials | 50 per month |
| CV splits | 5 (TimeSeriesSplit) |
| Confidence threshold | Optimized 0.50-0.55 |
| Training days | Optimized 10-500 |
| Random seed | 42 |
| Amount per trade | $1000 |

## Test Results

All 267 existing tests pass. One pre-existing failure in `test_adaptive_range_spike_filter.py::test_default_params` (window default mismatch 32 vs 16) — not related to iteration 001 changes.

## Report Structure

```
reports/iteration_001/
├── in_sample/
│   ├── quantstats.html
│   ├── trades.csv
│   ├── daily_pnl.csv
│   ├── monthly_pnl.csv
│   ├── per_symbol.csv
│   └── per_regime.csv
├── out_of_sample/
│   ├── quantstats.html
│   ├── trades.csv
│   ├── daily_pnl.csv
│   ├── monthly_pnl.csv
│   ├── per_symbol.csv
│   └── per_regime.csv
└── comparison.csv
```

## Notes

- The backtest is computationally intensive: ~60 months of walk-forward, each with 50 Optuna trials × 5 CV folds = 15,000 model fits total.
- Memory usage is manageable due to lazy monthly training — only one month's features are held in memory at a time.
- Verbose output logs every trade open/close and Optuna trial for debugging.
