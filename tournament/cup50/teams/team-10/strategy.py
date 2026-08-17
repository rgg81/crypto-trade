"""Fresh CUP-50 lane 10 centre: short-horizon relative-value convergence."""

from __future__ import annotations

import statistics

from crypto_trade.cup50.protocol import DecisionContextV2, TargetStrategyV2


class RelativeValueConvergence:
    uses_funding = False
    lookback_bars = 21

    def target_weights(self, context: DecisionContextV2, *, seed: int):
        changes: dict[str, float] = {}
        for symbol in context.eligible_symbols:
            history = context.bars.get(symbol)
            if history is None or len(history) <= self.lookback_bars:
                continue
            close = history["close"].astype(float)
            changes[symbol] = float(close.iloc[-1] / close.iloc[-1 - self.lookback_bars] - 1.0)
        if len(changes) < 4:
            return {}
        centre = statistics.median(changes.values())
        deviations = {symbol: centre - value for symbol, value in changes.items()}
        selected = dict(
            sorted(deviations.items(), key=lambda item: abs(item[1]), reverse=True)[:10]
        )
        gross = sum(abs(value) for value in selected.values())
        return {symbol: value / gross for symbol, value in selected.items()} if gross else {}


def build_strategy() -> TargetStrategyV2:
    return RelativeValueConvergence()
