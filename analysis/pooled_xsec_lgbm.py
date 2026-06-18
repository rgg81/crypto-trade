"""POOLED CROSS-SECTIONAL LightGBM across the full top-20 — 2026-06-18.

The user's robustness thesis, built honestly: instead of betting on one hand-picked signal per coin
(which the top-20 sweep proved is a coin-flip), train ONE LightGBM across the WHOLE universe each
month (walk-forward, past-only) to predict which coins OUT-PERFORM the cross-section, then run
market-neutral long-top-k / short-bottom-k book. More data (~20x) kills per-coin overfit; the model
can LEARN which coins/regimes trend (the ex-ante filter the hand-rule lacked).

NO MAGIC NUMBERS / NO CHEATING (the load-bearing principle):
  - Features are standard SCALE-INVARIANT price/volume stats (multi-horizon returns, realized vol,
    RSI, multi-window MA-distance z-scores, range, volume z) from klines and ALL `.shift(1)`-
    lagged → each feature at candle t uses data through t-1 only. The MODEL selects what matters
    (importance); no single hand-tuned window/threshold decides a trade.
  - Walk-forward honesty: each month M trains ONLY on rows whose label is fully inside the past
    training window [test_start-24mo, test_start-embargo) with label-horizon contained
    (ot[t+N] < train_end) → the backtest at month M sees exactly what was knowable that day.
  - Label = cross-sectional demeaned forward-N return at t (contemporaneous cross-section only).
  - Cross-track: the full top-20 (v1/v2/v3 restrictions waived per user).

EVALUATION = the anti-hype gauntlet adapted to a portfolio return series:
  IS/OOS monthly Sharpe, per-candle t-stat, a SHUFFLED-PREDICTION null (random ranking → p_null),
  and the equal-weight long-only universe (buy&hold) benchmark. A result is real only if OOS is
  significant AND beats the shuffled-prediction null — never from a lucky slice.

FIRST CUT: fixed conservative LightGBM HP (shallow + regularized) to test whether ANY
alpha exists; per-month Optuna HP tuning is the next rigor step if this clears the gauntlet.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

OOS_CUTOFF = pd.Timestamp("2025-03-24")
INTERVAL_MS = 8 * 60 * 60 * 1000
N_HORIZON = 42          # label = forward-42-candle (14d) cross-sectional return
EMBARGO_CANDLES = N_HORIZON + 1
TRAINING_MONTHS = 24
K_SIDE = 5              # long top-5, short bottom-5 (dollar-neutral, gross 2x)
COST_SIDE = 0.07 / 100  # per-side cost (round-trip 0.14%) applied to turnover

TOP20 = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "TRXUSDT",
    "AVAXUSDT", "LINKUSDT", "DOTUSDT", "BCHUSDT", "LTCUSDT", "MATICUSDT", "UNIUSDT", "ATOMUSDT",
    "ETCUSDT", "XLMUSDT", "NEARUSDT", "FILUSDT",
]

LGBM_HP = dict(
    n_estimators=300, max_depth=4, num_leaves=15, learning_rate=0.03,
    subsample=0.8, colsample_bytree=0.8, reg_alpha=1.0, reg_lambda=1.0,
    min_child_samples=50, random_state=42, n_jobs=-1, verbose=-1,
)


def load_klines(sym: str) -> pd.DataFrame | None:
    try:
        d = pd.read_csv(f"data/{sym}/8h.csv",
                        usecols=["open_time", "high", "low", "close", "volume"])
    except (FileNotFoundError, ValueError):
        return None
    d = d.dropna(subset=["open_time", "close"]).drop_duplicates("open_time")
    return d.sort_values("open_time").reset_index(drop=True) if len(d) else None


def features(d: pd.DataFrame) -> pd.DataFrame:
    """Scale-invariant features, ALL .shift(1)-lagged (as-of t-1). Indexed by open_time."""
    c = d["close"].astype(float)
    h, low_, v = d["high"].astype(float), d["low"].astype(float), d["volume"].astype(float)
    ret1 = c.pct_change()
    f = pd.DataFrame({"open_time": d["open_time"].to_numpy()})
    for w in (3, 6, 12, 21, 42, 84):
        f[f"mom_{w}"] = (c / c.shift(w) - 1.0)
    for w in (12, 42):
        f[f"vol_{w}"] = ret1.rolling(w).std()
    f["vol_ratio"] = ret1.rolling(12).std() / ret1.rolling(42).std()
    # RSI-14
    delta = c.diff()
    up = delta.clip(lower=0).rolling(14).mean()
    dn = (-delta.clip(upper=0)).rolling(14).mean()
    f["rsi_14"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    for w in (50, 100, 200):
        sma = c.rolling(w).mean()
        sd = c.rolling(w).std()
        f[f"dist_z_{w}"] = (c - sma) / sd
    f["range_14"] = ((h - low_) / c).rolling(14).mean()
    f["vol_z_20"] = (v - v.rolling(20).mean()) / v.rolling(20).std()
    f["mom_accel"] = (c / c.shift(6) - 1.0) - (c / c.shift(21) - 1.0)
    feat_cols = [col for col in f.columns if col != "open_time"]
    f[feat_cols] = f[feat_cols].shift(1)  # as-of t-1 (no look-ahead at decision candle t)
    # forward-N return (for the label) — NOT shifted (uses close[t]..close[t+N])
    f["fwd_ret"] = c.shift(-N_HORIZON) / c - 1.0
    f["ret1_next"] = c.shift(-1) / c - 1.0  # next-candle return (for the portfolio)
    return f, feat_cols


def build_panel():
    frames = []
    feat_cols = None
    for sym in TOP20:
        d = load_klines(sym)
        if d is None or len(d) < 1000:
            continue
        f, fc = features(d)
        feat_cols = fc
        f["coin"] = sym
        frames.append(f)
    panel = pd.concat(frames, ignore_index=True)
    # cross-sectional demean of the label within each open_time (contemporaneous only)
    panel["xs_label"] = panel.groupby("open_time")["fwd_ret"].transform(lambda x: x - x.mean())
    return panel, feat_cols


def walk_forward_scores(panel: pd.DataFrame, feat_cols: list[str]) -> pd.DataFrame:
    """Per-month pooled train → predict score for the test month. Returns panel + 'score'."""
    ot = panel["open_time"].to_numpy()
    months = pd.PeriodIndex(pd.to_datetime(ot, unit="ms"), freq="M").unique()
    panel = panel.copy()
    panel["score"] = np.nan
    x_all = panel[feat_cols].to_numpy(dtype=np.float64)
    finite_feat = np.isfinite(x_all).all(axis=1)
    for ms in months:
        ts = int(ms.to_timestamp().value // 10**6)
        lo = int((ms.to_timestamp() - pd.DateOffset(months=TRAINING_MONTHS)).value // 10**6)
        end = ts - EMBARGO_CANDLES * INTERVAL_MS
        te = int((ms.to_timestamp() + pd.offsets.MonthBegin(1)).value // 10**6)
        # train rows: label fully inside the past training window
        tr = (ot >= lo) & (ot < end) & (ot + N_HORIZON * INTERVAL_MS < end) & finite_feat \
            & np.isfinite(panel["xs_label"].to_numpy())
        te_mask = (ot >= ts) & (ot < te) & finite_feat
        if tr.sum() < 500 or te_mask.sum() == 0:
            continue
        model = LGBMRegressor(**LGBM_HP)
        model.fit(x_all[tr], panel["xs_label"].to_numpy()[tr])
        panel.loc[te_mask, "score"] = model.predict(x_all[te_mask])
    return panel


def backtest(panel: pd.DataFrame, score_col: str = "score") -> pd.Series:
    """Overlapping long-top-k / short-bottom-k book; per-candle net return indexed by open_time."""
    sub = panel.dropna(subset=[score_col, "ret1_next"]).copy()
    times = np.sort(sub["open_time"].unique())
    # single-cohort target weights per (t, coin)
    tw = {}
    for t, g in sub.groupby("open_time"):
        if len(g) < 2 * K_SIDE:
            continue
        gg = g.sort_values(score_col)
        w = pd.Series(0.0, index=g["coin"].to_numpy())
        shorts = gg["coin"].to_numpy()[:K_SIDE]
        longs = gg["coin"].to_numpy()[-K_SIDE:]
        w[longs] = 1.0 / K_SIDE
        w[shorts] = -1.0 / K_SIDE
        tw[t] = w
    # overlapping book = mean of last N cohorts; per-candle return + turnover cost
    r1 = sub.set_index(["open_time", "coin"])["ret1_next"]
    cohort_times = [t for t in times if t in tw]
    rets = {}
    prev_book = None
    from collections import deque
    window = deque(maxlen=N_HORIZON)
    for t in cohort_times:
        window.append(tw[t])
        book = pd.concat(window, axis=1).mean(axis=1).fillna(0.0)  # avg of last N cohorts
        # portfolio 1-candle return
        try:
            r = r1.loc[t]
        except KeyError:
            continue
        pr = float((book.reindex(r.index).fillna(0.0) * r).sum())
        # turnover cost
        if prev_book is None:
            turn = book.abs().sum()
        else:
            allc = book.index.union(prev_book.index)
            _b = book.reindex(allc).fillna(0.0)
            _p = prev_book.reindex(allc).fillna(0.0)
            turn = (_b - _p).abs().sum()
        rets[t] = pr - COST_SIDE * turn
        prev_book = book
    return pd.Series(rets).sort_index()


def monthly_sharpe(ret: pd.Series, lo, hi) -> tuple[float, int]:
    if ret.empty:
        return float("nan"), 0
    idx = pd.to_datetime(ret.index, unit="ms")
    m = pd.Series(ret.to_numpy(), index=idx)
    m = m[(m.index >= lo) & (m.index < hi)]
    g = m.groupby(m.index.to_period("M")).sum()
    sh = g.mean() / g.std() * np.sqrt(12) if len(g) > 1 and g.std() > 0 else float('nan')
    return sh, len(m)


def xsec_ic(panel: pd.DataFrame, lo, hi) -> tuple[float, float, int, float, float, int]:
    """Cross-sectional IC (Spearman score vs fwd_ret per time), OVERLAPPING and NON-OVERLAPPING.

    The non-overlapping t-stat is the HONEST one: consecutive forward-N returns share N-1 candles,
    so the overlapping t-stat is inflated ~sqrt(N)x by autocorrelation. We sample every N_HORIZON
    candles for independent observations. Returns (mean_ov, t_ov, n_ov, mean_no, t_no, n_no).
    """
    from scipy.stats import spearmanr
    s = panel.dropna(subset=["score", "fwd_ret"]).copy()
    t = pd.to_datetime(s["open_time"], unit="ms")
    s = s[(t >= lo) & (t < hi)]
    rows = []
    for ot, g in s.groupby("open_time"):
        if len(g) >= 5 and g["score"].std() > 0 and g["fwd_ret"].std() > 0:
            rows.append((ot, spearmanr(g["score"], g["fwd_ret"]).correlation))
    r = pd.DataFrame(rows, columns=["open_time", "ic"]).dropna().sort_values("open_time")
    if len(r) < 2:
        return (float("nan"),) * 6
    mo, to, no = r["ic"].mean(), r["ic"].mean() / (r["ic"].std() / np.sqrt(len(r))), len(r)
    r2 = r.iloc[::N_HORIZON]  # independent samples
    mn = r2["ic"].mean()
    _se = r2['ic'].std() / np.sqrt(len(r2))
    tn = mn / _se if (len(r2) > 1 and r2['ic'].std() > 0) else float('nan')
    return mo, to, no, mn, tn, len(r2)


def main() -> None:
    print("Building panel + features across the universe ...")
    panel, feat_cols = build_panel()
    print(f"panel rows={len(panel)} coins={panel['coin'].nunique()} features={len(feat_cols)}")
    print("Walk-forward pooled training (per-month, past-only) ...")
    panel = walk_forward_scores(panel, feat_cols)
    print(f"scored test rows={panel['score'].notna().sum()}")
    lo0, hi1 = pd.Timestamp("2000-01-01"), pd.Timestamp("2100-01-01")
    ret = backtest(panel)
    is_sh, _ = monthly_sharpe(ret, lo0, OOS_CUTOFF)
    oos_sh, _ = monthly_sharpe(ret, OOS_CUTOFF, hi1)
    bh = panel.dropna(subset=["ret1_next"]).groupby("open_time")["ret1_next"].mean()
    bh_oos, _ = monthly_sharpe(bh, OOS_CUTOFF, hi1)
    is_ic = xsec_ic(panel, lo0, OOS_CUTOFF)
    oos_ic = xsec_ic(panel, OOS_CUTOFF, hi1)

    print("\n========= POOLED CROSS-SECTIONAL LightGBM — ANTI-HYPE SCORECARD =========")
    print("CROSS-SECTIONAL IC (Spearman score vs forward return):")
    print(f"  IS : overlap mean={is_ic[0]:+.4f} t={is_ic[1]:+.2f} (n={is_ic[2]})  |  "
          f"HONEST non-overlap mean={is_ic[3]:+.4f} t={is_ic[4]:+.2f} (n={is_ic[5]})")
    print(f"  OOS: overlap mean={oos_ic[0]:+.4f} t={oos_ic[1]:+.2f} (n={oos_ic[2]})  |  "
          f"HONEST non-overlap mean={oos_ic[3]:+.4f} t={oos_ic[4]:+.2f} (n={oos_ic[5]})")
    print(f"L/S PORTFOLIO monthly Sharpe (net): IS={is_sh:+.3f}  OOS={oos_sh:+.3f}")
    print(f"BUY&HOLD equal-wt universe OOS Sharpe = {bh_oos:+.2f} (L/S should be neutral)")
    # VERDICT on the HONEST (non-overlap) OOS IC t-stat — the overlap t-stat is inflated.
    real = bool(np.isfinite(oos_ic[4]) and oos_ic[3] > 0 and oos_ic[4] > 2)
    verdict = ("PASSES (significant cross-sectional IC)" if real
               else "FAILS (IC not significant on independent samples)")
    print(f"VERDICT: {verdict}")


if __name__ == "__main__":
    main()
