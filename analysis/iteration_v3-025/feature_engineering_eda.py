"""
iter-v3/025 — Genuine feature engineering EDA (PIVOT MOMENT)
==============================================================

Per user directive 2026-05-08 + Critic FINAL Recommendation of iter-v3/024
(SHA `5a47f5d`):

After 3 consecutive INERT outcomes for off-the-shelf indicator additions
(iter-v3/015 microstructure tbr_zscore_30 INERT; iter-v3/019 funding_rate_zscore_30
INERT; iter-v3/024 btc_funding_rate_zscore_30 INERT), the 13-feature stack
appears saturated for direct feature additions. The model is finding stable
splits on the existing 13 primitives and new indicator-style features rank
14/14 reliably.

iter-v3/025 PIVOTS to genuine feature engineering: COMPOSED features built
from existing primitives that depth-3-5 LightGBM trees cannot construct
internally at the candidate-split level (a tree of depth 5 can express up
to 32 leaf regions but each internal split is on a SINGLE feature; it
cannot construct interaction expressions like `f1 × sign(f2 - threshold)`
without using one of those splits, leaving fewer for the actual decision).

This EDA evaluates 7 candidate engineered features and recommends ONE for
the iter-v3/025 axis (single-axis discipline preserved).

Methodology — composite score per candidate:
    1. Compute candidate per-symbol on IS-only window (BCH+LDO+TRX × 24mo).
    2. Spearman IC vs each of the 13 V3_FEATURE_COLUMNS (orthogonality).
       v3 hard gate: max |IC| < 0.70. Strict brief target: max |IC| < 0.50.
    3. ADF stationarity test on candidate series per symbol (p < 0.05).
    4. Distribution stability — no NaN explosion (>20%), no extreme outliers.
    5. Rank-IC vs forward 1/3/7-bar log-returns per symbol.
       Meaningful predictive signal: |rank-IC| >= 0.02 on at least 1 horizon.
    6. Composite score = orthogonality + rank-IC magnitude + interpretability +
                        implementation cost.

Candidates (7 evaluated; 1 chosen for the axis):
    1. regime_momentum_signed_5d = ret_5d × sign(hurst_100 - 0.5)
       Rationale: momentum × trend-regime sign. depth-5 trees cannot easily
       construct this from raw inputs because "sign(hurst - 0.5)" requires
       one tree split, then "ret_5d × sign(...)" requires nested splits;
       LightGBM colsample_bytree=1.0 + max_depth=5 has limited capacity.
       Implementation cost: LOW (composes existing primitives).
       Interpretability: HIGH (regime-conditional momentum is a textbook
       trader heuristic — momentum "works" in trending markets, fails in
       mean-reverting markets).

    2. vol_adj_autocorr = ret_autocorr_lag1_50 / (range_realized_vol_50 + eps)
       Rationale: per-unit-vol return persistence. Disambiguates regimes
       where autocorr is high but vol is also high (noise-driven persistence)
       from regimes where autocorr is high and vol is low (genuine signal).
       Implementation cost: LOW.
       Interpretability: MEDIUM (ratio interpretation is less intuitive).

    3. adx_signed_momentum = adx × sign(ret_14d) — REJECTED CANDIDATE
       Rationale: directional trend strength. NOTE: adx is a v3 GATE not
       a feature column; would require computing adx as a feature first OR
       using BTC's ADX via cross-asset feature primitive. EXCLUDED from
       composite score because v3's per-symbol architecture does not
       expose adx to the 13-feature stack (rejected without scoring).

    4. cross_asset_divergence_norm = (sym_ret_7d - btc_ret_14d) / (vwap_dev_20 + eps)
       Rationale: relative strength normalized by mean-reversion intensity.
       Captures alt-altcoin divergence with vol-context.
       Implementation cost: LOW.
       Interpretability: MEDIUM-HIGH.
       Note: sym_vs_btc_ret_7d (sym_ret_7d - btc_ret_7d) is already in the
       13-feature set. This candidate uses btc_ret_14d (mismatch horizons)
       AND normalizes by vwap_dev_20 — distinct mechanism.

    5. hurst_drift_50_200 = hurst_50 - hurst_200
       Rationale: multi-timeframe regime drift. hurst_diff_100_50 is in the
       feature set but hurst_drift_50_200 captures slower-vs-faster regime
       contrast. Note: hurst_50 + hurst_200 are in V3_FEATURE_COLUMNS_FULL
       (34 features) but hurst_50 is NOT in the 13-feature TOP_N subset.
       Implementation cost: LOW (just compute on log_close).
       Interpretability: MEDIUM (regime drift is more abstract).

    6. fracdiff_d05_close = fractional differentiation of close at d=0.5
       Rationale: López de Prado AFML Ch. 5 — preserves memory while
       achieving stationarity. Explicitly listed in v3 skill iter-v3/001
       scope but never implemented for d=0.5 (existing fracdiff_logclose_dstat
       uses FracdiffStat auto-d* which is per-symbol and varies; d=0.5
       is the canonical AFML midpoint between d=0 (memoryless) and d=1
       (fully differenced). FRACDIFF MODULE EXISTS at
       src/crypto_trade/features_v3/fracdiff_v3.py — extension cost is LOW.
       Interpretability: LOW for traders, HIGH for ML researchers.

    7. ret_kurt_to_skew_ratio = ret_kurt_50 / (|ret_skew_50| + eps)
       Rationale: fat-tail to asymmetry ratio. ret_kurt_50 + ret_skew_50
       are both in 13-feature set; the ratio is a normalized fat-tail
       intensity that may capture regime crashes (high kurt, modest skew)
       vs persistent drift (modest kurt, high skew).
       Implementation cost: LOW.
       Interpretability: LOW-MEDIUM (composite ratio of higher moments).

Inputs read (IS-only — training window pre-OOS_CUTOFF_DATE 2025-03-24):
    - data/{BCH,LDO,TRX}USDT/8h.csv — 8h klines (for close, high, low)
    - data/features_v3/{BCH,LDO,TRX}USDT_8h_features.parquet — 13 V3 features

Outputs (committed BEFORE the brief — Phase 5.5 reproducibility requirement):
    - analysis/iteration_v3-025/feature_engineering_eda_distribution.csv
    - analysis/iteration_v3-025/feature_engineering_eda_correlation.csv
    - analysis/iteration_v3-025/feature_engineering_eda_rankic.csv
    - analysis/iteration_v3-025/feature_engineering_eda_adf.csv
    - analysis/iteration_v3-025/feature_engineering_eda_composite.csv
    - analysis/iteration_v3-025/synthesis.md

Track isolation: this script runs on the v3 worktree only. Reads
data/{SYM}/8h.csv + data/features_v3/*.parquet. Zero edits to src/.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

# v3 sacred constants
OOS_CUTOFF_DATE = pd.Timestamp("2025-03-24", tz="UTC")
OOS_CUTOFF_MS = int(OOS_CUTOFF_DATE.value // 1_000_000)

TRAINING_MONTHS = 24
IS_START_TS = OOS_CUTOFF_DATE - pd.DateOffset(months=TRAINING_MONTHS)
IS_START_MS = int(IS_START_TS.value // 1_000_000)

V3_SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

# 13 V3_FEATURE_COLUMNS_TOP_N (the BASELINE feature set after dropping
# both funding variants at iter-v3/025 first commit).
V3_FEATURE_COLUMNS_TOP_N = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
)

# Forward-return horizons for rank-IC check
FWD_HORIZONS = (1, 3, 7)

# Gates
IC_THRESHOLD_HARD = 0.70
IC_THRESHOLD_BRIEF = 0.50
ADF_PVALUE_THRESHOLD = 0.05
RANKIC_MIN = 0.02
COVERAGE_FLOOR_PCT = 80.0

DATA_DIR = Path("data")
ANALYSIS_DIR = Path("analysis/iteration_v3-025")

EPS = 1e-6


def load_klines(symbol: str) -> pd.DataFrame:
    """Read raw 8h kline CSV for symbol."""
    path = DATA_DIR / symbol / "8h.csv"
    if not path.exists():
        raise FileNotFoundError(f"Kline CSV not found: {path}")
    df = pd.read_csv(path)
    df = df.sort_values("open_time").reset_index(drop=True)
    return df


def load_features(symbol: str) -> pd.DataFrame:
    """Read v3 features parquet for symbol."""
    path = DATA_DIR / "features_v3" / f"{symbol}_8h_features.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Features parquet not found: {path}")
    return pd.read_parquet(path)


def slice_is_window(df: pd.DataFrame) -> pd.DataFrame:
    """Filter rows to the IS training window [IS_START_MS, OOS_CUTOFF_MS)."""
    mask = (df["open_time"] >= IS_START_MS) & (df["open_time"] < OOS_CUTOFF_MS)
    return df.loc[mask].copy()


# ----------- Hurst (rescaled-range) — duplicate of regime_v3._rolling_hurst -----------
# Local copy so we can compute hurst_50 (which is NOT in V3_FEATURE_COLUMNS_TOP_N).


def _hurst_rs(window: np.ndarray) -> float:
    n = len(window)
    if n < 20:
        return np.nan
    lags = [5, 10, 20, 30, 50, 80]
    lags = [lag for lag in lags if lag < n]
    if len(lags) < 3:
        return np.nan
    rs_values: list[float] = []
    log_lags: list[float] = []
    for lag in lags:
        chunks = n // lag
        if chunks < 1:
            continue
        r_list: list[float] = []
        for i in range(chunks):
            chunk = window[i * lag : (i + 1) * lag]
            mean = chunk.mean()
            devs = chunk - mean
            cumdev = np.cumsum(devs)
            r = cumdev.max() - cumdev.min()
            s = chunk.std(ddof=1)
            if s > 0 and np.isfinite(r):
                r_list.append(r / s)
        if r_list:
            rs_values.append(np.mean(r_list))
            log_lags.append(np.log(lag))
    if len(rs_values) < 3:
        return np.nan
    log_rs = np.log(rs_values)
    slope, _ = np.polyfit(log_lags, log_rs, 1)
    return float(slope)


def rolling_hurst(log_close: pd.Series, window: int) -> pd.Series:
    """Past-only rolling Hurst exponent."""
    values = log_close.to_numpy()
    out = np.full(len(values), np.nan, dtype=np.float64)
    for i in range(window, len(values) + 1):
        out[i - 1] = _hurst_rs(values[i - window : i])
    return pd.Series(out, index=log_close.index)


# ----------- Fractional differentiation (López de Prado AFML Ch. 5) -----------


def _fracdiff_weights(d: float, size: int) -> np.ndarray:
    """Compute fracdiff weights w[k] for k=0..size-1.

    w[0] = 1.0
    w[k] = -w[k-1] * (d - k + 1) / k
    """
    w = np.zeros(size, dtype=np.float64)
    w[0] = 1.0
    for k in range(1, size):
        w[k] = -w[k - 1] * (d - k + 1) / k
    return w


def fracdiff_fixed_d(series: pd.Series, d: float = 0.5, threshold: float = 1e-3) -> pd.Series:
    """Fractional differentiation with fixed d and FFD weight truncation.

    Truncates the weight series at the first |w[k]| < threshold to keep the
    convolution computationally tractable. Past-only by construction (each
    output uses only past data).
    """
    # Compute weights up to a max horizon
    max_size = min(len(series), 1000)
    w = _fracdiff_weights(d, max_size)
    # Truncate at threshold
    cutoff = max_size
    for k in range(max_size):
        if abs(w[k]) < threshold:
            cutoff = k
            break
    w = w[:cutoff]
    # Convolve (lag-only, past data)
    values = series.to_numpy()
    out = np.full(len(values), np.nan, dtype=np.float64)
    for i in range(cutoff - 1, len(values)):
        window = values[i - cutoff + 1 : i + 1]
        if np.isnan(window).any():
            continue
        out[i] = float(np.dot(w[::-1], window))
    return pd.Series(out, index=series.index)


# ----------- Candidate constructors -----------


def candidate_1_regime_momentum_signed_5d(klines: pd.DataFrame, features: pd.DataFrame) -> pd.Series:
    """ret_5d * sign(hurst_100 - 0.5).

    ret_5d = log(close_t / close_{t-15}) at 8h cadence (15 bars = 5 days).
    sign(hurst_100 - 0.5): +1 if trending, -1 if mean-reverting.
    """
    close = klines["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    # ret_5d = past-only (uses log_close[t-15] vs log_close[t]; .shift(0) is fine
    # because we're computing for *time t* using current close vs close 15 bars ago,
    # both of which are observable at time t)
    ret_5d = log_close - log_close.shift(15)
    # Align hurst_100 from features parquet (already past-only via rolling 100-bar window)
    if "hurst_100" not in features.columns:
        return pd.Series(np.nan, index=klines.index)
    feature_aligned = klines.merge(
        features[["open_time", "hurst_100"]],
        on="open_time",
        how="left",
    )["hurst_100"].astype(float)
    sign_hurst = np.sign(feature_aligned - 0.5)
    sign_hurst = sign_hurst.replace(0, np.nan)  # Pure-RW edge case
    candidate = ret_5d * sign_hurst
    return candidate


def candidate_2_vol_adj_autocorr(klines: pd.DataFrame, features: pd.DataFrame) -> pd.Series:
    """ret_autocorr_lag1_50 / (range_realized_vol_50 + EPS)."""
    if (
        "ret_autocorr_lag1_50" not in features.columns
        or "range_realized_vol_50" not in features.columns
    ):
        return pd.Series(np.nan, index=klines.index)
    aligned = klines.merge(
        features[["open_time", "ret_autocorr_lag1_50", "range_realized_vol_50"]],
        on="open_time",
        how="left",
    )
    autocorr = aligned["ret_autocorr_lag1_50"].astype(float)
    vol = aligned["range_realized_vol_50"].astype(float)
    return autocorr / (vol + EPS)


def candidate_4_cross_asset_divergence_norm(
    klines: pd.DataFrame, features: pd.DataFrame, btc_features: pd.DataFrame | None
) -> pd.Series:
    """(sym_ret_7d - btc_ret_14d) / (vwap_dev_20 + EPS).

    Note: sym_vs_btc_ret_7d (sym_ret_7d - btc_ret_7d) is already in the
    feature set; this candidate uses btc_ret_14d (longer horizon mismatch)
    and normalizes by vwap_dev_20 (mean-reversion intensity).
    """
    close = klines["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    sym_ret_7d = log_close - log_close.shift(21)  # 21 bars = 7 days at 8h
    if (
        "btc_ret_14d" not in features.columns
        or "vwap_dev_20" not in features.columns
    ):
        return pd.Series(np.nan, index=klines.index)
    aligned = klines.merge(
        features[["open_time", "btc_ret_14d", "vwap_dev_20"]],
        on="open_time",
        how="left",
    )
    btc_ret_14d = aligned["btc_ret_14d"].astype(float)
    vwap_dev = aligned["vwap_dev_20"].astype(float)
    return (sym_ret_7d - btc_ret_14d) / (vwap_dev.abs() + EPS)


def candidate_5_hurst_drift_50_200(klines: pd.DataFrame, features: pd.DataFrame) -> pd.Series:
    """hurst_50 - hurst_200.

    hurst_200 is in features parquet (V3_FEATURE_COLUMNS_FULL); hurst_50
    must be computed locally (NOT in TOP_N subset).
    """
    close = klines["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    h50 = rolling_hurst(log_close, 50)
    if "hurst_200" in features.columns:
        aligned = klines.merge(
            features[["open_time", "hurst_200"]],
            on="open_time",
            how="left",
        )
        h200 = aligned["hurst_200"].astype(float)
    else:
        h200 = rolling_hurst(log_close, 200)
    return h50 - h200


def candidate_6_fracdiff_d05_close(klines: pd.DataFrame, features: pd.DataFrame) -> pd.Series:
    """Fractional differentiation of log(close) at d=0.5 (López de Prado AFML Ch. 5).

    Past-only by FFD construction. Not normalized — leave the model to figure
    out the scale (LightGBM is split-based, scale-invariant in any single
    feature). For interpretability and stability, we apply the FFD-truncated
    fracdiff with threshold=1e-3.
    """
    close = klines["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    return fracdiff_fixed_d(log_close, d=0.5, threshold=1e-3)


def candidate_7_ret_kurt_to_skew_ratio(klines: pd.DataFrame, features: pd.DataFrame) -> pd.Series:
    """ret_kurt_50 / (|ret_skew_50| + EPS)."""
    if "ret_kurt_50" not in features.columns or "ret_skew_50" not in features.columns:
        return pd.Series(np.nan, index=klines.index)
    aligned = klines.merge(
        features[["open_time", "ret_kurt_50", "ret_skew_50"]],
        on="open_time",
        how="left",
    )
    kurt = aligned["ret_kurt_50"].astype(float)
    skew = aligned["ret_skew_50"].astype(float)
    return kurt / (skew.abs() + EPS)


# ----------- Per-candidate evaluators -----------


def evaluate_candidate(
    name: str,
    series: pd.Series,
    klines: pd.DataFrame,
    features: pd.DataFrame,
    symbol: str,
) -> dict:
    """Compute distribution + IC + ADF + rank-IC for *series* on IS window.

    Returns a row dict for the per-candidate composite output.
    """
    # IS slice
    is_klines = slice_is_window(klines)
    is_klines = is_klines.reset_index(drop=True)
    is_features = slice_is_window(features).reset_index(drop=True)
    # Re-compute candidate on IS slice (some candidates rely on features
    # parquet which was loaded full; need .reset_index aligned with klines)
    series = series.iloc[
        klines.index[(klines["open_time"] >= IS_START_MS) & (klines["open_time"] < OOS_CUTOFF_MS)]
    ].reset_index(drop=True)

    # Distribution
    dist_n = int(series.notna().sum())
    dist_pct = 100.0 * dist_n / max(len(series), 1)
    if dist_n > 0:
        s = series.dropna()
        # Clip extreme outliers for distribution stat reporting
        dist_mean = float(s.mean())
        dist_std = float(s.std(ddof=1)) if dist_n > 1 else 0.0
        dist_min = float(s.min())
        dist_max = float(s.max())
        dist_p01 = float(s.quantile(0.01))
        dist_p99 = float(s.quantile(0.99))
        # Outlier check: ratio of |max-min| / std should be reasonable
        outlier_ratio = (dist_max - dist_min) / max(dist_std, EPS)
    else:
        dist_mean = dist_std = dist_min = dist_max = dist_p01 = dist_p99 = float("nan")
        outlier_ratio = float("nan")

    # IC vs 13 V3_FEATURE_COLUMNS
    max_abs_ic = 0.0
    max_abs_ic_feature = "<none>"
    n_ic_features = 0
    for fc in V3_FEATURE_COLUMNS_TOP_N:
        if fc not in is_features.columns:
            continue
        # Align series to is_features index
        if len(series) != len(is_features):
            # Mismatch — shouldn't happen if both sliced the same window
            continue
        sub = pd.DataFrame({"cand": series.values, "feat": is_features[fc].values}).dropna()
        if len(sub) < 100:
            continue
        ic = float(sub["cand"].corr(sub["feat"], method="spearman"))
        if not np.isnan(ic) and abs(ic) > max_abs_ic:
            max_abs_ic = abs(ic)
            max_abs_ic_feature = fc
        n_ic_features += 1

    # ADF stationarity
    s_for_adf = series.dropna()
    if len(s_for_adf) >= 100:
        try:
            _, adf_p, _, _, _, _ = adfuller(s_for_adf, autolag="AIC")
            adf_p = float(adf_p)
        except Exception:
            adf_p = float("nan")
    else:
        adf_p = float("nan")

    # Rank-IC vs forward returns
    close = is_klines["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    log_ret = log_close.diff()
    rankic_h = {}
    for h in FWD_HORIZONS:
        fwd_ret = log_ret.shift(-h).rolling(window=h).sum()
        sub = pd.DataFrame({"cand": series.values, "fwd": fwd_ret.values}).dropna()
        if len(sub) < 100:
            rankic_h[h] = float("nan")
        else:
            rankic_h[h] = float(sub["cand"].corr(sub["fwd"], method="spearman"))
    max_abs_rankic = max(
        (abs(v) for v in rankic_h.values() if not np.isnan(v)),
        default=float("nan"),
    )

    return {
        "candidate": name,
        "symbol": symbol,
        "n_valid": dist_n,
        "coverage_pct": round(dist_pct, 4),
        "mean": round(dist_mean, 6) if not np.isnan(dist_mean) else None,
        "std": round(dist_std, 6) if not np.isnan(dist_std) else None,
        "p01": round(dist_p01, 6) if not np.isnan(dist_p01) else None,
        "p99": round(dist_p99, 6) if not np.isnan(dist_p99) else None,
        "outlier_ratio_range_over_std": round(outlier_ratio, 4)
        if not np.isnan(outlier_ratio)
        else None,
        "max_abs_ic_vs_13_features": round(max_abs_ic, 6),
        "max_abs_ic_feature": max_abs_ic_feature,
        "n_ic_features": n_ic_features,
        "ic_passes_brief_target_lt_0p50": max_abs_ic < IC_THRESHOLD_BRIEF,
        "ic_passes_hard_gate_lt_0p70": max_abs_ic < IC_THRESHOLD_HARD,
        "adf_pvalue": round(adf_p, 6) if not np.isnan(adf_p) else None,
        "adf_passes": adf_p < ADF_PVALUE_THRESHOLD if not np.isnan(adf_p) else False,
        "rankic_h1": round(rankic_h[1], 6) if not np.isnan(rankic_h[1]) else None,
        "rankic_h3": round(rankic_h[3], 6) if not np.isnan(rankic_h[3]) else None,
        "rankic_h7": round(rankic_h[7], 6) if not np.isnan(rankic_h[7]) else None,
        "max_abs_rankic": round(max_abs_rankic, 6) if not np.isnan(max_abs_rankic) else None,
        "rankic_passes_min_0p02": max_abs_rankic >= RANKIC_MIN
        if not np.isnan(max_abs_rankic)
        else False,
    }


# ----------- Composite scoring -----------


def composite_score(rows_for_candidate: list[dict]) -> dict:
    """Aggregate per-symbol rows into a single composite score per candidate.

    Score components (each on [0, 1] scale):
        - orthogonality_score = 1 - (max_abs_ic / 0.50). Clipped to [0, 1].
        - rankic_score = max_abs_rankic / 0.10. Clipped to [0, 1].
        - stability_score = (coverage_pct / 100) AND (adf_passes).
        - interpretability_score = HARD-CODED prior per candidate (see below).
        - implementation_cost_score = HARD-CODED prior per candidate.

    Final composite = 0.30 × orthogonality + 0.30 × rankic + 0.20 × stability +
                      0.10 × interpretability + 0.10 × (1 - impl_cost).
    """
    if not rows_for_candidate:
        return {
            "candidate": "<unknown>",
            "composite_score": 0.0,
            "passes_brief_gate": False,
        }
    candidate = rows_for_candidate[0]["candidate"]

    # Aggregate across symbols (max IC is the worst-case orthogonality;
    # max rank-IC across symbols is the best-case predictive signal).
    max_ic = max(r["max_abs_ic_vs_13_features"] for r in rows_for_candidate)
    max_rankic = max(
        (r["max_abs_rankic"] or 0.0) for r in rows_for_candidate
    )
    min_coverage = min(r["coverage_pct"] for r in rows_for_candidate)
    all_adf_pass = all(r["adf_passes"] for r in rows_for_candidate)

    orthogonality_score = max(0.0, min(1.0, 1.0 - (max_ic / IC_THRESHOLD_BRIEF)))
    rankic_score = max(0.0, min(1.0, max_rankic / 0.10))
    stability_score = (
        (min_coverage / 100.0) * (1.0 if all_adf_pass else 0.5)
    )

    # Hard-coded priors (these are JUDGMENT calls per the methodology section)
    interpretability_priors = {
        "regime_momentum_signed_5d": 1.0,  # textbook trader heuristic
        "vol_adj_autocorr": 0.6,
        "cross_asset_divergence_norm": 0.7,
        "hurst_drift_50_200": 0.5,
        "fracdiff_d05_close": 0.7,  # canonical AFML; high for ML researchers
        "ret_kurt_to_skew_ratio": 0.4,
    }
    impl_cost_priors = {
        "regime_momentum_signed_5d": 0.1,  # very simple
        "vol_adj_autocorr": 0.1,
        "cross_asset_divergence_norm": 0.2,
        "hurst_drift_50_200": 0.3,  # need to compute hurst_50 (slow)
        "fracdiff_d05_close": 0.4,  # FFD weights + convolution overhead
        "ret_kurt_to_skew_ratio": 0.1,
    }
    interp = interpretability_priors.get(candidate, 0.5)
    impl = impl_cost_priors.get(candidate, 0.5)

    composite = (
        0.30 * orthogonality_score
        + 0.30 * rankic_score
        + 0.20 * stability_score
        + 0.10 * interp
        + 0.10 * (1.0 - impl)
    )

    return {
        "candidate": candidate,
        "max_abs_ic_vs_13_features": round(max_ic, 6),
        "max_abs_rankic_across_horizons_and_symbols": round(max_rankic, 6),
        "min_coverage_pct": round(min_coverage, 4),
        "all_adf_pass": all_adf_pass,
        "orthogonality_score": round(orthogonality_score, 4),
        "rankic_score": round(rankic_score, 4),
        "stability_score": round(stability_score, 4),
        "interpretability_prior": interp,
        "implementation_cost_prior": impl,
        "composite_score": round(composite, 4),
        "passes_brief_gate": (
            max_ic < IC_THRESHOLD_BRIEF
            and (max_rankic >= RANKIC_MIN)
            and all_adf_pass
            and (min_coverage >= COVERAGE_FLOOR_PCT)
        ),
    }


# ----------- Main -----------


def main() -> int:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    print(
        f"[iter-v3/025] feature_engineering_eda — IS window {IS_START_TS} → {OOS_CUTOFF_DATE}"
    )
    print(f"  V3_SYMBOLS = {V3_SYMBOLS}")
    print(f"  Evaluating 6 candidates (#3 adx_signed_momentum REJECTED — adx not in feature set)")

    # Per-symbol per-candidate rows
    distribution_rows: list[dict] = []
    correlation_rows: list[dict] = []
    rankic_rows: list[dict] = []
    adf_rows: list[dict] = []
    composite_rows: list[dict] = []

    # Group all rows for each candidate to compute composite
    candidate_to_rows: dict[str, list[dict]] = {}

    for symbol in V3_SYMBOLS:
        print(f"\n[ENV] {symbol}")
        klines = load_klines(symbol)
        features = load_features(symbol)
        # Construct each candidate
        candidates: dict[str, pd.Series] = {
            "regime_momentum_signed_5d": candidate_1_regime_momentum_signed_5d(klines, features),
            "vol_adj_autocorr": candidate_2_vol_adj_autocorr(klines, features),
            "cross_asset_divergence_norm": candidate_4_cross_asset_divergence_norm(
                klines, features, None
            ),
            "hurst_drift_50_200": candidate_5_hurst_drift_50_200(klines, features),
            "fracdiff_d05_close": candidate_6_fracdiff_d05_close(klines, features),
            "ret_kurt_to_skew_ratio": candidate_7_ret_kurt_to_skew_ratio(klines, features),
        }

        for name, series in candidates.items():
            row = evaluate_candidate(name, series, klines, features, symbol)
            distribution_rows.append(
                {
                    "candidate": name,
                    "symbol": symbol,
                    "n_valid": row["n_valid"],
                    "coverage_pct": row["coverage_pct"],
                    "mean": row["mean"],
                    "std": row["std"],
                    "p01": row["p01"],
                    "p99": row["p99"],
                    "outlier_ratio_range_over_std": row["outlier_ratio_range_over_std"],
                }
            )
            correlation_rows.append(
                {
                    "candidate": name,
                    "symbol": symbol,
                    "max_abs_ic_vs_13_features": row["max_abs_ic_vs_13_features"],
                    "max_abs_ic_feature": row["max_abs_ic_feature"],
                    "n_ic_features_compared": row["n_ic_features"],
                    "ic_passes_brief_target_lt_0p50": row["ic_passes_brief_target_lt_0p50"],
                    "ic_passes_hard_gate_lt_0p70": row["ic_passes_hard_gate_lt_0p70"],
                }
            )
            rankic_rows.append(
                {
                    "candidate": name,
                    "symbol": symbol,
                    "rankic_h1": row["rankic_h1"],
                    "rankic_h3": row["rankic_h3"],
                    "rankic_h7": row["rankic_h7"],
                    "max_abs_rankic": row["max_abs_rankic"],
                    "rankic_passes_min_0p02": row["rankic_passes_min_0p02"],
                }
            )
            adf_rows.append(
                {
                    "candidate": name,
                    "symbol": symbol,
                    "adf_pvalue": row["adf_pvalue"],
                    "adf_passes": row["adf_passes"],
                }
            )
            candidate_to_rows.setdefault(name, []).append(row)
            print(
                f"  {name:30s} max|IC|={row['max_abs_ic_vs_13_features']:.4f}, "
                f"max|rankIC|={row['max_abs_rankic']:.4f}, "
                f"ADF p={row['adf_pvalue']:.4f}, "
                f"cov={row['coverage_pct']:.1f}%"
            )

    # Composite scoring
    for name, rows in candidate_to_rows.items():
        composite_rows.append(composite_score(rows))

    # Sort by composite score descending
    composite_rows.sort(key=lambda r: r["composite_score"], reverse=True)

    # Write CSVs
    pd.DataFrame(distribution_rows).to_csv(
        ANALYSIS_DIR / "feature_engineering_eda_distribution.csv", index=False
    )
    pd.DataFrame(correlation_rows).to_csv(
        ANALYSIS_DIR / "feature_engineering_eda_correlation.csv", index=False
    )
    pd.DataFrame(rankic_rows).to_csv(
        ANALYSIS_DIR / "feature_engineering_eda_rankic.csv", index=False
    )
    pd.DataFrame(adf_rows).to_csv(
        ANALYSIS_DIR / "feature_engineering_eda_adf.csv", index=False
    )
    pd.DataFrame(composite_rows).to_csv(
        ANALYSIS_DIR / "feature_engineering_eda_composite.csv", index=False
    )

    # Top candidate
    top = composite_rows[0]

    # Synthesis
    candidates_passing_brief_gate = [
        r for r in composite_rows if r.get("passes_brief_gate")
    ]
    n_pass = len(candidates_passing_brief_gate)

    leaderboard_lines = []
    for i, r in enumerate(composite_rows, 1):
        leaderboard_lines.append(
            f"{i}. {r['candidate']:30s}  composite={r['composite_score']:.4f}  "
            f"max|IC|={r['max_abs_ic_vs_13_features']:.4f}  "
            f"max|rankIC|={r['max_abs_rankic_across_horizons_and_symbols']:.4f}  "
            f"ADF={'PASS' if r['all_adf_pass'] else 'FAIL'}  "
            f"brief_gate={'PASS' if r.get('passes_brief_gate') else 'fail'}"
        )

    synthesis = f"""# iter-v3/025 — Feature Engineering EDA Synthesis

