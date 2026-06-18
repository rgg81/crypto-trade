"""TOP-20 (ex-stablecoin) breadth test of the HONEST WALK-FORWARD SMA strategy — 2026-06-18.

Question (user): does the honest walk-forward SMA trend — which beat the hindsight-fixed-200 on
ETH and THETA — GENERALIZE across the top-20 coins (ex-stablecoins)?

Self-contained backtest faithful to the committed v1 deterministic core. It needs ONLY 8h klines
(the honest-walk-forward DECISION is pure price action — trend-state direction + conviction gate —
LightGBM bypassed), so it can sweep the FULL cross-track top-20 (the v1 runner excludes v2/v3
symbols). It reproduces the committed EXECUTION: fixed-horizon N=42 hold with an intrabar SL =
1.45 x NATR(entry) (atr_tp=100 is non-binding). It does NOT apply R5 vol-targeting (a per-coin risk
overlay), so it matches the committed RAW per-trade `net_pnl_pct`, NOT the R5-weighted
comparison.csv. The RAW signal is the right uniform cross-coin measure.

FAITHFULNESS (validated in __main__): with the SL on, this reproduces the committed RAW net_pnl_pct
monthly Sharpe for ETH (wf-select OOS ~+0.60) and THETA within proxy tolerance.

HONESTY / LEAK-SAFETY (the whole point):
  - Each month M, W* = argmax of the in-sample trend Sharpe over the PAST training window
    [test_start-24mo, test_start-embargo) ONLY (embargo=43 candles). The selection objective
    (close-to-close, mirroring the committed `_simulate_trend_window`) counts a trade only if BOTH
    entry and exit lie before train_end → strictly past-only.
  - Per-month conviction threshold q_thr = 0.40-quantile of |dist_atr_W*| over the training window.
  - Test signals read dist_atr_W*[t] built from close[t-1] (`.shift(1)`). No future data is read.
  - The fixed-200 arm is the BIASED reference only (a global window = the hindsight bias we reject).

Constants mirror the committed core: training_months=24, N=42, grid 50..400 step 25, q=0.40,
atr_sl=1.45, OOS_CUTOFF=2025-03-24, round-trip cost 0.14%.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

OOS_CUTOFF = pd.Timestamp("2025-03-24")
INTERVAL_MS = 8 * 60 * 60 * 1000
N_HORIZON = 42
EMBARGO_CANDLES = N_HORIZON + 1  # = compute_embargo_candles(20160, 480)
TRAINING_MONTHS = 24
GRID = list(range(50, 401, 25))
Q = 0.40
COST = 0.14 / 100.0
MIN_TRADES = 10
ATR_WIN = 14
ATR_SL = 1.45  # SL distance = ATR_SL x NATR(entry)

TOP20 = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "TRXUSDT",
    "AVAXUSDT", "LINKUSDT", "DOTUSDT", "BCHUSDT", "LTCUSDT", "MATICUSDT", "UNIUSDT", "ATOMUSDT",
    "ETCUSDT", "XLMUSDT", "NEARUSDT", "FILUSDT",
]


def load_klines(sym: str) -> pd.DataFrame | None:
    try:
        d = pd.read_csv(f"data/{sym}/8h.csv", usecols=["open_time", "high", "low", "close"])
    except (FileNotFoundError, ValueError):
        return None
    d = d.dropna(subset=["open_time", "high", "low", "close"]).drop_duplicates("open_time")
    d = d.sort_values("open_time").reset_index(drop=True)
    return d if len(d) > 0 else None


def build_grid(d: pd.DataFrame):
    ot = d["open_time"].to_numpy(dtype=np.int64)
    close = d["close"].to_numpy(dtype=np.float64)
    high = d["high"].to_numpy(dtype=np.float64)
    low = d["low"].to_numpy(dtype=np.float64)
    cp = pd.Series(close).shift(1).to_numpy()
    tr = np.maximum(high - low, np.maximum(np.abs(high - cp), np.abs(low - cp)))
    atr_lag = pd.Series(tr).rolling(ATR_WIN).mean().shift(1).to_numpy()  # past-only, for dist
    atr_now = pd.Series(tr).rolling(ATR_WIN).mean().to_numpy()  # at-entry, for SL sizing
    atr_safe = np.where(atr_lag > 0, atr_lag, np.nan)
    grid = {w: ((cp - pd.Series(close).rolling(w).mean().shift(1).to_numpy()) / atr_safe).astype(
        np.float64) for w in GRID}
    natr = np.where(close > 0, atr_now / close, np.nan)  # NATR(entry) for SL
    return ot, close, high, low, natr, grid


def sim_window_c2c(dist, close, ot, lo_ms, hi_ms, q_thr) -> np.ndarray:
    """Close-to-close in-sample trades for the SELECTION objective (mirrors committed)."""
    n = len(ot)
    i = int(np.searchsorted(ot, lo_ms, side="left"))
    i_end = int(np.searchsorted(ot, hi_ms, side="left"))
    rets = []
    while i < i_end:
        d = dist[i]
        if not np.isfinite(d) or abs(d) < q_thr:
            i += 1
            continue
        j = i + N_HORIZON
        if j >= n or ot[j] >= hi_ms:
            break
        ep, xp = close[i], close[j]
        if np.isfinite(ep) and np.isfinite(xp) and ep > 0:
            rets.append((1.0 if d > 0 else -1.0) * (xp / ep - 1.0) - COST)
        i = j + 1
    return np.array(rets, dtype=np.float64)


def thr_for(dist, ot, lo_ms, hi_ms):
    m = (ot >= lo_ms) & (ot < hi_ms)
    a = np.abs(dist[m])
    a = a[np.isfinite(a)]
    return float(np.quantile(a, Q)) if len(a) >= 50 else None


def trade_sharpe(rets) -> float:
    if len(rets) < MIN_TRADES:
        return -1e9
    sd = rets.std(ddof=1)
    return float(rets.mean() / sd) if sd > 0 else -1e9


def select_window(grid, close, ot, lo, end):
    best_w, best_s = None, -np.inf
    for w in GRID:
        q = thr_for(grid[w], ot, lo, end)
        if q is None:
            continue
        s = trade_sharpe(sim_window_c2c(grid[w], close, ot, lo, end, q))
        if s > best_s:
            best_s, best_w = s, w
    if best_w is None:
        return None
    q = thr_for(grid[best_w], ot, lo, end)
    return (best_w, q) if q is not None else None


def month_starts(ot):
    periods = pd.PeriodIndex(pd.to_datetime(ot, unit="ms"), freq="M").unique()
    return [p.to_timestamp() for p in periods]


def run_arm(grid, close, high, low, natr, ot, fixed_w):
    """Continuous walk-forward sim with fixed-horizon + 1.45xNATR intrabar SL.

    fixed_w=None → per-month SELECTION; else the (biased) fixed window.
    """
    per_month = {}
    for ms in month_starts(ot):
        ts = int(ms.value // 10**6)
        lo = int((ms - pd.DateOffset(months=TRAINING_MONTHS)).value // 10**6)
        end = ts - EMBARGO_CANDLES * INTERVAL_MS
        if fixed_w is None:
            per_month[ms.to_period("M")] = select_window(grid, close, ot, lo, end)
        else:
            q = thr_for(grid[fixed_w], ot, lo, end)
            per_month[ms.to_period("M")] = (fixed_w, q) if q is not None else None
    valid = sorted(m for m, v in per_month.items() if v is not None)
    if not valid:
        return pd.DataFrame(columns=["close_time", "ret", "win"])
    n = len(ot)
    i = int(np.searchsorted(ot, int(valid[0].to_timestamp().value // 10**6), side="left"))
    rows = []
    while i < n - 1:
        sel = per_month.get(pd.Timestamp(ot[i], unit="ms").to_period("M"))
        if sel is None:
            i += 1
            continue
        w, q = sel
        d = grid[w][i]
        ep, sl = close[i], natr[i]
        if not (np.isfinite(d) and abs(d) >= q and np.isfinite(ep) and ep > 0 and np.isfinite(sl)):
            i += 1
            continue
        direction = 1.0 if d > 0 else -1.0
        sl_frac = ATR_SL * sl
        j_max = min(i + N_HORIZON, n - 1)
        ret, exit_idx = None, j_max
        for k in range(i + 1, j_max + 1):  # intrabar SL scan
            if direction > 0 and low[k] <= ep * (1 - sl_frac):
                ret, exit_idx = -sl_frac - COST, k
                break
            if direction < 0 and high[k] >= ep * (1 + sl_frac):
                ret, exit_idx = -sl_frac - COST, k
                break
        if ret is None:  # timeout exit at close[j_max]
            xp = close[j_max]
            ret = direction * (xp / ep - 1.0) - COST if (np.isfinite(xp) and xp > 0) else None
        if ret is not None:
            rows.append((int(ot[exit_idx]), ret, w))
        i = exit_idx + 1
    return pd.DataFrame(rows, columns=["close_time", "ret", "win"])


def seg_sharpe(df, lo, hi):
    if df.empty:
        return float("nan"), 0
    x = df.copy()
    x["m"] = pd.to_datetime(x["close_time"], unit="ms").dt.to_period("M").dt.to_timestamp()
    x = x[(x["m"] >= lo) & (x["m"] < hi)]
    s = x.groupby("m")["ret"].sum()
    sh = s.mean() / s.std() * np.sqrt(12) if len(s) > 1 and s.std() > 0 else float("nan")
    return sh, len(x)


def main() -> None:
    lo0, hi1 = pd.Timestamp("2000-01-01"), pd.Timestamp("2100-01-01")
    print(f"{'coin':9s} | {'WF-SELECT IS/OOS (n)':>26s} | {'FIXED-200 IS/OOS (n)':>26s} | medW")
    print("-" * 86)
    rows = []
    for sym in TOP20:
        d = load_klines(sym)
        if d is None or len(d) < 1000:
            print(f"{sym:9s} | (insufficient klines)")
            continue
        ot, close, high, low, natr, grid = build_grid(d)
        wf = run_arm(grid, close, high, low, natr, ot, None)
        fx = run_arm(grid, close, high, low, natr, ot, 200)
        wis, nwi = seg_sharpe(wf, lo0, OOS_CUTOFF)
        woos, nwo = seg_sharpe(wf, OOS_CUTOFF, hi1)
        fis, nfi = seg_sharpe(fx, lo0, OOS_CUTOFF)
        foos, nfo = seg_sharpe(fx, OOS_CUTOFF, hi1)
        medw = int(wf["win"].median()) if not wf.empty else 0
        print(f"{sym:9s} | {wis:+6.2f}/{woos:+6.2f} ({nwi:>3}/{nwo:<3}) | "
              f"{fis:+6.2f}/{foos:+6.2f} ({nfi:>3}/{nfo:<3}) | {medw}")
        rows.append((sym, wis, woos, fis, foos))
    r = pd.DataFrame(rows, columns=["sym", "wf_is", "wf_oos", "fx_is", "fx_oos"]).dropna()
    print("-" * 86)
    print(f"coins evaluated (with OOS): {len(r)}")
    print(f"WF both-positive (IS>0 & OOS>0): {int(((r.wf_is>0)&(r.wf_oos>0)).sum())}/{len(r)}")
    print(f"WF OOS > 0:                      {int((r.wf_oos>0).sum())}/{len(r)}")
    print(f"WF OOS >= FIXED-200 OOS:         {int((r.wf_oos>=r.fx_oos).sum())}/{len(r)}")
    print(f"median WF  IS={r.wf_is.median():+.2f} OOS={r.wf_oos.median():+.2f} | "
          f"median FIX IS={r.fx_is.median():+.2f} OOS={r.fx_oos.median():+.2f}")
    print(f"mean   WF  IS={r.wf_is.mean():+.2f} OOS={r.wf_oos.mean():+.2f} | "
          f"mean   FIX IS={r.fx_is.mean():+.2f} OOS={r.fx_oos.mean():+.2f}")


if __name__ == "__main__":
    main()
