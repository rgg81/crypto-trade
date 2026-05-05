"""
Phase 7 Diagnostics — iter-v3/001 OOS Evaluation

Three questions the diary needs answered with NUMBERS:
1. IS-negative / OOS-positive inversion (IS Sharpe -0.07 → OOS +1.10):
   regime luck or flipped per-symbol pattern? Per-symbol IS/OOS PnL deltas.
2. MKR's 53% OOS concentration: dominated by 1-2 trades, or broad signal?
   Per-trade attribution of MKR's OOS PnL.
3. The 5.9 trades/month rate: which symbols/months are sparse?
   Per-month per-symbol trade-count grid.

Outputs: console tables plus CSVs in analysis/iteration_v3-001/.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "reports-v3" / "iteration_v3-001"
OUT_DIR = Path(__file__).resolve().parent

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC


def load_trades() -> tuple[pd.DataFrame, pd.DataFrame]:
    is_df = pd.read_csv(REPORT_DIR / "in_sample" / "trades.csv")
    oos_df = pd.read_csv(REPORT_DIR / "out_of_sample" / "trades.csv")
    for d in (is_df, oos_df):
        d["close_dt"] = pd.to_datetime(d["close_time"], unit="ms")
        d["month"] = d["close_dt"].dt.to_period("M").astype(str)
    return is_df, oos_df


def q1_is_oos_inversion(is_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    """Per-symbol IS vs OOS comparison for sign-flip diagnosis."""
    rows = []
    for sym in sorted(set(is_df.symbol) | set(oos_df.symbol)):
        is_sym = is_df[is_df.symbol == sym]
        oos_sym = oos_df[oos_df.symbol == sym]
        rows.append(
            {
                "symbol": sym,
                "is_n": len(is_sym),
                "is_wpnl": is_sym["weighted_pnl"].sum(),
                "is_winrate": (is_sym["pnl_pct"] > 0).mean() * 100 if len(is_sym) else 0,
                "is_avg_net": is_sym["net_pnl_pct"].mean() if len(is_sym) else 0,
                "oos_n": len(oos_sym),
                "oos_wpnl": oos_sym["weighted_pnl"].sum(),
                "oos_winrate": (oos_sym["pnl_pct"] > 0).mean() * 100 if len(oos_sym) else 0,
                "oos_avg_net": oos_sym["net_pnl_pct"].mean() if len(oos_sym) else 0,
                "wpnl_sign_flip": (
                    (is_sym["weighted_pnl"].sum() < 0)
                    != (oos_sym["weighted_pnl"].sum() < 0)
                ),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "q1_is_oos_per_symbol.csv", index=False, float_format="%.4f")
    return df


def q2_mkr_attribution(oos_df: pd.DataFrame) -> pd.DataFrame:
    """Per-trade attribution of MKR OOS contribution. Detect 1-2 dominant trades."""
    mkr = oos_df[oos_df.symbol == "MKRUSDT"].copy().reset_index(drop=True)
    mkr = mkr.sort_values("weighted_pnl", ascending=False).reset_index(drop=True)
    total = mkr["weighted_pnl"].sum()
    mkr["pct_of_mkr_oos"] = (mkr["weighted_pnl"] / total * 100) if total else 0
    mkr["cum_pct"] = mkr["pct_of_mkr_oos"].cumsum()
    mkr_out = mkr[
        ["close_dt", "direction", "entry_price", "exit_price", "exit_reason",
         "weight_factor", "net_pnl_pct", "weighted_pnl", "pct_of_mkr_oos", "cum_pct"]
    ]
    mkr_out.to_csv(OUT_DIR / "q2_mkr_oos_attribution.csv", index=False, float_format="%.4f")
    return mkr_out


def q3_trade_rate(oos_df: pd.DataFrame) -> pd.DataFrame:
    """Per-month per-symbol trade-count grid. Identify sparse months."""
    grid = oos_df.groupby(["month", "symbol"]).size().unstack(fill_value=0)
    grid["TOTAL"] = grid.sum(axis=1)
    grid.loc["TOTAL"] = grid.sum(axis=0)
    grid.to_csv(OUT_DIR / "q3_oos_monthly_trade_grid.csv", float_format="%.0f")
    return grid


def q3b_exit_reason_mix(oos_df: pd.DataFrame) -> pd.DataFrame:
    """Exit reason breakdown — diagnose if SL/TP/timeout mix is structural mismatch."""
    mix = (
        oos_df.groupby(["symbol", "exit_reason"])
        .agg(n=("pnl_pct", "size"), avg_pnl=("net_pnl_pct", "mean"),
             total_wpnl=("weighted_pnl", "sum"))
        .reset_index()
    )
    mix.to_csv(OUT_DIR / "q3b_oos_exit_reason_mix.csv", index=False, float_format="%.4f")
    return mix


def q4_regime_breakdown(is_df: pd.DataFrame) -> pd.DataFrame:
    """Year-by-year IS PnL per symbol — detect 'all damage in one year' pattern."""
    is_df = is_df.copy()
    is_df["year"] = is_df["close_dt"].dt.year
    g = is_df.groupby(["year", "symbol"])["weighted_pnl"].sum().unstack(fill_value=0)
    g["TOTAL"] = g.sum(axis=1)
    g.loc["TOTAL"] = g.sum(axis=0)
    g.to_csv(OUT_DIR / "q4_is_yearly_per_symbol.csv", float_format="%.4f")
    return g


def main() -> None:
    is_df, oos_df = load_trades()
    print(f"Loaded {len(is_df)} IS trades, {len(oos_df)} OOS trades.\n")

    print("=" * 72)
    print("Q1: IS vs OOS per-symbol — sign-flip diagnosis")
    print("=" * 72)
    q1 = q1_is_oos_inversion(is_df, oos_df)
    print(q1.to_string(index=False))
    print()

    print("=" * 72)
    print("Q2: MKR OOS attribution — top contributors (sorted by wpnl desc)")
    print("=" * 72)
    q2 = q2_mkr_attribution(oos_df)
    print(q2.head(10).to_string(index=False))
    print(f"\nMKR OOS trades: {len(q2)}")
    print(f"Top 1 contributes {q2.iloc[0]['pct_of_mkr_oos']:.1f}% of MKR OOS wpnl")
    print(f"Top 3 contribute {q2.head(3)['pct_of_mkr_oos'].sum():.1f}% of MKR OOS wpnl")
    print(f"Top 5 contribute {q2.head(5)['pct_of_mkr_oos'].sum():.1f}% of MKR OOS wpnl")
    print()

    print("=" * 72)
    print("Q3a: OOS monthly × symbol trade grid")
    print("=" * 72)
    q3 = q3_trade_rate(oos_df)
    print(q3.to_string())
    print()

    print("=" * 72)
    print("Q3b: OOS exit reason mix per symbol")
    print("=" * 72)
    q3b = q3b_exit_reason_mix(oos_df)
    print(q3b.to_string(index=False))
    print()

    print("=" * 72)
    print("Q4: IS yearly per-symbol (for regime context)")
    print("=" * 72)
    q4 = q4_regime_breakdown(is_df)
    print(q4.to_string())
    print()


if __name__ == "__main__":
    main()
