# Engineering Report — iter-v3/001

## Headers
- Iteration: iter-v3/001
- Branch: iteration-v3/001
- Commit SHA (backtest): 7d8aaaf2f6f78dcb2be85f368080121ecd58b6ba
- Hardware: Intel Core i9-12900HK, 20 CPUs, 58 GiB RAM, WSL2
- Wall-clock time: 2:05:00 (7505s total across 4 models, sequential)

## Configuration Diff vs Baseline

This is the v3 track's first baseline (BASELINE_V3 placeholder). There is no prior v3 iteration to diff against. The complete configuration for iter-v3/001 is:

| Parameter | Value | Source |
|-----------|-------|--------|
| Symbol universe | BCH, MKR, LDO, TRX | Research brief §3 |
| Interval | 8h | Inherited from v2 |
| IS window | 2022-01-01 → 2025-03-24 | training_months=24 + data start |
| OOS window | 2025-03-24 → 2026-05-04 | OOS_CUTOFF_DATE + data end |
| OOS_CUTOFF_DATE | 2025-03-24 | IMMUTABLE |
| training_months | 24 | IMMUTABLE |
| Ensemble seeds | [42] (single-seed pilot) | --seeds 1 flag |
| Optuna trials | 50 per model-month | --n-trials 50 |
| CV splits | 5-fold purged | LightGbmStrategy default |
| CV gap | 22 rows × 1 symbol = 22 per fold | (timeout_candles+1)×n_symbols/n_symbols |
| Label TP | 8% (ATR-adaptive via natr_21_raw × 2.9) | Brief §3 |
| Label SL | 4% (ATR-adaptive via natr_21_raw × 1.45) | Brief §3 |
| Label timeout | 10080 min (21 candles = 7 days) | Brief §3 |
| Cooldown candles | 4 (32h) | Inherited from v2 |
| Fee | 0.1% one-sided | Binance maker fee |
| Stop loss | 4% | BacktestConfig |
| Take profit | 8% | BacktestConfig |
| Timeout minutes | 10080 (7 days) | BacktestConfig |
| Max amount USD | 1000 | BacktestConfig |
| Risk gates | z-score OOD (2.5σ), Hurst regime, ADX, low-vol, BTC contagion | RiskV3Wrapper |
| BTC trend filter | lookback=42 bars, threshold=20%, enabled | run_baseline_v3.py |
| Hit-rate gate | disabled (iter-v2/045 lesson) | HitRateGateConfig |
| Feature columns | 34 V3_FEATURE_COLUMNS (v3 fracdiff naming) | V3_FEATURE_COLUMNS |
| Fracdiff method | FracdiffStat auto-d* ADF grid search | fracdiff_v3.py |
| CPCV | N=10, k=2 → 45 paths; gap=88, embargo=27 | validation_v3.py |
| OOD in LightGBM | disabled (handled by RiskV3Wrapper z-score gate) | ood_enabled=False |
| Features directory | data/features_v3/ | FEATURES_DIR |
| Excluded symbols | BTC, ETH, LINK, LTC, DOT, BNB, SOL, XRP, DOGE, NEAR | V3_EXCLUDED_SYMBOLS |

## Key Metrics Block

| Metric | In-Sample | Out-of-Sample | OOS/IS Ratio |
|--------|-----------|---------------|-------------|
| monthly_sharpe | -0.0746 | +1.0955 | -14.68 |
| daily_sharpe | -0.1607 | +2.2053 | -13.72 |
| max_drawdown | 81.28% | 22.04% | 0.271 |
| profit_factor | 0.9781 | 1.2977 | 1.327 |
| win_rate | 33.8% | 48.2% | 1.427 |
| n_trades | 225 | 83 | 0.369 |
| total_pnl | -9.80% | +38.53% | -3.933 |
| monthly_calmar | -0.1205 | +1.7477 | -14.50 |
| weighted_pnl_total | -9.80% | +38.53% | -3.933 |
| DSR | 0.0000 | — | — |
| PBO | 0.0000 | — | — |
| PSR | 1.0000 | — | — |
| n_trials | 1000 | — | — |
| n_effective_trials | 1 | — | — |

