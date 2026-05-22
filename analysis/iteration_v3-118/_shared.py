"""iter-v3/118 — engineered-feature axis EDA (cycle-6 EXPLORATION #9).

The axis under test (per `feedback_v3_axis_selection_quant_discipline.md` + the
/117 closeout recommendation):
    Does adding a NEW composed feature on the regime_momentum_signed_5d (/025
    PROMISING) lineage carry incremental directional signal beyond the 14-feature
    BASELINE_V3 stack on the BCH/LDO/TRX 8h cohort?

Recommendation framing (the /117 closeout QR's proposal): a composite of the
form

    composite_X = primitive_A * sign(primitive_B - threshold)

where primitive_A is a value-encoding feature, primitive_B is a regime-classifying
feature, and threshold is a regime-boundary scalar. The /025 precedent
(regime_momentum_signed_5d = ret_5d * sign(hurst_100 - 0.5)) is the design
template: IS +0.50 / OOS +0.84 vs anchor; importance 51% top vs 22-25% off-the-
shelf. KEPT in V3_FEATURE_COLUMNS since /028 CONFIRMATION-MERGE.

Motivation: cycle-6 has 7 NEGATIVE + 1 PROMISING-MECHANICAL. The PROMISING came
from the /116 no_confirm exit-layer primitive — a TRADE-CONSTRUCTION axis that
cuts trades failing to confirm momentum within K=4 candles. The structural
asymmetry it exploits — that mean-reversion-regime trades fail to confirm
momentum — is implicit in the gate but NOT exposed as a feature for LightGBM to
learn at ENTRY. A composed feature encoding "I am in a regime where momentum
fails to confirm" gives the LightGBM a direct entry signal for the same regime
structure that /116 currently exploits at exit.

Failure-mode motivation per /117 EDA T3 (per-offset AUC heterogeneity):
- BCH strongest at offset 0 = 0.6213
- LDO strongest at offset 0 = 0.5485
- TRX strongest at offset 16 = 0.5455
Per-offset structural information exists but is regime-conditional; a feature
encoding it at the value × regime-sign level is the engineered-feature axis.

Six candidate composites evaluated (T1):

  C1 = vwap_dev_20 * sign(hurst_100 - 0.5)
       — directional mean-reversion in trending vs MR regimes; vwap_dev_20 is
         the strongest mean-reversion primitive in TOP_N, hurst_100 is the
         canonical regime classifier (/025 template).

  C2 = ema_spread_atr_20 * sign(hurst_100 - 0.5)
       — trend strength flipped by regime; ema_spread_atr_20 is the canonical
         momentum primitive in TOP_N (/025 template applied to EMA spread).

  C3 = ema_spread_atr_20 * sign(range_realized_vol_50 - rolling_median_200)
       — value-by-volatility-regime composite (vol-conditional momentum).

  C4 = ret_autocorr_lag1_50 * sign(hurst_100 - 0.5)
       — autocorrelation flipped by regime (positive autocorr in trending is
         continuation; in MR is fade). Directly encodes the /116 no_confirm
         mechanism at the feature level.

  C5 = sym_vs_btc_ret_7d * sign(btc_ret_14d)
       — symbol-vs-BTC divergence conditioned on BTC trend direction; the
         cross-asset analog of /025's regime-conditional momentum.

  C6 = vwap_dev_20 * sign(ret_kurt_50 - 0)
       — VWAP mean-reversion conditional on tail-regime (positive kurt = heavy
         tail vs negative kurt = thin tail).

Linear Redundancy Pre-Falsifier per `feedback_v3_lr_pf_methodology.md`:
- composed-feature carve-out applies (R²>0.50 acceptable when the candidate is
  composed of primitives by construction). PRIMARY falsifier is Sharpe-Δ NOT
  importance rank at the production stage (post-EDA). At EDA stage, AUC is
  the primary discriminator (per /109 / /117 methodology); per-symbol AUC is
  the /117 g1 hard gate; importance rank is the /025 secondary benchmark.

NO CHEATING — strict IS-only invariant
--------------------------------------
Every feature/label row entering any computation has close_time < OOS_CUTOFF_MS
= 1742774400000 (2025-03-24). The post-cutoff OOS is NEVER read.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 -- IMMUTABLE
SYMBOLS: tuple[str, ...] = ("BCHUSDT", "LDOUSDT", "TRXUSDT")  # canonical /059 universe

# The /059 14-feature anchor stack (CANONICAL post-/059 since /028 CONFIRMATION-MERGE).
V3_FEATURE_COLUMNS: list[str] = [
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

# Triple-barrier label config (faithful to /059).
ATR_TP_MULT = 2.0
ATR_SL_MULT = 1.0
ATR_COL = "natr_21_raw"
TIMEOUT_BARS = 21  # 21 x 8h = 168h horizon — the /059 canonical timeout
FEE_PCT = 0.1

# Walk-forward fold geometry.
N_FOLDS_DEFAULT = 5
EMBARGO_BARS = 22  # /059 walk-forward embargo at the 8h timescale


def _is_only_fence(df: pd.DataFrame) -> pd.DataFrame:
    """Apply IS-only fence at row level. Defensive — raises if any row leaks."""
    out = df[df["close_time"] < OOS_CUTOFF_MS].copy()
    if (out["close_time"] >= OOS_CUTOFF_MS).any():
        raise RuntimeError("IS fence breach detected")
    return out


def load_features_is(symbol: str) -> pd.DataFrame:
    """Load one symbol's pre-computed 8h features parquet, IS-only fenced."""
    parquet = REPO_ROOT / "data" / "features_v3" / f"{symbol}_8h_features.parquet"
    df = pd.read_parquet(parquet)
    df = df.sort_values("open_time").reset_index(drop=True)
    df = _is_only_fence(df)
    return df


