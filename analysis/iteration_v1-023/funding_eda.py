"""iter-v1/023 EDA — Funding-rate feature family for v1 universe.

Anchor: BASELINE_V1.md (v0.v1-baseline-corrected; commit f8bc12c).

CRITICAL LOAD-BEARING PRIOR: the v3 funding axis is CLOSED at 4 EXPLORATION data
points (iter-v3/019/023/024/082), ALL INERT-by-importance. v3 catalog rule:
"funding-rate features at any window or transform CONSIDERED EXHAUSTED" against
the BCH/LDO/TRX universe. This EDA tests whether v1's structurally different
universe (BTC+ETH+LINK+LTC+DOT) — broader, more liquid, with established 5-symbol
joint loss surface — can break the v3 INERT pattern.

IS-ONLY DISCIPLINE (per `feedback_no_cheating.md`):
- All summary statistics computed on open_time < OOS_CUTOFF_DATE = 2025-03-24.
- Funding data goes back to 2019-09-10 for BTC/ETH — plenty of IS history.
- No OOS funding statistics computed — only summary distribution checks deferred
  to post-Phase 7 evaluation.

OUTPUTS:
- funding_availability.csv — per-symbol funding cache extent vs kline extent
- funding_distribution.csv — per-symbol IS-only mean/std/skew/kurt of raw rate
                             + count of |z| > 2 extreme funding events
- funding_zscore_ic.csv — IS-only IC vs V1_FEATURE_COLUMNS_PRUNED top features
                          (Spearman; Critic Check 4 requires < 0.7 for NEW family acceptance)
- funding_regime.csv — per-symbol IS-only quartile breakdown of z-score distribution
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add src to path so we can import features_v3 funding helpers (read-only use of math)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from crypto_trade.config import OOS_CUTOFF_DATE  # noqa: E402
from crypto_trade.features_v1 import V1_BASELINE_UNIVERSE, V1_FEATURE_COLUMNS_PRUNED  # noqa: E402

OOS_CUTOFF_MS = int(pd.Timestamp(OOS_CUTOFF_DATE).timestamp() * 1000)

DATA_DIR = ROOT / "data"
FUNDING_DIR = DATA_DIR / "funding_rates"
FEATURES_DIR = DATA_DIR / "features"
OUT_DIR = ROOT / "analysis" / "iteration_v1-023"

ZSCORE_WINDOW = 30  # 10 days at 8h cadence
ZSCORE_CLIP = 10.0


# ---------------------------------------------------------------------------
# Funding-rate z-score (mirrors features_v3.funding_v3.compute_funding_rate_zscore
# math but inline for EDA-only purposes; not importing v3 module per track-isolation
# discipline. The math is identical and trivial to reproduce.)
# ---------------------------------------------------------------------------


def compute_funding_zscore(
    kline_df: pd.DataFrame,
    funding_df: pd.DataFrame,
    window: int = ZSCORE_WINDOW,
    clip: float = ZSCORE_CLIP,
) -> pd.DataFrame:
    """Merge funding rates into kline frame and compute past-only rolling z-score."""
    funding = funding_df.copy()
    funding["open_time_aligned"] = (funding["funding_time"] // 60_000) * 60_000

    kline = kline_df.copy()
    kline["open_time_aligned"] = (kline["open_time"] // 60_000) * 60_000

    merged = kline.merge(
        funding[["open_time_aligned", "funding_rate"]],
        on="open_time_aligned",
        how="left",
    ).drop(columns=["open_time_aligned"])

    s = merged["funding_rate"].astype(float)
    s_shifted = s.shift(1)
    rmean = s_shifted.rolling(window=window, min_periods=window).mean()
    rstd = s_shifted.rolling(window=window, min_periods=window).std(ddof=1)
    z30 = (s - rmean) / rstd.replace(0, np.nan)
    z30 = z30.clip(lower=-clip, upper=clip)

    # 90-bar window (~30 days)
    s_shifted2 = s.shift(1)
    rmean2 = s_shifted2.rolling(window=90, min_periods=90).mean()
    rstd2 = s_shifted2.rolling(window=90, min_periods=90).std(ddof=1)
    z90 = (s - rmean2) / rstd2.replace(0, np.nan)
    z90 = z90.clip(lower=-clip, upper=clip)

    merged["funding_rate_zscore_30"] = z30.values
    merged["funding_rate_zscore_90"] = z90.values
    return merged


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    availability_rows: list[dict] = []
    distribution_rows: list[dict] = []
    regime_rows: list[dict] = []
    ic_rows: list[dict] = []

    # Top features by /021 PROMISING-METHODOLOGY feature-importance audit
    # (Spearman ρ=0.9448 across pool vs cohort isolation; top-5 features dominant).
    top_features = (
        "vol_atr_14",
        "trend_aroon_osc_50",
        "stat_autocorr_lag5",
        "stat_kurtosis_20",
        "mom_macd_line_12_26_9",
    )

    for symbol in V1_BASELINE_UNIVERSE:
        # Load kline
        kline_path = DATA_DIR / symbol / "8h.csv"
        kline = pd.read_csv(kline_path)

        # Load funding
        fund_path = FUNDING_DIR / f"{symbol}.csv"
        if not fund_path.exists():
            print(f"WARN: {symbol} funding cache missing → {fund_path}")
            continue
        funding = pd.read_csv(fund_path)

        # Availability comparison
        kline_min, kline_max = kline["open_time"].min(), kline["open_time"].max()
        fund_min, fund_max = funding["funding_time"].min(), funding["funding_time"].max()

        # Find first funding row at or after kline start
        first_match = funding["funding_time"][funding["funding_time"] >= kline_min].min()
        first_match_dt = pd.to_datetime(first_match, unit="ms") if pd.notna(first_match) else None

        availability_rows.append({
            "symbol": symbol,
            "kline_n": len(kline),
            "funding_n": len(funding),
            "kline_min_dt": pd.to_datetime(kline_min, unit="ms"),
            "kline_max_dt": pd.to_datetime(kline_max, unit="ms"),
            "funding_min_dt": pd.to_datetime(fund_min, unit="ms"),
            "funding_max_dt": pd.to_datetime(fund_max, unit="ms"),
            "first_funding_at_or_after_kline_start": first_match_dt,
            "funding_lag_days": (
                None
                if first_match is None or pd.isna(first_match)
                else (first_match - kline_min) / (1000 * 60 * 60 * 24)
            ),
        })

        # Compute z-score (past-only) merged into kline frame
        merged = compute_funding_zscore(kline, funding)

        # Filter to IS-ONLY for all distribution / IC checks
        is_mask = merged["open_time"] < OOS_CUTOFF_MS
        merged_is = merged[is_mask].copy()

        rate = merged_is["funding_rate"].dropna()
        z30 = merged_is["funding_rate_zscore_30"].dropna()
        z90 = merged_is["funding_rate_zscore_90"].dropna()

        distribution_rows.append({
            "symbol": symbol,
            "is_n_bars": len(merged_is),
            "raw_n_nonnull": len(rate),
            "raw_mean": rate.mean(),
            "raw_std": rate.std(),
            "raw_skew": rate.skew(),
            "raw_kurt": rate.kurt(),
            "raw_min": rate.min(),
            "raw_max": rate.max(),
            "raw_p01": rate.quantile(0.01),
            "raw_p99": rate.quantile(0.99),
            "raw_at_clamp_floor_pct": float(
                (np.isclose(rate, rate.quantile(0.001), atol=1e-7).sum()) / max(len(rate), 1) * 100
            ),
            "z30_n_nonnull": len(z30),
            "z30_extreme_2sigma_pct": float((z30.abs() > 2).sum() / max(len(z30), 1) * 100),
            "z30_extreme_3sigma_pct": float((z30.abs() > 3).sum() / max(len(z30), 1) * 100),
            "z30_at_clip_pct": float((z30.abs() >= ZSCORE_CLIP - 0.001).sum() / max(len(z30), 1) * 100),
            "z30_std": z30.std(),
            "z90_n_nonnull": len(z90),
            "z90_extreme_2sigma_pct": float((z90.abs() > 2).sum() / max(len(z90), 1) * 100),
            "z90_std": z90.std(),
        })

        # Per-symbol regime quartile breakdown of z30 (IS only)
        for q_lo, q_hi, label in [
            (-np.inf, -2.0, "extreme_negative_z<-2"),
            (-2.0, -1.0, "negative_-2_to_-1"),
            (-1.0, 1.0, "neutral_-1_to_1"),
            (1.0, 2.0, "positive_1_to_2"),
            (2.0, np.inf, "extreme_positive_z>2"),
        ]:
            in_bucket = (z30 > q_lo) & (z30 <= q_hi)
            count = int(in_bucket.sum())
            regime_rows.append({
                "symbol": symbol,
                "z30_band": label,
                "count": count,
                "share_pct": float(count / max(len(z30), 1) * 100),
            })

        # IC vs top V1 features (IS only)
        features_path = FEATURES_DIR / f"{symbol}_8h_features.parquet"
        if features_path.exists():
            feat_df = pd.read_parquet(features_path)
            # Merge with z-score by open_time
            merged_feat = merged_is.merge(
                feat_df[["open_time"] + [c for c in top_features if c in feat_df.columns]],
                on="open_time",
                how="inner",
            )
            for feat in top_features:
                if feat not in merged_feat.columns:
                    continue
                joint = merged_feat[["funding_rate_zscore_30", "funding_rate_zscore_90", feat]].dropna()
                if len(joint) < 100:
                    continue
                ic_z30 = joint["funding_rate_zscore_30"].corr(joint[feat], method="spearman")
                ic_z90 = joint["funding_rate_zscore_90"].corr(joint[feat], method="spearman")
                ic_rows.append({
                    "symbol": symbol,
                    "v1_feature": feat,
                    "n_obs": len(joint),
                    "ic_funding_z30_vs_feature": ic_z30,
                    "ic_funding_z90_vs_feature": ic_z90,
                    "passes_critic_check4_z30": abs(ic_z30) < 0.7,
                    "passes_critic_check4_z90": abs(ic_z90) < 0.7,
                })

    pd.DataFrame(availability_rows).to_csv(OUT_DIR / "funding_availability.csv", index=False)
    pd.DataFrame(distribution_rows).to_csv(OUT_DIR / "funding_distribution.csv", index=False)
    pd.DataFrame(regime_rows).to_csv(OUT_DIR / "funding_regime.csv", index=False)
    pd.DataFrame(ic_rows).to_csv(OUT_DIR / "funding_zscore_ic.csv", index=False)

    print(f"Outputs written under {OUT_DIR}/")
    print(f"  - funding_availability.csv ({len(availability_rows)} rows)")
    print(f"  - funding_distribution.csv ({len(distribution_rows)} rows)")
    print(f"  - funding_regime.csv ({len(regime_rows)} rows)")
    print(f"  - funding_zscore_ic.csv ({len(ic_rows)} rows)")
    print(f"\nOOS_CUTOFF_DATE: {OOS_CUTOFF_DATE} (ms = {OOS_CUTOFF_MS})")
    print(f"Tested universe: {V1_BASELINE_UNIVERSE}")
    print(f"V1_FEATURE_COLUMNS_PRUNED length: {len(V1_FEATURE_COLUMNS_PRUNED)}")


if __name__ == "__main__":
    main()
