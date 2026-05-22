"""iter-v3/102 — WorldQuant-101 formulaic-alpha library (v3-portable subset).

THE AXIS (user-directed 2026-05-18)
-----------------------------------
Explore the WorldQuant 101 Formulaic Alphas (Kakushadze 2015, arXiv 1601.00991)
as v3 engineered features.  The 101 alphas are a library of COMPOSED operators
on OHLCV + vwap + returns — exactly the Category-2 ENGINEERED feature class v3's
history says outperforms off-the-shelf indicators (iter-v3/025's
`regime_momentum_signed_5d`, a composed feature, is v3's only PROMISING feature
post-bootstrap; iter-v3/098's off-the-shelf families were NO-GO).

CRITICAL ADAPTATION — PER-SYMBOL PORT
-------------------------------------
The 101 Alphas are largely CROSS-SECTIONAL: `rank()` ranks a quantity across a
large asset universe at each timestamp; `IndNeutralize` demeans within industry;
`scale()` normalizes a cross-sectional vector.  v3 is a PER-SYMBOL architecture
(one LightGBM per coin on BCH/LDO/TRX).  The /088-092 cross-sectional
re-architecture is CLOSED (no edge).  Therefore this module ports ONLY the
TIME-SERIES-PURE alphas — the alphas whose Kakushadze formula uses solely
time-series operators on a SINGLE asset's own OHLCV/vwap/returns
(ts_*, delta, delay, correlation/covariance between the asset's own series,
decay_linear, stddev, ts_min/max, ts_argmin/argmax, ts_rank, sign, signedpower).

KEY ADAPTATION DECISIONS (documented for the brief + Critic):
  1. `rank(x)` cross-sectional → DROPPED.  Where a Kakushadze alpha is
     `rank(<time-series quantity>)`, the per-symbol port keeps the inner
     time-series quantity and drops the outer cross-sectional rank.  A monotone
     CS rank does not change the SIGN of a feature->label IC for a per-symbol
     model, and a depth-3-5 tree is invariant to monotone transforms of a single
     feature — so for a per-symbol learner the inner time-series quantity carries
     the same information the CS-ranked alpha would.  This is the standard
     per-symbol adaptation (cf. Jansen MLAT 2nd ed. Ch. 24 single-name use).
  2. `Ts_Rank(x, d)` — the TIME-SERIES rank (rank of x_t within its own trailing
     d-bar window) — is KEPT.  It is a pure time-series operator, fully
     per-symbol, NOT cross-sectional.  (Capital-Ts_Rank in Kakushadze == this.)
  3. `adv{d}` (average daily DOLLAR volume) — Kakushadze's adv is a 20/d-day mean
     of dollar volume.  For a single 8h-candle symbol this is just a rolling mean
     of `quote_volume` — fully time-series, fully per-symbol.  KEPT where an alpha
     uses adv only as one of its OWN-asset series (NOT as a cross-sectional
     universe screen).
  4. `IndNeutralize(x, industry)` → DROPPED.  No industry data; crypto has no
     GICS sector.  Alphas requiring IndNeutralize are SKIPPED entirely.
  5. `vwap` — not a parquet column.  Kakushadze's vwap is the volume-weighted
     average price; the faithful 8h-candle proxy is `quote_volume / volume`
     (the per-bar dollar-volume / base-volume = mean traded price).  Computed
     here, past-only (bar t's own vwap is known at bar t close).

ALL operators below are STRICTLY PAST-ONLY (rolling windows ending at bar t;
`.shift()` where the formula references a lag).  Verified per-operator in the
docstrings.  This module is IS-only-agnostic — the caller (alpha_ic_eda.py)
applies the `open_time < OOS_CUTOFF_MS` mask.  NO OOS is touched here.

REFERENCES
----------
- Kakushadze, Z. (2015). "101 Formulaic Alphas." arXiv:1601.00991; Wilmott
  Magazine 2016(84):72-80.  Appendix A — the 101 formulas + operator glossary.
- Jansen, S. (2020). *Machine Learning for Algorithmic Trading*, 2nd ed., Ch. 24
  — the canonical applied implementation of the 101 alphas.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ===========================================================================
# Operator glossary — Kakushadze Appendix A, time-series operators only.
# Every operator is past-only: a rolling window of length d ending at bar t,
# or an explicit .shift(d) for a lag.  Appending future bars never changes the
# value at bar t.
# ===========================================================================


def ts_delay(s: pd.Series, d: int) -> pd.Series:
    """delay(x, d) — value of x d bars ago.  Past-only: .shift(d)."""
    return s.shift(d)


def ts_delta(s: pd.Series, d: int) -> pd.Series:
    """delta(x, d) — x_t minus x_{t-d}.  Past-only: .diff(d)."""
    return s.diff(d)


def ts_sum(s: pd.Series, d: int) -> pd.Series:
    """sum(x, d) — rolling sum over the trailing d bars ending at t."""
    return s.rolling(d, min_periods=d).sum()


def ts_mean(s: pd.Series, d: int) -> pd.Series:
    """rolling mean over the trailing d bars ending at t."""
    return s.rolling(d, min_periods=d).mean()


def ts_std(s: pd.Series, d: int) -> pd.Series:
    """stddev(x, d) — rolling sample std over the trailing d bars ending at t."""
    return s.rolling(d, min_periods=d).std(ddof=1)


def ts_min(s: pd.Series, d: int) -> pd.Series:
    """ts_min(x, d) — rolling min over the trailing d bars ending at t."""
    return s.rolling(d, min_periods=d).min()


def ts_max(s: pd.Series, d: int) -> pd.Series:
    """ts_max(x, d) — rolling max over the trailing d bars ending at t."""
    return s.rolling(d, min_periods=d).max()


def ts_argmax(s: pd.Series, d: int) -> pd.Series:
    """ts_argmax(x, d) — bars since the max within the trailing d-bar window.

    Kakushadze: "which day ts_max(x, d) occurred on".  We return the offset in
    [0, d-1] from the window start (0 = oldest bar is the max, d-1 = current bar
    is the max).  Past-only — the window ends at bar t.
    """
    return s.rolling(d, min_periods=d).apply(lambda w: float(np.argmax(w)), raw=True)


def ts_argmin(s: pd.Series, d: int) -> pd.Series:
    """ts_argmin(x, d) — bars since the min within the trailing d-bar window."""
    return s.rolling(d, min_periods=d).apply(lambda w: float(np.argmin(w)), raw=True)


def ts_rank(s: pd.Series, d: int) -> pd.Series:
    """Ts_Rank(x, d) — TIME-SERIES rank of x_t within its trailing d-bar window.

    Returns the percentile rank in [0, 1] of the current bar's value among the
    trailing d bars (1.0 == current bar is the largest of the window).  This is
    a PURE TIME-SERIES operator — NOT the cross-sectional rank().  Fully
    per-symbol, fully past-only (window ends at bar t).
    """
    return s.rolling(d, min_periods=d).apply(
        lambda w: float(pd.Series(w).rank(pct=True).iloc[-1]), raw=False
    )


def ts_corr(a: pd.Series, b: pd.Series, d: int) -> pd.Series:
    """correlation(a, b, d) — rolling Pearson corr of two of the asset's OWN
    series over the trailing d bars ending at t.  Past-only.
    """
    return a.rolling(d, min_periods=d).corr(b)


def ts_cov(a: pd.Series, b: pd.Series, d: int) -> pd.Series:
    """covariance(a, b, d) — rolling covariance of two own series, trailing d."""
    return a.rolling(d, min_periods=d).cov(b)


def decay_linear(s: pd.Series, d: int) -> pd.Series:
    """decay_linear(x, d) — linearly weighted moving average, weights d, d-1,...,1
    (most recent bar gets the largest weight), normalized to sum 1.

    Kakushadze's `decay_linear` / WMA.  Past-only — the window ends at bar t.
    """
    w = np.arange(1, d + 1, dtype=np.float64)
    w /= w.sum()

    def _wma(window: np.ndarray) -> float:
        return float(np.dot(window, w))

    return s.rolling(d, min_periods=d).apply(_wma, raw=True)


def signedpower(s: pd.Series, a: float) -> pd.Series:
    """signedpower(x, a) — sign(x) * (|x| ** a).  Element-wise, past-only."""
    return np.sign(s) * (s.abs() ** a)


def scale_ts(s: pd.Series, d: int) -> pd.Series:
    """Per-symbol time-series re-scaling proxy for Kakushadze `scale(x)`.

    Kakushadze `scale(x, a)` rescales a CROSS-SECTIONAL vector so sum|x| = a.
    For a per-symbol port there is no cross-section to sum over; the faithful
    single-name analogue is to divide by the trailing-window mean absolute
    value (a causal normalization that preserves sign and shape).  Used only
    where an alpha's `scale()` wraps a time-series quantity.  Past-only.
    """
    denom = s.abs().rolling(d, min_periods=d).mean()
    return s / denom.replace(0.0, np.nan)


# ===========================================================================
# Base-field construction.
# vwap proxy = quote_volume / volume (per-bar volume-weighted mean price).
# adv{d} = trailing-d-bar mean of quote_volume (dollar volume) — per-symbol,
#          time-series; NOT a cross-sectional universe screen.
# ===========================================================================


def base_fields(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Return the Kakushadze base fields as past-only pd.Series for one symbol.

    `open`, `high`, `low`, `close`, `volume` — raw kline columns.
    `vwap`    — quote_volume / volume (per-bar VWAP proxy; known at bar t close).
    `returns` — close-to-close simple return = close.pct_change() (Kakushadze's
                daily `returns`).
    """
    o = df["open"].astype(float)
    h = df["high"].astype(float)
    low = df["low"].astype(float)
    c = df["close"].astype(float)
    v = df["volume"].astype(float).replace(0.0, np.nan)
    qv = df["quote_volume"].astype(float)
    vwap = qv / v
    returns = c.pct_change()
    return {
        "open": o,
        "high": h,
        "low": low,
        "close": c,
        "volume": df["volume"].astype(float),
        "vwap": vwap,
        "returns": returns,
    }


