"""Two-scale channel position: an established range left, and still being left now.

The lane's claim is that price departing a range which has held for months forces the resting stops
that accumulated at its edges and attracts momentum flow behind them, so the exit tends to run
rather than snap back. Position inside the trailing channel is the continuous way to say how close
a name is to that event, and it turns over far less than a binary flag that fires on every touch of
the edge.

One channel scale cannot separate two opposite states. A name sitting at the floor of its 15-week
channel is either still leaving that range downward, or it left months ago and has spent weeks
climbing back into it. The second is the recovery leg of a completed move, and it is precisely the
name that rips hardest when the whole cross-section rebounds -- which is why a single-scale reading
of this lane loses its money in exactly one place, market recoveries, and why the organizer's seed
scores 4.7 out of 100 in bull months while scoring 94 in chop.

So the channel is read twice. A long channel decides the ranking, because that is the range whose
stop clusters the thesis is about. A much shorter channel decides admission: a name may be taken
long only if it also sits in the upper part of its recent range, and short only if it also sits in
the lower part. Admission is a hard test rather than a discount, because a name whose recent range
position has flipped is not a weaker version of the trade, it is the opposite state, and a fraction
of it still bleeds through the episodes that hurt most.

Two consequences follow and are deliberate. The two sides are always taken in equal numbers, so the
book states a cross-sectional view and never a market-direction one. And a position whose admission
has lapsed is removed at twice the rate a new one is built, because a failed admission is an exit,
not a smaller position.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit


class ChannelPositionBreakout:
    """Rank the cross-section by channel position, admitted only where a shorter channel agrees."""

    # The evaluator overwrites these per neighbourhood point, so they are read at call time.
    channel_days = 105
    confirm_days = 18
    confirm_floor = 0.10
    quintile = 0.143

    # Funding never enters the mechanism; declaring that keeps the input honest rather than
    # accepting a stream the source silently ignores.
    uses_funding = False

    # Damping is deliberately off the tunable surface. It prices turnover, and a lane that tunes
    # its own cost damping ends up tuning the cost model instead of the mechanism. The exit rate is
    # not a free number either: it is twice the entry rate, which is the statement that a lapsed
    # admission is an exit.
    _ENTRY_DECAY = 0.20
    _EXIT_DECAY = 0.40
    _BAND = 0.05
    _SYMBOL_CAP = 0.15

    def __init__(self) -> None:
        self._smoother = _AsymmetricSmoother(
            decay=self._ENTRY_DECAY, exit_decay=self._EXIT_DECAY, band=self._BAND
        )

    def target_weights(self, context, *, seed: int):
        # Once a day: the channel moves on a months-long scale, so three decisions a day would pay
        # spread three times for the same view.
        if not toolkit.is_daily_decision(context):
            return None
        closes = toolkit.close_panel(context)
        if closes.empty:
            return {}
        highs = toolkit.column_panel(context, "high")
        lows = toolkit.column_panel(context, "low")
        anchor = self._channel_position(closes, highs, lows, float(self.channel_days))
        confirm = self._channel_position(closes, highs, lows, float(self.confirm_days))
        signals = self._select(anchor, confirm)
        if not signals:
            return {}
        weights = toolkit.vol_parity(
            signals,
            toolkit.realised_sigma(closes),
            symbol_cap=self._SYMBOL_CAP,
            neutral=True,
        )
        return self._smoother.update(weights, context.eligible_symbols)

    def _channel_position(
        self, closes: pd.DataFrame, highs: pd.DataFrame, lows: pd.DataFrame, days: float
    ) -> pd.Series:
        """Map each name onto [-1, +1]: -1 at the floor of its channel, +1 at the ceiling."""
        window = max(2, toolkit.bars_for_days(days))
        if closes.empty or len(closes) < window:
            return pd.Series(dtype=float)
        columns = [symbol for symbol in closes.columns if symbol in highs and symbol in lows]
        if not columns:
            return pd.Series(dtype=float)
        window_high = highs.loc[:, columns].tail(window)
        window_low = lows.loc[:, columns].tail(window)
        last = closes.loc[:, columns].tail(window).iloc[-1]
        # A name listed part-way through the window has no range that "has held for months"; a
        # channel measured over its short life would read as a breakout by construction.
        complete = (window_high.notna().sum() == window) & (window_low.notna().sum() == window)
        ceiling = window_high.max()
        floor = window_low.min()
        span = ceiling - floor
        # A flat channel has no position to measure and would divide by zero.
        usable = complete & span.gt(0.0) & np.isfinite(span) & np.isfinite(last)
        position = 2.0 * (last - floor) / span.where(span.gt(0.0)) - 1.0
        return position.where(usable).replace([np.inf, -np.inf], np.nan).dropna().astype(float)

    def _select(self, anchor: pd.Series, confirm: pd.Series) -> dict[str, float]:
        """Take the extremes of the long channel, among names the short channel still admits."""
        if anchor.empty or confirm.empty:
            return {}
        common = [symbol for symbol in anchor.index if symbol in confirm.index]
        if len(common) < 2:
            return {}
        floor = float(self.confirm_floor)
        long_pool = [symbol for symbol in common if float(confirm[symbol]) >= floor]
        short_pool = [symbol for symbol in common if float(confirm[symbol]) <= -floor]
        count = min(max(1, int(len(common) * float(self.quintile))), len(common) // 2)
        # Equal numbers a side. An unequal book would express how many names happened to be admitted
        # on each side, which is a market call this lane is not making and which the organizer's
        # risk unit would then size to the common volatility target as though it were the mechanism.
        take = min(count, len(long_pool), len(short_pool))
        if take < 1:
            return {}
        longs = sorted(long_pool, key=lambda symbol: (-float(anchor[symbol]), str(symbol)))[:take]
        shorts = sorted(short_pool, key=lambda symbol: (float(anchor[symbol]), str(symbol)))[:take]
        chosen = set(longs)
        signals = {str(symbol): 1.0 for symbol in longs}
        signals.update({str(symbol): -1.0 for symbol in shorts if symbol not in chosen})
        return signals


class _AsymmetricSmoother(toolkit.TargetSmoother):
    """Approach a new book gradually; leave a lapsed one at twice the rate.

    The shared smoother damps both directions equally, which means a name whose admission has
    lapsed is still two thirds held a week later. Admission here is binary, so its failure is an
    exit rather than a smaller position, and the two directions should not move at the same speed.
    """

    def __init__(self, *, decay: float, exit_decay: float, band: float) -> None:
        super().__init__(decay=decay, band=band)
        self.exit_decay = float(exit_decay)

    def update(self, raw: Mapping[str, float], eligible: Sequence[str]) -> dict[str, float] | None:
        allowed = set(map(str, eligible))
        blended: dict[str, float] = {}
        for symbol in set(self.current) | set(raw):
            if symbol not in allowed:
                continue
            previous = float(self.current.get(symbol, 0.0))
            target = float(raw.get(symbol, 0.0))
            rate = self.decay if abs(target) >= abs(previous) else self.exit_decay
            value = (1.0 - rate) * previous + rate * target
            if abs(value) >= self.prune:
                blended[symbol] = value
        total = sum(abs(value) for value in blended.values())
        if total > self.gross > 0.0:
            blended = {symbol: value / total * self.gross for symbol, value in blended.items()}
        self.current = blended
        move = sum(
            abs(blended.get(symbol, 0.0) - self.emitted.get(symbol, 0.0))
            for symbol in set(blended) | set(self.emitted)
        )
        if self.emitted and move < self.band:
            return None
        self.emitted = dict(blended)
        return dict(blended)


def build_strategy():
    return ChannelPositionBreakout()
