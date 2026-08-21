"""Aggregate direction timed by the breadth of the eligible cross-section.

The lane's claim is that breadth is a *market state*: the count of names participating thins out
before the aggregate rolls over and broadens before it recovers, because the marginal name is more
sensitive to flow than the aggregate. The seed states that claim in its least clever form -- three
breadth measures, one dead zone, flat in between -- and its own regime profile says where that form
breaks. It is right about direction when breadth is decisive (bear 87, bull 70 on the research
window) and it destroys itself when breadth is not (chop 0.5). It does not lose there because it has
no view; it loses because a hard dead zone makes it *trade* its lack of a view: every crossing
flattens the book, forgets it, and pays a full round trip to rebuild the same position days later.

This book keeps the seed's thesis and changes what happens near neutral.

1.  **The state is read at many horizons, not three.** Three measures at one lookback each is a bet
    that a particular lookback is the right one; nine measures spanning three families and three
    horizon multiples is a bet on breadth. No single lookback can move the state by more than about
    a ninth, which is what a state variable should look like.

2.  **The band is a no-*flip* band, not a no-*position* band.** Inside it the book keeps the side it
    already had. This is the whole change. Breadth near neutral is not evidence for the other side;
    it is absence of evidence, and the honest response to absence of evidence is to not act, which
    means holding, not liquidating. A constant position through a directionless market earns about
    nothing; a position that flattens and re-enters on every wobble earns about nothing minus its
    own turnover, and, under this scorer, forfeits the utilisation term as well.

3.  **The book is never sized by conviction.** Under the common risk unit a scalar multiple of the
    same book is executed identically, so "half size when unsure" is a no-op dressed as prudence.
    Conviction is expressed in exactly one place -- which side, or the previous side -- and nowhere
    else. Size belongs to the organizer.

Being wrong here is being wrong about direction on every name at once. That is the lane, and no
amount of construction hides it: a small reading is a small bet on a side, not a hedge.
"""

from __future__ import annotations

import math

import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2

# Below a handful of names a "fraction of the cross-section" is anecdote rather than breadth.
_MINIMUM_NAMES = 3
# Liquidity is ranked on a month so one squeeze cannot rewrite the basket for a single day.
_VOLUME_DAYS = 30
# Horizon multiples applied to the single declared horizon. Each family is read short, at, and long
# of the horizon, so the state is a spread of lookbacks rather than a choice of one.
_TREND_MULTIPLES = (0.5, 1.0, 2.0)
_RETURN_MULTIPLES = (0.25, 0.5, 1.0)
_EXTREME_MULTIPLES = (1.0, 1.5, 2.5)
# A measure shorter than this is a day of noise counted as a market state.
_MINIMUM_MEASURE_DAYS = 4.0
# Per-name ceiling inside the book, tighter than the organizer's per-symbol cap.
_SYMBOL_CAP = 0.15


