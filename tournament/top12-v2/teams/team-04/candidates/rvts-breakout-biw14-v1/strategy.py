"""Causal realized-volatility-curve breakout baseline for Team 04."""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd


SHORT_VOL_DAYS = 7
LONG_VOL_DAYS = 42
CURVE_LAG_DAYS = 7
MIN_CURVE_RATIO = 1.15
MIN_CURVE_STEEPENING = 1.08
CHANNEL_BARS = 42  # Fourteen days of 8h closing prices.
EVENT_BARS = 21  # Search the most recent seven days for a breakout.
MAX_NAMES_PER_SIDE = 3
WEIGHT_PER_NAME = 0.15


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _is_rebalance_boundary(decision_time: pd.Timestamp) -> bool:
    if decision_time != decision_time.normalize() or decision_time.weekday() != 0:
        return False
    return int(decision_time.isocalendar().week) % 2 == 0


def _root_mean_square(values: pd.Series) -> float:
    array = values.to_numpy(dtype=float, copy=False)
    return float(math.sqrt(float(np.mean(np.square(array)))))


def _signal(frame: pd.DataFrame, decision_time: pd.Timestamp) -> float | None:
    if not {"open_time", "close"}.issubset(frame.columns):
        return None

    # Work on a private copy and explicitly exclude every unfinished 8h bar.
    bars = frame.loc[:, ["open_time", "close"]].copy(deep=True)
    bars["open_time"] = pd.to_datetime(bars["open_time"], utc=True, errors="coerce")
    bars["close"] = pd.to_numeric(bars["close"], errors="coerce")
    bars = bars.dropna(subset=["open_time", "close"])
    bars = bars.loc[
        (bars["close"] > 0.0)
        & (bars["open_time"] + pd.Timedelta(hours=8) <= decision_time)
        & (bars["open_time"] >= decision_time - pd.Timedelta(days=56))
    ]
    bars = bars.sort_values("open_time", kind="mergesort")
    bars = bars.drop_duplicates(subset="open_time", keep="last").reset_index(drop=True)
    if len(bars) < 148:
        return None

    log_close = np.log(bars["close"].astype(float))
    returns = log_close.diff()
    return_times = bars["open_time"]

    short_cutoff = decision_time - pd.Timedelta(days=SHORT_VOL_DAYS)
    long_cutoff = decision_time - pd.Timedelta(days=LONG_VOL_DAYS)
    lag_boundary = decision_time - pd.Timedelta(days=CURVE_LAG_DAYS)
    lag_short_cutoff = lag_boundary - pd.Timedelta(days=SHORT_VOL_DAYS)
    lag_long_cutoff = lag_boundary - pd.Timedelta(days=LONG_VOL_DAYS)

    current_short = returns.loc[return_times >= short_cutoff].dropna()
    current_long = returns.loc[return_times >= long_cutoff].dropna()
    prior_short = returns.loc[
        (return_times >= lag_short_cutoff) & (return_times < lag_boundary)
    ].dropna()
    prior_long = returns.loc[
        (return_times >= lag_long_cutoff) & (return_times < lag_boundary)
    ].dropna()

    # Require roughly 80% of the expected observations so missing data cannot
    # turn a handful of returns into an apparent volatility regime.
    if min(len(current_short), len(prior_short)) < 17:
        return None
    if min(len(current_long), len(prior_long)) < 100:
        return None

    current_long_rv = _root_mean_square(current_long)
    prior_long_rv = _root_mean_square(prior_long)
    if current_long_rv <= 1e-12 or prior_long_rv <= 1e-12:
        return None

    current_curve = _root_mean_square(current_short) / current_long_rv
    prior_curve = _root_mean_square(prior_short) / prior_long_rv
    if not (math.isfinite(current_curve) and math.isfinite(prior_curve)):
        return None
    if current_curve < MIN_CURVE_RATIO:
        return None
    if prior_curve <= 1e-12 or current_curve / prior_curve < MIN_CURVE_STEEPENING:
        return None

    closes = bars["close"].to_numpy(dtype=float, copy=False)
    times = bars["open_time"].array
    first_event_index = max(CHANNEL_BARS, len(bars) - EVENT_BARS)
    event_direction = 0
    event_magnitude = 0.0

    # The most recent qualifying event wins if both breakout directions occur.
    for index in range(first_event_index, len(bars)):
        if times[index] < decision_time - pd.Timedelta(days=7):
            continue
        history = closes[index - CHANNEL_BARS : index]
        previous_high = float(np.max(history))
        previous_low = float(np.min(history))
        current_close = float(closes[index])
        if current_close > previous_high:
            event_direction = 1
            event_magnitude = math.log(current_close / previous_high)
        elif current_close < previous_low:
            event_direction = -1
            event_magnitude = math.log(previous_low / current_close)

    if event_direction == 0:
        return None

    # A stale event is rejected after price has crossed the old channel median.
    recent_median = float(np.median(closes[-CHANNEL_BARS:]))
    if event_direction > 0 and closes[-1] <= recent_median:
        return None
    if event_direction < 0 and closes[-1] >= recent_median:
        return None

    curve_excess = max(0.0, math.log(current_curve / MIN_CURVE_RATIO))
    strength = event_magnitude / current_long_rv + curve_excess
    if not math.isfinite(strength) or strength <= 0.0:
        return None
    return float(event_direction * strength)


class RealizedVolatilityTermStructureBreakout:
    """Biweekly balanced targets from volatility-confirmed price breakouts."""

    def target_weights(self, context: object, *, seed: int) -> Mapping[str, float] | None:
        del seed  # The rule is deterministic and intentionally uses no randomness.
        decision_time = _utc_timestamp(context.decision_time)
        if not _is_rebalance_boundary(decision_time):
            return None

        signals: list[tuple[str, float]] = []
        eligible = sorted(set(context.eligible_symbols))
        for symbol in eligible:
            frame = context.bars.get(symbol)
            if frame is None:
                continue
            value = _signal(frame, decision_time)
            if value is not None:
                signals.append((symbol, value))

        longs = sorted(
            ((symbol, value) for symbol, value in signals if value > 0.0),
            key=lambda item: (-item[1], item[0]),
        )
        shorts = sorted(
            ((symbol, value) for symbol, value in signals if value < 0.0),
            key=lambda item: (item[1], item[0]),
        )
        pair_count = min(MAX_NAMES_PER_SIDE, len(longs), len(shorts))
        if pair_count == 0:
            return {}

        weights: dict[str, float] = {}
        for symbol, _ in longs[:pair_count]:
            weights[symbol] = WEIGHT_PER_NAME
        for symbol, _ in shorts[:pair_count]:
            weights[symbol] = -WEIGHT_PER_NAME
        return {symbol: weights[symbol] for symbol in sorted(weights)}


def build_strategy() -> RealizedVolatilityTermStructureBreakout:
    return RealizedVolatilityTermStructureBreakout()
