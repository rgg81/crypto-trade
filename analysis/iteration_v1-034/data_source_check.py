"""iter-v1/034 Phase 1 — data source viability check.

Decision logged here:
  Liquidation feed: NOT VIABLE
    - data.binance.vision liquidationSnapshot retired (404 across all paths)
    - /fapi/v1/forceOrders is account-private or ~7-day public window
    - 3rd-party (Amberdata, Tardis.dev) not available in worktree

  Basis (perp - spot) z-score: VIABLE — both feeds already on disk
    - data/<SYM>/8h.csv (perp): 2020-01 onwards, all 5 v1 syms
    - data/spot/<SYM>/8h.csv (spot): 2018-01 onwards, all 5 v1 syms

  -> PIVOT to BASIS axis per cycle-5 menu fallback line 53-54.

This script:
  1. Verifies presence of both perp + spot 8h CSV for V1_BASELINE_UNIVERSE
  2. Loads + aligns the two on open_time
  3. Reports row count, coverage, basis dispersion per symbol

Run from worktree root:
    uv run python analysis/iteration_v1-034/data_source_check.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

V1_SYMBOLS = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")
DATA_DIR = Path("data")
IS_START_MS = 1577836800000  # 2020-01-01
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 (sacred constant)

print("\n=== iter-v1/034 Phase 1: data source viability check ===\n")
print("Decision: BASIS pivot (Liquidations not viable per Binance Vision 404s).")
print(f"V1 universe: {V1_SYMBOLS}\n")

rows = []
for sym in V1_SYMBOLS:
    perp_path = DATA_DIR / sym / "8h.csv"
    spot_path = DATA_DIR / "spot" / sym / "8h.csv"
    perp = pd.read_csv(perp_path)
    spot = pd.read_csv(spot_path)
    # IS window only
    perp_is = perp[(perp["open_time"] >= IS_START_MS) & (perp["open_time"] < OOS_CUTOFF_MS)]
    spot_is = spot[(spot["open_time"] >= IS_START_MS) & (spot["open_time"] < OOS_CUTOFF_MS)]
    # align by open_time
    merged = perp_is[["open_time", "close"]].rename(columns={"close": "perp"}).merge(
        spot_is[["open_time", "close"]].rename(columns={"close": "spot"}),
        on="open_time", how="inner",
    )
    merged["basis_bps"] = (merged["perp"] - merged["spot"]) / merged["spot"] * 10_000  # bps
    rows.append({
        "symbol": sym,
        "perp_rows_IS": len(perp_is),
        "spot_rows_IS": len(spot_is),
        "merged_rows_IS": len(merged),
        "perp_first": pd.to_datetime(perp_is["open_time"].iloc[0], unit="ms").strftime("%Y-%m-%d"),
        "spot_first": pd.to_datetime(spot_is["open_time"].iloc[0], unit="ms").strftime("%Y-%m-%d"),
        "merged_first": pd.to_datetime(merged["open_time"].iloc[0], unit="ms").strftime("%Y-%m-%d"),
        "basis_mean_bps": round(merged["basis_bps"].mean(), 2),
        "basis_std_bps": round(merged["basis_bps"].std(), 2),
        "basis_p1_bps": round(merged["basis_bps"].quantile(0.01), 2),
        "basis_p99_bps": round(merged["basis_bps"].quantile(0.99), 2),
    })

df = pd.DataFrame(rows)
print("Basis (perp-spot) IS coverage and dispersion:\n")
print(df.to_string(index=False))

# fetch cost: ZERO (data already on disk)
print("\nFetch cost: 0 min — both perp + spot 8h CSV already on disk.")
print("Anchor wall-clock from /016 (43-feat v1 EXPLORATION): ~50 min compute.")
print("Modal wall-clock estimate: ~50 min (1 NEW feature → negligible cost overhead).")
print("\nAxis decision: PROCEED with BASIS Z-SCORE (perp-spot) as NEW feature family.\n")

# write a small markdown summary for reproducibility
out = Path("analysis/iteration_v1-034/data_source_check_summary.csv")
df.to_csv(out, index=False)
print(f"Wrote: {out}")
