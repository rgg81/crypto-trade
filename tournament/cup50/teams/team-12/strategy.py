"""Fresh CUP-50 lane 12 centre: fixed, preregistered three-sleeve regime ensemble."""

from __future__ import annotations

import statistics

from crypto_trade.cup50.protocol import DecisionContextV2, TargetStrategyV2


class SimpleRegimeEnsemble:
    trend_bars = 189
    reversal_bars = 21
    funding_events = 63

    def target_weights(self, context: DecisionContextV2, *, seed: int):
        trend: dict[str, float] = {}
        recent: dict[str, float] = {}
        carry: dict[str, float] = {}
        funding = {
            str(symbol): group["funding_rate"]
            for symbol, group in context.funding.groupby("symbol", sort=False)
        }
        for symbol in context.eligible_symbols:
            history = context.bars.get(symbol)
            if history is not None and len(history) > self.trend_bars:
                close = history["close"].to_numpy(dtype=float, copy=False)
                trend[symbol] = float(close[-1] / close[-1 - self.trend_bars] - 1.0)
                recent[symbol] = float(close[-1] / close[-1 - self.reversal_bars] - 1.0)
            rates = funding.get(symbol)
            if rates is not None and len(rates) >= self.funding_events:
                carry[symbol] = -float(rates.iloc[-self.funding_events :].mean())
        recent_centre = statistics.median(recent.values()) if recent else 0.0
        raw = {
            symbol: trend.get(symbol, 0.0)
            + carry.get(symbol, 0.0)
            + recent_centre
            - recent.get(symbol, recent_centre)
            for symbol in context.eligible_symbols
        }
        selected = dict(sorted(raw.items(), key=lambda item: abs(item[1]), reverse=True)[:15])
        gross = sum(abs(value) for value in selected.values())
        return {symbol: value / gross for symbol, value in selected.items()} if gross else {}


def build_strategy() -> TargetStrategyV2:
    return SimpleRegimeEnsemble()
