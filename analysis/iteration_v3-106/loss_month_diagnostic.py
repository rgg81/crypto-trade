"""iter-v3/106 EDA script 1 — IS loss-month diagnostic.

User-directed risk-management axis: "analyse in IS the months where model
didn't perform. Those months most likely the model hasn't seen before it needs
to stop."

This script takes the canonical /059 baseline IS trade roster
(reports-v3/iteration_v3-059/in_sample/trades.csv — the 10-seed unified-ensemble
single trade roster, NOT /101/102/105 which carried rejected axes) and computes,
per calendar month, strictly IS-only:

  - net PnL%        (sum of net_pnl_pct over the month's trades)
  - weighted PnL    (sum of weighted_pnl — what feeds the portfolio Sharpe)
  - monthly Sharpe proxy (mean / std of per-trade weighted_pnl in the month)
  - trade count, win rate
  - per-symbol PnL attribution within the month

Then ranks the WORST months and prints a clean loss-vs-profit partition.

NO CHEATING — strictly IS-only. Every trade entering any computation has
open_time < OOS_CUTOFF_MS = 1742774400000 (2025-03-24). The OOS roster is never
read. The detector and its threshold (EDA scripts 2 + 3) are calibrated only on
the months identified here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.config import OOS_CUTOFF_MS

TRADES_CSV = "reports-v3/iteration_v3-059/in_sample/trades.csv"
OUT_DIR = "analysis/iteration_v3-106"


def load_is_trades() -> pd.DataFrame:
    df = pd.read_csv(TRADES_CSV)
    # Hard IS-only guard — assert no post-cutoff rows leaked into the /059 IS CSV.
    assert (df["open_time"] < OOS_CUTOFF_MS).all(), (
        "IS trade CSV contains post-cutoff rows — IS-only invariant violated"
    )
    df["open_dt"] = pd.to_datetime(df["open_time"], unit="ms")
    df["month"] = df["open_dt"].dt.to_period("M").astype(str)
    return df


def per_month_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for month, g in df.groupby("month"):
        wpnl = g["weighted_pnl"].to_numpy()
        net = g["net_pnl_pct"].to_numpy()
        # Monthly Sharpe proxy: per-trade weighted_pnl mean / std. With few trades
        # this is noisy, so we report it alongside the raw sum, which is the
        # robust signal for "did this month lose money".
        sharpe = float(wpnl.mean() / wpnl.std(ddof=1)) if len(wpnl) > 1 and wpnl.std(ddof=1) > 0 else np.nan
        rows.append(
            {
                "month": month,
                "n_trades": len(g),
                "win_rate": float((net > 0).mean()),
                "net_pnl_pct": float(net.sum()),
                "weighted_pnl": float(wpnl.sum()),
                "trade_sharpe": sharpe,
                "bch_wpnl": float(g.loc[g["symbol"] == "BCHUSDT", "weighted_pnl"].sum()),
                "trx_wpnl": float(g.loc[g["symbol"] == "TRXUSDT", "weighted_pnl"].sum()),
                "ldo_wpnl": float(g.loc[g["symbol"] == "LDOUSDT", "weighted_pnl"].sum()),
            }
        )
    out = pd.DataFrame(rows).sort_values("month").reset_index(drop=True)
    return out


def main() -> None:
    df = load_is_trades()
    tbl = per_month_table(df)

    n_active_months = len(tbl)
    loss = tbl[tbl["weighted_pnl"] < 0].copy()
    profit = tbl[tbl["weighted_pnl"] >= 0].copy()

    print("=" * 78)
    print("iter-v3/106 EDA 1 — IS LOSS-MONTH DIAGNOSTIC (/059 baseline IS roster)")
    print("=" * 78)
    print(f"IS trades total           : {len(df)}")
    print(f"IS active calendar months : {n_active_months}")
    print(f"  loss months (wpnl < 0)  : {len(loss)}  ({len(loss)/n_active_months:.0%})")
    print(f"  profit months (wpnl>=0) : {len(profit)}")
    print(f"IS total weighted_pnl     : {tbl['weighted_pnl'].sum():+.2f}")
    print(f"  sum over loss months    : {loss['weighted_pnl'].sum():+.2f}")
    print(f"  sum over profit months  : {profit['weighted_pnl'].sum():+.2f}")
    print()

    print("--- WORST 10 IS MONTHS by weighted_pnl ---")
    worst = tbl.sort_values("weighted_pnl").head(10)
    print(
        worst[
            ["month", "n_trades", "win_rate", "weighted_pnl", "net_pnl_pct", "bch_wpnl", "trx_wpnl", "ldo_wpnl"]
        ].to_string(index=False, float_format=lambda x: f"{x:.3f}")
    )
    print()

    print("--- ALL IS MONTHS (chronological) ---")
    print(
        tbl[["month", "n_trades", "win_rate", "weighted_pnl", "net_pnl_pct"]].to_string(
            index=False, float_format=lambda x: f"{x:.3f}"
        )
    )
    print()

    # Loss concentration: how much of the IS drag is in the worst-N months?
    sorted_w = tbl.sort_values("weighted_pnl")["weighted_pnl"].to_numpy()
    total = tbl["weighted_pnl"].sum()
    for n in (3, 5, 6, 8):
        drag = sorted_w[:n].sum()
        print(f"  worst {n} months: cumulative wpnl {drag:+.2f}  "
              f"(removing them would lift IS wpnl by {-drag:+.2f} -> {total - drag:+.2f})")

    tbl.to_csv(f"{OUT_DIR}/T1_per_month_is_pnl.csv", index=False)
    worst.to_csv(f"{OUT_DIR}/T1b_worst10_is_months.csv", index=False)
    print()
    print(f"Wrote {OUT_DIR}/T1_per_month_is_pnl.csv  ({len(tbl)} rows)")
    print(f"Wrote {OUT_DIR}/T1b_worst10_is_months.csv  (10 rows)")


if __name__ == "__main__":
    main()
