"""iter-v1/005 EXPLORATION — orthogonal NON-OHLCV feature audit (BTCUSDT, IS-only).

Diagnosis from iter-001..004: pruning OHLCV redundancy is NOT enough. The 41-col
prune base (V1_BTC_PRUNED_ITER002) confirmed IS -0.17 / OOS +0.48 at robust K=20 —
still an inversion. Every kept feature is OHLCV-derived (one shared price factor).
The diagnosed lever (iter-002 §4 own recommendation): add ORTHOGONAL, NON-OHLCV
feature families (funding, OI, long/short, basis) that carry information independent
of price.

This script (IS-ONLY, close_time < OOS_CUTOFF_MS = 2025-03-24) does THREE things:

  1. Parquet-availability inventory of every candidate orthogonal feature.
  2. IS IC (Spearman) of each candidate vs the forward label, at BOTH the 1-bar
     convention (mirrors runner _compute_forward_returns) AND the 21-bar convention
     (mirrors the MODEL's actual label horizon: timeout_minutes=10080 / 480 = 21).
     21-bar is PRIMARY (more decision-relevant); 1-bar reported for continuity.
  3. ORTHOGONALITY: max |Spearman| of each candidate vs the 41-col OHLCV base
     (we want genuinely orthogonal high-|IC| additions, not algebraic siblings of
     a base column). Also mean |rho| vs base, and ADF stationarity (informational).

It ranks the candidates by a screen score = |IC_21bar| * (1 - max_base_corr),
penalising redundancy with the OHLCV base, and emits the iter-005 best pick plus
the iter-006/007/008 sequence.

NO OOS DATA IS READ. NO BACKTEST IS RUN.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from statsmodels.tsa.stattools import adfuller

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC
PARQUET = Path("data/features/BTCUSDT_8h_features.parquet")
LABEL_HORIZON_BARS = 21  # timeout_minutes=10080 / (8h=480min) = 21 candles
OUT_DIR = Path("analysis/BTCUSDT/iteration_v1-005")

# The 41-col OHLCV prune base (V1_BTC_PRUNED_ITER002) — exact copy from the
# iter-002 feature_report.md proposed list. Every candidate's orthogonality is
# measured against THIS set.
BASE_41 = [
    "cal_dow_norm",
    "mom_macd_hist_12_26_9",
    "mom_macd_hist_5_13_3",
    "mr_bb_pctb_10",
    "mr_pct_from_high_10",
    "mr_pct_from_high_100",
    "mr_pct_from_low_100",
    "mr_pct_from_low_20",
    "mr_rsi_extreme_14",
    "stat_autocorr_lag1",
    "stat_autocorr_lag10",
    "stat_autocorr_lag5",
    "stat_kurtosis_10",
    "stat_kurtosis_30",
    "stat_kurtosis_50",
    "stat_skew_10",
    "stat_skew_20",
    "stat_skew_50",
    "trend_adx_14",
    "trend_adx_7",
    "trend_aroon_down_25",
    "trend_aroon_down_50",
    "trend_aroon_osc_14",
    "trend_aroon_osc_25",
    "trend_aroon_osc_50",
    "trend_plus_di_21",
    "trend_psar_af",
    "trend_sma_50",
    "trend_supertrend_10_2",
    "trend_supertrend_7_3",
    "vol_ad",
    "vol_cmf_20",
    "vol_garman_klass_50",
    "vol_hist_10",
    "vol_hist_5",
    "vol_obv",
    "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_10",
    "vol_taker_buy_ratio_sma_50",
    "vol_volume_pctchg_15",
    "vol_volume_pctchg_20",
]

# Candidate ORTHOGONAL non-OHLCV features. `family` groups them so the BATCH
# adds ONE family per screen (clean attribution). `available` is filled at
# runtime from the parquet. `lineage` records prior-iteration provenance.
CANDIDATES = {
    # ---- FUNDING family (perp-spot funding rate; positioning/carry signal) ----
    "funding_rate_zscore_30": ("funding", "iter-023 pooled-track: funding z-score 30-bar (10d)"),
    "funding_rate_zscore_90": ("funding", "iter-023 pooled-track: funding z-score 90-bar (30d)"),
    "btc_funding_spread_30_90": (
        "funding",
        "iter-052: funding term-structure slope (z30 - z90); STRONGLY LEARNED at /053 rank 4-10/48",
    ),
    "btc_funding_rate_8h_impulse": (
        "funding",
        "iter-052: funding shock detector (normalized 1st-diff); INERT at /053 rank>30/48 — DROPPED at /054",
    ),
    # ---- OPEN INTEREST family (leverage build/flush; flow independent of price) ----
    "oi_delta_30_z90": ("open_interest", "iter-025 pooled-track: OI delta z-score 90-bar"),
    "btc_oi_delta_5_z30": (
        "open_interest",
        "iter-058: OI 5-bar delta z-scored 30-bar; BASIN-LOTTERY at /058 multi-seed (spread 0.90)",
    ),
    "oi_price_divergence_30": (
        "open_interest",
        "iter-084: OI-price direction divergence z-score (CRV specialist; LOCAL-only there)",
    ),
    # ---- LONG/SHORT family (top-trader account ratio; positioning crowding) ----
    "long_short_zscore_30": (
        "long_short",
        "iter-049 pooled-track: top-trader long/short account ratio z-score 30-bar",
    ),
    # ---- BASIS family (perp-spot basis; carry/funding-arb structural signal) ----
    "basis_zscore_30": (
        "basis",
        "iter-034 pooled-track: perp-spot basis z-score; RETIRED at /040 (3-consec INERT pooled)",
    ),
}


def _spearman_ic(feat: np.ndarray, fwd: np.ndarray) -> float:
    """Spearman IC with pairwise-complete NaN handling."""
    mask = np.isfinite(feat) & np.isfinite(fwd)
    if mask.sum() < 100:
        return np.nan
    rho, _ = spearmanr(feat[mask], fwd[mask])
    return float(rho)


def _adf_pass(x: np.ndarray, alpha: float = 0.05) -> tuple[bool, float]:
    x = x[np.isfinite(x)]
    if len(x) < 50 or np.std(x) == 0:
        return False, np.nan
    try:
        stat, pval = adfuller(x, autolag="AIC")[:2]
    except Exception:
        return False, np.nan
    return bool(pval < alpha), float(pval)


def main() -> None:
    df = pd.read_parquet(PARQUET)
    # IS-only — mirror runner: open_time < OOS_CUTOFF_MS. Sort by time for forward-shift.
    is_df = df[df["open_time"] < OOS_CUTOFF_MS].sort_values("open_time").reset_index(drop=True)
    n_is = len(is_df)
    print(f"IS rows: {n_is}  ({pd.to_datetime(is_df['close_time'].min(), unit='ms')} -> "
          f"{pd.to_datetime(is_df['close_time'].max(), unit='ms')})")

    # Forward labels (PAST-ONLY shift; NO look-ahead — shift(-N) is future return AT
    # row t computed from prices we only KNOW at t+N, but it is the LABEL, not a
    # feature; the trailing N rows get NaN and are dropped pairwise). This mirrors
    # the runner's _compute_forward_returns (1-bar) and the model's 21-bar horizon.
    close = is_df["close"].astype(float)
    fwd_1 = np.log(close.shift(-1) / close).values
    fwd_21 = np.log(close.shift(-LABEL_HORIZON_BARS) / close).values

    # --- 1. Parquet availability inventory ---
    rows = []
    for feat, (family, lineage) in CANDIDATES.items():
        available = feat in df.columns
        rows.append({"feature": feat, "family": family, "available": available,
                     "lineage": lineage})
    inv = pd.DataFrame(rows)
    print("\n=== PARQUET AVAILABILITY ===")
    print(inv[["feature", "family", "available"]].to_string(index=False))

    # --- 2 & 3. IC + orthogonality vs the 41-col base + ADF ---
    base_present = [c for c in BASE_41 if c in is_df.columns]
    missing_base = [c for c in BASE_41 if c not in is_df.columns]
    if missing_base:
        print(f"\nWARNING: {len(missing_base)} base cols missing from parquet: {missing_base}")
    base_mat = is_df[base_present]

    results = []
    for feat, (family, lineage) in CANDIDATES.items():
        if feat not in is_df.columns:
            continue
        x = is_df[feat].astype(float).values
        nn = np.isfinite(x).sum()
        ic1 = _spearman_ic(x, fwd_1)
        ic21 = _spearman_ic(x, fwd_21)
        adf_ok, adf_p = _adf_pass(x)

        # Orthogonality: max & mean |Spearman| vs each base col (pairwise-complete)
        corrs = {}
        for bcol in base_present:
            b = base_mat[bcol].astype(float).values
            mask = np.isfinite(x) & np.isfinite(b)
            if mask.sum() < 100 or np.std(b[mask]) == 0:
                continue
            rho, _ = spearmanr(x[mask], b[mask])
            corrs[bcol] = abs(float(rho))
        if corrs:
            max_base = max(corrs.values())
            max_base_col = max(corrs, key=corrs.get)
            mean_base = float(np.mean(list(corrs.values())))
        else:
            max_base, max_base_col, mean_base = np.nan, "", np.nan

        # Screen score: signal density penalised by redundancy with base.
        score = abs(ic21) * (1.0 - max_base) if np.isfinite(max_base) else abs(ic21)

        results.append({
            "feature": feat, "family": family,
            "is_nonnan": nn, "is_cover_pct": round(100 * nn / n_is, 1),
            "ic_1bar": round(ic1, 4), "ic_21bar": round(ic21, 4),
            "abs_ic_21bar": round(abs(ic21), 4),
            "max_base_corr": round(max_base, 4), "max_base_col": max_base_col,
            "mean_base_corr": round(mean_base, 4),
            "orthogonality": round(1 - max_base, 4) if np.isfinite(max_base) else np.nan,
            "screen_score": round(score, 5),
            "adf_pass": adf_ok, "adf_p": round(adf_p, 4) if np.isfinite(adf_p) else np.nan,
            "lineage": lineage,
        })

    res = pd.DataFrame(results).sort_values("screen_score", ascending=False).reset_index(drop=True)
    print("\n=== IS IC + ORTHOGONALITY (sorted by screen_score = |IC_21bar| * orthogonality) ===")
    show = ["feature", "family", "is_cover_pct", "ic_1bar", "ic_21bar", "abs_ic_21bar",
            "max_base_corr", "max_base_col", "orthogonality", "screen_score", "adf_pass"]
    print(res[show].to_string(index=False))

    # --- Family-level best (one per family for the BATCH sequence) ---
    print("\n=== BEST CANDIDATE PER FAMILY (BATCH building block) ===")
    fam_best = res.sort_values("screen_score", ascending=False).groupby("family").head(1)
    fam_best = fam_best.sort_values("screen_score", ascending=False)
    print(fam_best[["family", "feature", "abs_ic_21bar", "orthogonality",
                    "screen_score", "is_cover_pct"]].to_string(index=False))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    inv.to_csv(OUT_DIR / "parquet_availability.csv", index=False)
    res.to_csv(OUT_DIR / "orthogonal_ic_table.csv", index=False)
    fam_best.to_csv(OUT_DIR / "family_best.csv", index=False)
    print(f"\nWrote: {OUT_DIR}/parquet_availability.csv, orthogonal_ic_table.csv, family_best.csv")

    # --- Sanity context: max |IC_21bar| of the 41-col OHLCV BASE itself ---
    base_ics = []
    for bcol in base_present:
        b = is_df[bcol].astype(float).values
        base_ics.append((bcol, abs(_spearman_ic(b, fwd_21))))
    base_ic_df = pd.DataFrame(base_ics, columns=["feature", "abs_ic_21bar"]).sort_values(
        "abs_ic_21bar", ascending=False)
    print("\n=== TOP-5 |IC_21bar| in the 41-col OHLCV base (context for candidate strength) ===")
    print(base_ic_df.head(5).to_string(index=False))
    print(f"base median |IC_21bar| = {base_ic_df['abs_ic_21bar'].median():.4f}")


if __name__ == "__main__":
    main()
