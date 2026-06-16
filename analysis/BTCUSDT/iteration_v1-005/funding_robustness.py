"""iter-v1/005 — robustness checks for the iter-005 pick (btc_funding_spread_30_90).

IS-ONLY. Three checks:
  (A) IS sub-period stability of |IC_21bar| (is the signal one-regime, or persistent?).
  (B) Funding-family internal |Spearman| (are the 4 funding cols redundant — should we
      add only the spread, not all four?).
  (C) Directional sign sanity: a negative IC means HIGH funding spread (relative funding
      heat) precedes LOWER forward return — the textbook over-leveraged-long mean-revert
      signal. We confirm the sign is economically coherent, not a fluke.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OOS_CUTOFF_MS = 1742774400000
PARQUET = Path("data/features/BTCUSDT_8h_features.parquet")
HORIZON = 21
OUT = Path("analysis/BTCUSDT/iteration_v1-005")

FUNDING = [
    "funding_rate_zscore_30", "funding_rate_zscore_90",
    "btc_funding_spread_30_90", "btc_funding_rate_8h_impulse",
]


def ic(feat, fwd):
    m = np.isfinite(feat) & np.isfinite(fwd)
    if m.sum() < 100:
        return np.nan, 0
    rho, _ = spearmanr(feat[m], fwd[m])
    return float(rho), int(m.sum())


def main():
    df = pd.read_parquet(PARQUET)
    is_df = df[df["open_time"] < OOS_CUTOFF_MS].sort_values("open_time").reset_index(drop=True)
    close = is_df["close"].astype(float)
    fwd = np.log(close.shift(-HORIZON) / close).values

    # (A) sub-period stability — 3 contiguous IS thirds
    print("=== (A) IS sub-period |IC_21bar| of btc_funding_spread_30_90 ===")
    x = is_df["btc_funding_spread_30_90"].astype(float).values
    thirds = np.array_split(np.arange(len(is_df)), 3)
    for i, idx in enumerate(thirds):
        rho, n = ic(x[idx], fwd[idx])
        lo = pd.to_datetime(is_df["close_time"].iloc[idx[0]], unit="ms").date()
        hi = pd.to_datetime(is_df["close_time"].iloc[idx[-1]], unit="ms").date()
        print(f"  third {i+1} [{lo}..{hi}] n={n:5d}  IC_21bar={rho:+.4f}")
    rho_all, n_all = ic(x, fwd)
    print(f"  full IS         n={n_all:5d}  IC_21bar={rho_all:+.4f}")

    # (B) funding-family internal redundancy
    print("\n=== (B) funding-family internal |Spearman| matrix (IS) ===")
    sub = is_df[FUNDING].astype(float)
    corr = sub.corr(method="spearman").abs()
    print(corr.round(3).to_string())

    # (C) directional coherence — bucket forward return by spread sign/magnitude
    print("\n=== (C) forward 21-bar return by funding-spread bucket (IS) ===")
    s = pd.Series(x)
    q = pd.qcut(s, 5, labels=["Q1(low)", "Q2", "Q3", "Q4", "Q5(high)"], duplicates="drop")
    tmp = pd.DataFrame({"bucket": q, "fwd": fwd})
    g = tmp.dropna().groupby("bucket", observed=True)["fwd"].agg(["mean", "median", "count"])
    print((g * np.array([[1, 1, 1]])).assign(
        mean=lambda d: (d["mean"] * 100).round(3),
        median=lambda d: (d["median"] * 100).round(3)).to_string())
    print("  (mean/median in % forward 21-bar log-return)")

    OUT.mkdir(parents=True, exist_ok=True)
    corr.to_csv(OUT / "funding_family_corr.csv")
    print(f"\nWrote: {OUT}/funding_family_corr.csv")


if __name__ == "__main__":
    main()
