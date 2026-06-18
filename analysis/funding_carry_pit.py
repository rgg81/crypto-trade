"""FUNDING CARRY — POINT-IN-TIME universe + capacity floor (the survivorship/realizability test).

funding_carry.py showed the cross-sectional funding-income carry is significant + IS/OOS-stable, but
used a fixed survivor list. This script removes the two leaks and adds realizability:
  - POINT-IN-TIME universe: at each rebalance t, a coin is eligible ONLY if its TRAILING-30d
    quote-volume (as-of t, past-only) clears a liquidity floor AND it has a valid funding signal.
    No "alive through OOS" filter, no recent/OOS-era volume ranking → coins enter/exit naturally,
    survivorship + recency leak removed.
  - CAPACITY floor: only liquid-enough coins trade; short-top-k / long-bottom-k drawn from the
    point-in-time-eligible set each period (k scales with how many are eligible).
  - Decompose funding-income vs price; IS/OOS monthly Sharpe; funding-only monthly t-stat.

If the funding carry survives THIS, it is a genuine candidate (modulo live frictions: funding
spikes/squeezes, short borrow at size, tail risk — still backtest-optimistic). Residual caveat: we
only have funding data for ~40 coins, itself a mild establishment bias (noted, not fixable here).
"""

from __future__ import annotations

import glob

import numpy as np
import pandas as pd

OOS_CUTOFF = pd.Timestamp("2025-03-24")
M_TRAIL = 9             # trailing-funding signal window (3 days)
LIQ_WIN = 90            # trailing liquidity window (30 days of 8h candles)
LIQ_FLOOR = 5e6         # min trailing avg 8h quote-volume ($) to be eligible (capacity floor)
FRAC = 0.25            # short top 25% funding / long bottom 25% of the eligible set each period
COST_SIDE = 0.07 / 100


def load_coin(sym: str) -> pd.DataFrame | None:
    try:
        k = pd.read_csv(f"data/{sym}/8h.csv", usecols=["open_time", "close", "quote_volume"])
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


def build_panel(universe: list[str]) -> pd.DataFrame:
    frames = []
    for sym in universe:
        d = load_coin(sym)
        if d is None:
            continue
        c = d["close"].astype(float)
        f = d["funding_rate"].astype(float)
        qv = d["quote_volume"].astype(float)
        g = pd.DataFrame({"open_time": d["open_time"].to_numpy(), "coin": sym})
        g["signal"] = f.rolling(M_TRAIL).mean().shift(1)            # past-only funding
        g["f_earned"] = f.shift(-1)
        g["r1"] = c.shift(-1) / c - 1.0
        g["liq"] = qv.rolling(LIQ_WIN).mean().shift(1)              # past-only trailing liquidity
        frames.append(g)
    return pd.concat(frames, ignore_index=True)


def carry_book_pit(panel: pd.DataFrame) -> pd.DataFrame:
    """Point-in-time eligible (liq>=floor) short-top / long-bottom funding, dollar-neutral."""
    sub = panel.dropna(subset=["signal", "f_earned", "r1", "liq"])
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
        w[gg["coin"].to_numpy()[:k]] = 1.0 / k          # lowest funding → LONG
        w[gg["coin"].to_numpy()[-k:]] = -1.0 / k        # highest funding → SHORT
        f = pd.Series(g["f_earned"].to_numpy(), index=g["coin"].to_numpy())
        r = pd.Series(g["r1"].to_numpy(), index=g["coin"].to_numpy())
        fund_pnl = float(-(w * f).sum())
        price_pnl = float((w * r).sum())
        if prev is None:
            turn = w.abs().sum()
        else:
            allc = w.index.union(prev.index)
            turn = (w.reindex(allc).fillna(0.0) - prev.reindex(allc).fillna(0.0)).abs().sum()
        rows.append((ot, fund_pnl, price_pnl, fund_pnl + price_pnl - COST_SIDE * turn, m))
        prev = w
    cols = ["open_time", "fund_pnl", "price_pnl", "net", "n_eligible"]
    return pd.DataFrame(rows, columns=cols).set_index("open_time")


def msharpe(series: pd.Series, idx, lo, hi):
    s = pd.Series(series.to_numpy(), index=idx)
    s = s[(s.index >= lo) & (s.index < hi)]
    g = s.groupby(s.index.to_period("M")).sum()
    if len(g) < 2 or g.std() == 0:
        return float("nan"), float("nan"), len(g)
    return g.mean() / g.std() * np.sqrt(12), g.mean() / (g.std() / np.sqrt(len(g))), len(g)


def main() -> None:
    syms = sorted(p.split("/")[-1][:-4] for p in glob.glob("data/funding_rates/*USDT.csv"))
    panel = build_panel(syms)
    book = carry_book_pit(panel)
    idx = pd.to_datetime(book.index, unit="ms")
    lo0, hi1 = pd.Timestamp("2000-01-01"), pd.Timestamp("2100-01-01")
    ppy = 365.25 * 3
    oos = book.loc[idx >= OOS_CUTOFF]
    print(f"funding coins available: {len(syms)} | median eligible/period: "
          f"{int(book['n_eligible'].median())} | periods: {len(book)}")
    print("\n===== FUNDING CARRY — POINT-IN-TIME + CAPACITY FLOOR =====")
    for comp in ["fund_pnl", "price_pnl", "net"]:
        is_sh, _, _ = msharpe(book[comp], idx, lo0, OOS_CUTOFF)
        oos_sh, _, _ = msharpe(book[comp], idx, OOS_CUTOFF, hi1)
        print(f"  {comp:10s}: IS Sharpe={is_sh:+.3f}  OOS Sharpe={oos_sh:+.3f}")
    for label, lo, hi in [("IS", lo0, OOS_CUTOFF), ("OOS", OOS_CUTOFF, hi1)]:
        sh, t, n = msharpe(book["fund_pnl"], idx, lo, hi)
        seg = book.loc[(idx >= lo) & (idx < hi), "fund_pnl"]
        print(f"  FUNDING-ONLY {label}: {seg.mean()*ppy*100:+.1f}%/yr  monthly t={t:+.2f} (n={n})")
    is_sh, _, _ = msharpe(book["net"], idx, lo0, OOS_CUTOFF)
    oos_sh, _, _ = msharpe(book["net"], idx, OOS_CUTOFF, hi1)
    print(f"  NET: IS Sharpe={is_sh:+.3f}  OOS Sharpe={oos_sh:+.3f}  "
          f"(OOS {oos['net'].mean()*ppy*100:+.1f}%/yr after cost)")
    yr = pd.Series(book["net"].to_numpy(), index=idx)
    ann = yr.groupby(yr.index.year).sum() * 100
    print("  net %/yr by year:", {int(k): round(v, 0) for k, v in ann.items()})


if __name__ == "__main__":
    main()
