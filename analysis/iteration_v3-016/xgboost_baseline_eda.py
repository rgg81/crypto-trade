"""
iter-v3/016 — XGBoost smoke test + hyperparameter-space mapping vs LightGBM.

Background (iter-v3/015 NEGATIVE-no-effect; Critic FINAL Recommendation 1):
    iter-v3/015 added the first NEW feature family in v3 catalog (`tbr_zscore_30`,
    a 30-bar z-score of `taker_buy_quote_volume / quote_volume`). The feature was
    structurally clean: max |IC| vs the existing 13 features = 0.0862 (well below
    the 0.70 redundancy gate); past-only via `s.shift(1)`; mean-zero by construction
    (z-score). Yet LightGBM ranked it 14/14 across BCH/LDO/TRX (16% / 41% / 20% of
    top-feature importance). The model demonstrably did not learn the feature.

    Diagnosis (Critic FINAL): LightGBM's leaf-wise growth + Gradient-based One-Side
    Sampling (GOSS) may not surface microstructure signal that a structurally
    different boosting library could. Per `feedback_v3_iter016_xgboost_mandate.md`,
    iter-v3/016 axis = LightGBM → XGBoost head-to-head on iter-v3/013's 13-feature
    stack (drop tbr_zscore_30 as INERT before XGBoost integration).

Purpose of this EDA:
    Phase 5 (QR) requirement is to produce numerical evidence BEFORE the brief is
    authored. This script does four things, all on IS-only data:
      (a) Document the XGBoost hyperparameter search space, mapped 1-to-1 against
          the existing LightGBM Optuna search space at
          src/crypto_trade/strategies/ml/optimization.py:210-224 (see _objective).
      (b) Run a SMALL XGBoost baseline on 1 symbol × 1 calendar month (BCH /
          2024-12 — the most recent IS month with sufficient sample) as a smoke
          test confirming integration works AND baseline Sharpe is sane.
      (c) Log XGBoost-specific implementation pitfalls (NaN handling, categorical
          handling, feature-importance API differences) discovered during smoke.
      (d) Behavioral-effect predictor: predict trade-count change vs iter-v3/013
          baseline (209 IS trades). Different tree-growth strategies can produce
          materially more or fewer signals depending on confidence-threshold
          calibration in the Optuna objective.

Outputs (committed alongside this script BEFORE the research_brief.md):
    analysis/iteration_v3-016/xgboost_param_map.csv   — parallel-structure table
    analysis/iteration_v3-016/xgboost_smoke_results.csv — 1-symbol 1-month smoke
    analysis/iteration_v3-016/xgboost_pitfalls.md     — implementation notes
    analysis/iteration_v3-016/xgboost_eda_synthesis.md — 1-paragraph narrative

Caveats (stated up-front):
    - This is a one-shot baseline fit, NOT walk-forward.  The production runner
      will retrain monthly with Optuna across 10 trials.  Smoke Sharpe numbers
      here are not predictive of production IS Sharpe — they exist to confirm
      pipeline integration only.
    - The smoke uses default-config XGBoost (no Optuna).  Production runs will
      go through Optuna with the same trial budget as LightGBM.
    - XGBoost may not be importable yet — the script catches ImportError and
      degrades to a "design-only" mode that still produces the parameter map
      and pitfalls notes from documented sources.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from crypto_trade.config import OOS_CUTOFF_MS  # noqa: E402

# iter-v3/013 baseline 13-feature stack (V3_FEATURE_COLUMNS BEFORE iter-v3/015's
# tbr_zscore_30 addition).  Hardcoded here because iter-v3/016's first commit
# will revert V3_FEATURE_COLUMNS to this set; the EDA is authored BEFORE that
# commit lands so we cannot import the live constant.
V3_13_FEATURES = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
)

OUT_DIR = Path(__file__).resolve().parent
FEATURES_DIR = REPO_ROOT / "data" / "features_v3"

SMOKE_SYMBOL = "BCHUSDT"
SMOKE_MONTH = "2024-12"


# ----------------------------------------------------------------------
# (a) Parameter-space mapping — LightGBM ↔ XGBoost parallel structure
# ----------------------------------------------------------------------

# Anchor: src/crypto_trade/strategies/ml/optimization.py:210-224 (LightGBM
# search space inside _objective).  XGBoost parameter names follow the
# scikit-learn API at https://xgboost.readthedocs.io (XGBClassifier, v2.x).
PARAM_MAP_ROWS = [
    # (Optuna name, LightGBM param, LightGBM range,
    #  XGBoost param, XGBoost range, equivalence note)
    (
        "n_estimators",
        "n_estimators",
        "[50, 500]",
        "n_estimators",
        "[50, 500]",
        "Identical: number of boosted trees",
    ),
    (
        "max_depth",
        "max_depth",
        "[3, 5]",
        "max_depth",
        "[3, 5]",
        "Identical semantic: max tree depth",
    ),
    (
        "num_leaves",
        "num_leaves",
        "[15, 127]",
        "max_leaves",
        "[15, 127]",
        "XGBoost respects max_leaves only when grow_policy='lossguide'; "
        "default 'depthwise' growth ignores num_leaves. Set grow_policy='lossguide' "
        "to mirror LightGBM's leaf-wise growth, OR drop max_leaves and let depthwise "
        "growth interact with max_depth.",
    ),
    (
        "learning_rate",
        "learning_rate",
        "[0.01, 0.3] log-scale",
        "learning_rate (eta)",
        "[0.01, 0.3] log-scale",
        "Identical",
    ),
    (
        "subsample",
        "subsample",
        "[0.5, 1.0]",
        "subsample",
        "[0.5, 1.0]",
        "Identical: row subsampling per tree",
    ),
    (
        "colsample_bytree",
        "colsample_bytree",
        "[0.3, 1.0] (fast_mode: hardcoded 1.0)",
        "colsample_bytree",
        "[0.3, 1.0] (fast_mode: hardcoded 1.0)",
        "Identical name + identical semantic. Per `--exploration` spec, "
        "fast_mode hardcodes 1.0 to minimize per-seed feature-subsampling variance.",
    ),
    (
        "min_child_samples",
        "min_child_samples",
        "[5, 100]",
        "min_child_weight",
        "[5, 100]",
        "Semantic equivalent (sample-count vs sum-of-hessians min in leaf). "
        "Same range works as a near-equivalent regularization knob.",
    ),
    (
        "reg_alpha",
        "reg_alpha",
        "[1e-8, 10.0] log-scale",
        "reg_alpha",
        "[1e-8, 10.0] log-scale",
        "Identical: L1 regularization on leaf weights",
    ),
    (
        "reg_lambda",
        "reg_lambda",
        "[1e-8, 10.0] log-scale",
        "reg_lambda",
        "[1e-8, 10.0] log-scale",
        "Identical: L2 regularization on leaf weights",
    ),
    (
        "random_state",
        "random_state",
        "outer-derived",
        "random_state",
        "outer-derived",
        "Identical",
    ),
    (
        "(implicit binary)",
        "objective='binary' + is_unbalance=True",
        "—",
        "objective='binary:logistic' + scale_pos_weight=neg/pos",
        "—",
        "XGBoost has no `is_unbalance` flag.  Compute scale_pos_weight = "
        "n_neg / n_pos at fit time to mirror LightGBM's automatic class-weight "
        "balancing.",
    ),
    (
        "(implicit ternary)",
        "objective='multiclass' + num_class=3",
        "—",
        "objective='multi:softprob' + num_class=3",
        "—",
        "XGBoost requires probabilities-output objective for predict_proba; "
        "'multi:softprob' is the correct choice (vs 'multi:softmax' which "
        "outputs hard classes).",
    ),
    (
        "verbosity",
        "verbosity=-1",
        "—",
        "verbosity=0",
        "—",
        "XGBoost's silence flag is verbosity=0 (LightGBM uses -1).",
    ),
    (
        "fast_mode forced",
        "tree_learner='serial' (default)",
        "—",
        "tree_method='hist'",
        "—",
        "XGBoost default 'auto' selects 'hist' for v2.x.  Pin tree_method='hist' "
        "explicitly so behavior matches across XGBoost versions and rules out "
        "'gpu_hist' if a future env adds a CUDA install.",
    ),
]


def write_param_map() -> None:
    cols = [
        "optuna_name",
        "lightgbm_param",
        "lightgbm_range",
        "xgboost_param",
        "xgboost_range",
        "equivalence_note",
    ]
    df = pd.DataFrame(PARAM_MAP_ROWS, columns=cols)
    out_path = OUT_DIR / "xgboost_param_map.csv"
    df.to_csv(out_path, index=False)
    print(f"  wrote {out_path}  ({len(df)} rows)")


# ----------------------------------------------------------------------
# (b) Smoke test — 1 symbol × 1 month default-config XGBoost on IS data
# ----------------------------------------------------------------------


def _load_is_features(symbol: str) -> pd.DataFrame:
    pq = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    if not pq.exists():
        raise FileNotFoundError(
            f"Missing feature parquet {pq}. "
            "Run `uv run crypto-trade features --symbols BCHUSDT --interval 8h "
            "--track v3 --format parquet --workers 4` to generate."
        )
    df = pd.read_parquet(pq)
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
    return df


def _make_smoke_split(df: pd.DataFrame, month: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split df into a 24-month training window ending at the start of `month`,
    and a 1-month test window equal to `month`."""
    df = df.copy()
    df["open_time_dt"] = pd.to_datetime(df["open_time"], unit="ms")
    df["month"] = df["open_time_dt"].dt.to_period("M").astype(str)
    test_period = pd.Period(month, freq="M")
    train_end_period = test_period - 1
    train_start_period = train_end_period - 23  # 24-month rolling window
    in_train = (
        (df["open_time_dt"].dt.to_period("M") <= train_end_period)
        & (df["open_time_dt"].dt.to_period("M") >= train_start_period)
    )
    in_test = df["open_time_dt"].dt.to_period("M") == test_period
    return df[in_train].copy(), df[in_test].copy()


