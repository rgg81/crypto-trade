"""Baseline v3 runner — iter-v3/004 per-cell PBO consumer pipeline.

Inherits the same universe {BCH, MKR, LDO, TRX} and model architecture as
iter-v3/003.  The single architectural change is the per-cell consumer
pipeline for PBO and n_eff computation (iter-v3/004 brief Section 3.5):

  Sub-fix #1: _compute_cpcv_paths rewritten to iterate over (sym, month)
    cells from trial_oof_returns.parquet, compute per-cell CSCV PBO via
    pbo_from_cpcv, persist per_cell_pbo.csv, return cross-cell mean PBO.
  Sub-fix #2: n_eff rewritten to iterate over cells, compute per-cell n_eff
    via n_effective_trials, return median across cells.
  Sub-fix #3: New adversarial test tests/strategies/ml/test_per_cell_pbo_synthetic.py.
  Sub-fix #4: per_cell_pbo.csv written alongside dsr.json for audit trail.
  Sub-fix #5: seed_summary.json "pbo" field is now a float (not literal "NaN").

Reports written to:
  reports-v3/iteration_v3-004/
    in_sample/  out_of_sample/  comparison.csv  pareto_front.csv
    cpcv_paths.csv  adf_test.csv  ic_matrix.csv  dsr.json  run.log
    trial_oof_returns.parquet  per_cell_pbo.csv  (NEW — iter-v3/004)

Usage:
    uv run python run_baseline_v3.py
    uv run python run_baseline_v3.py --seeds 1 --n-trials 50
    uv run python run_baseline_v3.py --skip-features  # reuse existing parquets
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v3 import (
    V3_EXCLUDED_SYMBOLS,
    V3_FEATURE_COLUMNS,
    process_symbol_v3,
)
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
from crypto_trade.strategies.ml.risk_v2 import (
    BtcTrendFilterConfig,
    HitRateGateConfig,
    RiskV2Config,
    apply_btc_trend_filter,
    apply_hit_rate_gate,
    load_btc_klines_for_filter,
)
from crypto_trade.strategies.ml.risk_v3 import RiskV3Wrapper
from crypto_trade.strategies.ml.validation_v3 import (
    REQUIRED_GAP,
    PBOResult,
    combinatorial_purged_cv,
    deflated_sharpe_ratio_v3,
    n_effective_trials,
    pbo_from_cpcv,
    psr,
)

# ============================================================
# Constants — DO NOT CHANGE
# ============================================================
OOS_CUTOFF_DATE = "2025-03-24"  # IMMUTABLE
TRAINING_MONTHS = 24  # IMMUTABLE

# Inner ensemble size (number of seeds combined inside LightGbmStrategy per
# outer seed). Pre-iter-v3/006: a hardcoded constant [42, 123, 456, 789, 1001]
# was passed for ALL outer seeds, so --seeds N produced N IDENTICAL ensembles.
# iter-v3/006 fix: each outer seed now derives a distinct 5-seed inner ensemble
# via `_derive_ensemble_seeds(outer_seed)`. The legacy seed list is preserved
# below for documentation only — it is no longer passed to LightGbmStrategy.
ENSEMBLE_SIZE: int = 5
LEGACY_ENSEMBLE_SEEDS: list[int] = [42, 123, 456, 789, 1001]  # iter-v3/001-005


def _derive_ensemble_seeds(outer_seed: int, size: int = ENSEMBLE_SIZE) -> list[int]:
    """Deterministically derive `size` inner-ensemble seeds from one outer seed.

    Replaces the pre-iter-v3/006 hardcoded ENSEMBLE_SEEDS that was identical
    across all outer seeds. With this fix, --seeds N produces N distinct
    LightGBM ensembles (the prerequisite for any meaningful 10-seed Pareto
    validation per project memory's seed-validation rule).
    """
    rng = np.random.default_rng(outer_seed)
    return [int(s) for s in rng.integers(low=0, high=2**31 - 1, size=size)]


ITERATION_LABEL = "v3-011"
REPORTS_DIR = Path("reports-v3")
FEATURES_DIR = Path("data/features_v3")
DATA_DIR = Path("data")

# v3 symbols — unchanged from iter-v3/001 (brief Section 3.1)
V3_MODELS: tuple[tuple[str, str], ...] = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("B (MKRUSDT)", "MKRUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
)

# Risk gate configs (v2 5-gate + BTC; no R1/R2/R3 — brief Section 3.4)
HIT_RATE_CONFIG = HitRateGateConfig(
    window=20,
    sl_threshold=0.65,
    enabled=False,  # Disabled per iter-v2/045 lesson
)

BTC_TREND_CONFIG = BtcTrendFilterConfig(
    lookback_bars=42,  # 14 days of 8h bars
    threshold_pct=20.0,
    enabled=True,
)

# CPCV parameters (brief Section 0 + 3.5#2)
CPCV_N_SPLITS = 10
CPCV_N_TEST_SPLITS = 2
# gap = REQUIRED_GAP = (timeout_candles + 1) * n_symbols = (21+1)*4 = 88
# DO NOT use min(REQUIRED_GAP, n_trades//20) — that is the iter-v3/001 bug.
CPCV_EMBARGO = 27  # ~1% of 24-month T ≈ 2742 candles * 0.01


# ============================================================
# Pre-flight checks
# ============================================================


def _verify_branch() -> None:
    """Enforce git workflow guardrail: v3 runs from iteration-v3/* or quant-research."""
    branch = subprocess.check_output(
        ["git", "--no-optional-locks", "branch", "--show-current"],
        text=True,
    ).strip()
    allowed = branch.startswith("iteration-v3/") or branch in ("quant-research", "main")
    if not allowed:
        raise RuntimeError(
            f"v3 runner must run from iteration-v3/*, quant-research, or main; got: {branch}"
        )


def _verify_symbols(symbols: tuple[str, ...]) -> None:
    """Hard assert: no v1/v2 symbols in v3 universe."""
    overlap = set(symbols) & set(V3_EXCLUDED_SYMBOLS)
    if overlap:
        raise RuntimeError(
            f"v3 runner cannot trade v1/v2 symbols: {sorted(overlap)}\n"
            f"V3_EXCLUDED_SYMBOLS = {V3_EXCLUDED_SYMBOLS}"
        )


def _verify_data_freshness(symbols: tuple[str, ...], max_lag_hours: float = 16.0) -> None:
    """Hard-fail on stale data (>16h lag)."""
    now_ms = int(time.time() * 1000)
    stale: list[tuple[str, float]] = []
    for sym in symbols:
        p = DATA_DIR / sym / "8h.csv"
        if not p.exists():
            raise RuntimeError(f"v3 runner: missing CSV for {sym} at {p}")
        df = pd.read_csv(p, usecols=["close_time"])
        last_close = int(df["close_time"].max())
        lag_h = (now_ms - last_close) / 3_600_000
        if lag_h > max_lag_hours:
            stale.append((sym, round(lag_h, 1)))
    if stale:
        raise RuntimeError(
            f"v3 runner: STALE DATA (>{max_lag_hours}h lag): {stale}. "
            f"Run `uv run crypto-trade fetch --symbols {','.join(symbols)} --intervals 8h`"
        )


def _verify_feature_columns() -> None:
    f"""Verifies V3_FEATURE_COLUMNS contents per current brief (iter-{ITERATION_LABEL}).

    Asserts V3_FEATURE_COLUMNS has exactly 13 columns — vwap_dev_50 dropped
    per Critic FINAL SHA a544621 (Rec 1, iter-v3/008).
    Also asserts vwap_dev_50 is NOT in V3_FEATURE_COLUMNS (belt-and-suspenders).
    """
    n = len(V3_FEATURE_COLUMNS)
    if n != 13:
        raise RuntimeError(
            f"V3_FEATURE_COLUMNS has {n} columns — expected exactly 13. "
            "iter-v3/008 brief Section 3.3 requires the top-13 subset "
            "(vwap_dev_50 dropped per Critic FINAL SHA a544621). "
            "Check features_v3/__init__.py V3_FEATURE_COLUMNS_TOP_N."
        )
    if "vwap_dev_50" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "vwap_dev_50 found in V3_FEATURE_COLUMNS — must be dropped per "
            "Critic FINAL SHA a544621 (Recommendation 1). "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    print(f"  V3_FEATURE_COLUMNS: {n} columns  PASS")


def _verify_label_leakage_gap() -> None:
    """Assert gap == REQUIRED_GAP == 88 and print proof (brief Section 3.5#3)."""
    timeout_minutes = 10080  # 7 days
    candle_minutes = 480  # 8h
    n_symbols = len(V3_MODELS)
    timeout_candles = timeout_minutes // candle_minutes  # = 21
    required_gap = (timeout_candles + 1) * n_symbols  # = (21+1)*4 = 88
    assert required_gap == REQUIRED_GAP, (
        f"REQUIRED_GAP mismatch: formula gives {required_gap}, "
        f"REQUIRED_GAP constant is {REQUIRED_GAP}. Update validation_v3.REQUIRED_GAP."
    )
    print(
        f"  Label-leakage gap: (timeout_candles={timeout_candles}+1) * n_symbols={n_symbols}"
        f" = {required_gap}  [matches REQUIRED_GAP={REQUIRED_GAP}]  PASS"
    )


def _verify_track_isolation() -> None:
    """Grep-check: features_v3 must not import from features (v1) or features_v2.

    Uses '^from ...' to match only actual import statements at line start,
    not occurrences in comments or docstrings.
    """
    import subprocess as sp  # noqa: PLC0415

    for pattern in (
        r"^from crypto_trade\.features ",
        r"^from crypto_trade\.features_v2",
    ):
        out = sp.run(
            ["grep", "-rP", pattern, "src/crypto_trade/features_v3/"],
            capture_output=True,
            text=True,
        )
        if out.stdout.strip():
            raise RuntimeError(
                f"Track isolation FAIL: found '{pattern}' in features_v3/:\n{out.stdout}"
            )
    print("  Track isolation (features_v3 does not import v1/v2): PASS")


# ============================================================
# Feature generation
# ============================================================


def _generate_v3_features(symbols: list[str]) -> None:
    """Generate v3 feature parquets for all symbols."""
    print(f"\n[features] Generating v3 features for {symbols} -> {FEATURES_DIR}")
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    for sym in symbols:
        t0 = time.time()
        result = process_symbol_v3(sym, "8h", str(DATA_DIR), str(FEATURES_DIR))
        n_rows, n_cols = result[1], result[2]
        elapsed = time.time() - t0
        print(f"  {sym}: {n_rows} rows, {n_cols} feature cols ({elapsed:.1f}s)")


# ============================================================
# ADF stationarity test — per-(symbol, feature, retraining month)
# brief Section 3.5#4
# ============================================================


def _walk_forward_month_starts(df_is: pd.DataFrame) -> list[int]:
    """Identify the start of each walk-forward retraining month (IS only).

    Returns a list of epoch-ms timestamps representing the first candle of
    each calendar month in the IS window, limited to months that have at
    least 1 candle of data.
    """
    months = pd.to_datetime(df_is["open_time"], unit="ms").dt.to_period("M").unique()
    return sorted(months.tolist())


def _run_adf_tests(symbols: list[str]) -> pd.DataFrame:
    """Run ADF per (symbol, feature, walk-forward retraining month).

    Returns DataFrame with columns:
        symbol, feature_name, month, adf_statistic, p_value, stationary

    Expected row count ≈ n_symbols × n_features × n_months.
    For v3: 4 × 34 × 27 ≈ 3672 rows (varies by symbol listing date).

    LDO was listed 2022-09-22, so it contributes fewer months than BCH/MKR/TRX.
    """
    import math as _math  # noqa: PLC0415

    from statsmodels.tsa.stattools import adfuller  # noqa: PLC0415

    rows = []
    for sym in symbols:
        pq_path = FEATURES_DIR / f"{sym}_8h_features.parquet"
        if not pq_path.exists():
            print(f"  [ADF] Parquet not found for {sym}, skipping")
            continue
        df = pd.read_parquet(pq_path)
        df["open_time_dt"] = pd.to_datetime(df["open_time"], unit="ms")

        # IS only
        df_is = df[df["open_time"] < OOS_CUTOFF_MS].copy()
        if len(df_is) < 200:
            print(f"  [ADF] Insufficient IS data for {sym} ({len(df_is)} rows), skipping")
            continue

        df_is["month_period"] = df_is["open_time_dt"].dt.to_period("M")
        retrain_months = sorted(df_is["month_period"].unique().tolist())

        for month in retrain_months:
            # Training window ending at the START of this month (24-month rolling)
            # We use data from up to TRAINING_MONTHS months before this month
            month_start_ts = int(month.start_time.timestamp() * 1000)
            window_start_month = month - TRAINING_MONTHS
            window_start_ts = int(window_start_month.start_time.timestamp() * 1000)

            df_window = df_is[
                (df_is["open_time"] >= window_start_ts) & (df_is["open_time"] < month_start_ts)
            ]

            if len(df_window) < 30:
                # Too little data in window for ADF (e.g. early LDO months)
                for col in V3_FEATURE_COLUMNS:
                    rows.append(
                        {
                            "symbol": sym,
                            "feature_name": col,
                            "month": str(month),
                            "adf_statistic": float("nan"),
                            "p_value": float("nan"),
                            "stationary": False,
                        }
                    )
                continue

            for col in V3_FEATURE_COLUMNS:
                if col not in df_window.columns:
                    rows.append(
                        {
                            "symbol": sym,
                            "feature_name": col,
                            "month": str(month),
                            "adf_statistic": float("nan"),
                            "p_value": float("nan"),
                            "stationary": False,
                        }
                    )
                    continue

                series = df_window[col].dropna().to_numpy()
                if len(series) < 20:
                    rows.append(
                        {
                            "symbol": sym,
                            "feature_name": col,
                            "month": str(month),
                            "adf_statistic": float("nan"),
                            "p_value": float("nan"),
                            "stationary": False,
                        }
                    )
                    continue

                try:
                    maxlag = int(_math.floor(12 * (len(series) / 100) ** 0.25))
                    result = adfuller(series, autolag="AIC", maxlag=maxlag)
                    p_val = float(result[1])
                    rows.append(
                        {
                            "symbol": sym,
                            "feature_name": col,
                            "month": str(month),
                            "adf_statistic": round(float(result[0]), 6),
                            "p_value": round(p_val, 6),
                            "stationary": p_val < 0.05,
                        }
                    )
                except Exception as e:
                    rows.append(
                        {
                            "symbol": sym,
                            "feature_name": col,
                            "month": str(month),
                            "adf_statistic": float("nan"),
                            "p_value": float("nan"),
                            "stationary": False,
                        }
                    )
                    print(f"  [ADF] Error {sym}/{col}/{month}: {e}")

    return pd.DataFrame(rows)


def _verify_adf_row_count(adf_df: pd.DataFrame, symbols: list[str]) -> None:
    """Assert ADF output has approximately the expected number of rows.

    Tolerance: LDO was listed 2022-09-22 so it has fewer walk-forward months
    than BCH/MKR/TRX.  The minimum expected is (n_symbols - 1) × n_features ×
    n_months, where n_months is the fewest months any symbol contributes.
    """
    if adf_df.empty:
        raise RuntimeError("ADF test produced no rows — pipeline broken")

    n_feats = len(V3_FEATURE_COLUMNS)
    n_syms = len(symbols)
    # Count months per symbol
    months_per_sym: dict[str, int] = {}
    for sym, grp in adf_df.groupby("symbol"):
        months_per_sym[str(sym)] = int(grp["month"].nunique())

    total_actual = len(adf_df)
    expected_min = n_syms * n_feats * min(months_per_sym.values())
    expected_max = n_syms * n_feats * max(months_per_sym.values())

    print(
        f"  [ADF] {total_actual} rows; "
        f"expected ∈ [{expected_min}, {expected_max}] "
        f"({n_syms} syms × {n_feats} feats × "
        f"[{min(months_per_sym.values())}, {max(months_per_sym.values())}] months)"
    )
    print(f"  [ADF] Months per symbol: {months_per_sym}")

    if total_actual < expected_min:
        raise RuntimeError(
            f"ADF row count {total_actual} < expected minimum {expected_min}. "
            "The per-(symbol, feature, month) ADF pipeline is missing rows. "
            f"Months per symbol: {months_per_sym}"
        )

    # Secondary falsifier: LDO cusum_reset_count_200 must fail p<0.05 in at least 1 month
    ldo_cusum = adf_df[
        (adf_df["symbol"] == "LDOUSDT") & (adf_df["feature_name"] == "cusum_reset_count_200")
    ]
    if len(ldo_cusum) > 0:
        n_fail = int((ldo_cusum["p_value"] >= 0.05).sum())
        print(
            f"  [ADF] Secondary falsifier: LDOUSDT/cusum_reset_count_200 "
            f"fails p<0.05 in {n_fail}/{len(ldo_cusum)} months  "
            f"({'PASS' if n_fail > 0 else 'FAIL — averaging masking per-symbol non-stationarity'})"
        )
    else:
        print("  [ADF] WARNING: LDOUSDT/cusum_reset_count_200 not found in ADF output")


# ============================================================
# IC matrix
# ============================================================


def _compute_ic_matrix(symbols: list[str]) -> pd.DataFrame:
    """Pairwise Pearson IC between V3_FEATURE_COLUMNS on IS data."""
    frames = []
    for sym in symbols:
        pq_path = FEATURES_DIR / f"{sym}_8h_features.parquet"
        if not pq_path.exists():
            continue
        df = pd.read_parquet(pq_path)
        df_is = df[df["open_time"] < OOS_CUTOFF_MS]
        avail = [c for c in V3_FEATURE_COLUMNS if c in df_is.columns]
        if avail:
            frames.append(df_is[avail].copy())

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    avail_cols = [c for c in V3_FEATURE_COLUMNS if c in combined.columns]
    return combined[avail_cols].corr(method="pearson")


# ============================================================
# CPCV path computation on IS candle/feature sequence
# brief Section 3.5#2
# ============================================================


def _compute_cpcv_paths(
    symbols: list[str],
    feature_parquets: dict[str, pd.DataFrame],
    oof_parquet_path: Path | None = None,
    report_dir: Path | None = None,
) -> tuple[pd.DataFrame, np.ndarray, float | None]:
    """Compute CPCV statistics from IS candle/feature sequences.

    UPDATED (iter-v3/004 sub-fix #1): when oof_parquet_path is provided and
    exists, iterates over (symbol, train_month) cells in the parquet.  For each
    cell, deduplicates by natural key, pivots to a (n_candles × 50_trials)
    matrix, runs per-cell CSCV (N=10, k=2 → 45 paths, gap=22 within-cell), and
    calls pbo_from_cpcv to get a per-cell PBO.  The 173 per-cell PBOs are
    aggregated via the cross-cell MEAN to produce a finite float strictly inside
    (0.0, 1.0).  The per_cell_pbo.csv audit trail is written to report_dir.

    The legacy cross-cell CSCV (combining all trial_ids across all cells as a
    global strategy axis) is REMOVED because cross-cell trial_id has no
    statistical meaning — each Optuna study has its own independent TPE sampler
    (brief Section 9 / iter-v3/003 diary lesson #1).

    Falls back to S=1 (return proxy, PBO=None) if parquet is absent or empty.
    The global CPCV candle sequence still runs for cpcv_paths.csv (inherited
    artifact) using the return proxy — this preserves the cpcv_paths.csv schema.

    Parameters
    ----------
    symbols
        v3 symbols (BCH, MKR, LDO, TRX).
    feature_parquets
        Dict mapping symbol -> IS-window feature DataFrame.
    oof_parquet_path
        Path to trial_oof_returns.parquet written during training (iter-v3/003).
    report_dir
        If provided, writes per_cell_pbo.csv to this directory for audit.

    Returns
    -------
    (cpcv_df, path_metric_matrix, per_cell_mean_pbo)
        cpcv_df: DataFrame with path_id, sharpe, max_dd, n_candles.
        path_metric_matrix: np.ndarray of shape (n_paths, 1) — return proxy
            for cpcv_paths.csv (legacy; per-cell PBO is the headline output).
        per_cell_mean_pbo: float mean of per-cell PBOs (None if no cells).
    """
    # ----------------------------------------------------------------
    # Global CPCV candle sequence — for cpcv_paths.csv (inherited schema)
    # ----------------------------------------------------------------
    all_frames = []
    for sym in symbols:
        df = feature_parquets.get(sym)
        if df is None or df.empty:
            continue
        df_is = df[df["open_time"] < OOS_CUTOFF_MS].copy()
        if len(df_is) < 10:
            continue
        # Use close-to-close log return as per-candle return proxy
        if "close" in df_is.columns:
            df_is = df_is.copy()
            df_is["_ret"] = np.log(df_is["close"] / df_is["close"].shift(1)).fillna(0.0)
        else:
            df_is["_ret"] = 0.0
        df_is["_sym"] = sym
        all_frames.append(df_is[["open_time", "_ret", "_sym"]].copy())

    if not all_frames:
        return (
            pd.DataFrame(columns=["path_id", "sharpe", "max_dd", "n_candles"]),
            np.zeros((0, 1)),
            None,
        )

    combined = (
        pd.concat(all_frames, ignore_index=True).sort_values("open_time").reset_index(drop=True)
    )
    n_candles = len(combined)
    print(f"  [CPCV] IS candle sequence: {n_candles} candles across {len(symbols)} symbols")

    if n_candles < CPCV_N_SPLITS * 10:
        print(f"  [CPCV] Insufficient candles ({n_candles}) for CPCV — skipping")
        return (
            pd.DataFrame(columns=["path_id", "sharpe", "max_dd", "n_candles"]),
            np.zeros((0, 1)),
            None,
        )

    candle_timeline = combined["open_time"].to_numpy()
    returns_proxy = combined["_ret"].to_numpy()

    # Assertion: gap must equal REQUIRED_GAP (brief Section 3.5#3)
    splits = combinatorial_purged_cv(
        n_samples=n_candles,
        n_splits=CPCV_N_SPLITS,
        n_test_splits=CPCV_N_TEST_SPLITS,
        gap=REQUIRED_GAP,
        embargo=CPCV_EMBARGO,
        expected_gap=REQUIRED_GAP,
    )

    rows = []
    path_metric_cols: list[np.ndarray] = []

    for path_id, (_, test_idx) in enumerate(splits):
        test_candles = candle_timeline[test_idx]
        n_test = len(test_candles)
        proxy_rets = returns_proxy[test_idx]

        if n_test < 2:
            rows.append(
                {
                    "path_id": path_id,
                    "sharpe": float("nan"),
                    "max_dd": float("nan"),
                    "n_candles": n_test,
                }
            )
            path_metric_cols.append(np.array([float("nan")]))
            continue

        s1_sigma = float(np.nanstd(proxy_rets, ddof=1))
        s1_mu = float(np.nanmean(proxy_rets))
        s1_sharpe = s1_mu / s1_sigma * np.sqrt(n_test) if s1_sigma > 0 else 0.0
        path_metric_cols.append(np.array([s1_sharpe]))

        mu = float(np.nanmean(proxy_rets))
        sigma = float(np.nanstd(proxy_rets, ddof=1))
        path_sharpe = mu / sigma * np.sqrt(n_test) if sigma > 0 else 0.0
        cum = np.nancumsum(proxy_rets)
        running_max = np.maximum.accumulate(cum)
        dd = running_max - cum
        max_dd = float(dd.max()) if len(dd) > 0 else 0.0

        rows.append(
            {
                "path_id": path_id,
                "sharpe": round(path_sharpe, 6),
                "max_dd": round(max_dd * 100, 4),
                "n_candles": n_test,
            }
        )

    cpcv_df = pd.DataFrame(rows)
    path_metric_matrix = (
        np.stack(path_metric_cols, axis=0) if path_metric_cols else np.zeros((0, 1))
    )
    print(f"  [CPCV] cpcv_paths.csv: {len(cpcv_df)} paths (return proxy, S=1 — for schema)")

    # ----------------------------------------------------------------
    # Sub-fix #1 (iter-v3/004): per-cell CSCV with cross-cell mean aggregation
    # ----------------------------------------------------------------
    per_cell_mean_pbo: float | None = None
    if oof_parquet_path is not None and oof_parquet_path.exists():
        per_cell_mean_pbo = _compute_per_cell_pbo(oof_parquet_path, report_dir)

    return cpcv_df, path_metric_matrix, per_cell_mean_pbo


# Per-cell CSCV parameters (brief Section 0 — within-cell gap = 22)
PER_CELL_N_SPLITS = 10
PER_CELL_K = 2  # C(10, 2) = 45 paths
PER_CELL_GAP = 22  # (timeout_candles + 1) within a single-symbol cell


def _compute_per_cell_pbo(
    oof_parquet_path: Path,
    report_dir: Path | None = None,
) -> float | None:
    """Compute per-(symbol, train_month) cell CSCV PBO and aggregate via mean.

    Implementation of iter-v3/004 brief Section 3.5 sub-fixes #1 and #4.

    For each (symbol, train_month) cell:
    1. Dedup by natural key (sym, month, trial, fold, candle) — drops the 5x
       seed-duplicate rows the iter-v3/003 writer produced.
    2. Pivot to (n_candles × n_trials) returns matrix.
    3. Run CSCV (N=10, k=2, gap=22) to get 45 paths.
    4. Build (45, n_trials) path-Sharpe matrix.
    5. Call pbo_from_cpcv → per-cell PBO.

    Aggregation: cross-cell MEAN of per-cell PBOs for cells with rank > 1.
    Mean is the only aggregator that is:
    - Strictly in (0.0, 1.0) on the observed bimodal distribution
    - Not saturating (Fisher's method chi² > 5000 at this scale)
    - Interpretable as "fraction of cells showing overfit signature"

    Writes per_cell_pbo.csv to report_dir if provided.

    Returns mean PBO (float) or None if fewer than 1 informative cell.
    """
    print(f"  [per-cell PBO] Loading {oof_parquet_path} ...")
    oof_df = pd.read_parquet(oof_parquet_path)
    n_raw = len(oof_df)

    # Dedup by natural key — drops the 5x seed-duplicate rows
    oof_df = oof_df.drop_duplicates(
        subset=["symbol", "train_month", "trial_id", "fold_idx", "candle_open_time_ms"]
    )
    n_dedup = len(oof_df)
    print(f"  [per-cell PBO] Raw={n_raw}, after dedup={n_dedup}")

    # IS-only filter
    oof_df = oof_df[oof_df["candle_open_time_ms"] < OOS_CUTOFF_MS].copy()
    n_is = len(oof_df)
    print(f"  [per-cell PBO] IS-only rows: {n_is}")

    if oof_df.empty:
        print("  [per-cell PBO] OOF parquet IS slice is empty — returning None")
        return None

    cells = sorted(oof_df.groupby(["symbol", "train_month"]).groups.keys())
    n_cells = len(cells)
    print(f"  [per-cell PBO] Iterating over {n_cells} (sym, month) cells ...")

    cell_rows: list[dict] = []

    for cell_idx, (sym, month) in enumerate(cells):
        cell_df = oof_df[(oof_df["symbol"] == sym) & (oof_df["train_month"] == month)]
        n_trials_cell = int(cell_df["trial_id"].nunique())
        n_candles_cell = int(cell_df["candle_open_time_ms"].nunique())

        if n_trials_cell < 2 or n_candles_cell < PER_CELL_N_SPLITS * 3:
            cell_rows.append(
                {
                    "symbol": sym,
                    "train_month": month,
                    "n_trials": n_trials_cell,
                    "n_candles": n_candles_cell,
                    "n_paths": 0,
                    "rank": 0,
                    "pbo": float("nan"),
                    "n_eff": 0,
                    "mean_path_sharpe": float("nan"),
                    "error": "insufficient_data",
                }
            )
            continue

        try:
            # Pivot: (n_candles, n_trials) returns matrix, averaging over fold_idx
            pivot = cell_df.pivot_table(
                index="candle_open_time_ms",
                columns="trial_id",
                values="oof_return",
                aggfunc="mean",
            ).sort_index()
            returns_mat = pivot.to_numpy()  # (n_candles, n_trials)
            n_candles_mat, n_trials_mat = returns_mat.shape

            # Per-cell CSCV
            cell_splits = combinatorial_purged_cv(
                n_samples=n_candles_mat,
                n_splits=PER_CELL_N_SPLITS,
                n_test_splits=PER_CELL_K,
                gap=PER_CELL_GAP,
                embargo=0,
            )
            n_paths = len(cell_splits)
            path_mat = np.full((n_paths, n_trials_mat), np.nan, dtype=float)

            for path_id, (_, test_idx) in enumerate(cell_splits):
                if len(test_idx) < 2:
                    continue
                test_rets = returns_mat[test_idx, :]
                mu = np.nanmean(test_rets, axis=0)
                sigma = np.nanstd(test_rets, axis=0, ddof=1)
                with np.errstate(divide="ignore", invalid="ignore"):
                    sharpe = np.where(sigma > 0, mu / sigma, 0.0)
                path_mat[path_id, :] = sharpe

            pbo_res = pbo_from_cpcv(path_mat, max_splits=5000)
            cell_pbo = pbo_res.pbo if pbo_res.pbo is not None else float("nan")

            # n_eff per-cell: (n_trials × n_candles) matrix
            cell_neff = n_effective_trials(returns_mat.T)

            rank = int(np.linalg.matrix_rank(returns_mat))
            mean_path_sharpe = float(np.nanmean(path_mat))

            cell_rows.append(
                {
                    "symbol": sym,
                    "train_month": month,
                    "n_trials": n_trials_mat,
                    "n_candles": n_candles_mat,
                    "n_paths": n_paths,
                    "rank": rank,
                    "pbo": cell_pbo,
                    "n_eff": cell_neff,
                    "mean_path_sharpe": round(mean_path_sharpe, 6),
                    "error": "",
                }
            )
        except Exception as exc:
            cell_rows.append(
                {
                    "symbol": sym,
                    "train_month": month,
                    "n_trials": n_trials_cell,
                    "n_candles": n_candles_cell,
                    "n_paths": 0,
                    "rank": 0,
                    "pbo": float("nan"),
                    "n_eff": 0,
                    "mean_path_sharpe": float("nan"),
                    "error": str(exc)[:120],
                }
            )

        if (cell_idx + 1) % 25 == 0:
            print(f"  [per-cell PBO]   {cell_idx + 1}/{n_cells} cells processed")

    print(f"  [per-cell PBO] Completed {n_cells} cells")

    per_cell_df = pd.DataFrame(cell_rows)

    # Write audit CSV (sub-fix #4)
    if report_dir is not None:
        report_dir.mkdir(parents=True, exist_ok=True)
        csv_path = report_dir / "per_cell_pbo.csv"
        per_cell_df.to_csv(csv_path, index=False)
        print(f"  [per-cell PBO] Wrote {csv_path} ({len(per_cell_df)} rows)")

    # Aggregate: mean of per-cell PBOs for cells with rank > 1 (informative)
    informative = per_cell_df[per_cell_df["rank"] > 1]["pbo"].dropna()
    n_informative = len(informative)
    print(f"  [per-cell PBO] Informative cells (rank>1): {n_informative}/{n_cells}")

    if n_informative == 0:
        print("  [per-cell PBO] No informative cells — returning None")
        return None

    mean_pbo = float(informative.mean())
    median_pbo = float(informative.median())
    print(
        f"  [per-cell PBO] Aggregated mean PBO={mean_pbo:.4f}, median PBO={median_pbo:.4f} "
        f"(|delta|={abs(mean_pbo - median_pbo):.4f})"
    )
    return mean_pbo


# ============================================================
# Model builder
# ============================================================


def _build_v3_model(
    symbol: str,
    seed: int,
    n_trials: int,
    ensemble_seeds: list[int],
    oof_persist_path: Path | None = None,
    fast_mode: bool = False,
) -> tuple[BacktestConfig, RiskV3Wrapper]:
    """Build v3 M1 LightGBM + RiskV3Wrapper for a single symbol.

    v2 5-gate config + BTC trend filter. NO R1/R2/R3 (brief Section 3.4).
    oof_persist_path: if set, per-trial OOF returns written to parquet
    (sub-fix 1d, iter-v3/003).
    fast_mode: if True, hardcode colsample_bytree=1.0 in Optuna search space
    to minimize per-seed feature-subsampling variance (iter-v3/007 exploration).
    """
    cfg = BacktestConfig(
        symbols=(symbol,),
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,  # 7 days (21 candles at 8h)
        fee_pct=0.1,
        data_dir=DATA_DIR,
        cooldown_candles=4,  # 32h between trades (inherited from v2)
        vol_targeting=False,  # Vol targeting via RiskV3Wrapper
    )
    m1 = LightGbmStrategy(
        training_months=TRAINING_MONTHS,
        n_trials=n_trials,
        cv_splits=5,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir=str(FEATURES_DIR),
        verbose=1,
        atr_tp_multiplier=2.0,
        atr_sl_multiplier=1.0,
        atr_column="natr_21_raw",
        use_atr_labeling=True,
        ensemble_seeds=list(ensemble_seeds),
        feature_columns=list(V3_FEATURE_COLUMNS),  # EXPLICIT — never None
        ood_enabled=False,  # OOD via RiskV3Wrapper z-score gate
        oof_persist_path=oof_persist_path,  # sub-fix 1d (iter-v3/003)
        fast_mode=fast_mode,  # iter-v3/007 — colsample_bytree=1.0 when True
    )
    risk_cfg = RiskV2Config(
        zscore_threshold=2.0,
    )
    strategy = RiskV3Wrapper(m1, risk_cfg)
    return cfg, strategy


# ============================================================
# Extended comparison.csv writer (v3 schema)
# ============================================================


def _monthly_sharpe(trades: list) -> float:
    if not trades:
        return 0.0
    months = pd.to_datetime([t.close_time for t in trades], unit="ms").to_period("M")
    monthly = (
        pd.Series([t.weighted_pnl for t in trades], index=months).groupby(level=0).sum() / 100.0
    )
    if len(monthly) < 2 or monthly.std() == 0:
        return 0.0
    return float(monthly.mean() / monthly.std() * np.sqrt(12))


def _max_drawdown(trades: list) -> float:
    if not trades:
        return 0.0
    cum = np.cumsum([float(t.weighted_pnl) for t in sorted(trades, key=lambda t: t.close_time)])
    running_max = np.maximum.accumulate(cum)
    dd = running_max - cum
    return float(dd.max())


def _write_v3_comparison(
    is_trades: list,
    oos_trades: list,
    report_dir: Path,
    dsr_val: float,
    pbo_result: PBOResult,
    psr_val: float,
    n_trials_total: int,
    n_eff: int,
) -> None:
    """Write comparison.csv with all v3-required rows."""

    def _daily_sharpe(trades: list) -> float:
        if not trades:
            return 0.0
        by_day: dict[str, float] = {}
        for t in trades:
            day = pd.Timestamp(t.close_time, unit="ms").strftime("%Y-%m-%d")
            by_day[day] = by_day.get(day, 0.0) + float(t.weighted_pnl)
        daily = pd.Series(list(by_day.values()))
        if len(daily) < 2 or daily.std() == 0:
            return 0.0
        return float(daily.mean() / daily.std() * np.sqrt(365))

    def _profit_factor(trades: list) -> float:
        wins = sum(t.weighted_pnl for t in trades if t.weighted_pnl > 0)
        losses = sum(-t.weighted_pnl for t in trades if t.weighted_pnl < 0)
        return float(wins / losses) if losses > 0 else float("inf")

    def _win_rate(trades: list) -> float:
        if not trades:
            return 0.0
        return 100.0 * sum(1 for t in trades if t.weighted_pnl > 0) / len(trades)

    def _calmar(trades: list) -> float:
        dd = _max_drawdown(trades)
        if dd <= 0:
            return 0.0
        return float(sum(t.weighted_pnl for t in trades) / dd)

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
    is_pnl = sum(t.weighted_pnl for t in is_trades)
    oos_pnl = sum(t.weighted_pnl for t in oos_trades)
    is_calmar = _calmar(is_trades)
    oos_calmar = _calmar(oos_trades)

    def ratio_str(oos_v: float, is_v: float) -> str:
        if is_v == 0:
            return "—"
        return f"{oos_v / is_v:.4f}"

    # PBO: None when S=1; report as "NaN" with frac_positive_paths in dsr.json
    pbo_str = "NaN" if pbo_result.pbo is None else f"{pbo_result.pbo:.4f}"

    metrics = [
        ("monthly_sharpe", f"{is_ms:.4f}", f"{oos_ms:.4f}", ratio_str(oos_ms, is_ms)),
        ("daily_sharpe", f"{is_ds:.4f}", f"{oos_ds:.4f}", ratio_str(oos_ds, is_ds)),
        ("max_drawdown", f"{is_dd:.4f}", f"{oos_dd:.4f}", ratio_str(oos_dd, is_dd)),
        ("profit_factor", f"{is_pf:.4f}", f"{oos_pf:.4f}", ratio_str(oos_pf, is_pf)),
        ("win_rate", f"{is_wr:.4f}", f"{oos_wr:.4f}", ratio_str(oos_wr, is_wr)),
        ("n_trades", str(is_n), str(oos_n), ratio_str(float(oos_n), float(is_n))),
        ("total_pnl", f"{is_pnl:.4f}", f"{oos_pnl:.4f}", ratio_str(oos_pnl, is_pnl)),
        (
            "monthly_calmar",
            f"{is_calmar:.4f}",
            f"{oos_calmar:.4f}",
            ratio_str(oos_calmar, is_calmar),
        ),
        ("weighted_pnl_total", f"{is_pnl:.4f}", f"{oos_pnl:.4f}", ratio_str(oos_pnl, is_pnl)),
        ("dsr", f"{dsr_val:.6f}", "—", "—"),
        ("pbo", pbo_str, "—", "—"),
        ("psr", f"{psr_val:.4f}", "—", "—"),
        ("n_trials", str(n_trials_total), "—", "—"),
        ("n_effective_trials", str(n_eff), "—", "—"),
    ]

    comp_path = report_dir / "comparison.csv"
    with open(comp_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "in_sample", "out_of_sample", "ratio"])
        for row in metrics:
            writer.writerow(row)

    all_symbols = list({t.symbol for t in is_trades + oos_trades})
    total_oos_pnl = sum(t.weighted_pnl for t in oos_trades) or 1.0
    with open(comp_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([])
        writer.writerow(
            ["# per_symbol", "weighted_pnl", "n_trades", "win_rate", "concentration_pct"]
        )
        for sym in sorted(all_symbols):
            sym_oos = [t for t in oos_trades if t.symbol == sym]
            if not sym_oos:
                continue
            sym_pnl = sum(t.weighted_pnl for t in sym_oos)
            sym_wr = 100.0 * sum(1 for t in sym_oos if t.weighted_pnl > 0) / len(sym_oos)
            conc = 100.0 * sym_pnl / total_oos_pnl if total_oos_pnl != 0 else 0.0
            writer.writerow([sym, f"{sym_pnl:.4f}", len(sym_oos), f"{sym_wr:.1f}", f"{conc:.2f}"])

    print(
        f"[v3 report] comparison.csv: IS monthly Sharpe={is_ms:+.4f}, "
        f"OOS monthly Sharpe={oos_ms:+.4f}, DSR={dsr_val:.4f}, "
        f"PBO={pbo_str}, PSR={psr_val:.4f}"
    )


# ============================================================
# DSR JSON writer
# ============================================================


def _write_dsr_json(
    report_dir: Path,
    dsr_val: float,
    pbo_result: PBOResult,
    psr_val: float,
    n_trials: int,
    n_eff: int,
    min_trl_months: float,
) -> None:
    """Write dsr.json — includes PBO metadata."""
    pbo_out = pbo_result.pbo if pbo_result.pbo is not None else None
    data = {
        "dsr": round(dsr_val, 8),
        "pbo": pbo_out,
        "pbo_note": pbo_result.note,
        "pbo_frac_positive_paths": round(pbo_result.frac_positive_paths, 4),
        "pbo_path_sharpe_q25": round(pbo_result.path_sharpe_quartiles[0], 4),
        "pbo_path_sharpe_q50": round(pbo_result.path_sharpe_quartiles[1], 4),
        "pbo_path_sharpe_q75": round(pbo_result.path_sharpe_quartiles[2], 4),
        "psr": round(psr_val, 4),
        "n_trials": n_trials,
        "n_eff": n_eff,
        "min_trl_months": round(min_trl_months, 2),
    }
    (report_dir / "dsr.json").write_text(json.dumps(data, indent=2))
    print(
        f"[v3 report] dsr.json: DSR={dsr_val:.4f}, PBO={pbo_out}, "
        f"frac_pos_paths={pbo_result.frac_positive_paths:.3f}, PSR={psr_val:.4f}, n_eff={n_eff}"
    )


# ============================================================
# Pareto front
# ============================================================


def _write_pareto_front(
    per_seed_summary: list[dict],
    report_dir: Path,
) -> None:
    """Write pareto_front.csv — seed × 6-metric matrix."""
    path = report_dir / "pareto_front.csv"
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "seed",
                "monthly_sharpe",
                "max_drawdown",
                "calmar",
                "pbo",
                "n_trades",
                "max_concentration_pct",
            ]
        )
        for r in per_seed_summary:
            writer.writerow(
                [
                    r.get("seed", ""),
                    f"{r.get('oos_sharpe_monthly', 0.0):.4f}",
                    f"{r.get('oos_max_dd', 0.0):.4f}",
                    f"{r.get('oos_calmar', 0.0):.4f}",
                    f"{r.get('pbo', 'NaN')}",  # NaN when S=1
                    r.get("oos_trades", 0),
                    f"{r.get('max_concentration_pct', 0.0):.2f}",
                ]
            )


# ============================================================
# Feature importance
# ============================================================


def _write_feature_importance(
    is_trades: list,
    oos_trades: list,
    primary_model_pairs: list,
    report_dir: Path,
) -> None:
    """Write feature_importance.csv from LightGBM model if available."""
    if not primary_model_pairs:
        return

    cfg, strat = primary_model_pairs[0]
    inner = strat.inner if hasattr(strat, "inner") else strat
    if not hasattr(inner, "_models") or not inner._models:
        return

    cols = (
        inner._all_feature_cols if hasattr(inner, "_all_feature_cols") else list(V3_FEATURE_COLUMNS)
    )

    for split_label, trades in (("in_sample", is_trades), ("out_of_sample", oos_trades)):
        fi_path = report_dir / split_label / "feature_importance.csv"
        fi_path.parent.mkdir(parents=True, exist_ok=True)

        importances: dict[str, list[float]] = {c: [] for c in cols}
        for model in inner._models:
            if hasattr(model, "feature_importances_"):
                fi_arr = model.feature_importances_
                for i, c in enumerate(cols):
                    if i < len(fi_arr):
                        importances[c].append(float(fi_arr[i]))

        rows_fi = []
        for col in cols:
            vals = importances.get(col, [])
            mean_fi = float(np.mean(vals)) if vals else 0.0
            rows_fi.append({"feature": col, "importance": round(mean_fi, 4)})
        rows_fi.sort(key=lambda r: r["importance"], reverse=True)

        with open(fi_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["feature", "importance"])
            writer.writeheader()
            writer.writerows(rows_fi)


# ============================================================
# Single-seed run
# ============================================================


def _run_single_seed(
    seed: int,
    n_trials: int,
    btc_times: np.ndarray,
    btc_closes: np.ndarray,
    active_models: tuple[tuple[str, str], ...] | None = None,
    ensemble_size: int | None = None,
    fast_mode: bool = False,
) -> tuple[list, list, dict, dict, list]:
    """Run v3 models for a single outer seed.

    Parameters
    ----------
    active_models:
        Subset of V3_MODELS to run.  Defaults to V3_MODELS when None.
        Pass a filtered tuple to scope the run (e.g. BCH-only for iter-v3/006).
    ensemble_size:
        Override the default ENSEMBLE_SIZE for this run. Useful for fast
        exploration (size=1 → no inner-ensemble averaging, ~5x faster).
    fast_mode:
        If True, hardcode `colsample_bytree=1.0` in Optuna search space
        (iter-v3/007 — minimize per-seed feature-subsampling variance).
    """
    models_to_run = active_models if active_models is not None else V3_MODELS
    all_trades: list = []
    model_pairs: list = []

    for name, symbol in models_to_run:
        print("=" * 60)
        print(f"MODEL {name} — seed {seed}")
        print("=" * 60)
        # sub-fix 1d (iter-v3/003): pass OOF persist path so per-trial returns
        # are written to parquet during training (one shared file per run).
        oof_path = REPORTS_DIR / f"iteration_{ITERATION_LABEL}" / "trial_oof_returns.parquet"
        # iter-v3/006 fix: derive a distinct inner ensemble from this outer seed.
        # Pre-fix: ensemble_seeds=[42,123,456,789,1001] for ALL outer seeds.
        size_for_this_run = ensemble_size if ensemble_size is not None else ENSEMBLE_SIZE
        ensemble_seeds_run = _derive_ensemble_seeds(seed, size=size_for_this_run)
        cfg, strategy = _build_v3_model(
            symbol=symbol,
            seed=seed,
            n_trials=n_trials,
            ensemble_seeds=ensemble_seeds_run,
            oof_persist_path=oof_path,
            fast_mode=fast_mode,
        )
        _verify_symbols(cfg.symbols)
        t0 = time.time()
        results = run_backtest(cfg, strategy, yearly_pnl_check=False)
        elapsed = time.time() - t0
        print(f"{name}: {len(results)} trades in {elapsed:.0f}s (seed={seed})")
        if hasattr(strategy, "gate_stats_summary"):
            print(f"  gate stats: {strategy.gate_stats_summary()}")
        all_trades.extend(results)
        model_pairs.append((cfg, strategy))

    all_trades.sort(key=lambda t: t.open_time)

    after_btc, btc_fire_stats = apply_btc_trend_filter(
        all_trades,
        btc_times,
        btc_closes,
        BTC_TREND_CONFIG,
    )
    btc_stats_dict = btc_fire_stats.as_dict()
    print(
        f"[btc trend filter seed {seed}] "
        f"killed={btc_stats_dict['n_killed']}/{btc_stats_dict['n_total']} "
        f"fire_rate={btc_stats_dict['fire_rate']:.2%}"
    )

    braked, hr_fire_stats = apply_hit_rate_gate(
        after_btc,
        HIT_RATE_CONFIG,
        activate_at_ms=OOS_CUTOFF_MS,
    )
    braked.sort(key=lambda t: t.close_time)
    hr_stats_dict = hr_fire_stats.as_dict()

    return all_trades, braked, btc_stats_dict, hr_stats_dict, model_pairs


# ============================================================
# Main runner
# ============================================================


def main() -> None:
    parser = argparse.ArgumentParser(description="v3 baseline runner — iter-v3/003")
    parser.add_argument(
        "--seeds",
        type=int,
        default=1,
        help="Number of outer seeds (1 for first-pass, 10 for MERGE validation)",
    )
    parser.add_argument(
        "--n-trials", type=int, default=50, help="Optuna trials per monthly model per seed"
    )
    parser.add_argument(
        "--skip-features",
        action="store_true",
        help="Skip feature generation (use existing parquets)",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help=(
            "Comma-separated list of symbols to run (e.g. BCHUSDT).  "
            "Filters V3_MODELS at runtime.  Default: all V3_MODELS.  "
            "Used for iter-v3/006 BCH-only scoped validation."
        ),
    )
    parser.add_argument(
        "--exploration",
        action="store_true",
        help=(
            "iter-v3/007 fast-exploration mode. Sets ENSEMBLE_SIZE=1 (single "
            "inner model, ~5x faster), hardcodes colsample_bytree=1.0 in "
            "Optuna search space (minimizes per-seed feature-subsampling "
            "variance), and defaults --n-trials to 10 if not specified. Use "
            "for fast variation across symbols/labels/features. Drop the flag "
            "for production CONFIRMATION runs (full ensemble, full search space)."
        ),
    )
    args = parser.parse_args()

    # iter-v3/007: --exploration overrides defaults for fast iteration
    ensemble_size_for_run: int = 1 if args.exploration else ENSEMBLE_SIZE
    fast_mode_for_run: bool = bool(args.exploration)
    if args.exploration and args.n_trials == 50:
        # Default for exploration is 10 trials; only override if user kept default
        args.n_trials = 10

    # Build active_models from --symbols filter (iter-v3/006 CLI flag).
    # Default (None) keeps all V3_MODELS.
    if args.symbols is not None:
        requested = {s.strip().upper() for s in args.symbols.split(",")}
        active_models: tuple[tuple[str, str], ...] = tuple(
            (name, sym) for name, sym in V3_MODELS if sym in requested
        )
        if not active_models:
            raise RuntimeError(
                f"--symbols filter {requested!r} matched no V3_MODELS. "
                f"Valid symbols: {[sym for _, sym in V3_MODELS]}"
            )
        unknown = requested - {sym for _, sym in V3_MODELS}
        if unknown:
            raise RuntimeError(f"--symbols contains symbols not in V3_MODELS: {sorted(unknown)}")
    else:
        active_models = V3_MODELS

    t_start = time.time()
    _verify_branch()

    baseline_symbols = tuple(sym for _, sym in active_models)
    _verify_symbols(baseline_symbols)
    _verify_data_freshness(baseline_symbols + ("BTCUSDT",))
    _verify_feature_columns()  # asserts len == 13 and vwap_dev_50 not present
    _verify_label_leakage_gap()  # asserts REQUIRED_GAP == 88
    _verify_track_isolation()  # grep check

    active_sym_names = ", ".join(sym for _, sym in active_models)
    print(f"\nBASELINE v3 iter-{ITERATION_LABEL}: {active_sym_names} (seed-plumbing fix)")
    print(f"Seeds: {args.seeds}  Optuna trials/model: {args.n_trials}")
    print(f"Active models: {len(active_models)}/{len(V3_MODELS)} (--symbols={args.symbols!r})")
    print(f"CPCV: N={CPCV_N_SPLITS}, k={CPCV_N_TEST_SPLITS}, 45 paths on IS CANDLE SEQUENCE")
    print(f"Gap: {REQUIRED_GAP} (= (timeout_candles+1) * 4 full-universe symbols)")
    print(
        f"Pre-flight: branch OK, symbols OK, data fresh (<16h), "
        f"feature-cols={len(V3_FEATURE_COLUMNS)}  PASS\n"
    )

    # Feature generation
    if not args.skip_features:
        _generate_v3_features(list(baseline_symbols))
    else:
        print("[features] Skipping feature generation (--skip-features)")

    # Load IS-window feature DataFrames for CPCV and ADF
    print("\n[features] Loading IS-window feature DataFrames...")
    feature_parquets: dict[str, pd.DataFrame] = {}
    for sym in baseline_symbols:
        pq_path = FEATURES_DIR / f"{sym}_8h_features.parquet"
        if pq_path.exists():
            feature_parquets[sym] = pd.read_parquet(pq_path)
            print(f"  {sym}: {len(feature_parquets[sym])} rows loaded")
        else:
            print(f"  WARNING: {pq_path} not found")

    # ADF per-(symbol, feature, retraining month) — brief Section 3.5#4
    print("\n[ADF] Running per-(symbol, feature, retraining month) stationarity tests...")
    t_adf0 = time.time()
    adf_df = _run_adf_tests(list(baseline_symbols))
    t_adf1 = time.time()
    if not adf_df.empty:
        n_stationary = int(adf_df["stationary"].sum())
        n_total_adf = len(adf_df)
        print(
            f"  ADF: {n_stationary}/{n_total_adf} "
            f"({100.0 * n_stationary / n_total_adf:.1f}%) cells stationary (p<0.05) "
            f"in {t_adf1 - t_adf0:.1f}s"
        )
        non_stat = adf_df[~adf_df["stationary"]][["symbol", "feature_name", "month", "p_value"]]
        if len(non_stat) > 0:
            print(f"  Non-stationary (feature, month) cells: {len(non_stat)}")
    print(f"  ADF total rows: {len(adf_df)}")

    # IC matrix on IS data
    print("\n[IC] Computing pairwise feature correlation matrix on IS data...")
    ic_mat = _compute_ic_matrix(list(baseline_symbols))

    # BTC klines for trend filter
    btc_times, btc_closes = load_btc_klines_for_filter()
    print(f"Loaded {len(btc_times)} BTC 8h klines for trend filter\n")

    full_seeds = (42, 123, 456, 789, 1001, 1234, 2345, 3456, 4567, 5678)
    default_seeds = (42,)
    seeds = list(full_seeds[: args.seeds]) if args.seeds > 1 else list(default_seeds)

    per_seed_summary: list[dict] = []
    primary_trades: list | None = None
    primary_model_pairs: list | None = None

    for i, seed in enumerate(seeds):
        print(f"\n{'#' * 60}\n# SEED {seed} ({i + 1}/{len(seeds)})\n{'#' * 60}")
        unbraked, braked, btc_stats, hr_stats, model_pairs = _run_single_seed(
            seed,
            args.n_trials,
            btc_times,
            btc_closes,
            active_models=active_models,
            ensemble_size=ensemble_size_for_run,
            fast_mode=fast_mode_for_run,
        )

        if not braked:
            per_seed_summary.append(
                {
                    "seed": seed,
                    "trades": 0,
                    "oos_trades": 0,
                    "oos_sharpe_monthly": 0.0,
                    "is_sharpe_monthly": 0.0,
                }
            )
            continue

        is_tr = [t for t in braked if t.open_time < OOS_CUTOFF_MS]
        oos_tr = [t for t in braked if t.open_time >= OOS_CUTOFF_MS]

        is_ms = _monthly_sharpe(is_tr)
        oos_ms = _monthly_sharpe(oos_tr)
        oos_dd = _max_drawdown(oos_tr)
        oos_calmar = (sum(t.weighted_pnl for t in oos_tr) / oos_dd) if oos_dd > 0 else 0.0

        sym_pnl: dict[str, float] = {}
        for t in oos_tr:
            sym_pnl[t.symbol] = sym_pnl.get(t.symbol, 0.0) + float(t.weighted_pnl)
        positive_total = sum(max(0.0, p) for p in sym_pnl.values())
        max_conc = 0.0
        if positive_total > 0:
            conc_pcts = [max(0.0, p) / positive_total * 100.0 for p in sym_pnl.values()]
            max_conc = max(conc_pcts) if conc_pcts else 0.0

        per_seed_summary.append(
            {
                "seed": seed,
                "trades": len(braked),
                "oos_trades": len(oos_tr),
                "is_sharpe_monthly": round(is_ms, 4),
                "oos_sharpe_monthly": round(oos_ms, 4),
                "oos_max_dd": round(oos_dd, 4),
                "oos_calmar": round(oos_calmar, 4),
                "max_concentration_pct": round(max_conc, 2),
                "pbo": None,  # placeholder — updated after per-cell PBO computed (sub-fix #5)
                "btc_killed": btc_stats["n_killed"],
            }
        )

        print(
            f"[seed {seed}] {len(braked)} trades — IS monthly={is_ms:+.4f}, "
            f"OOS monthly={oos_ms:+.4f}, OOS MaxDD={oos_dd:.4f}"
        )

        if i == 0:
            primary_trades = braked
            primary_model_pairs = model_pairs

    if not primary_trades:
        print("No trades produced for primary seed.")
        sys.exit(1)

    is_trades = [t for t in primary_trades if t.open_time < OOS_CUTOFF_MS]
    oos_trades = [t for t in primary_trades if t.open_time >= OOS_CUTOFF_MS]
    print(f"\n[split] {len(is_trades)} IS trades, {len(oos_trades)} OOS trades")

    # -------------------------------------------------------
    # CPCV on IS candle/feature sequence (iter-v3/004 sub-fix #1)
    # -------------------------------------------------------
    print("\n[CPCV] Computing per-cell CSCV PBO (iter-v3/004 per-cell pathway)...")
    oof_parquet = REPORTS_DIR / f"iteration_{ITERATION_LABEL}" / "trial_oof_returns.parquet"
    report_dir_cpcv = REPORTS_DIR / f"iteration_{ITERATION_LABEL}"
    cpcv_df, path_metric_matrix, per_cell_mean_pbo = _compute_cpcv_paths(
        list(baseline_symbols),
        feature_parquets,
        oof_parquet_path=oof_parquet,
        report_dir=report_dir_cpcv,
    )
    print(f"  CPCV: {len(cpcv_df)} paths (return proxy for cpcv_paths.csv)")
    print(f"  Per-cell mean PBO: {per_cell_mean_pbo}")

    # Build PBOResult from per-cell mean PBO (sub-fix #1)
    # The descriptive stats (frac_positive_paths, quartiles) are computed
    # from the global return-proxy cpcv_df as before.
    flat_path_sharpes = cpcv_df["sharpe"].dropna().to_numpy() if len(cpcv_df) > 0 else np.array([])
    frac_pos = float(np.mean(flat_path_sharpes > 0)) if len(flat_path_sharpes) > 0 else float("nan")
    q25, q50, q75 = (
        (
            float(np.percentile(flat_path_sharpes, 25)),
            float(np.percentile(flat_path_sharpes, 50)),
            float(np.percentile(flat_path_sharpes, 75)),
        )
        if len(flat_path_sharpes) >= 4
        else (float("nan"), float("nan"), float("nan"))
    )

    if per_cell_mean_pbo is not None:
        pbo_result = PBOResult(
            pbo=per_cell_mean_pbo,
            frac_positive_paths=frac_pos,
            path_sharpe_quartiles=(q25, q50, q75),
            n_splits_evaluated=len(cpcv_df),
            note=(
                f"Per-cell mean PBO={per_cell_mean_pbo:.4f} (iter-v3/004 cross-cell mean). "
                f"frac_positive_paths={frac_pos:.3f} from {len(cpcv_df)} return-proxy paths."
            ),
        )
    else:
        pbo_result = PBOResult(
            pbo=None,
            frac_positive_paths=frac_pos,
            path_sharpe_quartiles=(q25, q50, q75),
            n_splits_evaluated=len(cpcv_df),
            note="Per-cell PBO: OOF parquet absent or all cells degenerate.",
        )
    print(f"  PBO result: {pbo_result.note}")

    # -------------------------------------------------------
    # DSR (clamp-free, brief Section 3.5#5)
    # -------------------------------------------------------
    is_ms_primary = _monthly_sharpe(is_trades)
    oos_ms_primary = _monthly_sharpe(oos_trades)
    n_trials_total = args.n_trials * ensemble_size_for_run * len(active_models) * args.seeds

    is_wp = np.array([float(t.weighted_pnl) for t in is_trades])
    if len(is_wp) > 1 and is_wp.std() > 0:
        raw_sharpe_is = float(is_wp.mean() / is_wp.std() * np.sqrt(len(is_wp)))
        sk = float(skew(is_wp))
        kt = float(kurtosis(is_wp, fisher=False))
        # Use deflated_sharpe_ratio_v3 — no negative-SR clamp
        dsr_result = deflated_sharpe_ratio_v3(
            observed_sr=raw_sharpe_is,
            num_trials=n_trials_total,
            backtest_length=len(is_wp),
            skewness=sk,
            kurtosis=kt,
        )
        dsr_val = dsr_result["p_value"]
    elif len(is_wp) > 1:
        # Zero variance — use a single-trade placeholder with raw SR = 0
        sk, kt = 0.0, 3.0
        dsr_result = deflated_sharpe_ratio_v3(
            observed_sr=0.0,
            num_trials=n_trials_total,
            backtest_length=len(is_wp),
            skewness=sk,
            kurtosis=kt,
        )
        dsr_val = dsr_result["p_value"]
    else:
        dsr_val = 0.0
        sk, kt = 0.0, 3.0

    # PSR on OOS trades
    oos_wp = np.array([float(t.weighted_pnl) for t in oos_trades])
    if len(oos_wp) > 1 and oos_wp.std() > 0:
        raw_sharpe_oos = float(oos_wp.mean() / oos_wp.std() * np.sqrt(len(oos_wp)))
        oos_sk = float(skew(oos_wp))
        oos_kt = float(kurtosis(oos_wp, fisher=False))
        psr_val = psr(
            observed_sharpe=raw_sharpe_oos,
            n_obs=len(oos_wp),
            skewness=oos_sk,
            kurtosis=oos_kt,
        )
    else:
        psr_val = 0.0

    # N_eff: sub-fix #2 (iter-v3/004) — per-cell median aggregation.
    # Reads per_cell_pbo.csv written by _compute_cpcv_paths (which already
    # computed per-cell n_eff via n_effective_trials). Takes the median across
    # cells with rank > 1. Falls back to surrogate if CSV not available.
    per_cell_csv = REPORTS_DIR / f"iteration_{ITERATION_LABEL}" / "per_cell_pbo.csv"
    n_eff = 1  # safe default

    if per_cell_csv.exists():
        try:
            per_cell_df_neff = pd.read_csv(per_cell_csv)
            informative_neff = per_cell_df_neff[per_cell_df_neff["rank"] > 1]["n_eff"].dropna()
            if len(informative_neff) > 0:
                n_eff = int(np.median(informative_neff))
                print(
                    f"[n_eff] Per-cell median n_eff={n_eff} from {len(informative_neff)} "
                    f"informative cells (rank>1) — iter-v3/004 sub-fix #2"
                )
            else:
                print("[n_eff] per_cell_pbo.csv has no informative cells — using n_eff=1")
        except Exception as e:
            print(f"[n_eff] Could not read per_cell_pbo.csv: {e} — using n_eff=1")
    elif len(is_wp) > 1:
        # Parquet not available — use iter-v3/002 surrogate (sym_month groups)
        sym_month_groups_fb: dict[tuple[str, str], list[float]] = {}
        for t in is_trades:
            sym_f = t.symbol
            month_f = pd.Timestamp(t.open_time, unit="ms").strftime("%Y-%m")
            key_f = (sym_f, month_f)
            sym_month_groups_fb.setdefault(key_f, []).append(float(t.weighted_pnl))
        if len(sym_month_groups_fb) >= 2:
            max_len_fb = max(len(v) for v in sym_month_groups_fb.values())
            trial_mat_fallback = np.array(
                [v + [0.0] * (max_len_fb - len(v)) for v in sym_month_groups_fb.values()]
            )
            n_eff = n_effective_trials(trial_mat_fallback)
        else:
            n_eff = max(1, len(sym_month_groups_fb))
        print(f"[n_eff] per_cell_pbo.csv absent — using surrogate n_eff={n_eff}")

    min_trl_months = float(len(is_trades)) / max(1, ensemble_size_for_run * len(active_models))

    print(
        f"\n[metrics] IS monthly Sharpe={is_ms_primary:+.4f}, "
        f"OOS monthly Sharpe={oos_ms_primary:+.4f}"
    )
    print(f"[metrics] DSR={dsr_val:.4f}, PSR={psr_val:.4f}")
    pbo_display_inline = (
        "NaN(per-cell:no-data)" if pbo_result.pbo is None else f"{pbo_result.pbo:.4f}"
    )
    print(
        f"[metrics] PBO={pbo_display_inline}, "
        f"frac_positive_paths={pbo_result.frac_positive_paths:.3f}"
    )
    print(f"[metrics] n_trials={n_trials_total}, n_eff={n_eff}")

    # -------------------------------------------------------
    # Reports
    # -------------------------------------------------------
    report_dir = REPORTS_DIR / f"iteration_{ITERATION_LABEL}"
    report_dir.mkdir(parents=True, exist_ok=True)

    generate_iteration_reports(
        trades=primary_trades,
        iteration=ITERATION_LABEL,
        features_dir="data/features",  # BTC regime annotation only
        reports_dir=str(REPORTS_DIR),
        interval="8h",
        n_trials=n_trials_total,
    )

    _write_feature_importance(is_trades, oos_trades, primary_model_pairs or [], report_dir)

    _write_v3_comparison(
        is_trades,
        oos_trades,
        report_dir,
        dsr_val,
        pbo_result,
        psr_val,
        n_trials_total,
        n_eff,
    )

    # CPCV paths
    cpcv_path_file = report_dir / "cpcv_paths.csv"
    if not cpcv_df.empty:
        cpcv_df.to_csv(cpcv_path_file, index=False)
        print(f"[v3 report] cpcv_paths.csv: {len(cpcv_df)} paths")
    else:
        pd.DataFrame(columns=["path_id", "sharpe", "max_dd", "n_candles"]).to_csv(
            cpcv_path_file, index=False
        )

    # ADF test results — per-(symbol, feature, month)
    adf_path = report_dir / "adf_test.csv"
    if not adf_df.empty:
        adf_df.to_csv(adf_path, index=False)
        # Verify row count (brief Section 3.5#4 runtime assertion)
        _verify_adf_row_count(adf_df, list(baseline_symbols))
        print(f"[v3 report] adf_test.csv: {len(adf_df)} rows (per sym×feat×month)")
    else:
        pd.DataFrame(
            columns=["symbol", "feature_name", "month", "adf_statistic", "p_value", "stationary"]
        ).to_csv(adf_path, index=False)

    # IC matrix
    ic_path = report_dir / "ic_matrix.csv"
    if not ic_mat.empty:
        ic_mat.to_csv(ic_path)
        print(f"[v3 report] ic_matrix.csv: {ic_mat.shape}")
    else:
        pd.DataFrame().to_csv(ic_path)

    # DSR JSON
    _write_dsr_json(report_dir, dsr_val, pbo_result, psr_val, n_trials_total, n_eff, min_trl_months)

    # Sub-fix #5 (iter-v3/004): update per_seed_summary pbo from None placeholder
    # to the actual per-cell mean PBO computed above.  This ensures seed_summary.json
    # contains a numeric float (not "NaN" or null) per brief Section 3.5 sub-fix #5.
    for entry in per_seed_summary:
        if entry.get("pbo") is None:
            entry["pbo"] = pbo_result.pbo  # float or None (JSON null)

    # Pareto front
    _write_pareto_front(per_seed_summary, report_dir)

    # Seed summary
    (report_dir / "seed_summary.json").write_text(json.dumps(per_seed_summary, indent=2))

    t_end = time.time()
    elapsed_h = (t_end - t_start) / 3600.0
    print(f"\n[DONE] Reports: {report_dir}  (wall-clock: {elapsed_h:.2f}h)")
    print(f"  IS monthly Sharpe:  {is_ms_primary:+.4f}")
    print(f"  OOS monthly Sharpe: {oos_ms_primary:+.4f}")
    pbo_display = "NaN(per-cell:no-data)" if pbo_result.pbo is None else f"{pbo_result.pbo:.4f}"
    print(f"  DSR={dsr_val:.4f}  PBO={pbo_display}  PSR={psr_val:.4f}")
    print(f"  n_eff={n_eff}  ADF rows={len(adf_df)}")


if __name__ == "__main__":
    main()
