"""WorldQuant-101 formulaic-alpha features for v3 — iter-v3/102.

Category 2 ENGINEERED axis: Alpha#32 from Kakushadze (2015) "101 Formulaic Alphas"
(arXiv:1601.00991, Wilmott Magazine 2016(84):72-80), ported to the v3 per-symbol
crypto 8h panel.

CRITICAL ADAPTATION — PER-SYMBOL PORT
---------------------------------------
Alpha#32 Kakushadze verbatim (Appendix A):

    scale(((sum(close,7)/7) - close)) + (20 * scale(correlation(vwap, delay(close,5), 230)))

Kakushadze's ``scale(x)`` is a CROSS-SECTIONAL operator: it rescales a cross-sectional
vector so that sum(|x|) = 1.  v3 is a PER-SYMBOL architecture; there is no cross-section
to sum over.  The faithful per-symbol port replaces ``scale(x)`` with a causal trailing-
window mean-absolute normalization::

    scale_ts(x, d) = x / rolling_mean(|x|, window=d, min_periods=d)

This preserves sign and shape while bounding the feature's influence from any single bar.
Window = 100 bars (matches the /059 baseline hurst_100 window; absorbs roughly 33 days).

ALL operators are STRICTLY PAST-ONLY:
  - ``sum(close,7)/7``: rolling mean over the 7 bars ending at bar t (inclusive).
  - ``close`` at bar t: the current close, known at t.
  - ``delay(close,5)``: close shifted 5 bars back — strictly past.
  - ``correlation(vwap, delay(close,5), 230)``: Pearson rolling correlation over the
    230 bars ending at bar t, using only past values of both series.
  - ``scale_ts``: causal trailing-100-bar mean-abs normalization — past-only.
  - No bar after t is accessed anywhere in the computation.

TRACK ISOLATION:
  This module imports NOTHING from ``crypto_trade.features`` (v1) or
  ``crypto_trade.features_v2`` (v2).  Enforced by the Phase-6 pre-flight grep:

      grep -r "from crypto_trade.features " src/crypto_trade/features_v3/
      grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v3/

  Both must return empty (zero matches for formulaic_v3.py in particular).

WARM-UP:
  The 230-bar rolling correlation dominates; the first valid bar is at index 229.
  Including the 5-bar lag and the 100-bar scale_ts window, total warm-up is
  max(230 + 5 - 1, 100) - 1 + 1 ≈ 334 bars (~111 days on 8h candles).
  This is absorbed by the 24-month IS burn-in window at the walk-forward start.

ADF STATIONARITY:
  T9 from analysis/iteration_v3-102/alpha032_deepdive.py confirms ADF p < 0.05
  for BCH (p≈0), LDO (p=0.0409), TRX (p≈0) — 3/3 stationary.  Stationary by
  construction: scale_ts bounds the feature; the 7-bar SMA gap is mean-reverting;
  the 230-bar correlation is bounded ∈ [-1, 1].

REFERENCES:
  - Kakushadze, Z. (2015). "101 Formulaic Alphas." arXiv:1601.00991.
  - analysis/iteration_v3-102/alpha_lib.py — reference EDA implementation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Internal helpers (pure time-series, past-only)
# ---------------------------------------------------------------------------


def _scale_ts(s: pd.Series, d: int) -> pd.Series:
    """Causal per-symbol time-series scaling proxy for Kakushadze ``scale(x)``.

    Divides ``s`` by the trailing ``d``-bar mean of ``|s|``.  Past-only.
    Returns NaN where the denominator is 0 or where fewer than ``d`` bars
    are available (min_periods=d).

    Args:
        s: input series (any float pd.Series).
        d: trailing window length (bars).

    Returns:
        Element-wise ``s / mean(|s|, window=d)``.
    """
    denom = s.abs().rolling(d, min_periods=d).mean()
    return s / denom.replace(0.0, np.nan)


def _ts_sum(s: pd.Series, d: int) -> pd.Series:
    """Rolling sum over the trailing ``d`` bars ending at bar t.  Past-only."""
    return s.rolling(d, min_periods=d).sum()


def _ts_corr(x: pd.Series, y: pd.Series, d: int) -> pd.Series:
    """Rolling Pearson correlation between ``x`` and ``y`` over ``d`` bars.  Past-only.

    Returns NaN where fewer than ``d`` bars are available or where either series
    has zero variance in the window (pandas rolling.corr() behaviour).
    """
    return x.rolling(d, min_periods=d).corr(y)


# ---------------------------------------------------------------------------
# Alpha#32 — public API
# ---------------------------------------------------------------------------


def compute_alpha032(df: pd.DataFrame) -> pd.DataFrame:
    """Compute WorldQuant Alpha#32 (Kakushadze 2015) for one symbol.

    Kakushadze verbatim formula (Appendix A):
        scale(((sum(close,7)/7) - close)) + (20 * scale(correlation(vwap, delay(close,5), 230)))

    Per-symbol v3 port:
        scale_ts(term1, 100) + 20 * scale_ts(term2, 100)
        where:
          term1 = (rolling_mean(close, 7) - close)
          term2 = rolling_pearson_corr(vwap, close.shift(5), window=230)
          vwap  = quote_volume / volume   (per-bar proxy; known at bar t close)

    Two sub-signals:
      - Term 1: FAST MEAN-REVERSION GAP — how far the close sits below/above its
        own 7-bar (2.3-day) simple moving average.  Positive when the close is
        above the SMA (extended), negative when below (mean-reverting impulse).
      - Term 2: SLOW VWAP/PRICE LEAD-LAG — rolling correlation between the per-bar
        VWAP and the 5-bar-lagged close over a 230-bar (~77-day) window.  Captures
        persistent co-movement structure between traded price and past close.

    Args:
        df: DataFrame with columns ``close``, ``quote_volume``, ``volume``.
            All must be float-castable.  A ``volume`` of zero produces NaN for
            vwap at that bar (handled gracefully via replace(0.0, np.nan)).

    Returns:
        Copy of ``df`` with column ``alpha032`` appended (float64, NaN during
        warm-up period of ~334 bars).

    Raises:
        KeyError: if ``close``, ``quote_volume``, or ``volume`` is absent.
    """
    df = df.copy()

    close = df["close"].astype(float)
    volume = df["volume"].astype(float).replace(0.0, np.nan)
    quote_volume = df["quote_volume"].astype(float)
    vwap = quote_volume / volume  # per-bar proxy; known at bar t close; past-only

    # Term 1: fast mean-reversion gap (7-bar SMA − close), causal scale
    sma7 = _ts_sum(close, 7) / 7.0
    term1_raw = sma7 - close
    term1 = _scale_ts(term1_raw, 100)

    # Term 2: slow vwap/lagged-close correlation (230-bar window), causal scale
    close_lag5 = close.shift(5)  # delay(close, 5) — strictly past
    term2_raw = _ts_corr(vwap, close_lag5, 230)
    term2 = _scale_ts(term2_raw, 100)

    df["alpha032"] = term1 + 20.0 * term2

    return df


# ---------------------------------------------------------------------------
# GROUP_REGISTRY entry point
# ---------------------------------------------------------------------------


def add_formulaic_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add WorldQuant-101 formulaic-alpha features to the v3 feature frame.

    Currently adds one feature: ``alpha032``.

    Registered in ``features_v3.GROUP_REGISTRY`` under the key ``"formulaic_v3"``.
    Must be called AFTER ``regime`` (no dependency; ordering is cosmetic).
    Requires columns: ``close``, ``quote_volume``, ``volume``.

    Args:
        df: DataFrame produced by the preceding GROUP_REGISTRY steps.

    Returns:
        DataFrame with ``alpha032`` appended.
    """
    return compute_alpha032(df)
