"""Fresh CUP-50 lane 08 centre: funding-crowding reversal."""

from __future__ import annotations

import math

from crypto_trade.cup50.protocol import DecisionContextV2, TargetStrategyV2


class FundingCrowdingReversal:
    uses_bars = False
    lookback_events = 126

    def target_weights(self, context: DecisionContextV2, *, seed: int):
        scores: dict[str, float] = {}
        for symbol in context.eligible_symbols:
            rates = context.funding.loc[
                context.funding["symbol"].astype(str) == symbol, "funding_rate"
            ].astype(float)
            if len(rates) < self.lookback_events:
                continue
            window = rates.iloc[-self.lookback_events :]
            deviation = float(window.std(ddof=1))
            if deviation <= 0 or not math.isfinite(deviation):
                continue
            z_score = float((window.iloc[-1] - window.mean()) / deviation)
            if abs(z_score) >= 1.5:
                scores[symbol] = -z_score
        selected = dict(sorted(scores.items(), key=lambda item: abs(item[1]), reverse=True)[:10])
        gross = sum(abs(value) for value in selected.values())
        return {symbol: value / gross for symbol, value in selected.items()} if gross else {}


def build_strategy() -> TargetStrategyV2:
    return FundingCrowdingReversal()
