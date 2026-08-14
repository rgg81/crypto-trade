"""ABLATION (control, never nominable) -- the base book with the timing layer REMOVED.

Identical in every other respect to the team-10 nominee: equal weight, long, every eligible name,
rebalanced at every 8h boundary, flat risk policy, same warm-up. The only difference is that the
regime gate is gone and the book is always risk-on.

This is the comparison my mandate makes the centre of gravity: the identical book with the timing
layer disabled.
"""

from __future__ import annotations

from collections.abc import Mapping

WARMUP_BARS = 512  # the boundary at which the nominee's windows first become fully populated


class UntimedBaseBook:
    def __init__(self) -> None:
        self._index = 0

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        index = self._index
        self._index += 1
        if index < WARMUP_BARS:
            return {}
        eligible = list(context.eligible_symbols)
        if not eligible:
            return {}
        weight = 1.0 / len(eligible)
        return {symbol: weight for symbol in eligible}


def build_strategy() -> UntimedBaseBook:
    return UntimedBaseBook()
