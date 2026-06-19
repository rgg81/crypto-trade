"""portfolio-iteration EXPLORATION-001 — BTC time-series momentum (trend), standalone anchor.

First "little by little" step: validate that a vol-targeted multi-horizon trend signal on BTC nets
POSITIVE after realistic costs + funding. Long when trending up, short when down, sized inverse to
realized vol. Realistic execution: decide on CLOSE[t] -> fill at OPEN[t+1] -> hold. Taker cost
on position change; funding paid/earned on the perp hold. Signals past-only (leak-safe).

Anchor for the top-20 long/short portfolio (iter-002+ adds the cross-section).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

OOS_CUTOFF = pd.Timestamp("2025-03-24")
LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")
COST_SIDE = 0.0005             # taker ~0.05%/side (Binance perp taker)
HORIZONS = [21, 42, 84, 168]   # 8h candles ~ 7d / 14d / 28d / 56d
VOL_WIN = 84                   # ~28d realized-vol window
TARGET_VOL = 0.01              # per-candle target vol (scales leverage)
MAX_LEV = 2.0


def load_btc() -> pd.DataFrame:
    k = pd.read_csv("data/BTCUSDT/8h.csv")
    k = k.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
    f = pd.read_csv("data/funding_rates/BTCUSDT.csv")
    f = f.drop_duplicates(subset="funding_time", keep="last")
    f = f.set_index("funding_time")["funding_rate"]
    df = pd.DataFrame({"open": k["open"].astype(float), "close": k["close"].astype(float)})
    df["funding"] = f.reindex(df.index).fillna(0.0).astype(float)
    df.index = pd.to_datetime(df.index, unit="ms")
    return df


def msharpe(net: pd.Series, lo, hi) -> float:
    s = net[(net.index >= lo) & (net.index < hi)]
    g = s.groupby(s.index.to_period("M")).sum()
    return g.mean() / g.std() * np.sqrt(12) if len(g) > 1 and g.std() > 0 else float("nan")


def line(label: str, s: pd.Series) -> None:
    eq = (1 + s).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    yr = {int(k): round(v * 100, 0) for k, v in s.groupby(s.index.year).sum().items()}
    print(f"  {label:16} IS={msharpe(s, LO0, OOS_CUTOFF):+.2f} "
          f"OOS={msharpe(s, OOS_CUTOFF, HI1):+.2f} maxDD={dd*100:4.0f}% "
          f"netTot={(eq.iloc[-1]-1)*100:+.0f}%")
    print(f"     net%/yr={yr}")


def main() -> None:
    df = load_btc()
    close, opn, fund = df["close"], df["open"], df["funding"]
    # trend signal at close[t], PAST-ONLY: mean sign of trailing returns over multiple horizons
    sig = sum(np.sign(close / close.shift(h) - 1.0) for h in HORIZONS) / len(HORIZONS)
    rvol = close.pct_change().rolling(VOL_WIN).std()
    lev = (TARGET_VOL / rvol).clip(upper=MAX_LEV)
    pos = (sig * lev).shift(1)             # decided at close[t-1], applied to next candle (no leak)
    ret_fwd = opn.shift(-1) / opn - 1.0    # candle return open[t]->open[t+1]; pos already lagged
    fund_pay = -pos * fund                 # long pays funding when funding>0
    cost = COST_SIDE * (pos - pos.shift(1)).abs()
    net = (pos * ret_fwd + fund_pay - cost).dropna()
    bh = ret_fwd.reindex(net.index).fillna(0.0)

    print("EXPLORATION-001: BTC time-series momentum (vol-targeted L/S), realistic cost+funding")
    print(f"  horizons={HORIZONS}  vol_win={VOL_WIN}  target_vol={TARGET_VOL}  max_lev={MAX_LEV}")
    line("TREND (net)", net)
    line("buy&hold BTC", bh)
    print(f"  avg turnover/candle = {(pos - pos.shift(1)).abs().mean():.3f}")


if __name__ == "__main__":
    main()
