"""HEAD-TO-HEAD: broad cross-sectional carry vs selected carry-pairs — SAME realistic engine.

Question (user option 2): does the BROAD cross-sectional carry (short top-funding / long
bottom-funding across ALL coins, no pair-selection) generalize BETTER than IS-SELECTED carry pairs?
Selection adds overfit (pair_carry_portfolio: IS +2.69 -> OOS +0.63 shrinkage), so the broad book —
which selects nothing — should hold up better. We test both on the IDENTICAL realistic execution
model (next-bar-open fills, real 8h funding, 0.07%/leg cost) for a fair comparison.

  BROAD  : every rebalance, rank the eligible universe by trailing funding; short top-FRAC /
           long bottom-FRAC, equal-weight, dollar-neutral. NO selection of specific pairs/coins.
  PAIRS  : the 10 disjoint IS-selected carry pairs, IS-only inverse-vol weights (from
           pair_carry_portfolio) — the selection-based book.
"""

from __future__ import annotations

import glob
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
import pair_engine as pe  # noqa: E402

M_FUND = 9
FRAC = 0.25
LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")
MIN_OVERLAP = 2500


def stats(net: pd.Series) -> str:
    is_sh = pe.monthly_sharpe(net, LO0, pe.OOS_CUTOFF)
    oos_sh = pe.monthly_sharpe(net, pe.OOS_CUTOFF, HI1)
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    yr = {int(k): round(v * 100, 0) for k, v in net.groupby(net.index.year).sum().items()}
    return f"IS={is_sh:+.2f}  OOS={oos_sh:+.2f}  maxDD={dd * 100:.0f}%  net%/yr={yr}"


def broad_carry(coins: dict) -> pd.Series:
    """Realistic cross-sectional carry: decide close[t] -> fill open[t+1] -> hold candle t+1."""
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).sort_index()
    funds = pd.DataFrame({s: d["funding_rate"] for s, d in coins.items()}).reindex(opens.index)
    ftrail = funds.rolling(M_FUND).mean()                 # signal <= t
    ret = opens.shift(-2) / opens.shift(-1) - 1.0         # hold candle t+1: open[t+2]/open[t+1]-1
    fund_earn = funds.shift(-1)                            # funding settled over candle t+1
    elig = ftrail.notna() & ret.notna() & fund_earn.notna()
    ft_np = ftrail.to_numpy()
    elig_np = elig.to_numpy()
    cols = np.array(opens.columns)
    wvals = np.zeros_like(ft_np)
    for i in range(len(opens.index)):
        ecols = np.where(elig_np[i])[0]
        if len(ecols) < 4:
            continue
        k = int(len(ecols) * FRAC)
        if k < 1:
            continue
        order = ecols[np.argsort(ft_np[i, ecols])]        # ascending funding
        wvals[i, order[:k]] = 1.0 / k                     # lowest funding -> LONG
        wvals[i, order[-k:]] = -1.0 / k                   # highest funding -> SHORT
    w = pd.DataFrame(wvals, index=opens.index, columns=cols)
    price = (w * ret).sum(axis=1)
    funding = -(w * fund_earn).sum(axis=1)
    turn = (w - w.shift(1)).abs().sum(axis=1)
    net = price + funding - pe.COST_SIDE * turn
    net.index = pd.to_datetime(opens.index, unit="ms")     # datetime index for monthly agg
    return net.dropna()


def selected_pairs_carry(coins: dict) -> pd.Series:
    """The 10 disjoint IS-selected carry pairs, IS-only inverse-vol weights (the selection book)."""
    rows = []
    names = list(coins)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            df = coins[a].join(coins[b], lsuffix="_a", rsuffix="_b", how="inner")
            if len(df) < MIN_OVERLAP:
                continue
            bt = pe.run(df, pe.signal_weights(df, "carry"))
            is_sh = pe.monthly_sharpe(bt["net"], LO0, pe.OOS_CUTOFF)
            yr = bt["net"].groupby(bt.index.year).sum()
            pos = float((yr[yr.index < 2025] > 0).mean()) if (yr.index < 2025).any() else 0.0
            if np.isfinite(is_sh):
                rows.append((a, b, is_sh, pos))
    r = pd.DataFrame(rows, columns=["a", "b", "is_sh", "pos"])
    r = r.sort_values(["pos", "is_sh"], ascending=False)
    used: set = set()
    sel = []
    for _, x in r.iterrows():
        if x.a in used or x.b in used:
            continue
        sel.append((x.a, x.b))
        used.update((x.a, x.b))
        if len(sel) >= 10:
            break
    series = {}
    for a, b in sel:
        df = coins[a].join(coins[b], lsuffix="_a", rsuffix="_b", how="inner")
        series[f"{a}/{b}"] = pe.run(df, pe.signal_weights(df, "carry"))["net"]
    panel = pd.DataFrame(series).sort_index()
    inv = 1.0 / panel[panel.index < pe.OOS_CUTOFF].std()
    return (panel.fillna(0.0) * (inv / inv.sum())).sum(axis=1)


def main() -> None:
    syms = sorted(p.split("/")[-1][:-4] for p in glob.glob("data/funding_rates/*USDT.csv"))
    coins = {s: pe.load_coin(s) for s in syms}
    coins = {s: d for s, d in coins.items() if d is not None}
    print(f"head-to-head on the REALISTIC engine ({len(coins)} funding coins):\n")
    print(f"  BROAD x-sectional carry : {stats(broad_carry(coins))}")
    print(f"  SELECTED carry pairs    : {stats(selected_pairs_carry(coins))}")


if __name__ == "__main__":
    main()
