"""BTC /065 IS EDA — iter-v1/072 Phase 1.

USE ONLY IS DATA per user directive 2026-06-05 ("focus on IS, let's not cheat").

NO out_of_sample/* files are loaded anywhere in this script — verified by absence
of the substring "out_of_sample" below.

Goal: find the single load-bearing flaw in BTC /065's IS Sharpe = -0.18, then
propose 3-4 axes (feature-subset, ATR barrier, R-config, label-horizon) for the
LM Master to choose between at /072 EXPLORATION.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BTC_IS = ROOT / "reports-v1" / "iteration_v1-065" / "in_sample"
ETH_IS = ROOT / "reports-v1" / "iteration_v1-064" / "in_sample"
DOT_IS = ROOT / "reports-v1" / "iteration_v1-063" / "in_sample"

assert "out_of_sample" not in str(BTC_IS), "IS firewall violation"


def banner(s: str) -> None:
    print()
    print("=" * 80)
    print(s)
    print("=" * 80)


def load_trades() -> pd.DataFrame:
    df = pd.read_csv(BTC_IS / "trades.csv")
    df["open_time_dt"] = pd.to_datetime(df["open_time"], unit="ms", errors="coerce")
    df["close_time_dt"] = pd.to_datetime(df["close_time"], unit="ms", errors="coerce")
    df["month"] = df["open_time_dt"].dt.to_period("M")
    df["pnl"] = df["net_pnl_pct"].astype(float)
    df["win"] = (df["pnl"] > 0).astype(int)
    df["holding_candles"] = (
        (df["close_time"] - df["open_time"]) / (8 * 3600 * 1000)
    ).round().astype(int)
    return df


def per_month_loss_decomposition(trades: pd.DataFrame) -> None:
    banner("1) PER-MONTH IS LOSS DECOMPOSITION")
    monthly = pd.read_csv(BTC_IS / "monthly_pnl.csv")
    monthly = monthly.sort_values("pnl_pct").reset_index(drop=True)
    print("Worst 5 months by net PnL %:")
    print(monthly.head(5).to_string(index=False))
    print()
    print("Best 5 months by net PnL %:")
    print(monthly.tail(5).iloc[::-1].to_string(index=False))
    print()
    total_neg = monthly[monthly["pnl_pct"] < 0]["pnl_pct"].sum()
    total_pos = monthly[monthly["pnl_pct"] > 0]["pnl_pct"].sum()
    n_neg = (monthly["pnl_pct"] < 0).sum()
    n_pos = (monthly["pnl_pct"] > 0).sum()
    print(f"Negative months: {n_neg} (total {total_neg:.2f}%)")
    print(f"Positive months: {n_pos} (total {total_pos:.2f}%)")
    print(f"Net IS PnL: {monthly['pnl_pct'].sum():.2f}%  (Sharpe IS = -0.18)")
    print()
    # Top-5 worst months WR breakdown — needs trades.csv
    worst_months = monthly.head(5)["month"].tolist()
    print("Worst-5 months: trade-by-trade win-rate breakdown")
    for m in worst_months:
        sub = trades[trades["month"].astype(str) == m]
        if len(sub) == 0:
            continue
        wr = sub["win"].mean() * 100
        avg_pnl = sub["pnl"].mean()
        n_long = (sub["direction"] == 1).sum()
        n_short = (sub["direction"] == -1).sum()
        wr_long = sub[sub["direction"] == 1]["win"].mean() * 100 if n_long > 0 else float("nan")
        wr_short = sub[sub["direction"] == -1]["win"].mean() * 100 if n_short > 0 else float("nan")
        print(
            f"  {m}: n={len(sub):2d}  WR={wr:5.1f}%  avg_pnl={avg_pnl:6.2f}%  "
            f"long={n_long}(WR={wr_long:.0f}%)  short={n_short}(WR={wr_short:.0f}%)"
        )


def top_features_contribution(trades: pd.DataFrame) -> None:
    banner("2) TOP FEATURES — BTC vs ETH vs DOT specialists")
    btc_fi = pd.read_csv(BTC_IS / "feature_importance_Model_A_BTC_specialist_065.csv")
    eth_fi = pd.read_csv(ETH_IS / "feature_importance_Model_A_ETH_specialist_064.csv")
    dot_fi = pd.read_csv(DOT_IS / "feature_importance_Model_E_DOT_specialist_063.csv")

    print("BTC top-15:")
    print(btc_fi.head(15).to_string(index=False))
    print()

    # Bottom 14 = features ranked >= len-14 (low importance, drop candidates)
    n = len(btc_fi)
    bottom = btc_fi.tail(14)
    print(f"BTC BOTTOM-14 (ranks {n-13}-{n}, low gain — drop candidates):")
    print(bottom.to_string(index=False))
    print()

    # Compare top 10 of each
    btc_top10 = set(btc_fi.head(10)["feature_name"])
    eth_top10 = set(eth_fi.head(10)["feature_name"])
    dot_top10 = set(dot_fi.head(10)["feature_name"])

    print("Top-10 feature overlap:")
    print(f"  BTC ∩ ETH: {sorted(btc_top10 & eth_top10)}")
    print(f"  BTC ∩ DOT: {sorted(btc_top10 & dot_top10)}")
    print(f"  BTC unique vs ETH+DOT: {sorted(btc_top10 - eth_top10 - dot_top10)}")
    print(f"  ETH unique vs BTC: {sorted(eth_top10 - btc_top10)}")
    print(f"  DOT unique vs BTC: {sorted(dot_top10 - btc_top10)}")
    print()

    # Is BTC borrowing ETH/DOT features?
    eth_unique_in_btc_top10 = btc_top10 & (eth_top10 - dot_top10)
    print(f"  Features in ETH top10 but NOT DOT, present in BTC top10:")
    print(f"    {sorted(eth_unique_in_btc_top10) if eth_unique_in_btc_top10 else 'NONE'}")
    print()
    # Symmetric BTC top relying on ETH-features (eth_vs_btc_ratio etc.)
    eth_native = {f for f in btc_top10 if "eth" in f.lower()}
    btc_native_in_eth = {f for f in eth_top10 if "btc" in f.lower()}
    print(f"  BTC top10 features containing 'eth' (cross-asset borrowing): {eth_native}")
    print(f"  ETH top10 features containing 'btc': {btc_native_in_eth}")
    print()
    print("BTC rank of features that work for ETH/DOT (cross-check on which BTC under-uses):")
    for f in (eth_top10 | dot_top10) - btc_top10:
        row = btc_fi[btc_fi["feature_name"] == f]
        if len(row):
            r = int(row["importance_rank"].iloc[0])
            g = float(row["mean_gain"].iloc[0])
            print(f"  {f}: BTC rank={r:2d}  gain={g:.1f}")


def regime_breakdown() -> None:
    banner("3) REGIME BREAKDOWN")
    pr = pd.read_csv(BTC_IS / "per_regime.csv")
    print(pr.to_string(index=False))
    print()
    if len(pr) <= 1 or (pr["regime"].iloc[0] == "unknown" and len(pr) == 1):
        print("NOTE: per_regime.csv is DEGENERATE — single 'unknown' row at /065.")
        print("Regime tagging not active for /065 specialist run.")
        print("Falling back to manual regime decomposition by year + BTC-price cycle.")


def manual_regime_via_year(trades: pd.DataFrame) -> None:
    banner("3b) MANUAL REGIME PROXY — per-year stats (BTC cycle proxy)")
    trades = trades.copy()
    trades["year"] = trades["open_time_dt"].dt.year
    yr = trades.groupby("year").agg(
        n=("pnl", "size"),
        wr=("win", "mean"),
        avg_pnl=("pnl", "mean"),
        net_pnl=("pnl", "sum"),
        sharpe=("pnl", lambda s: s.mean() / (s.std() + 1e-9)),
    )
    yr["wr"] = (yr["wr"] * 100).round(1)
    yr["avg_pnl"] = yr["avg_pnl"].round(2)
    yr["net_pnl"] = yr["net_pnl"].round(2)
    yr["sharpe"] = yr["sharpe"].round(3)
    print(yr.to_string())
    print()

    # Direction breakdown by year
    print("Per-year direction breakdown:")
    for y, sub in trades.groupby("year"):
        long_pnl = sub[sub["direction"] == 1]["pnl"].sum()
        short_pnl = sub[sub["direction"] == -1]["pnl"].sum()
        n_long = (sub["direction"] == 1).sum()
        n_short = (sub["direction"] == -1).sum()
        wr_long = sub[sub["direction"] == 1]["win"].mean() * 100 if n_long > 0 else float("nan")
        wr_short = sub[sub["direction"] == -1]["win"].mean() * 100 if n_short > 0 else float("nan")
        print(
            f"  {y}: long n={n_long}(WR={wr_long:.1f}%, PnL={long_pnl:+.2f}%)  "
            f"short n={n_short}(WR={wr_short:.1f}%, PnL={short_pnl:+.2f}%)"
        )


def trade_pattern_flaws(trades: pd.DataFrame) -> None:
    banner("4) TRADE-PATTERN FLAWS")

    wins = trades[trades["pnl"] > 0]["pnl"]
    losses = trades[trades["pnl"] < 0]["pnl"]
    print(f"Total trades: {len(trades)}")
    print(f"Wins: {len(wins)} (avg = {wins.mean():.3f}%)  Losses: {len(losses)} (avg = {losses.mean():.3f}%)")
    print(f"Win rate: {len(wins) / len(trades) * 100:.2f}%")
    pf = wins.sum() / (-losses.sum()) if losses.sum() != 0 else float("inf")
    print(f"Profit factor (win-PnL / |loss-PnL|): {pf:.3f}")
    print(f"Win/Loss ratio: {wins.mean() / -losses.mean():.3f}")
    print()

    # Direction breakdown
    long = trades[trades["direction"] == 1]
    short = trades[trades["direction"] == -1]
    print(f"Long: n={len(long)}  WR={long['win'].mean() * 100:.1f}%  avg_pnl={long['pnl'].mean():+.3f}%  net={long['pnl'].sum():+.2f}%")
    print(f"Short: n={len(short)}  WR={short['win'].mean() * 100:.1f}%  avg_pnl={short['pnl'].mean():+.3f}%  net={short['pnl'].sum():+.2f}%")
    print()

    # Exit reason distribution
    er = trades.groupby("exit_reason").agg(
        n=("pnl", "size"),
        wr=("win", "mean"),
        avg_pnl=("pnl", "mean"),
        net=("pnl", "sum"),
    )
    er["wr"] = (er["wr"] * 100).round(1)
    er["avg_pnl"] = er["avg_pnl"].round(3)
    er["net"] = er["net"].round(2)
    er = er.sort_values("n", ascending=False)
    print("Exit-reason distribution:")
    print(er.to_string())
    print()

    # By direction × exit reason
    print("Direction × exit-reason joint:")
    cross = trades.groupby(["direction", "exit_reason"]).agg(
        n=("pnl", "size"),
        avg_pnl=("pnl", "mean"),
        net=("pnl", "sum"),
    )
    cross["avg_pnl"] = cross["avg_pnl"].round(3)
    cross["net"] = cross["net"].round(2)
    print(cross.to_string())
    print()

    # Holding-time stats
    print(f"Holding period (8h candles): mean={trades['holding_candles'].mean():.1f}, median={trades['holding_candles'].median():.1f}, max={trades['holding_candles'].max()}")
    print()

    # Top-5 worst single trades
    print("5 worst single trades:")
    worst = trades.nsmallest(5, "pnl")[["open_time_dt", "direction", "exit_reason", "pnl", "confidence"]]
    print(worst.to_string(index=False))
    print()
    print("5 best single trades:")
    best = trades.nlargest(5, "pnl")[["open_time_dt", "direction", "exit_reason", "pnl", "confidence"]]
    print(best.to_string(index=False))
    print()

    # Concentration: top trade as % of net positive
    sorted_pnl = trades["pnl"].sort_values(ascending=False)
    top1_share = sorted_pnl.iloc[0] / trades["pnl"].sum() if trades["pnl"].sum() != 0 else float("nan")
    top5_share = sorted_pnl.head(5).sum() / trades["pnl"].sum() if trades["pnl"].sum() != 0 else float("nan")
    print(f"Concentration: top-1 trade = {top1_share * 100:.1f}% of net IS PnL")
    print(f"               top-5 trades = {top5_share * 100:.1f}% of net IS PnL")


def confidence_sl_proximity_diagnostic(trades: pd.DataFrame) -> None:
    banner("5) ATR-BARRIER / CONFIDENCE DIAGNOSTIC")
    # Confidence distribution
    print(f"Confidence: mean={trades['confidence'].mean():.3f}  median={trades['confidence'].median():.3f}")
    print(f"Confidence quartiles:")
    print(trades["confidence"].describe()[["min", "25%", "50%", "75%", "max"]].to_string())
    print()
    # Confidence vs outcome
    trades = trades.copy()
    trades["conf_bin"] = pd.cut(
        trades["confidence"],
        bins=[-0.01, 0.05, 0.10, 0.15, 0.20, 0.30, 1.0],
        labels=["<0.05", "0.05-0.10", "0.10-0.15", "0.15-0.20", "0.20-0.30", "0.30+"],
    )
    cb = trades.groupby("conf_bin", observed=True).agg(
        n=("pnl", "size"),
        wr=("win", "mean"),
        avg_pnl=("pnl", "mean"),
        net=("pnl", "sum"),
    )
    cb["wr"] = (cb["wr"] * 100).round(1)
    cb["avg_pnl"] = cb["avg_pnl"].round(3)
    cb["net"] = cb["net"].round(2)
    print("Confidence-bin × outcome:")
    print(cb.to_string())
    print()
    # SL-hit vs TP-hit: ATR-barrier symmetry check
    sl_count = (trades["exit_reason"] == "stop_loss").sum()
    tp_count = (trades["exit_reason"] == "take_profit").sum()
    timeout_count = (trades["exit_reason"] == "timeout").sum()
    print(f"Barrier hit rate:  SL={sl_count} ({sl_count/len(trades)*100:.1f}%)  TP={tp_count} ({tp_count/len(trades)*100:.1f}%)  timeout={timeout_count} ({timeout_count/len(trades)*100:.1f}%)")
    print()
    # Average PnL conditional on exit
    if sl_count > 0:
        avg_sl = trades[trades["exit_reason"] == "stop_loss"]["pnl"].mean()
        print(f"  Avg SL pnl: {avg_sl:+.3f}%  (atr_sl=1.45 calibrated)")
    if tp_count > 0:
        avg_tp = trades[trades["exit_reason"] == "take_profit"]["pnl"].mean()
        print(f"  Avg TP pnl: {avg_tp:+.3f}%  (atr_tp=2.9 calibrated)")
    if timeout_count > 0:
        avg_to = trades[trades["exit_reason"] == "timeout"]["pnl"].mean()
        wr_to = trades[trades["exit_reason"] == "timeout"]["win"].mean() * 100
        print(f"  Avg timeout pnl: {avg_to:+.3f}%  WR={wr_to:.1f}%   (timeout proxy: TP too far OR TP arrived but unconfirmed)")


def consecutive_loss_streak_audit(trades: pd.DataFrame) -> None:
    banner("6) CONSECUTIVE-LOSS STREAK AUDIT (R1 candidate)")
    trades = trades.sort_values("open_time_dt").reset_index(drop=True)
    streak_loss = 0
    max_streak = 0
    streak_history = []
    for _, t in trades.iterrows():
        if t["pnl"] < 0:
            streak_loss += 1
            max_streak = max(max_streak, streak_loss)
        else:
            if streak_loss > 0:
                streak_history.append(streak_loss)
            streak_loss = 0
    if streak_loss > 0:
        streak_history.append(streak_loss)
    print(f"Max consecutive-loss streak: {max_streak}")
    print(f"All loss streaks (sorted desc): {sorted(streak_history, reverse=True)[:15]}")
    # Conditional: trade after k consecutive losses
    streak = 0
    rows = []
    for i, t in trades.iterrows():
        rows.append((i, streak, t["pnl"], t["win"]))
        if t["pnl"] < 0:
            streak += 1
        else:
            streak = 0
    pre_streak = pd.DataFrame(rows, columns=["idx", "prior_loss_streak", "pnl", "win"])
    print()
    print("Outcome conditional on prior consecutive-loss streak (R1 design input):")
    for k in [0, 1, 2, 3, 4, 5]:
        sub = pre_streak[pre_streak["prior_loss_streak"] == k]
        if len(sub) > 0:
            print(
                f"  Prior streak={k}: n={len(sub):3d}  WR={sub['win'].mean()*100:5.1f}%  "
                f"avg_pnl={sub['pnl'].mean():+6.3f}%  net={sub['pnl'].sum():+6.2f}%"
            )
    sub_3plus = pre_streak[pre_streak["prior_loss_streak"] >= 3]
    if len(sub_3plus) > 0:
        print(
            f"  Prior streak >=3: n={len(sub_3plus)}  WR={sub_3plus['win'].mean()*100:.1f}%  "
            f"net={sub_3plus['pnl'].sum():+.2f}%  -- R1=ON would skip these"
        )


def main() -> None:
    print(f"Loading BTC /065 IS artifacts from: {BTC_IS}")
    assert BTC_IS.exists(), f"Missing: {BTC_IS}"
    trades = load_trades()
    print(f"Loaded {len(trades)} BTC trades from {trades['open_time_dt'].min()} to {trades['close_time_dt'].max()}")

    per_month_loss_decomposition(trades)
    top_features_contribution(trades)
    regime_breakdown()
    manual_regime_via_year(trades)
    trade_pattern_flaws(trades)
    confidence_sl_proximity_diagnostic(trades)
    consecutive_loss_streak_audit(trades)

    banner("DONE")


if __name__ == "__main__":
    main()
