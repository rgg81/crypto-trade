"""Fresh CUP-50 lane 06 centre: defensive downside-risk selection."""

from __future__ import annotations

import math

from crypto_trade.cup50.protocol import DecisionContextV2, TargetStrategyV2


class DefensiveSelection:
    uses_funding = False
    lookback_bars = 126

    def target_weights(self, context: DecisionContextV2, *, seed: int):
        risks: dict[str, float] = {}
        for symbol in context.eligible_symbols:
            history = context.bars.get(symbol)
            if history is None or len(history) <= self.lookback_bars:
                continue
            returns = history["close"].pct_change().iloc[-self.lookback_bars :]
            downside = returns.clip(upper=0.0)
            risk = float(math.sqrt(float((downside * downside).mean())))
            if math.isfinite(risk):
                risks[symbol] = risk
        selected = sorted(risks, key=lambda symbol: (risks[symbol], symbol))[:10]
        return {symbol: 1.0 / len(selected) for symbol in selected} if selected else {}


def build_strategy() -> TargetStrategyV2:
    return DefensiveSelection()
