"""Full-OOS-window reconciliation: live dry_run.db vs backtest CSVs.

Compares trades from the live engine's catch-up output to the backtest
trades.csv files for v1 and v2. Reports field-by-field divergences
across the entire OOS window (2025-03-24 onwards) with extra detail on
March 2026 and April 2026 specifically.

Usage:
    uv run python scripts/reconcile_full_oos.py [--db data/dry_run.db]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from tests.live.test_backtest_parity_v2 import (  # noqa: E402
    TRADE_COLS,
    _read_closed_trades_from_db,
)

V1_TRADES_CSV = Path("reports/iteration_186/out_of_sample/trades.csv")
V2_TRADES_CSV = Path("reports-v2/iteration_v2-069/out_of_sample/trades.csv")
V1_SYMS = {"BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"}
V2_SYMS = {"DOGEUSDT", "SOLUSDT", "XRPUSDT", "NEARUSDT"}

OOS_CUTOFF_MS = pd.Timestamp("2025-03-24", tz="UTC").value // 1_000_000
MAR_2026_MS = pd.Timestamp("2026-03-01", tz="UTC").value // 1_000_000
APR_2026_MS = pd.Timestamp("2026-04-01", tz="UTC").value // 1_000_000


def _key(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_key"] = df["symbol"].astype(str) + "|" + df["open_time"].astype(str)
    return df


def _diff_shared(li: pd.DataFrame, bi: pd.DataFrame, label: str) -> int:
    """Compare every TRADE_COLS field on shared keys. Tolerance 5e-4 (CSV is 4dp)."""
    common = sorted(set(li.index) & set(bi.index))
    if not common:
        print(f"  {label}: no shared trades")
        return 0
    diffs: dict[str, list[tuple]] = {c: [] for c in TRADE_COLS}
    for k in common:
        for c in TRADE_COLS:
            a, b = li.at[k, c], bi.at[k, c]
            if isinstance(a, str):
                if a != b:
                    diffs[c].append((k, a, b))
            else:
                d = abs(float(a) - float(b))
                if d > 5e-4:
                    diffs[c].append((k, float(a), float(b), d))
    print(f"\n  {label}: {len(common)} shared trades")
    total_div = 0
    for c, items in diffs.items():
        if not items:
            print(f"    {c}: 0 ✓")
        else:
            total_div += len(items)
            print(f"    {c}: {len(items)} mismatches")
            for x in items[:3]:
                if len(x) == 4:
                    k, a, b, d = x
                    ot = pd.to_datetime(int(k.split("|")[1]), unit="ms", utc=True).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    sym = k.split("|")[0]
                    print(f"      {ot} {sym:9s} live={a:.6f} bt={b:.6f} Δ={d:.6f}")
                else:
                    k, a, b = x
                    print(f"      {k} live={a} bt={b}")
    return total_div


def _compare_window(
    label: str,
    live: pd.DataFrame,
    bt: pd.DataFrame,
    syms: set[str],
    floor_ms: int,
    ceil_ms: int | None = None,
) -> int:
    """Compare live vs bt over [floor_ms, ceil_ms). Returns total divergences."""
    cond_l = live["symbol"].isin(syms) & (live["open_time"] >= floor_ms)
    cond_b = bt["symbol"].isin(syms) & (bt["open_time"] >= floor_ms)
    if ceil_ms is not None:
        cond_l = cond_l & (live["open_time"] < ceil_ms)
        cond_b = cond_b & (bt["open_time"] < ceil_ms)
    live_w = _key(live[cond_l].sort_values("open_time"))
    bt_w = _key(bt[cond_b].sort_values("open_time"))

    only_live = sorted(set(live_w["_key"]) - set(bt_w["_key"]))
    only_bt = sorted(set(bt_w["_key"]) - set(live_w["_key"]))

    print("=" * 78)
    print(f"{label}: live={len(live_w)}  backtest={len(bt_w)}")
    print("=" * 78)
    print(f"  set match: {len(set(live_w['_key']) & set(bt_w['_key']))} shared")
    if only_live:
        print(f"  only-in-live ({len(only_live)}):")
        for k in only_live[:8]:
            ot = pd.to_datetime(int(k.split("|")[1]), unit="ms", utc=True).strftime(
                "%Y-%m-%d %H:%M"
            )
            sym = k.split("|")[0]
            print(f"    {ot} {sym}")
    if only_bt:
        print(f"  only-in-backtest ({len(only_bt)}):")
        for k in only_bt[:8]:
            ot = pd.to_datetime(int(k.split("|")[1]), unit="ms", utc=True).strftime(
                "%Y-%m-%d %H:%M"
            )
            sym = k.split("|")[0]
            print(f"    {ot} {sym}")

    total = len(only_live) + len(only_bt)
    if shared := set(live_w["_key"]) & set(bt_w["_key"]):
        li = live_w.set_index("_key")
        bi = bt_w.set_index("_key")
        # Restrict to shared keys for field comparison
        li = li.loc[sorted(shared)]
        bi = bi.loc[sorted(shared)]
        total += _diff_shared(li, bi, "field-by-field")
    return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/dry_run.db", type=str)
    args = ap.parse_args()

    db = Path(args.db)
    if not db.exists():
        sys.exit(f"DB not found: {db}")

    live = _read_closed_trades_from_db(db)
    print(f"Loaded {len(live)} closed trades from {db}")

    v1_bt = pd.read_csv(V1_TRADES_CSV)
    v2_bt = pd.read_csv(V2_TRADES_CSV)
    v2_bt = v2_bt[v2_bt["weight_factor"] > 0]
    print(
        f"Backtest: v1={len(v1_bt)}, v2 (nonzero weight)={len(v2_bt)}\n"
    )

    div_total = 0

    # ---- FULL OOS WINDOW ----
    print("\n┌────────────────────────────────────────────────────────────────────────────┐")
    print("│ FULL OOS WINDOW (open_time ≥ 2025-03-24)                                  │")
    print("└────────────────────────────────────────────────────────────────────────────┘")
    div_total += _compare_window("V1 full OOS", live, v1_bt, V1_SYMS, OOS_CUTOFF_MS)
    div_total += _compare_window("V2 full OOS", live, v2_bt, V2_SYMS, OOS_CUTOFF_MS)

    # ---- MARCH 2026 SPECIFICALLY ----
    print("\n┌────────────────────────────────────────────────────────────────────────────┐")
    print("│ MARCH 2026 (2026-03-01 ≤ open_time < 2026-04-01)                          │")
    print("└────────────────────────────────────────────────────────────────────────────┘")
    div_total += _compare_window("V1 March 2026", live, v1_bt, V1_SYMS, MAR_2026_MS, APR_2026_MS)
    div_total += _compare_window("V2 March 2026", live, v2_bt, V2_SYMS, MAR_2026_MS, APR_2026_MS)

    # ---- APRIL 2026 SPECIFICALLY ----
    print("\n┌────────────────────────────────────────────────────────────────────────────┐")
    print("│ APRIL 2026 (open_time ≥ 2026-04-01)                                       │")
    print("└────────────────────────────────────────────────────────────────────────────┘")
    div_total += _compare_window("V1 April 2026", live, v1_bt, V1_SYMS, APR_2026_MS)
    div_total += _compare_window("V2 April 2026", live, v2_bt, V2_SYMS, APR_2026_MS)

    print("\n" + "=" * 78)
    if div_total == 0:
        print("RESULT: ✓ ALL WINDOWS IDENTICAL — full backtest parity achieved")
    else:
        print(f"RESULT: ✗ {div_total} divergences across all windows — investigate above")
    print("=" * 78)


if __name__ == "__main__":
    main()
