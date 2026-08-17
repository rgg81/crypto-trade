"""Fresh CUP-50 lane 11 centre: historical weekday/settlement seasonality."""

from __future__ import annotations

from crypto_trade.cup50.protocol import DecisionContextV2, TargetStrategyV2


class CalendarSettlementSeasonality:
    uses_funding = False
    minimum_matches = 20

    def target_weights(self, context: DecisionContextV2, *, seed: int):
        scores: dict[str, float] = {}
        weekday, hour = context.decision_time.weekday(), context.decision_time.hour
        for symbol in context.eligible_symbols:
            history = context.bars.get(symbol)
            if history is None or len(history) < 2:
                continue
            frame = history.copy()
            returns = frame["close"].astype(float).pct_change()
            boundary = frame["close_time"].dt.ceil("8h")
            matches = returns[(boundary.dt.weekday == weekday) & (boundary.dt.hour == hour)]
            if len(matches.dropna()) >= self.minimum_matches:
                scores[symbol] = float(matches.mean())
        selected = dict(sorted(scores.items(), key=lambda item: abs(item[1]), reverse=True)[:10])
        gross = sum(abs(value) for value in selected.values())
        return {symbol: value / gross for symbol, value in selected.items()} if gross else {}


def build_strategy() -> TargetStrategyV2:
    return CalendarSettlementSeasonality()
