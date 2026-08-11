"""Team 05 -- short-horizon liquidity-shock reversal.  Candidate: cascade-snapback-01.

MECHANISM
---------
A liquidation cascade is a liquidity event, not an information event. Forced sellers do not choose
their price: margin engines and stop ladders emit market orders at whatever size the book can
absorb, so price travels further than the news in it justifies, and the excess is repaid once the
forced flow is exhausted. The trade is that repayment.

The lane's whole question is what separates a forced move from an informed one, since both look
like "a big red candle". Three things do, and this candidate uses all three:

  1. the move outran its own recent scale        -- ``z <= SHOCK_Z``
  2. it was printed by a burst of orders         -- ``trade-count spike >= FLOW_SPIKE``
  3. it happened to several names at once        -- ``breadth >= MIN_BREADTH``

(1) alone is just "a big move", and a big move on ordinary order flow is usually information: this
book measured such moves CONTINUING, not reverting. (2) is what forced flow looks like at bar
resolution -- a liquidation ladder is many small orders in a short window, so the trade count
spikes harder than the notional does. (3) separates a cascade from a single-name story: margin
engines unwind correlated collateral simultaneously, so a genuine deleveraging prints the same
signature across several members of a twenty-name universe in the same eight hours.

TIMING
------
Measured, not fitted. Averaged over every qualifying event in the in-sample window, the mean
open-to-open return of the shocked names runs: bar +1 flat (the cascade finishing), bar +2 +61 bp,
bar +3 +99 bp, bar +4 flat, bars +5/+6 negative. So the book deliberately does NOT buy the bar
after the shock -- ``ENTRY_DELAY`` lets the forced selling complete -- and holds ``HOLD_BARS``
boundaries, which covers the repayment and stops before the drift back.

COST
----
Reversal at an 8h cadence is inherently expensive, and the arithmetic is unforgiving: a name held
H bars in a book renormalised at every boundary costs about 2/H of turnover per invested bar no
matter how good the signal is. This candidate therefore does not renormalise. It enters once per
episode, returns ``None`` for the whole holding window -- which holds quantities and costs nothing
-- and exits once. Turnover per episode is ~2.0 whatever H is, and the book is flat between
episodes rather than permanently invested.

WHAT IT IS NOT
--------------
It is long-only, and that is a finding rather than a preference: measured over the same window,
shorting after an UP shock lost at every horizon and under every conditioning tried, including the
squeeze case. Up moves in this universe continue; down moves that carry the forced-flow signature
revert. The certificate records the numbers.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext

# --- declared neighbourhood coordinates (module-level, single-valued, plain literals) ---------
SHOCK_Z = -2.0
FLOW_SPIKE = 2.0
MIN_BREADTH = 2

# --- fixed structure -------------------------------------------------------------------------
LOOKBACK_BARS = 60
ENTRY_DELAY = 1
HOLD_BARS = 3
MAX_NAMES = 8


class CascadeSnapback:
    """Long the names a liquidity cascade over-sold, once the forced flow has finished."""

    def __init__(self) -> None:
        self._hold_remaining = 0
        self._in_position = False
        self._last_decision: pd.Timestamp | None = None

    # -- feature extraction -------------------------------------------------------------------
    def _shock_score(self, frame: pd.DataFrame) -> float:
        """Shock intensity of the trigger bar, or 0.0 if it does not qualify.

        The trigger bar is ``ENTRY_DELAY`` bars before the newest completed one, so the entry that
        follows lands after the cascade rather than inside it. Its scale -- the volatility and the
        trade-count level it is measured against -- comes strictly from bars BEFORE it, so a shock
        can never inflate its own reference and grade itself normal.
        """
        need = LOOKBACK_BARS + ENTRY_DELAY + 2
        if len(frame) < need:
            return 0.0
        close = frame["close"].to_numpy(dtype=float)
        trades = frame["trade_count"].to_numpy(dtype=float)
        p = len(close) - 1 - ENTRY_DELAY
        window = slice(p - LOOKBACK_BARS, p)

        prior = close[window.start - 1 : window.stop]
        if prior.size < LOOKBACK_BARS + 1 or not np.isfinite(prior).all() or (prior <= 0).any():
            return 0.0
        prior_returns = prior[1:] / prior[:-1] - 1.0
        sigma = float(np.std(prior_returns, ddof=1))
        if not np.isfinite(sigma) or sigma <= 0.0:
            return 0.0
        if close[p - 1] <= 0 or not np.isfinite(close[p]) or not np.isfinite(close[p - 1]):
            return 0.0
        z = (close[p] / close[p - 1] - 1.0) / sigma
        if not np.isfinite(z) or z > SHOCK_Z:
            return 0.0

        trade_scale = float(np.median(trades[window]))
        if not np.isfinite(trade_scale) or trade_scale <= 0.0:
            return 0.0
        flow = float(trades[p]) / trade_scale
        if not np.isfinite(flow) or flow < FLOW_SPIKE:
            return 0.0
        return -z

    # -- protocol ------------------------------------------------------------------------------
    def target_weights(
        self, context: DecisionContext, *, seed: int
    ) -> Mapping[str, float] | None:
        del seed  # the book is deterministic; no sampling anywhere in it
        # Decisions arrive in ascending order. The episode clock is the only carried state and it
        # is only meaningful under that ordering, so assert it rather than trusting it.
        if self._last_decision is not None and context.decision_time <= self._last_decision:
            raise ValueError("decision times must strictly increase")
        self._last_decision = context.decision_time

        if self._hold_remaining > 0:
            self._hold_remaining -= 1
            return None  # hold quantities: no rebalance, no turnover
        if self._in_position:
            self._in_position = False
            return {}  # the snap-back window has closed

        scores: dict[str, float] = {}
        for symbol in context.eligible_symbols:
            frame = context.bars.get(symbol)
            if frame is None:
                continue
            score = self._shock_score(frame)
            if score > 0.0:
                scores[symbol] = score
        if len(scores) < MIN_BREADTH:
            return None  # no cascade: stay flat, and pay nothing to stay flat

        ranked: Sequence[tuple[str, float]] = sorted(
            scores.items(), key=lambda item: (-item[1], item[0])
        )[:MAX_NAMES]
        weight = 1.0 / len(ranked)
        self._in_position = True
        self._hold_remaining = HOLD_BARS - 1
        return {symbol: weight for symbol, _ in ranked}


def build_strategy() -> CascadeSnapback:
    return CascadeSnapback()
