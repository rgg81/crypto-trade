"""Fresh CUP-50 lane 04 centre: BTC-residual cross-sectional momentum."""

from __future__ import annotations

from crypto_trade.cup50.protocol import DecisionContextV2, TargetStrategyV2


class ResidualMomentum:
    uses_funding = False
    lookback_bars = 126

    def target_weights(self, context: DecisionContextV2, *, seed: int):
        benchmark = context.bars.get("BTCUSDT")
        if benchmark is None or len(benchmark) <= self.lookback_bars:
            return {}
        btc = benchmark["close"].astype(float)
        btc_return = float(btc.iloc[-1] / btc.iloc[-1 - self.lookback_bars] - 1.0)
        residuals: dict[str, float] = {}
        for symbol in context.eligible_symbols:
            history = context.bars.get(symbol)
            if history is None or len(history) <= self.lookback_bars:
                continue
            close = history["close"].astype(float)
            residuals[symbol] = float(
                close.iloc[-1] / close.iloc[-1 - self.lookback_bars] - 1.0 - btc_return
            )
        ordered = sorted(residuals, key=lambda symbol: (residuals[symbol], symbol))
        count = min(5, len(ordered) // 2)
        if not count:
            return {}
        weight = 1.0 / (2 * count)
        return {
            **{symbol: -weight for symbol in ordered[:count]},
            **{symbol: weight for symbol in ordered[-count:]},
        }


def build_strategy() -> TargetStrategyV2:
    return ResidualMomentum()
