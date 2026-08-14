"""ABLATION (control, never nominable) -- a TREND gate in place of the volatility-regime gate.

Lane hygiene. The nominee's regime statistic carries a rank correlation of up to 0.31 with the
trailing market return, so part of what it knows could be momentum rather than volatility regime.
This control replaces the gate with the trailing market return itself, standardised the same way
and thresholded to the same selectivity, and changes nothing else.

    s[t]   sum(m[t-TREND_BARS+1 .. t])
    z[t]   (s[t] - mean(s[t-BASELINE_BARS+1 .. t])) / std(same)
    risk-on  <=>  z[t] >= TREND_THRESHOLD

A trend gate belongs to another team's mandate and is not something team-10 may nominate. It is run
here to find out whether the volatility channel is doing anything a price-trend channel does not
already do -- and the honest answer is reported either way.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

TREND_BARS = 90
BASELINE_BARS = 360
TREND_THRESHOLD = 0.0450
REBALANCE_CADENCE = 1


class TrendGate:
    def __init__(self) -> None:
        self._market: list[float] = []
        self._cum: list[float] = [0.0]
        self._sum: list[float] = []
        self._index = 0

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
        self._cum.append(self._cum[-1] + value)
        n = len(self._market)
        if n >= TREND_BARS:
            self._sum.append(self._cum[n] - self._cum[n - TREND_BARS])

    def _z(self) -> float | None:
        if len(self._sum) < BASELINE_BARS:
            return None
        window = self._sum[-BASELINE_BARS:]
        mean = sum(window) / BASELINE_BARS
        variance = sum(value * value for value in window) / BASELINE_BARS - mean * mean
        deviation = math.sqrt(variance if variance > 0.0 else 0.0)
        if deviation <= 0.0:
            return None
        return (window[-1] - mean) / deviation

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        self._observe(context)
        index = self._index
        self._index += 1
        if index % REBALANCE_CADENCE != 0:
            return None
        z = self._z()
        if z is None or z < TREND_THRESHOLD:
            return {}
        eligible = list(context.eligible_symbols)
        if not eligible:
            return {}
        weight = 1.0 / len(eligible)
        return {symbol: weight for symbol in eligible}


def build_strategy() -> TrendGate:
    return TrendGate()
