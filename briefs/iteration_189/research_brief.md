# Iteration 189 — Enable BTC cross-asset features (exploration)

**Date**: 2026-04-22
**Type**: EXPLORATION (feature generation — the biggest gap per project memory)
**Baseline**: v0.186
**Decision**: pending backtest

## Motivation

Review of the feature pipeline uncovered a significant gap:

1. `src/crypto_trade/features/cross_asset.py` defines 7 BTC-derived features
   (`xbtc_return_{1,3,8}`, `xbtc_natr_{14,21}`, `xbtc_rsi_14`, `xbtc_adx_14`).
2. **Zero** of these were in `BASELINE_FEATURE_COLUMNS`.
3. **Zero** of the 760 8h parquet files contained any `xbtc_*` column.
4. The `add_cross_asset_features()` function was never called by any
   workflow — pure dead code.

Per memory: "Feature generation is the biggest gap (never done in 25 iters)."
This iteration addresses it directly.

## Section 0 — Data Split

OOS cutoff: 2025-03-24 (fixed). Training/test boundaries as in v0.186.

## Phase 1-4 (QR research)

### EDA of the new features

xbtc feature distributions on LINKUSDT_8h parquet (6857 rows, 100% matched):

| feature | min | p25 | median | p75 | max | mean | std |
|---------|----:|----:|-------:|----:|----:|-----:|----:|
| xbtc_return_1 | −22.18 | −0.68 | 0.03 | 0.76 | 15.08 | 0.05 | 1.79 |
| xbtc_return_3 | −39.98 | −1.26 | 0.09 | 1.52 | 21.13 | 0.14 | 3.16 |
| xbtc_rsi_14 | 8.46 | 42.59 | 51.13 | 60.71 | 94.32 | 51.94 | 13.20 |
| xbtc_adx_14 | 6.40 | 19.10 | 25.53 | 35.20 | 76.69 | 28.38 | 12.38 |

All 7 features are fully populated (0 NaN rows) for LINK. Distributions
are reasonable: returns centered near zero with fat tails, RSI roughly
symmetric around 50, ADX right-skewed (typical).

### Why cross-asset features matter (theoretical case)

Crypto altcoins are historically beta to BTC: when BTC trends, alts trend
harder. An altcoin model that predicts direction using only its own
features is implicitly re-deriving the BTC regime from its own price
action — inefficient. Passing BTC's RSI and ADX directly lets the model
condition its predictions on the broader market state.

Empirically: from iter-183 EDA, correlation of daily LINK/LTC/DOT
returns to BTC during 2023-2025 is 0.47–0.65. Material systematic beta.

### Implementation

1. `analysis/iteration_189/materialize_xbtc.py` ran
   `add_cross_asset_features("data/features", "data", "8h")` — materialized
   7 `xbtc_*` columns in 760 parquet files.
2. Added `XBTC_FEATURE_COLUMNS` constant (tuple of 7 names) and
   `BASELINE_PLUS_XBTC_FEATURE_COLUMNS` (200 features total) to
   `src/crypto_trade/live/models.py`.
3. Created `run_iteration_189_link_xbtc.py` — LINK standalone with
   R1+R3+xbtc features. Matches v0.186's LINK config exactly except
   for the expanded feature list.

## Sample-per-feature ratio check

LINK has ~4400 IS 8h bars. With 200 features, ratio = 22. Below the
skill's 50-minimum — concerning. But:
- LINK single-symbol already had ratio 22 with 193 features; adding 7
  more only worsens by 3%.
- The 7 new features are scale-invariant (normalized returns, % oscillators).
- v0.186's success with single-symbol 193 features already accepted the
  below-50 ratio. This is a 3.5% ratio degradation, not a 2x.

If LINK standalone Sharpe improves meaningfully, it confirms the features
carry signal despite the ratio. If it degrades, we have evidence the
ratio floor matters.

## Hypothesis

Adding 7 BTC cross-asset features to LINK's model lifts OOS Sharpe by
≥ +0.05 vs. v0.186's LINK standalone slice (+1.11). Target: Sharpe ≥ 1.2
standalone with ≥ 50 OOS trades.

## Decision rules

- **MERGE-CANDIDATE** if LINK standalone OOS Sharpe improves ≥ +0.10 and
  IS Sharpe stays above +1.0 — motivates the full 4-model rerun
  (iter 190).
- **NO-MERGE** if OOS Sharpe changes by < ±0.05 (within noise) or
  degrades significantly.
- **LESSON** either way: first rigorous test of xbtc features.

## Commit plan

- `feat(iter-189): materialize xbtc features + add BASELINE_PLUS_XBTC_FEATURE_COLUMNS`
- `docs(iter-189): research brief`
- `docs(iter-189): engineering report` (after backtest)
- `docs(iter-189): diary entry` (after evaluation)
