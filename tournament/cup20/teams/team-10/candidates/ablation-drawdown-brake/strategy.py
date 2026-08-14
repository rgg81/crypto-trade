"""ABLATION (control, never nominable) -- the base book with NO timing layer and a declared
DRAWDOWN BRAKE instead.

The point of the control: a drawdown brake is what the declared risk policy gives a team for free,
and "high volatility, go flat" is mostly a drawdown brake wearing a signal's clothes. If a brake on
the untimed base book reaches the same place as the regime layer, the regime layer has added
nothing that was not already available without any signal at all.

Strategy source is byte-identical in behaviour to ablation-untimed; the difference is entirely in
risk_policy.json, which declares brakes at 5% / 10% / 15% drawdown scaling gross to 0.60 / 0.30 /
0.10. Charter section 6 is explicit that a declared brake watches the book the common risk unit has
already resized, so the levels at which it engages are not the levels it would see on this book
standing alone; that is disclosed rather than corrected for.
"""

from __future__ import annotations

from collections.abc import Mapping

WARMUP_BARS = 512


class BrakedBaseBook:
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


def build_strategy() -> BrakedBaseBook:
    return BrakedBaseBook()