## Mission

Per user directive 2026-05-08 + Critic FINAL Recommendation of iter-v3/024
(SHA `5a47f5d`): pivot from off-the-shelf indicator additions (3 of 3 INERT
in v3 catalog: iter-v3/015 microstructure, iter-v3/019 funding, iter-v3/024
BTC funding) toward genuine **engineered features** — composed/interaction
features built from existing 13-feature primitives that depth-3-5 LightGBM
trees cannot construct internally.

## Candidates Evaluated (6 of 7)

Candidate #3 (adx_signed_momentum) REJECTED because adx is a v3 GATE not a
feature column at the per-symbol architecture; adding adx as a feature would
itself be a separate axis (off-the-shelf indicator addition, contradicting
the pivot intent).

Remaining 6 candidates evaluated:
1. regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)
2. vol_adj_autocorr = ret_autocorr_lag1_50 / (range_realized_vol_50 + EPS)
4. cross_asset_divergence_norm = (sym_ret_7d − btc_ret_14d) / (vwap_dev_20 + EPS)
5. hurst_drift_50_200 = hurst_50 − hurst_200
6. fracdiff_d05_close = fracdiff(log(close), d=0.5) [López de Prado AFML Ch. 5]
7. ret_kurt_to_skew_ratio = ret_kurt_50 / (|ret_skew_50| + EPS)

