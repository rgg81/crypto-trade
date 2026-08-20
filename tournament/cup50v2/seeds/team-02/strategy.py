"""Continuous position inside the trailing price channel, long the top, short the bottom.

A range that has held for months accumulates resting orders and stop clusters at both edges, so
price leaving it forces those stops and attracts momentum flow rather than snapping back. Position
within that range is a continuous statement of how close a name is to the event, which turns over
far less than a binary breakout flag that fires on every touch of the edge. A name whose range
position disagrees with its own medium-term trend is breaking out against the prevailing drift and
carries less flow behind it, so it is taken at half size rather than dropped.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit


class ChannelPositionBreakout:
    """Rank the cross-section by where each name sits inside its own trailing channel."""

    # The evaluator overwrites these per neighbourhood point, so they are read at call time.
    channel_days = 84
    quintile = 0.20
    ma_days = 20

    # Funding never enters the mechanism; declaring that keeps the input honest rather than
    # accepting a stream the source silently ignores.
    uses_funding = False

    def __init__(self) -> None:
        # Damping is deliberately off the tunable surface. It prices turnover, and a lane that
        # tunes its own cost damping ends up tuning the cost model instead of the mechanism.
        self._smoother = toolkit.TargetSmoother(decay=0.20, band=0.05)

    def target_weights(self, context, *, seed: int):
        # Once a day: the channel moves on a months-long scale, so three decisions a day would pay
        # spread three times for the same view.
        if not toolkit.is_daily_decision(context):
            return None
        closes = toolkit.close_panel(context)
        scores = self._channel_scores(context, closes)
        if len(scores) < 2:
            return {}
        # At least one name a side, and never more than half the section per side.
        count = min(max(1, int(len(scores) * float(self.quintile))), len(scores) // 2)
        signals = self._trend_discount(toolkit.long_short_extremes(scores, count), scores, closes)
        if not signals:
            return {}
        weights = toolkit.vol_parity(
            signals, toolkit.realised_sigma(closes), symbol_cap=0.15, neutral=True
        )
        return self._smoother.update(weights, context.eligible_symbols)

    def _channel_scores(self, context, closes: pd.DataFrame) -> pd.Series:
        """Map each name onto [-1, +1]: -1 at the floor of its channel, +1 at the ceiling."""
        window = max(2, toolkit.bars_for_days(float(self.channel_days)))
        if closes.empty or len(closes) < window:
            return pd.Series(dtype=float)
        highs = toolkit.column_panel(context, "high").tail(window)
        lows = toolkit.column_panel(context, "low").tail(window)
        window_closes = closes.tail(window)
        scores: dict[str, float] = {}
        for symbol in window_closes.columns:
            if symbol not in highs.columns or symbol not in lows.columns:
                continue
            high = highs[symbol]
            low = lows[symbol]
            # A name listed part-way through the window has no range that "has held for months";
            # a channel measured over its short life would read as a breakout by construction.
            if int(high.notna().sum()) < window or int(low.notna().sum()) < window:
                continue
            ceiling = float(high.max())
            floor = float(low.min())
            last = float(window_closes[symbol].iloc[-1])
            span = ceiling - floor
            # A flat channel has no position to measure and would divide by zero.
            if not math.isfinite(span) or span <= 0.0 or not math.isfinite(last):
                continue
            scores[symbol] = 2.0 * (last - floor) / span - 1.0
        return pd.Series(scores, dtype=float)

    def _trend_discount(self, signals, scores: pd.Series, closes: pd.DataFrame) -> dict[str, float]:
        """Halve any position taken against the name's own medium-term trend.

        The comparison is against the side actually taken, not against the channel score. In a
        strong cross-section every score can be positive, so the bottom of the section is shorted
        while its score still reads long; comparing the score would leave those shorts undiscounted
        precisely when they are most exposed.
        """
        if not signals:
            return {}
        bars = max(2, toolkit.bars_for_days(float(self.ma_days)))
        window = closes.tail(bars)
        if window.empty:
            return dict(signals)
        average = window.mean(skipna=True)
        last = window.iloc[-1]
        adjusted: dict[str, float] = {}
        for symbol, signal in signals.items():
            drift = float(last.get(symbol, np.nan)) - float(average.get(symbol, np.nan))
            confirmed = math.isfinite(drift) and np.sign(drift) == np.sign(float(signal))
            # Unknown trend is treated as unconfirmed: the discount is the cautious default.
            adjusted[symbol] = float(signal) * (1.0 if confirmed else 0.5)
        return adjusted


def build_strategy():
    return ChannelPositionBreakout()
