"""QR Phase 1 — proper feature-level EDA on IS data only.

Four deliverables:
1. Feature correlation matrix — identify redundant / collinear features
2. Feature stationarity (ADF test) — identify non-stationary features
3. Feature value distribution — identify dead/constant features
4. Feature → forward-return crude correlation — predictive power ranking

STRICTLY IS-only. No OOS peeking.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.stats import spearmanr

from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v2 import V2_FEATURE_COLUMNS

SYMBOLS = ["DOGEUSDT", "SOLUSDT", "XRPUSDT", "NEARUSDT"]


def _load_is(sym: str) -> pd.DataFrame:
    df = pq.read_table(f"data/features_v2/{sym}_8h_features.parquet").to_pandas()
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
    return df


def _pool_is() -> pd.DataFrame:
    """Pool IS data across 4 symbols for a single 'portfolio IS' view."""
    frames = []
    for sym in SYMBOLS:
        df = _load_is(sym)
        df["symbol"] = sym
        frames.append(df[list(V2_FEATURE_COLUMNS) + ["symbol", "open_time", "close"]].copy())
    return pd.concat(frames, ignore_index=True)


def deliverable_1_correlation(df: pd.DataFrame) -> None:
    """Feature-feature correlation matrix. Flag |rho|>0.85 pairs."""
    feat_df = df[list(V2_FEATURE_COLUMNS)].dropna()
    print(f"\n=== 1. Feature Correlation Matrix ===")
    print(f"Rows used: {len(feat_df)}")
    corr = feat_df.corr(method="pearson").abs().values.copy()
    np.fill_diagonal(corr, 0)
    corr = pd.DataFrame(corr, index=V2_FEATURE_COLUMNS, columns=V2_FEATURE_COLUMNS)
    pairs = []
    for i, f_i in enumerate(V2_FEATURE_COLUMNS):
        for f_j in V2_FEATURE_COLUMNS[i + 1:]:
            if corr.loc[f_i, f_j] > 0.85:
                pairs.append((f_i, f_j, corr.loc[f_i, f_j]))
    pairs.sort(key=lambda x: -x[2])
    print(f"  Highly correlated pairs (|rho|>0.85): {len(pairs)}")
    for f_i, f_j, r in pairs[:30]:
        print(f"    {f_i:<30} <-> {f_j:<30}  rho={r:.3f}")
    if len(pairs) > 30:
        print(f"    (and {len(pairs) - 30} more)")


def deliverable_2_stationarity(df: pd.DataFrame) -> None:
    """Proxy for non-stationarity: rolling mean drift vs absolute level.

    True non-stationarity = level drifts over time. We measure:
    - Mean of first-half vs second-half of IS period.
    - Flag if |mean_h1 - mean_h2| / |std| > 0.3 (meaningful drift).
    """
    print(f"\n=== 2. Stationarity proxy (mean-drift test, IS data) ===")
    drift_scores = {}
    for sym in SYMBOLS:
        sym_df = df[df.symbol == sym].sort_values("open_time")
        mid = len(sym_df) // 2
        h1 = sym_df.iloc[:mid]
        h2 = sym_df.iloc[mid:]
        for f in V2_FEATURE_COLUMNS:
            s1, s2 = h1[f].dropna(), h2[f].dropna()
            if len(s1) < 50 or len(s2) < 50:
                continue
            std_full = sym_df[f].std()
            if std_full == 0 or np.isnan(std_full):
                continue
            drift = abs(s2.mean() - s1.mean()) / std_full
            drift_scores.setdefault(f, []).append(drift)
    per_feat = {f: np.mean(v) for f, v in drift_scores.items() if v}
    ranked = sorted(per_feat.items(), key=lambda x: -x[1])
    print(f"  High-drift features (mean drift >0.3 std across 4 symbols): "
          f"{sum(1 for _, d in per_feat.items() if d > 0.3)}")
    for f, d in ranked[:10]:
        print(f"    {f:<35}  drift_std={d:.3f}")


def deliverable_3_distribution(df: pd.DataFrame) -> None:
    """Feature distribution — flag near-constant or degenerate."""
    print(f"\n=== 3. Feature Distribution (dead feature check) ===")
    feat_df = df[list(V2_FEATURE_COLUMNS)].dropna()
    stats = pd.DataFrame({
        "std": feat_df.std(),
        "iqr": feat_df.quantile(0.75) - feat_df.quantile(0.25),
        "unique_count": feat_df.nunique(),
        "zero_frac": (feat_df == 0).sum() / len(feat_df),
    })
    # Flag degenerate
    dead = stats[(stats.iqr == 0) | (stats.unique_count < 10)]
    print(f"  Dead-ish features (IQR=0 or <10 unique values): {len(dead)}")
    print(dead.to_string() if len(dead) else "  (none — all features have reasonable variance)")
    # Ranking by std
    print("\n  Lowest-variance features (bottom 5):")
    print(stats.sort_values("std").head(5).to_string())


def deliverable_4_predictive(df: pd.DataFrame) -> None:
    """Feature → forward-return (24h = 3 bars) spearman correlation."""
    print(f"\n=== 4. Feature → 3-bar-Forward Return Correlation (crude) ===")
    print("  Per-symbol aggregated (mean Spearman rho across 4 symbols)")
    all_rhos = {f: [] for f in V2_FEATURE_COLUMNS}
    for sym in SYMBOLS:
        sym_df = df[df.symbol == sym].sort_values("open_time").reset_index(drop=True)
        sym_df["fwd_ret"] = sym_df["close"].shift(-3) / sym_df["close"] - 1
        sym_df = sym_df.dropna(subset=["fwd_ret"] + list(V2_FEATURE_COLUMNS))
        if len(sym_df) < 100:
            continue
        for f in V2_FEATURE_COLUMNS:
            rho, _ = spearmanr(sym_df[f], sym_df["fwd_ret"])
            if not np.isnan(rho):
                all_rhos[f].append(rho)
    agg = {f: (np.mean(rs), np.std(rs)) for f, rs in all_rhos.items() if rs}
    ranked = sorted(agg.items(), key=lambda x: -abs(x[1][0]))
    print("  Top 15 by |mean Spearman|:")
    for f, (m, s) in ranked[:15]:
        print(f"    {f:<35}  mean_rho={m:+.4f}  std_rho={s:.4f}")
    print("  Bottom 10 (weakest predictors):")
    for f, (m, s) in ranked[-10:]:
        print(f"    {f:<35}  mean_rho={m:+.4f}  std_rho={s:.4f}")


def main() -> None:
    print(f"QR Phase 1 EDA — v2 baseline iter-v2/059-clean")
    print(f"IS cutoff: 2025-03-24 (no OOS data used)")
    print(f"Symbols: {SYMBOLS}")
    print(f"Features: {len(V2_FEATURE_COLUMNS)}")

    df = _pool_is()
    print(f"Pooled IS rows: {len(df)}")

    deliverable_1_correlation(df)
    deliverable_2_stationarity(df)
    deliverable_3_distribution(df)
    deliverable_4_predictive(df)


if __name__ == "__main__":
    main()
