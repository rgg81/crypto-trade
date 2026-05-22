"""iter-v3/110 gating EDA — shared IS-only data loader + /059-faithful labeling.

The axis under test: SYMBOL SELECTION. v3 has traded the BCH/LDO/TRX universe
since cycle 1 and never re-opened it. The /109 permutation null (LightGBM
real-label feature->label held-out AUC 0.497, p=0.64) is SPECIFIC to that
universe's joint feature->label distribution — it does NOT constrain a
different universe. This EDA screens the full set of v3-eligible symbols by the
exact metric /109 used (held-out feature->label predictive AUC against a
per-symbol permutation null) to find a universe that carries IS-detectable
directional signal where BCH/LDO/TRX does not.

This module is a 22-symbol generalization of analysis/iteration_v3-109/_shared.py
(commit 4f77b1a). The labeler, the fold builder, and the IS-only invariant are
copied verbatim from /109 — the ONLY change is SYMBOLS (3 -> 22 candidates) and
a per-symbol loader that does not stack.

NO CHEATING — strict IS-only invariant:
  Every feature row entering any computation has ``close_time < OOS_CUTOFF_MS``.
  OOS_CUTOFF_MS = 1742774400000 (2025-03-24). The post-cutoff OOS is NEVER read.

Label faithfulness — replicates ``labeling.label_trades`` (label_mode=
"triple_barrier") exactly: ATR triple-barrier, atr_tp=2.0 / atr_sl=1.0, ATR
column ``natr_21_raw``, 21-candle (10080-min / 8h) timeout, fee 0.1%. The label
is sign(better-of long_pnl / short_pnl) — the directional target the v3 primary
model is trained to predict. Adverse-first intra-bar tie-break (SL before TP).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Repo root — anchors data/ regardless of the script's cwd.
REPO_ROOT = Path(__file__).resolve().parents[2]

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 — IMMUTABLE

# ---------------------------------------------------------------------------
# The candidate universe. All symbols with a generated 24-month v3 feature
# parquet, MINUS V3_EXCLUDED_SYMBOLS (v1/v2 symbols + MKR) and MINUS EOSUSDT
# (delisted — feature parquet ends 2025-05, only 176 OOS rows; not a live
# trading candidate). The 3 incumbents (BCH/LDO/TRX) are KEPT in the candidate
# set so the EDA measures them on the identical methodology — the screen must
# reproduce the /109 result on the incumbents to be trustworthy.
# ---------------------------------------------------------------------------
CANDIDATE_SYMBOLS = (
    "AAVEUSDT", "ADAUSDT", "ALGOUSDT", "ATOMUSDT", "AVAXUSDT", "AXSUSDT",
    "BCHUSDT", "CRVUSDT", "FILUSDT", "FTMUSDT", "GALAUSDT", "GRTUSDT",
    "HBARUSDT", "ICPUSDT", "LDOUSDT", "MANAUSDT", "RUNEUSDT", "SANDUSDT",
    "THETAUSDT", "TRXUSDT", "VETUSDT",
)
INCUMBENTS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

# /059 V3_FEATURE_COLUMNS — the 14-feature stack. The axis holds these IDENTICAL;
# the ONE clean variable is the symbol universe.
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
EMBARGO_CANDLES = TIMEOUT_MINUTES // INTERVAL_MINUTES + 1  # = 22, the /059 embargo


def _label_one_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """Triple-barrier label every candle of one symbol's IS frame.

    Faithful to ``labeling.label_trades`` (triple_barrier branch): forward-scan
    to the timeout candle, SL checked before TP within a bar (adverse-first),
    label = sign of the better of (long net PnL, short net PnL). Verbatim from
    analysis/iteration_v3-109/_shared.py.
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
    long_pnl_arr = np.zeros(n, dtype=np.float64)
    short_pnl_arr = np.zeros(n, dtype=np.float64)
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
        scanned = 0
        for j in range(i + 1, n):
            if close_time[j] > deadline:
                if long_res == 0:
                    long_res = -2
                if short_res == 0:
                    short_res = -2
                break
            scanned += 1
            h_bar = high[j]
            lo = low[j]
            last_close = close[j]
            if long_res == 0:
                if lo <= long_sl:
                    long_res = -1
                elif h_bar >= long_tp:
                    long_res = 1
            if short_res == 0:
                if h_bar >= short_sl:
                    short_res = -1
                elif lo <= short_tp:
                    short_res = 1
            if long_res != 0 and short_res != 0:
                break
        else:
            if long_res == 0:
                long_res = -2
            if short_res == 0:
                short_res = -2

        if scanned == 0:
            continue

        fwd_ret = (last_close - entry) / entry * 100.0
        tp_pnl = tp_dist / entry * 100.0
        sl_pnl = sl_dist / entry * 100.0

        if long_res == 1:
            long_pnl = tp_pnl - FEE_PCT
        elif long_res == -1:
            long_pnl = -sl_pnl - FEE_PCT
        else:
            long_pnl = fwd_ret - FEE_PCT
        if short_res == 1:
            short_pnl = tp_pnl - FEE_PCT
        elif short_res == -1:
            short_pnl = -sl_pnl - FEE_PCT
        else:
            short_pnl = -fwd_ret - FEE_PCT

        long_pnl_arr[i] = long_pnl
        short_pnl_arr[i] = short_pnl
        valid[i] = True
        label[i] = 1 if long_pnl >= short_pnl else -1

    out = df.copy()
    out["label"] = label
    out["long_pnl"] = long_pnl_arr
    out["short_pnl"] = short_pnl_arr
    out["best_edge"] = np.maximum(long_pnl_arr, short_pnl_arr)
    out["_valid_label"] = valid
    return out


