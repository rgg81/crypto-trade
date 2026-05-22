"""iter-v3/115 — coherent horizon-exit labeling gating EDA — shared IS-only loaders + labelers.

THE AXIS UNDER TEST (cycle-6 EXPLORATION slot #6 — a NEW labeling architecture):
A coherent **horizon-exit (fixed-horizon)** labeling architecture. The v3-canonical
label (`labeling.py:label_trades`, `label_mode="triple_barrier"`) labels each candle by
"did the trade hit the +2 ATR TP before the -1 ATR SL or the 21-candle timeout" — and
the backtest EXECUTION matches: a trade exits at the first of TP / SL / timeout. That
label-execution consistency is load-bearing (iter-v3/072 proved it). The horizon-exit
architecture trains the model on a DIFFERENT estimand — "is the N-candle forward return
positive" — AND changes execution to match: every trade exits at the fixed N-candle
horizon, the SL and TP barriers made effectively non-binding. label and execution stay
consistent BY CONSTRUCTION, just on a time-exit geometry instead of a price-barrier one.

WHY THIS IS NOT iter-v3/072 (and why /072's Critic Rec 1 mandates exactly this brief):
  iter-v3/072 swapped ONLY the label (`label_mode="fixed_horizon"`) and left the
  TP/SL barrier EXECUTION untouched. Result: EXPLORATION-NEGATIVE (IS -0.31 / OOS -0.66).
  The /072 diary root-cause (Section 3): "label-execution mismatch — the fixed-horizon
  label trains M1 to predict the 21-candle forward return sign, but the backtest STILL
  exits at TP/SL barriers. A trade can have positive 21-candle forward return YET hit SL
  on candle 3." The /072 Critic Recommendation 1 (diary Section 8): "A coherent
  fixed-horizon design needs BOTH a fixed-horizon label AND fixed-horizon execution exit
  — a 2-axis change requiring its own brief. Do NOT re-test fixed-horizon-label-only at a
  different horizon." iter-v3/115 IS that brief — it pairs the fixed-horizon label with
  fixed-horizon EXECUTION. The /072 NEGATIVE does not constrain it; /072 closed
  "label-execution decoupled", not "horizon-exit-coherent".

WHY THIS IS NOT /017 / /108 (meta-labeling) or /099 (abstention) or /105 (trend-scan):
  /017 + /108 meta-labeling = a SECONDARY take/skip model on the EXISTING primary roster;
  /108 conclusively proved that route dead (held-out AUC 0.56, permutation p=0.18).
  /099 = a 3-class abstention label (NO-GO at EDA, edge-free class AUC 0.548).
  /105 = a trend-scanning label (per-bar OLS-slope sign) — NEGATIVE, and crucially it too
  was a label-only change executed through the unchanged triple-barrier geometry; the /105
  diary's own meta-finding names that label-vs-execution geometry mismatch as the failure.
  iter-v3/115 is the FIRST v3 axis to change the PRIMARY model's estimand AND make the
  execution geometry consistent with it. It is genuinely structural and genuinely un-spent.

THE DECISIVE EDA GATE (per the /072 Critic Recommendation 3, verbatim):
  "Future labeling-axis EDAs MUST include a label-vs-execution-consistency diagnostic
  (fraction of bars where the candidate label agrees with the barrier-first-hit outcome
  the backtest realizes) BEFORE proposing the axis. Reframe disagreement-with-execution as
  a falsifier, not a feature."
  This EDA's headline test (T2) is exactly that — but with the polarity that makes it a
  GO test for a COHERENT design: under horizon-exit EXECUTION, the realized trade outcome
  IS the N-candle forward return, so the horizon-exit label is execution-consistent by
  construction (T2 confirms ~100% label==outcome agreement, the structural sanity check).
  The substantive GO question is whether the horizon-exit GEOMETRY itself produces a
  better IS trade book than the triple-barrier geometry — T3 (the counterfactual book
  comparison) and T4 (feature->label IC) answer it.

NO CHEATING — strict IS-only invariant:
  Every feature/label row entering any computation in THIS module has
  close_time < OOS_CUTOFF_MS = 1742774400000 (2025-03-24). The post-cutoff OOS is NEVER
  read by any script in analysis/iteration_v3-115/. There is NO OOS annex — this is a
  labeling-architecture axis, not a per-symbol gate-threshold axis, so there is no scalar
  threshold to fence and no OOS-coverage annex to commit. The horizon N is NOT tuned: it
  is FIXED at 21 candles (the v3-canonical triple-barrier timeout) by design, so the
  embargo (22 candles) and REQUIRED_GAP (66) stay byte-identical — the same fixed-N
  discipline iter-v3/072 used. See the brief Section 3.5 / Section 10.

Triple-barrier labeler — replicates labeling.label_trades(label_mode="triple_barrier")
exactly: ATR triple-barrier, atr_tp=2.0 / atr_sl=1.0, ATR column natr_21_raw, 21-candle
(10080-min / 8h) timeout, fee 0.1%, adverse-first (SL before TP) intra-bar tie-break.
The horizon-exit labeler replicates labeling.label_trades(label_mode="fixed_horizon"):
no barriers scanned, the forward scan runs to the N-th forward candle, the label is the
sign of the realized N-candle net return, the realized outcome is that same N-candle
net return.

ATR-SCALE CORRECTION vs the /114 EDA _shared.py: `natr_21_raw` is a NATR PERCENTAGE
(median ~3-5). The production v3 labeler converts it to a PRICE distance the same way
`lgbm.py:_load_atr_for_master` does — `atr_price = close * natr / 100` — before passing
it to `labeling.label_trades` as `atr_values`. The /114 EDA labeler used the raw NATR
percentage AS a price distance directly; for LDO/TRX (close ~$0.09-$1.9) that inflates
the barrier 100-6000x, making every candle time out. THIS module applies the correct
`atr_price = close * natr_pct / 100` conversion (label_triple_barrier below) so the
barrier mix matches production. This is a real bug fix; the /114 axis did not depend on
the barrier mix being right, so the bug was latent there.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 — IMMUTABLE
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")  # canonical /059 universe

# /059 V3_FEATURE_COLUMNS — the 14-feature 8h-only anchor stack. iter-v3/115 is a
# LABELING axis: the feature set is UNCHANGED. Listed here so the EDA can confirm it.
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
TIMEOUT_MINUTES = 10080  # 21 candles x 8h
INTERVAL_MINUTES = 480
TIMEOUT_CANDLES = TIMEOUT_MINUTES // INTERVAL_MINUTES  # = 21
FEE_PCT = 0.1

# horizon-exit config — N is FIXED at the v3-canonical 21-candle timeout (NOT tuned;
# see module docstring + brief Section 10). This is the SAME fixed-N discipline /072
# used so the embargo (22) and REQUIRED_GAP (66) stay byte-identical.
HORIZON_CANDLES = TIMEOUT_CANDLES  # = 21

# walk-forward fidelity (feedback_v3_eda_walkforward_faithful.md): the IS feature->label
# IC is measured on the runner's expanding monthly walk-forward, not the full panel.
WF_TRAIN_MONTHS = 24  # training_months — IMMUTABLE
WF_IS_FOLDS = 6  # last 6 one-month IS folds (the /099 EDA convention)


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
# Triple-barrier labeler — verbatim from analysis/iteration_v3-114/_shared.py.
# Returns the directional label + realized better-side NET PnL pct (the triple-barrier
# "candle outcome": the realized PnL if you had traded this candle in the model-favoured
# direction under TP/SL/timeout EXECUTION).
# --------------------------------------------------------------------------
def label_triple_barrier(df: pd.DataFrame) -> pd.DataFrame:
    """Triple-barrier label + realized barrier-execution candle outcome.

    Faithful to labeling.label_trades (triple_barrier branch): forward-scan to the
    timeout candle, SL checked before TP within a bar (adverse-first), label = sign of
    the better of (long net PnL, short net PnL).

    Adds columns:
        tb_label        1 if long is the better side else 0 (the directional target)
        tb_valid        True if the candle could be labelled (>=1 forward bar)
        tb_outcome_pct  realized NET PnL pct of the BETTER side under barrier EXECUTION
        tb_exit_reason  "tp" / "sl" / "timeout" for the better (model-favoured) side
        tb_long_pnl_pct  realized NET PnL pct of going LONG under barrier EXECUTION
        tb_short_pnl_pct realized NET PnL pct of going SHORT under barrier EXECUTION
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

    df["tb_label"] = label
    df["tb_valid"] = valid
    df["tb_outcome_pct"] = outcome
    df["tb_exit_reason"] = exit_reason
    df["tb_long_pnl_pct"] = long_pnl_arr
    df["tb_short_pnl_pct"] = short_pnl_arr
    return df


