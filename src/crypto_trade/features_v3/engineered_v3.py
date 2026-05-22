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

from pathlib import Path

import numpy as np
import pandas as pd

# iter-v3/085: default data root for the per-symbol funding-rate cache used by
# add_funding_regime_momentum_v3_features (mirrors funding_v3._DEFAULT_DATA_DIR).
_DEFAULT_DATA_DIR: Path = Path("data")


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


def compute_regime_momentum_signed_3d(df: pd.DataFrame) -> pd.Series:
    """3-bar variant of regime_momentum_signed_5d (sign-flip on hurst regime).

    Captures shorter-horizon (1-day at 8h cadence) regime persistence that the
    5-bar (5-day) variant misses.  Same sign-flip mechanism; different return
    lookback horizon.

    Construction:
    - ``ret_3d`` = close.shift(1) / close.shift(4) - 1.0
      bar t uses close[t-1] / close[t-4] - 1.0; strictly past-only (no close[t]).
    - ``hurst_100``: rolling 100-bar R/S Hurst exponent (computed by
      ``add_regime_v3_features``); already past-only by construction.
    - ``regime_sign`` = sign(hurst_100.shift(1) - 0.5):
        +1  if hurst_100[t-1] > 0.5  → trending regime  → momentum follows
        −1  if hurst_100[t-1] < 0.5  → mean-reversion   → momentum reverses
         0  if hurst_100[t-1] == 0.5 → pure random walk  → treated as 0.0

    Past-only by construction:
    - ``close.shift(1)``: bar t uses close[t-1]. Past-only.
    - ``close.shift(4)``: bar t uses close[t-4]. Past-only.
    - ``hurst_100`` is computed past-only by ``add_regime_v3_features``
      (100-bar trailing R/S window; first valid value at bar 99).
    - ``hurst.shift(1)``: bar t uses hurst_100[t-1]. Past-only.
    - Combined: first valid value appears at bar 100 (hurst_100 warm-up dominates
      over close.shift(4) warm-up of 4 bars).

    NaN warm-up: first 100 bars NaN before fillna.
    fillna(0.0): neutral fill (no regime signal) for warm-up bars.

    Args:
        df: DataFrame with columns ``close`` (float-castable) and ``hurst_100``
            (pre-computed by ``add_regime_v3_features``).

    Returns:
        pd.Series with ``regime_momentum_signed_3d`` values.
        First ~100 elements are 0.0 (NaN warm-up filled neutral).
        If ``hurst_100`` is missing, returns zeros (safe degradation; the runner's
        ``_verify_feature_columns`` assertion catches the gap downstream).
    """
    if "hurst_100" not in df.columns:
        return pd.Series(0.0, index=df.index, name="regime_momentum_signed_3d")

    close = df["close"].astype(float)
    ret_3d = close.shift(1) / close.shift(4) - 1.0  # past-only 3-bar return
    hurst = df["hurst_100"].astype(float)
    regime_sign = np.sign(hurst.shift(1) - 0.5)
    return (ret_3d * regime_sign).fillna(0.0)


def compute_efficiency_ratio_50(df: pd.DataFrame) -> pd.Series:
    """Kaufman efficiency ratio (1995): direction strength over noise — 50-bar window.

    Encodes the Kaufman (1995) adaptive-moving-average heuristic (*Smarter Trading*,
    Ch. 5): the ratio of net directional price displacement to total path length
    measures how efficiently price has moved — close to 1.0 in a clean trend,
    close to 0.0 in choppy mean-reverting markets.

    Construction:
    - ``direction[t]  = abs(close[t] - close[t-50])``  — net displacement over 50 bars.
    - ``noise[t]      = sum_{k=1}^{50} abs(close[t-k+1] - close[t-k])``  — total path.
    - ``er[t]         = direction[t] / (noise[t] + 1e-9)``  — epsilon prevents div-by-0.
    - ``.shift(1)`` applied to the ER series: bar t's value uses close[t-51..t-1] only.
    - ``.fillna(0.0)`` on warmup NaNs (first 51 bars): neutral zero is preferable to NaN
      propagation at training time; 0.0 = maximally choppy (no directional efficiency).
    - ``.clip(0.0, 1.0)``: output is bounded by triangle inequality; clip guards float
      precision edge cases near 0 (e.g., noise sum rounds to < direction from fp errors).

    Past-only by construction:
    - ``close.shift(50)``: bar t uses close[t-50]. Strictly past-only.
    - ``close.diff()``: bar t uses close[t] - close[t-1]. Past-only.
    - ``.rolling(50, min_periods=50).sum()``: sums bars [t-49..t]. Past-only.
    - ``.shift(1)`` on the ER result: the final bar-t value now uses bars [t-51..t-1].
      This additional shift ensures bar t cannot observe close[t] at model-inference time.
    - Appending future bars t+1, t+2, ... does NOT alter the value at bar t (all
      operations are causal rolling windows terminated at bar t-1 after the shift).

    NaN warm-up: first 51 bars are NaN before fillna (50-bar rolling noise window
    requires 50 bars, then shift(1) adds 1 more bar of warmup).  After fillna(0.0)
    the first 51 bars are 0.0 (neutral).  At 8h cadence: 51 bars ≈ 17 calendar days,
    well within the 24-month IS window (~2742 bars).

    IC gate note: efficiency_ratio_50 is a Category 1 indicator (external formula,
    NOT a Category 2 composed feature using existing v3 primitives).  The IC carve-out
    for Category 2 features does NOT apply.  Standard |IC| < 0.70 hard gate applies
    in full (checked by Critic Check 4 at Phase 7.5).

    Args:
        df: DataFrame with column ``close`` (float-castable).

    Returns:
        pd.Series with ``efficiency_ratio_50`` values (float, range [0.0, 1.0]).
        First 51 elements are 0.0 (warmup filled neutral).
        If ``close`` column is missing, returns a zero Series (safe degradation;
        the runner's ``_verify_feature_columns`` assertion catches the gap).
    """
    if "close" not in df.columns:
        return pd.Series(0.0, index=df.index, name="efficiency_ratio_50")

    close = df["close"].astype(float)
    direction = (close - close.shift(50)).abs()
    noise = close.diff().abs().rolling(50, min_periods=50).sum()
    er = direction / (noise + 1e-9)
    er = er.shift(1)  # past-only: bar t now sees close[t-51..t-1]
    return er.fillna(0.0).clip(0.0, 1.0)


