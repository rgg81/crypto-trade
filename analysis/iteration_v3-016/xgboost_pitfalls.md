# XGBoost integration pitfalls — iter-v3/016

Authoritative source: https://xgboost.readthedocs.io (v2.x, scikit-learn API).

## 1. Class-imbalance handling
**LightGBM**: `is_unbalance=True` automatically scales positive class weight by
`n_neg / n_pos`.
**XGBoost**: no `is_unbalance` flag.  Caller must compute and pass
`scale_pos_weight = n_neg / n_pos` per-fit.  In ternary mode (multi:softprob)
this is replaced by per-sample `sample_weight` (which the LightGBM path also
uses for `sample_uniqueness` weighting — the existing `train_weights` array
already covers this).

**Implementation impact**: optimization.py's `optimize_and_train` final retrain
must compute `scale_pos_weight` from `train_labels` before constructing the
XGBClassifier in the binary-objective path.  Engineer should mirror the
existing `is_unbalance=True` exactly: same denominator policy, no smoothing.

## 2. NaN handling
**LightGBM**: handles NaN natively (passes them as a separate split direction).
**XGBoost**: handles NaN natively (treats them as a missing-value direction
learned per split).  Both packages tolerate NaN inputs.

**Verification**: smoke script drops rows with NaN explicitly via `np.isfinite`
mask (same as the per-symbol importance EDA from iter-v3/015).  Production
behavior should match LightGBM's: pass NaN through and let XGBoost route them.
The runner's existing finite-mask in `optimization.py` likely already filters
NaN-row training samples, so no behavior change expected from this difference.

## 3. Feature importance API
**LightGBM**: `feature_importances_` returns gain by default
(controlled by `importance_type`, default `"split"` for `LGBMClassifier`).
**XGBoost**: `feature_importances_` returns gain by default
(controlled by `importance_type`, default `"gain"` for `XGBClassifier`).

**Implementation impact**: existing `_write_feature_importance` at
`run_baseline_v3.py:1110-1151` reads `model.feature_importances_` directly,
so the API call is portable.  HOWEVER the absolute scales differ — LightGBM
split-counts are integers; XGBoost gain values are floats normalized to sum=1.
This affects the **values** in `feature_importance.csv` but not the **rank**
that downstream Critic Falsifier 4 checks.  The fix at iter-v3/016 first
commit (per Critic FINAL Rec 3) makes this aggregation correct across
(symbol, month) cells regardless of which library produced it.

## 4. Tree growth strategy (the load-bearing difference)
**LightGBM**: leaf-wise (best-first) growth — grows the leaf with the largest
loss reduction.  Tends to overfit on small datasets; `max_depth` is a soft
cap.  Combined with GOSS sampling, may ignore features whose gradient
contribution is small but consistent (the iter-v3/015 `tbr_zscore_30`
hypothesis-of-failure).
**XGBoost**: depth-wise (level-wise) growth by default — splits all leaves at
current depth before going deeper.  More conservative; less prone to
overfitting; does NOT use GOSS.  May surface signal in features that
LightGBM ignores.

**Hyperparameter mapping**: setting `grow_policy='lossguide'` makes XGBoost
mimic LightGBM's leaf-wise behavior; the EDA's parameter map intentionally
keeps default `'depthwise'` to maximize the architectural difference.  This
is the load-bearing axis of the head-to-head.

## 5. Histogram binning
**LightGBM**: histogram-based with EFB (Exclusive Feature Bundling) on by
default; `max_bin=255`.
**XGBoost**: `tree_method='hist'` (default in v2.x) uses histograms with
`max_bin=256`.  No EFB.

**Implementation impact**: minimal at the 13-feature scale (EFB matters most
when feature count is in the hundreds with sparse one-hot encoding).  Pin
`tree_method='hist'` explicitly to rule out version drift.

## 6. Determinism & seeds
Both libraries respect `random_state` for tree-construction stochasticity.
Both are deterministic when `n_jobs=1`.  Set `n_jobs=1` in the production
runner (matches LightGBM's effective single-thread behavior under
ProcessPoolExecutor).

## 7. categorical features
**LightGBM**: native categorical support via `categorical_feature` parameter.
**XGBoost**: requires `enable_categorical=True` AND `dtype='category'` columns
in the input DataFrame.

**Implementation impact**: NONE.  All 13 V3 features are continuous floats —
no categorical inputs.  Skip enabling categorical support to avoid surprise
behavior.

## 8. Library version pinning
**XGBoost 2.x** is the recommended major version.  v3.x exists as of this
writing but introduces breaking API changes; pin `xgboost>=2.0,<3.0` in
pyproject.toml.  License: Apache-2.0 (compatible with the repo's license
posture).

## 9. CPU vs GPU
The smoke test forces `tree_method='hist'` (CPU).  `gpu_hist` is the GPU
mode but requires a CUDA install AND introduces non-determinism even with
fixed seeds in some XGBoost minor versions.  Production must remain on CPU
to preserve reproducibility (per BASELINE_V3 reproducibility rule).

## 10. Checkpoint behavior
**LightGBM**: `early_stopping_rounds` requires an eval set.
**XGBoost**: same semantic; `early_stopping_rounds` requires an `eval_set`
list.  iter-v3/016 production: do NOT use early stopping (LightGBM path
doesn't either at `optimization.py:289` and `:487`); train for the full
`n_estimators` count selected by Optuna.
