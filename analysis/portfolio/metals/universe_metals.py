"""Metals-portfolio foundation — fixed precious-metals universe + reusable backtest math.

Parallel to the crypto `portfolio-iteration` stack (analysis/portfolio/iter_*), but for the
4 Binance precious-metal perps. The crypto universe explicitly EXCLUDES these
(iter_002_top20.NON_COIN_PERPS lists XAU/XAG/XPT/XPD; PAXG is in its STABLE regex), so the
two tracks never overlap.

Design vs the crypto stack:
  - FIXED universe (no point-in-time liquidity ranking) — there are only 4 metals.
  - RAGGED starts handled point-in-time: gold/silver from 2015, platinum/palladium from 2022
    (Dukascopy depth). An asset carries weight only once it has signal history (NaN→0 weight).
  - Same leak-safe core as iter_002: decide on close[t]/open, fill at open[t+1], weights
    `.shift(1)`-lagged, taker cost on turnover, portfolio vol-target (past-only).

Risk sizing (user directive): ~15% annual vol target, ≤5× leverage.
Cost: 0.05% taker + 0.01% slippage = 0.06%/side (Binance metals-perp fee; tight spreads).
Funding is NOT modelled (no historical data; small for metals; out of scope per directive).

Data: data/<TICKER>/8h.csv produced by ingest_dukascopy.py (Dukascopy bid OHLC → 8h UTC).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[3]

# ── Universe ──────────────────────────────────────────────────────────────────────────
UNIVERSE: tuple[str, ...] = ("XAUUSDT", "XAGUSDT", "XPTUSDT", "XPDUSDT")
NAMES = {"XAUUSDT": "gold", "XAGUSDT": "silver", "XPTUSDT": "platinum", "XPDUSDT": "palladium"}


def metals_market_open(open_time_ms: int) -> bool:
    """True iff the 8h candle opening at ``open_time_ms`` is a metals MARKET-HOURS (24/5) candle.

    The strategy is 24/5 (Dukascopy has no weekend candles; CANDLES_PER_YEAR=825 and the vol target
    depend on it). Binance metal perps trade 24/7, so its live/backfill klines are filtered to the
    24/5 schedule the strategy was validated on: KEEP Mon-Fri (all 00/08/16 UTC slots) + the
    Sun-16:00 reopen candle (metals reopen ~Sun 22:00 UTC); DROP Sat (all) and Sun 00:00/08:00.
    (Derived from the Dukascopy 2024 pattern.) Epoch 1970-01-01 was a Thu, so dow = (days+3) % 7.
    """
    dow = (open_time_ms // 86_400_000 + 3) % 7  # Mon=0 .. Sun=6
    hour = (open_time_ms // 3_600_000) % 24
    return dow <= 4 or (dow == 6 and hour == 16)

# ── Sacred constants (inherited from the project) ─────────────────────────────────────
OOS_CUTOFF = pd.Timestamp("2025-03-24")  # immutable; IS < cutoff, OOS >= cutoff
LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")

# ── Cost / risk model ─────────────────────────────────────────────────────────────────
COST_SIDE = 0.0006  # 5bps taker + 1bp slippage, per side, on |Δweight| turnover
ANNUAL_TARGET_VOL = 0.15  # ~15% annualised portfolio vol target
MAX_LEV = 5.0  # leverage cap on the vol-target scalar
# 8h metals candles trade ~24/5 → ~825 candles/year (empirical from gold 2015-2026).
CANDLES_PER_YEAR = 825
TARGET_VOL = ANNUAL_TARGET_VOL / np.sqrt(CANDLES_PER_YEAR)  # per-candle target ≈ 0.0052

# ── Signal defaults (shared; individual iters may override) ───────────────────────────
HORIZONS = (21, 42, 84, 168)  # 7d / 14d / 28d / 56d in 8h candles
VOL_WIN = 84  # 28d realized-vol window for inverse-vol sizing
PORT_VOL_WIN = 84  # portfolio vol-target lookback


def load_metals(data_dir: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Load the 4 metals into {ticker: DataFrame} indexed by open_time (ms), OHLCV columns.

    Fixed universe (no liquidity filter). Missing files are skipped with a note so a
    partial run still works. De-dups + sorts each frame defensively.
    """
    base = Path(data_dir) if data_dir is not None else _ROOT / "data"
    coins: dict[str, pd.DataFrame] = {}
    for sym in UNIVERSE:
        p = base / sym / "8h.csv"
        if not p.exists():
            print(f"  ! {sym}: missing {p} — skipped")
            continue
        k = pd.read_csv(p, usecols=["open_time", "open", "high", "low", "close", "volume"])
        k = k.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
        coins[sym] = k
    return coins


