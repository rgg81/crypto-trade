"""Taker-flow pressure, with the sign flipped where the flow is being absorbed.

Taker buy volume is the half of the tape that crossed the spread to get filled: it is either
informed or reflexive, and either way it persists for days rather than minutes, so a trailing
buy/sell imbalance is a tradeable statement about who is in a hurry. The refinement that carries
the lane is absorption -- when days of aggressive buying meet a price that will not rise, the flow
is landing in a larger seller's inventory, and the honest reading of that imbalance is the opposite
of the one it looks like. So this lane follows pressure by default and fades it exactly where price
has refused to confirm it.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2

# Below this the |z| > 1 branch would fire on the bulk of the cross-section rather than on the
# genuinely lopsided tail, and the override would stop being an exception and become the rule.
FLIP_GATE = 1.0
DAYS_PER_YEAR = 365.0


class TakerFlowPressure:
    """Long the most aggressively bought names, short the most aggressively sold, absorption aside.

    Class attributes are the tunable surface; the evaluator rewrites them per neighbourhood point,
    so every one of them is read inside ``target_weights`` rather than captured at construction.
    """

    h_fast_days = 3
    h_slow_days = 10
    top_k = 10
    absorb = 0.25

    def __init__(self) -> None:
        # The fastest lane in the field: a 3-day flow window turns over quickly, so the band is
        # wider than the house default to keep the book from paying the spread on its own noise.
        self._smoother = toolkit.TargetSmoother(decay=0.30, band=0.08)

    def _imbalance(self, taker: pd.DataFrame, quote: pd.DataFrame, bars: int) -> pd.Series:
        """Signed share of trailing quote volume that was buyer-initiated, in [-1, +1].

        Both columns are per-bar sums, so summing bars over the horizon is the horizon's total and
        the ratio needs no reweighting. Dividing by traded value rather than differencing raw
        volume keeps a mega-cap and a mid-cap on the same scale.
        """
        if taker.empty or quote.empty or bars < 1 or len(quote) < bars:
            return pd.Series(dtype=float)
        buy_window = taker.tail(bars)
        total_window = quote.tail(bars)
        counts = total_window.notna().sum()
        buy = buy_window.sum(min_count=1)
        total = total_window.sum(min_count=1)
        flow = (2.0 * buy - total) / total
        usable = (counts >= max(1, bars // 2)) & (total > 0.0)
        return flow.where(usable).replace([np.inf, -np.inf], np.nan).dropna()

    def _absorption_adjusted(
        self, scores: pd.Series, move: pd.Series, limit: pd.Series
    ) -> pd.Series:
        """Flip lopsided flow that price has not confirmed; leave everything else alone."""
        adjusted: dict[str, float] = {}
        for symbol, raw in scores.items():
            score = float(raw)
            barrier = float(limit.get(symbol, float("nan")))
            response = float(move.get(symbol, float("nan")))
            confirmed = True
            if math.isfinite(barrier) and math.isfinite(response):
                if score > FLIP_GATE:
                    confirmed = response >= barrier
                elif score < -FLIP_GATE:
                    confirmed = response <= -barrier
            adjusted[str(symbol)] = score if confirmed else -score
        return pd.Series(adjusted, dtype=float)

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None
        eligible = context.eligible_symbols
        closes = toolkit.close_panel(context)
        taker = toolkit.column_panel(context, "taker_buy_quote_volume")
        quote = toolkit.column_panel(context, "quote_volume")
        if closes.empty or taker.empty or quote.empty:
            return self._smoother.update({}, eligible)
        # Inner alignment first: a symbol whose flow columns and closes disagree on coverage would
        # otherwise contribute an imbalance and a price response measured over different bars.
        taker, quote = taker.align(quote, join="inner")

        slow_bars = toolkit.bars_for_days(self.h_slow_days)
        fast = self._imbalance(taker, quote, toolkit.bars_for_days(self.h_fast_days))
        slow = self._imbalance(taker, quote, slow_bars)
        # Equal weight on purpose: the fast window says who is aggressive now, the slow one says
        # who has been aggressive for a while, and neither question dominates the other.
        blended = 0.5 * toolkit.cross_sectional_z(fast) + 0.5 * toolkit.cross_sectional_z(slow)
        blended = blended.replace([np.inf, -np.inf], np.nan).dropna()
        if blended.empty:
            return self._smoother.update({}, eligible)

        sigma = toolkit.realised_sigma(closes)
        # The bar for "price responded" is the symbol's own noise over the same horizon, not a flat
        # percentage: a quiet major moving 2% has confirmed the flow, a wild small-cap has not.
        daily_sigma = sigma / math.sqrt(DAYS_PER_YEAR)
        barrier = float(self.absorb) * daily_sigma * math.sqrt(float(self.h_slow_days))
        scores = self._absorption_adjusted(
            blended, toolkit.trailing_return(closes, slow_bars), barrier
        )

        # Shrink the book rather than refusing to trade when the roster is thinner than 2*top_k;
        # a lane that goes silent on a thin cross-section is a lane with a hole in its record.
        width = min(int(self.top_k), len(scores) // 2)
        picks = toolkit.long_short_extremes(scores, width)
        raw = toolkit.vol_parity(picks, sigma, neutral=True, symbol_cap=0.15)
        return self._smoother.update(raw, eligible)


def build_strategy() -> TakerFlowPressure:
    return TakerFlowPressure()
