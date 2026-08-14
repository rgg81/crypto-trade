"""Team 11 -- desk-closed share of trading activity, volatility-neutralised.

MECHANISM
---------
The 8h decision grid is the funding settlement clock, and it cuts the day at the boundaries the
market's own accounting uses. Around that clock sit participants who keep human schedules, and the
schedule they keep says who they are.

Two of the resulting calendar cells are the hours in which professional desks are shut: the
00:00-08:00 UTC settlement session, the thinnest window of the crypto day (27.4% of in-sample quote
volume against 39.4% for 08:00-16:00), and the weekend, when institutional participation
withdraws. A coin's DESK-CLOSED SHARE is the fraction of its trading activity that lands in those
cells. It contains no return, no funding rate and no volatility -- it is purely a statement about
WHEN a coin trades, and therefore about who is left holding it. A coin whose activity concentrates
in the desk-closed cells is priced predominantly by leveraged retail perpetual flow; a coin whose
activity concentrates in the weekday European and US sessions is priced alongside spot and
institutional participation. The book is short the former and long the latter.

WHY THE RAW SHARE IS NOT THE SIGNAL
-----------------------------------
Measured raw, the desk-closed share is cross-sectionally correlated with realised volatility, and
about 70% of its raw predictive content is shared with volatility, size and funding crowding --
which are other teams' mandates, not this one's. Shorting the raw share also embeds a short
high-beta tilt that a retail mania runs over, which is exactly what the 2020-08 to 2021-08 fold is.
The signal is therefore the share **residualised cross-sectionally against realised volatility**:
one ordinary least squares projection, per boundary, of the share's rank on the volatility rank.
What is left is the part of "when this coin trades" that volatility does not already say.

THE CLAIM IS ABOUT THE CLOCK AND WAS TESTED AS ONE
--------------------------------------------------
Against a shape-matched scrambled clock -- each day independently permuting its own three
settlement slots, each week independently nominating its own two "weekend" days, so cell sizes,
coin mix and volatility mix are held exactly and only the alignment with the real clock is
destroyed -- the true partition's rank IC is -0.0227 against a null centred at +0.0004 with
standard deviation 0.0051 (z = -4.5, 0 of 300 draws as extreme).

CAUSALITY
---------
Every quantity is read from bars that have already closed at the decision. The share and the
volatility are ratios and sums over past closed bars only; the transaction open the evaluator
fills at is never visible here, and no fitted artifact is staged -- the rolling accumulators are
built from the rows the DecisionContext streams during the run.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import pandas as pd

# --------------------------------------------------------------------------------------------
# Declared neighbourhood coordinates. Each is a module-level plain numeric literal on one line,
# assigned exactly once, and each visibly moves the executed book (charter 7.2 / playbook 6.1).
# --------------------------------------------------------------------------------------------

ACTIVITY_WINDOW_BARS = 252
"""Closed 8h bars over which the desk-closed share is measured (252 bars = 84 days)."""

VOLATILITY_WINDOW_BARS = 252
"""Closed 8h bars over which the realised volatility that is projected out is measured. Held equal
to ACTIVITY_WINDOW_BARS by design: the control must describe the same stretch of history as the
measure it is projected out of, which fixes it a priori rather than by search."""

REBALANCE_PHASE_BARS = 4
"""Which bar of the weekly cadence carries the rebalance, counted from Monday 00:00 UTC. At
cadence 21 the phase decomposes as (weekday, settlement slot) = (phase // 3, phase % 3), so 4 is
Tuesday 08:00 UTC -- a weekday boundary inside the deepest-liquidity session of the day. Chosen by
the same mechanism the signal rests on (do not trade when the desks are shut), not by the surface:
the full 21-point phase surface is reported in the research certificate and phase 4 sits at its
median, not at its maximum."""

WEIGHT_POWER = 1.0
"""Exponent applied to the centred cross-sectional rank before normalisation. Continuous, so every
declared variation moves every weight rather than passing through a quantiser."""

# --------------------------------------------------------------------------------------------
# Fixed structure (not swept)
# --------------------------------------------------------------------------------------------

REBALANCE_CADENCE_BARS = 21
"""Exactly one week, which is the cadence the mechanism is stated at and the cadence the universe
itself reconstitutes on."""

MINIMUM_NAMES = 8
"""Below this many measurable eligible symbols the book stands aside for that boundary."""

MINIMUM_COVERAGE = 0.60
"""Fraction of a window a symbol must actually have bars for to be scored."""

_MONDAY_EPOCH = pd.Timestamp("1970-01-05T00:00:00Z")
_WEEKEND_DAYS = (5, 6)
_DESK_CLOSED_SLOT = 0


def _is_desk_closed(open_time: pd.Timestamp) -> bool:
    """True for a bar that begins in a cell where professional desks are shut."""
    if open_time.dayofweek in _WEEKEND_DAYS:
        return True
    return (open_time.hour // 8) == _DESK_CLOSED_SLOT


class DeskClosedShare:
    """Cross-sectional long/short book on the volatility-neutralised desk-closed share."""

    def __init__(self) -> None:
        self._activity: dict[str, list[float]] = {}
        self._closed_flag: dict[str, list[bool]] = {}
        self._log_return: dict[str, list[float]] = {}
        self._last_close: dict[str, float] = {}
        self._consumed: dict[str, int] = {}
        self._keep = max(ACTIVITY_WINDOW_BARS, VOLATILITY_WINDOW_BARS)

    # -- measurement -------------------------------------------------------------------------

    def _ingest(self, symbol: str, frame: pd.DataFrame) -> None:
        """Append rows this symbol has not been shown before. The context frame only ever grows."""
        start = self._consumed.get(symbol, 0)
        if len(frame) <= start:
            return
        activity = self._activity.setdefault(symbol, [])
        flags = self._closed_flag.setdefault(symbol, [])
        returns = self._log_return.setdefault(symbol, [])
        block = frame.iloc[start:]
        opens = pd.DatetimeIndex(block["open_time"])
        notional = block["quote_volume"].to_numpy(dtype=float)
        closes = block["close"].to_numpy(dtype=float)
        previous = self._last_close.get(symbol)
        for open_time, traded, close in zip(opens, notional, closes, strict=True):
            activity.append(float(traded) if traded == traded and traded > 0.0 else 0.0)
            flags.append(_is_desk_closed(open_time))
            if previous is not None and previous > 0.0 and close == close and close > 0.0:
                returns.append(math.log(close / previous))
            else:
                returns.append(0.0)
            if close == close and close > 0.0:
                previous = close
        self._last_close[symbol] = previous if previous is not None else float("nan")
        self._consumed[symbol] = len(frame)
        if len(activity) > self._keep:
            excess = len(activity) - self._keep
            del activity[:excess]
            del flags[:excess]
            del returns[:excess]

    def _desk_closed_share(self, symbol: str) -> float | None:
        activity = self._activity.get(symbol)
        flags = self._closed_flag.get(symbol)
        if activity is None or flags is None:
            return None
        window = ACTIVITY_WINDOW_BARS
        if len(activity) < int(window * MINIMUM_COVERAGE):
            return None
        recent_activity = activity[-window:]
        recent_flags = flags[-window:]
        total = 0.0
        closed = 0.0
        for value, flag in zip(recent_activity, recent_flags, strict=True):
            total += value
            if flag:
                closed += value
        if total <= 0.0:
            return None
        return closed / total

    def _realised_volatility(self, symbol: str) -> float | None:
        returns = self._log_return.get(symbol)
        if returns is None:
            return None
        window = VOLATILITY_WINDOW_BARS
        if len(returns) < int(window * MINIMUM_COVERAGE):
            return None
        recent = returns[-window:]
        total = 0.0
        for value in recent:
            total += value * value
        return math.sqrt(total)

    # -- protocol ----------------------------------------------------------------------------

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        for symbol, frame in context.bars.items():
            self._ingest(str(symbol), frame)

        index = (context.decision_time - _MONDAY_EPOCH) // pd.Timedelta(hours=8)
        if (int(index) - REBALANCE_PHASE_BARS) % REBALANCE_CADENCE_BARS != 0:
            return None

        rows: list[tuple[str, float, float]] = []
        for symbol in context.eligible_symbols:
            name = str(symbol)
            share = self._desk_closed_share(name)
            volatility = self._realised_volatility(name)
            if share is not None and volatility is not None:
                rows.append((name, share, volatility))
        if len(rows) < MINIMUM_NAMES:
            return None

        share_rank = _centred_rank(rows, key=1)
        volatility_rank = _centred_rank(rows, key=2)
        residual = _project_out(share_rank, volatility_rank)
        return _rank_weights(residual)


def _centred_rank(
    rows: Sequence[tuple[str, float, float]], *, key: int
) -> dict[str, float]:
    """Cross-sectional rank on [-1, +1], ties broken by symbol so the map is deterministic."""
    ordered = sorted(rows, key=lambda row: (row[key], row[0]))
    count = len(ordered)
    half = (count - 1) / 2.0
    return {row[0]: (position - half) / half for position, row in enumerate(ordered)}


def _project_out(
    signal: Mapping[str, float], control: Mapping[str, float]
) -> dict[str, float]:
    """One ordinary least squares projection of ``signal`` on ``control``, cross-sectionally.

    Both inputs are centred ranks, so their means are zero by construction and no intercept is
    needed. What remains is the part of the calendar characteristic that realised volatility --
    the factor it shares most of its raw content with, and another team's mandate -- does not
    already explain.
    """
    cross = 0.0
    norm = 0.0
    for symbol, value in control.items():
        cross += signal[symbol] * value
        norm += value * value
    beta = cross / norm if norm > 0.0 else 0.0
    return {symbol: signal[symbol] - beta * control[symbol] for symbol in signal}


def _rank_weights(residual: Mapping[str, float]) -> Mapping[str, float]:
    """Re-rank the residual, raise to WEIGHT_POWER, flip sign, and dollar-neutralise.

    A HIGH desk-closed share is the short side, so the rank is negated before weighting.
    """
    ordered = sorted(residual.items(), key=lambda item: (item[1], item[0]))
    count = len(ordered)
    half = (count - 1) / 2.0
    raw: dict[str, float] = {}
    for position, (symbol, _value) in enumerate(ordered):
        centred = (position - half) / half
        magnitude = abs(centred) ** WEIGHT_POWER
        raw[symbol] = -(1.0 if centred >= 0.0 else -1.0) * magnitude

    mean = sum(raw.values()) / count
    centred_weights = {symbol: value - mean for symbol, value in raw.items()}
    gross = sum(abs(value) for value in centred_weights.values())
    if gross <= 0.0:
        return {}
    return {symbol: value / gross for symbol, value in centred_weights.items()}


def build_strategy() -> DeskClosedShare:
    return DeskClosedShare()
