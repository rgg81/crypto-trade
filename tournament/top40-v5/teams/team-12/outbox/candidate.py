"""team-12 -- volume-shock events, nominated book.

An extreme quote-volume bar is a state marker, not a directional signal: it marks a bar whose
marginal clearing price was set by flow that *had* to trade. The tradable question is not "was
there volume" but "what did that volume cost in price". A bar that moved a lot of price with many
small prints per unit of volume was impatient flow tearing through a thin book -- the liquidity
provider who absorbed it has to be paid, so the move reverses. A bar that moved little price with
few large prints per unit of volume was absorbed by a deep, two-sided book -- that is patient size,
not pressure, and it does not owe anybody a rebate.

So the book fades the event-bar move, and the *strength* of the fade is set by how dislocated the
event was. At the absorbed extreme the fade turns over into a mild drift. That is the sealed
thesis's Stage-A {Axis A x Axis B} cell, written continuously rather than as a median split.

Every quantity is recomputed from past-only rows at each decision; nothing is carried across
calls, no date or symbol identity is referenced, and every input is a log difference, a z-score or
a cross-sectional rank, so the book is invariant to price-magnitude rescaling and calendar shifts.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

# --- event definition -------------------------------------------------------------------------
LOOKBACK = 30  # L: trailing bars for every within-symbol baseline (sealed thesis default)
Z_LO = 1.0  # below this the bar is not an event at all
Z_HI = 2.5  # at and above this the event carries full weight
HOLD_BARS = 10  # overlapping event cross-sections held; 80h window, ~40h average holding

# --- book shape -------------------------------------------------------------------------------
REVERSAL_TILT = 0.5  # base fade applied at the median absorption state
FLATTEN = 0.5  # signed power on the score; spreads weight, preserves order and sign
MIN_CROSS = 3  # names needed before a single event cross-section can be ranked
MIN_BOOK = 4  # names needed before a book is worth submitting

# --- contract caps, held inside the limits so float noise cannot breach them --------------------
MAX_WEIGHT = 0.0990
MAX_GROSS = 0.980
MAX_NET = 0.240
CAP_PASSES = 8

MIN_HISTORY = 2 * LOOKBACK + 10 + HOLD_BARS  # 80: kills new-listing z-score artifacts
NEEDED = LOOKBACK + HOLD_BARS  # 40 rows actually read per symbol

RETURN_FLOOR = 1e-12  # guards log(0) on a bar that closed exactly at its open
WEIGHT_FLOOR = 5e-5  # dust below this is not worth a fill
EPS = 1e-12

REQUIRED = ("open_time", "open", "close", "quote_volume")
OPTIONAL_SIZE = "trade_count"


def _epoch_ns(values):
    """Nanoseconds since epoch for a timestamp-like array, or ``None`` if it is not one."""
    array = np.asarray(values)
    if array.dtype.kind == "M":
        return array.astype("datetime64[ns]").astype("int64")
    if array.dtype.kind in "iu":
        return array.astype("int64")
    try:
        index = pd.DatetimeIndex(pd.to_datetime(array, utc=True))
    except (TypeError, ValueError, OverflowError):
        return None
    return index.tz_localize(None).to_numpy(dtype="datetime64[ns]").astype("int64")


def _numeric(frame: pd.DataFrame, column: str) -> np.ndarray:
    """Column as float, with anything uncoercible turned into NaN rather than an exception."""
    return pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)


def _safe_log(values: np.ndarray) -> np.ndarray:
    """Elementwise log, NaN wherever the input is not strictly positive and finite."""
    out = np.full(values.shape, np.nan, dtype=float)
    usable = np.isfinite(values) & (values > 0.0)
    out[usable] = np.log(values[usable])
    return out


def _centred_rank(values: np.ndarray) -> np.ndarray:
    """Cross-sectional rank mapped to [-1, +1]; all-equal input scores zero, not a fake spread."""
    count = values.size
    if count < 2:
        return np.zeros(count, dtype=float)
    spread = float(np.max(values) - np.min(values))
    if not math.isfinite(spread) or spread <= EPS:
        return np.zeros(count, dtype=float)
    order = np.argsort(values, kind="stable")
    ranks = np.empty(count, dtype=float)
    ranks[order] = np.arange(count, dtype=float)
    return 2.0 * ranks / (count - 1.0) - 1.0


def _extremity(z: float) -> float:
    """Event weight: zero below Z_LO, one at Z_HI, linear between. Monotone in shock size."""
    if not math.isfinite(z) or z <= Z_LO:
        return 0.0
    if z >= Z_HI:
        return 1.0
    return (z - Z_LO) / (Z_HI - Z_LO)


def _log_zscore(logs: np.ndarray, pos: int) -> float:
    """z-score of a log series at ``pos`` against the LOOKBACK entries strictly before it."""
    current = logs[pos]
    if not math.isfinite(current):
        return float("nan")
    window = logs[pos - LOOKBACK : pos]
    usable = window[np.isfinite(window)]
    if usable.size < LOOKBACK - 2:
        return float("nan")
    sd = float(usable.std(ddof=1))
    if not math.isfinite(sd) or sd <= EPS:
        return float("nan")
    return (current - float(usable.mean())) / sd


def _centred(series, pos: int) -> float:
    """Value at ``pos`` less its own trailing median.

    Centring on the symbol's own history is load-bearing: the raw impact and average-trade-size
    ratios are dominated by contract size, and a contract-size sort is not the mechanism claimed.
    """
    if series is None:
        return 0.0
    current = series[pos]
    if not math.isfinite(current):
        return float("nan")
    window = series[pos - LOOKBACK : pos]
    usable = window[np.isfinite(window)]
    if usable.size < LOOKBACK // 2:
        return float("nan")
    return float(current - float(np.median(usable)))


def _tail(frame, boundary):
    """Past-only tail of one symbol as plain arrays, or ``None`` if it cannot be trusted."""
    if frame is None or not isinstance(frame, pd.DataFrame):
        return None
    for column in REQUIRED:
        if column not in frame.columns:
            return None

    total = len(frame)
    if total < MIN_HISTORY:
        return None

    # Rows are ordered oldest to newest, so anything at or beyond the boundary is a suffix.
    # Fast path first: convert the whole stamp column only when the last row is not already past.
    if boundary is not None:
        last = _epoch_ns(frame["open_time"].to_numpy()[-1:])
        if last is None or last.size != 1:
            return None
        if int(last[0]) >= boundary:
            stamps_all = _epoch_ns(frame["open_time"].to_numpy())
            if stamps_all is None or stamps_all.size != total:
                return None
            total = int(np.searchsorted(stamps_all, boundary, side="left"))
            if total < MIN_HISTORY:
                return None
            frame = frame.iloc[:total]

    tail = frame.iloc[total - NEEDED : total]
    stamps = _epoch_ns(tail["open_time"].to_numpy())
    if stamps is None or stamps.size != NEEDED:
        return None

    quote = _numeric(tail, "quote_volume")
    log_quote = _safe_log(quote)
    move = _safe_log(_numeric(tail, "close")) - _safe_log(_numeric(tail, "open"))

    # Axis A, dislocation: log|return| - log(quote volume). How much price did this flow cost?
    impact = _safe_log(np.abs(move) + RETURN_FLOOR) - log_quote
    # Axis B, composition: log(quote volume / trade count). Block prints or a crowd arriving?
    if OPTIONAL_SIZE in tail.columns:
        size = log_quote - _safe_log(_numeric(tail, OPTIONAL_SIZE))
    else:
        size = None

    return {"time": stamps, "log_quote": log_quote, "move": move, "impact": impact, "size": size}


def _cross_section(panel: dict, event_ns: int) -> dict:
    """Score every symbol whose bar starting at ``event_ns`` was a volume-shock event.

    Direction is the cross-sectionally demeaned event-bar return. The state is the average of the
    two dislocation ranks. The contribution is ``-direction * (tilt + state) * extremity``:
    a hard fade at the dislocated end, a mild drift at the absorbed end, scaled by shock size.
    """
    symbols: list = []
    extremity: list = []
    moves: list = []
    axis_a: list = []
    axis_b: list = []

    for symbol, data in panel.items():
        stamps = data["time"]
        pos = int(np.searchsorted(stamps, event_ns, side="left"))
        if pos >= stamps.size or int(stamps[pos]) != event_ns or pos < LOOKBACK:
            continue

        weight = _extremity(_log_zscore(data["log_quote"], pos))
        if weight <= 0.0:
            continue

        move = float(data["move"][pos])
        if not math.isfinite(move):
            continue

        dislocation = _centred(data["impact"], pos)
        if not math.isfinite(dislocation):
            continue

        composition = _centred(data["size"], pos)
        if not math.isfinite(composition):
            composition = 0.0

        symbols.append(symbol)
        extremity.append(weight)
        moves.append(move)
        axis_a.append(dislocation)
        axis_b.append(-composition)  # small average print size reads as dislocation

    if len(symbols) < MIN_CROSS:
        return {}

    state = 0.5 * (
        _centred_rank(np.array(axis_a, dtype=float))
        + _centred_rank(np.array(axis_b, dtype=float))
    )
    direction = _centred_rank(np.array(moves, dtype=float))
    contribution = -np.array(extremity, dtype=float) * direction * (REVERSAL_TILT + state)
    return dict(zip(symbols, contribution.tolist()))


def _book(scores: dict) -> dict:
    """Neutralise, spread, and seat the book strictly inside the contract's caps."""
    symbols = sorted(scores)
    raw = np.array([scores[symbol] for symbol in symbols], dtype=float)
    raw = raw - raw.mean()

    # Signed power transform: preserves the ordering and the sign of every name while pulling
    # weight out of the few largest scores and into the rest. This is what buys effective breadth.
    raw = np.sign(raw) * np.abs(raw) ** FLATTEN
    raw = raw - raw.mean()

    gross = float(np.abs(raw).sum())
    if not math.isfinite(gross) or gross <= EPS:
        return {}
    weights = raw * (MAX_GROSS / gross)

    # Cap and redistribute rather than clip. A bare clip silently collapses gross exposure.
    for _ in range(CAP_PASSES):
        over = np.abs(weights) > MAX_WEIGHT
        if not bool(over.any()):
            break
        weights[over] = np.sign(weights[over]) * MAX_WEIGHT
        free = ~over
        headroom = MAX_GROSS - float(np.abs(weights).sum())
        free_gross = float(np.abs(weights[free]).sum())
        if headroom <= EPS or free_gross <= EPS:
            break
        weights[free] *= 1.0 + headroom / free_gross

    weights = np.clip(weights, -MAX_WEIGHT, MAX_WEIGHT)
    gross = float(np.abs(weights).sum())
    if gross > MAX_GROSS:
        weights *= MAX_GROSS / gross

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
    """Dislocation-conditioned book over extreme quote-volume bars. Holds no state."""

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        boundary_array = _epoch_ns(np.asarray([context.decision_time]))
        boundary = (
            int(boundary_array[0])
            if boundary_array is not None and boundary_array.size == 1
            else None
        )

        panel: dict = {}
        for symbol in context.eligible_symbols:
            data = _tail(context.bars.get(symbol), boundary)
            if data is not None:
                panel[symbol] = data
        if len(panel) < MIN_CROSS:
            return None

        # Align the held cross-sections on open_time, never on position: symbols have unequal
        # history and may skip a bar, so the same integer offset is not the same bar.
        stamps: set = set()
        for data in panel.values():
            stamps.update(int(value) for value in data["time"][-HOLD_BARS:])
        event_times = sorted(stamps)[-HOLD_BARS:]
        if not event_times:
            return None

        scores: dict = {}
        for event_ns in event_times:
            for symbol, value in _cross_section(panel, event_ns).items():
                scores[symbol] = scores.get(symbol, 0.0) + value / HOLD_BARS

        live = {
            symbol: value
            for symbol, value in scores.items()
            if math.isfinite(value) and value != 0.0
        }
        if len(live) < MIN_BOOK:
            return None
        return _book(live)


def build_strategy() -> VolumeShockEvents:
    return VolumeShockEvents()
