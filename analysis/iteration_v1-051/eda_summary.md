# EDA Summary — iter-v1/051 — dot_vs_btc_ret_ratio_30

All values are INFORMATIONAL (per rule bf2c812/a6269df). No BLOCK on any EDA result — artifact existence is the gate criterion.

## ADF Stationarity

| Symbol | p-value | Status |
|---|---|---|
| DOTUSDT | 0.000000e+00 | PASS |

## IC Orthogonality (top 10 by |IC|)

| Peer Feature | |IC| | n_pairs | Status |
|---|---|---|---|
| trend_adx_14 | 0.1246 | 4906 | PASS |
| vol_bb_bandwidth_20 | 0.0844 | 4906 | PASS |
| interact_natr_x_adx | 0.0795 | 4906 | PASS |
| vol_range_spike_72 | 0.0566 | 4906 | PASS |
| oi_delta_30_z90 | 0.0547 | 3294 | PASS |
| mr_pct_from_high_20 | 0.0532 | 4906 | PASS |
| mr_pct_from_low_20 | 0.0446 | 4906 | PASS |
| vol_natr_14 | 0.0425 | 4906 | PASS |
| mom_roc_10 | 0.0388 | 4906 | PASS |
| stat_autocorr_lag5 | 0.0365 | 4906 | PASS |

## Distribution Stats

| Metric | Value |
|---|---|
| n | 4906 |
| mean | 0.013016 |
| std | 1.10656 |
| min | -6.95778 |
| p25 | -0.374122 |
| median | 0.0199649 |
| p75 | 0.425984 |
| max | 5.89013 |
| skew | -0.390842 |
| kurt | 4.63508 |
| pct_nan | 0.0236816 |
