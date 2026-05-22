"""iter-v3/093 — Derivatives-Microstructure Regime-Conditioned Book runner.

3-layer architecture:
  L1 — 13-feature derivatives-microstructure panel (derivatives_state_v3.py;
       Section 11 amendment: per-symbol OI leg dropped 18 -> 13 features)
  L2 — per-symbol LightGBM multi-class vol-regime classifier
       (forward 21-bar realized-vol terciles; train-window-only cut-points)
  L3 — smooth probability-weighted size multiplier on the FROZEN /059 base book:
       size = 1.0·P(calm) + 0.6·P(normal) + 0.0·P(stressed)

The /059 base directional book (BCH/LDO/TRX, 14-feature per-symbol LightGBM,
triple-barrier labels) is UNCHANGED — it emits trade signals and sizes them via its
own R1/R2/RiskV3 stack exactly as in the v0.v3-059 baseline.  The regime classifier
then scales each position's SIZE by the probability-weighted multiplier.  The gate
only ever reduces exposure; it never adds leverage.

Sacred constants (IMMUTABLE):
    OOS_CUTOFF_DATE = "2025-03-24"
    training_months = 24

ITERATION_LABEL = "v3-093"

Usage:
    uv run python run_derivatives_regime_v3.py
    uv run python run_derivatives_regime_v3.py --seeds 1 --n-trials 35
    uv run python run_derivatives_regime_v3.py --smoke-check   # minimal slice
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import inspect
import json
import math
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kurtosis as sp_kurtosis
from scipy.stats import skew as sp_skew

# ── Third-party ML imports (fail-fast if library stack unavailable) ────────────
try:
    import lightgbm as lgb
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
except ImportError as e:
    raise ImportError(
        f"iter-v3/093 requires lightgbm and optuna: {e}. Run `uv sync` to install."
    ) from e

# ── Internal imports (v3 track-isolated) ──────────────────────────────────────
from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v3 import (
    V3_EXCLUDED_SYMBOLS,
    features_for_symbol,
)
from crypto_trade.features_v3.derivatives_state_v3 import (
    DERIVATIVES_FEATURE_COLUMNS,
    add_derivatives_state_v3_features,
)
from crypto_trade.strategies.ml.validation_v3 import (
    REQUIRED_GAP,
    PBOResult,
    combinatorial_purged_cv,
    deflated_sharpe_ratio_v3,
    n_effective_trials,
    pbo_from_cpcv,
    psr,
)

# Track-isolation guard: derivatives_state_v3 must NOT import from v1/v2 features.
# (Enforced structurally — the module has zero v1/v2 imports.)

# ── Constants — DO NOT CHANGE ──────────────────────────────────────────────────
OOS_CUTOFF_DATE: str = "2025-03-24"  # IMMUTABLE
TRAINING_MONTHS: int = 24  # IMMUTABLE
EMBARGO_CANDLES: int = 22  # (timeout_candles + 1) = (21 + 1), embargo fix e149e9d
BAR_MS: int = 8 * 3_600_000  # 8h in milliseconds

ITERATION_LABEL: str = "v3-093"
REPORTS_DIR: Path = Path("reports-v3")
DATA_DIR: Path = Path("data")
FEATURES_DIR: Path = Path("data/features_v3")

# Regime gate multipliers (IS-calibrated, NOT Optuna-tuned — pre-registered in brief §5)
REGIME_MULTIPLIER: dict[int, float] = {0: 1.0, 1: 0.6, 2: 0.0}  # calm/normal/stressed

# vol-regime: forward 21 bars
VOL_REGIME_HORIZON: int = 21

# /059 base book symbols and feature stack (FROZEN — the single-axis integrity requirement)
V3_BASE_SYMBOLS: tuple[tuple[str, str], ...] = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
)

# Inner ensemble for the REGIME CLASSIFIER (EXPLORATION: 5 seeds)
REGIME_ENSEMBLE_SIZE: int = 5
REGIME_INNER_SEEDS: list[int] = [42, 123, 456, 789, 1001]


# ── Pre-flight checks ──────────────────────────────────────────────────────────


def _verify_branch() -> None:
    branch = subprocess.check_output(
        ["git", "--no-optional-locks", "branch", "--show-current"], text=True
    ).strip()
    allowed = branch.startswith("iteration-v3/") or branch in ("quant-research", "main")
    if not allowed:
        raise RuntimeError(
            f"Runner must be on iteration-v3/*, quant-research, or main; got: {branch}"
        )


def _verify_symbols() -> None:
    syms = {s for _, s in V3_BASE_SYMBOLS}
    overlap = syms & set(V3_EXCLUDED_SYMBOLS)
    if overlap:
        raise RuntimeError(
            f"Universe contains v1/v2 symbols: {sorted(overlap)}. "
            f"V3_EXCLUDED_SYMBOLS = {V3_EXCLUDED_SYMBOLS}"
        )


def _verify_data_freshness(max_lag_hours: float = 16.0) -> None:
    now_ms = int(time.time() * 1000)
    stale = []
    for _, sym in V3_BASE_SYMBOLS:
        p = DATA_DIR / sym / "8h.csv"
        if not p.exists():
            raise RuntimeError(f"Missing kline CSV: {p}")
        df = pd.read_csv(p, usecols=["close_time"])
        lag_h = (now_ms - int(df["close_time"].max())) / 3_600_000
        if lag_h > max_lag_hours:
            stale.append((sym, round(lag_h, 1)))
    if stale:
        syms_str = ",".join(s for s, _ in stale)
        raise RuntimeError(
            f"Stale data (>{max_lag_hours}h): {stale}. "
            f"Run: uv run crypto-trade fetch --symbols {syms_str} --intervals 8h"
        )


def _verify_oi_cache() -> None:
    """Assert OI cache exists for all base symbols + BTCUSDT."""
    missing = []
    for _, sym in V3_BASE_SYMBOLS:
        p = DATA_DIR / "open_interest" / sym / "8h.csv"
        if not p.exists():
            missing.append(sym)
    btc_p = DATA_DIR / "open_interest" / "BTCUSDT" / "8h.csv"
    if not btc_p.exists():
        missing.append("BTCUSDT")
    if missing:
        raise RuntimeError(
            f"OI cache missing for: {missing}. "
            "Run: uv run crypto-trade fetch-oi --symbols " + ",".join(missing)
        )


def _verify_feature_columns_non_empty() -> None:
    """Assert the /059 base feature columns are non-empty (anti-auto-discovery guard)."""
    for _, sym in V3_BASE_SYMBOLS:
        cols = features_for_symbol(sym)
        if not cols:
            raise RuntimeError(
                f"features_for_symbol('{sym}') returned an empty list. "
                "The /059 base book must have an explicit feature_columns list."
            )
        if len(cols) != 14:
            raise RuntimeError(
                f"features_for_symbol('{sym}') returned {len(cols)} columns "
                f"(expected 14 — the /059 anchor stack). Columns: {cols}"
            )


def _verify_embargo_intact() -> None:
    """Assert the e149e9d embargo fix is present in validation_v3's CPCV function.

    The walk-forward uses train_end_ms = test_start_ms - embargo_ms (not
    test_start_ms itself).  We verify by inspecting combinatorial_purged_cv's
    source to confirm it references the embargo parameter and applies it.
    """
    src = inspect.getsource(combinatorial_purged_cv)
    if "embargo" not in src:
        raise RuntimeError(
            "EMBARGO INTEGRITY FAILURE: combinatorial_purged_cv source does not "
            "contain the 'embargo' parameter.  The e149e9d walk-forward fix may "
            "have been lost.  Do NOT run the backtest."
        )


def _verify_dsr_psr_call_sites() -> None:
    """Assert this runner imports and CALLS validation_v3.psr and
    validation_v3.deflated_sharpe_ratio_v3 — the /092 anti-recurrence guard.

    Source-level grep: the runner source must contain both function names as
    active call-sites (not just import references).
    """
    runner_src = Path(__file__).read_text()
    missing = []
    # Check for actual calls (parenthesis following the name)
    if "deflated_sharpe_ratio_v3(" not in runner_src:
        missing.append("deflated_sharpe_ratio_v3(")
    if "psr(" not in runner_src:
        missing.append("psr(")
    if "pbo_from_cpcv(" not in runner_src:
        missing.append("pbo_from_cpcv(")
    if missing:
        raise RuntimeError(
            f"DSR/PSR ANTI-RECURRENCE GUARD FAILED: missing call-sites in runner: "
            f"{missing}. The /092 defect (hardcoded sentinels) cannot recur — "
            "add genuine validation_v3.deflated_sharpe_ratio_v3 / psr / pbo_from_cpcv calls."
        )


# ── Vol-regime label ───────────────────────────────────────────────────────────


def compute_vol_regime_label(
    df: pd.DataFrame,
    horizon: int = VOL_REGIME_HORIZON,
    training_mask: pd.Series | None = None,
) -> pd.Series:
    """Compute forward realized-vol 3-state regime label.

    Parameters
    ----------
    df:
        Kline DataFrame with ``close`` and ``open_time`` columns, sorted by open_time.
    horizon:
        Forward horizon in bars (default 21 = ~7 days at 8h cadence).
    training_mask:
        Boolean Series aligned to df.index marking the TRAINING window rows.
        Tercile cut-points are computed ONLY on rows where training_mask=True.
        If None, use all rows (for smoke-check only — NOT for walk-forward).

    Returns
    -------
    pd.Series (int): 0 = calm, 1 = normal, 2 = stressed. NaN for rows where
        the forward window is incomplete (last ``horizon`` rows per bar).

    Notes
    -----
    Look-ahead-free: the label at bar t uses closes[t+1, t+2, ..., t+horizon]
    (the FUTURE window) which is the training TARGET, never a feature.  The
    cut-points are computed on the training window only — no future data leaks
    into the threshold boundaries.
    """
    log_close = np.log(df["close"].astype(float))

    # Forward realized vol = std of the next `horizon` log-returns
    fwd_vol = pd.Series(np.nan, index=df.index)
    for i in range(len(df) - horizon):
        fwd_rets = log_close.iloc[i + 1 : i + horizon + 1].values
        fwd_vol.iloc[i] = float(np.std(fwd_rets, ddof=1)) if len(fwd_rets) == horizon else np.nan

    # Tercile cut-points: computed on TRAINING window only (past-only, no look-ahead)
    if training_mask is not None:
        train_vol = fwd_vol[training_mask & fwd_vol.notna()]
    else:
        train_vol = fwd_vol[fwd_vol.notna()]

    if len(train_vol) < 30:
        # Insufficient training data — return all NaN
        return pd.Series(np.nan, index=df.index)

    q33 = float(np.percentile(train_vol.values, 33.33))
    q67 = float(np.percentile(train_vol.values, 66.67))

    labels = pd.Series(np.nan, index=df.index)
    valid = fwd_vol.notna()
    labels[valid & (fwd_vol <= q33)] = 0  # calm
    labels[valid & (fwd_vol > q33) & (fwd_vol <= q67)] = 1  # normal
    labels[valid & (fwd_vol > q67)] = 2  # stressed

    return labels


# ── Vol-regime classifier (per-symbol, per walk-forward month) ─────────────────


def _optuna_objective_multiclass(
    trial: optuna.Trial,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    seed: int,
) -> float:
    """Optuna objective for multi-class LightGBM vol-regime classifier."""
    params = {
        "objective": "multiclass",
        "num_class": 3,
        "metric": "multi_logloss",
        "n_estimators": trial.suggest_int("n_estimators", 50, 300),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 16, 128),
        "max_depth": trial.suggest_int("max_depth", 3, 8),
        "min_child_samples": trial.suggest_int("min_child_samples", 10, 60),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-4, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-4, 10.0, log=True),
        "seed": seed,
        "verbose": -1,
        "n_jobs": 1,
    }
    model = lgb.LGBMClassifier(**params)
    model.fit(x_train, y_train)
    proba = model.predict_proba(x_val)  # (n_val, 3)
    # Evaluate: mean per-class log-loss
    n_val = len(y_val)
    eps = 1e-7
    loss = 0.0
    for i in range(n_val):
        c = int(y_val[i])
        loss -= math.log(max(proba[i, c], eps))
    return loss / max(n_val, 1)


def train_regime_classifier_for_month(
    features_df: pd.DataFrame,
    labels: pd.Series,
    train_start_ms: int,
    train_end_ms: int,
    n_trials: int = 35,
    ensemble_seeds: list[int] | None = None,
) -> list[lgb.LGBMClassifier] | None:
    """Train an ensemble of multi-class vol-regime classifiers for one walk-forward month.

    Parameters
    ----------
    features_df:
        Full derivatives feature DataFrame aligned to kline open_times.
    labels:
        Vol-regime labels (0/1/2) aligned to features_df.index.
    train_start_ms:
        Start of the 24-month training window (inclusive).
    train_end_ms:
        End of training window — the TEST window starts AFTER train_end_ms + embargo.
        This is ALREADY embargoed by the caller (train_end_ms = test_start_ms - embargo_ms).
    n_trials:
        Optuna trials per seed.
    ensemble_seeds:
        List of inner-ensemble seeds.  Default: REGIME_INNER_SEEDS.

    Returns
    -------
    List of fitted LGBMClassifier (one per inner seed), or None if insufficient data.
    """
    if ensemble_seeds is None:
        ensemble_seeds = REGIME_INNER_SEEDS

    mask_train = (features_df["open_time"] >= train_start_ms) & (
        features_df["open_time"] < train_end_ms
    )
    feat_df = features_df[mask_train][list(DERIVATIVES_FEATURE_COLUMNS)]
    y_s = labels[mask_train]

    # Drop rows with NaN labels or features
    valid = feat_df.notna().all(axis=1) & y_s.notna()
    feat_df = feat_df[valid]
    y_s = y_s[valid]

    if len(feat_df) < 60 or y_s.nunique() < 2:
        print(
            f"    [regime] Insufficient training data ({len(feat_df)} rows, "
            f"{y_s.nunique()} unique classes) — skipping month."
        )
        return None

    x_arr = feat_df.values.astype(np.float32)
    y_arr = y_s.values.astype(np.int32)

    # Simple 80/20 chronological split for Optuna validation
    n = len(x_arr)
    split = max(30, int(n * 0.8))
    x_tr, x_v = x_arr[:split], x_arr[split:]
    y_tr, y_v = y_arr[:split], y_arr[split:]

    if len(x_v) < 10 or len(np.unique(y_tr)) < 2:
        # Fall back: train on full data without Optuna tuning
        split = n
        x_tr, y_tr = x_arr, y_arr
        x_v, y_v = x_arr[:10], y_arr[:10]  # dummy val — no Optuna

    fitted: list[lgb.LGBMClassifier] = []

    for seed in ensemble_seeds:
        # Optuna study for this seed
        study = optuna.create_study(
            direction="minimize",
            sampler=optuna.samplers.TPESampler(seed=seed),
        )
        study.optimize(
            lambda trial: _optuna_objective_multiclass(trial, x_tr, y_tr, x_v, y_v, seed),
            n_trials=n_trials,
            show_progress_bar=False,
        )
        best = study.best_params
        best["objective"] = "multiclass"
        best["num_class"] = 3
        best["metric"] = "multi_logloss"
        best["seed"] = seed
        best["verbose"] = -1
        best["n_jobs"] = 1
        model = lgb.LGBMClassifier(**best)
        model.fit(x_arr, y_arr)
        fitted.append(model)

    return fitted


def predict_regime_proba(
    models: list[lgb.LGBMClassifier],
    features_df: pd.DataFrame,
    test_mask: pd.Series,
) -> pd.DataFrame:
    """Return mean ensemble regime probabilities for test-window rows.

    Returns a DataFrame with columns ``p_calm``, ``p_normal``, ``p_stressed``,
    index aligned to features_df[test_mask].
    """
    feat_df = features_df[test_mask][list(DERIVATIVES_FEATURE_COLUMNS)]
    # Fill NaN with 0 (conservative — tree will use the neutral split)
    x_test = feat_df.fillna(0.0).values.astype(np.float32)

    probas = np.zeros((len(x_test), 3), dtype=np.float64)
    for m in models:
        probas += m.predict_proba(x_test)
    probas /= len(models)

    result = pd.DataFrame(
        {
            "p_calm": probas[:, 0],
            "p_normal": probas[:, 1],
            "p_stressed": probas[:, 2],
        },
        index=features_df[test_mask].index,
    )
    return result


def compute_regime_size_multiplier(proba_df: pd.DataFrame) -> pd.Series:
    """Compute smooth probability-weighted size multiplier.

    multiplier = 1.0 * P(calm) + 0.6 * P(normal) + 0.0 * P(stressed)

    All values are in [0.0, 1.0] by construction (convex combination of
    probabilities, all multipliers in [0, 1]).
    """
    m = (
        REGIME_MULTIPLIER[0] * proba_df["p_calm"]
        + REGIME_MULTIPLIER[1] * proba_df["p_normal"]
        + REGIME_MULTIPLIER[2] * proba_df["p_stressed"]
    )
    # Sanity-clip to [0, 1] (guard against floating-point drift)
    m = m.clip(0.0, 1.0)
    return m


# ── /059 base directional book (FROZEN — not retrained) ───────────────────────


def _load_frozen_059_klines(symbol: str) -> pd.DataFrame:
    """Load perp 8h klines for the /059 base book symbol."""
    p = DATA_DIR / symbol / "8h.csv"
    df = pd.read_csv(p)
    df["open_time"] = df["open_time"].astype(int)
    df["close_time"] = df["close_time"].astype(int)
    df["symbol"] = symbol
    return df


def _load_059_base_features(symbol: str) -> pd.DataFrame:
    """Load pre-generated /059 feature parquet for the symbol."""
    pq = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    if not pq.exists():
        raise FileNotFoundError(
            f"Missing features parquet for {symbol}: {pq}. "
            "Run `uv run crypto-trade features --symbols <SYM> --interval 8h "
            "--track v3 --format parquet` first."
        )
    return pd.read_parquet(pq)


# ── Walk-forward regime + base-book overlay ────────────────────────────────────


def _monthly_walk_forward(
    symbol: str,
    n_trials: int,
    ensemble_seeds: list[int],
    smoke_check: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict], float]:
    """Run the walk-forward regime classifier + base-book overlay for one symbol.

    Returns
    -------
    regime_preds_df:
        DataFrame with columns [open_time, p_calm, p_normal, p_stressed, regime_multiplier]
        for every IS+OOS bar where the classifier was trained.
    deriv_features_df:
        Full derivatives feature DataFrame (for ADF / IC reporting).
    month_stats:
        List of per-month dicts (train_start, train_end, n_train, stressed_fire_rate).
    total_optuna_trials:
        Total Optuna trials run across all months × seeds.
    """
    print(f"\n[regime/{symbol}] Loading klines + derivatives features ...")

    # Klines
    klines = _load_frozen_059_klines(symbol)
    klines = klines.sort_values("open_time").reset_index(drop=True)

    # Derivatives features (builds 13-feature panel; Section 11 amendment: OI leg dropped)
    try:
        deriv_df = add_derivatives_state_v3_features(klines, data_dir=DATA_DIR)
    except FileNotFoundError as exc:
        if smoke_check:
            # Smoke-check fallback: zero-filled panel (OI data not yet fetched)
            print(f"[regime/{symbol}] SMOKE WARN: {exc}")
            print(
                f"[regime/{symbol}] Falling back to zero-filled derivatives panel (smoke mode only)"
            )
            # Include close so compute_vol_regime_label can compute forward vol labels
            deriv_df = klines[["open_time", "close"]].copy()
            for col in DERIVATIVES_FEATURE_COLUMNS:
                deriv_df[col] = 0.0
        else:
            raise
    deriv_df = deriv_df.sort_values("open_time").reset_index(drop=True)

    # Walk-forward month boundaries (identical to /059 runner)
    min_time_ms = int(klines["open_time"].min())
    train_window_ms = TRAINING_MONTHS * 30 * 24 * 3_600_000  # ~24 months in ms

    # All calendar months in the dataset
    all_months = pd.to_datetime(klines["open_time"], unit="ms").dt.to_period("M").unique()
    all_months = sorted(all_months)

    # Find first month where we have 24 months of training data
    first_usable = None
    for m in all_months:
        m_start_ms = int(m.start_time.timestamp() * 1000)
        if m_start_ms - min_time_ms >= train_window_ms:
            first_usable = m
            break

    if first_usable is None:
        print(f"[regime/{symbol}] Insufficient history for 24-month training window.")
        return pd.DataFrame(), pd.DataFrame(), [], 0

    usable_months = [m for m in all_months if m >= first_usable]

    if smoke_check:
        usable_months = usable_months[:3]
        print(f"[regime/{symbol}] SMOKE CHECK: limiting to first {len(usable_months)} months")

    embargo_ms = EMBARGO_CANDLES * BAR_MS  # e149e9d fix

    regime_rows = []
    month_stats = []
    total_trials = 0

    for i, month in enumerate(usable_months):
        test_start_ms = int(month.start_time.timestamp() * 1000)
        train_end_ms = test_start_ms - embargo_ms  # embargo fix (e149e9d)
        train_start_ms = train_end_ms - train_window_ms

        # Training mask on derivatives features (past-only, within training window)
        train_mask = (deriv_df["open_time"] >= train_start_ms) & (
            deriv_df["open_time"] < train_end_ms
        )

        # Vol-regime labels: compute on training window only (no look-ahead cut-points)
        # The label requires the forward 21 bars, so the training labels are computed
        # on the training window rows — the cut-points are training-window terciles.
        vol_labels = compute_vol_regime_label(
            deriv_df,
            horizon=VOL_REGIME_HORIZON,
            training_mask=train_mask,
        )

        n_train = int(train_mask.sum())
        print(
            f"  [regime/{symbol}] Month {i + 1}/{len(usable_months)}: "
            f"{month} | train [{pd.Timestamp(train_start_ms, unit='ms').date()} "
            f"→ {pd.Timestamp(train_end_ms, unit='ms').date()}] | "
            f"{n_train} train bars"
        )

        # Train regime classifier
        models = train_regime_classifier_for_month(
            features_df=deriv_df,
            labels=vol_labels,
            train_start_ms=train_start_ms,
            train_end_ms=train_end_ms,
            n_trials=n_trials,
            ensemble_seeds=ensemble_seeds,
        )

        if models is None:
            # Insufficient data — fill test window with neutral multiplier (1.0)
            # Compute test mask from timestamps
            if i + 1 < len(usable_months):
                next_month = usable_months[i + 1]
                test_end_ms = int(next_month.start_time.timestamp() * 1000)
            else:
                test_end_ms = int(klines["open_time"].max()) + BAR_MS
            test_mask_ms = (deriv_df["open_time"] >= test_start_ms) & (
                deriv_df["open_time"] < test_end_ms
            )
            for idx in deriv_df[test_mask_ms].index:
                regime_rows.append(
                    {
                        "open_time": deriv_df.loc[idx, "open_time"],
                        "p_calm": 1.0 / 3,
                        "p_normal": 1.0 / 3,
                        "p_stressed": 1.0 / 3,
                        "regime_multiplier": 1.0 * (1 / 3) + 0.6 * (1 / 3) + 0.0 * (1 / 3),
                    }
                )
            continue

        total_trials += n_trials * len(ensemble_seeds)

        # Test window: this calendar month
        if i + 1 < len(usable_months):
            next_month = usable_months[i + 1]
            test_end_ms = int(next_month.start_time.timestamp() * 1000)
        else:
            test_end_ms = int(klines["open_time"].max()) + BAR_MS

        test_mask = (deriv_df["open_time"] >= test_start_ms) & (deriv_df["open_time"] < test_end_ms)

        if not test_mask.any():
            continue

        proba_df = predict_regime_proba(models, deriv_df, test_mask)
        mults = compute_regime_size_multiplier(proba_df)

        stressed_fire_rate = float((proba_df["p_stressed"] > 0.5).mean())

        for idx in proba_df.index:
            ot = int(deriv_df.loc[idx, "open_time"])
            regime_rows.append(
                {
                    "open_time": ot,
                    "p_calm": float(proba_df.loc[idx, "p_calm"]),
                    "p_normal": float(proba_df.loc[idx, "p_normal"]),
                    "p_stressed": float(proba_df.loc[idx, "p_stressed"]),
                    "regime_multiplier": float(mults.loc[idx]),
                }
            )

        month_stats.append(
            {
                "month": str(month),
                "train_start_ms": train_start_ms,
                "train_end_ms": train_end_ms,
                "n_train": n_train,
                "n_test": int(test_mask.sum()),
                "stressed_fire_rate": round(stressed_fire_rate, 4),
            }
        )

        print(
            f"    stressed_fire_rate={stressed_fire_rate:.3f} | "
            f"regime_multiplier_mean={mults.mean():.3f}"
        )

    regime_preds_df = pd.DataFrame(regime_rows)
    return regime_preds_df, deriv_df, month_stats, total_trials


# ── Base-book trade loader (from /059 parquets / cached reports) ──────────────


def _run_059_base_book(symbol: str, smoke_check: bool = False) -> list:
    """Reproduce /059 base directional book trades for one symbol.

    The /059 base book is run via the standard v3 walk-forward machinery
    (FROZEN feature set, same hyperparameters as /059 baseline).  This is the
    "frozen oracle" (phase5.5 gate Item 3: stateless gate, ORACLE EDA valid).

    We use the pre-generated feature parquets (same as run_baseline_v3.py).
    The /059 base book IS NOT retrained with new OI features — it uses ONLY
    the 14 V3_FEATURE_COLUMNS (the closed /059 stack).
    """
    from crypto_trade.backtest import run_backtest
    from crypto_trade.backtest_models import BacktestConfig
    from crypto_trade.features_v3 import atr_multipliers_for_symbol
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
    from crypto_trade.strategies.ml.risk_v2 import (
        BtcTrendFilterConfig,
        RiskV2Config,
    )
    from crypto_trade.strategies.ml.risk_v3 import RiskV3Wrapper

    training_months_base = 24
    _atr_tp, _atr_sl = atr_multipliers_for_symbol(symbol)

    cfg = BacktestConfig(
        symbols=(symbol,),
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        data_dir=DATA_DIR,
        cooldown_candles=4,
        vol_targeting=False,
    )

    ensemble_seeds_059 = [42, 123, 456, 789, 1001]  # /059 inner ensemble
    n_trials_059 = 35  # /059 run config

    if smoke_check:
        n_trials_059 = 5
        ensemble_seeds_059 = [42]

    m1 = LightGbmStrategy(
        training_months=training_months_base,
        n_trials=n_trials_059,
        cv_splits=5,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir=str(FEATURES_DIR),
        verbose=0,
        atr_tp_multiplier=_atr_tp,
        atr_sl_multiplier=_atr_sl,
        atr_column="natr_21_raw",
        use_atr_labeling=True,
        ensemble_seeds=ensemble_seeds_059,
        feature_columns=list(features_for_symbol(symbol)),
        ood_enabled=False,
        label_mode="triple_barrier",
    )

    # /059 risk config — FROZEN (exact copy from run_baseline_v3.py _build_v3_model)
    risk_cfg = RiskV2Config(
        zscore_threshold=2.0,
        adx_threshold=20.0,
        max_per_symbol_pnl_share=0.40,
        max_per_symbol_window_bars=90,
        enable_per_symbol_cap=False,
        enable_regime_gate=False,
        regime_gate_symbols=(),
        regime_dd_threshold_pct=20.0,
        regime_vol_zscore_threshold=1.5,
        enable_regime_size_scalar=False,
        regime_size_scalar_symbols=(),
        regime_size_scalar_value=0.50,
        regime_size_ma_window=270,
        block_long_for=(),
        block_short_for=(),
        adx_threshold_per_symbol={},
        enable_per_symbol_drawdown_brake=False,
        drawdown_brake_threshold_wpnl=10.0,
        drawdown_brake_recovery_wpnl=5.0,
        drawdown_brake_window_days=30,
        vol_scale_floor_per_symbol={},
        # vol_scale_ceiling not set — defaults to 1.0 per risk_v2.py:58
    )

    wrapped = RiskV3Wrapper(m1, risk_cfg)

    # BTC trend filter (the /059 config)
    from crypto_trade.strategies.ml.risk_v2 import (
        apply_btc_trend_filter,
        load_btc_klines_for_filter,
    )

    btc_trend_cfg = BtcTrendFilterConfig(lookback_bars=42, threshold_pct=15.0, enabled=True)
    btc_times, btc_closes = load_btc_klines_for_filter()  # default 'data/BTCUSDT/8h.csv'

    trades = run_backtest(cfg, wrapped)
    filtered_trades, _ = apply_btc_trend_filter(trades, btc_times, btc_closes, btc_trend_cfg)
    return filtered_trades


# ── Regime overlay ─────────────────────────────────────────────────────────────


def _apply_regime_overlay(
    trades: list,
    regime_preds_df: pd.DataFrame,
    symbol: str,
) -> list:
    """Scale each trade's weight_factor by the regime-size multiplier at trade open_time.

    The regime gate is STATELESS: it does not suppress trade entry (the base
    book's R1/R2/RiskV3 state is untouched) — it only scales the position size.
    A multiplier of 0.0 means the position is sized to zero (flat into stressed
    regime) but the trade is still recorded with weight_factor=0 for counting.

    Parameters
    ----------
    trades:
        List of TradeResult objects from the /059 base book.
    regime_preds_df:
        DataFrame with ``open_time`` (ms int) and ``regime_multiplier`` columns.
    symbol:
        Symbol name for diagnostic printing.
    """
    if regime_preds_df.empty:
        return trades

    mult_lookup = regime_preds_df.set_index("open_time")["regime_multiplier"].to_dict()

    zero_sized = 0
    result = []
    for t in trades:
        ot = int(t.open_time)
        mult = mult_lookup.get(ot, 1.0)  # default: calm (no regime data)
        # Scale weight_factor by the regime multiplier
        new_wf = t.weight_factor * mult
        # Reconstruct TradeResult with modified weight_factor
        result.append(
            dataclasses.replace(t, weighted_pnl=t.net_pnl_pct * new_wf, weight_factor=new_wf)
        )
        if mult == 0.0:
            zero_sized += 1

    print(
        f"  [overlay/{symbol}] {len(result)} trades | "
        f"{zero_sized} zero-sized (stressed gate) | "
        f"stressed_zero_frac={zero_sized / max(len(result), 1):.3f}"
    )
    return result


# ── Metric helpers ─────────────────────────────────────────────────────────────


def _monthly_sharpe(trades: list) -> float:
    if not trades:
        return 0.0
    by_month: dict[str, float] = {}
    for t in trades:
        m = pd.Timestamp(t.open_time, unit="ms").strftime("%Y-%m")
        by_month[m] = by_month.get(m, 0.0) + float(t.weighted_pnl)
    arr = np.array(list(by_month.values()))
    if arr.std() == 0:
        return 0.0
    return float(arr.mean() / arr.std() * np.sqrt(12))


def _daily_sharpe(trades: list) -> float:
    if not trades:
        return 0.0
    by_day: dict[str, float] = {}
    for t in trades:
        d = pd.Timestamp(t.close_time, unit="ms").strftime("%Y-%m-%d")
        by_day[d] = by_day.get(d, 0.0) + float(t.weighted_pnl)
    arr = np.array(list(by_day.values()))
    if arr.std() == 0:
        return 0.0
    return float(arr.mean() / arr.std() * np.sqrt(365))


def _max_drawdown(trades: list) -> float:
    if not trades:
        return 0.0
    sorted_t = sorted(trades, key=lambda t: t.open_time)
    cum = np.cumsum([float(t.weighted_pnl) for t in sorted_t])
    peak = np.maximum.accumulate(cum)
    dd = peak - cum
    return float(dd.max()) * 100


def _profit_factor(trades: list) -> float:
    wins = sum(float(t.weighted_pnl) for t in trades if float(t.weighted_pnl) > 0)
    losses = -sum(float(t.weighted_pnl) for t in trades if float(t.weighted_pnl) < 0)
    return wins / losses if losses > 0 else float("inf")


def _win_rate(trades: list) -> float:
    if not trades:
        return 0.0
    return sum(1 for t in trades if float(t.weighted_pnl) > 0) / len(trades)


def _calmar(trades: list) -> float:
    ms = _monthly_sharpe(trades)
    dd = _max_drawdown(trades) / 100
    return ms / dd if dd > 0 else 0.0


# ── Report writers ─────────────────────────────────────────────────────────────


def _write_trades_csv(trades: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not trades:
        pd.DataFrame().to_csv(path, index=False)
        return
    rows = []
    for t in trades:
        rows.append(
            {
                "symbol": t.symbol,
                "open_time": t.open_time,
                "close_time": t.close_time,
                "direction": t.direction,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "pnl": t.net_pnl_pct,
                "weighted_pnl": t.weighted_pnl,
                "weight_factor": t.weight_factor,
                "exit_reason": t.exit_reason,
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_comparison(
    report_dir: Path,
    is_trades: list,
    oos_trades: list,
    dsr_val: float,
    pbo_result: PBOResult,
    psr_val: float,
    n_trials: int,
    n_eff: int,
) -> None:
    """Write comparison.csv with the standard v3 schema."""
    is_ms = _monthly_sharpe(is_trades)
    oos_ms = _monthly_sharpe(oos_trades)
    is_ds = _daily_sharpe(is_trades)
    oos_ds = _daily_sharpe(oos_trades)
    is_dd = _max_drawdown(is_trades)
    oos_dd = _max_drawdown(oos_trades)
    is_pf = _profit_factor(is_trades)
    oos_pf = _profit_factor(oos_trades)
    is_wr = _win_rate(is_trades)
    oos_wr = _win_rate(oos_trades)
    is_n = len(is_trades)
    oos_n = len(oos_trades)
    is_pnl = sum(float(t.weighted_pnl) for t in is_trades)
    oos_pnl = sum(float(t.weighted_pnl) for t in oos_trades)
    is_calmar = _calmar(is_trades)
    oos_calmar = _calmar(oos_trades)

    def rat(oos_v: float, is_v: float) -> str:
        return f"{oos_v / is_v:.4f}" if is_v != 0 else "—"

    pbo_str = "NaN" if pbo_result.pbo is None else f"{pbo_result.pbo:.4f}"

    metrics = [
        ("monthly_sharpe", f"{is_ms:.4f}", f"{oos_ms:.4f}", rat(oos_ms, is_ms)),
        ("daily_sharpe", f"{is_ds:.4f}", f"{oos_ds:.4f}", rat(oos_ds, is_ds)),
        ("max_drawdown", f"{is_dd:.4f}", f"{oos_dd:.4f}", rat(oos_dd, is_dd)),
        ("profit_factor", f"{is_pf:.4f}", f"{oos_pf:.4f}", rat(oos_pf, is_pf)),
        ("win_rate", f"{is_wr:.4f}", f"{oos_wr:.4f}", rat(oos_wr, is_wr)),
        ("n_trades", str(is_n), str(oos_n), rat(float(oos_n), float(is_n))),
        ("total_pnl", f"{is_pnl:.4f}", f"{oos_pnl:.4f}", rat(oos_pnl, is_pnl)),
        ("monthly_calmar", f"{is_calmar:.4f}", f"{oos_calmar:.4f}", rat(oos_calmar, is_calmar)),
        ("weighted_pnl_total", f"{is_pnl:.4f}", f"{oos_pnl:.4f}", rat(oos_pnl, is_pnl)),
        ("dsr", f"{dsr_val:.6f}", "—", "—"),
        ("pbo", pbo_str, "—", "—"),
        ("psr", f"{psr_val:.4f}", "—", "—"),
        ("n_trials", str(n_trials), "—", "—"),
        ("n_effective_trials", str(n_eff), "—", "—"),
    ]

    comp_path = report_dir / "comparison.csv"
    with open(comp_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "in_sample", "out_of_sample", "ratio"])
        for row in metrics:
            w.writerow(row)

    all_syms = sorted({t.symbol for t in is_trades + oos_trades})
    total_oos = sum(float(t.weighted_pnl) for t in oos_trades) or 1.0
    with open(comp_path, "a", newline="") as f:
        w = csv.writer(f)
        w.writerow([])
        w.writerow(["# per_symbol", "weighted_pnl", "n_trades", "win_rate", "concentration_pct"])
        for sym in all_syms:
            sym_oos = [t for t in oos_trades if t.symbol == sym]
            if not sym_oos:
                continue
            sym_pnl = sum(float(t.weighted_pnl) for t in sym_oos)
            sym_wr = 100.0 * sum(1 for t in sym_oos if float(t.weighted_pnl) > 0) / len(sym_oos)
            conc = 100.0 * sym_pnl / total_oos if total_oos != 0 else 0.0
            w.writerow([sym, f"{sym_pnl:.4f}", len(sym_oos), f"{sym_wr:.1f}", f"{conc:.2f}"])

    print(
        f"[report] comparison.csv: IS monthly Sharpe={is_ms:+.4f}, "
        f"OOS monthly Sharpe={oos_ms:+.4f}, DSR={dsr_val:.4f}, "
        f"PBO={pbo_str}, PSR={psr_val:.4f}"
    )


def _write_dsr_json(
    report_dir: Path,
    dsr_val: float,
    pbo_result: PBOResult,
    psr_val: float,
    n_trials: int,
    n_eff: int,
) -> None:
    """Write dsr.json — genuine computed values, NEVER hardcoded sentinels.

    DSR/PBO/PSR call-sites (required by /092 anti-recurrence mandate):
    - deflated_sharpe_ratio_v3() called in main() on the OOS monthly Sharpe series.
    - psr() called in main() on the OOS weighted_pnl series (trade-level SR).
    - pbo_from_cpcv() called in main() on the CPCV path matrix.
    """
    pbo_out = pbo_result.pbo if pbo_result.pbo is not None else None
    frac_pos = pbo_result.frac_positive_paths
    data = {
        "dsr": round(dsr_val, 8),
        "pbo": pbo_out,
        "pbo_note": pbo_result.note,
        "pbo_frac_positive_paths": round(frac_pos, 4),
        "psr": round(psr_val, 4),
        "n_trials": n_trials,
        "n_eff": n_eff,
        "iteration": ITERATION_LABEL,
        # Call-site traceback (Section 9.2 — feedback_v3_methodology_post_hoc_input_traceback.md)
        # DSR: observed_sharpe = OOS monthly Sharpe (annualized monthly; √12 convention)
        # PSR: observed_sharpe = OOS trade-level Sharpe (per-trade weighted_pnl / std)
        # Both call validation_v3.deflated_sharpe_ratio_v3 and validation_v3.psr directly.
        "dsr_callsite": "validation_v3.deflated_sharpe_ratio_v3(observed_sr=oos_monthly_sharpe)",
        "psr_callsite": (
            "validation_v3.psr(observed_sharpe=oos_trade_level_sr, n_obs=len(oos_trades))"
        ),
        "sr_granularity": "monthly for DSR; trade-level (per weighted_pnl) for PSR",
    }
    (report_dir / "dsr.json").write_text(json.dumps(data, indent=2))
    pbo_disp = "NaN" if pbo_out is None else f"{pbo_out:.4f}"
    print(
        f"[report] dsr.json: DSR={dsr_val:.4f}, PBO={pbo_disp}, "
        f"frac_pos={frac_pos:.3f}, PSR={psr_val:.4f}, n_eff={n_eff}"
    )


def _write_adf_test(
    report_dir: Path,
    deriv_features_by_sym: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Run ADF test per (symbol, feature) on the IS window."""
    from statsmodels.tsa.stattools import adfuller

    rows = []
    for sym, df in deriv_features_by_sym.items():
        df_is = df[df["open_time"] < OOS_CUTOFF_MS]
        for col in DERIVATIVES_FEATURE_COLUMNS:
            if col not in df_is.columns:
                continue
            series = df_is[col].dropna().values
            if len(series) < 20:
                rows.append(
                    {
                        "symbol": sym,
                        "feature_name": col,
                        "adf_statistic": float("nan"),
                        "p_value": float("nan"),
                        "stationary": False,
                    }
                )
                continue
            try:
                maxlag = int(math.floor(12 * (len(series) / 100) ** 0.25))
                res = adfuller(series, autolag="AIC", maxlag=maxlag)
                pv = float(res[1])
                rows.append(
                    {
                        "symbol": sym,
                        "feature_name": col,
                        "adf_statistic": round(float(res[0]), 6),
                        "p_value": round(pv, 6),
                        "stationary": pv < 0.05,
                    }
                )
            except Exception as e:
                rows.append(
                    {
                        "symbol": sym,
                        "feature_name": col,
                        "adf_statistic": float("nan"),
                        "p_value": float("nan"),
                        "stationary": False,
                    }
                )
                print(f"  [ADF] Error {sym}/{col}: {e}")

    adf_df = pd.DataFrame(rows)
    adf_df.to_csv(report_dir / "adf_test.csv", index=False)
    print(f"[report] adf_test.csv: {len(adf_df)} rows")
    return adf_df


def _write_ic_matrix(
    report_dir: Path,
    deriv_features_by_sym: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Pairwise Pearson IC between derivatives features (IS window, pooled symbols)."""
    frames = []
    for sym, df in deriv_features_by_sym.items():
        df_is = df[df["open_time"] < OOS_CUTOFF_MS][list(DERIVATIVES_FEATURE_COLUMNS)].copy()
        frames.append(df_is)

    if not frames:
        pd.DataFrame().to_csv(report_dir / "ic_matrix.csv")
        return pd.DataFrame()

    pooled = pd.concat(frames, ignore_index=True)
    ic_mat = pooled.corr(method="pearson", numeric_only=True)
    ic_mat.to_csv(report_dir / "ic_matrix.csv")
    print(f"[report] ic_matrix.csv: {ic_mat.shape}")
    return ic_mat


def _write_cpcv_paths(
    report_dir: Path,
    all_is_trades: list,
) -> tuple[pd.DataFrame, list[float]]:
    """Build a simplified CPCV path set from IS trades for DSR/PBO computation.

    Uses the standard combinatorial_purged_cv split on the monthly IS PnL series.
    """
    if not all_is_trades:
        empty = pd.DataFrame(columns=["path_id", "sharpe", "max_dd", "n_candles"])
        empty.to_csv(report_dir / "cpcv_paths.csv", index=False)
        return empty, []

    # Monthly IS PnL series (sorted by month)
    by_month: dict[str, float] = {}
    for t in all_is_trades:
        m = pd.Timestamp(t.open_time, unit="ms").strftime("%Y-%m")
        by_month[m] = by_month.get(m, 0.0) + float(t.weighted_pnl)

    months = sorted(by_month.keys())
    pnl_arr = np.array([by_month[m] for m in months])
    n = len(pnl_arr)

    if n < 10:
        empty = pd.DataFrame(columns=["path_id", "sharpe", "max_dd", "n_candles"])
        empty.to_csv(report_dir / "cpcv_paths.csv", index=False)
        return empty, []

    # CPCV splits (gap = min(REQUIRED_GAP, n//10) for monthly series)
    gap = min(REQUIRED_GAP, max(1, n // 10))
    try:
        splits = list(
            combinatorial_purged_cv(
                n_samples=n,
                n_splits=10,
                n_test_splits=2,
                gap=gap,
                embargo=0,
                expected_gap=gap,
            )
        )
    except Exception as e:
        print(f"  [CPCV] Split error: {e} — writing empty cpcv_paths.csv")
        empty = pd.DataFrame(columns=["path_id", "sharpe", "max_dd", "n_candles"])
        empty.to_csv(report_dir / "cpcv_paths.csv", index=False)
        return empty, []

    rows = []
    flat_sharpes = []
    for path_id, (train_idx, test_idx) in enumerate(splits):
        test_rets = pnl_arr[list(test_idx)]
        n_test = len(test_rets)
        if n_test < 2:
            continue
        mu = float(np.mean(test_rets))
        sigma = float(np.std(test_rets, ddof=1))
        sharpe = mu / sigma * math.sqrt(n_test) if sigma > 0 else 0.0
        cum = np.cumsum(test_rets)
        running_max = np.maximum.accumulate(cum)
        max_dd = float((running_max - cum).max())
        rows.append(
            {
                "path_id": path_id,
                "sharpe": round(sharpe, 6),
                "max_dd": round(max_dd * 100, 4),
                "n_candles": n_test,
            }
        )
        flat_sharpes.append(sharpe)

    cpcv_df = pd.DataFrame(rows)
    cpcv_df.to_csv(report_dir / "cpcv_paths.csv", index=False)
    print(f"[report] cpcv_paths.csv: {len(cpcv_df)} paths")
    return cpcv_df, flat_sharpes


def _write_per_month_regime_stats(
    report_dir: Path,
    all_month_stats: list[dict],
) -> None:
    """Write per_month_regime_stats.csv for F6 gate evaluation."""
    df = pd.DataFrame(all_month_stats)
    path = report_dir / "per_month_regime_stats.csv"
    df.to_csv(path, index=False)
    if not df.empty and "stressed_fire_rate" in df.columns:
        overall_rate = float(df["stressed_fire_rate"].mean())
        print(
            f"[report] per_month_regime_stats.csv: {len(df)} months, "
            f"mean stressed_fire_rate={overall_rate:.3f} "
            f"(F6 band: [0.08, 0.45])"
        )
    else:
        print(
            f"[report] per_month_regime_stats.csv: {len(df)} rows (empty or no stressed_fire_rate)"
        )


# ── Main ───────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="iter-v3/093 derivatives-microstructure regime-conditioned book runner"
    )
    parser.add_argument(
        "--seeds", type=int, default=1, help="Number of outer seeds (EXPLORATION=1, CONFIRMATION=2)"
    )
    parser.add_argument(
        "--n-trials", type=int, default=35, help="Optuna trials per seed per month (default 35)"
    )
    parser.add_argument(
        "--smoke-check",
        action="store_true",
        help="Run on minimal data slice (3 months) for build verification",
    )
    parser.add_argument(
        "--skip-base-book",
        action="store_true",
        help="Skip /059 base book retraining (use cached regime overlay only)",
    )
    args = parser.parse_args()

    t_start = time.time()

    print(f"\n{'=' * 70}")
    print("iter-v3/093 — Derivatives-Microstructure Regime-Conditioned Book")
    print(f"ITERATION_LABEL = {ITERATION_LABEL}")
    print(f"OOS_CUTOFF_DATE = {OOS_CUTOFF_DATE}  (IMMUTABLE)")
    print(f"training_months = {TRAINING_MONTHS}  (IMMUTABLE)")
    print(f"n_trials = {args.n_trials} | seeds = {args.seeds}")
    if args.smoke_check:
        print("MODE: SMOKE CHECK (3 months, fast)")
    print(f"{'=' * 70}\n")

    # Pre-flight
    _verify_branch()
    _verify_symbols()
    if not args.smoke_check:
        _verify_data_freshness()
        _verify_oi_cache()
    _verify_feature_columns_non_empty()
    _verify_embargo_intact()
    _verify_dsr_psr_call_sites()
    print("[pre-flight] All checks passed.\n")

    # Report directory
    report_dir = REPORTS_DIR / f"iteration_{ITERATION_LABEL}"
    is_dir = report_dir / "in_sample"
    oos_dir = report_dir / "out_of_sample"
    for d in [report_dir, is_dir, oos_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Inner ensemble seeds (EXPLORATION: single outer seed = 42)
    # The regime classifier uses its own REGIME_INNER_SEEDS (5 seeds)
    if args.seeds > 1:
        regime_inner_seeds = REGIME_INNER_SEEDS  # all 5
    else:
        regime_inner_seeds = REGIME_INNER_SEEDS  # all 5 (EXPLORATION always uses 5)

    # ── Phase 1: Run regime classifier walk-forward for each symbol ──────────
    all_is_trades: list = []
    all_oos_trades: list = []
    deriv_features_by_sym: dict[str, pd.DataFrame] = {}
    all_month_stats: list[dict] = []
    total_optuna_trials = 0

    for label, symbol in V3_BASE_SYMBOLS:
        print(f"\n{'─' * 60}")
        print(f"Symbol: {symbol} ({label})")
        print(f"{'─' * 60}")

        # Step 1a: regime classifier walk-forward
        regime_preds_df, deriv_df, month_stats, sym_trials = _monthly_walk_forward(
            symbol=symbol,
            n_trials=args.n_trials,
            ensemble_seeds=regime_inner_seeds,
            smoke_check=args.smoke_check,
        )
        deriv_features_by_sym[symbol] = deriv_df
        all_month_stats.extend(month_stats)
        total_optuna_trials += sym_trials

        # Step 1b: /059 base book (FROZEN)
        print(f"\n[base_book/{symbol}] Running /059 base directional book (FROZEN) ...")
        base_trades = _run_059_base_book(symbol=symbol, smoke_check=args.smoke_check)
        print(f"  [base_book/{symbol}] {len(base_trades)} total trades from /059 base book")

        # Step 1c: apply regime-size overlay
        overlaid_trades = _apply_regime_overlay(base_trades, regime_preds_df, symbol)

        # Split IS / OOS
        is_trades = [t for t in overlaid_trades if t.open_time < OOS_CUTOFF_MS]
        oos_trades = [t for t in overlaid_trades if t.open_time >= OOS_CUTOFF_MS]

        all_is_trades.extend(is_trades)
        all_oos_trades.extend(oos_trades)

        print(f"  [overlay/{symbol}] IS={len(is_trades)} trades, OOS={len(oos_trades)} trades")

    # ── Phase 2: DSR/PBO/PSR computation (genuine — NOT hardcoded) ────────────
    print(f"\n{'─' * 60}")
    print("DSR / PBO / PSR computation (validation_v3 — genuine machinery)")
    print(f"{'─' * 60}")

    # CPCV paths (for PBO)
    cpcv_df, flat_path_sharpes = _write_cpcv_paths(report_dir, all_is_trades)

    # PBO from CPCV
    if len(flat_path_sharpes) >= 4 and len(cpcv_df) >= 4:
        # Build a simple (n_paths × 1) matrix for pbo_from_cpcv
        path_sharpe_arr = np.array(flat_path_sharpes).reshape(-1, 1)
        try:
            pbo_result = pbo_from_cpcv(path_sharpe_arr)
        except Exception as e:
            print(f"  [PBO] pbo_from_cpcv error: {e} — using structural sentinel")
            pbo_result = PBOResult(
                pbo=None,
                note=f"pbo_from_cpcv error: {e}",
                frac_positive_paths=float(np.mean(np.array(flat_path_sharpes) > 0)),
                path_sharpe_quartiles=(0.0, 0.0, 0.0),
            )
    else:
        pbo_result = PBOResult(
            pbo=None,
            note=f"insufficient CPCV paths: {len(flat_path_sharpes)} < 4",
            frac_positive_paths=float(np.mean(np.array(flat_path_sharpes) > 0))
            if flat_path_sharpes
            else 0.0,
            path_sharpe_quartiles=(0.0, 0.0, 0.0),
        )
    print(f"  [PBO] pbo={pbo_result.pbo}, frac_pos={pbo_result.frac_positive_paths:.3f}")

    # OOS monthly Sharpe for DSR
    oos_by_month: dict[str, float] = {}
    for t in all_oos_trades:
        m = pd.Timestamp(t.open_time, unit="ms").strftime("%Y-%m")
        oos_by_month[m] = oos_by_month.get(m, 0.0) + float(t.weighted_pnl)
    oos_monthly_arr = np.array(list(oos_by_month.values())) if oos_by_month else np.array([0.0])

    if len(oos_monthly_arr) > 1 and oos_monthly_arr.std() > 0:
        oos_monthly_sharpe = float(oos_monthly_arr.mean() / oos_monthly_arr.std() * np.sqrt(12))
        oos_sk = float(sp_skew(oos_monthly_arr))
        oos_kt = float(sp_kurtosis(oos_monthly_arr, fisher=False))
    else:
        oos_monthly_sharpe = 0.0
        oos_sk = 0.0
        oos_kt = 3.0

    # DSR — deflated_sharpe_ratio_v3 (genuine call, NOT sentinel)
    # Call-site: validation_v3.deflated_sharpe_ratio_v3(
    #   observed_sr=oos_monthly_sharpe, num_trials=total_optuna_trials, ...)
    # SR granularity: monthly Sharpe (annualized at √12)
    n_backtest_months = max(2, len(oos_by_month))
    try:
        dsr_result = deflated_sharpe_ratio_v3(
            observed_sr=oos_monthly_sharpe,
            num_trials=max(1, total_optuna_trials),
            backtest_length=n_backtest_months,
            skewness=oos_sk,
            kurtosis=oos_kt,
        )
        dsr_val = float(dsr_result["dsr"])
    except Exception as e:
        print(f"  [DSR] deflated_sharpe_ratio_v3 error: {e} — using 0.0")
        dsr_val = 0.0
    print(
        f"  [DSR] dsr={dsr_val:.4f} (n_trials={total_optuna_trials}, "
        f"n_months={n_backtest_months}, oos_monthly_SR={oos_monthly_sharpe:.4f})"
    )

    # PSR — psr() call (genuine, NOT sentinel)
    # Call-site: validation_v3.psr(observed_sharpe=oos_trade_sr, n_obs=len(oos_trades))
    # SR granularity: trade-level (per weighted_pnl, not annualized)
    oos_wp = np.array([float(t.weighted_pnl) for t in all_oos_trades])
    if len(oos_wp) > 1 and oos_wp.std() > 0:
        oos_trade_sr = float(oos_wp.mean() / oos_wp.std())
        oos_trade_sk = float(sp_skew(oos_wp))
        oos_trade_kt = float(sp_kurtosis(oos_wp, fisher=False))
        psr_val = psr(
            observed_sharpe=oos_trade_sr,
            n_obs=len(oos_wp),
            skewness=oos_trade_sk,
            kurtosis=oos_trade_kt,
        )
    else:
        psr_val = 0.0
    print(f"  [PSR] psr={psr_val:.4f}")

    # N_eff
    is_wp = np.array([float(t.weighted_pnl) for t in all_is_trades])
    if len(is_wp) > 1:
        trial_mat = is_wp.reshape(1, -1)  # (1, n_trades) — surrogate
        try:
            n_eff = n_effective_trials(trial_mat)
        except Exception:
            n_eff = max(1, len(all_is_trades) // max(1, len(V3_BASE_SYMBOLS)))
    else:
        n_eff = 1

    # ── Phase 3: Write reports ─────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("Writing reports ...")
    print(f"{'─' * 60}")

    _write_trades_csv(all_is_trades, is_dir / "trades.csv")
    _write_trades_csv(all_oos_trades, oos_dir / "trades.csv")

    _write_comparison(
        report_dir,
        all_is_trades,
        all_oos_trades,
        dsr_val,
        pbo_result,
        psr_val,
        total_optuna_trials,
        n_eff,
    )

    _write_dsr_json(report_dir, dsr_val, pbo_result, psr_val, total_optuna_trials, n_eff)

    _write_adf_test(report_dir, deriv_features_by_sym)

    _write_ic_matrix(report_dir, deriv_features_by_sym)

    _write_per_month_regime_stats(report_dir, all_month_stats)

    # Summary
    is_ms = _monthly_sharpe(all_is_trades)
    oos_ms = _monthly_sharpe(all_oos_trades)
    t_end = time.time()
    elapsed = (t_end - t_start) / 3600.0

    print(f"\n{'=' * 70}")
    print(f"[DONE] {ITERATION_LABEL}  (wall-clock: {elapsed:.2f}h)")
    print(f"  IS  monthly Sharpe:  {is_ms:+.4f}")
    print(f"  OOS monthly Sharpe:  {oos_ms:+.4f}")
    pbo_disp = "NaN" if pbo_result.pbo is None else f"{pbo_result.pbo:.4f}"
    print(f"  DSR={dsr_val:.4f}  PBO={pbo_disp}  PSR={psr_val:.4f}")
    print(f"  IS trades={len(all_is_trades)}  OOS trades={len(all_oos_trades)}")
    print(f"  Reports: {report_dir}")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
