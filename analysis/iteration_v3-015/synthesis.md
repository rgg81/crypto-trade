# iter-v3/015 — TBR z-score 30 EDA Synthesis

## Decision

Candidate feature: **tbr_zscore_30** = z-score of (taker_buy_quote_volume / quote_volume) over rolling 30-bar window (~10 days at 8h cadence).


## Coverage check (IS window only)

| symbol   |   n_is_total |   n_valid_tbr_raw |   n_valid_tbr_zscore_30 |   coverage_zscore_pct | date_start          | date_end            |
|:---------|-------------:|------------------:|------------------------:|----------------------:|:--------------------|:--------------------|
| BCHUSDT  |         2193 |              2193 |                    2193 |                   100 | 2023-03-24 00:00:00 | 2025-03-23 16:00:00 |
| LDOUSDT  |         2193 |              2193 |                    2193 |                   100 | 2023-03-24 00:00:00 | 2025-03-23 16:00:00 |
| TRXUSDT  |         2193 |              2193 |                    2193 |                   100 | 2023-03-24 00:00:00 | 2025-03-23 16:00:00 |


Min coverage: 100.00% (PASS — floor 80.0%)


## Distribution check

| symbol   | feature       |    n |      mean |    median |      std |       p01 |       p05 |       p25 |      p75 |      p95 |      p99 |
|:---------|:--------------|-----:|----------:|----------:|---------:|----------:|----------:|----------:|---------:|---------:|---------:|
| BCHUSDT  | tbr_raw       | 2193 |  0.491888 |  0.491883 | 0.018325 |  0.448762 |  0.462619 |  0.480556 | 0.503423 | 0.52034  | 0.535281 |
| BCHUSDT  | tbr_zscore_30 | 2193 | -0.004995 | -0.009696 | 1.0048   | -2.35091  | -1.64371  | -0.688452 | 0.673393 | 1.63299  | 2.28613  |
| LDOUSDT  | tbr_raw       | 2193 |  0.486024 |  0.486401 | 0.019602 |  0.440138 |  0.452678 |  0.473367 | 0.498956 | 0.516575 | 0.530883 |
| LDOUSDT  | tbr_zscore_30 | 2193 | -0.000758 |  0.019228 | 1.00272  | -2.37542  | -1.67277  | -0.664468 | 0.675259 | 1.63753  | 2.3121   |
| TRXUSDT  | tbr_raw       | 2193 |  0.496636 |  0.49695  | 0.024713 |  0.436358 |  0.456852 |  0.481122 | 0.512318 | 0.53641  | 0.559886 |
| TRXUSDT  | tbr_zscore_30 | 2193 |  0.001981 |  0.008883 | 0.991321 | -2.29737  | -1.62781  | -0.651147 | 0.650561 | 1.5869   | 2.44468  |


## Correlation gate (vs 13 V3_FEATURE_COLUMNS)

Max |IC| across all (symbol × V3col) pairs: **0.1654**, reached at (LDOUSDT, vwap_dev_20).


Per-symbol max |IC|: BCHUSDT = 0.1518, LDOUSDT = 0.1654, TRXUSDT = 0.1354


IC gate (< 0.7): **PASS**


## Rank-IC vs forward returns (predictive signal)

| symbol   | feature       |   horizon_bars |   horizon_days |   n_pairs |   rank_ic_spearman |
|:---------|:--------------|---------------:|---------------:|----------:|-------------------:|
| BCHUSDT  | tbr_zscore_30 |              1 |           0.33 |      2192 |            0.00429 |
| BCHUSDT  | tbr_zscore_30 |              3 |           1    |      2190 |            0.01657 |
| BCHUSDT  | tbr_zscore_30 |              7 |           2.33 |      2186 |            0.06493 |
| LDOUSDT  | tbr_zscore_30 |              1 |           0.33 |      2192 |           -0.0265  |
| LDOUSDT  | tbr_zscore_30 |              3 |           1    |      2190 |           -0.01979 |
| LDOUSDT  | tbr_zscore_30 |              7 |           2.33 |      2186 |           -0.01426 |
| TRXUSDT  | tbr_zscore_30 |              1 |           0.33 |      2192 |           -0.01309 |
| TRXUSDT  | tbr_zscore_30 |              3 |           1    |      2190 |           -0.00698 |
| TRXUSDT  | tbr_zscore_30 |              7 |           2.33 |      2186 |            0.00399 |



## Overall verdict

- Coverage gate: **PASS**

- IC redundancy gate (< 0.7): **PASS**

- Non-trivial rank-IC (max |IC| >= 0.02): **PASS**


**Final**: candidate is tractable for iter-v3/015 EXPLORATION as a single new feature added to V3_FEATURE_COLUMNS (13 → 14).
