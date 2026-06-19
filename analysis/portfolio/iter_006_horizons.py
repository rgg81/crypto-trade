"""portfolio-iteration EXPLORATION-006 — trend-horizon ROBUSTNESS check (not an optimization).

Baseline trend uses horizons {7,14,28,56d}. Is the confirmed edge (trend+carry-tilt) robust to that
choice, or fragile/overfit to it? Run the SAME strategy (carry tilt λ=0.25, real funding) across
several fixed horizon sets and compare IS/OOS. Similar across sets => robust (keep base); wildly
divergent => fragile (red flag). We do NOT pick the best-OOS set (that would be selection bias).
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_004_funding as f4  # noqa: E402

LAM = 0.25
CONFIGS = {
    "short {3,7,14,28d}": [9, 21, 42, 84],
    "base {7,14,28,56d}": [21, 42, 84, 168],
    "long {14,28,56,112d}": [42, 84, 168, 336],
    "wide {7,14,28,56,112d}": [21, 42, 84, 168, 336],
}


def build(coins: dict, horizons: list):
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    close = pd.DataFrame({s: d["close"] for s, d in coins.items()}).astype(float)
    close = close.reindex(opens.index)
    qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).astype(float)
    qv = qv.reindex(opens.index)
    fund = f4.load_funding(opens.index, list(coins.keys())).reindex(opens.index)
    dt = pd.to_datetime(opens.index, unit="ms")
    for df in (opens, close, qv, fund):
        df.index = dt
    ret_fwd = opens.shift(-1) / opens - 1.0
    elig = qv.rolling(base.LIQ_WIN).mean().shift(1).rank(axis=1, ascending=False) <= base.TOP_N
    rvol = close.pct_change().rolling(base.VOL_WIN).std()
    trend = sum(np.sign(close / close.shift(h) - 1.0) for h in horizons) / len(horizons)
    carry = -np.sign(fund.rolling(f4.M_FUND).mean())
    raw = (((1 - LAM) * trend + LAM * carry) / rvol).where(elig)
    w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    fpnl = -(w * fund.shift(-1).reindex(columns=w.columns)).sum(axis=1)
    cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    return base.vol_target((pnl + fpnl - cost).dropna())


def main() -> None:
    coins = base.load_universe()
    print(f"EXPLORATION-006: trend-horizon robustness (tilt λ={LAM}) — {len(coins)} coins")
    for label, hz in CONFIGS.items():
        base.line(label, build(coins, hz))


if __name__ == "__main__":
    main()
