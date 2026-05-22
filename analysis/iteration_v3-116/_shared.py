"""iter-v3/116 — regime-conditioned exit-barrier architecture — gating EDA shared module.

THE AXIS UNDER TEST (cycle-6 EXPLORATION slot #7 — a TRADE-CONSTRUCTION / EXIT-LAYER axis):
A **regime-conditioned asymmetric exit barrier**. The v3-canonical triple-barrier
(`labeling.py`, `label_mode="triple_barrier"`) resolves every trade through a STATIC
+2.0 / -1.0 ATR barrier — the (tp_mult, sl_mult) pair is the SAME on every entry candle.
iter-v3/116 makes that pair a function of the ENTRY-BAR REGIME STATE: the entry candle
is bucketed by a regime variable (Hurst-100 regime indicator OR realized-vol z-score),
and each bucket gets its own (tp_mult, sl_mult). The directional LABEL ESTIMAND is
UNCHANGED — it stays the triple-barrier "which side wins under barrier execution"; only
the barrier GEOMETRY becomes state-dependent. Label and execution stay consistent BY
CONSTRUCTION because the runner derives BOTH the training label AND the live Signal exit
from the same per-entry multiplier (the same property /073's per-symbol axis used).

WHY THIS IS NOT A CLOSED / DEAD PATH — the dead-path adjacency confronted head-on:

  iter-v3/065  global SL widening 1.0 -> 1.5. REJECTED + reverted at /070. A GLOBAL knob
               — one constant for every candle in every regime. /116 conditions per
               entry-bar regime; the global knob is the degenerate 1-bucket case.

  iter-v3/042  global ATR tightening (1.5, 0.75). NEGATIVE. Again a GLOBAL knob.

  iter-v3/073  PER-SYMBOL triple-barrier asymmetry — `V3_ATR_MULTIPLIERS_PER_SYMBOL`
               populated with one (tp,sl) pair PER SYMBOL. SUSPICIOUS-OOS-DOMINANT,
               closed at catalog level. The conditioning variable was SYMBOL IDENTITY
               — a static label fixed for the symbol's whole history. /116 conditions on
               a DYNAMIC per-trade STATE variable (the entry-bar regime) that varies
               candle-to-candle within each symbol. Symbol identity != regime state.

  iter-v3/107  exit-layer re-architecture — 5 candidate exits (ATR-trailing stop,
               breakeven stop, ...). NULL-AT-EDA: every candidate LOWERED IS Sharpe.
               All 5 were STATIC re-architectures — the exit rule was the same function
               on every trade. A REGIME-CONDITIONED (state-dependent) barrier was NOT
               among the 5; the /107 NULL was specifically about static re-designs.

  ADX axis     CLOSED (`feedback_adx_axis_asymmetric_v3.md`). /116 does NOT use ADX as a
               feature OR a conditioning variable — the conditioning variables are
               Hurst-100 and the realized-vol z-score, both already /059 features.

  The genuinely-distinct degree of freedom is the CONDITIONING: does the OPTIMAL barrier
  geometry materially DIFFER across regime buckets? If every bucket wants the same 2:1,
  regime-conditioning is parameters with no signal and the /073 SUSPICIOUS pattern would
  recur. If buckets want materially different geometries AND a conditioned schedule beats
  static 2:1 walk-forward-faithfully, the axis is GO. The EDA below answers exactly that.

THE DECISIVE EDA GATE:
  This EDA re-resolves the existing /059 IS trade-candle outcomes under candidate barrier
  geometries directly on the 8h OHLCV path — no model retrain, no backtest. A barrier
  change only changes how a trade RESOLVES, never the entry or the model. So the EDA
  holds every IS entry fixed (symbol, direction, entry candle) and walks the path under
  candidate (tp,sl) pairs. This is the same /107/115 counterfactual machinery.

  g1  Regime buckets are non-degenerate and the per-bucket OPTIMAL barrier geometry
      MATERIALLY DIFFERS across buckets (else the axis is a no-op global knob).
  g2  A regime-CONDITIONED barrier schedule (per-bucket optimum) beats the static 2:1
      on the walk-forward-faithful per-symbol monthly Sharpe on >= 2/3 symbols, AND
      does not regress the worst symbol below a pre-set floor.
  g3  The conditioned-schedule advantage is ROBUST — it survives a regime-shuffle
      placebo (assign each entry a RANDOM bucket; the conditioned schedule must NOT
      beat static under shuffled buckets) and it survives a coarse out-of-fold check
      (the per-bucket optimum picked on IS-fold-A still helps on IS-fold-B).

PRE-REGISTERED GO RULE (synthesis script):
  GO  iff  g1 AND g2 AND g3.
  Per THE PRIME DIRECTIVE the EDA NEVER terminates the iteration — a NO-GO sharpens the
  brief's pre-registered failure mode and the backtest still runs. The GO/NO-GO verdict
  only sets the brief's modal prediction and the Section-7/8 pre-registration.

NO CHEATING — strict IS-only invariant:
  Every feature/label row entering any computation in THIS module has
  close_time < OOS_CUTOFF_MS = 1742774400000 (2025-03-24). The post-cutoff OOS is NEVER
  read by any script in analysis/iteration_v3-116/. There is NO OOS annex.
  The regime-bucket boundaries are chosen on IS-only quantiles; the per-bucket optimal
  multipliers are chosen on IS-only candle outcomes. Both are auditable: the bucket-edge
  table (T1) and the per-bucket grid table (T2) are committed BEFORE the synthesis runs,
  and every script asserts the IS-only filter.

Triple-barrier resolver — replicates labeling.label_trades(label_mode="triple_barrier")
exactly: ATR triple-barrier, ATR column natr_21_raw converted to a price distance via
`atr_price = close * natr_pct / 100` (the lgbm.py:_load_atr_for_master convention — the
SAME ATR-scale correction iter-v3/115's _shared.py applied), 21-candle (10080-min / 8h)
timeout, fee 0.1%, adverse-first (SL before TP) intra-bar tie-break. The resolver here is
PARAMETRIC in (tp_mult, sl_mult) so the EDA can sweep barrier geometries.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 — IMMUTABLE
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")  # canonical /059 universe

# /059 V3_FEATURE_COLUMNS — the 14-feature 8h-only anchor stack. iter-v3/116 is an
# EXIT-LAYER axis: the feature set is UNCHANGED. Listed so the EDA can confirm it and so
# the conditioning variables (hurst_100, a realvol z-score derived from
# range_realized_vol_50) are drawn from features already in the /059 stack.
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
ATR_TP_MULT = 2.0  # the STATIC /059 anchor TP multiplier
ATR_SL_MULT = 1.0  # the STATIC /059 anchor SL multiplier
ATR_COL = "natr_21_raw"
TIMEOUT_MINUTES = 10080  # 21 candles x 8h
INTERVAL_MINUTES = 480
TIMEOUT_CANDLES = TIMEOUT_MINUTES // INTERVAL_MINUTES  # = 21
FEE_PCT = 0.1

# walk-forward fidelity (feedback_v3_eda_walkforward_faithful.md): the runner trains on a
# 24-month expanding window and tests one calendar month at a time. The EDA's
# counterfactual monthly Sharpe is measured on the runner-faithful IS month grid.
WF_TRAIN_MONTHS = 24  # training_months — IMMUTABLE


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
def _features_path(symbol: str) -> Path:
    return REPO_ROOT / "data" / "features_v3" / f"{symbol}_8h_features.parquet"


def load_symbol_8h(symbol: str, is_only: bool = True) -> pd.DataFrame:
    """Load one symbol's 8h feature parquet. IS-only filter by default."""
    path = _features_path(symbol)
    if not path.exists():
        raise FileNotFoundError(f"missing v3 features parquet: {path}")
    df = pd.read_parquet(path)
    df = df.sort_values("close_time").reset_index(drop=True)
    if is_only:
        df = df.loc[df["close_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
        assert (df["close_time"] < OOS_CUTOFF_MS).all(), f"{symbol}: IS-only violated"
    return df


# --------------------------------------------------------------------------
# Parametric triple-barrier resolver — faithful to labeling.label_trades
# (triple_barrier branch) but PARAMETRIC in (tp_mult, sl_mult) so the EDA can sweep.
#
# Returns, per entry candle:
#   tb_label        1 if long is the better side else 0 (the directional target)
#   tb_outcome_pct  realized NET PnL pct of the BETTER (model-favoured) side
#   tb_long_pnl_pct realized NET PnL pct of going LONG
#   tb_short_pnl_pct realized NET PnL pct of going SHORT
#   tb_exit_reason  "tp"/"sl"/"timeout" for the better side
#
# Holds the entry fixed and walks the OHLCV path; SL checked before TP within a bar
# (adverse-first), label = sign of better-of(long net PnL, short net PnL).
# --------------------------------------------------------------------------
def resolve_triple_barrier(
    df: pd.DataFrame,
    tp_mult: float,
    sl_mult: float,
) -> pd.DataFrame:
    """Resolve every candle's triple-barrier outcome under a GIVEN (tp_mult, sl_mult).

    Faithful to labeling.label_trades (triple_barrier branch) and to
    analysis/iteration_v3-115/_shared.label_triple_barrier — the only change is the
    multipliers are parameters, not the hardcoded 2.0/1.0.
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
    outcome = np.full(n, np.nan)
    exit_reason = np.array(["none"] * n, dtype=object)
    long_pnl_arr = np.full(n, np.nan)
    short_pnl_arr = np.full(n, np.nan)

    for i in range(n):
        entry = close[i]
        if entry == 0:
            continue
        # natr_21_raw is a NATR PERCENTAGE — convert to a PRICE distance exactly as
        # lgbm.py:_load_atr_for_master does: atr_price = close * natr_pct / 100.
        # Fallback (NaN NATR) = 2% of price, matching labeling.label_trades line 330.
        if not np.isnan(atr[i]):
            a = entry * atr[i] / 100.0
        else:
            a = entry * 0.02
        tp_dist = a * tp_mult
        sl_dist = a * sl_mult
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

        long_pnl_arr[i] = long_pnl / entry * 100.0
        short_pnl_arr[i] = short_pnl / entry * 100.0
        if long_pnl >= short_pnl:
            label[i] = 1
            better_pnl = long_pnl
            res = long_res
        else:
            label[i] = 0
            better_pnl = short_pnl
            res = short_res
        valid[i] = True
        outcome[i] = better_pnl / entry * 100.0
        exit_reason[i] = {1: "tp", -1: "sl", -2: "timeout"}[res]

    out = df.copy()
    out["tb_label"] = label
    out["tb_valid"] = valid
    out["tb_outcome_pct"] = outcome
    out["tb_exit_reason"] = exit_reason
    out["tb_long_pnl_pct"] = long_pnl_arr
    out["tb_short_pnl_pct"] = short_pnl_arr
    return out


# --------------------------------------------------------------------------
# Directed outcome under a fixed direction
# --------------------------------------------------------------------------
def directed_outcome(resolved: pd.DataFrame, direction: np.ndarray) -> np.ndarray:
    """Net PnL pct under a SUPPLIED direction sequence (1=long, 0/-1=short).

    `resolved` is the output of resolve_triple_barrier. `direction` is an int array
    aligned to `resolved` rows. Returns the long-side PnL where direction==1, the
    short-side PnL elsewhere. Used to compare the SAME direction sequence (the /059
    model's calls, proxied by the static-barrier label) under different barrier
    geometries — a zero-foresight execution-geometry comparison.
    """
    long_pnl = resolved["tb_long_pnl_pct"].to_numpy(dtype=np.float64)
    short_pnl = resolved["tb_short_pnl_pct"].to_numpy(dtype=np.float64)
    is_long = np.asarray(direction) == 1
    return np.where(is_long, long_pnl, short_pnl)


# --------------------------------------------------------------------------
# monthly Sharpe of a per-candle outcome series — the v3 convention
# (verbatim from analysis/iteration_v3-115/horizon_exit_gating_eda._monthly_sharpe)
# --------------------------------------------------------------------------
def monthly_sharpe(outcome_pct: np.ndarray, open_time: np.ndarray) -> float:
    """Monthly Sharpe of a per-candle outcome series (annualization-free, v3 convention).

    Groups candle outcomes by calendar month, sums per month, then Sharpe = mean / std of
    the monthly sums. Mirrors the runner's monthly-Sharpe headline at the candle level.
    """
    m = np.isfinite(outcome_pct)
    if m.sum() < 12:
        return np.nan
    o = outcome_pct[m]
    t = open_time[m]
    months = pd.to_datetime(t, unit="ms", utc=True).tz_localize(None).to_period("M")
    s = pd.Series(o).groupby(months).sum()
    if len(s) < 6 or s.std(ddof=1) == 0:
        return np.nan
    return float(s.mean() / s.std(ddof=1))


# --------------------------------------------------------------------------
# Regime bucketing
# --------------------------------------------------------------------------
def realvol_zscore(df: pd.DataFrame, lookback: int = 50) -> np.ndarray:
    """Past-only rolling z-score of range_realized_vol_50.

    The z-score is computed with a `.shift(1)` so the entry candle's own realized-vol is
    EXCLUDED from its own mean/std — strictly past-only, look-ahead-clean. This is a
    DERIVED conditioning variable; `range_realized_vol_50` itself is a /059 feature.
    """
    rv = df["range_realized_vol_50"].astype(float)
    past = rv.shift(1)
    mu = past.rolling(lookback, min_periods=lookback // 2).mean()
    sd = past.rolling(lookback, min_periods=lookback // 2).std(ddof=1)
    z = (rv - mu) / sd
    return z.to_numpy(dtype=np.float64)


def bucket_by_quantile(
    values: np.ndarray, edges: list[float]
) -> np.ndarray:
    """Assign each value to a bucket index given quantile EDGE values (not probabilities).

    `edges` is the list of interior boundary values (e.g. [q33, q67] -> 3 buckets).
    NaN values -> bucket -1 (excluded). Bucket k contains values in (edges[k-1], edges[k]].
    """
    out = np.full(len(values), -1, dtype=np.int64)
    finite = np.isfinite(values)
    # np.digitize: bucket index = number of edges strictly below the value
    idx = np.digitize(values[finite], edges, right=True)
    out[finite] = idx
    return out
