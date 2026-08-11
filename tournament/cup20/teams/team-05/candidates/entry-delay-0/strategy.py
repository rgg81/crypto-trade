"""Team 05 -- short-horizon liquidity-shock reversal.  Candidate: entry-delay-0.

ENTRY PHASE. Buy at the first boundary after the shock instead of waiting one, which is
the only phase offset an event-triggered book has.

MECHANISM
---------
A liquidation cascade is a liquidity event, not an information event. Forced sellers do not choose
their price: margin engines and stop ladders emit market orders at whatever size the book can
absorb, so price travels further than the information in the move justifies, and the excess is
repaid once the forced flow is exhausted. This book buys the repayment.

The lane's whole question is what separates a forced move from an informed one, because both look
like one big red candle. Three conditions do the separating here:

  1. the move outran its own recent scale   -- ``z <= SHOCK_Z``
  2. it was printed by a burst of orders    -- ``trade count / trailing median >= FLOW_SPIKE``
  3. it hit several names at once           -- at least ``MIN_BREADTH`` members, same bar

(1) alone is just "a big move", and on this universe a big move on ordinary order flow CONTINUES
rather than reverting. (2) is what forced flow looks like at bar resolution: a liquidation ladder
is many small involuntary orders in a short window, so the trade count spikes harder than notional.
(3) separates a deleveraging from a single-name story -- a margin engine unwinds correlated
collateral simultaneously, so a real cascade prints the same signature across several members of a
twenty-name universe inside the same eight hours.

Conditions (1) and (2) define the EVENT. The basket is then the ``BASKET_NAMES`` eligible members
that fell furthest on the trigger bar, which is where the forced flow landed hardest. Sizing the
basket by how many names happened to cross a threshold would instead let a threshold-crossing count
set the book's exposure, and the per-symbol cap would then execute a two-name cascade at 0.40 gross
and an eight-name one at 1.00 -- an exposure lottery the mechanism never asked for.

TIMING
------
Measured, not fitted. Averaged over every qualifying event in the in-sample window, the mean
open-to-open return of the shocked names runs: bar +1 flat (the cascade finishing), bar +2 +61 bp
(t = 4.3), bar +3 +99 bp (t = 7.6), bar +4 flat, bars +5 and +6 negative. So ``ENTRY_DELAY`` skips
the bar in which the forced selling completes, and ``HOLD_BARS`` covers the repayment and stops
before the drift back.

COST
----
Reversal at an 8h cadence is inherently expensive and the arithmetic is unforgiving: a name held H
bars in a book renormalised every boundary costs about 2/H of turnover per invested bar no matter
how good the signal is. This book therefore does not renormalise. It enters once, returns ``None``
for the rest of the window -- which holds quantities and costs nothing -- exits once, and is flat
between episodes. Turnover per episode is about 2.0 whatever H is.

LONG ONLY
---------
A finding, not a preference. Shorting after an UP shock lost at every horizon from 8h to 72h, at
every threshold, and under every conditioning tried, including the market-wide squeeze case. Up
moves in this universe continue; down moves carrying the forced-flow signature revert.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext

# --- declared neighbourhood coordinates (module level, one value each, plain literals) --------
SHOCK_Z = -2.0
FLOW_SPIKE = 2.0
BASKET_NAMES = 8

# --- fixed structure --------------------------------------------------------------------------
MIN_BREADTH = 2
LOOKBACK_BARS = 60
ENTRY_DELAY = 0
HOLD_BARS = 3


class CascadeSnapback:
    """Long the names a liquidity cascade over-sold, once the forced flow has finished."""

    def __init__(self) -> None:
        self._hold_remaining = 0
        self._in_position = False
        self._last_decision: pd.Timestamp | None = None

    def _features(self, frame: pd.DataFrame) -> tuple[float, float] | None:
        """``(z, flow)`` for the trigger bar, or ``None`` when it cannot be measured.

        The trigger bar sits ``ENTRY_DELAY`` bars before the newest completed one, so the entry
        that follows lands after the cascade rather than inside it. Its scale -- the volatility and
        the trade-count level it is judged against -- is taken strictly from bars BEFORE it, so a
        shock can never inflate its own reference and grade itself normal.
        """
        need = LOOKBACK_BARS + ENTRY_DELAY + 2
        if len(frame) < need:
            return None
        close = frame["close"].to_numpy(dtype=float)
        trades = frame["trade_count"].to_numpy(dtype=float)
        p = len(close) - 1 - ENTRY_DELAY
        start = p - LOOKBACK_BARS

        prior = close[start - 1 : p]
        if prior.size < LOOKBACK_BARS + 1 or not np.isfinite(prior).all() or (prior <= 0).any():
            return None
        prior_returns = prior[1:] / prior[:-1] - 1.0
        sigma = float(np.std(prior_returns, ddof=1))
        if not np.isfinite(sigma) or sigma <= 0.0:
            return None
        if not np.isfinite(close[p]) or not np.isfinite(close[p - 1]) or close[p - 1] <= 0.0:
            return None
        z = (close[p] / close[p - 1] - 1.0) / sigma
        if not np.isfinite(z):
            return None

        trade_scale = float(np.median(trades[start:p]))
        if not np.isfinite(trade_scale) or trade_scale <= 0.0:
            return None
        flow = float(trades[p]) / trade_scale
        if not np.isfinite(flow):
            return None
        return z, flow

    def target_weights(
        self, context: DecisionContext, *, seed: int
    ) -> Mapping[str, float] | None:
        del seed  # deterministic book; nothing here samples
        # The episode clock is the only carried state and it is only meaningful under ascending
        # decision times, so assert the ordering rather than assuming it.
        if self._last_decision is not None and context.decision_time <= self._last_decision:
            raise ValueError("decision times must strictly increase")
        self._last_decision = context.decision_time

        if self._hold_remaining > 0:
            self._hold_remaining -= 1
            return None  # hold quantities: no rebalance, no turnover
        if self._in_position:
            self._in_position = False
            return {}  # the snap-back window has closed

        depth: dict[str, float] = {}
        qualifying = 0
        for symbol in context.eligible_symbols:
            frame = context.bars.get(symbol)
            if frame is None:
                continue
            measured = self._features(frame)
            if measured is None:
                continue
            z, flow = measured
            if z < 0.0:
                depth[symbol] = -z
            if z <= SHOCK_Z and flow >= FLOW_SPIKE:
                qualifying += 1
        if qualifying < MIN_BREADTH or not depth:
            return None  # no cascade: stay flat, and pay nothing to stay flat

        ranked = sorted(depth.items(), key=lambda item: (-item[1], item[0]))[:BASKET_NAMES]
        weight = 1.0 / len(ranked)
        self._in_position = True
        self._hold_remaining = HOLD_BARS - 1
        return {symbol: weight for symbol, _ in ranked}


def build_strategy() -> CascadeSnapback:
    return CascadeSnapback()
