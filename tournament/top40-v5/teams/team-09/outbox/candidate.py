"""team-09 — discovery candidate: volume-confirmed channel breakout.

The lane mandate in its most direct form: a Donchian channel breakout on closes, where an *entry*
requires confirmation from abnormal, direction-aligned taker participation, and an *exit* honours
any break regardless of participation.  Geometry and gate constants are drawn from the declared
parameter surface in ``lane/scouting/THESIS.md`` §5; nothing here is fitted to data.

Mechanism, counterparty and falsifiers: ``lane/outbox/RATIONALE.md``.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# --- declared configuration (THESIS.md §5.1-§5.2), mid-grid values, not searched -----------------
CHANNEL_LOOKBACK = 42       # N bars of 8h = 14 days; mid of the declared {6,12,21,42,84,168}
NORM_WINDOW = 63            # W bars for the per-symbol participation norm; from {21,63}
GATE_THRESHOLD = 1.0        # theta, in robust-z units; mid of the declared {0.5,1.0,1.5}

# --- fixed by construction (THESIS.md §5.4), declared rather than searched -----------------------
REPLAY_SPAN = 12            # break history replayed = REPLAY_SPAN*N + W + 2 bars
LIQUIDITY_WINDOW = 126      # trailing bars for the per-symbol liquidity read
LIQUIDITY_QUANTILE = 0.20   # drop the bottom quintile of the mounted universe
NET_BUDGET = 0.20           # our own |net|/gross ceiling; the engine hard cap is 0.25
MAX_WEIGHT = 0.10           # engine hard cap per symbol
GROSS_BUDGET = 1.0          # engine hard cap on sum of absolute weights
MAD_SCALE = 1.4826          # MAD -> sigma for a Gaussian
MIN_NORM_ROWS = 16          # a robust norm below this many observations is not trusted

REQUIRED_COLUMNS = frozenset({"close", "quote_volume", "taker_buy_quote_volume"})


def _robust_z(history: np.ndarray, value: float) -> float:
    """Robust z of ``value`` against the *prior* window, using median and MAD.

    Returns NaN when the window is too short or degenerate, which is treated downstream as
    "unconfirmed" rather than as a pass.
    """
    sample = history[np.isfinite(history)]
    if sample.size < MIN_NORM_ROWS or not math.isfinite(value):
        return float("nan")
    centre = float(np.median(sample))
    spread = float(np.median(np.abs(sample - centre)))
    if not math.isfinite(spread) or spread <= 0.0:
        return float("nan")
    return (value - centre) / (MAD_SCALE * spread)


def _taker_imbalance(quote_volume: np.ndarray, taker_buy_quote: np.ndarray) -> np.ndarray:
    """Share of quote volume lifted by buy-side takers, mapped to [-1, +1].

    This is who crossed the spread.  Passive volume is the side being run over, so it carries no
    directional information on its own.
    """
    share = np.where(quote_volume > 0.0, taker_buy_quote / np.where(quote_volume > 0.0, quote_volume, 1.0), np.nan)
    return 2.0 * share - 1.0


def _participation_score(
    quote_volume: np.ndarray, imbalance: np.ndarray, index: int, direction: int
) -> float:
    """Directional participation ``D`` at one bar: z(quote volume) * max(0, d * z(imbalance)).

    Abnormal participation alone is not enough — Karpoff (1987) says high volume mostly means a
    large move — so the volume z is multiplied by the aligned part of the taker imbalance z.  A
    break on ordinary or counter-aligned aggression scores zero or negative and is not taken.
    """
    start = index - NORM_WINDOW
    if start < 0:
        return float("nan")
    z_volume = _robust_z(quote_volume[start:index], float(quote_volume[index]))
    z_flow = _robust_z(imbalance[start:index], float(imbalance[index]))
    if not (math.isfinite(z_volume) and math.isfinite(z_flow)):
        return float("nan")
    return z_volume * max(0.0, direction * z_flow)


def _channel_breaks(close: np.ndarray) -> np.ndarray:
    """+1 where the close prints above the prior-N close high, -1 where below the prior-N low."""
    marks = np.zeros(close.size, dtype=np.int8)
    if close.size <= CHANNEL_LOOKBACK:
        return marks
    closes = pd.Series(close)
    upper = closes.rolling(CHANNEL_LOOKBACK).max().shift(1).to_numpy()
    lower = closes.rolling(CHANNEL_LOOKBACK).min().shift(1).to_numpy()
    marks[close > upper] = 1
    marks[close < lower] = -1
    return marks


def _breakout_state(
    close: np.ndarray, quote_volume: np.ndarray, imbalance: np.ndarray
) -> int:
    """Current position sign: +1 long, -1 short, 0 flat.

    The state is the direction of the most recent *confirmed* break, and a break in the opposite
    direction always closes it whether or not that break was confirmed.  Walking back over the
    trailing run of same-direction breaks is sufficient: any state older than the last direction
    change was already closed by it.
    """
    marks = _channel_breaks(close)
    events = np.flatnonzero(marks)
    if events.size == 0:
        return 0
    latest = int(marks[events[-1]])
    for position in range(events.size - 1, -1, -1):
        index = int(events[position])
        if int(marks[index]) != latest:
            return 0
        score = _participation_score(quote_volume, imbalance, index, latest)
        if math.isfinite(score) and score >= GATE_THRESHOLD:
            return latest
    return 0


class VolumeConfirmedBreakout:
    """Channel breakout whose entries require confirming taker participation.

    Holds no state between decisions: every read is recomputed from the past-only rows handed in
    with the context.
    """

    def target_weights(self, context, *, seed):
        minimum_rows = CHANNEL_LOOKBACK + NORM_WINDOW + 2
        replay_rows = REPLAY_SPAN * CHANNEL_LOOKBACK + NORM_WINDOW + 2

        weights = {symbol: 0.0 for symbol in context.eligible_symbols}

        frames = {}
        liquidity = {}
        for symbol in context.eligible_symbols:
            frame = context.bars.get(symbol)
            if frame is None or len(frame) < minimum_rows:
                continue
            if not REQUIRED_COLUMNS.issubset(frame.columns):
                continue
            window = frame.tail(replay_rows)
            recent = np.asarray(window["quote_volume"].to_numpy(), dtype=float)[-LIQUIDITY_WINDOW:]
            recent = recent[np.isfinite(recent)]
            if recent.size == 0:
                continue
            frames[symbol] = window
            liquidity[symbol] = float(np.median(recent))

        if not frames:
            return weights

        # Liquidity floor: bottom quintile of the mounted universe by trailing median quote volume.
        floor = float(np.quantile(np.array(list(liquidity.values()), dtype=float), LIQUIDITY_QUANTILE))

        longs = []
        shorts = []
        for symbol, frame in frames.items():
            if liquidity[symbol] <= 0.0 or liquidity[symbol] < floor:
                continue
            close = np.asarray(frame["close"].to_numpy(), dtype=float)
            quote_volume = np.asarray(frame["quote_volume"].to_numpy(), dtype=float)
            taker_buy_quote = np.asarray(frame["taker_buy_quote_volume"].to_numpy(), dtype=float)
            state = _breakout_state(
                close, quote_volume, _taker_imbalance(quote_volume, taker_buy_quote)
            )
            if state > 0:
                longs.append(symbol)
            elif state < 0:
                shorts.append(symbol)

        count_long = len(longs)
        count_short = len(shorts)
        if count_long + count_short == 0:
            return weights

        # Directional tilt is the breadth of the time-series signal, clipped to the net budget.
        # Whatever tilt the budget cannot carry is neutralised across the two sides, which is what
        # keeps a single-asset-class trend book two-sided under a |net| cap.
        tilt = (count_long - count_short) / float(count_long + count_short)
        tilt = max(-NET_BUDGET, min(NET_BUDGET, tilt))

        if count_long == 0 or count_short == 0:
            side = longs if count_long else shorts
            sign = 1.0 if count_long else -1.0
            unit = sign * NET_BUDGET / len(side)
            for symbol in side:
                weights[symbol] = unit
        else:
            long_unit = 0.5 * (1.0 + tilt) / count_long
            short_unit = 0.5 * (1.0 - tilt) / count_short
            for symbol in longs:
                weights[symbol] = long_unit
            for symbol in shorts:
                weights[symbol] = -short_unit

        # Respect the per-symbol cap by scaling the whole book rather than clipping names, so the
        # long/short balance survives the constraint instead of being distorted by it.
        peak = max(abs(value) for value in weights.values())
        if peak > MAX_WEIGHT:
            weights = {symbol: value * (MAX_WEIGHT / peak) for symbol, value in weights.items()}

        gross = sum(abs(value) for value in weights.values())
        if gross > GROSS_BUDGET:
            weights = {symbol: value * (GROSS_BUDGET / gross) for symbol, value in weights.items()}

        return {symbol: (value if math.isfinite(value) else 0.0) for symbol, value in weights.items()}


def build_strategy():
    return VolumeConfirmedBreakout()
