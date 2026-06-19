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


def walkforward_book(coins: dict) -> tuple[pd.Series, dict[str, pd.DataFrame]]:
    """THE BASELINE as a reusable function (EXPLORATION-002 hook).

    Per calendar month, pick the (M_FUND, FRAC, min_history) combo with the best PAST-window monthly
    Sharpe (train = trailing TRAIN_MONTHS, gap = GAP_CANDLES), then apply that combo to the test
    month. Coin selection is already point-in-time, so NOTHING uses future info (true OOS).

    Returns:
      wf_net : the stitched per-candle net (== carry_walkforward.main's "walk-forward" baseline).
      parts  : {"price","funding","cost","weights"} stitched the SAME way -> each test month's rows
               come from the combo chosen for that month. `weights` is the per-coin weight matrix
               (index = candle open_time, columns = coins) needed by weight-level risk overlays
               (per-coin caps, beta-hedge). Rows outside any selected test month are absent.

    Efficient: each combo's full (book, weights) is built once; the walk-forward just slices the
    chosen combo's precomputed rows per month.
    """
    combos = list(product(M_GRID, FRAC_GRID, HIST_GRID))
    books: dict[tuple, pd.DataFrame] = {}
    wmats: dict[tuple, pd.DataFrame] = {}
    for combo in combos:
        m, f, h = combo
        bk, wm = bc.build_book(coins, m_fund=m, frac=f, min_history=h)
        books[combo] = bk
        wmats[combo] = wm
    panel = pd.DataFrame({c: books[c]["net"] for c in combos}).sort_index()

    months = pd.PeriodIndex(panel.index, freq="M").unique().sort_values()
    step = 8 * 60 * 60 * 1000
    net_parts, price_parts, fund_parts, cost_parts, w_parts = [], [], [], [], []
    for ms in months:
        m_start = ms.to_timestamp()
        train_lo = m_start - pd.DateOffset(months=TRAIN_MONTHS)
        train_hi = m_start - pd.Timedelta(milliseconds=GAP_CANDLES * step)
        test_hi = (ms + 1).to_timestamp()
        train = panel[(panel.index >= train_lo) & (panel.index < train_hi)]
        test_mask = (panel.index >= m_start) & (panel.index < test_hi)
        if len(train) < 200 or not test_mask.any():
            continue
        train_sh = train.apply(msharpe)
        if not np.isfinite(train_sh.max()):
            continue
        best = train_sh.idxmax()
        bk = books[best]
        idx = bk.index[(bk.index >= m_start) & (bk.index < test_hi)]
        net_parts.append(bk["net"].loc[idx])
        price_parts.append(bk["price"].loc[idx])
        fund_parts.append(bk["funding"].loc[idx])
        cost_parts.append(bk["cost"].loc[idx])
        w_parts.append(wmats[best].loc[idx])
    wf_net = pd.concat(net_parts).sort_index().rename("net")
    parts = {
        "price": pd.concat(price_parts).sort_index().rename("price"),
        "funding": pd.concat(fund_parts).sort_index().rename("funding"),
        "cost": pd.concat(cost_parts).sort_index().rename("cost"),
        "weights": pd.concat(w_parts).sort_index(),
    }
    return wf_net, parts


def walkforward_net(coins: dict) -> pd.Series:
    """Convenience: just the baseline net series (walkforward_book has the full decomposition)."""
    return walkforward_book(coins)[0]


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