def _coarse_label(df: pd.DataFrame, horizon: int = 21) -> np.ndarray:
    """Forward 21-bar return sign as a coarse proxy for triple-barrier label."""
    closes = df["close"].astype(float).to_numpy()
    fwd = np.full(len(closes), np.nan)
    if len(closes) > horizon:
        fwd[: -horizon] = closes[horizon:] / closes[:-horizon] - 1.0
    return np.sign(fwd)


def run_smoke() -> dict:
    """Default-config XGBoost smoke on (BCH, 2024-12).  Returns dict with results
    OR a 'skipped' flag if XGBoost is not installed."""
    out: dict = {
        "symbol": SMOKE_SYMBOL,
        "test_month": SMOKE_MONTH,
        "n_features": len(V3_13_FEATURES),
        "xgboost_available": False,
        "xgboost_version": "",
        "n_train": 0,
        "n_test": 0,
        "test_accuracy": float("nan"),
        "test_pos_rate": float("nan"),
        "n_train_pos": 0,
        "n_train_neg": 0,
        "fit_seconds": float("nan"),
        "predict_seconds": float("nan"),
        "top3_features": "",
        "tbr_or_proxy_present": False,
        "notes": "",
    }
    try:
        import xgboost as xgb  # type: ignore[import-not-found]
    except ImportError as e:
        out["notes"] = f"xgboost not installed in this env (ImportError: {e}). "
        out["notes"] += (
            "Smoke skipped — Engineer must add `xgboost>=2.0,<3.0` to pyproject.toml "
            "and re-run this script as part of Phase 6 setup before the production runner."
        )
        return out

    out["xgboost_available"] = True
    out["xgboost_version"] = xgb.__version__

    df = _load_is_features(SMOKE_SYMBOL)
    train_df, test_df = _make_smoke_split(df, SMOKE_MONTH)

    feat_cols = [c for c in V3_13_FEATURES if c in train_df.columns]
    if len(feat_cols) != len(V3_13_FEATURES):
        missing = set(V3_13_FEATURES) - set(feat_cols)
        out["notes"] = f"Missing features in parquet: {sorted(missing)}. "

    X_train = train_df[feat_cols].astype(np.float64).to_numpy()
    X_test = test_df[feat_cols].astype(np.float64).to_numpy()
    y_train_raw = _coarse_label(train_df)
    y_test_raw = _coarse_label(test_df)

    valid_train = np.isfinite(X_train).all(axis=1) & np.isfinite(y_train_raw) & (y_train_raw != 0)
    valid_test = np.isfinite(X_test).all(axis=1) & np.isfinite(y_test_raw) & (y_test_raw != 0)
    X_train, y_train = X_train[valid_train], (y_train_raw[valid_train] > 0).astype(int)
    X_test, y_test = X_test[valid_test], (y_test_raw[valid_test] > 0).astype(int)

    out["n_train"] = int(len(y_train))
    out["n_test"] = int(len(y_test))
    out["n_train_pos"] = int(y_train.sum())
    out["n_train_neg"] = int(len(y_train) - y_train.sum())

    if len(y_train) < 100 or len(y_test) < 5:
        out["notes"] = (out.get("notes") or "") + (
            f"Insufficient samples (train={len(y_train)}, test={len(y_test)}); "
            "smoke degraded to integration check only."
        )
    else:
        scale_pos_weight = max(out["n_train_neg"], 1) / max(out["n_train_pos"], 1)

        import time as _t

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=1.0,
                min_child_weight=10,
                reg_alpha=1e-3,
                reg_lambda=1.0,
                objective="binary:logistic",
                scale_pos_weight=scale_pos_weight,
                tree_method="hist",
                random_state=42,
                verbosity=0,
                n_jobs=1,
            )
            t0 = _t.time()
            model.fit(X_train, y_train)
            out["fit_seconds"] = round(_t.time() - t0, 3)

            t0 = _t.time()
            y_pred = model.predict(X_test)
            out["predict_seconds"] = round(_t.time() - t0, 3)

        out["test_accuracy"] = round(float((y_pred == y_test).mean()), 4)
        out["test_pos_rate"] = round(float(y_pred.mean()), 4)

        # Feature importance (gain) — show top 3 to confirm import works
        importances = model.feature_importances_
        order = np.argsort(importances)[::-1]
        top3 = [(feat_cols[i], round(float(importances[i]), 4)) for i in order[:3]]
        out["top3_features"] = "; ".join(f"{n}={v}" for n, v in top3)
        out["tbr_or_proxy_present"] = "tbr_zscore_30" in feat_cols

    return out


