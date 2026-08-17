"""Fresh CUP-50 lane 07 centre: settled-funding carry."""

from __future__ import annotations

from crypto_trade.cup50.protocol import DecisionContextV2, TargetStrategyV2


class FundingCarry:
    uses_bars = False
    lookback_events = 63

    def target_weights(self, context: DecisionContextV2, *, seed: int):
        scores: dict[str, float] = {}
        funding = {
            str(symbol): group["funding_rate"]
            for symbol, group in context.funding.groupby("symbol", sort=False)
        }
        for symbol in context.eligible_symbols:
            rates = funding.get(symbol)
            if rates is None:
                continue
            if len(rates) < self.lookback_events:
                continue
            # A long pays positive funding; the carry position takes the opposite side.
            scores[symbol] = -float(rates.iloc[-self.lookback_events :].mean())
        selected = dict(sorted(scores.items(), key=lambda item: abs(item[1]), reverse=True)[:10])
        gross = sum(abs(value) for value in selected.values())
        return {symbol: value / gross for symbol, value in selected.items()} if gross else {}


def build_strategy() -> TargetStrategyV2:
    return FundingCarry()