## Composite Scoring

Score = 0.30 × orthogonality + 0.30 × rankIC magnitude + 0.20 × stability
        + 0.10 × interpretability_prior + 0.10 × (1 − implementation_cost_prior)

All scores on [0, 1]. Higher is better.

## Leaderboard (sorted by composite score, highest first)

```
{chr(10).join(leaderboard_lines)}
```

## Brief gates (per candidate)

- Coverage IS window per symbol: ≥ {COVERAGE_FLOOR_PCT}%
- Max |IC| vs 13 V3_FEATURE_COLUMNS: < {IC_THRESHOLD_BRIEF} (BRIEF target;
  hard gate at < {IC_THRESHOLD_HARD})
- ADF p-value: < {ADF_PVALUE_THRESHOLD} per symbol
- Max |rank-IC| vs forward returns: ≥ {RANKIC_MIN} on at least 1 horizon

Candidates passing ALL 4 brief gates: {n_pass} of 6

## RECOMMENDATION

**TOP candidate (composite score {top['composite_score']:.4f}):
`{top['candidate']}`**

Pre-commit per iter-v3/024 diary `Pre-Commit for iter-v3/025` section:
**iter-v3/025 axis = `regime_momentum_signed_5d`** = ret_5d × sign(hurst_100 − 0.5).

