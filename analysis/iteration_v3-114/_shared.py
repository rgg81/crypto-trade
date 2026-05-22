"""iter-v3/114 LDO kill-switch gating EDA — shared IS-only loader + labeler + triggers.

The axis under test (cycle-6 menu item 4 — risk management): a per-symbol LDO
regime-conditional EXOGENOUS-trigger kill-switch. A binary off/on gate that halts
LDO position-taking when an exogenous regime indicator — computed from price data
the kill-switch does NOT itself affect — fires.

Motivation (carried from the /113 diary's "Next Iteration Ideas"):
the /113 per-symbol OOS attribution named LDO the -33.09% dominant OOS drag
(net_pnl_pct, 25.0% WR over 16 trades) — BCH (+24.97%) and TRX (+7.73%) are
OOS-positive carriers; LDO is the difference between a flat and a positive book.
LDO is also structurally the weak symbol: it carries only 0.78% of /059's IS PnL
(9 IS trades, 33.3% WR) and has been a chronically-weak OOS contributor across
the cycle. A risk primitive that surgically suppresses LDO's loss-making
position-taking — without touching BCH/TRX — directly attacks the one symbol
that costs the book.

WHY AN EXOGENOUS TRIGGER (the /054 deadlock sidestep):
  A kill-switch is a STATEFUL primitive. Per `feedback_v3_oracle_eda_validity.md`,
  ORACLE EDA on a prior trade roster is INVALID for STATEFUL gates where
  signal-emission updates persistent state — iter-v3/054's per-symbol drawdown
  brake entered a permanent deadlock (brake-ON at OOS-start -> no LDO trades ->
  no state update -> frozen forever). An ENDOGENOUS trigger (LDO PnL streak)
  has exactly that failure mode: the kill-switch's own action freezes the LDO
  trade outcomes that would update the streak counter.

  An EXOGENOUS trigger does NOT. The trigger is a function of BTC price and LDO
  *price* (realized volatility) — NOT of LDO trade outcomes. The indicator
  updates from market data every 8h candle whether or not LDO is trading. The
  gate-state transition function is therefore INDEPENDENT of the gate's own
  action: it cannot deadlock. The kill-switch is "stateful" only in the trivial
  sense that its fired/not-fired bit is a per-bar function of an exogenous
  series; there is no closed feedback loop. This is the iter-v3/022-precedented
  pattern (BTC drawdown / BTC vol z-score gate on TRX) — already implemented,
  tested, and shipped as `RiskV3Wrapper` primitive 9. iter-v3/114 RE-TARGETS
  that exact primitive from TRX to LDO. Because the trigger is exogenous, an
  ORACLE counterfactual on the /059 LDO roster IS a valid prediction tool
  (Section 2 of the brief argues this formally).

NO CHEATING — strict IS-only invariant:
  Every 8h feature/label row entering any computation has close_time <
  OOS_CUTOFF_MS = 1742774400000 (2025-03-24). The post-cutoff OOS is NEVER read
  except where this module explicitly loads the /059 OOS LDO roster for the
  OOS-trigger-coverage sanity annex (T9) — and that annex is clearly fenced and
  used ONLY to size whether the gate would have any OOS surface, NOT to tune a
  threshold. All threshold calibration is strictly IS-only.

Label faithfulness — replicates labeling.label_trades (label_mode=
"triple_barrier") exactly: ATR triple-barrier, atr_tp=2.0 / atr_sl=1.0, ATR
column natr_21_raw, 21-candle (10080-min / 8h) timeout, fee 0.1%. The label is
sign(better-of long_pnl / short_pnl). Adverse-first intra-bar tie-break (SL
before TP). The per-trade NET PnL helper additionally returns the realized
better-side net PnL percentage — this is the "candle outcome" the broad
per-candle simulation (T3-T6) uses, since the 9-trade /059 LDO roster is far
too thin to clear an 8% behavioural-inertia floor on the roster alone.

The BTC/LDO regime triggers replicate `risk_v3._build_btc_regime_lookup`
byte-faithfully (drawdown shift(1), rolling max, vol-zscore expanding) so the
EDA's counterfactual is computed on the SAME trigger series the QE's production
gate will compute. Verbatim labeler from analysis/iteration_v3-113/_shared.py;
the daily-aggregation helper is dropped (not needed for a risk axis).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 — IMMUTABLE
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")  # canonical /059 universe
TARGET = "LDOUSDT"  # the kill-switch's only target symbol

# /059 V3_FEATURE_COLUMNS — the 14-feature 8h-only anchor stack. iter-v3/114 is
# a RISK axis: the feature set is UNCHANGED (the /113 multi-frequency features
# are dropped — V3_FEATURE_COLUMNS reverts 22 -> 14). Listed here only so the
# EDA can confirm it does NOT touch features.
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

# regime trigger parameters — byte-faithful to risk_v3._build_btc_regime_lookup
DD_LOOKBACK_BARS = 90  # 30 calendar days at 8h cadence
VOL_LOOKBACK_BARS = 90  # 30 calendar days at 8h cadence


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
def _features_path(symbol: str) -> Path:
    return REPO_ROOT / "data" / "features_v3" / f"{symbol}_8h_features.parquet"


def load_symbol_8h(symbol: str, is_only: bool = True) -> pd.DataFrame:
    """Load one symbol's 8h feature parquet. IS-only filter by default.

    Returns a frame with OHLCV + close_time + open_time + the V3 feature stack
    + natr_21_raw. The IS-only assertion is enforced when is_only=True.
    """
    path = _features_path(symbol)
    if not path.exists():
        raise FileNotFoundError(f"missing v3 features parquet: {path}")
    df = pd.read_parquet(path)
    df = df.sort_values("close_time").reset_index(drop=True)
    if is_only:
        df = df.loc[df["close_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
        assert (df["close_time"] < OOS_CUTOFF_MS).all(), f"{symbol}: IS-only violated"
    return df


def load_btc_8h_csv() -> pd.DataFrame:
    """Load data/BTCUSDT/8h.csv — the source the production regime gate reads."""
    path = REPO_ROOT / "data" / "BTCUSDT" / "8h.csv"
    df = pd.read_csv(path, usecols=["open_time", "close"])
    df = df.sort_values("open_time").reset_index(drop=True)
    df["close"] = df["close"].astype(float)
    return df


def load_059_ldo_roster(window: str) -> pd.DataFrame:
    """Load the canonical /059 LDO trade roster (IS or OOS).

    window: "in_sample" or "out_of_sample". The IS roster is the ORACLE-EDA
    counterfactual base; the OOS roster is read ONLY for the T9 trigger-coverage
    sanity annex (clearly fenced — used to size OOS surface, never to tune).
    """
    path = REPO_ROOT / "reports-v3" / "iteration_v3-059" / window / "trades.csv"
    df = pd.read_csv(path)
    df = df.loc[df["symbol"] == TARGET].reset_index(drop=True)
    return df


# --------------------------------------------------------------------------
# Triple-barrier labeller — verbatim from analysis/iteration_v3-113/_shared.py
# extended to also return the realized better-side NET PnL pct ("candle outcome")
# --------------------------------------------------------------------------
def label_one_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """Triple-barrier label + realized candle-outcome PnL for every 8h candle.

    Faithful to labeling.label_trades (triple_barrier branch): forward-scan to
    the timeout candle, SL checked before TP within a bar (adverse-first),
    label = sign of the better of (long net PnL, short net PnL).

    Adds three columns:
        label          1 if long is the better side else 0 (the directional target)
        label_valid    True if the candle could be labelled
        candle_net_pnl realized NET PnL pct of the BETTER side — the per-candle
                       "if you had traded this candle in the model-favoured
                       direction, this is the outcome". Used by the broad
                       per-candle simulation (T3-T6) because the 9-trade /059
                       LDO roster is too thin for a roster-only inertia test.
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
    candle_net = np.full(n, np.nan)

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
        # realized NET pnl PCT of the better side, normalised by entry price
        better = max(long_pnl, short_pnl)
        candle_net[i] = better / entry * 100.0

    df["label"] = label
    df["label_valid"] = valid
    df["candle_net_pnl"] = candle_net
    return df


