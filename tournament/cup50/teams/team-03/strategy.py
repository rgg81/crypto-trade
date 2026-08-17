"""Fresh CUP-50 lane 03 centre: volume-confirmed trend."""

from __future__ import annotations

from crypto_trade.cup50.protocol import DecisionContextV2, TargetStrategyV2


class VolumeConfirmedTrend:
    uses_funding = False
    momentum_bars = 126
    volume_bars = 63

    def target_weights(self, context: DecisionContextV2, *, seed: int):
        scores: dict[str, float] = {}
        for symbol in context.eligible_symbols:
            history = context.bars.get(symbol)
            if history is None or len(history) <= self.momentum_bars:
                continue
            close = history["close"].astype(float)
            volume = history["quote_volume"].astype(float)
            baseline = float(volume.iloc[-self.volume_bars :].median())
            if baseline <= 0:
                continue
            momentum = float(close.iloc[-1] / close.iloc[-1 - self.momentum_bars] - 1.0)
            confirmation = min(2.0, float(volume.iloc[-3:].mean()) / baseline)
            scores[symbol] = momentum * confirmation
        selected = dict(sorted(scores.items(), key=lambda item: abs(item[1]), reverse=True)[:20])
        gross = sum(abs(value) for value in selected.values())
        return {symbol: value / gross for symbol, value in selected.items()} if gross else {}


def build_strategy() -> TargetStrategyV2:
    return VolumeConfirmedTrend()