def load_labeled_symbol(sym: str) -> pd.DataFrame:
    """Load ONE symbol's IS-only labeled candle dataset.

    Returns a frame with the 14 V3 features, the triple-barrier ``label`` in
    {-1,+1}, ``best_edge``, ``long_pnl``, ``short_pnl``, ``symbol``,
    ``close_time``. Strictly ``close_time < OOS_CUTOFF_MS``. Candles without a
    complete forward label window OR with any NaN feature are dropped.
    """
    p = REPO_ROOT / f"data/features_v3/{sym}_8h_features.parquet"
    df = pd.read_parquet(p)
    # IS-only gate — assert before any computation
    is_df = df[df["close_time"] < OOS_CUTOFF_MS].copy()
    assert (is_df["close_time"] < OOS_CUTOFF_MS).all(), f"{sym}: IS gate violated"
    labeled = _label_one_symbol(is_df)
    labeled = labeled[labeled["_valid_label"]].copy()
    labeled = labeled.dropna(subset=V3_FEATURE_COLUMNS)
    labeled["symbol"] = sym
    # final IS-only assertion
    assert (labeled["close_time"] < OOS_CUTOFF_MS).all(), f"{sym}: post-label IS gate violated"
    return labeled.reset_index(drop=True)


def make_walk_forward_folds(
    df_sym: pd.DataFrame, n_folds: int = 8, embargo: int = EMBARGO_CANDLES
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Expanding-window walk-forward folds, embargo-purged.

    Verbatim from analysis/iteration_v3-109/_shared.py. The last ``n_folds``
    equal-size blocks are held-out test folds; the training set for fold k is
    every candle strictly BEFORE the fold start MINUS an ``embargo`` of 22
    candles so no label window straddles the train/test boundary. Returns
    (train_idx, test_idx) positional arrays.
    """
    df_sym = df_sym.sort_values("close_time").reset_index(drop=True)
    n = len(df_sym)
    fold_size = n // (n_folds + 2)  # leave >=2 fold-widths for the first train set
    folds = []
    for k in range(n_folds):
        test_start = n - (n_folds - k) * fold_size
        test_end = test_start + fold_size
        if k == n_folds - 1:
            test_end = n
        train_end = test_start - embargo
        if train_end < fold_size:
            continue
        train_idx = np.arange(0, train_end)
        test_idx = np.arange(test_start, test_end)
        folds.append((train_idx, test_idx))
    return folds