def adv(df: pd.DataFrame, d: int) -> pd.Series:
    """adv{d} — trailing d-bar mean of quote_volume (dollar volume).  Past-only.

    Per-symbol time-series quantity.  Kakushadze's adv enters the kept alphas
    only as one of the asset's own series in a correlation/delta — never as a
    cross-sectional universe filter.
    """
    return df["quote_volume"].astype(float).rolling(d, min_periods=d).mean()


# ===========================================================================
# The v3-portable formulaic-alpha basket.
#
# Each function returns ONE past-only pd.Series for a single symbol.
# Selection rule: the alpha's Kakushadze formula uses ONLY time-series operators
# on the single asset's own series.  Where the Kakushadze formula has an OUTER
# cross-sectional rank(...), the per-symbol port drops that outer rank and keeps
# the inner time-series quantity (decision #1 in the module docstring) — these
# are tagged "cs-rank-dropped" in ALPHA_NOTES.  Alphas needing IndNeutralize or a
# cross-sectional rank that cannot be cleanly stripped are NOT in this basket.
#
# Each docstring quotes the Kakushadze Appendix-A formula verbatim and states
# the adaptation applied.
# ===========================================================================


def alpha006(df: pd.DataFrame) -> pd.Series:
    """Alpha#6  Kakushadze: (-1 * correlation(open, volume, 10)).

    Pure time-series — correlation of the asset's own open and volume over a
    trailing 10-bar window.  NO adaptation needed (no rank, no IndNeutralize).
    Mechanism: when price-open and volume co-move strongly, the alpha is
    negative — a contrarian flow signal.
    """
    f = base_fields(df)
    return -1.0 * ts_corr(f["open"], f["volume"], 10)


