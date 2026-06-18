"""FUNDING CARRY — tail / squeeze / cost realizability (the honest Sharpe discount).

A Sharpe ~4 is meaningless if it hides catastrophic short-squeeze drawdowns or evaporates under
realistic slippage. This characterizes the REALIZABLE risk of the point-in-time carry book:
  - max drawdown of the compounded net equity (IS / OOS / full), funding-only vs net.
  - per-period return distribution: skew, kurtosis, worst periods + their funding-vs-price split
    (squeeze losses show up as large NEGATIVE price_pnl on the short leg).
  - COST STRESS: net Sharpe at 1x / 2x / 4x the baseline per-side cost (alts slip more than majors).
Reuses funding_carry_pit (point-in-time + capacity). Baseline params M=9 / $5M / FRAC=0.25.
"""

from __future__ import annotations

import sys

import pandas as pd

sys.path.insert(0, "analysis")
import funding_carry_pit as FP  # noqa: E402, N812


def max_drawdown(net: pd.Series) -> float:
    eq = (1.0 + net).cumprod()
    return float((eq / eq.cummax() - 1.0).min())


def main() -> None:
    syms = sorted(p.split("/")[-1][:-4] for p in FP.glob.glob("data/funding_rates/*USDT.csv"))
    panel = FP.build_panel(syms)
    book = FP.carry_book_pit(panel)
    idx = pd.to_datetime(book.index, unit="ms")
    book = book.set_index(idx)
    is_, oos = book[book.index < FP.OOS_CUTOFF], book[book.index >= FP.OOS_CUTOFF]

    print("===== FUNDING CARRY — TAIL / SQUEEZE / COST REALIZABILITY =====")
    print("Max drawdown (compounded net equity):")
    for label, b in [("FULL", book), ("IS", is_), ("OOS", oos)]:
        print(f"  {label:4}: net maxDD = {max_drawdown(b['net'])*100:6.1f}%   "
              f"funding-only maxDD = {max_drawdown(b['fund_pnl'])*100:6.1f}%")

    print("\nPer-period (8h) net return distribution:")
    for label, b in [("IS", is_), ("OOS", oos)]:
        r = b["net"]
        print(f"  {label}: mean={r.mean()*100:+.3f}% std={r.std()*100:.3f}% "
              f"skew={r.skew():+.2f} kurt={r.kurt():+.1f} "
              f"worst={r.min()*100:+.1f}% p1={r.quantile(0.01)*100:+.2f}%")

    print("\nWorst 5 periods (net) — funding vs price decomposition (squeeze = big -price):")
    worst = book.nsmallest(5, "net")
    for t, row in worst.iterrows():
        print(f"  {t.date()}: net={row['net']*100:+.1f}%  (funding={row['fund_pnl']*100:+.2f}%  "
              f"price={row['price_pnl']*100:+.1f}%)  n_eligible={int(row['n_eligible'])}")

    print("\nCost stress (OOS net monthly Sharpe at higher per-side cost):")
    base_cost = FP.COST_SIDE
    for mult in (1, 2, 4):
        FP.COST_SIDE = base_cost * mult
        b = FP.carry_book_pit(panel)
        bidx = pd.to_datetime(b.index, unit="ms")
        sh, _, _ = FP.msharpe(b["net"], bidx, FP.OOS_CUTOFF, pd.Timestamp("2100-01-01"))
        fsh, _, _ = FP.msharpe(b["fund_pnl"], bidx, FP.OOS_CUTOFF, pd.Timestamp("2100-01-01"))
        print(f"  cost {mult}x ({base_cost*mult*100:.2f}%/side): net OOS Sharpe={sh:+.2f}  "
              f"(funding-only Sharpe={fsh:+.2f}, cost-independent)")
    FP.COST_SIDE = base_cost


if __name__ == "__main__":
    main()
