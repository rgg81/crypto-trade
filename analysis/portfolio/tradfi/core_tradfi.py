"""TradFi-portfolio foundation — daily-bar leak-safe backtest core.

Forked from analysis/portfolio/metals/universe_metals.py, recalibrated for DAILY bars and a
self-updating stock universe. The leak-safe accounting is identical: decide on close[t],
fill at open[t+1], weights `.shift(1)`-lagged, taker cost on turnover, portfolio vol-target.
OOS stays hidden unless reveal_oos=True (CONFIRMATION).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[3]

OOS_CUTOFF = pd.Timestamp("2025-03-24")  # immutable; IS < cutoff, OOS >= cutoff
LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")

COST_SIDE = 0.0006  # 6 bps/side taker + slippage on |Δweight| turnover
ANNUAL_TARGET_VOL = 0.15
MAX_LEV = 5.0
CANDLES_PER_YEAR = 252  # US equity trading days/year
TARGET_VOL = ANNUAL_TARGET_VOL / np.sqrt(CANDLES_PER_YEAR)  # per-day target ≈ 0.00945

HORIZONS = (21, 63, 126, 252)  # ~1m / 3m / 6m / 12m in trading days
VOL_WIN = 63  # 3m realized-vol window for inverse-vol sizing
PORT_VOL_WIN = 63  # portfolio vol-target lookback

# Fixed IS regime tags (US equity regimes; IS-only, used for all-weather scoring).
_REGIMES = [
    ("bull", "2012-01-01", "2020-02-19"),
    ("bear", "2020-02-19", "2020-04-01"),  # COVID crash
    ("bull", "2020-04-01", "2022-01-03"),
    ("bear", "2022-01-03", "2022-10-13"),  # 2022 bear
    ("chop", "2022-10-13", "2023-06-01"),
    ("bull", "2023-06-01", "2025-03-24"),
]


def load_tradfi(symbols, data_dir=None) -> dict[str, pd.DataFrame]:
    """Load each symbol's daily CSV into {ticker: OHLCV DataFrame indexed by open_time ms}.

    Missing files are skipped with a note (point-in-time: a name not yet ingested is absent).
    """
    base = Path(data_dir) if data_dir is not None else _ROOT / "data"
    coins: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        p = base / sym / "1d.csv"
        if not p.exists():
            print(f"  ! {sym}: missing {p} — skipped")
            continue
        k = pd.read_csv(p, usecols=["open_time", "open", "high", "low", "close", "volume"])
        k = k.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
        coins[sym] = k
    return coins


def panels(coins: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Aligned float panels (DatetimeIndex) + leak-safe forward open-to-open return.

    ret_fwd[t] = open[t+1]/open[t] - 1 : the return earned by a position decided at close[t].
    NaN where an asset has no bar (ragged start / holiday) — never forward-filled.
    """
    cols = list(coins)
    opens = pd.DataFrame({s: coins[s]["open"] for s in cols}).astype(float).sort_index()
    out: dict[str, pd.DataFrame] = {"open": opens}
    for field in ("high", "low", "close"):
        out[field] = (
            pd.DataFrame({s: coins[s][field] for s in cols}).astype(float).reindex(opens.index)
        )
    idx = pd.to_datetime(opens.index, unit="ms")
    for df in out.values():
        df.index = idx
    out["ret_fwd"] = out["open"].shift(-1) / out["open"] - 1.0
    return out


def vol_target_scale(net: pd.Series) -> pd.Series:
    """Per-candle vol-target SCALAR (past-only): TARGET_VOL / trailing-vol, capped at MAX_LEV."""
    rv = net.rolling(PORT_VOL_WIN).std().shift(1)
    return (TARGET_VOL / rv).clip(upper=MAX_LEV).fillna(0.0)


def vol_target(net: pd.Series) -> pd.Series:
    """Scale a per-candle net-return series to ~ANNUAL_TARGET_VOL, capped at MAX_LEV."""
    return net * vol_target_scale(net)


def net_from_raw(raw: pd.DataFrame, ret_fwd: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """Leak-safe core: signed raw weights → (vol-targeted net return, lagged weight book).

    gross-normalise to 1 → LAG one bar (.shift(1)) → PnL = Σ w·ret_fwd → taker cost on
    |Δw| turnover → portfolio vol-target.
    """
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    cost = COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    net = (pnl - cost).dropna()
    return vol_target(net), w


def msharpe(net: pd.Series, lo=LO0, hi=HI1) -> float:
    """Annualised Sharpe from MONTHLY summed returns over [lo, hi) (√12 annualisation)."""
    s = net[(net.index >= lo) & (net.index < hi)]
    g = s.groupby(s.index.to_period("M")).sum()
    return g.mean() / g.std() * np.sqrt(12) if len(g) > 1 and g.std() > 0 else float("nan")


def turnover(w, lo=LO0, hi=HI1) -> float:
    """Mean per-candle gross turnover Σ|Δw| over [lo, hi)."""
    t = (
        (w - w.shift(1)).abs().sum(axis=1)
        if isinstance(w, pd.DataFrame)
        else (w - w.shift(1)).abs()
    )
    t = t[(t.index >= lo) & (t.index < hi)]
    return float(t.mean())


def maxdd(net: pd.Series) -> float:
    """Max drawdown of the compounded equity curve (negative fraction)."""
    eq = (1 + net).cumprod()
    return float((eq / eq.cummax() - 1).min())


def regime_of(idx: pd.DatetimeIndex) -> pd.Series:
    """Map each timestamp to a fixed IS regime label ('bull'|'bear'|'chop'|'oos')."""
    out = pd.Series("oos", index=idx, dtype=object)
    for label, lo, hi in _REGIMES:
        m = (idx >= pd.Timestamp(lo)) & (idx < pd.Timestamp(hi))
        out[m] = label
    return out


def regime_sharpe(net: pd.Series) -> dict[str, float]:
    """Per-regime annualised Sharpe over the IS window (all-weather scorecard)."""
    reg = regime_of(net.index)
    out: dict[str, float] = {}
    for label in ("bull", "bear", "chop"):
        sub = net[reg == label]
        g = sub.groupby(sub.index.to_period("M")).sum()
        out[label] = (
            float(g.mean() / g.std() * np.sqrt(12)) if len(g) > 1 and g.std() > 0 else float("nan")
        )
    return out


def perf_line(label: str, net: pd.Series, *, reveal_oos: bool = False) -> str:
    """One-line IS performance summary. OOS hidden unless reveal_oos=True (CONFIRMATION).

    When reveal_oos is False, maxDD and netTot are computed over the IS-only slice too —
    not just IS_Sharpe — so an EXPLORATION run leaks NO OOS information.
    """
    src = net if reveal_oos else is_only(net)
    eq = (1 + src).cumprod()
    parts = [
        f"  {label:18} IS_Sharpe={msharpe(net, LO0, OOS_CUTOFF):+.2f}",
        f"maxDD={maxdd(src) * 100:5.1f}%",
        f"netTot={(eq.iloc[-1] - 1) * 100:+.0f}%",
    ]
    if reveal_oos:
        parts.insert(2, f"OOS_Sharpe={msharpe(net, OOS_CUTOFF, HI1):+.2f}")
    return "  ".join(parts)


def is_only(net: pd.Series) -> pd.Series:
    """Slice a net series to the IN-SAMPLE window only (guards accidental OOS peeking)."""
    return net[net.index < OOS_CUTOFF]