def alpha012(df: pd.DataFrame) -> pd.Series:
    """Alpha#12  Kakushadze: (sign(delta(volume, 1)) * (-1 * delta(close, 1))).

    Pure time-series.  NO adaptation needed.  Mechanism: if volume rose vs the
    prior bar, fade the last close move; if volume fell, follow it — a
    volume-confirmed short-horizon reversal.
    """
    f = base_fields(df)
    return np.sign(ts_delta(f["volume"], 1)) * (-1.0 * ts_delta(f["close"], 1))


def alpha023(df: pd.DataFrame) -> pd.Series:
    """Alpha#23  Kakushadze:
    (((sum(high, 20) / 20) < high) ? (-1 * delta(high, 2)) : 0).

    Pure time-series (conditional on the asset's own 20-bar mean high).  NO
    adaptation needed.  Mechanism: only when the current high is above its
    20-bar average (an extended/over-stretched bar) does the alpha fire, fading
    the 2-bar change in high — a conditional mean-reversion of the high.
    """
    f = base_fields(df)
    cond = (ts_sum(f["high"], 20) / 20.0) < f["high"]
    val = -1.0 * ts_delta(f["high"], 2)
    return val.where(cond, 0.0)


def alpha024(df: pd.DataFrame) -> pd.Series:
    """Alpha#24  Kakushadze:
    ((((delta((sum(close,100)/100),100)/delay(close,100)) <= 0.05))
       ? (-1*(close - ts_min(close,100)))
       : (-1*delta(close,3))).

    Pure time-series.  NO adaptation needed.  Mechanism: a regime switch on the
    100-bar trend slope — in a flat/slow regime, fade distance from the 100-bar
    low; in a fast regime, fade the 3-bar change.
    """
    f = base_fields(df)
    c = f["close"]
    sma100 = ts_sum(c, 100) / 100.0
    slope = ts_delta(sma100, 100) / ts_delay(c, 100)
    branch_a = -1.0 * (c - ts_min(c, 100))
    branch_b = -1.0 * ts_delta(c, 3)
    return branch_a.where(slope <= 0.05, branch_b)