Rationale (independent of leaderboard rank — single-axis discipline):
- Tests "model can't compose" hypothesis directly: hurst_100 is rank 8 on
  BCH (importance=31) and rank 10 on LDO (importance=86) at iter-v3/024;
  ret_5d derivative is in the labeling pipeline but NOT as a feature column.
- The interaction (regime-conditional momentum) is a textbook trader
  heuristic (momentum "works" in trending markets, fails in mean-reverting
  markets) that depth-3-5 LightGBM trees cannot construct from raw inputs
  at the candidate-split level (each split is on a SINGLE feature; nested
  interaction would consume splits that are otherwise spent on the actual
  decision boundary).
- Implementation cost LOW: composes existing primitives (close, hurst_100).
- Interpretability HIGH: regime-conditional momentum is part of standard
  systematic-trading toolkit (Robert Carver, Ernest Chan).

The composite score may rank a different candidate higher (e.g., fracdiff
or hurst_drift) — but the iter-v3/024 diary pre-commit binds the iter-v3/025
axis. Cannot be renegotiated post-hoc per `feedback_v3_engineered_feature_pivot.md`
(to be committed at iter-v3/025 setup).

## Files

- analysis/iteration_v3-025/feature_engineering_eda_distribution.csv
- analysis/iteration_v3-025/feature_engineering_eda_correlation.csv
- analysis/iteration_v3-025/feature_engineering_eda_rankic.csv
- analysis/iteration_v3-025/feature_engineering_eda_adf.csv
- analysis/iteration_v3-025/feature_engineering_eda_composite.csv
"""
    (ANALYSIS_DIR / "synthesis.md").write_text(synthesis)
    print("\n" + synthesis)

    print(f"\n[OK] EDA complete. Top candidate: {top['candidate']} "
          f"(composite score {top['composite_score']:.4f}). "
          f"Brief gates pass: {n_pass} / 6 candidates.")
    print("Note: iter-v3/025 axis pre-committed via iter-v3/024 diary = "
          "regime_momentum_signed_5d (independent of composite ranking).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
