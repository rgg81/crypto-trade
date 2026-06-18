"""FUNDING CARRY — parameter sensitivity (is the edge robust, or knob-tuned?).

Anti-hype check: re-run the point-in-time funding carry across a GRID of reasonable choices for the
three knobs (trailing-funding window, liquidity floor, book fraction). If the funding-income edge is
structural it should hold across the whole grid; if it lives in one cell, it was knob-tuned. Reuses
funding_carry_pit (same point-in-time + capacity machinery), varying only the globals.
"""

from __future__ import annotations

import sys

import pandas as pd

sys.path.insert(0, "analysis")
import funding_carry_pit as FP  # noqa: E402, N812

M_GRID = [3, 6, 9, 21]              # trailing funding window (1d / 2d / 3d / 7d)
LIQ_GRID = [1e6, 5e6, 20e6]        # capacity floor ($ trailing 8h quote-vol)
FRAC_GRID = [0.15, 0.25, 0.40]     # short-top / long-bottom fraction of eligible set


def oos_metrics(book: pd.DataFrame):
    idx = pd.to_datetime(book.index, unit="ms")
    hi1 = pd.Timestamp("2100-01-01")
    fund_sh, _, _ = FP.msharpe(book["fund_pnl"], idx, FP.OOS_CUTOFF, hi1)
    net_sh, _, _ = FP.msharpe(book["net"], idx, FP.OOS_CUTOFF, hi1)
    seg = book.loc[idx >= FP.OOS_CUTOFF, "fund_pnl"]
    fund_yr = seg.mean() * 365.25 * 3 * 100
    return fund_sh, net_sh, fund_yr


def main() -> None:
    syms = FP.glob.glob("data/funding_rates/*USDT.csv")
    syms = sorted(p.split("/")[-1][:-4] for p in syms)
    print("OOS funding-only Sharpe / net Sharpe / funding %/yr, across the parameter grid:")
    print(f"{'M':>4} {'LIQ_FLOOR':>10} {'FRAC':>5} | {'fundSh':>7} {'netSh':>7} {'f%/yr':>7}")
    print("-" * 60)
    results = []
    for m in M_GRID:
        FP.M_TRAIL = m
        panel = FP.build_panel(syms)
        for liq in LIQ_GRID:
            FP.LIQ_FLOOR = liq
            for frac in FRAC_GRID:
                FP.FRAC = frac
                book = FP.carry_book_pit(panel)
                if book.empty:
                    continue
                fs, ns, fy = oos_metrics(book)
                results.append((m, liq, frac, fs, ns, fy))
                print(f"{m:>8} {liq:>10.0e} {frac:>5.2f} | {fs:>+7.2f} {ns:>+7.2f} {fy:>+8.1f}%")
    r = pd.DataFrame(results, columns=["m", "liq", "frac", "fund_sh", "net_sh", "fund_yr"])
    print("-" * 60)
    def stat(col):
        return f"min {col.min():+.2f}, med {col.median():+.2f}, max {col.max():+.2f}"
    print(f"cells: {len(r)} | fundSh>0: {int((r.fund_sh>0).sum())}/{len(r)} ({stat(r.fund_sh)})")
    print(f"net-Sharpe>0: {int((r.net_sh>0).sum())}/{len(r)} ({stat(r.net_sh)})")
    verdict = (r.fund_sh > 1.0).all()
    v = "ROBUST (funding edge holds in ALL cells)" if verdict else "fragile in some cells"
    print(f"VERDICT: {v}")


if __name__ == "__main__":
    main()
