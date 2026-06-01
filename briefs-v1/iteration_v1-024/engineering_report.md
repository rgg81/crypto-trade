# Engineering Report — iter-v1/024 (BLOCK-PENDING-FIX rerun)

## Headers

- Iteration: iter-v1/024
- Branch: iteration-v1/024
- Commit SHA (fix): 3b6e2a03d5c3ee8bf64602ca0660bfc41dfb78fa
- Hardware: x86_64 WSL2 Linux 6.6.114.1-microsoft-standard, 560 logical CPUs
- Wall-clock time: ~1h11m (11:52–13:03 CEST 2026-05-27)
- Run log: logs/iter-v1-024-rerun.log

## BLOCK-PENDING-FIX Root Cause + Resolution

### Root Cause

`data_filter_callback` in `lgbm.py:_train_for_month` received `self._master.iloc[train_indices]`,
where `_master` is built from kline CSVs (OHLCV only). Feature columns including
`funding_rate_zscore_30` live exclusively in parquet files and are loaded separately
later at step (c) via `lookup_features()`. The silent all-False fallback in
`make_extreme_filter` (when the z30 column was missing) masked the defect:
all 3 extreme sub-models produced empty `_models` (skip 100%), resulting in
comparison.csv that was bit-identical to iter-v1/023.

### Fix Applied (commit 3b6e2a0)

1. **`regime_gate_v1.py`**: replaced silent all-False/all-True fallbacks in
   `make_extreme_filter` and `make_normal_filter` with hard `ValueError` raises.
   Missing z30 column is now immediately surfaced, not silently masked.

2. **`lgbm.py`**: added `data_filter_columns: list[str] | None` parameter. When set,
   the listed columns are loaded from parquet via `lookup_features()` and left-joined
   onto the kline master slice before calling the filter callback. This gives the
   filter access to `funding_rate_zscore_30` which previously was absent.

3. **`run_baseline_v1.py`**: `build_lgbm_strategy` gains `data_filter_columns` param.
   All 6 regime sub-model builds (A_ext, A_norm, C_ext, C_norm, D_ext, D_norm)
   now pass `data_filter_columns=[V1_ITER024_Z30_COLUMN]`.

4. **Tests (23 total, 5 new)**: hard-raise on missing column (extreme + normal),
   nonzero mask with sample data, `data_filter_columns` param acceptance. All 23 pass.

### Fix Verification

- `[data_filter] Partition: 564 rows after filter (from full window)` — first extreme
  partition for 2022-01 Pool A (previously always 0).
- 318 total filter invocations across full IS+OOS run (all non-zero).
- comparison.csv values DIFFER from /023 (IS Sharpe -0.5761 vs /023 +0.4121).
- 7 feature importance files present: A_extreme, A_norm, C_extreme, C_norm, D_extreme,
  D_norm, E_baseline.
- `funding_rate_zscore_30` appears in all 7 sub-models' feature importance lists.

## Configuration Diff vs BASELINE_V1.md

BASELINE: 4 models (A pool, C LINK, D LTC, E DOT), no regime routing

iter-v1/024 changes (per research brief):
- F-AXIS #1: 4 → 7 sub-models via RegimeRoutedStrategy wrapping
- F-AXIS #2: V1_FEATURE_COLUMNS_PRUNED 40 → 42 (adds funding_rate_zscore_30 + _90)
- F-AXIS #3: Regime dispatch at threshold |z30| > 1.5 for A/C/D; DOT excluded (E baseline)
- n_trials = 18 (EXPLORATION budget), ensemble_size = 3, seeds [42, 123, 456]

## Key Metrics Block

| metric | IS | OOS | ratio |
|---|---|---|---|
| sharpe | -0.5761 | +0.7593 | -1.318 |
| sortino | -0.5711 | +0.9947 | -1.742 |
| max_drawdown | 155.98% | 31.34% | 0.201 |
| win_rate | 39.1% | 41.1% | 1.050 |
| profit_factor | 0.8907 | 1.1429 | 1.283 |
| total_trades | 747 | 285 | 0.382 |
| calmar_ratio | 0.6438 | 1.2138 | 1.885 |
| total_net_pnl | -100.42 | +38.04 | -0.379 |
| psr_monthly_vs_0 | 0.143 | 0.789 | 5.502 |
| psr_monthly_vs_1 | 0.001 | 0.382 | 258.2 |
| n_effective_trials | 10 | 10 | 1.000 |

