"""iter-v3/112 gating EDA — shared IS-only data loader + /059-faithful labeling.

The axis under test: does a POOLED (cross-symbol) LightGBM — ONE model trained
on the concatenated BCH+LDO+TRX panel — extract a SHARPER directional edge than
the PER-SYMBOL architecture v3 has used for all 111 iterations (three separate
LightGBMs, each trained on one symbol's thin ~50-75-IS-trade sample)?

The /111 diary's diagnosis: v3's recurring universe-iteration failure is
per-symbol models trained on thin per-symbol samples that overfit the IS book
and fail OOS. A pooled model trains on N× the effective sample — the orthogonal
structural response to per-symbol sample starvation.

This module builds the labeled IS dataset ONCE; the EDA scripts import it. It is
adapted verbatim from analysis/iteration_v3-109/_shared.py (the model-class
horse-race template the /111 diary recommends), with the BCH/LDO/TRX canonical
/059 universe held — the /111 diary explicitly recommends the canonical universe
so the architecture is the ONLY variable changed.

NO CHEATING — strict IS-only invariant:
  Every feature row entering any computation has ``close_time < OOS_CUTOFF_MS``.
  OOS_CUTOFF_MS = 1742774400000 (2025-03-24). The post-cutoff OOS is NEVER read.

Label faithfulness — replicates ``labeling.label_trades`` (label_mode=
"triple_barrier") exactly: ATR triple-barrier, atr_tp=2.0 / atr_sl=1.0, ATR
column ``natr_21_raw``, 21-candle (10080-min / 8h) timeout, fee 0.1%. The label
is sign(better-of long_pnl / short_pnl) — the directional target the v3 primary
model is trained to predict. Adverse-first intra-bar tie-break (SL before TP),
exactly as the production loop short-circuits.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Repo root — anchors data/ + reports-v3/ regardless of the script's cwd.
REPO_ROOT = Path(__file__).resolve().parents[2]

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 — IMMUTABLE
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")  # canonical /059 universe

# /059 V3_FEATURE_COLUMNS — the 14-feature stack. The axis holds these IDENTICAL;
# the ONE clean variable is the model architecture (pooled vs per-symbol).
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
            # no forward candle inside window — drop (end-of-data candle)
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
        # label = direction of the better net PnL (the v3 directional target)
        label[i] = 1 if long_pnl >= short_pnl else -1

    out = df.copy()
    out["label"] = label
    out["long_pnl"] = long_pnl_arr
    out["short_pnl"] = short_pnl_arr
    out["best_edge"] = np.maximum(long_pnl_arr, short_pnl_arr)
    out["_valid_label"] = valid
    return out


def load_labeled_is() -> pd.DataFrame:
    """Load the IS-only labeled candle dataset for BCH/LDO/TRX.

    Returns one frame, all 3 symbols stacked, with the 14 V3 features, the
    triple-barrier ``label`` in {-1,+1}, ``best_edge`` (PnL of the better
    direction), ``symbol``, ``close_time``. Strictly ``close_time < OOS_CUTOFF_MS``.
    """
    frames = []
    for sym in SYMBOLS:
        df = pd.read_parquet(REPO_ROOT / f"data/features_v3/{sym}_8h_features.parquet")
        # IS-only gate — assert before any computation
        is_df = df[df["close_time"] < OOS_CUTOFF_MS].copy()
        assert (is_df["close_time"] < OOS_CUTOFF_MS).all(), f"{sym}: IS gate violated"
        labeled = _label_one_symbol(is_df)
        # keep only candles with a complete forward label window AND non-NaN features
        labeled = labeled[labeled["_valid_label"]].copy()
        labeled = labeled.dropna(subset=V3_FEATURE_COLUMNS)
        labeled["symbol"] = sym
        frames.append(labeled)
    full = pd.concat(frames, ignore_index=True)
    # final IS-only assertion on the assembled frame
    assert (full["close_time"] < OOS_CUTOFF_MS).all(), "assembled frame: IS gate violated"
    return full


def make_time_aligned_folds(
    df_all: pd.DataFrame, n_folds: int = 8, embargo: int = EMBARGO_CANDLES
) -> list[tuple[int, int]]:
    """Build n_folds time-aligned expanding-window walk-forward boundaries.

    The pooled-vs-per-symbol horse race REQUIRES the train/test split to be
    defined on a SHARED TIME AXIS, not on per-symbol row counts — otherwise the
    pooled model and the per-symbol models would be evaluated on different
    calendar windows and the comparison would be confounded.

    Each fold k is a (test_start_ms, test_end_ms) pair on the global IS calendar.
    The per-symbol and pooled trainers both select their training rows as
    ``close_time < test_start_ms - embargo_ms`` and their test rows as
    ``test_start_ms <= close_time < test_end_ms`` — the SAME calendar window for
    both architectures. This mirrors ``walk_forward.generate_monthly_splits``
    (time-window selection) and the /059 22-candle embargo.

    Returns a list of (test_start_ms, test_end_ms) tuples.
    """
    ts = np.sort(df_all["close_time"].unique())
    n = len(ts)
    block = n // (n_folds + 2)  # leave >=2 block-widths for the first train set
    folds = []
    for k in range(n_folds):
        test_start_idx = n - (n_folds - k) * block
        test_end_idx = test_start_idx + block
        if k == n_folds - 1:
            test_end_idx = n
        if test_start_idx < block:  # need a usable minimum training set
            continue
        folds.append((int(ts[test_start_idx]), int(ts[min(test_end_idx, n - 1)])))
    return folds
