"""Shared IS-ONLY walk-forward harness for iter-v1/015 risk-method exploration (BTCUSDT).

Reproduces the iter-009/010/011/012 let-winners-run book VERBATIM:
  - 19-col HYBRID feature set, fixed_horizon N=9 (3d) forward-return label,
  - expanding monthly walk-forward, LightGBMRegressor, sign(prediction) = direction,
  - exit = min{SL 1.45*ATR adverse, 9-candle timeout}, TP non-binding ("let winners run"),
  - 0.1% fee per trade; ATR = close * vol_natr_21 / 100.

KEY DIFFERENCE vs iter-012: the walk-forward here ALSO returns the model PREDICTION MAGNITUDE
(per-OOF-trade), not just its sign. The prediction magnitude (= forecast forward-return) is the
model's own CONVICTION proxy — the discriminator iter-015 probes. (iter-012 discarded magnitude.)

OOS-VIGILANCE (HARD): every consumer hard-filters `open_time < OOS_CUTOFF_MS` and asserts
`df["open_time"].max() < OOS_CUTOFF_MS` BEFORE any forward quantity. The harness itself never reads
OOS; it operates on whatever frame the caller passes (callers pass the IS-only frame). All trend /
vol / drawdown state is stateless past-only.
"""

from __future__ import annotations

import lightgbm as lgb
import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24
SYMBOL = "BTCUSDT"
ATR_COLUMN = "vol_natr_21"
FEE_PCT = 0.1
ATR_SL = 1.45
N_LABEL = 9
CANDLES_PER_DAY = 3.0
CANDLES_PER_YEAR = 365.25 * CANDLES_PER_DAY
EMBARGO_C = N_LABEL + 3
SEEDS = (42, 123, 456, 789, 1001)

ITER009_FEATURES: tuple[str, ...] = (
    "trend_adx_7", "vol_garman_klass_10", "vol_atr_5", "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_5", "vol_mfi_7", "mom_rsi_9", "stat_autocorr_lag1",
    "mr_pct_from_high_5", "vol_cmf_10", "ent_shannon_10", "trend_adx_14",
    "trend_supertrend_14_3", "btc_funding_spread_30_90", "funding_rate_zscore_30",
    "stat_autocorr_lag5", "vol_range_spike_72", "mr_rsi_extreme_14", "stat_kurtosis_20",
)
BASE_PARAMS = dict(
    n_estimators=300, max_depth=4, num_leaves=15, learning_rate=0.03,
    min_child_samples=80, subsample=0.8, colsample_bytree=0.8,
    reg_alpha=0.5, reg_lambda=0.5, n_jobs=4, verbose=-1,
)


def load_is_frame(parquet_path):
    df = pd.read_parquet(parquet_path)
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
    return df


def fwd_return(close, n):
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] != 0:
            out[i] = (close[i + n] - close[i]) / close[i] * 100.0
    return out


def letrun(high, low, close, atr, direction, atr_sl, timeout_c):
    """Let-winners-run book. Returns (net_pct, exit_reason_code).
    exit_reason_code: 1=stop_loss, 0=timeout, nan=no trade."""
    n = len(close)
    out = np.full(n, np.nan)
    reason = np.full(n, np.nan)
    for i in range(n):
        d = direction[i]
        if not np.isfinite(d) or d == 0 or close[i] == 0:
            continue
        entry = close[i]
        a = atr[i] if np.isfinite(atr[i]) else entry * 0.02
        end = min(i + timeout_c, n - 1)
        if end <= i:
            continue
        hit_sl = False
        if d > 0:
            sl = entry - a * atr_sl
            ex = close[end]
            for j in range(i + 1, end + 1):
                if low[j] <= sl:
                    ex = sl
                    hit_sl = True
                    break
                ex = close[j]
            raw = (ex - entry) / entry * 100.0
        else:
            sl = entry + a * atr_sl
            ex = close[end]
            for j in range(i + 1, end + 1):
                if high[j] >= sl:
                    ex = sl
                    hit_sl = True
                    break
                ex = close[j]
            raw = (entry - ex) / entry * 100.0
        out[i] = raw - FEE_PCT
        reason[i] = 1.0 if hit_sl else 0.0
    return out, reason


def letrun_tighter_sl(high, low, close, atr, direction, atr_sl, timeout_c):
    """Variant for Probe C: an arbitrary (possibly tighter) SL multiple. Same as letrun but with the
    atr_sl passed explicitly so the caller can sweep it. Identical signature/semantics to letrun."""
    return letrun(high, low, close, atr, direction, atr_sl, timeout_c)


def expanding_wf_with_margin(X, y, ot_days, valid, params, seed,
                             min_train_days=365.0, step_days=30.0):
    """Expanding monthly walk-forward (iter-012 faithful) that ALSO returns the prediction MAGNITUDE.

    Returns (direction, oof_mask, pred_value) where pred_value is the regressor's raw forecast
    forward-return for each OOF row (0 elsewhere). The conviction proxy iter-015 needs."""
    n = len(X)
    embargo_days = EMBARGO_C / CANDLES_PER_DAY
    t0 = ot_days.min()
    ts = t0 + min_train_days + embargo_days
    preds, idx = [], []
    while ts < ot_days.max():
        te = ts + step_days
        tc = ts - embargo_days
        tr = valid & (ot_days < tc) & (ot_days >= t0)
        tem = valid & (ot_days >= ts) & (ot_days < te)
        if tr.sum() >= 200 and tem.sum() > 0:
            m = lgb.LGBMRegressor(random_state=seed, **params)
            m.fit(X[tr], y[tr])
            preds.append(m.predict(X[tem]))
            idx.append(np.where(tem)[0])
        ts = te
    if not idx:
        return np.zeros(n), np.zeros(n, dtype=bool), np.zeros(n)
    p = np.concatenate(preds)
    g = np.concatenate(idx)
    d = np.zeros(n)
    d[g] = np.sign(p)
    pv = np.zeros(n)
    pv[g] = p
    oof = np.zeros(n, dtype=bool)
    oof[g] = True
    return d, oof, pv


def pooled_ann_sharpe(r_weighted, n_total, min_n=12):
    """POOLED annualized Sharpe of (size-weighted) per-trade returns — the deployment-relevant figure
    and the metric a SIZING primitive actually moves (per-sub-period Sharpe is invariant to a
    within-window multiplier — the iter-012 lesson)."""
    rr = r_weighted[np.isfinite(r_weighted)]
    if len(rr) < min_n:
        return np.nan
    mean, std = float(np.mean(rr)), float(np.std(rr, ddof=1))
    if std <= 0:
        return np.nan
    return (mean / std) * np.sqrt(len(rr) / n_total * CANDLES_PER_YEAR)


def proxy_maxdd(weighted_returns_ordered):
    """Running-sum equity max drawdown (cum-pct points) of an ordered weighted-return sequence.
    Additive book (matches the backtest weighted_pnl accounting)."""
    eq = np.cumsum(weighted_returns_ordered)
    peak = np.maximum.accumulate(eq)
    dd = peak - eq
    return float(np.max(dd)) if len(dd) else 0.0


def sub_period_label(ot_days):
    """6-month IS sub-period label (matches iter-011/012 partitioning)."""
    d = pd.to_datetime(ot_days * 86400_000, unit="ms")
    half = np.where(d.month <= 6, "01", "07")
    return np.array([f"{y}-{h}" for y, h in zip(d.year.astype(str), half)])


# The 3 deterministically-negative IS sub-periods (iter-011 §3.1; seed-stable across all 5 seeds).
NEG_SUBPERIODS = ("2022-01", "2022-07", "2025-01")
