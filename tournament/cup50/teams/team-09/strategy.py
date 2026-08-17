"""Fresh CUP-50 lane 09 centre: taker-flow pressure."""

from __future__ import annotations

from crypto_trade.cup50.protocol import DecisionContextV2, TargetStrategyV2


class TakerFlowPressure:
    uses_funding = False
    lookback_bars = 42

    def target_weights(self, context: DecisionContextV2, *, seed: int):
        scores: dict[str, float] = {}
        for symbol in context.eligible_symbols:
            history = context.bars.get(symbol)
            if (
                history is None
                or len(history) < self.lookback_bars
                or "taker_buy_quote_volume" not in history
            ):
                continue
            window = history.iloc[-self.lookback_bars :]
            total = float(window["quote_volume"].astype(float).sum())
            if total <= 0:
                continue
            buy_share = float(window["taker_buy_quote_volume"].astype(float).sum()) / total
            scores[symbol] = buy_share - 0.5
        selected = dict(sorted(scores.items(), key=lambda item: abs(item[1]), reverse=True)[:15])
        gross = sum(abs(value) for value in selected.values())
        return {symbol: value / gross for symbol, value in selected.items()} if gross else {}


def build_strategy() -> TargetStrategyV2:
    return TakerFlowPressure()