# --------------------------------------------------------------------------
# Horizon-exit labeler — replicates labeling.label_trades(label_mode="fixed_horizon").
# No barriers. The forward scan runs to the N-th forward candle. The label is the sign
# of the realized N-candle net return; the realized outcome IS that N-candle net return
# (because under horizon-exit EXECUTION the trade is held to candle N regardless).
# --------------------------------------------------------------------------
def label_horizon_exit(df: pd.DataFrame, horizon: int = HORIZON_CANDLES) -> pd.DataFrame:
    """Horizon-exit label + realized horizon-execution candle outcome.

    Faithful to labeling.label_trades (fixed_horizon branch): no TP/SL scan; the trade is
    held to the N-th forward candle. long_pnl = N-candle forward return - fee;
    short_pnl = -(N-candle forward return) - fee; label = 1 if long_pnl >= short_pnl.

    Under horizon-exit EXECUTION the realized trade outcome IS the better-side N-candle
    net return — so the label and the execution are consistent BY CONSTRUCTION (this is
    exactly the property iter-v3/072 broke and the /072 Critic Rec 1 said a coherent
    design must restore).

    Adds columns:
        hz_label        1 if long is the better side else 0
        hz_valid        True if >= `horizon` forward bars exist
        hz_outcome_pct  realized NET PnL pct of the better side under horizon EXECUTION
        hz_long_pnl_pct  realized NET PnL pct of going LONG, held to candle N
        hz_short_pnl_pct realized NET PnL pct of going SHORT, held to candle N
    """
    df = df.sort_values("close_time").reset_index(drop=True)
    close = df["close"].to_numpy(dtype=np.float64)
    n = len(df)

    label = np.zeros(n, dtype=np.int64)
    valid = np.zeros(n, dtype=bool)
    outcome = np.full(n, np.nan)
    long_pnl_arr = np.full(n, np.nan)
    short_pnl_arr = np.full(n, np.nan)

    for i in range(n):
        entry = close[i]
        j = i + horizon
        if entry == 0 or j >= n:
            continue
        exit_close = close[j]
        fwd_ret_pct = (exit_close - entry) / entry * 100.0
        fee_pct_rt = FEE_PCT * 2.0  # round-trip fee in pct terms
        long_pnl = fwd_ret_pct - fee_pct_rt
        short_pnl = -fwd_ret_pct - fee_pct_rt
        long_pnl_arr[i] = long_pnl
        short_pnl_arr[i] = short_pnl
        if long_pnl >= short_pnl:
            label[i] = 1
            better = long_pnl
        else:
            label[i] = 0
            better = short_pnl
        valid[i] = True
        outcome[i] = better
    df["hz_label"] = label
    df["hz_valid"] = valid
    df["hz_outcome_pct"] = outcome
    df["hz_long_pnl_pct"] = long_pnl_arr
    df["hz_short_pnl_pct"] = short_pnl_arr
    return df


