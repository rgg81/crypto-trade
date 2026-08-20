"""Trade the rotation of retail attention between coins.

Attention in crypto is scarce and it rotates: a name's share of the total tape rises as it becomes
the story and drains as the crowd moves on, and that migration is slow enough to trade. The measure
is share of cross-sectional quote volume rather than raw turnover, because raw turnover mostly
reports whether the whole market is busy. Attention arriving without price is a different state
from attention following price, so each side is confirmed by the sign of the return over the same
window the attention was measured on.
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


class AttentionFlow:
    """Buy the names taking a growing share of the tape; sell the ones the crowd is leaving."""

    fast_days = 14
    slow_days = 90
    top_k = 10

    def __init__(self) -> None:
        # Attention rotates over weeks, so the book should too. The blend plus the no-trade band
        # keep day-to-day share noise from being paid for at the spread.
        self._smoother = toolkit.TargetSmoother(decay=0.20, band=0.05)

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None

        fast_bars = toolkit.bars_for_days(max(1, int(self.fast_days)))
        # The slow window stands for the symbol's normal level of interest. If a perturbed point
        # ever pushed it inside the fast window the ratio would compare a window with itself.
        slow_bars = max(fast_bars + 1, toolkit.bars_for_days(max(1, int(self.slow_days))))
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
        trend = toolkit.trailing_return(closes, fast_bars)

        signals = _confirmed_extremes(strength, trend, top_k)
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


def _confirmed_extremes(strength: pd.Series, trend: pd.Series, top_k: int) -> dict[str, float]:
    """Take the attention extremes, but only where price agrees with them.

    Share growing into a falling price is distribution rather than discovery, and share draining
    while price rises is a name the crowd left without anyone being hurt; neither is the state this
    lane wants to hold. Ties break on symbol so an unchanged cross-section produces an unchanged
    book. Either side may run alone -- a section where nothing qualifies as falling is a real
    state, and forcing a short would invent an opinion the mechanism does not have.
    """
    rising: list[str] = []
    falling: list[str] = []
    for symbol in map(str, strength.index):
        move = float(trend.get(symbol, float("nan")))
        if not math.isfinite(move) or move == 0.0:
            continue
        (rising if move > 0.0 else falling).append(symbol)
    rising.sort(key=lambda symbol: (-float(strength[symbol]), symbol))
    falling.sort(key=lambda symbol: (float(strength[symbol]), symbol))
    signals = {symbol: 1.0 for symbol in rising[:top_k]}
    signals.update({symbol: -1.0 for symbol in falling[:top_k]})
    return signals


def build_strategy() -> AttentionFlow:
    return AttentionFlow()
