# iter-v3/016 EDA synthesis — XGBoost head-to-head smoke

**Status**: smoke PASS.

## Hyperparameter map
13 of 13 LightGBM Optuna search-space dimensions have a clean XGBoost
equivalent (see `xgboost_param_map.csv`).  Two semantic-equivalence
substitutions: `min_child_samples` → `min_child_weight` (sample-count vs
hessian-sum, same range), and `is_unbalance=True` → `scale_pos_weight=neg/pos`
(must be computed per-fit; not a hyperparameter).  All other parameters map
1-to-1 with identical names and ranges.

## Smoke test summary
- Symbol: BCHUSDT; test month: 2024-12
- XGBoost installed: True (version 2.1.4)
- Train samples: 2171 (1083 pos / 1088 neg)
- Test samples: 72
- Test accuracy: 0.7083
- Top-3 features by gain: ret_skew_200=0.0944; ret_kurt_50=0.0922; ret_skew_50=0.0905
- Fit time: 2.116s; predict time: 0.001s

The smoke is a one-shot fit on coarse forward-return-sign labels — not a
walk-forward replication of the production runner.  It exists to confirm
integration mechanics (NaN handling, feature_importances_ API, scale_pos_weight
balancing, tree_method='hist' determinism) before the brief commits the
production XgboostStrategy class.

## Behavioral-effect prediction (saturation falsifier)
iter-v3/013 baseline: 209 IS trades, 38 calendar months, ~5.5 trades/month
average.  XGBoost's depth-wise growth is structurally MORE conservative than
LightGBM's leaf-wise — it tends to produce flatter probability surfaces, which
under a fixed `confidence_threshold` Optuna parameter means FEWER signals
clear the threshold.  Counter-balance: Optuna will re-optimize
`confidence_threshold` per-trial on the new probability calibration, so the
final threshold may be lower than LightGBM's.

**Predicted IS trade-count band**: [165, 250]
- Lower bound 165 ≈ 209 × 0.79 (XGBoost depth-wise more conservative on
  signal selection; threshold re-optimization partially absorbs the
  conservatism).
- Upper bound 250 ≈ 209 × 1.20 (XGBoost may surface signal LightGBM ignored,
  producing additional trade triggers; per Critic FINAL discussion of TBR
  failure-mode diagnosis).
- Median expectation: 200 (≈ ±5% of LightGBM baseline trade count).

**Saturation falsifier (per `feedback_axis_saturation_predictor.md`)**:
predicted IS trade-count change vs iter-v3/013 baseline is at least
ceil(0.05 × 209) = 11 trades in either direction.  If realized iter-v3/016
IS trade count is within [198, 220] (i.e., absolute change < 11 trades AND
trade-roster non-bit-identical to iter-v3/013), the model architecture
swap may have been mechanically inert — the brief's §4 outcome
interpretation must contain a row for this NULL-RESULT subtype.
