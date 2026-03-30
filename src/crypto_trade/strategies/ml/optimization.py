"""Optuna hyperparameter optimization with time-series CV and Sharpe metric.

Simplified: always uses all feature columns, no confidence threshold,
Sharpe computed from actual trade returns (long_pnls / short_pnls).
"""

from __future__ import annotations

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

    return float(mean / std)


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

    return float(mean / std)


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
) -> float:
    from sklearn.model_selection import TimeSeriesSplit

    # Confidence threshold — only trade when max(proba) >= threshold
    confidence_threshold = trial.suggest_float("confidence_threshold", 0.50, 0.85)

    # Training window size (optimized by Optuna when open_times provided)
    training_days: int | None = None
    if open_times is not None:
        training_days = trial.suggest_int("training_days", 10, 500, step=10)

    # LightGBM hyperparameters
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 50, 500),
        "max_depth": trial.suggest_int("max_depth", 3, 5),
        "num_leaves": trial.suggest_int("num_leaves", 15, 127),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.3, 1.0),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "random_state": seed,
        "verbosity": -1,
    }
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
    sharpes: list[float] = []
    feat_df = pd.DataFrame(train_features, columns=all_columns)

    for train_idx, val_idx in tscv.split(train_features):
        # Trim training data to last `training_days` days before validation
        if training_days is not None and open_times is not None:
            val_start_time = open_times[val_idx[0]]
            cutoff_ms = val_start_time - training_days * 86_400_000
            trimmed_mask = open_times[train_idx] >= cutoff_ms
            train_idx = train_idx[trimmed_mask]
            if len(train_idx) == 0:
                return -10.0

        feat_tr = feat_df.iloc[train_idx]
        feat_val = feat_df.iloc[val_idx]
        y_train = y[train_idx]
        w_train = w[train_idx]

        model = lgb.LGBMClassifier(**params)
        model.fit(feat_tr, y_train, sample_weight=w_train)

        # Predict and filter by confidence threshold
        y_proba = model.predict_proba(feat_val)

        sharpe = compute_sharpe_with_threshold(
            y_proba, long_pnls[val_idx], short_pnls[val_idx],
            confidence_threshold, ternary=ternary,
        )
        sharpes.append(sharpe)

    mean_sharpe = float(np.mean(sharpes))

    if verbose > 0:
        print(
            f"    [trial {trial.number}] Sharpe={mean_sharpe:.4f} "
            f"(folds: {', '.join(f'{s:.4f}' for s in sharpes)})"
        )

    return mean_sharpe


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
) -> tuple[lgb.LGBMClassifier, list[str], float]:
    """Run Optuna optimization and return (model, columns, confidence_threshold).

    Uses all feature columns (no group/period selection).
    Confidence threshold is optimized by Optuna and applied at inference time.
    Sharpe is computed from actual trade returns filtered by threshold.

    cv_gap: number of rows to exclude between training and validation folds,
    preventing label leakage from overlapping triple-barrier labels.
    """
    import optuna

    if verbose <= 0:
        optuna.logging.set_verbosity(optuna.logging.WARNING)

    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)

    if sample_weights is None:
        sample_weights = np.ones(len(train_labels), dtype=np.float64)

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
        ),
        n_trials=n_trials,
    )

    best = study.best_params
    best_threshold = best.get("confidence_threshold", 0.50)

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

    # Trim to best training_days for final retrain
    final_mask = np.ones(len(train_labels), dtype=bool)
    if open_times is not None and "training_days" in best:
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
    params = {
        "n_estimators": best["n_estimators"],
        "max_depth": best["max_depth"],
        "num_leaves": best["num_leaves"],
        "learning_rate": best["learning_rate"],
        "subsample": best["subsample"],
        "colsample_bytree": best["colsample_bytree"],
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
            f"  Retrained on full data ({feat_full.shape[0]} samples, "
            f"{len(all_columns)} features)"
        )

    return model, all_columns, best_threshold
