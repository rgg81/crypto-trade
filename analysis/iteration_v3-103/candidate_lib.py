"""iter-v3/103 — candidate composed-feature library (formulaic-alphas round 2).

This module defines the iter-v3/103 EDA candidate basket. Per the /102 closeout
Lesson 1, /103 does NOT re-port another thin literal WorldQuant alpha selected by
a held-out-tail accuracy proxy. Instead it ENGINEERS v3-specific *composed*
features from the formulaic-alpha operator toolkit — the pattern that produced
v3's only PROMISING post-bootstrap feature (iter-v3/025 regime_momentum_signed_5d:
ret_5d x sign(hurst_100 - 0.5)).

DESIGN PRINCIPLE — encode an interaction a depth-3-5 tree CANNOT compose
-----------------------------------------------------------------------
A LightGBM at depth 3-5 splits on axis-aligned thresholds. It can approximate a
sum of monotone functions but it CANNOT compute, in one feature:
  - the *recency* of a windowed extremum (ts_argmax / ts_argmin)  -> a
    position-in-window scalar, not a level
  - a *sign-conditioned product* of two primitives (the /025 pattern)
  - a windowed percentile *rank* of a derived quantity (ts_rank)
Each /103 candidate is built from those operators so the single column carries
genuine non-tree-representable structure.

ALL OPERATORS ARE STRICTLY PAST-ONLY
------------------------------------
Every rolling op uses min_periods == window (no partial window straddles a
train/test boundary), no centered window, no full-series statistic, no bfill.
shift(k) is strictly past. Adversarial truncation audit in past_only_audit.py
(EDA Script 3) confirms bit-identity when 60 future bars are removed.

TRACK ISOLATION: imports nothing from crypto_trade.features (v1) or
crypto_trade.features_v2 (v2). Pure pandas/numpy.

REFERENCES
  - Kakushadze, Z. (2015). "101 Formulaic Alphas." arXiv:1601.00991.
  - src/crypto_trade/features_v3/formulaic_v3.py — the retained /102 operator library.
  - src/crypto_trade/features_v3/engineered_v3.py — regime_momentum_signed_5d (the
    proven v3 composed-feature pattern).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ===========================================================================
# Strictly-past-only time-series operators (formulaic-alpha toolkit)
# ===========================================================================


def ts_delay(s: pd.Series, d: int) -> pd.Series:
    """value d bars ago. Past-only (shift(d))."""
    return s.shift(d)


def ts_mean(s: pd.Series, d: int) -> pd.Series:
    """rolling mean over the trailing d bars ending at t. Past-only."""
    return s.rolling(d, min_periods=d).mean()


def ts_std(s: pd.Series, d: int) -> pd.Series:
    """rolling sample std over the trailing d bars ending at t. Past-only."""
    return s.rolling(d, min_periods=d).std(ddof=1)


def ts_argmax(s: pd.Series, d: int) -> pd.Series:
    """bars-since the max within the trailing d-bar window. Past-only.

    Returns 0 if the max is the current bar, d-1 if it is the oldest bar in the
    window. This is the Kakushadze ts_argmax recency operator: a depth-3 tree
    cannot derive 'how long ago the local high was' from price levels.
    """
    return s.rolling(d, min_periods=d).apply(
        lambda w: float(d - 1 - np.argmax(w)), raw=True
    )


def ts_argmin(s: pd.Series, d: int) -> pd.Series:
    """bars-since the min within the trailing d-bar window. Past-only."""
    return s.rolling(d, min_periods=d).apply(
        lambda w: float(d - 1 - np.argmin(w)), raw=True
    )


def ts_rank(s: pd.Series, d: int) -> pd.Series:
    """percentile rank (0..1) of the current value within its trailing d-bar
    window. Past-only. The last element's rank among the window."""

    def _rank(w: np.ndarray) -> float:
        last = w[-1]
        return float((w <= last).sum() - 1) / float(len(w) - 1)

    return s.rolling(d, min_periods=d).apply(_rank, raw=True)


def ts_corr(a: pd.Series, b: pd.Series, d: int) -> pd.Series:
    """rolling Pearson correlation of a and b over the trailing d bars. Past-only."""
    return a.rolling(d, min_periods=d).corr(b)


def decay_linear(s: pd.Series, d: int) -> pd.Series:
    """linearly-weighted moving average over the trailing d bars (weight d on the
    current bar down to 1 on the oldest). Past-only. Kakushadze decay_linear."""
    w = np.arange(1, d + 1, dtype=np.float64)
    w = w / w.sum()

    def _wma(window: np.ndarray) -> float:
        return float(np.dot(window, w))

    return s.rolling(d, min_periods=d).apply(_wma, raw=True)


