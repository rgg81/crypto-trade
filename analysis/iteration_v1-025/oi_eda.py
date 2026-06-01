"""iter-v1/025 — Phase 1 EDA for Open-Interest delta family.

EDA scope (per dispatch instructions):
1. Verify OI data availability for V1_BASELINE_UNIVERSE (BTC/ETH/LINK/LTC/DOT).
2. Per-symbol OI time-series coverage + extent.
3. OI delta computation:
     oi_delta_30 = (open_interest_t − open_interest_{t−30}) / open_interest_{t−30}
     z-scored on a 90-bar (30-day) past-only rolling window.
4. IC between {oi_delta_30, oi_delta_30_z90} and V1_FEATURE_COLUMNS_PRUNED
   top-5 features (5 sym × 2 features × 5 baseline features = 50 IC pairs).
   Critic Check 4 threshold: |IC| < 0.70.
5. Per-symbol OI delta distribution + extreme-event count (|z| > 2 events).
6. ORACLE EDA: per-symbol/per-cohort, what IS PnL Δ would a synthetic
   long-suppress (or short-suppress) gate at oi_delta_30 extreme bands
   project? — matched to /023 funding ORACLE methodology.
7. Cross-orthogonality vs funding: IC between oi_delta_30(_z90) and
   funding_rate_zscore_30(_z90) on per-symbol basis (does OI delta carry
   new signal or duplicate funding?).
8. ADF stationarity on raw oi_delta_30 and z90 series (informational).

IS-only discipline:
    All computations restricted to open_time < OOS_CUTOFF_DATE = 2025-03-24.
    The runner enforces this; the EDA mirrors it via the same constant.

Outputs (committed to git):
    analysis/iteration_v1-025/
        oi_availability.csv       — per-symbol coverage extent
        oi_distribution.csv       — per-symbol oi_delta_30 distribution
        oi_extreme_counts.csv     — per-symbol |z|>2 event counts
        oi_ic_matrix.csv          — IC matrix (50 entries)
        oi_funding_orthogonality.csv  — OI delta vs funding family IC
        oi_oracle_band_attribution.csv  — ORACLE EDA, IS-only
        oi_adf_test.csv           — ADF stationarity (informational)
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Project paths
PROJECT_ROOT = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
OUT_DIR = PROJECT_ROOT / "analysis" / "iteration_v1-025"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Sacred constants
OOS_CUTOFF_DATE = datetime(2025, 3, 24, tzinfo=timezone.utc)
OOS_CUTOFF_MS = int(OOS_CUTOFF_DATE.timestamp() * 1000)

V1_BASELINE_UNIVERSE = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")

# OI delta parameters (per dispatch spec)
OI_LOOKBACK = 30  # 30-bar percentage change (10 days at 8h cadence)
OI_ZSCORE_WINDOW = 90  # 90-bar (30-day) z-score window

# V1_FEATURE_COLUMNS_PRUNED top-5 features (selected by mean importance across
# v1 cycle-3 iterations — taken from baseline /baseline + /016-/024 inspection)
# These match the dispatch spec's "top-5 baseline features" reference.
# Selected based on robust appearance in feature_importance.csv across iterations.
TOP5_FEATURES = (
    "mom_rsi_14",
    "vol_atr_14",
    "vol_natr_14",
    "stat_log_return_1",
    "mom_macd_hist_12_26_9",
)


def load_klines(symbol: str) -> pd.DataFrame:
    """Load 8h klines for a symbol from data/<SYM>/8h.csv."""
    path = PROJECT_ROOT / "data" / symbol / "8h.csv"
    if not path.exists():
        raise FileNotFoundError(f"kline cache missing: {path}")
    df = pd.read_csv(path)
    df["open_time"] = df["open_time"].astype("int64")
    df["close"] = df["close"].astype(float)
    return df


def load_oi(symbol: str) -> pd.DataFrame | None:
    """Load 8h OI for a symbol; return None if cache missing."""
    path = PROJECT_ROOT / "data" / "open_interest" / symbol / "8h.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df["open_time"] = df["open_time"].astype("int64")
    df["sum_open_interest"] = df["sum_open_interest"].astype(float)
    return df


def load_funding(symbol: str) -> pd.DataFrame | None:
    """Load funding rates for a symbol from data/funding_rates/<SYM>.csv."""
    path = PROJECT_ROOT / "data" / "funding_rates" / f"{symbol}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df["funding_time"] = df["funding_time"].astype("int64")
    df["funding_rate"] = df["funding_rate"].astype(float)
    return df


def compute_oi_delta_features(oi_df: pd.DataFrame) -> pd.DataFrame:
    """Compute oi_delta_30 and oi_delta_30_z90 (past-only).

    oi_delta_30_t = (oi_t − oi_{t−30}) / oi_{t−30}
    oi_delta_30_z90_t = (oi_delta_30_t − mean(oi_delta_30_{t−90..t−1})) / std(...)

    Look-ahead-clean: the rolling-window denominator uses .shift(1).
    Handle oi_{t-30}=0 by masking the percent change to NaN (early-history
    sentinel rows where OI was effectively zero before listing was active).
    Clip oi_delta_30 to [-1.0, 5.0] to suppress data-quality artefacts
    (a 500% OI jump in 30 bars is extreme but plausible — beyond that is data error).
    """
    df = oi_df.sort_values("open_time").reset_index(drop=True).copy()
    oi = df["sum_open_interest"].astype(float)
    # Pct change over 30 bars (mask zero-denominator to NaN)
    denom = oi.shift(OI_LOOKBACK).replace(0, np.nan)
    df["oi_delta_30"] = ((oi - oi.shift(OI_LOOKBACK)) / denom).clip(-1.0, 5.0)
    # 90-bar past-only z-score (use .shift(1) for the rolling window)
    s = df["oi_delta_30"].astype(float)
    s_shifted = s.shift(1)
    rmean = s_shifted.rolling(OI_ZSCORE_WINDOW, min_periods=OI_ZSCORE_WINDOW).mean()
    rstd = s_shifted.rolling(OI_ZSCORE_WINDOW, min_periods=OI_ZSCORE_WINDOW).std(ddof=1)
    df["oi_delta_30_z90"] = ((s - rmean) / rstd.replace(0, np.nan)).clip(-10, 10)
    return df


def compute_funding_zscore(funding_df: pd.DataFrame, klines: pd.DataFrame, window: int) -> pd.Series:
    """Past-only z-score of funding rate, aligned to kline open_times."""
    f = funding_df.copy()
    f["open_time_aligned"] = (f["funding_time"] // 60_000) * 60_000
    k = klines.copy()
    k["open_time_aligned"] = (k["open_time"] // 60_000) * 60_000
    merged = k.merge(
        f[["open_time_aligned", "funding_rate"]], on="open_time_aligned", how="left"
    ).drop(columns=["open_time_aligned"])
    merged.index = k.index
    s = merged["funding_rate"].astype(float)
    s_shifted = s.shift(1)
    rmean = s_shifted.rolling(window, min_periods=window).mean()
    rstd = s_shifted.rolling(window, min_periods=window).std(ddof=1)
    return ((s - rmean) / rstd.replace(0, np.nan)).clip(-10, 10)


def compute_top5_features(klines: pd.DataFrame) -> pd.DataFrame:
    """Compute the top-5 baseline features for IC analysis.

    These mirror the V1_FEATURE_COLUMNS_PRUNED top-5 by mean importance.
    Past-only by construction.
    """
    df = klines.sort_values("open_time").reset_index(drop=True).copy()
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)

    # stat_log_return_1 — past-only log return (shifted)
    df["stat_log_return_1"] = (np.log(close) - np.log(close.shift(1)))

    # mom_rsi_14 — Wilder RSI, past-only
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["mom_rsi_14"] = 100 - (100 / (1 + rs))

    # vol_atr_14 — ATR (Wilder)
    tr = pd.concat(
        [
            (high - low).rename("hl"),
            (high - close.shift(1)).abs().rename("hc"),
            (low - close.shift(1)).abs().rename("lc"),
        ],
        axis=1,
    ).max(axis=1)
    df["vol_atr_14"] = tr.ewm(alpha=1 / 14, adjust=False).mean()

    # vol_natr_14 — NATR (ATR / close × 100)
    df["vol_natr_14"] = df["vol_atr_14"] / close * 100

    # mom_macd_hist_12_26_9 — MACD histogram
    ema_fast = close.ewm(span=12, adjust=False).mean()
    ema_slow = close.ewm(span=26, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    macd_signal = macd_line.ewm(span=9, adjust=False).mean()
    df["mom_macd_hist_12_26_9"] = macd_line - macd_signal

    # Shift all features by 1 bar (past-only at decision time)
    for col in TOP5_FEATURES:
        df[col] = df[col].shift(1)

    return df


def is_only_mask(df: pd.DataFrame) -> pd.Series:
    """Return boolean mask for rows where open_time < OOS_CUTOFF_MS (IS-only)."""
    return df["open_time"] < OOS_CUTOFF_MS


def adf_pvalue(series: pd.Series) -> float:
    """Return ADF p-value, NaN if statsmodels unavailable or series too short."""
    try:
        from statsmodels.tsa.stattools import adfuller
    except ImportError:
        return np.nan
    s = series.dropna()
    if len(s) < 50:
        return np.nan
    try:
        return float(adfuller(s.values, autolag="AIC")[1])
    except Exception:
        return np.nan


def main() -> None:
    print("=" * 60)
    print("iter-v1/025 — OI delta family Phase 1 EDA")
    print("=" * 60)

    # ----------------------------------------------------------------------
    # Step 1: data availability + extent
    # ----------------------------------------------------------------------
    avail_rows = []
    for sym in V1_BASELINE_UNIVERSE:
        oi = load_oi(sym)
        kl = load_klines(sym)
        kl_first = int(kl["open_time"].iloc[0])
        kl_last = int(kl["open_time"].iloc[-1])
        if oi is None:
            avail_rows.append(
                {
                    "symbol": sym,
                    "oi_status": "MISSING",
                    "oi_first_ms": "",
                    "oi_last_ms": "",
                    "oi_n_rows": 0,
                    "oi_first_iso": "",
                    "oi_last_iso": "",
                    "kline_first_iso": pd.Timestamp(kl_first, unit="ms", tz="UTC").isoformat(),
                    "kline_last_iso": pd.Timestamp(kl_last, unit="ms", tz="UTC").isoformat(),
                    "oi_is_rows": 0,
                    "kline_is_rows": int((kl["open_time"] < OOS_CUTOFF_MS).sum()),
                    "kline_oos_rows": int((kl["open_time"] >= OOS_CUTOFF_MS).sum()),
                }
            )
            continue
        oi_first = int(oi["open_time"].iloc[0])
        oi_last = int(oi["open_time"].iloc[-1])
        oi_is = oi[oi["open_time"] < OOS_CUTOFF_MS]
        avail_rows.append(
            {
                "symbol": sym,
                "oi_status": "PRESENT",
                "oi_first_ms": oi_first,
                "oi_last_ms": oi_last,
                "oi_n_rows": len(oi),
                "oi_first_iso": pd.Timestamp(oi_first, unit="ms", tz="UTC").isoformat(),
                "oi_last_iso": pd.Timestamp(oi_last, unit="ms", tz="UTC").isoformat(),
                "kline_first_iso": pd.Timestamp(kl_first, unit="ms", tz="UTC").isoformat(),
                "kline_last_iso": pd.Timestamp(kl_last, unit="ms", tz="UTC").isoformat(),
                "oi_is_rows": len(oi_is),
                "kline_is_rows": int((kl["open_time"] < OOS_CUTOFF_MS).sum()),
                "kline_oos_rows": int((kl["open_time"] >= OOS_CUTOFF_MS).sum()),
            }
        )
    avail_df = pd.DataFrame(avail_rows)
    avail_df.to_csv(OUT_DIR / "oi_availability.csv", index=False)
    print("\n=== OI availability ===")
    print(avail_df.to_string(index=False))

    present_symbols = [r["symbol"] for r in avail_rows if r["oi_status"] == "PRESENT"]
    missing_symbols = [r["symbol"] for r in avail_rows if r["oi_status"] == "MISSING"]
    print(f"\nPresent: {present_symbols}")
    print(f"Missing: {missing_symbols}")
    print(f"OOS_CUTOFF: {OOS_CUTOFF_DATE.isoformat()}")

    if not present_symbols:
        print("\n*** NO OI DATA AVAILABLE — aborting downstream EDA ***")
        sys.exit(1)

    # ----------------------------------------------------------------------
    # Step 2: per-symbol OI distribution + extreme-event counts (PRESENT only)
    # ----------------------------------------------------------------------
    distrib_rows = []
    extreme_rows = []
    feat_dfs: dict[str, pd.DataFrame] = {}
    for sym in present_symbols:
        oi = load_oi(sym)
        kl = load_klines(sym)

        # Compute OI delta on the OI series alone (aligned to OI's open_time grid).
        oi_feat = compute_oi_delta_features(oi)

        # Merge into kline grid (left-join; some kline bars before OI start = NaN)
        merged = kl.merge(
            oi_feat[["open_time", "oi_delta_30", "oi_delta_30_z90"]],
            on="open_time",
            how="left",
        )

        # IS-only slice for distribution
        is_mask = merged["open_time"] < OOS_CUTOFF_MS
        merged_is = merged[is_mask].copy()

        d30 = merged_is["oi_delta_30"].dropna()
        z90 = merged_is["oi_delta_30_z90"].dropna()

        distrib_rows.append(
            {
                "symbol": sym,
                "is_kline_rows": int(is_mask.sum()),
                "is_d30_non_null": len(d30),
                "is_d30_non_null_pct": round(100 * len(d30) / max(1, int(is_mask.sum())), 1),
                "d30_mean": round(float(d30.mean()), 6) if len(d30) else np.nan,
                "d30_std": round(float(d30.std(ddof=1)), 6) if len(d30) else np.nan,
                "d30_p01": round(float(d30.quantile(0.01)), 6) if len(d30) else np.nan,
                "d30_p10": round(float(d30.quantile(0.10)), 6) if len(d30) else np.nan,
                "d30_p25": round(float(d30.quantile(0.25)), 6) if len(d30) else np.nan,
                "d30_median": round(float(d30.median()), 6) if len(d30) else np.nan,
                "d30_p75": round(float(d30.quantile(0.75)), 6) if len(d30) else np.nan,
                "d30_p90": round(float(d30.quantile(0.90)), 6) if len(d30) else np.nan,
                "d30_p99": round(float(d30.quantile(0.99)), 6) if len(d30) else np.nan,
                "d30_min": round(float(d30.min()), 6) if len(d30) else np.nan,
                "d30_max": round(float(d30.max()), 6) if len(d30) else np.nan,
                "z90_n": len(z90),
                "z90_mean": round(float(z90.mean()), 4) if len(z90) else np.nan,
                "z90_std": round(float(z90.std(ddof=1)), 4) if len(z90) else np.nan,
            }
        )

        # Extreme events: |z90|>2
        if len(z90) > 0:
            n_total = len(z90)
            n_pos2 = int((z90 > 2).sum())
            n_neg2 = int((z90 < -2).sum())
            n_pos3 = int((z90 > 3).sum())
            n_neg3 = int((z90 < -3).sum())
            extreme_rows.append(
                {
                    "symbol": sym,
                    "z90_n": n_total,
                    "n_pos_z>2": n_pos2,
                    "pct_pos_z>2": round(100 * n_pos2 / n_total, 2),
                    "n_neg_z>2": n_neg2,
                    "pct_neg_z>2": round(100 * n_neg2 / n_total, 2),
                    "n_pos_z>3": n_pos3,
                    "n_neg_z>3": n_neg3,
                }
            )

        feat_dfs[sym] = merged  # cache for downstream

    pd.DataFrame(distrib_rows).to_csv(OUT_DIR / "oi_distribution.csv", index=False)
    print("\n=== OI delta distribution (IS-only) ===")
    print(pd.DataFrame(distrib_rows).to_string(index=False))

    pd.DataFrame(extreme_rows).to_csv(OUT_DIR / "oi_extreme_counts.csv", index=False)
    print("\n=== OI |z90|>2 extreme-event counts (IS-only) ===")
    print(pd.DataFrame(extreme_rows).to_string(index=False))

    # ----------------------------------------------------------------------
    # Step 3: IC matrix vs baseline TOP5 features
    # ----------------------------------------------------------------------
    ic_rows = []
    for sym in present_symbols:
        merged = feat_dfs[sym]
        kl = load_klines(sym)
        top5 = compute_top5_features(kl)
        m = merged.merge(top5[["open_time"] + list(TOP5_FEATURES)], on="open_time", how="left")
        is_mask = m["open_time"] < OOS_CUTOFF_MS
        m_is = m[is_mask]
        for oi_col in ("oi_delta_30", "oi_delta_30_z90"):
            for base_col in TOP5_FEATURES:
                pair = m_is[[oi_col, base_col]].dropna()
                if len(pair) < 50:
                    ic = np.nan
                else:
                    # Spearman IC (rank correlation, common in cross-asset feature analysis)
                    ic = float(pair[oi_col].rank().corr(pair[base_col].rank()))
                ic_rows.append(
                    {
                        "symbol": sym,
                        "oi_feature": oi_col,
                        "baseline_feature": base_col,
                        "ic_spearman": round(ic, 4) if not np.isnan(ic) else np.nan,
                        "n_pairs": len(pair),
                    }
                )
    ic_df = pd.DataFrame(ic_rows)
    ic_df.to_csv(OUT_DIR / "oi_ic_matrix.csv", index=False)
    print(f"\n=== IC matrix: {len(ic_df)} pairs (Critic Check 4 threshold |IC| < 0.70) ===")
    print(ic_df.to_string(index=False))
    max_abs_ic = float(ic_df["ic_spearman"].abs().max()) if len(ic_df) else 0.0
    print(f"\nMax |IC|: {max_abs_ic:.4f} {'PASS' if max_abs_ic < 0.7 else 'FAIL (>= 0.7)'}")

    # ----------------------------------------------------------------------
    # Step 4: Orthogonality vs funding family
    # ----------------------------------------------------------------------
    ortho_rows = []
    for sym in present_symbols:
        merged = feat_dfs[sym]
        kl = load_klines(sym)
        f = load_funding(sym)
        if f is None:
            continue
        fz30 = compute_funding_zscore(f, kl, 30)
        fz90 = compute_funding_zscore(f, kl, 90)
        kl["funding_rate_zscore_30"] = fz30.values
        kl["funding_rate_zscore_90"] = fz90.values
        m = merged.merge(
            kl[["open_time", "funding_rate_zscore_30", "funding_rate_zscore_90"]],
            on="open_time",
            how="left",
        )
        is_mask = m["open_time"] < OOS_CUTOFF_MS
        m_is = m[is_mask]
        for oi_col in ("oi_delta_30", "oi_delta_30_z90"):
            for fund_col in ("funding_rate_zscore_30", "funding_rate_zscore_90"):
                pair = m_is[[oi_col, fund_col]].dropna()
                if len(pair) < 50:
                    ic = np.nan
                else:
                    ic = float(pair[oi_col].rank().corr(pair[fund_col].rank()))
                ortho_rows.append(
                    {
                        "symbol": sym,
                        "oi_feature": oi_col,
                        "funding_feature": fund_col,
                        "ic_spearman": round(ic, 4) if not np.isnan(ic) else np.nan,
                        "n_pairs": len(pair),
                    }
                )
    ortho_df = pd.DataFrame(ortho_rows)
    ortho_df.to_csv(OUT_DIR / "oi_funding_orthogonality.csv", index=False)
    print("\n=== OI vs funding family IC (F-AXIS #3 threshold |IC| < 0.5) ===")
    if len(ortho_df):
        print(ortho_df.to_string(index=False))
        max_abs_ortho = float(ortho_df["ic_spearman"].abs().max())
        print(f"\nMax |IC| OI-vs-funding: {max_abs_ortho:.4f} {'PASS (orthogonal)' if max_abs_ortho < 0.5 else 'FAIL (redundant)'}")

    # ----------------------------------------------------------------------
    # Step 5: ORACLE EDA — band-conditional IS PnL attribution proxy
    # ----------------------------------------------------------------------
    # For each symbol, compute IS forward 8h log return at bar t.
    # Then bin by oi_delta_30_z90 quintile.
    # Compute: count, mean forward return, sum forward return per band.
    # If a band shows strongly directional forward returns AND high concentration,
    # OI delta might predict future moves.
    oracle_rows = []
    for sym in present_symbols:
        kl = load_klines(sym)
        merged = feat_dfs[sym]
        # Forward log return (next-bar OPEN-to-CLOSE or NEXT-bar return)
        kl["fwd_log_ret"] = (np.log(kl["close"].astype(float)).shift(-1)
                             - np.log(kl["close"].astype(float)))
        m = merged.merge(kl[["open_time", "fwd_log_ret"]], on="open_time", how="left")
        is_mask = m["open_time"] < OOS_CUTOFF_MS
        m_is = m[is_mask].dropna(subset=["oi_delta_30_z90", "fwd_log_ret"])
        if len(m_is) < 100:
            continue

        # Quintile bins
        m_is = m_is.assign(z_bin=pd.qcut(m_is["oi_delta_30_z90"], q=5, labels=[
            "Q1 (extreme negative)", "Q2", "Q3 (mid)", "Q4", "Q5 (extreme positive)"
        ]))
        for label, grp in m_is.groupby("z_bin", observed=True):
            oracle_rows.append(
                {
                    "symbol": sym,
                    "band": label,
                    "n_obs": len(grp),
                    "z90_min": round(float(grp["oi_delta_30_z90"].min()), 4),
                    "z90_max": round(float(grp["oi_delta_30_z90"].max()), 4),
                    "mean_fwd_log_ret_bp": round(float(grp["fwd_log_ret"].mean()) * 10_000, 2),
                    "std_fwd_log_ret_bp": round(float(grp["fwd_log_ret"].std(ddof=1)) * 10_000, 2),
                    "sum_fwd_log_ret_pct": round(float(grp["fwd_log_ret"].sum()) * 100, 4),
                    "sharpe_proxy": round(
                        float(grp["fwd_log_ret"].mean() / grp["fwd_log_ret"].std(ddof=1) * np.sqrt(3 * 365))
                        if grp["fwd_log_ret"].std(ddof=1) > 0 else 0.0,
                        4,
                    ),
                }
            )

    oracle_df = pd.DataFrame(oracle_rows)
    oracle_df.to_csv(OUT_DIR / "oi_oracle_band_attribution.csv", index=False)
    print("\n=== ORACLE EDA: per-symbol forward-return by oi_delta_30_z90 quintile (IS-only) ===")
    if len(oracle_df):
        print(oracle_df.to_string(index=False))

    # ----------------------------------------------------------------------
    # Step 6: ADF stationarity (informational)
    # ----------------------------------------------------------------------
    adf_rows = []
    for sym in present_symbols:
        merged = feat_dfs[sym]
        is_mask = merged["open_time"] < OOS_CUTOFF_MS
        m_is = merged[is_mask]
        adf_rows.append(
            {
                "symbol": sym,
                "oi_delta_30_adf_pvalue": round(adf_pvalue(m_is["oi_delta_30"]), 6),
                "oi_delta_30_z90_adf_pvalue": round(adf_pvalue(m_is["oi_delta_30_z90"]), 6),
                "oi_delta_30_stationary": adf_pvalue(m_is["oi_delta_30"]) < 0.05,
                "oi_delta_30_z90_stationary": adf_pvalue(m_is["oi_delta_30_z90"]) < 0.05,
            }
        )
    adf_df = pd.DataFrame(adf_rows)
    adf_df.to_csv(OUT_DIR / "oi_adf_test.csv", index=False)
    print("\n=== ADF stationarity (IS-only) ===")
    print(adf_df.to_string(index=False))

    print("\n=== Phase 1 EDA complete ===")
    print(f"Outputs: {OUT_DIR}")


if __name__ == "__main__":
    main()
