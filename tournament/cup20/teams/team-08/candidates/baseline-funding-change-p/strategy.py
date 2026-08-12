"""Team 08 transparent baseline: the crudest statement the lane can make.

The mandate is reversion in funding *dynamics*. The simplest possible expression of that,
with nothing else in it, is: for each coin take the most recent funding rate, subtract the
mean of the funding rates before it over a fixed regime window, sort the cross-section on
that difference, short the coins whose funding has risen most against their own regime and
buy the coins whose funding has fallen most. Equal weight, dollar neutral, one third of the
cross-section a side, rebalanced daily.

There is deliberately no normalisation by the coin's own funding scale, no control for the
funding LEVEL, no dispersion gate, no concentration and no holding-period logic. It exists
to be the reference every later result is read against, and to be the thing the exact sign
inversion is run on.

Causality. ``DecisionContext.funding`` is documented to contain rows strictly earlier than
the decision time, but this strategy does not rely on that: it applies the ``<`` cut itself,
on ``funding_time``, before anything is computed. The bars frame is not read at all, so no
candle -- forming or closed -- can enter a weight.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy

# --- material parameters ----------------------------------------------------------------
REGIME_WINDOW = 20  # funding events defining "the coin's own recent regime"
REBALANCE_BARS = 3  # 8h decision boundaries between rebalances (one calendar day)
SIDE_FRACTION = 3.0  # one third of the eligible cross-section on each side
MINIMUM_CROSS_SECTION = 8

# The funding archive is read as a time tail rather than a row count, so a symbol that
# settles four-hourly and one that settles eight-hourly are both covered. 45 days holds at
# least 135 eight-hourly events, comfortably more than REGIME_WINDOW + 1.
TAIL_DAYS = 45


class FundingChangeReversion:
    """Short the coins whose funding rose most against their own recent regime."""

    def __init__(self) -> None:
        self._bars_since_rebalance = REBALANCE_BARS

    def target_weights(
        self, context: DecisionContext, *, seed: int
    ) -> Mapping[str, float] | None:
        if self._bars_since_rebalance < REBALANCE_BARS:
            self._bars_since_rebalance += 1
            return None
        self._bars_since_rebalance = 1

        scores = _funding_change(context)
        eligible = [s for s in context.eligible_symbols if s in scores]
        if len(eligible) < MINIMUM_CROSS_SECTION:
            return {}
        per_side = int(len(eligible) // SIDE_FRACTION)
        if per_side < 1:
            return {}

        ordered = sorted(eligible, key=lambda s: scores[s])
        weight = 0.5 / per_side
        targets = {s: weight for s in ordered[:per_side]}
        targets.update({s: -weight for s in ordered[-per_side:]})
        return targets


def _funding_change(context: DecisionContext) -> dict[str, float]:
    """Last funding rate minus the mean of the REGIME_WINDOW rates before it."""
    frame = context.funding
    if frame is None or len(frame) == 0:
        return {}
    # Integer nanoseconds throughout: a tz-aware column's ``.to_numpy()`` is an object array
    # of Timestamps, which neither searchsorts nor compares against a naive datetime64.
    times = pd.DatetimeIndex(frame["funding_time"]).asi8
    boundary = int(pd.Timestamp(context.decision_time).value)
    start = boundary - TAIL_DAYS * 86_400_000_000_000
    lo = int(np.searchsorted(times, start, side="left"))
    hi = int(np.searchsorted(times, boundary, side="left"))  # strictly before, enforced here
    if hi <= lo:
        return {}
    symbols = frame["symbol"].to_numpy()[lo:hi]
    rates = frame["funding_rate"].to_numpy(dtype=float)[lo:hi]

    out: dict[str, float] = {}
    for symbol in context.eligible_symbols:
        own = rates[symbols == symbol]
        if own.size < REGIME_WINDOW + 1:
            continue
        latest = float(own[-1])
        regime = float(np.mean(own[-(REGIME_WINDOW + 1) : -1]))
        out[symbol] = latest - regime
    return out


def build_strategy() -> TargetStrategy:
    return FundingChangeReversion()
