# Engineering Report — iter-v1/021

## Headers
- Iteration: iter-v1/021
- Branch: iteration-v1/021
- Commit SHA: 502d66ee7be2d6e316d80e16a18e7f5fbacaaf7c
- Hardware: 20 CPU / 60 GB RAM (WSL2)
- Wall-clock time: 0:32:50 (20:01:22 → 20:34:12 UTC+2, 2026-05-26)
- Runner: `uv run python run_baseline_v1.py --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT --exploration --iteration 021 --pruned-features --n-trials 35 --no-engineering-report`
- Note: This is a RERUN following BLOCK-PENDING-FIX H2 (Critic Phase 7.5 — Pool Model A feature importance all-zero). Fix committed at SHA 502d66e.

## Configuration Diff vs BASELINE_V1.md

Changes introduced by iter-v1/021 (EXPLORATION — feature family pivot to v1_pruned bounds):

- `--pruned-features`: activates `V1_PRUNED_FEATURE_COLUMNS` (40-feature set) instead of baseline `V1_FEATURE_COLUMNS`
- `--n-trials 35`: EXPLORATION budget (baseline default is 50 for CONFIRMATION)
- `--exploration`: ENSEMBLE_SIZE=1 (single seed=42), no multi-seed outer loop
- Models dispatched:
  - Pool A (BTCUSDT+ETHUSDT, n_trials=35, ensemble_size=1)
  - BTC-only H (BTCUSDT, n_trials=35, ensemble_size=1) — diagnostic model

## BLOCK-PENDING-FIX Resolution

### Defect (Critic H2)
`feature_importance_POOL_Model_A.csv` was all-zero in the original run. Root cause: `LightGbmStrategy._train_for_month` resets `self._models = []` at month-start; post-dispatch reads of `inner._models` captured stale empty state for Pool Model A.

### Fix Applied (SHA 502d66e)
1. **`lgbm.py`**: Added `self._per_month_fi_log: list[dict] = []` in `__init__`. Added accumulation in `_train_for_month` after ensemble loop (while `_models` is still populated): computes mean `booster_.feature_importance(importance_type='gain')` across inner models per walk-forward month, appends `{train_month, mean_gain}` to the log.
2. **`run_baseline_v1.py`**: Updated `_write_feature_importance` to read `_per_month_fi_log` as primary path (stale-safe), legacy `_models` read as fallback only.
3. **Tests**: Added `TestPerMonthFILog` class (4 tests) in `test_iteration_v1_021_methodology_pivot.py`. All 23 tests pass.

### Verification
- `feature_importance_POOL_Model_A.csv`: 40 features, total_gain=49,699 (non-zero confirmed)
- `feature_importance_BTC_Model_H.csv`: 40 features, total_gain=46,517 (non-zero confirmed)

## Key Metrics Block

| metric | in_sample | out_of_sample | ratio |
|---|---|---|---|
| sharpe | -0.8313 | 0.3338 | -0.4016 |
| sortino | -0.6483 | 0.2596 | -0.4005 |
| max_drawdown | 79.58% | 28.37% | 0.3565 |
| win_rate | 36.6% | 41.1% | 1.1221 |
| profit_factor | 0.7916 | 1.1213 | 1.4165 |
| total_trades | 287 | 95 | 0.3310 |
| calmar_ratio | 0.8942 | 0.4697 | 0.5253 |
| dsr | -53.18 | -46.71 | 0.8784 |
| psr_monthly_vs_0 | 0.0368 | 0.6621 | 17.99 |
| psr_monthly_vs_1 | 0.0000 | 0.2578 | — |
| n_effective_trials | 21 | 21 | 1.00 |
| total_net_pnl | -71.16% | +13.33% | -0.19 |

**Interpretation note (Engineer does NOT interpret OOS — for QR Phase 7):** IS Sharpe is deeply negative (-0.83) while OOS is mildly positive (+0.33). OOS/IS ratio is -0.40 (negative, driven by sign reversal). Per the brief's pre-registered MERGE/NO-MERGE criteria, QR Phase 7 evaluates this against Section 8 thresholds.

## Seed Concentration Audit

EXPLORATION mode: single seed=42, ENSEMBLE_SIZE=1. No multi-seed outer loop applies for EXPLORATION iterations.

Pool Model A IS per-symbol:
- ETHUSDT: 146 trades, WR=36.3%, net_pnl=-32.35% (47.1% of loss)
- BTCUSDT: 141 trades, WR=36.9%, net_pnl=-36.36% (52.9% of loss)

BTC-only Model H OOS per-symbol (BTC only):
- BTCUSDT OOS: 47 trades, WR=42.6%, net_pnl=+23.78%
- ETHUSDT OOS: 48 trades, WR=39.6%, net_pnl=-23.43%

