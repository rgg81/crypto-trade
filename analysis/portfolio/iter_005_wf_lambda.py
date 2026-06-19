"""portfolio-iteration EXPLORATION-005 — WALK-FORWARD carry-tilt weight λ (no OOS peek).

iter-004 found a carry tilt λ=0.25 lifts OOS (+0.50 -> +1.31), but on IS λ=0 and λ=0.25 tie, so
0.25 was effectively OOS-picked. This selects λ per calendar month on the PAST window only (best past
monthly Sharpe), applies it to the test month, and stitches — a true walk-forward. If the OOS lift
survives honest λ-selection it is real and trend+carry-tilt becomes baseline; if not, reject.

Efficient: trend & carry signals computed ONCE; each λ's net derived from the shared blend.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_004_funding as f4  # noqa: E402

TRAIN_MONTHS = 24
GAP_CANDLES = 3
LAM_GRID = [0.0, 0.1, 0.25, 0.4]


def lam_nets(coins: dict) -> dict:
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
    trend = sum(np.sign(close / close.shift(h) - 1.0) for h in base.HORIZONS) / len(base.HORIZONS)
    carry = -np.sign(fund.rolling(f4.M_FUND).mean())
    fund_next = fund.shift(-1)
    nets = {}
    for lam in LAM_GRID:
        raw = (((1 - lam) * trend + lam * carry) / rvol).where(elig)
        w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
        pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
        fpnl = -(w * fund_next.reindex(columns=w.columns)).sum(axis=1)
        cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
        nets[lam] = base.vol_target((pnl + fpnl - cost).dropna())
    return nets


def walkforward(nets: dict) -> tuple[pd.Series, list]:
    panel = pd.DataFrame(nets).sort_index()
    months = pd.PeriodIndex(panel.index, freq="M").unique().sort_values()
    step = 8 * 60 * 60 * 1000
    parts, picks = [], []
    for ms in months:
        m0 = ms.to_timestamp()
        lo = m0 - pd.DateOffset(months=TRAIN_MONTHS)
        hi = m0 - pd.Timedelta(milliseconds=GAP_CANDLES * step)
        test_hi = (ms + 1).to_timestamp()
        train = panel[(panel.index >= lo) & (panel.index < hi)]
        test = panel[(panel.index >= m0) & (panel.index < test_hi)]
        if len(train) < 200 or test.empty:
            continue
        tsh = train.apply(lambda s: base.msharpe(s, base.LO0, base.HI1))
        if not np.isfinite(tsh.max()):
            continue
        best = tsh.idxmax()
        picks.append((m0.year, best))
        parts.append(test[best].rename("net"))
    return pd.concat(parts).sort_index(), picks


def main() -> None:
    coins = base.load_universe()
    nets = lam_nets(coins)
    print(f"EXPLORATION-005: walk-forward λ selection — {len(coins)} candidates, grid {LAM_GRID}")
    wf, picks = walkforward(nets)
    base.line("WALK-FWD λ", wf)
    from collections import Counter
    oos = Counter(b for y, b in picks if y >= 2025)
    print(f"     OOS λ-picks: {dict(sorted(oos.items()))}")
    base.line("fixed λ=0 (trend)", nets[0.0])
    base.line("fixed λ=0.25", nets[0.25])


if __name__ == "__main__":
    main()
