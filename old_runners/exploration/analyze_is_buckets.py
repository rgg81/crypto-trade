"""IS-only bucket analysis for iter 157 rule-based filter.

Computes per-bucket WR and mean PnL for:
- BTC NATR_21 quartile at trade open
- Traded-symbol ADX_14 quartile
- Hour of day
- Symbol
- Direction
- (regime-dependent combos)

Identifies buckets with below-break-even WR (< 33.3% for 8%/4% RR) for
rule-based exclusion.
"""

import csv
import datetime
from pathlib import Path

import numpy as np
import pandas as pd


OOS_CUTOFF_MS = int(
    datetime.datetime(2025, 3, 24, tzinfo=datetime.UTC).timestamp() * 1000
)

SYMBOLS = ["BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT"]


def lookup_asof(df: pd.DataFrame, col: str, ts_ms: int) -> float:
    idx = df.index.searchsorted(ts_ms, side="right") - 1
    if idx < 0:
        return np.nan
    val = df[col].iloc[idx]
    return float(val) if not pd.isna(val) else np.nan


def main() -> None:
    # Load IS trades only
    trades = []
    with open("reports/iteration_138/in_sample/trades.csv") as f:
        for row in csv.DictReader(f):
            trades.append(row)
    print(f"IS trades loaded: {len(trades)}")

    # Load feature frames
    frames = {}
    for sym in SYMBOLS:
        path = f"data/features/{sym}_8h_features.parquet"
        df = pd.read_parquet(path, columns=[
            "open_time", "vol_natr_21", "trend_adx_14", "mom_rsi_14",
        ])
        df = df.set_index("open_time").sort_index()
        frames[sym] = df
    btc_df = frames["BTCUSDT"]

    # Enrich trades with features
    records = []
    for t in trades:
        sym = t["symbol"]
        ot = int(t["open_time"])
        sym_df = frames[sym]
        rec = {
            "symbol": sym,
            "direction": int(t["direction"]),
            "hour": datetime.datetime.fromtimestamp(
                ot / 1000, tz=datetime.UTC
            ).hour,
            "net_pnl": float(t["net_pnl_pct"]),
            "is_win": int(float(t["net_pnl_pct"]) > 0),
            "sym_natr_21": lookup_asof(sym_df, "vol_natr_21", ot),
            "sym_adx_14": lookup_asof(sym_df, "trend_adx_14", ot),
            "sym_rsi_14": lookup_asof(sym_df, "mom_rsi_14", ot),
            "btc_natr_21": lookup_asof(btc_df, "vol_natr_21", ot),
            "btc_adx_14": lookup_asof(btc_df, "trend_adx_14", ot),
            "btc_rsi_14": lookup_asof(btc_df, "mom_rsi_14", ot),
        }
        records.append(rec)

    df = pd.DataFrame(records)
    overall_wr = df["is_win"].mean()
    overall_pnl = df["net_pnl"].mean()
    print(f"Overall IS WR: {overall_wr*100:.1f}%, mean PnL: {overall_pnl:+.2f}%")
    print(f"Break-even WR (8%/4% = 1:2): 33.3%\n")

    # Bucket by BTC NATR quartile
    print("=== BTC NATR_21 at open (quartiles) ===")
    df["btc_natr_q"] = pd.qcut(df["btc_natr_21"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    print(df.groupby("btc_natr_q", observed=True).agg(
        n=("is_win", "count"),
        wr=("is_win", "mean"),
        mean_pnl=("net_pnl", "mean"),
        min_natr=("btc_natr_21", "min"),
        max_natr=("btc_natr_21", "max"),
    ).round(3))

    # Bucket by traded-symbol ADX quartile
    print("\n=== Traded-symbol ADX_14 (quartiles) ===")
    df["sym_adx_q"] = pd.qcut(df["sym_adx_14"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    print(df.groupby("sym_adx_q", observed=True).agg(
        n=("is_win", "count"),
        wr=("is_win", "mean"),
        mean_pnl=("net_pnl", "mean"),
    ).round(3))

    # Bucket by traded-symbol NATR quartile
    print("\n=== Traded-symbol NATR_21 (quartiles) ===")
    df["sym_natr_q"] = pd.qcut(df["sym_natr_21"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    print(df.groupby("sym_natr_q", observed=True).agg(
        n=("is_win", "count"),
        wr=("is_win", "mean"),
        mean_pnl=("net_pnl", "mean"),
    ).round(3))

    # Hour of day
    print("\n=== Hour of day ===")
    print(df.groupby("hour").agg(
        n=("is_win", "count"),
        wr=("is_win", "mean"),
        mean_pnl=("net_pnl", "mean"),
    ).round(3))

    # Direction
    print("\n=== Direction ===")
    print(df.groupby("direction").agg(
        n=("is_win", "count"),
        wr=("is_win", "mean"),
        mean_pnl=("net_pnl", "mean"),
    ).round(3))

    # Symbol
    print("\n=== Symbol ===")
    print(df.groupby("symbol").agg(
        n=("is_win", "count"),
        wr=("is_win", "mean"),
        mean_pnl=("net_pnl", "mean"),
    ).round(3))

    # Symbol x Direction
    print("\n=== Symbol × Direction ===")
    print(df.groupby(["symbol", "direction"]).agg(
        n=("is_win", "count"),
        wr=("is_win", "mean"),
        mean_pnl=("net_pnl", "mean"),
    ).round(3))

    # Combination: BTC NATR quartile × Symbol
    print("\n=== BTC NATR × Symbol (mean PnL) ===")
    pivot = df.pivot_table(
        index="btc_natr_q", columns="symbol", values="net_pnl",
        aggfunc="mean", observed=True,
    ).round(2)
    print(pivot)

    # Print NATR quartile breakpoints for OOS filter
    print("\n=== BTC NATR_21 quartile thresholds (IS) ===")
    for q in [0.25, 0.5, 0.75, 0.8, 0.9]:
        print(f"  p{q*100:.0f}: {df['btc_natr_21'].quantile(q):.3f}")
    print("\n=== Traded-sym ADX_14 quartile thresholds (IS) ===")
    for q in [0.1, 0.25, 0.5, 0.75, 0.9]:
        print(f"  p{q*100:.0f}: {df['sym_adx_14'].quantile(q):.3f}")
    print("\n=== Traded-sym NATR_21 quartile thresholds (IS) ===")
    for q in [0.25, 0.5, 0.75, 0.9]:
        print(f"  p{q*100:.0f}: {df['sym_natr_21'].quantile(q):.3f}")


if __name__ == "__main__":
    main()
