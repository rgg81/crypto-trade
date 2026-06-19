"""portfolio-iteration EXPLORATION-003 — trend-AGREEMENT gate on the iter-002 TS-trend baseline.

ONE change vs baseline: only hold a coin when its multi-horizon trend signals AGREE — i.e. require
|mean-sign over {7,14,28,56d}| >= gate. gate=0 is the baseline (all). gate=0.5 keeps coins where
>=3 of 4 horizons agree; gate=1.0 only when ALL 4 agree. Hypothesis: filtering weak/conflicting
trends (whipsaw) lifts OOS Sharpe and cuts the -28% DD without breaking IS.

Reuses the iter-002 universe loader + conventions. Realistic cost, vol-targeted, leak-safe.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402


def build_gated(coins: dict, gate: float):
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    close = pd.DataFrame({s: d["close"] for s, d in coins.items()}).astype(float)
    close = close.reindex(opens.index)
    qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).astype(float)
    qv = qv.reindex(opens.index)
    opens.index = pd.to_datetime(opens.index, unit="ms")
    close.index = opens.index
    qv.index = opens.index
    ret_fwd = opens.shift(-1) / opens - 1.0
    liq = qv.rolling(base.LIQ_WIN).mean().shift(1)
    elig = liq.rank(axis=1, ascending=False) <= base.TOP_N
    rvol = close.pct_change().rolling(base.VOL_WIN).std()
    sig = sum(np.sign(close / close.shift(h) - 1.0) for h in base.HORIZONS) / len(base.HORIZONS)
    sig = sig.where(sig.abs() >= gate, 0.0)              # trend-agreement gate
    raw = (sig / rvol).where(elig)
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    net = (pnl - cost).dropna()
    return base.vol_target(net)


def main() -> None:
    coins = base.load_universe()
    print(f"EXPLORATION-003: trend-agreement gate on TS-trend baseline — {len(coins)} candidates")
    for gate in [0.0, 0.5, 1.0]:
        net = build_gated(coins, gate)
        label = f"gate={gate} ({'baseline' if gate == 0 else f'>={int(gate*4)}/4 agree'})"
        base.line(label, net)


if __name__ == "__main__":
    main()