# --------------------------------------------------------------------------
# Exogenous regime triggers — byte-faithful to risk_v3._build_btc_regime_lookup
# --------------------------------------------------------------------------
def build_btc_regime_series(btc: pd.DataFrame) -> pd.DataFrame:
    """Per-bar BTC drawdown_30d (%) and vol_zscore_30d — PAST-ONLY (shift(1)).

    Byte-faithful re-implementation of risk_v3._build_btc_regime_lookup so the
    EDA counterfactual is computed on the SAME series the production gate uses.

    drawdown_pct[t] = (close[t-1] - max(close[t-90:t-1])) / max(...) * 100
                      (negative when falling)
    vol_zscore[t]   = (rollstd30[t-1] - expanding_mean) / expanding_std
                      where rollstd30 = 30-bar std of 1-period log returns and
                      the expanding window uses only past bars.
    """
    df = btc.sort_values("open_time").reset_index(drop=True).copy()
    df["log_ret"] = np.log(df["close"] / df["close"].shift(1))

    close_shifted = df["close"].shift(1)
    rolling_max = close_shifted.rolling(window=DD_LOOKBACK_BARS, min_periods=1).max()
    df["btc_drawdown_pct"] = (close_shifted - rolling_max) / rolling_max * 100.0

    logret_shifted = df["log_ret"].shift(1)
    rolling_std = logret_shifted.rolling(window=VOL_LOOKBACK_BARS, min_periods=2).std()
    expanding_mean = rolling_std.expanding(min_periods=10).mean()
    expanding_std = rolling_std.expanding(min_periods=10).std().replace(0.0, np.nan)
    df["btc_vol_zscore"] = (rolling_std - expanding_mean) / expanding_std

    return df[["open_time", "btc_drawdown_pct", "btc_vol_zscore"]]