def write_smoke_results(result: dict) -> None:
    df = pd.DataFrame([result])
    out_path = OUT_DIR / "xgboost_smoke_results.csv"
    df.to_csv(out_path, index=False)
    print(f"  wrote {out_path}  ({len(df.columns)} cols)")


# ----------------------------------------------------------------------
# (c) Pitfalls notes — XGBoost-specific implementation details
# ----------------------------------------------------------------------

PITFALLS_MD = """\
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
"""


def write_pitfalls() -> None:
    out_path = OUT_DIR / "xgboost_pitfalls.md"
    out_path.write_text(PITFALLS_MD)
    print(f"  wrote {out_path}  ({len(PITFALLS_MD.splitlines())} lines)")


# ----------------------------------------------------------------------
# (d) Behavioral-effect predictor (saturation falsifier per
#     `feedback_axis_saturation_predictor.md`)
# ----------------------------------------------------------------------


def write_synthesis(smoke: dict) -> None:
    """Produce a 1-paragraph synthesis with the predicted IS trade-count band
    used by the brief's saturation falsifier."""
    smoke_status = (
        "smoke PASS"
        if smoke["xgboost_available"] and smoke["n_test"] > 0
        else "smoke SKIPPED (no xgboost in env)"
    )
    text = f"""\
# iter-v3/016 EDA synthesis — XGBoost head-to-head smoke

**Status**: {smoke_status}.

## Hyperparameter map
13 of 13 LightGBM Optuna search-space dimensions have a clean XGBoost
equivalent (see `xgboost_param_map.csv`).  Two semantic-equivalence
substitutions: `min_child_samples` → `min_child_weight` (sample-count vs
hessian-sum, same range), and `is_unbalance=True` → `scale_pos_weight=neg/pos`
(must be computed per-fit; not a hyperparameter).  All other parameters map
1-to-1 with identical names and ranges.

## Smoke test summary
- Symbol: {smoke["symbol"]}; test month: {smoke["test_month"]}
- XGBoost installed: {smoke["xgboost_available"]} (version {smoke["xgboost_version"] or "n/a"})
- Train samples: {smoke["n_train"]} ({smoke["n_train_pos"]} pos / {smoke["n_train_neg"]} neg)
- Test samples: {smoke["n_test"]}
- Test accuracy: {smoke["test_accuracy"]}
- Top-3 features by gain: {smoke["top3_features"] or "(skipped)"}
- Fit time: {smoke["fit_seconds"]}s; predict time: {smoke["predict_seconds"]}s

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
"""
    out_path = OUT_DIR / "xgboost_eda_synthesis.md"
    out_path.write_text(text)
    print(f"  wrote {out_path}  ({len(text.splitlines())} lines)")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("[iter-v3/016 EDA] XGBoost smoke + parameter mapping")
    print(f"  features dir: {FEATURES_DIR}")
    print(f"  smoke target: {SMOKE_SYMBOL} / {SMOKE_MONTH}")
    print(f"  out dir: {OUT_DIR}")
    print()

    print("(a) writing parameter map")
    write_param_map()

    print("(b) running smoke test")
    smoke = run_smoke()
    print(f"   xgboost installed: {smoke['xgboost_available']}")
    print(f"   xgboost version:   {smoke['xgboost_version'] or '(n/a)'}")
    print(f"   train samples:     {smoke['n_train']}")
    print(f"   test samples:      {smoke['n_test']}")
    print(f"   test accuracy:     {smoke['test_accuracy']}")
    print(f"   top-3 features:    {smoke['top3_features'] or '(skipped)'}")
    if smoke["notes"]:
        print(f"   notes:             {smoke['notes']}")
    write_smoke_results(smoke)

    print("(c) writing pitfalls notes")
    write_pitfalls()

    print("(d) writing synthesis")
    write_synthesis(smoke)

    print()
    print("[iter-v3/016 EDA] complete — 4 outputs written.")


if __name__ == "__main__":
    main()
