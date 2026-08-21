"""Trade the migration of retail attention between coins -- from the side the tape is not on.

The lane's measure is a name's share of the eligible cross-section's tape rather than its raw
turnover, because raw turnover mostly reports whether the whole market is busy. The seed read a
rising share as a name becoming the story and bought it. Measured over the research window that is
the wrong way round at every horizon a book can actually hold: conditional on which way a name is
moving, the names the crowd has *not* found are the ones that keep going, and the names the crowd
is piling into are the ones that stop. The seed's own overlay, inverted and nothing else changed,
roughly doubles its in-sample score.

So the book is built the other way, in three parts.

*Direction is a control, not a forecast.* Share of the tape and return are correlated -- a name that
moves gets looked at -- so ranking attention across the whole cross-section smuggles in a disguised
reversal bet. Splitting first on the sign of the trailing move and ranking attention *inside* each
side removes that, and it is the same distinction the lane's mandate draws between attention that
arrives without price and attention that follows it.

*Attention picks the names.* Among the rising names the book owns the quietest; among the falling
names it sells the loudest.

*The short side is guarded.* A falling name that has already collapsed is capitulation, not
distribution: it is where squeezes start, and a name too newly listed to have a trailing high cannot
be judged at all. Those names are ranked last rather than removed, so the short side is always
filled and the book never acquires a market-direction bet it did not ask for.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2

# A share reading only means something when the symbol was quoted through most of the window. A
# name that listed halfway in would otherwise be averaged over a stretch of tape it never traded,
# and its ratio would report its listing date rather than its attention.
COVERAGE = 0.75

# How far below its own trailing high a falling name may sit and still be preferred as a short.
# Deeper than this is a name that has already had its accident.
GUARD_FLOOR = 0.50


class AttentionFlow:
    """Own the quiet side of a move; sell the loud side of one."""

    fast_days = 7
    slow_days = 20
    trend_days = 18
    top_k = 10
    guard_days = 60

    def __init__(self) -> None:
        # Attention rotates over weeks, so the book should too. The blend plus the no-trade band
        # keep day-to-day share noise from being paid for at the spread.
        self._smoother = toolkit.TargetSmoother(decay=0.20, band=0.05)
        # Which names are currently owned and which are currently sold, so that a position is not
        # swapped for a marginally better-ranked one every single day. Rebuilt from the replay like
        # everything else: it is only ever the previous decision's output.
        self._held: dict[str, set[str]] = {"long": set(), "short": set()}

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None

        fast_bars = toolkit.bars_for_days(max(1, int(self.fast_days)))
        # The slow window stands for the symbol's normal level of interest. If a perturbed point
        # ever pushed it inside the fast window the ratio would compare a window with itself.
        slow_bars = max(fast_bars + 1, toolkit.bars_for_days(max(1, int(self.slow_days))))
        trend_bars = toolkit.bars_for_days(max(1, int(self.trend_days)))
        guard_bars = toolkit.bars_for_days(max(1, int(self.guard_days)))
        top_k = max(1, int(self.top_k))

        share = _share_panel(context)
        if share.empty or len(share) < slow_bars:
            return None

        attention = _attention(share, fast_bars, slow_bars)
        if attention.empty:
            return self._smoother.update({}, context.eligible_symbols)

        # Z-scoring makes "unusually large share of the tape" comparable across a cross-section
        # whose members differ in size by two orders of magnitude.
        strength = toolkit.cross_sectional_z(attention)
        closes = toolkit.close_panel(context, symbols=[str(name) for name in strength.index])
        if closes.empty:
            return self._smoother.update({}, context.eligible_symbols)
        trend = toolkit.trailing_return(closes, trend_bars)
        guarded = _guarded(closes, guard_bars)

        signals = _quiet_and_loud(strength, trend, guarded, top_k, self._held)
        if not signals:
            return self._smoother.update({}, context.eligible_symbols)

        # Equal conviction on a wild name and a calm one is not equal risk, so both sides are
        # levelled by realised volatility rather than by the size of the attention reading.
        sigma = toolkit.realised_sigma(closes)
        raw = toolkit.vol_parity(signals, sigma, neutral=True, symbol_cap=0.15)
        return self._smoother.update(raw, context.eligible_symbols)


def _share_panel(context: DecisionContextV2) -> pd.DataFrame:
    """Each bar's quote volume as a fraction of the eligible cross-section's total that bar."""
    volume = toolkit.column_panel(context, "quote_volume")
    if volume.empty:
        return volume
    # A bar with no tape is missing information rather than a zero share; masking it stops a halted
    # or not-yet-listed symbol from diluting its own average with structural zeros.
    live = volume.astype(float).where(volume > 0.0)
    totals = live.sum(axis=1, skipna=True)
    return live.div(totals.where(totals > 0.0), axis=0)


def _attention(share: pd.DataFrame, fast_bars: int, slow_bars: int) -> pd.Series:
    """Log ratio of a symbol's recent share of the tape to its own longer-run share."""
    recent = share.tail(fast_bars)
    baseline = share.tail(slow_bars)
    fast = recent.mean(skipna=True)
    slow = baseline.mean(skipna=True)
    covered = (recent.notna().sum() >= COVERAGE * fast_bars) & (
        baseline.notna().sum() >= COVERAGE * slow_bars
    )
    # Guard the log: a symbol with no tape in a window has no attention to measure, and a
    # non-positive mean would put an infinity into the cross-section that the z-score would then
    # smear over every other name.
    ratio = (fast / slow).where(covered & (fast > 0.0) & (slow > 0.0))
    ratio = ratio.replace([np.inf, -np.inf], np.nan).dropna()
    if ratio.empty:
        return pd.Series(dtype=float)
    return np.log(ratio)


