# Engineering Report: Iteration 003

## Implementation Summary

Added `feature_columns` parameter to `LightGbmStrategy`. When provided, filters discovered features to the specified list.

## Changes

### `lgbm.py`
- Added `feature_columns: list[str] | None = None` parameter to `__init__`
- In `compute_features()`, intersects provided list with discovered columns

## Deviation from Brief

The brief specified 40 features. However, only **25 survived** the parquet file intersection (`_discover_feature_columns` takes the intersection across ALL parquet files). The 15 missing features (including the top 3 by importance: vol_ad, vol_vwap, vol_obv) are absent from some symbols' parquet files.

## Results

- 211,056 total trades (vs 195,642 in iter 002) — 8% more
- 36,606 OOS trades (vs 26,545) — 38% more
- Win rate slightly improved: 31.2% vs 30.7%
- OOS Sharpe worsened: -2.17 vs -1.96
- Runtime: 6,993s (vs ~16,910s for iter 002) — 2.4x faster
