"""Team 03 -- momentum admitted only when the path that produced it looks like a trend.

Mechanism
---------
Two coins can post the same trailing return by completely different paths. Over a formation
window of ``FORMATION_BARS`` 8-hour bars we read the net displacement to get a DIRECTION, and we
read the RUN STRUCTURE of the individual bars to decide whether that direction deserves any size
at all. The run statistic is the count of bars whose own step agreed with the net direction,
standardised against a coin-flip null:

    z = (2 * agreeing_fraction - 1) * sqrt(FORMATION_BARS)

A name is admitted only when ``z >= PERSISTENCE_Z_FLOOR``. Standardising matters: a fixed
FRACTION threshold is a different test at every window length -- under the null the fraction
concentrates as sqrt(N) -- so a fraction gate silently changes selectivity whenever the formation
moves, which makes the formation axis a threshold axis in disguise. In z units the selectivity is
held roughly fixed while the horizon moves.

Why run structure should carry information that the endpoint return does not: on the twenty most
liquid perpetuals a 5-day displacement of a given size arrives either as many consecutive
eight-hour sessions of one-sided flow -- slow leverage accumulation, funding and basis pulling in
the same direction, the reflexive regime that keeps going -- or as one or two violent impulses
(a liquidation cascade, a single repricing headline) around otherwise two-sided flow. The first
kind of move has flow behind it that has not finished; the second has already spent itself and is
as likely to retrace. The endpoint return cannot tell them apart. The run count can.

The falsifier we pre-registered against this is the one that matters: at a fixed momentum
magnitude the high-persistence and low-persistence halves should continue at the same rate if the
story is false. They do not -- see RESEARCH-CERTIFICATE.md -- and the gate-removal ablation is
journaled beside the nominee.

Controls, none of which is the mechanism
----------------------------------------
* inverse-volatility weighting inside the admitted set, so one high-beta alt cannot own the book;
* ``SMOOTH_BARS`` overlapping tranches -- the target is the average of the admitted book over the
  last SMOOTH_BARS bars -- which sets the holding period and is what makes the turnover and
  cost-density floors reachable at all;
* ``NET_EXPOSURE_DAMPING``, a partial subtraction of the book's own average weight, which trims
  (but deliberately does not remove) the net directional tilt the gate produces in a one-way
  market. At the declared value the executed book still carries roughly a third of its gross as
  net exposure: this is a risk control on a directional trend book, not a neutralisation.

The evaluator normalises every emitted row to unit gross, so nothing here can express a view on
the book's overall size -- only on which names, which side, and in what proportion.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext

# --- declared neighbourhood coordinates -------------------------------------------------------
FORMATION_BARS = 15
PERSISTENCE_Z_FLOOR = 1.10
SMOOTH_BARS = 33
NET_EXPOSURE_DAMPING = 0.45
REBALANCE_PHASE = 1

# --- other material parameters ----------------------------------------------------------------
REBALANCE_EVERY = 3

# Ablation switches. They are 1 in the nominee and exist so that the journaled ablations run the
# IDENTICAL code path with one control removed, rather than a second implementation that could
# differ somewhere else and be credited to the control.
USE_GATE = 0
USE_INVERSE_VOLATILITY = 1

_BAR_NANOSECONDS = 8 * 3600 * 1_000_000_000


def _boundary_index(decision_time: pd.Timestamp) -> int:
    """Which 8-hour slot of the UTC grid this decision sits in.

    The epoch is a multiple of eight hours, so this is a stable, state-free index: the same
    boundary always gets the same number regardless of where a run starts.
    """
    return int(pd.Timestamp(decision_time).value // _BAR_NANOSECONDS)


def _admitted_history(closes: np.ndarray) -> np.ndarray:
    """Signed, inverse-vol-scaled admitted position at each of the last ``SMOOTH_BARS`` bars.

    Index 0 is the most recent bar. A bar with too little history, or one whose formation window
    fails the run gate, contributes exactly zero.
    """
    formation = int(FORMATION_BARS)
    smooth = int(SMOOTH_BARS)
    steps = np.diff(np.log(closes))
    usable = min(smooth, steps.size - formation + 1)
    if usable <= 0:
        return np.zeros(0)
    # windows[j] is the block of `formation` steps ending j bars before the last one.
    windows = np.lib.stride_tricks.sliding_window_view(steps, formation)[-usable:][::-1]
    displacement = windows.sum(axis=1)
    direction = np.sign(displacement)
    agreeing = (np.sign(windows) == direction[:, None]).sum(axis=1) / formation
    score = (2.0 * agreeing - 1.0) * np.sqrt(formation)
    volatility = windows.std(axis=1, ddof=1)
    admitted = (direction != 0.0) & (volatility > 0.0)
    if USE_GATE:
        admitted &= score >= PERSISTENCE_Z_FLOOR
    position = np.zeros(usable)
    if USE_INVERSE_VOLATILITY:
        np.divide(direction, volatility, out=position, where=admitted)
    else:
        np.copyto(position, direction, where=admitted)
    return position


class GatedTrendStrategy:
    """Emit signed targets on the declared cadence; hold quantities on every other boundary."""

    def target_weights(
        self, context: DecisionContext, *, seed: int
    ) -> Mapping[str, float] | None:
        del seed  # the rule is deterministic; nothing here is sampled
        if _boundary_index(context.decision_time) % int(REBALANCE_EVERY) != int(
            REBALANCE_PHASE
        ) % int(REBALANCE_EVERY):
            return None

        symbols: Sequence[str] = tuple(context.eligible_symbols)
        histories: dict[str, np.ndarray] = {}
        depth = 0
        for symbol in symbols:
            frame = context.bars.get(symbol)
            if frame is None or len(frame) < int(FORMATION_BARS) + 1:
                continue
            closes = frame["close"].to_numpy(dtype=float)
            if not np.isfinite(closes).all() or (closes <= 0.0).any():
                continue
            history = _admitted_history(closes)
            if history.size == 0:
                continue
            histories[symbol] = history
            depth = max(depth, history.size)
        if not histories:
            return {}

        # Each historical bar's cross-section is normalised to unit gross before averaging, so a
        # bar on which only two names were admitted contributes as much book as one on which
        # twelve were. The average over bars is the overlapping-tranche construction: at most one
        # tranche of the book can be re-formed per bar, which is what bounds turnover.
        names = tuple(histories)
        matrix = np.zeros((depth, len(names)))
        for column, symbol in enumerate(names):
            history = histories[symbol]
            matrix[: history.size, column] = history
        gross = np.abs(matrix).sum(axis=1)
        matrix[gross > 0.0] /= gross[gross > 0.0, None]
        weights = matrix.mean(axis=0)

        live = np.abs(weights) > 0.0
        if not live.any():
            return {}
        if NET_EXPOSURE_DAMPING > 0.0:
            weights[live] -= NET_EXPOSURE_DAMPING * weights.sum() / live.sum()

        total = np.abs(weights).sum()
        if not np.isfinite(total) or total <= 0.0:
            return {}
        weights = weights / total
        return {
            symbol: float(weight)
            for symbol, weight in zip(names, weights, strict=True)
            if weight != 0.0 and np.isfinite(weight)
        }


def build_strategy() -> GatedTrendStrategy:
    return GatedTrendStrategy()
