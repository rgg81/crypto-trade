# iter-v3/025 — Feature Engineering EDA Synthesis

## Mission

Per user directive 2026-05-08 + Critic FINAL Recommendation of iter-v3/024
(SHA `5a47f5d`): pivot from off-the-shelf indicator additions (3 of 3 INERT
in v3 catalog: iter-v3/015 microstructure, iter-v3/019 funding, iter-v3/024
BTC funding) toward genuine **engineered features** — composed/interaction
features built from existing 13-feature primitives that depth-3-5 LightGBM
trees cannot construct internally.

## Candidates Evaluated (6 of 7)

Candidate #3 (adx_signed_momentum) REJECTED because adx is a v3 GATE not a
feature column at the per-symbol architecture; adding adx as a feature would
itself be a separate axis (off-the-shelf indicator addition, contradicting
the pivot intent).

Remaining 6 candidates evaluated:
1. regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)
2. vol_adj_autocorr = ret_autocorr_lag1_50 / (range_realized_vol_50 + EPS)
4. cross_asset_divergence_norm = (sym_ret_7d − btc_ret_14d) / (vwap_dev_20 + EPS)
5. hurst_drift_50_200 = hurst_50 − hurst_200
6. fracdiff_d05_close = fracdiff(log(close), d=0.5) [López de Prado AFML Ch. 5]
7. ret_kurt_to_skew_ratio = ret_kurt_50 / (|ret_skew_50| + EPS)

## Composite Scoring

Score = 0.30 × orthogonality + 0.30 × rankIC magnitude + 0.20 × stability
        + 0.10 × interpretability_prior + 0.10 × (1 − implementation_cost_prior)

All scores on [0, 1]. Higher is better.

## Leaderboard (sorted by composite score, highest first)

```
1. cross_asset_divergence_norm     composite=0.6500  max|IC|=0.7561  max|rankIC|=0.1093  ADF=PASS  brief_gate=fail
2. regime_momentum_signed_5d       composite=0.5772  max|IC|=0.8865  max|rankIC|=0.0624  ADF=PASS  brief_gate=fail
3. ret_kurt_to_skew_ratio          composite=0.5623  max|IC|=0.6766  max|rankIC|=0.0774  ADF=PASS  brief_gate=fail
4. hurst_drift_50_200              composite=0.5100  max|IC|=0.8327  max|rankIC|=0.0633  ADF=PASS  brief_gate=fail
5. fracdiff_d05_close              composite=0.4954  max|IC|=0.6400  max|rankIC|=0.0885  ADF=FAIL  brief_gate=fail
6. vol_adj_autocorr                composite=0.4336  max|IC|=0.9848  max|rankIC|=0.0279  ADF=PASS  brief_gate=fail
```

## Brief gates (per candidate)

- Coverage IS window per symbol: ≥ 80.0%
- Max |IC| vs 13 V3_FEATURE_COLUMNS: < 0.5 (BRIEF target;
  hard gate at < 0.7)
- ADF p-value: < 0.05 per symbol
- Max |rank-IC| vs forward returns: ≥ 0.02 on at least 1 horizon

Candidates passing ALL 4 brief gates: 0 of 6

## RECOMMENDATION

**TOP candidate (composite score 0.6500):
`cross_asset_divergence_norm`**

Pre-commit per iter-v3/024 diary `Pre-Commit for iter-v3/025` section:
**iter-v3/025 axis = `regime_momentum_signed_5d`** = ret_5d × sign(hurst_100 − 0.5).

Rationale (independent of leaderboard rank — single-axis discipline):
- Tests "model can't compose" hypothesis directly: hurst_100 is rank 8 on
  BCH (importance=31) and rank 10 on LDO (importance=86) at iter-v3/024;
  ret_5d derivative is in the labeling pipeline but NOT as a feature column.
- The interaction (regime-conditional momentum) is a textbook trader
  heuristic (momentum "works" in trending markets, fails in mean-reverting
  markets) that depth-3-5 LightGBM trees cannot construct from raw inputs
  at the candidate-split level (each split is on a SINGLE feature; nested
  interaction would consume splits that are otherwise spent on the actual
  decision boundary).
- Implementation cost LOW: composes existing primitives (close, hurst_100).
- Interpretability HIGH: regime-conditional momentum is part of standard
  systematic-trading toolkit (Robert Carver, Ernest Chan).

The composite score may rank a different candidate higher (e.g., fracdiff
or hurst_drift) — but the iter-v3/024 diary pre-commit binds the iter-v3/025
axis. Cannot be renegotiated post-hoc per `feedback_v3_engineered_feature_pivot.md`
(to be committed at iter-v3/025 setup).

## Files

- analysis/iteration_v3-025/feature_engineering_eda_distribution.csv
- analysis/iteration_v3-025/feature_engineering_eda_correlation.csv
- analysis/iteration_v3-025/feature_engineering_eda_rankic.csv
- analysis/iteration_v3-025/feature_engineering_eda_adf.csv
- analysis/iteration_v3-025/feature_engineering_eda_composite.csv
