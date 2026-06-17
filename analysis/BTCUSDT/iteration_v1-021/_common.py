"""Shared IS-ONLY trend-state book reconstruction + stability primitives — iter-v1/021 (BTCUSDT).

This module reconstructs the DETERMINISTIC skeleton of the iter-020 MERGED book:
  - direction  = sign(close[t-1] - SMA200[t-1])            (stateless trend-state override)
  - conviction = |close[t-1] - SMA200[t-1]| / ATR14[t-1]   (signed trend strength, ATR units)
  - gate fires when conviction >= q_thr(t), q_thr = PAST-ONLY quantile of |conviction|.

It does NOT model the LightGBM timing/sizing layer (that interacts with the gate in the real
backtest); like iter-018/iter-020's committed scripts it works on the price+gate skeleton, which
is the layer the iter-021 axis modifies. Every primitive is `.shift(1)` past-only; every threshold
is selected on PAST rows only (training-window quantile, purged by N_LABEL). OOS is NEVER read.

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert BEFORE any
forward quantity; the forward N-return is computed AFTER the filter. `src/` + runner + OOS UNTOUCHED.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 — sacred
SYMBOL = "BTCUSDT"
PARQUET = f"data/features/{SYMBOL}_8h_features.parquet"

N_LABEL = 42  # 14d at 8h — iter-020 fixed_horizon
BARS_PER_YEAR = 365.0 * 3.0
SUBPERIOD_DAYS = 182.5
MIN_SUB_TRADES = 8
SMA_WIN = 200
ATR_WIN = 14
RT_COST = 0.14  # 0.1% fee + 2.0 bps/side slippage round-trip ~= 0.14%
Q_GATE = 0.40  # iter-020 MERGED conviction quantile


def load_is() -> pd.DataFrame:
    """Load the BTC feature parquet, hard-filtered to IS (open_time < OOS_CUTOFF_MS)."""
    df = pd.read_parquet(PARQUET)
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
    return df


def fwd_log_return(close: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] > 0 and close[i + n] > 0:
            out[i] = np.log(close[i + n] / close[i])
    return out


def past_only_primitives(df: pd.DataFrame):
    """Return (cp, sma, atr, dist_atr) all past-only (.shift(1)). dist_atr = signed conviction."""
    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    cp = pd.Series(close).shift(1).to_numpy()
    sma = pd.Series(close).rolling(SMA_WIN).mean().shift(1).to_numpy()
    prev_close = pd.Series(close).shift(1).to_numpy()
    tr = np.maximum(
        high - low,
        np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)),
    )
    atr = pd.Series(tr).rolling(ATR_WIN).mean().shift(1).to_numpy()
    dist_atr = (cp - sma) / np.where(atr > 0, atr, np.nan)
    return cp, sma, atr, dist_atr


def subperiod_bounds(ot_days: np.ndarray):
    t0, t1 = ot_days.min(), ot_days.max()
    edges, edge = [], t0
    while edge < t1:
        edges.append((edge, edge + SUBPERIOD_DAYS))
        edge += SUBPERIOD_DAYS
    return edges


def ann_sharpe(r: np.ndarray, tpy: float) -> float:
    r = r[np.isfinite(r)]
    if len(r) < 3 or np.std(r, ddof=1) == 0:
        return np.nan
    return float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(tpy))


def past_only_gate_threshold(dist_atr, ot_days, bounds, q):
    """PAST-ONLY conviction threshold: for each sub-period, the q-quantile of |dist_atr| over
    candles strictly before the sub-period's first row minus N_LABEL (purge). Mirrors the
    walk-forward training-window-stat convention used in the runner."""
    thr = np.full(len(dist_atr), np.nan)
    row_idx = np.arange(len(dist_atr))
    for lo, hi in bounds:
        tm = (ot_days >= lo) & (ot_days < hi)
        if tm.sum() == 0:
            continue
        first_i = int(row_idx[tm].min())
        cut = first_i - N_LABEL
        if cut < SMA_WIN + ATR_WIN:
            continue
        past = np.abs(dist_atr[:cut])
        past = past[np.isfinite(past)]
        if len(past) < 50:
            continue
        thr[row_idx[tm]] = float(np.quantile(past, q))
    return thr


def stability(pnl, fire, ot_days, bounds, tpy):
    """Per-sub-period stability fingerprint of a firing book. pnl already net of cost."""
    sh = []
    for lo, hi in bounds:
        m = (ot_days >= lo) & (ot_days < hi) & fire & np.isfinite(pnl)
        arr = pnl[m]
        sh.append(ann_sharpe(arr, tpy) if len(arr) >= MIN_SUB_TRADES else np.nan)
    s = np.array(sh, float)
    valid = s[np.isfinite(s)]
    recent_list = [v for v in reversed(s) if np.isfinite(v)]
    recent = recent_list[0] if recent_list else np.nan
    recent3 = recent_list[:3]
    allt = pnl[fire & np.isfinite(pnl)]
    return dict(
        per_sub=[round(float(x), 3) if np.isfinite(x) else np.nan for x in s],
        full=round(ann_sharpe(allt, tpy), 4) if len(allt) else np.nan,
        frac_pos=round(float(np.mean(valid > 0)), 3) if len(valid) else np.nan,
        dispersion=round(float(np.std(valid, ddof=1)), 4) if len(valid) > 1 else np.nan,
        worst=round(float(np.min(valid)), 4) if len(valid) else np.nan,
        recent=round(float(recent), 4) if np.isfinite(recent) else np.nan,
        recent3=round(float(np.mean(recent3)), 4) if recent3 else np.nan,
        n_scored=int(len(valid)),
        n_trades=int(len(allt)),
        win_rate=round(float(np.mean(allt > 0)), 4) if len(allt) else np.nan,
        mean_ret_pct=round(float(np.mean(allt) * 100.0), 4) if len(allt) else np.nan,
    )


def monthly_concentration(pnl, fire, ot_ms):
    """Max single-CALENDAR-MONTH share of the (gross, positive-sum) and net book.
    Returns (max_month_share_of_net_abs, n_months_traded, top2_share)."""
    f = fire & np.isfinite(pnl)
    if f.sum() == 0:
        return np.nan, 0, np.nan
    ts = pd.to_datetime(ot_ms[f], unit="ms")
    months = ts.to_period("M").astype(str)
    sub = pd.DataFrame({"m": months, "pnl": pnl[f]})
    by = sub.groupby("m")["pnl"].sum()
    net = by.sum()
    if abs(net) < 1e-9:
        return np.nan, int(by.shape[0]), np.nan
    # share of net carried by each month (signed contribution / total net)
    shares = (by / net).sort_values(ascending=False)
    top1 = float(shares.iloc[0])
    top2 = float(shares.iloc[:2].sum()) if shares.shape[0] >= 2 else top1
    return top1, int(by.shape[0]), top2
