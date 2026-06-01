# EDA Summary — iter-v1/053

Multi-seed validation iter; EDA same as /052 by construction.

Features unchanged: `btc_funding_rate_8h_impulse`, `btc_funding_spread_30_90`.
Values below are recomputed for idempotent verification only.

All values are INFORMATIONAL. No ABORT on any threshold — artifact existence is the Phase 5.5 gate criterion.

Symbol: BTCUSDT | IS barrier: `close_time < 1742774400000`

## ADF Stationarity

| Feature | p-value | Status |
|---|---|---|
| btc_funding_rate_8h_impulse | 0.000000e+00 | PASS |
| btc_funding_spread_30_90 | 5.024015e-24 | PASS |

## IC Orthogonality — Top 10 by |IC| per new feature


### btc_funding_rate_8h_impulse

| Peer Feature | |IC| | n_pairs | Status |
|---|---|---|---|
| funding_rate_zscore_30 | 0.5067 | 5575 | MODERATE_IC (informational) abs=0.5067 |
| funding_rate_zscore_90 | 0.4911 | 5637 | MODERATE_IC (informational) abs=0.4911 |
| stat_return_5 | 0.0952 | 5637 | PASS |
| long_short_zscore_30 | 0.0754 | 4195 | PASS |
| trend_ema_cross_5_12 | 0.0690 | 5637 | PASS |
| mom_roc_10 | 0.0649 | 5637 | PASS |
| trend_minus_di_14 | 0.0647 | 5637 | PASS |
| mom_rsi_14 | 0.0642 | 5637 | PASS |
| interact_rsi_x_natr | 0.0637 | 5637 | PASS |
| trend_plus_di_14 | 0.0635 | 5637 | PASS |

### btc_funding_spread_30_90

| Peer Feature | |IC| | n_pairs | Status |
|---|---|---|---|
| funding_rate_zscore_30 | 0.5173 | 5575 | MODERATE_IC (informational) abs=0.5173 |
| trend_aroon_osc_50 | 0.1947 | 5575 | PASS |
| mom_macd_hist_12_26_9 | 0.1429 | 5575 | PASS |
| funding_rate_zscore_90 | 0.1315 | 5575 | PASS |
| interact_rsi_x_adx | 0.1170 | 5575 | PASS |
| mom_macd_line_12_26_9 | 0.1154 | 5575 | PASS |
| trend_supertrend_14_3 | 0.0874 | 5575 | PASS |
| mom_rsi_14 | 0.0760 | 5575 | PASS |
| interact_rsi_x_natr | 0.0759 | 5575 | PASS |
| mr_rsi_extreme_14 | 0.0758 | 5575 | PASS |

## Distribution Statistics


### btc_funding_rate_8h_impulse

| Metric | Value |
|---|---|
| n | 5637 |
| mean | 0.00419789 |
| std | 1.07527 |
| min | -8.42827 |
| p25 | -0.295722 |
| median | 0 |
| p75 | 0.320707 |
| max | 9.40564 |
| skew | 0.180124 |
| kurt | 8.71746 |
| pct_nan | 0.015715 |

### btc_funding_spread_30_90

| Metric | Value |
|---|---|
| n | 5575 |
| mean | -0.0248081 |
| std | 0.917185 |
| min | -10.2044 |
| p25 | -0.388936 |
| median | 0.0067386 |
| p75 | 0.394413 |
| max | 10.0294 |
| skew | -1.64786 |
| kurt | 40.1746 |
| pct_nan | 0.0265409 |