def _voting_names(panel: pd.DataFrame, bars: int) -> pd.Series:
    """Names with enough of the window observed to vote.

    Without this a name listed three days ago votes on a three-bar "50-day average" and counts for
    as much as a name with the whole window behind it, which quietly turns breadth into a measure
    of how many new listings the universe happens to hold.
    """
    return panel.tail(bars).notna().sum() >= max(_MINIMUM_NAMES, bars // 2)


def _as_signal(votes: pd.Series) -> float:
    """Map a fraction of the cross-section onto [-1, +1]; an empty vote is not a reading."""
    if votes.empty:
        return float("nan")
    return 2.0 * float(votes.mean()) - 1.0


def _breadth_above_average(panel: pd.DataFrame, bars: int) -> float:
    """Fraction of names trading above their own moving average."""
    window = panel.tail(bars)
    average = window.mean()
    last = panel.iloc[-1]
    usable = _voting_names(panel, bars) & last.notna() & average.notna()
    return _as_signal((last > average)[usable])


def _breadth_positive_return(panel: pd.DataFrame, bars: int) -> float:
    """Fraction of names with a positive trailing return over a fixed horizon."""
    return _as_signal(toolkit.trailing_return(panel, bars) > 0.0)


def _breadth_new_extremes(panel: pd.DataFrame, bars: int) -> float:
    """Net new highs less new lows: already a net fraction on [-1, +1], so it is used as-is.

    Re-mapping it through 2*f-1 like the other two would report a quiet tape as maximally bearish.
    """
    window = panel.tail(bars)
    last = panel.iloc[-1]
    usable = _voting_names(panel, bars) & last.notna()
    highs = (last >= window.max())[usable]
    lows = (last <= window.min())[usable]
    if highs.empty:
        return float("nan")
    return float(int(highs.sum()) - int(lows.sum())) / float(len(highs))


class BreadthMarketStateTiming:
    # One horizon, read at three multiples per family. Days, not bars: the multiples do the
    # spreading, so this number is the centre of a fan rather than a single chosen lookback.
    horizon = 32
    # How decisive breadth has to be before the book changes side. Inside the band the previous
    # side is kept: near neutral breadth is absence of evidence, not evidence for the other side.
    band = 0.22
    # Trailing window, in days, used to risk-equalise the names inside the book.
    sigma_days = 30
    # Exponential blending of the emitted book. On a one-sided book this is not a size control --
    # the risk unit removes scale -- it is a delay on the side change, which is the point.
    decay = 0.15

    def __init__(self) -> None:
        self._smoother = toolkit.TargetSmoother(decay=float(self.decay), band=0.05)
        # The one piece of carried state: which side the book is on. It is a deterministic
        # function of the streamed past, so it reconstructs from any replay of the same stream.
        self._side = 0.0

    # -- state -------------------------------------------------------------------------------

    def _measure_bars(self, multiple: float) -> int:
        days = max(_MINIMUM_MEASURE_DAYS, float(self.horizon) * multiple)
        return max(3, toolkit.bars_for_days(days))

    def _breadth_state(self, panel: pd.DataFrame) -> float:
        """Average every breadth measure the available history can actually support.

        Measures whose window is longer than the history simply do not vote. A book that refuses to
        deploy until its longest lookback is satisfied is flat through the beginning of its own
        record for a reason that has nothing to do with the market.
        """
        readings: list[float] = []
        available = len(panel)
        for multiple in _TREND_MULTIPLES:
            bars = self._measure_bars(multiple)
            if available > bars:
                readings.append(_breadth_above_average(panel, bars))
        for multiple in _RETURN_MULTIPLES:
            bars = self._measure_bars(multiple)
            if available > bars:
                readings.append(_breadth_positive_return(panel, bars))
        for multiple in _EXTREME_MULTIPLES:
            bars = self._measure_bars(multiple)
            if available > bars:
                readings.append(_breadth_new_extremes(panel, bars))
        usable = [value for value in readings if math.isfinite(value)]
        if not usable:
            return float("nan")
        return sum(usable) / len(usable)

    # -- book --------------------------------------------------------------------------------

    def _tradeable(self, context: DecisionContextV2, panel: pd.DataFrame) -> list[str]:
        """Every eligible name that actually traded over the past month.

        The universe is already the fifty most liquid perpetuals, so an aggregate view has no
        reason to hold a subset of it: holding all of them is the lower-variance way to take the
        same bet, and the risk unit converts that lower variance straight back into the common
        volatility target rather than into a smaller book. The volume filter is a causal safety
        check, not a selection: a name with no month of trading behind it cannot be sized.
        """
        volume = toolkit.column_panel(context, "quote_volume")
        if volume.empty:
            return []
        median = volume.tail(toolkit.bars_for_days(_VOLUME_DAYS)).median()
        traded = [name for name in median[median > 0.0].index if name in panel.columns]
        return sorted(traded, key=lambda name: (-float(median[name]), str(name)))

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None
        panel = toolkit.close_panel(context)
        if panel.empty:
            return None
        state = self._breadth_state(panel)
        if not math.isfinite(state):
            return None  # no reading yet; holding beats inventing a direction

        threshold = abs(float(self.band))
        if state >= threshold:
            self._side = 1.0
        elif state <= -threshold:
            self._side = -1.0
        if self._side == 0.0:
            return None  # never had a decisive reading; there is nothing to hold yet

        names = self._tradeable(context, panel)
        if not names:
            return None
        sigma_bars = max(9, toolkit.bars_for_days(self.sigma_days))
        raw = toolkit.vol_parity(
            {name: self._side for name in names},
            toolkit.realised_sigma(panel[names], bars=sigma_bars),
            gross=1.0,
            symbol_cap=_SYMBOL_CAP,
            # Deliberately directional: there is no second side to balance against, so the neutral
            # two-budget split would be meaningless here.
            neutral=False,
        )
        if not raw:
            return None  # a sizing failure is not a market view
        return self._smoother.update(raw, context.eligible_symbols)


def build_strategy() -> BreadthMarketStateTiming:
    return BreadthMarketStateTiming()
