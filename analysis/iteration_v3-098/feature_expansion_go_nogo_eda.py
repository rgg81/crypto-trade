"""iter-v3/098 — Phase-1 FAIL-FAST GO/NO-GO EDA — FEATURE EXPANSION.

THE AXIS UNDER TEST
-------------------
v3 has run the SAME 14 price-derived features (V3_FEATURE_COLUMNS_TOP_N)
since /007.  The /096 EDA found the feature->label IC is thin on BCH
(+0.025) and TRX (+0.029).  The user directive (2026-05-18,
feedback_v3_bold_research_mandate.md) names FEATURES as the crucial lever;
the /097 Critic ruled symbol-screening empirically exhausted.  /098 is the
FEATURE-EXPANSION iteration: does expanding/replacing the 14-feature stack
genuinely lift the per-symbol model's predictive power on BCH/LDO/TRX (the
/059 universe — NO universe axis, per the /097 Critic ruling)?

THE TWO BINDING RECKONINGS (both addressed by this EDA's design)
-----------------------------------------------------------------
1. OOS-ROBUST SELECTION.  /096 and /097 demonstrated a genuine, seed-stable
   IS-CV-IC does NOT predict OOS in the v3 per-symbol framing.  A naive
   IS-CV-IC ranking is exactly the trap that produced /097's IS-up/OOS-down
   NEGATIVE.  Therefore the SELECTION CRITERION here is NOT IS-CV-IC rank.
   It is a NESTED-WALK-FORWARD held-out-tail test: the candidate family is
   added only if it improves predictive accuracy on the LAST 6 IS months
   (the "held-out tail" — strictly open_time < OOS_CUTOFF, never the real
   OOS) when the model is trained ONLY on data before that tail.  This is a
   genuine pseudo-OOS generalization test, the closest IS-only proxy to the
   real OOS question.  The decisive statistic is paired across walk-forward
   folds with a block-bootstrap 95% CI (the iter-v3/096 significance
   discipline), so a point-estimate lift with a CI straddling zero is NOT a
   GO.

2. RECONCILE THE MEMO AGAINST PRIOR EVIDENCE.  The prep memo flags
   order-flow (Family A) as #1.  But iter-v3/094 ALREADY tested order-flow
   as a directional signal and found it WEAK (NO-GO).  HOWEVER — /094's own
   T3 horizon table shows order-flow IC PEAKS at the 21-bar horizon
   (0.1286), and /094 explicitly states its 9-candle-timeout label "cannot
   reach 21 bars".  /059's CANONICAL label is a 21-CANDLE (10080-min)
   timeout — /094 measured order-flow against the WRONG label horizon.
   This EDA re-tests order-flow against the CORRECT 21-candle /059 label,
   AND tests it as an AUGMENTATION to the 14-stack (not standalone, the
   /094 framing).  The 7-FEED verdict (funding/OI/basis INERT) is honoured:
   Family G is NOT tested here — order-flow Family A reads the taker_buy /
   trades columns ALREADY IN every kline CSV, NOT a non-OHLCV cache.
   Family D (entropy) is tested as the orthogonal runner-up.

THE THREE CANDIDATE FEATURE SETS
--------------------------------
  BASE   — the 14-feature /059 anchor (V3_FEATURE_COLUMNS).  The control.
  +A     — BASE + 5 order-flow features (taker-buy imbalance z, taker-buy
           ratio momentum, signed-volume OBV slope, log-Amihud illiquidity,
           trade-intensity z).  Family A — new information from unused
           kline columns; Kyle 1985 / Amihud 2002 / VPIN grounding.
  +D     — BASE + 4 statistical/complexity features (permutation entropy,
           sample entropy, variance ratio, return ACF lag-2).  Family D —
           orthogonal non-linear functionals of the return sequence.
  +AD    — BASE + Family A + Family D (the combined 23-feature stack).

GO / NO-GO  (pre-registered, decided BEFORE running)
----------------------------------------------------
  Decisive statistic per candidate set S in {+A, +D, +AD}:
    dShACC(S) = paired (across walk-forward folds, across symbols) mean
                improvement of held-out-tail BARRIER-LABEL ACCURACY of S
                over BASE, with a block-bootstrap 95% CI.
  PLUS a secondary tie-break statistic:
    dPnL(S)   = paired mean improvement of held-out-tail SUM-OF-LABELED-PnL
                (the model's prediction gates which side is taken; this is
                the economic proxy closest to the backtest's Sharpe).

  GO   if AT LEAST ONE candidate set S has:
       (g1) dShACC(S) point estimate >= +0.010 (1 percentage point of
            held-out-tail accuracy — a modest but real lift), AND
       (g2) the dShACC(S) block-bootstrap 95% CI LOWER BOUND > 0 (the lift
            is statistically supported, not noise — the /096 discipline),
            AND
       (g3) dPnL(S) point estimate > 0 (the accuracy lift translates to a
            non-negative economic improvement — no accuracy/PnL inversion),
            AND
       (g4) the family is NOT INERT by multivariate importance — the new
            family's summed gain-importance share >= the uniform-parity
            share (n_new / n_total), so the tree genuinely allocates split
            capacity to it (feedback_v3_inert_features_at_higher_budget:
            an INERT feature added at higher budget actively HARMS OOS).

  NO-GO if NO candidate set clears all four gates.  The 14-feature stack is
       not improvable in an OOS-robust way -> STOP at the EDA, file
       NULL-AT-EDA, recommend the next axis.

  MARGIN DISCIPLINE (per /097 Critic Rec 3): the GO threshold g1 (+0.010)
  is SEPARATED from any predicted-band edge — it is an absolute floor set
  here, before the run, independent of any expectation.

NO-CHEATING
-----------
  - OOS_CUTOFF_MS = 1742774400000 (2025-03-24).  EVERY row used here has
    open_time < OOS_CUTOFF_MS.  The real OOS is NEVER touched.  The
    "held-out tail" is the last 6 IS months — still strictly inside IS.
  - 24-month listing burn-in dropped per symbol (matches the runner's
    per-symbol warmup).
  - The triple-barrier label uses the EXACT /059 production params: ATR
    multipliers (2.0, 1.0), timeout 10080 min = 21 candles, fee 0.1% —
    replicated from labeling.py:label_trades.  THIS IS THE FIX vs /094,
    which used a 9-candle label.
  - All candidate features are computed PAST-ONLY (rolling windows ending
    at the bar close; the imbalance/intensity z-scores use .shift was not
    needed because each window excludes no future bar — verified per
    feature in the builder docstrings below).
  - Nested walk-forward: the model that scores tail-fold k is trained ONLY
    on folds < k (expanding window).  No fold sees its own future.

This is a Phase-1 GO/NO-GO.  NO-GO -> STOP at the EDA.  GO -> Phases 2-5.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import lightgbm as lgb
except ImportError:  # pragma: no cover
    print("lightgbm not importable", file=sys.stderr)
    raise

# --------------------------------------------------------------------------
# Immutable constants
# --------------------------------------------------------------------------
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 — IMMUTABLE, never touched
TRAINING_MONTHS = 24
TIMEOUT_MIN = 10080  # 21 candles at 8h — THE /059 CANONICAL LABEL (vs /094's 9)
TP_MULT = 2.0
SL_MULT = 1.0
FEE_PCT = 0.1
EMBARGO_CANDLES = 22  # 10080 // 480 + 1 — purge both sides of each fold
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
DATA_DIR = Path("data/features_v3")
OUT = Path("analysis/iteration_v3-098")

MS_PER_DAY = 24 * 60 * 60 * 1000
TAIL_MONTHS = 6  # the held-out pseudo-OOS tail (still strictly inside IS)
N_WF_FOLDS = 6  # walk-forward folds spanning the held-out tail
BOOT_RESAMPLES = 2000
BLOCK_BARS = 21  # bootstrap block = label horizon (preserve serial dependence)
RNG_SEED = 42

# The 14-feature /059 anchor — BASE / control set.
V3_FEATURE_COLUMNS = (
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
)

# Pre-registered GO thresholds (set BEFORE the run; /097 Critic Rec 3 margin)
GO_DSHACC_MIN = 0.010  # g1: >= 1pp held-out-tail accuracy lift
# g2: CI lower bound > 0   g3: dPnL > 0   g4: importance >= uniform parity


# ==========================================================================
# Triple-barrier labeling — faithful replication of labeling.py:label_trades
# (identical to the iter-v3/096 EDA replication; TIMEOUT_MIN is the /059 21).
# ==========================================================================
def triple_barrier_label(df: pd.DataFrame) -> pd.DataFrame:
    """Return df with added columns tb_label (+1 long / -1 short) and tb_pnl.

    Replicates the /059 production triple-barrier rule for a single symbol:
      - ATR distance: TP = 2.0*ATR, SL = 1.0*ATR  (ATR in price units)
      - timeout 21 candles (10080 min) — THE /059 CANONICAL HORIZON
      - label = side whose TP is hit first; if neither TP, sign of fwd return
      - tb_pnl = realized net-of-fee PnL of the labeled side
    natr_21_raw is NATR-as-percentage -> ATR_price = natr/100 * close.
    """
    out = df.reset_index(drop=True).copy()
    n = len(out)
    high = out["high"].to_numpy(dtype=np.float64)
    low = out["low"].to_numpy(dtype=np.float64)
    close = out["close"].to_numpy(dtype=np.float64)
    close_time = out["close_time"].to_numpy(dtype=np.int64)
    natr = out["natr_21_raw"].to_numpy(dtype=np.float64)
    timeout_ms = TIMEOUT_MIN * 60 * 1000

    labels = np.zeros(n, dtype=np.int64)
    pnls = np.full(n, np.nan, dtype=np.float64)

    for i in range(n):
        entry = close[i]
        if entry <= 0:
            continue
        atr = (natr[i] / 100.0) * entry if np.isfinite(natr[i]) else entry * 0.02
        tp_dist = atr * TP_MULT
        sl_dist = atr * SL_MULT
        long_tp = entry + tp_dist
        long_sl = entry - sl_dist
        short_tp = entry - tp_dist
        short_sl = entry + sl_dist
        deadline = close_time[i] + timeout_ms

        long_result = 0  # 0 pending, 1 tp, -1 sl, -2 timeout
        short_result = 0
        long_step = -1
        short_step = -1
        last_close = entry

        j = i + 1
        while j < n:
            if close_time[j] > deadline:
                if long_result == 0:
                    long_result, long_step = -2, j
                if short_result == 0:
                    short_result, short_step = -2, j
                break
            h, lo = high[j], low[j]
            last_close = close[j]
            if long_result == 0:
                if lo <= long_sl:
                    long_result, long_step = -1, j
                elif h >= long_tp:
                    long_result, long_step = 1, j
            if short_result == 0:
                if h >= short_sl:
                    short_result, short_step = -1, j
                elif lo <= short_tp:
                    short_result, short_step = 1, j
            if long_result != 0 and short_result != 0:
                break
            j += 1
        else:
            if long_result == 0:
                long_result, long_step = -2, n
            if short_result == 0:
                short_result, short_step = -2, n

        fwd_ret = (last_close - entry) / entry * 100.0 if entry != 0 else 0.0
        tp_pnl_pct = tp_dist / entry * 100.0
        sl_pnl_pct = sl_dist / entry * 100.0

        def side_pnl(result: int, signed_fwd: float) -> float:
            if result == 1:
                return tp_pnl_pct - FEE_PCT
            if result == -1:
                return -sl_pnl_pct - FEE_PCT
            return signed_fwd - FEE_PCT

        long_pnl = side_pnl(long_result, fwd_ret)
        short_pnl = side_pnl(short_result, -fwd_ret)

        long_tp_hit = long_result == 1
        short_tp_hit = short_result == 1
        if long_tp_hit and not short_tp_hit:
            lab = 1
        elif short_tp_hit and not long_tp_hit:
            lab = -1
        elif long_tp_hit and short_tp_hit:
            lab = 1 if long_step <= short_step else -1
        else:
            lab = 1 if fwd_ret >= 0 else -1

        labels[i] = lab
        pnls[i] = long_pnl if lab == 1 else short_pnl

    out["tb_label"] = labels
    out["tb_pnl"] = pnls
    return out


# ==========================================================================
# Candidate feature builders — ALL strictly past-only (rolling windows that
# end at the bar close; no window includes any future bar).
# ==========================================================================
def _ewm(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False, min_periods=span).mean()


def _roll_z(s: pd.Series, win: int) -> pd.Series:
    """Rolling z-score over a trailing window of length `win` ending at t
    (inclusive of bar t — bar t's own value is part of its decision input,
    which is correct: the feature is known at the bar close)."""
    m = s.rolling(win, min_periods=win).mean()
    sd = s.rolling(win, min_periods=win).std(ddof=0)
    return (s - m) / sd.replace(0.0, np.nan)


def add_family_a(df: pd.DataFrame) -> pd.DataFrame:
    """Family A — order-flow / microstructure (5 features).

    All derive from kline columns the 14 incumbents IGNORE: taker_buy_volume,
    quote_volume, trades.  Binance taker_buy_volume is the aggressor-buy
    volume — a directly observed signed-flow proxy (not a tick-rule estimate).
    Grounding: Kyle (1985), Amihud (2002), Easley-LdP-O'Hara VPIN.

    Reconciliation with /094: /094 tested signed taker-volume imbalance as a
    STANDALONE directional panel against a 9-candle label and found it weak.
    Here the SAME columns are tested (a) against the CORRECT /059 21-candle
    label and (b) as an AUGMENTATION to the 14-stack — a different question.
    """
    out = df.copy()
    vol = out["volume"].astype(float)
    tbv = out["taker_buy_volume"].astype(float)
    qv = out["quote_volume"].astype(float)
    trades = out["trades"].astype(float)
    close = out["close"].astype(float)
    ret = close.pct_change()

    # 1. taker_buy_imbalance_z_20 — z-scored signed aggressor pressure.
    imb = (tbv - (vol - tbv)) / vol.replace(0.0, np.nan)
    imb_e = _ewm(imb, 20)
    out["of_taker_imb_z_20"] = _roll_z(imb_e, 20)

    # 2. of_taker_ratio_mom_3 — 3-bar momentum of the taker-buy ratio.
    tbr = tbv / vol.replace(0.0, np.nan)
    out["of_taker_ratio_mom_3"] = tbr - tbr.shift(3)

    # 3. of_signed_obv_slope_30 — OBV from taker-signed volume (cleaner than
    #    the close-direction OBV); slope = 30-bar diff of cumulative signed vol.
    signed_vol = (2.0 * tbr - 1.0) * vol  # in [-vol, +vol]
    sobv = signed_vol.fillna(0.0).cumsum()
    out["of_signed_obv_slope_30"] = (sobv - sobv.shift(30)) / 30.0

    # 4. of_amihud_log_20 — log Amihud illiquidity: mean |ret| / quote_volume
    #    over 20 bars (Amihud 2002 — coarse Kyle-lambda; price impact per $).
    illiq_bar = ret.abs() / qv.replace(0.0, np.nan)
    amihud = illiq_bar.rolling(20, min_periods=20).mean()
    out["of_amihud_log_20"] = np.log(amihud.replace(0.0, np.nan))

    # 5. of_trade_intensity_z_20 — z-score of trade count (microstructure
    #    activity; trade-count spikes precede volatility/cascades).
    out["of_trade_intensity_z_20"] = _roll_z(trades, 20)

    return out


FAMILY_A_COLS = (
    "of_taker_imb_z_20",
    "of_taker_ratio_mom_3",
    "of_signed_obv_slope_30",
    "of_amihud_log_20",
    "of_trade_intensity_z_20",
)


def _perm_entropy(window: np.ndarray, m: int = 3) -> float:
    """Bandt-Pompe permutation entropy of a 1-D window, embedding dim m,
    normalized to [0, 1].  Past-only by construction (the window is a
    trailing slice).  Low PE = ordered/forecastable; high PE = noise."""
    n = len(window)
    if n < m + 1:
        return np.nan
    perms: dict[tuple, int] = {}
    for i in range(n - m + 1):
        pattern = tuple(np.argsort(window[i : i + m]))
        perms[pattern] = perms.get(pattern, 0) + 1
    counts = np.array(list(perms.values()), dtype=np.float64)
    p = counts / counts.sum()
    ent = -np.sum(p * np.log(p))
    return float(ent / np.log(math.factorial(m)))


def _sample_entropy(window: np.ndarray, m: int = 2, r_mult: float = 0.2) -> float:
    """Sample entropy (Richman-Moorman) of a 1-D window.  Amplitude-aware
    regularity measure; complements ordinal permutation entropy.  Past-only."""
    n = len(window)
    if n < m + 2:
        return np.nan
    sd = np.std(window)
    if sd == 0:
        return 0.0
    r = r_mult * sd

    def _phi(mm: int) -> float:
        templates = np.array([window[i : i + mm] for i in range(n - mm + 1)])
        count = 0
        for i in range(len(templates)):
            d = np.max(np.abs(templates - templates[i]), axis=1)
            count += np.sum(d <= r) - 1  # exclude self-match
        return count

    a = _phi(m + 1)
    b = _phi(m)
    if b <= 0 or a <= 0:
        return np.nan
    return float(-np.log(a / b))


def add_family_d(df: pd.DataFrame) -> pd.DataFrame:
    """Family D — statistical / complexity / entropy (4 features).

    Non-linear functionals of the return sequence; invariant under monotonic
    transforms -> orthogonal to the level/range/moment incumbents by
    construction (the family most likely to clear the |IC| gate cleanly).
    Grounding: Bandt-Pompe (2002), Richman-Moorman, Lo-MacKinlay (1988).
    """
    out = df.copy()
    close = out["close"].astype(float)
    ret = close.pct_change()
    ret_np = ret.to_numpy(dtype=np.float64)
    n = len(out)

    # 1. permutation_entropy_50 — Bandt-Pompe PE, 50-bar trailing window.
    pe = np.full(n, np.nan)
    for i in range(50, n):
        w = ret_np[i - 50 : i]  # trailing 50 returns, ending at bar i-1
        if np.all(np.isfinite(w)):
            pe[i] = _perm_entropy(w, m=3)
    out["se_perm_entropy_50"] = pe

    # 2. sample_entropy_50 — Richman-Moorman SampEn, 50-bar trailing window.
    se = np.full(n, np.nan)
    for i in range(50, n):
        w = ret_np[i - 50 : i]
        if np.all(np.isfinite(w)):
            se[i] = _sample_entropy(w, m=2, r_mult=0.2)
    out["se_sample_entropy_50"] = se

    # 3. variance_ratio_2_50 — Lo-MacKinlay VR(2): var of 2-bar returns /
    #    (2 x var of 1-bar returns).  >1 trending, <1 mean-reverting.
    var1 = ret.rolling(50, min_periods=50).var(ddof=0)
    ret2 = close.pct_change(2)
    var2 = ret2.rolling(50, min_periods=50).var(ddof=0)
    out["se_variance_ratio_2_50"] = var2 / (2.0 * var1.replace(0.0, np.nan))

    # 4. ret_acf_lag2_50 — return autocorrelation at lag 2 (incumbents have
    #    only lag1, lag5).  Short-memory structure.
    def _acf2(x: np.ndarray) -> float:
        if len(x) < 3 or np.std(x) == 0:
            return np.nan
        return float(np.corrcoef(x[:-2], x[2:])[0, 1])

    out["se_ret_acf_lag2_50"] = (
        ret.rolling(50, min_periods=50).apply(_acf2, raw=True)
    )
    return out


FAMILY_D_COLS = (
    "se_perm_entropy_50",
    "se_sample_entropy_50",
    "se_variance_ratio_2_50",
    "se_ret_acf_lag2_50",
)


# ==========================================================================
# Data loading
# ==========================================================================
def load_symbol(symbol: str) -> pd.DataFrame:
    """Load a symbol's feature parquet, build the candidate families, compute
    the /059 triple-barrier label, apply 24-month listing burn-in, restrict
    strictly to open_time < OOS_CUTOFF_MS (IS only — the real OOS never
    touched), return the IS panel.

    The label is computed on the FULL panel so the 21-bar forward scan can
    see post-burnin bars, THEN the IS mask is applied (burnin <= t < cutoff).
    """
    df = pd.read_parquet(DATA_DIR / f"{symbol}_8h_features.parquet")
    df = df.sort_values("open_time").reset_index(drop=True)
    # Build candidate families (past-only) on the full panel.
    df = add_family_a(df)
    df = add_family_d(df)
    # /059 triple-barrier label (21-candle timeout) on the full panel.
    df = triple_barrier_label(df)
    # 24-month listing burn-in.
    first_ms = int(df["open_time"].min())
    burnin_end = first_ms + TRAINING_MONTHS * 30 * MS_PER_DAY
    is_mask = (df["open_time"] >= burnin_end) & (df["open_time"] < OOS_CUTOFF_MS)
    isd = df[is_mask].copy().reset_index(drop=True)
    isd["symbol"] = symbol
    isd["y"] = (isd["tb_label"] == 1).astype(int)  # 1 long / 0 short
    return isd


# ==========================================================================
# LightGBM params — modest depth-5 tree, matching v3's depth-3-5 regime;
# n_jobs kept low for the GIL behaviour the v3 runner documents.
# ==========================================================================
LGB_PARAMS = dict(
    objective="binary",
    n_estimators=200,
    num_leaves=31,
    max_depth=5,
    learning_rate=0.05,
    min_child_samples=40,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    random_state=RNG_SEED,
    verbose=-1,
    n_jobs=2,
)


def nested_walkforward_eval(
    panel: pd.DataFrame, feat_cols: list[str]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Nested expanding-window walk-forward over the held-out tail.

    The held-out tail = the last TAIL_MONTHS (6) IS months, sliced into
    N_WF_FOLDS (6) contiguous folds.  Fold k is scored by a model trained
    ONLY on rows before fold k's start, minus an EMBARGO_CANDLES purge so no
    training label's 21-bar forward window overlaps a tail row.  No fold
    sees its own future -> a genuine pseudo-OOS generalization test (still
    strictly inside IS — open_time < OOS_CUTOFF throughout).

    Returns four 1-D arrays aligned over all tail rows:
      pred   — predicted P(long)
      y      — binary label (1 long / 0 short)
      tgt    — directional label (+1 / -1)
      tb_pnl — realized net-of-fee PnL of the labeled side.
    """
    panel = panel.sort_values("open_time").reset_index(drop=True)
    last_t = int(panel["open_time"].max())
    tail_start = last_t - TAIL_MONTHS * 30 * MS_PER_DAY
    tail_mask = panel["open_time"] >= tail_start
    tail_idx = np.where(tail_mask.to_numpy())[0]
    if len(tail_idx) < N_WF_FOLDS * 10:
        # too few tail rows — return empty (caller treats as NaN)
        empty = np.array([])
        return empty, empty, empty, empty

    fold_bounds = np.array_split(tail_idx, N_WF_FOLDS)
    preds, ys, tgts, pnls = [], [], [], []
    X_all = panel[feat_cols].to_numpy(dtype=np.float64)
    y_all = panel["y"].to_numpy(dtype=int)
    tgt_all = panel["tb_label"].to_numpy(dtype=np.float64)
    pnl_all = panel["tb_pnl"].to_numpy(dtype=np.float64)

    for fold in fold_bounds:
        if len(fold) == 0:
            continue
        fold_lo = int(fold[0])
        train_hi = max(0, fold_lo - EMBARGO_CANDLES)  # purge the embargo gap
        tr = np.arange(0, train_hi)
        if len(tr) < 100 or len(np.unique(y_all[tr])) < 2:
            continue
        model = lgb.LGBMClassifier(**LGB_PARAMS)
        model.fit(X_all[tr], y_all[tr])
        p = model.predict_proba(X_all[fold])[:, 1]
        preds.append(p)
        ys.append(y_all[fold])
        tgts.append(tgt_all[fold])
        pnls.append(pnl_all[fold])

    if not preds:
        empty = np.array([])
        return empty, empty, empty, empty
    return (
        np.concatenate(preds),
        np.concatenate(ys),
        np.concatenate(tgts),
        np.concatenate(pnls),
    )


