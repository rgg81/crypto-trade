"""Receive perpetual funding from the crowded side, and stand aside when the crowd is extreme.

Funding is the price leveraged traders pay to hold a perpetual, and the side paying it is the
crowded one, so shorting a persistently high-funding name and holding a low- or negative-funding
one collects that flow. The premium is regime-coupled rather than all-weather: the crowding that
pays best is the positioning that liquidates, and months of carry are lost in the days it unwinds.
This lane therefore treats an extreme reading as a different state from a high one -- when a
symbol's own latest rate sits far out in its own trailing distribution, the lane takes no position
in it at all rather than a larger one.

Note that funding settles every 4h for some symbols and eras and every 8h for others, so
``settlements`` counts events rather than days: the averaging window is defined in the units the
premium actually accrues in, and a symbol on a faster clock is deliberately averaged over a
shorter span of wall time.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2

# The guard window is a symbol's own funding regime, not the cross-section's: what counts as an
# extreme rate for a high-beta alt is unremarkable for BTC, so each name is scored against itself.
GUARD_HISTORY = 540
GUARD_MINIMUM = 60


class FundingCarryCrowdingGuarded:
    """Short high funding, hold low funding, and skip whatever is priced at a tail."""

    settlements = 21
    z_guard = 2.5
    top_k = 10

    def __init__(self) -> None:
        # Funding carry is a slow, persistent quantity; a low decay keeps the book from paying the
        # spread to chase settlement-to-settlement noise in a signal that changes over weeks.
        self._smoother = toolkit.TargetSmoother(decay=0.15, band=0.05)

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None

        settlements = max(1, int(self.settlements))
        top_k = max(1, int(self.top_k))
        guard = float(self.z_guard)
        history = toolkit.funding_by_symbol(context)

        signals: dict[str, float] = {}
        for symbol in map(str, context.eligible_symbols):
            series = history.get(symbol)
            if series is None or series.empty:
                continue
            clean = series.replace([np.inf, -np.inf], np.nan).dropna()
            if len(clean) < max(settlements, GUARD_MINIMUM):
                continue
            if self._is_crowded(clean, guard):
                continue
            # Positive funding means longs pay shorts, so the carry side of a high-funding name is
            # short: the signal is the negation of the average rate received.
            carry = float(clean.tail(settlements).mean())
            if math.isfinite(carry) and carry != 0.0:
                signals[symbol] = -carry

        if not signals:
            # No opinion is a real state for this lane -- a quiet or uniformly guarded funding
            # cross-section should decay the book out, not force a position.
            return self._smoother.update({}, context.eligible_symbols)

        # Rank by magnitude of carry, not by side: whether the book ends up net long or short is a
        # property of where funding sits, and forcing a symmetric split would invent an opinion.
        chosen = toolkit.top_by_absolute(pd.Series(signals, dtype=float), top_k)
        if chosen.empty:
            return self._smoother.update({}, context.eligible_symbols)

        # The signal needs no bars, but the sizing does: equal carry on a wild name and a calm one
        # is not equal risk, so names are levelled by their own realised volatility.
        panel = toolkit.close_panel(context, symbols=list(map(str, chosen.index)))
        sigma = toolkit.realised_sigma(panel)
        raw = toolkit.vol_parity(chosen.to_dict(), sigma, neutral=True, symbol_cap=0.15)
        return self._smoother.update(raw, context.eligible_symbols)

    @staticmethod
    def _is_crowded(rates: pd.Series, guard: float) -> bool:
        """True when the latest rate is a tail event in the symbol's own funding history.

        A degenerate history -- a symbol pinned at a constant rate -- has no distribution to be
        extreme within, so it is treated as ordinary rather than as infinitely crowded.
        """
        window = rates.tail(GUARD_HISTORY)
        spread = float(window.std(ddof=1))
        if not math.isfinite(spread) or spread <= 0.0:
            return False
        z = (float(window.iloc[-1]) - float(window.mean())) / spread
        return math.isfinite(z) and abs(z) >= guard


def build_strategy() -> FundingCarryCrowdingGuarded:
    return FundingCarryCrowdingGuarded()
