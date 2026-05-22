"""Optuna hyperparameter optimization for XGBoost — parallel to optimization.py.

Uses XGBoost's depth-wise (level-wise) tree growth with ``tree_method='hist'``
instead of LightGBM's leaf-wise growth.  The Optuna integration pattern is
byte-identical to ``optimization.py`` (library-agnostic).

Key differences from optimization.py:
- ``lgb.LGBMClassifier`` → ``xgb.XGBClassifier``
- ``is_unbalance=True`` → ``scale_pos_weight = n_neg / n_pos`` (per-fit)
- ``objective='binary'`` → ``objective='binary:logistic'``
- ``objective='multiclass'`` → ``objective='multi:softprob'`` + ``num_class=3``
- ``num_leaves`` Optuna param DROPPED (no-op under depthwise growth)
- ``tree_method='hist'`` pinned; ``grow_policy='depthwise'`` pinned
- ``n_jobs=1`` pinned (determinism)
- ``verbosity=0`` (XGBoost uses 0 for silent, not -1)
- All other Optuna, CV, OOF buffer patterns identical to optimization.py

See iter-v3/016 brief §2.1 for param-mapping table and design decisions.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import xgboost as xgb

if TYPE_CHECKING:
    import optuna


# ---------------------------------------------------------------------------
# Re-export label helpers so xgb.py can import from a single place
# ---------------------------------------------------------------------------
from crypto_trade.strategies.ml.optimization import (
    classes_to_labels,
    classes_to_labels_ternary,
    compute_per_candle_pnl,
    compute_sharpe,
    compute_sharpe_with_threshold,
    labels_to_classes,
    labels_to_classes_ternary,
)

__all__ = [
    "classes_to_labels",
    "classes_to_labels_ternary",
    "compute_per_candle_pnl",
    "compute_sharpe",
    "compute_sharpe_with_threshold",
    "labels_to_classes",
    "labels_to_classes_ternary",
    "optimize_and_train_xgb",
]


# ---------------------------------------------------------------------------
# Optuna objective — XGBoost variant
# ---------------------------------------------------------------------------


def _objective_xgb(
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
) -> float:
    from sklearn.model_selection import TimeSeriesSplit

    # Confidence threshold — only trade when max(proba) >= threshold
    confidence_threshold = trial.suggest_float("confidence_threshold", 0.50, 0.85)

    # Training window size (optimized by Optuna when open_times provided)
    training_days: int | None = None
    if open_times is not None:
        training_days = trial.suggest_int("training_days", 10, 500, step=10)

    # XGBoost hyperparameters
    # fast_mode (iter-v3/007): hardcode colsample_bytree=1.0 to minimize
    # per-seed feature-subsampling variance during fast exploration.
    fast_mode = trial.study.user_attrs.get("fast_mode", False)

    # NOTE: num_leaves is DROPPED (no-op under depthwise growth per §2.1).
    # grow_policy='depthwise' and tree_method='hist' are pinned (load-bearing
    # architectural axis: maximise difference from LightGBM leaf-wise).
    params: dict = {
        "n_estimators": trial.suggest_int("n_estimators", 50, 500),
        "max_depth": trial.suggest_int("max_depth", 3, 5),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": 1.0 if fast_mode else trial.suggest_float("colsample_bytree", 0.3, 1.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 5, 100),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "random_state": seed,
        "tree_method": "hist",  # pinned — rules out GPU fallback
        "grow_policy": "depthwise",  # pinned — maximise architectural difference
        "n_jobs": 1,  # pinned — determinism
        "verbosity": 0,  # XGBoost: 0=silent (not -1 like LightGBM)
    }

    if ternary:
        # XGBoost multi:softprob returns [n_samples, n_classes] probabilities
        params["objective"] = "multi:softprob"
        params["num_class"] = 3
        y = labels_to_classes_ternary(train_labels)
    else:
        # XGBoost binary:logistic — class imbalance via scale_pos_weight
        params["objective"] = "binary:logistic"
        n_neg = int((train_labels == -1).sum())
        n_pos = int((train_labels == 1).sum())
        params["scale_pos_weight"] = max(n_neg, 1) / max(n_pos, 1)
        y = labels_to_classes(train_labels)

    tscv = TimeSeriesSplit(n_splits=cv_splits, gap=cv_gap)

    import pandas as pd

    if verbose > 0:
        n_long = int((train_labels == 1).sum())
        n_short = int((train_labels == -1).sum())
        total = len(train_labels)
        td_str = f", training_days={training_days}" if training_days is not None else ""
        print(
            f"    [xgb trial {trial.number}] {len(all_columns)} features{td_str} | "
            f"threshold={confidence_threshold:.3f} | "
            f"labels: {n_long} long, {n_short} short "
            f"({100 * n_long / total:.0f}/{100 * n_short / total:.0f}%)"
        )

    w = train_weights
    sharpes: list[float] = []
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

        model = xgb.XGBClassifier(**params)
        model.fit(feat_tr, y_train, sample_weight=w_train)

        # Predict and filter by confidence threshold
        y_proba = model.predict_proba(feat_val)

        sharpe = compute_sharpe_with_threshold(
            y_proba,
            long_pnls[val_idx],
            short_pnls[val_idx],
            confidence_threshold,
            ternary=ternary,
        )
        sharpes.append(sharpe)

        # Per-trial OOF return capture (mirrors optimization.py sub-fix 1a)
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

    mean_sharpe = float(np.mean(sharpes))

    if verbose > 0:
        print(
            f"    [xgb trial {trial.number}] Sharpe={mean_sharpe:.4f} "
            f"(folds: {', '.join(f'{s:.4f}' for s in sharpes)})"
        )

    return mean_sharpe


# ---------------------------------------------------------------------------
# Main entry point — parallel to optimize_and_train in optimization.py
# ---------------------------------------------------------------------------


def optimize_and_train_xgb(
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
) -> tuple[xgb.XGBClassifier, list[str], float]:
    """Run Optuna optimization with XGBoost and return (model, columns, threshold).

    Parallel to ``optimize_and_train`` in optimization.py.  Returns an
    ``xgb.XGBClassifier`` instead of ``lgb.LGBMClassifier``; all other
    return semantics are identical.

    Optuna search space changes vs optimization.py:
    - ``num_leaves`` DROPPED (no-op under depthwise growth)
    - ``min_child_samples`` → ``min_child_weight`` (same range [5, 100])
    - ``objective='binary'`` → ``'binary:logistic'``; ``is_unbalance`` → ``scale_pos_weight``
    - ``objective='multiclass'`` → ``'multi:softprob'``
    - ``grow_policy='depthwise'`` and ``tree_method='hist'`` pinned
    """
    import optuna

    if verbose <= 0:
        optuna.logging.set_verbosity(optuna.logging.WARNING)

    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    # Propagate fast_mode to _objective_xgb via study user_attrs
    study.set_user_attr("fast_mode", fast_mode)

    if sample_weights is None:
        sample_weights = np.ones(len(train_labels), dtype=np.float64)

    oof_buffer: list[dict] | None = [] if oof_persist_path is not None else None

    study.optimize(
        lambda trial: _objective_xgb(
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
        ),
        n_trials=n_trials,
    )

    # Flush per-trial OOF buffer to parquet (mirrors optimization.py sub-fix 1b)
    if oof_persist_path is not None and oof_buffer:
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
            combined.to_parquet(oof_persist_path, index=False)
        else:
            new_df.to_parquet(oof_persist_path, index=False)

    best = study.best_params
    best_threshold = best.get("confidence_threshold", 0.50)

    if verbose > 0:
        best_trial = study.best_trial
        print(f"  XGB Optuna: {n_trials} trials, best Sharpe = {best_trial.value:.4f}")
        print(
            f"  Best params: n_estimators={best['n_estimators']}, "
            f"max_depth={best['max_depth']}, "
            f"lr={best['learning_rate']:.4f}"
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

    # Final retrain with best hyperparams on full training window
    final_params: dict = {
        "n_estimators": best["n_estimators"],
        "max_depth": best["max_depth"],
        "learning_rate": best["learning_rate"],
        "subsample": best["subsample"],
        "colsample_bytree": best.get("colsample_bytree", 1.0),
        "min_child_weight": best["min_child_weight"],
        "reg_alpha": best["reg_alpha"],
        "reg_lambda": best["reg_lambda"],
        "random_state": seed,
        "tree_method": "hist",
        "grow_policy": "depthwise",
        "n_jobs": 1,
        "verbosity": 0,
    }
    if ternary:
        final_params["objective"] = "multi:softprob"
        final_params["num_class"] = 3
    else:
        final_params["objective"] = "binary:logistic"
        n_neg = int((train_labels[final_mask] == -1).sum())
        n_pos = int((train_labels[final_mask] == 1).sum())
        # Remap labels: train_labels uses {-1, 1}; labels_to_classes maps to {0, 1}
        final_params["scale_pos_weight"] = max(n_neg, 1) / max(n_pos, 1)

    model = xgb.XGBClassifier(**final_params)
    model.fit(feat_full, y, sample_weight=final_weights)

    if verbose > 0:
        print(
            f"  XGB retrained on full data ({feat_full.shape[0]} samples, "
            f"{len(all_columns)} features)"
        )

    return model, all_columns, best_threshold