def build_ldo_realvol_zscore(ldo_8h: pd.DataFrame) -> pd.DataFrame:
    """Per-bar LDO realized-volatility z-score — PAST-ONLY (shift(1)).

    A SECOND, LDO-native exogenous trigger candidate (the brief evaluates BTC-DD,
    BTC-vol-z, and LDO-realvol-z and picks whichever separates best on IS data).
    LDO realized vol is a function of LDO *price*, NOT LDO trade outcomes — so it
    is exogenous to the kill-switch in exactly the same deadlock-free sense as
    the BTC triggers (the kill-switch halts LDO *trading*, not LDO *price*).

    ldo_realvol_zscore[t] = (rollstd30[t-1] - expanding_mean) / expanding_std
    on LDO's own 1-period log returns. Same construction as the BTC vol z-score.
    """
    df = ldo_8h.sort_values("open_time").reset_index(drop=True).copy()
    df["log_ret"] = np.log(df["close"] / df["close"].shift(1))
    logret_shifted = df["log_ret"].shift(1)
    rolling_std = logret_shifted.rolling(window=VOL_LOOKBACK_BARS, min_periods=2).std()
    expanding_mean = rolling_std.expanding(min_periods=10).mean()
    expanding_std = rolling_std.expanding(min_periods=10).std().replace(0.0, np.nan)
    df["ldo_realvol_zscore"] = (rolling_std - expanding_mean) / expanding_std
    return df[["open_time", "ldo_realvol_zscore"]]


def asof_trigger(
    decision_open_times: np.ndarray,
    trigger_df: pd.DataFrame,
    trigger_col: str,
    key_col: str = "open_time",
) -> np.ndarray:
    """Past-only as-of join: for every decision open_time, return the trigger
    value of the most-recent trigger row with key STRICTLY LESS than the
    decision open_time.

    This is the EXACT contract of risk_v3._regime_gate_fires:
        idx = np.searchsorted(trigger_times, open_time_ms, side="left") - 1
    The trigger row at key == decision open_time is EXCLUDED (the gate cannot
    see the current bar). For an 8h symbol decision and an 8h BTC/LDO trigger
    series, decision open_time and trigger open_time coincide bar-for-bar, so
    side="left" selects the strictly-prior bar — the past-only contract.
    """
    keys = trigger_df[key_col].to_numpy(dtype=np.int64)
    vals = trigger_df[trigger_col].to_numpy(dtype=np.float64)
    out = np.full(len(decision_open_times), np.nan)
    idx = np.searchsorted(keys, decision_open_times.astype(np.int64), side="left") - 1
    ok = idx >= 0
    out[ok] = vals[idx[ok]]
    return out