def alpha028(df: pd.DataFrame) -> pd.Series:
    """Alpha#28  Kakushadze:
    scale(((correlation(adv20, low, 5) + ((high + low) / 2)) - close)).

    Per-symbol port: `scale()` is the cross-sectional re-scale — replaced by the
    causal time-series scale_ts (decision #5; window 100).  `adv20` is the
    asset's own 20-bar dollar-volume mean (per-symbol; decision #3).  All else
    is time-series.  Mechanism: blends a liquidity-price correlation with the
    candle midpoint-minus-close (an intrabar reversal proxy).
    """
    f = base_fields(df)
    a20 = adv(df, 20)
    raw = ts_corr(a20, f["low"], 5) + ((f["high"] + f["low"]) / 2.0) - f["close"]
    return scale_ts(raw, 100)


def alpha032(df: pd.DataFrame) -> pd.Series:
    """Alpha#32  Kakushadze:
    (scale(((sum(close,7)/7) - close)) +
     (20 * scale(correlation(vwap, delay(close,5), 230)))).

    Per-symbol port: `scale()` → causal scale_ts (window 100).  All inner
    quantities (7-bar SMA gap; long 230-bar corr of vwap with lagged close) are
    time-series on the asset's own series.  Mechanism: a fast mean-reversion
    term plus a slow vwap/price lead-lag term.
    """
    f = base_fields(df)
    term1 = scale_ts((ts_sum(f["close"], 7) / 7.0) - f["close"], 100)
    term2 = 20.0 * scale_ts(ts_corr(f["vwap"], ts_delay(f["close"], 5), 230), 100)
    return term1 + term2


def alpha034(df: pd.DataFrame) -> pd.Series:
    """Alpha#34  Kakushadze:
    rank(((1 - rank((stddev(returns,2) / stddev(returns,5)))) +
          (1 - rank(delta(close,1))))).

    Per-symbol port: cs-rank-dropped (decision #1) — the OUTER rank and the two
    INNER rank() wrappers are cross-sectional; for a per-symbol learner the
    informative content is the un-ranked composite.  We keep
    ((1 - vol_ratio) + (1 - delta_close)) with vol_ratio and delta_close left in
    raw units.  Mechanism: rewards bars with falling short-vs-medium vol ratio
    and a falling last close — a low-vol pullback signal.
    """
    f = base_fields(df)
    vol_ratio = ts_std(f["returns"], 2) / ts_std(f["returns"], 5)
    return (1.0 - vol_ratio) + (1.0 - ts_delta(f["close"], 1))


