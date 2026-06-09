"""v1 composed (engineered) features — iter-v1/040 (feature-family EXPLORATION #7/10 cycle-5).

Track-isolated: ZERO imports from crypto_trade.features_v2 or crypto_trade.features_v3.
The Hurst R/S math is COPIED (not imported) from features_v3/regime_v3.py to maintain
v1↔v3 isolation per the v1 track discipline.

Composed feature exported:
  - ``regime_momentum_signed_5d``: ret_5d × sign(hurst_100 − 0.5)

Feature definition (canonical):

    ret_5d[t]                    = log(close[t]) − log(close[t−15])
                                   (15 bars × 8h = 120h ≈ 5 calendar days)
    hurst_100[t]                 = rolling 100-bar R/S Hurst exponent of log(close)
                                   (window ends at bar t; first valid at bar 99)
    regime_sign[t]               = sign(hurst_100[t] − 0.5)
                                   +1 if trending, −1 if mean-reverting, NaN if = 0.5
    regime_momentum_signed_5d[t] = ret_5d[t] × regime_sign[t]

EDA finding (iter-v1/040 eda.py):
    sign(hurst_100 − 0.5) = +1 in 100% of IS samples for all 5 v1 symbols. The feature
    is therefore mechanically equivalent to ret_5d (15-bar log return). The lift seen in
    v3/025 PROMISING + v3/028 CONFIRMATION-MERGE is attributed to the NEW 15-bar (120h)
    momentum horizon — not to the regime-conditioning sign flip. v1 currently has
    stat_log_return_5 (5-bar = 40h); this adds a 3× longer horizon.

Stationarity:
    ADF p-value < 2e-13 for all 5 v1 IS symbols (documented in EDA, Section 1.2).

Past-only discipline:
    - ret_5d[t] uses close[t-15..t] via log_close.shift(15) — no future leak.
    - hurst_100[t] is computed by _rolling_hurst (values[i-window:i]) — the value
      stored at index i is the R/S slope over bars i-window..i-1, ending strictly
      BEFORE bar i. The rolling_hurst implementation is BYTE-FOR-BYTE identical to
      features_v3/regime_v3.py:69-75 — past-only invariant already verified by
      v3 test suite.

NaN burn-in:
    First max(15, 100) - 1 = 99 bars are NaN (hurst_100 dominates).

Track isolation enforcement:
    Phase 6.0 pre-flight Critic verifies:
        grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v1/
        grep -r "from crypto_trade.features_v3" src/crypto_trade/features_v1/
    Both must return empty. This module has ZERO such imports.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Hurst R/S helpers — BYTE-FOR-BYTE copies from features_v3/regime_v3.py:34-75
# (copied not imported for v1 track isolation)
# ---------------------------------------------------------------------------


def _hurst_rs(window: np.ndarray) -> float:
    """Rescaled-range Hurst exponent for a single 1D window of log prices.

    BYTE-FOR-BYTE copy from src/crypto_trade/features_v3/regime_v3.py:34-66.
    Retained here for v1 track isolation (no cross-track imports).
    """
    n = len(window)
    if n < 20:
        return np.nan
    lags = [5, 10, 20, 30, 50, 80]
    lags = [lag for lag in lags if lag < n]
    if len(lags) < 3:
        return np.nan
    rs_values: list[float] = []
    log_lags: list[float] = []
    for lag in lags:
        chunks = n // lag
        if chunks < 1:
            continue
        r_list: list[float] = []
        for i in range(chunks):
            chunk = window[i * lag : (i + 1) * lag]
            mean = chunk.mean()
            devs = chunk - mean
            cumdev = np.cumsum(devs)
            r = cumdev.max() - cumdev.min()
            s = chunk.std(ddof=1)
            if s > 0 and np.isfinite(r):
                r_list.append(r / s)
        if r_list:
            rs_values.append(np.mean(r_list))
            log_lags.append(np.log(lag))
    if len(rs_values) < 3:
        return np.nan
    log_rs = np.log(rs_values)
    slope, _ = np.polyfit(log_lags, log_rs, 1)
    return float(slope)


def _rolling_hurst(log_close: pd.Series, window: int) -> pd.Series:
    """Rolling Hurst exponent via rescaled range. Returns NaN until window filled.

    BYTE-FOR-BYTE copy from src/crypto_trade/features_v3/regime_v3.py:69-75.
    Retained here for v1 track isolation (no cross-track imports).
    """
    values = log_close.to_numpy()
    out = np.full(len(values), np.nan, dtype=np.float64)
    for i in range(window, len(values) + 1):
        out[i - 1] = _hurst_rs(values[i - window : i])
    return pd.Series(out, index=log_close.index)


# ---------------------------------------------------------------------------
# Composed feature computation
# ---------------------------------------------------------------------------


def compute_regime_momentum_signed_5d(
    df: pd.DataFrame,
    ret_window_bars: int = 15,
    hurst_window: int = 100,
) -> pd.DataFrame:
    """Compute regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5).

    Computes both ret_5d and hurst_100 from scratch if hurst_100 is not
    already in ``df``. This allows the function to be used standalone (e.g.
    in tests or in the feature CLI single-group mode).

    Parameters
    ----------
    df:
        Kline DataFrame with at least ``close`` (float-castable) column.
    ret_window_bars:
        Number of bars for the log-return look-back (default 15 = 5 days at 8h).
    hurst_window:
        Rolling window in bars for the R/S Hurst exponent (default 100).

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with ``regime_momentum_signed_5d`` column appended.
        Rows where sign(hurst_100 − 0.5) == 0 (pure random walk) are set to NaN.
        First max(ret_window_bars, hurst_window) − 1 rows are NaN (burn-in).

    Notes
    -----
    Past-only by construction:
    - ret_5d[t] = log_close[t] − log_close[t − ret_window_bars].
      The shift(ret_window_bars) ensures only past bars are used.
    - hurst_100[t] is computed over values[t-window:t] ending strictly before t+1
      (values[i-window:i] in _rolling_hurst; the bar-i value uses bars i-window to i-1).
    """
    df = df.copy()
    close = df["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))

    # ret_5d: past-only by shift(ret_window_bars)
    ret_5d = log_close - log_close.shift(ret_window_bars)

    # hurst_100: compute from log_close if not already present
    if "hurst_100" not in df.columns:
        df["hurst_100"] = _rolling_hurst(log_close, hurst_window)

    hurst = df["hurst_100"].astype(float)
    sign_hurst = np.sign(hurst - 0.5)
    # Pure random-walk edge case (hurst_100 == 0.5 → sign = 0): treat as NaN.
    sign_hurst = sign_hurst.replace(0.0, np.nan)

    df["regime_momentum_signed_5d"] = ret_5d * sign_hurst
    return df


def add_composed_v1_features(
    df: pd.DataFrame,
    ret_window_bars: int = 15,
    hurst_window: int = 100,
) -> pd.DataFrame:
    """Registry wrapper: add all composed v1 features to ``df``.

    Currently adds: ``regime_momentum_signed_5d``.

    Called by the v1 features registry (features/__init__.py GROUP_REGISTRY)
    via ``uv run crypto-trade features --track v1 --groups composed_v1``.

    Parameters
    ----------
    df:
        Kline DataFrame with at least ``close`` (float-castable) column.
    ret_window_bars:
        Log-return look-back in bars (default 15 = 5 days at 8h cadence).
    hurst_window:
        Rolling Hurst window in bars (default 100).

    Returns
    -------
    pd.DataFrame
        Input df with ``regime_momentum_signed_5d`` column appended.
    """
    return compute_regime_momentum_signed_5d(
        df, ret_window_bars=ret_window_bars, hurst_window=hurst_window
    )


# ---------------------------------------------------------------------------
# iter-v1/085 composed features — UNI specialist mean-reversion set
# ---------------------------------------------------------------------------

# Constants for rev_halflife_50
REV_HALFLIFE_AR_WINDOW: int = 50  # trailing AR(1) window for phi estimation
REV_HALFLIFE_ZNORM_WINDOW: int = 90  # z-normalization window for the half-life series
REV_HALFLIFE_CAP: float = 50.0  # cap for extreme/undefined half-life (in bars)
REV_HALFLIFE_CLIP: float = 5.0  # final z-score clip

# Constants for rev_vol_gate_signed
REV_VOL_GATE_SOFT_LO: float = 0.0  # vol_state_z_natr_30 threshold: gate=1 below this
REV_VOL_GATE_SOFT_HI: float = 1.0  # vol_state_z_natr_30 threshold: gate=0 above this


def compute_rev_halflife_50(
    df: pd.DataFrame,
    ar_window: int = REV_HALFLIFE_AR_WINDOW,
    znorm_window: int = REV_HALFLIFE_ZNORM_WINDOW,
    cap: float = REV_HALFLIFE_CAP,
    clip: float = REV_HALFLIFE_CLIP,
) -> pd.DataFrame:
    """Compute ``rev_halflife_50`` = z-normalized rolling AR(1) mean-reversion half-life.

    Measures how fast returns oscillate/revert in a trailing 50-bar window.
    Separates fast-reverting regimes (actionable at 21-bar timeout) from slow-drift
    regimes that look reverting but aren't tradeable at this horizon.

    Definition (past-only, IS-safe):
        ret_1[t]         = log(close[t] / close[t-1])   (1-bar log return)
        phi[t]           = Pearson corr of ret_1[k] on ret_1[k-1] over k in [t-49, t]
                           (rolling AR(1) lag-1 autocorr via rolling(50).apply(corr_lag1))
        half_life_raw[t] = ln(0.5) / ln(|phi[t]|)  when 0 < |phi[t]| < 1 (oscillatory)
                           else cap (no reversion or undefined)
        half_life_raw    clipped to [0, cap]
        rev_halflife_50[t] = z-score of half_life_raw over trailing znorm_window bars,
                             clipped [-clip, +clip], then shifted by 1.

    When phi ≈ -1, half-life ≈ 0 (oscillating every bar — fast reversion).
    When phi ≈ 0,  half-life → ∞ → capped at cap (random walk, no reversion).

    Parameters
    ----------
    df:
        Kline DataFrame with ``close`` (float-castable) column.
    ar_window:
        Trailing window in bars for AR(1) phi estimation (default 50 = ~17 days at 8h).
    znorm_window:
        Rolling window in bars for z-normalization of half_life_raw (default 90 = 30 days).
    cap:
        Cap in bars for extreme/undefined half-life values (default 50 bars).
    clip:
        Absolute clip for the final z-score output (default 5.0).

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with ``rev_halflife_50`` column appended.
        First (ar_window + znorm_window) rows will be NaN (burn-in + shift).

    Notes
    -----
    Past-only by construction:
    - ret_1[t] = log(close[t] / close[t-1]) via .shift(1) — past-only.
    - phi[t]: rolling(ar_window).apply(lag1_corr, raw=True) — uses only bars [t-49, t].
    - vmu and vsd: rolling(znorm_window) of half_life_raw — window [t-89, t], past-only.
    - Additional .shift(1) on the output ensures bar t's feature uses data from <= t-1.

    Rolling corr helper mirrors the ``stat_autocorr`` pattern in statistical.py:25-27
    (Pearson correlation of series with its own lag-1 via rolling apply).
    """
    df = df.copy()
    close = df["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))

    # 1-bar log return
    ret_1 = log_close - log_close.shift(1)
    ret_1_values = ret_1.to_numpy(dtype=np.float64)

    # Rolling AR(1): Pearson lag-1 autocorrelation over ar_window bars
    n = len(ret_1_values)
    phi_arr = np.full(n, np.nan, dtype=np.float64)
    for i in range(ar_window, n + 1):
        window = ret_1_values[i - ar_window : i]
        # Pearson correlation of window[1:] on window[:-1]
        x = window[:-1]
        y = window[1:]
        # Remove NaN pairs
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.sum() < 5:  # need minimum observations
            phi_arr[i - 1] = np.nan
            continue
        x_clean, y_clean = x[mask], y[mask]
        if x_clean.std() < 1e-12 or y_clean.std() < 1e-12:
            phi_arr[i - 1] = np.nan
            continue
        corr = np.corrcoef(x_clean, y_clean)[0, 1]
        phi_arr[i - 1] = float(corr)

    phi_series = pd.Series(phi_arr, index=ret_1.index)

    # Half-life: ln(0.5) / ln(|phi|) when 0 < |phi| < 1; else cap
    abs_phi = phi_series.abs()
    # Avoid log(0) or log(1) — clamp |phi| to (1e-9, 1 - 1e-9)
    abs_phi_safe = abs_phi.clip(lower=1e-9, upper=1.0 - 1e-9)
    # Only compute where |phi| is valid (non-NaN and in (0, 1))
    hl_raw = np.where(
        phi_series.notna() & (abs_phi > 1e-9) & (abs_phi < 1.0 - 1e-9),
        np.log(0.5) / np.log(abs_phi_safe),
        cap,
    )
    # For NaN phi: set to cap (no signal about reversion speed)
    hl_raw = np.where(phi_series.isna(), np.nan, hl_raw)
    hl_series = pd.Series(hl_raw, index=ret_1.index).clip(lower=0.0, upper=cap)

    # Z-normalize over trailing znorm_window bars
    vmu = hl_series.rolling(window=znorm_window, min_periods=znorm_window).mean()
    vsd = hl_series.rolling(window=znorm_window, min_periods=znorm_window).std(ddof=1)
    z = (hl_series - vmu) / vsd.replace(0.0, np.nan)

    # Shift by 1: bar t's value uses only data from bars <= t-1
    df["rev_halflife_50"] = z.shift(1).clip(-clip, clip)

    return df


def compute_rev_vol_gate_signed(
    df: pd.DataFrame,
    gate_lo: float = REV_VOL_GATE_SOFT_LO,
    gate_hi: float = REV_VOL_GATE_SOFT_HI,
) -> pd.DataFrame:
    """Compute ``rev_vol_gate_signed`` = rev_extension_z_3 × soft vol-regime gate.

    Binds the directional reversion signal (rev_extension_z_3) to the volatility
    state (vol_state_z_natr_30): pass the reversion signal through at full strength
    in compressed-vol regimes, and damp it to zero in vol-expansion regimes.

    Gate definition:
        g[t] = 1.0                                    when vol_state_z_natr_30[t] <= gate_lo
        g[t] = linearly ramp 1→0  when vol_state_z_natr_30[t] in (gate_lo, gate_hi]
        g[t] = 0.0                                    when vol_state_z_natr_30[t] > gate_hi
        (g[t] = 1.0 when vol_state_z_natr_30 is NaN — conservative pass-through)

        rev_vol_gate_signed[t] = rev_extension_z_3[t] * g[t]

    IMPORTANT: This function requires that ``rev_extension_z_3`` AND ``vol_state_z_natr_30``
    are already present in ``df`` as columns. Call compute_rev_extension_z_3() and
    compute_vol_state_z_natr_30() BEFORE calling this function.

    The feature mechanically correlates with rev_extension_z_3 by construction (Category-2
    composed feature). Per feedback_v3_engineered_feature_pivot.md, the strict |IC|<0.50
    gate is INAPPROPRIATE; the falsifier is importance >= 30 gain AND Sharpe-Delta.

    Parameters
    ----------
    df:
        DataFrame with ``rev_extension_z_3`` and ``vol_state_z_natr_30`` columns
        already computed.
    gate_lo:
        vol_state_z_natr_30 threshold: gate = 1.0 at or below this level (default 0.0).
    gate_hi:
        vol_state_z_natr_30 threshold: gate = 0.0 above this level (default 1.0).

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with ``rev_vol_gate_signed`` column appended.

    Raises
    ------
    KeyError
        If ``rev_extension_z_3`` or ``vol_state_z_natr_30`` are missing from df.

    Notes
    -----
    Past-only by construction: both input features (rev_extension_z_3 and
    vol_state_z_natr_30) are already shifted by 1 from their respective compute
    functions. No additional shift needed here.
    """
    if "rev_extension_z_3" not in df.columns:
        raise KeyError(
            "rev_extension_z_3 must be in df before calling compute_rev_vol_gate_signed. "
            "Call compute_rev_extension_z_3() first."
        )
    if "vol_state_z_natr_30" not in df.columns:
        raise KeyError(
            "vol_state_z_natr_30 must be in df before calling compute_rev_vol_gate_signed. "
            "Call compute_vol_state_z_natr_30() first."
        )

    df = df.copy()
    rev_signal = df["rev_extension_z_3"].astype(float)
    vol_z = df["vol_state_z_natr_30"].astype(float)

    # Soft gate: piecewise linear 1 → 0 over [gate_lo, gate_hi]
    # NaN vol_z: conservative pass-through (g=1)
    g = np.where(
        np.isnan(vol_z.values),
        1.0,
        np.where(
            vol_z.values <= gate_lo,
            1.0,
            np.where(
                vol_z.values >= gate_hi,
                0.0,
                # linear ramp from 1 → 0
                1.0 - (vol_z.values - gate_lo) / (gate_hi - gate_lo),
            ),
        ),
    )

    df["rev_vol_gate_signed"] = rev_signal.values * g

    return df


def add_composed_v1_085_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Add iter-v1/085 composed features to ``df`` in correct dependency order.

    Order is load-bearing:
    1. compute_rev_extension_z_3 (independent; needs only close)
    2. compute_vol_state_z_natr_30 (independent; needs only high/low/close)
       [IMPORTED from volatility_v1 — NOT registered in composed_v1 registry]
    3. compute_rev_halflife_50 (independent; needs only close)
    4. compute_rev_vol_gate_signed (depends on 1 + 2 already in df)

    NOTE: This function is NOT the GROUP_REGISTRY entry for composed_v1
    (which stays as add_composed_v1_features for regime_momentum_signed_5d).
    This is a standalone helper for the /085 runner which calls the features in order.

    Used by the features CLI group ``composed_v1_085`` registered separately.

    Parameters
    ----------
    df:
        Kline DataFrame with ``close``, ``high``, ``low`` columns.

    Returns
    -------
    pd.DataFrame
        df with all 4 iter-v1/085 feature columns appended:
        rev_extension_z_3, vol_state_z_natr_30, rev_halflife_50, rev_vol_gate_signed.
    """
    # Import volatility_v1 locally to avoid circular dep risk at module level
    from crypto_trade.features_v1.mean_reversion_v1 import compute_rev_extension_z_3
    from crypto_trade.features_v1.volatility_v1 import compute_vol_state_z_natr_30

    df = compute_rev_extension_z_3(df)
    df = compute_vol_state_z_natr_30(df)
    df = compute_rev_halflife_50(df)
    df = compute_rev_vol_gate_signed(df)
    return df


__all__ = [
    "_hurst_rs",
    "_rolling_hurst",
    "compute_regime_momentum_signed_5d",
    "add_composed_v1_features",
    # iter-v1/085 additions
    "REV_HALFLIFE_AR_WINDOW",
    "REV_HALFLIFE_ZNORM_WINDOW",
    "REV_HALFLIFE_CAP",
    "REV_HALFLIFE_CLIP",
    "REV_VOL_GATE_SOFT_LO",
    "REV_VOL_GATE_SOFT_HI",
    "compute_rev_halflife_50",
    "compute_rev_vol_gate_signed",
    "add_composed_v1_085_features",
]