_VOL_NORMALIZED_RET_5D_EPS: float = 1e-6


def compute_vol_normalized_ret_5d(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: ret_5d / (range_realized_vol_50 + epsilon).

    Encodes the canonical Sharpe-like risk-normalized momentum (Sinclair, Vol Trading;
    LdP AFML Ch. 8): how unusual is this 5d return given recent volatility regime?

    Construction:
    - ret_5d = log(close_t / close_{t-15}) at 8h cadence (15 bars * 8h = 5 days).
    - range_realized_vol_50: rolling 50-bar high-low realized vol (computed by
      add_tail_risk_v3_features).
    - epsilon = 1e-6 prevents zero-vol division.

    Past-only by construction:
    - ret_5d.shift(15) ensures bar t uses close at t-15 (no look-ahead).
    - range_realized_vol_50 is past-only (rolling window); the v3 implementation
      uses .shift(1) inside add_tail_risk_v3_features.

    NaN warm-up: first ~49 bars NaN from range_realized_vol_50's 50-bar window (ret_5d
    warm-up is 15 bars; the denominator's 50-bar window dominates).

    IC carve-out applies (per ``feedback_v3_engineered_feature_pivot.md``):
    - vol_normalized_ret_5d shares variance with both source primitives by construction.
    - |IC| with range_realized_vol_50 expected ~0.3-0.5 (denominator inverse).
    - |IC| with ret_5d direction expected ~0.7+ (numerator dominant direction signal).
    - Strict |IC|<0.50 gate is INAPPROPRIATE for Category 2 composed features.
    - Binding gate: importance >=30 in at least 2 of 4 symbols (relaxed Falsifier).

    Args:
        df: DataFrame with columns 'close' (float-castable) and 'range_realized_vol_50'
            (pre-computed by add_tail_risk_v3_features).

    Returns:
        Copy of df with vol_normalized_ret_5d column appended.
        If range_realized_vol_50 is missing the column is set to all-NaN without error,
        so the pipeline fails loudly at the feature-column assertion downstream.
    """
    df = df.copy()
    close = df["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    # 15 bars at 8h cadence = 5 calendar days
    ret_5d = log_close - log_close.shift(15)

    if "range_realized_vol_50" not in df.columns:
        df["vol_normalized_ret_5d"] = np.nan
        return df

    rv = df["range_realized_vol_50"].astype(float)
    df["vol_normalized_ret_5d"] = ret_5d / (rv + _VOL_NORMALIZED_RET_5D_EPS)
    return df


def compute_hurst_drift_50_200(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: hurst_50 - hurst_200 (regime-drift across time-scales).

    Construction (uses existing past-only parquet primitives):
    - hurst_50  = rolling 50-bar R/S Hurst exponent, computable as hurst_100 -
      hurst_diff_100_50 (since hurst_diff_100_50 = hurst_100 - rolling_hurst(close, 50)
      in regime_v3.py:126).
    - hurst_200 = rolling 200-bar R/S Hurst exponent (in parquet via
      add_regime_v3_features).
    - hurst_drift_50_200 = hurst_50 - hurst_200
                         = hurst_100 - hurst_diff_100_50 - hurst_200

    Mechanism: positive drift = short-horizon (50-bar) trending stronger than
    long-horizon (200-bar) — mean-reversion entering; negative = long-horizon
    trending stronger — momentum building.

    Stationarity: ADF p << 0.05 by construction (bounded difference of two bounded
    R/S Hurst measurements). Verified across all 4 symbols at
    analysis/iteration_v3-053/axis2_adf_per_symbol.csv (SHA `1fc6d55`).

    Linear redundancy DISCLOSURE (R^2 = 1.000 EXACT):
    hurst_drift_50_200 is the exact linear combination
    hurst_100 - hurst_diff_100_50 - hurst_200 (verified at
    analysis/iteration_v3-053/axis5_linear_redundancy.csv). Tree models with
    depth-3 splits on (hurst_100, hurst_diff_100_50, hurst_200) can approximate
    this linear combination via axis-aligned hyperrectangles, but NOT exactly.
    Single-column representation MAY improve colsample_bytree efficiency at low
    Optuna budget (n_trials=35 single-seed) — this is the REFRAMED HYPOTHESIS B basis.

    Univariate signal: Spearman rho NOT significant at p<0.05 in any of 4 symbols
    (mean rho +0.0114 — weakest of any v3 Category 2 candidate). See
    analysis/iteration_v3-053/axis4_univariate_spearman.csv.

    Past-only by construction:
    - All 3 source primitives are past-only (computed by upstream regime_v3 group).
    - Element-wise subtraction at row t uses only past-only values at row t.
    - Appending future bars does NOT alter the value at t.

    NaN warm-up: first 200 bars NaN (dominated by hurst_200 200-bar warm-up).

    iter-v3/053: ACTIVATED as 15th element of V3_FEATURE_COLUMNS_TOP_N.
    REFRAMED HYPOTHESIS B: primary value is to document the Linear Redundancy
    Pre-Falsifier (LR-PF) methodology for future Category 2 composed-feature
    axis selections.

    Args:
        df: DataFrame with columns ``hurst_100``, ``hurst_diff_100_50``, ``hurst_200``
            (pre-computed by ``add_regime_v3_features``).

    Returns:
        Copy of ``df`` with ``hurst_drift_50_200`` column appended. If any source
        primitive is missing, the column is set to all-NaN without error (runner's
        _verify_feature_columns assertion catches the gap downstream).
    """
    df = df.copy()
    required = ("hurst_100", "hurst_diff_100_50", "hurst_200")
    if not all(c in df.columns for c in required):
        df["hurst_drift_50_200"] = np.nan
        return df
    df["hurst_drift_50_200"] = (
        df["hurst_100"].astype(float)
        - df["hurst_diff_100_50"].astype(float)
        - df["hurst_200"].astype(float)
    )
    return df


_TREND_EFFICIENCY_SIGNED_EPS: float = 1e-9


def compute_trend_efficiency_signed(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: kaufman_efficiency_50 × sign(ret_20d).

    Encodes the direction-asymmetric version of the Kaufman (1995) efficiency
    ratio. The unsigned ER was DISASTROUS at iter-v3/043 (IS -0.8445 / OOS
    -0.8990; all 4 symbols broken) because it treats trending-up and trending-
    down markets identically. This SIGNED variant adds directional information:

        +ER  → price moved efficiently in the LONG direction (trending up cleanly)
        -ER  → price moved efficiently in the SHORT direction (trending down cleanly)
         ≈0  → choppy / sideways regardless of direction

    Construction:
    - ``kaufman_er_50 = abs(close - close.shift(50)) / sum(abs(close.diff()), 50)``
      capped to [0, 1]; shift(1) applied to make it past-only.
    - ``ret_20d = log(close / close.shift(60))`` at 8h cadence (60 bars ≈ 20 days).
    - ``sign_ret_20d`` = sign(ret_20d); 0 if exactly flat (treated as NaN-equivalent
      below but left as 0.0 for numerical stability).
    - ``trend_efficiency_signed = kaufman_er_50 * sign_ret_20d``

    The sign factor converts the [0, 1] unsigned ER to [-1, +1] signed space.
    Output range: [-1, +1].

    Past-only by construction:
    - ``close.shift(50)`` and ``close.diff().rolling(50)`` use bars up to t-1
      after shift(1) is applied to the ER result.
    - ``close.shift(60)`` uses bar t-60 (past-only).
    - Appending future bars does NOT alter the value at t.

    NaN warm-up: first 61 bars are NaN (60-bar ret_20d dominates over 51-bar ER
    warm-up after shift(1)).

    IC carve-out: NOT applicable for the signed product. The ER primitive itself
    was Category 1 at iter-v3/043; the SIGNED COMPOSITION uses the existing
    efficiency_ratio_50 as a building block combined with ret_20d direction.
    This is a Category 2 composed feature per the ``feedback_v3_engineered_feature_pivot.md``
    methodology (composed feature gate: importance >= 30 in ≥2 symbols, NOT |IC|<0.70).

    Args:
        df: DataFrame with column ``close`` (float-castable).

    Returns:
        Copy of ``df`` with ``trend_efficiency_signed`` column appended.
        If ``close`` is missing, the column is set to all-NaN without error.
    """
    df = df.copy()
    if "close" not in df.columns:
        df["trend_efficiency_signed"] = np.nan
        return df

    close = df["close"].astype(float)

    # Kaufman ER (unsigned) at 50-bar window; shift(1) for past-only
    direction = (close - close.shift(50)).abs()
    noise = close.diff().abs().rolling(50, min_periods=50).sum()
    er = (direction / (noise + _TREND_EFFICIENCY_SIGNED_EPS)).clip(0.0, 1.0).shift(1)

    # 20-day direction (60 bars at 8h cadence = 20 calendar days)
    log_close = np.log(close.clip(lower=1e-12))
    ret_20d = log_close - log_close.shift(60)
    sign_ret_20d = np.sign(ret_20d)

    df["trend_efficiency_signed"] = er * sign_ret_20d
    return df


def compute_vol_regime_x_momentum(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: ret_5d × (atr_pct_rank_200 - 0.5).

    Encodes the vol-regime-conditional momentum signal (Asness, Moskowitz, &
    Pedersen 2013 value-and-momentum across asset classes; adapted to intraday
    vol percentile rank regime filter):

        - atr_pct_rank_200 > 0.5 → current vol ABOVE median → momentum signal
          gets positive sign (trending regime in high-vol environment)
        - atr_pct_rank_200 < 0.5 → current vol BELOW median → momentum signal
          gets negative sign (mean-reversion tendency in calm markets)
        - atr_pct_rank_200 == 0.5 → exactly at median → feature is 0.0

    Construction:
    - ``ret_5d = log(close / close.shift(15))`` at 8h cadence (15 bars ≈ 5 days).
    - ``atr_pct_rank_200``: 200-bar ATR percentile rank (computed by
      ``add_regime_v3_features``; upstream in GROUP_REGISTRY).
    - ``vol_regime_x_momentum = ret_5d * (atr_pct_rank_200 - 0.5)``

    Output range: approximately [-0.5, +0.5] (bounded by ret_5d and the [-0.5,
    +0.5] range of the centered ATR rank factor).

    Past-only by construction:
    - ``close.shift(15)``: uses bar t-15 (past-only).
    - ``atr_pct_rank_200`` is computed past-only by ``add_regime_v3_features``
      (200-bar trailing rolling window).
    - Appending future bars does NOT alter the value at t.

    NaN warm-up: first ~199 bars NaN (atr_pct_rank_200 dominates; requires
    200 bars for the rolling ATR percentile rank).

    Args:
        df: DataFrame with columns ``close`` (float-castable) and ``atr_pct_rank_200``
            (pre-computed by ``add_regime_v3_features``).

    Returns:
        Copy of ``df`` with ``vol_regime_x_momentum`` column appended.
        If ``atr_pct_rank_200`` is missing, the column is set to all-NaN without error.
    """
    df = df.copy()
    if "close" not in df.columns or "atr_pct_rank_200" not in df.columns:
        df["vol_regime_x_momentum"] = np.nan
        return df

    close = df["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    # 15 bars at 8h cadence = 5 calendar days
    ret_5d = log_close - log_close.shift(15)

    atr_rank = df["atr_pct_rank_200"].astype(float)
    vol_factor = atr_rank - 0.5  # centered at 0 when at median
    df["vol_regime_x_momentum"] = ret_5d * vol_factor
    return df


_RANGE_EFFICIENCY_50_EPS: float = 1e-9


def compute_range_efficiency_50(df: pd.DataFrame) -> pd.DataFrame:
    """Sign-invariant feature: Kaufman-style UNSIGNED path efficiency, 50-bar.

    iter-v3/076 NEW feature (cycle-2 EXPLORATION #6). A feature-internal IS-regime
    discriminator the LightGBM model learns: it measures HOW price has moved
    (clean efficient directional move vs choppy sideways grind), NOT WHICH WAY.

    Construction:
    - ``path  = |close[t] - close[t-50]|``  — net 50-bar directional displacement.
    - ``noise = sum_{k=1}^{50} |close[t-k+1] - close[t-k]|``  — total path length.
    - ``er    = path / (noise + 1e-9)``  — Kaufman (1995) efficiency ratio.
    - ``.clip(0.0, 1.0)``: bounded by the triangle inequality; clip guards float
      precision near 0 (noise sum can round below path from fp errors).
    - ``.shift(1)`` applied to the ER series: bar t's value uses close[t-51..t-1]
      only — the signal bar's own close is NEVER observed at inference time.
    - ``.fillna(0.0)`` on the first 51 warm-up bars: neutral 0.0 = maximally
      choppy (no directional efficiency); preferable to NaN propagation at
      training time.

    Output range [0, 1]. 1.0 = a perfectly clean monotone move; 0.0 = a choppy
    grind that ends where it started.

    SIGN-INVARIANT (the load-bearing property for iter-v3/076): the feature's
    value is the SAME for a clean up-trend and a clean down-trend, and the SAME
    for choppy grind regardless of net direction. It is therefore NOT a monotone
    proxy for the bull/bear regime axis — a choppy low-efficiency grind exists in
    BOTH bear and bull markets; a clean efficient move exists in BOTH. iter-v3/076
    EDA T3 verified |regime-sign correlation| = 0.010 (the feature's value
    distribution is statistically the same across the IS bear/chop window and the
    OOS uptrend window). This is what lets a model learn to down-weight the
    choppy-grind drag WITHIN IS bear/chop WITHOUT the IS-up/OOS-down trade-off
    that iter-v3/075 demonstrated is structural to a directional-regime
    discriminator. The feature's job is regime-QUALITY conditioning alongside the
    14 directional BASELINE_V3 features — NOT to provide direction itself.

    RE-EVALUATION DISCLOSURE (iter-v3/076 brief Section 10.2): this is the SAME
    Kaufman path-efficiency MATH as ``compute_efficiency_ratio_50`` (the unsigned
    ER feature ``efficiency_ratio_50`` that was DISASTROUS-NEGATIVE at
    iter-v3/043, IS -0.8445 / OOS -0.8990, and is on the BASELINE_V3.md "BANNED"
    list). ``range_efficiency_50`` is its deliberate, rule-sanctioned
    RE-EVALUATION under ``feedback_v3_walkforward_lookahead_bug.md`` (cycle-3
    verdicts pre-date the walk-forward fix and are eligible for re-evaluation),
    with (a) a DIFFERENT universe — the post-bootstrap 3-symbol BCH/LDO/TRX set,
    NOT /043's 4-symbol+ALGO universe; and (b) a DIFFERENT role — a 15th
    regime-QUALITY conditioning feature alongside 14 directional features, NOT a
    STANDALONE directional signal (which is how /043 used it, and why /043's
    docstring records the failure mode as "treats trending-up and trending-down
    markets identically"). The feature is named ``range_efficiency_50``, NOT
    ``efficiency_ratio_50``, so the literal-name pre-flight ban stays meaningful.
    The precedent for a same-family-different-role feature with a new name is
    ``compute_trend_efficiency_signed`` (iter-v3/063, the signed variant).

    Past-only by construction:
    - ``close.shift(50)``: bar t uses close[t-50]. Strictly past-only.
    - ``close.diff()``: bar t uses close[t] - close[t-1]. Past-only.
    - ``.rolling(50, min_periods=50).sum()``: sums bars [t-49..t]. Past-only.
    - ``.shift(1)`` on the ER result: the final bar-t value uses bars [t-51..t-1].
      This shift ensures bar t cannot observe close[t] at model-inference time.
    - Appending future bars t+1, t+2, ... does NOT alter the value at bar t (all
      operations are causal rolling windows terminated at bar t-1 after the shift).

    NaN warm-up: first 51 bars are NaN before fillna (50-bar rolling noise window
    + the shift(1)). After fillna(0.0) the first 51 bars are 0.0 (neutral). At 8h
    cadence: 51 bars ~= 17 calendar days, well within the 24-month IS window.

    Args:
        df: DataFrame with column ``close`` (float-castable).

    Returns:
        Copy of ``df`` with ``range_efficiency_50`` column appended (float, range
        [0.0, 1.0]). If ``close`` is missing, the column is set to all-NaN
        without error — the runner's ``_verify_feature_columns`` assertion
        catches the gap downstream.
    """
    df = df.copy()
    if "close" not in df.columns:
        df["range_efficiency_50"] = np.nan
        return df

    close = df["close"].astype(float)
    path = (close - close.shift(50)).abs()
    noise = close.diff().abs().rolling(50, min_periods=50).sum()
    er = (path / (noise + _RANGE_EFFICIENCY_50_EPS)).clip(0.0, 1.0)
    # .shift(1): bar t now sees close[t-51..t-1] only (past-only at inference).
    df["range_efficiency_50"] = er.shift(1).fillna(0.0)
    return df


def compute_ema_signed_volregime(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: ema_spread_atr_20 × sign(range_realized_vol_50 - rolling_median_200).

    Encodes a vol-regime-conditioned momentum signal at a slower timescale
    (~67 calendar days at 8h cadence) than /025's regime_momentum_signed_5d
    (~33-day Hurst regime).

    Construction:
    - ``ema_spread_atr_20``: 20-bar EMA spread normalised by ATR (computed by
      ``add_momentum_accel_v3_features``).
    - ``range_realized_vol_50``: 50-bar rolling realized vol from log-returns
      (computed by ``add_tail_risk_v3_features``).
    - ``vol_median_200``: trailing 200-bar rolling median of range_realized_vol_50
      (hand-chosen window per brief Section 0; matches longest TOP_N rolling
      window — hurst_200, atr_pct_rank_200 — and is structurally slower than
      the value primitive it conditions).
    - ``vol_regime_sign``: sign(range_realized_vol_50 − vol_median_200);
        +1 if realized vol > median (high-vol regime)
        −1 if realized vol < median (low-vol regime)
         0 (degenerate equality case) → treated as NaN (no signal)

    Past-only by construction:
    - ``ema_spread_atr_20`` is past-only (momentum_accel computed it past-only).
    - ``range_realized_vol_50`` is past-only (tail_risk computed it past-only).
    - ``rolling(window=200, min_periods=200).median()`` is a trailing window;
      value at t uses only bars 0..t-1+1 ≤ t. Both upstream primitives run
      BEFORE engineered_v3 in GROUP_REGISTRY; appending future bars does NOT
      alter the value at t.

    NaN warm-up: first 200 bars are NaN (vol_median_200 needs 200-bar
    history; the underlying primitives range_realized_vol_50 and
    ema_spread_atr_20 stabilise earlier so they are dominated).

    Args:
        df: DataFrame with columns ``ema_spread_atr_20`` (from momentum_accel)
            and ``range_realized_vol_50`` (from tail_risk).

    Returns:
        Copy of ``df`` with ``ema_signed_volregime`` column appended.
        If a source primitive is missing, the column is set to all-NaN
        without error (downstream feature-column assertion will fail loudly).
    """
    df = df.copy()
    if "ema_spread_atr_20" not in df.columns or "range_realized_vol_50" not in df.columns:
        df["ema_signed_volregime"] = np.nan
        return df
    ema = df["ema_spread_atr_20"].astype(float)
    rv = df["range_realized_vol_50"].astype(float)
    rv_med200 = rv.rolling(window=200, min_periods=200).median()
    vol_diff = rv - rv_med200
    sign_vol = np.sign(vol_diff)
    sign_vol = sign_vol.replace(0.0, np.nan)
    df["ema_signed_volregime"] = ema * sign_vol
    return df


def compute_ret5d_signed_tbi(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: ret_5d x sign(taker_buy_imbalance_20).

    Encodes an order-flow-regime-conditioned momentum signal at the
    microstructure timescale (~7 calendar days at 8h cadence via 20-bar
    taker-buy imbalance window). Structurally orthogonal to:
    - /025 regime_momentum_signed_5d (~33-day Hurst regime; long-memory)
    - /118 ema_signed_volregime (~67-day vol regime; return-volatility) — CLOSED

    Construction:
    - ``ret_5d``: log(close_t / close_{t-15}) at 8h cadence.
      15 bars x 8h = 120h ~= 5 calendar days. Past-only by .shift(15).
      Identical to the value primitive in regime_momentum_signed_5d (/025).
    - ``taker_buy_imbalance_20``: 20-bar rolling order-flow imbalance
      (precomputed by add_taker_buy_imbalance_20; past-only by construction).
      Threshold = 0 (zero-cross of imbalance; positive = buy-imbalanced;
      negative = sell-imbalanced).
    - ``order_flow_sign``: sign(taker_buy_imbalance_20);
        +1 if imbalance > 0 (buy-dominated regime) -> momentum confirmed
        -1 if imbalance < 0 (sell-dominated regime) -> momentum faded
         0 (degenerate zero case) -> treated as NaN (no signal)

    Past-only by construction:
    - ``ret_5d`` is past-only (log_close.shift(15)).
    - ``taker_buy_imbalance_20`` is past-only (microstructure_v3 computed it
      past-only at parquet generation).
    - Upstream primitives (close, taker_buy_imbalance_20) run BEFORE
      engineered_v3 in GROUP_REGISTRY; the past-only invariant is preserved.

    NaN warm-up: first 19 bars are NaN (taker_buy_imbalance_20 needs 20-bar
    history). ret_5d warm-up (15 bars) is dominated.

    Args:
        df: DataFrame with columns ``close`` (float-castable) and
            ``taker_buy_imbalance_20`` (from microstructure_v3).

    Returns:
        Copy of ``df`` with ``ret5d_signed_tbi`` column appended.
        If a source primitive is missing, the column is set to all-NaN
        without error (downstream feature-column assertion will fail loudly).
    """
    df = df.copy()
    if "close" not in df.columns or "taker_buy_imbalance_20" not in df.columns:
        df["ret5d_signed_tbi"] = np.nan
        return df
    close = df["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    # 15 bars at 8h cadence = 5 calendar days (identical to /025's ret_5d)
    ret_5d = log_close - log_close.shift(15)
    tbi = df["taker_buy_imbalance_20"].astype(float)
    sign_tbi = np.sign(tbi)
    # Zero-imbalance edge case: treat as NaN (no signal)
    sign_tbi = sign_tbi.replace(0.0, np.nan)
    df["ret5d_signed_tbi"] = ret_5d * sign_tbi
    return df


def add_engineered_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """GROUP_REGISTRY entry point for all Category 2 (composed) v3 features.

    iter-v3/048: vol_normalized_ret_5d ADDED to dispatch (NEW 15th feature in
    V3_FEATURE_COLUMNS_TOP_N). Composed feature: ret_5d / (range_realized_vol_50 + ε).
    Canonical Sharpe-like risk-normalized momentum (Sinclair, Vol Trading; LdP AFML Ch. 8).
    range_realized_vol_50 is rank-1 TRX importance (313/313; mean rank 3.00 across 4 symbols).
    TRX has flat importance distribution (2.5× top:bottom ratio) — risk-normalized momentum
    may give Optuna better split quality on TRX (the IS-axis-bottleneck symbol).
    IC carve-out applies per feedback_v3_engineered_feature_pivot.md.
    Cycle 3 plan Axis 1; QR EDA SHA a230cd1; cycle 3 #9 of 10.

    iter-v3/044: regime_momentum_signed_3d UNIVERSAL DISPATCH REVERTED. The orchestrator's
    setup commit `1f56c72` added 3d to dispatch + V3_FEATURE_COLUMNS_TOP_N as a 15th feature.
    QR EDA at SHA `eff841e` (cycle3_is_diagnosis.py) established that the IS bottleneck
    is direction-asymmetric per-symbol (ALGO LONG single largest attribution loss); the 3d
    variant does NOT discriminate ALGO LONG WR (22.2% > 0, 13.3% <=0) and ranks 14/14 in
    ALGO model. Universal addition would dilute colsample picks without addressing the
    bottleneck. compute_regime_momentum_signed_3d retained as dead code (zero revert cost,
    available for future per-symbol experiments); NOT dispatched. Replacement axis:
    per-symbol ATR widening for ALGOUSDT only (V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"]
    = (2.0, 1.5)). efficiency_ratio_50 also removed from dispatch (iter-v3/043 DISASTROUS
    NEGATIVE; dead code retained).

    iter-v3/043: efficiency_ratio_50 ADDED to dispatch — DISASTROUS NEGATIVE (IS -0.8445
    / OOS -0.8990; all 4 symbols broken). Removed from dispatch at iter-v3/044.
    compute_efficiency_ratio_50 retained as dead code; NOT dispatched.

    iter-v3/037: cross_asset_divergence_norm RE-DISPATCHED for per-symbol parquet generation.
    ``compute_cross_asset_divergence_norm`` was dead code since iter-v3/028. Re-adding to
    dispatch adds the column to ALL symbol parquets (same pattern as fracdiff_d05_close).
    Only LDOUSDT's explicit ``feature_columns=`` list (via V3_FEATURES_PER_SYMBOL) includes
    ``cross_asset_divergence_norm`` at model-train time. BCH/TRX/ALGO parquets contain the
    column but it is NOT passed to LightGBM for those symbols. Tests whether LDO-specific
    BTC-coupling signal works in isolation (iter-v3/027 universal application failed with
    IS Sharpe collapse -0.2817 + OOS spike +1.6786; 3-iter monotonic IS degradation).
    LDO rationale: btc_ret_14d rank 6 in LDO model (iter-v3/035); LDO OOS wpnl +3.98
    (weakest contributor, 35.0% WR) — primary target for BTC-coupling signal improvement.

    iter-v3/036 (REVERTED): vol_adj_autocorr was dispatched for TRX-only per-symbol parquet.
    TRX entry in V3_FEATURES_PER_SYMBOL REMOVED (iter-v3/036 NEGATIVE result: TRX OOS wpnl
    fell ~15 units vs iter-v3/035 anchor). ``compute_vol_adj_autocorr`` reverted to dead code.

    iter-v3/034: fracdiff_d05_close ADDED (LdP AFML Ch. 5 FFD at d=0.5;
    fixed-window fractional differentiation of log(close); memory-preserving
    stationary feature complementary to regime_momentum_signed_5d).

    iter-v3/028: cross_asset_divergence_norm DROPPED from dispatch (revert 15 → 14;
    matches iter-v3/025 anchor exactly; stacking FALSIFIED at iter-v3/027 per
    `feedback_v3_engineered_features_dont_stack.md`).  ``compute_cross_asset_divergence_norm``
    was RETAINED as dead code at zero revert cost.  Per Critic FINAL ``966f4c1`` of
    iter-v3/027 + user directive 2026-05-08.

    Currently computes (dispatch order):
    - ``regime_momentum_signed_5d`` (iter-v3/025, KEPT): composed feature combining
      5-day momentum with Hurst regime classifier.  Depends on ``hurst_100``
      from ``regime`` group (upstream in GROUP_REGISTRY).
    - ``fracdiff_d05_close`` (iter-v3/034, KEPT): FFD of log(close) at d=0.5.
      Depends only on ``close`` column.  BCH-only at model level (V3_FEATURES_PER_SYMBOL).
    - ``cross_asset_divergence_norm`` (iter-v3/037, RE-ADDED to dispatch):
      (sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + 1e-6). LDO-only at model level
      (V3_FEATURES_PER_SYMBOL["LDOUSDT"]).  Column is generated for all symbols so
      LDO's parquet contains it; BCH/TRX/ALGO parquets also contain it but it is NOT
      passed to LightGBM for those symbols.  Depends on ``btc_ret_14d`` (cross_btc group)
      and ``vwap_dev_20`` (volume_micro group), both upstream in GROUP_REGISTRY.
    - ``vol_normalized_ret_5d`` (iter-v3/048, NEW; dispatched universally):
      ret_5d / (range_realized_vol_50 + 1e-6). Risk-normalized 5-day momentum. ALL 4
      symbols receive the column in their parquets AND it is in V3_FEATURE_COLUMNS_TOP_N
      (universal model-level dispatch). Depends on ``range_realized_vol_50`` from
      ``tail_risk`` group (upstream in GROUP_REGISTRY).

    Dead code retained (zero revert cost):
    - ``compute_vol_adj_autocorr``: reverted at iter-v3/037 (iter-v3/036 NEGATIVE).
    - ``compute_efficiency_ratio_50``: DISASTROUS NEGATIVE at iter-v3/043 (IS -0.8445 /
      OOS -0.8990; all 4 symbols broken); removed from dispatch at iter-v3/044.
    - ``compute_regime_momentum_signed_3d``: ad-hoc orchestrator pick at iter-v3/044
      setup commit `1f56c72`; REVERTED before backtest based on QR EDA at SHA `eff841e`
      (does not address direction-asymmetric per-symbol IS bottleneck — ALGO LONG WR not
      discriminated by 3d sign; ranks 14/14 in ALGO model).

    Each new composed feature must be listed in the iteration's research brief Section
    2.2 and validated with an adversarial past-only test.

    Args:
        df: DataFrame that has already been processed by ``add_regime_v3_features``
            (so ``hurst_100`` is available for regime_momentum_signed_5d),
            ``add_cross_btc_v3_features`` (so ``btc_ret_14d`` is available for
            cross_asset_divergence_norm), and ``add_volume_micro_v3_features``
            (so ``vwap_dev_20`` is available for cross_asset_divergence_norm).
            All upstream in GROUP_REGISTRY.

    Returns:
        Copy of ``df`` with all active engineered v3 features appended.
    """
    df = compute_regime_momentum_signed_5d(df)  # iter-v3/025 (KEPT; mandated by engineered pivot)
    # iter-v3/052: fracdiff_d05_close PARKED (dropped from V3_FEATURE_COLUMNS_TOP_N; column
    # still generated for zero-revert-cost per /051 PARKED policy). Compute call RETAINED.
    df = compute_fracdiff_d05_close(df)  # iter-v3/034 (PARKED at /052; column generated but unused)
    # iter-v3/063: trend_efficiency_signed ADDED — Kaufman ER × sign(ret_20d).
    # Signed variant of the unsigned ER that was DISASTROUS at /043 (IS -0.8445 / OOS -0.8990).
    # Direction flip addresses the bottleneck: unsigned ER treats long/short trends identically.
    # Category 2 composed feature; IC carve-out applies per feedback_v3_engineered_feature_pivot.md.
    df = compute_trend_efficiency_signed(df)  # iter-v3/063 NEW (ACTIVATED)
    # iter-v3/063: vol_regime_x_momentum ADDED — ret_5d × (atr_pct_rank_200 - 0.5).
    # Momentum signal conditioned on vol regime (above/below 200-bar ATR median).
    # Depends on atr_pct_rank_200 from add_regime_v3_features (upstream in GROUP_REGISTRY).
    df = compute_vol_regime_x_momentum(df)  # iter-v3/063 NEW (ACTIVATED)
    df = compute_cross_asset_divergence_norm(df)  # iter-v3/037 RE-ADDED (LDO-only at model level)
    # iter-v3/048: vol_normalized_ret_5d ADDED (15th feature in V3_FEATURE_COLUMNS_TOP_N).
    # Canonical Sharpe-like risk-normalized momentum: ret_5d / (range_realized_vol_50 + ε).
    # range_realized_vol_50 is rank-1 TRX importance (313/313) and mean rank 3.00 across all 4
    # symbols. TRX has flat importance distribution (2.5× ratio) — model can't discriminate.
    # Depends on range_realized_vol_50 from add_tail_risk_v3_features (upstream in GROUP_REGISTRY).
    # IC carve-out per feedback_v3_engineered_feature_pivot.md (Category 2 composed feature).
    # Cycle 3 plan Axis 1 per feedback_v3_axis_selection_quant_discipline.md.
    # iter-v3/049: vol_normalized_ret_5d DROPPED from V3_FEATURE_COLUMNS_TOP_N (PATH C-clean);
    #   compute_vol_normalized_ret_5d retained in dispatch as inert column (zero revert cost).
    df = compute_vol_normalized_ret_5d(df)  # iter-v3/048 (inert; DROPPED from TOP_N at /049)
    # iter-v3/052: ACTIVATE compute_regime_momentum_signed_3d dispatch (was dead code since /044
    #   revert). PIVOT from orchestrator-mandated LDO-removal axis (pre-falsified by /052 EDA SHA
    #   `0a10581`) to QR-EDA-backed /051 RANKED #2 (SHA `290f37b`).
    #   Mechanism: ret_3d × sign(hurst_100 − 0.5). Orthogonal time-scale variant of
    #   regime_momentum_signed_5d (iter-v3/028 baseline edge ingredient; multi-seed validated).
    #   IC strict-gate PASS: max|IC|=0.6192<0.70 all 4 syms (NO carve-out needed).
    #   ADF stationary p=0 all 4 syms. Univariate ρ -0.057 mean (stronger than fracdiff -0.044).
    #   IC with 5d sister 0.43-0.47 (below 0.50 stacking-risk threshold from iter-v3/026).
    #   /044 ALGO LONG falsification CONDITIONAL on ALGO universe; ALGO REVERTED at /051+/052.
    #   fracdiff_d05_close PARKED: column still computed (above) but dropped from
    #   V3_FEATURE_COLUMNS_TOP_N; compute + 5 adversarial tests retained (zero revert cost).
    # iter-v3/052: regime_momentum_signed_3d ACTIVATED (SWAP fracdiff → 3d at 15th slot).
    # iter-v3/053: regime_momentum_signed_3d DROPPED from V3_FEATURE_COLUMNS_TOP_N (PARKED per
    #   /052 closeout PATH C-suspicious; dispatch call RETAINED at zero revert cost).
    df["regime_momentum_signed_3d"] = compute_regime_momentum_signed_3d(
        df
    )  # dead code at /053 (PARKED)
    # iter-v3/053: hurst_drift_50_200 ADDED — NEW dispatch at /053 setup.
    #   Mechanism: hurst_50 − hurst_200 = hurst_100 − hurst_diff_100_50 − hurst_200.
    #   Category 1 NEW engineered feature; REFRAMED HYPOTHESIS B (LR-PF methodology doc).
    #   R^2=1.0 linear redundancy with 3 source primitives (EDA SHA `1fc6d55`
    #   axis5_linear_redundancy.csv).
    #   Univariate Spearman ρ NOT significant at p<0.05 in any of 4 symbols (mean +0.0114).
    #   Max |IC| 0.85-0.88 with hurst_diff_100_50 (source primitive); Category 2 carve-out applies.
    #   Feature is computable from existing parquet columns — NO parquet regen required.
    df = compute_hurst_drift_50_200(df)  # iter-v3/053 ACTIVATE
    # iter-v3/076: range_efficiency_50 ADDED — Kaufman-style UNSIGNED 50-bar path
    # efficiency. The cycle-2 EXPLORATION #6 axis: a sign-invariant feature-internal
    # IS-regime discriminator the model learns. SIGN-INVARIANT (regime-sign |corr|
    # 0.010 per /076 EDA T3) — it measures HOW price moves, not WHICH WAY, so it
    # breaks the /075 IS-up/OOS-down tension (a directional-regime discriminator
    # de-rates IS and OOS together; a regime-orthogonal feature does not).
    # RE-EVALUATION of the /043-DISASTROUS efficiency_ratio_50 math under
    # feedback_v3_walkforward_lookahead_bug.md, on the 3-symbol universe, as a
    # regime-QUALITY conditioning feature (NOT a standalone directional signal).
    # See compute_range_efficiency_50 docstring + /076 brief Section 10.2.
    df = compute_range_efficiency_50(df)  # iter-v3/076 (PARKED — reverted /077; dead code)
    # iter-v3/118: ema_signed_volregime ADDED — NEW 15th feature in V3_FEATURE_COLUMNS_TOP_N.
    # Category-2 composed feature: ema_spread_atr_20 × sign(range_realized_vol_50 - median_200).
    # Vol-regime-conditioned momentum at ~67-day rolling-median timescale (slower than /025's
    # ~33-day Hurst-regime timescale). T9 POOLED multivariate-lift +0.0081 (> 0.005 gate);
    # importance rank 8-10/15, gain 38-63% across all 3 symbols (EDA SHA `60a45e8`).
    # Depends on ema_spread_atr_20 (momentum_accel) and range_realized_vol_50 (tail_risk),
    # both upstream in GROUP_REGISTRY. Section 0 hand-chosen: rolling-median window = 200 bars.
    # /025 PROMISING lineage; per `feedback_v3_engineered_features_proven.md`.
    df = compute_ema_signed_volregime(df)  # iter-v3/118 (DEAD CODE — REMOVED from TOP_N at /119)
    df = compute_ret5d_signed_tbi(df)  # iter-v3/119 NEW (15th V3_FEATURE_COLUMNS feature)
    # compute_efficiency_ratio_50 REMOVED from dispatch at iter-v3/044 — DISASTROUS NEGATIVE.
    # compute_vol_adj_autocorr REVERTED at iter-v3/037 — iter-v3/036 NEGATIVE; dead code.
    return df


# ===========================================================================
# iter-v3/085 — funding-regime-conditioned momentum (cycle-3 EXPLORATION #4)
# ===========================================================================

_FUNDING_REGIME_Z_WINDOW: int = 30  # 30 8h funding-settlement cycles = 10 days
_FUNDING_REGIME_Z_EPS: float = 1e-9


def compute_funding_regime_momentum_5d(df: pd.DataFrame, funding_df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: regime_momentum_signed_5d × sign(funding_z_30).

    iter-v3/085 — cycle-3 EXPLORATION #4. A Category-2 composed feature: the
    regime-conditioned momentum primitive ``regime_momentum_signed_5d`` is
    sign-switched a SECOND time by the prevailing funding-CROWDING regime.

    Hypothesis: momentum into a crowded long is exhaustion (fade it); momentum
    into a crowded short is a squeeze setup (follow it). The funding rate
    encodes positioning crowding; a depth-4 LightGBM cannot compose this
    funding×momentum sign-interaction from the primitives.

    THIS IS NOT THE CLOSED v3 FUNDING AXIS. The closed axis (/019/023/024/082 —
    ``funding_rate_zscore_30``, ``btc_funding_rate_zscore_30``, the /082 4-channel
    family) fed funding as a DIRECT model feature. Here the funding rate enters
    ONLY as a ``sign()`` switch inside a composed feature — it is never a column
    the tree splits on directly. Category-2 composed construction (the
    ``feedback_v3_engineered_feature_pivot.md`` carve-out family).

    Construction:
    - ``regime_momentum_signed_5d``: the existing composed primitive
      (``ret_5d × sign(hurst_100 − 0.5)``) — must be present in ``df`` (it is
      computed earlier in ``add_engineered_v3_features``).
    - ``funding_z_30``: 30-period (10-day) z-score of the past-only funding rate
      = ``(rate − mean(rate.shift(1), 30)) / (std(rate.shift(1), 30) + 1e-9)``.
    - ``funding_regime_momentum_5d = regime_momentum_signed_5d × sign(funding_z_30)``.
      ``sign(0) == 0`` only for exactly-zero funding-z (degenerate early-window
      rows); 0 is replaced with NaN so the composed feature is NaN there.

    Past-only by construction (Critic Check 1):
    - ``regime_momentum_signed_5d`` is verified past-only (see
      ``compute_regime_momentum_signed_5d``).
    - ``funding_rate[t]`` settled at candle ``open_time`` and is broadcast
      ~5 min before the 8h boundary — knowable at bar t open (the identical
      convention ``funding_v3.compute_funding_family`` uses).
    - ``funding_z_30`` applies ``rate.shift(1)`` BEFORE the 30-bar rolling
      mean/std, so bar t's own settlement never enters its own z-score window.
    - The composed feature is an element-wise product of two past-only series.

    Args:
        df: DataFrame with ``open_time``, ``close`` and ``regime_momentum_signed_5d``.
        funding_df: DataFrame with ``funding_time`` (ms int) and ``funding_rate``.

    Returns:
        Copy of ``df`` with ``funding_regime_momentum_5d`` appended. If
        ``regime_momentum_signed_5d`` is missing the column is all-NaN (the
        pipeline then fails loudly at the downstream feature-column assertion).
    """
    df = df.copy()

    if "regime_momentum_signed_5d" not in df.columns:
        df["funding_regime_momentum_5d"] = np.nan
        return df

    # --- merge funding rate (round to minute to absorb settlement jitter) ----
    funding = funding_df.copy()
    funding["open_time_aligned"] = (funding["funding_time"] // 60_000) * 60_000
    df["open_time_aligned"] = (df["open_time"] // 60_000) * 60_000
    merged = df.merge(
        funding[["open_time_aligned", "funding_rate"]],
        on="open_time_aligned",
        how="left",
    ).drop(columns=["open_time_aligned"])
    merged.index = df.index
    df = df.drop(columns=["open_time_aligned"])
    r = merged["funding_rate"].astype(float)

    # --- funding_z_30 — PAST-ONLY: .shift(1) before the rolling window -------
    fr_lag = r.shift(1)
    fz = (
        r - fr_lag.rolling(_FUNDING_REGIME_Z_WINDOW, min_periods=_FUNDING_REGIME_Z_WINDOW).mean()
    ) / (
        fr_lag.rolling(_FUNDING_REGIME_Z_WINDOW, min_periods=_FUNDING_REGIME_Z_WINDOW).std(ddof=1)
        + _FUNDING_REGIME_Z_EPS
    )

    # --- the composed feature ------------------------------------------------
    # sign(funding_z); 0 (exactly-zero funding-z) -> NaN so the product is NaN.
    funding_regime_sign = np.sign(fz).replace(0.0, np.nan)
    df["funding_regime_momentum_5d"] = (
        df["regime_momentum_signed_5d"].astype(float) * funding_regime_sign
    )
    return df


def add_funding_regime_momentum_v3_features(
    df: pd.DataFrame, data_dir: Path | str = _DEFAULT_DATA_DIR
) -> pd.DataFrame:
    """GROUP_REGISTRY entry point for ``funding_regime_momentum_v3`` (iter-v3/085).

    Reads the per-symbol ``data/funding_rates/<SYMBOL>.csv`` cache (the same
    cache ``add_funding_family_v3_features`` uses; populated by
    ``uv run crypto-trade fetch-funding``) and appends ``funding_regime_momentum_5d``.

    MUST be registered AFTER ``engineered_v3`` in GROUP_REGISTRY — it depends on
    ``regime_momentum_signed_5d`` being computed by ``add_engineered_v3_features``.

    Raises:
        KeyError: if ``df`` has no ``symbol`` column.
        FileNotFoundError: if the funding-rate cache for the symbol is absent.
    """
    data_dir = Path(data_dir)
    symbol = df["symbol"].iloc[0] if "symbol" in df.columns else None
    if symbol is None:
        raise KeyError(
            "df must contain a 'symbol' column for the funding_regime_momentum_v3 "
            "feature group. Set df['symbol'] = '<SYMBOL>' before calling "
            "add_funding_regime_momentum_v3_features."
        )
    cache_path = data_dir / "funding_rates" / f"{symbol}.csv"
    if not cache_path.exists():
        raise FileNotFoundError(
            f"Funding-rate cache not found: {cache_path}. "
            f"Run: uv run crypto-trade fetch-funding --symbols {symbol}"
        )
    funding_df = pd.read_csv(cache_path)
    if len(funding_df) == 0:
        df = df.copy()
        df["funding_regime_momentum_5d"] = np.nan
        return df
    return compute_funding_regime_momentum_5d(df, funding_df)


__all__ = [
    "add_engineered_v3_features",
    "add_funding_regime_momentum_v3_features",
    "compute_cross_asset_divergence_norm",
    "compute_efficiency_ratio_50",
    "compute_ema_signed_volregime",
    "compute_fracdiff_d05_close",
    "compute_funding_regime_momentum_5d",
    "compute_hurst_drift_50_200",
    "compute_range_efficiency_50",
    "compute_regime_momentum_signed_3d",
    "compute_regime_momentum_signed_5d",
    "compute_ret5d_signed_tbi",
    "compute_trend_efficiency_signed",
    "compute_vol_adj_autocorr",
    "compute_vol_normalized_ret_5d",
    "compute_vol_regime_x_momentum",
]
