"""team-12 -- volume-shock events, discovery baseline.

An extreme quote-volume z-score marks a bar whose clearing price was set by flow that had to
trade. Whether the absorber of that flow is paid for reversal or the shock is the front of a
drift depends on how much price the flow cost per unit of volume. This is the sealed thesis's
Stage-A cell {Axis A only, H = 3} at its declared defaults, and nothing else.

Timing: the event is the last closed bar in ``bars``; the book is entered at the next open. The
holding period is expressed as an overlapping average over the last ``HOLD_BARS`` event
cross-sections, recomputed from past-only rows at every decision, so no state is carried.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

# --- thesis section 4.1/4.2 declared defaults; none of these are searched in discovery ---
LOOKBACK = 30  # L: trailing bars for the volume z-score and the absorption baseline
Z_ENTRY = 2.0  # z*: event threshold on the log quote-volume z-score
HOLD_BARS = 3  # H: overlapping holding period, 3 x 8h = 24h
MIN_HISTORY = 2 * LOOKBACK + 10 + HOLD_BARS  # kills new-listing z-score artifacts
NEEDED = LOOKBACK + HOLD_BARS  # rows actually read per symbol

# --- exposure caps, held just inside the contract so float noise cannot breach them ---
MAX_WEIGHT = 0.0995
MAX_GROSS = 0.995
MAX_NET = 0.245

RETURN_FLOOR = 1e-12  # guards log(0) on a bar that closed exactly at its open
WEIGHT_FLOOR = 1e-6  # dust below this is not worth a fill
EPS = 1e-12

BAR_COLUMNS = ("open", "close", "quote_volume")


def _past_only(frame: pd.DataFrame, decision_time: pd.Timestamp) -> pd.DataFrame:
    """Drop anything at or beyond the decision boundary that the runner did not already drop."""
    index = frame.index
    if not isinstance(index, pd.DatetimeIndex):
        return frame
    try:
        mask = index <= decision_time
    except TypeError:
        return frame
    if bool(mask.all()):
        return frame
    return frame.loc[mask]


def _extract(frame, decision_time):
    """Return the (open, close, quote_volume) tail this strategy reads, or ``None``."""
    if frame is None or not isinstance(frame, pd.DataFrame):
        return None
    for column in BAR_COLUMNS:
        if column not in frame.columns:
            return None
    frame = _past_only(frame, decision_time)
    if len(frame) < MIN_HISTORY:
        return None
    tail = frame.iloc[-NEEDED:]
    return tuple(tail[column].to_numpy(dtype=float) for column in BAR_COLUMNS)


def _bar_return(open_px: float, close_px: float) -> float:
    """Intrabar log return -- the return the event bar's own volume actually produced."""
    if not (math.isfinite(open_px) and math.isfinite(close_px)):
        return float("nan")
    if open_px <= 0.0 or close_px <= 0.0:
        return float("nan")
    return math.log(close_px / open_px)


def _volume_z(quote_volume: np.ndarray, idx: int) -> float:
    """z-score of log quote volume at ``idx`` against the LOOKBACK bars strictly before it."""
    current = quote_volume[idx]
    window = quote_volume[idx - LOOKBACK : idx]
    if window.size < LOOKBACK or not math.isfinite(current) or current <= 0.0:
        return float("nan")
    if not bool(np.all(np.isfinite(window))) or bool(np.any(window <= 0.0)):
        return float("nan")
    logs = np.log(window)
    sd = float(logs.std(ddof=1))
    if not math.isfinite(sd) or sd <= EPS:
        return float("nan")
    return (math.log(current) - float(logs.mean())) / sd


def _log_impact(open_px: float, close_px: float, quote_volume: float) -> float:
    """Log Amihud impact: how much price the bar moved per unit of quote volume."""
    ret = _bar_return(open_px, close_px)
    if not math.isfinite(ret) or not math.isfinite(quote_volume) or quote_volume <= 0.0:
        return float("nan")
    return math.log(abs(ret) + RETURN_FLOOR) - math.log(quote_volume)


