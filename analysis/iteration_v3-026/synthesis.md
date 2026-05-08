# iter-v3/026 — Second Engineered Feature EDA Synthesis

## Mission

Per Critic FINAL Recommendation of iter-v3/025 (review SHA `402643d`) + user directive
2026-05-08: **iter-v3/026 axis = SECOND ENGINEERED FEATURE** stacked ON TOP of the
iter-v3/025 14-feature stack (regime_momentum_signed_5d KEPT). Tests whether the FEATURE
ENGINEERING pivot is consistently productive — i.e., whether engineered features generalize
beyond the single iter-v3/025 PROMISING result.

iter-v3/025 fired PATH A unambiguously:
- Importance 51% of top portfolio (~2× any prior NEW feature)
- IS Δ +0.50 / OOS Δ +0.84 vs iter-v3/018 BOOTSTRAP anchor
- BCH/LDO frozen-baseline pattern from iter-v3/020-024 DISSOLVED

A second engineered feature with structurally orthogonal mechanism would (a) further
validate the engineered-features-OUTPERFORM-off-the-shelf hypothesis (`feedback_v3_engineered_features_proven.md`)
and (b) build a multi-feature engineered-features stack incrementally. PATH A in iter-v3/026
qualifies for CONFIRMATION-bundle inclusion at iter-v3/029 (multi-seed validation).

## Candidates Evaluated (4 of 4)

Per Critic FINAL Recommendation of iter-v3/025 + user directive specifying
`vol_adj_autocorr` as #1 candidate:

1. **vol_adj_autocorr** = ret_autocorr_lag1_50 / (range_realized_vol_50 + EPS)
   — autocorrelation per unit vol; structurally orthogonal to regime_momentum
2. cross_asset_divergence_norm = (sym_ret_7d − btc_ret_14d) / (vwap_dev_20 + EPS)
   — relative-strength normalized
3. fracdiff_d05_close = fracdiff(log(close), d=0.5) [López de Prado AFML Ch. 5]
   — memory-preserving stationarity (v3 skill mandate iter-v3/001 never delivered)
4. ret_kurt_to_skew_ratio = ret_kurt_50 / (|ret_skew_50| + EPS)
   — fat-tail to asymmetry ratio

## IC Carve-Out (Category 2 axes) — REMINDER

Per `feedback_v3_engineered_feature_pivot.md`, IC orthogonality gate is INFORMATIONAL ONLY
for engineered (composed) features. The binding gate is the LightGBM model output:
**feature importance rank ≤10 AND absolute importance ≥30** for at least 1 symbol.

The composite score is **augmented** for iter-v3/026 with a NEW component:
**orthogonality-to-regime_momentum_signed_5d** (weight 0.20). Lower IC vs the iter-v3/025
PROMISING engineered feature = more orthogonal mechanism = better candidate. This rewards
mechanistic distinctness from the existing engineered feature.

## Composite Scoring (iter-v3/026 weights)

Score = 0.10 × orthogonality_to_14_features (informational)
        + 0.20 × orthogonality_to_regime_momentum (NEW for iter-v3/026)
        + 0.30 × rankIC magnitude
        + 0.20 × stability (coverage × ADF)
        + 0.10 × interpretability_prior
        + 0.10 × (1 − implementation_cost_prior)

## Leaderboard (sorted by composite score, highest first)

```
1. ret_kurt_to_skew_ratio          composite=0.7322  max|IC|_14=0.6766  max|IC|_rm=0.0753  max|rankIC|=0.0774  ADF=PASS  brief_gate=PASS
2. cross_asset_divergence_norm     composite=0.6643  max|IC|_14=0.7561  max|IC|_rm=0.4643  max|rankIC|=0.1093  ADF=PASS  brief_gate=PASS
3. vol_adj_autocorr                composite=0.6035  max|IC|_14=0.9848  max|IC|_rm=0.0753  max|rankIC|=0.0279  ADF=PASS  brief_gate=PASS
4. fracdiff_d05_close              composite=0.4954  max|IC|_14=0.6400  max|IC|_rm=0.5681  max|rankIC|=0.0885  ADF=FAIL  brief_gate=fail
```

## Brief gates (per candidate)

- Coverage IS window per symbol: ≥ 80.0%
- ADF p-value: < 0.05 per symbol
- Max |rank-IC| vs forward returns: ≥ 0.02 on at least 1 horizon
- Max |IC| vs 14 features: INFORMATIONAL (Category 2 IC carve-out)

Candidates passing ALL 3 binding brief gates: 3 of 4

## RECOMMENDATION

Pre-commit per iter-v3/025 Critic FINAL Recommendation (review SHA `402643d`)
+ user directive 2026-05-08:

**iter-v3/026 axis = `vol_adj_autocorr`** = ret_autocorr_lag1_50 / (range_realized_vol_50 + EPS)

Rationale (independent of leaderboard rank — single-axis discipline):
- Tests "second engineered feature with orthogonal mechanism" hypothesis directly: source
  primitives (ret_autocorr_lag1_50, range_realized_vol_50) are NON-OVERLAPPING with
  regime_momentum_signed_5d's primitives (close-derived ret_5d, hurst_100). The two
  engineered features encode structurally distinct interactions:
  - regime_momentum: directional 5-day return × Hurst regime classifier
  - vol_adj_autocorr: lag-1 return persistence / range-realized vol
- Implementation cost LOWEST: composes 2 existing primitives, both already in features
  parquet. ~10 lines of code added to engineered_v3.py.
- Critic FINAL of iter-v3/025 explicitly named this as "strong candidate" + "structurally
  orthogonal mechanism".
- Composite leaderboard ranking is INFORMATIONAL; single-axis discipline binds independent
  of rank.

## Files

- analysis/iteration_v3-026/second_engineered_eda_distribution.csv
- analysis/iteration_v3-026/second_engineered_eda_correlation.csv
- analysis/iteration_v3-026/second_engineered_eda_rankic.csv
- analysis/iteration_v3-026/second_engineered_eda_adf.csv
- analysis/iteration_v3-026/second_engineered_eda_composite.csv
