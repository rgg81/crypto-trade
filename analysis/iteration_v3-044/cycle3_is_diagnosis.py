"""
iter-v3/044 — Cycle 3 IS Bottleneck Diagnosis (QR analysis script)

Question: WHY is iter-v3/040 anchor IS Sharpe stuck at +0.79?
3 NEGATIVE iterations in a row (041 pruning, 042 universal ATR, 043 Kaufman ER)
suggest the IS surface is at a local maximum resistant to small changes.
But what specifically is the IS bottleneck?

Approach:
- Read iter-v3/040 IS trades + OOS trades + per-symbol importance.
- Decompose IS Sharpe contribution by (symbol, direction).
- Identify whether the constraint is:
  (a) per-symbol — one symbol drags the aggregate,
  (b) per-direction — long/short asymmetry,
  (c) per-temporal — specific months dominate the loss,
  (d) per-feature — universal under-importance of regime/momentum filtering.
- Cross-check IS pattern vs OOS pattern. If pattern PERSISTS OOS, structural;
  if pattern only IS, model overfit; if pattern only OOS, regime shift.

Outputs:
- analysis/iteration_v3-044/is_constraint_analysis.csv
- analysis/iteration_v3-044/synthesis.md (free-form narrative summary)

Per-symbol attribution from comparison.csv format isn't available so we
recompute from in_sample/out_of_sample trades.csv.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ITER = "iteration_v3-040"
ROOT = Path(__file__).resolve().parents[2]
IS_TRADES = ROOT / f"reports-v3/{ITER}/in_sample/trades.csv"
OOS_TRADES = ROOT / f"reports-v3/{ITER}/out_of_sample/trades.csv"
PORTFOLIO_IMP = ROOT / f"reports-v3/{ITER}/in_sample/model_importance_last_month_portfolio.csv"

OUT_DIR = ROOT / "analysis/iteration_v3-044"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "is_constraint_analysis.csv"


def per_symbol_direction_breakdown(trades: pd.DataFrame, label: str) -> pd.DataFrame:
    """Per-symbol per-direction trade breakdown."""
    grp = (
        trades.groupby(["symbol", "direction"])
        .agg(
            n_trades=("weighted_pnl", "count"),
            sum_pnl=("weighted_pnl", "sum"),
            avg_pnl=("weighted_pnl", "mean"),
            std_pnl=("weighted_pnl", "std"),
            wr_pct=("weighted_pnl", lambda s: (s > 0).mean() * 100),
        )
        .reset_index()
    )
    grp["sharpe_per_trade"] = grp["avg_pnl"] / grp["std_pnl"]
    grp["window"] = label
    grp["direction_label"] = grp["direction"].map({1: "LONG", -1: "SHORT"})
    return grp


def main() -> None:
    is_trades = pd.read_csv(IS_TRADES)
    oos_trades = pd.read_csv(OOS_TRADES)
    is_trades["close_dt"] = pd.to_datetime(is_trades["close_time"], unit="ms")
    oos_trades["close_dt"] = pd.to_datetime(oos_trades["close_time"], unit="ms")
    is_trades["year_month"] = is_trades["close_dt"].dt.to_period("M")
    oos_trades["year_month"] = oos_trades["close_dt"].dt.to_period("M")

    # Total IS / OOS
    total_is = is_trades["weighted_pnl"].sum()
    total_oos = oos_trades["weighted_pnl"].sum()

    print("=" * 70)
    print("DIAGNOSIS 1 — Per-symbol contribution")
    print("=" * 70)
    per_sym = (
        is_trades.groupby("symbol")
        .agg(
            n_trades=("weighted_pnl", "count"),
            sum_pnl=("weighted_pnl", "sum"),
            avg_pnl=("weighted_pnl", "mean"),
            std_pnl=("weighted_pnl", "std"),
            wr_pct=("weighted_pnl", lambda s: (s > 0).mean() * 100),
        )
        .reset_index()
    )
    per_sym["sharpe_per_trade"] = per_sym["avg_pnl"] / per_sym["std_pnl"]
    per_sym["pct_of_total_is_pnl"] = per_sym["sum_pnl"] / total_is * 100
    print(per_sym.to_string(index=False))
    print()
    print(f"  Total IS PnL: {total_is:.2f} (sum of weighted_pnl across all symbols)")
    print(f"  Total OOS PnL: {total_oos:.2f}")

    print("=" * 70)
    print("DIAGNOSIS 2 — Per-direction breakdown (IS)")
    print("=" * 70)
    is_dir = per_symbol_direction_breakdown(is_trades, "IS")
    print(is_dir.to_string(index=False))

    print()
    print("=" * 70)
    print("DIAGNOSIS 3 — Per-direction breakdown (OOS)")
    print("=" * 70)
    oos_dir = per_symbol_direction_breakdown(oos_trades, "OOS")
    print(oos_dir.to_string(index=False))

    # IS vs OOS asymmetry comparison (does the long/short imbalance PERSIST OOS?)
    print()
    print("=" * 70)
    print("DIAGNOSIS 4 — IS-vs-OOS direction-asymmetry persistence")
    print("=" * 70)
    is_dir["wr_pct_round"] = is_dir["wr_pct"].round(1)
    oos_dir["wr_pct_round"] = oos_dir["wr_pct"].round(1)
    cmp = is_dir[["symbol", "direction_label", "n_trades", "wr_pct"]].merge(
        oos_dir[["symbol", "direction_label", "n_trades", "wr_pct"]],
        on=["symbol", "direction_label"], how="outer", suffixes=("_is", "_oos")
    )
    cmp["wr_persist_diff"] = cmp["wr_pct_oos"] - cmp["wr_pct_is"]
    print(cmp.to_string(index=False))

    # Temporal — worst IS months
    print()
    print("=" * 70)
    print("DIAGNOSIS 5 — Worst IS months by total PnL")
    print("=" * 70)
    monthly = (
        is_trades.groupby("year_month")
        .agg(n=("weighted_pnl", "count"), pnl=("weighted_pnl", "sum"))
        .reset_index()
    )
    monthly = monthly.sort_values("pnl", ascending=True)
    print("BOTTOM 10 IS months (largest losses):")
    print(monthly.head(10).to_string(index=False))
    print("TOP 5 IS months:")
    print(monthly.tail(5).to_string(index=False))

    # Per-symbol direction-asymmetry summary stat
    print()
    print("=" * 70)
    print("DIAGNOSIS 6 — Direction-asymmetry severity per symbol (IS)")
    print("=" * 70)
    sym_asym = []
    for sym in is_trades["symbol"].unique():
        sub = is_trades[is_trades["symbol"] == sym]
        long_pnl = sub[sub["direction"] == 1]["weighted_pnl"].sum()
        short_pnl = sub[sub["direction"] == -1]["weighted_pnl"].sum()
        long_wr = (sub[sub["direction"] == 1]["weighted_pnl"] > 0).mean() * 100 if len(sub[sub["direction"] == 1]) else float("nan")
        short_wr = (sub[sub["direction"] == -1]["weighted_pnl"] > 0).mean() * 100 if len(sub[sub["direction"] == -1]) else float("nan")
        long_n = len(sub[sub["direction"] == 1])
        short_n = len(sub[sub["direction"] == -1])
        # Net per-direction net contribution
        pnl_imbalance = long_pnl - short_pnl
        wr_gap = (long_wr - short_wr) if not (np.isnan(long_wr) or np.isnan(short_wr)) else float("nan")
        sym_asym.append({
            "symbol": sym,
            "long_n": long_n,
            "long_pnl": long_pnl,
            "long_wr": long_wr,
            "short_n": short_n,
            "short_pnl": short_pnl,
            "short_wr": short_wr,
            "wr_gap_long_minus_short": wr_gap,
            "pnl_imbalance_long_minus_short": pnl_imbalance,
        })
    sym_asym_df = pd.DataFrame(sym_asym).sort_values("pnl_imbalance_long_minus_short")
    print(sym_asym_df.to_string(index=False))
    print()
    print(
        "Symbols with strongly NEGATIVE pnl_imbalance (long_pnl << short_pnl) "
        "are bear-trend symbols where the model is taking bad long signals.\n"
        "Symbols with strongly POSITIVE pnl_imbalance are bull-trend symbols where "
        "shorts are bad."
    )

    # Per-symbol bear-trend check: net market move
    print()
    print("=" * 70)
    print("DIAGNOSIS 7 — Per-symbol net IS price move (market trend)")
    print("=" * 70)
    market_trend = []
    for sym in ["BCHUSDT", "LDOUSDT", "TRXUSDT", "ALGOUSDT"]:
        try:
            df = pd.read_csv(ROOT / f"data/{sym}/8h.csv")
            df["close_dt"] = pd.to_datetime(df["close_time"], unit="ms").dt.tz_localize("UTC")
            df["close"] = pd.to_numeric(df["close"])
            IS_START = pd.Timestamp("2023-03-24", tz="UTC")
            IS_END = pd.Timestamp("2025-03-24", tz="UTC")
            is_d = df[(df["close_dt"] >= IS_START) & (df["close_dt"] < IS_END)]
            oos_d = df[(df["close_dt"] >= IS_END)]
            if len(is_d) > 0 and len(oos_d) > 0:
                is_ret = (is_d["close"].iloc[-1] / is_d["close"].iloc[0] - 1) * 100
                oos_ret = (oos_d["close"].iloc[-1] / oos_d["close"].iloc[0] - 1) * 100
                market_trend.append({
                    "symbol": sym,
                    "is_market_return_pct": is_ret,
                    "oos_market_return_pct": oos_ret,
                })
        except Exception as e:  # noqa: BLE001
            print(f"  Skip {sym}: {e}")
    mt_df = pd.DataFrame(market_trend)
    print(mt_df.to_string(index=False))

    # Combine: market trend × direction asymmetry
    print()
    print("=" * 70)
    print("DIAGNOSIS 8 — Combined: bear-trend symbols → long signals fail")
    print("=" * 70)
    merged = sym_asym_df.merge(mt_df, on="symbol", how="outer")
    print(merged.to_string(index=False))

    # Save full table
    sym_asym_df.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {OUT_CSV}")


if __name__ == "__main__":
    main()