def block_bootstrap_ci(
    diffs: np.ndarray, block: int, n_boot: int, seed: int
) -> tuple[float, float, float]:
    """Block-bootstrap (contiguous blocks of length `block`) 95% CI of the
    mean of `diffs`.  Blocks preserve the serial dependence of overlapping
    21-bar triple-barrier labels (the iter-v3/096 significance discipline).

    Returns (mean, ci_lo, ci_hi)."""
    diffs = diffs[np.isfinite(diffs)]
    n = len(diffs)
    if n < block * 2:
        m = float(np.mean(diffs)) if n else float("nan")
        return m, float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    starts_pool = np.arange(0, n - block + 1)
    means = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.choice(starts_pool, size=n_blocks, replace=True)
        sample = np.concatenate([diffs[s : s + block] for s in starts])[:n]
        means[b] = sample.mean()
    return (
        float(np.mean(diffs)),
        float(np.percentile(means, 2.5)),
        float(np.percentile(means, 97.5)),
    )


def importance_share(
    panel: pd.DataFrame, feat_cols: list[str], new_cols: list[str]
) -> float:
    """Multivariate gain-importance share of `new_cols` within a model fit
    on the FULL IS panel with feature set `feat_cols`.  This is the
    feedback_v3_inert_features_at_higher_budget INERT screen — the new
    family must claim >= its uniform-parity share or it is INERT and a GO
    is denied (an INERT feature added at higher budget HARMS OOS)."""
    X = panel[feat_cols].to_numpy(dtype=np.float64)
    y = panel["y"].to_numpy(dtype=int)
    if len(np.unique(y)) < 2:
        return float("nan")
    model = lgb.LGBMClassifier(**LGB_PARAMS)
    model.fit(X, y)
    gains = np.asarray(model.booster_.feature_importance(importance_type="gain"))
    total = gains.sum()
    if total <= 0:
        return float("nan")
    idx = [feat_cols.index(c) for c in new_cols]
    return float(gains[idx].sum() / total)