def _absorption(op: np.ndarray, cl: np.ndarray, qv: np.ndarray, idx: int) -> float:
    """Axis A: the event bar's impact-per-volume, centred on the symbol's own trailing median.

    The raw ratio is dominated by symbol size, so centring on the symbol's own history is what
    turns it into a state variable rather than a market-cap sort.
    """
    current = _log_impact(op[idx], cl[idx], qv[idx])
    if not math.isfinite(current):
        return float("nan")
    history = [_log_impact(op[j], cl[j], qv[j]) for j in range(idx - LOOKBACK, idx)]
    if len(history) < LOOKBACK or not all(math.isfinite(value) for value in history):
        return float("nan")
    return current - float(np.median(history))


def _event_leg(panel: dict, lag: int) -> dict:
    """Score one event cross-section: the bar sitting ``lag`` bars behind the boundary.

    Absorbed shocks (low impact per unit volume for that symbol) are held in the direction of the
    event bar. Dislocated shocks (high impact per unit volume) are faded. The split is the
    cross-sectional median of Axis A among that bar's events, exactly as preregistered.
    """
    events = []
    for symbol, (op, cl, qv) in panel.items():
        idx = len(qv) - 1 - lag
        z = _volume_z(qv, idx)
        if not math.isfinite(z) or z < Z_ENTRY:
            continue
        ret = _bar_return(op[idx], cl[idx])
        if not math.isfinite(ret) or ret == 0.0:
            continue
        state = _absorption(op, cl, qv, idx)
        if not math.isfinite(state):
            continue
        events.append((state, symbol, 1.0 if ret > 0.0 else -1.0))

    count = len(events)
    if count < 2:
        return {}

    events.sort(key=lambda item: item[0])
    half = count // 2
    leg = {}
    for rank, (_, symbol, direction) in enumerate(events):
        if rank < half:
            leg[symbol] = direction  # absorbed -> drift
        elif rank >= count - half:
            leg[symbol] = -direction  # dislocated -> reversal
    return leg


def _book(scores: dict) -> dict:
    """Dollar-neutralise, gross-normalise, then hold the contract's caps with room to spare."""
    symbols = [symbol for symbol, score in scores.items() if score != 0.0]
    if len(symbols) < 2:
        return {}

    raw = np.array([scores[symbol] for symbol in symbols], dtype=float)
    raw = raw - raw.mean()
    gross = float(np.abs(raw).sum())
    if not math.isfinite(gross) or gross <= EPS:
        return {}

    weights = np.clip(raw * (MAX_GROSS / gross), -MAX_WEIGHT, MAX_WEIGHT)
    gross = float(np.abs(weights).sum())
    if gross > MAX_GROSS:
        weights = weights * (MAX_GROSS / gross)

    net = float(weights.sum())
    if abs(net) > MAX_NET:
        side = weights > 0.0 if net > 0.0 else weights < 0.0
        dominant = float(np.abs(weights[side]).sum())
        if dominant > EPS:
            weights[side] *= max(0.0, 1.0 - (abs(net) - MAX_NET) / dominant)

    return {
        symbol: float(weight)
        for symbol, weight in zip(symbols, weights)
        if abs(float(weight)) >= WEIGHT_FLOOR
    }


class VolumeShockEvents:
    """Absorption-conditioned book over extreme quote-volume bars. Holds no state."""

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        decision_time = context.decision_time
        bars = context.bars

        panel = {}
        for symbol in context.eligible_symbols:
            arrays = _extract(bars.get(symbol), decision_time)
            if arrays is not None:
                panel[symbol] = arrays
        if len(panel) < 2:
            return {}

        scores: dict = {}
        for lag in range(HOLD_BARS):
            for symbol, direction in _event_leg(panel, lag).items():
                scores[symbol] = scores.get(symbol, 0.0) + direction

        return _book(scores)


def build_strategy() -> VolumeShockEvents:
    return VolumeShockEvents()