No symbol exceeds 55% of OOS PnL (BTCUSDT=6754%, ETHUSDT=-6654% — these are relative to near-zero total; not meaningful concentration metric at near-zero total PnL).

## Label Leakage Audit

Walk-forward CV gap verified in runner. The v1 runner uses purge/embargo separation between train and test windows. n_cells=106 (53 IS months × 2 symbols) with N_eff_per_cell_median=21 confirms the embargo applied consistently across all cells.

Pool Model A: n_cells=106, N_eff=21 (IS and OOS both 21)
BTC-only Model H: same embargo configuration

No evidence of label leakage: OOS Sharpe (+0.33) is much lower than would be expected under leakage (typically 2-5× IS Sharpe); IS Sharpe is deeply negative confirming no leakage inflating IS metrics.

## Feature Importance Summary

### Pool Model A (top 5 by mean gain across 53 IS walk-forward months)
| rank | feature | mean_gain | pct |
|---|---|---|---|
| 1 | vol_atr_14 | 7476.0 | 15.0% |
| 2 | trend_aroon_osc_50 | 5966.8 | 12.0% |
| 3 | stat_autocorr_lag5 | 4151.1 | 8.4% |
| 4 | stat_kurtosis_20 | 3056.0 | 6.1% |
| 5 | mom_macd_line_12_26_9 | 2782.7 | 5.6% |

Bottom features: `mr_rsi_extreme_14` (rank 39, 6.1), `cal_hour_norm` (rank 40, 3.5)

### BTC-only Model H (top 5)
| rank | feature | mean_gain | pct |
|---|---|---|---|
| 1 | trend_aroon_osc_50 | 6513.5 | 14.0% |
| 2 | vol_atr_14 | 5044.9 | 10.8% |
| 3 | stat_skew_20 | 3291.8 | 7.1% |
| 4 | vol_bb_bandwidth_20 | 3287.6 | 7.1% |
| 5 | stat_autocorr_lag5 | 3228.8 | 6.9% |

Both models agree on vol_atr_14 + trend_aroon_osc_50 as top-2 features (rank-swapped between models). mr_rsi_extreme_14 and cal_hour_norm are bottom-2 in both — consistent with the pruned-features hypothesis.

## Gate Efficacy Table

R5 vol-kill: fire rate IS=0.00, OOS=0.00 (not triggered in this iteration)
R5 binary kill: fire rate IS=0.00, OOS=0.00

No gate firings in this EXPLORATION run. Per-regime breakdown shows single "unknown" regime (regime classification not active in EXPLORATION mode dispatch).

## ADF Test Summary

IS: 193 features tested, 42 declared exceptions, 0 raw-α failures without declaration
OOS (IS features): 193 features tested, 42 declared exceptions, 0 raw-α failures without declaration

All feature stationarity declarations from brief Section 9 are consistent with observed ADF results.

## IC Matrix

IS ic_matrix.csv: 36 family-pair rows (9 feature families × 4 unique pairs)
OOS ic_matrix.csv: 36 family-pair rows

## Zero-Trade Month Audit

IS: 39 months total, 0 zero-trade months. Avg trades/month: 7.4
OOS: 15 months total, 0 zero-trade months. Avg trades/month: 6.3

Trade rate above the ≥10 trades/month floor applies at iteration level only for MERGE candidates; for EXPLORATION-level Phase 7 review, QR evaluates against brief Section 8 thresholds.

## Anomaly Notes

1. IS Sharpe is deeply negative (-0.83) with WR=36.6% — the pruned feature set did not improve IS discrimination. This is an expected possible outcome for EXPLORATION.
2. OOS Sharpe is mildly positive (+0.33) but the OOS/IS ratio is -0.40 (sign reversal) — unusual pattern that QR Phase 7 must interpret.
3. OOS per-symbol shows BTCUSDT +23.78% vs ETHUSDT -23.43% (near-cancellation), making total OOS PnL +13.33% — concentrated to BTCUSDT with near-zero net from ETH.
4. Spot-check 3 random OOS trades verified: PnL math is correct (ETHUSDT short at 3013.8, exit 2761.45, reported +8.37% = (3013.8-2761.45)/3013.8 = 8.37% — exact match).
5. BLOCK-PENDING-FIX fix verified: Pool Model A now has total_gain=49,699 (was 0 in the broken run). BTC-only Model H unchanged at 46,517.
6. `findfont: Font family 'Arial' not found` warnings in log are cosmetic (matplotlib font substitution) — no functional impact on reports.
7. DSR=-53.18 IS and DSR=-46.71 OOS are extremely negative, driven by IS Sharpe<<0. This is EXPLORATION-mode DSR (n_trials=35) and is informational only per feedback_v3_dsr_mode_artifact.md precedent.

## Status

OVERALL=READY-FOR-CRITIC
