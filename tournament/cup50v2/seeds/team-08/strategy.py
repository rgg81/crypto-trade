"""Fade the single-bar liquidation cascade, then stand aside.

A leveraged market liquidates in cascades: a move large enough to trigger margin calls forces
selling that triggers more selling, and the print overshoots whatever news started it. The tell is
a day extreme in *both* return and traded value -- an extreme return on ordinary turnover is
usually repricing, which is the one thing this lane must not fade. Each shock is faded for a fixed
number of days and then closed regardless of outcome, so the book is flat whenever nothing has
happened; that emptiness is the mechanism, not a failure of it.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2, TargetStrategyV2

# One window serves both legs: the volatility a move is judged extreme against and the turnover it
# is judged abnormal against are measured over the same trailing month, so the two halves of the
# event definition cannot disagree about what "normal" means.
_REFERENCE_DAYS = 30
_SIGMA_BARS = toolkit.bars_for_days(_REFERENCE_DAYS)
_DAYS_PER_YEAR = 365.0


class VolumeShockEventReversal:
    """Short the spike, buy the flush, hold a fixed number of days, then flatten."""

    k_sigma = 2.5
    vol_mult = 3.0
    hold_days = 5
    max_open = 10

    def __init__(self) -> None:
        # An event book cannot be rebuilt from a single decision's context: nothing in the stream
        # records which day a position was opened on, so entry dates are carried as state.
        self._open: dict[str, dict[str, object]] = {}
        self._cooldown: dict[str, pd.Timestamp] = {}
        # decay=1.0, band=0.0: a band would swallow both the open and the close of a book that is
        # empty most days. The smoother is kept only for its roster pruning and gross budget.
        self._smoother = toolkit.TargetSmoother(decay=1.0, band=0.0)

    def target_weights(
        self, context: DecisionContextV2, *, seed: int
    ) -> Mapping[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None
        now = pd.Timestamp(context.decision_time)
        eligible = set(map(str, context.eligible_symbols))
        hold = max(1, int(self.hold_days))
        self._retire(now, eligible, hold)

        panel = toolkit.close_panel(context)
        sigma = toolkit.realised_sigma(panel, bars=_SIGMA_BARS)
        shocks = self._shocks(context, panel, sigma)
        self._enter(shocks, now, eligible, hold)

        if not self._open:
            return self._smoother.update({}, context.eligible_symbols)
        signals = {symbol: float(state["direction"]) for symbol, state in self._open.items()}
        raw = toolkit.vol_parity(signals, sigma, neutral=True, symbol_cap=0.15)
        return self._smoother.update(raw, context.eligible_symbols)

    def _retire(self, now: pd.Timestamp, eligible: set[str], hold: int) -> None:
        """Close on the clock, not the outcome, and release expired re-entry bans.

        The thesis is that the overshoot decays over days, so a fixed exit states it exactly;
        letting a winner run or a loser breathe would be a second, unstated mechanism.
        """
        horizon = pd.Timedelta(days=hold)
        for symbol, state in list(self._open.items()):
            if symbol not in eligible or now - state["opened"] >= horizon:
                del self._open[symbol]
        for symbol, release in list(self._cooldown.items()):
            if now >= release:
                del self._cooldown[symbol]

    def _shocks(
        self, context: DecisionContextV2, panel: pd.DataFrame, sigma: pd.Series
    ) -> pd.Series:
        """Signed one-day returns of names that printed an extreme move on abnormal turnover."""
        moves = toolkit.trailing_return(panel, toolkit.BARS_PER_DAY)
        turnover = self._daily_turnover(context)
        if moves.empty or sigma.empty or len(turnover) <= _REFERENCE_DAYS:
            return pd.Series(dtype=float)
        latest = turnover.iloc[-1]
        # The event day is excluded from its own reference so a big print cannot raise the bar it
        # has to clear.
        usual = turnover.iloc[-1 - _REFERENCE_DAYS : -1].median()
        fired: dict[str, float] = {}
        for symbol in moves.index:
            move = float(moves[symbol])
            scale = float(sigma.get(symbol, float("nan"))) / math.sqrt(_DAYS_PER_YEAR)
            today = float(latest.get(symbol, float("nan")))
            normal = float(usual.get(symbol, float("nan")))
            if not math.isfinite(scale) or scale <= 0.0:
                continue  # a name with no measurable volatility has nothing to be extreme against
            if not math.isfinite(today) or not math.isfinite(normal) or normal <= 0.0:
                continue
            if abs(move) > self.k_sigma * scale and today > self.vol_mult * normal:
                fired[str(symbol)] = move
        return pd.Series(fired, dtype=float)

    def _daily_turnover(self, context: DecisionContextV2) -> pd.DataFrame:
        """Quote volume summed into UTC days, oldest first."""
        volume = toolkit.column_panel(context, "quote_volume")
        if volume.empty:
            return volume
        # close_time ends a bar, so the bar ending at midnight belongs to the day that just closed.
        # Stepping back a millisecond makes that true whether the stamp is inclusive or exclusive.
        stamps = pd.DatetimeIndex(volume.index) - pd.Timedelta(milliseconds=1)
        return volume.groupby(stamps.floor("D")).sum(min_count=1)

    def _enter(self, shocks: pd.Series, now: pd.Timestamp, eligible: set[str], hold: int) -> None:
        """Fade the largest shocks first, up to the concurrency limit."""
        if shocks.empty:
            return
        ranked = sorted(shocks.index, key=lambda name: (-abs(float(shocks[name])), str(name)))
        room = max(0, int(self.max_open)) - len(self._open)
        for symbol in ranked:
            if room <= 0:
                break
            if symbol not in eligible or symbol in self._open or symbol in self._cooldown:
                continue
            move = float(shocks[symbol])
            self._open[symbol] = {"direction": -1.0 if move > 0.0 else 1.0, "opened": now}
            # Bar re-entry for twice the holding period: a cascade that keeps printing events is a
            # repricing, and repeatedly refreshing the same fade is how a reversal book dies.
            self._cooldown[symbol] = now + pd.Timedelta(days=2 * hold)
            room -= 1


def build_strategy() -> TargetStrategyV2:
    return VolumeShockEventReversal()
