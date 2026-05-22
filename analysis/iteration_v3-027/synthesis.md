# iter-v3/027 — Third Engineered Feature EDA Synthesis

## Mission

Per Critic FINAL Recommendation of iter-v3/026 (review SHA `8839bbb`) + user directive
2026-05-08 + diary lessons (a)-(g) of iter-v3/026: **iter-v3/027 axis = DIFFERENT engineered
feature ALONE on top of regime_momentum**.

iter-v3/025 PROMISING-clean (regime_momentum_signed_5d alone): IS +0.88 / OOS +1.22.

iter-v3/026 NEGATIVE-SUSPICIOUS-OOS (regime_momentum + vol_adj_autocorr stacked): IS Sharpe
collapse to +0.05 (PATH C fires) + OOS spike to +1.45 (single-seed-suspect; 27× IS/OOS daily
Sharpe ratio is structurally absurd; iter-v3/013 lottery precedent + worst IS MaxDD in v3
history at 51.37% + BCH 78% concentration regression).

NEW memory rule `feedback_v3_engineered_features_dont_stack.md`: test ONE engineered feature
alone at single-seed; defer stacking to multi-seed CONFIRMATION.

iter-v3/027 axis isolates the question: **was iter-v3/026's destabilization vol_adj_autocorr-
specific, OR a structural property of stacking 2 engineered features at single-seed
n_trials=35?** Testing a DIFFERENT engineered feature ALONE on top of regime_momentum (the
proven iter-v3/025 setup with vol_adj_autocorr DROPPED) disambiguates this:
- PATH A (PROMISING) → iter-v3/026 destabilization was vol_adj_autocorr-specific OR a stacking
  artifact; engineered features can be stacked SEQUENTIALLY at single-seed (one alone at a
  time) but not simultaneously
- PATH C (NEGATIVE) → destabilization is NOT vol_adj_autocorr-specific; engineered stacking
  is structurally fragile at single-seed even with 1 new feature; pivot remains single-feature
  (only regime_momentum_signed_5d) at this architecture

## Candidates Evaluated (4 of 4)

Per Critic FINAL Recommendation of iter-v3/026 + EDA leaderboard from iter-v3/025/026:

1. **cross_asset_divergence_norm** = (sym_ret_7d − btc_ret_14d) / (|vwap_dev_20| + EPS)
   — relative-strength normalized; **Critic-named pre-commit recommendation**
2. ret_kurt_to_skew_ratio = ret_kurt_50 / (|ret_skew_50| + EPS)
   — fat-tail to asymmetry ratio; iter-v3/028 fallback if iter-v3/027 PATH B/C
3. fracdiff_d05_close = fracdiff(log(close), d=0.5) [López de Prado AFML Ch. 5]
4. hurst_drift_50_200 = hurst_50 − hurst_200 (multi-timeframe regime drift)

## IC Carve-Out (Category 2 axes) — REMINDER

Per `feedback_v3_engineered_feature_pivot.md`, IC orthogonality gate is INFORMATIONAL ONLY
for engineered (composed) features. The binding gate is the LightGBM model output:
**feature importance rank ≤10 AND absolute importance ≥30** for at least 1 symbol.

The composite score (mirroring iter-v3/026 weights) includes
**orthogonality-to-regime_momentum_signed_5d** (weight 0.20). Lower IC vs the iter-v3/025
PROMISING engineered feature = more orthogonal mechanism = better candidate.

## Composite Scoring (iter-v3/027 weights, mirror iter-v3/026)

Score = 0.10 × orthogonality_to_14_features (informational)
        + 0.20 × orthogonality_to_regime_momentum
        + 0.30 × rankIC magnitude
        + 0.20 × stability (coverage × ADF)
        + 0.10 × interpretability_prior
        + 0.10 × (1 − implementation_cost_prior)

## Leaderboard (sorted by composite score, highest first)

```
1. ret_kurt_to_skew_ratio          composite=0.7322  max|IC|_14=0.6766  max|IC|_rm=0.0753  max|rankIC|=0.0774  ADF=PASS  brief_gate=PASS
2. hurst_drift_50_200              composite=0.6940  max|IC|_14=0.5970  max|IC|_rm=0.0726  max|rankIC|=0.0643  ADF=PASS  brief_gate=PASS
3. cross_asset_divergence_norm     composite=0.6643  max|IC|_14=0.7561  max|IC|_rm=0.4643  max|rankIC|=0.1093  ADF=PASS  brief_gate=PASS
4. fracdiff_d05_close              composite=0.4954  max|IC|_14=0.6400  max|IC|_rm=0.5681  max|rankIC|=0.0885  ADF=FAIL  brief_gate=fail
```

## Brief gates (per candidate)

- Coverage IS window per symbol: ≥ 80.0%
- ADF p-value: < 0.05 per symbol
- Max |rank-IC| vs forward returns: ≥ 0.02 on at least 1 horizon
- Max |IC| vs 14 features: INFORMATIONAL (Category 2 IC carve-out)

Candidates passing ALL 3 binding brief gates: 3 of 4

## RECOMMENDATION

Pre-commit per iter-v3/026 Critic FINAL Recommendation (review SHA `8839bbb`)
+ user directive 2026-05-08:

**iter-v3/027 axis = `cross_asset_divergence_norm`** = (sym_ret_7d − btc_ret_14d) / (|vwap_dev_20| + EPS)

Rationale (independent of leaderboard rank — single-axis discipline):
- Tests the disambiguation hypothesis directly: if a DIFFERENT engineered feature ALONE on
  top of regime_momentum produces clean co-directional IS+OOS lift (PATH A), then iter-v3/026's
  destabilization was vol_adj_autocorr-specific OR a stacking artifact.
- Different mechanism from regime_momentum AND from vol_adj_autocorr:
  - regime_momentum: directional 5-day return × Hurst regime classifier
  - vol_adj_autocorr (DROPPED): lag-1 autocorrelation / range-realized vol
  - cross_asset_divergence_norm: alt-vs-BTC return divergence / vwap-deviation
- Source primitives non-overlapping with regime_momentum (sym_ret_7d/btc_ret_14d/vwap_dev_20
  vs close-derived ret_5d/hurst_100). Genuinely new interaction signal.
- Implementation cost LOW: composes 3 existing primitives, all already in features parquet.
  ~10 lines of code added to engineered_v3.py.
- Critic FINAL of iter-v3/026 explicitly named this as recommended candidate with rationale
  "Different mechanism (relative-strength); uses existing primitives (sym_ret_7d, btc_ret_14d,
  vwap_dev_20); lowest implementation cost".
- Composite leaderboard ranking is INFORMATIONAL; single-axis discipline binds independent
  of rank.

## Files

- analysis/iteration_v3-027/third_engineered_eda_distribution.csv
- analysis/iteration_v3-027/third_engineered_eda_correlation.csv
- analysis/iteration_v3-027/third_engineered_eda_rankic.csv
- analysis/iteration_v3-027/third_engineered_eda_adf.csv
- analysis/iteration_v3-027/third_engineered_eda_composite.csv
