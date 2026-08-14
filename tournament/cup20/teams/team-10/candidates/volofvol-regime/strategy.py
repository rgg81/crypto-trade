"""team-10 -- volatility-regime risk-on / risk-off timing.

WHAT THIS IS
------------
A timing layer over the most transparent base book available on this universe: equal weight, long,
every eligible name. The layer decides only whether the book is ON or OFF at each decision, from a
volatility-regime statistic computed causally from past bars.

The regime variable is NOT the level of volatility. It is the **coefficient of variation of
short-horizon realised volatility over a rolling window** -- how STEADY the variance process has
been, not how large it is -- standardised against its own trailing history.

    m[t]     equal-weight market log return observed at decision t: the mean, across the symbols
             eligible at t, of log(last closed bar's close / the close before it). The last bar
             closed by decision t is the bar that OPENED at t-1, so m[t] is a strictly past
             quantity and one bar is all the lag the runner's own truncation rule permits.
    rv[j]    sqrt(mean(m[j-FORMATION_BARS+1 .. j]^2))
    vov[t]   std(rv[t-OUTER_BARS+1 .. t]) / mean(same)       <- scale-free by construction
    z[t]     (vov[t] - mean(vov[t-BASELINE_BARS+1 .. t])) / std(same)

    risk-on  <=>  z[t] <= REGIME_THRESHOLD

Risk-on emits equal weights over the eligible set; risk-off emits {} (flat). Between scheduled
boundaries the strategy returns None and the evaluator holds quantities. Every window must be
fully populated before the layer takes a view; until then the book stands flat.

WHY THIS SIGN, AND WHY NOT THE LEVEL
------------------------------------
The obvious reading of this mandate is "volatility is high, go flat". Measured through identical
machinery over the same window, a gate on the volatility LEVEL in that direction has a negative
median ranking score at every formation window tried, and a gate on the level in EITHER direction
cannot be distinguished from a random gate that is flat for the same fraction of the window. What
survives is the second-order statistic: in a market whose leverage is renewed continuously through
perpetual funding, a variance process that keeps bursting and collapsing is one where positioning
is being forcibly reset, and that is where the drift is negative. A variance process that is
steady -- steadily high or steadily low, the statistic does not care which -- is one absorbing flow
without breaking, and that is where the drift is positive. Steadiness, not size.

The evaluator renormalises every rebalance row to unit gross, so scaling weights is a no-op and
"less exposure" can only be expressed as flat or as net exposure. This layer uses flat. It declares
no risk policy: a drawdown brake would supply exactly the protection the timing layer is being
tested for, and the point of the exercise is to find out whether the regime signal supplies it.

Roles: long only. The book never emits a negative weight.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

# --- declared neighbourhood coordinates ------------------------------------------------------
# Module-level, one value each, plain numeric literals, named exactly as in neighbourhood.json.
FORMATION_BARS = 5
OUTER_BARS = 150
BASELINE_BARS = 360
REGIME_THRESHOLD = -0.30

# --- fixed, not swept ------------------------------------------------------------------------
REBALANCE_CADENCE = 1
REBALANCE_PHASE = 0


class VolOfVolRegime:
    """Risk-on when the variance process has been steady; flat when it has not."""

    def __init__(self) -> None:
        self._market: list[float] = []  # m[t], one value per decision boundary
        self._sq_cum: list[float] = [0.0]  # running sum of m^2
        self._rv: list[float] = []  # rv[j], aligned with _market
        self._vov: list[float] = []  # vov[t], NaN-free, only appended once defined
        self._index = 0

    # -- the observed market return -----------------------------------------------------------
    def _observe(self, context) -> None:
        total = 0.0
        count = 0
        for symbol in context.eligible_symbols:
            frame = context.bars.get(symbol)
            if frame is None or len(frame) < 2:
                continue
            closes = frame["close"]
            last = float(closes.iloc[-1])
            previous = float(closes.iloc[-2])
            if last > 0.0 and previous > 0.0:
                total += math.log(last / previous)
                count += 1
        value = total / count if count else 0.0
        self._market.append(value)
        self._sq_cum.append(self._sq_cum[-1] + value * value)

    # -- the regime statistic -----------------------------------------------------------------
    def _update_regime(self) -> None:
        n = len(self._market)
        if n >= FORMATION_BARS:
            window = self._sq_cum[n] - self._sq_cum[n - FORMATION_BARS]
            self._rv.append(math.sqrt(window / FORMATION_BARS))
        if len(self._rv) >= OUTER_BARS:
            window = self._rv[-OUTER_BARS:]
            mean = sum(window) / OUTER_BARS
            if mean > 0.0:
                variance = sum(value * value for value in window) / OUTER_BARS - mean * mean
                self._vov.append(math.sqrt(variance if variance > 0.0 else 0.0) / mean)

    def _regime_z(self) -> float | None:
        if len(self._vov) < BASELINE_BARS:
            return None
        window = self._vov[-BASELINE_BARS:]
        mean = sum(window) / BASELINE_BARS
        variance = sum(value * value for value in window) / BASELINE_BARS - mean * mean
        deviation = math.sqrt(variance if variance > 0.0 else 0.0)
        if deviation <= 0.0:
            return None
        return (window[-1] - mean) / deviation

    # -- the protocol -------------------------------------------------------------------------
    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        self._observe(context)
        self._update_regime()
        index = self._index
        self._index += 1

        if index % REBALANCE_CADENCE != REBALANCE_PHASE % REBALANCE_CADENCE:
            return None  # hold quantities between scheduled boundaries

        z = self._regime_z()
        if z is None or z > REGIME_THRESHOLD:
            return {}  # risk-off, or not yet enough history to have a view
        eligible = list(context.eligible_symbols)
        if not eligible:
            return {}
        weight = 1.0 / len(eligible)
        return {symbol: weight for symbol in eligible}


def build_strategy() -> VolOfVolRegime:
    return VolOfVolRegime()