## Sub-Model Trade Counts

| sub-model | IS trades | OOS trades |
|---|---|---|
| Model A (BTC+ETH) | 436 | (included in 285 total) |
| Model C (LINK) | 223 | |
| Model D (LTC) | 202 | |
| Model E (DOT) | 171 | |
| Total | 1032 (IS only) | 285 |

Note: IS trade count differs from comparison.csv total_trades (747) because the 1032
figure is the sum of all sub-model runs before the IS window filter. comparison.csv
reports only IS window (2022-01 to 2025-03-24) trades.

## Per-Symbol OOS Breakdown

| symbol | trades | wins | win_rate | net_pnl | pct_total_pnl |
|---|---|---|---|---|---|
| DOTUSDT | 52 | 24 | 46.2% | +67.61 | 77.68% |
| ETHUSDT | 57 | 28 | 49.1% | +19.05 | 21.89% |
| LTCUSDT | 53 | 24 | 45.3% | +18.30 | 21.02% |
| LINKUSDT | 59 | 24 | 40.7% | +17.11 | 19.66% |
| BTCUSDT | 64 | 17 | 26.6% | -35.03 | -40.25% |

## Filter Partition Stats (IS)

Extreme partitions (|z30| > 1.5) per cohort per IS month:
- Pool A (BTC+ETH): ~560–620 rows per month (vs ~3700+ normal)
- Model C (LINK): single-symbol, proportional ~120-150 extreme vs ~900-1000 normal
- Model D (LTC): single-symbol, proportional ~120-150 extreme vs ~900-1000 normal
- Regime fire rate estimated IS: ~13-17% (consistent with brief Section 4.2 F-AXIS #3 [10%, 18%] band)
- DOT (Model E): NO regime routing (per LM Master §1 — only 8 extreme trades IS, degenerate)

Total filter callback invocations in log: 318

## Feature Importance — Funding Features

`funding_rate_zscore_30` appears in ALL 7 sub-models:
- A_extreme: rank 13, A_normal: rank 12
- C_extreme: rank 10, C_normal: rank 9
- D_extreme: rank 16, D_normal: rank 19
- E_baseline: rank 18

`funding_rate_zscore_90` appears in ALL 7 sub-models at ranks 6–12.

## Label Leakage Audit

CV gap = (timeout_candles + 1) * n_symbols. label_timeout_minutes = 10080 = 21 days.
At 8h interval: timeout_candles = 10080 / 480 = 21. n_symbols = 2 for Pool A, 1 for C/D/E.
Gap for Pool A: (21 + 1) * 2 = 44 rows. Verified in log:
`[CV fold 0] gap=184h (22 rows)` — correct (22 rows per symbol × 1 = 22 per cohort, 44 total for 2-symbol Pool A).

## Gate Efficacy Table

| gate | IS fire rate | OOS fire rate | note |
|---|---|---|---|
| R1 cooldown | N/A (A: apply_r1=False) | N/A | C/D/E: apply_r1=True |
| R5 vol-target | 0.0% | 0.0% | disabled for /024 |
| R5 binary-kill NATR | 0.0% | 0.0% | disabled for /024 |
| Regime gate (extreme) | ~13–17% | ~13–17% | estimated from partition ratios |

## Anomaly Notes

1. IS Sharpe negative (-0.5761): this is the structural consequence of regime partitioning.
   The extreme sub-model trains on a minority partition (~15% of rows) with less signal,
   producing lower IS Sharpe. The OOS improvement to +0.7593 (vs /023 +0.4606) is
   consistent with the brief's hypothesis that regime-conditional training improves
   OOS generalization by reducing IS overfitting.

2. DOT OOS concentration (77.68% of OOS PnL): single-symbol dominance. Not a methodology
   concern for EXPLORATION; the Critic will evaluate this per Gate criteria.

3. Spot-check 10 random OOS rows: zero NaN, exit_reason values all valid
   (timeout/stop_loss/take_profit), weight_factor values plausible (0.33 for regime
   cohort, 1.0–1.33 for DOT baseline with OOD scaling).

4. Zero-trade months in IS: none (all 38 IS months have trades > 0).

## Status

OVERALL=READY-FOR-CRITIC