def _guarded(closes: pd.DataFrame, guard_bars: int) -> set[str]:
    """Names with a full trailing window and a last price still near its high.

    Two different objections to shorting are answered by the same test. A name that has been quoted
    for less than the window has no trailing high, so there is nothing to measure it against and the
    only thing known about it is that it is new -- which in this market is a reason not to be short
    of it. A name that has one and sits far below it has already had its fall; what is left is a
    crowded, damaged position that squeezes rather than bleeds.
    """
    window = closes.tail(guard_bars)
    if window.empty:
        return set()
    counted = window.notna().sum()
    high = window.max(skipna=True)
    last = window.ffill().iloc[-1]
    floor = min(max(float(GUARD_FLOOR), 0.0), 1.0)
    keep = (counted >= guard_bars) & (high > 0.0) & (last >= (1.0 - floor) * high)
    return {str(name) for name, value in keep.items() if bool(value)}


# A held name is kept while it is still ranked inside this fraction of its own side. The entry is
# where the attention reading earns its keep; re-ranking the whole book on it every day mostly pays
# the spread to swap one marginal name for another, and turnover is the binding cost here.
RETAIN = 0.60


def _retain(order: list[str], held: set[str], top_k: int) -> list[str]:
    """Keep the names already on this side that are still ranked highly, then fill from the top."""
    band = max(top_k, int(round(len(order) * RETAIN)))
    position = {symbol: index for index, symbol in enumerate(order)}
    keep = [symbol for symbol in order[:band] if symbol in held][:top_k]
    for symbol in order:
        if len(keep) >= top_k:
            break
        if symbol not in keep:
            keep.append(symbol)
    return sorted(keep, key=lambda symbol: position[symbol])


def _quiet_and_loud(
    strength: pd.Series,
    trend: pd.Series,
    guarded: set[str],
    top_k: int,
    held: dict[str, set[str]],
) -> dict[str, float]:
    """Own the quietest names that are rising; sell the loudest guarded names that are falling.

    Ties break on symbol so an unchanged cross-section produces an unchanged book. The guard orders
    the short candidates rather than filtering them: a section whose falling names have all already
    collapsed still gets a short side, made of the least damaged of them, because the alternative is
    a book that quietly turns long whenever the market has just fallen. Either side may still run
    alone when the cross-section genuinely offers nothing on the other -- that is a real state, and
    inventing a position to fill it would be an opinion the mechanism does not have.
    """
    rising: list[str] = []
    falling: list[str] = []
    for symbol in map(str, strength.index):
        move = float(trend.get(symbol, float("nan")))
        if not math.isfinite(move) or move == 0.0:
            continue
        (rising if move > 0.0 else falling).append(symbol)
    rising.sort(key=lambda symbol: (float(strength[symbol]), symbol))
    falling.sort(
        key=lambda symbol: (0 if symbol in guarded else 1, -float(strength[symbol]), symbol)
    )
    longs = _retain(rising, held["long"], top_k)
    shorts = _retain(falling, held["short"], top_k)
    held["long"] = set(longs)
    held["short"] = set(shorts)
    signals = {symbol: 1.0 for symbol in longs}
    signals.update({symbol: -1.0 for symbol in shorts})
    return signals


def build_strategy() -> AttentionFlow:
    return AttentionFlow()