def scale_ts(s: pd.Series, d: int) -> pd.Series:
    """causal per-symbol analogue of Kakushadze cross-sectional scale(): divide by
    the trailing d-bar mean of |s|. Past-only. Bounds single-bar influence."""
    denom = s.abs().rolling(d, min_periods=d).mean()
    return s / denom.replace(0.0, np.nan)


# ===========================================================================
# Base fields (per-symbol, past-only)
# ===========================================================================


def _base(df: pd.DataFrame) -> dict[str, pd.Series]:
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    open_ = df["open"].astype(float)
    volume = df["volume"].astype(float).replace(0.0, np.nan)
    quote_volume = df["quote_volume"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    return {
        "close": close,
        "high": high,
        "low": low,
        "open": open_,
        "volume": volume,
        "quote_volume": quote_volume,
        "log_close": log_close,
        "vwap": quote_volume / volume,  # per-bar VWAP proxy, known at bar t close
        "ret_1": log_close.diff(1),
    }


# ===========================================================================
# iter-v3/103 candidate composed features
# ===========================================================================
# Each candidate is a function df -> pd.Series. ALL strictly past-only.
# The design intent of each is documented inline; the EDA decides which (if any)
# clears the IS-predictive bar.


def cand_recency_weighted_momentum(df: pd.DataFrame) -> pd.Series:
    """C1 — RECENCY-GATED MOMENTUM: ret_5d x (1 - argmax_recency/(W-1)).

    ret_5d (the /025 momentum primitive) DOWN-WEIGHTED by how stale the local
    high is. argmax over a 20-bar window: if the high is recent (argmax->0 bars
    ago) the gate ->1 (momentum is fresh, trust it); if the high is old
    (argmax->W-1) the gate ->0 (the move is exhausted, fade the momentum signal).

    A depth-3-5 tree CANNOT compute 'bars since the 20-bar high' — ts_argmax is a
    genuinely non-tree-representable operator. The gate is in [0, 1]; the feature
    keeps the sign of ret_5d but scales magnitude by trend freshness.
    """
    b = _base(df)
    ret_5d = b["log_close"] - b["log_close"].shift(15)  # 15 bars x 8h = 5 days
    argmax_20 = ts_argmax(b["close"], 20)  # bars-since 20-bar high
    freshness = 1.0 - (argmax_20 / 19.0)  # 1 = high is now, 0 = high 19 bars ago
    return ret_5d * freshness


def cand_argmax_argmin_skew(df: pd.DataFrame) -> pd.Series:
    """C2 — EXTREMA-RECENCY SKEW: (argmin_recency - argmax_recency) / (W-1).

    Pure recency-asymmetry. argmax_recency = bars-since the 30-bar high;
    argmin_recency = bars-since the 30-bar low. If the LOW is more recent than
    the HIGH the value is negative (price has been falling toward a fresh low ->
    bearish microstructure); if the HIGH is more recent it is positive. Range
    [-1, +1]. This is a directional regime descriptor a tree cannot derive from
    price levels — it needs the *positions* of two windowed extrema.
    """
    b = _base(df)
    argmax_30 = ts_argmax(b["close"], 30)
    argmin_30 = ts_argmin(b["close"], 30)
    return (argmin_30 - argmax_30) / 29.0


def cand_vol_decayed_trend(df: pd.DataFrame) -> pd.Series:
    """C3 — DECAY-WEIGHTED RETURN over a VOL-RANK gate.

    decay_linear of 1-bar log returns over 10 bars (a recency-weighted momentum
    that emphasises the most recent bars) MULTIPLIED by sign(atr_pct_rank_200 -
    0.5). In high-vol regimes (rank > 0.5) the decayed-momentum keeps its sign
    (trend-follow); in low-vol regimes it flips (mean-revert). This is the /025
    sign-conditioned-product pattern with a decay_linear momentum core instead of
    a plain ret_5d. atr_pct_rank_200 is an existing past-only parquet column.
    """
    b = _base(df)
    decayed = decay_linear(b["ret_1"], 10)
    if "atr_pct_rank_200" not in df.columns:
        return pd.Series(np.nan, index=df.index)
    vol_rank = df["atr_pct_rank_200"].astype(float)
    regime_sign = np.sign(vol_rank - 0.5).replace(0.0, np.nan)
    return decayed * regime_sign


def cand_corr_gated_momentum(df: pd.DataFrame) -> pd.Series:
    """C4 — VOLUME-CONFIRMATION-GATED MOMENTUM: ret_5d x ts_corr(close, volume, 20).

    ret_5d gated by the rolling 20-bar correlation between close and volume. When
    price and volume rise together (corr > 0) the momentum is volume-confirmed
    and keeps its sign and magnitude; when price rises on falling volume
    (corr < 0) the feature flips the momentum's contribution. The corr term is in
    [-1, 1]; this is a continuous (not sign-only) gate. A tree cannot compute a
    rolling price-volume correlation.
    """
    b = _base(df)
    ret_5d = b["log_close"] - b["log_close"].shift(15)
    cv = ts_corr(b["close"], b["volume"], 20)
    return ret_5d * cv


def cand_tsrank_dispersion(df: pd.DataFrame) -> pd.Series:
    """C5 — WINDOWED-RANK OF NORMALISED DISPERSION: ts_rank(ret_std_20 / ret_std_60, 50).

    The 50-bar percentile rank of the ratio of short-window (20-bar) return
    dispersion to long-window (60-bar) return dispersion. A high rank means
    short-term volatility has spiked relative to its own recent history -> regime
    transition / stress; a low rank means calm. ts_rank converts the raw ratio to
    a 50-bar percentile so the feature is self-normalising across the IS window.
    This is a sign-free regime-stress descriptor.
    """
    b = _base(df)
    std_short = ts_std(b["ret_1"], 20)
    std_long = ts_std(b["ret_1"], 60)
    ratio = std_short / std_long.replace(0.0, np.nan)
    return ts_rank(ratio, 50)


def cand_scaled_reversal_pressure(df: pd.DataFrame) -> pd.Series:
    """C6 — CAUSAL-SCALED REVERSAL PRESSURE: scale_ts(close - ts_mean(close,7), 100)
    x sign(hurst_100 - 0.5).

    The Kakushadze alpha032 fast term (SMA-gap mean-reversion impulse) but
    SIGN-CONDITIONED on the Hurst regime — the /025 mechanism. In a mean-reverting
    regime (hurst < 0.5) a positive SMA-gap (price above its SMA) is a fade
    signal and the sign flip makes the feature negative; in a trending regime
    (hurst > 0.5) the same gap is a continuation signal. This explicitly repairs
    alpha032's /102 weakness: alpha032's fast term had a regime-INDEPENDENT sign,
    so its IS IC flipped across symbols (BCH -0.0255, LDO +0.0413, TRX +0.0395).
    Conditioning on hurst makes the directional meaning regime-consistent.
    """
    b = _base(df)
    sma_gap = b["close"] - ts_mean(b["close"], 7)
    scaled = scale_ts(sma_gap, 100)
    if "hurst_100" not in df.columns:
        return pd.Series(np.nan, index=df.index)
    hurst = df["hurst_100"].astype(float)
    regime_sign = np.sign(hurst - 0.5).replace(0.0, np.nan)
    return scaled * regime_sign


def cand_argmax_gap_signed(df: pd.DataFrame) -> pd.Series:
    """C7 — SIGNED EXTREMUM-PROXIMITY: (close/ts_max(close,20) - 1) x trend_sign.

    How far below the 20-bar high the close sits (a non-positive pullback depth),
    SIGN-CONDITIONED by the 20-day trend direction. In an uptrend a shallow
    pullback (close near the high) is bullish continuation; in a downtrend the
    same proximity is a lower-high rejection. trend_sign = sign(ret over 60 bars).
    Distinct from C6: this is a *level-proximity* feature, not an SMA-gap; and the
    extremum is a max() not a mean().
    """
    b = _base(df)
    roll_max = b["close"].rolling(20, min_periods=20).max()
    pullback = b["close"] / roll_max - 1.0  # <= 0; 0 = at the high
    ret_60 = b["log_close"] - b["log_close"].shift(60)  # 20-day trend
    trend_sign = np.sign(ret_60).replace(0.0, np.nan)
    return pullback * trend_sign


# Candidate registry: name -> (function, one-line note)
CANDIDATE_REGISTRY: dict[str, tuple] = {
    "recency_weighted_momentum_5d": (
        cand_recency_weighted_momentum,
        "C1: ret_5d x (1 - argmax20_recency); momentum down-weighted by trend staleness",
    ),
    "extrema_recency_skew_30": (
        cand_argmax_argmin_skew,
        "C2: (argmin30 - argmax30)/29; recency asymmetry of windowed high vs low",
    ),
    "vol_decayed_trend": (
        cand_vol_decayed_trend,
        "C3: decay_linear(ret,10) x sign(atr_rank200 - 0.5); decayed momentum, vol-regime gate",
    ),
    "corr_gated_momentum_5d": (
        cand_corr_gated_momentum,
        "C4: ret_5d x corr(close,volume,20); momentum gated by volume confirmation",
    ),
    "tsrank_dispersion_ratio": (
        cand_tsrank_dispersion,
        "C5: ts_rank(std20/std60, 50); 50-bar percentile of short/long dispersion ratio",
    ),
    "scaled_reversal_pressure_signed": (
        cand_scaled_reversal_pressure,
        "C6: scale_ts(close - sma7,100) x sign(hurst-0.5); alpha032 fast term, regime-conditioned",
    ),
    "argmax_pullback_signed_20": (
        cand_argmax_gap_signed,
        "C7: (close/max20 - 1) x sign(ret60); signed pullback depth from the 20-bar high",
    ),
}
