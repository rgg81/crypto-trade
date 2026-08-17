"""Fresh CUP-50 lane 05 centre: liquidity-shock reversal."""

from __future__ import annotations

from crypto_trade.cup50.protocol import DecisionContextV2, TargetStrategyV2


class LiquidityShockReversal:
    uses_funding = False
    lookback_bars = 84

    def target_weights(self, context: DecisionContextV2, *, seed: int):
        scores: dict[str, float] = {}
        for symbol in context.eligible_symbols:
            history = context.bars.get(symbol)
            if history is None or len(history) <= self.lookback_bars:
                continue
            window = history.iloc[-self.lookback_bars :]
            volume = window["quote_volume"]
            baseline = float(volume.median())
            previous = float(window["close"].iloc[-2])
            if baseline <= 0 or previous <= 0:
                continue
            shock = float(volume.iloc[-1] / baseline)
            recent_return = float(window["close"].iloc[-1] / previous - 1.0)
            if shock >= 2.0:
                scores[symbol] = -recent_return * shock
        selected = dict(sorted(scores.items(), key=lambda item: abs(item[1]), reverse=True)[:10])
        gross = sum(abs(value) for value in selected.values())
        return {symbol: value / gross for symbol, value in selected.items()} if gross else {}


def build_strategy() -> TargetStrategyV2:
    return LiquidityShockReversal()
