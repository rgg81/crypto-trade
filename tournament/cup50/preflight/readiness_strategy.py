"""Non-promoteable flat-book strategy used only for the full-IS readiness replay."""

from __future__ import annotations

from crypto_trade.cup50.protocol import DecisionContextV2


class ReadinessStrategy:
    uses_bars = False
    uses_funding = False

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float]:
        del context, seed
        return {}


def build_strategy() -> ReadinessStrategy:
    return ReadinessStrategy()
