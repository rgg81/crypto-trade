"""iter-v3/113 multi-frequency feature gating EDA — shared IS-only loader + labeler.

The axis under test (cycle-6 menu item 3 — multi-frequency feature engineering):
does a representation that mixes a COARSER bar frequency (1d) into the 8h model
carry held-out directional signal that the 8h-only 14-feature stack LACKS?

Motivation (carried from the /112 diary's "Next Iteration Ideas" + /109 §3):
the /105->/109 convergent chain established that v3's 14-feature representation
on the BCH/LDO/TRX *8h* universe carries no IS-detectable directional signal to
a 100-shuffle permutation test (/109 observed feature->label AUC 0.497, p=0.64).
That null is a property of the **8h representation specifically**. A different
bar frequency is a genuinely different signal-to-noise regime the 8h null does
not reach. This EDA measures whether daily-bar (1d) features — a coarser, less
microstructure-noisy representation — add predictive signal the 8h stack lacks.

WHY DAILY (coarser) AND NOT 1h (finer):
  The 8h candles open at exactly 00/08/16 UTC — three per UTC day. A 1d bar is
  therefore an EXACT, look-ahead-free aggregation of three consecutive 8h bars;
  no new data fetch and no sub-bar alignment ambiguity. A daily feature attached
  to an 8h decision row uses ONLY the most-recently-CLOSED daily bar (a causal
  backward as-of join keyed on daily close_time <= the 8h row's open_time). The
  finer 1h direction is a real SNR regime too but (a) needs a fresh 1h fetch and
  (b) has an intra-8h-bar alignment surface; this EDA scopes the clean coarser
  case. The brief carries a 1h secondary annex for the QE only if the EDA's 1d
  result is a hard NO-GO.

NO CHEATING — strict IS-only invariant:
  Every 8h feature/label row entering any computation has close_time <
  OOS_CUTOFF_MS = 1742774400000 (2025-03-24). The daily bars are aggregated
  ONLY from IS 8h candles. The post-cutoff OOS is NEVER read.

Label faithfulness — replicates labeling.label_trades (label_mode=
"triple_barrier") exactly: ATR triple-barrier, atr_tp=2.0 / atr_sl=1.0, ATR
column natr_21_raw, 21-candle (10080-min / 8h) timeout, fee 0.1%. The label is
sign(better-of long_pnl / short_pnl) — the directional target the v3 primary
model is trained to predict. Adverse-first intra-bar tie-break (SL before TP),
exactly as the production loop short-circuits. Verbatim from
analysis/iteration_v3-112/_shared.py with the daily-aggregation helper added.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 — IMMUTABLE
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")  # canonical /059 universe

# /059 V3_FEATURE_COLUMNS — the 14-feature 8h-only anchor stack. The axis adds
# coarser-frequency features ON TOP of this; the comparison is 8h-only vs
# 8h+daily, with everything else held /059-identical.
V3_FEATURE_COLUMNS = [
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
    "regime_momentum_signed_5d",
]

# /059 triple-barrier label config (BASELINE_V3.md "Code Configuration")
ATR_TP_MULT = 2.0
ATR_SL_MULT = 1.0
ATR_COL = "natr_21_raw"
TIMEOUT_MINUTES = 10080  # 21 candles × 8h
INTERVAL_MINUTES = 480
FEE_PCT = 0.1

# 8h day-of-UTC structure: three candles open at 00/08/16. A daily bar
# aggregates the three 8h candles whose open_time falls in [day, day+1d).
MS_PER_DAY = 86_400_000


def _label_one_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """Triple-barrier label every 8h candle of one symbol's IS frame.

    Faithful to labeling.label_trades (triple_barrier branch): forward-scan to
    the timeout candle, SL checked before TP within a bar (adverse-first),
    label = sign of the better of (long net PnL, short net PnL).
    """
    df = df.sort_values("close_time").reset_index(drop=True)
    close = df["close"].to_numpy(dtype=np.float64)
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    close_time = df["close_time"].to_numpy(dtype=np.int64)
    atr = df[ATR_COL].to_numpy(dtype=np.float64)
    n = len(df)
    timeout_ms = TIMEOUT_MINUTES * 60 * 1000

    label = np.zeros(n, dtype=np.int64)
    valid = np.zeros(n, dtype=bool)

    for i in range(n):
        entry = close[i]
        if entry == 0:
            continue
        a = atr[i] if not np.isnan(atr[i]) else entry * 0.02
        tp_dist = a * ATR_TP_MULT
        sl_dist = a * ATR_SL_MULT
        deadline = close_time[i] + timeout_ms

        long_tp = entry + tp_dist
        long_sl = entry - sl_dist
        short_tp = entry - tp_dist
        short_sl = entry + sl_dist

        long_res = 0  # 1=tp -1=sl -2=timeout 0=pending
        short_res = 0
        last_close = entry
        for j in range(i + 1, n):
            if close_time[j] > deadline:
                if long_res == 0:
                    long_res = -2
                if short_res == 0:
                    short_res = -2
                break
            h_bar = high[j]
            l_bar = low[j]
            last_close = close[j]
            # adverse-first within the bar: SL before TP
            if long_res == 0:
                if l_bar <= long_sl:
                    long_res = -1
                elif h_bar >= long_tp:
                    long_res = 1
            if short_res == 0:
                if h_bar >= short_sl:
                    short_res = -1
                elif l_bar <= short_tp:
                    short_res = 1
        else:
            # ran off the end of the frame without hitting the deadline
            if long_res == 0:
                long_res = -2
            if short_res == 0:
                short_res = -2

        fee = entry * (FEE_PCT / 100.0) * 2.0
        if long_res == 1:
            long_pnl = tp_dist - fee
        elif long_res == -1:
            long_pnl = -sl_dist - fee
        else:
            long_pnl = (last_close - entry) - fee
        if short_res == 1:
            short_pnl = tp_dist - fee
        elif short_res == -1:
            short_pnl = -sl_dist - fee
        else:
            short_pnl = (entry - last_close) - fee

        label[i] = 1 if long_pnl >= short_pnl else 0
        valid[i] = True

    df["label"] = label
    df["label_valid"] = valid
    return df


def _aggregate_to_daily(df8h: pd.DataFrame) -> pd.DataFrame:
    """Aggregate one symbol's 8h OHLCV frame into 1d (daily) bars.

    The 8h candles open at 00/08/16 UTC; a daily bar groups the (up to) three
    8h candles whose open_time falls in [day_start, day_start + 1d). For each
    daily bar:
        open       = first 8h open in the day
        high       = max 8h high
        low        = min 8h low
        close      = last 8h close
        volume     = sum 8h volume
        day_open   = day_start epoch-ms
        day_close  = last 8h close_time in the day  (the CAUSAL timestamp:
                     the daily feature for any 8h decision row is only valid
                     once day_close <= that 8h row's open_time)

    Days with fewer than 3 8h candles (data gaps) are still aggregated — partial
    days are kept; they are a faithful reflection of the data the runner sees.
    """
    df = df8h.sort_values("open_time").reset_index(drop=True).copy()
    df["day_open"] = (df["open_time"] // MS_PER_DAY) * MS_PER_DAY
    grp = df.groupby("day_open", sort=True)
    daily = pd.DataFrame(
        {
            "day_open": grp["day_open"].first().to_numpy(),
            "open": grp["open"].first().to_numpy(),
            "high": grp["high"].max().to_numpy(),
            "low": grp["low"].min().to_numpy(),
            "close": grp["close"].last().to_numpy(),
            "volume": grp["volume"].sum().to_numpy(),
            "day_close": grp["close_time"].last().to_numpy(),
            "n_8h": grp.size().to_numpy(),
        }
    ).reset_index(drop=True)
    return daily


def _add_daily_features(daily: pd.DataFrame) -> pd.DataFrame:
    """Compute the candidate COARSER-frequency feature family on the daily bars.

    All features are scale-invariant and strictly past-only (every rolling
    window uses only bars at index <= t; no centered windows; no shift into the
    future). Eight candidates across three mechanism groups — the EDA scores
    them as a family and individually:

    Trend / momentum (daily):
        d_ret_5d        — 5-day log return on the daily close (a 5-bar daily
                          momentum; the 8h analogue would be a 15-bar window —
                          the daily version smooths intra-day microstructure).
        d_ret_10d       — 10-day log return on the daily close.
        d_trend_slope_10 — OLS slope of log(close) vs bar index over 10 daily
                          bars, normalized by mean log-price (a smoothed daily
                          trend-strength estimate).
    Volatility regime (daily):
        d_realvol_10    — std of 1-day log returns over 10 daily bars
                          (annualization-free; a daily-scale realized-vol).
        d_realvol_ratio — d_realvol_5 / d_realvol_20 (a daily vol-regime ratio:
                          >1 = vol expanding, <1 = vol contracting).
        d_atr_pctrank_60 — percentile rank of the daily true-range / close over
                          a 60-day window (where the current daily range sits
                          in its own recent distribution).
    Path efficiency (daily):
        d_efficiency_10 — Kaufman efficiency ratio on the daily close over 10
                          bars: |close_t - close_{t-10}| / sum(|1-day moves|).
                          Coarser-grid path-cleanliness; near 1 = clean daily
                          trend, near 0 = daily chop.
        d_close_pos_20  — where the current daily close sits in the [min,max]
                          of the last 20 daily highs/lows (a daily Williams-%R
                          analogue; scale-invariant in [0,1]).
    """
    d = daily.sort_values("day_open").reset_index(drop=True).copy()
    close = d["close"].to_numpy(dtype=np.float64)
    high = d["high"].to_numpy(dtype=np.float64)
    low = d["low"].to_numpy(dtype=np.float64)
    n = len(d)
    log_close = np.log(np.where(close > 0, close, np.nan))

    def _lag_ret(h: int) -> np.ndarray:
        out = np.full(n, np.nan)
        if n > h:
            out[h:] = log_close[h:] - log_close[:-h]
        return out

    d["d_ret_5d"] = _lag_ret(5)
    d["d_ret_10d"] = _lag_ret(10)

    # OLS slope of log_close vs index over a 10-bar trailing window
    slope = np.full(n, np.nan)
    win = 10
    x = np.arange(win, dtype=np.float64)
    x_c = x - x.mean()
    denom = np.sum(x_c**2)
    for t in range(win - 1, n):
        y = log_close[t - win + 1 : t + 1]
        if np.any(np.isnan(y)):
            continue
        y_c = y - y.mean()
        slope[t] = np.sum(x_c * y_c) / denom / (np.abs(y.mean()) + 1e-12)
    d["d_trend_slope_10"] = slope

    log_ret_1d = np.concatenate([[np.nan], np.diff(log_close)])
    rv = lambda w: pd.Series(log_ret_1d).rolling(w, min_periods=w).std().to_numpy()  # noqa: E731
    d["d_realvol_10"] = rv(10)
    rv5, rv20 = rv(5), rv(20)
    with np.errstate(divide="ignore", invalid="ignore"):
        d["d_realvol_ratio"] = np.where(rv20 > 0, rv5 / rv20, np.nan)

    # daily true-range / close, percentile-ranked over 60 bars
    prev_close = np.concatenate([[np.nan], close[:-1]])
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    with np.errstate(divide="ignore", invalid="ignore"):
        tr_norm = np.where(close > 0, tr / close, np.nan)
    d["d_atr_pctrank_60"] = (
        pd.Series(tr_norm).rolling(60, min_periods=60).apply(lambda s: s.rank(pct=True).iloc[-1])
    ).to_numpy()

    # Kaufman efficiency ratio over 10 daily bars
    eff = np.full(n, np.nan)
    abs_1d = np.abs(log_ret_1d)
    for t in range(10, n):
        net = np.abs(log_close[t] - log_close[t - 10])
        path = np.nansum(abs_1d[t - 9 : t + 1])
        if path > 0:
            eff[t] = net / path
    d["d_efficiency_10"] = eff

    # daily close position in the last-20-bar [min low, max high] channel
    roll_lo = pd.Series(low).rolling(20, min_periods=20).min().to_numpy()
    roll_hi = pd.Series(high).rolling(20, min_periods=20).max().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        d["d_close_pos_20"] = np.where(
            (roll_hi - roll_lo) > 0, (close - roll_lo) / (roll_hi - roll_lo), np.nan
        )

    return d


DAILY_FEATURES = [
    "d_ret_5d",
    "d_ret_10d",
    "d_trend_slope_10",
    "d_realvol_10",
    "d_realvol_ratio",
    "d_atr_pctrank_60",
    "d_efficiency_10",
    "d_close_pos_20",
]


def load_labeled_is(symbol: str) -> pd.DataFrame:
    """Load one symbol's IS 8h feature parquet, label it, attach daily features.

    Returns an 8h-grid frame with: the 14 /059 features, the triple-barrier
    `label`, and the 8 candidate daily features causally as-of-joined.

    The daily features are joined with merge_asof on `day_close <=
    8h.open_time` — the daily bar must be fully CLOSED strictly before the 8h
    decision candle opens. This is the causal alignment: the 8h model deciding
    at open_time t may use only daily bars whose last 8h sub-candle closed at or
    before t. (close_time of the prior 8h candle == open_time of the next, so
    `day_close <= open_time` admits the daily bar that ended on the boundary —
    correct, because that daily bar's information set is complete at t.)
    """
    pq = REPO_ROOT / "data" / "features_v3" / f"{symbol}_8h_features.parquet"
    df = pd.read_parquet(pq)
    df = df[df["close_time"] < OOS_CUTOFF_MS].copy()
    df = df.sort_values("open_time").reset_index(drop=True)
    assert (df["close_time"] < OOS_CUTOFF_MS).all(), f"{symbol}: IS-only invariant violated"

    df = _label_one_symbol(df)

    # Build daily bars from the IS 8h frame, compute the daily feature family.
    daily = _aggregate_to_daily(df)
    daily = _add_daily_features(daily)
    daily_join = daily[["day_close"] + DAILY_FEATURES].sort_values("day_close").reset_index(
        drop=True
    )

    # Causal as-of join: most-recently-CLOSED daily bar at the 8h row's open.
    df = df.sort_values("open_time").reset_index(drop=True)
    merged = pd.merge_asof(
        df,
        daily_join,
        left_on="open_time",
        right_on="day_close",
        direction="backward",
        allow_exact_matches=True,
    )
    merged["symbol"] = symbol
    return merged


def load_all_is() -> pd.DataFrame:
    """Concatenate the labeled IS frames for all three v3 symbols."""
    frames = [load_labeled_is(s) for s in SYMBOLS]
    out = pd.concat(frames, ignore_index=True)
    assert (out["close_time"] < OOS_CUTOFF_MS).all(), "assembled frame: IS-only invariant violated"
    return out
