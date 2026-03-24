"""Optuna hyperparameter optimization with time-series CV and Sharpe metric."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import lightgbm as lgb
import numpy as np

if TYPE_CHECKING:
    import optuna

# ---------------------------------------------------------------------------
# Feature column mapping
# ---------------------------------------------------------------------------

# Group prefixes — note vol_ is shared by volatility and volume groups
_VOLATILITY_INDICATORS = frozenset(
    {"atr", "natr", "bb_bandwidth", "bb_pctb", "range_spike", "garman_klass", "parkinson", "hist"}
)
_VOLUME_INDICATORS = frozenset(
    {
        "obv",
        "cmf",
        "mfi",
        "ad",
        "vwap",
        "taker_buy_ratio",
        "taker_buy_ratio_sma",
        "volume_pctchg",
        "volume_rel",
    }
)

_GROUP_PREFIX_MAP = {
    "mom": "momentum",
    "trend": "trend",
    "mr": "mean_reversion",
    "stat": "statistical",
}

# Columns with no period (always included if group selected)
_NO_PERIOD_COLUMNS = frozenset(
    {
        "vol_obv",
        "vol_ad",
        "vol_vwap",
        "vol_taker_buy_ratio",
        "trend_psar_af",
        "trend_psar_dir",
        "mr_dist_vwap",
    }
)

# Pattern for MACD columns: mom_macd_{type}_{fast}_{slow}_{signal}
_MACD_RE = re.compile(r"^mom_macd_(?:line|hist|signal)_(\d+)_(\d+)_(\d+)$")
# Pattern for cross columns: trend_{type}_cross_{fast}_{slow}
_CROSS_RE = re.compile(r"^trend_(?:ema|sma)_cross_(\d+)_(\d+)$")
# Pattern for supertrend: trend_supertrend_{length}_{mult}
_SUPERTREND_RE = re.compile(r"^trend_supertrend_(\d+)_")
# Generic trailing number
_TRAILING_NUM_RE = re.compile(r"_(\d+)$")
# Autocorr pattern: stat_autocorr_lag{N}
_AUTOCORR_RE = re.compile(r"^stat_autocorr_lag(\d+)$")


def _classify_vol_column(col: str) -> str | None:
    """Disambiguate vol_ columns into 'volatility' or 'volume' group."""
    # Strip prefix
    suffix = col[4:]  # after 'vol_'
    for indicator in _VOLATILITY_INDICATORS:
        if suffix == indicator or suffix.startswith(indicator + "_"):
            return "volatility"
    for indicator in _VOLUME_INDICATORS:
        if suffix == indicator or suffix.startswith(indicator + "_"):
            return "volume"
    return None


def _parse_column(col: str) -> tuple[str | None, int | None]:
    """Parse a feature column name into (group_name, period_or_None)."""
    if col in _NO_PERIOD_COLUMNS:
        if col.startswith("vol_"):
            group = _classify_vol_column(col)
        else:
            group = _GROUP_PREFIX_MAP.get(col.split("_")[0])
        if group is None and col.startswith("trend_"):
            group = "trend"
        if group is None and col.startswith("mr_"):
            group = "mean_reversion"
        return group, None

    # MACD: use slow period
    m = _MACD_RE.match(col)
    if m:
        return "momentum", int(m.group(2))

    # Cross: use slow period
    m = _CROSS_RE.match(col)
    if m:
        return "trend", int(m.group(2))

    # Supertrend: use length
    m = _SUPERTREND_RE.match(col)
    if m:
        return "trend", int(m.group(1))

    # Autocorr
    m = _AUTOCORR_RE.match(col)
    if m:
        return "statistical", int(m.group(1))

    # vol_ disambiguation
    if col.startswith("vol_"):
        group = _classify_vol_column(col)
        if group is None:
            return None, None
        m2 = _TRAILING_NUM_RE.search(col)
        return group, int(m2.group(1)) if m2 else None

    # Generic: prefix -> group, trailing number -> period
    prefix = col.split("_")[0]
    group = _GROUP_PREFIX_MAP.get(prefix)
    if group is None:
        return None, None
    m2 = _TRAILING_NUM_RE.search(col)
    return group, int(m2.group(1)) if m2 else None


def build_feature_column_map(
    all_feature_columns: list[str],
    group_names: list[str] | None = None,
) -> dict[str, dict[int | None, list[str]]]:
    """Build mapping: {group_name: {period_or_None: [column_names]}}.

    If *group_names* is None, all 6 groups are included.
    """
    if group_names is None:
        group_names = ["momentum", "volatility", "trend", "volume", "mean_reversion", "statistical"]

    result: dict[str, dict[int | None, list[str]]] = {g: {} for g in group_names}

    for col in all_feature_columns:
        group, period = _parse_column(col)
        if group is None or group not in result:
            continue
        result[group].setdefault(period, []).append(col)

    return result


def select_feature_columns(
    feature_col_map: dict[str, dict[int | None, list[str]]],
    use_groups: dict[str, bool],
    min_period: int,
    max_period: int,
) -> list[str]:
    """Select feature columns based on group toggles and period range."""
    selected: list[str] = []
    for group, periods in feature_col_map.items():
        if not use_groups.get(group, False):
            continue
        for period, cols in periods.items():
            if period is None:
                # Always include no-period features if group is selected
                selected.extend(cols)
            elif min_period <= period <= max_period:
                selected.extend(cols)
    return sorted(selected)


# ---------------------------------------------------------------------------
# Sharpe metric
# ---------------------------------------------------------------------------


def compute_sharpe(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    tp_pct: float,
    sl_pct: float,
    fee_pct: float,
) -> float:
    """Compute Sharpe ratio from simulated trade PnL.

    Every prediction is a trade (binary: long or short, no skip).
    Correct direction → +tp_pct - fee_pct
    Wrong direction  → -sl_pct - fee_pct
    """
    if len(y_pred) < 2:
        return -10.0

    correct = y_true == y_pred
    pnls = np.where(correct, tp_pct - fee_pct, -sl_pct - fee_pct)

    mean = pnls.mean()
    std = pnls.std()
    if std == 0:
        return -10.0

    return float(mean / std)


def compute_sharpe_with_threshold(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    threshold: float,
    tp_pct: float,
    sl_pct: float,
    fee_pct: float,
    min_trades: int = 20,
) -> float:
    """Compute Sharpe ratio filtering by prediction confidence.

    Only evaluates samples where ``max(P(short), P(long)) >= threshold``.
    Returns ``-10.0`` penalty if fewer than *min_trades* survive the filter.
    """
    confidence = y_proba.max(axis=1)
    mask = confidence >= threshold

    n_trades = int(mask.sum())
    if n_trades < min_trades:
        return -10.0

    pred_classes = y_proba.argmax(axis=1)
    y_pred = classes_to_labels(pred_classes)

    y_filtered = y_true[mask]
    pred_filtered = y_pred[mask]

    correct = y_filtered == pred_filtered
    pnls = np.where(correct, tp_pct - fee_pct, -sl_pct - fee_pct)

    mean = pnls.mean()
    std = pnls.std()
    if std == 0:
        return -10.0

    return float(mean / std)


# ---------------------------------------------------------------------------
# Label encoding: {-1, 1} <-> {0, 1} for binary LightGBM
# ---------------------------------------------------------------------------

_LABEL_TO_CLASS = {-1: 0, 1: 1}
_CLASS_TO_LABEL = {0: -1, 1: 1}


def labels_to_classes(labels: np.ndarray) -> np.ndarray:
    """Convert {-1, 1} labels to {0, 1} classes for LightGBM."""
    return np.vectorize(_LABEL_TO_CLASS.get)(labels).astype(np.intp)


def classes_to_labels(classes: np.ndarray) -> np.ndarray:
    """Convert {0, 1} classes back to {-1, 1} labels."""
    return np.vectorize(_CLASS_TO_LABEL.get)(classes).astype(np.intp)


# ---------------------------------------------------------------------------
# Optuna optimization
# ---------------------------------------------------------------------------

ALL_GROUPS = ["momentum", "volatility", "trend", "volume", "mean_reversion", "statistical"]


def _objective(
    trial: optuna.Trial,
    train_features: np.ndarray,
    train_labels: np.ndarray,
    train_weights: np.ndarray,
    all_columns: list[str],
    feature_col_map: dict[str, dict[int | None, list[str]]],
    cv_splits: int,
    tp_pct: float,
    sl_pct: float,
    fee_pct: float,
    seed: int,
    verbose: int = 0,
    open_times: np.ndarray | None = None,
) -> float:
    from sklearn.model_selection import TimeSeriesSplit

    # Feature selection
    use_groups: dict[str, bool] = {}
    for g in ALL_GROUPS:
        use_groups[g] = trial.suggest_categorical(f"use_{g}", [True, False])

    if not any(use_groups.values()):
        # Force at least one group on
        use_groups["momentum"] = True

    min_period = trial.suggest_int("min_period", 3, 30)
    max_period = trial.suggest_int("max_period", max(min_period + 1, 10), 100)

    confidence_threshold = trial.suggest_float("confidence_threshold", 0.50, 0.55)

    # Training window size (optimized by Optuna when open_times provided)
    training_days: int | None = None
    if open_times is not None:
        training_days = trial.suggest_int("training_days", 10, 500, step=10)

    selected_cols = select_feature_columns(feature_col_map, use_groups, min_period, max_period)
    if not selected_cols:
        return -10.0

    # Map column names to indices
    col_indices = [all_columns.index(c) for c in selected_cols]
    feat = train_features[:, col_indices]

    # LightGBM hyperparameters (binary classification: short=0, long=1)
    params = {
        "objective": "binary",
        "n_estimators": trial.suggest_int("n_estimators", 50, 500),
        "max_depth": trial.suggest_int("max_depth", 3, 5),
        "num_leaves": trial.suggest_int("num_leaves", 15, 127),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.3, 1.0),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "is_unbalance": True,
        "random_state": seed,
        "verbosity": -1,
    }

    y = labels_to_classes(train_labels)
    tscv = TimeSeriesSplit(n_splits=cv_splits)

    import pandas as pd

    if verbose > 0:
        n_long = int((train_labels == 1).sum())
        n_short = int((train_labels == -1).sum())
        total = len(train_labels)
        avg_w = float(train_weights.mean())
        active_groups = [g for g, on in use_groups.items() if on]
        td_str = f", training_days={training_days}" if training_days is not None else ""
        print(
            f"    [trial {trial.number}] {len(selected_cols)} features "
            f"(groups={active_groups}, period={min_period}-{max_period}{td_str}) | "
            f"labels: {n_long} long, {n_short} short "
            f"({100 * n_long / total:.0f}/{100 * n_short / total:.0f}%) | "
            f"avg_weight={avg_w:.2f} | threshold={confidence_threshold:.3f}"
        )

    # Collect all val probabilities across folds for the classification report
    all_val_labels: list[np.ndarray] = []
    all_val_probas: list[np.ndarray] = []

    w = train_weights
    sharpes: list[float] = []
    feat_df = pd.DataFrame(feat, columns=selected_cols)
    for train_idx, val_idx in tscv.split(feat):
        # Trim training data to last `training_days` days before validation start
        if training_days is not None and open_times is not None:
            val_start_time = open_times[val_idx[0]]
            cutoff_ms = val_start_time - training_days * 86_400_000
            trimmed_mask = open_times[train_idx] >= cutoff_ms
            train_idx = train_idx[trimmed_mask]
            if len(train_idx) == 0:
                return -10.0

        feat_tr, feat_val = feat_df.iloc[train_idx], feat_df.iloc[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        w_train = w[train_idx]

        model = lgb.LGBMClassifier(**params)
        model.fit(feat_tr, y_train, sample_weight=w_train)

        y_proba = model.predict_proba(feat_val)
        y_val_labels = classes_to_labels(y_val)

        all_val_labels.append(y_val_labels)
        all_val_probas.append(y_proba)

        sharpe = compute_sharpe_with_threshold(
            y_val_labels, y_proba, confidence_threshold, tp_pct, sl_pct, fee_pct
        )
        sharpes.append(sharpe)

    mean_sharpe = float(np.mean(sharpes))

    if verbose > 0:
        from sklearn.metrics import classification_report

        y_true_all = np.concatenate(all_val_labels)
        y_proba_all = np.concatenate(all_val_probas)
        confidence_all = y_proba_all.max(axis=1)
        mask = confidence_all >= confidence_threshold
        n_trades = int(mask.sum())
        n_total = len(y_true_all)
        print(
            f"    [trial {trial.number}] Sharpe={mean_sharpe:.4f} "
            f"(folds: {', '.join(f'{s:.4f}' for s in sharpes)}) | "
            f"trades={n_trades}/{n_total}"
        )
        if n_trades > 0:
            y_pred_all = classes_to_labels(y_proba_all.argmax(axis=1))
            report = classification_report(
                y_true_all[mask],
                y_pred_all[mask],
                labels=[-1, 1],
                target_names=["short", "long"],
                zero_division=0,
            )
            print(report)

    return mean_sharpe


def optimize_and_train(
    train_features: np.ndarray,
    train_labels: np.ndarray,
    all_columns: list[str],
    feature_col_map: dict[str, dict[int | None, list[str]]],
    n_trials: int,
    cv_splits: int,
    tp_pct: float,
    sl_pct: float,
    fee_pct: float,
    seed: int,
    verbose: int = 0,
    sample_weights: np.ndarray | None = None,
    open_times: np.ndarray | None = None,
    train_end_ms: int | None = None,
) -> tuple[lgb.LGBMClassifier, list[str], float]:
    """Run Optuna optimization and return (best_model, selected_columns, confidence_threshold).

    The best model is retrained on the full training data with the best params.
    When *open_times* is provided, Optuna also optimizes ``training_days`` (5–15)
    to trim the training window per fold and for the final retrain.
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
            all_columns,
            feature_col_map,
            cv_splits,
            tp_pct,
            sl_pct,
            fee_pct,
            seed,
            verbose,
            open_times=open_times,
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

    # Reconstruct feature selection from best params
    use_groups = {g: best[f"use_{g}"] for g in ALL_GROUPS}
    if not any(use_groups.values()):
        use_groups["momentum"] = True
    selected_cols = select_feature_columns(
        feature_col_map, use_groups, best["min_period"], best["max_period"]
    )

    if verbose > 0:
        print(f"  Selected {len(selected_cols)}/{len(all_columns)} features")
        preview = selected_cols[:8]
        suffix = f", ... (+{len(selected_cols) - 8} more)" if len(selected_cols) > 8 else ""
        print(f"  Features: {', '.join(preview)}{suffix}")

    import pandas as pd

    col_indices = [all_columns.index(c) for c in selected_cols]

    # Trim to best training_days for final retrain
    final_mask = np.ones(len(train_labels), dtype=bool)
    if open_times is not None and "training_days" in best:
        best_training_days = best["training_days"]
        anchor_ms = train_end_ms if train_end_ms is not None else int(open_times[-1])
        cutoff_ms = anchor_ms - best_training_days * 86_400_000
        final_mask = open_times >= cutoff_ms

    feat_full = pd.DataFrame(train_features[final_mask][:, col_indices], columns=selected_cols)
    y = labels_to_classes(train_labels[final_mask])
    final_weights = sample_weights[final_mask]

    # Retrain on full training data
    params = {
        "objective": "binary",
        "n_estimators": best["n_estimators"],
        "max_depth": best["max_depth"],
        "num_leaves": best["num_leaves"],
        "learning_rate": best["learning_rate"],
        "subsample": best["subsample"],
        "colsample_bytree": best["colsample_bytree"],
        "min_child_samples": best["min_child_samples"],
        "reg_alpha": best["reg_alpha"],
        "reg_lambda": best["reg_lambda"],
        "is_unbalance": True,
        "random_state": seed,
        "verbosity": -1,
    }

    model = lgb.LGBMClassifier(**params)
    model.fit(feat_full, y, sample_weight=final_weights)

    if verbose > 0:
        print(
            f"  Retrained on full data ({feat_full.shape[0]} samples, "
            f"{len(selected_cols)} features)"
        )

    return model, selected_cols, best_threshold
