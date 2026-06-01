"""v1 reporting helpers — iter-v1/001 methodology axis.

Provides post-hoc reporting functions that wire v3-rigor Critic checks into the
v1 runner:

    1. ``compute_psr_columns``        — PSR at monthly AND daily granularity
                                        (both vs 0 and vs 1.0 benchmark).
    2. ``compute_n_eff_and_dsr``      — N_eff-corrected DSR via PCA on the
                                        per-trial OOF return matrix loaded from
                                        the oof_persist_path parquet.
                                        iter-v1/008: refactored to per-cell PCA
                                        aggregation (aggfunc="mean") as PRIMARY.
                                        Legacy global-flatten kept as secondary.
    3. ``write_dsr_json``             — consolidated dsr.json artifact.
                                        iter-v1/008: extended schema with per-cell
                                        n_eff fields.
    4. ``write_adf_test_csv``         — per-feature ADF + Bonferroni p-values
                                        + exception_class (193 rows).
    5. ``write_ic_matrix_csv``        — per-family Spearman IC matrix (Fisher-z
                                        averaged, 8×8 symmetric).

All functions are PURELY POST-HOC — none of them modify predictions, feature
columns, or trade rosters. The runner calls them AFTER ``generate_iteration_reports``
returns.

Track isolation
---------------
This module imports from:
- ``crypto_trade.strategies.ml.validation_v1`` (PSR, n_effective_trials)
- ``crypto_trade.features_v1`` (V1_FEATURE_COLUMNS)
Standard library and scientific stack (numpy, scipy, pandas, statsmodels) only.
NO import from features_v2 or features_v3.

Usage (runner snippet)
----------------------
::

    from crypto_trade.strategies.ml.reporting_v1 import (
        V1_FAMILY_MAP,
        compute_psr_columns,
        compute_n_eff_and_dsr,
        write_dsr_json,
        write_adf_test_csv,
        write_ic_matrix_csv,
    )

    psr_cols = compute_psr_columns(monthly_returns_is, daily_returns_is, label="IS")
    n_eff, dsr_val, method = compute_n_eff_and_dsr(
        oof_parquet_path, n_trials_total, sharpe, returns
    )
    write_dsr_json(report_dir, dsr_val, n_trials, n_eff, psr_val, min_trl_months)
    write_adf_test_csv(report_dir, feature_df)
    write_ic_matrix_csv(report_dir, feature_df, forward_returns)

iter-v1/008 per-cell PCA refactor (aggfunc="mean")
---------------------------------------------------
The original global-flatten strategy in ``_pca_n_eff_from_parquet`` (now renamed
``_pca_n_eff_global_flatten``) collapses ALL (symbol × train_month × trial) rows
into a single flat matrix.  This saturates at n_eff = n_trials_naive because all
50 (or 35) unique trial IDs are present across the combined pool.

The new ``_per_cell_n_eff_from_parquet`` function operates per (symbol, train_month)
cell.  Within each cell, ``pivot_table(aggfunc="mean")`` is used because each
(trial_id, candle_open_time_ms) pair appears MULTIPLE TIMES in the parquet (once
per walk-forward fold that covers the candle's train-month).  Using aggfunc="first"
silently discards 2/3 of that fold information; aggfunc="mean" aggregates honestly.

Empirical calibration on /005 proxy (n_trials=35, /005 config):
  aggfunc="first" → per-cell n_eff median 20 (upper bound)
  aggfunc="mean"  → per-cell n_eff median ~11 (corrected)
LM Master single-cell calibration at BASELINE_V1 config (ETHUSDT 2022-01):
  aggfunc="mean"  → n_eff = 9

The BASELINE_V1 anchor (n_trials=50, 193 features, default bounds) is predicted
to yield n_eff_per_cell_median in [10, 18] with point estimate ~11-13.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.features_v1 import V1_FEATURE_COLUMNS
from crypto_trade.strategies.ml.validation_v1 import n_effective_trials, psr

# ---------------------------------------------------------------------------
# Feature family map — maps V1_FEATURE_COLUMNS prefixes to 8 logical families.
# Brief Section 2 Table 2 declares exactly these 8 active families.
# cross_asset and entropy_cusum are EXCLUDED (0 columns in v1 baseline).
# ---------------------------------------------------------------------------

#: Volume feature name prefixes (distinguishes volume from volatility under vol_)
_VOLUME_PREFIXES: tuple[str, ...] = (
    "vol_ad",
    "vol_obv",
    "vol_vwap",
    "vol_cmf",
    "vol_volume",
    "vol_tpv",
    "vol_mfi",
)


def _assign_family(col: str) -> str:
    """Return the logical family name for a V1_FEATURE_COLUMNS column."""
    if col.startswith("cal_"):
        return "calendar"
    if col.startswith("interact_"):
        return "interaction"
    if col.startswith("mom_"):
        return "momentum"
    if col.startswith("mr_"):
        return "mean_reversion"
    if col.startswith("stat_"):
        return "statistical"
    if col.startswith("trend_"):
        return "trend"
    if col.startswith("vol_"):
        if any(col.startswith(pfx) for pfx in _VOLUME_PREFIXES):
            return "volume"
        return "volatility"
    return "unknown"


#: Canonical family -> [feature_names] mapping (computed once at import).
V1_FAMILY_MAP: dict[str, list[str]] = {}
for _col in V1_FEATURE_COLUMNS:
    _fam = _assign_family(_col)
    V1_FAMILY_MAP.setdefault(_fam, []).append(_col)

#: Canonical 8-family ordering for ic_matrix.csv rows/columns.
V1_FAMILIES: list[str] = [
    "calendar",
    "interaction",
    "mean_reversion",
    "momentum",
    "statistical",
    "trend",
    "volatility",
    "volume",
]

# ---------------------------------------------------------------------------
# ADF exception class taxonomy (pre-declared per brief Section 2 + LM Master §3)
# ---------------------------------------------------------------------------

#: Features classified as regime_indicator (intentionally non-stationary).
_REGIME_INDICATOR_PREFIXES: tuple[str, ...] = (
    "trend_ema_",
    "trend_sma_",
    "trend_supertrend",
    "trend_psar",
    "trend_aroon",
    "mr_dist_sma_",
    "mr_dist_vwap",
)

#: Features classified as random_walk_proxy (cumulative by construction).
_RANDOM_WALK_PROXY_COLS: tuple[str, ...] = (
    "vol_obv",
    "vol_ad",
)

#: Features classified as composed (interactions of stationary feeds).
_COMPOSED_PREFIX: str = "interact_"


def _assign_exception_class(col: str) -> str | None:
    """Return the pre-declared ADF exception class, or None if none applies."""
    if any(col.startswith(pfx) for pfx in _REGIME_INDICATOR_PREFIXES):
        return "regime_indicator"
    if col in _RANDOM_WALK_PROXY_COLS:
        return "random_walk_proxy"
    if col.startswith(_COMPOSED_PREFIX):
        return "composed"
    return None


# ---------------------------------------------------------------------------
# 1. PSR computation — monthly and daily granularities
# ---------------------------------------------------------------------------


def compute_psr_columns(
    monthly_returns: list[float] | np.ndarray,
    daily_returns: list[float] | np.ndarray,
) -> dict[str, float]:
    """Compute PSR at both monthly and daily granularities.

    Parameters
    ----------
    monthly_returns
        List of monthly PnL% values (non-annualized).  For IS: ~39 values.
        For OOS: ~15 values.  MUST NOT be annualized (iter-v3/056 trap).
    daily_returns
        List of daily PnL% values (non-annualized).  For IS: ~416 values.
        For OOS: ~131 values.

    Returns
    -------
    dict with keys:
        psr_monthly_vs_0   — PSR(monthly SR, benchmark=0)
        psr_monthly_vs_1   — PSR(monthly SR, benchmark=1.0)  [merge gate column]
        psr_daily_vs_0     — PSR(daily SR, benchmark=0)

    Notes
    -----
    All inputs are NON-ANNUALIZED return series.  PSR's variance correction
    uses (n_obs - 1), which must match the granularity of the observed_sharpe.
    Passing an annualized SR + n_months reproduces the iter-v3/056 130× error.

    The benchmark for monthly-vs-1 is SR = 1.0 expressed at MONTHLY frequency:
    Annualized SR=1.0 → monthly SR = 1.0 / sqrt(12) ≈ 0.2887.  Per Bailey &
    LdP (2014) the benchmark must be at the SAME frequency as observed_sharpe.
    """
    monthly_arr = np.asarray(monthly_returns, dtype=float)
    daily_arr = np.asarray(daily_returns, dtype=float)

    # Monthly SR (non-annualized: mean/std of monthly returns)
    if len(monthly_arr) >= 2 and monthly_arr.std() > 0:
        monthly_sr = float(monthly_arr.mean() / monthly_arr.std())
        monthly_skew = float(_safe_skew(monthly_arr))
        monthly_kurt = float(_safe_kurt(monthly_arr))
        n_monthly = len(monthly_arr)
    else:
        monthly_sr = 0.0
        monthly_skew = 0.0
        monthly_kurt = 3.0
        n_monthly = max(len(monthly_arr), 1)

    # Daily SR (non-annualized)
    if len(daily_arr) >= 2 and daily_arr.std() > 0:
        daily_sr = float(daily_arr.mean() / daily_arr.std())
        daily_skew = float(_safe_skew(daily_arr))
        daily_kurt = float(_safe_kurt(daily_arr))
        n_daily = len(daily_arr)
    else:
        daily_sr = 0.0
        daily_skew = 0.0
        daily_kurt = 3.0
        n_daily = max(len(daily_arr), 1)

    # Benchmark at monthly frequency: annualized SR=1.0 → monthly SR = 1/sqrt(12)
    monthly_benchmark_1 = 1.0 / math.sqrt(12)

    psr_monthly_vs_0 = psr(
        observed_sharpe=monthly_sr,
        n_obs=n_monthly,
        skewness=monthly_skew,
        kurtosis=monthly_kurt,
        benchmark_sharpe=0.0,
    )
    psr_monthly_vs_1 = psr(
        observed_sharpe=monthly_sr,
        n_obs=n_monthly,
        skewness=monthly_skew,
        kurtosis=monthly_kurt,
        benchmark_sharpe=monthly_benchmark_1,
    )
    psr_daily_vs_0 = psr(
        observed_sharpe=daily_sr,
        n_obs=n_daily,
        skewness=daily_skew,
        kurtosis=daily_kurt,
        benchmark_sharpe=0.0,
    )

    return {
        "psr_monthly_vs_0": psr_monthly_vs_0,
        "psr_monthly_vs_1": psr_monthly_vs_1,
        "psr_daily_vs_0": psr_daily_vs_0,
    }


def _safe_skew(arr: np.ndarray) -> float:
    """Compute skewness with fallback for short or constant series."""
    if len(arr) < 3:
        return 0.0
    mean = arr.mean()
    std = arr.std(ddof=1)
    if std <= 0:
        return 0.0
    n = len(arr)
    return float(
        ((arr - mean) ** 3).mean() / std**3 * n / ((n - 1) * (n - 2)) * (n - 1) * (n - 2) / n
    )


def _safe_kurt(arr: np.ndarray) -> float:
    """Compute raw kurtosis with fallback (raw, not excess; Gaussian = 3)."""
    if len(arr) < 4:
        return 3.0
    mean = arr.mean()
    std = arr.std(ddof=1)
    if std <= 0:
        return 3.0
    return float(((arr - mean) ** 4).mean() / std**4)


# ---------------------------------------------------------------------------
# 2. N_eff PCA + N_eff-corrected DSR
# ---------------------------------------------------------------------------

_DSR_EULER_MASCHERONI = 0.5772156649015328


def compute_n_eff_and_dsr(
    oof_parquet_path: Path | None,
    n_trials_naive: int,
    observed_sharpe: float,
    returns: list[float],
    *,
    n_eff_pca_method: str = "auto",
) -> tuple[int, float, str]:
    """Load OOF parquet, compute per-cell N_eff (PRIMARY) + corrected DSR.

    iter-v1/008: refactored to use ``_per_cell_n_eff_from_parquet`` as PRIMARY
    estimator.  The legacy ``_pca_n_eff_global_flatten`` (formerly
    ``_pca_n_eff_from_parquet``) is kept for back-compat side-by-side reporting
    but its result does NOT feed into the returned n_eff or dsr_corrected.

    Parameters
    ----------
    oof_parquet_path
        Path to the per-trial OOF parquet produced by optimization.py when
        oof_persist_path is set.  If None or not found, falls back to using
        n_trials_naive (same as the existing naive DSR).
    n_trials_naive
        Optuna trials per (symbol, train_month) cell.  Used as fallback when
        the parquet is unavailable and as the NaN-guard threshold.
    observed_sharpe
        Annualized Sharpe (daily granularity) used for DSR computation.
    returns
        Daily return series for DSR skew/kurtosis inputs.
    n_eff_pca_method
        "auto" selects eigvalsh per-cell (default).  Passed to sub-functions.

    Returns
    -------
    (n_eff, dsr_corrected, method_used)
        n_eff           — per-cell-median effective trial count (1 ≤ n_eff ≤ n_trials_naive)
        dsr_corrected   — DSR computed with n_eff (per-cell median)
        method_used     — string describing the PCA estimator used
    """
    n_eff = n_trials_naive
    method_used = "naive_fallback"

    if oof_parquet_path is not None and Path(oof_parquet_path).exists():
        try:
            per_cell_result = _per_cell_n_eff_from_parquet(
                Path(oof_parquet_path),
                n_trials_naive,
            )
            n_eff = per_cell_result["n_eff_per_cell_median"]
            method_used = "eigvalsh_cov_per_cell_median_aggfunc_mean"
        except Exception as exc:
            print(
                f"[reporting_v1] WARNING: per-cell N_eff PCA failed ({exc}); "
                "falling back to naive n_trials"
            )
            n_eff = n_trials_naive
            method_used = f"naive_fallback_exception:{type(exc).__name__}"

    # Sanity check: n_eff must be at most n_trials_naive (LM Master invariant).
    # Equality (n_eff == n_trials_naive) is a valid PCA outcome meaning all trials
    # are linearly independent in the OOF return space — not a wiring bug.
    # The _no_compression suffix in method_used distinguishes this from naive_fallback
    # (naive_fallback = parquet not wired; no_compression = parquet wired, PCA ran,
    # but found no redundancy).
    if n_eff >= n_trials_naive and n_trials_naive > 1:
        # PCA produced no compression — keep n_eff at n_trials_naive and flag it
        n_eff = n_trials_naive
        method_used = method_used + "_no_compression"

    # Compute DSR using N_eff (replaces naive n_trials in the deflation term)
    dsr_corrected = _compute_dsr_corrected(
        observed_sharpe=observed_sharpe,
        n_eff=n_eff,
        returns=returns,
    )

    return n_eff, dsr_corrected, method_used


def _per_cell_n_eff_from_parquet(
    parquet_path: Path,
    n_trials_naive: int,
) -> dict[str, Any]:
    """Per-cell N_eff via PCA, aggregated via median across cells.

    iter-v1/008 PRIMARY estimator.  Operates per (symbol, train_month) cell,
    uses ``aggfunc="mean"`` in pivot_table so that multiple walk-forward fold
    occurrences of the same (trial_id, candle_open_time_ms) pair are aggregated
    honestly rather than silently discarded (aggfunc="first" defect — LM Master
    Phase 4.5 Rec #1 ADOPTED).

    Parquet schema (from optimization.py):
        trial_id, symbol, train_month, fold_idx, candle_open_time_ms, oof_return

    Returns
    -------
    dict with keys:
        n_eff_per_cell_median       — int, median across cells (PRIMARY)
        n_eff_per_cell_trimmed_mean — int, 10%-trimmed mean (LM Master Rec #2)
        n_eff_per_cell_p25          — int, 25th percentile
        n_eff_per_cell_p75          — int, 75th percentile
        n_eff_per_cell_min          — int
        n_eff_per_cell_max          — int
        n_eff_per_cell_by_symbol    — dict[str, int], per-symbol median (Rec #2 + Risk #3)
        n_cells                     — int, total cells processed
    """
    from scipy.stats import trim_mean  # noqa: PLC0415

    df = pd.read_parquet(parquet_path)

    # Validate schema
    required_cols = {"trial_id", "oof_return"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"OOF parquet missing columns: {missing}. Found: {list(df.columns)}")

    # Time axis: candle_open_time_ms preferred; fall back to fold_idx
    if "candle_open_time_ms" in df.columns:
        time_col = "candle_open_time_ms"
    elif "fold_idx" in df.columns:
        time_col = "fold_idx"
    else:
        raise ValueError("OOF parquet has no time-axis column (candle_open_time_ms or fold_idx)")

    # Drop NaN oof_return rows (incomplete trials) BEFORE grouping
    df = df.dropna(subset=["oof_return"])
    if df.empty:
        return {
            "n_eff_per_cell_median": n_trials_naive,
            "n_eff_per_cell_trimmed_mean": n_trials_naive,
            "n_eff_per_cell_p25": n_trials_naive,
            "n_eff_per_cell_p75": n_trials_naive,
            "n_eff_per_cell_min": n_trials_naive,
            "n_eff_per_cell_max": n_trials_naive,
            "n_eff_per_cell_by_symbol": {},
            "n_cells": 0,
        }

    # Group by (symbol, train_month) cells; fall back to single group if columns absent
    if "symbol" in df.columns and "train_month" in df.columns:
        group_cols = ["symbol", "train_month"]
    elif "symbol" in df.columns:
        group_cols = ["symbol"]
    else:
        # No grouping columns — treat entire parquet as a single cell
        group_cols = []

    per_cell_n_eff: list[int] = []
    # For by-symbol aggregation: symbol → list[n_eff_per_cell]
    by_symbol_cells: dict[str, list[int]] = {}

    if group_cols:
        cells = df.groupby(group_cols)
        n_cells = cells.ngroups
        for key, cell_df in cells:
            cell_n_eff = _compute_cell_n_eff(cell_df, time_col, n_trials_naive)
            per_cell_n_eff.append(cell_n_eff)
            # Track by symbol for LM Master Risk #3 diagnostic
            if "symbol" in df.columns:
                sym = key[0] if isinstance(key, tuple) else str(key)
                by_symbol_cells.setdefault(sym, []).append(cell_n_eff)
    else:
        # Single-cell path
        cell_n_eff = _compute_cell_n_eff(df, time_col, n_trials_naive)
        per_cell_n_eff = [cell_n_eff]
        n_cells = 1

    if not per_cell_n_eff:
        return {
            "n_eff_per_cell_median": n_trials_naive,
            "n_eff_per_cell_trimmed_mean": n_trials_naive,
            "n_eff_per_cell_p25": n_trials_naive,
            "n_eff_per_cell_p75": n_trials_naive,
            "n_eff_per_cell_min": n_trials_naive,
            "n_eff_per_cell_max": n_trials_naive,
            "n_eff_per_cell_by_symbol": {},
            "n_cells": 0,
        }

    arr = np.array(per_cell_n_eff, dtype=float)

    # Per-symbol medians (LM Master Phase 4.5 Risk #3 diagnostic)
    n_eff_by_symbol: dict[str, int] = {
        sym: int(np.median(np.array(vals))) for sym, vals in by_symbol_cells.items()
    }

    return {
        "n_eff_per_cell_median": int(np.median(arr)),
        "n_eff_per_cell_trimmed_mean": int(trim_mean(arr, 0.10)),
        "n_eff_per_cell_p25": int(np.percentile(arr, 25)),
        "n_eff_per_cell_p75": int(np.percentile(arr, 75)),
        "n_eff_per_cell_min": int(arr.min()),
        "n_eff_per_cell_max": int(arr.max()),
        "n_eff_per_cell_by_symbol": n_eff_by_symbol,
        "n_cells": n_cells,
    }


def _compute_cell_n_eff(
    cell_df: pd.DataFrame,
    time_col: str,
    n_trials_naive: int,
) -> int:
    """Compute n_eff for a single (symbol, train_month) cell via PCA.

    Uses aggfunc="mean" so multiple walk-forward fold occurrences of the same
    (trial_id, candle_open_time_ms) pair are averaged honestly.

    LM Master Phase 4.5 Rec #1 ADOPTED:
        Each (trial_id, candle_open_time_ms) pair appears multiple times (once
        per walk-forward fold that covers the candle).  aggfunc="first" silently
        drops 2/3 of fold info; aggfunc="mean" aggregates honestly.
        Empirical impact on BTCUSDT 2022-01: first → n_eff=19; mean → n_eff=11.
    """
    # LM Master Phase 4.5 Risk #2: NaN guard for variable-trial-count cells
    unique_trials = cell_df["trial_id"].nunique()
    if unique_trials < n_trials_naive:
        print(
            f"[reporting_v1] WARNING: per-cell PCA: cell has {unique_trials} unique trials "
            f"(< n_trials_naive={n_trials_naive}); pruner may be active or cell is partial"
        )

    # Pivot: rows = trial_id, cols = time steps, values = oof_return
    # aggfunc="mean": folds that cover the same candle → averaged OOF return
    try:
        pivot = cell_df.pivot_table(
            index="trial_id",
            columns=time_col,
            values="oof_return",
            aggfunc="mean",  # CRITICAL: LM Master Phase 4.5 Rec #1 ADOPTED
        )
    except Exception as exc:
        print(f"[reporting_v1] WARNING: pivot_table failed in cell: {exc}; using 1")
        return 1

    n_rows = pivot.shape[0]
    if n_rows < 2 or pivot.shape[1] < 2:
        return 1

    # Fill NaN with 0 (neutral — no contribution from missing time periods)
    mat = pivot.fillna(0.0).to_numpy(dtype=float)

    return int(n_effective_trials(mat))


def _pca_n_eff_global_flatten(
    parquet_path: Path,
    n_trials_naive: int,
    method: str,
) -> tuple[int, str]:
    """Load OOF parquet and return (n_eff, method_used) via GLOBAL row-axis flatten.

    LEGACY (iter-v1/001) estimator — renamed from ``_pca_n_eff_from_parquet`` at
    iter-v1/008.  Kept for back-compat side-by-side reporting.  Does NOT feed
    into ``compute_n_eff_and_dsr`` primary path; only used for comparison.

    The global flatten collapses ALL (symbol × train_month × trial) rows into a
    single flat matrix.  This saturates at n_eff = n_trials_naive because all
    unique trial IDs are present across the combined pool (iter-v1/001 post-mortem:
    5 symbols × 53 train-months × 5 fold_idx collapsed to 50 unique trial_id keys).
    """
    df = pd.read_parquet(parquet_path)

    # Validate schema — must have oof_return and trial_id columns at minimum
    required_cols = {"trial_id", "oof_return"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"OOF parquet missing columns: {missing}. Found: {list(df.columns)}")

    # Create a unique row key = (symbol, train_month, trial_id) — each cell's trial
    if "symbol" in df.columns and "train_month" in df.columns:
        df["_trial_key"] = (
            df["symbol"].astype(str)
            + "__"
            + df["train_month"].astype(str)
            + "__t"
            + df["trial_id"].astype(str)
        )
    else:
        df["_trial_key"] = "t" + df["trial_id"].astype(str)

    # Time axis: use candle_open_time_ms if available, otherwise fold_idx
    if "candle_open_time_ms" in df.columns:
        time_col = "candle_open_time_ms"
    elif "fold_idx" in df.columns:
        time_col = "fold_idx"
    else:
        raise ValueError("OOF parquet has no time-axis column (candle_open_time_ms or fold_idx)")

    # Drop NaN oof_return rows (incomplete trials)
    df = df.dropna(subset=["oof_return"])
    if df.empty:
        return n_trials_naive, "parquet_empty_after_dropna"

    # Pivot: rows = unique (symbol, month, trial); cols = time steps
    pivot = df.pivot_table(
        index="_trial_key",
        columns=time_col,
        values="oof_return",
        aggfunc="first",
    )

    n_rows = pivot.shape[0]
    if n_rows < 2:
        return 1, "parquet_too_few_rows"

    # Fill NaN with 0 (brief LM Master §2: NaN-padded matrix; 0 = neutral)
    mat = pivot.fillna(0.0).to_numpy(dtype=float)

    # Memory guard: if matrix is very large, use truncated SVD approach
    n_t = mat.shape[1]
    n_r = mat.shape[0]

    # n_effective_trials uses eigvalsh on the (n_rows × n_rows) covariance.
    # If n_rows is large (>5000), use randomized PCA via SVD on the smaller dimension.
    if n_r > 2000 and n_r > n_t:
        # SVD on centered matrix — eigenvalues of XTX / (n-1) = singular values squared / (n-1)
        mat_c = mat - mat.mean(axis=1, keepdims=True)
        # Use numpy SVD (full_matrices=False to get min(n_r,n_t) singular values)
        try:
            _, s, _ = np.linalg.svd(mat_c, full_matrices=False)
            eigenvalues = np.sort(s**2)[::-1]
            eigenvalues = np.clip(eigenvalues, 0, None)
            total_var = float(eigenvalues.sum())
            if total_var == 0:
                return 1, "svd_zero_variance"
            cumvar = np.cumsum(eigenvalues) / total_var
            n_eff = int(np.searchsorted(cumvar, 0.95)) + 1
            n_eff = min(n_eff, n_r)
            used_method = "svd_randomized"
        except np.linalg.LinAlgError:
            n_eff = n_trials_naive
            used_method = "svd_failed_fallback"
    else:
        n_eff = n_effective_trials(mat)
        used_method = "eigvalsh_cov"

    return n_eff, used_method


def _compute_dsr_corrected(
    observed_sharpe: float,
    n_eff: int,
    returns: list[float],
) -> float:
    """Compute DSR using N_eff as the multiple-testing correction term.

    Implements Bailey & LdP (2014) Eq. 8:
        DSR = PSR(E[max_SR])
    where E[max_SR] = (1 - gamma) * Z^{-1}(1 - 1/n_eff)
                     + gamma * Z^{-1}(1 - 1/(n_eff * e))
    and gamma is the Euler-Mascheroni constant.

    Parameters
    ----------
    observed_sharpe
        Annualized daily Sharpe.
    n_eff
        Effective trial count from PCA.
    returns
        Daily return series (for skew/kurtosis).
    """
    from scipy.stats import norm

    if n_eff <= 0:
        n_eff = 1

    ret_arr = np.asarray(returns, dtype=float)
    n_obs = len(ret_arr)

    if n_obs < 2:
        return 0.0

    std_r = float(ret_arr.std(ddof=1))
    if std_r <= 0:
        return 0.0

    skew = float(_safe_skew(ret_arr))
    kurt = float(_safe_kurt(ret_arr))

    # Annualized Sharpe → daily non-annualized
    daily_sr = observed_sharpe / math.sqrt(252)

    # E[max_SR] formula (Bailey & LdP 2014, Eq. 8, using n_eff)
    gamma = _DSR_EULER_MASCHERONI
    if n_eff == 1:
        e_max_sr = 0.0
    else:
        z1 = norm.ppf(1.0 - 1.0 / n_eff)
        z2 = norm.ppf(1.0 - 1.0 / (n_eff * math.e))
        e_max_sr = (1.0 - gamma) * z1 + gamma * z2

    # PSR with e_max_sr as benchmark (Bailey & LdP DSR = PSR(SR* = E[max_SR]))
    variance_num = max(
        1.0 - skew * daily_sr + (kurt - 1.0) / 4.0 * daily_sr**2,
        1e-12,
    )
    std_sr = math.sqrt(variance_num / (n_obs - 1))
    if std_sr <= 0:
        return 1.0 if daily_sr > e_max_sr else 0.0

    z = (daily_sr - e_max_sr) / std_sr
    return float(norm.cdf(z))


# ---------------------------------------------------------------------------
# 3. dsr.json writer
# ---------------------------------------------------------------------------


def write_dsr_json(
    report_dir: Path,
    *,
    dsr: float,
    pbo: float | None,
    psr_val: float,
    n_trials: int,
    n_eff: int,
    n_eff_pca_method: str,
    min_trl_months: float,
    label: str = "",
    # iter-v1/008 per-cell N_eff fields (optional; None = not yet computed)
    n_eff_per_cell_median: int | None = None,
    n_eff_per_cell_trimmed_mean: int | None = None,
    n_eff_per_cell_p25: int | None = None,
    n_eff_per_cell_p75: int | None = None,
    n_eff_per_cell_min: int | None = None,
    n_eff_per_cell_max: int | None = None,
    n_eff_per_cell_by_symbol: dict[str, int] | None = None,
    n_cells: int | None = None,
) -> Path:
    """Write consolidated dsr.json to report_dir/dsr.json.

    Parameters
    ----------
    report_dir
        Iteration report directory (is_dir or oos_dir — called for each half).
    dsr
        N_eff-corrected DSR (replaces naive DSR in comparison.csv).
    pbo
        Probability of Backtest Overfitting from CPCV. ``None`` when CPCV is
        deferred (iter-v1/001 case; declared in brief Section 9 as fallback).
    psr_val
        PSR (monthly, vs 1.0) — the merge-gate column value.
    n_trials
        Optuna trials per (symbol, train_month) cell (naive count for reference).
    n_eff
        Effective trial count from per-cell PCA median (iter-v1/008 PRIMARY).
        For pre-/008 runs this is the global-flatten n_eff (back-compat).
        1 ≤ n_eff ≤ n_trials.
    n_eff_pca_method
        String describing the PCA estimator used.
    min_trl_months
        Minimum monthly SR benchmark for DSR (expressed at monthly frequency).
    label
        Optional label ("IS" or "OOS") for logging.
    n_eff_per_cell_median
        iter-v1/008: median n_eff across (symbol, train_month) cells.
        None when per-cell refactor not yet run (pre-/008 callers).
    n_eff_per_cell_trimmed_mean
        iter-v1/008: 10%-trimmed mean across cells (LM Master Rec #2).
    n_eff_per_cell_p25, n_eff_per_cell_p75
        iter-v1/008: IQR bounds across cells.
    n_eff_per_cell_min, n_eff_per_cell_max
        iter-v1/008: range bounds across cells.
    n_eff_per_cell_by_symbol
        iter-v1/008: per-symbol median dict (LM Master Risk #3 diagnostic).
    n_cells
        iter-v1/008: total (symbol, train_month) cells processed.
    """
    payload: dict[str, Any] = {
        "dsr": round(dsr, 6),
        "pbo": pbo,  # null when CPCV deferred — brief Section 9 approves this
        "psr": round(psr_val, 6),
        "n_trials": n_trials,
        # Legacy field kept for back-compat; iter-v1/008+ this equals n_eff_per_cell_median
        "n_eff": n_eff,
        "n_eff_pca_method": n_eff_pca_method,
        "min_trl_months": round(min_trl_months, 6),
    }
    # iter-v1/008 per-cell fields — only emitted when the per-cell refactor ran
    if n_eff_per_cell_median is not None:
        payload["n_eff_per_cell_median"] = n_eff_per_cell_median
        payload["n_eff_method_per_cell"] = "eigvalsh_cov_per_cell_median_aggfunc_mean"
    if n_eff_per_cell_trimmed_mean is not None:
        payload["n_eff_per_cell_trimmed_mean"] = n_eff_per_cell_trimmed_mean
    if n_eff_per_cell_p25 is not None:
        payload["n_eff_per_cell_p25"] = n_eff_per_cell_p25
    if n_eff_per_cell_p75 is not None:
        payload["n_eff_per_cell_p75"] = n_eff_per_cell_p75
    if n_eff_per_cell_min is not None:
        payload["n_eff_per_cell_min"] = n_eff_per_cell_min
    if n_eff_per_cell_max is not None:
        payload["n_eff_per_cell_max"] = n_eff_per_cell_max
    if n_eff_per_cell_by_symbol is not None:
        payload["n_eff_per_cell_by_symbol"] = n_eff_per_cell_by_symbol
    if n_cells is not None:
        payload["n_cells"] = n_cells

    out_path = report_dir / "dsr.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    if label:
        per_cell_str = (
            f" n_eff_per_cell_median={n_eff_per_cell_median}"
            if n_eff_per_cell_median is not None
            else ""
        )
        print(
            f"[reporting_v1] {label} dsr.json written: "
            f"dsr={dsr:.4f} n_eff={n_eff}{per_cell_str} psr={psr_val:.4f}"
        )
    return out_path


# ---------------------------------------------------------------------------
# 4. ADF per-feature CSV
# ---------------------------------------------------------------------------


def write_adf_test_csv(
    report_dir: Path,
    feature_df: pd.DataFrame,
    *,
    alpha_raw: float = 0.05,
    label: str = "",
) -> Path:
    """Run ADF test on each V1_FEATURE_COLUMNS column and write adf_test.csv.

    Parameters
    ----------
    report_dir
        IS or OOS report directory. File is written to report_dir/adf_test.csv.
    feature_df
        DataFrame with ALL V1_FEATURE_COLUMNS as columns (loaded from the IS-window
        feature parquet). Must NOT include OOS rows (IS-only per brief Section 2).
    alpha_raw
        Raw significance level for individual tests. Default 0.05.
    label
        Optional label for progress logging.

    Output schema
    -------------
    feature, family, adf_stat, p_value_raw, p_value_bonferroni, lags_used,
    n_obs, exception_class, bonferroni_pass, raw_pass

    Columns:
        exception_class     — pre-declared class or empty string (null=None)
        bonferroni_pass     — True if p_value_raw < (alpha_raw / n_features)
        raw_pass            — True if p_value_raw < alpha_raw
    """
    from statsmodels.tsa.stattools import adfuller

    cols = list(V1_FEATURE_COLUMNS)
    n_features = len(cols)
    bonferroni_alpha = alpha_raw / n_features

    rows = []
    for col in cols:
        family = _assign_family(col)
        exc_class = _assign_exception_class(col)

        if col not in feature_df.columns:
            rows.append(
                {
                    "feature": col,
                    "family": family,
                    "adf_stat": "",
                    "p_value_raw": "",
                    "p_value_bonferroni": bonferroni_alpha,
                    "lags_used": "",
                    "n_obs": 0,
                    "exception_class": exc_class or "",
                    "bonferroni_pass": "",
                    "raw_pass": "",
                }
            )
            continue

        series = feature_df[col].dropna()
        if len(series) < 20:
            rows.append(
                {
                    "feature": col,
                    "family": family,
                    "adf_stat": "",
                    "p_value_raw": "",
                    "p_value_bonferroni": bonferroni_alpha,
                    "lags_used": "",
                    "n_obs": len(series),
                    "exception_class": exc_class or "",
                    "bonferroni_pass": "",
                    "raw_pass": "",
                }
            )
            continue

        try:
            adf_result = adfuller(series.values, autolag="AIC")
            adf_stat = float(adf_result[0])
            p_raw = float(adf_result[1])
            lags = int(adf_result[2])
            n_obs = int(adf_result[3])
        except Exception as exc:
            # ADF can fail on pathological constant series
            rows.append(
                {
                    "feature": col,
                    "family": family,
                    "adf_stat": f"ERROR:{type(exc).__name__}",
                    "p_value_raw": "",
                    "p_value_bonferroni": bonferroni_alpha,
                    "lags_used": "",
                    "n_obs": len(series),
                    "exception_class": exc_class or "",
                    "bonferroni_pass": "",
                    "raw_pass": "",
                }
            )
            continue

        rows.append(
            {
                "feature": col,
                "family": family,
                "adf_stat": f"{adf_stat:.6f}",
                "p_value_raw": f"{p_raw:.6f}",
                "p_value_bonferroni": f"{bonferroni_alpha:.8f}",
                "lags_used": lags,
                "n_obs": n_obs,
                "exception_class": exc_class or "",
                "bonferroni_pass": str(p_raw < bonferroni_alpha),
                "raw_pass": str(p_raw < alpha_raw),
            }
        )

    out_path = report_dir / "adf_test.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "feature",
        "family",
        "adf_stat",
        "p_value_raw",
        "p_value_bonferroni",
        "lags_used",
        "n_obs",
        "exception_class",
        "bonferroni_pass",
        "raw_pass",
    ]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Summary counts for runner output
    n_raw_fail = sum(1 for r in rows if r["raw_pass"] == "False" and r["exception_class"] == "")
    n_with_exception = sum(1 for r in rows if r["exception_class"] != "")
    if label:
        print(
            f"[reporting_v1] {label} adf_test.csv: {n_features} features, "
            f"{n_with_exception} declared exceptions, "
            f"{n_raw_fail} raw-α failures without declaration"
        )
    return out_path


# ---------------------------------------------------------------------------
# 5. IC matrix CSV
# ---------------------------------------------------------------------------


def write_ic_matrix_csv(
    report_dir: Path,
    feature_df: pd.DataFrame,
    forward_returns: pd.Series | np.ndarray,
    *,
    label: str = "",
) -> Path:
    """Compute per-family Spearman IC matrix and write ic_matrix.csv.

    For each of the 8 V1 feature families:
    1. Compute per-feature Spearman IC vs forward_returns over the IS window.
    2. Fisher-z transform each IC, average within family, back-transform.
    3. Report: family_mean_ic, family_median_ic, family_iqr_low/high, n_features.

    For the off-diagonal pairwise cells:
    - Spearman IC between family-A mean-feature rank and family-B mean-feature rank.
    - Fisher-z'd for off-diagonal aggregation.

    NaN handling: per-pair dropna (per LM Master §2 saturation risk note).
    cross_asset and entropy_cusum are excluded (0 columns in v1 baseline).

    Parameters
    ----------
    report_dir
        IS or OOS report directory. File written to report_dir/ic_matrix.csv.
    feature_df
        DataFrame of IS-window features (all V1_FEATURE_COLUMNS as columns).
    forward_returns
        Per-row next-candle log-return (1-bar forward return). Must align
        index with feature_df.
    label
        Optional label for logging.

    Output schema
    -------------
    family_a, family_b, ic_mean_fisher, ic_median, ic_iqr_low, ic_iqr_high,
    n_features_a, n_features_b
    """
    from scipy.stats import spearmanr

    fwd = np.asarray(forward_returns, dtype=float)

    # Pre-compute per-feature Spearman IC vs forward returns (per-pair dropna)
    feature_ic: dict[str, float] = {}
    for col in V1_FEATURE_COLUMNS:
        if col not in feature_df.columns:
            feature_ic[col] = float("nan")
            continue
        feat = feature_df[col].values.astype(float)
        mask = ~(np.isnan(feat) | np.isnan(fwd))
        if mask.sum() < 5:
            feature_ic[col] = float("nan")
            continue
        try:
            ic_val, _ = spearmanr(feat[mask], fwd[mask])
            feature_ic[col] = float(ic_val) if not math.isnan(ic_val) else float("nan")
        except Exception:
            feature_ic[col] = float("nan")

    # Per-family IC aggregation (Fisher-z transform)
    fam_stats: dict[str, dict] = {}
    for fam in V1_FAMILIES:
        cols_in_fam = V1_FAMILY_MAP.get(fam, [])
        ics = [
            feature_ic[c] for c in cols_in_fam if not math.isnan(feature_ic.get(c, float("nan")))
        ]
        if not ics:
            fam_stats[fam] = {
                "mean_ic": 0.0,
                "median_ic": 0.0,
                "iqr_low": 0.0,
                "iqr_high": 0.0,
                "n_features": len(cols_in_fam),
                "mean_rank": None,
            }
            continue
        ic_arr = np.array(ics)
        # Fisher-z average: atanh(ic) → mean → tanh
        z_vals = np.arctanh(np.clip(ic_arr, -0.9999, 0.9999))
        mean_z = float(z_vals.mean())
        mean_ic = float(np.tanh(mean_z))
        median_ic = float(np.median(ic_arr))
        iqr_low = float(np.percentile(ic_arr, 25))
        iqr_high = float(np.percentile(ic_arr, 75))
        # Mean-feature rank (for pairwise off-diagonal IC)
        # Use mean of raw feature values ranked together (Spearman uses ranks)
        fam_mean_vals = (
            np.nanmean(
                np.stack(
                    [
                        feature_df[c].values.astype(float)
                        for c in cols_in_fam
                        if c in feature_df.columns
                    ],
                    axis=1,
                ),
                axis=1,
            )
            if any(c in feature_df.columns for c in cols_in_fam)
            else None
        )
        fam_stats[fam] = {
            "mean_ic": mean_ic,
            "median_ic": median_ic,
            "iqr_low": iqr_low,
            "iqr_high": iqr_high,
            "n_features": len(cols_in_fam),
            "mean_rank_vals": fam_mean_vals,
        }

    # Build 8×8 ic_matrix rows (both triangles + diagonal = full symmetric matrix)
    rows = []
    for i, fam_a in enumerate(V1_FAMILIES):
        for fam_b in V1_FAMILIES[i:]:
            stats_a = fam_stats[fam_a]
            stats_b = fam_stats[fam_b]
            if fam_a == fam_b:
                # Diagonal: self-IC = within-family mean
                ic_cell = stats_a["mean_ic"]
                ic_median = stats_a["median_ic"]
                ic_iqr_low = stats_a["iqr_low"]
                ic_iqr_high = stats_a["iqr_high"]
            else:
                # Off-diagonal: Spearman IC between family-A mean-vals and family-B mean-vals
                vals_a = stats_a.get("mean_rank_vals")
                vals_b = stats_b.get("mean_rank_vals")
                if vals_a is None or vals_b is None:
                    ic_cell = float("nan")
                    ic_median = float("nan")
                    ic_iqr_low = float("nan")
                    ic_iqr_high = float("nan")
                else:
                    mask = ~(np.isnan(vals_a) | np.isnan(vals_b) | np.isnan(fwd))
                    if mask.sum() < 5:
                        ic_cell = float("nan")
                        ic_median = float("nan")
                        ic_iqr_low = float("nan")
                        ic_iqr_high = float("nan")
                    else:
                        try:
                            ic_cell_raw, _ = spearmanr(vals_a[mask], vals_b[mask])
                            ic_cell = (
                                float(ic_cell_raw) if not math.isnan(ic_cell_raw) else float("nan")
                            )
                        except Exception:
                            ic_cell = float("nan")
                        # Off-diagonal doesn't have per-feature iqr; report nan
                        ic_median = ic_cell
                        ic_iqr_low = float("nan")
                        ic_iqr_high = float("nan")
            rows.append(
                {
                    "family_a": fam_a,
                    "family_b": fam_b,
                    "ic_mean_fisher": f"{ic_cell:.6f}" if not math.isnan(ic_cell) else "nan",
                    "ic_median": f"{ic_median:.6f}" if not math.isnan(ic_median) else "nan",
                    "ic_iqr_low": f"{ic_iqr_low:.6f}" if not math.isnan(ic_iqr_low) else "nan",
                    "ic_iqr_high": f"{ic_iqr_high:.6f}" if not math.isnan(ic_iqr_high) else "nan",
                    "n_features_a": stats_a["n_features"],
                    "n_features_b": stats_b["n_features"],
                }
            )

    out_path = report_dir / "ic_matrix.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "family_a",
        "family_b",
        "ic_mean_fisher",
        "ic_median",
        "ic_iqr_low",
        "ic_iqr_high",
        "n_features_a",
        "n_features_b",
    ]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    if label:
        print(f"[reporting_v1] {label} ic_matrix.csv: {len(rows)} family-pair rows")
    return out_path


# ---------------------------------------------------------------------------
# Comparison.csv PSR + N_eff row appender
# ---------------------------------------------------------------------------


def append_psr_rows_to_comparison(
    comparison_csv_path: Path,
    is_psr_cols: dict[str, float],
    oos_psr_cols: dict[str, float],
    is_n_eff: int,
    oos_n_eff: int,
    *,
    is_n_eff_per_cell_median: int | None = None,
    oos_n_eff_per_cell_median: int | None = None,
) -> None:
    """Append PSR and n_effective_trials rows to an existing comparison.csv.

    Called AFTER generate_iteration_reports() has written comparison.csv.
    Appends 4 rows: psr_monthly_vs_0, psr_monthly_vs_1, psr_daily_vs_0,
    n_effective_trials (legacy global-flatten).

    iter-v1/008: also appends ``n_eff_per_cell_median`` row when the per-cell
    refactor ran.  Pass ``is_n_eff_per_cell_median`` and
    ``oos_n_eff_per_cell_median`` to enable the new row.

    Parameters
    ----------
    comparison_csv_path
        Absolute path to the existing comparison.csv.
    is_psr_cols
        Dict from compute_psr_columns() for IS half.
    oos_psr_cols
        Dict from compute_psr_columns() for OOS half.
    is_n_eff
        Effective trial count from IS half PCA (global-flatten legacy).
    oos_n_eff
        Effective trial count from OOS half PCA (global-flatten legacy).
    is_n_eff_per_cell_median
        iter-v1/008: per-cell median n_eff for IS half. None = not yet computed.
    oos_n_eff_per_cell_median
        iter-v1/008: per-cell median n_eff for OOS half. None = not yet computed.
    """

    def _ratio(oos_v: float | int, is_v: float | int) -> str:
        if is_v == 0:
            return "—"
        return f"{oos_v / is_v:.4f}"

    new_rows = [
        [
            "psr_monthly_vs_0",
            f"{is_psr_cols['psr_monthly_vs_0']:.6f}",
            f"{oos_psr_cols['psr_monthly_vs_0']:.6f}",
            _ratio(oos_psr_cols["psr_monthly_vs_0"], is_psr_cols["psr_monthly_vs_0"]),
        ],
        [
            "psr_monthly_vs_1",
            f"{is_psr_cols['psr_monthly_vs_1']:.6f}",
            f"{oos_psr_cols['psr_monthly_vs_1']:.6f}",
            _ratio(oos_psr_cols["psr_monthly_vs_1"], is_psr_cols["psr_monthly_vs_1"]),
        ],
        [
            "psr_daily_vs_0",
            f"{is_psr_cols['psr_daily_vs_0']:.6f}",
            f"{oos_psr_cols['psr_daily_vs_0']:.6f}",
            _ratio(oos_psr_cols["psr_daily_vs_0"], is_psr_cols["psr_daily_vs_0"]),
        ],
        [
            "n_effective_trials",
            str(is_n_eff),
            str(oos_n_eff),
            _ratio(oos_n_eff, is_n_eff),
        ],
    ]

    # iter-v1/008: per-cell median row (emitted when per-cell refactor ran)
    if is_n_eff_per_cell_median is not None and oos_n_eff_per_cell_median is not None:
        new_rows.append(
            [
                "n_eff_per_cell_median",
                str(is_n_eff_per_cell_median),
                str(oos_n_eff_per_cell_median),
                _ratio(oos_n_eff_per_cell_median, is_n_eff_per_cell_median),
            ]
        )

    with open(comparison_csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)

    per_cell_str = (
        f" n_eff_per_cell_median IS={is_n_eff_per_cell_median} OOS={oos_n_eff_per_cell_median}"
        if is_n_eff_per_cell_median is not None
        else ""
    )
    print(
        f"[reporting_v1] comparison.csv updated: "
        f"psr_monthly_vs_0/1, psr_daily_vs_0, n_effective_trials appended. "
        f"IS n_eff={is_n_eff} OOS n_eff={oos_n_eff}{per_cell_str}"
    )


def append_r5_rows_to_comparison(
    comparison_csv_path: Path,
    r5_fire_rate_is: float,
    r5_fire_rate_oos: float,
) -> None:
    """Append r5_fire_rate_is and r5_fire_rate_oos rows to an existing comparison.csv.

    Called AFTER append_psr_rows_to_comparison().  The anchor (baseline) value
    for both rows is 0.0 because R5 was not enabled on the baseline.  The
    ratio column is omitted (``—``) when the IS fire rate is 0.

    Parameters
    ----------
    comparison_csv_path
        Absolute path to the existing comparison.csv.
    r5_fire_rate_is
        Fraction of IS order-eligible signals where R5 fired (0.0 – 1.0).
    r5_fire_rate_oos
        Fraction of OOS order-eligible signals where R5 fired (0.0 – 1.0).
    """
    anchor_is = 0.0  # R5 not enabled on baseline
    anchor_oos = 0.0

    def _ratio(oos_v: float, is_v: float) -> str:
        if is_v == 0:
            return "—"
        return f"{oos_v / is_v:.4f}"

    new_rows = [
        [
            "r5_fire_rate_is",
            f"{anchor_is:.6f}",
            f"{r5_fire_rate_is:.6f}",
            _ratio(r5_fire_rate_is, anchor_is),
        ],
        [
            "r5_fire_rate_oos",
            f"{anchor_oos:.6f}",
            f"{r5_fire_rate_oos:.6f}",
            _ratio(r5_fire_rate_oos, anchor_oos),
        ],
    ]

    with open(comparison_csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)

    print(
        f"[reporting_v1] comparison.csv updated: r5_fire_rate_is={r5_fire_rate_is:.4f} "
        f"r5_fire_rate_oos={r5_fire_rate_oos:.4f} appended."
    )


def append_r5_binary_kill_rows_to_comparison(
    comparison_csv_path: Path,
    r5_kill_fire_rate_is: float,
    r5_kill_fire_rate_oos: float,
) -> None:
    """Append r5_binary_kill_fire_rate_is and r5_binary_kill_fire_rate_oos rows.

    Fixes the D-RPRT-001 defect from iter-v1/010: each row now places the IS
    fire rate in the ``in_sample`` column and the OOS fire rate in the
    ``out_of_sample`` column, matching the standard comparison.csv schema
    (metric, in_sample, out_of_sample, ratio).

    Both rows carry the same IS and OOS values — the metric name records which
    half is the primary subject of that row.  The ratio column is OOS/IS for
    each row.  When IS fire rate is 0, ratio is emitted as '—'.

    Called AFTER append_r5_rows_to_comparison() (which handles /010's
    proportional-scaling fire-rate rows).  The anchor (baseline) value for
    both rows is 0.0 because R5-BINARY-KILL was not enabled on the baseline.

    Parameters
    ----------
    comparison_csv_path
        Absolute path to the existing comparison.csv.
    r5_kill_fire_rate_is
        Fraction of IS candidate signals where R5-BINARY-KILL fired (0.0–1.0).
    r5_kill_fire_rate_oos
        Fraction of OOS candidate signals where R5-BINARY-KILL fired (0.0–1.0).
    """

    def _ratio(oos_v: float, is_v: float) -> str:
        if is_v == 0:
            return "—"
        return f"{oos_v / is_v:.4f}"

    # Schema: [metric, in_sample, out_of_sample, ratio]
    # Both rows carry IS rate in in_sample and OOS rate in out_of_sample.
    # This is the D-RPRT-001 fix: values belong in the column that matches
    # the sample-half label, not inverted.
    new_rows = [
        [
            "r5_binary_kill_fire_rate_is",
            f"{r5_kill_fire_rate_is:.6f}",
            f"{r5_kill_fire_rate_oos:.6f}",
            _ratio(r5_kill_fire_rate_oos, r5_kill_fire_rate_is),
        ],
        [
            "r5_binary_kill_fire_rate_oos",
            f"{r5_kill_fire_rate_is:.6f}",
            f"{r5_kill_fire_rate_oos:.6f}",
            _ratio(r5_kill_fire_rate_oos, r5_kill_fire_rate_is),
        ],
    ]

    with open(comparison_csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)

    print(
        f"[reporting_v1] comparison.csv updated: "
        f"r5_binary_kill_fire_rate_is={r5_kill_fire_rate_is:.4f} "
        f"r5_binary_kill_fire_rate_oos={r5_kill_fire_rate_oos:.4f} appended."
    )


def append_vol_ceiling_rows_to_comparison(
    comparison_csv_path: Path,
    vol_ceiling_fire_rate_is: float,
    vol_ceiling_fire_rate_oos: float,
) -> None:
    """Append vol_ceiling_fire_rate_is and vol_ceiling_fire_rate_oos rows.

    F-AXIS #2 wiring proof for iter-v1/038 (per-symbol rv-ceiling risk-primitive).
    Schema: [metric, in_sample, out_of_sample, ratio].
    Baseline value is 0.0 (ceiling not enabled on baseline).
    Ratio is OOS/IS; emitted as '—' when IS fire rate is 0.

    Parameters
    ----------
    comparison_csv_path
        Absolute path to the existing comparison.csv.
    vol_ceiling_fire_rate_is
        Fraction of IS candidate signals where vol ceiling fired (0.0–1.0).
    vol_ceiling_fire_rate_oos
        Fraction of OOS candidate signals where vol ceiling fired (0.0–1.0).
    """

    def _ratio(oos_v: float, is_v: float) -> str:
        if is_v == 0:
            return "—"
        return f"{oos_v / is_v:.4f}"

    new_rows = [
        [
            "vol_ceiling_fire_rate_is",
            f"{vol_ceiling_fire_rate_is:.6f}",
            f"{vol_ceiling_fire_rate_oos:.6f}",
            _ratio(vol_ceiling_fire_rate_oos, vol_ceiling_fire_rate_is),
        ],
        [
            "vol_ceiling_fire_rate_oos",
            f"{vol_ceiling_fire_rate_is:.6f}",
            f"{vol_ceiling_fire_rate_oos:.6f}",
            _ratio(vol_ceiling_fire_rate_oos, vol_ceiling_fire_rate_is),
        ],
    ]

    with open(comparison_csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)

    print(
        f"[reporting_v1] comparison.csv updated: "
        f"vol_ceiling_fire_rate_is={vol_ceiling_fire_rate_is:.4f} "
        f"vol_ceiling_fire_rate_oos={vol_ceiling_fire_rate_oos:.4f} appended "
        f"[iter-v1/038 F-AXIS#2 wiring proof]."
    )
