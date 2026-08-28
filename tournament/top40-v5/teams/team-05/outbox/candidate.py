"""team-05 -- illiquidity-conditioned short-horizon reversal.

Refinement candidate. The premium being harvested is the rent paid to whoever supplies
immediacy when the intermediary sector will not (Nagel 2012): a lagged cross-sectional
return is a noisy observation of the inventory the market-making sector was just forced
to absorb, and the compensation for holding that inventory scales with how thin the book
was when it arrived (Amihud 2002; Bianchi/Babiak/Dickerson 2022).

Structure, in the order the code applies it:

  1. a 9-bar (72h) dislocation, normalised by the symbol's own trailing volatility and
     cross-sectionally demeaned, so the signal is relative mispricing rather than beta;
  2. blended with the reversal of 9-bar taker-buy imbalance -- a directly observed read
     on which side crossed the spread, i.e. on the inventory the makers ended up with;
  3. selected to the extreme tails of the combined cross-sectional rank, because only
     large dislocations are plausibly inventory rather than information;
  4. tilted linearly toward high ex-ante Amihud illiquidity -- this is the mandate, and
     it is the term that is supposed to carry the edge;
  5. risk-balanced by inverse trailing volatility at constant gross exposure;
  6. and finally averaged across 18 overlapping sleeves. That last step is the whole
     point of this revision: the identity w_t - w_{t-1} = (s_t - s_{t-H}) / H makes
     turnover fall as 1/H with no dependence on the intervening sleeves, which is the
     only lever that moves gross edge per unit turnover by the order of magnitude the
     cost gate demands.

No volatility targeting: gross is pinned at 1.0 every bar and the organizer's common
ex-ante risk unit sets the scale. No funding signal. No persistent state, no RNG, no
absolute dates, no symbol identities, no price levels.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# ---- horizon and window lengths (bars; the dataset bar is 8h) -----------------------
FORMATION_BARS = 9          # 72h dislocation window
SLEEVE_SPAN = 18            # overlapping sleeves -> ~3.2d mean holding, turnover ~ 2/H
VOL_BARS = 21               # trailing realised volatility
ILLIQ_BARS = 21             # Amihud averaging window
LIQVOL_BARS = 30            # median quote volume, for the tradeability floor
PANEL_BARS = 72             # rows retained per symbol (>= LIQVOL_BARS + SLEEVE_SPAN + 2)
MIN_HISTORY = 30            # a symbol needs this many bars to enter the panel at all

VOL_MIN_PERIODS = 10
ILLIQ_MIN_PERIODS = 10
LIQVOL_MIN_PERIODS = 10
FLOW_MIN_PERIODS = 4

# ---- signal shaping ----------------------------------------------------------------
FLOW_WEIGHT = 0.30          # weight on the taker-imbalance reversal rank
KEEP_FRACTION = 0.60        # fraction of the cross-section carrying weight
MIN_KEEP = 16
MAX_KEEP = 40
TILT_FLOOR = 0.40           # illiquidity tilt at the most liquid name
TILT_SLOPE = 1.20           # tilt at the most illiquid name = FLOOR + SLOPE
VOL_CLIP_LO = 0.50          # winsorise sigma to [LO, HI] x cross-sectional median
VOL_CLIP_HI = 2.50
LIQ_FLOOR_Q = 0.10          # drop the thinnest decile by median quote volume

# ---- book limits (the evaluator re-applies its own) --------------------------------
GROSS_TARGET = 1.0
MAX_WEIGHT = 0.10
NET_CAP = 0.10
DUST = 0.0015
MIN_NAMES = 12
MIN_SLEEVES = 3

REQUIRED_COLUMNS = ("open_time", "close", "quote_volume", "taker_buy_quote_volume")


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
    finite = values[np.isfinite(values.to_numpy(dtype=float))]
    count = len(finite)
    if count < MIN_NAMES:
        return None
    ranks = finite.rank(method="average")
    return (ranks - (count + 1.0) / 2.0) / float(count)


def _balance(weights):
    """Scale each side to half the gross target, so the sleeve is exactly neutral."""
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


def _sleeve(formation, sigma, illiquidity, liquid_volume, imbalance):
    """One dated reversal sleeve: gross 1.0, dollar neutral, illiquidity-tilted."""
    usable = (
        formation.notna()
        & sigma.notna()
        & illiquidity.notna()
        & liquid_volume.notna()
        & (sigma > 0.0)
        & (illiquidity > 0.0)
        & (liquid_volume > 0.0)
    )
    names = usable.index[usable.to_numpy()]
    if len(names) < MIN_NAMES:
        return None

    # Tradeability floor: the mandate tilts into thinness, so the very thinnest tail is
    # excluded rather than levered into, where realised cost would outrun the premium.
    depth = liquid_volume.reindex(names)
    deep = depth.index[(depth >= depth.quantile(LIQ_FLOOR_Q)).to_numpy()]
    if len(deep) >= MIN_NAMES:
        names = deep

    volatility = sigma.reindex(names)
    dislocation = formation.reindex(names) / (volatility * math.sqrt(FORMATION_BARS))
    dislocation = dislocation - dislocation.median()

    score = _centered_rank(-dislocation)
    if score is None:
        return None

    # Observable inventory: takers who lifted offers left the maker sector short, and a
    # move the makers had to absorb is the move that should decay.
    flow = imbalance.reindex(score.index)
    if int(flow.notna().sum()) >= max(MIN_NAMES, int(0.6 * len(score))):
        flow = flow.fillna(flow.median())
        flow_score = _centered_rank(-(flow - flow.median()))
        if flow_score is not None:
            blended = (1.0 - FLOW_WEIGHT) * score.reindex(
                flow_score.index
            ) + FLOW_WEIGHT * flow_score
            reblended = _centered_rank(blended)
            if reblended is not None:
                score = reblended

    names = score.index
    magnitude = score.abs()
    keep = int(round(KEEP_FRACTION * len(names)))
    keep = min(max(keep, MIN_KEEP), MAX_KEEP, len(names) - 1)
    if keep < 4:
        return None
    threshold = float(magnitude.nlargest(keep).iloc[-1])
    selected = np.sign(score) * (magnitude - threshold).clip(lower=0.0)

    # The mandate, as a continuous multiplier rather than a fitted gate.
    tilt = TILT_FLOOR + TILT_SLOPE * illiquidity.reindex(names).rank(pct=True)

    volatility = sigma.reindex(names)
    median_volatility = float(volatility.median())
    if not (np.isfinite(median_volatility) and median_volatility > 0.0):
        return None
    winsorised = volatility.clip(
        lower=VOL_CLIP_LO * median_volatility, upper=VOL_CLIP_HI * median_volatility
    )
    inverse_volatility = median_volatility / winsorised

    return _balance(selected * tilt * inverse_volatility)


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
    """Overlapping-sleeve cross-sectional reversal, tilted toward illiquid names.

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
        if close is None or len(close.index) < FORMATION_BARS + 2:
            return None
        quote_volume = _column_panel(bars, symbols, "quote_volume")
        taker_buy = _column_panel(bars, symbols, "taker_buy_quote_volume")
        if quote_volume is None or taker_buy is None:
            return None
        quote_volume = quote_volume.reindex(index=close.index, columns=close.columns)
        taker_buy = taker_buy.reindex(index=close.index, columns=close.columns)

        log_close = np.log(close.where(close > 0.0))
        bar_return = log_close.diff()
        traded = quote_volume.where(quote_volume > 0.0)

        formation = log_close.diff(FORMATION_BARS)
        sigma = bar_return.rolling(VOL_BARS, min_periods=VOL_MIN_PERIODS).std()
        illiquidity = (
            (bar_return.abs() / traded)
            .rolling(ILLIQ_BARS, min_periods=ILLIQ_MIN_PERIODS)
            .mean()
        )
        depth = traded.rolling(LIQVOL_BARS, min_periods=LIQVOL_MIN_PERIODS).median()
        imbalance = (
            (taker_buy / traded - 0.5)
            .rolling(FORMATION_BARS, min_periods=FLOW_MIN_PERIODS)
            .mean()
        )

        rows = len(close.index)
        sleeves = []
        for lag in range(min(SLEEVE_SPAN, rows)):
            position = rows - 1 - lag
            if position < 0:
                break
            sleeve = _sleeve(
                formation.iloc[position],
                sigma.iloc[position],
                illiquidity.iloc[position],
                depth.iloc[position],
                imbalance.iloc[position],
            )
            if sleeve is not None:
                sleeves.append(sleeve)
        if len(sleeves) < MIN_SLEEVES:
            return None

        composite = pd.concat(sleeves, axis=1).fillna(0.0).mean(axis=1)
        book = _finalise(composite)
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
