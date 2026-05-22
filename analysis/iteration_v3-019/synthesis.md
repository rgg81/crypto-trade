# iter-v3/019 — Funding Rate Z-score (funding_rate_zscore_30) EDA Synthesis

## Decision

Candidate feature: **funding_rate_zscore_30** = z-score of Binance Futures funding rate over rolling 30-bar window (~10 days = 9 funding cycles at 8h cadence).


## Funding-rate kline alignment (sanity check)

| symbol   |   funding_kline_align_pct |
|:---------|--------------------------:|
| BCHUSDT  |                       100 |
| LDOUSDT  |                       100 |
| TRXUSDT  |                       100 |


Min alignment: 100.00% (PASS — floor 95%)


## Coverage check (IS window only)

| symbol   |   n_is_total |   n_valid_funding_raw |   n_valid_funding_zscore_30 |   coverage_zscore_pct | date_start          | date_end            |   funding_kline_align_pct |
|:---------|-------------:|----------------------:|----------------------------:|----------------------:|:--------------------|:--------------------|--------------------------:|
| BCHUSDT  |         2193 |                  2193 |                        2193 |                   100 | 2023-03-24 00:00:00 | 2025-03-23 16:00:00 |                       100 |
| LDOUSDT  |         2193 |                  2193 |                        2193 |                   100 | 2023-03-24 00:00:00 | 2025-03-23 16:00:00 |                       100 |
| TRXUSDT  |         2193 |                  2193 |                        2193 |                   100 | 2023-03-24 00:00:00 | 2025-03-23 16:00:00 |                       100 |


Min coverage: 100.00% (PASS — floor 80.0%)


## Distribution check

| symbol   | feature                |    n |         mean |    median |           std |     skew |      kurt |       p01 |       p05 |       p25 |      p75 |      p95 |      p99 |
|:---------|:-----------------------|-----:|-------------:|----------:|--------------:|---------:|----------:|----------:|----------:|----------:|---------:|---------:|---------:|
| BCHUSDT  | funding_rate           | 2193 |    -2.9e-05  | -1e-06    |      0.000205 |  -0.8881 |    8.3956 | -0.000656 | -0.000351 | -0.000121 | 0.0001   | 0.000101 | 0.000566 |
| BCHUSDT  | funding_rate_zscore_30 | 2193 |  1420.76     |  0.281409 |  66532        |  46.8295 | 2193      | -4.79265  | -2.06316  | -0.434442 | 0.717049 | 1.50845  | 3.25766  |
| LDOUSDT  | funding_rate           | 2193 |     0.000129 |  0.0001   |      0.000151 |   2.9862 |   12.9057 | -0.000133 | -1.1e-05  |  9.6e-05  | 0.0001   | 0.000426 | 0.000824 |
| LDOUSDT  | funding_rate_zscore_30 | 2193 | -6336.76     |  0.262701 | 140863        | -26.4046 |  757.244  | -6.80391  | -2.37973  | -0.517989 | 0.55451  | 1.53626  | 3.56668  |
| TRXUSDT  | funding_rate           | 2193 |     3e-06    |  6.7e-05  |      0.000194 |  -1.1011 |    6.1419 | -0.000669 | -0.000367 | -7e-05    | 0.0001   | 0.00021  | 0.000467 |
| TRXUSDT  | funding_rate_zscore_30 | 2193 | -7830.48     |  0.286318 | 366664        | -46.8295 | 2193      | -4.57059  | -2.53232  | -0.582874 | 0.7164   | 1.2306   | 2.31388  |


## ADF stationarity check

| symbol   | feature                |   adf_stat |   adf_p | pass_threshold   |    n |
|:---------|:-----------------------|-----------:|--------:|:-----------------|-----:|
| BCHUSDT  | funding_rate_zscore_30 |   -46.8188 |       0 | True             | 2193 |
| LDOUSDT  | funding_rate_zscore_30 |   -46.8923 |       0 | True             | 2193 |
| TRXUSDT  | funding_rate_zscore_30 |   -46.8188 |       0 | True             | 2193 |


ADF gate (p < 0.05): **PASS**


## Correlation gate (vs 13 V3_FEATURE_COLUMNS)

Max |IC| across all (symbol × V3col) pairs: **0.3758**, reached at (TRXUSDT, vwap_dev_20).


Per-symbol max |IC|: BCHUSDT = 0.2192, LDOUSDT = 0.2417, TRXUSDT = 0.3758


IC redundancy hard gate (< 0.7): **PASS**


IC strict brief target (< 0.5): **PASS**


### Full IC matrix (symbol × V3 feature)

