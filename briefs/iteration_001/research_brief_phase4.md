# Phase 4: Data Filtering — Iteration 001

## Outlier Analysis

8h candle returns show kurtosis ~20 (extreme fat tails). 1.6% of candles have |return| > 10%. Notable outlier symbols:

- **DOGEUSDT**: kurtosis 104, skew +5.7 — meme pump/dump cycles
- **LUNAUSDT**: kurtosis 57, skew -4.5 — collapse event (May 2022)
- **1000LUNCBUSD**: kurtosis 68, skew +5.1 — post-collapse volatility

These extreme candles are real market events. They represent exactly the conditions the strategy will encounter in live trading. Removing them would create an unrealistically smooth backtest.

## Filtering Decisions

### 1. Outlier Handling: No Removal, No Winsorization

- Extreme candles are genuine market events, not data errors
- The triple-barrier labeling with SL=2% naturally limits exposure to these events
- Walk-forward training includes these events in their historical context
- **Decision**: Keep all data as-is. The SL mechanism is the outlier protection.

### 2. Volume Filter: None for Iteration 001

- Minimum quote volume at p10 is $3.3M per 8h candle — all symbols in our universe have meaningful liquidity
- The symbol selection criteria (1095+ IS candles, active USDT) already filters out extremely illiquid symbols
- Volume features (vol_volume_rel, vol_cmf, etc.) are available for the model to learn volume-dependent patterns
- **Decision**: No volume threshold. Let the model learn.

### 3. Minimum Symbol History: 1095 IS candles (already in Phase 3)

- Already required in symbol universe selection
- Ensures every symbol has at least 12 months of training data before first test month

### 4. Date Exclusions: None

- **LUNA collapse (May 2022)**: Kept. LUNAUSDT is a delisted USDT pair that the model should learn from. The walk-forward handles this correctly — models trained before May 2022 will predict May 2022 poorly, which is realistic.
- **Exchange outages**: Not systematically identifiable from candle data. The rare missing candles (gaps) are handled by the existing infrastructure.
- **Decision**: No date ranges excluded.

### 5. Feature NaN Handling

- Features with lookback windows (e.g., SMA-100, RSI-30) produce NaN for early rows
- The feature pipeline already handles this — first ~100 rows per symbol will have partial NaNs
- LightGBM handles NaN natively — no imputation needed
- **Decision**: No special NaN handling. LightGBM's built-in NaN routing is appropriate.

### 6. Pair Deduplication

- BUSD and USDC pairs are near-perfect correlates of USDT pairs (correlation >0.99)
- Including them would double-count the same market dynamics
- **Decision**: Already handled by Phase 3 symbol selection (USDT-only)

## Summary of Filters

| Filter | Action |
|--------|--------|
| Extreme returns | Keep (SL handles risk) |
| Volume threshold | None (all candidates are liquid) |
| Min history | 1095 IS candles (from Phase 3) |
| Date exclusions | None |
| Feature NaN | LightGBM native handling |
| Pair dedup | USDT-only (from Phase 3) |

This is a deliberately minimal filtering approach for iteration 001. If the backtest reveals specific data quality issues (e.g., model overfitting to LUNA collapse, concentrated losses in low-volume symbols), future iterations can add targeted filters.
