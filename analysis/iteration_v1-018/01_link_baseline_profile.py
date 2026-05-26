"""LINK baseline profile analysis — iter-v1/018 Phase 1 EDA.

Per `feedback_v1_per_cohort_exploration_strategy.md`: cycle-3 EXPLORATIONs pivot to
per-cohort specialization. This iteration tests **LINK-only** specialization.

Reads BASELINE_V1 (v0.v1-baseline-corrected; commit f8bc12c) trades, computes
LINK's per-symbol IS/OOS statistics in detail, compares to other symbols, and
quantifies the "LINK structural OOS edge" claim made at /017 closeout.

Outputs (committed):
- link_per_symbol_compare.csv : per-symbol IS/OOS metrics (LINK vs others)
- link_exit_reason_compare.csv : exit distribution per symbol IS/OOS
- link_monthly_oos.csv : LINK per-month OOS PnL (regime check)
- link_direction_split.csv : LINK long-vs-short PnL split

NO TRAINING. NO MODEL FIT. Pure descriptive analysis from baseline trades.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "reports-v1" / "iteration_v1-baseline"
OUT = ROOT / "analysis" / "iteration_v1-018"
OUT.mkdir(parents=True, exist_ok=True)


def annualized_monthly_sharpe(pnl_pct: pd.Series, close_ms: pd.Series) -> tuple[float, int]:
    """Aggregate net_pnl_pct by calendar month of close_time and return
    monthly-return Sharpe annualized by sqrt(12).
    """
    if len(pnl_pct) == 0:
        return 0.0, 0
    dt = pd.to_datetime(close_ms, unit="ms")
    s = pd.Series(pnl_pct.values, index=dt)
    monthly = s.resample("ME").sum()
    if len(monthly) < 2 or monthly.std() == 0:
        return 0.0, len(monthly)
    return float(monthly.mean() / monthly.std() * math.sqrt(12)), len(monthly)


def per_symbol_block(df: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    for sym in sorted(df["symbol"].unique()):
        sub = df[df["symbol"] == sym]
        wins = (sub["net_pnl_pct"] > 0).sum()
        n = len(sub)
        sr, n_months = annualized_monthly_sharpe(sub["net_pnl_pct"], sub["close_time"])
        avg_w = sub.loc[sub["net_pnl_pct"] > 0, "net_pnl_pct"].mean() if wins else 0.0
        avg_l = sub.loc[sub["net_pnl_pct"] <= 0, "net_pnl_pct"].mean() if (n - wins) else 0.0
        sl = (sub["exit_reason"] == "stop_loss").sum()
        tp = (sub["exit_reason"] == "take_profit").sum()
        to = (sub["exit_reason"] == "timeout").sum()
        eod = (sub["exit_reason"] == "end_of_data").sum()
        # PnL by direction
        long_pnl = sub.loc[sub["direction"] == 1, "net_pnl_pct"].sum()
        short_pnl = sub.loc[sub["direction"] == -1, "net_pnl_pct"].sum()
        n_long = (sub["direction"] == 1).sum()
        n_short = (sub["direction"] == -1).sum()
        rows.append(
            dict(
                split=label,
                symbol=sym,
                n_trades=int(n),
                wins=int(wins),
                win_rate=round(wins / max(n, 1), 4),
                avg_pnl_pct=round(sub["net_pnl_pct"].mean(), 4),
                avg_win_pnl=round(avg_w, 4),
                avg_loss_pnl=round(avg_l, 4),
                std_pnl_pct=round(sub["net_pnl_pct"].std(), 4),
                total_net_pnl_pct=round(sub["net_pnl_pct"].sum(), 4),
                total_weighted_pnl=round(sub["weighted_pnl"].sum(), 4),
                sharpe_monthly_ann=round(sr, 4),
                n_months=int(n_months),
                pct_SL=round(sl / max(n, 1), 4),
                pct_TP=round(tp / max(n, 1), 4),
                pct_TO=round(to / max(n, 1), 4),
                n_long=int(n_long),
                n_short=int(n_short),
                long_pnl_pct=round(long_pnl, 4),
                short_pnl_pct=round(short_pnl, 4),
                eod=int(eod),
            )
        )
    return pd.DataFrame(rows).sort_values(["split", "total_net_pnl_pct"], ascending=[True, False])


def main() -> None:
    print(f"Reading baseline trades from {BASE}")
    is_df = pd.read_csv(BASE / "in_sample" / "trades.csv")
    oos_df = pd.read_csv(BASE / "out_of_sample" / "trades.csv")
    print(f"  IS: {len(is_df)} trades | OOS: {len(oos_df)} trades")

    # 1. Per-symbol IS+OOS profile
    per_sym = pd.concat([per_symbol_block(is_df, "IS"), per_symbol_block(oos_df, "OOS")])
    per_sym_path = OUT / "link_per_symbol_compare.csv"
    per_sym.to_csv(per_sym_path, index=False)
    print(f"\n[1] Per-symbol IS+OOS profile → {per_sym_path}")
    print(per_sym.to_string(index=False))

    # 2. LINK monthly OOS PnL  (regime stability check)
    link_oos = oos_df[oos_df["symbol"] == "LINKUSDT"].copy()
    link_oos["close_dt"] = pd.to_datetime(link_oos["close_time"], unit="ms")
    link_oos["month"] = link_oos["close_dt"].dt.to_period("M").astype(str)
    monthly = (
        link_oos.groupby("month")
        .agg(
            n_trades=("symbol", "size"),
            net_pnl_pct=("net_pnl_pct", "sum"),
            wins=("net_pnl_pct", lambda s: int((s > 0).sum())),
            avg=("net_pnl_pct", "mean"),
        )
        .reset_index()
    )
    monthly_path = OUT / "link_monthly_oos.csv"
    monthly.to_csv(monthly_path, index=False)
    print(f"\n[2] LINK OOS monthly PnL → {monthly_path}")
    print(monthly.to_string(index=False))

    # 3. LINK direction split (long vs short)
    rows = []
    for label, df in [("IS", is_df), ("OOS", oos_df)]:
        link = df[df["symbol"] == "LINKUSDT"]
        for direction in (1, -1):
            sub = link[link["direction"] == direction]
            wins = (sub["net_pnl_pct"] > 0).sum()
            n = len(sub)
            rows.append(
                dict(
                    split=label,
                    direction=("long" if direction == 1 else "short"),
                    n_trades=int(n),
                    wins=int(wins),
                    win_rate=round(wins / max(n, 1), 4),
                    total_net_pnl_pct=round(sub["net_pnl_pct"].sum(), 4),
                    avg_pnl_pct=round(sub["net_pnl_pct"].mean() if n else 0.0, 4),
                )
            )
    dirsplit = pd.DataFrame(rows)
    dirsplit_path = OUT / "link_direction_split.csv"
    dirsplit.to_csv(dirsplit_path, index=False)
    print(f"\n[3] LINK direction split (long/short) → {dirsplit_path}")
    print(dirsplit.to_string(index=False))

    # 4. LINK iteration-level OOS trajectory: scan /011-/017
    # Map (read each iter's OOS LINK trades, compute total + WR)
    rows = []
    for iter_id in [11, 12, 13, 14, 15, 16, 17]:
        iter_dir = ROOT / "reports-v1" / f"iteration_v1-{iter_id:03d}"
        oos_path = iter_dir / "out_of_sample" / "trades.csv"
        if not oos_path.exists():
            rows.append(
                dict(iter=iter_id, exists=False, link_oos_trades=0, link_oos_net_pnl=0.0)
            )
            continue
        d = pd.read_csv(oos_path)
        l = d[d["symbol"] == "LINKUSDT"]
        rows.append(
            dict(
                iter=iter_id,
                exists=True,
                link_oos_trades=int(len(l)),
                link_oos_net_pnl=round(float(l["net_pnl_pct"].sum()), 4),
                link_oos_wr=(
                    round(float((l["net_pnl_pct"] > 0).mean()), 4) if len(l) else 0.0
                ),
                link_oos_avg=round(float(l["net_pnl_pct"].mean()), 4) if len(l) else 0.0,
            )
        )
    traj = pd.DataFrame(rows)
    traj_path = OUT / "link_oos_trajectory_011_017.csv"
    traj.to_csv(traj_path, index=False)
    print(f"\n[4] LINK OOS trajectory across /011-/017 → {traj_path}")
    print(traj.to_string(index=False))


if __name__ == "__main__":
    main()
