# Engineering Report — iter-v3/024

## Status: READY-FOR-CRITIC

Wall-clock 0.23h (14 min). Setup `b28db27`, gate `4a50c5c`, brief `c1c2f15`, EDA `afdb8bc`.

## Hypothesis-Implementation Alignment

DROP per-symbol funding_rate_zscore_30 + ADD btc_funding_rate_zscore_30 (cross-asset broadcast). V3_FEATURE_COLUMNS=14 (column count preserved; atomic switch). Single-axis discipline preserved per brief §0.5 "switch funding source." Adversarial past-only test PASS.

## Headline Metrics

| Metric | Value | vs Anchor |
|--------|-------|-----------|
| IS monthly Sharpe | +0.9750 | Δ +0.60 (largest IS lift post-bootstrap) |
| OOS monthly Sharpe | -0.8170 | Δ -1.20 (3rd worst single-seed in v3) |
| OOS MaxDD | 49.97% | 2nd consecutive 50%+ breach (iter-v3/023 was 49.93%) |
| OOS Trades | 85 | < 130 floor |
| DSR | 0.000003 | structural artifact |
| PBO mean | 0.0843 | PASS |
| PSR | 0.0000 | collapsed |
| n_eff | 19 | consistent with n_trials=35 |

## Per-symbol breakdown OOS

| Symbol | PnL | Trades | WR |
|--------|-----|--------|-----|
| BCH | -18.65 | 33 | 33.3% |
| LDO | -27.75 | 11 | 27.3% (catastrophic) |
| TRX | +14.31 | 41 | 46.3% (only positive) |

## Feature Importance — btc_funding_rate_zscore_30 RANK

Portfolio: rank **14/14**, importance 76 vs top vwap_dev_20=321 (23.7% of top). Same dead-last pattern as per-symbol funding at iter-v3/019/023.

## INERT-OVERFIT Pattern Confirmed (Generalized)

iter-v3/023 (per-symbol funding at n=35): rank 14/14, OOS -1.07
iter-v3/024 (BTC cross-asset funding at n=35): rank 14/14, OOS -0.82

Both confirm `feedback_v3_inert_features_at_higher_budget.md`: adding INERT features to V3_FEATURE_COLUMNS at higher Optuna budgets actively HARMS OOS via expanded overfit space.

**Both funding variants** (per-symbol AND cross-asset BTC) produce:
- Rank 14/14 importance
- IS lift (lottery overshoot)
- OOS collapse (-0.8 to -1.1)
- 50%+ OOS MaxDD

**Funding family (in entirety) is permanently CLOSED** for v3's per-symbol LightGBM at the 13-feature stack. Both per-symbol AND cross-asset variants tested; both INERT.

## §4.4 Classification

EXPLORATION-NEGATIVE (clean) — same pattern as iter-v3/023. PATH C fires (OOS Δ -1.20 < -0.10).

## Recommendations

iter-v3/025 should pivot AWAY from off-the-shelf feature additions toward **genuine feature engineering**: composed/interaction/regime-conditional features built from existing primitives rather than fetched from new data sources. Rationale: 3 of 3 funding-family axes (per-symbol funding 019, per-symbol retest 023, cross-asset BTC 024) all rank 14/14. The 13-feature stack appears saturated for direct additions; the model needs INTERACTION expressions the trees can't compose at depth 3-5 from raw features.

Candidates for iter-v3/025 feature engineering:
1. Regime-conditional momentum: `ret_5d × sign(hurst_100 - 0.5)`
2. Vol-adjusted return persistence: `ret_autocorr_lag1_50 / range_realized_vol_50`
3. ADX-momentum interaction: `adx × sign(ret_14d)`
4. Cross-asset divergence normalized: `(sym_ret_7d - btc_ret_14d) / vwap_dev_20`
5. Multi-timeframe regime drift: `hurst_50 - hurst_100`
6. Fractional differentiation of returns (López de Prado AFML Ch. 5)
