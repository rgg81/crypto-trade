"""carry-iteration — WALK-FORWARD param selection for cash-and-carry (no-bias confirmation).

EXPLORATION-006 used a hand-picked funding window (M=9). The no-bias mandate says params must be
selected per-month on PAST data. This picks the funding window M each calendar month on the trailing
window (best past monthly Sharpe), applies it to the test month, and stitches — a true walk-forward.

Reports walk-forward net IS/OOS at MAKER cost, no-floor vs $5M spot floor (capacity-respecting), vs
the fixed-M=9 reference.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
import cash_carry as cc  # noqa: E402
import pair_engine as pe  # noqa: E402

LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")
TRAIN_MONTHS = 24
GAP_CANDLES = 3
M_GRID = [1, 3, 9, 21]


def msharpe(net: pd.Series) -> float:
    g = net.groupby(net.index.to_period("M")).sum()
    return g.mean() / g.std() * np.sqrt(12) if len(g) > 1 and g.std() > 0 else float("nan")


def walkforward(coins: dict, cost_side: float, min_spot_liq):
    nets = {}
    for m in M_GRID:
        net, _, _, _ = cc.build_basis_book(coins, m_fund=m, thresh=0.0,
                                           cost_side=cost_side, min_spot_liq=min_spot_liq)
        nets[m] = net
    panel = pd.DataFrame(nets).sort_index()
    months = pd.PeriodIndex(panel.index, freq="M").unique().sort_values()
    step = 8 * 60 * 60 * 1000
    parts = []
    picks = []
    for ms in months:
        m_start = ms.to_timestamp()
        train_lo = m_start - pd.DateOffset(months=TRAIN_MONTHS)
        train_hi = m_start - pd.Timedelta(milliseconds=GAP_CANDLES * step)
        test_hi = (ms + 1).to_timestamp()
        train = panel[(panel.index >= train_lo) & (panel.index < train_hi)]
        test = panel[(panel.index >= m_start) & (panel.index < test_hi)]
        if len(train) < 200 or test.empty:
            continue
        tsh = train.apply(msharpe)
        if not np.isfinite(tsh.max()):
            continue
        best = tsh.idxmax()
        picks.append((m_start.year, best))
        parts.append(test[best].rename("net"))
    return pd.concat(parts).sort_index(), picks


def rep(label: str, net: pd.Series) -> None:
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    yr = {int(k): round(v * 100, 0) for k, v in net.groupby(net.index.year).sum().items()}
    print(f"  {label:30} IS={msharpe(net[net.index < pe.OOS_CUTOFF]):+.2f} "
          f"OOS={msharpe(net[net.index >= pe.OOS_CUTOFF]):+.2f} maxDD={dd*100:4.0f}%")
    print(f"     net%/yr={yr}")


def main() -> None:
    from collections import Counter
    coins = cc.load_basis_universe()
    print(f"CASH-AND-CARRY walk-forward M-selection (no-bias) — {len(coins)} coins, MAKER cost")
    for label, floor in [("no floor", None), ("$5M spot floor", 5e6), ("$20M spot floor", 2e7)]:
        net, picks = walkforward(coins, cc.MAKER, floor)
        rep(f"walk-forward, {label}", net)
        oos_picks = Counter(m for y, m in picks if y >= 2025)
        print(f"     OOS M-picks: {dict(sorted(oos_picks.items()))}")
    print("\n  reference (fixed hand-picked M=9, MAKER):")
    n_nf, _, _, _ = cc.build_basis_book(coins, m_fund=9, thresh=0.0, cost_side=cc.MAKER)
    n_5, _, _, _ = cc.build_basis_book(coins, m_fund=9, thresh=0.0,
                                       cost_side=cc.MAKER, min_spot_liq=5e6)
    rep("fixed M=9, no floor", n_nf)
    rep("fixed M=9, $5M floor", n_5)


if __name__ == "__main__":
    main()
