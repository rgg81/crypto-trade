"""Non-promoteable full-gross strategy used only for the full-IS readiness replay."""

from __future__ import annotations

from crypto_trade.cup50.protocol import DecisionContextV2


class ReadinessStrategy:
    uses_bars = False
    uses_funding = False

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float]:
        del seed
        if not context.eligible_symbols:
            return {}
        symbols = tuple(sorted(context.eligible_symbols))
        count = min(5, len(symbols))
        boundary = int(context.decision_time.timestamp() // (8 * 60 * 60))
        offset = (boundary * count) % len(symbols)
        selected = [symbols[(offset + index) % len(symbols)] for index in range(count)]
        return {symbol: 1.0 / count for symbol in selected}


def build_strategy() -> ReadinessStrategy:
    return ReadinessStrategy()
