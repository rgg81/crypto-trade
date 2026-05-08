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


def add_engineered_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """GROUP_REGISTRY entry point for all Category 2 (composed) v3 features.

    Currently computes:
    - ``regime_momentum_signed_5d`` (iter-v3/025): composed feature combining
      5-day momentum with Hurst regime classifier.

    Future Category 2 features are added here in subsequent iterations.  Each
    new composed feature must be listed in the iteration's research brief Section
    2.2 and validated with an adversarial past-only test.

    Args:
        df: DataFrame that has already been processed by ``add_regime_v3_features``
            (so ``hurst_100`` is available).

    Returns:
        Copy of ``df`` with all engineered v3 features appended.
    """
    df = compute_regime_momentum_signed_5d(df)
    return df


__all__ = [
    "add_engineered_v3_features",
    "compute_regime_momentum_signed_5d",
]