# --------------------------------------------------------------------------
# walk-forward folding — the runner's expanding monthly walk-forward
# --------------------------------------------------------------------------
def _month_floor_ms(ts_ms: int) -> int:
    dt = pd.Timestamp(ts_ms, unit="ms", tz="UTC")
    return int(pd.Timestamp(year=dt.year, month=dt.month, day=1, tz="UTC").value // 1_000_000)


def is_month_starts(df: pd.DataFrame, n_folds: int = WF_IS_FOLDS) -> list[int]:
    """Return the open_time-ms month-start boundaries of the last `n_folds` IS months.

    The runner trains on a 24-month expanding window and tests one calendar month at a
    time. The EDA's feature->label IC is measured on the last `n_folds` IS test months so
    it is faithful to the runner's walk-forward, not the full panel
    (feedback_v3_eda_walkforward_faithful.md).
    """
    ot = df["open_time"].to_numpy(dtype=np.int64)
    months = sorted({_month_floor_ms(int(t)) for t in ot})
    return months[-n_folds:] if len(months) >= n_folds else months


def spearman_ic(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation — pure numpy, NaN-safe."""
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 8:
        return np.nan
    xr = pd.Series(x[m]).rank().to_numpy()
    yr = pd.Series(y[m]).rank().to_numpy()
    if np.std(xr) == 0 or np.std(yr) == 0:
        return np.nan
    return float(np.corrcoef(xr, yr)[0, 1])
