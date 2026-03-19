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
_VOLUME_INDICATORS = frozenset({
    "obv", "cmf", "mfi", "ad", "vwap", "taker_buy_ratio",
    "taker_buy_ratio_sma", "volume_pctchg", "volume_rel",
})

_GROUP_PREFIX_MAP = {
    "mom": "momentum",
    "trend": "trend",
    "mr": "mean_reversion",
    "stat": "statistical",
}

# Columns with no period (always included if group selected)
_NO_PERIOD_COLUMNS = frozenset({
    "vol_obv", "vol_ad", "vol_vwap", "vol_taker_buy_ratio",
    "trend_psar_af", "trend_psar_dir", "mr_dist_vwap",
})

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

    Correct direction → +tp_pct - fee_pct
    Wrong direction  → -sl_pct - fee_pct
    Skip (pred=0)    → no trade
    """
    trade_mask = y_pred != 0
    if trade_mask.sum() < 2:
        return -10.0

    y_t = y_true[trade_mask]
    y_p = y_pred[trade_mask]

    correct = y_t == y_p
    # Also count as correct if true label is 0 (skip) — it's a wrong prediction
    # Actually: if we predicted a direction but the label is skip, it's random
    # Treat label=0 as wrong for both directions
    pnls = np.where(correct, tp_pct - fee_pct, -sl_pct - fee_pct)

    mean = pnls.mean()
    std = pnls.std()
    if std == 0:
        return -10.0

    return float(mean / std)


# ---------------------------------------------------------------------------
# Label encoding: {-1, 0, 1} <-> {0, 1, 2} for LightGBM
# ---------------------------------------------------------------------------

_LABEL_TO_CLASS = {-1: 0, 0: 1, 1: 2}
_CLASS_TO_LABEL = {0: -1, 1: 0, 2: 1}


def labels_to_classes(labels: np.ndarray) -> np.ndarray:
    """Convert {-1, 0, 1} labels to {0, 1, 2} classes for LightGBM."""
    return np.vectorize(_LABEL_TO_CLASS.get)(labels).astype(np.intp)


def classes_to_labels(classes: np.ndarray) -> np.ndarray:
    """Convert {0, 1, 2} classes back to {-1, 0, 1} labels."""
    return np.vectorize(_CLASS_TO_LABEL.get)(classes).astype(np.intp)


# ---------------------------------------------------------------------------
# Optuna optimization
# ---------------------------------------------------------------------------

ALL_GROUPS = ["momentum", "volatility", "trend", "volume", "mean_reversion", "statistical"]


def _objective(
    trial: optuna.Trial,
    train_features: np.ndarray,
    train_labels: np.ndarray,
    all_columns: list[str],
    feature_col_map: dict[str, dict[int | None, list[str]]],
    cv_splits: int,
    tp_pct: float,
    sl_pct: float,
    fee_pct: float,
    seed: int,
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

    selected_cols = select_feature_columns(feature_col_map, use_groups, min_period, max_period)
    if not selected_cols:
        return -10.0

    # Map column names to indices
    col_indices = [all_columns.index(c) for c in selected_cols]
    feat = train_features[:, col_indices]

    # LightGBM hyperparameters
    params = {
        "objective": "multiclass",
        "num_class": 3,
        "n_estimators": trial.suggest_int("n_estimators", 50, 500),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "num_leaves": trial.suggest_int("num_leaves", 15, 127),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.3, 1.0),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "is_unbalance": trial.suggest_categorical("is_unbalance", [True, False]),
        "random_state": seed,
        "verbosity": -1,
    }

    y = labels_to_classes(train_labels)
    tscv = TimeSeriesSplit(n_splits=cv_splits)

    sharpes: list[float] = []
    for train_idx, val_idx in tscv.split(feat):
        feat_tr, feat_val = feat[train_idx], feat[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        model = lgb.LGBMClassifier(**params)
        model.fit(feat_tr, y_train)

        y_pred_classes = model.predict(feat_val)
        y_pred_labels = classes_to_labels(np.asarray(y_pred_classes))
        y_val_labels = classes_to_labels(y_val)

        sharpe = compute_sharpe(y_val_labels, y_pred_labels, tp_pct, sl_pct, fee_pct)
        sharpes.append(sharpe)

    return float(np.mean(sharpes))


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
) -> tuple[lgb.LGBMClassifier, list[str]]:
    """Run Optuna optimization and return (best_model, selected_columns).

    The best model is retrained on the full training data with the best params.
    """
    import optuna

    if verbose <= 0:
        optuna.logging.set_verbosity(optuna.logging.WARNING)

    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)

    study.optimize(
        lambda trial: _objective(
            trial,
            train_features,
            train_labels,
            all_columns,
            feature_col_map,
            cv_splits,
            tp_pct,
            sl_pct,
            fee_pct,
            seed,
        ),
        n_trials=n_trials,
    )

    best = study.best_params

    if verbose > 0:
        best_trial = study.best_trial
        print(f"  Optuna: {n_trials} trials, best Sharpe = {best_trial.value:.4f}")
        print(f"  Best params: n_estimators={best['n_estimators']}, "
              f"max_depth={best['max_depth']}, "
              f"lr={best['learning_rate']:.4f}, leaves={best['num_leaves']}")

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

    col_indices = [all_columns.index(c) for c in selected_cols]
    feat_full = train_features[:, col_indices]
    y = labels_to_classes(train_labels)

    # Retrain on full training data
    params = {
        "objective": "multiclass",
        "num_class": 3,
        "n_estimators": best["n_estimators"],
        "max_depth": best["max_depth"],
        "num_leaves": best["num_leaves"],
        "learning_rate": best["learning_rate"],
        "subsample": best["subsample"],
        "colsample_bytree": best["colsample_bytree"],
        "min_child_samples": best["min_child_samples"],
        "reg_alpha": best["reg_alpha"],
        "reg_lambda": best["reg_lambda"],
        "is_unbalance": best["is_unbalance"],
        "random_state": seed,
        "verbosity": -1,
    }

    model = lgb.LGBMClassifier(**params)
    model.fit(feat_full, y)

    if verbose > 0:
        print(f"  Retrained on full data ({feat_full.shape[0]} samples, "
              f"{len(selected_cols)} features)")

    return model, selected_cols
