"""Team 05 -- short-horizon liquidity-shock reversal.  Candidate: cascade-breadth-b3.

CONTROL STRENGTH. The cascade condition tightened from two simultaneous shocked members
to three. Asks whether the breadth conditioner is at a plateau or a cliff.

MECHANISM
---------
A liquidation cascade is a liquidity event, not an information event. Forced sellers do not choose
their price: margin engines and stop ladders emit market orders at whatever size the book can
absorb, so price travels further than the information in the move justifies, and the excess is
repaid once the forced flow is exhausted. This book buys the repayment.

The lane's whole question is what separates a forced move from an informed one, because both look
like one big red candle. What separates them here is SIMULTANEITY. Information arrives at one
asset; a margin engine unwinds correlated collateral across the whole book at once. So a move is
treated as forced only when several members of a twenty-name universe print an outsized down bar
inside the SAME eight hours:

  * outsized       -- close-to-close return over the trailing return standard deviation
                      is at or below ``SHOCK_Z``, with that deviation measured strictly BEFORE the
                      bar so a shock can never inflate its own reference and grade itself normal;
  * simultaneous   -- at least ``MIN_BREADTH`` eligible members clear that bar in the same bar.

Return magnitude alone is not enough and the certificate shows it: on this universe a large
single-name move CONTINUES rather than reverting, and a book built on magnitude alone earned 22
bps per unit of turnover against this one's 43, was positive in two folds of four instead of four,
and died at 3x cost.

A trade-count spike was tested as a third condition -- the intuition being that a liquidation
ladder is many small involuntary orders -- and it is retained here only as a disabled constant.
Measured, it removed a quarter of the events and moved gross edge per unit turnover the wrong way.
``FLOW_SPIKE = 0.0`` is cleared by every finite positive flow, so the gate is off; the flow is
still computed because the same guard rejects a symbol whose trade-count history is unusable.

TIMING
------
Measured, not fitted. Averaged over every qualifying event in the in-sample window, the mean
open-to-open return of the shocked names runs: bar +1 flat (the cascade finishing), bar +2 +61 bp
(t = 4.3), bar +3 +99 bp (t = 7.6), bar +4 flat, bars +5 and +6 negative. ``ENTRY_DELAY`` skips the
bar in which the forced selling completes; ``HOLD_BARS`` covers the repayment and stops before the
drift back.

BASKET
------
The event decides WHETHER to trade; the ranking decides WHICH names. The basket is the
``BASKET_NAMES`` eligible members that fell furthest on the trigger bar, where the forced flow
landed hardest. Sizing the basket by how many names happened to cross a threshold instead -- the
first design, trial #47 -- lets a threshold-crossing count set the book's exposure, and the
per-symbol cap then executes a two-name cascade at 0.40 gross and an eight-name one at 1.00. That
is an exposure lottery the mechanism never asked for and charter section 14.7 does not redistribute
back.

COST
----
Reversal at an 8h cadence is inherently expensive and the arithmetic is unforgiving: a name held H
bars in a book renormalised every boundary costs about 2/H of turnover per invested bar no matter
how good the signal is. This book therefore does not renormalise. It enters once, returns ``None``
for the rest of the window -- which holds quantities and costs nothing -- exits once, and is flat
between episodes.

LONG ONLY
---------
A finding, not a preference. Shorting after an UP shock lost at every horizon from 8h to 72h, at
every threshold, and under every conditioning tried, including the market-wide squeeze case. Up
moves in this universe continue; down moves that arrive as a simultaneous multi-name cascade
revert.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext

# --- declared neighbourhood coordinates (module level, one value each, plain literals) --------
SHOCK_Z = -2.0
BASKET_NAMES = 8
LOOKBACK_BARS = 60

# --- fixed structure --------------------------------------------------------------------------
MIN_BREADTH = 3
ENTRY_DELAY = 1
HOLD_BARS = 3
FLOW_SPIKE = 0.0  # disabled: every finite positive flow clears 0.0 (see module docstring)


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
        the trade-count level it is judged against -- is taken strictly from bars BEFORE it.
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
