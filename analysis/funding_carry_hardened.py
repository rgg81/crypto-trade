"""FUNDING CARRY — HARDENED deployable config (low-turnover + squeeze stop).

The realizability check found the carry's killer is a ~-50% drawdown from short-SQUEEZE blowups
(a single -14% 8h candle) plus cost-sensitivity. This characterizes a deployable config:
  - M_TRAIL=21 (7d signal): the sensitivity grid showed long signals cut turnover -> less cost.
  - SQUEEZE STOP S: per position, cap the per-candle adverse move via intra-candle high/low. A short
    is stopped at +S if the candle HIGH spiked >= S above entry; a long stopped at -S if the LOW
    dropped >= S. Bounds per-position loss -> meant to cap the tail.
Compares net Sharpe (1x + 2x cost) + max drawdown + worst candle, no-stop vs stops {.25,.15,.10}.
Point-in-time universe + $5M capacity floor (same honest setup as funding_carry_pit).

FINDING: M_TRAIL=21 fixes the cost-fragility (OOS net Sharpe +2.11 at 2x cost vs M=9's +0.43); the
squeeze STOP is COUNTERPRODUCTIVE (crypto spikes mean-revert intra-candle, so stopping at the high
locks the worst tick -> worse DD). The ~-44% DD is the price-leg directional tail; fix = beta-hedge
or vol-target, NOT stops.
"""

from __future__ import annotations

import glob

import numpy as np
import pandas as pd

OOS_CUTOFF = pd.Timestamp("2025-03-24")
M_TRAIL = 21
LIQ_WIN = 90
LIQ_FLOOR = 5e6
FRAC = 0.25
COST_SIDE = 0.07 / 100


def load_coin(sym: str):
    try:
        k = pd.read_csv(f"data/{sym}/8h.csv",
                        usecols=["open_time", "high", "low", "close", "quote_volume"])
        fr = pd.read_csv(f"data/funding_rates/{sym}.csv")
    except (FileNotFoundError, ValueError):
        return None
    k = k.dropna(subset=["open_time", "close"]).drop_duplicates("open_time")
    k = k.sort_values("open_time")
    step = 8 * 60 * 60 * 1000
    fr = fr.dropna(subset=["funding_time", "funding_rate"]).copy()
    fr["open_time"] = (fr["funding_time"] // step) * step
    fr = fr.groupby("open_time", as_index=False)["funding_rate"].mean()
    d = k.merge(fr, on="open_time", how="left").sort_values("open_time").reset_index(drop=True)
    d["funding_rate"] = d["funding_rate"].fillna(0.0)
    return d if len(d) > 1000 else None


def build_panel(universe):
    frames = []
    for sym in universe:
        d = load_coin(sym)
        if d is None:
            continue
        c = d["close"].astype(float)
        f = d["funding_rate"].astype(float)
        g = pd.DataFrame({"open_time": d["open_time"].to_numpy(), "coin": sym})
        g["signal"] = f.rolling(M_TRAIL).mean().shift(1)
        g["f_earned"] = f.shift(-1)
        g["r1"] = c.shift(-1) / c - 1.0
        g["up_exc"] = d["high"].astype(float).shift(-1) / c - 1.0   # short adverse (price up)
        g["dn_exc"] = 1.0 - d["low"].astype(float).shift(-1) / c    # long adverse (price down)
        g["liq"] = d["quote_volume"].astype(float).rolling(LIQ_WIN).mean().shift(1)
        frames.append(g)
    return pd.concat(frames, ignore_index=True)


def carry_book(panel, stop=None):
    sub = panel.dropna(subset=["signal", "f_earned", "r1", "liq", "up_exc", "dn_exc"])
    sub = sub[sub["liq"] >= LIQ_FLOOR]
    rows = []
    prev = None
    for ot, g in sub.groupby("open_time"):
        m = len(g)
        k = int(m * FRAC)
        if k < 1 or m < 4:
            continue
        gg = g.sort_values("signal")
        w = pd.Series(0.0, index=g["coin"].to_numpy())
        w[gg["coin"].to_numpy()[:k]] = 1.0 / k
        w[gg["coin"].to_numpy()[-k:]] = -1.0 / k
        gi = g.set_index("coin")
        r1 = gi["r1"]
        if stop is not None:  # bound per-position price return via intra-candle excursion
            long_ret = np.where(gi["dn_exc"] >= stop, -stop, r1)
            short_ret = np.where(gi["up_exc"] >= stop, stop, r1)
            ww = w.reindex(gi.index)
            pos_ret = pd.Series(np.where(ww > 0, long_ret, np.where(ww < 0, short_ret, r1)),
                                index=gi.index)
        else:
            pos_ret = r1
        f = gi["f_earned"]
        fund_pnl = float(-(w.reindex(gi.index) * f).sum())
        price_pnl = float((w.reindex(gi.index) * pos_ret).sum())
        if prev is None:
            turn = w.abs().sum()
        else:
            allc = w.index.union(prev.index)
            turn = (w.reindex(allc).fillna(0.0) - prev.reindex(allc).fillna(0.0)).abs().sum()
        rows.append((ot, fund_pnl, price_pnl, fund_pnl + price_pnl - COST_SIDE * turn))
        prev = w
    cols = ["open_time", "fund_pnl", "price_pnl", "net"]
    return pd.DataFrame(rows, columns=cols).set_index("open_time")


def msharpe(net, idx, lo, hi):
    s = pd.Series(net.to_numpy(), index=idx)
    s = s[(s.index >= lo) & (s.index < hi)]
    g = s.groupby(s.index.to_period("M")).sum()
    return g.mean() / g.std() * np.sqrt(12) if len(g) > 1 and g.std() > 0 else float("nan")


def max_dd(net):
    eq = (1.0 + net).cumprod()
    return float((eq / eq.cummax() - 1.0).min())


def main():
    global COST_SIDE
    syms = sorted(p.split("/")[-1][:-4] for p in glob.glob("data/funding_rates/*USDT.csv"))
    panel = build_panel(syms)
    hi1 = pd.Timestamp("2100-01-01")
    print(f"HARDENED carry (M_TRAIL={M_TRAIL}, $5M floor, FRAC={FRAC}); squeeze-stop comparison:")
    print(f"{'stop':>6} | {'netSh1x':>8} {'netSh2x':>8} {'fullDD':>7} {'oosDD':>7} {'worst':>7}")
    print("-" * 56)
    base = COST_SIDE
    for stop in (None, 0.25, 0.15, 0.10):
        COST_SIDE = base
        b = carry_book(panel, stop)
        idx = pd.to_datetime(b.index, unit="ms")
        sh1 = msharpe(b["net"], idx, OOS_CUTOFF, hi1)
        COST_SIDE = base * 2
        b2 = carry_book(panel, stop)
        sh2 = msharpe(b2["net"], pd.to_datetime(b2.index, unit="ms"), OOS_CUTOFF, hi1)
        oos = b[idx >= OOS_CUTOFF]
        lbl = "none" if stop is None else f"{stop:.0%}"
        print(f"{lbl:>6} | {sh1:>+9.2f} {sh2:>+9.2f} {max_dd(b['net'])*100:>6.1f}% "
              f"{max_dd(oos['net'])*100:>6.1f}% {b['net'].min()*100:>+7.1f}%")
    COST_SIDE = base


if __name__ == "__main__":
    main()
