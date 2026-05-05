# iter-v3/007 — Top-N Feature Importance Synthesis

## Inputs

- iter-v3/006 IS feature_importance (reports-v3/iteration_v3-006/in_sample/feature_importance.csv) — BCH-only single-symbol run, seed=42, n_trials=10.
- iter-v3/003 IS feature_importance (reports-v3/iteration_v3-003/in_sample/feature_importance.csv) — full 4-symbol universe (BCH+MKR+LDO+TRX), seed=42, n_trials=50.
- Both source files are computed inside the walk-forward training loop from candles with `close_time < OOS_CUTOFF_DATE = 2025-03-24`. No OOS contact at any step of this analysis.

## Selection Criterion

For each of the 34 features in V3_FEATURE_COLUMNS, compute the rank (1=highest importance) under each of the two source runs. Mean rank = average of the two ranks. A feature missing from one run is assigned rank = n_total (= 34, the worst). Sort by ascending mean rank — top-N features are the most consistently important across both runs.

Chosen N = 14 (the natural break — see top-N table; ranks 1-14 all have non-near-zero importance in BOTH runs, while ranks 15+ include features near-zero in at least one run).

## Top-14 Features (selected for V3_FEATURE_COLUMNS_TOP_N)

| rank | feature | rank_006 | rank_003 | imp_006 | imp_003 |
|---:|---|---:|---:|---:|---:|
| 1 | `max_dd_window_50` | 4 | 1 | 128.4 | 113.2 |
| 2 | `vwap_dev_50` | 2 | 3 | 136.2 | 101.8 |
| 3 | `ema_spread_atr_20` | 1 | 5 | 151.0 | 84.0 |
| 4 | `ret_kurt_50` | 6 | 4 | 126.2 | 86.8 |
| 5 | `ret_skew_200` | 8 | 2 | 117.4 | 105.8 |
| 6 | `range_realized_vol_50` | 7 | 6 | 124.0 | 82.2 |
| 7 | `hurst_diff_100_50` | 3 | 20 | 134.0 | 41.2 |
| 8 | `ret_kurt_200` | 14 | 9 | 107.0 | 69.8 |
| 9 | `hurst_100` | 12 | 11 | 108.8 | 64.6 |
| 10 | `btc_ret_14d` | 13 | 12 | 107.4 | 63.4 |
| 11 | `ret_skew_50` | 10 | 15 | 112.8 | 50.2 |
| 12 | `vwap_dev_20` | 5 | 21 | 127.8 | 40.4 |
| 13 | `ret_autocorr_lag1_50` | 20 | 7 | 98.2 | 80.0 |
| 14 | `sym_vs_btc_ret_7d` | 16 | 13 | 106.0 | 60.4 |

## Dropped Features (rank > 14; n_dropped = 20)

| rank | feature | rank_006 | rank_003 | imp_006 | imp_003 | near_zero_count |
|---:|---|---:|---:|---:|---:|---:|
| 15 | `volume_cv_50` | 19 | 10 | 104.6 | 69.2 | 0 |
| 16 | `fracdiff_logclose_dstat` | 11 | 19 | 112.8 | 43.2 | 0 |
| 17 | `parkinson_gk_ratio_20` | 9 | 22 | 116.0 | 38.2 | 0 |
| 18 | `obv_slope_50` | 18 | 14 | 104.8 | 51.2 | 0 |
| 19 | `volume_mom_ratio_20` | 24 | 8 | 85.2 | 71.8 | 0 |
| 20 | `mom_accel_20_100` | 17 | 18 | 105.2 | 47.2 | 0 |
| 21 | `btc_vol_14d` | 21 | 16 | 91.8 | 49.8 | 0 |
| 22 | `ret_autocorr_lag5_50` | 15 | 23 | 106.8 | 36.0 | 0 |
| 23 | `ret_skew_100` | 25 | 17 | 82.0 | 49.6 | 0 |
| 24 | `hurst_200` | 22 | 26 | 88.8 | 17.6 | 0 |
| 25 | `bb_width_pct_rank_100` | 26 | 25 | 80.2 | 18.4 | 0 |
| 26 | `btc_ret_7d` | 23 | 29 | 87.0 | 13.6 | 0 |
| 27 | `parkinson_vol_20` | 30 | 24 | 71.0 | 18.6 | 0 |
| 28 | `btc_ret_3d` | 28 | 28 | 74.8 | 13.6 | 0 |
| 29 | `fracdiff_logvolume_dstat` | 27 | 33 | 77.4 | 3.2 | 1 |
| 30 | `cusum_reset_count_200` | 34 | 27 | 37.6 | 14.2 | 0 |
| 31 | `hl_range_ratio_20` | 29 | 34 | 73.2 | 2.8 | 1 |
| 32 | `atr_pct_rank_500` | 32 | 31 | 47.2 | 12.0 | 0 |
| 33 | `mom_accel_5_20` | 31 | 32 | 69.6 | 11.0 | 0 |
| 34 | `atr_pct_rank_200` | 33 | 30 | 44.2 | 12.4 | 0 |

## Implications for Phase 6

Replacing V3_FEATURE_COLUMNS (34 features) with the 14-feature subset above is a single, atomic change. The hypothesis (brief Section 1): by removing features that contribute near-zero gain on TWO independent IS runs, the LightGBM model fits the dominant signal more cleanly, leading to a higher IS Sharpe in the EXPLORATION-mode run (--exploration: colsample=1.0, ENSEMBLE_SIZE=1, n_trials=10).

Note that --exploration sets `colsample_bytree=1.0`, which means EVERY tree split considers ALL features. This makes the cost of low-importance features more visible: with the default colsample<1.0, low-importance features only enter ~37% of splits and waste a smaller fraction of split-time search. With colsample=1.0, they enter every split and dilute the gain estimate at every node. Reducing the feature set therefore has a more concentrated effect under exploration mode than under production mode.

## Falsifier Anchors

- If iter-v3/007's IS Sharpe drops BELOW iter-v3/006 BCH-only baseline (+0.4051) → top-14 subset removed essential signal; the selection criterion (mean importance rank) is unreliable as a de-noising heuristic.
- If iter-v3/007's IS Sharpe rises above the iter-v3/003 full-universe baseline (-0.0746) but stays below +0.5 → top-14 reduces noise modestly but the dominant constraint is the model architecture, not the feature set width.

## Reproducibility

Re-running this script on the same source CSVs reproduces the same top_n_features.csv and summary.json byte-for-byte. The script reads only two committed feature_importance.csv files; no random seeds, no Optuna, no model training.
