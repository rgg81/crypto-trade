"""ABLATION (control, never nominable) -- a RANDOM gate at matched selectivity.

The gate reads no market data at all. It is a two-state Markov chain whose transition
probabilities are set so that it is risk-on for the same fraction of the window as the nominee
(0.472) with the same mean spell lengths (90 bars on, 106 bars off, 38 switches). It starts at the
same boundary the nominee's windows first fill.

If a regime layer cannot beat this, it is not timing anything: it is being flat for a while and
collecting the mechanical benefit of lower exposure, which the common risk unit then partly
reverses. Measuring that benefit is the whole reason this control exists.
"""

from __future__ import annotations

import random
from collections.abc import Mapping

WARMUP_BARS = 512
LEAVE_ON_PROBABILITY = 0.011074
LEAVE_OFF_PROBABILITY = 0.009420
GATE_SEED = 20260814


class MatchedRandomGate:
    def __init__(self) -> None:
        self._rng = random.Random(GATE_SEED)
        self._index = 0
        self._on = True

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        index = self._index
        self._index += 1
        if index < WARMUP_BARS:
            return {}
        draw = self._rng.random()
        if self._on:
            if draw < LEAVE_ON_PROBABILITY:
                self._on = False
        elif draw < LEAVE_OFF_PROBABILITY:
            self._on = True
        if not self._on:
            return {}
        eligible = list(context.eligible_symbols)
        if not eligible:
            return {}
        weight = 1.0 / len(eligible)
        return {symbol: weight for symbol in eligible}


def build_strategy() -> MatchedRandomGate:
    return MatchedRandomGate()
