"""portfolio-iteration EXPLORATION-002 — top-20 LONG/SHORT portfolio (diversified trend + xsec).

Extends the iter-001 BTC trend anchor to a portfolio. Two long/short modes on a POINT-IN-TIME top-20
(ranked each candle by trailing $-volume, ex-stablecoins):
  - TS-TREND   : each coin long/short by its OWN trend (mean-sign over horizons), inverse-vol sized.
  - XSEC-MOM   : rank the top-20 by trailing return; long winners, short losers (dollar-neutral).
  - COMBO      : average of the two (both diversified across the cross-section).
Portfolio is vol-targeted (past-only). Realistic: decide close[t] -> fill open[t+1] -> hold; taker
cost on turnover; funding paid/earned on perp holds. All signals past-only (leak-safe).

Goal vs iter-001: diversification should CUT the -35% single-asset DD and lift OOS Sharpe.
"""

from __future__ import annotations

import glob
import re

import numpy as np
import pandas as pd

OOS_CUTOFF = pd.Timestamp("2025-03-24")
LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")
COST_SIDE = 0.0005
HORIZONS = [21, 42, 84, 168]
VOL_WIN = 84
MIN_HISTORY = 2190            # ~2y of 8h candles — established-coin candidate pool
TOP_N = 20                   # point-in-time universe size
LIQ_WIN = 90                 # trailing-30d volume window for the liquidity rank
PORT_VOL_WIN = 84            # portfolio vol-target window
TARGET_VOL = 0.01            # per-candle portfolio vol target
MAX_LEV = 3.0
STABLE = re.compile(r"(USDC|BUSD|FDUSD|TUSD|USD1|DAI|USDP|EUR|USTC|FRAX|PAXG|XUSD|USDE)")


def load_universe() -> dict:
    coins = {}
    for p in sorted(glob.glob("data/*USDT/8h.csv")):
        sym = p.split("/")[1]
        if not sym.endswith("USDT") or STABLE.search(sym) or not sym.isascii():
            continue
        try:
            k = pd.read_csv(p, usecols=["open_time", "open", "close", "quote_volume"])
        except Exception:
            continue
        if len(k) < MIN_HISTORY:
            continue
        k = k.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
        coins[sym] = k
    return coins


def msharpe(net: pd.Series, lo, hi) -> float:
    s = net[(net.index >= lo) & (net.index < hi)]
    g = s.groupby(s.index.to_period("M")).sum()
    return g.mean() / g.std() * np.sqrt(12) if len(g) > 1 and g.std() > 0 else float("nan")


def vol_target(net: pd.Series) -> pd.Series:
    rv = net.rolling(PORT_VOL_WIN).std().shift(1)
    scale = (TARGET_VOL / rv).clip(upper=MAX_LEV).fillna(0.0)
    return net * scale


def build(coins: dict, mode: str) -> tuple[pd.Series, pd.DataFrame]:
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    close = pd.DataFrame({s: d["close"] for s, d in coins.items()}).astype(float)
    close = close.reindex(opens.index)
    qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).astype(float)
    qv = qv.reindex(opens.index)
    opens.index = pd.to_datetime(opens.index, unit="ms")
    close.index = opens.index
    qv.index = opens.index
    ret_fwd = opens.shift(-1) / opens - 1.0
    # point-in-time top-N by trailing $-volume (past-only)
    liq = qv.rolling(LIQ_WIN).mean().shift(1)
    rank_liq = liq.rank(axis=1, ascending=False)
    elig = rank_liq <= TOP_N
    # per-coin signals (past-only)
    rvol = close.pct_change().rolling(VOL_WIN).std()
    if mode == "ts_trend":
        sig = sum(np.sign(close / close.shift(h) - 1.0) for h in HORIZONS) / len(HORIZONS)
        raw = (sig / rvol).where(elig)
    elif mode == "xsec_mom":
        mom = close / close.shift(84) - 1.0                  # 28d trailing return
        r = mom.where(elig).rank(axis=1)                     # cross-sectional rank within top-N
        n = elig.sum(axis=1)
        raw = (r.sub(n.add(1) / 2, axis=0)).div(n, axis=0).where(elig)   # centered, dollar-neutral
    else:  # combo
        ts, _ = build(coins, "ts_trend")
        xs, _ = build(coins, "xsec_mom")
        return (ts + xs) / 2.0, pd.DataFrame()
    # normalize gross to 1, lag, costs, funding-free for now (funding tilt is a later iter)
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    cost = COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    net = (pnl - cost).dropna()
    return vol_target(net), w


def line(label: str, s: pd.Series) -> None:
    eq = (1 + s).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    yr = {int(k): round(v * 100, 0) for k, v in s.groupby(s.index.year).sum().items()}
    print(f"  {label:14} IS={msharpe(s, LO0, OOS_CUTOFF):+.2f} "
          f"OOS={msharpe(s, OOS_CUTOFF, HI1):+.2f} maxDD={dd*100:4.0f}% "
          f"netTot={(eq.iloc[-1]-1)*100:+.0f}%")
    print(f"     net%/yr={yr}")


def main() -> None:
    coins = load_universe()
    print(f"EXPLORATION-002: top-{TOP_N} L/S (PIT, ex-stables) — {len(coins)} candidates")
    for mode in ["ts_trend", "xsec_mom", "combo"]:
        net, _ = build(coins, mode)
        line(mode, net)


if __name__ == "__main__":
    main()
