"""Team-01 candidate: slow per-coin time-series momentum on the point-in-time top-20 perpetuals.

Mechanism. A perpetual future has no expiry and no overnight gap, and its marginal buyer is a
leveraged one. A move that persists therefore feeds itself: unrealised profit on open perpetual
positions is collateral, so a trend mechanically expands the buying power of the side that is
winning, while the losing side is liquidated into the move rather than out of it. The 24/7 tape
gives that loop no nightly reset in which positioning can be squared, and the funding rate -- the
only force pulling the perpetual back to spot -- settles a few basis points every eight hours,
which is far too small to stop a trend and only large enough to tax the crowd that is riding it.
The hypothesis this candidate tests is that the resulting own-price persistence, measured over
weeks on a coin's own history and nothing else, is still worth more than 7.5 bps a side on the
twenty most liquid names in the market.

Construction, per coin, from that coin's own closed bars and nothing else:

    r          8h log returns of the coin's own closes
    sigma      standard deviation of r over VOLATILITY_MULTIPLE * FORMATION_BARS bars
    z(l)       sum(r over the last l bars) / (sigma * sqrt(l)), a trend t-statistic,
               for l over a four-rung ladder at 1/3, 2/3, 1 and 2 times FORMATION_BARS
    c(l)       clip( sign(z) * max(|z| - TREND_THRESHOLD, 0), -1, +1 )
    c          the mean of c(l) over the four rungs
    c_bar      the mean of c over the last HOLDING_BARS decision boundaries
    w          c_bar / sigma, normalised to unit gross across the eligible set

Three deliberate properties.

*The ladder* averages four estimates of one latent quantity -- how strongly this coin is trending
-- rather than betting the book on a single lookback. The horizons are noisy measurements of the
same state, so averaging them cuts estimator variance without changing what is being estimated.

*The soft threshold* is a shrinkage, not a filter on a second statistic: it subtracts a constant
from the magnitude of the same t-statistic that carries the signal. It does two things at once.
Near a zero crossing a hard sign would trade the entire position for an arbitrarily small change
in the underlying trend, which is pure cost carrying no information; the shrunk conviction passes
through zero continuously instead. And when the trend is not distinguishable from noise the coin's
own weight is exactly zero rather than a full-size guess.

*The holding overlap* is a mean over the last HOLDING_BARS boundaries' convictions, which is the
overlapping-portfolio construction written per coin. It is the strategy's holding horizon, and it
is deliberately expressed this way rather than as a rebalance clock: a clocked cadence longer than
one bar has a phase offset, and a result obtained at one phase is a result about that phase. This
formulation decides at every boundary and has no phase to choose.

Nothing here compares one coin against another. Every quantity is a function of a single coin's
own price history; the only cross-coin operation in the file is the unit-gross normalisation, which
the evaluator performs on any book it is handed regardless of what the team returns.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np

from crypto_trade.tournament.protocol import DecisionContext

# --- declared neighbourhood coordinates -------------------------------------------------------
FORMATION_BARS = 45
HOLDING_BARS = 9
TREND_THRESHOLD = 0.35
# ----------------------------------------------------------------------------------------------

# Frozen structural choices, not swept coordinates.
VOLATILITY_MULTIPLE = 2
LADDER_THIRDS_ONE = 1
LADDER_THIRDS_TWO = 2
LADDER_THIRDS_THREE = 3
LADDER_THIRDS_SIX = 6
# Per-bar volatility below this is a stale or pegged feed, not a tradeable one: 1e-4 per 8h bar is
# under 0.2% annualised, which no live perpetual on this universe has ever printed over 30 days.
# Sizing is 1/sigma, so admitting such a coin would hand it the whole book.
MINIMUM_VOLATILITY = 0.0001


class SlowTimeSeriesMomentum:
    """Per-coin own-history trend conviction, sized inversely to that coin's own volatility."""

    def target_weights(
        self, context: DecisionContext, *, seed: int
    ) -> Mapping[str, float] | None:
        formation = int(FORMATION_BARS)
        holding = max(1, int(HOLDING_BARS))
        threshold = float(TREND_THRESHOLD)
        window = max(3, int(VOLATILITY_MULTIPLE) * formation)
        legs = [
            max(3, int(round(formation * thirds / 3.0)))
            for thirds in (
                LADDER_THIRDS_ONE,
                LADDER_THIRDS_TWO,
                LADDER_THIRDS_THREE,
                LADDER_THIRDS_SIX,
            )
        ]
        span = max(max(legs), window) + holding

        raw: dict[str, float] = {}
        for symbol in context.eligible_symbols:
            weight = self._weight(context, symbol, legs, window, holding, threshold, span)
            if weight is not None:
                raw[symbol] = weight
        gross = sum(abs(value) for value in raw.values())
        if gross <= 0.0:
            return {}
        return {symbol: value / gross for symbol, value in raw.items()}

    @staticmethod
    def _weight(context, symbol, legs, window, holding, threshold, span):
        frame = context.bars.get(symbol)
        if frame is None or len(frame) < span + 1:
            return None
        close = frame["close"].iloc[-(span + 1) :].to_numpy(dtype=float)
        if not np.isfinite(close).all() or (close <= 0.0).any():
            return None
        returns = np.diff(np.log(close))
        total = np.concatenate(([0.0], np.cumsum(returns)))
        square = np.concatenate(([0.0], np.cumsum(returns * returns)))
        count = len(returns)

        conviction_sum = 0.0
        sigma_now = 0.0
        for age in range(holding):
            end = count - age
            summed = total[end] - total[end - window]
            squared = square[end] - square[end - window]
            variance = (squared - summed * summed / window) / (window - 1)
            if not math.isfinite(variance) or variance <= 0.0:
                return None
            sigma = math.sqrt(variance)
            if sigma <= MINIMUM_VOLATILITY:
                return None
            if age == 0:
                sigma_now = sigma
            rung_sum = 0.0
            for leg in legs:
                trend = total[end] - total[end - leg]
                z = trend / (sigma * math.sqrt(leg))
                shrunk = math.copysign(max(abs(z) - threshold, 0.0), z)
                rung_sum += max(-1.0, min(1.0, shrunk))
            conviction_sum += rung_sum / len(legs)

        conviction = conviction_sum / holding
        if conviction == 0.0 or sigma_now <= 0.0:
            return None
        return conviction / sigma_now


def build_strategy() -> SlowTimeSeriesMomentum:
    return SlowTimeSeriesMomentum()
