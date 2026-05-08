"""
iter-v3/027 — THIRD engineered feature EDA (DIFFERENT engineered feature ALONE)
=================================================================================

Per Critic FINAL Recommendation of iter-v3/026 (SHA `8839bbb`) + user directive
2026-05-08 + diary lessons (a)-(g) of iter-v3/026:

iter-v3/025 PROMISING-clean: `regime_momentum_signed_5d` (= ret_5d × sign(hurst_100 − 0.5))
landed PATH A unambiguously (importance 51% top portfolio; IS +0.50 / OOS +0.84 vs anchor).

iter-v3/026 NEGATIVE-SUSPICIOUS-OOS: stacking `vol_adj_autocorr` ON TOP produced IS Sharpe
collapse to +0.0493 (lowest in post-bootstrap; PATH C fires) + OOS spike to +1.4501 with
27× IS/OOS daily Sharpe ratio (structurally absurd; iter-v3/013 lottery precedent +
worst IS MaxDD in v3 history at 51.37% + BCH 78% concentration regression). Falsifier 4
PASSES (vol_adj_autocorr importance 283 = 45% of top — feature USED, NOT INERT). Mechanism:
combining 2 engineered features at single-seed n_trials=35 expands Optuna search space
beyond depth-3-5 LightGBM's representational capacity.

NEW memory rule `feedback_v3_engineered_features_dont_stack.md` (established at
iter-v3/026 closeout): test ONE engineered feature alone at single-seed; defer stacking
to multi-seed CONFIRMATION (iter-v3/029+).

iter-v3/027 axis = DIFFERENT engineered feature ALONE on top of regime_momentum:
- DROP `vol_adj_autocorr` from V3_FEATURE_COLUMNS (revert 15 → 14)
- KEEP `regime_momentum_signed_5d` (proven at iter-v3/025; do NOT revert)
- ADD a NEW engineered feature alone (14 → 15 with new feature)

Critic FINAL Recommendation of iter-v3/026 pre-commits `cross_asset_divergence_norm` as
the recommended candidate (different mechanism from regime_momentum: relative-strength
normalized; uses existing primitives; lowest implementation cost with non-overlapping
mechanism; #1 EDA leaderboard at iter-v3/025 SHA `917605b` with composite 0.6500).

Per `feedback_v3_engineered_features_proven.md` (established at iter-v3/025 closeout):
- Off-the-shelf NEW features (microstructure, funding, BTC funding) all hit rank 14/14 INERT
- Engineered/composed features are HIGHEST-priority axis category for the remainder of the
  post-bootstrap cycle (iter-v3/026/027/028)
- IC orthogonality CARVE-OUT applies (composed features mechanically correlate with primitives;
  per `feedback_v3_engineered_feature_pivot.md` the binding gate is feature-importance
  rank ≤10 + importance ≥30)

This EDA evaluates 4 candidates ALONE on top of the iter-v3/025 14-feature stack (which
already contains regime_momentum_signed_5d but NOT vol_adj_autocorr — iter-v3/027 reverts
the iter-v3/026 stacking). Pre-commit binds to candidate #1 (cross_asset_divergence_norm)
per Critic FINAL Rec; remaining 3 candidates evaluated as fallbacks for iter-v3/028+ if
iter-v3/027 lands PATH B/C.

Methodology — composite score per candidate (mirrors iter-v3/026 weights):
    1. Compute candidate per-symbol on IS-only window (BCH+LDO+TRX × 24mo).
    2. Spearman IC vs each of the 14 V3_FEATURE_COLUMNS (orthogonality).
       Hard gate < 0.70 + brief target < 0.50 — INFORMATIONAL ONLY for engineered features
       per `feedback_v3_engineered_feature_pivot.md` IC carve-out.
       The composed feature regime_momentum_signed_5d is ALSO present in this 14-feature
       reference set — i.e., we measure each candidate's correlation against the iter-v3/025
       PROMISING engineered feature too, to flag mechanistic redundancy.
    3. ADF stationarity test on candidate series per symbol (p < 0.05).
    4. Distribution stability — coverage_pct, outlier_ratio.
    5. Rank-IC vs forward 1/3/7-bar log-returns per symbol (IC carve-out only relaxes IC
       gate, not predictive-information gate).
    6. ORTHOGONALITY-TO-REGIME-MOMENTUM check: max |IC| of candidate vs the iter-v3/025
       PROMISING engineered feature. Lower = more orthogonal mechanism = better candidate.

Candidates (4 evaluated; #1 is the Critic-named recommendation per iter-v3/026):
    1. cross_asset_divergence_norm = (sym_ret_7d − btc_ret_14d) / (|vwap_dev_20| + EPS)
       Mechanism: RELATIVE-STRENGTH NORMALIZED. Captures alt-altcoin divergence with
       vol-context. Different mechanism from regime_momentum (regime-conditional momentum)
       AND from vol_adj_autocorr (per-unit-vol persistence — DROPPED at iter-v3/027).
       Note: sym_vs_btc_ret_7d already in feature set (rank 13); this candidate uses
       btc_ret_14d (mismatch horizon) AND normalizes by vwap_dev_20 — distinct mechanism
       from sym_vs_btc_ret_7d already in 14-feature set.
       Implementation cost: LOWEST among non-overlapping-mechanism candidates.
       Interpretability: MEDIUM-HIGH (relative-strength normalization is standard
       systematic-trading toolkit per Robert Carver, Ernest Chan).

    2. ret_kurt_to_skew_ratio = ret_kurt_50 / (|ret_skew_50| + EPS)
       Mechanism: fat-tail to asymmetry ratio. Both source primitives in 14-feature set;
       the ratio normalizes fat-tail intensity by directional asymmetry.
       Implementation cost: LOW.
       Interpretability: LOW-MEDIUM.
       At iter-v3/026 EDA: composite 0.7322 (#1 leaderboard). Held back as iter-v3/028
       fallback if iter-v3/027 PATH B/C.

    3. fracdiff_d05_close = fracdiff(log(close), d=0.5) [López de Prado AFML Ch. 5]
       Mechanism: preserves memory while achieving stationarity at d=0.5. v3 skill mandate
       from iter-v3/001 brief — never delivered. Fracdiff_v3 module exists; this is a
       d=0.5 fixed-point variant of the auto-d* fracdiff already in V3_FEATURE_COLUMNS.
       Implementation cost: LOW.
       Interpretability: LOW for traders, HIGH for ML researchers.
       At iter-v3/026 EDA: ADF FAIL on TRX (p=0.229). Re-evaluated here.

    4. hurst_drift_50_200 = hurst_50 − hurst_200 (multi-timeframe regime drift)
       Mechanism: trend-vs-mean-reversion regime DRIFT — short-window Hurst minus
       long-window Hurst. Captures regime CHANGES (vs regime_momentum which captures
       regime LEVEL).
       NOTE: Requires hurst_50 and hurst_200 primitives. hurst_200 IS in V3_FEATURE_COLUMNS_FULL
       (computed by add_regime_v3_features) — verify before computing.
       Implementation cost: MEDIUM (may require adding hurst_50 primitive if not present).
       Interpretability: HIGH.

Inputs read (IS-only — training window pre-OOS_CUTOFF_DATE 2025-03-24):
    - data/{BCH,LDO,TRX}USDT/8h.csv — 8h klines (for close, high, low)
    - data/features_v3/{BCH,LDO,TRX}USDT_8h_features.parquet — features parquet
      (must contain regime_momentum_signed_5d for stack-on-top correlation check)

Outputs (committed BEFORE the brief — Phase 5.5 reproducibility requirement):
    - analysis/iteration_v3-027/third_engineered_eda_distribution.csv
    - analysis/iteration_v3-027/third_engineered_eda_correlation.csv
    - analysis/iteration_v3-027/third_engineered_eda_rankic.csv
    - analysis/iteration_v3-027/third_engineered_eda_adf.csv
    - analysis/iteration_v3-027/third_engineered_eda_composite.csv
    - analysis/iteration_v3-027/synthesis.md

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

# 14 V3_FEATURE_COLUMNS_TOP_N (the iter-v3/025 PROMISING stack — includes
# regime_momentum_signed_5d; DOES NOT include vol_adj_autocorr — iter-v3/027 reverts).
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
    "regime_momentum_signed_5d",  # iter-v3/025 PROMISING engineered feature
)

# The iter-v3/025 PROMISING engineered feature — used for the
# orthogonality-to-regime-momentum check (mechanistic redundancy diagnostic).
ITER_25_ENGINEERED_FEATURE = "regime_momentum_signed_5d"

# Forward-return horizons for rank-IC check
FWD_HORIZONS = (1, 3, 7)

# Gates
IC_THRESHOLD_HARD = 0.70
IC_THRESHOLD_BRIEF = 0.50
ADF_PVALUE_THRESHOLD = 0.05
RANKIC_MIN = 0.02
COVERAGE_FLOOR_PCT = 80.0

DATA_DIR = Path("data")
ANALYSIS_DIR = Path("analysis/iteration_v3-027")

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
    """Fractional differentiation with fixed d and FFD weight truncation."""
    max_size = min(len(series), 1000)
    w = _fracdiff_weights(d, max_size)
    cutoff = max_size
    for k in range(max_size):
        if abs(w[k]) < threshold:
            cutoff = k
            break
    w = w[:cutoff]
    values = series.to_numpy()
    out = np.full(len(values), np.nan, dtype=np.float64)
    for i in range(cutoff - 1, len(values)):
        window = values[i - cutoff + 1 : i + 1]
        if np.isnan(window).any():
            continue
        out[i] = float(np.dot(w[::-1], window))
    return pd.Series(out, index=series.index)


# ----------- Hurst exponent (R/S analysis) — for hurst_drift_50_200 candidate -----------


def _rolling_hurst(values: np.ndarray, window: int) -> np.ndarray:
    """Rolling Hurst exponent via R/S analysis, past-only.

    Output[i] uses values[i-window:i] (past-only; first valid value at index window).
    """
    n = len(values)
    out = np.full(n, np.nan, dtype=np.float64)
    if n < window:
        return out
    for i in range(window, n):
        sub = values[i - window:i]
        if np.isnan(sub).any():
            continue
        rs = _rs_stat(sub)
        if rs is None or rs <= 0:
            continue
        out[i] = float(np.log(rs) / np.log(window))
    return out


def _rs_stat(sub: np.ndarray) -> float | None:
    """Rescaled-range stat for a single window (R / S)."""
    diffs = np.diff(sub)
    if len(diffs) == 0:
        return None
    mean = diffs.mean()
    z = diffs - mean
    cumsum = np.cumsum(z)
    R = float(cumsum.max() - cumsum.min())
    S = float(diffs.std(ddof=0))
    if S < EPS:
        return None
    return R / S


# ----------- Candidate constructors -----------


def candidate_1_cross_asset_divergence_norm(
    klines: pd.DataFrame, features: pd.DataFrame
) -> pd.Series:
    """(sym_ret_7d − btc_ret_14d) / (|vwap_dev_20| + EPS).

    Past-only construction:
    - sym_ret_7d = log(close_t / close_{t-21}) at 8h cadence (21 bars × 8h = 7 days)
    - btc_ret_14d already past-only via add_cross_btc_v3_features (42-bar trailing window)
    - vwap_dev_20 already past-only via add_volume_micro_v3_features (20-bar trailing VWAP)

    Mechanism: relative-strength normalized by mean-reversion intensity. Captures
    alt-altcoin divergence with vol-context. Distinct from sym_vs_btc_ret_7d (already
    in feature set) by using btc_ret_14d (mismatch horizon) + vwap_dev_20 normalization.
    """
    close = klines["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    sym_ret_7d = log_close - log_close.shift(21)  # 21 bars = 7 days at 8h
    if "btc_ret_14d" not in features.columns or "vwap_dev_20" not in features.columns:
        return pd.Series(np.nan, index=klines.index)
    aligned = klines.merge(
        features[["open_time", "btc_ret_14d", "vwap_dev_20"]],
        on="open_time",
        how="left",
    )
    btc_ret_14d = aligned["btc_ret_14d"].astype(float)
    vwap_dev = aligned["vwap_dev_20"].astype(float)
    return (sym_ret_7d - btc_ret_14d) / (vwap_dev.abs() + EPS)


def candidate_2_ret_kurt_to_skew_ratio(klines: pd.DataFrame, features: pd.DataFrame) -> pd.Series:
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


def candidate_3_fracdiff_d05_close(klines: pd.DataFrame, features: pd.DataFrame) -> pd.Series:
    """Fractional differentiation of log(close) at d=0.5 (López de Prado AFML Ch. 5)."""
    close = klines["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    return fracdiff_fixed_d(log_close, d=0.5, threshold=1e-3)


def candidate_4_hurst_drift_50_200(klines: pd.DataFrame, features: pd.DataFrame) -> pd.Series:
    """hurst_50 − hurst_200 (multi-timeframe regime drift).

    NOTE: hurst_200 IS in V3_FEATURE_COLUMNS_FULL (computed by add_regime_v3_features).
    hurst_50 is NOT pre-computed; this function reconstructs it via R/S analysis on
    log-returns (matches add_regime_v3_features methodology).

    Past-only by construction:
    - hurst_50 reconstructed via 50-bar trailing R/S window (returns at i-50:i)
    - hurst_200 from features parquet (already past-only via 200-bar trailing window)
    """
    if "hurst_200" not in features.columns:
        return pd.Series(np.nan, index=klines.index)
    aligned = klines.merge(
        features[["open_time", "hurst_200"]],
        on="open_time",
        how="left",
    )
    close = aligned["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    log_ret = log_close.diff().to_numpy()
    hurst_50 = _rolling_hurst(log_ret, 50)
    hurst_200 = aligned["hurst_200"].astype(float).to_numpy()
    return pd.Series(hurst_50 - hurst_200, index=aligned.index)


# ----------- regime_momentum reconstruction (in case parquet lacks the column) -----------


def reconstruct_regime_momentum(klines: pd.DataFrame, features: pd.DataFrame) -> pd.Series:
    """Reconstruct iter-v3/025's regime_momentum_signed_5d if missing from features parquet."""
    close = klines["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    ret_5d = log_close - log_close.shift(15)
    if "hurst_100" not in features.columns:
        return pd.Series(np.nan, index=klines.index)
    aligned = klines.merge(
        features[["open_time", "hurst_100"]],
        on="open_time",
        how="left",
    )
    hurst = aligned["hurst_100"].astype(float)
    sign_hurst = np.sign(hurst - 0.5)
    sign_hurst = sign_hurst.replace(0, np.nan)
    return ret_5d * sign_hurst


# ----------- Per-candidate evaluators -----------


def evaluate_candidate(
    name: str,
    series: pd.Series,
    klines: pd.DataFrame,
    features: pd.DataFrame,
    symbol: str,
) -> dict:
    """Compute distribution + IC + ADF + rank-IC for *series* on IS window."""
    is_klines = slice_is_window(klines).reset_index(drop=True)
    is_features = slice_is_window(features).reset_index(drop=True)
    series = series.iloc[
        klines.index[(klines["open_time"] >= IS_START_MS) & (klines["open_time"] < OOS_CUTOFF_MS)]
    ].reset_index(drop=True)

    # Distribution
    dist_n = int(series.notna().sum())
    dist_pct = 100.0 * dist_n / max(len(series), 1)
    if dist_n > 0:
        s = series.dropna()
        dist_mean = float(s.mean())
        dist_std = float(s.std(ddof=1)) if dist_n > 1 else 0.0
        dist_min = float(s.min())
        dist_max = float(s.max())
        dist_p01 = float(s.quantile(0.01))
        dist_p99 = float(s.quantile(0.99))
        outlier_ratio = (dist_max - dist_min) / max(dist_std, EPS)
    else:
        dist_mean = dist_std = dist_min = dist_max = dist_p01 = dist_p99 = float("nan")
        outlier_ratio = float("nan")

    # IC vs 14 V3_FEATURE_COLUMNS (includes regime_momentum_signed_5d)
    max_abs_ic = 0.0
    max_abs_ic_feature = "<none>"
    n_ic_features = 0
    for fc in V3_FEATURE_COLUMNS_TOP_N:
        if fc not in is_features.columns:
            continue
        if len(series) != len(is_features):
            continue
        sub = pd.DataFrame({"cand": series.values, "feat": is_features[fc].values}).dropna()
        if len(sub) < 100:
            continue
        ic = float(sub["cand"].corr(sub["feat"], method="spearman"))
        if not np.isnan(ic) and abs(ic) > max_abs_ic:
            max_abs_ic = abs(ic)
            max_abs_ic_feature = fc
        n_ic_features += 1

    # ORTHOGONALITY-TO-REGIME-MOMENTUM
    if ITER_25_ENGINEERED_FEATURE in is_features.columns:
        rm_aligned = is_features[ITER_25_ENGINEERED_FEATURE].astype(float).reset_index(drop=True)
    else:
        rm = reconstruct_regime_momentum(klines, features)
        rm_aligned = (
            rm.iloc[
                klines.index[
                    (klines["open_time"] >= IS_START_MS) & (klines["open_time"] < OOS_CUTOFF_MS)
                ]
            ].reset_index(drop=True)
        )
    sub_rm = pd.DataFrame({"cand": series.values, "rm": rm_aligned.values}).dropna()
    if len(sub_rm) >= 100:
        ic_vs_rm = abs(float(sub_rm["cand"].corr(sub_rm["rm"], method="spearman")))
    else:
        ic_vs_rm = float("nan")

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
        "max_abs_ic_vs_14_features": round(max_abs_ic, 6),
        "max_abs_ic_feature": max_abs_ic_feature,
        "n_ic_features_compared": n_ic_features,
        "max_abs_ic_vs_regime_momentum": round(ic_vs_rm, 6) if not np.isnan(ic_vs_rm) else None,
        "ic_passes_brief_target_lt_0p50_INFORMATIONAL": max_abs_ic < IC_THRESHOLD_BRIEF,
        "ic_passes_hard_gate_lt_0p70_INFORMATIONAL": max_abs_ic < IC_THRESHOLD_HARD,
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


# ----------- Composite scoring (mirrors iter-v3/026 weights) -----------


def composite_score(rows_for_candidate: list[dict]) -> dict:
    """Aggregate per-symbol rows into a single composite score per candidate.

    iter-v3/027 weights mirror iter-v3/026 (orthogonality-to-regime-momentum 0.20):
        - orthogonality_score_to_14_features (0.10): 1 - max_abs_ic_vs_14 / 0.50, clipped
        - orthogonality_score_to_regime_momentum (0.20): 1 - max_abs_ic_vs_rm / 0.50, clipped
        - rankic_score (0.30): max_abs_rankic / 0.10, clipped
        - stability_score (0.20): coverage * (1.0 if all_adf_pass else 0.5)
        - interpretability_score (0.10): hard-coded prior
        - implementation_cost_score (0.10): hard-coded prior (1 - cost)
    """
    if not rows_for_candidate:
        return {"candidate": "<unknown>", "composite_score": 0.0, "passes_brief_gate": False}
    candidate = rows_for_candidate[0]["candidate"]

    max_ic_vs_14 = max(r["max_abs_ic_vs_14_features"] for r in rows_for_candidate)
    max_ic_vs_rm = max(
        (r["max_abs_ic_vs_regime_momentum"] or 0.0) for r in rows_for_candidate
    )
    max_rankic = max((r["max_abs_rankic"] or 0.0) for r in rows_for_candidate)
    min_coverage = min(r["coverage_pct"] for r in rows_for_candidate)
    all_adf_pass = all(r["adf_passes"] for r in rows_for_candidate)

    orthogonality_score_14 = max(0.0, min(1.0, 1.0 - (max_ic_vs_14 / IC_THRESHOLD_BRIEF)))
    orthogonality_score_rm = max(0.0, min(1.0, 1.0 - (max_ic_vs_rm / IC_THRESHOLD_BRIEF)))
    rankic_score = max(0.0, min(1.0, max_rankic / 0.10))
    stability_score = (min_coverage / 100.0) * (1.0 if all_adf_pass else 0.5)

    interpretability_priors = {
        "cross_asset_divergence_norm": 0.7,
        "ret_kurt_to_skew_ratio": 0.4,
        "fracdiff_d05_close": 0.7,
        "hurst_drift_50_200": 0.8,
    }
    impl_cost_priors = {
        "cross_asset_divergence_norm": 0.2,  # 3 existing primitives
        "ret_kurt_to_skew_ratio": 0.1,  # 2 existing primitives
        "fracdiff_d05_close": 0.4,  # FFD weights + convolution overhead
        "hurst_drift_50_200": 0.5,  # may need hurst_50 primitive added
    }
    interp = interpretability_priors.get(candidate, 0.5)
    impl = impl_cost_priors.get(candidate, 0.5)

    composite = (
        0.10 * orthogonality_score_14
        + 0.20 * orthogonality_score_rm
        + 0.30 * rankic_score
        + 0.20 * stability_score
        + 0.10 * interp
        + 0.10 * (1.0 - impl)
    )

    return {
        "candidate": candidate,
        "max_abs_ic_vs_14_features": round(max_ic_vs_14, 6),
        "max_abs_ic_vs_regime_momentum": round(max_ic_vs_rm, 6),
        "max_abs_rankic_across_horizons_and_symbols": round(max_rankic, 6),
        "min_coverage_pct": round(min_coverage, 4),
        "all_adf_pass": all_adf_pass,
        "orthogonality_score_to_14": round(orthogonality_score_14, 4),
        "orthogonality_score_to_regime_momentum": round(orthogonality_score_rm, 4),
        "rankic_score": round(rankic_score, 4),
        "stability_score": round(stability_score, 4),
        "interpretability_prior": interp,
        "implementation_cost_prior": impl,
        "composite_score": round(composite, 4),
        "passes_brief_gate": (
            (max_rankic >= RANKIC_MIN) and all_adf_pass and (min_coverage >= COVERAGE_FLOOR_PCT)
        ),  # IC gate INFORMATIONAL ONLY per Category-2 carve-out
    }


# ----------- Main -----------


def main() -> int:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    print(
        f"[iter-v3/027] third_engineered_eda — IS window {IS_START_TS} → {OOS_CUTOFF_DATE}"
    )
    print(f"  V3_SYMBOLS = {V3_SYMBOLS}")
    print(
        f"  ALONE on iter-v3/025 14-feature stack (regime_momentum_signed_5d KEPT; "
        f"vol_adj_autocorr DROPPED — iter-v3/026 stacking falsified)"
    )
    print(f"  Evaluating 4 candidates for THIRD engineered feature (replacement, NOT stacked)")
    print(
        f"  IC carve-out applies (Category 2 axis) — feature-importance rank gates the model"
    )
    print(
        f"  Pre-commit per Critic FINAL Rec of iter-v3/026: cross_asset_divergence_norm"
    )

    distribution_rows: list[dict] = []
    correlation_rows: list[dict] = []
    rankic_rows: list[dict] = []
    adf_rows: list[dict] = []
    composite_rows: list[dict] = []
    candidate_to_rows: dict[str, list[dict]] = {}

    for symbol in V3_SYMBOLS:
        print(f"\n[ENV] {symbol}")
        klines = load_klines(symbol)
        features = load_features(symbol)
        candidates: dict[str, pd.Series] = {
            "cross_asset_divergence_norm": candidate_1_cross_asset_divergence_norm(
                klines, features
            ),
            "ret_kurt_to_skew_ratio": candidate_2_ret_kurt_to_skew_ratio(klines, features),
            "fracdiff_d05_close": candidate_3_fracdiff_d05_close(klines, features),
            "hurst_drift_50_200": candidate_4_hurst_drift_50_200(klines, features),
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
                    "max_abs_ic_vs_14_features": row["max_abs_ic_vs_14_features"],
                    "max_abs_ic_feature": row["max_abs_ic_feature"],
                    "max_abs_ic_vs_regime_momentum": row["max_abs_ic_vs_regime_momentum"],
                    "n_ic_features_compared": row["n_ic_features_compared"],
                    "ic_passes_brief_target_lt_0p50_INFORMATIONAL": row[
                        "ic_passes_brief_target_lt_0p50_INFORMATIONAL"
                    ],
                    "ic_passes_hard_gate_lt_0p70_INFORMATIONAL": row[
                        "ic_passes_hard_gate_lt_0p70_INFORMATIONAL"
                    ],
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
                f"  {name:30s} max|IC|_14={row['max_abs_ic_vs_14_features']:.4f}, "
                f"max|IC|_rm={row['max_abs_ic_vs_regime_momentum']}, "
                f"max|rankIC|={row['max_abs_rankic']}, "
                f"ADF p={row['adf_pvalue']}, "
                f"cov={row['coverage_pct']:.1f}%"
            )

    for name, rows in candidate_to_rows.items():
        composite_rows.append(composite_score(rows))

    composite_rows.sort(key=lambda r: r["composite_score"], reverse=True)

    pd.DataFrame(distribution_rows).to_csv(
        ANALYSIS_DIR / "third_engineered_eda_distribution.csv", index=False
    )
    pd.DataFrame(correlation_rows).to_csv(
        ANALYSIS_DIR / "third_engineered_eda_correlation.csv", index=False
    )
    pd.DataFrame(rankic_rows).to_csv(
        ANALYSIS_DIR / "third_engineered_eda_rankic.csv", index=False
    )
    pd.DataFrame(adf_rows).to_csv(ANALYSIS_DIR / "third_engineered_eda_adf.csv", index=False)
    pd.DataFrame(composite_rows).to_csv(
        ANALYSIS_DIR / "third_engineered_eda_composite.csv", index=False
    )

    top = composite_rows[0]
    candidates_passing_brief_gate = [r for r in composite_rows if r.get("passes_brief_gate")]
    n_pass = len(candidates_passing_brief_gate)

    leaderboard_lines = []
    for i, r in enumerate(composite_rows, 1):
        leaderboard_lines.append(
            f"{i}. {r['candidate']:30s}  composite={r['composite_score']:.4f}  "
            f"max|IC|_14={r['max_abs_ic_vs_14_features']:.4f}  "
            f"max|IC|_rm={r['max_abs_ic_vs_regime_momentum']:.4f}  "
            f"max|rankIC|={r['max_abs_rankic_across_horizons_and_symbols']:.4f}  "
            f"ADF={'PASS' if r['all_adf_pass'] else 'FAIL'}  "
            f"brief_gate={'PASS' if r.get('passes_brief_gate') else 'fail'}"
        )

    synthesis = f"""# iter-v3/027 — Third Engineered Feature EDA Synthesis

## Mission

Per Critic FINAL Recommendation of iter-v3/026 (review SHA `8839bbb`) + user directive
2026-05-08 + diary lessons (a)-(g) of iter-v3/026: **iter-v3/027 axis = DIFFERENT engineered
feature ALONE on top of regime_momentum**.

iter-v3/025 PROMISING-clean (regime_momentum_signed_5d alone): IS +0.88 / OOS +1.22.

iter-v3/026 NEGATIVE-SUSPICIOUS-OOS (regime_momentum + vol_adj_autocorr stacked): IS Sharpe
collapse to +0.05 (PATH C fires) + OOS spike to +1.45 (single-seed-suspect; 27× IS/OOS daily
Sharpe ratio is structurally absurd; iter-v3/013 lottery precedent + worst IS MaxDD in v3
history at 51.37% + BCH 78% concentration regression).

NEW memory rule `feedback_v3_engineered_features_dont_stack.md`: test ONE engineered feature
alone at single-seed; defer stacking to multi-seed CONFIRMATION.

iter-v3/027 axis isolates the question: **was iter-v3/026's destabilization vol_adj_autocorr-
specific, OR a structural property of stacking 2 engineered features at single-seed
n_trials=35?** Testing a DIFFERENT engineered feature ALONE on top of regime_momentum (the
proven iter-v3/025 setup with vol_adj_autocorr DROPPED) disambiguates this:
- PATH A (PROMISING) → iter-v3/026 destabilization was vol_adj_autocorr-specific OR a stacking
  artifact; engineered features can be stacked SEQUENTIALLY at single-seed (one alone at a
  time) but not simultaneously
- PATH C (NEGATIVE) → destabilization is NOT vol_adj_autocorr-specific; engineered stacking
  is structurally fragile at single-seed even with 1 new feature; pivot remains single-feature
  (only regime_momentum_signed_5d) at this architecture

## Candidates Evaluated (4 of 4)

Per Critic FINAL Recommendation of iter-v3/026 + EDA leaderboard from iter-v3/025/026:

1. **cross_asset_divergence_norm** = (sym_ret_7d − btc_ret_14d) / (|vwap_dev_20| + EPS)
   — relative-strength normalized; **Critic-named pre-commit recommendation**
2. ret_kurt_to_skew_ratio = ret_kurt_50 / (|ret_skew_50| + EPS)
   — fat-tail to asymmetry ratio; iter-v3/028 fallback if iter-v3/027 PATH B/C
3. fracdiff_d05_close = fracdiff(log(close), d=0.5) [López de Prado AFML Ch. 5]
4. hurst_drift_50_200 = hurst_50 − hurst_200 (multi-timeframe regime drift)

## IC Carve-Out (Category 2 axes) — REMINDER

Per `feedback_v3_engineered_feature_pivot.md`, IC orthogonality gate is INFORMATIONAL ONLY
for engineered (composed) features. The binding gate is the LightGBM model output:
**feature importance rank ≤10 AND absolute importance ≥30** for at least 1 symbol.

The composite score (mirroring iter-v3/026 weights) includes
**orthogonality-to-regime_momentum_signed_5d** (weight 0.20). Lower IC vs the iter-v3/025
PROMISING engineered feature = more orthogonal mechanism = better candidate.

## Composite Scoring (iter-v3/027 weights, mirror iter-v3/026)

Score = 0.10 × orthogonality_to_14_features (informational)
        + 0.20 × orthogonality_to_regime_momentum
        + 0.30 × rankIC magnitude
        + 0.20 × stability (coverage × ADF)
        + 0.10 × interpretability_prior
        + 0.10 × (1 − implementation_cost_prior)

## Leaderboard (sorted by composite score, highest first)

```
{chr(10).join(leaderboard_lines)}
```

## Brief gates (per candidate)

- Coverage IS window per symbol: ≥ {COVERAGE_FLOOR_PCT}%
- ADF p-value: < {ADF_PVALUE_THRESHOLD} per symbol
- Max |rank-IC| vs forward returns: ≥ {RANKIC_MIN} on at least 1 horizon
- Max |IC| vs 14 features: INFORMATIONAL (Category 2 IC carve-out)

Candidates passing ALL 3 binding brief gates: {n_pass} of 4

## RECOMMENDATION

Pre-commit per iter-v3/026 Critic FINAL Recommendation (review SHA `8839bbb`)
+ user directive 2026-05-08:

**iter-v3/027 axis = `cross_asset_divergence_norm`** = (sym_ret_7d − btc_ret_14d) / (|vwap_dev_20| + EPS)

Rationale (independent of leaderboard rank — single-axis discipline):
- Tests the disambiguation hypothesis directly: if a DIFFERENT engineered feature ALONE on
  top of regime_momentum produces clean co-directional IS+OOS lift (PATH A), then iter-v3/026's
  destabilization was vol_adj_autocorr-specific OR a stacking artifact.
- Different mechanism from regime_momentum AND from vol_adj_autocorr:
  - regime_momentum: directional 5-day return × Hurst regime classifier
  - vol_adj_autocorr (DROPPED): lag-1 autocorrelation / range-realized vol
  - cross_asset_divergence_norm: alt-vs-BTC return divergence / vwap-deviation
- Source primitives non-overlapping with regime_momentum (sym_ret_7d/btc_ret_14d/vwap_dev_20
  vs close-derived ret_5d/hurst_100). Genuinely new interaction signal.
- Implementation cost LOW: composes 3 existing primitives, all already in features parquet.
  ~10 lines of code added to engineered_v3.py.
- Critic FINAL of iter-v3/026 explicitly named this as recommended candidate with rationale
  "Different mechanism (relative-strength); uses existing primitives (sym_ret_7d, btc_ret_14d,
  vwap_dev_20); lowest implementation cost".
- Composite leaderboard ranking is INFORMATIONAL; single-axis discipline binds independent
  of rank.

## Files

- analysis/iteration_v3-027/third_engineered_eda_distribution.csv
- analysis/iteration_v3-027/third_engineered_eda_correlation.csv
- analysis/iteration_v3-027/third_engineered_eda_rankic.csv
- analysis/iteration_v3-027/third_engineered_eda_adf.csv
- analysis/iteration_v3-027/third_engineered_eda_composite.csv
"""
    (ANALYSIS_DIR / "synthesis.md").write_text(synthesis)
    print("\n" + synthesis)

    print(
        f"\n[OK] EDA complete. Top candidate by composite: {top['candidate']} "
        f"(composite score {top['composite_score']:.4f}). "
        f"Brief gates pass: {n_pass} / 4 candidates."
    )
    print(
        "Note: iter-v3/027 axis pre-committed per iter-v3/026 Critic FINAL Rec + user "
        "directive 2026-05-08 = cross_asset_divergence_norm (independent of composite ranking)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
