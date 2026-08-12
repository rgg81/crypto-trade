"""Team 08 CONTROL -- the nominee with the cross-sectional dispersion gate REMOVED.

Mechanism
---------
Funding is the cashflow that clears a leveraged positioning imbalance, so the funding path is
the imbalance's path: building, peaking, unwinding. The LEVEL says how big the imbalance is.
What the level cannot say is where in that cycle a coin sits, and that is what this book
trades.

For each coin the current leg of its own funding term structure -- the mean of the last
``SHORT_WINDOW`` settlements -- is measured against its own recent regime, the mean of the
last ``LONG_WINDOW``, and the difference is expressed in that coin's OWN funding standard
deviation over the same regime window. A chronically high-funding coin scores near zero,
because its current leg equals its own regime; only a coin that has moved AGAINST its own
history scores at all. That is what makes this a dynamics book rather than a level book
structurally, and not merely by intent -- measured on the in-sample window, the mean
cross-sectional correlation between the emitted weights and the funding level is +0.09, and
funding carry is 16% of gross PnL, against -1.00 and -35% for the same machinery driven by
the level itself.

The cross-sectional dispersion of that measure is the second half of the signal, and it is
used as a gate rather than as a selector. When every coin's funding moves the same way the
move is market-wide -- a change in the price of leverage, not a change in who is crowded --
and the cross-section has nothing to say about relative positioning. The book only opens when
dispersion sits in the upper part of its own trailing distribution. Removing the gate takes
the in-sample book from +0.73 to -0.43 Sharpe, and a RANDOM gate admitting the same fraction
of boundaries gives -0.47, so what the gate does is choose which boundaries, not how many.

Book
----
Short the coin whose funding has risen most against its own regime, buy the one that has
fallen most, one name a side, equal weight, dollar neutral. Concentration is not decoration:
per unit gross the alpha is 22.6 bps at three names a side against 6.5 at ten, so nearly all
of it lives in the extreme name, and under a common volatility target a concentrated book
also turns over less notional for the same rotation count.

The pair is held until the imbalance it was opened on has cleared -- until the score gap
between the two legs closes to zero -- or ``MAX_HOLD_BARS`` boundaries, whichever comes
first, and is then rolled into a fresh pair if the gate is open or closed if it is not. That
exit is what makes the holding horizon a plateau rather than a spike. With a FIXED holding
period the in-sample 2x Sharpe ran +0.81 at 12 boundaries and -0.57 at 11 and -0.05 at 13:
under an event clock the holding period IS the phase offset, because it decides which
boundaries are ever sampled. With the gap exit the same axis reads +0.50/+0.42/+0.36/+0.63
across 12/15/18/24. The certificate reports both profiles.

There is no rebalance phase to choose: entries follow either an expiry or a gate opening, and
forcing the strategy to sit out its first 0-3 boundaries moves the full-window Sharpe by
0.09.

Causality
---------
The strategy applies its own ``funding_time < decision_time`` cut rather than trusting the
context to have applied one, and reads no bar at all. A change-based signal reaches back two
observations, so this is verified by corruption rather than asserted: corrupting every
funding row at or after an instant leaves every earlier decision byte-identical; corrupting
only the settlements stamped ON a boundary leaves that boundary's weights unchanged and later
ones different; corrupting every bar in the snapshot changes nothing anywhere. Note that
``funding_time`` is the exchange's raw event stamp and lands a few milliseconds after the
settlement instant on about half the rows, so the boundary test selects on
``settlement_time``; selecting on ``funding_time`` would silently test nothing on the rest.

``seed`` is accepted and unused: the book is a deterministic function of the past-only rows.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy

# --- neighbourhood coordinates (module level, single valued, plain literals) --------------
SHORT_WINDOW = 3  # funding settlements in the current leg of the term structure
LONG_WINDOW = 30  # funding settlements defining the coin's own recent regime
DISPERSION_GATE = 0.00  # trailing percentile of cross-sectional dispersion required to open
MAX_HOLD_BARS = 18  # 8h boundaries a pair may be held before it is closed regardless

# --- other frozen parameters --------------------------------------------------------------
NAMES_PER_SIDE = 1
DISPERSION_WINDOW = 270  # boundaries (90 days) the dispersion percentile is measured over
DISPERSION_MIN_OBSERVATIONS = 90
SCALE_FLOOR = 0.00002  # 0.2bp floor on the own-units denominator: funding sits exactly on the
# 0.01% anchor 37% of the time, so an unfloored standard deviation would divide by quantisation
MINIMUM_CROSS_SECTION = 8
TAIL_DAYS = 60  # funding archive tail read per decision; >= LONG_WINDOW events at 8h and at 4h


class FundingTermDynamicsReversion:
    def __init__(self) -> None:
        self._dispersion: deque[float] = deque(maxlen=DISPERSION_WINDOW)
        self._longs: tuple[str, ...] = ()
        self._shorts: tuple[str, ...] = ()
        self._bars_held = 0
        self._invested = False

    def target_weights(
        self, context: DecisionContext, *, seed: int
    ) -> Mapping[str, float] | None:
        spreads = _term_spreads(context)
        self._dispersion.append(_dispersion(spreads))

        if self._invested:
            self._bars_held += 1
            if self._bars_held < MAX_HOLD_BARS and self._still_open(spreads, context):
                return None

        book = self._form(spreads)
        if book is not None:
            self._invested = True
            self._bars_held = 0
            return book
        if self._invested:
            self._invested = False
            self._bars_held = 0
            self._longs = ()
            self._shorts = ()
            return {}  # nothing left to fade and the gate is shut: stand aside
        return None

    def _still_open(self, spreads: Mapping[str, float], context: DecisionContext) -> bool:
        """The imbalance has not yet cleared and both legs are still tradeable."""
        eligible = set(context.eligible_symbols)
        if not eligible.issuperset(self._longs) or not eligible.issuperset(self._shorts):
            return False
        try:
            gap = float(np.mean([spreads[s] for s in self._shorts])) - float(
                np.mean([spreads[s] for s in self._longs])
            )
        except KeyError:
            return False
        return bool(np.isfinite(gap)) and gap > 0.0

    def _form(self, spreads: dict[str, float]) -> dict[str, float] | None:
        if len(spreads) < max(MINIMUM_CROSS_SECTION, 2 * NAMES_PER_SIDE + 2):
            return None
        if not self._gate_open():
            return None
        ordered = sorted(spreads, key=lambda s: (spreads[s], s))
        self._longs = tuple(ordered[:NAMES_PER_SIDE])
        self._shorts = tuple(ordered[-NAMES_PER_SIDE:])
        weight = 0.5 / NAMES_PER_SIDE
        book = {s: weight for s in self._longs}
        book.update({s: -weight for s in self._shorts})
        return book

    def _gate_open(self) -> bool:
        """Is today's cross-sectional dispersion high in its own trailing distribution?"""
        if not self._dispersion or not np.isfinite(self._dispersion[-1]):
            return False
        history = np.asarray([v for v in self._dispersion if np.isfinite(v)], dtype=float)
        if history.size < DISPERSION_MIN_OBSERVATIONS:
            return True  # too little history to rank against; do not filter on noise
        current = float(self._dispersion[-1])
        below = float((history < current).sum())
        tied = float((history == current).sum())
        percentile = (below + (tied + 1.0) / 2.0) / history.size
        return percentile >= DISPERSION_GATE


