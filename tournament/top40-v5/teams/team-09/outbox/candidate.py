"""team-09 — decision candidate: event-stamped, volume-confirmed channel breakout.

Family: time-series trend.  Mandate: channel breakout gated on participation.

The position in a symbol is *stamped at a break event*, not recomputed as a continuous function
of every new bar:

  sign  — the direction of the break that established the current channel state, held until an
          opposite break stops-and-reverses it (three Donchian machines at 21 / 42 / 84 bars,
          averaged);
  size  — a participation confidence read *on that same establishing break bar* and then frozen
          for the life of the state.

Freezing the gate at the event is the difference between this candidate and the previous one.
The gate is a classification of a break (informed repricing vs inventory shock); implemented as a
per-bar multiplier it injects turnover at the gate statistic's noise frequency instead of at the
signal's, which is what put trial t02 under the triple-cost line.

Mechanism, counterparty and falsifiers: ``lane/outbox/RATIONALE.md``.
Preregistered thesis: ``lane/scouting/THESIS.md``.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# --- signal geometry (THESIS §5.1) ------------------------------------------------------------
# Channel basis is the extreme of closes, as declared.  exit_fraction = 1.0 (symmetric
# stop-and-reverse) is what the state machine below implements: any opposite break closes.
CHANNEL_LOOKBACKS = (21, 42, 84)        # 7 / 14 / 28 days on 8h bars

# --- participation gate (THESIS §5.2) ---------------------------------------------------------
NORM_WINDOW = 63                        # W: the per-symbol trailing norm, in bars
GATE_THETA = 1.0                        # theta, used as a tanh scale rather than as a cliff
GATE_GAMMA = 0.6                        # confidence spans [1-g, 1+g] = [0.4, 1.6]; never signed
Z_CLIP = 4.0
MIN_NORM_ROWS = 24

# --- fixed by construction (THESIS §5.4) ------------------------------------------------------
HISTORY_TAIL = 1000                     # bars replayed when locating the establishing break
LIQ_WINDOW = 126                        # trailing bars for the per-symbol liquidity read
LIQ_DROP = 0.20                         # drop the bottom quintile of the mounted universe
MIN_NAMES = 12                          # below this the book is not a portfolio; stay flat

# --- portfolio construction under the organiser's caps ----------------------------------------
GROSS_TARGET = 0.95
GROSS_CAP = 0.99
MAX_WEIGHT = 0.090
NET_TILT_MAX = 0.18
NET_TILT_SCALE = 0.50
NET_CAP = 0.22

EPS = 1e-12
TINY = 1e-300
# Warm-up for the *shortest* machine only.  A symbol short of a longer machine's history is not
# excluded: that machine simply contributes zero to a denominator that is always the full ensemble
# size, so a young listing is downweighted rather than dropped.  This is the intended treatment of
# listing-era heterogeneity (THESIS §6) and it protects effective breadth early in the window.
MIN_BARS = min(CHANNEL_LOOKBACKS) + NORM_WINDOW + 2
REQUIRED_COLUMNS = frozenset(
    {"close", "quote_volume", "taker_buy_quote_volume", "trade_count"}
)


def _robust_z(reference: np.ndarray, value: float) -> float:
    """Robust z of ``value`` against a strictly *prior* window, via median and MAD.

    Returns 0.0 — the neutral reading, not a pass — when the window is short or degenerate.
    """
    if not math.isfinite(value):
        return 0.0
    sample = reference[np.isfinite(reference)]
    if sample.size < MIN_NORM_ROWS:
        return 0.0
    centre = float(np.median(sample))
    scale = 1.4826 * float(np.median(np.abs(sample - centre)))
    if not (scale > EPS):
        return 0.0
    z = (value - centre) / scale
    if not math.isfinite(z):
        return 0.0
    return max(-Z_CLIP, min(Z_CLIP, z))


def _break_marks(closes: pd.Series, close: np.ndarray, lookback: int) -> np.ndarray:
    """+1 where the close prints above the prior-``lookback`` close high, -1 where below the low."""
    marks = np.zeros(close.size, dtype=np.int8)
    if close.size <= lookback:
        return marks
    rolling = closes.rolling(lookback)
    upper = rolling.max().shift(1).to_numpy()
    lower = rolling.min().shift(1).to_numpy()
    valid = np.isfinite(upper) & np.isfinite(lower)
    marks[valid & (close > upper)] = 1
    marks[valid & (close < lower)] = -1
    return marks


def _establishing_break(marks: np.ndarray) -> tuple[int, int]:
    """Direction of the current channel state and the index of the break that established it.

    The state is the direction of the most recent break; an opposite break always closes, so any
    state older than the last direction change was already stopped out.  Walking back to the
    *first* break of the current same-direction run is what makes the stamp stable: further breaks
    in the same direction extend the trend, they do not re-stamp the position.
    """
    events = np.flatnonzero(marks)
    if events.size == 0:
        return 0, -1
    direction = int(marks[events[-1]])
    stamp = int(events[-1])
    for position in range(events.size - 1, -1, -1):
        index = int(events[position])
        if int(marks[index]) != direction:
            break
        stamp = index
    return direction, stamp


def _confidence(
    log_volume: np.ndarray,
    imbalance: np.ndarray,
    log_ticket: np.ndarray,
    stamp: int,
    direction: int,
) -> float:
    """Participation confidence read on the establishing break bar, in [1-gamma, 1+gamma].

    ``align`` is the direction-signed taker imbalance: who crossed the spread, relative to the
    break.  ``amp`` is how far participation and ticket size departed from this symbol's own
    trailing norm — how much the alignment reading deserves to be trusted, never a reading in its
    own right (Karpoff 1987: raw volume tracks the size of the move, so a volume gate alone risks
    being a volatility filter in costume).

    Returns exactly 1.0 — the ungated weight — whenever the norm window is unavailable.
    """
    start = stamp - NORM_WINDOW
    if start < 0:
        return 1.0
    z_flow = _robust_z(imbalance[start:stamp], float(imbalance[stamp]))
    z_volume = _robust_z(log_volume[start:stamp], float(log_volume[stamp]))
    z_ticket = _robust_z(log_ticket[start:stamp], float(log_ticket[stamp]))
    align = math.tanh(direction * z_flow / GATE_THETA)
    amp = 0.5 * (1.0 + math.tanh(0.5 * (z_volume + z_ticket) / GATE_THETA))
    return 1.0 + GATE_GAMMA * align * amp


def _participation_series(frame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The three scale-free participation statistics, per bar.

    Every one is a ratio or a log-difference read against the symbol's *own* history, so none of
    them can be compared to a cross-sectional volume level and a global rescale leaves them fixed.
    """
    quote_volume = np.nan_to_num(
        frame["quote_volume"].to_numpy(dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0
    )
    taker_buy = np.nan_to_num(
        frame["taker_buy_quote_volume"].to_numpy(dtype=np.float64),
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )
    trades = np.nan_to_num(
        frame["trade_count"].to_numpy(dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0
    )
    quote_volume = np.maximum(quote_volume, 0.0)
    taker_buy = np.maximum(taker_buy, 0.0)
    trades = np.maximum(trades, 0.0)

    traded = quote_volume > EPS
    safe_volume = np.where(traded, quote_volume, 1.0)
    imbalance = np.where(traded, 2.0 * taker_buy / safe_volume - 1.0, np.nan)
    log_volume = np.where(traded, np.log(np.maximum(safe_volume, TINY)), np.nan)

    counted = traded & (trades > EPS)
    safe_trades = np.where(counted, trades, 1.0)
    log_ticket = np.where(
        counted, np.log(np.maximum(safe_volume / safe_trades, TINY)), np.nan
    )
    return log_volume, imbalance, log_ticket


def _symbol_score(frame) -> float | None:
    """Ensemble breakout state, each machine's sign scaled by its own frozen break confidence.

    A machine that has not broken yet contributes zero and still divides, so a symbol only carries
    a full-magnitude position when every horizon agrees.
    """
    close = frame["close"].to_numpy(dtype=np.float64)
    if close.size < MIN_BARS or not np.all(np.isfinite(close)) or np.any(close <= 0.0):
        return None
    log_volume, imbalance, log_ticket = _participation_series(frame)
    closes = pd.Series(close)

    total = 0.0
    for lookback in CHANNEL_LOOKBACKS:
        direction, stamp = _establishing_break(_break_marks(closes, close, lookback))
        if direction == 0:
            continue
        total += direction * _confidence(
            log_volume, imbalance, log_ticket, stamp, direction
        )
    return total / float(len(CHANNEL_LOOKBACKS))


def _finalise(weights: np.ndarray) -> np.ndarray:
    """Apply the organiser's caps, shaving the dominant side last for the net cap."""
    for _ in range(3):
        weights = np.clip(weights, -MAX_WEIGHT, MAX_WEIGHT)
        gross = float(np.sum(np.abs(weights)))
        if not (gross > EPS):
            return np.zeros_like(weights)
        weights = weights * (GROSS_TARGET / gross)

    weights = np.clip(weights, -MAX_WEIGHT, MAX_WEIGHT)
    gross = float(np.sum(np.abs(weights)))
    if gross > GROSS_CAP:
        weights = weights * (GROSS_CAP / gross)

    net = float(np.sum(weights))
    if abs(net) > NET_CAP:
        longs = weights > 0.0
        long_sum = float(np.sum(weights[longs]))
        short_sum = -float(np.sum(weights[~longs]))
        if net > 0.0 and long_sum > EPS:
            factor = min(1.0, max(0.0, (NET_CAP + short_sum) / long_sum))
            weights = np.where(longs, weights * factor, weights)
        elif net < 0.0 and short_sum > EPS:
            factor = min(1.0, max(0.0, (NET_CAP + long_sum) / short_sum))
            weights = np.where(longs, weights, weights * factor)
    return weights


class EventStampedBreakout:
    """Channel breakout whose position size is stamped by participation at the break.

    Holds nothing between decisions: every quantity is recomputed from the past-only rows handed
    in with the context.
    """

    def target_weights(self, context, *, seed):
        eligible = list(context.eligible_symbols)
        flat = {symbol: 0.0 for symbol in eligible}

        names = []
        scores = []
        liquidity = []
        for symbol in eligible:
            frame = context.bars.get(symbol)
            if frame is None or len(frame) < MIN_BARS:
                continue
            if not REQUIRED_COLUMNS.issubset(frame.columns):
                continue
            window = frame.tail(HISTORY_TAIL)

            volume = np.nan_to_num(
                window["quote_volume"].to_numpy(dtype=np.float64),
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )[-LIQ_WINDOW:]
            median_volume = float(np.median(volume)) if volume.size else 0.0
            if not (median_volume > 0.0):
                continue

            score = _symbol_score(window)
            if score is None or not math.isfinite(score):
                continue

            names.append(symbol)
            scores.append(score)
            liquidity.append(median_volume)

        if len(names) < MIN_NAMES:
            return flat

        # Liquidity floor: bottom quintile of the mounted universe by trailing median quote
        # volume.  Declared fixed by construction; it protects the participation statistics from
        # the thinnest and most wash-contaminated names (Cong et al. 2023).
        liquidity = np.asarray(liquidity, dtype=np.float64)
        floor = float(np.quantile(liquidity, LIQ_DROP))
        keep = liquidity >= floor
        if int(np.count_nonzero(keep)) < MIN_NAMES:
            keep = np.ones_like(liquidity, dtype=bool)
        names = [symbol for symbol, take in zip(names, keep) if take]
        values = np.asarray(scores, dtype=np.float64)[keep]

        # gross <= 1.0 against |net| <= 0.25 means a fully invested book cannot be one-sided, so
        # the time-series signal is spent as a cross-sectional core plus a bounded directional
        # tilt.  Nothing in the *score* is cross-sectional: only the budget is.
        market = float(np.mean(values))
        relative = values - market
        spread = float(np.sum(np.abs(relative)))
        if not (spread > EPS):
            return flat

        core = relative / spread
        tilt = NET_TILT_MAX * math.tanh(market / NET_TILT_SCALE)
        weights = _finalise(core + tilt * np.abs(core))

        book = dict(flat)
        for symbol, weight in zip(names, weights):
            value = float(weight)
            book[symbol] = value if math.isfinite(value) else 0.0
        return book


def build_strategy():
    return EventStampedBreakout()
