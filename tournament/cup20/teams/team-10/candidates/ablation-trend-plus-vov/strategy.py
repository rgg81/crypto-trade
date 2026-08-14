"""ABLATION (control, never nominable) -- ORTHOGONALITY: does the volatility-regime channel add
anything ON TOP of a price-trend channel?

Journal #107 measured a trailing-return gate alone at matched selectivity. This run keeps that gate
exactly and ANDs it with the nominee's vol-of-vol gate, changing nothing else. If the conjunction
improves on the trend gate alone, the volatility channel carries information the price-trend channel
does not already have, which is the only version of "my lane contributes" that survives the fact
that vol-of-vol is 0.31 correlated with trailing returns.

Selectivity necessarily falls when two gates are ANDed, so this is not a matched-selectivity
comparison and is not presented as one; it is an orthogonality test.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

TREND_BARS = 90
BASELINE_BARS = 360
TREND_THRESHOLD = 0.0450
FORMATION_BARS = 5
OUTER_BARS = 150
REGIME_THRESHOLD = -0.30
REBALANCE_CADENCE = 1


class TrendPlusVolOfVol:
    def __init__(self) -> None:
        self._market: list[float] = []
        self._cum: list[float] = [0.0]
        self._sq_cum: list[float] = [0.0]
        self._sum: list[float] = []
        self._rv: list[float] = []
        self._vov: list[float] = []
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
        self._sq_cum.append(self._sq_cum[-1] + value * value)
        n = len(self._market)
        if n >= TREND_BARS:
            self._sum.append(self._cum[n] - self._cum[n - TREND_BARS])
        if n >= FORMATION_BARS:
            window = self._sq_cum[n] - self._sq_cum[n - FORMATION_BARS]
            self._rv.append(math.sqrt(window / FORMATION_BARS))
        if len(self._rv) >= OUTER_BARS:
            window = self._rv[-OUTER_BARS:]
            mean = sum(window) / OUTER_BARS
            if mean > 0.0:
                variance = sum(v * v for v in window) / OUTER_BARS - mean * mean
                self._vov.append(math.sqrt(variance if variance > 0.0 else 0.0) / mean)

    @staticmethod
    def _z(series: list[float], base: int) -> float | None:
        if len(series) < base:
            return None
        window = series[-base:]
        mean = sum(window) / base
        variance = sum(v * v for v in window) / base - mean * mean
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
        trend = self._z(self._sum, BASELINE_BARS)
        vov = self._z(self._vov, BASELINE_BARS)
        if trend is None or vov is None:
            return {}
        if trend < TREND_THRESHOLD or vov > REGIME_THRESHOLD:
            return {}
        eligible = list(context.eligible_symbols)
        if not eligible:
            return {}
        weight = 1.0 / len(eligible)
        return {symbol: weight for symbol in eligible}


def build_strategy() -> TrendPlusVolOfVol:
    return TrendPlusVolOfVol()
