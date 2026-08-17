"""Fresh CUP-50 lane 01 centre: slow per-contract trend."""

from __future__ import annotations

from crypto_trade.cup50.protocol import DecisionContextV2, TargetStrategyV2


class SlowTrend:
    uses_funding = False
    lookback_bars = 378  # 126 complete days

    def target_weights(self, context: DecisionContextV2, *, seed: int):
        signals: dict[str, float] = {}
        for symbol in context.eligible_symbols:
            history = context.bars.get(symbol)
            if history is None or len(history) <= self.lookback_bars:
                continue
            close = history["close"].astype(float)
            change = float(close.iloc[-1] / close.iloc[-1 - self.lookback_bars] - 1.0)
            if change:
                signals[symbol] = 1.0 if change > 0 else -1.0
        gross = sum(abs(value) for value in signals.values())
        return {symbol: value / gross for symbol, value in signals.items()} if gross else {}


def build_strategy() -> TargetStrategyV2:
    return SlowTrend()