def alpha035(df: pd.DataFrame) -> pd.Series:
    """Alpha#35  Kakushadze:
    ((Ts_Rank(volume,32) * (1 - Ts_Rank(((close+high)-low),16))) *
     (1 - Ts_Rank(returns,32))).

    Pure time-series — every rank here is the TIME-SERIES Ts_Rank (decision #2),
    NOT cross-sectional.  NO cs adaptation needed.  Mechanism: high recent
    volume rank, low recent (close+high-low) rank, and low recent return rank —
    an accumulation-into-weakness signal.
    """
    f = base_fields(df)
    vr = ts_rank(f["volume"], 32)
    chl = ts_rank((f["close"] + f["high"]) - f["low"], 16)
    rr = ts_rank(f["returns"], 32)
    return vr * (1.0 - chl) * (1.0 - rr)


def alpha043(df: pd.DataFrame) -> pd.Series:
    """Alpha#43  Kakushadze:
    (ts_rank((volume / adv20), 20) * ts_rank((-1 * delta(close, 7)), 8)).

    Pure time-series — both ranks are Ts_Rank (per-symbol; decision #2); adv20
    is the asset's own 20-bar dollar-volume mean (decision #3).  NO cs
    adaptation needed.  Mechanism: high relative-volume rank combined with a
    high rank of the negative 7-bar close change — volume-confirmed reversal.
    """
    f = base_fields(df)
    rel_vol = f["volume"] / adv(df, 20)
    return ts_rank(rel_vol, 20) * ts_rank(-1.0 * ts_delta(f["close"], 7), 8)


def alpha046(df: pd.DataFrame) -> pd.Series:
    """Alpha#46  Kakushadze:
    ((0.25 < (((delay(close,20)-delay(close,10))/10) -
              ((delay(close,10)-close)/10)))
       ? -1
       : (((((delay(close,20)-delay(close,10))/10) -
            ((delay(close,10)-close)/10)) < 0)
           ? 1
           : (-1 * (close - delay(close,1))))).

    Pure time-series.  NO adaptation needed.  Mechanism: a momentum-curvature
    regime switch — compares the close slope over [t-20,t-10] vs [t-10,t]; a
    strongly positive curvature → short, negative → long, otherwise fade the
    1-bar move.
    """
    f = base_fields(df)
    c = f["close"]
    curv = ((ts_delay(c, 20) - ts_delay(c, 10)) / 10.0) - (
        (ts_delay(c, 10) - c) / 10.0
    )
    out = pd.Series(np.nan, index=df.index)
    out = out.mask(curv < 0, 1.0)
    out = out.mask(curv >= 0, -1.0 * (c - ts_delay(c, 1)))
    out = out.mask(curv > 0.25, -1.0)
    return out


def alpha049(df: pd.DataFrame) -> pd.Series:
    """Alpha#49  Kakushadze:
    (((((delay(close,20)-delay(close,10))/10) -
       ((delay(close,10)-close)/10)) < (-1 * 0.1))
       ? 1
       : (-1 * (close - delay(close,1)))).

    Pure time-series.  NO adaptation needed.  Mechanism: the Alpha#46 curvature
    with a single threshold — if the close-slope curvature is sharply negative,
    go long; otherwise fade the 1-bar move.
    """
    f = base_fields(df)
    c = f["close"]
    curv = ((ts_delay(c, 20) - ts_delay(c, 10)) / 10.0) - (
        (ts_delay(c, 10) - c) / 10.0
    )
    return pd.Series(1.0, index=df.index).where(
        curv < -0.1, -1.0 * (c - ts_delay(c, 1))
    )


