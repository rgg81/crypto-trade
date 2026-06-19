"""CARRY ITERATION — EXPLORATION-001: per-month WALK-FORWARD parameter selection (kill the bias).

The canonical broad_carry uses GLOBAL params (M_FUND=9, FRAC=0.25, min_history=2190) chosen by
looking at the whole sample -> a hindsight bias. This makes parameter-finding part of the
WALK-FORWARD: each calendar month, the (M_FUND, FRAC, min_history) combo is selected on the PAST
training window ONLY (best past monthly Sharpe), then applied to the test month. Coin selection is
already point-in-time (per-candle funding rank + point-in-time min-history), so NOTHING is chosen
with future information — the OOS here is a TRUE walk-forward out-of-sample.

Efficient design: precompute each combo's full realized net series once (build_book), then the
walk-forward is just per-month combo-selection on past nets. Reports the walk-forward net IS/OOS +
per-year + DD vs the fixed-global-param baseline, plus the per-month chosen-combo log.
"""

from __future__ import annotations

import sys
from itertools import product

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
import broad_carry as bc  # noqa: E402
import pair_engine as pe  # noqa: E402

LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")
TRAIN_MONTHS = 24
GAP_CANDLES = 3                       # tiny embargo (carry hold is 1 candle)
M_GRID = [3, 9, 21]
FRAC_GRID = [0.15, 0.25, 0.40]
HIST_GRID = [1095, 2190]              # ~1y / ~2y point-in-time listing-age


def msharpe(net: pd.Series) -> float:
    g = net.groupby(net.index.to_period("M")).sum()
    return g.mean() / g.std() * np.sqrt(12) if len(g) > 1 and g.std() > 0 else float("nan")


def report(label: str, net: pd.Series) -> None:
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    oe = (1 + net[net.index >= pe.OOS_CUTOFF]).cumprod()
    odd = float((oe / oe.cummax() - 1).min())
    yr = {int(k): round(v * 100, 0) for k, v in net.groupby(net.index.year).sum().items()}
    print(f"  {label:34} IS={msharpe(net[net.index < pe.OOS_CUTOFF]):+.2f} "
          f"OOS={msharpe(net[net.index >= pe.OOS_CUTOFF]):+.2f} fullDD={dd*100:4.0f}% "
          f"oosDD={odd*100:4.0f}%")
    print(f"      net%/yr={yr}")


def main() -> None:
    coins = bc.load_universe()
    combos = list(product(M_GRID, FRAC_GRID, HIST_GRID))
    print(f"EXPLORATION-001: walk-forward param selection over {len(combos)} combos "
          f"(M x FRAC x min_history), {len(coins)} coins. Precomputing combo nets...")
    nets = {}
    for (m, f, h) in combos:
        nets[(m, f, h)] = bc.build_book(coins, m_fund=m, frac=f, min_history=h)[0]["net"]
    panel = pd.DataFrame(nets).sort_index()

    months = pd.PeriodIndex(panel.index, freq="M").unique().sort_values()
    step = 8 * 60 * 60 * 1000
    wf_parts = []
    sel_log = []
    for ms in months:
        m_start = ms.to_timestamp()
        train_lo = m_start - pd.DateOffset(months=TRAIN_MONTHS)
        train_hi = m_start - pd.Timedelta(milliseconds=GAP_CANDLES * step)
        test_hi = (ms + 1).to_timestamp()
        train = panel[(panel.index >= train_lo) & (panel.index < train_hi)]
        test = panel[(panel.index >= m_start) & (panel.index < test_hi)]
        if len(train) < 200 or test.empty:
            continue
        train_sh = train.apply(msharpe)
        if not np.isfinite(train_sh.max()):
            continue
        best = train_sh.idxmax()
        wf_parts.append(test[best].rename("net"))
        sel_log.append((m_start.year, best))
    wf = pd.concat(wf_parts).sort_index()

    print("\n=== WALK-FORWARD param-selected carry (NO global param bias) ===")
    report("walk-forward param-selected", wf)
    print("\n=== reference: FIXED global params (2y / M=9 / FRAC=0.25) — has the bias ===")
    fixed = bc.build_book(coins, m_fund=9, frac=0.25, min_history=2190)[0]["net"]
    report("fixed global (2y,M9,F.25)", fixed)
    # which combos the walk-forward picked (are they stable, or thrashing?)
    from collections import Counter
    picks = Counter(b for _, b in sel_log)
    print("\nmost-picked combos (M,FRAC,hist):", picks.most_common(5))


if __name__ == "__main__":
    main()