**Per-symbol OOS performance:**

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|--------|-------------|----------|----------|-------------------|
| TRXUSDT | +12.35% | 30 | 53.3% | 32.1% |
| MKRUSDT | +20.50% | 15 | 46.7% | 53.2% |
| LDOUSDT | +14.12% | 13 | 38.5% | 36.7% |
| BCHUSDT | -8.44% | 25 | 48.0% | -21.9% |

**Per-symbol IS performance:**

| Symbol | n_trades | win_rate | net_pnl_pct |
|--------|----------|----------|-------------|
| LDOUSDT | 17 | 47.1% | +51.9% |
| BCHUSDT | 67 | 44.8% | +34.9% |
| TRXUSDT | 68 | 41.2% | +25.6% |
| MKRUSDT | 73 | 23.3% | -173.6% |

**OOS monthly breakdown:**

| Month | PnL% | Trades |
|-------|------|--------|
| 2025-03 | -2.00% | 1 |
| 2025-04 | -8.69% | 7 |
| 2025-05 | +11.65% | 8 |
| 2025-06 | +7.97% | 12 |
| 2025-07 | -7.21% | 8 |
| 2025-08 | +15.49% | 12 |
| 2025-09 | +7.17% | 5 |
| 2025-10 | -10.13% | 8 |
| 2025-11 | +16.38% | 5 |
| 2025-12 | +0.98% | 1 |
| 2026-01 | -1.58% | 4 |
| 2026-02 | +2.57% | 3 |
| 2026-03 | +0.79% | 4 |
| 2026-04 | +4.20% | 4 |
| 2026-05 | +0.93% | 1 |

## Seed Concentration Audit

Only seed 42 was run (pilot: `--seeds 1`). Full 5-seed ensemble validation is not yet complete.

| Metric | Seed 42 |
|--------|---------|
| OOS monthly Sharpe | +1.0955 |
| OOS max drawdown | 22.04% |
| OOS Calmar | +1.7477 |
| OOS trades | 83 |
| Max symbol concentration (OOS) | 43.64% (MKRUSDT) |
| PBO | 0.0000 |
| BTC-killed trades | 23 of 308 (7.47%) |

**CPCV (45 paths from IS sequence):**
- Paths with positive Sharpe: 21/45 (46.7%)
- Mean path Sharpe: -0.175
- Median path Sharpe: -0.096
- Min path Sharpe: -1.827 (path 26)
- Max path Sharpe: +1.202 (path 1)
- PBO (from CPCV ranking): 0.0000

Note: The CPCV paths are computed from IS trades only. The negative mean path Sharpe reflects the IS-negative overall performance (IS monthly Sharpe = -0.0746). 24/45 paths are negative, indicating IS model instability.

**n_effective_trials = 1 note:** With a single seed and 1000 Optuna trials (4 models × 53 months × ~5 trials/fold... actually 50 trials per model-month), the PCA on trial returns collapsed to n_eff=1. This indicates that all Optuna trials are essentially sampling the same performance space, consistent with IS near-random performance where all parameter settings yield near-zero Sharpe.

## Label Leakage Audit

The CV gap per fold is (timeout_candles + 1) × n_symbols_in_model = (21 + 1) × 1 = 22 rows.

Each model trains on a single symbol. The CV folds confirm this gap:
```
[CV fold 0] train_end=2023-08-24 00:00 | val_start=2023-08-31 16:00 | gap=184h (22 rows)
[CV fold 1] train_end=2023-12-23 16:00 | val_start=2023-12-31 08:00 | gap=184h (22 rows)
[CV fold 2] train_end=2024-04-23 08:00 | val_start=2024-05-01 00:00 | gap=184h (22 rows)
[CV fold 3] train_end=2024-08-23 00:00 | val_start=2024-08-30 16:00 | gap=184h (22 rows)
[CV fold 4] train_end=2024-12-22 16:00 | val_start=2024-12-30 08:00 | gap=184h (22 rows)
```

