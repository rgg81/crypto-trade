"""Optuna hyperparameter optimization with time-series CV and Sharpe metric.

Simplified: always uses all feature columns, no confidence threshold,
Sharpe computed from actual trade returns (long_pnls / short_pnls).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import lightgbm as lgb
import numpy as np

if TYPE_CHECKING:
    import optuna


# ---------------------------------------------------------------------------
# Sharpe metric — uses actual trade returns
# ---------------------------------------------------------------------------


def compute_sharpe(
    y_pred_labels: np.ndarray,
    long_pnls: np.ndarray,
    short_pnls: np.ndarray,
) -> float:
    """Compute Sharpe ratio from actual trade PnLs.

    For each prediction, the PnL is determined by the predicted direction:
    - predict long  (1) → pnl = long_pnls[i]
    - predict short (-1) → pnl = short_pnls[i]

    Both long_pnls and short_pnls are already net of fees.
    """
    if len(y_pred_labels) < 2:
        return -10.0

    pnls = np.where(y_pred_labels == 1, long_pnls, short_pnls)

    mean = pnls.mean()
    std = pnls.std()
    if std == 0:
        return -10.0

    sharpe = float(mean / std)
    if abs(sharpe) > 100:
        return -10.0
    return sharpe


def compute_sharpe_with_threshold(
    y_proba: np.ndarray,
    long_pnls: np.ndarray,
    short_pnls: np.ndarray,
    threshold: float,
    min_trades: int = 20,
    ternary: bool = False,
) -> float:
    """Compute Sharpe from actual PnLs, filtering by prediction confidence.

    Only includes trades where max(P(short), P(long)) >= threshold.
    Returns -10.0 penalty if fewer than *min_trades* survive the filter.

    When ternary=True, y_proba has 3 columns [P(short), P(neutral), P(long)].
    Confidence is computed from long/short only; neutral predictions are skipped.
    """
    if ternary:
        # 3-class: [short=0, neutral=1, long=2]
        # Confidence = max(P(short), P(long)), ignoring P(neutral)
        directional_proba = y_proba[:, [0, 2]]  # short, long
        confidence = directional_proba.max(axis=1)
        mask = confidence >= threshold
        n_trades = int(mask.sum())
        if n_trades < min_trades:
            return -10.0
        # Direction: 0=short, 1=long (within the 2-col subset)
        dir_pred = directional_proba[mask].argmax(axis=1)
        y_pred = np.where(dir_pred == 1, 1, -1)  # map to labels
    else:
        confidence = y_proba.max(axis=1)
        mask = confidence >= threshold
        n_trades = int(mask.sum())
        if n_trades < min_trades:
            return -10.0
        pred_classes = y_proba[mask].argmax(axis=1)
        y_pred = classes_to_labels(pred_classes)

    pnls = np.where(y_pred == 1, long_pnls[mask], short_pnls[mask])

    mean = pnls.mean()
    std = pnls.std()
    if std == 0:
        return -10.0

    sharpe = float(mean / std)
    # Guard against numerical overflow (e.g., 1 trade with std≈0 → Sharpe=1e15).
    # No real strategy achieves |Sharpe| > 100.  Discovered in iter 094.
    if abs(sharpe) > 100:
        return -10.0
    return sharpe


def compute_sortino_with_threshold(
    y_proba: np.ndarray,
    long_pnls: np.ndarray,
    short_pnls: np.ndarray,
    threshold: float,
    min_trades: int = 20,
    ternary: bool = False,
) -> float:
    """Compute Sortino from actual PnLs, filtering by prediction confidence.

    Sortino = mean(pnls) / downside_std(pnls)
    where downside_std = std of pnls[pnls < 0] (ddof=0).

    Returns -10.0 penalty if:
      - fewer than min_trades survive the confidence filter
      - fewer than 2 downside trades exist (downside_std undefined or zero)
      - downside_std is zero (all downside trades identical)
      - |Sortino| > 100 (numerical overflow guard, mirrors Sharpe path)

    Only difference from compute_sharpe_with_threshold: denominator is the
    standard deviation of NEGATIVE-PnL trades only (right-skew-aware).
    Same confidence masking, same prediction logic, same class mapping.

    iter-v1/037: loss-function axis (NEW 12th family in v1 catalog).
    """
    if ternary:
        # 3-class: [short=0, neutral=1, long=2]
        directional_proba = y_proba[:, [0, 2]]  # short, long
        confidence = directional_proba.max(axis=1)
        mask = confidence >= threshold
        n_trades = int(mask.sum())
        if n_trades < min_trades:
            return -10.0
        dir_pred = directional_proba[mask].argmax(axis=1)
        y_pred = np.where(dir_pred == 1, 1, -1)
    else:
        confidence = y_proba.max(axis=1)
        mask = confidence >= threshold
        n_trades = int(mask.sum())
        if n_trades < min_trades:
            return -10.0
        pred_classes = y_proba[mask].argmax(axis=1)
        y_pred = classes_to_labels(pred_classes)

    pnls = np.where(y_pred == 1, long_pnls[mask], short_pnls[mask])

    mean = pnls.mean()
    downside = pnls[pnls < 0]
    if len(downside) < 2:
        # No meaningful downside distribution — return penalty rather than +inf or NaN
        return -10.0
    down_std = downside.std()
    if down_std == 0:
        return -10.0

    sortino = float(mean / down_std)
    if abs(sortino) > 100:
        return -10.0
    return sortino


def compute_per_candle_pnl(
    y_proba: np.ndarray,
    long_pnls: np.ndarray,
    short_pnls: np.ndarray,
    threshold: float,
    ternary: bool = False,
) -> np.ndarray:
    """Compute per-candle PnL for validation set rows (pre-aggregation).

    Returns a float64 array of length len(y_proba) where:
    - rows below confidence threshold are assigned 0.0 (no trade)
    - rows above threshold are assigned the realised long or short PnL

    Used by _objective to build the per-trial OOF return buffer for
    iter-v3/003 trial_oof_returns.parquet.
    """
    n = len(y_proba)
    pnls_out = np.zeros(n, dtype=np.float64)
    if ternary:
        directional_proba = y_proba[:, [0, 2]]  # short, long columns
        confidence = directional_proba.max(axis=1)
        mask = confidence >= threshold
        if mask.any():
            dir_pred = directional_proba[mask].argmax(axis=1)
            y_pred = np.where(dir_pred == 1, 1, -1)
            pnls_out[mask] = np.where(y_pred == 1, long_pnls[mask], short_pnls[mask])
    else:
        confidence = y_proba.max(axis=1)
        mask = confidence >= threshold
        if mask.any():
            pred_classes = y_proba[mask].argmax(axis=1)
            y_pred = classes_to_labels(pred_classes)
            pnls_out[mask] = np.where(y_pred == 1, long_pnls[mask], short_pnls[mask])
    return pnls_out


# ---------------------------------------------------------------------------
# Label encoding: {-1, 1} <-> {0, 1} for binary, {-1, 0, 1} <-> {0, 1, 2} for ternary
# ---------------------------------------------------------------------------

_LABEL_TO_CLASS = {-1: 0, 1: 1}
_CLASS_TO_LABEL = {0: -1, 1: 1}

_TERNARY_LABEL_TO_CLASS = {-1: 0, 0: 1, 1: 2}
_TERNARY_CLASS_TO_LABEL = {0: -1, 1: 0, 2: 1}


def labels_to_classes(labels: np.ndarray) -> np.ndarray:
    """Convert {-1, 1} labels to {0, 1} classes for LightGBM."""
    return np.vectorize(_LABEL_TO_CLASS.get)(labels).astype(np.intp)


def labels_to_classes_ternary(labels: np.ndarray) -> np.ndarray:
    """Convert {-1, 0, 1} labels to {0, 1, 2} classes for LightGBM multiclass."""
    return np.vectorize(_TERNARY_LABEL_TO_CLASS.get)(labels).astype(np.intp)


def classes_to_labels(classes: np.ndarray) -> np.ndarray:
    """Convert {0, 1} classes back to {-1, 1} labels."""
    return np.vectorize(_CLASS_TO_LABEL.get)(classes).astype(np.intp)


def classes_to_labels_ternary(classes: np.ndarray) -> np.ndarray:
    """Convert {0, 1, 2} classes back to {-1, 0, 1} labels."""
    return np.vectorize(_TERNARY_CLASS_TO_LABEL.get)(classes).astype(np.intp)


# ---------------------------------------------------------------------------
# Optuna optimization — only LightGBM hyperparams + training_days
# ---------------------------------------------------------------------------


def _objective(
    trial: optuna.Trial,
    train_features: np.ndarray,
    train_labels: np.ndarray,
    train_weights: np.ndarray,
    long_pnls: np.ndarray,
    short_pnls: np.ndarray,
    all_columns: list[str],
    cv_splits: int,
    seed: int,
    verbose: int = 0,
    open_times: np.ndarray | None = None,
    ternary: bool = False,
    cv_gap: int = 0,
    train_month: str = "",
    symbols_arr: np.ndarray | None = None,
    oof_buffer: list[dict] | None = None,
    bounds_profile: str = "default",
    min_child_samples_lower_bound: int | None = None,
) -> float:
    from sklearn.model_selection import TimeSeriesSplit

    # Confidence threshold — only trade when max(proba) >= threshold
    confidence_threshold = trial.suggest_float("confidence_threshold", 0.50, 0.85)

    # Training window size (optimized by Optuna when open_times provided).
    #
    # FULL-WINDOW-TRAINING design: when the study user_attr "full_window_training"
    # is True, training_days is NOT added to the search space — it stays None, which
    # makes the CV per-fold trim below (`if training_days is not None ...`) a no-op,
    # so every fold trains on the full available window. Default False (key absent)
    # is BYTE-IDENTICAL to prior behavior: training_days is suggested + sliced.
    _full_window_training = trial.study.user_attrs.get("full_window_training", False)
    training_days: int | None = None
    if open_times is not None and not _full_window_training:
        training_days = trial.suggest_int("training_days", 10, 500, step=10)

    # LightGBM hyperparameters
    # iter-v3/007 fast_mode: hardcode colsample_bytree=1.0 (skip Optuna suggest)
    # to minimize per-seed feature-subsampling variance during fast exploration.
    # Production runs (fast_mode=False) keep colsample in the search space.
    #
    # bounds_profile — selects the Optuna search bounds for key hyperparameters:
    #   "default"   — original bounds calibrated for the 193-feature v1/v2/v3 stack.
    #   "v1_pruned" — tighter bounds for iter-v1/002+ 40-feature pruned set per LM
    #                 Master Phase 4.5 Recs #1–3:
    #                   num_leaves upper 127 → 63  (depth-5 max = 31 leaves; 63 is 2×)
    #                   colsample_bytree lower 0.3 → 0.5  (40 deduped features; IC-stripped)
    #                   min_child_samples lower 5 → 20    (regularise small per-cell windows)
    #                 max_depth [3,5] UNCHANGED (Rec #4 adopted as no-op).
    #   Unknown profiles fall back to "default" silently (forward-compat).
    _pruned = bounds_profile in ("v1_pruned", "v1_pruned_axis016")
    # iter-v1/016: "v1_pruned_axis016" pins subsample=1.0 and colsample_bytree=1.0 for
    # sample-weighting axis isolation (LM Master Rec #2 ADOPTED-CONDITIONAL).
    # subsample and colsample are tuned in the normal v1_pruned search space —
    # leaving them free would confound F-AXIS-MECHANISM attribution for /016.
    # This profile is /016-only; future iterations revert to "v1_pruned".
    _pin_subsampling = bounds_profile == "v1_pruned_axis016"
    # iter-v1/063: "v1_specialist" profile — SPECIALIST + BUNDLE methodology.
    #   max_depth = 5   FIXED (not suggested; set by lgbm.py after optimization)
    #   num_leaves = 31 FIXED (LightGBM default; not suggested)
    #   min_child_samples REMOVED (uses LGBM default 20; not in search space)
    #   n_estimators upper bound = specialist_n_estimators_max (wall-clock mitigation)
    #   subsample, colsample_bytree, learning_rate, reg_alpha, reg_lambda STILL tunable
    #   confidence_threshold STILL Optuna-tunable per seed (load-bearing)
    _specialist = bounds_profile == "v1_specialist"
    _specialist_n_est_max = (
        int(trial.study.user_attrs.get("specialist_n_estimators_max", 500)) if _specialist else 500
    )
    fast_mode = trial.study.user_attrs.get("fast_mode", False)
    # n_estimators upper bound: 500 for specialist (wall-clock mitigation), else original.
    _n_est_max = _specialist_n_est_max if _specialist else 500
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 50, _n_est_max),
        # max_depth: FIXED at 5 for specialist (not suggested); tunable otherwise.
        "max_depth": 5 if _specialist else trial.suggest_int("max_depth", 3, 5),
        # num_leaves: FIXED at 31 for specialist (not suggested); tunable otherwise.
        "num_leaves": 31
        if _specialist
        else trial.suggest_int("num_leaves", 15, 63 if _pruned else 127),
        "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.05, log=True)
        if _specialist
        else trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": 1.0
        if _pin_subsampling
        else trial.suggest_float(
            "subsample", 0.4 if _specialist else (0.5 if _pruned else 0.5), 1.0
        ),
        "colsample_bytree": 1.0
        if (fast_mode or _pin_subsampling)
        else trial.suggest_float(
            "colsample_bytree",
            0.4 if _specialist else (0.5 if _pruned else 0.3),
            1.0,
        ),
        # min_child_samples: REMOVED from search space for specialist (uses LGBM default 20).
        # For non-specialist: honor min_child_samples_lower_bound or profile default.
        **(
            {}
            if _specialist
            else {
                "min_child_samples": trial.suggest_int(
                    "min_child_samples",
                    # iter-v1/041: min_child_samples_lower_bound threads a per-iteration
                    # Optuna lower bound override.  When set, overrides the v1_pruned default
                    # of 20.  None = BIT-IDENTICAL to prior behaviour (20 for pruned, 5 otherwise).
                    min_child_samples_lower_bound
                    if min_child_samples_lower_bound is not None
                    else (20 if _pruned else 5),
                    100,
                )
            }
        ),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True)
        if _specialist
        else trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True)
        if _specialist
        else trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "random_state": seed,
        "verbosity": -1,
    }
    # For specialist profile, min_child_samples uses LGBM default (20) — not in params dict.
    # LightGBM will use its internal default when the key is absent.
    if ternary:
        params["objective"] = "multiclass"
        params["num_class"] = 3
        y = labels_to_classes_ternary(train_labels)
    else:
        params["objective"] = "binary"
        params["is_unbalance"] = True
        y = labels_to_classes(train_labels)
    # gap prevents label leakage across CV folds — excludes training samples
    # whose triple-barrier labels could see into the validation period.
    tscv = TimeSeriesSplit(n_splits=cv_splits, gap=cv_gap)

    import pandas as pd

    if verbose > 0:
        n_long = int((train_labels == 1).sum())
        n_short = int((train_labels == -1).sum())
        total = len(train_labels)
        td_str = f", training_days={training_days}" if training_days is not None else ""
        print(
            f"    [trial {trial.number}] {len(all_columns)} features{td_str} | "
            f"threshold={confidence_threshold:.3f} | "
            f"labels: {n_long} long, {n_short} short "
            f"({100 * n_long / total:.0f}/{100 * n_short / total:.0f}%)"
        )

    w = train_weights
    scores: list[float] = []
    feat_df = pd.DataFrame(train_features, columns=all_columns)

    import datetime

    for fold_k, (train_idx, val_idx) in enumerate(tscv.split(train_features)):
        # Trim training data to last `training_days` days before validation
        if training_days is not None and open_times is not None:
            val_start_time = open_times[val_idx[0]]
            cutoff_ms = val_start_time - training_days * 86_400_000
            trimmed_mask = open_times[train_idx] >= cutoff_ms
            train_idx = train_idx[trimmed_mask]
            if len(train_idx) == 0:
                return -10.0

        # Label leakage audit — print on first trial only
        if trial.number == 0 and verbose > 0 and open_times is not None:
            last_train_ms = int(open_times[train_idx[-1]])
            first_val_ms = int(open_times[val_idx[0]])
            gap_ms = first_val_ms - last_train_ms
            last_t = datetime.datetime.fromtimestamp(
                last_train_ms / 1000, tz=datetime.UTC
            ).strftime("%Y-%m-%d %H:%M")
            first_v = datetime.datetime.fromtimestamp(
                first_val_ms / 1000, tz=datetime.UTC
            ).strftime("%Y-%m-%d %H:%M")
            gap_hours = gap_ms / 3_600_000
            print(
                f"    [CV fold {fold_k}] train_end={last_t} | val_start={first_v} | "
                f"gap={gap_hours:.0f}h ({cv_gap} rows)"
            )

        feat_tr = feat_df.iloc[train_idx]
        feat_val = feat_df.iloc[val_idx]
        y_train = y[train_idx]
        w_train = w[train_idx]

        model = lgb.LGBMClassifier(**params)
        model.fit(feat_tr, y_train, sample_weight=w_train)

        # Predict and filter by confidence threshold
        y_proba = model.predict_proba(feat_val)

        # iter-v1/037: dispatch to Sortino or Sharpe based on study user_attr
        _optuna_objective = trial.study.user_attrs.get("optuna_objective", "sharpe")
        if _optuna_objective == "sortino":
            score_fn = compute_sortino_with_threshold
        elif _optuna_objective == "sharpe":
            score_fn = compute_sharpe_with_threshold
        else:
            raise ValueError(f"Unknown optuna_objective: {_optuna_objective!r}")

        score = score_fn(
            y_proba,
            long_pnls[val_idx],
            short_pnls[val_idx],
            confidence_threshold,
            ternary=ternary,
        )
        scores.append(score)

        # Sub-fix 1a (iter-v3/003): capture per-candle OOF returns for trial buffer
        if oof_buffer is not None:
            per_candle = compute_per_candle_pnl(
                y_proba,
                long_pnls[val_idx],
                short_pnls[val_idx],
                confidence_threshold,
                ternary=ternary,
            )
            for local_i, global_i in enumerate(val_idx):
                candle_ts = int(open_times[global_i]) if open_times is not None else int(global_i)
                sym = str(symbols_arr[global_i]) if symbols_arr is not None else ""
                oof_buffer.append(
                    {
                        "trial_id": trial.number,
                        "symbol": sym,
                        "train_month": train_month,
                        "fold_idx": fold_k,
                        "candle_open_time_ms": candle_ts,
                        "oof_return": float(per_candle[local_i]),
                    }
                )

    mean_score = float(np.mean(scores))

    if verbose > 0:
        # Label the metric in the log based on the active objective
        _obj_label = trial.study.user_attrs.get("optuna_objective", "sharpe").capitalize()
        print(
            f"    [trial {trial.number}] {_obj_label}={mean_score:.4f} "
            f"(folds: {', '.join(f'{s:.4f}' for s in scores)})"
        )

    return mean_score


def optimize_and_train(
    train_features: np.ndarray,
    train_labels: np.ndarray,
    all_columns: list[str],
    long_pnls: np.ndarray,
    short_pnls: np.ndarray,
    n_trials: int,
    cv_splits: int,
    seed: int,
    verbose: int = 0,
    sample_weights: np.ndarray | None = None,
    open_times: np.ndarray | None = None,
    train_end_ms: int | None = None,
    ternary: bool = False,
    cv_gap: int = 0,
    oof_persist_path: Path | None = None,
    train_month: str = "",
    symbols_arr: np.ndarray | None = None,
    fast_mode: bool = False,
    bounds_profile: str = "default",
    params_persist_path: Path | None = None,
    model_role: str = "",
    symbol: str = "",
    optuna_objective: str = "sharpe",
    min_child_samples_lower_bound: int | None = None,
    full_window_training: bool = False,
) -> tuple[lgb.LGBMClassifier, list[str], float]:
    """Run Optuna optimization and return (model, columns, confidence_threshold).

    Uses all feature columns (no group/period selection).
    Confidence threshold is optimized by Optuna and applied at inference time.
    Sharpe (or Sortino when optuna_objective='sortino') is computed from actual
    trade returns filtered by threshold.

    optuna_objective: 'sharpe' (default, BIT-IDENTICAL to all pre-/037 callers)
        or 'sortino' (iter-v1/037 loss-function axis). Propagated to _objective
        via study user_attrs so the lambda closure is stateless.

    cv_gap: number of rows to exclude between training and validation folds,
    preventing label leakage from overlapping triple-barrier labels.

    oof_persist_path: if set, per-trial OOF candle returns are appended to
    this parquet file after study.optimize() returns (sub-fix 1b, iter-v3/003).
    train_month and symbols_arr are embedded in each row for multi-symbol grouping.

    bounds_profile: selects the Optuna hyperparameter search bounds.
        "default"          — original bounds for the 193-feature v1/v2/v3 stack.
        "v1_pruned"        — tighter bounds for iter-v1/002+ 40-feature pruned set per
                             LM Master Phase 4.5 Recs #1–3 (num_leaves≤63,
                             colsample≥0.5, min_child_samples≥20). v3 and v2 are
                             NOT affected — they continue with "default".
        "v1_pruned_axis016" — iter-v1/016 only: v1_pruned bounds PLUS subsample=1.0
                              and colsample_bytree=1.0 pinned (LM Master Rec #2
                              ADOPTED-CONDITIONAL; isolates the sample-weighting axis
                              from sub-sampling perturbations in Optuna search).

    params_persist_path: if set, after study.optimize() completes, append ONE row to
        the parquet at this path capturing study.best_params + metadata per
        (model_role, symbol, train_month, seed). iter-v1/021 H1 diagnostic.
        Uses atomic write via tempfile.mkstemp + os.replace (same pattern as
        oof_persist_path). NO .get(default) silent drops — all 11 hyperparameter
        columns are written explicitly; pinned values (subsample=1.0 for
        v1_pruned_axis016; colsample_bytree=1.0 for fast_mode) are written as the
        pinned constant, NOT silently dropped to a default.
    model_role: caller-provided model identifier (e.g. "Model_A_pool",
        "Model_H_BTC"). Embedded in each params_persist_path row.
    symbol: caller-provided symbol (e.g. "BTCUSDT"). Embedded in each row.
    min_child_samples_lower_bound: iter-v1/041 — when set, overrides the
        per-profile default Optuna lower bound for min_child_samples.
        None = BIT-IDENTICAL to prior behaviour (20 for v1_pruned, 5 for default).
        Use 50 for iter-v1/041 triple-barrier tighten (denser-label noise mitigation).
    """
    import optuna

    if verbose <= 0:
        optuna.logging.set_verbosity(optuna.logging.WARNING)

    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    # iter-v3/007: propagate fast_mode to _objective via study user_attrs
    study.set_user_attr("fast_mode", fast_mode)
    # iter-v1/037: propagate optuna_objective to _objective via study user_attrs.
    # Default "sharpe" is BIT-IDENTICAL to all pre-/037 callers.
    if optuna_objective not in ("sharpe", "sortino"):
        raise ValueError(
            f"optuna_objective must be 'sharpe' or 'sortino'; got {optuna_objective!r}"
        )
    study.set_user_attr("optuna_objective", optuna_objective)
    # FULL-WINDOW-TRAINING design: propagate to _objective so training_days is not
    # suggested (and the CV per-fold slice is skipped). Default False is
    # BYTE-IDENTICAL to all prior callers.
    study.set_user_attr("full_window_training", full_window_training)

    if sample_weights is None:
        sample_weights = np.ones(len(train_labels), dtype=np.float64)

    # Sub-fix 1a: shared mutable buffer; _objective appends rows per (trial, fold)
    oof_buffer: list[dict] | None = [] if oof_persist_path is not None else None

    study.optimize(
        lambda trial: _objective(
            trial,
            train_features,
            train_labels,
            sample_weights,
            long_pnls,
            short_pnls,
            all_columns,
            cv_splits,
            seed,
            verbose,
            open_times=open_times,
            ternary=ternary,
            cv_gap=cv_gap,
            train_month=train_month,
            symbols_arr=symbols_arr,
            oof_buffer=oof_buffer,
            bounds_profile=bounds_profile,
            min_child_samples_lower_bound=min_child_samples_lower_bound,
        ),
        n_trials=n_trials,
    )

    # Sub-fix 1b: flush per-trial OOF buffer to parquet (append if file exists).
    # iter-v3/082 infra fix: atomic write via write-to-temp + os.replace().
    # to_parquet() in-place truncates then streams — a mid-write interruption
    # leaves a file with no Parquet footer ("magic bytes not found") that
    # corrupts every subsequent read.  os.replace() is atomic on POSIX: readers
    # always see a complete old or complete new file, never a partial write.
    # The writers are strictly serial (outer symbol loop + serial walk-forward
    # months, study.optimize n_jobs=1), so no cross-writer lock is needed.
    if oof_persist_path is not None and oof_buffer:
        import os
        import tempfile

        import pandas as pd

        oof_persist_path.parent.mkdir(parents=True, exist_ok=True)
        new_df = pd.DataFrame(
            oof_buffer,
            columns=[
                "trial_id",
                "symbol",
                "train_month",
                "fold_idx",
                "candle_open_time_ms",
                "oof_return",
            ],
        )
        if oof_persist_path.exists():
            existing = pd.read_parquet(oof_persist_path)
            combined = pd.concat([existing, new_df], ignore_index=True)
        else:
            combined = new_df
        # Write to a sibling temp file, then atomically replace the target.
        tmp_fd, tmp_name = tempfile.mkstemp(dir=oof_persist_path.parent, suffix=".parquet.tmp")
        try:
            os.close(tmp_fd)
            combined.to_parquet(tmp_name, index=False)
            os.replace(tmp_name, oof_persist_path)
        except Exception:
            # Clean up temp file on failure; do not leave a partial write.
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    best = study.best_params
    best_threshold = best.get("confidence_threshold", 0.50)

    # iter-v1/021: flush Optuna best_params to params_persist_path parquet.
    # Captures all 11 hyperparameter columns per (model_role, symbol, train_month, seed)
    # for the pool-anchor training-time diagnostic (H1 falsifier).
    #
    # CRITICAL: NO .get(default) silent drops.
    # - For v1_pruned_axis016 (subsample=1.0 pinned), write the pinned constant 1.0
    #   explicitly — the TPE search never suggested subsample/colsample, so they are
    #   absent from best, but the EFFECTIVE value is known (the pinned constant).
    # - For fast_mode (colsample_bytree=1.0 hardcoded), write 1.0 explicitly.
    # - If a key is unexpectedly absent from best, log a WARNING to stderr so the
    #   Phase 7.5 Layer C audit can catch the partial-visibility issue.
    if params_persist_path is not None:
        import os
        import sys
        import tempfile

        import pandas as pd

        _is_axis016 = bounds_profile == "v1_pruned_axis016"
        _is_fast = fast_mode  # resolved above via study.user_attrs

        def _get_param(key: str, pinned_value: float | int | None = None) -> float | int:
            """Retrieve a param with explicit logging on miss (no silent drop)."""
            if key in best:
                return best[key]
            if pinned_value is not None:
                return pinned_value
            print(
                f"[params_persist_path] WARNING: key {key!r} missing from study.best_params "
                f"for model_role={model_role!r} symbol={symbol!r} train_month={train_month!r} "
                f"seed={seed}; bounds_profile={bounds_profile!r}. "
                "H1 falsifier visibility is PARTIAL for this row.",
                file=sys.stderr,
            )
            return float("nan")

        # subsample: pinned at 1.0 for v1_pruned_axis016; otherwise sampled
        _subsample_pinned = 1.0 if _is_axis016 else None
        # colsample_bytree: pinned at 1.0 for fast_mode OR v1_pruned_axis016; otherwise sampled
        _colsample_pinned = 1.0 if (_is_fast or _is_axis016) else None

        params_row = {
            "model_role": model_role,
            "symbol": symbol,
            "train_month": train_month,
            "seed": seed,
            "best_objective_value": float(study.best_value),
            "confidence_threshold": _get_param("confidence_threshold"),
            "training_days": _get_param("training_days") if "training_days" in best else None,
            "n_estimators": _get_param("n_estimators"),
            "max_depth": _get_param("max_depth"),
            "num_leaves": _get_param("num_leaves"),
            "learning_rate": _get_param("learning_rate"),
            "subsample": _get_param("subsample", _subsample_pinned),
            "colsample_bytree": _get_param("colsample_bytree", _colsample_pinned),
            "min_child_samples": _get_param("min_child_samples"),
            "reg_alpha": _get_param("reg_alpha"),
            "reg_lambda": _get_param("reg_lambda"),
        }

        params_persist_path.parent.mkdir(parents=True, exist_ok=True)
        new_params_df = pd.DataFrame([params_row])
        if params_persist_path.exists():
            existing_params = pd.read_parquet(params_persist_path)
            combined_params = pd.concat([existing_params, new_params_df], ignore_index=True)
        else:
            combined_params = new_params_df
        tmp_fd, tmp_name = tempfile.mkstemp(dir=params_persist_path.parent, suffix=".parquet.tmp")
        try:
            os.close(tmp_fd)
            combined_params.to_parquet(tmp_name, index=False)
            os.replace(tmp_name, params_persist_path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    if verbose > 0:
        best_trial = study.best_trial
        print(f"  Optuna: {n_trials} trials, best Sharpe = {best_trial.value:.4f}")
        print(
            f"  Best params: n_estimators={best['n_estimators']}, "
            f"max_depth={best['max_depth']}, "
            f"lr={best['learning_rate']:.4f}, leaves={best['num_leaves']}"
        )
        print(f"  Best confidence_threshold: {best_threshold:.3f}")
        if "training_days" in best:
            print(f"  Best training_days: {best['training_days']}")

    import pandas as pd

    # Trim to best training_days for final retrain.
    # FULL-WINDOW-TRAINING design: when full_window_training is True, training_days
    # was never suggested (so "training_days" is absent from best and this slice would
    # already be skipped). The explicit `not full_window_training` guard documents the
    # intent and keeps the final fit on the full window — consistent with the CV folds.
    final_mask = np.ones(len(train_labels), dtype=bool)
    if not full_window_training and open_times is not None and "training_days" in best:
        best_training_days = best["training_days"]
        anchor_ms = train_end_ms if train_end_ms is not None else int(open_times[-1])
        cutoff_ms = anchor_ms - best_training_days * 86_400_000
        final_mask = open_times >= cutoff_ms

    feat_full = pd.DataFrame(train_features[final_mask], columns=all_columns)
    if ternary:
        y = labels_to_classes_ternary(train_labels[final_mask])
    else:
        y = labels_to_classes(train_labels[final_mask])
    final_weights = sample_weights[final_mask]

    # Retrain on full training data
    # iter-v3/007: in fast_mode, colsample_bytree is hardcoded to 1.0 (not in
    # the Optuna search space), so `best` won't contain it — use 1.0 directly.
    # iter-v1/016: v1_pruned_axis016 also pins subsample=1.0 (not suggested),
    # so apply the same .get(..., 1.0) safety fallback.
    params = {
        "n_estimators": best["n_estimators"],
        "max_depth": best["max_depth"],
        "num_leaves": best["num_leaves"],
        "learning_rate": best["learning_rate"],
        "subsample": best.get("subsample", 1.0),
        "colsample_bytree": best.get("colsample_bytree", 1.0),
        "min_child_samples": best["min_child_samples"],
        "reg_alpha": best["reg_alpha"],
        "reg_lambda": best["reg_lambda"],
        "random_state": seed,
        "verbosity": -1,
    }
    if ternary:
        params["objective"] = "multiclass"
        params["num_class"] = 3
    else:
        params["objective"] = "binary"
        params["is_unbalance"] = True

    model = lgb.LGBMClassifier(**params)
    model.fit(feat_full, y, sample_weight=final_weights)

    if verbose > 0:
        print(
            f"  Retrained on full data ({feat_full.shape[0]} samples, {len(all_columns)} features)"
        )

    return model, all_columns, best_threshold