def alpha051(df: pd.DataFrame) -> pd.Series:
    """Alpha#51  Kakushadze:
    (((((delay(close,20)-delay(close,10))/10) -
       ((delay(close,10)-close)/10)) < (-1 * 0.05))
       ? 1
       : (-1 * (close - delay(close,1)))).

    Pure time-series.  NO adaptation needed.  Identical structure to Alpha#49
    with a -0.05 threshold (a less extreme curvature trigger).
    """
    f = base_fields(df)
    c = f["close"]
    curv = ((ts_delay(c, 20) - ts_delay(c, 10)) / 10.0) - (
        (ts_delay(c, 10) - c) / 10.0
    )
    return pd.Series(1.0, index=df.index).where(
        curv < -0.05, -1.0 * (c - ts_delay(c, 1))
    )


def alpha053(df: pd.DataFrame) -> pd.Series:
    """Alpha#53  Kakushadze:
    (-1 * delta((((close-low)-(high-close)) / (close-low)), 9)).

    Pure time-series.  NO adaptation needed.  The inner term is the candle-close
    position within its range; the alpha is the negative 9-bar change of it — a
    reversal of intrabar buying pressure.  (close-low) can be 0 on a doji; we
    guard the denominator.
    """
    f = base_fields(df)
    rng = (f["close"] - f["low"]).replace(0.0, np.nan)
    inner = ((f["close"] - f["low"]) - (f["high"] - f["close"])) / rng
    return -1.0 * ts_delta(inner, 9)


def alpha054(df: pd.DataFrame) -> pd.Series:
    """Alpha#54  Kakushadze:
    ((-1 * ((low - close) * (open^5))) / ((low - high) * (close^5))).

    Pure time-series — element-wise on the asset's own OHLC.  NO adaptation
    needed.  Mechanism: a candle-shape ratio — where the close sits relative to
    the low/high, weighted by the open/close 5th-power ratio.  (low-high) is
    strictly negative except on a flat bar; guard the denominator.
    """
    f = base_fields(df)
    num = -1.0 * ((f["low"] - f["close"]) * (f["open"] ** 5))
    den = ((f["low"] - f["high"]) * (f["close"] ** 5)).replace(0.0, np.nan)
    return num / den


def alpha068(df: pd.DataFrame) -> pd.Series:
    """Alpha#68  Kakushadze (per-symbol port):
    ((Ts_Rank(correlation(rank(high), rank(adv15), 8.91644), 13.9333) <
      rank(delta(((close*0.518371)+(low*(1-0.518371))), 1.06157)))
       ? 1 : -1)  ... ORIGINAL is a cs-rank comparison.

    Per-symbol port: cs-rank-dropped (decision #1).  Both sides of the
    Kakushadze inequality wrap cross-sectional rank()s.  Stripping the
    cross-sectional ranks, the per-symbol informative quantity is the
    DIFFERENCE of the two inner time-series terms — we return
    (Ts_Rank(corr(high, adv15, 9), 14)) - z(delta(0.518*close + 0.482*low, 1)),
    a continuous version of the Kakushadze sign comparison.  Both Ts_Rank and
    the correlation are pure time-series; adv15 is per-symbol (decision #3).
    """
    f = base_fields(df)
    a15 = adv(df, 15)
    left = ts_rank(ts_corr(f["high"], a15, 9), 14)
    blended = (f["close"] * 0.518371) + (f["low"] * (1.0 - 0.518371))
    right = ts_delta(blended, 1)
    # put `right` on a comparable causal scale before the difference
    right_z = right / right.abs().rolling(100, min_periods=100).mean().replace(
        0.0, np.nan
    )
    return left - right_z


def alpha084(df: pd.DataFrame) -> pd.Series:
    """Alpha#84  Kakushadze:
    SignedPower(Ts_Rank((vwap - ts_max(vwap, 15.3217)), 20.7127),
                delta(close, 4.96796)).

    Pure time-series — Ts_Rank is per-symbol (decision #2), vwap is the
    per-bar VWAP proxy (decision #5).  NO cross-sectional adaptation needed.
    Mechanism: how far vwap sits below its own 15-bar max (a pullback rank),
    raised to a signed power of the 4-bar close change — momentum-scaled
    pullback.
    """
    f = base_fields(df)
    inner = ts_rank(f["vwap"] - ts_max(f["vwap"], 15), 21)
    expo = ts_delta(f["close"], 5)
    # SignedPower(x, a) = sign(x) * |x|^a ; here a is a (small) series.
    # |inner| in [0,1] so |inner|^expo is finite; sign(inner) >= 0 by Ts_Rank.
    return np.sign(inner) * (inner.abs() ** expo)


