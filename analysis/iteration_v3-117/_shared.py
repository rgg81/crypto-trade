"""iter-v3/117 — multi-offset 24h derived-series gating EDA (cycle-6 EXPLORATION #8).

The axis under test (per `feedback_v3_candle_frequency_unblocked.md`, user
directive 2026-05-20):
    Does aggregating the existing 8h candle stream into a 24h decision grid
    (with the 3-offset multi-offset derived-series technique, offsets 0h / 8h /
    16h UTC) produce a feature->label representation that carries HELD-OUT
    directional signal that the /109-/116 8h representation LACKS — on the
    canonical BCH/LDO/TRX universe, with a faithful 24h-scaled triple-barrier
    directional label?

Motivation
----------
- /105->/109 chain: terminal finding "the 14-feature representation on the
  BCH/LDO/TRX 8h universe carries no IS-detectable directional signal". Per
  `feedback_v3_candle_frequency_unblocked.md`, this null was explicitly
  scoped to the 8h bar frequency.
- /113 (multi-frequency feature engineering): the 8h+daily POOLED stack did
  NOT clear its 100-shuffle null (T4 AUC 0.5015, p=0.39). The
  daily-ONLY POOLED stack DID clear (T5 AUC 0.5275, p=0.00) -- direct prior
  evidence that the daily-frequency representation carries signal the 8h
  cannot exploit, when /113 was constrained to attach daily features TO an
  8h decision grid. iter-v3/117 changes the decision grid itself to 24h.
- iter-v3/110-/116: cycle 6's six EXPLORATION-NEGATIVEs (universe x2,
  pooled-architecture, multi-frequency-features-on-8h, risk-management,
  labeling-architecture) and the /116 PROMISING-MECHANICAL (an EXIT-LAYER
  primitive on top of the /059 signal, NOT new signal) empirically
  reconfirmed the binding constraint sits at the 8h representation.

Multi-offset derivation (the user's 2026-05-20 technique)
---------------------------------------------------------
The 8h candles open at exactly 00, 08, 16 UTC -- three candles per UTC day.
A 24h bar derived at offset `o in {0, 8, 16}` (hours into the day) is the
aggregation of the three consecutive 8h candles whose open_time falls in
[D + o, D + o + 24h).

  Offset 0h:  covers 00:00 -> 24:00 UTC (= UTC calendar day; 3 sub-bars at
              00/08/16). day_close = end of the 16:00-bar = 23:59:59.999.
  Offset 8h:  covers 08:00 -> 32:00 UTC (= D+1 08:00). 3 sub-bars at 08/16
              of day D + 00 of day D+1. day_close = end of D+1 00:00-bar
              = D+1 07:59:59.999.
  Offset 16h: covers 16:00 -> 40:00 UTC (= D+1 16:00). 3 sub-bars at 16 of
              day D + 00/08 of day D+1. day_close = end of D+1 08:00-bar
              = D+1 15:59:59.999.

Each offset produces its own independent strictly-past-only daily time
series. The 3 series have DISJOINT day_close timestamps offset by 8h from
each other -- the offset-0h series closes at 24:00, offset-8h at 08:00 of
the next day, offset-16h at 16:00 of the next day.

CAUSAL CORRECTNESS (the look-ahead-free assertion):
    For any 24h decision row in offset O at day-window-close time t_close,
    the OHLCV aggregation uses ONLY 8h candles with close_time <= t_close.
    The 3 sub-bars per 24h row are the 3 consecutive 8h candles whose
    open_time lies in [t_close - 24h, t_close). No future bar peek; no
    cross-offset peek; the offset 0h, 8h, 16h series do not look at each
    other.

Pooled-offset training (architectural choice)
---------------------------------------------
Each symbol gets ONE LightGBM model trained on the CONCATENATED 3-offset
panel for that symbol (with an `offset_id in {0, 8, 16}` categorical column
in the feature stack). Rationale:
- Data efficiency: 3x training rows per model (~4500 daily rows per symbol
  IS vs ~1500 for a per-offset-only model). Closes the data-count gap vs
  the 8h baseline (~5500 rows).
- Architectural parsimony: 1 model per symbol -- mirrors the /059
  per-symbol pattern (NOT a /112-pooled-across-symbols regression).
- Single Optuna fit surface -- fewer overfit surfaces per symbol-month.
- Label-leakage between offsets at fold boundaries handled by the
  walk-forward time embargo (REQUIRED_GAP becomes 22 * 3 = 66 daily-bar
  gap, identical formula to /113 but applied at the daily timescale).

Feature set
-----------
The /059 14-feature stack RECOMPUTED on the 24h daily bars. Each feature's
underlying lookback window is preserved in BAR units, so a feature that
was 50 bars (= 50 * 8h = 16.67 days at 8h) becomes 50 daily bars (= 50
days at 24h) -- a structurally COARSER smoothing. We DO NOT scale the
lookback windows down to "preserve calendar-time equivalence"; the whole
point of the axis is to test whether the daily REPRESENTATION (with its
natural bar-unit lookbacks) carries signal the 8h cannot reach. Bar-unit
lookbacks at 24h sample DIFFERENT calendar-time horizons than the 8h
versions -- that is the experimental signal.

Label
-----
Triple-barrier, /059-faithful AT THE 24H DECISION GRID under
calendar-time-equivalent scaling. atr_tp = 2.0, atr_sl = 1.0, fee = 0.1%.
Timeout = 7 daily bars = 7 days (calendar-time-equivalent to /059's
21 x 8h = 168h = 7 days at 8h). BAR-count scaling (21 daily bars = 21
days) was REJECTED on a pre-registered EDA finding: at 21 daily bars the
+2 ATR target dominates the -1 ATR stop in the 3x-longer calendar window,
collapsing BCH label-positive rate to 99.13% (T6) -- not a labelling fix,
a representation artifact. Calendar-time-equivalent scaling is the
hand-chosen design choice that preserves /059's barrier-asymmetry
geometry at the new bar grid (declared hand-chosen per
feedback_v3_brief_parameter_provenance.md).

ATR column: natr_21_raw is computed directly on the 24h bars (no read of
the existing 8h features parquet -- the EDA is fully self-contained on
raw OHLCV CSV).

NO CHEATING -- strict IS-only invariant
---------------------------------------
Every 8h feature/label row entering any computation has close_time <
OOS_CUTOFF_MS = 1742774400000 (2025-03-24). The 24h bars are aggregated
ONLY from IS 8h candles. The post-cutoff OOS is NEVER read.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 -- IMMUTABLE
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")  # canonical /059 universe

# /059 V3_FEATURE_COLUMNS -- the 14-feature anchor stack (RECOMPUTED at 24h).
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

# Triple-barrier label config.
# ATR multipliers unchanged from /059 (2.0 / 1.0); timeout scaled to
# calendar-time-equivalent (7 daily bars = 7 days = /059's 168h horizon).
# The BAR-count-equivalent scaling (21 daily bars = 21 days) collapses
# BCH label-positive rate to 99.13% -- artifact of barrier asymmetry at
# 3x longer calendar horizon (T6_label_balance_BAR_COUNT_EQUIV.csv).
ATR_TP_MULT = 2.0
ATR_SL_MULT = 1.0
ATR_COL = "natr_21_raw"
TIMEOUT_BARS = 7  # 7 daily bars (= 7 days = /059's calendar-time horizon)
FEE_PCT = 0.1

# 8h -> 24h aggregation constants
MS_PER_HOUR = 3_600_000
MS_PER_DAY = 86_400_000
MS_PER_8H = 8 * MS_PER_HOUR

OFFSETS_H = (0, 8, 16)  # the 3 offset starts (hours into day)


# -----------------------------------------------------------------------------
# 8h CSV loader -- IS-only fence at load time
# -----------------------------------------------------------------------------

def load_8h_is(symbol: str) -> pd.DataFrame:
    """Load one symbol's 8h CSV, IS-only fence applied at load time.

    Returns columns: open_time, open, high, low, close, volume, close_time.
    Asserts close_time < OOS_CUTOFF_MS for every row.
    """
    csv_path = REPO_ROOT / "data" / symbol / "8h.csv"
    df = pd.read_csv(csv_path)
    df = df[df["close_time"] < OOS_CUTOFF_MS].copy()
    df = df.sort_values("open_time").reset_index(drop=True)
    # Defensive assertion
    if (df["close_time"] >= OOS_CUTOFF_MS).any():
        raise RuntimeError(f"IS fence breached for {symbol}")
    cols_keep = ["open_time", "open", "high", "low", "close", "volume", "close_time"]
    return df[cols_keep].astype(
        {
            "open_time": "int64",
            "close_time": "int64",
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "float64",
        }
    )


# -----------------------------------------------------------------------------
# Multi-offset 24h aggregation
# -----------------------------------------------------------------------------

def aggregate_to_24h(df8h: pd.DataFrame, offset_h: int) -> pd.DataFrame:
    """Aggregate one symbol's 8h frame to a 24h series at offset `offset_h`.

    Each 24h bar groups the (up to) three consecutive 8h candles whose
    open_time falls in [D + offset_h, D + offset_h + 24h) where D is a UTC
    day boundary. Returns columns:
        bar_open_time   -- start of the 24h window (epoch ms)
        bar_close_time  -- close_time of the LAST 8h sub-bar in the window
                           (the CAUSAL timestamp -- the bar's features and
                           label are only valid once bar_close_time is in
                           the past)
        open / high / low / close / volume
        offset_h        -- the offset in hours (0, 8, 16)
        n_8h            -- number of 8h sub-bars in this 24h bar (1, 2, or 3)

    Bars with fewer than 3 sub-bars (boundary/gap days) are kept; downstream
    feature computation tolerates partial windows via min_periods.

    LOOK-AHEAD-FREE: each 24h bar's bar_close_time is the close_time of the
    most-recent 8h candle entering its aggregation -- by construction, every
    sub-bar's close_time <= bar_close_time, and the bar's OHLCV depends on
    no candle after it. The 3 offset series are computed INDEPENDENTLY of
    each other -- the offset-0 aggregation never reads offset-8 bars.
    """
    if offset_h not in OFFSETS_H:
        raise ValueError(f"offset_h must be one of {OFFSETS_H}")
    df = df8h.sort_values("open_time").reset_index(drop=True).copy()
    offset_ms = offset_h * MS_PER_HOUR
    # Bucket each 8h candle into a 24h window whose start = D + offset_h.
    # bucket_id = floor((open_time - offset_ms) / MS_PER_DAY) * MS_PER_DAY + offset_ms
    shifted = df["open_time"].to_numpy(dtype="int64") - offset_ms
    bucket = (shifted // MS_PER_DAY) * MS_PER_DAY + offset_ms
    df["bar_open_time"] = bucket
    grp = df.groupby("bar_open_time", sort=True)
    bars = pd.DataFrame(
        {
            "bar_open_time": grp["bar_open_time"].first().to_numpy(),
            "open": grp["open"].first().to_numpy(),
            "high": grp["high"].max().to_numpy(),
            "low": grp["low"].min().to_numpy(),
            "close": grp["close"].last().to_numpy(),
            "volume": grp["volume"].sum().to_numpy(),
            "bar_close_time": grp["close_time"].last().to_numpy(),
            "n_8h": grp.size().to_numpy(),
        }
    ).reset_index(drop=True)
    bars["offset_h"] = offset_h
    # Defensive: bar_close_time MUST be > bar_open_time and within 24h of it.
    delta = bars["bar_close_time"] - bars["bar_open_time"]
    if (delta <= 0).any():
        raise RuntimeError(f"bar_close_time <= bar_open_time for offset_h={offset_h}")
    if (delta > MS_PER_DAY).any():
        raise RuntimeError(
            f"bar_close_time > bar_open_time + 24h for offset_h={offset_h} (suggests aggregation bug)"
        )
    return bars


def build_multi_offset_24h(symbol: str) -> pd.DataFrame:
    """Build the offset-concatenated 24h panel for one symbol (IS-only).

    Loads the 8h CSV, builds the 3 offset series (0/8/16h), concatenates them
    along the row axis, and SORTS by bar_close_time. The resulting frame is
    the per-symbol training/labelling panel for the pooled-offset model.
    """
    df8h = load_8h_is(symbol)
    parts = []
    for off in OFFSETS_H:
        bars = aggregate_to_24h(df8h, off)
        parts.append(bars)
    panel = pd.concat(parts, axis=0, ignore_index=True)
    panel = panel.sort_values("bar_close_time").reset_index(drop=True)
    return panel


# -----------------------------------------------------------------------------
# 14-feature stack computed on 24h bars (per-offset-isolated)
# -----------------------------------------------------------------------------

def _compute_natr_21(df: pd.DataFrame) -> np.ndarray:
    """natr_21_raw on 24h bars -- 21-bar TR / close mean."""
    high = df["high"].to_numpy(dtype="float64")
    low = df["low"].to_numpy(dtype="float64")
    close = df["close"].to_numpy(dtype="float64")
    prev_close = np.concatenate([[np.nan], close[:-1]])
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    atr = pd.Series(tr).rolling(21, min_periods=21).mean().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        natr = np.where(close > 0, atr / close, np.nan)
    return natr


def _ema(x: np.ndarray, span: int) -> np.ndarray:
    return pd.Series(x).ewm(span=span, adjust=False, min_periods=span).mean().to_numpy()


def _hurst_window(x: np.ndarray, w: int) -> np.ndarray:
    """Rescaled-range Hurst exponent on a rolling window of log-returns.

    Past-only: out[t] uses x[t-w+1 .. t]. NaN where insufficient history or
    when the R/S statistic is degenerate.
    """
    n = len(x)
    out = np.full(n, np.nan)
    if n < w + 1:
        return out
    log_x = np.log(np.where(x > 0, x, np.nan))
    log_ret = np.concatenate([[np.nan], np.diff(log_x)])
    for t in range(w, n):
        seg = log_ret[t - w + 1 : t + 1]
        if np.any(np.isnan(seg)):
            continue
        mean_seg = seg.mean()
        dev = seg - mean_seg
        cum = np.cumsum(dev)
        R = cum.max() - cum.min()
        S = seg.std(ddof=0)
        if S > 0 and R > 0:
            out[t] = np.log(R / S) / np.log(w)
    return out


def compute_features_24h(panel_one_offset: pd.DataFrame) -> pd.DataFrame:
    """Compute the /059 14-feature stack on ONE offset's 24h series.

    Critical: features are computed INDEPENDENTLY per offset (rolling windows
    over that offset's own bars only). After computing per-offset, the EDA
    re-concatenates the 3 offsets and sorts by bar_close_time.

    Two of the 14 features are cross-asset (btc_ret_14d and sym_vs_btc_ret_7d).
    For symbols == BTCUSDT (not in v3 universe) these would self-reference;
    for v3 symbols we need the matching BTCUSDT 24h series at the same offset.
    See compute_features_for_symbol() which handles the BTC cross-asset join.
    """
    d = panel_one_offset.sort_values("bar_close_time").reset_index(drop=True).copy()
    close = d["close"].to_numpy(dtype="float64")
    high = d["high"].to_numpy(dtype="float64")
    low = d["low"].to_numpy(dtype="float64")
    n = len(d)
    log_close = np.log(np.where(close > 0, close, np.nan))
    log_ret = np.concatenate([[np.nan], np.diff(log_close)])

    # natr_21_raw -- used by label
    d["natr_21_raw"] = _compute_natr_21(d)

    # max_dd_window_50: max drawdown from rolling 50-bar peak
    roll_max = pd.Series(close).rolling(50, min_periods=50).max().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        dd = np.where(roll_max > 0, (close - roll_max) / roll_max, np.nan)
    d["max_dd_window_50"] = dd  # negative or 0

    # ema_spread_atr_20: (close - ema20) / atr14
    ema20 = _ema(close, 20)
    atr14 = pd.Series(
        np.maximum(high - low, np.maximum(np.abs(high - np.concatenate([[np.nan], close[:-1]])),
                                          np.abs(low - np.concatenate([[np.nan], close[:-1]]))))
    ).rolling(14, min_periods=14).mean().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        d["ema_spread_atr_20"] = np.where(atr14 > 0, (close - ema20) / atr14, np.nan)

    # ret_kurt_50 / ret_kurt_200 / ret_skew_50 / ret_skew_200 (rolling moments
    # on log-returns).
    s_ret = pd.Series(log_ret)
    d["ret_kurt_50"] = s_ret.rolling(50, min_periods=50).kurt().to_numpy()
    d["ret_kurt_200"] = s_ret.rolling(200, min_periods=200).kurt().to_numpy()
    d["ret_skew_50"] = s_ret.rolling(50, min_periods=50).skew().to_numpy()
    d["ret_skew_200"] = s_ret.rolling(200, min_periods=200).skew().to_numpy()

    # range_realized_vol_50: rolling std of log_ret over 50 bars
    d["range_realized_vol_50"] = s_ret.rolling(50, min_periods=50).std().to_numpy()

    # hurst_100, hurst_diff_100_50 (hurst_100 - hurst_50)
    d["hurst_100"] = _hurst_window(close, 100)
    h50 = _hurst_window(close, 50)
    d["hurst_diff_100_50"] = d["hurst_100"].to_numpy() - h50

    # vwap_dev_20: (close - vwap_20) / close
    vol = d["volume"].to_numpy(dtype="float64")
    pv = close * vol
    pv20 = pd.Series(pv).rolling(20, min_periods=20).sum().to_numpy()
    v20 = pd.Series(vol).rolling(20, min_periods=20).sum().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        vwap20 = np.where(v20 > 0, pv20 / v20, np.nan)
        d["vwap_dev_20"] = np.where(close > 0, (close - vwap20) / close, np.nan)

    # ret_autocorr_lag1_50: rolling 50-bar lag-1 autocorrelation of log_ret
    def _ac_lag1(s: pd.Series) -> float:
        # corr of s[:-1] vs s[1:]
        if s.isna().any() or len(s) < 3:
            return np.nan
        a = s.iloc[:-1].to_numpy()
        b = s.iloc[1:].to_numpy()
        sa = a.std()
        sb = b.std()
        if sa == 0 or sb == 0:
            return np.nan
        return float(((a - a.mean()) * (b - b.mean())).mean() / (sa * sb))

    d["ret_autocorr_lag1_50"] = s_ret.rolling(50, min_periods=50).apply(_ac_lag1, raw=False).to_numpy()

    # regime_momentum_signed_5d: ret_5d * sign(hurst_100 - 0.5)
    # ret_5d on 24h bars = 5-bar log return.
    out_5 = np.full(n, np.nan)
    if n > 5:
        out_5[5:] = log_close[5:] - log_close[:-5]
    sign_h = np.sign(d["hurst_100"].to_numpy() - 0.5)
    d["regime_momentum_signed_5d"] = out_5 * sign_h

    return d


def add_btc_cross_features(
    symbol_panel: pd.DataFrame, btc_panel_by_offset: dict[int, pd.DataFrame]
) -> pd.DataFrame:
    """Attach btc_ret_14d and sym_vs_btc_ret_7d to a symbol's per-offset panel.

    btc_ret_14d: 14-bar log return of BTCUSDT at the SAME offset.
    sym_vs_btc_ret_7d: (sym 7-bar log return) - (btc 7-bar log return) at the
                       same offset.

    Both are computed on the same offset's BTC bars and joined by
    bar_close_time (exact equality; same offset means bars at identical
    UTC timestamps modulo any data-gap days). Past-only by construction.
    """
    d = symbol_panel.sort_values("bar_close_time").reset_index(drop=True).copy()
    offset_h = int(d["offset_h"].iloc[0])
    btc = btc_panel_by_offset[offset_h].sort_values("bar_close_time").reset_index(drop=True)
    btc_close = btc["close"].to_numpy(dtype="float64")
    btc_log = np.log(np.where(btc_close > 0, btc_close, np.nan))
    n_b = len(btc)
    btc_ret_14d = np.full(n_b, np.nan)
    btc_ret_7d = np.full(n_b, np.nan)
    if n_b > 14:
        btc_ret_14d[14:] = btc_log[14:] - btc_log[:-14]
    if n_b > 7:
        btc_ret_7d[7:] = btc_log[7:] - btc_log[:-7]
    btc_join = pd.DataFrame(
        {
            "bar_close_time": btc["bar_close_time"].to_numpy(),
            "btc_ret_14d": btc_ret_14d,
            "btc_ret_7d": btc_ret_7d,
        }
    )
    d = d.merge(btc_join, on="bar_close_time", how="left")
    sym_close = d["close"].to_numpy(dtype="float64")
    sym_log = np.log(np.where(sym_close > 0, sym_close, np.nan))
    n = len(d)
    sym_ret_7d = np.full(n, np.nan)
    if n > 7:
        sym_ret_7d[7:] = sym_log[7:] - sym_log[:-7]
    d["sym_vs_btc_ret_7d"] = sym_ret_7d - d["btc_ret_7d"].to_numpy()
    d = d.drop(columns=["btc_ret_7d"])
    return d


# -----------------------------------------------------------------------------
# Triple-barrier label on 24h bars
# -----------------------------------------------------------------------------

def label_24h_panel(df: pd.DataFrame) -> pd.DataFrame:
    """Triple-barrier label every 24h bar in one symbol-offset panel.

    Faithful to v3 labeling.label_trades (triple_barrier): forward-scan to
    the timeout candle, SL checked before TP within a bar (adverse-first),
    label = sign of the better of (long net PnL, short net PnL). Operates
    ON A SINGLE OFFSET (input must be filtered to one offset_h).

    Timeout = 21 daily BARS (NOT 21 calendar days regardless of gaps; we
    advance through the offset's bar sequence). Label is left NaN if the
    21-bar forward window runs off the panel end.
    """
    d = df.sort_values("bar_close_time").reset_index(drop=True).copy()
    close = d["close"].to_numpy(dtype="float64")
    high = d["high"].to_numpy(dtype="float64")
    low = d["low"].to_numpy(dtype="float64")
    atr = d[ATR_COL].to_numpy(dtype="float64")
    n = len(d)
    label = np.zeros(n, dtype="int64")
    valid = np.zeros(n, dtype=bool)
    for i in range(n):
        entry = close[i]
        if entry <= 0:
            continue
        a = atr[i] if not np.isnan(atr[i]) else entry * 0.02
        tp_dist = a * ATR_TP_MULT
        sl_dist = a * ATR_SL_MULT
        long_tp = entry + tp_dist
        long_sl = entry - sl_dist
        short_tp = entry - tp_dist
        short_sl = entry + sl_dist
        long_res = 0
        short_res = 0
        last_close = entry
        deadline_idx = i + TIMEOUT_BARS
        if deadline_idx >= n:
            continue
        for j in range(i + 1, deadline_idx + 1):
            h_bar = high[j]
            l_bar = low[j]
            last_close = close[j]
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
            if long_res != 0 and short_res != 0:
                break
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
    d["label"] = label
    d["label_valid"] = valid
    return d


# -----------------------------------------------------------------------------
# Top-level loader: build the labelled pooled-offset panel per symbol
# -----------------------------------------------------------------------------

def load_labeled_is(symbol: str, btc_offset_panels: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Build one symbol's IS-only, multi-offset 24h panel with features + label.

    Steps (look-ahead-free):
        1. Load 8h IS-only CSV.
        2. For each offset in (0, 8, 16): aggregate 8h -> 24h, compute
           14 features on that offset's bars (using same-offset BTC for
           cross-asset features), label with triple-barrier on that
           offset's bars.
        3. Concatenate the 3 offsets, sort by bar_close_time. Add an
           `offset_id` integer column (0, 8, 16) as the categorical
           offset feature.
        4. Drop rows where label_valid == False OR any feature is NaN.

    Returns one frame per symbol with the columns:
        bar_close_time, offset_h, offset_id, <14 features>, label,
        natr_21_raw, close, high, low, volume, open
    """
    parts = []
    for off in OFFSETS_H:
        df8h = load_8h_is(symbol)
        # Per-offset aggregation + feature compute + label.
        # Build only this offset's bars (avoid loading the multi-offset
        # frame here; we want strict per-offset isolation for features).
        bars = aggregate_to_24h(df8h, off)
        feat = compute_features_24h(bars)
        feat = add_btc_cross_features(feat, btc_offset_panels)
        labeled = label_24h_panel(feat)
        parts.append(labeled)
    panel = pd.concat(parts, axis=0, ignore_index=True)
    panel = panel.sort_values("bar_close_time").reset_index(drop=True)
    panel["offset_id"] = panel["offset_h"].astype("int64")
    # Filter to valid-label rows where all 14 features are non-NaN.
    feat_cols = list(V3_FEATURE_COLUMNS)
    keep = panel["label_valid"] & panel[feat_cols].notna().all(axis=1)
    panel = panel[keep].reset_index(drop=True)
    return panel


def build_btc_offset_panels() -> dict[int, pd.DataFrame]:
    """Build the per-offset BTCUSDT 24h panels (just close + bar_close_time).

    Used by add_btc_cross_features. Computed once and shared across symbols.
    BTCUSDT data is loaded from data/BTCUSDT/8h.csv (already cached in the
    worktree per the v1 BTC fetch -- BTCUSDT is in the v1 universe).
    """
    out: dict[int, pd.DataFrame] = {}
    df8h = load_8h_is("BTCUSDT")
    for off in OFFSETS_H:
        out[off] = aggregate_to_24h(df8h, off)
    return out


# -----------------------------------------------------------------------------
# Walk-forward fold geometry on 24h bars (IS-only)
# -----------------------------------------------------------------------------

N_FOLDS_DEFAULT = 5
EMBARGO_BARS = 22  # /059 walk-forward embargo, applied at the daily timescale


def walk_forward_folds(n: int, n_folds: int = N_FOLDS_DEFAULT) -> list[tuple[np.ndarray, np.ndarray]]:
    """Expanding-window folds with a 22-daily-bar embargo purged before test.

    Returns a list of (train_idx, test_idx).

    NOTE on multi-offset embargo: the panel is concatenated across the 3
    offsets and sorted by bar_close_time. Two rows whose offsets differ by
    8h have bar_close_time differing by ~8h -- so the per-offset 22-bar
    embargo translates to ~66 bars at the concatenated panel level (3
    offsets x 22 bars). We use 66-bar embargo at the concatenated level to
    cover cross-offset label leakage within the same offset's forward
    window. This matches the runner's REQUIRED_GAP formula
    (timeout+1) * n_symbols * n_offset_series applied AT FOLD BOUNDARY.
    """
    start = int(n * 0.40)
    test_span = n - start
    chunk = test_span // n_folds
    folds = []
    cross_offset_embargo = EMBARGO_BARS * 3  # 66 -- multi-offset gap
    for k in range(n_folds):
        test_lo = start + k * chunk
        test_hi = start + (k + 1) * chunk if k < n_folds - 1 else n
        train_hi = max(0, test_lo - cross_offset_embargo)
        train_idx = np.arange(0, train_hi)
        test_idx = np.arange(test_lo, test_hi)
        if len(train_idx) >= 200 and len(test_idx) >= 50:
            folds.append((train_idx, test_idx))
    return folds
