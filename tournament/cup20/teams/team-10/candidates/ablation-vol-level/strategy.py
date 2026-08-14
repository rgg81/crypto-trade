"""ABLATION (control, never nominable) -- THE OBVIOUS READING OF THE MANDATE.

"Volatility is high, go flat." Identical machinery to the nominee -- same market return series,
same formation and standardisation windows, same base book, same cadence, same flat risk policy --
with one substitution: the regime statistic is the LEVEL of realised volatility rather than the
steadiness of it.

    rv[t]  sqrt(mean(m[t-FORMATION_BARS+1 .. t]^2))
    z[t]   (rv[t] - mean(rv[t-BASELINE_BARS+1 .. t])) / std(same)
    risk-on  <=>  z[t] <= LEVEL_THRESHOLD

LEVEL_THRESHOLD is calibrated so this control is risk-on for the SAME fraction of the window as the
nominee. It is calibrated on the whole in-sample window, which gives the control MORE information
than the nominee has -- deliberately, because the comparison should be biased in the control's
favour rather than against it.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

FORMATION_BARS = 150
BASELINE_BARS = 360
LEVEL_THRESHOLD = 0.2844
REBALANCE_CADENCE = 1


class VolLevelGate:
    def __init__(self) -> None:
        self._sq_cum: list[float] = [0.0]
        self._n = 0
        self._rv: list[float] = []
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
        self._n += 1
        self._sq_cum.append(self._sq_cum[-1] + value * value)
        if self._n >= FORMATION_BARS:
            window = self._sq_cum[self._n] - self._sq_cum[self._n - FORMATION_BARS]
            self._rv.append(math.sqrt(window / FORMATION_BARS))

    def _z(self) -> float | None:
        if len(self._rv) < BASELINE_BARS:
            return None
        window = self._rv[-BASELINE_BARS:]
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
        if z is None or z > LEVEL_THRESHOLD:
            return {}
        eligible = list(context.eligible_symbols)
        if not eligible:
            return {}
        weight = 1.0 / len(eligible)
        return {symbol: weight for symbol in eligible}


def build_strategy() -> VolLevelGate:
    return VolLevelGate()