def panels(coins: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Build aligned float panels (DatetimeIndex) + the leak-safe forward open-to-open return.

    Returns dict with keys open/high/low/close/ret_fwd (all columns = tickers). NaN where an
    asset has no candle (ragged start / holiday) — never forward-filled (no fabrication).
    ret_fwd[t] = open[t+1]/open[t] - 1 : the return earned by a position decided at close[t].
    """
    cols = list(coins)
    opens = pd.DataFrame({s: coins[s]["open"] for s in cols}).astype(float).sort_index()
    out = {"open": opens}
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
    """The per-candle vol-target SCALAR (past-only): TARGET_VOL / trailing-vol, capped at MAX_LEV.

    Factored out so the live layer can reconstruct DEPLOYED weights = gross-normed-lagged-weight ×
    this scalar (the position the desk actually holds). `.shift(1)` keeps candle t's scale known at
    the close of t-1.
    """
    rv = net.rolling(PORT_VOL_WIN).std().shift(1)
    return (TARGET_VOL / rv).clip(upper=MAX_LEV).fillna(0.0)


def vol_target(net: pd.Series) -> pd.Series:
    """Scale a per-candle net-return series to ~ANNUAL_TARGET_VOL, capped at MAX_LEV."""
    return net * vol_target_scale(net)


def net_from_raw(raw: pd.DataFrame, ret_fwd: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """Leak-safe core: signed raw weights → (vol-targeted net return, deployed weight book).

    gross-normalise to 1 → LAG one candle (.shift(1)) → PnL = Σ w·ret_fwd → taker cost on
    |Δw| turnover → portfolio vol-target. Identical accounting to iter_002.build's tail.
    """
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    cost = COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    net = (pnl - cost).dropna()
    return vol_target(net), w


def deployed_from_raw(raw: pd.DataFrame, ret_fwd: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """Single-source DEPLOYED-position decomposition of a leg — mirrors `net_from_raw` EXACTLY but
    also returns the post-vol-target weight book the desk actually holds.

    `net_from_raw` returns the gross-normed *lagged* weight `w` (pre-vol-target). The position the
    desk HOLDS during candle t is `w[t] × vol_target_scale[t]`. Returns `(net, deployed_w)` with
    `net` bit-identical to `net_from_raw`'s first return, so the live layer reconstructs positions
    from the same arithmetic — no drift. (For the anchor leg the brake scalar is applied on top.)
    """
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    cost = COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    net0 = (pnl - cost).dropna()
    scale = vol_target_scale(net0)
    deployed = w.mul(scale.reindex(w.index).fillna(0.0), axis=0)
    return net0 * scale, deployed


def msharpe(net: pd.Series, lo=LO0, hi=HI1) -> float:
    """Annualised Sharpe from MONTHLY summed returns over [lo, hi) (√12 annualisation)."""
    s = net[(net.index >= lo) & (net.index < hi)]
    g = s.groupby(s.index.to_period("M")).sum()
    return g.mean() / g.std() * np.sqrt(12) if len(g) > 1 and g.std() > 0 else float("nan")


def turnover(w: pd.Series | pd.DataFrame, lo=LO0, hi=HI1) -> float:
    """Mean per-candle gross turnover Σ|Δw| over [lo, hi) — for cost-realism reporting."""
    if isinstance(w, pd.DataFrame):
        t = (w - w.shift(1)).abs().sum(axis=1)
    else:
        t = (w - w.shift(1)).abs()
    t = t[(t.index >= lo) & (t.index < hi)]
    return float(t.mean())


def maxdd(net: pd.Series) -> float:
    """Max drawdown of the compounded equity curve (negative fraction)."""
    eq = (1 + net).cumprod()
    return float((eq / eq.cummax() - 1).min())


def perf_line(label: str, net: pd.Series, *, reveal_oos: bool = False) -> str:
    """One-line IS performance summary. OOS stays hidden unless reveal_oos=True (CONFIRMATION)."""
    eq = (1 + net).cumprod()
    is_sr = msharpe(net, LO0, OOS_CUTOFF)
    parts = [
        f"  {label:16} IS_Sharpe={is_sr:+.2f}",
        f"maxDD={maxdd(net) * 100:5.1f}%",
        f"netTot={(eq.iloc[-1] - 1) * 100:+.0f}%",
    ]
    if reveal_oos:
        parts.insert(2, f"OOS_Sharpe={msharpe(net, OOS_CUTOFF, HI1):+.2f}")
    return "  ".join(parts)


def is_only(net: pd.Series) -> pd.Series:
    """Slice a net series to the IN-SAMPLE window only (guards against accidental OOS peeking)."""
    return net[net.index < OOS_CUTOFF]
