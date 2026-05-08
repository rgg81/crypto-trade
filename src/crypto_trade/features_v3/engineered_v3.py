"""v3 engineered (composed/interaction) features — iter-v3/025+.

Category 2 axis in the v3 catalog: features built from EXISTING primitives
rather than off-the-shelf indicator additions (Category 1).  The distinction
matters for the IC orthogonality gate: composed features share variance with
their source primitives by construction (see ``feedback_v3_engineered_feature_pivot.md``).
The binding evidence gate for Category 2 axes is feature importance rank ≤10
AND absolute importance ≥30, NOT pairwise IC.

Track-isolated: NO imports from ``crypto_trade.features`` (v1) or
``crypto_trade.features_v2`` (v2).  Enforced by Phase 6 pre-flight grep.

Module dependency order (GROUP_REGISTRY insertion order matters):
  ``engineered_v3`` MUST run AFTER ``regime`` (which produces ``hurst_100``).
  In the current GROUP_REGISTRY dict the insertion order is preserved, so
  ``engineered_v3`` is registered AFTER ``regime`` and BEFORE ``fracdiff``.

iter-v3/034: ``compute_fracdiff_d05_close`` added (LdP AFML Ch. 5 FFD at d=0.5).
  Pure-numpy inline implementation; does NOT import from fracdiff_v3.py to
  preserve intra-module clarity.  fracdiff PyPI package UNAVAILABLE (statsmodels
  version conflict); see brief Section 9.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_regime_momentum_signed_5d(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: ret_5d × sign(hurst_100 − 0.5).

    Encodes the textbook trader heuristic: momentum works in trending regimes;
    momentum reverses in mean-reverting regimes.

    Construction:
    - ``ret_5d`` = log(close_t / close_{t-15}) at 8h cadence.
      15 bars × 8h = 120h ≈ 5 calendar days.
    - ``hurst_100``: rolling 100-bar R/S Hurst exponent (computed by
      ``add_regime_v3_features``).
    - ``regime_sign`` = sign(hurst_100 − 0.5):
        +1  if hurst_100 > 0.5  → trending regime  → momentum follows
        −1  if hurst_100 < 0.5  → mean-reversion   → momentum reverses
         0  if hurst_100 == 0.5 → pure random walk  → treated as NaN (no signal)

    Past-only by construction:
    - ``ret_5d = log_close_t − log_close_{t-15}`` uses only bars ≤ t.
      The shift(15) ensures bar t uses close at t−15, not t (no look-ahead).
    - ``hurst_100`` is computed from a 100-bar trailing window that ends at t−1
      (``_rolling_hurst`` iterates ``values[i-window:i]``, so the value at
      position i represents the window ending at i−1 of the original series;
      the first valid value appears at index ``window−1 = 99``).
      Combined: first valid ``regime_momentum_signed_5d`` appears at bar 99
      (hurst_100 warm-up) since ret_5d warm-up (bar 15) is dominated.

    NaN warm-up: first 99 bars are NaN (hurst_100 needs 100 bars; bars 0..98).

    Args:
        df: DataFrame with columns ``close`` (float-castable) and ``hurst_100``
            (pre-computed by ``add_regime_v3_features``).

    Returns:
        Copy of ``df`` with ``regime_momentum_signed_5d`` column appended.
        If ``hurst_100`` is missing the column is set to all-NaN without error,
        so the pipeline fails loudly at the feature-column assertion downstream.
    """
    df = df.copy()
    close = df["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    # 15 bars at 8h cadence = 5 calendar days
    ret_5d = log_close - log_close.shift(15)

    if "hurst_100" not in df.columns:
        df["regime_momentum_signed_5d"] = np.nan
        return df

    hurst = df["hurst_100"].astype(float)
    sign_hurst = np.sign(hurst - 0.5)
    # Pure random-walk edge case (hurst_100 == 0.5 → sign = 0): treat as NaN.
    # np.sign(0.0) == 0.0; replacing 0 with NaN propagates correctly through
    # multiplication so the composed feature is NaN for pure-RW bars.
    sign_hurst = sign_hurst.replace(0.0, np.nan)

    df["regime_momentum_signed_5d"] = ret_5d * sign_hurst
    return df


_VOL_ADJ_AUTOCORR_EPS: float = 1e-6
_VOL_ADJ_AUTOCORR_CAP: float = 100.0


def compute_vol_adj_autocorr(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: ret_autocorr_lag1_50 / (range_realized_vol_50 + EPS).

    Encodes the textbook microstructure heuristic (Sinclair, *Volatility Trading*;
    López de Prado, AFML Ch. 8): return persistence is a meaningful signal only
    when normalized by realized volatility.  The same lag-1 autocorrelation has
    different implications:

    - Low-vol regime, high autocorr  → genuine momentum/persistence signal worth trading
    - High-vol regime, high autocorr → noise-driven persistence; chasing it is a value trap

    Construction:
    - ``ret_autocorr_lag1_50``: 50-bar trailing rolling Pearson correlation of returns
      and their lag-1 shift (computed by ``add_momentum_accel_v3_features``).
    - ``range_realized_vol_50``: 50-bar trailing rolling realized vol from high/low
      ranges (computed by ``add_tail_risk_v3_features``).
    - ``vol_adj_autocorr = ret_autocorr_lag1_50 / (range_realized_vol_50 + EPS)``
      where EPS = 1e-6 prevents division by zero.
    - Output is clipped to [−100, +100] to prevent infinity from near-zero denominators.

    Past-only by construction:
    - ``ret_autocorr_lag1_50`` is computed past-only by ``add_momentum_accel_v3_features``
      (50-bar trailing rolling correlation of returns and lag-1 returns).
    - ``range_realized_vol_50`` is computed past-only by ``add_tail_risk_v3_features``
      (50-bar trailing rolling realized vol from high/low ranges).
    - Division is an element-wise past-only operation: value at row t uses only the
      source primitive values at row t (which are themselves past-only).
    - Both source primitives are upstream in GROUP_REGISTRY (tail_risk, momentum_accel
      run before engineered_v3); appending future bars does NOT alter the value at t.

    NaN warm-up: first ~49 bars are NaN (both source primitives require 50-bar windows;
    rows 0..48 have insufficient history for the 50-bar rolling computations).

    Args:
        df: DataFrame with columns ``ret_autocorr_lag1_50`` and ``range_realized_vol_50``
            (pre-computed by upstream feature groups).

    Returns:
        Copy of ``df`` with ``vol_adj_autocorr`` column appended.
        If either source primitive is missing, the column is set to all-NaN without
        error — the runner's ``_verify_feature_columns`` assertion catches the gap.
    """
    df = df.copy()
    if "ret_autocorr_lag1_50" not in df.columns:
        df["vol_adj_autocorr"] = np.nan
        return df
    if "range_realized_vol_50" not in df.columns:
        df["vol_adj_autocorr"] = np.nan
        return df

    autocorr = df["ret_autocorr_lag1_50"].astype(float)
    vol = df["range_realized_vol_50"].astype(float)
    raw = autocorr / (vol + _VOL_ADJ_AUTOCORR_EPS)
    # Cap at ±100 to prevent infinity from near-zero denominators (e.g., vol == 0
    # on synthetic or thinly-traded data; EPS alone is insufficient when vol < EPS).
    df["vol_adj_autocorr"] = raw.clip(lower=-_VOL_ADJ_AUTOCORR_CAP, upper=_VOL_ADJ_AUTOCORR_CAP)
    return df


_CROSS_ASSET_DIVERGENCE_EPS: float = 1e-6
_CROSS_ASSET_DIVERGENCE_CAP: float = 100.0


def compute_cross_asset_divergence_norm(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: (sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + EPS).

    Encodes the textbook systematic-trading heuristic (Robert Carver,
    *Systematic Trading*; Ernest Chan, *Quantitative Trading*): alt-vs-BTC return
    divergence is a meaningful signal only when normalized by the alt's local
    mean-reversion intensity.  The same alt-BTC divergence has different implications:

    - High |divergence|, low |vwap_dev_20| (price near VWAP, low MR intensity)
      → genuine relative-strength signal worth trading
    - High |divergence|, high |vwap_dev_20| (price far from VWAP, high MR intensity)
      → divergence may already be priced in or about to revert; value-trap signal

    Construction:
    - ``sym_ret_7d = log(close_t / close_{t-21})`` at 8h cadence.
      21 bars × 8h = 168h = 7 calendar days.  Computed inline from ``close``
      via ``.shift(21)``; past-only.
    - ``btc_ret_14d``: 42-bar trailing log return of BTC (computed by
      ``add_cross_btc_v3_features``; upstream in GROUP_REGISTRY).  Past-only.
    - ``vwap_dev_20``: 20-bar trailing VWAP deviation (computed by
      ``add_volume_micro_v3_features``; upstream in GROUP_REGISTRY).  Past-only.
    - ``raw = (sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + EPS)``
      where EPS = 1e-6 prevents division by zero.
    - Output clipped to [−CAP, +CAP] = [−100, +100] to prevent infinity from
      near-zero denominators (e.g., vwap_dev_20 == 0 on thinly-traded data;
      EPS alone insufficient when |vwap_dev| < EPS).

    Note on horizon mismatch: sym_ret_7d (21-bar, 7-day) MINUS btc_ret_14d (42-bar,
    14-day) encodes momentum-divergence: when the symbol's recent 7-day momentum
    diverges from BTC's longer-window 14-day momentum, the relative-strength signal
    is information-rich.  Structurally distinct from sym_vs_btc_ret_7d (already in
    feature set) which uses matching 7-day horizons for both.

    Past-only by construction:
    - ``sym_ret_7d``: log_close(t) − log_close(t−21); shift(21) is past-only.
      First 21 bars NaN (insufficient history).
    - ``btc_ret_14d``: upstream rolling 42-bar window ending at t; past-only.
      First ~41 bars NaN (dominant warm-up; 42-bar window controls).
    - ``vwap_dev_20``: upstream rolling 20-bar window ending at t; past-only.
    - Division and clip: element-wise at row t; no future-bar context needed.
    - Appending future bars after t does NOT alter the value at t.

    NaN warm-up: first ~41 bars are NaN (btc_ret_14d 42-bar window dominates;
    sym_ret_7d 21-bar warm-up is subsumed).

    Args:
        df: DataFrame with columns ``close`` (float-castable), ``btc_ret_14d``
            (pre-computed by ``add_cross_btc_v3_features``), and ``vwap_dev_20``
            (pre-computed by ``add_volume_micro_v3_features``).

    Returns:
        Copy of ``df`` with ``cross_asset_divergence_norm`` column appended.
        If ``btc_ret_14d`` or ``vwap_dev_20`` is missing, the column is set to
        all-NaN without error — the runner's ``_verify_feature_columns`` assertion
        catches the gap downstream.
    """
    df = df.copy()
    if "btc_ret_14d" not in df.columns:
        df["cross_asset_divergence_norm"] = np.nan
        return df
    if "vwap_dev_20" not in df.columns:
        df["cross_asset_divergence_norm"] = np.nan
        return df

    close = df["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    # 21 bars at 8h cadence = 7 calendar days (matches sym_ret_7d in cross_btc_v3.py)
    sym_ret_7d = log_close - log_close.shift(21)

    btc_ret_14d = df["btc_ret_14d"].astype(float)
    vwap_dev = df["vwap_dev_20"].astype(float)
    raw = (sym_ret_7d - btc_ret_14d) / (vwap_dev.abs() + _CROSS_ASSET_DIVERGENCE_EPS)
    df["cross_asset_divergence_norm"] = raw.clip(
        lower=-_CROSS_ASSET_DIVERGENCE_CAP, upper=_CROSS_ASSET_DIVERGENCE_CAP
    )
    return df


_FRACDIFF_D05_CLOSE_WEIGHT_THRESHOLD: float = 1e-4
_FRACDIFF_D05_CLOSE_D: float = 0.5


def _fracdiff_d05_weights(threshold: float = _FRACDIFF_D05_CLOSE_WEIGHT_THRESHOLD) -> np.ndarray:
    """Compute FFD weights for d=0.5, truncated at |w_k| < threshold.

    Uses the iterative recurrence from LdP AFML Ch. 5:
        w_0 = 1
        w_k = -w_{k-1} * (d - k + 1) / k   for k >= 1

    For d=0.5 the weights decay as approximately C * k^{-1.5}.  The truncation
    point at threshold=1e-4 is typically around k=120-150 bars.

    Returns:
        1-D numpy array of weights w_0, w_1, ..., w_{W-1}  where W is the
        truncation window length.  w_0 = 1.0 (current bar), w_1, w_2, ... are
        the lagged weights (all negative for d < 1).
    """
    d = _FRACDIFF_D05_CLOSE_D
    weights: list[float] = [1.0]
    k = 1
    while True:
        w_next = -weights[-1] * (d - k + 1) / k
        if abs(w_next) < threshold:
            break
        weights.append(w_next)
        k += 1
    return np.array(weights, dtype=np.float64)


def compute_fracdiff_d05_close(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: Fixed-window Fractional Differencing of log(close) at d=0.5.

    Implements the FFD (Fixed-window Fractional Differencing) algorithm from
    López de Prado (2018), *Advances in Financial Machine Learning*, Chapter 5.

    Construction:
    - ``log_close = log(close.clip(lower=1e-12))``
    - Weights: w_k = -w_{k-1} * (d - k + 1) / k for k >= 1, w_0 = 1.
      Truncated at |w_k| < 1e-4 (approximately 120-150 lags at d=0.5).
    - ``fracdiff_d05_close[t] = sum_{k=0}^{W-1} w_k * log_close[t-k]``
      where W is the truncation window length.

    Stationarity: ADF p < 0.05 expected at d=0.5 per AFML §5.4 theory.
    Memory: the d=0.5 output preserves long-memory (autocorrelation decays as
    k^{2*0.5-1} = k^0, i.e., slowly), unlike full differencing (d=1) which
    destroys all memory.

    Past-only by construction:
    - FFD at bar t uses ONLY log_close[t], log_close[t-1], ..., log_close[t-W+1].
      All lookback positions are strictly in the past relative to bar t.
    - The loop `for i in range(W-1, n)` guarantees that i+1..n are never accessed
      when computing position i.
    - Appending future bars t+1, t+2, ... to the input series does NOT alter the
      value at bar t (no trailing-window centering; purely causal).

    NaN warm-up: first (W-1) bars are NaN where W = len(weights).
    Typical W ≈ 120-150 at threshold=1e-4.  At 8h cadence: 150 bars ≈ 50 calendar
    days.  The IS window (24 months ≈ 2742 bars) easily absorbs this warm-up.

    Args:
        df: DataFrame with column ``close`` (float-castable).

    Returns:
        Copy of ``df`` with ``fracdiff_d05_close`` column appended.
        If ``close`` is missing, the column is set to all-NaN without error;
        the runner's ``_verify_feature_columns`` assertion catches the gap.
    """
    df = df.copy()
    if "close" not in df.columns:
        df["fracdiff_d05_close"] = np.nan
        return df

    close = df["close"].astype(float).clip(lower=1e-12)
    log_close = np.log(close)
    values = log_close.to_numpy(dtype=np.float64, copy=True)
    n = len(values)

    weights = _fracdiff_d05_weights()
    w_window = len(weights)
    # Reverse weights so that dot(w_rev, window_slice) = sum_k w_k * log_close[t-k]
    # with w_rev[0] = w_{W-1} (oldest lag) and w_rev[W-1] = w_0 = 1.0 (current bar).
    w_rev = weights[::-1]

    out = np.full(n, np.nan, dtype=np.float64)
    for i in range(w_window - 1, n):
        window_slice = values[i - w_window + 1 : i + 1]
        if np.isnan(window_slice).any():
            # Propagate NaN from upstream (e.g., missing close data)
            continue
        out[i] = float(np.dot(w_rev, window_slice))

    df["fracdiff_d05_close"] = out
    return df


def add_engineered_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """GROUP_REGISTRY entry point for all Category 2 (composed) v3 features.

    iter-v3/034: fracdiff_d05_close ADDED (LdP AFML Ch. 5 FFD at d=0.5;
    fixed-window fractional differentiation of log(close); memory-preserving
    stationary feature complementary to regime_momentum_signed_5d).
    Net column count: 15 (14 → 15; see V3_FEATURE_COLUMNS_TOP_N update).

    iter-v3/028: cross_asset_divergence_norm DROPPED from dispatch (revert 15 → 14;
    matches iter-v3/025 anchor exactly; MINI-VALIDATION of iter-v3/025 ALONE at
    --seeds 2; stacking FALSIFIED at iter-v3/027 per
    `feedback_v3_engineered_features_dont_stack.md`).  ``compute_cross_asset_divergence_norm``
    is RETAINED as dead code at zero revert cost.  ``compute_vol_adj_autocorr``
    likewise retained as dead code.  Per Critic FINAL ``966f4c1`` of iter-v3/027 +
    user directive 2026-05-08.

    iter-v3/027 (context): vol_adj_autocorr DROPPED (iter-v3/026 stacking falsified;
    IS Sharpe collapse +0.0493 + OOS spike +1.4501 at single-seed n_trials=35).
    cross_asset_divergence_norm ADDED then DROPPED here at iter-v3/028.

    Currently computes (dispatch order):
    - ``regime_momentum_signed_5d`` (iter-v3/025, KEPT): composed feature combining
      5-day momentum with Hurst regime classifier.  Depends on ``hurst_100``
      from ``regime`` group (upstream in GROUP_REGISTRY).
    - ``fracdiff_d05_close`` (iter-v3/034, NEW): FFD of log(close) at d=0.5.
      Depends only on ``close`` column (no upstream feature dependency beyond OHLCV).

    Each new composed feature must be listed in the iteration's research brief Section
    2.2 and validated with an adversarial past-only test.

    Args:
        df: DataFrame that has already been processed by ``add_regime_v3_features``
            (so ``hurst_100`` is available for regime_momentum_signed_5d).
            Upstream in GROUP_REGISTRY.

    Returns:
        Copy of ``df`` with all active engineered v3 features appended.
    """
    df = compute_regime_momentum_signed_5d(df)  # iter-v3/025 (KEPT; mandated by engineered pivot)
    df = compute_fracdiff_d05_close(df)  # iter-v3/034 (NEW; LdP AFML Ch. 5 FFD d=0.5)
    # compute_cross_asset_divergence_norm DROPPED at iter-v3/028 — revert 15 → 14;
    # stacking FALSIFIED at iter-v3/027; function retained as dead code at zero cost.
    # compute_vol_adj_autocorr DROPPED at iter-v3/027 — function retained as dead code.
    return df


__all__ = [
    "add_engineered_v3_features",
    "compute_cross_asset_divergence_norm",
    "compute_fracdiff_d05_close",
    "compute_regime_momentum_signed_5d",
    "compute_vol_adj_autocorr",
]
