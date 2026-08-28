"""team-05 -- illiquidity-conditioned short-horizon reversal (nomination).

The premium is the rent paid to whoever supplies immediacy when the intermediary sector
will not (Nagel 2012). A lagged cross-sectional return is a noisy observation of the
inventory the market-making sector was just forced to absorb; the compensation for
holding that inventory scales with how thin the book was when it arrived (Amihud 2002;
Bianchi/Babiak/Dickerson 2022). Hence the mandate: reversal strength should rise with
ex-ante illiquidity, and the trade should be taken on the moves a thin book had to
absorb rather than on every short-horizon move.

Structure, in the order the code applies it:

  1. a 24h dislocation, normalised by the symbol's own trailing volatility and ranked
     cross-sectionally, so the signal is relative mispricing rather than beta;
  2. residualised, in the cross-section and at every sleeve date, against the 4-day
     trend measured up to the *start* of the formation window -- the non-overlapping
     medium-horizon momentum factor. Trial t02 showed that factor is large and
     continuation-signed in this universe; a reversal book that does not hedge it is
     short momentum by accident (Da/Liu/Schaumburg 2014, Liu/Tsyvinski/Wu 2022);
  3. tilted linearly by the ex-ante Amihud illiquidity percentile -- this is the
     mandate, and the term that is supposed to carry the edge. The most liquid name in
     the cross-section carries no weight at all;
  4. risk-balanced by inverse trailing volatility at constant gross exposure, clipped
     tightly so the balance cannot cancel the illiquidity tilt it sits next to;
  5. averaged across overlapping dated sleeves, weighted by how liquidity-stressed the
     market was on the bar each sleeve was formed -- the "when liquidity was actually
     scarce" half of the mandate, bounded to a 4:1 emphasis;
  6. and finally re-neutralised, as a whole book, against the current medium-horizon
     trend, so the delivered exposure is momentum-orthogonal at every decision and not
     merely at formation.

The sleeve average is what controls turnover. Under equal sleeve weights the difference
w_t - w_{t-1} = (s_t - s_{t-H}) / H telescopes exactly, so turnover falls as 1/H with no
dependence on the intervening path; the bounded stress weighting perturbs that identity
rather than replacing it, at the cost of some extra turnover. It is the only lever that
moves realised cost by an order of magnitude, and t02 demonstrated it works
(797/yr -> 81/yr). It does *not* move gross edge per unit turnover, which is invariant
to holding period -- see RATIONALE.md section 2.

No volatility targeting: gross is pinned at 1.0 every bar and the organizer's common
ex-ante risk unit sets the scale. Funding is never read. No persistent state, no RNG,
no absolute dates, no symbol identities, no price levels.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# ---- horizons, in dataset bars (the bar is 8h) --------------------------------------
FORMATION_BARS = 3          # 24h dislocation -- the daily horizon of the crypto reversal
MOMENTUM_BARS = 12          # 4d trend, measured up to the start of the formation window
SLEEVE_SPAN = 18            # overlapping dated sleeves; turnover ~ 2/SLEEVE_SPAN
ILLIQ_BARS = 21             # Amihud averaging window (~7d)
VOL_BARS = 21               # trailing realised volatility
DEPTH_BARS = 30             # median quote volume, for the tradeability floor
PANEL_BARS = 96             # rows retained per symbol
MIN_HISTORY = 30            # a symbol needs this many rows to enter the panel at all

VOL_MIN_PERIODS = 10
ILLIQ_MIN_PERIODS = 10
DEPTH_MIN_PERIODS = 10

# ---- shaping ------------------------------------------------------------------------
DEPTH_FLOOR_Q = 0.10        # drop the thinnest decile: below it participation caps bind
VOL_CLIP_LO = 0.70          # winsorise sigma to [LO, HI] x cross-sectional median
VOL_CLIP_HI = 1.50
STRESS_RANGE = 0.60         # sleeve weight in [1-R, 1+R]: a 4:1 stressed/calm emphasis

# ---- book limits (the evaluator re-applies its own) ---------------------------------
GROSS_TARGET = 1.0
MAX_WEIGHT = 0.10
NET_CAP = 0.10
DUST = 0.0010
MIN_NAMES = 12
MIN_SLEEVES = 3

REQUIRED_COLUMNS = ("open_time", "close", "quote_volume")


def _usable_symbols(bars, eligible):
    """Eligible symbols that carry the columns and the history this book needs."""
    names = []
    for symbol in eligible:
        if symbol not in bars:
            continue
        frame = bars[symbol]
        if frame is None or len(frame) < MIN_HISTORY:
            continue
        columns = frame.columns
        if all(column in columns for column in REQUIRED_COLUMNS):
            names.append(symbol)
    return names


def _column_panel(bars, symbols, column):
    """Wide panel aligned on ``open_time``.

    The per-symbol frames carry a positional RangeIndex and unequal history, so
    concatenating on the frame index would align integer positions and return a panel
    that is almost entirely NaN. ``open_time`` is the only correct alignment key.
    """
    series = {}
    for symbol in symbols:
        tail = bars[symbol].iloc[-PANEL_BARS:]
        stamps = pd.Index(tail["open_time"].to_numpy())
        values = pd.to_numeric(tail[column], errors="coerce").to_numpy(dtype=float)
        column_series = pd.Series(values, index=stamps)
        column_series = column_series[~column_series.index.duplicated(keep="last")]
        series[symbol] = column_series
    if not series:
        return None
    return pd.concat(series, axis=1).sort_index()


def _centered_rank(values):
    """Cross-sectional rank mapped to (-0.5, +0.5); non-finite entries are dropped."""
    numeric = pd.to_numeric(values, errors="coerce")
    finite = numeric[np.isfinite(numeric.to_numpy(dtype=float))]
    count = len(finite)
    if count < MIN_NAMES:
        return None
    ranks = finite.rank(method="average")
    return (ranks - (count + 1.0) / 2.0) / float(count)


def _residual(target, factor):
    """Cross-sectional residual of ``target`` after projecting out ``factor``.

    Both arguments are centred ranks, so the slope is a correlation and the residual is
    bounded. This is a hedge, not a bet: the slope is measured on the cross-section
    present at this decision rather than assumed.
    """
    aligned = factor.reindex(target.index)
    y = target.to_numpy(dtype=float)
    x = aligned.to_numpy(dtype=float)
    usable = np.isfinite(x) & np.isfinite(y)
    if int(usable.sum()) < MIN_NAMES:
        return target
    x = np.where(usable, x, 0.0)
    x = x - float(x[usable].mean())
    x = np.where(usable, x, 0.0)
    denominator = float(np.dot(x, x))
    if not (np.isfinite(denominator) and denominator > 0.0):
        return target
    slope = float(np.dot(x, np.where(usable, y, 0.0))) / denominator
    if not np.isfinite(slope):
        return target
    return pd.Series(y - slope * x, index=target.index)


def _balance(weights):
    """Scale each side to half the gross target, so the book is exactly neutral."""
    finite = weights[np.isfinite(weights.to_numpy(dtype=float))]
    if finite.empty:
        return None
    positive = finite[finite > 0.0]
    negative = finite[finite < 0.0]
    if positive.empty or negative.empty:
        return None
    positive_sum = float(positive.sum())
    negative_sum = float(-negative.sum())
    if not (positive_sum > 0.0 and negative_sum > 0.0):
        return None
    book = pd.Series(0.0, index=finite.index, dtype=float)
    book.loc[positive.index] = positive * (0.5 * GROSS_TARGET / positive_sum)
    book.loc[negative.index] = negative * (0.5 * GROSS_TARGET / negative_sum)
    return book


def _sleeve(dislocation, trend, sigma, illiquidity, depth):
    """One dated sleeve: gross 1.0, dollar neutral, momentum-hedged, illiquidity-tilted."""
    usable = (
        dislocation.notna()
        & trend.notna()
        & sigma.notna()
        & illiquidity.notna()
        & depth.notna()
        & (sigma > 0.0)
        & (illiquidity > 0.0)
        & (depth > 0.0)
    )
    names = usable.index[usable.to_numpy()]
    if len(names) < MIN_NAMES:
        return None

    # Tradeability floor. The mandate tilts into thinness, so the very thinnest tail is
    # excluded rather than levered into: below it the participation cap binds and the
    # weight becomes un-filled gross rather than a position.
    available = depth.reindex(names)
    deep = available.index[(available >= available.quantile(DEPTH_FLOOR_Q)).to_numpy()]
    if len(deep) >= MIN_NAMES:
        names = deep

    volatility = sigma.reindex(names)
    fast = _centered_rank(dislocation.reindex(names) / volatility)
    slow = _centered_rank(trend.reindex(names) / volatility)
    if fast is None:
        return None

    # Fade the dislocation, but only the part of it that is not the medium-horizon
    # trend. The trend window ends where the formation window begins, so the hedge
    # cannot cancel the signal it is protecting.
    score = -fast if slow is None else -_residual(fast, slow)

    names = score.index

    # The mandate, as a continuous multiplier rather than a fitted gate: weight rises
    # linearly in the ex-ante illiquidity percentile, and the most liquid name in the
    # cross-section carries no weight at all.
    tilt = illiquidity.reindex(names).rank(pct=True)

    # Cross-sectional risk balancing at constant gross -- not a volatility target. The
    # clip is deliberately tight: illiquid names are usually the volatile ones, and an
    # unbounded 1/sigma would quietly undo the tilt above it.
    volatility = sigma.reindex(names)
    median_volatility = float(volatility.median())
    if not (np.isfinite(median_volatility) and median_volatility > 0.0):
        return None
    winsorised = volatility.clip(
        lower=VOL_CLIP_LO * median_volatility, upper=VOL_CLIP_HI * median_volatility
    )
    inverse_volatility = median_volatility / winsorised

    return _balance(score * tilt * inverse_volatility)


def _stress_weights(stress, positions):
    """Sleeve weights in [1-R, 1+R], ranked by market-wide liquidity stress.

    ``stress`` is the cross-sectional median of each bar's realised price impact
    divided by that symbol's own recent average impact -- a unitless, scale-free read
    on whether the market as a whole was thinner than its own norm on that bar. Ranking
    inside the sleeve window keeps it relative, so there is no level and no threshold.
    """
    count = len(positions)
    if count == 0:
        return None
    values = np.asarray(
        [float(stress.iloc[position]) for position in positions], dtype="float64"
    )
    if not np.all(np.isfinite(values)):
        return np.full(count, 1.0 / count, dtype="float64")
    if count == 1:
        return np.ones(1, dtype="float64")
    percentile = (
        np.asarray(pd.Series(values).rank(method="average"), dtype="float64") - 0.5
    ) / float(count)
    raw = (1.0 - STRESS_RANGE) + 2.0 * STRESS_RANGE * percentile
    total = float(raw.sum())
    if not (np.isfinite(total) and total > 0.0):
        return np.full(count, 1.0 / count, dtype="float64")
    return raw / total


def _neutralise(book, factor):
    """Project the delivered book off the current medium-horizon trend factor."""
    if factor is None:
        return book
    common = book.index.intersection(factor.index)
    if len(common) < MIN_NAMES:
        return book
    weights = book.reindex(common).to_numpy(dtype=float)
    exposure = factor.reindex(common).to_numpy(dtype=float)
    usable = np.isfinite(weights) & np.isfinite(exposure)
    if int(usable.sum()) < MIN_NAMES:
        return book
    exposure = np.where(usable, exposure, 0.0)
    exposure = exposure - float(exposure[usable].mean())
    exposure = np.where(usable, exposure, 0.0)
    denominator = float(np.dot(exposure, exposure))
    if not (np.isfinite(denominator) and denominator > 0.0):
        return book
    slope = float(np.dot(exposure, np.where(usable, weights, 0.0))) / denominator
    if not np.isfinite(slope):
        return book
    adjusted = book.copy()
    adjusted.loc[common] = weights - slope * exposure
    return adjusted


def _finalise(weights):
    """Dust cut, per-symbol cap, gross cap, residual net trim."""
    book = weights[weights.abs() >= DUST]
    if len(book) < MIN_NAMES:
        book = weights[weights.abs() > 0.0]
    balanced = _balance(book)
    if balanced is None:
        return None

    for _ in range(4):
        if float(balanced.abs().max()) <= MAX_WEIGHT + 1e-12:
            break
        clipped = balanced.clip(lower=-MAX_WEIGHT, upper=MAX_WEIGHT)
        rebalanced = _balance(clipped)
        if rebalanced is None:
            balanced = clipped
            break
        balanced = rebalanced

    book = balanced.clip(lower=-MAX_WEIGHT, upper=MAX_WEIGHT)
    gross = float(book.abs().sum())
    if gross > GROSS_TARGET:
        book = book * (GROSS_TARGET / gross)

    net = float(book.sum())
    if abs(net) > NET_CAP:
        side = book > 0.0 if net > 0.0 else book < 0.0
        side_gross = float(book[side].abs().sum())
        trim = abs(net) - NET_CAP
        if side_gross > trim:
            book.loc[side] = book[side] * ((side_gross - trim) / side_gross)
    return book


class IlliquidityConditionedReversal:
    """Overlapping-sleeve short-horizon reversal, conditioned on illiquidity.

    Stateless: every decision is a pure function of the past-only rows in ``context``.
    """

    def target_weights(self, context, *, seed):
        members = context.eligible_symbols
        eligible = [] if members is None else list(members)
        if len(eligible) < MIN_NAMES:
            return None

        bars = context.bars
        symbols = _usable_symbols(bars, eligible)
        if len(symbols) < MIN_NAMES:
            return None

        close = _column_panel(bars, symbols, "close")
        if close is None:
            return None
        rows = len(close.index)
        if rows < MOMENTUM_BARS + FORMATION_BARS + 2:
            return None
        quote_volume = _column_panel(bars, symbols, "quote_volume")
        if quote_volume is None:
            return None
        quote_volume = quote_volume.reindex(index=close.index, columns=close.columns)

        log_close = np.log(close.where(close > 0.0))
        bar_return = log_close.diff()
        traded = quote_volume.where(quote_volume > 0.0)

        dislocation = log_close.diff(FORMATION_BARS)
        # The trend window ends where the formation window begins: the hedge and the
        # signal never share a bar.
        trend = log_close.diff(MOMENTUM_BARS).shift(FORMATION_BARS)
        sigma = bar_return.rolling(VOL_BARS, min_periods=VOL_MIN_PERIODS).std()

        impact = bar_return.abs() / traded
        illiquidity = impact.rolling(ILLIQ_BARS, min_periods=ILLIQ_MIN_PERIODS).mean()
        depth = traded.rolling(DEPTH_BARS, min_periods=DEPTH_MIN_PERIODS).median()
        # Market-wide liquidity stress: how impactful this bar was relative to each
        # symbol's own recent norm, taken at the cross-sectional median.
        stress = (impact / illiquidity.where(illiquidity > 0.0)).median(axis=1)

        positions = [
            rows - 1 - lag for lag in range(min(SLEEVE_SPAN, rows)) if rows - 1 - lag >= 0
        ]
        sleeves = []
        kept_positions = []
        for position in positions:
            sleeve = _sleeve(
                dislocation.iloc[position],
                trend.iloc[position],
                sigma.iloc[position],
                illiquidity.iloc[position],
                depth.iloc[position],
            )
            if sleeve is not None:
                sleeves.append(sleeve)
                kept_positions.append(position)
        if len(sleeves) < MIN_SLEEVES:
            return None

        weights = _stress_weights(stress, kept_positions)
        if weights is None:
            return None
        panel = pd.concat(sleeves, axis=1, keys=range(len(sleeves))).fillna(0.0)
        composite = panel.mul(weights, axis=1).sum(axis=1)

        # Keep the delivered exposure momentum-orthogonal at the decision itself, not
        # only at the date each sleeve was formed.
        current_trend = _centered_rank(
            trend.iloc[-1].reindex(composite.index)
            / sigma.iloc[-1].reindex(composite.index)
        )
        book = _finalise(_neutralise(composite, current_trend))
        if book is None:
            return None

        tradable = set(eligible)
        targets = {}
        for symbol, weight in book.items():
            value = float(weight)
            if symbol in tradable and math.isfinite(value) and abs(value) >= 1e-6:
                targets[str(symbol)] = value
        return targets or None


def build_strategy():
    return IlliquidityConditionedReversal()
