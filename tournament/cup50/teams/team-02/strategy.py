"""Fresh CUP-50 lane 02 centre: causal channel breakout."""

from __future__ import annotations

from crypto_trade.cup50.protocol import DecisionContextV2, TargetStrategyV2


class BreakoutTrend:
    uses_funding = False
    lookback_bars = 189  # 63 days

    def target_weights(self, context: DecisionContextV2, *, seed: int):
        signals: dict[str, float] = {}
        for symbol in context.eligible_symbols:
            history = context.bars.get(symbol)
            if history is None or len(history) <= self.lookback_bars:
                continue
            window = history.iloc[-self.lookback_bars - 1 : -1]
            close = float(history["close"].iloc[-1])
            if close > float(window["high"].max()):
                signals[symbol] = 1.0
            elif close < float(window["low"].min()):
                signals[symbol] = -1.0
        gross = sum(abs(value) for value in signals.values())
        return {symbol: value / gross for symbol, value in signals.items()} if gross else {}


def build_strategy() -> TargetStrategyV2:
    return BreakoutTrend()