def alpha101(df: pd.DataFrame) -> pd.Series:
    """Alpha#101  Kakushadze: ((close - open) / ((high - low) + 0.001)).

    Pure time-series — the canonical intrabar body-vs-range ratio.  NO
    adaptation needed.  Kakushadze's simplest alpha; a single-bar momentum
    primitive.  Included as a basket SANITY ANCHOR — if a richer alpha cannot
    beat this trivial one on the IC screen, the basket is weak.
    """
    f = base_fields(df)
    return (f["close"] - f["open"]) / ((f["high"] - f["low"]) + 0.001)


# Engineered VARIANT (Category-2 composition, v3-history-aligned).
# Not a raw Kakushadze alpha — a regime-conditioned composition of one, in the
# spirit of iter-v3/025's regime_momentum_signed_5d.  Tested in the basket so
# the EDA can compare a raw alpha vs a regime-signed version of it.
def alpha053_regime_signed(df: pd.DataFrame) -> pd.Series:
    """ENGINEERED: alpha053 * sign(hurst_100 - 0.5).

    v3's only PROMISING post-bootstrap feature (regime_momentum_signed_5d) is a
    momentum primitive sign-switched by the Hurst regime.  alpha053 is a
    9-bar reversal of intrabar buying pressure; in a trending regime a reversal
    signal should be FADED, in a mean-reverting regime FOLLOWED — the same
    composition logic.  Past-only: hurst_100 is a 100-bar trailing R/S exponent
    (parquet column, past-only by construction).
    """
    base = alpha053(df)
    if "hurst_100" not in df.columns:
        return pd.Series(np.nan, index=df.index)
    sign_h = np.sign(df["hurst_100"].astype(float) - 0.5).replace(0.0, np.nan)
    return base * sign_h


# Registry: name -> (builder, kakushadze_formula_tag, adaptation_tag)
ALPHA_REGISTRY: dict[str, callable] = {
    "alpha006": alpha006,
    "alpha012": alpha012,
    "alpha023": alpha023,
    "alpha024": alpha024,
    "alpha028": alpha028,
    "alpha032": alpha032,
    "alpha034": alpha034,
    "alpha035": alpha035,
    "alpha043": alpha043,
    "alpha046": alpha046,
    "alpha049": alpha049,
    "alpha051": alpha051,
    "alpha053": alpha053,
    "alpha054": alpha054,
    "alpha068": alpha068,
    "alpha084": alpha084,
    "alpha101": alpha101,
    "alpha053_regime_signed": alpha053_regime_signed,
}

ALPHA_NOTES: dict[str, str] = {
    "alpha006": "pure time-series; no adaptation",
    "alpha012": "pure time-series; no adaptation",
    "alpha023": "pure time-series; no adaptation",
    "alpha024": "pure time-series; no adaptation",
    "alpha028": "scale()->causal scale_ts; adv20 per-symbol",
    "alpha032": "scale()->causal scale_ts; all inner time-series",
    "alpha034": "cs-rank-dropped (3 ranks stripped); per-symbol composite",
    "alpha035": "pure time-series (all Ts_Rank, per-symbol)",
    "alpha043": "pure time-series (Ts_Rank per-symbol); adv20 per-symbol",
    "alpha046": "pure time-series; no adaptation",
    "alpha049": "pure time-series; no adaptation",
    "alpha051": "pure time-series; no adaptation",
    "alpha053": "pure time-series; no adaptation",
    "alpha054": "pure time-series; no adaptation",
    "alpha068": "cs-rank-dropped (2 ranks stripped); continuous difference",
    "alpha084": "pure time-series (Ts_Rank per-symbol); vwap proxy",
    "alpha101": "pure time-series; SANITY ANCHOR (trivial body/range)",
    "alpha053_regime_signed": "ENGINEERED Category-2: alpha053 x sign(hurst-0.5)",
}