| symbol   | against               |   ic_spearman |   n_pairs |
|:---------|:----------------------|--------------:|----------:|
| BCHUSDT  | max_dd_window_50      |        0.0892 |      2193 |
| BCHUSDT  | ema_spread_atr_20     |        0.127  |      2193 |
| BCHUSDT  | ret_kurt_50           |       -0.0495 |      2193 |
| BCHUSDT  | ret_skew_200          |        0.0316 |      2193 |
| BCHUSDT  | range_realized_vol_50 |       -0.1252 |      2193 |
| BCHUSDT  | hurst_diff_100_50     |        0.0263 |      2193 |
| BCHUSDT  | ret_kurt_200          |       -0.0652 |      2193 |
| BCHUSDT  | hurst_100             |       -0.0315 |      2193 |
| BCHUSDT  | btc_ret_14d           |        0.0606 |      2193 |
| BCHUSDT  | ret_skew_50           |        0.0691 |      2193 |
| BCHUSDT  | vwap_dev_20           |        0.2192 |      2193 |
| BCHUSDT  | ret_autocorr_lag1_50  |       -0.0339 |      2193 |
| BCHUSDT  | sym_vs_btc_ret_7d     |        0.1319 |      2193 |
| LDOUSDT  | max_dd_window_50      |        0.0234 |      2193 |
| LDOUSDT  | ema_spread_atr_20     |        0.1922 |      2193 |
| LDOUSDT  | ret_kurt_50           |        0.0012 |      2193 |
| LDOUSDT  | ret_skew_200          |       -0.0191 |      2193 |
| LDOUSDT  | range_realized_vol_50 |       -0.1348 |      2193 |
| LDOUSDT  | hurst_diff_100_50     |       -0.0921 |      2193 |
| LDOUSDT  | ret_kurt_200          |        0.0257 |      2193 |
| LDOUSDT  | hurst_100             |       -0.0476 |      2193 |
| LDOUSDT  | btc_ret_14d           |        0.1459 |      2193 |
| LDOUSDT  | ret_skew_50           |        0.0263 |      2193 |
| LDOUSDT  | vwap_dev_20           |        0.2417 |      2193 |
| LDOUSDT  | ret_autocorr_lag1_50  |        0.1223 |      2193 |
| LDOUSDT  | sym_vs_btc_ret_7d     |        0.1561 |      2193 |
| TRXUSDT  | max_dd_window_50      |       -0.0089 |      2193 |
| TRXUSDT  | ema_spread_atr_20     |        0.1245 |      2193 |
| TRXUSDT  | ret_kurt_50           |       -0.0505 |      2193 |
| TRXUSDT  | ret_skew_200          |       -0.0311 |      2193 |
| TRXUSDT  | range_realized_vol_50 |       -0.0366 |      2193 |
| TRXUSDT  | hurst_diff_100_50     |       -0.0082 |      2193 |
| TRXUSDT  | ret_kurt_200          |       -0.0012 |      2193 |
| TRXUSDT  | hurst_100             |       -0.006  |      2193 |
| TRXUSDT  | btc_ret_14d           |        0.063  |      2193 |
| TRXUSDT  | ret_skew_50           |        0.0151 |      2193 |
| TRXUSDT  | vwap_dev_20           |        0.3758 |      2193 |
| TRXUSDT  | ret_autocorr_lag1_50  |        0.0983 |      2193 |
| TRXUSDT  | sym_vs_btc_ret_7d     |        0.0922 |      2193 |


## Rank-IC vs forward returns (predictive signal)

| symbol   | feature                |   horizon_bars |   horizon_days |   n_pairs |   rank_ic_spearman |
|:---------|:-----------------------|---------------:|---------------:|----------:|-------------------:|
| BCHUSDT  | funding_rate_zscore_30 |              1 |           0.33 |      2192 |           -0.00022 |
| BCHUSDT  | funding_rate_zscore_30 |              3 |           1    |      2190 |           -0.01937 |
| BCHUSDT  | funding_rate_zscore_30 |              7 |           2.33 |      2186 |           -0.01033 |
| LDOUSDT  | funding_rate_zscore_30 |              1 |           0.33 |      2192 |           -0.01007 |
| LDOUSDT  | funding_rate_zscore_30 |              3 |           1    |      2190 |           -0.02287 |
| LDOUSDT  | funding_rate_zscore_30 |              7 |           2.33 |      2186 |           -0.02342 |
| TRXUSDT  | funding_rate_zscore_30 |              1 |           0.33 |      2192 |            0.01626 |
| TRXUSDT  | funding_rate_zscore_30 |              3 |           1    |      2190 |           -0.02179 |
| TRXUSDT  | funding_rate_zscore_30 |              7 |           2.33 |      2186 |           -0.0485  |


Max |rank-IC| across symbols × horizons: **0.0485**


Non-trivial rank-IC (>= 0.02): **PASS** (this is informational at EDA — non-trivial rank-IC is desirable but not REQUIRED; LightGBM can extract signal from features with weak univariate rank-IC via tree interactions)


## Saturation predictor (IS trade count band)

Anchor: iter-v3/018 IS trades = 172 (cumulative across 3 symbols at primary seed 42 = multi-seed mean cumulative)


Predicted IS trade band (±25% per `feedback_axis_saturation_predictor.md`): **[129, 215]**


Mechanism: funding_rate_zscore_30 enters LightGBM feature space at iter-v3/019 — it does NOT directly gate trades (no risk gate uses it). Trade selection changes ONLY via Optuna's reshaped loss surface. Most likely outcome: trade timing redirection within the universe, not wholesale add/remove. Predicted IS trade count IN BAND on the basis that the 14-feature stack hyperparameters (n_estimators, learning_rate, depth, colsample_bytree) are similar enough to keep trade counts within ±25% with high confidence — same operating regime as iter-v3/015 (13 → 14 features observed 209 → 205, -1.9% change).


**Falsifier (per `feedback_axis_saturation_predictor.md`)**: if observed IS trade count < 129 or > 215, the EXPLORATION outcome will be classified differently than the central prediction — potentially EXPLORATION-NEGATIVE-no-effect (if axis was saturated and produced bit-identical roster) or NEGATIVE-failed-axis (if behavioral change exceeded predicted band).


## Overall verdict

- Funding-kline alignment gate (>= 95%): **PASS**

- Coverage gate (>= 80.0%): **PASS**

- IC redundancy hard gate (< 0.7): **PASS**

- IC strict brief target (< 0.5): **PASS**

- ADF stationarity gate (p < 0.05): **PASS**

- Non-trivial rank-IC (informational): **PASS**


**Final**: candidate is TRACTABLE for iter-v3/019 EXPLORATION (single new feature added to V3_FEATURE_COLUMNS, 13 → 14).
