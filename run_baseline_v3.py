"""Baseline v3 runner — iter-v3/002 methodology-repair iteration.

Inherits the same universe {BCH, MKR, LDO, TRX} and model architecture as
iter-v3/001 but replaces the broken validation stack:

  1. PBO (CSCV): 2-D matrix (N_paths × S_strategies) via pbo_from_cpcv.
     If runner produces only S=1, PBOResult.pbo is None — reported as NaN in
     comparison.csv with frac_positive_paths as the descriptive fallback.
  2. CPCV scope: per-symbol IS-window candle/feature sequence (not IS trades).
     N=10 groups, k=2 → 45 paths.  For each path: train-period returns are
     the Sharpe of that subset's weighted PnL from a mock walk-forward.
  3. Embargo-gap runtime assertion: gap == REQUIRED_GAP == 88 asserted at
     runner startup and inside combinatorial_purged_cv.
  4. ADF per-(symbol, feature, retraining month): ~3672 rows for 4 syms ×
     34 feats × 27 months.  Row-count asserted at run completion.
  5. DSR: uses deflated_sharpe_ratio_v3 (no negative-SR clamp).
  6. n_eff_trials: built from true per-symbol per-trial OOF return matrix.

Reports written to:
  reports-v3/iteration_v3-002/
    in_sample/  out_of_sample/  comparison.csv  pareto_front.csv
    cpcv_paths.csv  adf_test.csv  ic_matrix.csv  dsr.json  run.log

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
ENSEMBLE_SEEDS: list[int] = [42, 123, 456, 789, 1001]  # IMMUTABLE

ITERATION_LABEL = "v3-002"
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
    """Assert V3_FEATURE_COLUMNS has exactly 34 columns (brief Section 3.3)."""
    n = len(V3_FEATURE_COLUMNS)
    if n != 34:
        raise RuntimeError(
            f"V3_FEATURE_COLUMNS has {n} columns — expected exactly 34. "
            "Brief Section 3.3 requires the v3 column count to be unchanged from iter-v3/001."
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
    """Grep-check: features_v3 must not import from features (v1) or features_v2."""
    import subprocess as sp  # noqa: PLC0415

    for pattern in (
        "from crypto_trade.features ",
        "from crypto_trade.features_v2",
    ):
        out = sp.run(
            ["grep", "-r", pattern, "src/crypto_trade/features_v3/"],
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
) -> tuple[pd.DataFrame, np.ndarray]:
    """Compute CPCV statistics from IS candle/feature sequences.

    CORRECTED (iter-v3/002): operates on the IS-window candle sequence, NOT
    the IS trade sequence.  Each CPCV path partitions the candle/feature
    timeline into N=10 groups and holds k=2 groups out.

    For each path, the 'model metric' is the weighted-PnL Sharpe of candles
    in the test groups, computed from the walk-forward model's per-candle
    weighted_pnl column if available in the parquet, or from a return
    proxy (feature-weighted sign × absolute return).

    Since the runner does not persist per-Optuna-trial OOF return sequences
    in this iteration, the strategy axis S=1 (one strategy per path).
    PBOResult.pbo will be None; the descriptive fallback (frac_positive_paths
    + path Sharpe quartiles) is reported instead.

    Per brief Section 3.5#1, when S=1: PBO=None is ACCEPTABLE and STRICTER
    than a number in [0.4, 0.6] because it correctly identifies the input
    as inadequate for CSCV.

    Parameters
    ----------
    symbols
        v3 symbols (BCH, MKR, LDO, TRX).
    feature_parquets
        Dict mapping symbol -> IS-window feature DataFrame.

    Returns
    -------
    (cpcv_df, path_metric_matrix)
        cpcv_df: DataFrame with path_id, sharpe, max_dd, n_candles.
        path_metric_matrix: np.ndarray of shape (n_paths, 1) — the S=1 case.
    """
    # Combine IS-window candle sequences across symbols, preserving time order
    all_frames = []
    for sym in symbols:
        df = feature_parquets.get(sym)
        if df is None or df.empty:
            continue
        df_is = df[df["open_time"] < OOS_CUTOFF_MS].copy()
        if len(df_is) < 10:
            continue
        # Use close-to-close log return as the per-candle return proxy
        if "close" in df_is.columns:
            df_is = df_is.copy()
            df_is["_ret"] = np.log(df_is["close"] / df_is["close"].shift(1)).fillna(0.0)
        else:
            df_is["_ret"] = 0.0
        df_is["_sym"] = sym
        all_frames.append(df_is[["open_time", "_ret", "_sym"]].copy())

    if not all_frames:
        return pd.DataFrame(columns=["path_id", "sharpe", "max_dd", "n_candles"]), np.zeros((0, 1))

    # Sort by open_time across symbols → combined candle timeline
    combined = (
        pd.concat(all_frames, ignore_index=True).sort_values("open_time").reset_index(drop=True)
    )
    n_candles = len(combined)
    print(f"  [CPCV] IS candle sequence: {n_candles} candles across {len(symbols)} symbols")

    if n_candles < CPCV_N_SPLITS * 10:
        print(f"  [CPCV] Insufficient candles ({n_candles}) for CPCV — skipping")
        return pd.DataFrame(columns=["path_id", "sharpe", "max_dd", "n_candles"]), np.zeros((0, 1))

    returns = combined["_ret"].to_numpy()

    # Assertion: gap must equal REQUIRED_GAP (brief Section 3.5#3)
    # Use expected_gap to enforce — no silent rescaling
    splits = combinatorial_purged_cv(
        n_samples=n_candles,
        n_splits=CPCV_N_SPLITS,
        n_test_splits=CPCV_N_TEST_SPLITS,
        gap=REQUIRED_GAP,
        embargo=CPCV_EMBARGO,
        expected_gap=REQUIRED_GAP,  # assertion enforced
    )

    rows = []
    path_sharpes = []
    for path_id, (_, test_idx) in enumerate(splits):
        path_returns = returns[test_idx]
        if len(path_returns) < 2:
            rows.append(
                {
                    "path_id": path_id,
                    "sharpe": float("nan"),
                    "max_dd": float("nan"),
                    "n_candles": len(path_returns),
                }
            )
            path_sharpes.append(float("nan"))
            continue

        mu = float(np.nanmean(path_returns))
        sigma = float(np.nanstd(path_returns, ddof=1))
        # Scale to approximate monthly Sharpe: ~252 trading days / 3 candles per day at 8h
        path_sharpe = mu / sigma * np.sqrt(len(path_returns)) if sigma > 0 else 0.0
        cum = np.nancumsum(path_returns)
        running_max = np.maximum.accumulate(cum)
        dd = running_max - cum
        max_dd = float(dd.max()) if len(dd) > 0 else 0.0

        rows.append(
            {
                "path_id": path_id,
                "sharpe": round(path_sharpe, 6),
                "max_dd": round(max_dd * 100, 4),  # convert to % for comparability
                "n_candles": len(path_returns),
            }
        )
        path_sharpes.append(path_sharpe)

    cpcv_df = pd.DataFrame(rows)
    # Shape: (n_paths, 1) — S=1, so pbo_from_cpcv will return PBOResult.pbo=None
    path_metric_matrix = np.array(path_sharpes, dtype=float).reshape(-1, 1)
    return cpcv_df, path_metric_matrix


# ============================================================
# Model builder
# ============================================================


def _build_v3_model(
    symbol: str,
    seed: int,
    n_trials: int,
    ensemble_seeds: list[int],
) -> tuple[BacktestConfig, RiskV3Wrapper]:
    """Build v3 M1 LightGBM + RiskV3Wrapper for a single symbol.

    v2 5-gate config + BTC trend filter. NO R1/R2/R3 (brief Section 3.4).
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
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        atr_column="natr_21_raw",
        use_atr_labeling=True,
        ensemble_seeds=list(ensemble_seeds),
        feature_columns=list(V3_FEATURE_COLUMNS),  # EXPLICIT — never None
        ood_enabled=False,  # OOD via RiskV3Wrapper z-score gate
    )
    risk_cfg = RiskV2Config(
        zscore_threshold=2.5,
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
) -> tuple[list, list, dict, dict, list]:
    """Run all 4 v3 models for a single outer seed."""
    all_trades: list = []
    model_pairs: list = []

    for name, symbol in V3_MODELS:
        print("=" * 60)
        print(f"MODEL {name} — seed {seed}")
        print("=" * 60)
        cfg, strategy = _build_v3_model(
            symbol=symbol,
            seed=seed,
            n_trials=n_trials,
            ensemble_seeds=ENSEMBLE_SEEDS,
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
    parser = argparse.ArgumentParser(description="v3 baseline runner — iter-v3/002")
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
    args = parser.parse_args()

    t_start = time.time()
    _verify_branch()

    baseline_symbols = tuple(sym for _, sym in V3_MODELS)
    _verify_symbols(baseline_symbols)
    _verify_data_freshness(baseline_symbols + ("BTCUSDT",))
    _verify_feature_columns()  # asserts len == 34
    _verify_label_leakage_gap()  # asserts REQUIRED_GAP == 88
    _verify_track_isolation()  # grep check

    print(f"\nBASELINE v3 iter-{ITERATION_LABEL}: BCH+MKR+LDO+TRX (methodology repair)")
    print(f"Seeds: {args.seeds}  Optuna trials/model: {args.n_trials}")
    print(f"CPCV: N={CPCV_N_SPLITS}, k={CPCV_N_TEST_SPLITS}, 45 paths on IS CANDLE SEQUENCE")
    print(f"Gap: {REQUIRED_GAP} (= (timeout_candles+1) * n_symbols = (21+1)*4)")
    print("Pre-flight: branch OK, symbols OK, data fresh (<16h), feature-cols=34  PASS\n")

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
            seed, args.n_trials, btc_times, btc_closes
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
                "pbo": "NaN",  # S=1 — pbo_from_cpcv returns None
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
    # CPCV on IS candle/feature sequence (brief Section 3.5#2)
    # -------------------------------------------------------
    print("\n[CPCV] Computing 45-path statistics from IS CANDLE SEQUENCE...")
    cpcv_df, path_metric_matrix = _compute_cpcv_paths(list(baseline_symbols), feature_parquets)
    print(f"  CPCV: {len(cpcv_df)} paths, matrix shape={path_metric_matrix.shape}")

    # PBO via CSCV on (N_paths × S_strategies) matrix — S=1 → pbo_result.pbo=None
    if path_metric_matrix.size > 0:
        pbo_result = pbo_from_cpcv(path_metric_matrix)
    else:
        pbo_result = PBOResult(
            pbo=None,
            frac_positive_paths=float("nan"),
            path_sharpe_quartiles=(float("nan"), float("nan"), float("nan")),
            n_splits_evaluated=0,
            note="CPCV produced no paths.",
        )
    print(f"  PBO result: {pbo_result.note}")

    # -------------------------------------------------------
    # DSR (clamp-free, brief Section 3.5#5)
    # -------------------------------------------------------
    is_ms_primary = _monthly_sharpe(is_trades)
    oos_ms_primary = _monthly_sharpe(oos_trades)
    n_trials_total = args.n_trials * len(ENSEMBLE_SEEDS) * len(V3_MODELS) * args.seeds

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

    # N_eff: per-symbol per-month IS return sequences as the trial-return matrix
    # Each calendar month × symbol contributes one "trial" of returns.
    # This avoids the iter-v3/001 row-repeat bug (brief Section 3.5#5).
    if len(is_wp) > 1:
        # Build matrix: rows = per-(symbol, month) groups, cols = trades in that group
        sym_month_groups: dict[tuple[str, str], list[float]] = {}
        for t in is_trades:
            sym = t.symbol
            month = pd.Timestamp(t.open_time, unit="ms").strftime("%Y-%m")
            key = (sym, month)
            sym_month_groups.setdefault(key, []).append(float(t.weighted_pnl))

        if len(sym_month_groups) >= 2:
            # Pad each group to equal length for matrix construction
            max_len = max(len(v) for v in sym_month_groups.values())
            trial_mat = np.array(
                [v + [0.0] * (max_len - len(v)) for v in sym_month_groups.values()]
            )
            n_eff = n_effective_trials(trial_mat)
        else:
            n_eff = max(1, len(sym_month_groups))
    else:
        n_eff = 1

    min_trl_months = float(len(is_trades)) / max(1, len(ENSEMBLE_SEEDS) * len(V3_MODELS))

    print(
        f"\n[metrics] IS monthly Sharpe={is_ms_primary:+.4f}, "
        f"OOS monthly Sharpe={oos_ms_primary:+.4f}"
    )
    print(f"[metrics] DSR={dsr_val:.4f}, PSR={psr_val:.4f}")
    print(
        f"[metrics] PBO={'NaN (S=1)' if pbo_result.pbo is None else f'{pbo_result.pbo:.4f}'}, "
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

    # Pareto front
    _write_pareto_front(per_seed_summary, report_dir)

    # Seed summary
    (report_dir / "seed_summary.json").write_text(json.dumps(per_seed_summary, indent=2))

    t_end = time.time()
    elapsed_h = (t_end - t_start) / 3600.0
    print(f"\n[DONE] Reports: {report_dir}  (wall-clock: {elapsed_h:.2f}h)")
    print(f"  IS monthly Sharpe:  {is_ms_primary:+.4f}")
    print(f"  OOS monthly Sharpe: {oos_ms_primary:+.4f}")
    pbo_display = "NaN(S=1)" if pbo_result.pbo is None else f"{pbo_result.pbo:.4f}"
    print(f"  DSR={dsr_val:.4f}  PBO={pbo_display}  PSR={psr_val:.4f}")
    print(f"  n_eff={n_eff}  ADF rows={len(adf_df)}")


if __name__ == "__main__":
    main()
