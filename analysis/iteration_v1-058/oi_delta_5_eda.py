"""EDA script — iter-v1/058: btc_oi_delta_5_z30 short-window OI delta feature.

IS-ONLY analysis (never touches OOS data).

Produces:
  - IS Pearson IC between btc_oi_delta_5_z30 and oi_delta_30_z90
  - Distribution statistics (mean, std, 1st/99th percentile) of btc_oi_delta_5_z30 on IS data
  - IC orthogonality check vs vol_volume_rel_20 (highest-risk cluster)
  - OI data availability coverage check

Run:
    cd /home/roberto/crypto-trade/.worktrees/quant-research
    uv run python analysis/iteration_v1-058/oi_delta_5_eda.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
IS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC (OOS start; IS ends here)
DATA_DIR = Path("data")
SYMBOL = "BTCUSDT"
INTERVAL = "8h"


def load_klines_is() -> pd.DataFrame:
    """Load BTC klines restricted to IS window."""
    klines_path = DATA_DIR / SYMBOL / f"{INTERVAL}.csv"
    df = pd.read_csv(klines_path)
    df.columns = [c.lower().strip() for c in df.columns]
    df["open_time"] = df["open_time"].astype("int64")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df[df["open_time"] < IS_CUTOFF_MS].copy()
    df = df.sort_values("open_time").reset_index(drop=True)
    df["symbol"] = SYMBOL
    return df


def load_oi_is() -> pd.DataFrame:
    """Load BTC OI data restricted to IS window."""
    oi_path = DATA_DIR / "open_interest" / SYMBOL / f"{INTERVAL}.csv"
    oi = pd.read_csv(oi_path)
    oi.columns = [c.lower().strip() for c in oi.columns]
    oi["open_time"] = oi["open_time"].astype("int64")
    oi = oi[oi["open_time"] < IS_CUTOFF_MS].copy()
    oi = oi.sort_values("open_time").reset_index(drop=True)
    return oi


def compute_oi_delta_zscore(
    oi_series: pd.Series,
    delta_window: int,
    zscore_window: int,
    delta_clip_low: float = -1.0,
    delta_clip_high: float = 5.0,
    zscore_clip: float = 10.0,
) -> pd.Series:
    """Compute past-only OI delta z-score (mirrors open_interest_v1.py logic)."""
    oi = oi_series.astype(float)
    denom = oi.shift(delta_window).replace(0, np.nan)
    oi_delta = ((oi - oi.shift(delta_window)) / denom).clip(delta_clip_low, delta_clip_high)
    s_shifted = oi_delta.shift(1)
    rmean = s_shifted.rolling(window=zscore_window, min_periods=zscore_window).mean()
    rstd = s_shifted.rolling(window=zscore_window, min_periods=zscore_window).std(ddof=1)
    zscore = (oi_delta - rmean) / rstd.replace(0, np.nan)
    return zscore.clip(-zscore_clip, zscore_clip)


def main() -> None:
    print("=" * 70)
    print("iter-v1/058 EDA — btc_oi_delta_5_z30 IS-only analysis")
    print("=" * 70)

    # --- Load data ---
    klines = load_klines_is()
    oi = load_oi_is()

    print(
        f"\n[Data] BTC IS klines: {len(klines)} rows ({klines['open_time'].iloc[0]} → {klines['open_time'].iloc[-1]})"
    )
    print(
        f"[Data] BTC IS OI rows: {len(oi)} rows ({oi['open_time'].iloc[0]} → {oi['open_time'].iloc[-1]})"
    )

    # --- OI coverage check ---
    klines_ms = set(klines["open_time"].values)
    oi_ms = set(oi["open_time"].values)
    coverage_pct = 100 * len(klines_ms & oi_ms) / len(klines_ms)
    missing = len(klines_ms - oi_ms)
    print(f"\n[OI coverage] {coverage_pct:.1f}% of IS kline bars have OI data")
    print(f"[OI coverage] Missing OI bars in IS: {missing}")

    # Merge OI onto klines
    oi_keyed = oi[["open_time", "sum_open_interest"]].rename(
        columns={"open_time": "_key", "sum_open_interest": "oi"}
    )
    klines["_key"] = klines["open_time"]
    merged = klines.merge(oi_keyed, on="_key", how="left").drop(columns=["_key"])
    oi_series = merged["oi"].astype(float)

    # --- Compute btc_oi_delta_5_z30 (NEW) ---
    btc_oi_delta_5_z30 = compute_oi_delta_zscore(oi_series, delta_window=5, zscore_window=30)
    print(f"\n[btc_oi_delta_5_z30] Burn-in: first {5 + 30} rows NaN")
    non_nan_count = btc_oi_delta_5_z30.notna().sum()
    nan_count = btc_oi_delta_5_z30.isna().sum()
    print(f"[btc_oi_delta_5_z30] Non-NaN rows: {non_nan_count} / {len(btc_oi_delta_5_z30)}")
    print(f"[btc_oi_delta_5_z30] NaN rows: {nan_count}")

    # Distribution stats
    valid = btc_oi_delta_5_z30.dropna()
    p1, p99 = np.percentile(valid, [1, 99])
    print(f"\n[btc_oi_delta_5_z30 distribution]")
    print(f"  mean = {valid.mean():.4f}")
    print(f"  std  = {valid.std():.4f}")
    print(f"  min  = {valid.min():.4f}")
    print(f"  p1   = {p1:.4f}")
    print(f"  p99  = {p99:.4f}")
    print(f"  max  = {valid.max():.4f}")
    if abs(p1) > 4 or abs(p99) > 4:
        print(
            "  WARNING: 99th percentile z-score exceeds ±4 — fat-tail flag (RF-1 from lgbm_advisor)"
        )
    else:
        print("  OK: 99th percentile within ±4 (no fat-tail concern)")

    # --- Compute oi_delta_30_z90 (existing) for IC comparison ---
    oi_delta_30_z90 = compute_oi_delta_zscore(oi_series, delta_window=30, zscore_window=90)

    # IC between the two OI features (align on non-NaN intersection)
    both_valid = btc_oi_delta_5_z30.notna() & oi_delta_30_z90.notna()
    ic_oi_sister = btc_oi_delta_5_z30[both_valid].corr(oi_delta_30_z90[both_valid])
    print(f"\n[IC with sister feature oi_delta_30_z90]")
    print(f"  Pearson IC = {ic_oi_sister:.4f}")
    if abs(ic_oi_sister) < 0.55:
        print("  PASS: within LM Master estimate range |IC| ≈ 0.30–0.55 (expected)")
    elif abs(ic_oi_sister) < 0.70:
        print("  NOTE: IC in [0.55, 0.70) — moderate overlap; informational")
    elif abs(ic_oi_sister) < 0.80:
        print("  WARNING: IC in [0.70, 0.80) — sister-correlation threshold approaching (Rec 1)")
    else:
        print(
            "  BLOCK: IC ≥ 0.80 — LightGBM split budget likely routes to established sister; abort"
        )

    # --- Load parquet features for IC orthogonality check ---
    parquet_path = DATA_DIR / "features_v1" / f"{SYMBOL}_8h.parquet"
    if parquet_path.exists():
        feats = pd.read_parquet(parquet_path)
        feats = (
            feats[feats.index < pd.Timestamp("2025-03-24", tz="UTC")]
            if feats.index.tzinfo
            else feats
        )

        # IC vs vol_volume_rel_20 (highest-risk cluster from /048)
        if "vol_volume_rel_20" in feats.columns:
            # Align by position (same IS window)
            n = min(len(feats), len(btc_oi_delta_5_z30))
            vol_series = feats["vol_volume_rel_20"].iloc[-n:].reset_index(drop=True)
            new_feat = btc_oi_delta_5_z30.iloc[-n:].reset_index(drop=True)
            both_ok = vol_series.notna() & new_feat.notna()
            ic_vol = new_feat[both_ok].corr(vol_series[both_ok])
            print(f"\n[IC orthogonality vs vol_volume_rel_20 (high-risk cluster)]")
            print(f"  Pearson IC = {ic_vol:.4f}")
            if abs(ic_vol) < 0.60:
                print("  PASS: orthogonality gate (|IC| < 0.60)")
            else:
                print("  BLOCK: |IC| ≥ 0.60 vs vol_volume_rel_20 — abort per /048 precedent")
        else:
            print(
                "\n[IC orthogonality] vol_volume_rel_20 not in parquet — skipping (parquet not regenerated yet)"
            )
    else:
        print(
            f"\n[IC orthogonality] Parquet not found at {parquet_path} — skipping (regen required first)"
        )

    print("\n" + "=" * 70)
    print("EDA complete. Summary:")
    print(f"  OI coverage: {coverage_pct:.1f}%")
    print(f"  btc_oi_delta_5_z30 non-NaN IS rows: {non_nan_count}")
    print(f"  IC with oi_delta_30_z90: {ic_oi_sister:.4f}")
    print(f"  p99 abs value: {max(abs(p1), abs(p99)):.2f} (threshold: 4.0)")
    print("=" * 70)


if __name__ == "__main__":
    main()
