"""Forensic trade-by-trade comparison: BASELINE (main, Apr 5) vs clean reproduction (Apr 20).

Main's `reports/iteration_152_min33_max200/` = BASELINE measurement giving +2.83 OOS Sharpe.
Local `reports/iteration_152_core/` = clean reproduction giving +1.04 OOS Sharpe.

We match trades by (symbol, open_time) to answer:
1. How many trades appear in BOTH runs? In only one?
2. For shared trades, do entry/exit/PnL match?
3. For unique trades, what's the pattern — extra OPEN signals or missing ones?
4. Which months differ most?
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import sys

BASELINE_DIR = Path("/home/roberto/crypto-trade/reports/iteration_152_min33_max200")
# arg[1]: clean reports dir (default: iteration_152_core)
CLEAN_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("reports/iteration_152_core")


def _load(p: Path, tag: str) -> pd.DataFrame:
    df = pd.read_csv(p)
    df["open_time"] = pd.to_numeric(df["open_time"])
    df["close_time"] = pd.to_numeric(df["close_time"])
    df["source"] = tag
    df["open_ts"] = pd.to_datetime(df["open_time"], unit="ms")
    df["month"] = df["open_ts"].dt.to_period("M")
    return df


def main() -> None:
    base = _load(BASELINE_DIR / "out_of_sample" / "trades.csv", "BASELINE")
    clean = _load(CLEAN_DIR / "out_of_sample" / "trades.csv", "CLEAN")

    print("=" * 72)
    print("OOS TRADE COUNT COMPARISON")
    print("=" * 72)
    print(f"BASELINE trades:  {len(base)} (Apr 5 measurement, reported +2.83 Sharpe)")
    print(f"CLEAN trades:     {len(clean)} (Apr 20 measurement, fresh data)")
    print()

    # Key for matching: (symbol, open_time, direction)
    base["key"] = list(zip(base.symbol, base.open_time, base.direction, strict=False))
    clean["key"] = list(zip(clean.symbol, clean.open_time, clean.direction, strict=False))

    base_keys = set(base["key"])
    clean_keys = set(clean["key"])

    shared_keys = base_keys & clean_keys
    baseline_only = base_keys - clean_keys
    clean_only = clean_keys - base_keys

    print(f"Trades in BOTH runs:        {len(shared_keys)}")
    print(f"Trades only in BASELINE:    {len(baseline_only)}")
    print(f"Trades only in CLEAN:       {len(clean_only)}")
    print()

    # For shared trades: compare metrics
    base_shared = base[base.key.isin(shared_keys)].set_index("key").sort_index()
    clean_shared = clean[clean.key.isin(shared_keys)].set_index("key").sort_index()

    print("=" * 72)
    print("SHARED TRADES — do entry/exit/PnL MATCH?")
    print("=" * 72)

    for col in ["entry_price", "exit_price", "weight_factor", "net_pnl_pct", "weighted_pnl"]:
        a = base_shared[col].to_numpy()
        b = clean_shared[col].to_numpy()
        diff = a - b
        nz = (np.abs(diff) > 1e-6).sum()
        rel = np.abs(diff / (np.abs(a) + 1e-9)).max() if len(a) else 0
        print(
            f"  {col:<18}: {nz}/{len(diff)} trades differ  "
            f"(max abs Δ = {np.abs(diff).max():.6f}, max rel Δ = {rel:.4%})"
        )

    # Exit-reason concordance
    exit_mismatch = (base_shared.exit_reason != clean_shared.exit_reason).sum()
    print(f"  exit_reason      : {exit_mismatch}/{len(base_shared)} trades differ in exit_reason")

    # Total PnL on shared trades
    base_shared_pnl = base_shared.weighted_pnl.sum()
    clean_shared_pnl = clean_shared.weighted_pnl.sum()
    print(f"\n  Shared-trades wpnl: BASELINE={base_shared_pnl:+.2f}, CLEAN={clean_shared_pnl:+.2f}")

    # Breakdown of unique trades per source
    print("\n" + "=" * 72)
    print("BASELINE-ONLY trades (dropped by clean)")
    print("=" * 72)
    base_only_df = base[base.key.isin(baseline_only)]
    print(f"Count: {len(base_only_df)}, net wpnl: {base_only_df.weighted_pnl.sum():+.2f}")
    print(f"  WR: {100 * (base_only_df.weighted_pnl > 0).mean():.1f}%")
    print("\n  By month:")
    by_month = base_only_df.groupby("month").agg(
        trades=("weighted_pnl", "size"),
        wpnl=("weighted_pnl", "sum"),
        wr=("weighted_pnl", lambda s: 100 * (s > 0).mean()),
    )
    print(by_month.to_string())
    print("\n  By symbol:")
    by_sym = base_only_df.groupby("symbol").agg(
        trades=("weighted_pnl", "size"),
        wpnl=("weighted_pnl", "sum"),
    )
    print(by_sym.to_string())

    print("\n" + "=" * 72)
    print("CLEAN-ONLY trades (new in clean, not in baseline)")
    print("=" * 72)
    clean_only_df = clean[clean.key.isin(clean_only)]
    print(f"Count: {len(clean_only_df)}, net wpnl: {clean_only_df.weighted_pnl.sum():+.2f}")
    print(f"  WR: {100 * (clean_only_df.weighted_pnl > 0).mean():.1f}%")
    print("\n  By month:")
    by_month = clean_only_df.groupby("month").agg(
        trades=("weighted_pnl", "size"),
        wpnl=("weighted_pnl", "sum"),
        wr=("weighted_pnl", lambda s: 100 * (s > 0).mean()),
    )
    print(by_month.to_string())
    print("\n  By symbol:")
    by_sym = clean_only_df.groupby("symbol").agg(
        trades=("weighted_pnl", "size"),
        wpnl=("weighted_pnl", "sum"),
    )
    print(by_sym.to_string())

    # Per-month shared-trade agreement
    print("\n" + "=" * 72)
    print("PER-MONTH OVERLAP (OOS)")
    print("=" * 72)
    # Bucket all trades by (month, source), report overlap counts
    for m in sorted(set(base.month) | set(clean.month)):
        bm = base[base.month == m]
        cm = clean[clean.month == m]
        bm_keys = set(bm.key)
        cm_keys = set(cm.key)
        shared = bm_keys & cm_keys
        print(
            f"  {m}: BASELINE={len(bm):3d}  CLEAN={len(cm):3d}  "
            f"shared={len(shared):3d}  "
            f"base-only={len(bm_keys - cm_keys):3d}  "
            f"clean-only={len(cm_keys - bm_keys):3d}"
        )


if __name__ == "__main__":
    main()