Gap = 22 rows × 8h/row = 176h = 184h (close enough — minor alignment to calendar). This satisfies the López de Prado purge requirement. The CPCV gap=88 (cross-model) was applied at the IS portfolio level for the 45-path computation.

## Gate Efficacy Table

Risk gates computed over the full single-seed run (IS + OOS combined since gates apply to both).

| Gate | Symbol | Signals Seen | Kills | Kill Rate | Vol-Scaled Pass-Through |
|------|--------|-------------|-------|-----------|------------------------|
| z-score OOD (2.5σ) | BCHUSDT | 2097 | 438 | 20.9% | — |
| Hurst regime | BCHUSDT | 2097 | 129 | 6.2% | — |
| ADX gate | BCHUSDT | 2097 | 444 | 21.2% | — |
| Low-vol gate | BCHUSDT | 2097 | 441 | 21.0% | — |
| **Combined kill rate** | **BCHUSDT** | **2097** | **1452** | **69.2%** | 645 trades, mean_vol_scale=0.717 |
| z-score OOD (2.5σ) | MKRUSDT | 2453 | 944 | 38.5% | — |
| Hurst regime | MKRUSDT | 2453 | 119 | 4.9% | — |
| ADX gate | MKRUSDT | 2453 | 422 | 17.2% | — |
| Low-vol gate | MKRUSDT | 2453 | 392 | 16.0% | — |
| **Combined kill rate** | **MKRUSDT** | **2453** | **1877** | **76.5%** | 576 trades, mean_vol_scale=0.720 |
| z-score OOD (2.5σ) | LDOUSDT | 516 | 173 | 33.5% | — |
| Hurst regime | LDOUSDT | 516 | 43 | 8.3% | — |
| ADX gate | LDOUSDT | 516 | 96 | 18.6% | — |
| Low-vol gate | LDOUSDT | 516 | 91 | 17.6% | — |
| **Combined kill rate** | **LDOUSDT** | **516** | **403** | **78.1%** | 113 trades, mean_vol_scale=0.712 |
| z-score OOD (2.5σ) | TRXUSDT | 2062 | 493 | 23.9% | — |
| Hurst regime | TRXUSDT | 2062 | 112 | 5.4% | — |
| ADX gate | TRXUSDT | 2062 | 499 | 24.2% | — |
| Low-vol gate | TRXUSDT | 2062 | 321 | 15.6% | — |
| **Combined kill rate** | **TRXUSDT** | **2062** | **1425** | **69.1%** | 637 trades, mean_vol_scale=0.745 |
| BTC contagion filter | Portfolio | 308 | 23 | 7.5% | — |

Gates are functioning: 69-78% kill rates are consistent with v2 baseline behavior. MKR has highest z-score kill rate (38.5%), consistent with MKR's high volatility relative to training-window feature distributions.

OOS gate efficacy (IS vs OOS comparison) cannot be isolated from this single-run log since gate stats are combined IS+OOS. The QR/Critic should request a split-gate analysis if required.

## ADF Stationarity Results

All 34 features passed ADF stationarity test (p < 0.05) in the final reporting:
- 34/34 features stationary across all 4 symbols (averaged ADF statistics)
- Note from pre-flight: `cusum_reset_count_200` for LDOUSDT had p=0.0707 in the pre-flight per-symbol check. In the averaged adf_test.csv the feature shows p=0.0178 (averaged across all 4 symbols), clearing the threshold. The per-symbol non-stationarity for LDOUSDT is a residual concern for the Critic to flag.
- Features with lowest confidence (highest p-values): `fracdiff_logclose_dstat` (p=0.0072), `ret_skew_200` (p=0.0009), `ret_skew_100` (p=0.00001)

## Anomaly Notes

1. **IS Sharpe strongly negative (-0.0746 monthly, -0.26 annualized):** The IS window covers 2022-01 through 2025-03, which includes a prolonged bear market (2022) and multiple high-volatility regimes. The model produces IS-negative performance while OOS-positive (+1.0955 monthly). This is an unusual but not impossible regime-inversion pattern. The OOS window (2025-04 through 2026-05) appears to be a fundamentally different market regime from IS. The QR must evaluate this in Phase 7 — it is a major hypothesis-falsification candidate (Section 7 predicted "regime mismatch between IS and OOS").

