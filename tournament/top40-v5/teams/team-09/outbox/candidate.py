"""team-09 — volume-confirmed channel breakout (time-series trend).

Signal: George-Hwang nearness to a running channel extreme, ensembled over four
lookbacks, per symbol.  Gate: the position taken at the channel edge is amplified
when the aggressive (taker) flow in the same bars is aligned with the break and
abnormal in size and ticket, and attenuated when it is not.  The gate term is
proportional to |channel score|, so it acts at the break and vanishes mid-range.

Every decision is a pure function of the past-only rows in ``context``.  No state
crosses a decision boundary, no randomness, no absolute dates, no symbol names,
no price levels -- all statistics are ratios or log-differences taken against the
symbol's own trailing distribution.
"""

from __future__ import annotations

import math

import numpy as np

# --- signal geometry (THESIS 5.1) ------------------------------------------
# Channel basis is the extreme of closes; exit is symmetric (exit_fraction 1.0),
# which the continuous nearness score expresses without needing carried state.
CHANNEL_LOOKBACKS = (21, 42, 84, 168)   # 7 / 14 / 28 / 56 days on 8h bars
PRICE_SMOOTH = 3                        # bars averaged into the channel probe

# --- participation gate (THESIS 5.2) ---------------------------------------
NORM_WINDOW = 63                        # 21 days; the longer declared window
CONFIRM_BARS = 2                        # declared k = 2
GATE_THETA = 1.0                        # declared theta = 1.0, as a tanh scale
GATE_GAMMA = 0.6                        # soft scaler: modulation spans [0.4, 1.6]
Z_CLIP = 4.0

# --- fixed by construction (THESIS 5.4) ------------------------------------
MIN_BARS = 96
LIQ_WINDOW = 126
LIQ_DROP = 0.20                         # drop the bottom quintile by liquidity
MIN_NAMES = 10

# --- portfolio construction under the organiser's caps ---------------------
XS_CLIP = 3.0
XS_SHRINK = 0.20
XS_POWER = 0.70
GROSS_TARGET = 0.95
GROSS_CAP = 0.99
MAX_WEIGHT = 0.090
NET_TILT_MAX = 0.18
NET_TILT_SCALE = 0.50
NET_CAP = 0.22

TAIL = 200
EPS = 1e-12


def _rolling_sum(values, k):
    """Trailing ``k``-bar sums; result has ``len(values) - k + 1`` entries."""
    if k <= 1:
        return values
    if values.size < k:
        return values[:0]
    cumulative = np.cumsum(values)
    out = cumulative[k - 1:].copy()
    out[1:] -= cumulative[:-k]
    return out


def _robust_z(reference, value):
    """(value - median) / (1.4826 * MAD); 0.0 when the scale is degenerate."""
    if reference.size < 16 or not math.isfinite(value):
        return 0.0
    median = float(np.median(reference))
    scale = 1.4826 * float(np.median(np.abs(reference - median)))
    if not (scale > EPS):
        return 0.0
    z = (value - median) / scale
    if not math.isfinite(z):
        return 0.0
    return max(-Z_CLIP, min(Z_CLIP, z))


def _series_z(series, window):
    """Robust z of the latest observation against its own trailing window."""
    usable = min(window, series.size - 1)
    if usable < 16:
        return 0.0
    reference = series[-(usable + 1):-1]
    reference = reference[np.isfinite(reference)]
    return _robust_z(reference, float(series[-1]))


def _channel_score(close):
    """Nearness to the running channel extreme, averaged over the lookbacks.

    +1 means the smoothed price sits on the top of every available channel, -1 on
    the bottom.  Scale-free: it is a ratio of price differences.
    """
    if close.size < PRICE_SMOOTH + 2:
        return None
    probe = float(np.mean(close[-PRICE_SMOOTH:]))
    total = 0.0
    used = 0
    for lookback in CHANNEL_LOOKBACKS:
        if close.size < lookback:
            continue
        window = close[-lookback:]
        high = float(np.max(window))
        low = float(np.min(window))
        width = high - low
        if not (width > EPS):
            continue
        total += (2.0 * probe - high - low) / width
        used += 1
    if used == 0:
        return None
    return max(-1.0, min(1.0, total / used))


