"""Show specific trades that differ between BASELINE and CLEAN runs.

For each BASELINE-only trade: show symbol, time, direction, entry, exit, PnL
For each CLEAN-only trade: same
For shared trades with different PnL: show both sides.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

BASELINE_DIR = Path("/home/roberto/crypto-trade/reports/iteration_152_min33_max200")
CLEAN_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("reports/iteration_152_core")


def _load(p: Path) -> pd.DataFrame:
    df = pd.read_csv(p)
    df["open_time"] = pd.to_numeric(df["open_time"])
    df["close_time"] = pd.to_numeric(df["close_time"])
    df["open_ts"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_ts"] = pd.to_datetime(df["close_time"], unit="ms")
    df["key"] = list(zip(df.symbol, df.open_time, df.direction, strict=False))
    return df


def main() -> None:
    base = _load(BASELINE_DIR / "out_of_sample" / "trades.csv")
    clean = _load(CLEAN_DIR / "out_of_sample" / "trades.csv")

    shared = set(base.key) & set(clean.key)
    base_only = base[~base.key.isin(shared)].sort_values("open_time").reset_index(drop=True)
    clean_only = clean[~clean.key.isin(shared)].sort_values("open_time").reset_index(drop=True)

    print("=" * 95)
    print(f"BASELINE-ONLY TRADES ({len(base_only)}) — BASELINE opened these, CLEAN did not")
    print("=" * 95)
    print(f"{'open_ts':<20} {'sym':<9} {'dir':<3} {'entry':>10} {'exit':>10} "
          f"{'exit_reason':<15} {'net_pnl%':>8} {'wpnl':>7}")
    for _, r in base_only.iterrows():
        print(
            f"{r.open_ts.strftime('%Y-%m-%d %H:%M'):<20} {r.symbol:<9} "
            f"{r.direction:+d}  {r.entry_price:>10.4f} {r.exit_price:>10.4f} "
            f"{r.exit_reason:<15} {r.net_pnl_pct:>+8.2f} {r.weighted_pnl:>+7.2f}"
        )
    print(f"\nBASELINE-only net wpnl: {base_only.weighted_pnl.sum():+.2f}  "
          f"WR: {100 * (base_only.weighted_pnl > 0).mean():.1f}%")

    print("\n" + "=" * 95)
    print(f"CLEAN-ONLY TRADES ({len(clean_only)}) — CLEAN opened these, BASELINE did not")
    print("=" * 95)
    print(f"{'open_ts':<20} {'sym':<9} {'dir':<3} {'entry':>10} {'exit':>10} "
          f"{'exit_reason':<15} {'net_pnl%':>8} {'wpnl':>7}")
    for _, r in clean_only.iterrows():
        print(
            f"{r.open_ts.strftime('%Y-%m-%d %H:%M'):<20} {r.symbol:<9} "
            f"{r.direction:+d}  {r.entry_price:>10.4f} {r.exit_price:>10.4f} "
            f"{r.exit_reason:<15} {r.net_pnl_pct:>+8.2f} {r.weighted_pnl:>+7.2f}"
        )
    print(f"\nCLEAN-only net wpnl: {clean_only.weighted_pnl.sum():+.2f}  "
          f"WR: {100 * (clean_only.weighted_pnl > 0).mean():.1f}%")

    # Focus on July 2025 — catastrophic month in CLEAN
    print("\n" + "=" * 95)
    print("JULY 2025 DETAIL — BASELINE vs CLEAN side-by-side")
    print("=" * 95)
    b_jul = base[(base.open_ts >= "2025-07-01") & (base.open_ts < "2025-08-01")].sort_values("open_time")
    c_jul = clean[(clean.open_ts >= "2025-07-01") & (clean.open_ts < "2025-08-01")].sort_values("open_time")
    print(f"BASELINE Jul 2025: {len(b_jul)} trades, wpnl {b_jul.weighted_pnl.sum():+.2f}, "
          f"WR {100 * (b_jul.weighted_pnl > 0).mean():.1f}%")
    print(f"CLEAN    Jul 2025: {len(c_jul)} trades, wpnl {c_jul.weighted_pnl.sum():+.2f}, "
          f"WR {100 * (c_jul.weighted_pnl > 0).mean():.1f}%")
    print()
    print("BASELINE July trades:")
    for _, r in b_jul.iterrows():
        mark = "SHARED" if r.key in shared else "baseline-only"
        print(f"  {r.open_ts.strftime('%m-%d %H:%M'):<12} {r.symbol:<9} {r.direction:+d} "
              f"entry={r.entry_price:>10.4f} exit={r.exit_price:>10.4f} "
              f"{r.exit_reason:<12} wpnl={r.weighted_pnl:>+6.2f}  [{mark}]")
    print("\nCLEAN July trades:")
    for _, r in c_jul.iterrows():
        mark = "SHARED" if r.key in shared else "clean-only"
        print(f"  {r.open_ts.strftime('%m-%d %H:%M'):<12} {r.symbol:<9} {r.direction:+d} "
              f"entry={r.entry_price:>10.4f} exit={r.exit_price:>10.4f} "
              f"{r.exit_reason:<12} wpnl={r.weighted_pnl:>+6.2f}  [{mark}]")


if __name__ == "__main__":
    main()