def _dispersion(spreads: Mapping[str, float]) -> float:
    if len(spreads) < MINIMUM_CROSS_SECTION:
        return float("nan")
    return float(np.std(np.fromiter(spreads.values(), dtype=float)))


def _term_spreads(context: DecisionContext) -> dict[str, float]:
    """Per coin: (short-leg mean - regime mean) in that coin's own funding standard deviations."""
    frame = context.funding
    if frame is None or len(frame) == 0:
        return {}
    # Integer nanoseconds: a tz-aware column's ``.to_numpy()`` is an object array of Timestamps,
    # which neither searchsorts nor compares against a naive datetime64.
    times = pd.DatetimeIndex(frame["funding_time"]).asi8
    boundary = int(pd.Timestamp(context.decision_time).value)
    lo = int(np.searchsorted(times, boundary - TAIL_DAYS * 86_400_000_000_000, side="left"))
    hi = int(np.searchsorted(times, boundary, side="left"))  # strictly before, enforced here
    if hi <= lo:
        return {}
    symbols = frame["symbol"].to_numpy()[lo:hi]
    rates = frame["funding_rate"].to_numpy(dtype=float)[lo:hi]

    out: dict[str, float] = {}
    for symbol in sorted(context.eligible_symbols):
        own = rates[symbols == symbol]
        if own.size < SHORT_WINDOW:
            continue
        regime = own[-LONG_WINDOW:]
        value = (float(np.mean(own[-SHORT_WINDOW:])) - float(np.mean(regime))) / max(
            float(np.std(regime)), SCALE_FLOOR
        )
        if np.isfinite(value):
            out[symbol] = value
    return out


def build_strategy() -> TargetStrategy:
    return FundingTermDynamicsReversion()