def _confirmation(quote_volume, taker_buy_quote, trade_count):
    """Read the participation at the channel edge.

    Returns ``(align, amp)``.  ``align`` in (-1, 1) is squashed robust-z of
    aggressive buy pressure -- positive means takers were lifting offers.  ``amp``
    in (0, 1) says how abnormal the participation was and how large the tickets
    were, i.e. how much the alignment reading should be trusted.
    """
    k = CONFIRM_BARS
    volume_k = _rolling_sum(quote_volume, k)
    taker_k = _rolling_sum(taker_buy_quote, k)
    count_k = _rolling_sum(trade_count, k)
    if volume_k.size < 20:
        return 0.0, 0.5

    traded = volume_k > EPS
    safe_volume = np.where(traded, volume_k, 1.0)
    imbalance = np.where(traded, 2.0 * taker_k / safe_volume - 1.0, np.nan)
    log_volume = np.where(traded, np.log(safe_volume), np.nan)

    counted = traded & (count_k > EPS)
    safe_count = np.where(counted, count_k, 1.0)
    log_ticket = np.where(counted, np.log(np.where(counted, volume_k / safe_count, 1.0)), np.nan)

    z_imbalance = _series_z(imbalance, NORM_WINDOW)
    z_volume = _series_z(log_volume, NORM_WINDOW)
    z_ticket = _series_z(log_ticket, NORM_WINDOW)

    align = math.tanh(z_imbalance / GATE_THETA)
    amp = 0.5 * (1.0 + math.tanh(0.5 * (z_volume + z_ticket) / GATE_THETA))
    return align, amp


def _clean(frame, column):
    values = frame[column].to_numpy(dtype=np.float64)
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    return np.maximum(values, 0.0)


def _finalise(weights):
    """Apply the organiser's caps, shaving the dominant side for the net cap."""
    weights = np.clip(weights, -MAX_WEIGHT, MAX_WEIGHT)
    gross = float(np.sum(np.abs(weights)))
    if gross > EPS:
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


class VolumeConfirmedBreakout:
    """Channel breakout gated on informed participation, run as a portfolio."""

    def target_weights(self, context, *, seed):
        bars = context.bars
        names = []
        signals = []
        liquidity = []

        for symbol in context.eligible_symbols:
            if symbol not in bars:
                continue
            frame = bars[symbol]
            if frame is None or len(frame) < MIN_BARS:
                continue
            recent = frame.iloc[-TAIL:]

            close = recent["close"].to_numpy(dtype=np.float64)
            if close.size < MIN_BARS or not np.all(np.isfinite(close)) or np.any(close <= 0.0):
                continue
            channel = _channel_score(close)
            if channel is None:
                continue

            quote_volume = _clean(recent, "quote_volume")
            median_volume = float(np.median(quote_volume[-LIQ_WINDOW:]))
            if not (median_volume > 0.0):
                continue

            align, amp = _confirmation(
                quote_volume,
                _clean(recent, "taker_buy_quote_volume"),
                _clean(recent, "trade_count"),
            )
            # Confirmation scales with |channel|: it bites at the break, not mid-range.
            score = channel + GATE_GAMMA * abs(channel) * align * amp
            if not math.isfinite(score):
                continue

            names.append(symbol)
            signals.append(score)
            liquidity.append(median_volume)

        if len(names) < MIN_NAMES:
            return {}

        liquidity = np.asarray(liquidity, dtype=np.float64)
        floor = float(np.quantile(liquidity, LIQ_DROP))
        keep = liquidity >= floor
        if int(np.count_nonzero(keep)) < MIN_NAMES:
            keep = np.ones_like(liquidity, dtype=bool)

        names = [symbol for symbol, take in zip(names, keep) if take]
        scores = np.asarray(signals, dtype=np.float64)[keep]

        # The caps force a long-short book: gross 1.0 against |net| 0.25 cannot be
        # one-sided.  Split the time-series signal into a cross-sectional core plus
        # a bounded directional tilt carrying the market-wide trend.
        market = float(np.mean(scores))
        relative = scores - market
        spread = float(np.std(relative))
        if not (spread > EPS):
            return {}

        z = np.clip(relative / spread, -XS_CLIP, XS_CLIP)
        shrunk = np.sign(z) * np.maximum(np.abs(z) - XS_SHRINK, 0.0)
        shaped = np.sign(shrunk) * np.power(np.abs(shrunk), XS_POWER)
        total = float(np.sum(np.abs(shaped)))
        if not (total > EPS):
            return {}

        core = shaped / total
        tilt = NET_TILT_MAX * math.tanh(market / NET_TILT_SCALE)
        weights = _finalise(core + tilt * np.abs(core))

        return {
            symbol: float(weight)
            for symbol, weight in zip(names, weights)
            if abs(weight) > 1e-6 and math.isfinite(weight)
        }


def build_strategy():
    return VolumeConfirmedBreakout()