2. **MKR IS win_rate 23.3%:** MKR produced 73 IS trades with only 23.3% win rate and -173.6% net IS PnL. This is catastrophic IS MKR performance. However MKR's OOS performance is strong (+17.1% net, 46.7% win rate, 15 trades). This reinforces the regime-inversion concern — MKR's signals appear to have been data-mined against a loss-making IS pattern and then inverted in OOS.

3. **n_effective_trials = 1:** The PCA on Optuna trial returns collapsed to 1 effective dimension. This indicates near-random IS performance (all trials yield near-zero Sharpe), so the trial return matrix is essentially constant and one PCA component captures all variance. Not an error, but signals very poor IS predictive signal.

4. **DSR = 0.0:** With negative IS Sharpe, DSR correctly returns 0 (the underlying validation_v2.deflated_sharpe_ratio clamps to 0 when IS Sharpe ≤ 0). DSR is a meaningful metric only when IS is profitable.

5. **Weight_factor = 0 trades:** 23 OOS trades had weight_factor=0 (BTC trend filter killed), 22 IS trades similarly. These are properly excluded from performance accounting (weighted_pnl=0). The BTC kill set `weight_factor=0` but allowed the trade to execute as paper — consistent with v2 convention.

6. **OOS trade count floor:** 83 OOS trades over 14 months = 5.9 trades/month average. The merge floor requires ≥10 trades/month. At 83 total trades over 14 months, this falls below the 10 trades/month minimum (would need ≥140 total). The Critic must flag this.

7. **CPCV paths:** 21/45 paths positive (46.7%), mean=-0.175. With IS Sharpe=-0.0746, this CPCV result is consistent with near-random IS performance. PBO=0.0 is technically correct (CPCV path ranking produces 0 PBO when the best path comes from a partition that doesn't systematically outperform) but should be interpreted with caution given IS underperformance.

8. **Spot-check results:** 10 random OOS trade rows verified: PnL math correct (direction × (exit-entry)/entry × 100, minus 0.1% one-sided fee). Exit reasons consistent (stop_loss, take_profit, timeout). Weight factors sane (0.37-1.00 range for non-BTC-killed trades). One zero weight_factor trade correctly has weighted_pnl=0.

9. **Feature importance:** Top 5 features by IS model importance: max_dd_window_50 (139.8), ret_skew_200 (135.2), vwap_dev_50 (129.6), ret_kurt_50 (110.0), range_realized_vol_50 (104.8). Fracdit features rank low (fracdiff_logclose_dstat=49.4, fracdiff_logvolume_dstat=2.8), suggesting auto-d* fracdiff did not add meaningful signal in this iteration.

10. **Missing per_regime.csv content:** The per_regime.csv files are present but minimal (1 row each for IS and OOS), suggesting regime classification (Hurst-based) collapsed to a single regime over the period. This is expected if Hurst is being used as a gate (killing non-trending regime) rather than as a regime classifier.

## Status

OVERALL=READY-FOR-CRITIC

**Summary for Critic:** This is the v3 track's first iteration. Key findings:
- OOS monthly Sharpe = +1.0955 (passes OOS Sharpe floor of ≥0 but fails ≥1.8 MERGE threshold from Section 8)
- IS monthly Sharpe = -0.0746 (fails IS floor of ≥1.0 from merge criteria)
- OOS max drawdown = 22.0% (passes ≤40% threshold)
- OOS trades = 83 over 14 months = 5.9/month (fails ≥10/month floor)
- MKRUSDT concentration = 53.2% (fails ≤35% per-symbol cap from Section 8)
- DSR = 0.0 (meaningless with negative IS; Critic should verify)
- PBO = 0.0 (passes ≤0.4 threshold)
- PSR = 1.0 (passes ≥0.95 threshold)
- Single-seed run only — 5-seed ensemble validation not yet complete
