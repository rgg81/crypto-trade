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


def add_engineered_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """GROUP_REGISTRY entry point for all Category 2 (composed) v3 features.

    iter-v3/044: regime_momentum_signed_3d ADDED to dispatch. 3-bar variant of the proven
    regime_momentum_signed_5d sign-flip mechanism. ret_3d = close.shift(1)/close.shift(4) - 1.0;
    same hurst_100 sign-flip as 5d variant; different lookback horizon (1 day vs 5 days).
    Column added to ALL symbol parquets; ALL 4 symbols receive it via V3_FEATURE_COLUMNS_TOP_N
    at model-train time (15 features). Past-only: close.shift(1), close.shift(4), hurst.shift(1).
    efficiency_ratio_50 removed from dispatch (iter-v3/043 DISASTROUS NEGATIVE; dead code retained).

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
    - ``regime_momentum_signed_3d`` (iter-v3/044, NEW): 3-bar variant of the sign-flip.
      ret_3d = close.shift(1)/close.shift(4) - 1.0 * sign(hurst_100.shift(1) - 0.5).
      Depends on ``hurst_100`` from ``regime`` group (upstream in GROUP_REGISTRY).
      Universal: ALL 4 symbols receive it via V3_FEATURE_COLUMNS_TOP_N (15 features).
    - ``fracdiff_d05_close`` (iter-v3/034, KEPT): FFD of log(close) at d=0.5.
      Depends only on ``close`` column.  BCH-only at model level (V3_FEATURES_PER_SYMBOL).
    - ``cross_asset_divergence_norm`` (iter-v3/037, RE-ADDED to dispatch):
      (sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + 1e-6). LDO-only at model level
      (V3_FEATURES_PER_SYMBOL["LDOUSDT"]).  Column is generated for all symbols so
      LDO's parquet contains it; BCH/TRX/ALGO parquets also contain it but it is NOT
      passed to LightGBM for those symbols.  Depends on ``btc_ret_14d`` (cross_btc group)
      and ``vwap_dev_20`` (volume_micro group), both upstream in GROUP_REGISTRY.

    Dead code retained (zero revert cost):
    - ``compute_vol_adj_autocorr``: reverted at iter-v3/037 (iter-v3/036 NEGATIVE).
    - ``compute_efficiency_ratio_50``: DISASTROUS NEGATIVE at iter-v3/043 (IS -0.8445 /
      OOS -0.8990; all 4 symbols broken); removed from dispatch at iter-v3/044.

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
    df["regime_momentum_signed_3d"] = compute_regime_momentum_signed_3d(df)  # iter-v3/044 (NEW)
    df = compute_fracdiff_d05_close(df)  # iter-v3/034 (KEPT; BCH-only at model level)
    df = compute_cross_asset_divergence_norm(df)  # iter-v3/037 RE-ADDED (LDO-only at model level)
    # compute_efficiency_ratio_50 REMOVED from dispatch at iter-v3/044 — DISASTROUS NEGATIVE.
    # compute_vol_adj_autocorr REVERTED at iter-v3/037 — iter-v3/036 NEGATIVE; dead code.
    return df


__all__ = [
    "add_engineered_v3_features",
    "compute_cross_asset_divergence_norm",
    "compute_efficiency_ratio_50",
    "compute_fracdiff_d05_close",
    "compute_regime_momentum_signed_3d",
    "compute_regime_momentum_signed_5d",
    "compute_vol_adj_autocorr",
]