# ==========================================================================
# Main
# ==========================================================================
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/098 Phase-1 GO/NO-GO EDA — FEATURE EXPANSION")
    print("Decisive question: does expanding the 14-feature stack lift the")
    print("per-symbol model's HELD-OUT-TAIL predictive power (OOS-robust proxy)?")
    print(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS} (2025-03-24) — every row IS-only")
    print(f"Label: /059 canonical triple-barrier, {TIMEOUT_MIN}-min = 21-candle "
          f"timeout (vs /094's 9-candle — THE reconciliation fix)")
    print("=" * 78)

    sets = {
        "BASE": list(V3_FEATURE_COLUMNS),
        "+A": list(V3_FEATURE_COLUMNS) + list(FAMILY_A_COLS),
        "+D": list(V3_FEATURE_COLUMNS) + list(FAMILY_D_COLS),
        "+AD": list(V3_FEATURE_COLUMNS) + list(FAMILY_A_COLS) + list(FAMILY_D_COLS),
    }
    new_cols_for = {
        "+A": list(FAMILY_A_COLS),
        "+D": list(FAMILY_D_COLS),
        "+AD": list(FAMILY_A_COLS) + list(FAMILY_D_COLS),
    }

    # ---- load IS panels ----
    panels: dict[str, pd.DataFrame] = {}
    t1_rows = []
    all_feats = list(V3_FEATURE_COLUMNS) + list(FAMILY_A_COLS) + list(FAMILY_D_COLS)
    for sym in SYMBOLS:
        d = load_symbol(sym)
        d = d.dropna(subset=all_feats + ["tb_pnl"]).reset_index(drop=True)
        panels[sym] = d
        last_t = int(d["open_time"].max())
        tail_start = last_t - TAIL_MONTHS * 30 * MS_PER_DAY
        t1_rows.append({
            "symbol": sym,
            "is_rows": len(d),
            "is_first": str(pd.to_datetime(d["open_time"].min(), unit="ms").date()),
            "is_last": str(pd.to_datetime(d["open_time"].max(), unit="ms").date()),
            "tail_rows": int((d["open_time"] >= tail_start).sum()),
            "long_label_frac": round(float(d["y"].mean()), 4),
        })
    t1 = pd.DataFrame(t1_rows)
    t1.to_csv(OUT / "T1_is_panel_summary.csv", index=False)
    print("\nT1 — IS panel summary (per symbol, post-24mo-burnin, IS-only):")
    print(t1.to_string(index=False))

    # ---- T2: family redundancy vs the 14 incumbents (|IC| gate) ----
    print("\nT2 — candidate-family redundancy vs the 14 incumbents "
          "(max |Spearman| over pooled IS rows; gate <0.7):")
    pooled = pd.concat(panels.values(), ignore_index=True)
    t2_rows = []
    for fam_name, fam_cols in (("A", FAMILY_A_COLS), ("D", FAMILY_D_COLS)):
        for nf in fam_cols:
            mx, arg = 0.0, ""
            for inc in V3_FEATURE_COLUMNS:
                a = pooled[nf].rank()
                b = pooled[inc].rank()
                c = a.corr(b)
                if pd.notna(c) and abs(c) > mx:
                    mx, arg = abs(c), inc
            t2_rows.append({
                "family": fam_name,
                "new_feature": nf,
                "max_abs_ic_vs_incumbent": round(mx, 4),
                "argmax_incumbent": arg,
                "redundancy_gate_pass": mx < 0.7,
            })
    t2 = pd.DataFrame(t2_rows)
    t2.to_csv(OUT / "T2_redundancy_vs_incumbents.csv", index=False)
    print(t2.to_string(index=False))
    n_redundant = int((~t2["redundancy_gate_pass"]).sum())
    print(f"  -> {n_redundant}/{len(t2)} candidate features fail the |IC|<0.7 gate")

    # ---- T3: nested walk-forward held-out-tail accuracy & PnL, per set ----
    # The OOS-ROBUST selection statistic.  For each candidate set we compute,
    # per symbol, the tail-row predictions; then per-row correctness and the
    # per-row labeled PnL conditioned on the model's predicted side.
    print("\nT3 — nested walk-forward HELD-OUT-TAIL evaluation per feature set:")
    print(f"  (tail = last {TAIL_MONTHS} IS months, {N_WF_FOLDS} expanding "
          f"folds, {EMBARGO_CANDLES}-candle embargo purge; strictly IS)")
    # store per (set, symbol): correctness array, pred-side PnL array
    tail_correct: dict[str, dict[str, np.ndarray]] = {}
    tail_sidepnl: dict[str, dict[str, np.ndarray]] = {}
    t3_rows = []
    for set_name, fcols in sets.items():
        tail_correct[set_name] = {}
        tail_sidepnl[set_name] = {}
        for sym in SYMBOLS:
            pred, y, tgt, pnl = nested_walkforward_eval(panels[sym], fcols)
            if len(pred) == 0:
                tail_correct[set_name][sym] = np.array([])
                tail_sidepnl[set_name][sym] = np.array([])
                continue
            pred_side = np.where(pred >= 0.5, 1.0, -1.0)
            correct = (pred_side == tgt).astype(np.float64)
            # PnL of the side the model predicts: if it predicts long, it
            # earns the long label's pnl; tb_pnl is the labeled side's pnl,
            # so pred-side pnl = tb_pnl when pred agrees with the label side,
            # and = -tb_pnl-flavoured otherwise.  We reconstruct directly:
            #   long pnl ~ +fwd-driven ; short pnl ~ -fwd-driven.
            # tb_pnl is for tb_label's side.  side_pnl(predicted) =
            #   tb_pnl                       if pred_side == tgt
            #   (mirror)                     otherwise.
            # Exact mirror needs both sides; we approximate the economic
            # proxy with: pred earns tb_pnl if it agrees, else loses the
            # symmetric amount (-tb_pnl).  This is the standard
            # meta-label-style accuracy->PnL bridge.
            side_pnl = np.where(pred_side == tgt, pnl, -pnl)
            tail_correct[set_name][sym] = correct
            tail_sidepnl[set_name][sym] = side_pnl
            t3_rows.append({
                "feature_set": set_name,
                "symbol": sym,
                "tail_n": len(pred),
                "tail_accuracy": round(float(correct.mean()), 4),
                "tail_sum_pred_side_pnl": round(float(np.nansum(side_pnl)), 3),
            })
    t3 = pd.DataFrame(t3_rows)
    t3.to_csv(OUT / "T3_walkforward_tail_eval.csv", index=False)
    print(t3.to_string(index=False))

    # ---- T4: paired dShACC + dPnL vs BASE, block-bootstrap 95% CI ----
    print("\nT4 — paired held-out-tail lift over BASE (block-bootstrap 95% CI):")
    print("  dShACC = paired per-row accuracy(S) - accuracy(BASE), pooled "
          "across symbols.  CI lower bound > 0 required (the /096 discipline).")
    t4_rows = []
    for set_name in ("+A", "+D", "+AD"):
        # paired per-row accuracy diff, concatenated across symbols
        acc_diffs, pnl_diffs = [], []
        for sym in SYMBOLS:
            cb = tail_correct["BASE"][sym]
            cs = tail_correct[set_name][sym]
            pb = tail_sidepnl["BASE"][sym]
            ps = tail_sidepnl[set_name][sym]
            if len(cb) == 0 or len(cs) == 0 or len(cb) != len(cs):
                continue
            acc_diffs.append(cs - cb)
            pnl_diffs.append(ps - pb)
        acc_d = np.concatenate(acc_diffs) if acc_diffs else np.array([])
        pnl_d = np.concatenate(pnl_diffs) if pnl_diffs else np.array([])
        acc_m, acc_lo, acc_hi = block_bootstrap_ci(
            acc_d, BLOCK_BARS, BOOT_RESAMPLES, RNG_SEED
        )
        pnl_m, pnl_lo, pnl_hi = block_bootstrap_ci(
            pnl_d, BLOCK_BARS, BOOT_RESAMPLES, RNG_SEED + 1
        )
        t4_rows.append({
            "feature_set": set_name,
            "dShACC_mean": round(acc_m, 5),
            "dShACC_ci_lo": round(acc_lo, 5),
            "dShACC_ci_hi": round(acc_hi, 5),
            "dPnL_mean": round(pnl_m, 4),
            "dPnL_ci_lo": round(pnl_lo, 4),
            "dPnL_ci_hi": round(pnl_hi, 4),
            "n_tail_rows": len(acc_d),
        })
    t4 = pd.DataFrame(t4_rows)
    t4.to_csv(OUT / "T4_paired_lift_bootstrap.csv", index=False)
    print(t4.to_string(index=False))

    # ---- T5: multivariate importance share — the INERT screen ----
    print("\nT5 — multivariate gain-importance share of the new family "
          "(full-IS-panel fit; INERT if share < uniform parity):")
    t5_rows = []
    for set_name in ("+A", "+D", "+AD"):
        fcols = sets[set_name]
        ncols = new_cols_for[set_name]
        parity = len(ncols) / len(fcols)
        # per-symbol importance share, then mean
        shares = []
        for sym in SYMBOLS:
            sh = importance_share(panels[sym], fcols, ncols)
            if pd.notna(sh):
                shares.append(sh)
        mean_share = float(np.mean(shares)) if shares else float("nan")
        t5_rows.append({
            "feature_set": set_name,
            "n_new": len(ncols),
            "n_total": len(fcols),
            "uniform_parity_share": round(parity, 4),
            "mean_importance_share": round(mean_share, 4),
            "importance_gate_pass": bool(
                pd.notna(mean_share) and mean_share >= parity
            ),
        })
    t5 = pd.DataFrame(t5_rows)
    t5.to_csv(OUT / "T5_importance_share.csv", index=False)
    print(t5.to_string(index=False))

    # ---- GO / NO-GO verdict ----
    print("\n" + "=" * 78)
    print("GO / NO-GO VERDICT  (pre-registered 4-gate rule)")
    print("=" * 78)
    verdict_rows = []
    any_go = False
    best_set = None
    for set_name in ("+A", "+D", "+AD"):
        r4 = t4[t4["feature_set"] == set_name].iloc[0]
        r5 = t5[t5["feature_set"] == set_name].iloc[0]
        g1 = bool(r4["dShACC_mean"] >= GO_DSHACC_MIN)
        g2 = bool(r4["dShACC_ci_lo"] > 0.0)
        g3 = bool(r4["dPnL_mean"] > 0.0)
        g4 = bool(r5["importance_gate_pass"])
        set_go = g1 and g2 and g3 and g4
        any_go = any_go or set_go
        if set_go and best_set is None:
            best_set = set_name
        verdict_rows.append({
            "feature_set": set_name,
            "g1_dShACC>=0.010": g1,
            "g2_CI_lo>0": g2,
            "g3_dPnL>0": g3,
            "g4_importance>=parity": g4,
            "SET_GO": set_go,
        })
        print(f"  {set_name:>4}: g1(dShACC>={GO_DSHACC_MIN}) {'PASS' if g1 else 'FAIL'} | "
              f"g2(CI_lo>0) {'PASS' if g2 else 'FAIL'} | "
              f"g3(dPnL>0) {'PASS' if g3 else 'FAIL'} | "
              f"g4(imp>=parity) {'PASS' if g4 else 'FAIL'}  ->  "
              f"{'GO' if set_go else 'no'}")
    vdf = pd.DataFrame(verdict_rows)
    vdf.loc[len(vdf)] = {
        "feature_set": "VERDICT",
        "g1_dShACC>=0.010": "",
        "g2_CI_lo>0": "",
        "g3_dPnL>0": "",
        "g4_importance>=parity": "",
        "SET_GO": "GO" if any_go else "NO-GO",
    }
    vdf.to_csv(OUT / "T6_go_nogo_verdict.csv", index=False)
    print("  ----")
    print(f"  OVERALL VERDICT: {'GO' if any_go else 'NO-GO'}"
          + (f"  (winning set: {best_set})" if best_set else ""))
    print("=" * 78)


if __name__ == "__main__":
    main()
