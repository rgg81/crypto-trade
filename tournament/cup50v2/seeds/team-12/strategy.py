"""Aggregate directional exposure timed by the breadth of the eligible cross-section.

Breadth turns before price: the marginal name is more sensitive to flow than the aggregate, so the
count of names participating in an advance thins out well before the aggregate rolls over, and
broadens again before it recovers. This book reads three breadth measures over the eligible names,
averages them into a single market-state score, and holds one net direction sized by how decisive
that score is. Unlike the other lanes the output is primarily a NET DIRECTION rather than a
cross-sectional book, so it is the one lane that can be wrong about direction outright: a small
reading is not a hedge, it is a small bet, and a wrong sign loses on every name at once.
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
    """Fraction of names trading above their own moving average: the slowest of the three."""
    window = panel.tail(bars)
    average = window.mean()
    last = panel.iloc[-1]
    usable = _voting_names(panel, bars) & last.notna() & average.notna()
    return _as_signal((last > average)[usable])


def _breadth_positive_return(panel: pd.DataFrame, bars: int) -> float:
    """Fraction of names with a positive trailing return: participation over a fixed horizon."""
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
    ma_days = 50
    ret_days = 20
    hl_days = 60
    dead_zone = 0.20
    basket = 20

    def __init__(self) -> None:
        # Breadth is a state variable that persists for weeks, so the book is blended slowly and
        # the no-trade band is wide enough that a one-day wobble in the score costs nothing.
        self._smoother = toolkit.TargetSmoother(decay=0.15, band=0.05)

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None
        ma_bars = toolkit.bars_for_days(self.ma_days)
        ret_bars = toolkit.bars_for_days(self.ret_days)
        hl_bars = toolkit.bars_for_days(self.hl_days)
        panel = toolkit.close_panel(context)
        if panel.empty or len(panel) <= max(ma_bars, ret_bars, hl_bars):
            return None  # no reading yet; holding beats inventing a direction

        # Any single breadth measure is noisy; three that disagree are informative on their own.
        measures = [
            _breadth_above_average(panel, ma_bars),
            _breadth_positive_return(panel, ret_bars),
            _breadth_new_extremes(panel, hl_bars),
        ]
        readable = [value for value in measures if math.isfinite(value)]
        if not readable:
            return None
        state = sum(readable) / len(readable)

        # The dead zone is the whole defence against a directional book trading its own noise:
        # near neutral the measures are a coin flip and every crossing would pay a full round trip.
        if abs(state) < float(self.dead_zone):
            return self._flatten()
        # Doubling before the clip means a two-thirds majority is already full size; breadth this
        # one-sided is rare enough that halving the response to it would waste the signal.
        exposure = max(-1.0, min(1.0, 2.0 * state))

        names = self._basket(context, panel)
        if not names:
            return None
        direction = math.copysign(1.0, exposure)
        raw = toolkit.vol_parity(
            {name: direction for name in names},
            toolkit.realised_sigma(panel[names]),
            gross=abs(exposure),
            symbol_cap=0.15,
            # Deliberately directional: there is no second side to balance against, so the neutral
            # two-budget split would be meaningless here.
            neutral=False,
        )
        if not raw:
            return None  # a sizing failure is not a market view
        return self._smoother.update(raw, context.eligible_symbols)

    def _flatten(self) -> dict[str, float]:
        """Go flat now, and forget the book so the next signal ramps from zero rather than
        resuming a stale one the evaluator was never actually holding."""
        self._smoother.current = {}
        self._smoother.emitted = {}
        return {}

    def _basket(self, context: DecisionContextV2, panel: pd.DataFrame) -> list[str]:
        """The most liquid eligible names: an aggregate view belongs where it can be absorbed."""
        volume = toolkit.column_panel(context, "quote_volume")
        if volume.empty:
            return []
        median = volume.tail(toolkit.bars_for_days(_VOLUME_DAYS)).median()
        traded = [name for name in median[median > 0.0].index if name in panel.columns]
        ordered = sorted(traded, key=lambda name: (-float(median[name]), str(name)))
        return ordered[: max(1, int(self.basket))]


def build_strategy() -> BreadthMarketStateTiming:
    return BreadthMarketStateTiming()
