"""Team-01 transparent baseline: unshaped per-coin time-series momentum.

The simplest thing the lane's hypothesis can be stated as. For each coin the runner declares
eligible, take the sign of that coin's own trailing log return over FORMATION_BARS 8h bars, size
it inversely to that coin's own realised volatility, and normalise the book to unit gross. No
horizon ladder, no conviction shaping, no threshold, no holding overlap, and a risk policy that
declares nothing. Nothing in it looks at any other coin: the only cross-coin operation is the
unit-gross normalisation the evaluator performs anyway.

This exists so that everything the shaped candidate adds can be read as a difference against a
baseline a reader can verify by eye, and so that the exact sign inversion of a transparent rule is
on the record.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np

from crypto_trade.tournament.protocol import DecisionContext

FORMATION_BARS = 45
VOLATILITY_BARS = 90
MINIMUM_VOLATILITY = 0.0001


class BaselineTimeSeriesMomentum:
    """sign(own trailing return) / own volatility, per coin, no shaping of any kind."""

    def target_weights(
        self, context: DecisionContext, *, seed: int
    ) -> Mapping[str, float] | None:
        formation = int(FORMATION_BARS)
        window = int(VOLATILITY_BARS)
        needed = max(formation, window) + 1
        raw: dict[str, float] = {}
        for symbol in context.eligible_symbols:
            frame = context.bars.get(symbol)
            if frame is None or len(frame) < needed + 1:
                continue
            close = frame["close"].iloc[-(needed + 1) :].to_numpy(dtype=float)
            if not np.isfinite(close).all() or (close <= 0.0).any():
                continue
            returns = np.diff(np.log(close))
            sigma = float(np.std(returns[-window:], ddof=1))
            if not math.isfinite(sigma) or sigma <= MINIMUM_VOLATILITY:
                continue
            trend = float(returns[-formation:].sum())
            if trend == 0.0:
                continue
            raw[symbol] = math.copysign(1.0, trend) / sigma
        gross = sum(abs(weight) for weight in raw.values())
        if gross <= 0.0:
            return {}
        return {symbol: weight / gross for symbol, weight in raw.items()}


def build_strategy() -> BaselineTimeSeriesMomentum:
    return BaselineTimeSeriesMomentum()