# -----------------------------------------------------------------------------
# Triple-barrier label on 8h bars (faithful to /059 labelling.label_trades)
# -----------------------------------------------------------------------------


def label_triple_barrier(df: pd.DataFrame) -> pd.DataFrame:
    """Triple-barrier label every 8h bar in one symbol's panel.

    Faithful to v3 labelling.label_trades (triple_barrier): forward-scan to the
    timeout candle, SL checked before TP within a bar (adverse-first), label =
    sign of the better of (long net PnL, short net PnL).
    """
    d = df.sort_values("open_time").reset_index(drop=True).copy()
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
# Candidate composite features (C1..C6)
# -----------------------------------------------------------------------------

EPS = 1e-12


def _rolling_median_past_only(x: np.ndarray, window: int) -> np.ndarray:
    return pd.Series(x).rolling(window, min_periods=window).median().to_numpy()


def compute_candidates(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the 6 candidate composites on a symbol's 8h-feature panel.

    All composites are STRICTLY past-only — they read only existing same-row
    feature columns whose values were computed past-only by the
    features_v3 pipeline (verified at /059 / /060 audit, and the
    `range_realized_vol_50` rolling median is computed past-only here).
    """
    d = df.copy()
    # Primitive aliases (existing in parquet).
    vwap = d["vwap_dev_20"].to_numpy(dtype="float64")
    ema = d["ema_spread_atr_20"].to_numpy(dtype="float64")
    hurst = d["hurst_100"].to_numpy(dtype="float64")
    autocorr = d["ret_autocorr_lag1_50"].to_numpy(dtype="float64")
    realvol = d["range_realized_vol_50"].to_numpy(dtype="float64")
    sym_vs_btc = d["sym_vs_btc_ret_7d"].to_numpy(dtype="float64")
    btc14 = d["btc_ret_14d"].to_numpy(dtype="float64")
    kurt50 = d["ret_kurt_50"].to_numpy(dtype="float64")

    # Sign helpers (NaN-preserving).
    def _sign(x: np.ndarray, threshold: float) -> np.ndarray:
        out = np.full_like(x, np.nan, dtype="float64")
        mask = ~np.isnan(x)
        out[mask] = np.where(x[mask] > threshold, 1.0, -1.0)
        return out

    # Vol regime classifier (rolling-200 median, past-only).
    realvol_med200 = _rolling_median_past_only(realvol, 200)

    d["C1_vwap_signed_hurst"] = vwap * _sign(hurst, 0.5)
    d["C2_ema_signed_hurst"] = ema * _sign(hurst, 0.5)
    d["C3_ema_signed_volregime"] = ema * _sign(realvol - realvol_med200, 0.0)
    d["C4_autocorr_signed_hurst"] = autocorr * _sign(hurst, 0.5)
    d["C5_symvsbtc_signed_btctrend"] = sym_vs_btc * _sign(btc14, 0.0)
    d["C6_vwap_signed_kurt"] = vwap * _sign(kurt50, 0.0)

    return d


CANDIDATE_NAMES: tuple[str, ...] = (
    "C1_vwap_signed_hurst",
    "C2_ema_signed_hurst",
    "C3_ema_signed_volregime",
    "C4_autocorr_signed_hurst",
    "C5_symvsbtc_signed_btctrend",
    "C6_vwap_signed_kurt",
)


# -----------------------------------------------------------------------------
# Walk-forward fold geometry on 8h bars (IS-only)
# -----------------------------------------------------------------------------


def walk_forward_folds(n: int, n_folds: int = N_FOLDS_DEFAULT) -> list[tuple[np.ndarray, np.ndarray]]:
    """Expanding-window folds with a 22-bar embargo purged before test."""
    start = int(n * 0.40)
    test_span = n - start
    chunk = test_span // n_folds
    folds = []
    for k in range(n_folds):
        test_lo = start + k * chunk
        test_hi = start + (k + 1) * chunk if k < n_folds - 1 else n
        train_hi = max(0, test_lo - EMBARGO_BARS)
        train_idx = np.arange(0, train_hi)
        test_idx = np.arange(test_lo, test_hi)
        if len(train_idx) >= 200 and len(test_idx) >= 50:
            folds.append((train_idx, test_idx))
    return folds


# -----------------------------------------------------------------------------
# Per-symbol panel builder (features + label + candidates, IS-only)
# -----------------------------------------------------------------------------


def build_labeled_panel(symbol: str) -> pd.DataFrame:
    """Load symbol's 8h features, label, add 6 candidates. IS-only fenced."""
    df = load_features_is(symbol)
    df = label_triple_barrier(df)
    df = compute_candidates(df)
    feat_cols = list(V3_FEATURE_COLUMNS) + list(CANDIDATE_NAMES)
    keep_cols = ["open_time", "close_time", "close", "label", "label_valid"] + feat_cols
    keep_cols = [c for c in keep_cols if c in df.columns]
    df = df[keep_cols].copy()
    # Filter to valid-label rows where all 14 baseline + 6 candidates are non-NaN.
    keep = df["label_valid"] & df[feat_cols].notna().all(axis=1)
    df = df[keep].reset_index(drop=True)
    df["symbol"] = symbol
    return df
